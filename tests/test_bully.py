import asyncio
import pytest

from lep.algorithms.bully import BullyAlgorithm
from lep.network.controller import NetworkController
from lep.transport.transport import SimulatedTransport, MessageDispatcher

@pytest.mark.asyncio
async def test_bully_election():
    all_nodes = [1, 2, 3]
    network = NetworkController()
    dispatcher = MessageDispatcher()
    transport = SimulatedTransport(1, all_nodes, network, dispatcher)
    dispatcher.register_transport(1, transport)
    algo = BullyAlgorithm(1, all_nodes, transport)
    await algo.start()
    await asyncio.sleep(10)  # Wait for election
    status = algo.get_status()
    # In bully, highest ID should be leader
    assert status["leader_id"] == 3
    if algo.node_id == 3:
        assert status["role"] == "leader"
    else:
        assert status["role"] == "follower"