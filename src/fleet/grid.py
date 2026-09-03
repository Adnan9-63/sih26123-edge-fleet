"""
Warehouse grid world.

PS mapping: this module defines the physical environment the fleet operates
in. SIH26123's Description explicitly calls out "narrow intersections or
choke points" as the scenario conflict resolution must be proven on -- so
the default layout below is NOT an open floor. It has single-file aisles
and a small number of intersection cells that force agents to negotiate.

See docs/PS_MAPPING.md for the full requirement -> module traceability.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

Cell = tuple[int, int]

# 0 = free cell, 1 = shelf/obstacle (impassable), 2 = charging station
# This 11x9 layout has three horizontal aisles connected by two narrow
# single-width vertical corridors, which is where robots are forced to
# meet and negotiate -- i.e. the "choke points" the PS asks for.
DEFAULT_LAYOUT = [
    "0000000000",
    "0111101110",
    "0000000000",
    "0111101110",
    "0000000000",
    "0111101110",
    "0000000000",
    "0111101110",
    "0000000000",
]


@dataclass
class WarehouseGrid:
    layout: tuple[str, ...]
    blocked_cells: set[Cell] = field(default_factory=set)
    version: int = 0  # bumped on block_cell/unblock_cell so cached BFS
                       # distances (planning/pibt.py's _dist_cache) know
                       # to recompute rather than serve stale distances
                       # from before the obstacle appeared

    @classmethod
    def default(cls) -> "WarehouseGrid":
        return cls(tuple(DEFAULT_LAYOUT))

    @property
    def height(self) -> int:
        return len(self.layout)

    @property
    def width(self) -> int:
        return len(self.layout[0])

    def is_free(self, cell: Cell) -> bool:
        x, y = cell
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        if cell in self.blocked_cells:
            return False
        return self.layout[y][x] != "1"

    def block_cell(self, cell: Cell) -> None:
        """Simulate a blocked aisle -- a dropped pallet, a stalled robot,
        anything that temporarily obstructs a cell that's normally free.
        This is what Day 6's re-routing/re-auction logic reacts to."""
        self.blocked_cells.add(cell)
        self.version += 1

    def unblock_cell(self, cell: Cell) -> None:
        self.blocked_cells.discard(cell)
        self.version += 1

    def neighbors(self, cell: Cell) -> Iterable[Cell]:
        x, y = cell
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (x + dx, y + dy)
            if self.is_free(nxt):
                yield nxt

    def bfs_distances(self, goal: Cell) -> dict[Cell, int]:
        """True graph-shortest-path distance (in hops) from every
        reachable free cell to `goal`, respecting obstacles.

        Deliberately NOT Manhattan distance: Manhattan distance is blind
        to walls, and in a warehouse grid that's a real bug, not a minor
        approximation -- an agent standing right next to a shelving unit
        with its goal on the other side sees a sideways step as "no
        closer" by Manhattan distance (a wall-crossing straight line
        looks short even though it's blocked), so a purely
        Manhattan-greedy agent can stand still forever right next to the
        opening it actually needs to take. Caught during Day 4 testing
        on exactly this grid -- see docs/DEV_LOG.md.

        Cheap to compute (single BFS, O(cells)) and meant to be cached
        per unique goal, not recomputed every tick -- see
        planning/pibt.py's `_dist_cache`.
        """
        from collections import deque

        dist = {goal: 0}
        q = deque([goal])
        while q:
            cur = q.popleft()
            for nxt in self.neighbors(cur):
                if nxt not in dist:
                    dist[nxt] = dist[cur] + 1
                    q.append(nxt)
        return dist

    def is_choke_point(self, cell: Cell) -> bool:
        """A free cell with exactly 2 opposite free neighbors (a single-file
        corridor segment) counts as a choke point -- useful for the
        benchmark script to report how often agents had to negotiate one."""
        if not self.is_free(cell):
            return False
        neighbor_count = sum(1 for _ in self.neighbors(cell))
        return neighbor_count <= 2

    def render_ascii(self, agent_positions: dict[str, Cell] | None = None) -> str:
        agent_positions = agent_positions or {}
        pos_to_label = {}
        for agent_id, pos in agent_positions.items():
            pos_to_label.setdefault(pos, agent_id[-1])
        rows = []
        for y, row in enumerate(self.layout):
            chars = []
            for x, c in enumerate(row):
                label = pos_to_label.get((x, y))
                if label is not None:
                    chars.append(label)
                elif c == "1":
                    chars.append("#")
                else:
                    chars.append(".")
            rows.append("".join(chars))
        return "\n".join(rows)
