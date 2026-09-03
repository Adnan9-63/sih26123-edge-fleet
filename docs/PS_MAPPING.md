# PS26123 requirement -> implementation traceability

Every line below is copied from the official problem statement text
(SIH26123, Bharat Electronics Limited). Each is mapped to the exact
module that satisfies it, so there is no ambiguity — for us, for judges,
or for anyone else on the team — about whether we've actually built what
was asked, versus something adjacent to it.

## Background (why this exists)

| PS says | Where we address it |
|---|---|
| Centralized cloud path planning causes high network latency | No cloud call exists anywhere in the tick loop — see `sim/engine.py`, each agent's plan is computed locally |
| Wi-Fi dead-zone vulnerabilities | `comms/p2p.py` is peer-to-peer (ROS2/DDS or UDP multicast) — no single access point dependency |
| Single-point-of-failure risk | No component in the architecture, including the dashboard, sits in any agent's control loop — see `ARCHITECTURE.md` |

## Description — three required capabilities

| # | PS requirement (verbatim) | Module | Status |
|---|---|---|---|
| 1 | "Decentralized Communication: Inter-robot messaging to share position and intent without a central server" | `comms/p2p.py` | **Done** -- UDP multicast, no broker; 3/3 tests passing |
| 2 | "Dynamic Multi-Agent Conflict Resolution: Resolving deadlocks and avoiding collisions at narrow intersections or choke points in real-time" | `planning/pibt.py` | **Done** -- PIBT alone satisfies this; `avoidance/orca.py` remains an optional stretch layer, not required for compliance |
| 3 | "Task Allocation & Re-routing: Automatically re-assigning pickup points or changing paths if one robot encounters a blocked aisle" | `allocation/auction.py` | **Done** -- decentralized auction + blocked-aisle release, 4/4 tests passing |

Note on requirement 2: the default layout in `grid.py` is deliberately
**not** an open floor — it has single-width vertical corridors connecting
horizontal aisles, so choke points exist by construction and every demo
run is forced to exercise them. This was a conscious choice, not an
oversight — an open-floor demo would technically avoid ever testing the
one scenario the PS names explicitly.

## Expected Solution — three deliverables + success criteria

| PS requirement (verbatim) | Module | Status |
|---|---|---|
| "Decentralized Network Stack: A peer-to-peer communication protocol where robots share localization data locally" | `comms/p2p.py`, `Agent`/`PeerState` fields | **Done** |
| "Multi-Agent Path Planning: Implementation of algorithms for edge hardware" | `planning/pibt.py` — chosen specifically for low per-agent, per-tick compute cost (see module docstring for why) | **Done** |
| "Fleet Dashboard: A lightweight monitoring UI that visualizes the entire fleet's real-time positions and battery status" | `dashboard/render_pygame.py`, reading `Agent.to_dashboard_row()` | **Done** -- verified headless + visually inspected, see docs/DEV_LOG.md Day 7 |
| **Success Criteria**: zero inter-robot collisions | `benchmark/stop_and_wait_baseline.py` compares `engine.total_collisions` across both planners | **Done** -- 0 collisions in every scenario, both planners, see docs/BENCHMARK_RESULTS.md |
| **Success Criteria**: >=20% faster than "traditional stop-and-wait" on overlapping paths | Same benchmark script; stop-and-wait baseline uses the same engine but halts on conflict instead of PIBT resolving it | **Done, exceeded** -- ≥93-97% (conservative, reproducible; baseline DNF under real contention), see docs/BENCHMARK_RESULTS.md |

## One thing worth being upfront about

The PS Description says the system "must run locally on edge hardware
(e.g., Raspberry Pi or Jetson Nano) onboard each robot," but the Expected
Solution explicitly asks for "**a multi-robot simulation**." We're
building the simulation, as asked — but every algorithm choice
(PIBT over CBS, ORCA over a joint-space solver, no cloud calls anywhere)
was made so that the exact same code could run on that class of edge
hardware if it were ever deployed to physical robots. That's a design
constraint we're honoring in software, not a requirement we're skipping.
Say this explicitly in the idea PPT's Feasibility slide — don't let a
judge find the tension and think it's an oversight.

## Team size / hardware minimum

- PS asks for "at least 3 AMRs" — `scripts/run_demo.py` runs 3 by default,
  `Agent` list is trivially extendable; stretch goal is demoing 8-10+ to
  show the coordination actually scales (see main dev log).
