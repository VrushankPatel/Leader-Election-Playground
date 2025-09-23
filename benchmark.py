#!/usr/bin/env python3
import asyncio
import json
import os
import statistics
from typing import Dict, List

from lep.orchestrator.orchestrator import Orchestrator


async def run_benchmark(
    scenarios: List[str], runs: int = 5, output_dir: str = "benchmarks"
):
    os.makedirs(output_dir, exist_ok=True)
    results = {}

    for scenario_file in scenarios:
        scenario_name = os.path.basename(scenario_file).replace(".yaml", "")
        results[scenario_name] = []

        for run in range(runs):
            print(f"Running {scenario_name} run {run + 1}/{runs}")
            run_output = f"{output_dir}/{scenario_name}_run_{run}"
            orch = Orchestrator(scenario_file, run_output, seed=42 + run)
            await orch.run_scenario()
            with open(f"{run_output}/results.json", "r") as f:
                result = json.load(f)
            results[scenario_name].append(result)

    # Aggregate results
    aggregated = aggregate_results(results)
    with open(f"{output_dir}/aggregated_results.json", "w") as f:
        json.dump(aggregated, f, indent=2)

    print(f"Benchmarks completed. Results in {output_dir}")


def aggregate_results(results: Dict) -> Dict:
    aggregated = {}
    for scenario, runs in results.items():
        aggregated[scenario] = {
            "election_latencies": [r.get("election_latency", 0) for r in runs],
            "leader_uptimes": [r.get("leader_uptime", 0) for r in runs],
            "safety_violations": sum(
                1 for r in runs if r.get("safety_violations", False)
            ),
            "message_counts": [r.get("message_count", 0) for r in runs],
        }
        # Compute stats
        keys_to_process = [
            key
            for key in aggregated[scenario]
            if isinstance(aggregated[scenario][key], list)
        ]
        for key in keys_to_process:
            values = aggregated[scenario][key]
            if values:
                aggregated[scenario][f"{key}_mean"] = statistics.mean(values)
                aggregated[scenario][f"{key}_median"] = statistics.median(values)
                aggregated[scenario][f"{key}_95p"] = (
                    statistics.quantiles(values, n=20)[18]
                    if len(values) >= 20
                    else max(values)
                )
    return aggregated


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run leader election benchmarks")
    parser.add_argument("scenarios", nargs="+", help="Scenario YAML files")
    parser.add_argument(
        "--runs", type=int, default=5, help="Number of runs per scenario"
    )
    parser.add_argument("--output-dir", default="benchmarks", help="Output directory")
    args = parser.parse_args()
    asyncio.run(
        run_benchmark(args.scenarios, runs=args.runs, output_dir=args.output_dir)
    )
