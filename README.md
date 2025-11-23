# **code-assistant-benchmarks**

A collection of **real-world coding tasks** designed to benchmark AI coding assistants — including GitHub Copilot (paid + local), Ollama-powered models, ChatGPT, Codeium, Continue.dev, Tabnine, LM Studio models, and any other LLM-based development tool.

These benchmarks evaluate the assistant’s ability to:

- Understand and modify multi-file codebases  
- Perform refactoring  
- Add/remove files  
- Maintain behavior under architectural changes  
- Write and update tests  
- Run and verify code
- Infer missing or incomplete instructions  
- Work across various programming languages  

The goal is to measure **accuracy, autonomy, reasoning, code quality, and reliability** in practical developer workflows.

---

## **Why this repository exists**

Most benchmarks only test “toy” prompts or isolated functions.  
Real developers need assistants that can:

- Read a project  
- Understand its structure  
- Safely refactor it  
- Write new components  
- Update tests  
- Keep everything running  

This repo provides **realistic, reproducible tasks** that expose the strengths and weaknesses of any coding model.

---

## **How to use these benchmarks**

### 🔹 1. Choose a benchmark project  
Each benchmark lives in its own directory (e.g., `python/todo_counter`, `python/order_refactor`, etc.).

Every project includes:

- `instructions.md` — high-level or minimal instructions  
- A starting codebase  
- Tests to validate correctness  
- Expected outputs  
- Optional *detailed* instruction versions for comparison  

### 🔹 2. Open the project in your editor  
Open the directory in VS Code, JetBrains, or your preferred environment.

### 🔹 3. Paste the instructions into the coding assistant  
Choose which model you want to evaluate:

- GitHub Copilot (GPT-4.1 / Claude / Qwen / Phi depending on tier)  
- Copilot using local Ollama models  
- ChatGPT VS Code extension  
- Continue.dev with local LLMs  
- Codeium  
- Tabnine  
- LM Studio models  
- Your own fine-tuned LLM  

Paste the contents of **`instructions.md`** and let the assistant attempt the task.

### 🔹 4. Run the tests  
Each benchmark includes a test runner, such as:

```bash
python -m tests.run_tests
