"""
Single-agent A* pathfinding on the warehouse grid.

Day 1-2 milestone. This runs independently per-agent with no knowledge of
other agents -- multi-agent conflict resolution is layered on top of this
in planning/pibt.py (Day 4-5), not folded into the search itself. Keeping
this pure and agent-local matters for the PS: each robot's compute must be
cheap enough to plausibly run on edge hardware (Raspberry Pi / Jetson
Nano), so we deliberately avoid a joint-space search across all agents.
"""
from __future__ import annotations

import heapq

from fleet.grid import Cell, WarehouseGrid


def manhattan(a: Cell, b: Cell) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(grid: WarehouseGrid, start: Cell, goal: Cell) -> list[Cell]:
    """Returns a list of cells from start to goal inclusive, or [] if
    unreachable. Standard grid A* with Manhattan heuristic."""
    if start == goal:
        return [start]

    frontier: list[tuple[int, int, Cell]] = [(0, 0, start)]
    came_from: dict[Cell, Cell] = {}
    cost_so_far: dict[Cell, int] = {start: 0}
    counter = 0  # tie-breaker so heap never compares Cell tuples directly

    while frontier:
        _, _, current = heapq.heappop(frontier)

        if current == goal:
            return _reconstruct(came_from, start, goal)

        for nxt in grid.neighbors(current):
            new_cost = cost_so_far[current] + 1
            if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:
                cost_so_far[nxt] = new_cost
                priority = new_cost + manhattan(nxt, goal)
                counter += 1
                heapq.heappush(frontier, (priority, counter, nxt))
                came_from[nxt] = current

    return []  # no path found


def _reconstruct(came_from: dict[Cell, Cell], start: Cell, goal: Cell) -> list[Cell]:
    path = [goal]
    while path[-1] != start:
        path.append(came_from[path[-1]])
    path.reverse()
    return path
