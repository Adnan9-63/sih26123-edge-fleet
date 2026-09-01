"""
Decentralized peer-to-peer messaging layer.

STATUS: Day 3 milestone.

PS mapping: "Decentralized Communication: Inter-robot messaging to share
position and intent without a central server" + Expected Solution's
"Decentralized Network Stack: A peer-to-peer communication protocol where
robots share localization data locally."

Two target backends, same interface below, so the rest of the codebase
never cares which one is running underneath:

1. ROS2 + DDS (preferred): genuinely broker-free peer discovery -- unlike
   MQTT, which requires a central broker and would reintroduce the single
   point of failure this PS explicitly asks us to remove.
2. Fallback if the team isn't fluent in ROS2 under time pressure: raw UDP
   multicast between independent processes. Still broker-free, just more
   manual -- do NOT substitute MQTT as a shortcut here.

TODO (Day 3):
- Peer.broadcast(position, velocity_intent, task_id) -- fire-and-forget,
  no acknowledgement required (matches "share ... locally", not "commit
  ... globally")
- Peer.poll_neighbors() -> dict[agent_id, LastKnownState]
- a `kill()` method that simulates a dropped robot -- used for the
  resilience demo (fleet keeps functioning when one agent goes dark)
"""
from __future__ import annotations

from dataclasses import dataclass

from fleet.grid import Cell


@dataclass
class PeerState:
    agent_id: str
    pos: Cell
    intent_cell: Cell | None
    task_id: str | None
    battery: float


class Peer:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    def broadcast(self, state: PeerState) -> None:
        raise NotImplementedError("Day 3: publish over ROS2/DDS topic (or UDP multicast fallback)")

    def poll_neighbors(self) -> dict[str, PeerState]:
        raise NotImplementedError("Day 3: subscribe / read latest peer states")
