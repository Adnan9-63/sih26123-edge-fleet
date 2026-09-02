"""
Tick-based simulation engine.

Supports two interchangeable planner modes, selected at construction:

  mode="naive" (Day 1-2 default) -- agents follow their independently
  planned A* paths and step forward blindly, with no conflict resolution.
  If two agents' paths cross at the same tick, this mode just detects and
  counts it. This is deliberately kept as-is -- it becomes the
  "traditional stop-and-wait"-style baseline the benchmark compares
  against later.

  mode="pibt" (Day 4) -- delegates each tick's next-cell decisions to
  planning.pibt.plan_step(), which is collision-free and swap-free by
  construction (see that module for why). This is the same engine, same
  grid, same agents -- only the planner differs, which is exactly what
  makes the benchmark comparison honest (see ARCHITECTURE.md, "Benchmark
  methodology").
"""
from __future__ import annotations

from dataclasses import dataclass, field

from fleet.agent import Agent
from fleet.grid import WarehouseGrid
from fleet.planning import pibt as pibt_planner
from fleet.planning.astar import astar


@dataclass
class TickResult:
    tick: int
    collisions_this_tick: list[tuple[str, str]] = field(default_factory=list)


class SimulationEngine:
    def __init__(self, grid: WarehouseGrid, agents: list[Agent], mode: str = "naive"):
        if mode not in ("naive", "pibt"):
            raise ValueError(f"unknown mode {mode!r}, expected 'naive' or 'pibt'")
        self.grid = grid
        self.agents = {a.agent_id: a for a in agents}
        self.mode = mode
        self.tick_count = 0
        self.total_collisions = 0
        self._plan_all()

    def _plan_all(self) -> None:
        for agent in self.agents.values():
            agent.path = astar(self.grid, agent.pos, agent.goal)

    def _propose_naive(self) -> dict[str, tuple]:
        proposed: dict[str, tuple] = {}
        for agent in self.agents.values():
            if agent.at_goal or len(agent.path) < 2:
                proposed[agent.agent_id] = agent.pos
            else:
                proposed[agent.agent_id] = agent.path[1]
        return proposed

    def _propose_pibt(self) -> dict[str, tuple]:
        # PIBT doesn't need a precomputed path -- it re-derives the best
        # direction toward agent.goal every tick from the grid directly.
        # tick_count is passed through purely to vary tie-breaks and
        # escape symmetric deadlocks -- see plan_step's docstring.
        return pibt_planner.plan_step(self.grid, self.agents, tick=self.tick_count)

    def step(self) -> TickResult:
        self.tick_count += 1

        if self.mode == "naive":
            proposed = self._propose_naive()
        else:
            proposed = self._propose_pibt()

        # Collision check runs regardless of mode -- in "pibt" mode this
        # should always come back empty. Checking it anyway rather than
        # assuming it is exactly what turns "PIBT prevents collisions"
        # from a claim into a continuously-verified property.
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
            if self.mode == "naive" and moved and len(agent.path) >= 2:
                agent.path.pop(0)
            agent.drain_battery(moved=moved)

            # blocked_ticks feeds PIBT's priority (planning/pibt.py) --
            # it must only track genuine, unwanted blockage. An agent
            # sitting at its own goal "fails to move" every tick by
            # choice, not by contention; if that counted toward
            # priority the same as real blockage, an at-goal agent's
            # priority climbs forever and permanently out-ranks (and so
            # permanently blocks) any agent still trying to pass through
            # it -- caught during Day 4 testing on the 3-agent scenario,
            # see docs/DEV_LOG.md.
            if agent.at_goal:
                agent.blocked_ticks = 0
            elif moved:
                agent.blocked_ticks = 0
            else:
                agent.blocked_ticks += 1

        return result

    def all_at_goal(self) -> bool:
        return all(a.at_goal for a in self.agents.values())

    def dashboard_state(self) -> list[dict]:
        return [a.to_dashboard_row() for a in self.agents.values()]
