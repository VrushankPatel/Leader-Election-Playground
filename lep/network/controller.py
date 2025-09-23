import random
from typing import Dict, List, Set, Tuple

class NetworkController:
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.partitions: Set[Tuple[int, int]] = set()
        self.delays: Dict[Tuple[int, int], float] = {}  # in ms
        self.drop_rates: Dict[Tuple[int, int], float] = {}  # 0-1

    def set_partition(self, node1: int, node2: int, partitioned: bool):
        pair: Tuple[int, int] = (min(node1, node2), max(node1, node2))
        if partitioned:
            self.partitions.add(pair)
        else:
            self.partitions.discard(pair)

    def set_delay(self, node1: int, node2: int, delay_ms: float):
        pair: Tuple[int, int] = (min(node1, node2), max(node1, node2))
        self.delays[pair] = delay_ms

    def set_drop_rate(self, node1: int, node2: int, rate: float):
        pair: Tuple[int, int] = (min(node1, node2), max(node1, node2))
        self.drop_rates[pair] = rate

    def is_partitioned(self, node1: int, node2: int) -> bool:
        pair: Tuple[int, int] = (min(node1, node2), max(node1, node2))
        return pair in self.partitions

    def get_delay(self, node1: int, node2: int) -> float:
        pair: Tuple[int, int] = (min(node1, node2), max(node1, node2))
        return self.delays.get(pair, 0.0)

    def should_drop(self, node1: int, node2: int) -> bool:
        pair: Tuple[int, int] = (min(node1, node2), max(node1, node2))
        rate = self.drop_rates.get(pair, 0.0)
        return self.rng.random() < rate