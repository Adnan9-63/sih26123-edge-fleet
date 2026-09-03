"""
PIBT -- Priority Inheritance with Backtracking. Day 4.

Reference: Okumura, Machida, Defago, Tamura, "Priority Inheritance with
Backtracking for Iterative Multi-agent Path Finding" (IJCAI 2019). Each
tick, every agent gets a priority; starting from the highest-priority
undecided agent, we try to move it toward its goal. If its preferred
next cell is occupied, we recursively ask the occupant to move out of
the way FIRST (that occupant inherits the mover's urgency for the
purpose of this one negotiation) -- and if that chain of asks loops back
on itself (a cycle), the lower-priority agent in the cycle yields rather
than the two of them deadlocking or swapping through each other.

This keeps every tick's decision local: each agent only ever reasons
about its own immediate neighbors, never the whole fleet at once -- which
is why it fits the PS's "algorithms for edge hardware" requirement (see
ARCHITECTURE.md, "Why PIBT, not CBS").

Priority source: `Agent.blocked_ticks` (already tracked in engine.py) --
an agent that has failed to move for longer gets higher priority next
tick.

TWO CANDIDATE-ORDERING MODES -- this is the part that took two failed
attempts to get right during Day 4 testing (see docs/DEV_LOG.md for the
full story), and is worth documenting clearly so nobody "simplifies" it
back to a single ordering later:

  - An agent resolving its OWN turn (nobody is displacing it) ranks
    "stay" fairly, by true distance to its goal. This matters for an
    agent that has already arrived: staying has distance 0 and must sort
    first, or an arrived agent gets recursively evicted from its own
    goal cell by whoever needs to pass, and can oscillate forever.

  - An agent that is being RECURSIVELY asked to vacate a specific cell
    because a higher-priority agent wants it must treat "refuse and stay
    right here" as the LAST resort, tried only after every other
    neighbor fails -- even neighbors that are further from its own goal.
    Without this, an occupant whose only real escape route is a
    temporary detour will always prefer "just stay" (since staying is
    never worse, distance-wise, than backing away), and two facing
    agents deadlock permanently rather than one of them stepping aside.

Both are needed together. The first alone reintroduces the oscillation
bug; the second alone reintroduces eviction of arrived agents.
"""
from __future__ import annotations

import zlib

from fleet.agent import Agent
from fleet.grid import Cell, WarehouseGrid


def _stable_jitter(agent_id: str, tick: int) -> int:
    """Deterministic, reproducible tie-break jitter -- deliberately NOT
    Python's built-in hash(). hash() on strings is randomized per-process
    by default (PYTHONHASHSEED), which meant the benchmark's tick counts
    varied between runs even though correctness never did -- unacceptable
    for a number that gets cited in the idea PPT. zlib.crc32 is stable
    across runs, processes, and machines. Caught by re-running Day 7's
    benchmark twice and getting two different (both correct, both
    zero-collision) tick counts -- see docs/DEV_LOG.md."""
    return zlib.crc32(f"{agent_id}-{tick}".encode()) % 997


# One BFS per unique (goal, grid.version), cached across calls -- cheap
# (O(cells), once per goal, not per tick) and correctly accounts for
# walls, unlike raw Manhattan distance. Keyed on grid.version (not just
# goal) so a dynamically blocked aisle (grid.block_cell) correctly
# invalidates stale distances instead of silently serving a route
# through a cell that's no longer passable -- see grid.py's `version`
# field and docs/DEV_LOG.md Day 6 entry.
_dist_cache: dict[tuple[Cell, int], dict[Cell, int]] = {}


def _dist_to_goal(grid: WarehouseGrid, cell: Cell, goal: Cell) -> int:
    key = (goal, grid.version)
    if key not in _dist_cache:
        _dist_cache[key] = grid.bfs_distances(goal)
    return _dist_cache[key].get(cell, 10**6)  # unreachable -> effectively infinite


def plan_step(grid: WarehouseGrid, agents: dict[str, Agent], tick: int = 0) -> dict[str, Cell]:
    """Returns {agent_id: next_cell} for every agent, for this one tick.
    Guaranteed collision-free and swap-free by construction -- see the
    two guards inside `pibt` below.

    `tick` feeds a tie-break jitter (see `order` below) -- it does NOT
    affect safety (collisions are impossible regardless of tie-break,
    since that's enforced by cycle detection + reservations, not by
    priority order), only liveness in one specific pathological case:
    two agents whose goals are literally each other's current cell (a
    pure positional swap request). With a FIXED tie-break, that exact
    scenario cycles forever -- verified during Day 4 testing, see
    docs/DEV_LOG.md. A fixed priority order means the same agent always
    goes first and always gets recursively refused the same way, forever.
    Varying the tie-break by tick is the standard practical fix for
    exactly this kind of symmetric deadlock (the same technique behind
    randomized exponential backoff in networking) -- it costs nothing
    when there's no symmetry to break, and reliably breaks it when there
    is."""

    occupancy: dict[Cell, str] = {a.pos: aid for aid, a in agents.items()}
    decided: dict[str, Cell] = {}
    reserved_by: dict[Cell, str] = {}
    in_progress: set[str] = set()

    # blocked_ticks dominates (genuine starvation-based fairness); the
    # jitter term only breaks EXACT ties, and changes deterministically
    # tick to tick so a persistent symmetric standoff doesn't reproduce
    # the same losing order forever -- see _stable_jitter's docstring for
    # why this isn't Python's hash().
    order = sorted(
        agents.keys(),
        key=lambda aid: (-agents[aid].blocked_ticks, _stable_jitter(aid, tick), aid),
    )

    def candidates(agent: Agent, being_displaced: bool) -> list[Cell]:
        dist = lambda c: _dist_to_goal(grid, c, agent.goal)
        nbrs = sorted(grid.neighbors(agent.pos), key=lambda c: (dist(c), c))
        if being_displaced:
            return nbrs + [agent.pos]  # refusing to move is the last resort
        all_cells = nbrs + [agent.pos]
        all_cells.sort(key=lambda c: (dist(c), c))
        return all_cells  # "stay" ranked fairly by true distance

    def pibt(agent_id: str, being_displaced: bool = False) -> bool:
        if agent_id in decided:
            return True
        if agent_id in in_progress:
            return False  # cycle: caller should try its next candidate instead
        in_progress.add(agent_id)
        agent = agents[agent_id]

        for cell in candidates(agent, being_displaced):
            if cell in reserved_by and reserved_by[cell] != agent_id:
                continue  # another agent already claimed this cell as their next move

            occupant_id = occupancy.get(cell)
            if occupant_id is not None and occupant_id != agent_id:
                if occupant_id not in decided:
                    if not pibt(occupant_id, being_displaced=True):
                        continue  # occupant couldn't clear out; try our next candidate
                if decided.get(occupant_id) == cell:
                    continue  # occupant ultimately stayed -- cell is still occupied
                if decided.get(occupant_id) == agent.pos:
                    continue  # swap guard: occupant is moving into exactly our current
                              # cell at the same time we'd move into theirs

            decided[agent_id] = cell
            reserved_by[cell] = agent_id
            in_progress.discard(agent_id)
            return True

        in_progress.discard(agent_id)
        return False

    for agent_id in order:
        if agent_id not in decided:
            pibt(agent_id)

    # Defensive fallback: on a well-formed grid this should never
    # trigger, but if some agent genuinely exhausted every candidate,
    # force it to hold position rather than leave it undecided.
    for agent_id, agent in agents.items():
        if agent_id not in decided:
            decided[agent_id] = agent.pos

    return decided
