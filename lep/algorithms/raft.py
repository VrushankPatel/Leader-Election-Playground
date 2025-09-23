import asyncio
import logging
import random
from enum import Enum
from typing import List, Optional

from ..transport.transport import Transport

logger = logging.getLogger(__name__)

class RaftState(Enum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"

class RaftAlgorithm:
    def __init__(self, node_id: int, all_nodes: List[int], transport: Transport, seed: int = 42):
        self.node_id = node_id
        self.all_nodes = all_nodes
        self.transport = transport
        self.state = RaftState.FOLLOWER
        self.current_term = 0
        self.voted_for: Optional[int] = None
        self.leader_id: Optional[int] = None
        self.votes_received = 0
        self.rng = random.Random(seed + node_id)
        self.election_timeout = self.rng.uniform(1.0, 2.0)  # seconds
        self.heartbeat_interval = 0.5
        self.last_heartbeat = asyncio.get_event_loop().time()

        # Persistence (simulated)
        self.persistent_voted_for = None

        # Register handlers
        self.transport.register_handler("request_vote", self.handle_request_vote)
        self.transport.register_handler("vote_response", self.handle_vote_response)
        self.transport.register_handler("append_entries", self.handle_append_entries)

    async def start(self):
        logger.info(f"Node {self.node_id} starting Raft algorithm")
        asyncio.create_task(self.election_timer())
        asyncio.create_task(self.heartbeat_sender())

    async def election_timer(self):
        while True:
            timeout = self.election_timeout if self.state != RaftState.LEADER else float('inf')
            await asyncio.sleep(timeout)
            if self.state != RaftState.LEADER and self.should_start_election():
                await self.start_election()

    def should_start_election(self) -> bool:
        current_time = asyncio.get_event_loop().time()
        return current_time - self.last_heartbeat > self.election_timeout

    async def start_election(self):
        self.current_term += 1
        self.state = RaftState.CANDIDATE
        self.voted_for = self.node_id
        self.votes_received = 1  # vote for self
        self.persist_vote()
        logger.info(f"Node {self.node_id} starting election for term {self.current_term}")

        # Request votes from all
        vote_req = {
            "type": "request_vote",
            "term": self.current_term,
            "candidate_id": self.node_id,
            "last_log_index": 0,
            "last_log_term": 0
        }
        responses = await self.transport.broadcast(vote_req)
        # Process responses (in real, async)
        for node, resp in responses.items():
            if resp and isinstance(resp, dict) and resp.get("vote_granted"):
                self.votes_received += 1

        majority = len(self.all_nodes) // 2 + 1
        if self.votes_received >= majority:
            await self.become_leader()

    async def become_leader(self):
        self.state = RaftState.LEADER
        self.leader_id = self.node_id
        logger.info(f"Node {self.node_id} became leader for term {self.current_term}")
        # Send initial heartbeat
        await self.send_heartbeat()

    async def send_heartbeat(self):
        if self.state == RaftState.LEADER:
            heartbeat = {
                "type": "append_entries",
                "term": self.current_term,
                "leader_id": self.node_id,
                "prev_log_index": 0,
                "prev_log_term": 0,
                "entries": [],
                "leader_commit": 0
            }
            await self.transport.broadcast(heartbeat)

    async def heartbeat_sender(self):
        while True:
            await asyncio.sleep(self.heartbeat_interval)
            await self.send_heartbeat()

    async def handle_request_vote(self, message):
        term = message["term"]
        candidate = message["candidate_id"]
        if term > self.current_term:
            self.current_term = term
            self.state = RaftState.FOLLOWER
            self.voted_for = None
        granted = (self.voted_for is None or self.voted_for == candidate) and term >= self.current_term
        if granted:
            self.voted_for = candidate
            self.persist_vote()
        response = {
            "type": "vote_response",
            "term": self.current_term,
            "vote_granted": granted
        }
        return response

    async def handle_vote_response(self, message):
        # Already handled in start_election
        pass

    async def handle_append_entries(self, message):
        term = message["term"]
        leader = message["leader_id"]
        if term >= self.current_term:
            self.current_term = term
            self.state = RaftState.FOLLOWER
            self.leader_id = leader
            self.last_heartbeat = asyncio.get_event_loop().time()
            # Send success response
            return {"type": "append_response", "term": self.current_term, "success": True}

    def persist_vote(self):
        # Simulate persistence
        self.persistent_voted_for = self.voted_for

    def get_status(self):
        return {
            "node_id": self.node_id,
            "role": self.state.value,
            "leader_id": self.leader_id,
            "term": self.current_term,
            "uptime": 0  # TODO
        }