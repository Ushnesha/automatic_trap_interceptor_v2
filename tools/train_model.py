"""
tools/train_model.py — Train the ML predictor
===============================================
Run AFTER collecting data with --collect-data flag.

STEPS:
    1. Collect data (500+ throws):
       python sim_main.py --auto 500 --headless --collect-data

    2. Train the model:
       python tools/train_model.py

    3. Run with ML predictor:
       python sim_main.py --ml

    4. Benchmark ML vs physics:
       python sim_main.py --ml --auto 100
       python sim_main.py --auto 100

INSTALL:
    pip install scikit-learn numpy
"""

import os
import sys
import csv
import pickle
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

DATA_PATH  = os.path.join(os.path.dirname(__file__), '..', 'data',   'throws.csv')
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'predictor.pkl')


def load_data():
    if not os.path.exists(DATA_PATH):
        print(f"[TRAIN] No data found at {DATA_PATH}")
        print("[TRAIN] Collect data first:")
        print("  python sim_main.py --auto 500 --headless --collect-data")
        return None, None

    X, y = [], []
    with open(DATA_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            features = []
            for i in range(10):
                features.extend([float(row[f'x{i}']), float(row[f'y{i}'])])
            X.append(features)
            y.append(float(row['landing_x']))

    print(f"[TRAIN] Loaded {len(X)} samples from {DATA_PATH}")
    return np.array(X), np.array(y)


def train():
    print("=" * 54)
    print("  SmartBin ML Predictor — Training")
    print("=" * 54)

    try:
        from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_absolute_error
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
    except ImportError:
        print("[TRAIN] scikit-learn not installed.")
        print("[TRAIN] Run: pip install scikit-learn")
        return

    X, y = load_data()
    if X is None:
        return

    if len(X) < 50:
        print(f"[TRAIN] Only {len(X)} samples — need 50+ for good results.")
        print("[TRAIN] Collect more: python sim_main.py --auto 200 --headless --collect-data")
        return

    # Split train/val
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.15, random_state=42
    )
    print(f"[TRAIN] Train: {len(X_train)}  Val: {len(X_val)}")

    # Try two models, pick the better one
    models = {
        'RandomForest': Pipeline([
            ('scaler', StandardScaler()),
            ('model',  RandomForestRegressor(
                n_estimators=200,
                max_depth=12,
                min_samples_leaf=2,
                n_jobs=-1,
                random_state=42,
            ))
        ]),
        'GradientBoosting': Pipeline([
            ('scaler', StandardScaler()),
            ('model',  GradientBoostingRegressor(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.05,
                random_state=42,
            ))
        ]),
    }

    best_model = None
    best_err   = float('inf')
    best_name  = ''

    for name, model in models.items():
        print(f"\n[TRAIN] Training {name}...")
        model.fit(X_train, y_train)
        pred    = model.predict(X_val)
        mae_px  = mean_absolute_error(y_val, pred)
        print(f"[TRAIN] {name} MAE = {mae_px:.1f} pixels")
        if mae_px < best_err:
            best_err   = mae_px
            best_model = model
            best_name  = name

    print(f"\n[TRAIN] Best model: {best_name}  (MAE = {best_err:.1f} px)")

    # Save
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(best_model, f)

    print(f"[TRAIN] Model saved → {MODEL_PATH}")
    print(f"[TRAIN] Run with ML: python sim_main.py --ml")
    print(f"[TRAIN] Benchmark:   python sim_main.py --ml --auto 100 --headless")


if __name__ == '__main__':
    train()
