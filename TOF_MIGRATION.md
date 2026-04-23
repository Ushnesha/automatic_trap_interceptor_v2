# TOF Camera Migration Guide

## Overview
The codebase has been updated to use **ArduCAM TOF (Time-of-Flight)** depth camera instead of HSV color-based detection. This provides more reliable object detection in varying lighting conditions.

## Key Changes

### 1. Configuration (`config/sim_settings.py`)
**Removed:**
- `HSV_LOWER` and `HSV_UPPER` color ranges
- Frame resolution changed from 640x480 to 320x240 (TOF native resolution)

**Added:**
- `TOF_MIN_DEPTH` (0.1m) — minimum valid distance
- `TOF_MAX_DEPTH` (2.0m) — maximum valid distance  
- `TOF_OBJECT_DEPTH` (0.5m) — expected distance to objects
- `TOF_DEPTH_TOLERANCE` (±0.3m) — tolerance band around expected depth

### 2. Camera Module (`src/camera_real.py`)
**Old:** RGB frame capture from Pi Camera v2
**New:** Depth frame from ArduCAM TOF
- Outputs raw depth data in meters
- 320x240 resolution @ 10fps (typical for TOF)
- Automatically normalizes depth values from raw camera output

### 3. Detection Module (`src/detect_real.py`)
**Old:** HSV color thresholding + morphology
**New:** Depth range filtering + morphology
- `find_object()` — default method using depth range
- `find_object_by_proximity()` — alternative: finds closest object
- `get_depth_stats()` — debug method to inspect depth distribution

## Getting Started

### Hardware Setup
1. Connect ArduCAM TOF camera via USB to Raspberry Pi
2. Install required libraries:
   ```bash
   pip install opencv-python numpy scipy
   ```

### Tuning Detection Parameters
Use the interactive tuning tool to find optimal depth thresholds:

```bash
python3 tools/tune_tof.py
```

**Controls:**
- **↑/↓ arrows:** Adjust `TOF_OBJECT_DEPTH` (±0.05m steps)
- **←/→ arrows:** Adjust `TOF_DEPTH_TOLERANCE` (±0.05m steps)
- **'q':** Quit and print final settings

The tool shows:
- Depth visualization (grayscale)
- Red overlay = current detection zone
- Green circle = detected object center

### Running SmartBin
```bash
# Normal operation (Kalman filter)
python3 main_pi.py

# With ML predictor
python3 main_pi.py --ml

# With data collection
python3 main_pi.py --collect-data
```

## Troubleshooting

### "Failed to initialize TOF camera"
- Check USB connection: `lsusb | grep ArduCAM`
- Verify device: `ls -la /dev/video*`
- Try: `cv2.VideoCapture(1)` or `cv2.VideoCapture(2)` instead of `0`

### No objects detected
1. Run `tools/tune_tof.py` to see depth distribution
2. Check depth statistics (min/max/mean values)
3. Adjust `TOF_OBJECT_DEPTH` and `TOF_DEPTH_TOLERANCE` based on stats

### Noisy detections
- Increase `MIN_OBJECT_AREA` to filter small noise clusters
- Adjust morphological kernel size in `find_object()` (currently 5x5)

## Detection Methods

### Default: `find_object()`
Good for stable background. Uses depth range filtering:
- Keeps pixels within `[TOF_OBJECT_DEPTH ± TOF_DEPTH_TOLERANCE]`
- Applies morphological closing/opening
- Finds largest connected component

**When to use:** Structured scenes, known object distance

### Alternative: `find_object_by_proximity()`
Good when background depth is unpredictable. Finds closest object:
- Locates minimum depth within valid range
- No range filtering required

**When to use:** Dynamic backgrounds, variable distances

Switch in `main_pi.py`:
```python
# Change from:
position = detector.find_object(frame)

# To:
position = detector.find_object_by_proximity(frame)
```

## FAQ

**Q: Why 320x240 instead of 640x480?**
A: ArduCAM TOF native resolution is 320x240. Higher resolution is possible but reduces frame rate and increases latency.

**Q: How do I know the right depth range?**
A: Use `tools/tune_tof.py` to visualize live depth. Typical object distances are 0.3-1.0m.

**Q: Can I use both TOF and color detection?**
A: Not currently, but you can hybrid it:
- Use TOF as primary detector (fast, reliable)
- Fall back to color if TOF fails (for edge cases)

**Q: Why is detection slower than before?**
A: TOF runs at ~10fps (hardware limit). Color detection at 30fps was faster, but less reliable.

## Performance Notes

- **Frame rate:** ~10fps (TOF hardware limit)
- **Detection latency:** ~100ms per frame
- **CPU usage:** Low (simple depth thresholding)
- **Accuracy:** Better in low light, independent of color

## Reverting to HSV (if needed)

If you need to revert to color detection:
1. Restore HSV settings from git
2. Revert `camera_real.py` to use BGR frames
3. Revert `detect_real.py` to HSV detection
4. Restore original `main_pi.py` calls

```bash
git checkout HEAD -- config/sim_settings.py src/camera_real.py src/detect_real.py
```
