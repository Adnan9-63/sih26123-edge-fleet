"""
Tick-based simulation engine.

DAY 1-2 SCOPE: agents follow their independently-planned A* paths and
naively step forward each tick. This intentionally does NOT resolve
conflicts yet -- if two agents' paths cross at the same tick, this engine
currently just detects and counts it. That is deliberate: it means we can
run this exact engine as the "traditional stop-and-wait" style baseline
later in benchmark/, then swap in the PIBT-based conflict-resolving
planner (Day 4-5) and diff the two runs to produce the honest, on-screen
comparison the PS's Success Criteria asks for (zero collisions, >=20%
faster than the naive baseline).

Do not add conflict resolution to this file directly -- it belongs in
planning/pibt.py so the two behaviours stay swappable and comparable.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from fleet.agent import Agent
from fleet.grid import WarehouseGrid
from fleet.planning.astar import astar


@dataclass
class TickResult:
    tick: int
    collisions_this_tick: list[tuple[str, str]] = field(default_factory=list)


class SimulationEngine:
    def __init__(self, grid: WarehouseGrid, agents: list[Agent]):
        self.grid = grid
        self.agents = {a.agent_id: a for a in agents}
        self.tick_count = 0
        self.total_collisions = 0
        self._plan_all()

    def _plan_all(self) -> None:
        for agent in self.agents.values():
            agent.path = astar(self.grid, agent.pos, agent.goal)

    def step(self) -> TickResult:
        self.tick_count += 1
        proposed: dict[str, tuple] = {}

        for agent in self.agents.values():
            if agent.at_goal or len(agent.path) < 2:
                proposed[agent.agent_id] = agent.pos
                continue
            proposed[agent.agent_id] = agent.path[1]

        # naive same-cell collision check (swap/edge conflicts are handled
        # once PIBT lands in Day 4-5 -- flagged explicitly, not silently
        # ignored)
        occupancy: dict[tuple, list[str]] = {}
        for agent_id, cell in proposed.items():
            occupancy.setdefault(cell, []).append(agent_id)

        result = TickResult(tick=self.tick_count)
        for cell, ids in occupancy.items():
            if len(ids) > 1:
                for i in range(len(ids)):
                    for j in range(i + 1, len(ids)):
                        result.collisions_this_tick.append((ids[i], ids[j]))
                self.total_collisions += len(ids) - 1

        for agent in self.agents.values():
            new_pos = proposed[agent.agent_id]
            moved = new_pos != agent.pos
            agent.pos = new_pos
            if moved and len(agent.path) >= 2:
                agent.path.pop(0)
            agent.drain_battery(moved=moved)
            agent.blocked_ticks = 0 if moved else agent.blocked_ticks + 1

        return result

    def all_at_goal(self) -> bool:
        return all(a.at_goal for a in self.agents.values())

    def dashboard_state(self) -> list[dict]:
        return [a.to_dashboard_row() for a in self.agents.values()]
