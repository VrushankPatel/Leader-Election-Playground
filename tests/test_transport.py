import asyncio
import pytest

from lep.network.controller import NetworkController
from lep.transport.transport import SimulatedTransport


@pytest.mark.asyncio
async def test_simulated_transport_send():
    network = NetworkController()
    transport = SimulatedTransport(1, [1, 2, 3], network)
    # Send to self? But broadcast excludes self
    response = await transport.send_message(2, {"type": "test"})
    assert response == "response"


@pytest.mark.asyncio
async def test_simulated_transport_broadcast():
    network = NetworkController()
    transport = SimulatedTransport(1, [1, 2, 3], network)
    results = await transport.broadcast({"type": "test"})
    assert 2 in results
    assert 3 in results
    assert 1 not in results  # Not to self


@pytest.mark.asyncio
async def test_simulated_transport_partition():
    network = NetworkController()
    transport = SimulatedTransport(1, [1, 2], network)
    network.set_partition(1, 2, True)
    response = await transport.send_message(2, {"type": "test"})
    assert response is None


def test_simulated_transport_register_handler():
    network = NetworkController()
    transport = SimulatedTransport(1, [1, 2], network)
    def dummy_handler(msg):
        return "handled"
    transport.register_handler("test", dummy_handler)
    assert "test" in transport.handlers