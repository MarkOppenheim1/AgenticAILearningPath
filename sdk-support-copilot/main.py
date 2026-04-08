import asyncio
from dotenv import load_dotenv

from agents import Agent, Runner, function_tool, SQLiteSession

from tools import create_refund_ticket, create_escalation_case

import uuid

load_dotenv()

refund_tool = function_tool(create_refund_ticket)
escalation_tool = function_tool(create_escalation_case)

support_agent = Agent(
    name="Support Copilot",
    model="gpt-5.4-nano",
    instructions=(
        "You are a customer support copilot.\n"
        "Be concise, professional, and practical.\n"
        "\n"
        "When to use tools:\n"
        "- Use create_refund_ticket when the user is clearly asking for a refund or refund-related action.\n"
        "- Use create_escalation_case when the user asks for a manager, supervisor, escalation, complaint handling, or formal review.\n"
        "\n"
        "When not to use tools:\n"
        "- If the user is only asking a general support question, answer directly.\n"
        "- If the request is ambiguous, ask one short clarifying question before using a tool.\n"
        "\n"
        "Never pretend a tool was run if it was not."
    ),
    tools=[refund_tool, escalation_tool],
)



async def main() -> None:
    print("Support Copilot (OpenAI Agents SDK)")
    print("Type 'exit' to quit.\n")

    session = SQLiteSession(uuid.uuid4().hex, "conversations.db")


    while True:
        user_input = input("User: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break

        result = await Runner.run(
            support_agent,
            user_input,
            session=session,
        )

        print(f"\nAssistant: {result.final_output}\n")


if __name__ == "__main__":
    asyncio.run(main())