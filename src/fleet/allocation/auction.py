"""
Decentralized task allocation via a Contract Net Protocol style auction.

STATUS: Day 6 milestone.

PS mapping: "Task Allocation & Re-routing: Automatically re-assigning
pickup points or changing paths if one robot encounters a blocked aisle."

No dispatcher assigns tasks. When a pickup task appears, every idle agent
computes its own bid (distance to task + battery headroom) and broadcasts
it over the p2p layer; the best bidder claims the task. If an agent gets
stuck (blocked_ticks exceeds a threshold -- see Agent.blocked_ticks), it
voluntarily re-auctions its own task rather than waiting indefinitely.
This is the second, independent piece of evidence (alongside PIBT/ORCA)
that nothing here runs through a central coordinator.

TODO (Day 6):
- bid(agent, task) -> float
- run_auction(idle_agents, open_tasks) -> dict[agent_id, task_id]
- re_auction_if_blocked(agent, threshold_ticks=5)
- unit test: a blocked agent's task gets picked up by a different agent
  within N ticks, with no central dispatcher object involved anywhere in
  the call path (assert no such object exists / is imported)
"""
from __future__ import annotations


def run_auction(*args, **kwargs):
    raise NotImplementedError("Day 6: implement Contract Net style bidding here")
