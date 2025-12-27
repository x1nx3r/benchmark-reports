#!/usr/bin/env python3
"""Analyze LLM Judge Results for consistency across tasks."""

import json
import os
from collections import defaultdict

def main():
    results_dir = "/mnt/libraries/benchresults/llm_judge_results"
    files = [f for f in os.listdir(results_dir) if f.endswith(".json")]
    files.sort()

    all_results = {}
    parse_errors = []

    for f in files:
        try:
            with open(os.path.join(results_dir, f), "r") as fp:
                data = json.load(fp)
                all_results[f] = data
        except json.JSONDecodeError as e:
            parse_errors.append((f, str(e)))

    if parse_errors:
        print("=== JSON Parse Errors ===")
        for f, err in parse_errors:
            print(f"  {f}: {err}")
        print()

    print(f"Successfully loaded {len(all_results)} / {len(files)} files")
    print()

    # Analyze each file
    print("=" * 100)
    print(f"{'Task':<55} | {'Total':>6} | {'Correct':>8} | {'Acc %':>7} | {'Avg Score':>10}")
    print("=" * 100)

    summary_data = []
    for f in sorted(all_results.keys()):
        data = all_results[f]
        total = len(data)
        correct = sum(1 for item in data if item.get("is_correct", False))
        acc = (correct / total * 100) if total > 0 else 0
        
        scores = [item.get("reasoning_score", 0) for item in data if item.get("reasoning_score") is not None]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        task_name = f.replace("_res.json", "").replace(".json", "").replace("_", " ")[:50]
        summary_data.append((task_name, total, correct, acc, avg_score))
        print(f"{task_name:<55} | {total:>6} | {correct:>8} | {acc:>6.1f}% | {avg_score:>10.2f}")

    print("=" * 100)

    # Overall stats
    total_all = sum(s[1] for s in summary_data)
    correct_all = sum(s[2] for s in summary_data)
    overall_acc = (correct_all / total_all * 100) if total_all > 0 else 0
    print(f"{'OVERALL':<55} | {total_all:>6} | {correct_all:>8} | {overall_acc:>6.1f}% |")
    print()

    # Error type distribution
    print("=== Error Type Distribution Across All Tasks ===")
    error_counts = defaultdict(int)
    for data in all_results.values():
        for item in data:
            error_type = item.get("error_type", "unknown")
            error_counts[error_type] += 1

    for error_type, count in sorted(error_counts.items(), key=lambda x: -x[1]):
        pct = count / total_all * 100
        print(f"  {error_type:<25}: {count:>5} ({pct:>5.1f}%)")

    # Score distribution
    print()
    print("=== Reasoning Score Distribution ===")
    score_dist = defaultdict(int)
    for data in all_results.values():
        for item in data:
            score = item.get("reasoning_score", 0)
            score_dist[score] += 1

    for score in sorted(score_dist.keys()):
        count = score_dist[score]
        pct = count / total_all * 100
        print(f"  Score {score}: {count:>5} ({pct:>5.1f}%)")

    # Per-task error breakdown
    print()
    print("=== Per-Task Error Type Breakdown ===")
    for f in sorted(all_results.keys()):
        data = all_results[f]
        task_name = f.replace("_res.json", "").replace(".json", "").replace("_", " ")[:40]
        task_errors = defaultdict(int)
        for item in data:
            error_type = item.get("error_type", "unknown")
            task_errors[error_type] += 1
        
        error_summary = ", ".join([f"{k}: {v}" for k, v in sorted(task_errors.items(), key=lambda x: -x[1])])
        print(f"  {task_name:<42} | {error_summary}")

if __name__ == "__main__":
    main()
