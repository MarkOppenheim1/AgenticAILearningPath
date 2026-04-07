# evals/run_evals.py
from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

from app.graph import graph
from evals.test_cases import TEST_CASES


def normalize_sources(sources: list[str]) -> set[str]:
    return {s.strip().lower() for s in sources if s and isinstance(s, str)}


def score_case(case: dict, result: dict) -> dict:
    expected_type = case["expected_request_type"]
    expected_action = case["expected_action"]
    expected_sources = normalize_sources(case.get("expected_sources", []))

    actual_type = result.get("request_type")
    actual_action = result.get("recommended_action")
    actual_sources = normalize_sources(result.get("answer_sources", []))

    request_type_pass = actual_type == expected_type
    action_pass = actual_action == expected_action
    source_pass = (
        True if not expected_sources else len(expected_sources.intersection(actual_sources)) > 0
    )

    passed = request_type_pass and action_pass and source_pass

    return {
        "name": case["name"],
        "input": case["input"],
        "passed": passed,
        "request_type_pass": request_type_pass,
        "action_pass": action_pass,
        "source_pass": source_pass,
        "expected_request_type": expected_type,
        "actual_request_type": actual_type,
        "expected_action": expected_action,
        "actual_action": actual_action,
        "expected_sources": sorted(expected_sources),
        "actual_sources": sorted(actual_sources),
        "classification_reason": result.get("classification_reason"),
        "answer_confidence": result.get("answer_confidence"),
        "draft_response": result.get("draft_response"),
    }


def run_case(case: dict, idx: int) -> dict:
    config = {"configurable": {"thread_id": f"eval-case-{idx}"}}
    result = graph.invoke(
        {"user_query": case["input"]},
        config=config,
    )
    return score_case(case, result)

def print_failures(results: list[dict]) -> None:
    print("\n=== FAILURES ONLY ===")
    for r in results:
        if r["passed"]:
            continue
        print(f"- {r['name']}")
        print(f"  input: {r['input']}")
        print(f"  expected type/action: {r['expected_request_type']} / {r['expected_action']}")
        print(f"  actual type/action: {r['actual_request_type']} / {r['actual_action']}")
        print(f"  expected sources: {r['expected_sources']}")
        print(f"  actual sources: {r['actual_sources']}")
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

    """ for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"[{status}] {r['name']}")
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
        print(f"  confidence: {r['answer_confidence']}")
        print(f"  reason: {r['classification_reason']}")
        print(f"  answer: {r['draft_response']}")
        print() """
    
    print_failures(results)

    print("=== SUMMARY ===")
    print(f"Total: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")


if __name__ == "__main__":
    main()