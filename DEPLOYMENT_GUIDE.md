# SmartBin Deployment Guide: Raspberry Pi 5

Complete step-by-step guide to run SmartBin on real hardware (Pi 5 + Camera + L298N + Mecanum wheels).

---

## Prerequisites

### Hardware Required
- **Raspberry Pi 5** (4GB+ RAM recommended)
- **Pi Camera Module** (v2 or v3)
- **L298N Motor Driver**
- **Mecanum Wheels Chassis** with 4 motors
- **Orange ball** (or similar colored sphere for detection)
- **Power supply** (5.1V for Pi, 12V for motors)
- **Jumper wires, breadboard**

### Software Required
- Raspberry Pi OS (Bullseye or later)
- Python 3.9+
- Git

---

## Phase 1: Hardware Assembly & Wiring

### Step 1.1: Connect Camera to Pi 5

1. **Locate Camera CSI port** (flat ribbon connector on top of Pi)
2. **Power off the Pi**
3. **Gently pull up the black latch** on CSI port
4. **Insert Camera ribbon** (blue side facing away from Pi)
5. **Push down the latch** to secure
6. **Power on Pi**

**Test camera:**
```bash
libcamera-hello --list-cameras
```
Expected output:
```
0 : imx708 [4608x3456] (/base/soc/i2c0mux/i2c@0,0/imx708@1a)
```

---

### Step 1.2: Connect L298N Motor Driver to Pi 5

**L298N Pinout:**
```
L298N Pin  →  Pi 5 GPIO
IN1        →  GPIO 17 (Motor A direction)
IN2        →  GPIO 27 (Motor A direction)
IN3        →  GPIO 22 (Motor B direction)
IN4        →  GPIO 23 (Motor B direction)
ENA        →  GPIO 12 (PWM Motor A speed)
ENB        →  GPIO 13 (PWM Motor B speed)
GND        →  GND
+12V       →  +12V power supply
```

**Wiring steps:**
1. Connect L298N GND to Pi GND
2. Connect L298N +12V to power supply positive
3. Connect motor wires to L298N OUT1-OUT4
4. Connect GPIO pins as above

**Verify GPIO access:**
```bash
gpio readall
```

---

### Step 1.3: Connect Mecanum Wheels

**Motor connections to L298N:**
- **Motor A (Left)** → L298N OUT1, OUT2
- **Motor B (Right)** → L298N OUT3, OUT4

For **omnidirectional strafe** (left-right movement):
```
Strafe Right:  Motor A forward, Motor B backward
Strafe Left:   Motor A backward, Motor B forward
```

**Test motors:**
```bash
# Manual test (if GPIO already configured)
gpio mode 17 out
gpio write 17 1  # Motor ON
gpio write 17 0  # Motor OFF
```

---

## Phase 2: Software Setup on Pi 5

### Step 2.1: Update System & Install Dependencies

```bash
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    python3-pip \
    python3-dev \
    git \
    libatlas-base-dev \
    libjasper-dev \
    libharfbuzz0b \
    libwebp6 \
    libtiff5 \
    libjasper1 \
    libharfbuzz0b \
    libwebp6 \
    libtiff5 \
    libatlas-base-dev
```

---

### Step 2.2: Clone SmartBin Repository

```bash
cd ~
git clone <your-repo-url> smartbin_v4
cd smartbin_v4
```

---

### Step 2.3: Install Python Dependencies

```bash
pip3 install --upgrade pip setuptools wheel

# Core dependencies
pip3 install numpy opencv-python

# ML support (optional, for training)
pip3 install scikit-learn

# GPIO control for real hardware
pip3 install RPi.GPIO
```

**Check installations:**
```bash
python3 -c "import cv2; print(cv2.__version__)"
python3 -c "import numpy; print(numpy.__version__)"
python3 -c "import RPi.GPIO; print('GPIO OK')"
```

---

## Phase 3: Adapt Code for Real Hardware

### Step 3.1: Create Real Hardware Motor Driver

Replace `src/sim_motors.py` with real GPIO control:

