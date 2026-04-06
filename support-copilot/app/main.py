from dotenv import load_dotenv
load_dotenv()

from langgraph.types import Command
from graph import graph

def main():
    thread_id = "demo-thread-1"

    question = input("User: ")

    config = {
        "configurable": {"thread_id": thread_id}
    }

    result = graph.invoke(
        {"user_query": question},
        config=config
    )

    if "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        print("\n=== HUMAN APPROVAL REQUIRED ===")
        print("Question:", payload["question"])
        print("Draft:\n", payload["draft_response"])

        decision = input("\nType approved or rejected: ").strip().lower()

        resumed = graph.invoke(
            Command(resume=decision),
            config=config
        )

        print("\nResumed state:", resumed)
        print("\nAssistant:", resumed.get("final_response", "No final_response found"))
    else:
        print("\nAssistant:", result["final_response"])

if __name__ == "__main__":
    main()