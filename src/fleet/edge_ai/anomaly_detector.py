"""
Anomaly detector using Isolation Forest for Edge-AI based fleet coordination.
PS mapping: SIH26123
"""
from __future__ import annotations
import random
from pathlib import Path

try:
    import pandas as pd
    from sklearn.ensemble import IsolationForest
    import joblib
except ImportError:
    pd = None
    IsolationForest = None
    joblib = None

MODEL_PATH = Path(__file__).resolve().parent / "models" / "anomaly_model.joblib"

class AnomalyDetector:
    """
    Detects anomalies in robot health using Isolation Forest for PS SIH26123.
    """
    def __init__(self):
        self.model = None
        if MODEL_PATH.exists() and joblib is not None:
            self.model = joblib.load(MODEL_PATH)
            
    def detect_anomaly(self, robot_telemetry: dict) -> bool:
        """
        Flags robots as anomalous (True) or normal (False) based on telemetry.
        Telemetry includes: blocked_ticks, battery, battery_drain_rate, distance_to_goal, movement_variance.
        """
        if self.model is not None and pd is not None:
            df = pd.DataFrame([robot_telemetry])
            features = ['blocked_ticks', 'battery', 'battery_drain_rate', 'distance_to_goal', 'movement_variance']
            # Fill missing keys with sensible defaults just in case
            for f in features:
                if f not in df.columns:
                    df[f] = 0
            df = df[features]
            prediction = self.model.predict(df)[0]
            # IsolationForest returns -1 for anomaly, 1 for normal
            return bool(prediction == -1)
        else:
            # Fallback heuristic
            return bool(robot_telemetry.get('blocked_ticks', 0) >= 10)
            
    @staticmethod
    def generate_training_data(num_samples: int = 1000):
        """Generates synthetic normal operation data for anomaly detection (PS SIH26123)."""
        import pandas as pd
        data = []
        for _ in range(num_samples):
            # Mostly normal operation
            blocked_ticks = random.randint(0, 3)
            battery = random.uniform(20, 100)
            battery_drain_rate = random.uniform(0.1, 0.5)
            distance_to_goal = random.randint(0, 20)
            movement_variance = random.uniform(0, 1.0)
            
            data.append({
                'blocked_ticks': blocked_ticks,
                'battery': battery,
                'battery_drain_rate': battery_drain_rate,
                'distance_to_goal': distance_to_goal,
                'movement_variance': movement_variance
            })
        return pd.DataFrame(data)
        
    @staticmethod
    def train_model():
        """Trains the Isolation Forest model and saves it using joblib (PS SIH26123)."""
        if pd is None or IsolationForest is None or joblib is None:
            raise ImportError("Required libraries for training are not installed.")
            
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        df = AnomalyDetector.generate_training_data()
        X = df[['blocked_ticks', 'battery', 'battery_drain_rate', 'distance_to_goal', 'movement_variance']]
        
        model = IsolationForest(contamination=0.05, random_state=42)
        model.fit(X)
        joblib.dump(model, MODEL_PATH)
