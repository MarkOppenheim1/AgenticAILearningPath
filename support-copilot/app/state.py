from typing import List, Optional, TypedDict


class CopilotState(TypedDict, total=False):
    user_query: str
    retrieved_chunks: List[str]

    request_type: str
    classification_reason: str
    needs_approval: bool

    draft_response: str
    answer_confidence: str
    answer_sources: List[str]
    recommended_action: str

    approval_decision: Optional[str]

    tool_name: Optional[str]
    tool_input: dict
    tool_result: Optional[str]

    final_response: str