**File:** `src/motors.py` (NEW - for real Pi)

```python
import RPi.GPIO as GPIO
import time

class RealMotors:
    """Real L298N motor control for Raspberry Pi 5"""
    
    def __init__(self, settings):
        self.S = settings
        self._vx = 0.0
        self._target_px = None
        self._integral = 0.0
        self._prev_err = None
        self._ppm_x = settings.FRAME_WIDTH / settings.ARENA_W
        
        # GPIO pins for L298N
        self.IN1 = 17  # Motor A direction 1
        self.IN2 = 27  # Motor A direction 2
        self.IN3 = 22  # Motor B direction 1
        self.IN4 = 23  # Motor B direction 2
        self.ENA = 12  # PWM Motor A (speed)
        self.ENB = 13  # PWM Motor B (speed)
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([self.IN1, self.IN2, self.IN3, self.IN4], GPIO.OUT)
        
        # PWM for speed control (1000 Hz)
        self.pwm_a = GPIO.PWM(self.ENA, 1000)
        self.pwm_b = GPIO.PWM(self.ENB, 1000)
        self.pwm_a.start(0)
        self.pwm_b.start(0)
        
        print(f"[MOTOR] Real L298N motors initialized")
        print(f"[MOTOR] KP={settings.PID_KP} KI={settings.PID_KI} KD={settings.PID_KD}")
    
    def move_to_x(self, target_x_pixels):
        """Move can to target X using PID control"""
        self._target_px = target_x_pixels
        S = self.S
        dt = S.SIM_TIMESTEP
        
        # Pixel → meters
        target_m = (target_x_pixels / self._ppm_x) - S.ARENA_W / 2
        current_m = 0.0  # TODO: Get from encoder/IMU
        error = target_m - current_m
        
        # Dead zone
        if abs(error) < S.POSITION_TOL:
            self._vx = 0.0
            self._integral = 0.0
            self._apply_velocity(0.0)
            return
        
        # PID calculation (same as simulator)
        self._integral += error * dt
        max_i = S.CAN_MAX_SPEED / max(S.PID_KI, 0.001)
        self._integral = max(-max_i, min(max_i, self._integral))
        
        deriv = 0.0
        if self._prev_err is not None and dt > 0:
            deriv = (error - self._prev_err) / dt
        self._prev_err = error
        
        cmd = S.PID_KP * error + S.PID_KI * self._integral + S.PID_KD * deriv
        cmd = max(-S.CAN_MAX_SPEED, min(S.CAN_MAX_SPEED, cmd))
        
        # Acceleration ramp
        max_delta = S.CAN_ACCEL * dt
        if cmd > self._vx + max_delta:
            cmd = self._vx + max_delta
        elif cmd < self._vx - max_delta:
            cmd = self._vx - max_delta
        
        self._vx = cmd
        self._apply_velocity(self._vx)
    
    def _apply_velocity(self, velocity):
        """Convert velocity to PWM signals"""
        # Normalize velocity to PWM duty cycle (0-100%)
        max_speed = self.S.CAN_MAX_SPEED
        duty = abs(velocity) / max_speed * 100
        duty = max(0, min(100, duty))
        
        if velocity > 0.1:
            # Strafe right
            GPIO.output(self.IN1, GPIO.HIGH)   # Motor A forward
            GPIO.output(self.IN2, GPIO.LOW)
            GPIO.output(self.IN3, GPIO.LOW)    # Motor B backward
            GPIO.output(self.IN4, GPIO.HIGH)
        elif velocity < -0.1:
            # Strafe left
            GPIO.output(self.IN1, GPIO.LOW)    # Motor A backward
            GPIO.output(self.IN2, GPIO.HIGH)
            GPIO.output(self.IN3, GPIO.HIGH)   # Motor B forward
            GPIO.output(self.IN4, GPIO.LOW)
        else:
            # Stop
            GPIO.output(self.IN1, GPIO.LOW)
            GPIO.output(self.IN2, GPIO.LOW)
            GPIO.output(self.IN3, GPIO.LOW)
            GPIO.output(self.IN4, GPIO.LOW)
            duty = 0
        
        self.pwm_a.ChangeDutyCycle(duty)
        self.pwm_b.ChangeDutyCycle(duty)
    
    def center(self):
        """Reset to center position"""
        self._vx = 0.0
        self._integral = 0.0
        self._prev_err = None
        self._apply_velocity(0.0)
        print("[MOTOR] Centered")
    
    def stop(self):
        self._vx = 0.0
        self._apply_velocity(0.0)
    
    def reset(self):
        self._vx = 0.0
        self._target_px = None
        self._integral = 0.0
        self._prev_err = None
    
    def cleanup(self):
        """Cleanup GPIO on exit"""
        GPIO.cleanup()
    
    @property
    def vx(self):
        return self._vx
    
    @property
    def target_px(self):
        return self._target_px
```

