"""
Day 1 headless demo.

Places 3 agents on the default warehouse layout -- deliberately routed
through the narrow vertical corridors so you can already see, even before
conflict resolution exists (that's Day 4-5), *where* the conflicts will
happen. Run this now; run it again after PIBT lands and diff the
behaviour -- that diff is your evidence for the benchmark claim later.

Usage:
    python scripts/run_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fleet.agent import Agent
from fleet.grid import WarehouseGrid
from fleet.sim.engine import SimulationEngine

MAX_TICKS = 40


def main() -> None:
    grid = WarehouseGrid.default()

    agents = [
        Agent(agent_id="agent-1", pos=(0, 0), goal=(9, 8)),
        Agent(agent_id="agent-2", pos=(9, 0), goal=(0, 8)),
        Agent(agent_id="agent-3", pos=(4, 0), goal=(4, 8)),  # goes straight through a choke point
    ]

    engine = SimulationEngine(grid, agents)

    print(f"Warehouse layout ({grid.width}x{grid.height}), {len(agents)} agents\n")

    for tick in range(1, MAX_TICKS + 1):
        result = engine.step()
        positions = {a.agent_id: a.pos for a in engine.agents.values()}

        print(f"--- tick {tick} ---")
        print(grid.render_ascii(positions))
        for row in engine.dashboard_state():
            print(f"  {row['id']}: pos=({row['x']},{row['y']}) battery={row['battery']}% task={row['task']}")
        if result.collisions_this_tick:
            print(f"  !! naive same-cell conflicts this tick (expected -- Day 1 has no resolver yet): "
                  f"{result.collisions_this_tick}")
        print()

        if engine.all_at_goal():
            print(f"All agents reached goal at tick {tick}.")
            break

    print(f"\nTotal naive conflicts this run: {engine.total_collisions} "
          f"(this number is exactly what PIBT/ORCA, added Day 4-5, must drive to zero)")


if __name__ == "__main__":
    main()
