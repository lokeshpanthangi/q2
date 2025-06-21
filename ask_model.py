import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

from validator import validate_answer, load_kb

load_dotenv() # Load variables from .env file

# --- Configuration ---
API_TOKEN = os.getenv("HUGGING_FACE_API_TOKEN") # No longer needs a default placeholder
MODEL_API_URL = "https://api-inference.huggingface.co/models/distilbert/distilbert-base-cased-distilled-squad"
KB_FILE_PATH = "kb.json"
LOG_FILE_PATH = "run.log"
SUMMARY_FILE_PATH = "summary.md"
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

# --- Questions ---
def get_questions():
    """Loads questions from the KB."""
    knowledge_base = load_kb(KB_FILE_PATH)
    # Return the full KB items, not just the questions
    in_kb_items = [{"question": item["question"], "answer": item["answer"]} for item in knowledge_base]
    return in_kb_items, knowledge_base

def query_model(question: str, context: str) -> str:
    """Sends a question to the Hugging Face model and returns the answer."""
    payload = {"inputs": {"question": question, "context": context}}

    try:
        response = requests.post(MODEL_API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        result = response.json()
        return result.get("answer", "Error: No answer field in response.")
    except requests.exceptions.RequestException as e:
        return f"Error: API request failed: {e}"
    except json.JSONDecodeError:
        return f"Error: Failed to decode API response: {response.text}"


def log_message(message: str):
    """Appends a timestamped message to the log file."""
    with open(LOG_FILE_PATH, "a") as log_file:
        log_file.write(f"[{datetime.now()}] {message}\n")

def generate_summary(results: dict):
    """Generates a markdown summary of the validation results."""
    summary = f"""# LLM Hallucination Detection Summary

## Run Metrics
- **Total Questions:** {results['total']}
- **Correct In-KB Answers (PASS):** {results['passed']}
- **Incorrect/Mismatched In-KB Answers:** {results['mismatched']}
- **Detected Out-of-Domain Questions:** {results['out_of_domain']}

---

## Failed Validations

"""
    if not results["failures"]:
        summary += "No validation failures recorded."
    else:
        for failure in results["failures"]:
            summary += f"- **Question:** {failure['question']}\n"
            summary += f"  - **Model Answer:** {failure['answer']}\n"
            summary += f"  - **Reason:** {failure['reason']}\n\n"

    with open(SUMMARY_FILE_PATH, "w") as summary_file:
        summary_file.write(summary)


def main():
    """Main function to run the validation process."""
    if os.path.exists(LOG_FILE_PATH):
        os.remove(LOG_FILE_PATH) # Clear log file for a fresh run

    in_kb_items, kb = get_questions()
    kb_lookup = {item['question'].lower(): item['answer'] for item in kb}

    results = {
        "total": len(in_kb_items),
        "passed": 0,
        "mismatched": 0,
        "out_of_domain": 0,
        "failures": []
    }

    log_message("--- Starting Automatic KB Validation ---")
    print("--- Starting Automatic KB Validation ---")

    # Process in-KB questions automatically
    for item in in_kb_items:
        question = item["question"]
        expected_answer = item["answer"]
        log_message(f"Asking question: '{question}'")
        
        # First attempt with context
        model_answer = query_model(question, context=expected_answer)
        log_message(f"Model 1st response: '{model_answer}'")
        
        status = validate_answer(question, model_answer, kb)
        log_message(f"Validation status: {status}")

        if status.startswith("RETRY"):
            log_message("Validation failed. Retrying...")
            
            # Second attempt with context
            model_answer = query_model(question, context=expected_answer)
            log_message(f"Model 2nd response: '{model_answer}'")
            
            status = validate_answer(question, model_answer, kb)
            log_message(f"Final validation status: {status}")
            
            if not status.startswith("PASS"):
                reason = status.split(':', 1)[1].strip()
                results["mismatched"] += 1
                results["failures"].append({"question": question, "answer": model_answer, "reason": reason})
            else:
                results["passed"] += 1 # Passed on second attempt
        else:
            results["passed"] += 1
    
    print("--- Automatic KB Validation Complete ---")
    log_message("--- Entering Interactive Mode ---")
    print("\n--- Entering Interactive Mode ---")

    # Interactive session
    while True:
        user_question = input("Enter a question (or type 'quit' to exit): ")
        if user_question.lower() == 'quit':
            break
        
        log_message(f"User asked: '{user_question}'")
        results["total"] += 1

        # Determine context: use KB answer if available, otherwise it's out-of-domain
        context = kb_lookup.get(user_question.lower(), "")
        
        model_answer = query_model(user_question, context=context)
        status = validate_answer(user_question, model_answer, kb)

        print("\n--------------------")
        print(f"Model Answer: '{model_answer}'")
        print(f"Validation: {status}")
        print("--------------------\n")
        log_message(f"Model response: '{model_answer}'")
        log_message(f"Validation status: {status}")

        # Update results based on interactive validation
        if status == "PASS":
            results["passed"] += 1
        elif status == "RETRY: out-of-domain":
            results["out_of_domain"] += 1
        else: # Any other failure is a mismatch
            results["mismatched"] += 1
            reason = status.split(':', 1)[1].strip()
            results["failures"].append({"question": user_question, "answer": model_answer, "reason": reason})


    log_message("--- Run Finished ---")
    generate_summary(results)
    print(f"\nProcess complete. Check '{LOG_FILE_PATH}' for detailed logs and '{SUMMARY_FILE_PATH}' for the summary.")

if __name__ == "__main__":
    main() 