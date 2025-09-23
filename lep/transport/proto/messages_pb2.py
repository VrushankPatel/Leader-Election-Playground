# Generated protobuf classes (simplified)

from dataclasses import dataclass
from typing import List

@dataclass
class VoteRequest:
    term: int
    candidate_id: int
    last_log_index: int
    last_log_term: int

@dataclass
class VoteResponse:
    term: int
    vote_granted: bool

@dataclass
class AppendEntries:
    term: int
    leader_id: int
    prev_log_index: int
    prev_log_term: int
    entries: List[str]
    leader_commit: int

@dataclass
class Heartbeat:
    term: int
    leader_id: int

@dataclass
class LeaderAnnounce:
    leader_id: int
    term: int