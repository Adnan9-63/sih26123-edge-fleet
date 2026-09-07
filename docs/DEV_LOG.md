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

**Built:** `dashboard/render_pygame.py` (real pygame implementation,
verified headless via `SDL_VIDEODRIVER=dummy` and visually inspected via
a saved screenshot -- grid, obstacles, color-coded agents, battery dots,
live HUD, all correct), `benchmark/stop_and_wait_baseline.py` (three
scenarios, real numbers below), and upgraded `mode="naive"` in
`sim/engine.py` from "doesn't avoid collisions at all" (Day 1-2's
placeholder) to a genuine stop-and-wait baseline: check-before-move
against start-of-tick occupancy, wait if blocked, no negotiation.

**The actual benchmark numbers** (see `docs/BENCHMARK_RESULTS.md` for
the full output, regenerate anytime with
`python benchmark/stop_and_wait_baseline.py` -- confirmed identical
across repeated runs and fresh processes, see the reproducibility fix
below):

| Scenario | stop-and-wait | PIBT | improvement |
|---|---|---|---|
| no_contention (control) | 10 ticks | 10 ticks | 0% -- proves the comparison isn't rigged |
| head_on_choke | DNF (>300 ticks) | 10 ticks | ≥96.7% (conservative lower bound) |
| three_agent_multi_choke | DNF (>300 ticks) | 20 ticks | ≥93.3% (conservative lower bound) |

Zero collisions in every run, both modes. The PS asks for "a minimum
20% reduction ... when handling overlapping paths" -- both contended
scenarios clear that by a wide margin, and the no-contention control
scenario is there specifically to preempt "you only picked scenarios
that favor PIBT" -- it's included and it shows 0% difference, honestly,
because there's nothing to negotiate there.

**A reproducibility bug caught by simply running the benchmark twice:**
the first version of these numbers showed 17 ticks on one run and 23 on
another for the exact same scenario -- both zero-collision, both
correct, but not reproducible, which is a real problem for a number
that's about to be cited in a PPT. Root cause: PIBT's tie-break jitter
(`planning/pibt.py`, added Day 4 to escape symmetric deadlocks) used
Python's built-in `hash()` on strings, which is randomized per-process
by default (`PYTHONHASHSEED`) as a security feature -- meaning the exact
tie-break order, and so the exact tick count, could differ every run
even on the same machine. Fixed by switching to `zlib.crc32`, which is
stable across runs, processes, and machines. Reverified across 3
independent fresh processes with `PYTHONHASHSEED=random` explicitly set
-- identical 20-tick result every time. This is the kind of thing worth
mentioning if a judge asks "how do we know these numbers are real" --
because they were caught NOT being reliably real, once, and fixed.

**Why "DNF" instead of a real stop-and-wait completion time:** traced
this directly -- naive mode plans its A* path ONCE and never replans.
In every contended scenario tested, it permanently deadlocks: either two
agents facing off with neither willing to back off (no negotiation
mechanism exists to make either yield), or one agent parks at its goal
directly on the ONLY precomputed path another agent has, which that
agent then waits behind forever since it never learns to route around a
newly-stationary obstacle. This is a real, well-documented property of
static-path no-negotiation baselines in narrow environments, not a bug
in the baseline implementation -- it's exactly the failure mode the PS's
own Background section describes wanting to move away from. Reported
honestly as DNF with a conservative lower-bound percentage (using the
300-tick cap itself, not an invented "true" completion time) rather than
overstating the result.

**Status: PS26123 is now requirement-complete.** Every line in
`docs/PS_MAPPING.md` has real, tested code behind it. 18/18 tests
passing fleet-wide.

---

## Post-Day-7 — larger fleet + browser-based visual demo

**Why:** the pygame dashboard is real and correct, but it's a desktop window only visible on whoever's laptop runs it -- not shareable, not deployable, and visually plain (flat colored circles). For a live pitch, that's a real weakness worth fixing.

**Built:**
- `grid.py`: added `WarehouseGrid.large()` -- a bigger, more realistic multi-aisle floor plan (17x11, 8 parallel shelf columns with periodic cross-aisles and an open staging zone) alongside the existing `default()`, which every prior test stays pinned to unchanged.
- `scripts/export_demo_run.py`: runs a real 9-robot, 9-task scenario through the actual tested engine (auction + PIBT + a dynamically blocked aisle mid-run) and exports every tick as JSON. Nothing in this file is scripted or faked -- it's the same `SimulationEngine`, `run_auction`, and `check_blocked_agents` that the test suite covers.
- `visuals/warehouse_demo.html`: a single self-contained browser file (no server, no build step, no dependencies beyond two Google Fonts) that replays the exported run with smooth interpolated motion, a live fleet sidebar (battery bars, per-robot task status), a scrubbable timeline with event markers, and a live event feed. Verified visually via headless-browser screenshots at multiple points in playback -- task pickup markers, the blocked-aisle hazard overlay, and end-of-run "8/9 done, 1 remaining" states all render correctly.

**Real result from this run:** 9 robots, 9 tasks, one dynamically blocked aisle mid-run, 0 collisions, complete in 13 ticks. Notably, PIBT routed around the blocked cell on its own without needing the task-reassignment safety net to fire -- a genuinely good sign, not a missed feature (the reassignment path is still separately tested in `tests/test_auction.py`).

**To regenerate after any engine change:** `python scripts/export_demo_run.py`, then re-open `visuals/warehouse_demo.html` (the data is embedded at generation time, so the HTML must be rebuilt if the JSON changes -- see the file for the generation step).

---

## Isometric upgrade to the visual demo

Upgraded `visuals/warehouse_demo.html` from flat top-down to an isometric ("2.5D") view -- real depth on the shelf racks (proper 3-face isometric boxes with gradient shading), robots with grounding shadows, motion trails, all rendered on a pure Canvas 2D isometric projection (no WebGL/Three.js dependency added).

**Deliberate design decision, worth keeping:** a full 3D camera view was considered and rejected -- real warehouse fleet-ops software is top-down/isometric specifically because a 3D camera can let one object visually hide another, which is the opposite of what a coordination demo should ever do. To make sure this version never has that problem even with isometric depth: floor and shelf geometry render first (back-to-front), then EVERY robot renders in an unconditional second pass on top, sorted only by relative position to each other. A robot can never be hidden behind a shelf, structurally, not by luck. Verified visually via headless-browser screenshots at several points in playback, including the exact tick where the most shelf rows are between the camera and the robots.

Same underlying `visuals/demo_run.json` -- no simulation change, purely a rendering upgrade.
