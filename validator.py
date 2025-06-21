import json

def validate_answer(question: str, model_answer: str, knowledge_base: list) -> str:
    """
    Validates a model's answer against a knowledge base.

    Args:
        question: The question that was asked.
        model_answer: The answer provided by the language model.
        knowledge_base: A list of dictionary objects, where each object has a 'question' and 'answer' key.

    Returns:
        A status string: "PASS", "RETRY: answer differs from KB", or "RETRY: out-of-domain".
    """
    for entry in knowledge_base:
        if entry["question"].lower() == question.lower():
            # Question is in the KB. Now check the answer.
            if entry["answer"].lower() in model_answer.lower():
                return "PASS"
            else:
                return f"RETRY: answer differs from KB (Expected: {entry['answer']})"
    
    # If the loop completes, the question was not found in the KB.
    return "RETRY: out-of-domain"

def load_kb(file_path: str) -> list:
    """Loads the knowledge base from a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f) 