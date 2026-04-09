import asyncio
import uuid
from dotenv import load_dotenv

from agents import Agent, Runner, SQLiteSession

load_dotenv()

session_id = uuid.uuid4().hex
session = SQLiteSession(session_id, "research.db")


planner = Agent(
    name="Planner",
    model="gpt-5.4-nano",
    instructions=(
        "You are a research planner.\n"
        "Break the user's request into clear steps.\n"
        "Then hand off to the Researcher."
    ),
)

researcher = Agent(
    name="Researcher",
    model="gpt-5.4-nano",
    instructions=(
        "You gather relevant information.\n"
        "Be factual and structured.\n"
        "Then hand off to the Writer."
    ),
)

writer = Agent(
    name="Writer",
    model="gpt-5.4-nano",
    instructions=(
        "You synthesize research into a clear, structured report.\n"
        "Be concise and professional."
        "Then hand off to the Critic."
    ),
)

critic = Agent(
    name="Critic",
    model="gpt-5.4-nano",
    instructions=(
        "Review the report.\n"
        "Identify gaps, missing points, or weak reasoning.\n"
        "Improve the output."
    ),
)

# Hand-offs
planner.handoffs = [researcher]
researcher.handoffs = [writer]
writer.handoffs = [critic]

# Entry point
entry_agent = planner

def debug_trace(result):
    print("\n--- TRACE ---")

    for i, item in enumerate(result.new_items, start=1):
        agent = getattr(item, "agent", None)
        agent_name = agent.name if agent else "Unknown"

        print(f"{i}. {type(item).__name__} | Agent: {agent_name}")


async def main():
    print("Research Agent")
    print(f"Session: {session_id}\n")

    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        result = await Runner.run(
            entry_agent,
            user_input,
            session=session,
        )

        debug_trace(result)
        print("FINAL:", result.last_agent.name)
        
        print("\n--- RESULT ---")
        print(result.final_output)
        print()

        


if __name__ == "__main__":
    asyncio.run(main())