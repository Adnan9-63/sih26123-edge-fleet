"""
Generates a full, real simulation run on the larger warehouse layout with
a bigger fleet, and exports every tick as JSON for the browser-based
visual demo (visuals/warehouse_demo.html). This is NOT scripted or faked
-- it runs the actual tested engine (comms/allocation/PIBT), the same
code covered by tests/, and just records what really happened.

Scenario, deliberately designed to exercise every subsystem in one run:
  - 9 robots start idle in the staging area
  - 9 pickup tasks scattered across the shelf aisles
  - a real decentralized auction (allocation/auction.py) assigns them
  - PIBT (planning/pibt.py) handles all movement + choke-point negotiation
  - partway through, one aisle gets dynamically blocked (grid.block_cell)
    to trigger a real re-auction and show a task reassigned to a
    different robot -- not scripted, this is check_blocked_agents +
    run_auction actually firing mid-run

Usage:
    python scripts/export_demo_run.py
Writes: visuals/demo_run.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fleet.agent import Agent
from fleet.allocation.auction import Task, check_blocked_agents, run_auction
from fleet.grid import WarehouseGrid
from fleet.sim.engine import SimulationEngine

MAX_TICKS = 400
BLOCK_AISLE_AT_TICK = 3
BLOCK_CELL = (8, 7)  # a shared cross-aisle cell most robots pass through early


def main() -> None:
    grid = WarehouseGrid.large()

    staging_row = grid.height - 1
    start_cols = [1, 3, 5, 7, 9, 11, 13, 15, 2]
    agents = {
        f"R{i+1}": Agent(agent_id=f"R{i+1}", pos=(c, staging_row), goal=(c, staging_row))
        for i, c in enumerate(start_cols)
    }

    pickup_cells = [(2, 0), (12, 0), (14, 2), (8, 2), (0, 0), (16, 2), (6, 0), (4, 2), (10, 0)]
    open_tasks = [Task(task_id=f"T{i+1}", pickup_cell=c) for i, c in enumerate(pickup_cells)]
    open_tasks = run_auction(grid, agents, open_tasks)
    assert open_tasks == [], "every robot should have won exactly one task at start"

    engine = SimulationEngine(grid, list(agents.values()), mode="pibt")

    frames = []
    events = []
    completed_tasks = set()
    blocked_triggered = False

    def snapshot(tick: int) -> dict:
        return {
            "tick": tick,
            "collisions": engine.total_collisions,
            "agents": [
                {"id": a.agent_id, "x": a.pos[0], "y": a.pos[1],
                 "battery": round(a.battery, 1), "task": a.task_id}
                for a in engine.agents.values()
            ],
        }

    frames.append(snapshot(0))

    for tick in range(1, MAX_TICKS + 1):
        if tick == BLOCK_AISLE_AT_TICK and not blocked_triggered:
            grid.block_cell(BLOCK_CELL)
            blocked_triggered = True
            events.append({"tick": tick, "type": "aisle_blocked", "cell": list(BLOCK_CELL)})

        engine.step()

        released = check_blocked_agents(engine.agents, open_tasks=[])
        if released:
            for t in released:
                events.append({"tick": tick, "type": "task_released", "task": t.task_id})
            run_auction(grid, engine.agents, released)
            for a in engine.agents.values():
                if a.task_id in {t.task_id for t in released}:
                    events.append({"tick": tick, "type": "task_reassigned",
                                    "task": a.task_id, "agent": a.agent_id})

        for a in engine.agents.values():
            if a.task_id is not None and a.pos == a.goal and a.task_id not in completed_tasks:
                completed_tasks.add(a.task_id)
                events.append({"tick": tick, "type": "task_completed",
                                "task": a.task_id, "agent": a.agent_id})
                a.task_id = None

        frames.append(snapshot(tick))

        if len(completed_tasks) == len(pickup_cells):
            break

    print(f"Simulation finished in {len(frames)-1} ticks. "
          f"Collisions: {engine.total_collisions}. Tasks completed: {len(completed_tasks)}/{len(pickup_cells)}")
    assert engine.total_collisions == 0, "demo export must be collision-free"

    out = {
        "grid": {"width": grid.width, "height": grid.height, "layout": list(grid.layout),
                 "blocked_cells": [list(c) for c in grid.blocked_cells]},
        "pickup_cells": [list(c) for c in pickup_cells],
        "frames": frames,
        "events": events,
        "meta": {"total_ticks": len(frames) - 1, "collisions": engine.total_collisions,
                 "robot_count": len(agents), "task_count": len(pickup_cells)},
    }

    out_dir = Path(__file__).resolve().parent.parent / "visuals"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "demo_run.json"
    out_path.write_text(json.dumps(out))
    print(f"Written to {out_path} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
