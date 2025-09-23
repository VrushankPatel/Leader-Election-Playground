import pytest

from lep.network.controller import NetworkController
from lep.transport.transport import MessageDispatcher, SimulatedTransport


@pytest.mark.asyncio
async def test_simulated_transport_send():
    network = NetworkController()
    dispatcher = MessageDispatcher()
    transport1 = SimulatedTransport(1, [1, 2, 3], network, dispatcher)
    transport2 = SimulatedTransport(2, [1, 2, 3], network, dispatcher)
    dispatcher.register_transport(1, transport1)
    dispatcher.register_transport(2, transport2)

    async def handler(msg):
        return "response"

    transport2.register_handler("test", handler)
    response = await transport1.send_message(2, {"type": "test"})
    assert response == "response"


@pytest.mark.asyncio
async def test_simulated_transport_broadcast():
    network = NetworkController()
    dispatcher = MessageDispatcher()
    transport1 = SimulatedTransport(1, [1, 2, 3], network, dispatcher)
    transport2 = SimulatedTransport(2, [1, 2, 3], network, dispatcher)
    transport3 = SimulatedTransport(3, [1, 2, 3], network, dispatcher)
    dispatcher.register_transport(1, transport1)
    dispatcher.register_transport(2, transport2)
    dispatcher.register_transport(3, transport3)

    async def handler(msg):
        return f"response_from_{msg.get('from', 'unknown')}"

    transport2.register_handler("test", handler)
    transport3.register_handler("test", handler)
    results = await transport1.broadcast({"type": "test"})
    assert 2 in results
    assert 3 in results
    assert 1 not in results  # Not to self
    assert results[2] == "response_from_1"
    assert results[3] == "response_from_1"


@pytest.mark.asyncio
async def test_simulated_transport_partition():
    network = NetworkController()
    dispatcher = MessageDispatcher()
    transport1 = SimulatedTransport(1, [1, 2], network, dispatcher)
    transport2 = SimulatedTransport(2, [1, 2], network, dispatcher)
    dispatcher.register_transport(1, transport1)
    dispatcher.register_transport(2, transport2)
    network.set_partition(1, 2, True)

    async def handler(msg):
        return "response"

    transport2.register_handler("test", handler)
    response = await transport1.send_message(2, {"type": "test"})
    assert response is None


def test_simulated_transport_register_handler():
    network = NetworkController()
    dispatcher = MessageDispatcher()
    transport = SimulatedTransport(1, [1, 2], network, dispatcher)

    def dummy_handler(msg):
        return "handled"

    transport.register_handler("test", dummy_handler)
    assert "test" in transport.handlers
