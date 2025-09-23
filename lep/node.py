import asyncio
import logging

from aiohttp import web

try:
    from prometheus_client import Counter, Gauge, generate_latest
except ImportError:
    generate_latest = None

from .algorithms.bully import BullyAlgorithm
from .algorithms.raft import RaftAlgorithm
from .algorithms.zab import ZabAlgorithm
from .network.controller import NetworkController
from .transport.transport import SimulatedTransport

logger = logging.getLogger(__name__)


class Node:
    def __init__(
        self,
        node_id: int,
        all_nodes: list,
        algorithm: str,
        port: int = 8080,
        message_dispatcher=None,
    ):
        self.node_id = node_id
        self.all_nodes = all_nodes
        self.algorithm = algorithm
        self.port = port + node_id
        self.network_controller = NetworkController()
        transport = SimulatedTransport(
            node_id, all_nodes, self.network_controller, message_dispatcher
        )
        if algorithm == "bully":
            self.algo = BullyAlgorithm(node_id, all_nodes, transport)
        elif algorithm == "raft":
            self.algo = RaftAlgorithm(node_id, all_nodes, transport)
        elif algorithm == "zab":
            self.algo = ZabAlgorithm(node_id, all_nodes, transport)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

        # Prometheus metrics
        if generate_latest:
            self.leader_gauge = Gauge(
                "leader_election_leader", "Current leader ID", ["node_id"]
            )
            self.term_gauge = Gauge("leader_election_term", "Current term", ["node_id"])
            self.election_counter = Counter(
                "leader_election_count",
                "Number of elections started",
                ["node_id"],
            )
            self.leader_gauge.labels(node_id=self.node_id).set(0)
            self.term_gauge.labels(node_id=self.node_id).set(0)

    async def start(self):
        await self.algo.start()
        app = web.Application()
        app.router.add_get("/status", self.status_handler)
        app.router.add_post("/control", self.control_handler)
        if generate_latest:
            app.router.add_get("/metrics", self.metrics_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", self.port)
        await site.start()
        logger.info(f"Node {self.node_id} listening on port {self.port}")
        # Update metrics periodically
        asyncio.create_task(self.update_metrics())
        # Keep running
        while True:
            await asyncio.sleep(1)

    async def status_handler(self, request):
        status = self.algo.get_status()
        return web.json_response(status)

    async def control_handler(self, request):
        data = await request.json()
        action = data.get("action")
        if action == "crash":
            # Simulate crash
            pass
        elif action == "restart":
            # Simulate restart
            pass
        return web.json_response({"status": "ok"})

    async def metrics_handler(self, request):
        if generate_latest:
            status = self.algo.get_status()
            self.leader_gauge.labels(node_id=self.node_id).set(
                status.get("leader_id", 0) or 0
            )
            self.term_gauge.labels(node_id=self.node_id).set(status.get("term", 0))
            return web.Response(
                text=generate_latest(),
                content_type="text/plain; charset=utf-8",
            )
        return web.Response(text="Metrics not available", status=503)

    async def stop(self):
        await self.algo.stop()

    async def restart(self):
        await self.algo.restart()

    async def update_metrics(self):
        while True:
            await asyncio.sleep(5)  # Update every 5 seconds
            # Could update counters here if needed


async def main():
    import sys

    node_id = int(sys.argv[1])
    all_nodes = [1, 2, 3]  # Example
    algorithm = sys.argv[2] if len(sys.argv) > 2 else "bully"
    node = Node(node_id, all_nodes, algorithm)
    await node.start()


if __name__ == "__main__":
    asyncio.run(main())
