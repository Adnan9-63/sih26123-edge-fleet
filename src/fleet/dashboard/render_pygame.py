"""
Lightweight fleet monitoring dashboard.

STATUS: Day 7 milestone.

PS mapping: Expected Solution -- "Fleet Dashboard: A lightweight
monitoring UI that visualizes the entire fleet's real-time positions and
battery status."

IMPORTANT (read this before wiring it in): this module is a READ-ONLY
observer. It must only ever call SimulationEngine.dashboard_state() and
draw it -- it must never call back into agent planning, comms, or
allocation. That one-directional data flow is what keeps this a passive
dashboard rather than an accidental central controller; see the
architecture diagram in ARCHITECTURE.md.

TODO (Day 7):
- pygame window, one rect per grid cell (obstacle vs free vs charging)
- one circle per agent, color-coded by battery level (green -> amber -> red)
- HUD text per agent: id, battery %, current task
- overlay: running collision count + elapsed ticks, for the live benchmark
  demo (see benchmark/stop_and_wait_baseline.py)
"""
from __future__ import annotations


def run(*args, **kwargs):
    raise NotImplementedError("Day 7: pygame render loop reading engine.dashboard_state()")
