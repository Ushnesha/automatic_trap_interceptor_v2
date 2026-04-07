# SmartBin: Autonomous Interceptor Trash Can

An AI-powered robot that catches thrown objects using real-time computer vision, predictive physics, and machine learning.

## Overview

SmartBin is a Raspberry Pi 4-based system that detects incoming projectiles via camera, predicts their landing position using Kalman filtering + ballistic physics (or ML), and moves a trash can underneath using PID-controlled Mecanum wheels.

**Hardware:**
- Raspberry Pi 4
- Pi Camera v2
- L298N Motor Driver
- Mecanum Wheels Chassis
- Orange ball (detection target)

---

## Quick Start

### Installation
```bash
pip install pygame numpy
pip install scikit-learn   # For ML training only
```

### Run Simulator (Manual Mode)
```bash
python sim_main.py
```
Controls: **SPACE** = throw | **R** = reset | **A** = auto×500 | **Q** = quit

### Run with Physics Predictor (Auto Mode)
```bash
python sim_main.py --auto 20
```
Automatically throws 20 objects and reports catch score.

---

## Features

### 1. Real-Time Vision Detection
- HSV-based orange ball detection
- Fast centroid computation using numpy
- Noise filtering by minimum blob area
- **File:** `src/detect.py`

### 2. Prediction System (Dual Mode)

#### Physics + Kalman Filter (Default)
- Kalman filter smooths noisy camera detections
- Tracks: position (x, z), velocity (vx, vz)
- Solves ballistic equations with gravity (9.81 m/s²)
- Works from **frame 2** (minimal latency)
- **File:** `src/predict.py`

#### Machine Learning (Optional)
- RandomForest or GradientBoosting regressor
- Learns from 500+ collected throws
- Input: last 10 (x, y) positions → predicts landing X
- Automatically falls back to Kalman if insufficient data
- **File:** `src/ml_predictor.py`

### 3. Motor Control
- PID controller for smooth movement
- Mecanum wheels for omnidirectional motion
- Acceleration limits prevent overshooting
- **File:** `src/sim_motors.py`

### 4. Data Collection & Training
- Collect throw trajectories during simulation
- Train ML model on collected data
- Automatic model selection (best validation accuracy)
- **Files:** `src/ml_predictor.py`, `tools/train_model.py`

---

## Usage

### Headless Mode (Faster, No GUI)
```bash
python sim_main.py --headless
```

### Slow Motion
```bash
python sim_main.py --slow
```

### Auto-Throw with Options
```bash
# Throw 20 objects
python sim_main.py --auto 20

# Throw 500 in headless mode
python sim_main.py --auto 500 --headless

# Throw 500 and collect training data
python sim_main.py --auto 500 --headless --collect-data
```

### Use ML Predictor
```bash
# First, collect and train (see ML Workflow below)
python sim_main.py --ml

# Benchmark ML accuracy
python sim_main.py --ml --auto 100 --headless
```

---

## ML Workflow

### Step 1: Collect Training Data
```bash
python sim_main.py --auto 500 --headless --collect-data
```
- Runs 500 automatic throws
- Records (x, y) positions and landing X for each throw
- Saves to `data/throws.csv`
- Takes ~2-3 minutes

### Step 2: Train the Model
```bash
python tools/train_model.py
```
- Loads data from `data/throws.csv`
- Tries RandomForest and GradientBoosting
- Evaluates on 15% validation set
- Saves best model to `models/predictor.pkl`
- Prints Mean Absolute Error (MAE) in pixels

### Step 3: Run with ML
```bash
python sim_main.py --ml
```
- Loads trained model automatically
- Uses ML predictions instead of physics
- Falls back to Kalman if model unavailable

### Step 4: Benchmark
```bash
# Test with ML
python sim_main.py --ml --auto 100 --headless

# Compare vs physics-only
python sim_main.py --auto 100 --headless
```

---

## Architecture

### Pipeline (Sense → Detect → Predict → Act)

```
1. SENSE
   └─ Camera captures frame of flying object

2. DETECT
   └─ Orange ball centroid via HSV + blob detection

3. PREDICT
   ├─ Kalman Filter (smooths noisy detections)
   ├─ Build physics model (velocity, gravity)
   └─ Solve ballistic equation OR use ML model

4. ACT
   └─ PID controller moves can to predicted X
```

