import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

try:
    import grpc

    from .proto import messages_pb2 as pb
    from .proto import messages_pb2_grpc as pb_grpc
except ImportError:
    grpc = None
    pb = None
    pb_grpc = None

logger = logging.getLogger(__name__)


class MessageDispatcher:
    def __init__(self, start_monotonic: float = 0.0):
        self.transports: Dict[int, Any] = {}
        self.logs: List[Dict] = []
        self.start_monotonic = start_monotonic

    def register_transport(self, node_id: int, transport: Any):
        self.transports[node_id] = transport

    async def deliver_message(self, from_node: int, to_node: int, message):
        # Log the message with relative monotonic timestamp
        log_entry = {
            "timestamp": time.monotonic() - self.start_monotonic,
            "from": from_node,
            "to": to_node,
            "message": message,
        }
        self.logs.append(log_entry)
        if to_node in self.transports:
            return await self.transports[to_node].receive_message(
                from_node, message
            )

    def save_logs(self, filename: str):
        with open(filename, "w") as f:
            json.dump(self.logs, f, indent=2)
        logger.info(f"Message logs saved to {filename}")


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
    def __init__(
        self,
        node_id: int,
        all_nodes: List[int],
        network_controller,
        message_dispatcher: MessageDispatcher,
    ):
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
        # Add 'from' if not present
        if "from" not in message:
            message["from"] = self.node_id
        # Deliver the message to the target node's transport
        response = await self.message_dispatcher.deliver_message(
            self.node_id, to_node, message
        )
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
    def __init__(
        self,
        node_id: int,
        host: str,
        port: int,
        all_nodes: List[int],
        node_ports: Dict[int, int],
    ):
        if pb is None or pb_grpc is None:
            raise ImportError(
                "gRPC protobuf modules not generated. Run protoc first."
            )
        self.node_id = node_id
        self.host = host
        self.port = port
        self.all_nodes = all_nodes
        self.node_ports = node_ports
        self.handlers: Dict[str, Callable] = {}
        self.server = None
        self.channel = None

    async def start_server(self):
        self.server = grpc.aio.server()
        pb_grpc.add_LeaderElectionServicer_to_server(
            LeaderElectionServicer(self.handlers), self.server
        )
        self.server.add_insecure_port(f"{self.host}:{self.port}")
        await self.server.start()
        logger.info(f"gRPC server started on {self.host}:{self.port}")

    async def stop_server(self):
        if self.server:
            await self.server.stop(0)

    async def send_message(self, to_node: int, message) -> Optional[object]:
        if to_node not in self.node_ports:
            return None
        port = self.node_ports[to_node]
        async with grpc.aio.insecure_channel(f"{self.host}:{port}") as channel:
            stub = pb_grpc.LeaderElectionStub(channel)
            # Convert message dict to protobuf
            pb_msg = self._dict_to_pb(message)
            if isinstance(pb_msg, pb.VoteRequest):
                response = await stub.RequestVote(pb_msg)
                return self._pb_to_dict(response)
            elif isinstance(pb_msg, pb.AppendEntriesRequest):
                response = await stub.AppendEntries(pb_msg)
                return self._pb_to_dict(response)
            elif isinstance(pb_msg, pb.Heartbeat):
                response = await stub.SendHeartbeat(pb_msg)
                return self._pb_to_dict(response)
            elif isinstance(pb_msg, pb.LeaderAnnounce):
                response = await stub.AnnounceLeader(pb_msg)
                return self._pb_to_dict(response)
            elif isinstance(pb_msg, pb.Coordinator):
                response = await stub.SendCoordinator(pb_msg)
                return self._pb_to_dict(response)
            elif isinstance(pb_msg, pb.Election):
                response = await stub.SendElection(pb_msg)
                return self._pb_to_dict(response)
        return None

    async def broadcast(self, message) -> Dict[int, Optional[object]]:
        results = {}
        for node in self.all_nodes:
            if node != self.node_id:
                results[node] = await self.send_message(node, message)
        return results

    def register_handler(self, message_type: str, handler):
        self.handlers[message_type] = handler

    def _dict_to_pb(self, msg_dict):
        msg_type = msg_dict.get("type")
        if msg_type == "request_vote":
            return pb.VoteRequest(
                term=msg_dict["term"],
                candidate_id=msg_dict["candidate_id"],
                last_log_index=msg_dict.get("last_log_index", 0),
                last_log_term=msg_dict.get("last_log_term", 0),
            )
        elif msg_type == "append_entries":
            return pb.AppendEntriesRequest(
                term=msg_dict["term"],
                leader_id=msg_dict["leader_id"],
                prev_log_index=msg_dict.get("prev_log_index", 0),
                prev_log_term=msg_dict.get("prev_log_term", 0),
                entries=msg_dict.get("entries", []),
                leader_commit=msg_dict.get("leader_commit", 0),
            )
        elif msg_type == "heartbeat":
            return pb.Heartbeat(
                term=msg_dict.get("term", 0), leader_id=msg_dict["leader_id"]
            )
        elif msg_type == "leader_announce":
            return pb.LeaderAnnounce(
                leader_id=msg_dict["leader_id"], term=msg_dict.get("term", 0)
            )
        elif msg_type == "coordinator":
            return pb.Coordinator(leader=msg_dict["leader"])
        elif msg_type == "election":
            return pb.Election()
        return None

    def _pb_to_dict(self, pb_msg):
        if isinstance(pb_msg, pb.VoteResponse):
            return {
                "type": "vote_response",
                "term": pb_msg.term,
                "vote_granted": pb_msg.vote_granted,
            }
        return {}


