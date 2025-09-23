Leader Election Playground — implement Bully, Raft, and Zab; run partition/latency benchmarks; produce reproducible comparisons and artifacts.

Agenda

Purpose and success criteria.

Requirements (functional, nonfunctional, infra).

Design: components, protocol modules, APIs, data models.

Test & benchmark plan (scenarios, metrics, measurement).

Deliverables, automation, and timeline.
Confirm to proceed to code scaffolding, test harness, or CI automation.

1. Purpose & Success Criteria

Purpose. Build a reproducible sandbox that implements three leader-election algorithms (Bully, Raft, Zab), exercises them under controlled network partitions and delays, and reports latency, throughput, correctness, and availability tradeoffs.

Success criteria.

Working implementations of Bully, single-decree Raft (leader election + heartbeat), and Zab leader election (ZooKeeper-style).

Deterministic test harness to inject partitions, packet loss, and message delay.

Benchmark reports with metrics: leader election latency, leader change rate, availability (fraction of time a leader is present), safety violations (split-brain), and recovery time.

Reproducible scripts and Docker-based environment.

Clean API to swap algorithms and cluster size.

2. Requirements
Functional

Node processes communicate over message RPC (gRPC or plain TCP with protobuf).

Each protocol supports:

Start, stop, force-crash, restart node.

Explicit election trigger (timeout expiry or manual).

Expose local state via HTTP/JSON (role, term, leader, log index if applicable).

Deterministic simulated network controller:

Partition subsets, delay messages (ms distribution), drop messages (percent), reorder messages.

Recorder that logs all messages (timestamped) and produces deterministic replay.

Nonfunctional

Language: Go or Rust preferred for low-latency and concurrency clarity. (Pick one; I can scaffold).

Single-threaded logical behavior per node to ease reasoning; concurrency for I/O only.

Tests runnable locally with Docker Compose and on CI.

Telemetry: Prometheus metrics + Grafana dashboards optional.

Constraints

No external ZooKeeper/etcd dependencies for core algorithms.

Use protobuf for wire format.

Minimize randomness; seed RNGs for reproducibility.

3. System Design
Components

Node binary

Modules: Transport, ProtocolAdapter, StateMachine, Persistence (optional), MetricsEndpoint.

Transport layer

Pluggable real (gRPC/TCP) and simulated (in-memory controller) transports.

Protocol modules

BullyModule: uses ID comparison and election messages.

RaftModule: minimal election: RequestVote, AppendEntries heartbeat stubs. Support terms, votedFor.

ZabModule: leader proposal election similar to ZooKeeper leader election flow (vote, ack).

Network Controller

API to set partitions/delays/drops per node pair.

Can operate in scheduled scenarios file.

Harness / Orchestrator

Scenario runner: start cluster, apply failures, collect metrics, stop.

Recorder & Replay

Log all inter-node messages with monotonic timestamp and payload.

Replay mode to feed messages deterministically to debug safety violations.

Data Models / APIs

Protobuf messages: VoteRequest, VoteResponse, Heartbeat, LeaderAnnounce, Control (start/stop).

HTTP endpoints per node:

GET /status → { node_id, role, leader_id, term, uptime }

POST /control → { action: "crash"|"restart"|"pause"|"resume" }

Orchestrator CLI:

run-scenario --file=scenario.yaml --out=results/

4. Protocol-specific notes
Bully

Node IDs numeric; highest ID wins.

Timeout-based election start on missed heartbeat.

No log replication. Safety: watch for split-brain; verify only one leader by quorum observation.

Raft (election subset)

Implement election and heartbeat only. No full log replication required but leave stubs for AppendEntries.

Persistent votedFor to disk to test restart behavior.

Randomized election timeouts (seeded).

Zab

Follow leader election pattern: proposal, ack, leader acceptance.

Maintain acknowledged zxid (proposal id) ordering where applicable.

5. Test & Benchmark Plan
Cluster sizes

3, 5, 7 nodes.

Scenarios

Normal: no faults, measure leader election latency on startup.

Single node crash: crash leader, measure time to elect new leader.

Network partition: split 3/2 on 5-node cluster. Measure split-brain and leader churn.

Message delay: apply 50–500ms delay distribution to links.

Packet loss: 0–30% random drop.

Flapping: repeatedly partition and heal at intervals.

Restart with persistence: restart nodes while preserving vote persistence.

Metrics (collected per run)

Election latency: time from leader failure detection to stable leader for majority for N consecutive heartbeats.

Leader uptime fraction: fraction of scenario time with a valid leader.

Leader switch count.

Safety violations: concurrent leaders observed by majority.

Message count and bandwidth.

CPU and memory per node.

Measurement methodology

Use orchestrator timestamps as source of truth.

Define "stable leader" as same leader observed by at least floor(N/2)+1 nodes for 3 consecutive heartbeats.

Run each scenario 20 times with different RNG seeds. Report median and 95th percentile.

6. Implementation plan (high level steps)

Choose language and scaffolding.

Implement transport and protobuf APIs.

Implement Bully, Raft, Zab modules with common lifecycle.

Implement network controller and orchestrator.

Add logging, recorder, and replay.

Write scenarios and CI pipeline.

Run benchmarks for 3/5/7 nodes, collect results.

Produce report with graphs and findings.

7. Deliverables

Source repo with modular layout.

Docker Compose and Makefile to run scenarios.

Scenario YAML files and results CSVs.

Replayable message logs.

Benchmark report (Markdown + CSV + optional Grafana dashboard).

README with reproducible steps.

8. Automation & Reuse

CLI and scenario.yaml for reproducible runs.

Recorder log format JSONL for downstream analysis.

analyze.py script to compute metrics from logs and produce plots.

Template to add new protocols as plugins.

9. Minimal Tech Stack Recommendation

Language: Go.

Transport: gRPC + protobuf.

Container: Docker.

Testing: Go test + integration scripts.

Metrics: Prometheus-compatible / JSONL logs.

Orchestration: Docker Compose and a small Python/Go orchestrator.

10. Risks and mitigations

Non-determinism across runs. Mitigate by seeding RNGs and using orchestrator timestamps.

Clock skew. Use orchestrator monotonic clock and avoid relying on system wall clock.

Complexity of Zab. Implement simplified variant focusing on leader election.

11. Implementation Status

Completed:
- Project structure with Python, requirements, setup.py
- Transport layer with simulated transport and protobuf messages
- Network controller for partitions, delays, drops
- Bully algorithm implementation
- Raft election module
- Zab leader election module
- Orchestrator for scenario running and metrics
- Backend APIs with aiohttp for node status/control
- TUI frontend using rich for visualization
- Scenario YAMLs and run scripts
- Comprehensive tests for all modules
- Full CI pipeline with GitHub Actions
- Benchmarks and performance analysis scripts
- Docker integration
- Replay functionality for logs
- Advanced metrics and Grafana integration

Pending:
- None
