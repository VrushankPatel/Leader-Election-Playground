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
    def __init__(self, scenario_file: str, output_dir: str = "results"):
        self.scenario_file = scenario_file
        self.output_dir = output_dir
        self.scenario = self.load_scenario()
        self.network_controller = NetworkController(
            seed=self.scenario.get("seed", 42)
        )
        self.nodes = {}
        self.start_time = None
        self.logs = []

    def load_scenario(self):
        with open(self.scenario_file, "r") as f:
            return yaml.safe_load(f)

    async def run_scenario(self):
        logger.info(f"Running scenario: {self.scenario['name']}")
        self.start_time = time.time()
        cluster_size = self.scenario["cluster_size"]
        algorithm = self.scenario["algorithm"]
        transport_type = self.scenario.get("transport", "simulated")
        all_nodes = list(range(1, cluster_size + 1))

        # Start nodes
        if transport_type == "simulated":
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

        # Apply network conditions only for simulated transport
        if transport_type == "simulated":
            self.apply_network_conditions()

        # Run for duration
        duration = self.scenario.get("duration", 30)
        await asyncio.sleep(duration)

        # Collect metrics
        metrics = self.collect_metrics()
        self.save_results(metrics)

    def apply_network_conditions(self):
        conditions = self.scenario.get("network_conditions", {})
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
