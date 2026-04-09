# Support Copilot

A Python support copilot built as a learning project for modern agentic AI patterns.

## 🚀 Features

- LangGraph orchestration
- RAG (Retrieval-Augmented Generation)
- Human-in-the-loop approval
- Structured outputs (Pydantic)
- Tool execution (refund + escalation)
- Eval harness for testing

## 🧠 What It Does

This copilot can:
- Answer support questions from local docs
- Classify requests (safe, sensitive, requires_human)
- Require approval for sensitive actions
- Execute tools after approval
- Run evaluation tests

## 📁 Project Structure

support-copilot/
  app/
  data/
  evals/
  requirements.txt
  .env

## ⚙️ Setup

git clone https://github.com/MarkOppenheim1/AgenticAILearningPath.git
cd AgenticAILearningPath/support-copilot

python -m venv .venv
.\.venv\Scripts\Activate.ps1   (Windows)

pip install -r requirements.txt

Create .env:
OPENAI_API_KEY=sk-...

## ▶️ Run

python -m app.main

## 🧪 Eval

python -m evals.run_evals

## 📜 License

MIT
