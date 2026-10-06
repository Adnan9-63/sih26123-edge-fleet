"""
Decentralized peer-to-peer messaging layer -- Day 3.

PS mapping: "Decentralized Communication: Inter-robot messaging to share
position and intent without a central server" + Expected Solution's
"Decentralized Network Stack: A peer-to-peer communication protocol where
robots share localization data locally."

IMPLEMENTATION CHOICE: UDP multicast, not MQTT, not a plain socket server.

Why not MQTT: MQTT requires a central broker process. Every message
passes through it. That is a single point of failure -- exactly what this
PS is asking us to remove. Using MQTT "for convenience" would technically
contradict our own architecture.

Why not ROS2/DDS here: DDS is the more "industry standard" answer (see
ARCHITECTURE.md) and is a legitimate stretch upgrade later, but it adds a
real setup cost (a full ROS2 install, and on Windows realistically a WSL2
layer) that isn't worth paying for on Day 3 under a 7-day clock. UDP
multicast gets the same core property -- no broker, no central server,
pure peer-to-peer -- with zero extra installs, on any OS, using only the
Python standard library.

How it works: every agent joins the same multicast group and port. To
broadcast, an agent sends one UDP packet to the group; every other agent
that has joined receives it directly. There is no process anywhere
relaying, queueing, or brokering that packet -- if you unplug the network
switch between two robots, they simply stop hearing each other, but
neither robot's own logic breaks, which is exactly the failure mode this
PS's Background section describes wanting to avoid.

`Peer.kill()` simulates a robot going dark (comms cut, not process
killed) -- this is what powers the resilience demo in ARCHITECTURE.md:
kill one agent's Peer mid-run and show the rest of the fleet keeps
functioning; the killed agent's last-known state simply goes stale and
gets dropped by its neighbors after STALE_AFTER seconds.
"""
from __future__ import annotations

import json
import socket
import struct
import threading
import time
from dataclasses import asdict, dataclass

MULTICAST_GROUP = "239.255.42.99"
PORT = 5007
STALE_AFTER = 2.0  # seconds -- a neighbor we haven't heard from in this long is dropped


@dataclass
class PeerState:
    agent_id: str
    x: int
    y: int
    intent_x: int | None   # next cell this agent intends to move into
    intent_y: int | None
    task_id: str | None
    battery: float
    ts: float = 0.0


class Peer:
    """One robot's link into the decentralized comms fabric. Each Agent
    owns exactly one Peer -- there is no shared or central Peer anywhere
    in the system."""

    def __init__(self, agent_id: str, group: str = MULTICAST_GROUP, port: int = PORT):
        self.agent_id = agent_id
        self.group = group
        self.port = port
        self._neighbors: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._running = False
        self._send_sock: socket.socket | None = None
        self._recv_sock: socket.socket | None = None
        self._recv_thread: threading.Thread | None = None

    def start(self) -> None:
        self._send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        self._recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._recv_sock.bind(("", self.port))
        mreq = struct.pack("4sl", socket.inet_aton(self.group), socket.INADDR_ANY)
        self._recv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self._recv_sock.settimeout(0.5)

        self._running = True
        self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._recv_thread.start()

    def _recv_loop(self) -> None:
        while self._running:
            try:
                data, _addr = self._recv_sock.recvfrom(2048)
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                msg = json.loads(data.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                continue
            if msg.get("agent_id") == self.agent_id:
                continue  # ignore our own broadcast
            with self._lock:
                self._neighbors[msg["agent_id"]] = msg

    def broadcast(self, state: PeerState, drop_rate: float = 0.0) -> None:
        """Broadcasts state to neighbors. 
        `drop_rate` simulates RF-degraded defense environments where packets randomly fail.
        """
        if not self._send_sock:
            raise RuntimeError("Peer.start() must be called before broadcast()")
            
        import random
        if drop_rate > 0.0 and random.random() < drop_rate:
            return  # Simulate packet drop (chaos engineering)
            
        state.ts = time.time()
        payload = json.dumps(asdict(state)).encode("utf-8")
        self._send_sock.sendto(payload, (self.group, self.port))

    def poll_neighbors(self) -> dict[str, dict]:
        """Returns the latest known state of every neighbor heard from
        within the last STALE_AFTER seconds. Anything older is dropped --
        this is what makes a killed/disconnected robot disappear from
        everyone else's view without any central process noticing or
        announcing it."""
        now = time.time()
        with self._lock:
            fresh = {aid: s for aid, s in self._neighbors.items() if now - s["ts"] <= STALE_AFTER}
            self._neighbors = fresh
            return dict(fresh)

    def kill(self) -> None:
        """Simulate this robot's comms going dark (network cut), not the
        whole process dying -- used for the live resilience demo."""
        self._running = False
        if self._send_sock:
            self._send_sock.close()
            self._send_sock = None
        if self._recv_sock:
            try:
                self._recv_sock.close()
            except OSError:
                pass
            self._recv_sock = None
