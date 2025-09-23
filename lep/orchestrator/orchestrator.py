import asyncio
import json
import logging
import time
from typing import Dict

import yaml

from ..algorithms.bully import BullyAlgorithm
from ..algorithms.raft import RaftAlgorithm
from ..algorithms.zab import ZabAlgorithm
from ..network.controller import NetworkController
from ..transport.transport import (
    GRPCTransport,
    MessageDispatcher,
    SimulatedTransport,
)

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, scenario_file: str, output_dir: str = "results", seed: int = None):
        self.scenario_file = scenario_file
        self.output_dir = output_dir
        self.scenario = self.load_scenario()
        if seed is not None:
            self.scenario["seed"] = seed
        self.network_controller = NetworkController(
            seed=self.scenario.get("seed", 42)
        )
        self.nodes = {}
        self.start_time = None
        self.start_monotonic = None

    def load_scenario(self):
        with open(self.scenario_file, "r") as f:
            return yaml.safe_load(f)

    async def run_scenario(self):
        logger.info(f"Running scenario: {self.scenario['name']}")
        self.start_time = time.time()
        self.start_monotonic = time.monotonic()
        cluster_size = self.scenario["cluster_size"]
        algorithm = self.scenario["algorithm"]
        transport_type = self.scenario.get("transport", "simulated")
        all_nodes = list(range(1, cluster_size + 1))

        # Start nodes
        if transport_type == "simulated":
            dispatcher = MessageDispatcher(start_monotonic=self.start_monotonic)
            for node_id in all_nodes:
                transport = SimulatedTransport(
                    node_id, all_nodes, self.network_controller, dispatcher
                )
                dispatcher.register_transport(node_id, transport)
                if algorithm == "bully":
                    algo = BullyAlgorithm(node_id, all_nodes, transport)
                elif algorithm == "raft":
                    algo = RaftAlgorithm(node_id, all_nodes, transport)
                elif algorithm == "zab":
                    algo = ZabAlgorithm(node_id, all_nodes, transport)
                else:
                    raise ValueError(f"Unknown algorithm: {algorithm}")
                self.nodes[node_id] = algo
                await algo.start()
        else:  # grpc
            for node_id in all_nodes:
                node_ports = {nid: 50050 + nid for nid in all_nodes}
                transport = GRPCTransport(
                    node_id,
                    "localhost",
                    node_ports[node_id],
                    all_nodes,
                    node_ports,
                )
                await transport.start_server()
                if algorithm == "bully":
                    algo = BullyAlgorithm(node_id, all_nodes, transport)
                elif algorithm == "raft":
                    algo = RaftAlgorithm(node_id, all_nodes, transport)
                elif algorithm == "zab":
                    algo = ZabAlgorithm(node_id, all_nodes, transport)
                else:
                    raise ValueError(f"Unknown algorithm: {algorithm}")
                self.nodes[node_id] = algo
                await algo.start()

        # Apply initial network conditions only for simulated transport
        if transport_type == "simulated":
            self.apply_network_conditions()

        # Run timed actions
        actions = self.scenario.get("actions", [])
        actions.sort(key=lambda x: x["time"])
        current_time = 0
        for action in actions:
            sleep_time = action["time"] - current_time
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            await self.apply_action(action)
            current_time = action["time"]

        # Run remaining duration
        duration = self.scenario.get("duration", 30)
        remaining = duration - current_time
        if remaining > 0:
            await asyncio.sleep(remaining)

        # Collect metrics
        metrics = self.collect_metrics()
        self.save_results(metrics)

        # Save message logs
        if transport_type == "simulated":
            dispatcher.save_logs(f"{self.output_dir}/messages.log")

    async def replay_scenario(self, log_file: str):
        logger.info(f"Replaying scenario from {log_file}")
        with open(log_file, "r") as f:
            logs = json.load(f)
        if not logs:
            logger.warning("No logs to replay")
            return
        min_ts = min(log["timestamp"] for log in logs)
        logs.sort(key=lambda x: x["timestamp"])

        # Load scenario for cluster setup
        cluster_size = self.scenario["cluster_size"]
        algorithm = self.scenario["algorithm"]
        all_nodes = list(range(1, cluster_size + 1))

        # Start nodes in simulated mode without network conditions
        dispatcher = MessageDispatcher()
        for node_id in all_nodes:
            transport = SimulatedTransport(
                node_id, all_nodes, self.network_controller, dispatcher
            )
            dispatcher.register_transport(node_id, transport)
            if algorithm == "bully":
                algo = BullyAlgorithm(node_id, all_nodes, transport)
            elif algorithm == "raft":
                algo = RaftAlgorithm(node_id, all_nodes, transport)
            elif algorithm == "zab":
                algo = ZabAlgorithm(node_id, all_nodes, transport)
            else:
                raise ValueError(f"Unknown algorithm: {algorithm}")
            self.nodes[node_id] = algo
            await algo.start()

        # Replay messages
        for log_entry in logs:
            delay = log_entry["timestamp"] - min_ts
            if delay > 0:
                await asyncio.sleep(delay)
            await dispatcher.deliver_message(
                log_entry["from"], log_entry["to"], log_entry["message"]
            )

        # Collect metrics
        metrics = self.collect_metrics()
        self.save_results(metrics)

    def apply_network_conditions(self):
        conditions = self.scenario.get("network_conditions", [])
        for cond in conditions:
            if cond["type"] == "partition":
                self.network_controller.set_partition(
                    cond["node1"], cond["node2"], True
                )
            elif cond["type"] == "delay":
                self.network_controller.set_delay(
                    cond["node1"], cond["node2"], cond["delay_ms"]
                )
            elif cond["type"] == "drop":
                self.network_controller.set_drop_rate(
                    cond["node1"], cond["node2"], cond["rate"]
                )

    async def apply_action(self, action):
        if action["type"] == "partition":
            self.network_controller.set_partition(
                action["node1"], action["node2"], True
            )
        elif action["type"] == "heal":
            self.network_controller.set_partition(
                action["node1"], action["node2"], False
            )
        elif action["type"] == "crash":
            await self.nodes[action["node"]].stop()
        elif action["type"] == "restart":
            await self.nodes[action["node"]].restart()
        else:
            logger.warning(f"Unknown action type: {action['type']}")

    def collect_metrics(self) -> Dict:
        duration = time.time() - self.start_time if self.start_time else 0
        metrics = {
            "scenario": self.scenario["name"],
            "algorithm": self.scenario["algorithm"],
            "cluster_size": self.scenario["cluster_size"],
            "duration": duration,
            "nodes": {},
        }
        leaders = []
        for node_id, algo in self.nodes.items():
            status = algo.get_status()
            metrics["nodes"][node_id] = status
            if status["role"] == "leader":
                leaders.append(node_id)
        metrics["leaders"] = leaders
        metrics["safety_violations"] = len(leaders) > 1
        return metrics

    def save_results(self, metrics: Dict):
        import os

        os.makedirs(self.output_dir, exist_ok=True)
        with open(f"{self.output_dir}/results.json", "w") as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Results saved to {self.output_dir}/results.json")


async def main():
    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python -m lep.orchestrator run-scenario "
            "--file=scenario.yaml"
        )
        return
    scenario_file = sys.argv[2].split("=")[1]
    orch = Orchestrator(scenario_file)
    await orch.run_scenario()


if __name__ == "__main__":
    asyncio.run(main())
