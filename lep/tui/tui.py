import asyncio
from typing import Dict, List

import aiohttp
from rich.console import Console
from rich.live import Live
from rich.table import Table

console = Console()


class TUI:
    def __init__(self, nodes: List[int], ports: Dict[int, int]):
        self.nodes = nodes
        self.ports = ports

    async def fetch_status(self, node_id: int) -> Dict:
        port = self.ports[node_id]
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:{port}/status") as resp:
                    return await resp.json()
        except Exception:
            return {
                "node_id": node_id,
                "role": "unknown",
                "leader_id": None,
                "term": 0,
            }

    async def display(self):
        with Live(console=console, refresh_per_second=1) as live:
            while True:
                table = Table(title="Cluster Status")
                table.add_column("Node ID", style="cyan")
                table.add_column("Role", style="magenta")
                table.add_column("Leader ID", style="green")
                table.add_column("Term", style="yellow")

                statuses = await asyncio.gather(
                    *[self.fetch_status(n) for n in self.nodes]
                )
                for status in statuses:
                    table.add_row(
                        str(status["node_id"]),
                        status["role"],
                        str(status.get("leader_id", "None")),
                        str(status.get("term", 0)),
                    )
                live.update(table)
                await asyncio.sleep(1)


async def main():
    nodes = [1, 2, 3]
    ports = {1: 8081, 2: 8082, 3: 8083}
    tui = TUI(nodes, ports)
    await tui.display()


if __name__ == "__main__":
    asyncio.run(main())
