"""
Live visual demo -- run this to actually SEE the fleet dashboard, with a
real window (not headless). Needs pygame installed and a real display,
so run this on your own machine, not in a remote/headless environment.

Usage:
    python scripts/run_dashboard_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fleet.agent import Agent
from fleet.grid import WarehouseGrid
from fleet.sim.engine import SimulationEngine
from fleet.dashboard import render_pygame


def main() -> None:
    grid = WarehouseGrid.default()
    agents = [
        Agent(agent_id="agent-1", pos=(0, 0), goal=(9, 8)),
        Agent(agent_id="agent-2", pos=(9, 0), goal=(0, 8)),
        Agent(agent_id="agent-3", pos=(4, 0), goal=(4, 8)),
    ]
    engine = SimulationEngine(grid, agents, mode="pibt")

    print("Opening dashboard window -- close it, or wait for all agents to reach goal.")
    render_pygame.run(grid, engine, max_ticks=200)
    print(f"Finished after {engine.tick_count} ticks. Collisions: {engine.total_collisions}")


if __name__ == "__main__":
    main()
