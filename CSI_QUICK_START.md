# CSI TOF Quick Start

Your ArduCAM TOF camera is connected via **CSI port** (not USB). Here's what to do:

## Step 1: Enable Camera in Raspberry Pi

```bash
sudo raspi-config
# Interface Options → Camera → Enable → Yes → Reboot
```

## Step 2: Install Libraries

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-picamera2 libcamera-tools
pip install opencv-python numpy scipy
```

## Step 3: Diagnose Camera

```bash
cd /path/to/smartbin_v4
python3 tools/diagnose_camera.py
```

This checks:
- ✓ CSI camera detection
- ✓ libcamera support
- ✓ Picamera2 availability
- ✓ Actual depth capture

**All green?** → Go to Step 4

**Something red?** → See CSI_SETUP.md troubleshooting

## Step 4: Tune Detection

```bash
python3 tools/tune_tof.py
```

Visual feedback showing:
- Depth visualization (grayscale)
- Red zone = current detection range
- Green dot = detected object

**Arrow keys:**
- ↑/↓ adjust depth (±0.05m)
- ←/→ adjust tolerance (±0.05m)
- q = quit

## Step 5: Run SmartBin

```bash
python3 main_pi.py
```

Done! 🎉

---

## Key Differences from USB

| Aspect | USB | CSI |
|--------|-----|-----|
| Connection | USB port | CSI ribbon cable |
| Power | USB power | CSI power (built-in) |
| Driver | cv2.VideoCapture | Picamera2 / libcamera |
| Latency | High | Low |
| Typical FPS | 5-10 | 10-15 |

## If Camera Not Found

1. **Check cable:**
   - Fully seated in CSI0 port
   - Contacts facing inward (gold side down)

2. **Verify detection:**
   ```bash
   libcamera-hello
   ```
   Should show live preview for 3 seconds

3. **Check permissions:**
   ```bash
   sudo usermod -a -G video $USER
   # Log out and back in
   ```

4. **Run diagnostic:**
   ```bash
   python3 tools/diagnose_camera.py
   ```

## Files Changed

- `config/sim_settings.py` — TOF depth parameters (not HSV)
- `src/camera_real.py` — CSI depth capture (Picamera2)
- `src/detect_real.py` — Depth-based detection (not color)
- `tools/tune_tof.py` — Parameter tuning tool
- `tools/diagnose_camera.py` — Camera diagnostic tool

All old HSV code is removed. No USB driver needed.

## Next: Tuning

Once diagnosed successfully, run `tune_tof.py` to find optimal:
- **TOF_OBJECT_DEPTH** — how far away objects are (typically 0.3-1.0m)
- **TOF_DEPTH_TOLERANCE** — tolerance band around that distance

See **CSI_SETUP.md** for detailed setup and troubleshooting.
