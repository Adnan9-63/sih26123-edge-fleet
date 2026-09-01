import time

from fleet.comms.p2p import Peer, PeerState


def _make_state(agent_id: str, x: int, y: int) -> PeerState:
    return PeerState(
        agent_id=agent_id, x=x, y=y, intent_x=x + 1, intent_y=y,
        task_id=None, battery=99.0,
    )


def test_peer_discovers_another_peers_broadcast():
    a = Peer("agent-1")
    b = Peer("agent-2")
    try:
        a.start()
        b.start()
        time.sleep(0.2)

        a.broadcast(_make_state("agent-1", x=1, y=1))
        time.sleep(0.3)

        seen = b.poll_neighbors()
        assert "agent-1" in seen
        assert seen["agent-1"]["x"] == 1
    finally:
        a.kill()
        b.kill()


def test_peer_ignores_its_own_broadcast():
    a = Peer("agent-1")
    try:
        a.start()
        time.sleep(0.2)
        a.broadcast(_make_state("agent-1", x=3, y=3))
        time.sleep(0.3)
        assert "agent-1" not in a.poll_neighbors()
    finally:
        a.kill()


def test_killed_peer_goes_stale_and_is_dropped():
    """This is the property the resilience demo depends on: a robot whose
    comms go dark should disappear from its neighbors' view on its own,
    with no central process announcing the disconnection."""
    a = Peer("agent-1")
    b = Peer("agent-2")
    try:
        a.start()
        b.start()
        time.sleep(0.2)

        a.broadcast(_make_state("agent-1", x=5, y=5))
        time.sleep(0.3)
        assert "agent-1" in b.poll_neighbors()

        a.kill()
        time.sleep(2.2)  # past STALE_AFTER
        assert "agent-1" not in b.poll_neighbors()
    finally:
        a.kill()
        b.kill()
