import asyncio
import pytest

from lep.algorithms.zab import ZabAlgorithm
from lep.network.controller import NetworkController
from lep.transport.transport import SimulatedTransport


@pytest.mark.asyncio
async def test_zab_election():
    all_nodes = [1, 2, 3]
    network = NetworkController()
    transports = {}
    algorithms = {}

    for node_id in all_nodes:
        transports[node_id] = SimulatedTransport(node_id, all_nodes, network)
        algorithms[node_id] = ZabAlgorithm(node_id, all_nodes, transports[node_id])

    # Start all algorithms
    for algo in algorithms.values():
        await algo.start()

    # Wait for election to complete
    await asyncio.sleep(2.0)

    # Check that exactly one leader is elected
    leaders = [node for node, algo in algorithms.items() if algo.state.value == "leading"]
    assert len(leaders) == 1

    leader_id = leaders[0]
    # Check that all nodes recognize the leader
    for algo in algorithms.values():
        assert algo.leader_id == leader_id


@pytest.mark.asyncio
async def test_zab_leader_failure():
    all_nodes = [1, 2, 3]
    network = NetworkController()
    transports = {}
    algorithms = {}

    for node_id in all_nodes:
        transports[node_id] = SimulatedTransport(node_id, all_nodes, network)
        algorithms[node_id] = ZabAlgorithm(node_id, all_nodes, transports[node_id])

    # Start all
    for algo in algorithms.values():
        await algo.start()

    await asyncio.sleep(2.0)

    # Find initial leader
    initial_leader = next(node for node, algo in algorithms.items() if algo.state.value == "leading")

    # Simulate leader failure by partitioning it
    for n in all_nodes:
        if n != initial_leader:
            network.set_partition(initial_leader, n, True)

    # Wait for new election
    await asyncio.sleep(4.0)

    # Check new leader elected among remaining
    remaining_nodes = [n for n in all_nodes if n != initial_leader]
    leaders = [node for node in remaining_nodes if algorithms[node].state.value == "leading"]
    assert len(leaders) == 1

    new_leader = leaders[0]
    for node in remaining_nodes:
        if node != new_leader:
            assert algorithms[node].leader_id == new_leader