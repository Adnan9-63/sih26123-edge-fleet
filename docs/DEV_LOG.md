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

**Built:** `comms/p2p.py` using UDP multicast (`239.255.42.99:5007`),
not ROS2/DDS and not MQTT. `Peer.broadcast()` sends one UDP packet to the
multicast group; every other `Peer` that joined the group receives it
directly — no broker, no relay process, no central server anywhere in
the path. `Peer.poll_neighbors()` returns only neighbors heard from
within the last `STALE_AFTER` (2s) seconds, so anything older is dropped
automatically. `Peer.kill()` simulates a robot's comms going dark.

**Decision log:** picked UDP multicast over ROS2/DDS for now — DDS is
the more "textbook decentralized" answer and stays on the table as a
stretch upgrade, but a full ROS2 install (WSL2 on Windows) wasn't worth
the setup time against a 7-day clock. UDP multicast keeps the same core
property (broker-free, peer-to-peer) with zero extra installs on any OS.

**Verified:** 3 tests in `tests/test_p2p.py`, all passing — two peers
discover each other's broadcasts, a peer ignores its own broadcast, and
critically: a killed peer's last-known state goes stale and disappears
from its neighbor's view within ~2 seconds, with nothing else in the
system needing to notice or announce the disconnection. This last test
is the actual proof behind the live resilience demo in
`ARCHITECTURE.md` — kill one robot's connection on stage, the rest keep
running.

**Next:** Day 4-5 — PIBT conflict resolution + ORCA local avoidance,
wired to actually use `Peer.poll_neighbors()` for the "intent" data this
layer now shares but nothing consumes yet.

---

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
