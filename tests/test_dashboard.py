import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from fleet.agent import Agent
from fleet.dashboard import render_pygame
from fleet.grid import WarehouseGrid
from fleet.sim.engine import SimulationEngine


def test_dashboard_runs_headless_without_crashing_and_never_mutates_agents():
    """Not a visual test (can't be, in CI) -- but it does verify the
    read-only claim in render_pygame's docstring for real: run the
    dashboard, then confirm every agent's position/goal is EXACTLY what
    engine.step() alone would have produced, i.e. the dashboard loop
    added nothing of its own."""
    grid = WarehouseGrid.default()
    agents = [
        Agent(agent_id="agent-1", pos=(0, 0), goal=(9, 8)),
        Agent(agent_id="agent-2", pos=(9, 0), goal=(0, 8)),
    ]
    engine = SimulationEngine(grid, agents, mode="pibt")

    reference_grid = WarehouseGrid.default()
    reference_engine = SimulationEngine(
        reference_grid,
        [Agent(agent_id="agent-1", pos=(0, 0), goal=(9, 8)),
         Agent(agent_id="agent-2", pos=(9, 0), goal=(0, 8))],
        mode="pibt",
    )
    for _ in range(15):
        reference_engine.step()

    render_pygame.run(grid, engine, max_ticks=15)

    for agent_id in engine.agents:
        assert engine.agents[agent_id].pos == reference_engine.agents[agent_id].pos, (
            "dashboard-driven run diverged from a plain engine.step() run -- "
            "the dashboard must be strictly read-only"
        )
