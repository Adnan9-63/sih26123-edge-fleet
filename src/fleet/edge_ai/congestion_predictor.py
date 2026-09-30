"""
Congestion predictor using XGBoost for Edge-AI based fleet coordination.
PS mapping: SIH26123
"""
from __future__ import annotations
import os
import random
from pathlib import Path

try:
    import pandas as pd
    import xgboost as xgb
    import joblib
except ImportError:
    pd = None
    xgb = None
    joblib = None

MODEL_PATH = Path(__file__).resolve().parent / "models" / "congestion_model.joblib"

class CongestionPredictor:
    """
    Predicts aisle congestion using XGBoost for PS SIH26123.
    """
    def __init__(self):
        self.model = None
        if MODEL_PATH.exists() and joblib is not None:
            self.model = joblib.load(MODEL_PATH)
            
    def predict_congestion(self, zone_features: dict) -> dict[str, float]:
        """
        Predicts a congestion score (0.0 to 1.0) for each zone.
        zone_features takes the format:
        {
            'north': {'active_robots': 2, 'pending_tasks': 1, 'time_step': 10},
            'central': ...
        }
        """
        results = {}
        for zone, features in zone_features.items():
            if self.model is not None and pd is not None:
                # Use trained model
                df = pd.DataFrame([features])
                # Ensure correct column order
                df = df[['active_robots', 'pending_tasks', 'time_step']]
                score = float(self.model.predict(df)[0])
                results[zone] = max(0.0, min(1.0, score))
            else:
                # Fallback heuristic
                score = (features.get('active_robots', 0) * 0.1) + (features.get('pending_tasks', 0) * 0.05)
                results[zone] = max(0.0, min(1.0, score))
        return results
        
    @staticmethod
    def generate_training_data(num_samples: int = 1000):
        """Generates synthetic training data for congestion prediction (PS SIH26123)."""
        import pandas as pd
        data = []
        for _ in range(num_samples):
            active_robots = random.randint(0, 10)
            pending_tasks = random.randint(0, 5)
            time_step = random.randint(0, 1000)
            # Synthetic target
            congestion = (active_robots * 0.1) + (pending_tasks * 0.05) + random.uniform(-0.05, 0.05)
            congestion = max(0.0, min(1.0, congestion))
            data.append({
                'active_robots': active_robots,
                'pending_tasks': pending_tasks,
                'time_step': time_step,
                'target': congestion
            })
        return pd.DataFrame(data)
        
    @staticmethod
    def train_model():
        """Trains the XGBoost model for congestion prediction and saves using joblib (PS SIH26123)."""
        if pd is None or xgb is None or joblib is None:
            raise ImportError("Required libraries for training are not installed.")
        
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        df = CongestionPredictor.generate_training_data()
        X = df[['active_robots', 'pending_tasks', 'time_step']]
        y = df['target']
        model = xgb.XGBRegressor(n_estimators=50, max_depth=3, random_state=42)
        model.fit(X, y)
        joblib.dump(model, MODEL_PATH)
