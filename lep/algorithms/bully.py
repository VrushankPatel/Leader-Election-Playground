import asyncio
import logging
from enum import Enum
from typing import List, Optional

from ..transport.transport import Transport

logger = logging.getLogger(__name__)


class BullyState(Enum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


class BullyAlgorithm:
    def __init__(
        self, node_id: int, all_nodes: List[int], transport: Transport
    ):
        self.node_id = node_id
        self.all_nodes = sorted(all_nodes)
        self.transport = transport
        self.state = BullyState.FOLLOWER
        self.leader_id: Optional[int] = None
        self.election_timeout = 5.0  # seconds
        self.heartbeat_interval = 1.0
        self.last_heartbeat = asyncio.get_event_loop().time()
        self.start_time = asyncio.get_event_loop().time()
        self.election_task = None
        self.heartbeat_task = None
        self.election_responses = set()
        self.expecting_answers = False

        # Register message handlers
        self.transport.register_handler("election", self.handle_election)
        self.transport.register_handler("answer", self.handle_answer)
        self.transport.register_handler("coordinator", self.handle_coordinator)
        self.transport.register_handler("heartbeat", self.handle_heartbeat)

    async def start(self):
        logger.info(f"Node {self.node_id} starting Bully algorithm")
        self.election_task = asyncio.create_task(self.election_timer())
        self.heartbeat_task = asyncio.create_task(self.heartbeat_sender())
        if self.node_id == min(self.all_nodes):
            await self.start_election()

    async def stop(self):
        if self.election_task:
            self.election_task.cancel()
        if self.heartbeat_task:
            self.heartbeat_task.cancel()

    async def restart(self):
        await self.stop()
        # Reset state
        self.state = BullyState.FOLLOWER
        self.leader_id = None
        self.last_heartbeat = asyncio.get_event_loop().time()
        self.start_time = asyncio.get_event_loop().time()
        self.election_responses = set()
        self.expecting_answers = False
        await self.start()

    async def election_timer(self):
        while True:
            await asyncio.sleep(self.election_timeout)
            if (
                self.state != BullyState.LEADER
                and self.should_start_election()
            ):
                await self.start_election()

    def should_start_election(self) -> bool:
        if self.leader_id is None:
            return True
        current_time = asyncio.get_event_loop().time()
        return current_time - self.last_heartbeat > self.election_timeout

    async def start_election(self):
        logger.info(f"Node {self.node_id} starting election")
        self.state = BullyState.CANDIDATE
        higher_nodes = [n for n in self.all_nodes if n > self.node_id]
        if not higher_nodes:
            # I'm the highest, become leader
            await self.become_leader()
            return

        self.expecting_answers = True
        self.election_responses = set()
        # Send election to higher nodes
        for node in higher_nodes:
            await self.transport.send_message(
                node, {"type": "election", "from": self.node_id}
            )

        # Wait for answers or timeout
        await asyncio.sleep(2.0)
        self.expecting_answers = False
        if not self.election_responses:
            # No answers, become leader
            await self.become_leader()

    async def become_leader(self):
        self.state = BullyState.LEADER
        self.leader_id = self.node_id
        logger.info(f"Node {self.node_id} became leader")
        # Send coordinator to all
        await self.transport.broadcast(
            {"type": "coordinator", "leader": self.node_id}
        )

    async def heartbeat_sender(self):
        while True:
            if self.state == BullyState.LEADER:
                await self.transport.broadcast(
                    {"type": "heartbeat", "leader": self.node_id}
                )
            await asyncio.sleep(self.heartbeat_interval)

    async def handle_election(self, message):
        sender = message["from"]
        if sender < self.node_id:
            # Send answer
            await self.transport.send_message(
                sender, {"type": "answer", "from": self.node_id}
            )
            # Start own election if not already
            if self.state != BullyState.CANDIDATE:
                await self.start_election()

    async def handle_answer(self, message):
        if self.expecting_answers:
            self.election_responses.add(
                message["from"]
            )  # In bully, answers prevent becoming leader

    async def handle_coordinator(self, message):
        leader = message["leader"]
        self.leader_id = leader
        self.state = (
            BullyState.FOLLOWER
            if leader != self.node_id
            else BullyState.LEADER
        )
        self.last_heartbeat = asyncio.get_event_loop().time()
        logger.info(f"Node {self.node_id} acknowledges leader {leader}")

    async def handle_heartbeat(self, message):
        self.last_heartbeat = asyncio.get_event_loop().time()
        # If not leader, update leader_id if from leader
        if "leader" in message:
            self.leader_id = message["leader"]

    def get_status(self):
        return {
            "node_id": self.node_id,
            "role": self.state.value,
            "leader_id": self.leader_id,
            "term": 0,  # Bully doesn't have terms
            "uptime": asyncio.get_event_loop().time() - self.start_time,
        }
