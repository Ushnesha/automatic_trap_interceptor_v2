# TOF CSI Setup Checklist

## Hardware ✓

- [ ] ArduCAM TOF camera connected to **CSI0 port**
- [ ] Ribbon cable **fully seated** (contacts facing inward)
- [ ] Power connected (CSI port provides power)
- [ ] Raspberry Pi 5 running Bookworm OS

## Software Installation

### Step 1: Enable Camera Interface
```bash
sudo raspi-config
# Navigate to: Interface Options > Camera > Enable > Yes
# Reboot when done
```
- [ ] Camera interface enabled
- [ ] Raspberry Pi rebooted

### Step 2: Install System Libraries
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3-picamera2 libcamera-tools python3-opencv
```
- [ ] python3-picamera2 installed
- [ ] libcamera-tools installed
- [ ] opencv installed

### Step 3: Install Python Dependencies
```bash
pip install opencv-python numpy scipy
```
- [ ] opencv-python installed
- [ ] numpy installed
- [ ] scipy installed

## Verification

### Check 1: libcamera Detection
```bash
libcamera-hello
```
- [ ] Shows camera preview for 3 seconds
- [ ] Output mentions "arducam" or "tof"

### Check 2: Verify Camera List
```bash
libcamera-still --list-cameras
```
- [ ] Shows "arducam_tof [320x240]" or similar
- [ ] Returns exit code 0

### Check 3: Run Diagnostic
```bash
python3 tools/diagnose_camera.py
```
- [ ] ✓ Raspberry Pi Camera Detection
- [ ] ✓ libcamera Support
- [ ] ✓ Picamera2 Library
- [ ] ✓ SmartBin Camera Module
- [ ] All frames captured successfully

**If any check fails**, see CSI_SETUP.md troubleshooting section.

## Configuration Tuning

### Step 1: Visualize Depth
```bash
python3 tools/tune_tof.py
```
- [ ] Window opens showing depth visualization
- [ ] Red zone visible (detection range)
- [ ] Can see depth values printed

### Step 2: Find Object Distance
Place your object (ball) in front of the camera and note the depth statistics.

Example output:
```
Frame 1: (320, 240) | range: 0.35m - 0.75m
```

**Note your typical depth:** _____ m

### Step 3: Adjust Parameters
In `tools/tune_tof.py`:
- Press **↑** or **↓** to adjust `TOF_OBJECT_DEPTH`
- Press **←** or **→** to adjust `TOF_DEPTH_TOLERANCE`

Target: Green circle appears on your object

- [ ] Found optimal `TOF_OBJECT_DEPTH`
- [ ] Found optimal `TOF_DEPTH_TOLERANCE`

### Step 4: Update Settings
Edit `config/sim_settings.py`:
```python
TOF_OBJECT_DEPTH = 0.X      # Your measured distance
TOF_DEPTH_TOLERANCE = 0.Y   # Your tolerance
```
- [ ] Updated `TOF_OBJECT_DEPTH` in settings
- [ ] Updated `TOF_DEPTH_TOLERANCE` in settings

## Testing

### Test 1: Single Frame Capture
```bash
python3 << 'PYTHON'
from src.camera_real import RealCamera
from config.sim_settings import SimSettings

camera = RealCamera(settings=SimSettings())
depth = camera.get_depth_frame()
print(f"Captured: {depth.shape}")
print(f"Depth range: {depth.min():.2f}m - {depth.max():.2f}m")
camera.cleanup()
PYTHON
```
- [ ] Successfully captured depth frame
- [ ] Depth values are reasonable (0.1m - 2.0m range)

### Test 2: Detection Test
```bash
python3 << 'PYTHON'
from src.camera_real import RealCamera
from src.detect_real import RealDetector
from config.sim_settings import SimSettings

settings = SimSettings()
camera = RealCamera(settings=settings)
detector = RealDetector(settings=settings)

for i in range(5):
    depth = camera.get_depth_frame()
    obj = detector.find_object(depth)
    print(f"Frame {i+1}: {obj}")

camera.cleanup()
PYTHON
```
- [ ] Successfully captured 5 frames
- [ ] `find_object()` returns coordinates or None
- [ ] Detects objects when present

### Test 3: Full Integration
```bash
python3 main_pi.py
```
- [ ] Starts without errors
- [ ] Prints "[RUNNING] Frames: X" every few seconds
- [ ] Detection working (prints position when object visible)
- [ ] Can stop with Ctrl+C

- [ ] Integration test successful

## Final Verification

Before running SmartBin on real robot:

- [ ] All hardware checks passed
- [ ] All software packages installed
- [ ] Camera diagnostic passed
- [ ] Parameters tuned
- [ ] Single frame capture works
- [ ] Detection test works
- [ ] Full integration test works

## Documentation

- [ ] Read CSI_QUICK_START.md
- [ ] Read CSI_SETUP.md
- [ ] Understand TOF vs HSV differences

## Ready to Deploy

```bash
python3 main_pi.py
```

- [ ] SmartBin running
- [ ] Catching objects successfully

## Troubleshooting Log

If you encounter issues, document them here:

**Issue 1:**
```
Error: [CAMERA] Failed to initialize TOF camera
Action taken: 
Result: 
```

**Issue 2:**
```
Error: 
Action taken: 
Result: 
```

---

## Support

If you're stuck:
1. Check CSI_SETUP.md troubleshooting section
2. Run `python3 tools/diagnose_camera.py` to get detailed diagnostics
3. Verify CSI ribbon is fully seated
4. Check Raspberry Pi camera is enabled via `raspi-config`

Good luck! 🎉
