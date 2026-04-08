import asyncio
import uuid
from dotenv import load_dotenv

from agents import Agent, Runner, SQLiteSession
from agents.mcp import MCPServerStdio

load_dotenv()

session_id = uuid.uuid4().hex
session = SQLiteSession(session_id, "conversations.db")

mcp_server = MCPServerStdio(
    params={
        "command": "python",
        "args": ["mcp_server.py"],
    }
)

support_agent = Agent(
    name="Support Copilot MCP",
    model="gpt-5.4-nano",
    instructions=(
        "You are a customer support copilot.\n"
        "Be concise, professional, and practical.\n"
        "\n"
        "Use MCP tools when needed:\n"
        "- Use retrieve_support_context for policy, billing, refunds, cancellations, "
        "shipping, account management, and support procedures.\n"
        "- Use create_refund_ticket only when the user clearly wants a refund action "
        "and you have enough details.\n"
        "- Use create_escalation_case when the user asks for a manager, supervisor, "
        "escalation, complaint handling, or formal review.\n"
        "\n"
        "Ground policy answers in retrieved context.\n"
        "If the request is ambiguous, ask one short clarifying question.\n"
        "Never claim a tool was run unless it actually ran."
    ),
    mcp_servers=[mcp_server],
)


async def main() -> None:
    print("Support Copilot (OpenAI Agents SDK + MCP)")
    print(f"Session ID: {session_id}")
    print("Type 'exit' to quit.\n")

    async with mcp_server:
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