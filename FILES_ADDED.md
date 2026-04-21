# Phase 3: Code Adaptation - Files Added to Codebase

All files for real Raspberry Pi 5 deployment have been **added to the codebase**.

## New Files Created ✅

### 1. **src/motors_real.py** — Real L298N Motor Control
- GPIO-based PWM control for Mecanum wheels
- Pins: GPIO 17, 27, 22, 23 (direction), GPIO 12, 13 (speed)
- Implements same PID algorithm as simulator but with real GPIO
- Includes strafe left/right control

**Usage:** Imported in `main_pi.py` instead of `src/sim_motors.py`

---

### 2. **src/camera_real.py** — Real Camera Capture
- Uses OpenCV (cv2) for camera capture
- Supports libcamera backend (preferred for Pi 5)
- Falls back to legacy camera interface if needed
- 640×480 @ 30fps

**Usage:** Imported in `main_pi.py` instead of `src/sim_camera.py`

---

### 3. **src/detect_real.py** — Real Object Detection
- OpenCV HSV color filtering
- Morphological operations (MORPH_CLOSE, MORPH_OPEN) to reduce noise
- Contour detection and centroid calculation
- Same HSV range as simulator (orange ball detection)
- Includes fast BGR alternative method

**Usage:** Imported in `main_pi.py` instead of `src/detect.py`

---

### 4. **main_pi.py** — Raspberry Pi 5 Entry Point
- Real hardware main loop (replaces `sim_main.py`)
- Supports same flags: `--ml`, `--collect-data`
- 30 FPS main loop
- Proper hardware cleanup on exit
- Comprehensive error handling

**Usage:** 
```bash
python3 main_pi.py                    # Kalman physics
python3 main_pi.py --ml               # ML predictor
python3 main_pi.py --collect-data     # Collect throw data
```

---

### 5. **DEPLOYMENT_GUIDE.md** — Complete Deployment Instructions
- 6 phases: Hardware assembly, Software setup, Code adaptation, Testing, Troubleshooting, Optimization
- Detailed GPIO wiring diagrams
- Step-by-step hardware tests
- Emergency stop procedures
- 50+ pages of comprehensive guidance

**Read before deploying to Pi!**

---

### 6. **HARDWARE_SWITCH.md** — Simulator ↔ Real Hardware Reference
- Quick command reference for both modes
- Import differences explained
- Development workflow
- File structure comparison
- Training data transfer procedures

**Quick lookup guide**

---

### 7. **FILES_ADDED.md** — This File
Documentation of what was added and why

---

## File Locations

```
smartbin_v4/
├── main_pi.py                  ← START HERE for Pi 5 ⭐
├── DEPLOYMENT_GUIDE.md         ← READ FIRST
├── HARDWARE_SWITCH.md          ← Quick reference
├── FILES_ADDED.md              ← This file
│
└── src/
    ├── motors_real.py          ⭐ NEW
    ├── camera_real.py          ⭐ NEW
    ├── detect_real.py          ⭐ NEW
    │
    ├── sim_motors.py           (simulator only)
    ├── sim_camera.py           (simulator only)
    ├── detect.py               (simulator fast path)
    ├── predict.py              (SHARED - both use this)
    ├── ml_predictor.py         (SHARED - both use this)
    └── logger.py               (SHARED - both use this)
```

---

## What's Shared (No Changes Needed)

These modules work for **both simulator and real hardware**:
- ✅ `src/predict.py` — Kalman filter (same physics)
- ✅ `src/ml_predictor.py` — ML training/prediction
- ✅ `tools/train_model.py` — Model training script
- ✅ `config/sim_settings.py` — Configuration (tune for Pi if needed)
- ✅ `src/logger.py` — Logging utilities

---

## What's Different

### Simulator Path (sim_main.py)
```
Camera → SimCamera (fake)
      ↓
   Frame
      ↓
Detection → Detector (fast BGR)
      ↓
Position (cx, cy)
      ↓
Prediction → Predictor/MLPredictor (same)
      ↓
Landing X
      ↓
Motors → SimMotors (direct position update)
      ↓
GUI Render
```

### Real Hardware Path (main_pi.py)
```
Camera → RealCamera (cv2 capture)
      ↓
   Frame
      ↓
Detection → RealDetector (HSV + morphology)
      ↓
Position (cx, cy)
      ↓
Prediction → Predictor/MLPredictor (same)
      ↓
Landing X
      ↓
Motors → RealMotors (GPIO PWM signals)
      ↓
No GUI (headless)
```

---

## Next Steps

### To Deploy to Pi 5:

1. **Read:** `DEPLOYMENT_GUIDE.md` (Phases 1-2: Hardware setup)
2. **Wire:** L298N + Mecanum wheels to GPIO pins
3. **Install:** Python dependencies on Pi
4. **Test:** Run hardware tests (camera, motors, detection)
5. **Run:** `python3 main_pi.py`

### To Understand Code Flow:

1. **Read:** `HARDWARE_SWITCH.md` (quick comparison)
2. **Compare:** `src/sim_motors.py` ↔ `src/motors_real.py`
3. **Compare:** `src/sim_camera.py` ↔ `src/camera_real.py`
4. **Compare:** `src/detect.py` ↔ `src/detect_real.py`

### For ML Training on Real Hardware:

```bash
# On Pi 5: collect data
python3 main_pi.py --collect-data

# Train
python3 tools/train_model.py

# Use trained model
python3 main_pi.py --ml
```

---

## Important Considerations

### 1. **GPIO Safety**
- Code in `motors_real.py` controls real motors
- **Remove wheels before testing** GPIO pins
- Use `GPIO.cleanup()` in finally block (implemented)

### 2. **Performance on Pi 5**
- Real hardware is ~3× slower than simulator
- Increased latency (50-150ms vs <20ms)
- Recommended: `MIN_POINTS_TO_PREDICT = 4` (not 2)
- ML training on real data improves accuracy

### 3. **Camera Issues**
- Pi 5 prefers libcamera backend
- Fallback to legacy interface if needed
- Requires proper CSI connection and power

### 4. **Motor Configuration**
- GPIO pins hardcoded in `motors_real.py` (lines 30-35)
- If using different pins, update these values
- PWM frequency: 1000 Hz (tunable)

---

## Testing Checklist

- [ ] Camera works: `libcamera-hello --list-cameras`
- [ ] GPIO accessible: `gpio readall`
- [ ] Python deps installed: `pip3 list`
- [ ] Camera capture works (see DEPLOYMENT_GUIDE Phase 4.1)
- [ ] Motors move (SAFETY: wheels off!)
- [ ] Detection works on real ball
- [ ] Full system runs: `python3 main_pi.py`
- [ ] Catches working

---

## Support

**Issues with real hardware?**
- Check `DEPLOYMENT_GUIDE.md` Phase 5 (Troubleshooting)
- Verify GPIO connections match `motors_real.py`
- Test camera independently
- Run motor tests with wheels removed

**Code questions?**
- Compare simulator vs real versions
- See `HARDWARE_SWITCH.md` for architecture
- Check inline code comments

