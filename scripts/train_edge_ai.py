"""
Script to generate training data and train Edge-AI models for PS SIH26123.
"""
import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from fleet.edge_ai.congestion_predictor import CongestionPredictor
from fleet.edge_ai.anomaly_detector import AnomalyDetector

def main():
    print("Training CongestionPredictor...")
    CongestionPredictor.train_model()
    print("CongestionPredictor training complete and model saved.")
    
    print("Training AnomalyDetector...")
    AnomalyDetector.train_model()
    print("AnomalyDetector training complete and model saved.")
    
if __name__ == "__main__":
    main()
