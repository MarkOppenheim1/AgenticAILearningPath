import asyncio
import uuid
from dotenv import load_dotenv

from agents import Agent, Runner, function_tool, SQLiteSession

from tools import create_refund_ticket, create_escalation_case
from retrieve import retrieve_support_context

load_dotenv()

retrieve_tool = function_tool(retrieve_support_context)

refund_tool = function_tool(
    create_refund_ticket,
    needs_approval=True,
)

escalation_tool = function_tool(
    create_escalation_case,
    needs_approval=True,
)

support_agent = Agent(
    name="Support Copilot",
    model="gpt-5.4-nano",
    instructions=(
        "You are a customer support copilot.\n"
        "Be concise, professional, and practical.\n"
        "\n"
        "You have access to internal support knowledge through the "
        "retrieve_support_context tool.\n"
        "Use that tool whenever a user asks about policy, billing, refunds, "
        "cancellations, shipping, account management, or support procedures.\n"
        "\n"
        "Rules:\n"
        "- Ground support answers in retrieved support context.\n"
        "- Mention the relevant source names when useful.\n"
        "- If the retrieved context is insufficient, say so clearly.\n"
        "- Use create_refund_ticket only for clear refund-related actions.\n"
        "- Use create_escalation_case only for manager/supervisor/escalation/"
        "formal-review requests.\n"
        "- Never claim a tool was run unless it actually ran.\n"
        "- If a request is ambiguous, ask one short clarifying question."
    ),
    tools=[retrieve_tool, refund_tool, escalation_tool],
)

session_id = uuid.uuid4().hex
session = SQLiteSession(session_id, "conversations.db")


def prompt_approval(tool_name: str, arguments: str | None) -> bool:
    answer = input(f"Approve {tool_name} with {arguments}? [y/N]: ").strip().lower()
    return answer in {"y", "yes", "approved"}


async def main() -> None:
    print("Support Copilot (OpenAI Agents SDK + RAG + approval)")
    print("Type 'exit' to quit.\n")
    print(f"Session ID: {session_id}\n")

    while True:
        user_input = input("User: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break

        result = await Runner.run(
            support_agent,
            user_input,
            session=session,
        )

        while result.interruptions:
            state = result.to_state()

            for interruption in result.interruptions:
                approved = await asyncio.get_running_loop().run_in_executor(
                    None,
                    prompt_approval,
                    interruption.name or "unknown_tool",
                    str(interruption.arguments),
                )

                if approved:
                    state.approve(interruption)
                else:
                    state.reject(interruption)

            result = await Runner.run(
                support_agent,
                state,
                session=session,
            )

        print(f"\nAssistant: {result.final_output}\n")


if __name__ == "__main__":
    asyncio.run(main())