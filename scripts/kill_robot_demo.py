"""
Resilience demo for the SIH26123 warehouse fleet project.

PS mapping: "Decentralized Communication: Inter-robot messaging to share
position and intent without a central server" & "Resilience".
Shows that the P2P network survives a robot going offline without any central
coordinator noticing or managing the failure.
"""

import sys
import time
import multiprocessing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from fleet.comms.p2p import Peer, PeerState
from fleet.planning.astar import astar
from fleet.grid import WarehouseGrid

def robot_worker(agent_id: str, start_pos: tuple, goal_pos: tuple, kill_after: float):
    grid = WarehouseGrid.default()
    peer = Peer(agent_id)
    peer.start()
    
    pos = start_pos
    start_time = time.time()
    
    print(f"[{agent_id}] Started.")
    
    while True:
        if kill_after and (time.time() - start_time) > kill_after:
            print(f"\n[{agent_id}] --> COMMS CUT <--")
            peer.kill()
            kill_after = None
            
        path = astar(grid, pos, goal_pos)
        next_pos = path[1] if len(path) > 1 else pos
        
        if peer._running:
            state = PeerState(
                agent_id=agent_id,
                x=pos[0], y=pos[1],
                intent_x=next_pos[0], intent_y=next_pos[1],
                task_id=None, battery=100.0
            )
            peer.broadcast(state)
            
        time.sleep(0.2)

def monitor_worker():
    peer = Peer("monitor")
    peer.start()
    
    print("[Monitor] Watching network for 10 seconds...")
    start_time = time.time()
    while time.time() - start_time < 10.0:
        neighbors = peer.poll_neighbors()
        visible = sorted(list(neighbors.keys()))
        print(f"[Monitor] visible agents: {visible}")
        time.sleep(1.0)
        
if __name__ == "__main__":
    p1 = multiprocessing.Process(target=robot_worker, args=("R1", (1, 1), (9, 1), None))
    p2 = multiprocessing.Process(target=robot_worker, args=("R2", (5, 5), (5, 5), 5.0))
    p3 = multiprocessing.Process(target=robot_worker, args=("R3", (1, 7), (9, 7), None))
    
    p1.start()
    p2.start()
    p3.start()
    
    monitor = multiprocessing.Process(target=monitor_worker)
    monitor.start()
    monitor.join()
    
    p1.terminate()
    p2.terminate()
    p3.terminate()
    print("Demo complete.")
