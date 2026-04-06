# app/state.py
from typing import TypedDict, List, Optional

class CopilotState(TypedDict, total=False):
    user_query: str
    retrieved_chunks: List[str]
    
    request_type: str
    classification_reason: str
    needs_approval: bool
    
    draft_response: str
    approval_decision: Optional[str]
    final_response: str