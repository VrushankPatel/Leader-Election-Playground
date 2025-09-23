import asyncio
import json
import logging
from aiohttp import web

from .algorithms.bully import BullyAlgorithm
from .algorithms.raft import RaftAlgorithm
from .algorithms.zab import ZabAlgorithm
from .network.controller import NetworkController
from .transport.transport import SimulatedTransport

logger = logging.getLogger(__name__)

class Node:
    def __init__(self, node_id: int, all_nodes: list, algorithm: str, port: int = 8080):
        self.node_id = node_id
        self.all_nodes = all_nodes
        self.algorithm = algorithm
        self.port = port + node_id
        self.network_controller = NetworkController()
        transport = SimulatedTransport(node_id, all_nodes, self.network_controller)
        if algorithm == "bully":
            self.algo = BullyAlgorithm(node_id, all_nodes, transport)
        elif algorithm == "raft":
            self.algo = RaftAlgorithm(node_id, all_nodes, transport)
        elif algorithm == "zab":
            self.algo = ZabAlgorithm(node_id, all_nodes, transport)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

    async def start(self):
        await self.algo.start()
        app = web.Application()
        app.router.add_get('/status', self.status_handler)
        app.router.add_post('/control', self.control_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        logger.info(f"Node {self.node_id} listening on port {self.port}")
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

async def main():
    import sys
    node_id = int(sys.argv[1])
    all_nodes = [1, 2, 3]  # Example
    algorithm = sys.argv[2] if len(sys.argv) > 2 else "bully"
    node = Node(node_id, all_nodes, algorithm)
    await node.start()

if __name__ == "__main__":
    asyncio.run(main())