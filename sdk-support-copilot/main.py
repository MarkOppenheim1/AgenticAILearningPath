import asyncio
import re
import uuid
from datetime import datetime
from dotenv import load_dotenv

from agents import Agent, Runner, SQLiteSession
from agents.mcp import MCPServerStdio, MCPServerStdioParams

load_dotenv()


def looks_like_business_hours() -> bool:
    now = datetime.now()
    return now.weekday() < 5 and 9 <= now.hour < 17


def has_invoice_id(text: str) -> bool:
    return bool(re.search(r"\bINV[-_]?\d+\b", text, flags=re.IGNORECASE))


def has_email(text: str) -> bool:
    return bool(
        re.search(
            r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
            text,
            flags=re.IGNORECASE,
        )
    )


def auto_approve(interruption) -> bool:
    tool_name = interruption.name or ""
    args_text = str(interruption.arguments or "")

    if tool_name == "retrieve_support_context":
        return True

    if tool_name == "create_refund_ticket":
        return (
            has_invoice_id(args_text)
            and has_email(args_text)
            and looks_like_business_hours()
        )

    if tool_name == "create_escalation_case":
        risky_terms = ["legal", "lawsuit", "fraud", "chargeback", "attorney"]
        lower_args = args_text.lower()
        return not any(term in lower_args for term in risky_terms)

    return False


def prompt_approval(tool_name: str, arguments: str | None) -> bool:
    answer = input(f"Approve {tool_name} with {arguments}? [y/N]: ").strip().lower()
    return answer in {"y", "yes", "approved"}


session_id = uuid.uuid4().hex
session = SQLiteSession(session_id, "conversations.db")

mcp_server = MCPServerStdio(
    params=MCPServerStdioParams(
        command="python",
        args=["mcp_server.py"],
    ),
    require_approval={
        "retrieve_support_context": "never",
        "create_refund_ticket": "always",
        "create_escalation_case": "always",
    },
)

faq_agent = Agent(
    name="FAQ Agent",
    model="gpt-5.4-nano",
    handoff_description=(
        "Handles support FAQs, policy questions, billing explanations, "
        "account management, shipping, cancellations, and refund policy lookups."
    ),
    instructions=(
        "You are the FAQ specialist.\n"
        "Use retrieve_support_context for support-policy and documentation questions.\n"
        "Ground answers in retrieved context.\n"
        "Be concise and practical.\n"
        "Do not create refund or escalation actions yourself unless truly necessary.\n"
        "If the user is mainly asking for information, answer directly."
    ),
    mcp_servers=[mcp_server],
)

actions_agent = Agent(
    name="Actions Agent",
    model="gpt-5.4-nano",
    handoff_description=(
        "Handles internal support actions such as refund requests and manager/escalation cases."
    ),
    instructions=(
        "You are the actions specialist.\n"
        "Use retrieve_support_context when policy context is needed before acting.\n"
        "Use create_refund_ticket only when the user clearly wants a refund action "
        "and sufficient details are available.\n"
        "Use create_escalation_case when the user asks for a manager, supervisor, "
        "formal review, complaint handling, or escalation.\n"
        "If key details are missing, ask one short clarifying question first.\n"
        "Never claim a tool was run unless it actually ran."
    ),
    mcp_servers=[mcp_server],
)

triage_agent = Agent(
    name="Triage Agent",
    model="gpt-5.4-nano",
    instructions=(
        "You are the triage agent.\n"
        "Route the user to the best specialist.\n"
        "\n"
        "Send informational or policy questions to FAQ Agent.\n"
        "Send action-oriented requests like refunds, manager requests, disputes, "
        "or escalation requests to Actions Agent.\n"
        "\n"
        "Only answer directly if the request is trivial and does not require a specialist."
    ),
    handoffs=[faq_agent, actions_agent],
)


async def main() -> None:
    print("Support Copilot (OpenAI Agents SDK + MCP + handoffs)")
    print(f"Session ID: {session_id}")
    print("Type 'exit' to quit.\n")

    async with mcp_server:
        while True:
            user_input = input("User: ").strip()
            if user_input.lower() in {"exit", "quit"}:
                break

            result = await Runner.run(
                triage_agent,
                user_input,
                session=session,
            )

            while result.interruptions:
                state = result.to_state()

                for interruption in result.interruptions:
                    tool_name = interruption.name or "unknown_tool"
                    tool_args = str(interruption.arguments or "")

                    if auto_approve(interruption):
                        print(f"\nAUTO-APPROVED: {tool_name}")
                        state.approve(interruption)
                    else:
                        approved = await asyncio.get_running_loop().run_in_executor(
                            None,
                            prompt_approval,
                            tool_name,
                            tool_args,
                        )

                        if approved:
                            state.approve(interruption)
                        else:
                            state.reject(interruption)

                result = await Runner.run(
                    triage_agent,
                    state,
                    session=session,
                )

            print(f"\nAssistant: {result.final_output}\n")


if __name__ == "__main__":
    asyncio.run(main())