class LeaderElectionServicer(pb_grpc.LeaderElectionServicer):
    def __init__(self, handlers):
        self.handlers = handlers

    async def RequestVote(self, request, context):
        msg = {
            "type": "request_vote",
            "term": request.term,
            "candidate_id": request.candidate_id,
            "last_log_index": request.last_log_index,
            "last_log_term": request.last_log_term,
        }
        response = await self._handle(msg)
        return pb.VoteResponse(
            term=response.get("term", 0),
            vote_granted=response.get("vote_granted", False),
        )

    async def AppendEntries(self, request, context):
        msg = {
            "type": "append_entries",
            "term": request.term,
            "leader_id": request.leader_id,
            "prev_log_index": request.prev_log_index,
            "prev_log_term": request.prev_log_term,
            "entries": list(request.entries),
            "leader_commit": request.leader_commit,
        }
        response = await self._handle(msg)
        return pb.VoteResponse(
            term=response.get("term", 0),
            vote_granted=response.get("success", False),
        )

    async def SendHeartbeat(self, request, context):
        msg = {
            "type": "heartbeat",
            "term": request.term,
            "leader_id": request.leader_id,
        }
        response = await self._handle(msg)
        return pb.VoteResponse(term=response.get("term", 0), vote_granted=True)

    async def AnnounceLeader(self, request, context):
        msg = {
            "type": "leader_announce",
            "leader_id": request.leader_id,
            "term": request.term,
        }
        response = await self._handle(msg)
        return pb.VoteResponse(term=response.get("term", 0), vote_granted=True)

    async def SendCoordinator(self, request, context):
        msg = {
            "type": "coordinator",
            "leader": request.leader,
        }
        response = await self._handle(msg)
        return pb.VoteResponse(term=response.get("term", 0), vote_granted=True)

    async def SendElection(self, request, context):
        msg = {
            "type": "election",
        }
        response = await self._handle(msg)
        return pb.VoteResponse(term=response.get("term", 0), vote_granted=True)

    async def _handle(self, msg):
        msg_type = msg["type"]
        if msg_type in self.handlers:
            return await self.handlers[msg_type](msg)
        return {}
