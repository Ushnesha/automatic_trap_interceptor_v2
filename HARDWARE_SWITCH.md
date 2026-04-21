# Switching Between Simulator & Real Hardware

## Quick Reference

### Simulator (Development)
```bash
# Simulator with GUI
python sim_main.py

# Simulator headless (fast)
python sim_main.py --auto 100 --headless

# Collect training data (simulator)
python sim_main.py --auto 500 --headless --collect-data

# Train ML model
python tools/train_model.py

# Test ML on simulator
python sim_main.py --ml
```

**Files used:**
- `src/sim_world.py` — Physics engine
- `src/sim_camera.py` — Simulated camera
- `src/sim_motors.py` — Simulated motors
- `src/sim_renderer.py` — Pygame GUI

---

### Real Hardware (Pi 5)
```bash
# Real hardware with Kalman physics
python3 main_pi.py

# Real hardware with ML predictor
python3 main_pi.py --ml

# Collect data from real throws
python3 main_pi.py --collect-data

# Collect + train on real hardware
python3 main_pi.py --collect-data
python3 tools/train_model.py
python3 main_pi.py --ml
```

**Files used:**
- `src/camera_real.py` — Real camera capture
- `src/motors_real.py` — L298N GPIO control
- `src/detect_real.py` — OpenCV detection
- `src/predict.py` — Kalman filter (same as simulator)

---

## Import Differences

### Simulator Entry Point (sim_main.py)
```python
from src.sim_camera import SimCamera
from src.sim_motors import SimMotors
from src.sim_world import SimWorld
```

### Real Hardware Entry Point (main_pi.py)
```python
from src.camera_real import RealCamera
from src.motors_real import RealMotors
from src.detect_real import RealDetector
```

---

## Module Comparison

| Feature | Simulator | Real Hardware |
|---------|-----------|---------------|
| **Camera** | `SimCamera` (fake) | `RealCamera` (cv2) |
| **Motors** | `SimMotors` (direct) | `RealMotors` (GPIO PWM) |
| **Detection** | `Detector` (fast BGR) | `RealDetector` (HSV + morphology) |
| **Physics** | `SimWorld` (accurate) | N/A (real physics) |
| **Prediction** | `Predictor` or `MLPredictor` | `Predictor` or `MLPredictor` |
| **Entry** | `sim_main.py` | `main_pi.py` |
| **GUI** | Pygame (optional) | None (headless) |

---

## Configuration

Both use same settings: `config/sim_settings.py`

For real hardware, recommended changes:
```python
# config/sim_settings.py
MIN_POINTS_TO_PREDICT = 4  # Increase from 2 (real hardware is slower)
KALMAN_Q = 0.1             # Increase (real camera noisier)
KALMAN_R = 0.01            # Increase (real measurements less precise)
```

---

## Training Data Transfer

Transfer trained ML model between systems:

```bash
# On simulator: train model
python sim_main.py --auto 500 --headless --collect-data
python tools/train_model.py

# Files created:
# - models/predictor.pkl
# - data/throws.csv

# On Pi 5: copy these files
scp -r models/ pi@raspberrypi:~/smartbin_v4/
scp -r data/ pi@raspberrypi:~/smartbin_v4/

# On Pi 5: use trained model
python3 main_pi.py --ml
```

---

## Development Workflow

### Step 1: Develop & Test on Simulator
```bash
# Fast iteration on desktop
python sim_main.py --auto 20

# Train ML model
python sim_main.py --auto 500 --headless --collect-data
python tools/train_model.py

# Benchmark
python sim_main.py --ml --auto 100 --headless
```

### Step 2: Deploy to Pi 5
```bash
# Copy codebase
scp -r smartbin_v4/ pi@raspberrypi:~/

# On Pi 5:
python3 main_pi.py

# Or with pre-trained model
python3 main_pi.py --ml
```

### Step 3: Fine-Tune on Real Hardware
```bash
# On Pi 5: collect real data
python3 main_pi.py --collect-data

# Train on real data (better generalization)
python3 tools/train_model.py

# Test with real-trained model
python3 main_pi.py --ml
```

---

## File Structure

```
smartbin_v4/
├── sim_main.py              ← Simulator entry
├── main_pi.py               ← Real hardware entry ⭐ NEW
│
├── src/
│   ├── sim_world.py         (simulator only)
│   ├── sim_camera.py        (simulator only)
│   ├── sim_motors.py        (simulator only)
│   ├── sim_renderer.py      (simulator only)
│   │
│   ├── camera_real.py       ⭐ NEW (real hardware)
│   ├── motors_real.py       ⭐ NEW (real hardware)
│   ├── detect_real.py       ⭐ NEW (real hardware)
│   │
│   ├── detect.py            (shared - simulator fast path)
│   ├── predict.py           (shared - Kalman filter)
│   ├── ml_predictor.py      (shared - ML training)
│   └── logger.py            (shared - logging)
│
├── config/
│   └── sim_settings.py      (shared - settings)
│
├── tools/
│   └── train_model.py       (shared - ML training)
│
├── data/
│   └── throws.csv           (generated - training data)
│
├── models/
│   └── predictor.pkl        (generated - trained model)
│
├── README.md
├── DEPLOYMENT_GUIDE.md
└── HARDWARE_SWITCH.md       ⭐ NEW (this file)
```

---

## Debugging Tips

### Simulator Issues
```bash
# Check Python/dependencies
python --version
pip list | grep pygame

# Run with debug output
python sim_main.py --auto 5 2>&1 | grep ERROR
```

### Real Hardware Issues
```bash
# Test camera
python3 -c "import cv2; cap = cv2.VideoCapture(0); ret, f = cap.read(); print(f.shape if ret else 'FAIL')"

# Test GPIO
python3 -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); GPIO.setup(17, GPIO.OUT); GPIO.output(17, 1); print('GPIO OK')"

# Test with debug
python3 main_pi.py 2>&1 | grep -i error
```

---

## Common Issues

| Issue | Simulator | Real Hardware |
|-------|-----------|---------------|
| Slow FPS | Increase resolution, disable GUI | Reduce frame processing overhead |
| Low catch rate | Tune PID gains | Collect real training data |
| Camera fails | Not applicable | Check CSI connection, libcamera |
| Motors not moving | Check SimWorld state | Check GPIO, L298N power |

---

## Performance Targets

### Simulator
- FPS: 60 (GUI), unlimited (headless)
- Catch rate: 85-95% (physics-only or ML)
- Latency: <20ms per frame

### Real Hardware (Pi 5)
- FPS: 25-30 (depends on camera processing)
- Catch rate: 60-80% initially, 85%+ with ML training
- Latency: 50-150ms per frame (camera + processing)