---

### Step 3.2: Create Real Camera Driver

Replace `src/sim_camera.py` with real camera capture:

**File:** `src/camera.py` (NEW - for real Pi)

```python
import cv2
import numpy as np

class RealCamera:
    """Real Pi Camera capture using OpenCV"""
    
    def __init__(self, settings):
        self.S = settings
        
        # Use libcamera backend (Pi 5 prefers this)
        self.cap = cv2.VideoCapture(
            "libcamerasrc ! video/x-raw,width=640,height=480 ! videoconvert ! "
            "video/x-raw,format=BGR ! appsink",
            cv2.CAP_GSTREAMER
        )
        
        if not self.cap.isOpened():
            # Fallback to legacy camera interface
            print("[CAMERA] libcamera failed, trying legacy interface")
            self.cap = cv2.VideoCapture(0)
        
        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Warm up camera
        for _ in range(10):
            self.cap.read()
        
        print("[CAMERA] Real Pi Camera initialized (640x480 @ 30fps)")
    
    def get_frame(self):
        """Capture frame from real camera"""
        ret, frame = self.cap.read()
        if not ret:
            print("[CAMERA] Failed to read frame")
            return None
        return frame
    
    def world_to_pixel_x(self, world_x):
        """Convert world meters to pixel X"""
        ppm_x = self.S.FRAME_WIDTH / self.S.ARENA_W
        pixel_x = (world_x + self.S.ARENA_W/2) * ppm_x
        return int(pixel_x)
    
    def cleanup(self):
        """Release camera"""
        self.cap.release()
```

---

### Step 3.3: Create Real Detection with OpenCV

Replace `src/detect.py` with real cv2 code:

**File:** `src/detect_real.py` (NEW - for real Pi)

```python
import cv2
import numpy as np

class RealDetector:
    """Real orange ball detection using OpenCV"""
    
    def __init__(self, settings):
        self.S = settings
        self.lower = np.array(settings.HSV_LOWER, dtype=np.uint8)
        self.upper = np.array(settings.HSV_UPPER, dtype=np.uint8)
        print(f"[DETECT] HSV range: {settings.HSV_LOWER} -> {settings.HSV_UPPER}")
    
    def find_object(self, frame):
        """Find orange ball in real camera frame"""
        if frame is None:
            return None
        
        # Convert BGR to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Create mask
        mask = cv2.inRange(hsv, self.lower, self.upper)
        
        # Morphological operations to reduce noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Find largest contour (ball)
        largest = max(contours, key=cv2.contourArea)
        
        # Check minimum area
        if cv2.contourArea(largest) < self.S.MIN_OBJECT_AREA:
            return None
        
        # Calculate centroid
        M = cv2.moments(largest)
        if M["m00"] == 0:
            return None
        
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        
        return (cx, cy)
```

---

### Step 3.4: Create Adapter Script

Create `main_pi.py` to load real hardware modules:

