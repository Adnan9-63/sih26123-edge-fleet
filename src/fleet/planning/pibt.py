"""
PIBT-style decentralized multi-agent conflict resolution.

STATUS: Day 4-5 milestone. Not yet implemented -- interface defined now so
engine.py can be wired against it early and swapped in without a rewrite.

Reference: Okumura et al., "Priority Inheritance with Backtracking for
Iterative Multi-agent Path Finding" (IJCAI 2019). Each tick, every agent
gets a priority; the highest-priority agent adjacent to a contested cell
claims it, and agents it displaces recursively try alternative cells,
inheriting its priority so they get resolved before lower-priority agents.
This keeps each tick's decision local and cheap (a handful of adjacent
cells per agent) rather than a joint search over the whole fleet -- which
is why it fits the PS's "algorithms for edge hardware" requirement.

TODO (Day 4):
- priorities: dict[agent_id, float], bumped each tick an agent fails to move
- plan_step(grid, agents, occupied) -> dict[agent_id, next_cell]
- recursive PIBT() helper implementing priority inheritance + backtracking
- unit test: two agents approaching each other in a 1-wide corridor must
  resolve without collision and without both agents deadlocking
"""
from __future__ import annotations

from fleet.agent import Agent
from fleet.grid import WarehouseGrid


def plan_step(grid: WarehouseGrid, agents: list[Agent]) -> dict[str, tuple[int, int]]:
    raise NotImplementedError("Day 4-5: implement PIBT priority inheritance + backtracking here")
