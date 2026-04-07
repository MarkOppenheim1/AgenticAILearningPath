# app/nodes.py
from typing import Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from retrieve import retrieve_context_strings


class ClassificationResult(BaseModel):
    request_type: Literal["safe", "sensitive", "requires_human"]
    reason: str = Field(
        description="Short explanation for the classification"
    )

llm = ChatOpenAI(model="gpt-5-nano", temperature=0)
classifier_llm = llm.with_structured_output(ClassificationResult)


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

    if request_type not in {"safe", "sensitive", "requires_human"}:
        request_type = "requires_human"
        reason = f"Unexpected classifier label returned. Original reason: {reason}"

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
            "draft_response": (
                "I don't have enough information in the support docs "
                "to answer that confidently."
            )
        }

    prompt = f"""
        You are a customer support copilot.

        Rules:
        - Answer only from the provided context.
        - If the context is insufficient, say so clearly.
        - Do not invent policy details.
        - Be concise and helpful.

        User question:
        {state["user_query"]}

        Context:
        {context}
        """
    result = llm.invoke(prompt)
    return {"draft_response": result.content}