```python
"""
main_pi.py — SmartBin for Raspberry Pi 5
Uses real camera, motors, and detection instead of simulator
"""

import argparse
import time
import sys

from src.camera import RealCamera
from src.motors import RealMotors
from src.detect_real import RealDetector
from src.predict import Predictor
from src.ml_predictor import MLPredictor
from src.logger import Logger
from config.sim_settings import SimSettings


def main():
    args = argparse.ArgumentParser(description='SmartBin on Pi 5').parse_args()
    settings = SimSettings()
    log = Logger()
    
    log.header("SmartBin on Raspberry Pi 5")
    log.info("Hardware: Pi 5 | Camera | L298N | Mecanum")
    
    try:
        # Initialize real hardware
        camera = RealCamera(settings=settings)
        motors = RealMotors(settings=settings)
        detector = RealDetector(settings=settings)
        predictor = Predictor(settings=settings)
        
        log.success("All hardware initialized!")
        log.info("Press Ctrl+C to stop")
        
        frame_count = 0
        
        while True:
            frame = camera.get_frame()
            if frame is None:
                continue
            
            frame_count += 1
            
            # Detect ball
            position = detector.find_object(frame)
            
            if position:
                cx, cy = position
                log.debug(f"[DETECT] Ball at ({cx}, {cy})")
                
                # Predict landing
                predictor.add_point(position)
                predicted_x = predictor.get_predicted_landing_x()
                
                if predicted_x is not None:
                    log.debug(f"[PREDICT] Landing X = {predicted_x:.1f}px")
                    
                    # Move motors
                    motors.move_to_x(predicted_x)
            
            # Control loop timing (~30 FPS)
            if frame_count % 30 == 0:
                log.info(f"[RUNNING] Frames processed: {frame_count}")
            
            time.sleep(0.033)  # ~30 FPS
    
    except KeyboardInterrupt:
        log.info("Stopped by user")
    
    finally:
        # Cleanup
        camera.cleanup()
        motors.cleanup()
        log.info("Hardware cleaned up")


if __name__ == '__main__':
    main()
```

---

## Phase 4: Testing on Real Hardware

### Step 4.1: Test Camera

```bash
cd ~/smartbin_v4

# Test camera capture
python3 -c "
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    print(f'Camera OK: {frame.shape}')
    cv2.imwrite('/tmp/test.jpg', frame)
else:
    print('Camera FAILED')
cap.release()
"

# View test image
ls -la /tmp/test.jpg
```

---

### Step 4.2: Test Motors (IMPORTANT - Safety First!)

```bash
# Test motor control with GPIO
python3 << 'EOF'
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
IN1, IN2, IN3, IN4 = 17, 27, 22, 23
ENA, ENB = 12, 13

GPIO.setup([IN1, IN2, IN3, IN4], GPIO.OUT)
pwm_a = GPIO.PWM(ENA, 1000)
pwm_b = GPIO.PWM(ENB, 1000)
pwm_a.start(0)
pwm_b.start(0)

try:
    # Strafe right
    GPIO.output([IN1, IN3, IN4], [GPIO.HIGH, GPIO.LOW, GPIO.HIGH])
    GPIO.output([IN2], [GPIO.LOW])
    pwm_a.ChangeDutyCycle(50)  # 50% speed
    pwm_b.ChangeDutyCycle(50)
    print("Strafe RIGHT for 2 seconds...")
    time.sleep(2)
    
    # Strafe left
    GPIO.output([IN1, IN2, IN3, IN4], [GPIO.LOW, GPIO.HIGH, GPIO.HIGH, GPIO.LOW])
    print("Strafe LEFT for 2 seconds...")
    time.sleep(2)
    
    # Stop
    GPIO.output([IN1, IN2, IN3, IN4], [GPIO.LOW, GPIO.LOW, GPIO.LOW, GPIO.LOW])
    print("STOPPED")

finally:
    GPIO.cleanup()
    print("GPIO cleaned up")
EOF
```

⚠️ **Safety:** Remove wheels before testing motors!

---

### Step 4.3: Test Detection

```bash
python3 << 'EOF'
import cv2
import numpy as np
from config.sim_settings import SimSettings
from src.detect_real import RealDetector

settings = SimSettings()
detector = RealDetector(settings)

cap = cv2.VideoCapture(0)

for i in range(30):
    ret, frame = cap.read()
    if not ret:
        continue
    
    pos = detector.find_object(frame)
    if pos:
        print(f"Frame {i}: Ball detected at {pos}")
    else:
        print(f"Frame {i}: No ball")

cap.release()
EOF
```

