def calculate_metrics(cut_result_registry, actual_results):
    metrics = {
        "total": 0,
        "correct": 0,
        "accuracy": 0.0,
        "true_positives": 0,
        "true_negatives": 0,
        "false_positives": 0,
        "false_negatives": 0,
    }

    for cut_entry in cut_result_registry:
        test_filename = cut_entry.test_filename
        expected = cut_entry.should_pass
        actual = actual_results.get(test_filename, False)

        metrics["total"] += 1

        if expected == actual:
            metrics["correct"] += 1

        if expected and actual:
            metrics["true_positives"] += 1
        elif not expected and not actual:
            metrics["true_negatives"] += 1
        elif not expected and actual:
            metrics["false_positives"] += 1
        elif expected and not actual:
            metrics["false_negatives"] += 1

    if metrics["total"] > 0:
        metrics["accuracy"] = metrics["correct"] / metrics["total"]

    return metrics


def print_metrics(metrics):
    print("\n" + "=" * 50)
    print("DXBENCH METRICS")
    print("=" * 50)
    print(f"Total test files:    {metrics['total']}")
    print(f"Correct predictions: {metrics['correct']}")
    print(f"Accuracy:           {metrics['accuracy']:.2%}")
    print()
    print("Confusion Matrix:")
    print(f"  True Positives:   {metrics['true_positives']} (should pass & did pass)")
    print(f"  True Negatives:   {metrics['true_negatives']} (should fail & did fail)")
    print(f"  False Positives:  {metrics['false_positives']} (should fail but passed)")
    print(f"  False Negatives:  {metrics['false_negatives']} (should pass but failed)")
    print("=" * 50)
