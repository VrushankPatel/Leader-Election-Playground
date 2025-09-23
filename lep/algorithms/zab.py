import asyncio
import logging
from enum import Enum
from typing import List, Optional, Set

from ..transport.transport import Transport

logger = logging.getLogger(__name__)

class ZabState(Enum):
    LOOKING = "looking"
    LEADER = "leader"
    FOLLOWING = "following"

class ZabAlgorithm:
    def __init__(self, node_id: int, all_nodes: List[int], transport: Transport):
        self.node_id = node_id
        self.all_nodes = sorted(all_nodes)
        self.transport = transport
        self.state = ZabState.LOOKING
        self.leader_id: Optional[int] = None
        self.epoch = 0
        self.voted_for: Optional[int] = None
        self.votes_received: Set[int] = set()
        self.acks_received: Set[int] = set()
        self.election_timeout = 3.0
        self.last_activity = asyncio.get_event_loop().time()
        self.start_time = asyncio.get_event_loop().time()

        # Register handlers
        self.transport.register_handler("vote", self.handle_vote)
        self.transport.register_handler("ack", self.handle_ack)
        self.transport.register_handler("leader", self.handle_leader)

    async def start(self):
        logger.info(f"Node {self.node_id} starting Zab algorithm")
        asyncio.create_task(self.election_timer())

    async def election_timer(self):
        while True:
            await asyncio.sleep(self.election_timeout)
            if self.state == ZabState.LOOKING and self.should_start_election():
                await self.start_election()

    def should_start_election(self) -> bool:
        current_time = asyncio.get_event_loop().time()
        return current_time - self.last_activity > self.election_timeout

    async def start_election(self):
        self.epoch += 1
        self.voted_for = self.node_id
        self.votes_received = {self.node_id}
        self.acks_received = set()
        logger.info(f"Node {self.node_id} starting election for epoch {self.epoch}")

        # Send vote to all
        vote_msg = {
            "type": "vote",
            "epoch": self.epoch,
            "candidate": self.node_id
        }
        responses = await self.transport.broadcast(vote_msg)
        # Process responses
        for node, resp in responses.items():
            if resp and isinstance(resp, dict):
                if resp.get("type") == "ack":
                    self.acks_received.add(node)

        # If majority ack, become leader
        majority = len(self.all_nodes) // 2 + 1
        if len(self.acks_received) >= majority - 1:  # -1 for self
            await self.become_leader()

    async def become_leader(self):
        self.state = ZabState.LEADER
        self.leader_id = self.node_id
        logger.info(f"Node {self.node_id} became leader for epoch {self.epoch}")
        # Send leader message
        leader_msg = {
            "type": "leader",
            "epoch": self.epoch,
            "leader": self.node_id
        }
        await self.transport.broadcast(leader_msg)

    async def handle_vote(self, message):
        epoch = message["epoch"]
        candidate = message["candidate"]
        if epoch > self.epoch:
            self.epoch = epoch
            self.state = ZabState.LOOKING
            self.voted_for = candidate
            self.last_activity = asyncio.get_event_loop().time()
            # Send ack
            ack_msg = {
                "type": "ack",
                "epoch": self.epoch,
                "voter": self.node_id
            }
            return ack_msg
        elif epoch == self.epoch and candidate == self.voted_for:
            # Already voted for this
            return {"type": "ack", "epoch": self.epoch, "voter": self.node_id}

    async def handle_ack(self, message):
        voter = message["voter"]
        self.acks_received.add(voter)
        majority = len(self.all_nodes) // 2 + 1
        if len(self.acks_received) >= majority and self.state == ZabState.LOOKING:
            await self.become_leader()

    async def handle_leader(self, message):
        epoch = message["epoch"]
        leader = message["leader"]
        if epoch >= self.epoch:
            self.epoch = epoch
            self.leader_id = leader
            self.state = ZabState.FOLLOWING if leader != self.node_id else ZabState.LEADER
            self.last_activity = asyncio.get_event_loop().time()
            logger.info(f"Node {self.node_id} following leader {leader}")

    def get_status(self):
        return {
            "node_id": self.node_id,
            "role": self.state.value,
            "leader_id": self.leader_id,
            "term": self.epoch,
            "uptime": asyncio.get_event_loop().time() - self.start_time
        }