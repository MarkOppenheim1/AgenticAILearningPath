from typing import Literal, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from app.retrieve import retrieve_context_strings


class ClassificationResult(BaseModel):
    request_type: Literal["safe", "sensitive", "requires_human"]
    reason: str = Field(description="Short explanation for the classification")


class AnswerResult(BaseModel):
    answer: str = Field(description="Customer support answer grounded in the provided context")
    confidence: Literal["high", "medium", "low"] = Field(
        description="Confidence in whether the answer is well-supported by the retrieved context"
    )
    sources: List[str] = Field(
        description="List of source filenames used to support the answer"
    )
    action: Literal["none", "approve_needed", "escalate"] = Field(
        description="Recommended next step"
    )


llm = ChatOpenAI(model="gpt-5.4-nano", temperature=0)
classifier_llm = llm.with_structured_output(ClassificationResult)
answer_llm = llm.with_structured_output(AnswerResult)


def retrieve_context(state):
    chunks = retrieve_context_strings(state["user_query"], k=4)
    return {"retrieved_chunks": chunks}


def classify_request(state):
    query = state["user_query"]
    context = "\n\n".join(state.get("retrieved_chunks", []))

    prompt = f"""
You are classifying customer support requests for a support copilot.

Classify into exactly one of these:
- safe
- sensitive
- requires_human

Classification rules:
- safe: straightforward FAQ or account guidance grounded in the provided context
- sensitive: policy, billing, refunds, compensation, cancellations with possible financial or policy impact
- requires_human: context is insufficient, request is high-risk, ambiguous, asks for exceptions, or should not be answered automatically

User query:
{query}

Retrieved context:
{context}
"""

    try:
        parsed = classifier_llm.invoke(prompt)
        request_type = parsed.request_type.strip()
        reason = parsed.reason.strip()
    except Exception as e:
        request_type = "requires_human"
        reason = f"Structured classifier failed: {e}"

    needs_approval = request_type == "sensitive"

    return {
        "request_type": request_type,
        "classification_reason": reason,
        "needs_approval": needs_approval,
    }


def _extract_sources(chunks: list[str]) -> list[str]:
    sources = []
    for chunk in chunks:
        if chunk.startswith("[SOURCE: "):
            first_line = chunk.splitlines()[0]
            source = first_line.replace("[SOURCE: ", "").replace("]", "").strip()
            if source not in sources:
                sources.append(source)
    return sources


def draft_response(state):
    context_chunks = state.get("retrieved_chunks", [])
    context = "\n\n".join(context_chunks)
    request_type = state.get("request_type", "requires_human")
    retrieved_sources = _extract_sources(context_chunks)

    if request_type == "requires_human":
        return {
            "draft_response": (
                "I do not have enough confidence to answer this automatically. "
                "Please route this request to a human support reviewer."
            ),
            "answer_confidence": "low",
            "answer_sources": retrieved_sources,
            "recommended_action": "escalate",
        }

    if not context.strip():
        return {
            "draft_response": (
                "I don't have enough information in the support docs "
                "to answer that confidently."
            ),
            "answer_confidence": "low",
            "answer_sources": [],
            "recommended_action": "escalate",
        }

    prompt = f"""
You are a customer support copilot.

Answer using only the provided context.

Return:
- a concise support answer
- a confidence level
- the supporting source filenames
- the recommended action

Rules:
- Do not invent policy details
- If context is weak, confidence should be low
- Only include sources that are actually relevant

User question:
{state["user_query"]}

Request type:
{request_type}

Available sources:
{retrieved_sources}

Context:
{context}
"""

    try:
        parsed = answer_llm.invoke(prompt)

        answer = parsed.answer.strip()
        confidence = parsed.confidence
        sources = parsed.sources
    except Exception as e:
        answer = f"Failed to generate structured answer: {e}"
        confidence = "low"
        sources = retrieved_sources

    if request_type == "safe":
        action = "none"
    elif request_type == "sensitive":
        action = "approve_needed"
    else:
        action = "escalate"

    return {
        "draft_response": answer,
        "answer_confidence": confidence,
        "answer_sources": sources,
        "recommended_action": action,
    }


def select_tool(state):
    query = state["user_query"].lower()
    request_type = state.get("request_type", "requires_human")
    approval_decision = state.get("approval_decision")
    recommended_action = state.get("recommended_action", "escalate")

    if request_type != "sensitive":
        return {
            "tool_name": None,
            "tool_input": {},
        }

    if approval_decision != "approved":
        return {
            "tool_name": None,
            "tool_input": {},
        }

    if recommended_action != "approve_needed":
        return {
            "tool_name": None,
            "tool_input": {},
        }

    refund_terms = [
        "refund",
        "money back",
        "chargeback",
        "billing reversal",
    ]

    escalation_terms = [
        "escalate",
        "manager",
        "supervisor",
        "speak to a manager",
        "speak with a manager",
        "talk to a manager",
        "manager review",
        "formal complaint",
        "complaint",
    ]

    if any(term in query for term in refund_terms):
        return {
            "tool_name": "create_refund_ticket",
            "tool_input": {"user_query": state["user_query"]},
        }

    if any(term in query for term in escalation_terms):
        return {
            "tool_name": "create_escalation_case",
            "tool_input": {"user_query": state["user_query"]},
        }

    return {
        "tool_name": None,
        "tool_input": {},
    }