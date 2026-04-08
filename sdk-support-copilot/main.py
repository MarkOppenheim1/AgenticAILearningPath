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
    },
    require_approval={
        "retrieve_support_context": "never",
        "create_refund_ticket": "always",
        "create_escalation_case": "always",
    },
)

support_agent = Agent(
    name="Support Copilot MCP",
    model="gpt-5.4-nano",
    instructions=(
        "You are a customer support copilot.\n"
        "Be concise, professional, and practical.\n"
        "\n"
        "Use retrieve_support_context for policy, billing, refunds, cancellations, "
        "shipping, account management, and support procedures.\n"
        "Use create_refund_ticket only when the user clearly wants a refund action "
        "and you have enough details.\n"
        "Use create_escalation_case when the user asks for a manager, supervisor, "
        "escalation, complaint handling, or formal review.\n"
        "\n"
        "Ground policy answers in retrieved context.\n"
        "If the request is ambiguous, ask one short clarifying question.\n"
        "Never claim a tool was run unless it actually ran."
    ),
    mcp_servers=[mcp_server],
)


def prompt_approval(tool_name: str, arguments: str | None) -> bool:
    answer = input(f"Approve {tool_name} with {arguments}? [y/N]: ").strip().lower()
    return answer in {"y", "yes", "approved"}


async def main() -> None:
    print("Support Copilot (OpenAI Agents SDK + MCP + approval)")
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