#!/usr/bin/env python3
import json
import matplotlib.pyplot as plt
import os

def analyze_results(results_file: str, output_dir: str = "analysis"):
    os.makedirs(output_dir, exist_ok=True)

    with open(results_file, 'r') as f:
        results = json.load(f)

    # Generate plots
    scenarios = list(results.keys())
    means = [results[s].get("election_latencies_mean", 0) for s in scenarios]

    plt.bar(scenarios, means)
    plt.title("Mean Election Latency by Scenario")
    plt.ylabel("Latency (s)")
    plt.savefig(f"{output_dir}/election_latency.png")
    plt.close()

    print(f"Analysis plots saved to {output_dir}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python analyze.py results.json")
        sys.exit(1)
    analyze_results(sys.argv[1])