# Leader Election Playground

A reproducible sandbox for implementing and benchmarking leader election algorithms: Bully, Raft, and Zab.

## Overview

This project provides working implementations of three leader-election algorithms, allowing users to exercise them under controlled network conditions (partitions, delays, packet loss) and compare their performance in terms of latency, throughput, correctness, and availability.

## Features

- **Algorithms Implemented**: Bully, Raft (election subset), Zab (leader election)
- **Network Simulation**: Deterministic injection of partitions, delays, and drops
- **Benchmarking**: Automated scenarios with metrics collection
- **Visualization**: TUI frontend and web UI for cluster state monitoring
- **Web UI**: Frontend served on port 8080 for real-time cluster visualization
- **Reproducibility**: Seeded RNGs and deterministic replay

## Quick Start

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run a scenario: `python run_scenario.py scenarios/normal.yaml`
4. (Optional) Run web UI: `python web_server.py` to serve cluster visualization on port 8080

## Architecture

- **Backend**: Python with gRPC/protobuf for communication
- **Frontend**: Text-based UI and web UI for visualization
- **Modules**: Pluggable algorithm implementations
- **Orchestrator**: Scenario runner and metrics collector

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.