### File Structure
```
smartbin_v4/
├── sim_main.py              # Entry point
├── config/
│   └── sim_settings.py      # All hardware constants
├── src/
│   ├── sim_world.py         # Physics engine
│   ├── sim_camera.py        # Camera simulator
│   ├── sim_motors.py        # Motor PID controller
│   ├── detect.py            # Orange ball detection
│   ├── predict.py           # Kalman + ballistic solver
│   ├── ml_predictor.py      # ML fallback + data collector
│   ├── sim_renderer.py      # Pygame GUI
│   └── logger.py            # Logging utilities
├── tools/
│   └── train_model.py       # ML model training script
├── data/
│   └── throws.csv           # Collected training data
├── models/
│   └── predictor.pkl        # Trained ML model
└── README.md
```

---

## Configuration

All constants in `config/sim_settings.py`:

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `ARENA_W`, `ARENA_H` | 3.0, 2.5 m | Real-world arena size |
| `FRAME_WIDTH`, `FRAME_HEIGHT` | 640, 480 px | Camera resolution |
| `GRAVITY` | 9.81 m/s² | Ballistic physics |
| `KALMAN_Q`, `KALMAN_R` | 0.05, 0.004 | Filter noise tuning |
| `PID_KP`, `PID_KI`, `PID_KD` | 7.0, 0.1, 1.0 | Motor control gains |
| `CAN_MAX_SPEED` | 4.5 m/s | Motor speed limit |
| `POSITION_TOL` | 0.04 m | Dead zone for stopping |
| `HSV_LOWER`, `HSV_UPPER` | (3,70,70), (30,255,255) | Orange detection range |

---

## Accuracy & Performance

### Physics-Only (Kalman)
- **Accuracy:** ~85-90% catch rate (depends on physics tuning)
- **Latency:** Minimal (prediction from frame 2)
- **Training:** None required
- **Speed:** Very fast predictions

### ML Mode
- **Accuracy:** ~92-95% catch rate (learns simulator quirks)
- **Latency:** Slightly higher (feature extraction)
- **Training:** Requires 50-500+ throws
- **Speed:** Fast for inference, moderate for training

### Why ML Helps
- Learns camera detection biases
- Adapts to simulator imperfections
- Captures real-world physics on actual Pi hardware
- Ideal for deployment with specific camera calibration

---

## Command Reference

| Command | Purpose |
|---------|---------|
| `python sim_main.py` | GUI, manual throw (SPACE key) |
| `python sim_main.py --headless` | No window, manual throw |
| `python sim_main.py --slow` | 50ms delay per frame |
| `python sim_main.py --auto N` | Auto-throw N objects |
| `python sim_main.py --ml` | Use ML predictor |
| `python sim_main.py --collect-data` | Save throw data to CSV |
| `python sim_main.py --auto 500 --headless --collect-data` | Collect training data fast |
| `python tools/train_model.py` | Train ML model on collected data |

---

## Troubleshooting

### No trained model found
```
[ML] No trained model found.
[ML] Train first: python tools/train_model.py
```
→ Collect data and train: `python sim_main.py --auto 500 --headless --collect-data` then `python tools/train_model.py`

### Only 10 samples, need 50+
→ Collect more: `python sim_main.py --auto 200 --headless --collect-data`

### Camera returns None
→ Check frame is being captured in `src/sim_camera.py`. On real Pi, replace with cv2 code.

### Low catch rate
→ Tune PID gains in `config/sim_settings.py` (KP, KI, KD)
→ Adjust Kalman noise (KALMAN_Q, KALMAN_R)
→ Collect more training data for ML mode

---

## Real Hardware Deployment

To run on actual Raspberry Pi 4:

1. **Replace camera module:**
   - `src/sim_camera.py` → Use `cv2.VideoCapture(0)` + real frame capture

2. **Replace motor control:**
   - `src/sim_motors.py` → Use GPIO PWM signals to L298N driver

3. **Replace detection:**
   - `src/detect.py` → Use real `cv2.inRange()`, `cv2.findContours()`

4. **Collect real data:**
   ```bash
   python sim_main.py --auto 500 --collect-data
   ```
   (data will be more accurate with real camera)

5. **Retrain model:**
   ```bash
   python tools/train_model.py
   ```

6. **Deploy:**
   ```bash
   python sim_main.py --ml
   ```

---

## Dependencies

```
pygame          # Simulator GUI
numpy           # Numerical computing
scikit-learn    # ML training (optional)
opencv-python   # Real Pi deployment (optional)
```

Install all:
```bash
pip install pygame numpy scikit-learn opencv-python
```

---

## Author Notes

- **Simulator accuracy:** Matches real physics (gravity, drag, bounce)
- **Kalman filter:** Robust to camera noise, works immediately
- **ML mode:** Learns specific hardware quirks and improves accuracy
- **PID control:** Smooth, responsive motor movement with limits
- **Modular design:** Easy to swap components for real hardware

---

## License & Attribution

SmartBin v4 — Robotics AI Project, Semester 2

