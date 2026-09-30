"""
Multi-process distributed demo for the SIH26123 warehouse fleet project.

PS mapping: "Decentralized Communication: Inter-robot messaging to share
position and intent without a central server" + Expected Solution's
"Decentralized Network Stack: A peer-to-peer communication protocol where
robots share localization data locally."

This script demonstrates TRUE decentralized operation by spawning separate 
Python processes for each robot. They communicate solely over UDP multicast 
using the P2P module.
"""

import sys
import time
import argparse
import multiprocessing
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from fleet.comms.p2p import Peer, PeerState
from fleet.planning.astar import astar
from fleet.grid import WarehouseGrid

def robot_worker(agent_id: str, start_pos: tuple, goal_pos: tuple, kill_after: float = None):
    grid = WarehouseGrid.default()
    peer = Peer(agent_id)
    peer.start()
    
    pos = start_pos
    battery = 100.0
    start_time = time.time()
    
    print(f"[{agent_id}] Process started. Pos: {pos}, Goal: {goal_pos}")
    
    while True:
        elapsed = time.time() - start_time
        if kill_after and elapsed > kill_after:
            print(f"[{agent_id}] Killing comms to demonstrate resilience...")
            peer.kill()
            kill_after = None # Trigger once
        
        # Determine next intended cell
        path = astar(grid, pos, goal_pos)
        next_pos = path[1] if len(path) > 1 else pos
        
        # Broadcast current state and intent
        if peer._running:
            state = PeerState(
                agent_id=agent_id,
                x=pos[0],
                y=pos[1],
                intent_x=next_pos[0],
                intent_y=next_pos[1],
                task_id=None,
                battery=battery
            )
            try:
                peer.broadcast(state)
            except RuntimeError:
                pass # Comms might be killed
        
        # Poll neighbors
        neighbors = peer.poll_neighbors()
        
        # Local conflict resolution
        conflict = False
        for n_id, n_state in neighbors.items():
            n_pos = (n_state['x'], n_state['y'])
            n_intent = (n_state['intent_x'], n_state['intent_y'])
            
            # Don't step on someone's current cell
            if next_pos == n_pos:
                conflict = True
            # Tie breaker if competing for same next cell
            elif next_pos == n_intent and next_pos != pos:
                if n_id < agent_id:
                    conflict = True
                    
        if not conflict and next_pos != pos:
            pos = next_pos
            battery -= 0.1
            if pos == goal_pos:
                # Swap goals to keep moving for the demo
                goal_pos = start_pos
                start_pos = pos
                
        time.sleep(0.2)

def dashboard_worker(timeout: float):
    grid = WarehouseGrid.default()
    peer = Peer("dashboard")
    peer.start()
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        neighbors = peer.poll_neighbors()
        
        positions = {}
        for n_id, n_state in neighbors.items():
            positions[n_id] = (n_state['x'], n_state['y'])
            
        print("\033[H\033[J", end="") # Clear screen
        print(f"--- Live Fleet Dashboard ({len(neighbors)} agents visible) ---")
        print(grid.render_ascii(positions))
        for n_id, n_state in neighbors.items():
            print(f"{n_id}: pos=({n_state['x']},{n_state['y']}) intent=({n_state['intent_x']},{n_state['intent_y']}) batt={n_state['battery']:.1f}")
        
        time.sleep(0.2)
        
    print("\n[Dashboard] Demo completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--kill-robot", action="store_true", help="Kill one robot's comms mid-run")
    parser.add_argument("--duration", type=float, default=15.0, help="Demo duration in seconds")
    args = parser.parse_args()

    # Define 3 robots
    robots = [
        {"id": "R1", "start": (1, 1), "goal": (9, 7)},
        {"id": "R2", "start": (9, 1), "goal": (1, 7)},
        {"id": "R3", "start": (1, 4), "goal": (9, 4)}
    ]
    
    processes = []
    
    for i, r in enumerate(robots):
        kill_time = 5.0 if (args.kill_robot and i == 1) else None
        p = multiprocessing.Process(
            target=robot_worker, 
            args=(r["id"], r["start"], r["goal"], kill_time)
        )
        processes.append(p)
        p.start()
        
    dashboard = multiprocessing.Process(target=dashboard_worker, args=(args.duration,))
    dashboard.start()
    
    dashboard.join()
    
    for p in processes:
        p.terminate()
        p.join()
        
    print("All processes terminated.")
