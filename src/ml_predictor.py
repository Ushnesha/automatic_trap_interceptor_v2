"""
src/ml_predictor.py
ML predictor + ThrowDataCollector.
Same interface as original ml_predictor.py:
    MLPredictor.add_point((cx, cy))
    MLPredictor.get_predicted_landing_x() → float or None
    MLPredictor.reset()
    ThrowDataCollector.record(positions, landing_px)
    ThrowDataCollector.save()

MLPredictor falls back to Predictor (Kalman) if no model trained.
Once trained it uses scikit-learn RandomForest for faster, more
accurate predictions than raw physics.

HOW TO TRAIN:
    1. python sim_main.py --auto 500 --headless --collect-data
    2. python tools/train_model.py
    3. python sim_main.py --ml
"""

import os
import csv
import numpy as np
import time
from collections import deque


MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'predictor.pkl')
DATA_PATH  = os.path.join(os.path.dirname(__file__), '..', 'data',   'throws.csv')


class MLPredictor:
    """
    Drop-in replacement for Predictor.
    Uses scikit-learn model when trained, falls back to Kalman otherwise.
    """

    def __init__(self, settings):
        self.S       = settings
        self.history = deque(maxlen=30)
        self._last_x = None
        self.model   = None
        self._ppm_x  = settings.FRAME_WIDTH  / settings.ARENA_W
        self._ppm_z  = settings.FRAME_HEIGHT / settings.ARENA_H
        self._load_model()

    def _load_model(self):
        if not os.path.exists(MODEL_PATH):
            print("[ML] No trained model found.")
            print("[ML] Train first: python tools/train_model.py")
            print("[ML] Falling back to Kalman predictor.")
            return
        try:
            import pickle
            with open(MODEL_PATH, 'rb') as f:
                self.model = pickle.load(f)
            print(f"[ML] Model loaded: {MODEL_PATH}")
        except Exception as e:
            print(f"[ML] Failed to load model: {e}")

    def reset(self):
        self.history.clear()
        self._last_x = None

    def add_point(self, position):
        cx, cy, depth = position
        # 2. Reject noise/jumps
        if len(self.history) >= 1:
            prev = self.history[-1]
            # Check pixel jump (2D)
            pixel_dist = ((cx - prev['x'])**2 + (cy - prev['y'])**2)**0.5
            # Check depth jump (1D)
            depth_jump = abs(depth - prev['z'])
            
            # If the object jumped more than 100 pixels OR more than 0.5 meters 
            # in a single frame, it's likely sensor noise.
            if pixel_dist > 100 or depth_jump > 0.5:
                return

        # 3. Store EVERYTHING including depth (z)
        self.history.append({
            'x': cx, 
            'y': cy, 
            'z': depth, # Important for projectile math!
            't': time.time()
        })

    def get_predicted_landing_x(self):
        if len(self.history) < 3:
            return None

        # 1. Get the most recent 3 points
        p1, p2, p3 = list(self.history)[-3:]
        
        # 2. Calculate vertical velocity (Vy) using Depth and Cy
        # Note: cy is pixels, you must convert to meters first!
        dt = p3['t'] - p2['t']
        dy = self.pixels_to_meters_y(p3['y'], p3['z']) - self.pixels_to_meters_y(p2['y'], p2['z'])
        vy = dy / dt

        # 3. Solve for Time to Impact (t_impact)
        # y(t) = y_start + vy*t - 0.5*g*t^2
        current_y = self.pixels_to_meters_y(p3['y'], p3['z'])
        g = 9.81
        
        # Quadratic formula for t: (-b - sqrt(b^2 - 4ac)) / 2a
        # 0 = -0.5g*t^2 + vy*t + current_y
        discriminant = vy**2 + 2 * g * current_y
        if discriminant < 0: return None # Physics error
        
        t_impact = (vy + np.sqrt(discriminant)) / g

        # 4. Predict where X will be at that time
        dx = self.pixels_to_meters_x(p3['x'], p3['z']) - self.pixels_to_meters_x(p2['x'], p2['z'])
        vx = dx / dt
        
        predicted_x_meters = self.pixels_to_meters_x(p3['x'], p3['z']) + (vx * t_impact)
        
        # 5. Convert back to pixels for the Motor class
        return self.meters_to_pixels_x(predicted_x_meters)

    def _build_features(self):
        """10 (x,y) positions → flat feature vector of length 20."""
        points = list(self.history)[-10:]
        while len(points) < 10:
            points.insert(0, points[0])
        features = []
        for p in points:
            features.extend([p['x'], p['y']])
        return np.array(features, dtype=np.float32)

    def _kalman_fallback(self):
        """Use the Kalman predictor as a fallback."""
        if not hasattr(self, '_fallback'):
            from src.predict import Predictor
            self._fallback = Predictor(self.S)
            # Replay history into fallback
            for p in self.history:
                self._fallback.add_point((p['x'], p['y']))
        elif len(self.history) > 0:
            last = self.history[-1]
            self._fallback.add_point((last['x'], last['y']))
        result = self._fallback.get_predicted_landing_x()
        if result is not None:
            self._last_x = result
        return result

    def get_velocity(self):
        if len(self.history) < 2:
            return (0, 0)
        oldest = self.history[0]
        newest = self.history[-1]
        dt = newest['t'] - oldest['t']
        if dt <= 0:
            return (0, 0)
        return (
            (newest['x'] - oldest['x']) / dt,
            (newest['y'] - oldest['y']) / dt,
        )


class ThrowDataCollector:
    """
    Records throw data during simulation for ML training.
    Same interface as original ThrowDataCollector.

    Usage:
        collector = ThrowDataCollector()
        collector.record(position_list, actual_landing_px)
        collector.save()
    """

    def __init__(self):
        self.records = []
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
        print(f"[DATA] Collector ready → {DATA_PATH}")

    def record(self, position_history, actual_landing_x):
        """
        Save one throw.
        position_history: list of (cx, cy) tuples
        actual_landing_x: where ball actually landed in pixels
        """
        if len(position_history) < 3:
            return

        row = []
        for item in position_history[:10]:
            if isinstance(item, tuple):
                px, py = item
            else:
                px, py = item[0], item[1]
            row.extend([float(px), float(py)])

        # Pad to 20 values (10 positions × 2)
        while len(row) < 20:
            row.extend([0.0, 0.0])

        row.append(float(actual_landing_x))
        self.records.append(row)

    def save(self):
        if not self.records:
            print("[DATA] No records to save.")
            return

        headers = []
        for i in range(10):
            headers.extend([f'x{i}', f'y{i}'])
        headers.append('landing_x')

        with open(DATA_PATH, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(self.records)

        print(f"[DATA] Saved {len(self.records)} records → {DATA_PATH}")
        print("[DATA] Train now: python tools/train_model.py")
