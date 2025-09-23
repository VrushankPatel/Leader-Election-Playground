import asyncio

import pytest

from lep.algorithms.bully import BullyAlgorithm
from lep.network.controller import NetworkController
from lep.transport.transport import MessageDispatcher, SimulatedTransport


@pytest.mark.asyncio
async def test_bully_election():
    all_nodes = [1, 2, 3]
    network = NetworkController()
    dispatcher = MessageDispatcher()
    transports = {}
    algorithms = {}

    for node_id in all_nodes:
        transports[node_id] = SimulatedTransport(
            node_id, all_nodes, network, dispatcher
        )
        dispatcher.register_transport(node_id, transports[node_id])
        algorithms[node_id] = BullyAlgorithm(node_id, all_nodes, transports[node_id])

    # Start all algorithms
    for algo in algorithms.values():
        await algo.start()

    await asyncio.sleep(10)  # Wait for election
    # In bully, highest ID should be leader
    for node_id, algo in algorithms.items():
        status = algo.get_status()
        assert status["leader_id"] == 3
        if node_id == 3:
            assert status["role"] == "leader"
        else:
            assert status["role"] == "follower"

    # Stop algorithms
    for algo in algorithms.values():
        await algo.stop()
