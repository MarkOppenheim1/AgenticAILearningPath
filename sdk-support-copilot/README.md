# SDK Support Copilot

A modern agentic AI project built using the **OpenAI Agents SDK + MCP (Model Context Protocol)**.

This project demonstrates how to build a production-style support copilot using:

- OpenAI Agents SDK (agent runtime)
- MCP (tool interoperability layer)
- Retrieval-Augmented Generation (RAG)
- Multi-agent orchestration (agents-as-tools)
- Conditional approval workflows
- Local FAISS vector database

---

## 🚀 Features

### 🧠 Agent Runtime
- Built with OpenAI Agents SDK
- Orchestrator + specialist agents
- Session memory with `SQLiteSession`

### 🔧 MCP Tools (decoupled)
- `retrieve_support_context` (RAG)
- `create_refund_ticket`
- `create_escalation_case`

### 📚 Retrieval (RAG)
- Markdown-based knowledge base
- Chunking + embeddings
- FAISS similarity search

### 🔐 Approval System
- Tool-level approval via MCP
- Conditional auto-approval logic

### 🔀 Multi-Agent Architecture
- Orchestrator agent (routing)
- FAQ agent (retrieval + answers)
- Actions agent (refunds + escalation)

### 🌐 MCP over HTTP
- Runs as standalone service
- Can be reused across systems

---

## 📁 Project Structure

```text
sdk-support-copilot/
  main.py
  mcp_server.py
  data/
    docs/
      refund_policy.md
      cancellation_policy.md
      shipping_faq.md
      account_management.md
      billing_faq.md
  .env
  requirements.txt
  README.md
```

---

## ⚙️ Setup Instructions

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd sdk-support-copilot
```

---

### 2. Create Virtual Environment

#### Windows (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### Windows (CMD)
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

#### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If needed:

```bash
pip install openai-agents mcp langchain-core langchain-community \
langchain-openai langchain-text-splitters faiss-cpu python-dotenv
```

---

### 4. Configure Environment

Create `.env` in project root:

```env
OPENAI_API_KEY=sk-...
PORT=8000
```

---

## ▶️ Running the System

### Step 1 — Start MCP Server (HTTP)

```bash
python mcp_server.py
```

Server will run on:

```
http://127.0.0.1:8000/mcp
```

---

### Step 2 — Run Agent App

Open a new terminal:

```bash
python main.py
```

---

## 🧪 Example Queries

### FAQ
```
How do I reset my password?
```

### Refund (multi-turn)
```
Can I get a refund for my annual plan?
My account email is mark@example.com and invoice ID is INV-12345
```

### Escalation
```
I'd like to speak to a manager about my invoice
```

---

## 🔍 How It Works

### Agent Flow

```text
User → Orchestrator
          ↓
     (decides)
          ↓
   FAQ Agent OR Actions Agent
          ↓
     MCP Tools
          ↓
     Response
```

---

### MCP Architecture

```text
Agent App
   ↓
MCP Client
   ↓ HTTP
MCP Server (tools)
   ↓
Data / Logic
```

---

### Approval Flow

```text
Tool call → require_approval
             ↓
     auto_approve() OR user prompt
             ↓
         execute tool
```

---

## 🧠 Key Concepts Demonstrated

- Agents vs workflows
- Tool orchestration
- Retrieval grounding
- Human-in-the-loop systems
- Protocol-based tool access (MCP)
- Multi-agent coordination

---

## ⚠️ Common Issues

### MCP connection errors
- Ensure server is running
- Verify correct URL (`/mcp` path)

### Retrieval timeout
- First run builds index → slower
- Increase timeout or warm startup

### Missing API key
- Ensure `.env` exists
- Ensure `load_dotenv()` is called

---

## 🔥 Future Improvements

- Add eval harness
- Add caching layer
- Add retry logic
- Add authentication to MCP server
- Connect to real backend APIs

---

## 📜 License

MIT (or your choice)

---

## 💡 Notes

This project is designed as a hands-on exploration of modern agentic AI systems using OpenAI Agents SDK and MCP.

It demonstrates real-world patterns used in production systems including orchestration, retrieval, and tool execution.

