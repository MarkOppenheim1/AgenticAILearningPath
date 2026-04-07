from dotenv import load_dotenv
load_dotenv()

from langgraph.types import Command
from app.graph import graph


def main():
    thread_id = "demo-thread-1"
    question = input("User: ")

    config = {"configurable": {"thread_id": thread_id}}

    result = graph.invoke(
        {"user_query": question},
        config=config
    )

    print("\n--- CLASSIFICATION ---")
    print("request_type:", result.get("request_type"))
    print("reason:", result.get("classification_reason"))

    print("\n--- ANSWER OBJECT ---")
    print("confidence:", result.get("answer_confidence"))
    print("sources:", result.get("answer_sources"))
    print("recommended_action:", result.get("recommended_action"))

    if "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        print("\n=== HUMAN APPROVAL REQUIRED ===")
        print("Question:", payload["question"])
        print("Type:", payload.get("request_type"))
        print("Reason:", payload.get("classification_reason"))
        print("Confidence:", payload.get("answer_confidence"))
        print("Sources:", payload.get("answer_sources"))
        print("Recommended action:", payload.get("recommended_action"))
        print("Draft:\n", payload["draft_response"])

        decision = input("\nType approved or rejected: ").strip().lower()

        resumed = graph.invoke(
            Command(resume=decision),
            config=config
        )

        print("\n--- TOOL ---")
        print("tool_name:", resumed.get("tool_name"))
        print("tool_result:", resumed.get("tool_result"))

        print("\nAssistant:", resumed.get("final_response", "No final response found"))
    else:
        print("\nAssistant:", result["final_response"])


if __name__ == "__main__":
    main()