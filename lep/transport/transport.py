import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Callable, Any

# Assuming protobuf generated classes
# from .proto.messages_pb2 import *
# from .proto.messages_pb2_grpc import *

logger = logging.getLogger(__name__)

class MessageDispatcher:
    def __init__(self):
        self.transports: Dict[int, Any] = {}

    def register_transport(self, node_id: int, transport: Any):
        self.transports[node_id] = transport

    async def deliver_message(self, from_node: int, to_node: int, message):
        if to_node in self.transports:
            return await self.transports[to_node].receive_message(from_node, message)

class Transport(ABC):
    @abstractmethod
    async def send_message(self, to_node: int, message) -> Optional[object]:
        pass

    @abstractmethod
    async def broadcast(self, message) -> Dict[int, Optional[object]]:
        pass

    @abstractmethod
    def register_handler(self, message_type: str, handler):
        pass

class SimulatedTransport(Transport):
    def __init__(self, node_id: int, all_nodes: List[int], network_controller, message_dispatcher: MessageDispatcher):
        self.node_id = node_id
        self.all_nodes = all_nodes
        self.network_controller = network_controller
        self.message_dispatcher = message_dispatcher
        self.handlers: Dict[str, Callable] = {}

    async def send_message(self, to_node: int, message) -> Optional[object]:
        if self.network_controller.is_partitioned(self.node_id, to_node):
            return None
        delay = self.network_controller.get_delay(self.node_id, to_node)
        if delay > 0:
            await asyncio.sleep(delay / 1000.0)  # delay in ms
        if self.network_controller.should_drop(self.node_id, to_node):
            return None
        # Deliver the message to the target node's transport
        response = await self.message_dispatcher.deliver_message(self.node_id, to_node, message)
        return response

    async def broadcast(self, message) -> Dict[int, Optional[object]]:
        results = {}
        for node in self.all_nodes:
            if node != self.node_id:
                results[node] = await self.send_message(node, message)
        return results

    def register_handler(self, message_type: str, handler):
        self.handlers[message_type] = handler

    async def receive_message(self, from_node: int, message):
        message_type = message.get("type")
        if message_type in self.handlers:
            response = await self.handlers[message_type](message)
            return response
        return None

class GRPCTransport(Transport):
    def __init__(self, node_id: int, host: str, port: int):
        self.node_id = node_id
        self.host = host
        self.port = port
        # TODO: Implement gRPC server and client

    async def send_message(self, to_node: int, message) -> Optional[object]:
        # TODO: Implement gRPC call
        return None

    async def broadcast(self, message) -> Dict[int, Optional[object]]:
        # TODO: Broadcast via gRPC
        return {}

    def register_handler(self, message_type: str, handler):
        # TODO: Register gRPC handlers
        pass