#!/usr/bin/env python3
import json
import os

import matplotlib.pyplot as plt


def analyze_results(results_file: str, output_dir: str = "analysis"):
    os.makedirs(output_dir, exist_ok=True)

    with open(results_file, "r") as f:
        results = json.load(f)

    # Generate plots
    scenarios = list(results.keys())

    # Election latency
    means = [results[s].get("election_latencies_mean", 0) for s in scenarios]
    plt.figure(figsize=(10, 6))
    plt.bar(scenarios, means)
    plt.title("Mean Election Latency by Scenario")
    plt.ylabel("Latency (s)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/election_latency.png")
    plt.close()

    # Leader uptime
    uptimes = [results[s].get("leader_uptimes_mean", 0) for s in scenarios]
    plt.figure(figsize=(10, 6))
    plt.bar(scenarios, uptimes)
    plt.title("Mean Leader Uptime Fraction by Scenario")
    plt.ylabel("Uptime Fraction")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/leader_uptime.png")
    plt.close()

    # Safety violations
    violations = [results[s].get("safety_violations", 0) for s in scenarios]
    plt.figure(figsize=(10, 6))
    plt.bar(scenarios, violations)
    plt.title("Safety Violations by Scenario")
    plt.ylabel("Number of Violations")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/safety_violations.png")
    plt.close()

    # Message counts
    messages = [results[s].get("message_counts_mean", 0) for s in scenarios]
    plt.figure(figsize=(10, 6))
    plt.bar(scenarios, messages)
    plt.title("Mean Message Count by Scenario")
    plt.ylabel("Message Count")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/message_count.png")
    plt.close()

    print(f"Analysis plots saved to {output_dir}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python analyze.py results.json")
        sys.exit(1)
    analyze_results(sys.argv[1])
