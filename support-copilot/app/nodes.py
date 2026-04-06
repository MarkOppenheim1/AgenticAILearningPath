# app/nodes.py
import json
import re

from langchain_openai import ChatOpenAI
from retrieve import retrieve_context_strings

llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)


def retrieve_context(state):
    chunks = retrieve_context_strings(state["user_query"], k=4)
    return {"retrieved_chunks": chunks}


def _parse_json_response(text: str) -> dict:
    """Parse model output that may include markdown code fences."""
    text = text.strip()

    # Remove ```json ... ``` or ``` ... ``` fences if present
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    return json.loads(text)


def classify_request(state):
    query = state["user_query"]
    context = "\n\n".join(state.get("retrieved_chunks", []))

    prompt = f"""
You are classifying customer support requests for a support copilot.

Return JSON only. Do not use markdown code fences.

Schema:
{{
  "request_type": "safe" | "sensitive" | "requires_human",
  "reason": "<short explanation>"
}}

Classification rules:
- "safe": straightforward FAQ or account guidance grounded in the provided context
- "sensitive": policy, billing, refunds, compensation, cancellations with possible financial or policy impact
- "requires_human": the context is insufficient, the request is high-risk, ambiguous, asks for exceptions, or should not be answered automatically

User query:
{query}

Retrieved context:
{context}
"""

    result = llm.invoke(prompt)

    # Handle both string and content object cases
    raw_text = result.content if isinstance(result.content, str) else str(result.content)
    print("\nDEBUG classifier raw output:")
    print(raw_text)

    try:
        parsed = _parse_json_response(raw_text)
        request_type = parsed["request_type"]
        reason = parsed["reason"]
    except Exception as e:
        request_type = "requires_human"
        reason = f"Classifier returned invalid JSON. Error: {e}"

    needs_approval = request_type == "sensitive"

    return {
        "request_type": request_type,
        "classification_reason": reason,
        "needs_approval": needs_approval,
    }


def draft_response(state):
    context = "\n\n".join(state.get("retrieved_chunks", []))
    request_type = state.get("request_type", "requires_human")

    if request_type == "requires_human":
        return {
            "draft_response": (
                "I do not have enough confidence to answer this automatically. "
                "Please route this request to a human support reviewer."
            )
        }

    if not context.strip():
        return {
            "draft_response": "I don't have enough information in the support docs to answer that confidently."
        }

    prompt = f"""
You are a customer support copilot.

Rules:
- Answer only from the provided context.
- If the context is insufficient, say so clearly.
- Do not invent policy details.
- Be concise and helpful.

User question:
{state['user_query']}

Context:
{context}
"""
    result = llm.invoke(prompt)
    return {"draft_response": result.content}