#!/usr/bin/env python3
import asyncio
import sys

from lep.orchestrator.orchestrator import Orchestrator

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_scenario.py <scenario_file> [output_dir]")
        sys.exit(1)
    scenario_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "results"
    orch = Orchestrator(scenario_file, output_dir)
    asyncio.run(orch.run_scenario())