---

### Step 4.4: Full System Test

```bash
# Run the Pi 5 main program
python3 main_pi.py
```

**Expected output:**
```
═══════════════════════════════════════════════════════
  SmartBin on Raspberry Pi 5
═══════════════════════════════════════════════════════
[CAMERA] Real Pi Camera initialized (640x480 @ 30fps)
[DETECT] HSV range: (3, 70, 70) -> (30, 255, 255)
[MOTOR] Real L298N motors initialized
[RUNNING] Frames processed: 30
[DETECT] Ball at (320, 240)
[PREDICT] Landing X = 325.5px
[MOTOR] Moving to 325.5px
...
```

---

## Phase 5: Troubleshooting

### Camera Issues

**Problem:** Camera returns None
```
Solution:
1. Check ribbon connection (CSI port)
2. Verify with: libcamera-hello --list-cameras
3. Try: sudo raspi-config → Camera → Enable
4. Reboot: sudo reboot
```

**Problem:** OpenCV can't access camera
```
Solution:
1. Install libcamera tools: sudo apt install -y libcamera-tools
2. Use libcamera backend in code
3. Check permissions: groups pi (should include video)
```

---

### Motor Issues

**Problem:** Motors don't move
```
Solution:
1. Check GPIO pins (17, 27, 22, 23, 12, 13)
2. Test with: gpio readall
3. Verify L298N power (12V)
4. Check jumper connections
5. Test GPIO directly with RPi.GPIO
```

**Problem:** Motors move in wrong direction
```
Solution:
Swap IN1/IN2 or IN3/IN4 in motors.py
```

---

### Detection Issues

**Problem:** Orange ball not detected
```
Solution:
1. Check HSV_LOWER and HSV_UPPER in settings.py
   Run: python3 tools/calibrate_hsv.py
2. Adjust lighting (ensure good illumination)
3. Print detected colors: print(cv2.cvtColor(frame, cv2.COLOR_BGR2HSV))
```

---

## Phase 6: Optimization & ML Training

### Step 6.1: Train ML Model on Real Data

Once basic system works:

```bash
# Collect real throws
python3 main_pi.py --collect-data

# Train on real hardware quirks
python3 tools/train_model.py

# Test with ML
python3 main_pi.py --ml
```

This learns camera biases and motor characteristics specific to your Pi 5.

---

### Step 6.2: Tune PID Gains

Adjust in `config/sim_settings.py`:

```python
PID_KP = 7.0   # Increase if response too slow
PID_KI = 0.1   # Increase if drifting
PID_KD = 1.0   # Increase if oscillating
```

**Test with different values:**
```bash
python3 main_pi.py  # Throw objects, observe motion
```

---

## Summary Checklist

- [ ] Camera connected and tested
- [ ] L298N wired to GPIO pins
- [ ] Mecanum wheels assembled
- [ ] Python dependencies installed
- [ ] `src/motors.py` → `src/motors_real.py` created
- [ ] `src/detect.py` → `src/detect_real.py` created
- [ ] `src/camera.py` created
- [ ] `main_pi.py` created and tested
- [ ] Motors tested (without wheels attached!)
- [ ] Camera detection calibrated
- [ ] Full system tested with throws
- [ ] ML model trained on real data (optional)
- [ ] PID gains tuned

---

## Performance Tips

1. **Use headless mode** (no GUI) for faster processing
2. **Set MIN_POINTS_TO_PREDICT = 4** for real hardware (not 2)
3. **Train ML model** on real camera data for best accuracy
4. **Use multi-threading** for camera capture to avoid blocking
5. **Monitor CPU/temp** with `vcgencmd measure_temp`

---

## Emergency Stop

If motors run away:

```bash
# Kill the process
sudo kill -9 $(pgrep -f main_pi.py)

# Or press Ctrl+C (triggers GPIO cleanup)
```

