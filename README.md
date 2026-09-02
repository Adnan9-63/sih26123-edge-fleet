# SIH26123 — Edge-AI Distributed Fleet Coordination for Warehouse AMRs

**Problem statement:** [SIH26123](https://sih.gov.in) — Bharat Electronics
Limited — Smart Automation

A fully decentralized coordination and collision-avoidance framework for a
multi-robot warehouse fleet: no cloud, no central dispatcher, no single
point of failure. Every robot plans, negotiates, and bids for tasks
independently, communicating peer-to-peer with its neighbors.

See [`docs/PS_MAPPING.md`](docs/PS_MAPPING.md) for the line-by-line
mapping from the official problem statement text to what's implemented
where — nothing in this repo exists without a reason traceable back to
the spec. See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full system
design and why each algorithm was chosen.

## Quick start

```bash
pip install -r requirements.txt
python -m pytest tests/ -v          # run the test suite
python scripts/run_demo.py          # headless demo, 3 agents on the default map
```

## Status

Build is sequenced over 7 days, each day's code merged and tagged
individually — see [`docs/DEV_LOG.md`](docs/DEV_LOG.md) for the running
log with what shipped each day and why.

- [x] **Day 1-2** — grid world with narrow choke points, single-agent A*, tick engine, tests
- [x] **Day 3** — decentralized comms layer (UDP multicast, no broker)
- [x] **Day 4** — PIBT conflict resolution (13/13 tests passing; see docs/DEV_LOG.md for real bugs found and fixed)
- [ ] **Day 5** — ORCA local avoidance (bonus layer — PIBT alone already satisfies the PS's core conflict-resolution ask; see dev log)
- [ ] **Day 6** — decentralized auction-based task allocation, blocked-aisle re-routing
- [ ] **Day 7** — fleet dashboard, stop-and-wait baseline benchmark, final numbers

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
    pibt.py                 multi-agent conflict resolution (Day 4-5)
  avoidance/
    orca.py                 real-time local collision avoidance (Day 4-5)
  comms/
    p2p.py                   decentralized peer messaging (Day 3)
  allocation/
    auction.py               decentralized task bidding (Day 6)
  sim/
    engine.py                 tick-based simulation loop
  dashboard/
    render_pygame.py          fleet monitoring UI (Day 7)
tests/                        pytest suite, grows alongside each module
scripts/run_demo.py           headless entry point
benchmark/                    stop-and-wait baseline vs PIBT+ORCA comparison
docs/
  PS_MAPPING.md                requirement -> implementation traceability
  DEV_LOG.md                    daily build log
```
