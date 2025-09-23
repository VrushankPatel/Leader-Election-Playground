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
        "seed": 42,
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(scenario_data, f)
        scenario_file = f.name

    try:
        orch = Orchestrator(scenario_file)
        assert orch.scenario == scenario_data
    finally:
        os.unlink(scenario_file)


@pytest.mark.asyncio
async def test_orchestrator_run_scenario():
    import os

    os.environ["TESTING"] = "1"
    scenario_data = {
        "name": "test_run",
        "algorithm": "bully",
        "cluster_size": 3,
        "duration": 0.5,
        "seed": 42,
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(scenario_data, f)
        scenario_file = f.name

    with tempfile.TemporaryDirectory() as output_dir:
        try:
            orch = Orchestrator(scenario_file, output_dir)
            await orch.run_scenario()

            # Check results saved
            results_file = os.path.join(output_dir, "results.json")
            assert os.path.exists(results_file)
            with open(results_file, "r") as f:
                metrics = json.load(f)
            assert metrics["scenario"] == "test_run"
            assert len(metrics["nodes"]) == 3
        finally:
            os.unlink(scenario_file)


def test_orchestrator_collect_metrics():
    scenario_data = {
        "name": "test_metrics",
        "algorithm": "bully",
        "cluster_size": 3,
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(scenario_data, f)
        scenario_file = f.name

    try:
        orch = Orchestrator(scenario_file)

        # Mock nodes
        class MockAlgo:
            def __init__(self):
                self.algo = self

            def get_status(self):
                return {"role": "follower", "leader_id": 3}

        orch.nodes = {1: MockAlgo(), 2: MockAlgo(), 3: MockAlgo()}
        orch.nodes[3].algo.get_status = lambda: {"role": "leader", "leader_id": 3}
        metrics = orch.collect_metrics()
        assert metrics["leaders"] == [3]
        assert not metrics["safety_violations"]
    finally:
        os.unlink(scenario_file)


@pytest.mark.asyncio
async def test_orchestrator_replay_scenario():
    import os

    os.environ["TESTING"] = "1"
    scenario_data = {
        "name": "test_replay",
        "algorithm": "bully",
        "cluster_size": 3,
        "duration": 2.0,
        "seed": 42,
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(scenario_data, f)
        scenario_file = f.name

    with tempfile.TemporaryDirectory() as output_dir:
        try:
            # Run original scenario
            orch = Orchestrator(scenario_file, output_dir)
            await orch.run_scenario()

            # Check logs exist
            log_file = os.path.join(output_dir, "messages.log")
            assert os.path.exists(log_file)

            # Replay
            replay_output_dir = output_dir + "_replay"
            orch_replay = Orchestrator(scenario_file, replay_output_dir)
            await orch_replay.replay_scenario(log_file)

            # Check replay results
            replay_results_file = os.path.join(replay_output_dir, "results.json")
            assert os.path.exists(replay_results_file)
            with open(replay_results_file, "r") as f:
                replay_metrics = json.load(f)
            assert replay_metrics["scenario"] == "test_replay"
            assert len(replay_metrics["nodes"]) == 3
        finally:
            os.unlink(scenario_file)
