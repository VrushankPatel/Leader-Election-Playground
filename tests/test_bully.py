import asyncio
import pytest
from unittest.mock import Mock

from lep.algorithms.bully import BullyAlgorithm
from lep.network.controller import NetworkController
from lep.transport.transport import SimulatedTransport

@pytest.mark.asyncio
async def test_bully_election():
    all_nodes = [1, 2, 3]
    network = NetworkController()
    transport = SimulatedTransport(1, all_nodes, network)
    algo = BullyAlgorithm(1, all_nodes, transport)
    await algo.start()
    await asyncio.sleep(0.1)
    # Check if node 3 becomes leader (highest ID)
    assert algo.get_status()["role"] == "follower"  # Assuming not leader yet
    # In full test, check after election