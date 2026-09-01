"""
ORCA local collision avoidance, wrapping the Python-RVO2 library.

STATUS: Day 4-5 milestone.

Reference: van den Berg, Guy, Lin, Manocha, "Reciprocal n-body collision
avoidance" -- each agent computes its own collision-free velocity from a
small linear program using only the positions/velocities of nearby agents
it can locally observe. No negotiation or message exchange is required for
avoidance itself, which is what makes this a genuinely decentralized layer
rather than a coordinator computing everyone's velocity.

Install: pip install rvo2

TODO (Day 4-5):
- build_simulator(agents, neighbor_dist, time_horizon) -> rvo2.PyRVOSimulator
- step(sim, agents) -> updated continuous-space positions
- reconcile continuous-space ORCA output back onto the discrete grid PIBT
  plans on (two layers, one hybrid tick loop)
"""
from __future__ import annotations


def build_simulator(*args, **kwargs):
    raise NotImplementedError("Day 4-5: wrap rvo2.PyRVOSimulator here")
