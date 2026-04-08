# evals/run_evals.py
from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

from langgraph.types import Command

from app.graph import graph
from evals.test_cases import TEST_CASES


def normalize_sources(sources: list[str]) -> set[str]:
    return {s.strip().lower() for s in sources if s and isinstance(s, str)}


def score_case(case: dict, result: dict) -> dict:
    expected_type = case["expected_request_type"]
    expected_action = case["expected_action"]
    expected_sources = normalize_sources(case.get("expected_sources", []))
    expected_tool_name = case.get("expected_tool_name")

    actual_type = result.get("request_type")
    actual_action = result.get("recommended_action")
    actual_sources = normalize_sources(result.get("answer_sources", []))
    actual_tool_name = result.get("tool_name")

    request_type_pass = actual_type == expected_type
    action_pass = actual_action == expected_action
    source_pass = (
        True if not expected_sources else len(expected_sources.intersection(actual_sources)) > 0
    )
    tool_pass = actual_tool_name == expected_tool_name

    passed = request_type_pass and action_pass and source_pass and tool_pass

    return {
        "name": case["name"],
        "input": case["input"],
        "passed": passed,
        "request_type_pass": request_type_pass,
        "action_pass": action_pass,
        "source_pass": source_pass,
        "tool_pass": tool_pass,
        "expected_request_type": expected_type,
        "actual_request_type": actual_type,
        "expected_action": expected_action,
        "actual_action": actual_action,
        "expected_sources": sorted(expected_sources),
        "actual_sources": sorted(actual_sources),
        "expected_tool_name": expected_tool_name,
        "actual_tool_name": actual_tool_name,
        "classification_reason": result.get("classification_reason"),
        "answer_confidence": result.get("answer_confidence"),
        "draft_response": result.get("draft_response"),
        "tool_result": result.get("tool_result"),
        "final_response": result.get("final_response"),
    }


def run_case(case: dict, idx: int) -> dict:
    config = {"configurable": {"thread_id": f"eval-case-{idx}"}}

    initial = graph.invoke(
        {"user_query": case["input"]},
        config=config,
    )

    if "__interrupt__" in initial:
        result = graph.invoke(
            Command(resume="approved"),
            config=config,
        )
    else:
        result = initial

    return score_case(case, result)


def print_failures(results: list[dict]) -> None:
    print("\n=== FAILURES ONLY ===")
    for r in results:
        if r["passed"]:
            continue

        print(f"- {r['name']}")
        print(f"  input: {r['input']}")
        print(
            f"  request_type: expected={r['expected_request_type']} actual={r['actual_request_type']} "
            f"({'OK' if r['request_type_pass'] else 'BAD'})"
        )
        print(
            f"  action: expected={r['expected_action']} actual={r['actual_action']} "
            f"({'OK' if r['action_pass'] else 'BAD'})"
        )
        print(
            f"  sources: expected={r['expected_sources']} actual={r['actual_sources']} "
            f"({'OK' if r['source_pass'] else 'BAD'})"
        )
        print(
            f"  tool: expected={r['expected_tool_name']} actual={r['actual_tool_name']} "
            f"({'OK' if r['tool_pass'] else 'BAD'})"
        )
        print(f"  confidence: {r['answer_confidence']}")
        print(f"  reason: {r['classification_reason']}")
        print(f"  answer: {r['draft_response']}")
        print(f"  tool_result: {r['tool_result']}")
        print()


def main():
    results = []

    for idx, case in enumerate(TEST_CASES, start=1):
        scored = run_case(case, idx)
        results.append(scored)

    total = len(results)
    passed = sum(1 for r in results if r["passed"])

    print("\n=== EVAL RESULTS ===")
    print(f"Passed {passed}/{total}")
    print()

    print_failures(results)

    print("=== SUMMARY ===")
    print(f"Total: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")


if __name__ == "__main__":
    main()