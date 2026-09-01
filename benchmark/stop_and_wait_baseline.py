"""
The benchmark that actually proves the PS's Success Criteria:

    "Zero inter-robot collisions and a minimum 20% reduction in total
    task completion time compared to traditional stop-and-wait methods
    when handling overlapping paths."

STATUS: Day 7 milestone. Depends on planning/pibt.py and
avoidance/orca.py both being implemented first.

Method (see ARCHITECTURE.md "Benchmark methodology" for the full
rationale): run the SAME SimulationEngine, on the SAME scenario
(deliberately overlapping paths through the grid's choke points), twice:

  1. Baseline: agents halt whenever their next planned cell is currently
     occupied or about to be occupied by another agent (this is the
     literal "traditional stop-and-wait" the PS names).
  2. Treatment: agents use PIBT for discrete conflict resolution and
     ORCA for continuous local avoidance instead of halting.

Report, side by side: total ticks to completion, total collisions,
percentage improvement. This script's output is what goes directly onto
the idea PPT's technical approach slide -- do not hand-wave this number,
generate it.

TODO (Day 7):
- build_overlapping_scenario() -> (grid, agents) that GUARANTEES at least
  one head-on conflict in a choke point (don't rely on random luck)
- run_stop_and_wait(grid, agents) -> ticks, collisions
- run_pibt_orca(grid, agents) -> ticks, collisions
- print a comparison table; save it to docs/BENCHMARK_RESULTS.md
"""
from __future__ import annotations


def main() -> None:
    raise NotImplementedError("Day 7: implement both runs and the comparison, see module docstring")


if __name__ == "__main__":
    main()
