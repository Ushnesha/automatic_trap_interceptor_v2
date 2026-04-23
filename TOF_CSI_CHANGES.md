# TOF Camera Update - Complete Change List

Your codebase has been successfully migrated from **HSV color detection** to **TOF depth detection via CSI port**.

## Files Modified

### 1. `config/sim_settings.py`
**Removed:**
- `HSV_LOWER = (3, 70, 70)`
- `HSV_UPPER = (30, 255, 255)`

**Changed:**
- Frame resolution: 640x480 → **320x240** (TOF native)

**Added:**
- `TOF_MIN_DEPTH = 0.1` (minimum valid distance)
- `TOF_MAX_DEPTH = 2.0` (maximum valid distance)
- `TOF_OBJECT_DEPTH = 0.5` (expected object distance, **tune this!**)
- `TOF_DEPTH_TOLERANCE = 0.3` (±tolerance, **tune this!**)

### 2. `src/camera_real.py`
**Complete rewrite** for CSI TOF:
- Removed: Pi Camera v2 / libcamera USB pipeline
- Added: Picamera2 + libcamera CSI support
- Returns: depth frame (meters) instead of BGR frame
- Methods:
  - `get_depth_frame()` — capture depth from CSI TOF
  - `get_frame()` — wrapper for compatibility
  - `cleanup()` — release CSI resources

### 3. `src/detect_real.py`
**Complete rewrite** for depth-based detection:
- Removed: all HSV conversion and color filtering
- Added: depth thresholding and morphology
- Methods:
  - `find_object()` — default (range-based)
  - `find_object_by_proximity()` — alternative (closest object)
  - `get_depth_stats()` — debug statistics

### 4. `main_pi.py`
**No changes needed** — still calls:
- `detector.find_object(frame)` (now works with depth)

## Files Created

### Documentation

1. **CSI_QUICK_START.md** — Start here! Quick 5-step setup
2. **CSI_SETUP.md** — Detailed hardware/software setup + troubleshooting
3. **TOF_MIGRATION.md** — Technical migration guide
4. **TOF_CSI_CHANGES.md** — This file

### Tools

1. **tools/diagnose_camera.py** — Verify CSI camera connection
   ```bash
   python3 tools/diagnose_camera.py
   ```

2. **tools/tune_tof.py** — Interactive depth tuning
   ```bash
   python3 tools/tune_tof.py
   ```

## Key Differences: HSV → TOF

| Aspect | Old (HSV) | New (TOF) |
|--------|-----------|-----------|
| **Detection** | Color range filtering | Depth range filtering |
| **Camera** | Pi Camera v2 (RGB) | ArduCAM TOF (depth) |
| **Connection** | CSI port (or USB) | CSI port |
| **Resolution** | 640x480 | 320x240 |
| **Frame rate** | 30 fps | 10 fps |
| **Lighting** | Color-dependent | Lighting-independent |
| **Configuration** | HSV_LOWER/UPPER | TOF_OBJECT_DEPTH ± TOF_DEPTH_TOLERANCE |

## What Changed in Your Code

### Before (HSV)
```python
frame = camera.get_frame()  # BGR image
position = detector.find_object(frame)  # HSV thresholding
```

### After (TOF)
```python
frame = camera.get_frame()  # Depth frame (meters)
position = detector.find_object(frame)  # Depth thresholding
```

**No change in calling code!** Same interface, different backend.

## Required Tuning

Once your CSI camera is working, you **must tune two parameters**:

1. **TOF_OBJECT_DEPTH** (default 0.5m)
   - The expected distance from camera to objects
   - Run `tools/tune_tof.py` and press ↑/↓ arrows to adjust
   - Typical range: 0.3m - 1.0m

2. **TOF_DEPTH_TOLERANCE** (default ±0.3m)
   - How much variation around the expected depth
   - Run `tools/tune_tof.py` and press ←/→ arrows to adjust
   - Typical range: ±0.1m to ±0.5m

Example:
```
If objects are always ~60cm away:
  TOF_OBJECT_DEPTH = 0.6
  TOF_DEPTH_TOLERANCE = 0.15  (so range is 0.45-0.75m)
```

## Quick Start Checklist

- [ ] **Connect** ArduCAM TOF to CSI0 port (ribbon fully seated)
- [ ] **Enable** camera in `sudo raspi-config`
- [ ] **Install** packages: `sudo apt install python3-picamera2 libcamera-tools`
- [ ] **Diagnose** camera: `python3 tools/diagnose_camera.py`
- [ ] **Tune** parameters: `python3 tools/tune_tof.py`
- [ ] **Run** SmartBin: `python3 main_pi.py`

## Troubleshooting

**"Camera not found":**
- Check CSI ribbon is fully seated
- Run `libcamera-hello` to test
- See CSI_SETUP.md "Troubleshooting" section

**"No objects detected":**
- Run `tools/tune_tof.py` to visualize depth
- Adjust `TOF_OBJECT_DEPTH` and `TOF_DEPTH_TOLERANCE`
- See CSI_SETUP.md "Tuning" section

**"ImportError: No module named 'picamera2'":**
- Install: `sudo apt install python3-picamera2`

**"Depth range is all zeros":**
- CSI cable may not be fully seated
- Try reseating the ribbon in CSI0 port

## Reverting (if needed)

To go back to HSV color detection:
```bash
git checkout HEAD -- config/sim_settings.py src/camera_real.py src/detect_real.py
```

But you'll lose CSI support and revert to USB-only setup.

## Performance

- **Resolution:** 320x240 (TOF native)
- **Frame rate:** ~10 fps (TOF hardware limit)
- **Latency:** ~100ms per frame
- **CPU usage:** Low (simple depth thresholding)
- **Accuracy:** Better in low light, no color dependency

## Next Steps

1. Read **CSI_QUICK_START.md** for 5-step setup
2. Run `tools/diagnose_camera.py` to verify camera
3. Run `tools/tune_tof.py` to find optimal depth thresholds
4. Run `python3 main_pi.py` to start SmartBin

Questions? See CSI_SETUP.md or TOF_MIGRATION.md.
