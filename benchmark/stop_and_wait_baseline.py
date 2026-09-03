"""
The benchmark that actually proves the PS's Success Criteria:

    "Zero inter-robot collisions and a minimum 20% reduction in total
    task completion time compared to traditional stop-and-wait methods
    when handling overlapping paths."

Runs the SAME SimulationEngine on the SAME scenarios, twice each --
mode="naive" (a real stop-and-wait baseline, see sim/engine.py) and
mode="pibt" -- so the only variable that changes is the planner. See
ARCHITECTURE.md, "Benchmark methodology," for why that matters.

Three scenarios, deliberately including a non-contending control:

  1. no_contention   -- two agents using entirely different corridors.
     Sanity check: naive is not just generically slow, it performs
     identically to PIBT when there's nothing to negotiate.

  2. head_on_choke    -- two agents forced through the same single-width
     corridor from opposite ends. This is the exact scenario the PS
     names ("collisions at narrow intersections or choke points").

  3. three_agent_multi_choke -- the fuller scenario from the Day 1 demo,
     three agents through multiple choke points at once.

TICK_CAP exists because naive stop-and-wait can deadlock permanently
under real contention (see docs/DEV_LOG.md Day 7 entry for why -- it's a
genuine, realistic property of static-path no-negotiation baselines, not
a bug). When naive hits the cap without finishing, this is reported
honestly as DNF (did not finish), with the percentage improvement
computed as a CONSERVATIVE LOWER BOUND using the cap itself -- never
inventing a completion time that may not exist.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fleet.agent import Agent
from fleet.grid import WarehouseGrid
from fleet.sim.engine import SimulationEngine

TICK_CAP = 300


@dataclass
class RunResult:
    mode: str
    ticks: int | None  # None means DNF within TICK_CAP
    collisions: int


def _run(grid_factory, agents_factory, mode: str) -> RunResult:
    grid = grid_factory()
    agents = agents_factory()
    engine = SimulationEngine(grid, agents, mode=mode)
    for t in range(1, TICK_CAP + 1):
        engine.step()
        if engine.all_at_goal():
            return RunResult(mode=mode, ticks=t, collisions=engine.total_collisions)
    return RunResult(mode=mode, ticks=None, collisions=engine.total_collisions)


def _scenario_no_contention():
    return WarehouseGrid.default, lambda: [
        Agent(agent_id="a", pos=(1, 0), goal=(1, 8)),
        Agent(agent_id="b", pos=(8, 0), goal=(8, 8)),
    ]


def _scenario_head_on_choke():
    return WarehouseGrid.default, lambda: [
        Agent(agent_id="north", pos=(5, 0), goal=(5, 8)),
        Agent(agent_id="south", pos=(5, 8), goal=(5, 0)),
    ]


def _scenario_three_agent_multi_choke():
    return WarehouseGrid.default, lambda: [
        Agent(agent_id="agent-1", pos=(0, 0), goal=(9, 8)),
        Agent(agent_id="agent-2", pos=(9, 0), goal=(0, 8)),
        Agent(agent_id="agent-3", pos=(4, 0), goal=(4, 8)),
    ]


SCENARIOS = {
    "no_contention": _scenario_no_contention,
    "head_on_choke": _scenario_head_on_choke,
    "three_agent_multi_choke": _scenario_three_agent_multi_choke,
}


def _pct_improvement(naive: RunResult, pibt: RunResult) -> str:
    if pibt.ticks is None:
        return "N/A -- PIBT itself did not finish, investigate before claiming anything"
    naive_ticks = naive.ticks if naive.ticks is not None else TICK_CAP
    pct = 100.0 * (naive_ticks - pibt.ticks) / naive_ticks
    label = f"{pct:.1f}%"
    if naive.ticks is None:
        label += f" (CONSERVATIVE LOWER BOUND -- naive never finished within the {TICK_CAP}-tick cap, true gap may be larger or infinite)"
    return label


def main() -> None:
    lines: list[str] = []
    lines.append("# Benchmark results: stop-and-wait baseline vs PIBT\n")
    lines.append(f"Tick cap per run: {TICK_CAP}\n")

    for name, factory in SCENARIOS.items():
        grid_factory, agents_factory = factory()
        naive = _run(grid_factory, agents_factory, "naive")
        pibt = _run(grid_factory, agents_factory, "pibt")

        naive_str = f"{naive.ticks} ticks" if naive.ticks is not None else f"DNF (>{TICK_CAP} ticks)"
        pibt_str = f"{pibt.ticks} ticks" if pibt.ticks is not None else f"DNF (>{TICK_CAP} ticks)"

        block = [
            f"## {name}",
            f"- stop-and-wait: {naive_str}, {naive.collisions} collisions",
            f"- PIBT:          {pibt_str}, {pibt.collisions} collisions",
            f"- improvement:   {_pct_improvement(naive, pibt)}",
            "",
        ]
        lines.extend(block)
        print("\n".join(block))

    out_path = "docs/BENCHMARK_RESULTS.md"
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Written to {out_path}")


if __name__ == "__main__":
    main()
