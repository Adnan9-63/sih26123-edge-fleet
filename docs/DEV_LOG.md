# Development log

One entry per working day. Write it the same day you write the code —
this doubles as the source material for the idea PPT's technical
approach and feasibility slides later, so keep it honest: what worked,
what didn't, what you'd do differently.

---

## Day 1-2 — grid world, A*, tick engine

**Built:** `grid.py` (warehouse layout with narrow choke points by
design, not an open floor), `agent.py` (state model incl. battery from
day one, since the dashboard needs it later), `planning/astar.py`
(single-agent pathfinding), `sim/engine.py` (tick loop; agents follow
their independent A* paths with no conflict resolution yet — that's
intentional, see the module docstring), `tests/test_astar.py` (5 tests,
all passing).

**Verified:** ran `scripts/run_demo.py` end to end — 3 agents reach goal
in 17 ticks on the default map, one of them routed straight through a
choke point on purpose.

**Decision log:** chose to keep `engine.py`'s naive step logic instead of
building conflict resolution into it directly, so the exact same engine
can later run both the stop-and-wait baseline *and* the PIBT-resolved
version for an honest, apples-to-apples benchmark (see
`benchmark/README` once Day 7 lands).

**Next:** Day 3 — decentralized comms layer.

---

## Day 3 — comms layer

*(fill in: what backend you actually used — ROS2/DDS or UDP fallback —
and why; what `Peer.broadcast`/`poll_neighbors` ended up looking like;
any surprises)*

---

## Day 4-5 — PIBT + ORCA

*(fill in: did PIBT's finite-time guarantee hold in your test scenarios;
how you wired continuous-space ORCA output back onto the discrete grid;
the two-robot head-on-in-a-corridor test case and what it showed)*

---

## Day 6 — task allocation

*(fill in: bidding formula used; what happened when you forced a blocked
aisle mid-run — did re-auctioning actually kick in within a few ticks)*

---

## Day 7 — dashboard + benchmark

*(fill in: the actual numbers — collision count and tick count,
stop-and-wait baseline vs PIBT+ORCA, the real percentage improvement)*
