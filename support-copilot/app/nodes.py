# app/nodes.py
from langchain_openai import ChatOpenAI
from retrieve import simple_retrieve

llm = ChatOpenAI(model="gpt-5-nano", temperature=0)

def retrieve_context(state):
    chunks = simple_retrieve(state["user_query"])
    return {"retrieved_chunks": chunks}

def classify_request(state):
    query = state["user_query"].lower()
    risky_terms = ["refund", "cancel account", "legal", "compensation", "escalate", "billing change"]
    needs_approval = any(term in query for term in risky_terms)

    if "refund" in query or "billing" in query:
        request_type = "policy_sensitive"
    elif "how" in query or "what" in query:
        request_type = "faq"
    else:
        request_type = "general"

    return {
        "request_type": request_type,
        "needs_approval": needs_approval,
    }

def draft_response(state):
    context = "\n\n".join(state.get("retrieved_chunks", []))
    prompt = f"""
You are a customer support copilot.
Answer ONLY from the provided context.
If the context is insufficient, say so clearly, and do not answer for another assumed question.

User question:
{state['user_query']}

Context:
{context}
"""
    result = llm.invoke(prompt)
    return {"draft_response": result.content}