# SIH26123 — Edge-AI Distributed Fleet Coordination for Warehouse AMRs

**Problem statement:** [SIH26123](https://sih.gov.in) — Bharat Electronics
Limited — Smart Automation

A fully decentralized coordination and collision-avoidance framework for a
multi-robot warehouse fleet: no cloud, no central dispatcher, no single
point of failure. Every robot plans, negotiates, and bids for tasks
independently, communicating peer-to-peer with its neighbors. Designed
for deployment in air-gapped, RF-degraded environments (military depots,
hazardous-material warehouses) where cloud connectivity cannot be assumed
and collision safety is non-negotiable.

Includes an **Edge-AI layer** (XGBoost congestion prediction + Isolation
Forest anomaly detection) running entirely on-device within the compute
budget of a Raspberry Pi / Jetson Nano.

See [`docs/PS_MAPPING.md`](docs/PS_MAPPING.md) for the line-by-line
mapping from the official problem statement text to what's implemented
where — nothing in this repo exists without a reason traceable back to
the spec. See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full system
design and why each algorithm was chosen.

## Quick start

```bash
pip install -r requirements.txt
python scripts/train_edge_ai.py              # train the Edge-AI models
python -m pytest tests/ -v                   # run the full test suite (23/23 tests passing)
python scripts/run_demo.py                   # headless demo, 3 agents on the default map
python benchmark/stop_and_wait_baseline.py   # regenerate docs/BENCHMARK_RESULTS.md

# To run the true decentralized P2P demo (3 processes over UDP multicast):
python scripts/run_distributed_demo.py --kill-robot  # kills Robot 2 live to prove resilience
```

To see the live dashboard (needs a real display, not headless):
```python
from fleet.grid import WarehouseGrid
from fleet.agent import Agent
from fleet.sim.engine import SimulationEngine
from fleet.dashboard import render_pygame

grid = WarehouseGrid.default()
agents = [Agent("a1", (0,0), (9,8)), Agent("a2", (9,0), (0,8)), Agent("a3", (4,0), (4,8))]
engine = SimulationEngine(grid, agents, mode="pibt")
render_pygame.run(grid, engine)
```

## Visual demo (live, shareable, no install needed)

`visuals/warehouse_demo.html` runs the real fleet algorithm **live, in the browser** —
not a replay of a fixed recording. Click **New Run** for a fresh randomized scenario
(6-10 robots), or click any open aisle tile while it's running to block it and watch
the fleet re-route on the spot. Just open the file in any browser, nothing to install.

This is a JS port of the core simulation (`visuals/fleet_sim.js`), verified
independently against the same scenarios the Python test suite covers:
```bash
node visuals/verify_js_port.js      # standalone check, no browser needed
```
The Python implementation remains the sole tested source behind every benchmark
number and PPT claim — the JS port exists only to drive this interactive demo.

## Status

Build is sequenced over 7 days, each day's code merged and tagged
individually — see [`docs/DEV_LOG.md`](docs/DEV_LOG.md) for the running
log with what shipped each day and why.

- [x] **Day 1-2** — grid world with narrow choke points, single-agent A*, tick engine, tests
- [x] **Day 3** — decentralized comms layer (UDP multicast, no broker)
- [x] **Day 4** — PIBT conflict resolution (see docs/DEV_LOG.md for real bugs found and fixed)
- [x] **Day 5** — Edge-AI layer: XGBoost congestion predictor + Isolation Forest anomaly detector, integrated into auction bidding and fleet health monitoring
- [x] **Day 6** — decentralized task auction + blocked-aisle re-routing
- [x] **Day 7** — fleet dashboard, stop-and-wait baseline benchmark — **requirement-complete, 23/23 tests passing**, real numbers in `docs/BENCHMARK_RESULTS.md`

## Why decentralized (and why that's the point)

Commercial warehouse robotics platforms today — even market leaders —
still run a central software "brain" that orchestrates the fleet, cloud
or on-prem. That's exactly the latency / Wi-Fi-dead-zone / single-point-
of-failure risk this PS describes. This project removes that brain
entirely: each robot is an independent process, and the fleet keeps
functioning even if any one robot's connection drops. See
`ARCHITECTURE.md` for the resilience demo this makes possible.

## Repo layout

```
src/fleet/
  grid.py                 warehouse map (narrow aisles + choke points, by design)
  agent.py                per-robot state (position, battery, task, priority)
  planning/
    astar.py               single-agent pathfinding (Day 1-2)
    pibt.py                 multi-agent conflict resolution (Day 4)
  edge_ai/
    congestion_predictor.py  XGBoost aisle congestion prediction (Day 5)
    anomaly_detector.py      Isolation Forest robot health monitoring (Day 5)
  comms/
    p2p.py                   decentralized peer messaging (Day 3)
  allocation/
    auction.py               decentralized task bidding (Day 6)
  sim/
    engine.py                 tick-based simulation loop
  dashboard/
    render_pygame.py          fleet monitoring UI (Day 7)
tests/                        pytest suite, grows alongside each module
scripts/
  run_demo.py                 headless entry point
  run_distributed_demo.py     multi-process P2P demo (kill a robot live)
benchmark/                    stop-and-wait baseline vs PIBT comparison
docs/
  PS_MAPPING.md                requirement -> implementation traceability
  DEV_LOG.md                    daily build log
  JUDGE_QA.md                   scripted answers to expected judge questions
```
