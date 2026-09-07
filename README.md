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
- A starting codebase when the task calls for one
- In some older benchmarks, visible tests and expected outputs

New hidden-test benchmarks keep their evaluator under `evaluators/`, outside the
task directory. Give the coding model access only to the selected task directory;
do not mount or copy the corresponding evaluator into its workspace. After the
model finishes, the benchmark operator runs the evaluator manually against the
completed task. This separation prevents the model from reading or tailoring its
implementation to the correctness tests.

### 🔹 2. Open the project in your editor of choice
Open the directory in VS Code, JetBrains, or your preferred environment.

### 🔹 3. Paste the instructions into the coding assistant  
Choose which model you want to evaluate:

- GitHub Copilot with online models
- Copilot using local Ollama models  
- ChatGPT-Codex Visual Studio Code extension  
- Continue.dev with local LLMs  
- Codeium  
- Tabnine  
- LM Studio models  
- Your own fine-tuned LLM  

Paste the contents of **`instructions.md`** and let the assistant attempt the task.
