# LLM Hallucination Detection & Guardrail System

## 1. Overview

This project is a Python-based system designed to detect and mitigate "hallucinations" in Language Model (LLM) responses. It functions as a set of guardrails by validating the LLM's answers against a predefined factual Knowledge Base (KB).

The system first automatically verifies a known set of facts and then enters an interactive mode, allowing a user to ask any question and see the validation result in real-time. This serves as a practical demonstration of how to enforce factuality and prevent a model from confidently answering questions about topics it has not been trained on (out-of-domain queries).

---

## 2. Features

- **Knowledge Base Validation:** Automatically checks LLM responses against a local `kb.json` file.
- **Hallucination Detection:** Identifies and flags when a model's answer to a known question differs from the ground truth.
- **Out-of-Domain Guardrail:** Detects when a question is not covered by the knowledge base and prevents the model from "guessing."
- **Automated Retry Logic:** Attempts to re-query the model once if a validation check initially fails.
- **Interactive Mode:** Allows a user to ask questions directly from the terminal and get immediate feedback on the model's answer and validation status.
- **Comprehensive Logging:** Records every transaction (questions, answers, validation results) in `run.log` for debugging and auditing.
- **Automated Summary Reports:** Generates a clean `summary.md` file with performance metrics after each run.
- **Secure Configuration:** Uses a `.env` file for securely managing the Hugging Face API token.

---

## 3. How It Works

The system operates in two main phases when you execute `python ask_model.py`:

#### Phase 1: Automatic KB Validation

1.  **Load Knowledge:** The script loads the 10 factual question-answer pairs from `kb.json`.
2.  **Query & Extract:** For each question, it queries the `distilbert/distilbert-base-cased-distilled-squad` model on Hugging Face. Crucially, it provides the correct answer from the KB as the `context`. As this is an **extractive** model, its job is to extract the answer from the provided context.
3.  **Validate:** The model's extracted answer is compared against the known answer in the KB.
4.  **Log:** The result (`PASS` or `RETRY`) is logged, and if a retry is needed, the process is repeated once.

#### Phase 2: Interactive Mode

1.  **User Prompt:** After the automatic validation is complete, the script prompts you to enter a question.
2.  **Context Check:** It checks if your question exists in the `kb.json` file.
    - If **yes**, it retrieves the correct answer to use as the context.
    - If **no**, it uses an empty string `""` as the context, signaling an out-of-domain query.
3.  **Query & Validate:** The model is queried, and the response is immediately validated.
4.  **Instant Feedback:** The model's answer and the validation result (`PASS`, `RETRY: answer differs from KB`, or `RETRY: out-of-domain`) are printed directly to the terminal.
5.  **Loop:** The system waits for your next question. You can type `quit` to exit.

Upon exit, a final `summary.md` is generated with the combined results from both the automatic and interactive sessions.

---

## 4. Project Structure

```
q2/
├── .env                  # Securely stores your API token (you must create this)
├── README.md             # This file
├── ask_model.py          # The main script to run the project
├── kb.json               # The knowledge base with Q-A pairs
├── run.log               # Detailed log file generated after a run
├── summary.md            # Summary report file generated after a run
└── validator.py          # Contains the core validation logic
```

---

## 5. Setup and Usage

Follow these steps to run the project:

**Step 1: Install Dependencies**

This project requires Python 3 and the `requests` and `python-dotenv` libraries.

```bash
pip install requests python-dotenv
```

**Step 2: Create the Environment File**

1.  In the project's root directory, create a new file named `.env`.
2.  Add your Hugging Face API token to this file in the following format:

    ```
    HUGGING_FACE_API_TOKEN=your_actual_token_here
    ```

**Step 3: Run the Script**

Execute the main script from your terminal:

```bash
python ask_model.py
```

The script will first run the automatic validation and then prompt you for interactive questions.

---

## 6. What We Learned From Building This Project

This project provided several critical insights into working with LLMs in a real-world setting:

1.  **Extractive vs. Generative Models:** The most significant lesson was understanding the fundamental difference between model types. Our chosen model, `distilbert-squad`, is **extractive**, meaning it finds answers within a provided `context`. It doesn't generate new text. Our initial `404` errors and nonsensical responses were due to providing it with no context to extract from. This highlighted the importance of reading the model's documentation to understand its specific architecture and requirements.

2.  **Context is King:** We learned that the input to an LLM is more than just a prompt. The `context` you provide fundamentally shapes its output. For extractive models, the context is everything. For generative models, it steers the response. Garbage in, garbage out.

3.  **The Necessity of Guardrails:** We cannot blindly trust LLMs for factual applications. This project demonstrated two simple but powerful guardrail patterns:
    *   **Fact-Checking:** If you have a knowledge base, you can force the model to align with known facts.
    *   **Domain Awareness:** By checking against the KB, we can determine if a question is "in-domain" or "out-of-domain" and prevent the model from hallucinating an answer to something it doesn't know.

4.  **Real-World Debugging is Iterative:** Our journey to a working solution was not linear. We systematically diagnosed and solved a chain of distinct problems:
    *   `401 Unauthorized`: An authentication issue, fixed by correctly implementing API token management.
    *   `404 Not Found`: A configuration issue, fixed by finding the correct model identifier.
    *   **Logical Error**: A conceptual issue, fixed by understanding the model's extractive nature and providing the correct context in the API call.

5.  **Software Engineering Best Practices Matter:** Even in a small project, following good practices paid off. Separating logic into `validator.py` and `ask_model.py` made the code cleaner, and using a `.env` file for our API token kept our credentials secure and out of the source code.