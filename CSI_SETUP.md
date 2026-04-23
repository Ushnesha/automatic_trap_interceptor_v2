# ArduCAM TOF via CSI Port Setup

## Hardware Connection

Your ArduCAM TOF camera is connected via **CSI (Camera Serial Interface) port** on Raspberry Pi 5.

### Physical Setup
1. **CSI Ribbon Cable** connects to the CSI0 port (near USB ports)
2. **Power**: CSI cameras draw power from the Raspberry Pi's CSI port
3. **No USB adapter needed** — pure CSI connection

## Software Setup

### 1. Enable Camera Interface
First, enable the camera in Raspberry Pi settings:

```bash
sudo raspi-config
# Navigate to: Interface Options > Camera > Enable
# Select "Yes"
# Reboot
```

### 2. Install Required Libraries

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install camera libraries
sudo apt install -y python3-picamera2 python3-libcamera

# Install Python dependencies
pip install opencv-python numpy scipy
```

### 3. Verify Camera Connection

```bash
# Check if camera is detected
libcamera-hello

# List connected cameras
libcamera-still --list-cameras

# Expected output:
# Available cameras
# 0 : arducam_tof [320x240]
```

If you see the ArduCAM TOF in the list, the connection is working.

## Testing the Camera

### Test 1: Capture Raw Depth

```bash
python3 << 'PYTHON'
from src.camera_real import RealCamera
from config.sim_settings import SimSettings

settings = SimSettings()
camera = RealCamera(settings=settings)

# Capture one frame
depth = camera.get_depth_frame()

if depth is not None:
    print(f"✓ Success! Captured {depth.shape}")
    print(f"  Depth range: {depth.min():.2f}m - {depth.max():.2f}m")
else:
    print("✗ Failed to capture frame")

camera.cleanup()
PYTHON
```

### Test 2: Visual Depth Viewer

```bash
python3 << 'PYTHON'
import cv2
import numpy as np
from src.camera_real import RealCamera
from config.sim_settings import SimSettings

settings = SimSettings()
camera = RealCamera(settings=settings)

for _ in range(60):  # 60 frames
    depth = camera.get_depth_frame()
    if depth is None:
        print("Camera not ready")
        break
    
    # Normalize for display
    valid = depth > 0
    if np.any(valid):
        d_min, d_max = depth[valid].min(), depth[valid].max()
        depth_vis = ((depth - d_min) / (d_max - d_min + 1e-6) * 255).astype(np.uint8)
        depth_vis = cv2.applyColorMap(depth_vis, cv2.COLORMAP_JET)
        
        cv2.imshow("TOF Depth", depth_vis)
        if cv2.waitKey(30) & 0xFF == ord('q'):
            break

camera.cleanup()
cv2.destroyAllWindows()
PYTHON
```

### Test 3: Run Tuning Tool

```bash
python3 tools/tune_tof.py
```

Should show live depth visualization with red overlay showing detection zone.

## Troubleshooting

### "Camera not found" / "Failed to initialize TOF camera"

1. **Verify CSI connection:**
   ```bash
   vcgencmd get_camera
   # Expected: supported=1 detected=1
   ```

2. **Check libcamera:**
   ```bash
   libcamera-hello --timeout 2000
   # Should show camera preview for 2 seconds
   ```

3. **Try different camera index:**
   Edit `camera_real.py` and try CSI0 or CSI1:
   ```python
   # In _init_libcamera():
   pipeline = (
       "libcamerasrc camera-name=arducam_tof ! "  # Try removing this line
       "video/x-raw,width=320,height=240,format=BGR ! "
       "videoconvert ! "
       "video/x-raw,format=BGR ! appsink"
   )
   ```

4. **Check permissions:**
   ```bash
   # Make sure your user can access cameras
   sudo usermod -a -G video $USER
   # Log out and back in
   ```

### "ImportError: No module named 'picamera2'"

```bash
# Install picamera2
sudo apt install -y python3-picamera2

# Or via pip (on Pi 5)
pip install picamera2
```

### "Depth range is too limited" or "All zeros"

The camera might not be outputting data correctly. Verify:

1. **CSI ribbon is fully seated** in the connector
2. **Ribbon orientation** is correct (contacts facing inward)
3. **Try different camera firmware**:
   ```bash
   sudo rpi-update
   sudo reboot
   ```

### Low frame rate (~2-5 fps instead of 10)

TOF cameras have inherent frame rate limitations. This is normal:
- **Typical:** 10-15 fps
- **Acceptable:** 5-10 fps
- **Problem:** < 2 fps (check CPU load, thermal throttling)

Check CPU temp:
```bash
vcgencmd measure_temp
```

## Performance Notes

- **Resolution:** 320x240 (native TOF)
- **Frame rate:** ~10 fps (hardware limit)
- **Latency:** ~100ms per frame
- **Data format:** Depth in meters, float32

## Dual Camera Setup (Optional)

If you want to use both TOF and regular camera:

```bash
# Check both cameras
libcamera-still --list-cameras

# In code, specify which one to use:
# CSI0 = TOF
# CSI1 = regular camera (if connected)
```

## Next Steps

1. Run `python3 tools/tune_tof.py` to verify detection
2. Adjust `TOF_OBJECT_DEPTH` and `TOF_DEPTH_TOLERANCE` based on your setup
3. Run `python3 main_pi.py` to start SmartBin
