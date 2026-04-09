import asyncio
import re
import uuid
from datetime import datetime
from dotenv import load_dotenv

from agents import Agent, Runner, SQLiteSession
from agents.mcp import MCPServerStreamableHttp, MCPServerStreamableHttpParams

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

mcp_server = MCPServerStreamableHttp(
    params=MCPServerStreamableHttpParams(
        url="http://127.0.0.1:8000/mcp",
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
    instructions=(
        "You are the FAQ specialist. "
        "You MUST call retrieve_support_context before answering. "
        "Never answer from your own knowledge. "
        "Only answer from retrieved support documentation."
    ),
    mcp_servers=[mcp_server],
)

actions_agent = Agent(
    name="Actions Agent",
    model="gpt-5.4-nano",
    instructions=(
        "You are the actions specialist. "
        "Use retrieve_support_context when policy context is needed before acting. "
        "Use create_refund_ticket only for clear refund actions with enough details. "
        "Use create_escalation_case for manager, supervisor, complaint, or escalation requests."
    ),
    mcp_servers=[mcp_server],
)

faq_tool = faq_agent.as_tool(
    tool_name="answer_support_question",
    tool_description="Answer support FAQs and policy questions using support documentation.",
)

actions_tool = actions_agent.as_tool(
    tool_name="handle_support_action",
    tool_description="Handle action-oriented support requests like refunds, disputes, complaints, and escalations.",
)

orchestrator_agent = Agent(
    name="Support Orchestrator",
    model="gpt-5.4-nano",
    instructions=(
        "You are the support orchestrator. "
        "All FAQ and policy questions MUST go through answer_support_question. "
        "All action-oriented requests MUST go through handle_support_action. "
        "Do not answer policy questions yourself."
    ),
    tools=[faq_tool, actions_tool],
)

async def main() -> None:
    print("Support Copilot (OpenAI Agents SDK + MCP over HTTP)")
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

if __name__ == "__main__":
    asyncio.run(main())