"""
Agent (AMR) state.

PS mapping: the Expected Solution requires the Fleet Dashboard to show
"real-time positions and battery status" -- so battery is a first-class
field here from day 1, not bolted on later.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from fleet.grid import Cell


@dataclass
class Agent:
    agent_id: str
    pos: Cell
    goal: Cell
    path: list[Cell] = field(default_factory=list)
    priority: float = 0.0          # used by the PIBT-style planner (Day 4-5)
    battery: float = 100.0         # percent; drains per tick moved
    task_id: str | None = None     # set by the auction allocator (Day 6)
    blocked_ticks: int = 0         # consecutive ticks unable to move

    def drain_battery(self, moved: bool, idle_drain: float = 0.02, move_drain: float = 0.08) -> None:
        self.battery = max(0.0, self.battery - (move_drain if moved else idle_drain))

    @property
    def at_goal(self) -> bool:
        return self.pos == self.goal

    def to_dashboard_row(self) -> dict:
        """Shape consumed by the dashboard (src/fleet/dashboard/render_pygame.py)."""
        return {
            "id": self.agent_id,
            "x": self.pos[0],
            "y": self.pos[1],
            "battery": round(self.battery, 1),
            "task": self.task_id,
            "blocked_ticks": self.blocked_ticks,
        }
