import asyncio
import json
import os
import tempfile
import pytest
import yaml

from lep.orchestrator.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_orchestrator_load_scenario():
    scenario_data = {
        "name": "test_scenario",
        "algorithm": "bully",
        "cluster_size": 3,
        "duration": 1,
        "seed": 42
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(scenario_data, f)
        scenario_file = f.name

    try:
        orch = Orchestrator(scenario_file)
        assert orch.scenario == scenario_data
    finally:
        os.unlink(scenario_file)


@pytest.mark.asyncio
async def test_orchestrator_run_scenario():
    scenario_data = {
        "name": "test_run",
        "algorithm": "bully",
        "cluster_size": 3,
        "duration": 0.5,
        "seed": 42
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(scenario_data, f)
        scenario_file = f.name

    with tempfile.TemporaryDirectory() as output_dir:
        try:
            orch = Orchestrator(scenario_file, output_dir)
            await orch.run_scenario()

            # Check results saved
            results_file = os.path.join(output_dir, "results.json")
            assert os.path.exists(results_file)
            with open(results_file, 'r') as f:
                metrics = json.load(f)
            assert metrics["scenario"] == "test_run"
            assert len(metrics["nodes"]) == 3
        finally:
            os.unlink(scenario_file)


def test_orchestrator_collect_metrics():
    scenario_data = {
        "name": "test_metrics",
        "algorithm": "bully",
        "cluster_size": 3
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(scenario_data, f)
        scenario_file = f.name

    try:
        orch = Orchestrator(scenario_file)
        # Mock nodes
        class MockAlgo:
            def get_status(self):
                return {"role": "follower", "leader_id": 3}
        orch.nodes = {1: MockAlgo(), 2: MockAlgo(), 3: MockAlgo()}
        orch.nodes[3].get_status = lambda: {"role": "leader", "leader_id": 3}
        metrics = orch.collect_metrics()
        assert metrics["leaders"] == [3]
        assert not metrics["safety_violations"]
    finally:
        os.unlink(scenario_file)