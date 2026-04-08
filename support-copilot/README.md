Support Copilot
A Python support copilot built as a learning project for modern agentic AI patterns with:
LangGraph for orchestration
FAISS + embeddings for retrieval
Structured outputs with Pydantic
Human-in-the-loop approval
Tool execution for refund and escalation actions
Eval harness for regression testing
This project started as a simple support assistant and evolved into a small agent workflow that can:
answer support questions from local Markdown docs
classify requests as safe / sensitive / requires human
require approval for sensitive actions
execute internal tools after approval
run evals against expected behavior
---
Features
1. Retrieval-Augmented Support Answers
The copilot loads local support docs from `data/docs/`, chunks them, embeds them, and retrieves relevant context with FAISS.
2. Request Classification
Each user request is classified into one of:
`safe`
`sensitive`
`requires_human`
This determines routing and approval behavior.
3. Structured Answers
The answer node returns structured state including:
drafted response
confidence
sources
recommended action
4. Human Approval
Sensitive requests trigger a human approval step before internal actions are taken.
5. Internal Tools
After approval, the copilot can run tools such as:
`create_refund_ticket`
`create_escalation_case`
6. Evaluation Harness
The project includes eval scripts to test:
classification
recommended action
source grounding
tool selection
---
Project Structure
```text
support-copilot/
  app/
    __init__.py
    main.py
    graph.py
    state.py
    retrieve.py
    nodes.py
    approval.py
    tool_node.py
    tools.py
  data/
    docs/
      refund_policy.md
      cancellation_policy.md
      shipping_faq.md
      account_management.md
      billing_faq.md
  evals/
    __init__.py
    test_cases.py
    run_evals.py
  requirements.txt
  .env
  README.md
```
---
How to Clone and Run
1. Clone the repository
```bash
git clone <your-repo-url>
cd support-copilot
```
Replace `<your-repo-url>` with your actual Git repository URL.
---
2. Create a virtual environment
Windows PowerShell
```powershell
python -m venv .venv
```
Windows Command Prompt
```cmd
python -m venv .venv
```
macOS / Linux
```bash
python3 -m venv .venv
```
---
3. Activate the virtual environment
Windows PowerShell
```powershell
.\.venv\Scripts\Activate.ps1
```
If PowerShell blocks activation, run this once in PowerShell:
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
Then activate again:
```powershell
.\.venv\Scripts\Activate.ps1
```
Windows Command Prompt
```cmd
.venv\Scripts\activate.bat
```
macOS / Linux
```bash
source .venv/bin/activate
```
---
4. Install dependencies
```bash
pip install -r requirements.txt
```
If `requirements.txt` is not fully up to date yet, these are the main packages used in this project:
```bash
pip install langgraph langchain-core langchain-community langchain-openai langchain-text-splitters faiss-cpu pydantic python-dotenv openai
```
---
5. Set up the `.env` file
Create a file named `.env` in the project root:
```text
support-copilot/.env
```
Example:
```env
OPENAI_API_KEY=sk-...
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=support-copilot
```
Required
`OPENAI_API_KEY`
Optional but recommended
`LANGSMITH_TRACING=true`
`LANGSMITH_API_KEY`
`LANGSMITH_PROJECT=support-copilot`
If you do not want tracing yet, you can omit the LangSmith values and keep only:
```env
OPENAI_API_KEY=sk-...
```
---
6. Add support documents
Place your support knowledge docs inside:
```text
data/docs/
```
Current examples include:
`refund_policy.md`
`cancellation_policy.md`
`shipping_faq.md`
`account_management.md`
`billing_faq.md`
These Markdown files are used as the local retrieval corpus.
---
7. Run the app
From the project root:
```bash
python -m app.main
```
You should run it from the project root so package imports like `from app.graph import graph` work correctly.
---
8. Run the eval harness
From the project root:
```bash
python -m evals.run_evals
```
This runs the predefined test suite and reports pass/fail across:
request classification
recommended action
sources
tool selection
---
Example Usage
Safe FAQ
```text
User: How do I reset my password?
```
Expected behavior:
classified as `safe`
answered directly
no approval required
no tool called
Sensitive Refund Request
```text
User: Can I get a refund for my annual plan after 10 days?
```
Expected behavior:
classified as `sensitive`
approval required
after approval, may create a refund ticket
Escalation Request
```text
User: I'd like to speak to a manager about my invoice
```
Expected behavior:
classified as `sensitive`
approval required
after approval, may create an escalation case
---
How the System Works
Graph Flow
```text
retrieve_context
  -> classify_request
  -> draft_response
  -> approval_gate
  -> select_tool
  -> run_tool
  -> finalize_response
```
Nodes Overview
retrieve_context  
Retrieves relevant chunks from local support docs using FAISS.
classify_request  
Classifies the request into `safe`, `sensitive`, or `requires_human`.
draft_response  
Produces a structured answer with confidence, sources, and recommended action.
approval_gate  
Interrupts for human approval on sensitive requests.
select_tool  
Chooses an internal tool after approval.
run_tool  
Executes the selected tool.
finalize_response  
Formats the final output for the user.
---
Tools
The project currently includes two sample internal tools:
`create_refund_ticket(user_query: str)`
Creates a simulated refund ticket.
`create_escalation_case(user_query: str)`
Creates a simulated escalation case.
These are intentionally local mock tools for learning and testing.
---
Retrieval Details
Retrieval uses:
`langchain_text_splitters.RecursiveCharacterTextSplitter`
`OpenAIEmbeddings`
`FAISS`
The FAISS index can be:
built in memory
optionally saved to disk for reuse
Support docs are split into chunks and retrieved semantically rather than by keyword only.
---
Evaluation Details
The eval harness is designed to support iterative improvement.
Each test case can check:
expected request type
expected recommended action
expected source overlap
expected tool name
Some eval cases auto-approve interruptions so post-approval tool execution can be tested end-to-end.
---
Common Commands
Activate venv
```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```
Install dependencies
```bash
pip install -r requirements.txt
```
Run app
```bash
python -m app.main
```
Run evals
```bash
python -m evals.run_evals
```
---
Common Issues
`ModuleNotFoundError: No module named 'app'`
Run from the project root with:
```bash
python -m app.main
```
instead of:
```bash
python app/main.py
```
`OPENAI_API_KEY` not found
Make sure:
`.env` exists in the project root
`load_dotenv()` is called before importing modules that initialize OpenAI clients
PowerShell activation blocked
Run:
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
Then activate the venv again.
First run is slow
The first run may take longer because embeddings and the FAISS index are being built.
---
Suggested Next Improvements
Possible next upgrades for this project:
persist FAISS index to disk automatically
add LangSmith trace screenshots/examples
add stricter eval scoring
add approval-mode evals for approved vs rejected branches
add a web UI
replace mock tools with real ticketing integrations
expose tools via MCP
---
License
Add the license of your choice here, for example:
```text
MIT
```
---
Notes
This project was built as a hands-on learning path for modern agentic AI engineering and demonstrates:
workflow orchestration
semantic retrieval
structured model outputs
human approval gates
tool calling
evaluation-driven iteration
