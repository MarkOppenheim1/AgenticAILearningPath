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
    client_session_timeout_seconds=30,
    require_approval={
        "retrieve_support_context": "never",
        "create_refund_ticket": "always",
        "create_escalation_case": "always",
    },
)

faq_agent = Agent(
    name="FAQ Agent",
    model="gpt-5.4-nano",
    instructions=(
        "You are the FAQ specialist.\n\n"
        "CRITICAL RULES:\n"
        "- ALWAYS call retrieve_support_context BEFORE answering any question.\n"
        "- You must call retrieve_support_context before producing any answer.\n"
        "- NEVER answer from your own knowledge.\n"
        "- ONLY answer using retrieved support documents.\n"
        "- If retrieval does not return useful information, say you don't have enough information.\n\n"
        "After retrieving context:\n"
        "- Answer concisely\n"
        "- Use the retrieved content\n"
        "- Mention sources when relevant\n"
    ),
    mcp_servers=[mcp_server],
)

actions_agent = Agent(
    name="Actions Agent",
    model="gpt-5.4-nano",
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

faq_tool = faq_agent.as_tool(
    tool_name="answer_support_question",
    tool_description=(
        "Answer support FAQs and policy questions using support documentation."
    ),
)

actions_tool = actions_agent.as_tool(
    tool_name="handle_support_action",
    tool_description=(
        "Handle action-oriented support requests like refunds, manager requests, "
        "complaints, disputes, and escalations."
    ),
)

orchestrator_agent = Agent(
    name="Support Orchestrator",
    model="gpt-5.4-nano",
    instructions=(
        "You are the support orchestrator.\n\n"
        "IMPORTANT:\n"
        "- All FAQ/policy questions MUST go through answer_support_question.\n"
        "- Do NOT answer policy questions yourself.\n"
        "- The FAQ agent is responsible for retrieval.\n\n"
        "Routing:\n"
        "- Use answer_support_question for informational/policy questions\n"
        "- Use handle_support_action for refunds, escalation, disputes\n"
    ),
    tools=[faq_tool, actions_tool],
)

def debug_run_result(result) -> None:
    print("\n=== DEBUG ===")
    print("Last agent:", getattr(result.last_agent, "name", result.last_agent))
    print("Final output:", result.final_output)
    print("Interruptions:", len(getattr(result, "interruptions", []) or []))

    print("\nNew items:")
    for idx, item in enumerate(result.new_items, start=1):
        print(f"{idx}. {type(item).__name__}")
        print(item)
        print()


async def main() -> None:
    print("Support Copilot (OpenAI Agents SDK + MCP + agents as tools)")
    print(f"Session ID: {session_id}")
    print("Type 'exit' to quit.\n")

    async with mcp_server:
        while True:
            user_input = input("User: ").strip()
            if user_input.lower() in {"exit", "quit"}:
                break

            result = await Runner.run(
                orchestrator_agent,
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
                    orchestrator_agent,
                    state,
                    session=session,
                )

            print(f"\nAssistant: {result.final_output}\n")
            #debug_run_result(result)


if __name__ == "__main__":
    asyncio.run(main())