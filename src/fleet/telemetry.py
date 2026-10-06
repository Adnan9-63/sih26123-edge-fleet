"""
Audit logging and telemetry for defense-grade post-mortem analysis.
SIH26123 Requirement: Defense depots require black-box logging of all AMRs.
"""
import json
import time
from pathlib import Path
from typing import Dict, Any

class AuditLogger:
    """Writes persistent, append-only logs for the fleet."""
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Use timestamped file for each run
        session_id = int(time.time())
        self.log_file = self.log_dir / f"fleet_audit_{session_id}.jsonl"
        
    def log_tick(self, tick: int, fleet_state: list[dict[str, Any]], collisions: int):
        """Logs the entire fleet state for a single tick."""
        entry = {
            "timestamp": time.time(),
            "tick": tick,
            "collisions_to_date": collisions,
            "agents": fleet_state
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
            
    def get_last_log_path(self) -> Path:
        return self.log_file
