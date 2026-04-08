import asyncio
from dotenv import load_dotenv

from agents import Agent, Runner, function_tool, SQLiteSession

from tools import create_refund_ticket, create_escalation_case

import uuid

load_dotenv()

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
        "Use create_refund_ticket when the user is clearly asking for a refund.\n"
        "Use create_escalation_case when the user asks for a manager, supervisor, "
        "escalation, complaint handling, or formal review.\n"
        "\n"
        "If the request is ambiguous, ask one short clarifying question.\n"
        "Never claim a tool was run unless it actually ran."
    ),
    tools=[refund_tool, escalation_tool],
)

session = SQLiteSession(uuid.uuid4().hex, "conversations.db")


def prompt_approval(tool_name: str, arguments: str | None) -> bool:
    answer = input(f"Approve {tool_name} with {arguments}? [y/N]: ").strip().lower()
    return answer in {"y", "yes", "approved"}


async def main() -> None:
    print("Support Copilot (OpenAI Agents SDK + approval)")
    print("Type 'exit' to quit.\n")

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
                    interruption.arguments,
                )

                if approved:
                    state.approve(interruption, always_approve=False)
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