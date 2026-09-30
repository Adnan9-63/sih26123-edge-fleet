"""
Tests for Edge-AI components.
PS mapping: SIH26123
"""
from __future__ import annotations
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from fleet.edge_ai.congestion_predictor import CongestionPredictor
from fleet.edge_ai.anomaly_detector import AnomalyDetector
from fleet.allocation.auction import _bid, Task, WarehouseGrid
from fleet.agent import Agent

def test_congestion_predictor_fallback():
    # Test fallback
    predictor = CongestionPredictor()
    predictor.model = None  # Force fallback
    features = {'north': {'active_robots': 2, 'pending_tasks': 1, 'time_step': 10}}
    res = predictor.predict_congestion(features)
    assert 'north' in res
    assert res['north'] == (2 * 0.1) + (1 * 0.05)
    
def test_congestion_predictor_model():
    predictor = CongestionPredictor()
    # Train to create model
    predictor.train_model()
    predictor_new = CongestionPredictor()
    assert predictor_new.model is not None
    features = {'north': {'active_robots': 2, 'pending_tasks': 1, 'time_step': 10}}
    res = predictor_new.predict_congestion(features)
    assert 'north' in res
    assert 0.0 <= res['north'] <= 1.0

def test_anomaly_detector_fallback():
    detector = AnomalyDetector()
    detector.model = None
    telemetry = {'blocked_ticks': 11}
    assert detector.detect_anomaly(telemetry) == True
    telemetry2 = {'blocked_ticks': 5}
    assert detector.detect_anomaly(telemetry2) == False
    
def test_anomaly_detector_model():
    detector = AnomalyDetector()
    detector.train_model()
    detector_new = AnomalyDetector()
    assert detector_new.model is not None
    telemetry = {'blocked_ticks': 1, 'battery': 100, 'battery_drain_rate': 0.1, 'distance_to_goal': 5, 'movement_variance': 0.1}
    assert isinstance(detector_new.detect_anomaly(telemetry), (bool, int))

def test_auction_bid_congestion():
    class DummyGrid:
        def bfs_distances(self, cell):
            return {(0, 0): 10}
            
    grid = DummyGrid()
    agent = Agent(agent_id="A", pos=(0,0), goal=(0,0), battery=100.0)
    task_north = Task(task_id="T1", pickup_cell=(5, 1))
    
    # test backwards compatibility
    bid1 = _bid(grid, agent, task_north)
    
    # test with dictionary
    bid2 = _bid(grid, agent, task_north, congestion_predictor={'north': 0.5})
    assert bid2 > bid1
