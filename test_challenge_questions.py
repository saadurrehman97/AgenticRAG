"""Test script for challenge questions."""

from src.cli import initialize_system
from typing import List, Dict


CHALLENGE_QUESTIONS = [
    {
        "id": 1,
        "category": "Multi-hop Query",
        "question": "Which projects or services mentioned in the documents depend on AuthService?",
        "expected_elements": ["Project", "Service", "depend"],
    },
    {
        "id": 2,
        "category": "Reasoning + Tool Use",
        "question": "Summarize all documents related to the authentication subsystem and calculate how many services depend on it.",
        "expected_elements": ["AuthService", "multiple", "services", "depend"],
    },
    {
        "id": 3,
        "category": "Error Handling",
        "question": "Find details about the module called NonExistentModule",
        "expected_elements": ["no", "non-existent", "not available"],
    },
    {
        "id": 4,
        "category": "Dependency Analysis",
        "question": "What services does PaymentRouter depend on?",
        "expected_elements": ["AuthService", "DatabaseService", "NotificationService"],
    },
    {
        "id": 5,
        "category": "Complex Multi-hop",
        "question": "Which project uses PaymentRouter and what authentication system does it use?",
        "expected_elements": ["ProjectAlpha", "AuthService", "CheckoutService"],
    },
]


def run_challenge_tests(verbose: bool = True) -> Dict[str, any]:
    """
    Run all challenge questions and report results.

    Args:
        verbose: Whether to print detailed output

    Returns:
        Dictionary with test results
    """
    print("=" * 80)
    print("🧪 CHALLENGE QUESTIONS TEST SUITE")
    print("=" * 80)
    print()

    # Initialize system
    print("Initializing system...")
    agent = initialize_system(
        data_dir="data",
        graph_dir="graph",
        rebuild_graph=False,
    )
    print()

    results = {
        "total": len(CHALLENGE_QUESTIONS),
        "passed": 0,
        "failed": 0,
        "details": [],
    }

    for challenge in CHALLENGE_QUESTIONS:
        print("─" * 80)
        print(f"Test #{challenge['id']}: {challenge['category']}")
        print("─" * 80)
        print(f"Question: {challenge['question']}")
        print()

        try:
            # Run query
            result = agent.run(challenge["question"])

            # Check if answer was generated
            if not result["answer"] or result["answer"] == "No answer generated":
                status = "❌ FAILED"
                results["failed"] += 1
                reason = "No answer generated"
            elif result.get("error"):
                status = "⚠️  PARTIAL"
                results["failed"] += 1
                reason = f"Error occurred: {result['error']}"
            else:
                # Check if expected elements are in the answer
                answer_lower = result["answer"].lower()
                found_elements = [
                    elem for elem in challenge["expected_elements"]
                    if elem.lower() in answer_lower
                ]

                if len(found_elements) >= len(challenge["expected_elements"]) * 0.5:
                    status = "✅ PASSED"
                    results["passed"] += 1
                    reason = f"Found {len(found_elements)}/{len(challenge['expected_elements'])} expected elements"
                else:
                    status = "❌ FAILED"
                    results["failed"] += 1
                    reason = f"Only found {len(found_elements)}/{len(challenge['expected_elements'])} expected elements"

            if verbose:
                print(f"Status: {status}")
                print(f"Reason: {reason}")
                print()
                print("Answer:")
                print(result["answer"])
                print()
                print("Execution Details:")
                print(f"  • Router Decision: {result['router_decision']}")
                print(f"  • Retrieved Chunks: {result['retrieved_chunks']}")
                print(f"  • Tools Used: {', '.join(result['tools_used']) if result['tools_used'] else 'None'}")
                print(f"  • Steps: {len(result['steps_executed'])}")
                print()

            results["details"].append({
                "id": challenge["id"],
                "category": challenge["category"],
                "question": challenge["question"],
                "status": status,
                "reason": reason,
                "answer": result["answer"],
                "execution": {
                    "router_decision": result["router_decision"],
                    "retrieved_chunks": result["retrieved_chunks"],
                    "tools_used": result["tools_used"],
                    "steps": result["steps_executed"],
                },
            })

        except Exception as e:
            status = "❌ ERROR"
            results["failed"] += 1
            reason = str(e)

            if verbose:
                print(f"Status: {status}")
                print(f"Error: {reason}")
                print()

            results["details"].append({
                "id": challenge["id"],
                "category": challenge["category"],
                "question": challenge["question"],
                "status": status,
                "reason": reason,
            })

        print()

    # Print summary
    print("=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {results['total']}")
    print(f"Passed: {results['passed']} ✅")
    print(f"Failed: {results['failed']} ❌")
    print(f"Success Rate: {(results['passed'] / results['total'] * 100):.1f}%")
    print("=" * 80)
    print()

    return results


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test challenge questions")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output for each test",
    )
    parser.add_argument(
        "--save-results",
        type=str,
        help="Save results to JSON file",
    )

    args = parser.parse_args()

    try:
        results = run_challenge_tests(verbose=args.verbose or True)

        if args.save_results:
            import json
            with open(args.save_results, "w") as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to {args.save_results}")

    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return 1

    return 0 if results["failed"] == 0 else 1


if __name__ == "__main__":
    exit(main())
