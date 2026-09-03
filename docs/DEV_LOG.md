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

## Day 4 — PIBT conflict resolution

**Built:** `planning/pibt.py` (real implementation, priority inheritance
+ backtracking), wired into `sim/engine.py` as a second `mode="pibt"`
alongside Day 1-2's `mode="naive"` -- same engine, swappable planner,
exactly so the benchmark comparison later is apples-to-apples.

**Three real bugs found and fixed by testing, not by inspection** --
worth keeping this honest in the record, because catching these is
exactly the kind of thing a judge might probe for, and "we tested it and
found X" is a stronger answer than pretending it worked first try:

1. *Arrived agents getting evicted.* First version ranked "stay" as
   always-last regardless of true distance. An agent that had already
   reached its goal would get recursively bumped out of its own goal
   cell by the next agent that needed to pass, and could oscillate
   forever. Fix: rank "stay" fairly by true distance-to-goal on an
   agent's own turn (distance 0 if already there, so it sorts first) --
   but NOT when an agent is being recursively displaced by someone else
   (see #2).

2. *Symmetric standoffs.* Fixing #1 alone reintroduced a different
   failure: two agents facing off with a real detour available would
   both just choose "stay" forever, since staying is never worse,
   distance-wise, than backing away. Fix: an agent being recursively
   asked to vacate a specific cell must treat "refuse and stay" as the
   absolute last resort, tried only after every real alternative fails --
   different rule from an agent resolving its own turn.

3. *Manhattan distance is blind to walls.* One agent (starting cell had
   no direct opening toward its goal, only a sideways detour to reach
   the actual corridor) sat still forever, because Manhattan distance
   scored the necessary sideways step as "no better than standing still"
   -- it doesn't know a wall is in the way. Fix: replaced Manhattan
   distance with true BFS graph-distance (`grid.bfs_distances`), cached
   per goal so it's still cheap per tick.

4. *Priority accounting for at-goal agents.* Even after #1-3, one
   3-agent scenario still stalled: an agent sitting at its own goal kept
   accumulating "blocked" priority every tick it "failed to move" --
   except it wasn't failing, it was succeeding at staying. That let it
   permanently out-rank (and block) an agent still trying to path
   through it. Fix: `blocked_ticks` freezes at 0 for an agent that's at
   its goal, since it isn't genuinely blocked.

**Known, deliberate limitation (not a bug):** a literal positional swap
-- two agents whose goal is exactly each other's current cell -- is not
guaranteed to resolve. Verified empirically to persist 500+ ticks with
zero convergence, though safety (zero collisions) holds throughout. This
is a known degenerate case for local MAPF planners generally, and the
right fix is at the task-allocation layer (Day 6): never assign two
agents to directly swap destinations. See
`tests/test_pibt.py::test_direct_positional_swap_is_safe_but_not_guaranteed_to_resolve`
for the documented test.

**Verified:** 13/13 tests passing, including the forced head-on
choke-point corridor scenario (the one the PS explicitly asks for) and
the full 3-agent scenario from the Day 1 demo, now conflict-free.

**Next:** Day 5 -- ORCA local avoidance layer, or straight to Day 6
(task allocation) if the team decides ORCA is a stretch-goal rather than
core scope given PIBT alone already satisfies the PS's discrete
conflict-resolution requirement.

---

## Day 5 — ORCA (if pursued)

*(fill in: how continuous-space ORCA output was reconciled back onto the
discrete grid PIBT plans on; whether it was scoped in or deferred)*

---

## Day 6 — task allocation

**Built:** `allocation/auction.py` -- decentralized bidding (`run_auction`,
lowest bid wins, bid = true graph distance + battery penalty) and
blocked-agent release (`check_blocked_agents`, releases a task back to
the open pool if `Agent.blocked_ticks >= RE_AUCTION_THRESHOLD` while
carrying it). Also extended `grid.py` with dynamic obstacles
(`block_cell`/`unblock_cell`) to actually simulate "a robot encounters a
blocked aisle," which the PS names explicitly.

**One correctness fix that mattered:** `planning/pibt.py`'s BFS distance
cache was keyed only on goal cell, computed once and reused forever --
correct for a static grid, wrong the moment `block_cell` changes what's
reachable. Added `grid.version` (bumped on every block/unblock) and
rekeyed the cache on `(goal, grid.version)`, so a newly blocked aisle
can't silently serve stale, now-invalid distances.

**Verified:** 4 new tests, including a full end-to-end scenario -- two
agents, one task, the entire x=0 corridor sealed with `block_cell`
before the auction even runs. The auction correctly bids on *true*
graph distance (not Manhattan), so it already avoids the sealed route
without needing the blocked-agent check to intervene at all -- both
mechanisms (auction-time avoidance and mid-task release) are tested, but
this particular scenario exercises the first one. 17/17 tests passing
fleet-wide.

**Design note kept honest in the code:** `run_auction` is written as a
pure function, not an object holding state or authority. It's documented
explicitly as computing the SAME outcome independent, comms.p2p-based
per-robot bidding would converge to -- a simulation convenience for
fast, testable resolution, not a dispatcher. Worth being able to explain
this distinction clearly if a judge asks "isn't a shared task-allocation
function just a central coordinator by another name."

**Next:** Day 7 -- fleet dashboard + the actual stop-and-wait vs
PIBT benchmark, which is what finally produces the real numbers for the
PS's Success Criteria.

---

## Day 7 — dashboard + benchmark

*(fill in: the actual numbers — collision count and tick count,
stop-and-wait baseline vs PIBT+ORCA, the real percentage improvement)*
