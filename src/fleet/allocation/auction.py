"""
Decentralized task allocation via a Contract Net Protocol style auction.
Day 6.

PS mapping: "Task Allocation & Re-routing: Automatically re-assigning
pickup points or changing paths if one robot encounters a blocked
aisle."

No dispatcher object holds authority anywhere in this module. Every
function here is written as something each agent computes about itself
(its own bid) or about the currently-known task pool -- in a real
deployment this same logic runs independently on each robot's own edge
hardware, with bids exchanged over comms/p2p.py (already built, Day 3).
`run_auction` below is a pure function that resolves that same
decentralized-bidding outcome deterministically and fast, which is what
a synchronous simulation needs for testability -- it is a simulation
convenience for computing the SAME result decentralized bidding would
converge to, not a central authority making the decision. See
ARCHITECTURE.md.

Two responsibilities:

1. `run_auction` -- when a new pickup task appears, every idle agent
   bids (distance to task + a battery penalty so a low-battery agent
   isn't sent across the warehouse when a closer or fresher one is
   available); lowest bid wins.

2. `check_blocked_agents` -- "changing paths" is already handled by
   PIBT's own per-tick replanning (planning/pibt.py recomputes the best
   direction every tick, so temporary contention resolves itself). What
   PIBT can't fix is a genuinely stuck agent (e.g. blocked by a
   grid.block_cell obstacle with no way around it) -- if an agent's
   Agent.blocked_ticks exceeds RE_AUCTION_THRESHOLD while it's carrying
   a task, this releases that task back to the open pool so a
   *different*, unblocked agent can pick it up instead, rather than the
   fleet waiting indefinitely on one stuck robot.
"""
from __future__ import annotations

from dataclasses import dataclass

from fleet.agent import Agent
from fleet.grid import Cell, WarehouseGrid

RE_AUCTION_THRESHOLD = 5  # ticks of no progress before a task is released


@dataclass
class Task:
    task_id: str
    pickup_cell: Cell


def _bid(grid: WarehouseGrid, agent: Agent, task: Task, congestion_predictor=None) -> float:
    """Lower is better. True graph distance (not Manhattan -- see
    planning/pibt.py's Day 4 fix for why that distinction matters on a
    grid with walls), plus a battery penalty so a low-battery agent
    isn't preferred over a closer, fresher one for a long haul."""
    dist = grid.bfs_distances(task.pickup_cell).get(agent.pos, 10**6)
    battery_penalty = (100.0 - agent.battery) * 0.05
    
    congestion_penalty = 0.0
    if congestion_predictor is not None:
        y = task.pickup_cell[1]
        if 0 <= y <= 2:
            zone = 'north'
        elif 3 <= y <= 5:
            zone = 'central'
        else:
            zone = 'south'
            
        if isinstance(congestion_predictor, dict):
            score = congestion_predictor.get(zone, 0.0)
        else:
            # If a mock or predictor object with a score attribute/method that we don't have features for
            try:
                score = congestion_predictor.predict_congestion({zone: {}}).get(zone, 0.0)
            except:
                score = 0.0
                
        congestion_penalty = score * 50.0  # arbitrary penalty scaling
        
    return dist + battery_penalty + congestion_penalty


def run_auction(grid: WarehouseGrid, agents: dict[str, Agent], open_tasks: list[Task]) -> list[Task]:
    """Assigns as many open_tasks as possible to idle agents (agents with
    no current task_id), lowest-bid-wins. Mutates agent.task_id and
    agent.goal directly for winners. Returns the tasks that remain
    unassigned (e.g. because every agent is already busy)."""
    idle_agents = [a for a in agents.values() if a.task_id is None]
    still_open: list[Task] = []

    for task in open_tasks:
        if not idle_agents:
            still_open.append(task)
            continue

        best_agent = min(idle_agents, key=lambda a: _bid(grid, a, task))
        best_agent.task_id = task.task_id
        best_agent.goal = task.pickup_cell
        best_agent.blocked_ticks = 0
        idle_agents.remove(best_agent)

    return still_open


def check_blocked_agents(agents: dict[str, Agent], open_tasks: list[Task]) -> list[Task]:
    """Call once per tick, after engine.step(). Any agent stuck on an
    active task for too long releases it back to open_tasks (returned,
    appended to whatever the caller already has) and goes idle at its
    current position rather than continuing to wait."""
    newly_open: list[Task] = []
    for agent in agents.values():
        if agent.task_id is not None and agent.blocked_ticks >= RE_AUCTION_THRESHOLD:
            newly_open.append(Task(task_id=agent.task_id, pickup_cell=agent.goal))
            agent.task_id = None
            agent.goal = agent.pos  # idle in place until the next auction
            agent.blocked_ticks = 0
    return newly_open
