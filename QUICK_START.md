# Quick Start: SmartBin on Raspberry Pi 5

## ⚡ 30-Second Overview

You now have **two complete deployment options**:

### 🖥️ Simulator (Development on Desktop)
```bash
python sim_main.py --auto 100 --headless
```
Fast development, visual debugging, perfect physics.

### 🤖 Real Hardware (Pi 5 + Camera + Motors)
```bash
python3 main_pi.py
```
Real-world testing, learns actual hardware characteristics.

---

## 📋 Checklist: Is Code Ready for Pi 5?

✅ **Phase 3 Complete:** All real hardware code files added
- `main_pi.py` — Real hardware entry point
- `src/motors_real.py` — GPIO + PWM control
- `src/camera_real.py` — OpenCV camera capture
- `src/detect_real.py` — HSV detection with morphology

✅ **Documentation Complete:**
- `DEPLOYMENT_GUIDE.md` — 50+ pages, 6 phases
- `HARDWARE_SWITCH.md` — Simulator vs real hardware comparison
- `FILES_ADDED.md` — What was added and why

✅ **Shared Code (No Changes):**
- `src/predict.py` — Kalman filter (works for both)
- `src/ml_predictor.py` — ML training (works for both)
- `config/sim_settings.py` — Configuration (tune for Pi if needed)

---

## 🚀 Next Steps to Deploy on Pi 5

### Step 1: Physical Hardware (1-2 hours)
Follow `DEPLOYMENT_GUIDE.md` **Phase 1:**
- Plug camera into CSI port
- Wire L298N to GPIO pins (17, 27, 22, 23, 12, 13)
- Connect motors to L298N outputs
- Assemble Mecanum wheels

### Step 2: Software Setup (30 minutes)
Follow `DEPLOYMENT_GUIDE.md` **Phase 2:**
```bash
# On Pi 5:
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip git
pip3 install opencv-python numpy RPi.GPIO scikit-learn

git clone <your-repo> smartbin_v4
cd smartbin_v4
```

### Step 3: Testing (30 minutes)
Follow `DEPLOYMENT_GUIDE.md` **Phase 4:**
```bash
# Test camera
libcamera-hello --list-cameras

# Test motors (WHEELS OFF!)
python3 << 'EOF'
import RPi.GPIO as GPIO
# Test code from DEPLOYMENT_GUIDE.md Phase 4.2
EOF

# Test detection
python3 tools/test_detection.py

# Full system
python3 main_pi.py
```

### Step 4: Optimization (Optional)
Follow `DEPLOYMENT_GUIDE.md` **Phase 6:**
```bash
# Collect real data
python3 main_pi.py --collect-data

# Train on real hardware
python3 tools/train_model.py

# Use trained model
python3 main_pi.py --ml
```

---

## 📁 Code Organization

### Simulator (unchanged)
```
sim_main.py              ← Run this for desktop testing
├── src/sim_world.py     (physics engine)
├── src/sim_camera.py    (fake camera)
├── src/sim_motors.py    (simulated motors)
└── src/sim_renderer.py  (Pygame GUI)
```

### Real Hardware (⭐ NEW)
```
main_pi.py               ← Run this on Pi 5 ⭐
├── src/camera_real.py   (OpenCV camera) ⭐
├── src/motors_real.py   (GPIO + PWM) ⭐
└── src/detect_real.py   (HSV detection) ⭐
```

### Shared (Both Use)
```
src/predict.py          (Kalman filter)
src/ml_predictor.py     (ML training)
tools/train_model.py    (Training script)
config/sim_settings.py  (Configuration)
```

---

## 🔧 GPIO Pinout

| Function | GPIO Pin |
|----------|----------|
| Motor A Dir 1 | GPIO 17 |
| Motor A Dir 2 | GPIO 27 |
| Motor B Dir 1 | GPIO 22 |
| Motor B Dir 2 | GPIO 23 |
| Motor A Speed (PWM) | GPIO 12 |
| Motor B Speed (PWM) | GPIO 13 |

**See** `DEPLOYMENT_GUIDE.md` **Step 1.2** for detailed wiring.

---

## 🎯 Expected Performance

### Simulator
- FPS: 60 (GUI), unlimited (headless)
- Catch rate: 85-95%
- Latency: <20ms

### Real Hardware (Pi 5)
- FPS: 25-30
- Catch rate: 60-80% (initially), 85%+ (with ML)
- Latency: 50-150ms

⚠️ **Real hardware is slower** — recommended to increase `MIN_POINTS_TO_PREDICT` from 2 to 4.

---

## 📖 Documentation Map

| Document | Purpose | Read When |
|----------|---------|-----------|
| **README.md** | Project overview | First time |
| **DEPLOYMENT_GUIDE.md** | Complete deployment instructions | Before deploying to Pi |
| **HARDWARE_SWITCH.md** | Simulator vs real hardware | Switching between modes |
| **FILES_ADDED.md** | What's new in the code | Understanding changes |
| **QUICK_START.md** | This file | Starting deployment |

---

## ⚠️ Important Safety Notes

1. **Remove wheels before testing motors** — Don't want it rolling away!
2. **Use GPIO.cleanup()** — Implemented in `motors_real.py`
3. **Check CSI connection** — Camera power is critical
4. **L298N power separate from Pi** — Don't share supply without proper isolation

---

## 🐛 Troubleshooting

**Camera not working?**
```bash
libcamera-hello --list-cameras
# If fails: check CSI ribbon, reboot, enable camera in raspi-config
```

**Motors not moving?**
```bash
# Test GPIO
gpio readall

# Check L298N power (12V)
# Check GPIO pins in motors_real.py match your wiring
```

**Detection failing?**
```bash
# Adjust HSV range in config/sim_settings.py
# Or collect data to train ML model
python3 main_pi.py --collect-data
```

**Full troubleshooting:** See `DEPLOYMENT_GUIDE.md` Phase 5

---

## 📊 Commands Quick Reference

| Goal | Command |
|------|---------|
| Test simulator | `python sim_main.py --auto 100` |
| Collect simulator data | `python sim_main.py --auto 500 --headless --collect-data` |
| Train ML model | `python tools/train_model.py` |
| Test on Pi 5 | `python3 main_pi.py` |
| Test with ML on Pi | `python3 main_pi.py --ml` |
| Collect real data | `python3 main_pi.py --collect-data` |

---

## ✅ Are You Ready?

**YES:** Start with `DEPLOYMENT_GUIDE.md` Phase 1 (Hardware setup)

**MAYBE:** Read `HARDWARE_SWITCH.md` to understand differences

**UNSURE:** Check `FILES_ADDED.md` to see what code exists

---

## 💡 Pro Tips

1. **Start with simulator** — Tune PID gains before hardware
2. **Collect real data** — ML trained on real hardware >> pre-trained models
3. **Test motors first** — Verify GPIO and L298N before full system
4. **Use headless mode** — Faster processing on Pi
5. **Monitor CPU temp** — `vcgencmd measure_temp` during testing

---

**Ready to build your SmartBin?** 🎉

Start with Phase 1 of `DEPLOYMENT_GUIDE.md` and work through systematically.

Good luck! 🚀

