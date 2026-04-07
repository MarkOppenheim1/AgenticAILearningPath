from datetime import datetime, UTC
import uuid

def create_refund_ticket(user_query: str) -> str:
    ticket_id = f"refund-{uuid.uuid4().hex[:8]}"
    created_at = datetime.now(UTC).isoformat(timespec="seconds") + "Z"

    return (
        f"Refund ticket created successfully.\n"
        f"Ticket ID: {ticket_id}\n"
        f"Created at: {created_at}\n"
        f"Reason: {user_query}"
    )

def create_escalation_case(user_query: str) -> str:
    case_id = f"esc-{uuid.uuid4().hex[:8]}"
    created_at = datetime.now(UTC).isoformat(timespec="seconds") + "Z"

    return (
        f"Escalation case created.\n"
        f"Case ID: {case_id}\n"
        f"Created at: {created_at}\n"
        f"Summary: {user_query}"
    )