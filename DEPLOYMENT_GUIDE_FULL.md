# SmartBin Deployment Guide - Complete

## Overview

This guide covers deploying SmartBin on a Raspberry Pi 5 with:
- **Camera:** ArduCAM TOF (Time-of-Flight) via CSI port
- **Wheels:** Mecanum wheels
- **Motor Driver:** L298N dual-motor driver
- **Power:** Battery system (recommended 5V/3A for Pi, 12V for motors)

**Estimated time:** 2-3 hours (first setup)

---

## Part 1: Hardware Assembly

### 1.1 Physical Components Needed

**Core:**
- Raspberry Pi 5 (4GB+ RAM recommended)
- ArduCAM TOF camera
- 4x Mecanum wheels (omnidirectional)
- 4x DC motors (3-6V, ~200-300 RPM)
- L298N motor driver module (dual channel)
- Chassis/robot body

**Power:**
- 5V USB-C power supply (3A+) for Raspberry Pi
- 12V battery pack for motor power (optional: second battery)
- Power distribution board or breadboard
- Jumper wires, breadboard (optional)

**Optional:**
- Heat sink for Raspberry Pi
- Fan for cooling
- Camera case/mount
- Motor mounting brackets

### 1.2 Hardware Connection Diagram

```
RASPBERRY PI 5
├─ CSI0 Port → ArduCAM TOF Camera (ribbon cable)
├─ GPIO 17 (pin 11) → L298N IN1 (Motor A forward)
├─ GPIO 27 (pin 13) → L298N IN2 (Motor A backward)
├─ GPIO 23 (pin 16) → L298N IN3 (Motor B forward)
├─ GPIO 24 (pin 18) → L298N IN4 (Motor B backward)
├─ GPIO 12 (pin 32) → L298N ENA (PWM speed A)
├─ GPIO 13 (pin 33) → L298N ENB (PWM speed B)
├─ GND → L298N GND
└─ 5V (USB-C) → Power supply

L298N MOTOR DRIVER
├─ Motor A terminals → Left motors (in parallel)
├─ Motor B terminals → Right motors (in parallel)
├─ 12V battery+ → +12V input
├─ 12V battery- → GND (common with Pi GND)
└─ GND → Raspberry Pi GND (must be common)

MOTORS (4 total)
├─ Left-Front (Motor A)
├─ Left-Rear (Motor A)
├─ Right-Front (Motor B)
├─ Right-Rear (Motor B)
```

### 1.3 Wiring Checklist

**Raspberry Pi Power:**
- [ ] USB-C cable to 5V/3A power supply
- [ ] Power supply confirmed working

**ArduCAM TOF:**
- [ ] CSI ribbon cable to CSI0 port
- [ ] Ribbon fully seated (contacts facing inward)
- [ ] Camera not forced (gentle insertion)

**L298N Motor Driver to Pi:**
- [ ] GPIO 17 → IN1
- [ ] GPIO 27 → IN2
- [ ] GPIO 23 → IN3
- [ ] GPIO 24 → IN4
- [ ] GPIO 12 → ENA (PWM)
- [ ] GPIO 13 → ENB (PWM)
- [ ] GND (any Pi GND) → GND (L298N)

**Motors to L298N:**
- [ ] Motor A+ → OUT1
- [ ] Motor A- → OUT2
- [ ] Motor B+ → OUT3
- [ ] Motor B- → OUT4

**Power to L298N:**
- [ ] +12V battery → +12V input
- [ ] -12V battery → GND input
- [ ] GND from battery → GND on Pi (common ground!)

**Important:** Pi and motor power must share a common GND. Without this, signals won't work.

### 1.4 Mecanum Wheel Configuration

Mecanum wheels have rollers at 45°. Set them up for holonomic movement:

```
        Front
    [LF]    [RF]
      
    [LR]    [RR]
        Back
```

**Wheel rotation to move forward:**
- LF (left-front): clockwise
- RF (right-front): clockwise  
- LR (left-rear): clockwise
- RR (right-rear): clockwise

**Code mapping in `src/motors_real.py`:**
```python
# Motor A (left side):  LF + LR
# Motor B (right side): RF + RR
```

---

## Part 2: Raspberry Pi 5 Operating System Setup

### 2.1 Install Raspberry Pi OS

**On your laptop/desktop:**

1. Download Raspberry Pi Imager:
   https://www.raspberrypi.com/software/

2. Insert microSD card (32GB+ recommended)

3. Open Imager:
   - Choose Device: "Raspberry Pi 5"
   - Choose OS: "Raspberry Pi OS (64-bit)" → "Bookworm"
   - Choose Storage: Your SD card
   - Click Settings (gear icon):
     - Set hostname: `smartbin`
     - Enable SSH
     - Set username: `pi` (or your preferred)
     - Set password: (remember this!)
     - Set WiFi SSID and password (if not Ethernet)
     - Set timezone
   - Click Write

4. Wait ~5 minutes for writing to complete

5. Insert SD card into Raspberry Pi 5

### 2.2 First Boot

1. Connect to Ethernet (or WiFi if configured)
2. Connect USB-C power to Pi 5
3. Wait 2-3 minutes for first boot
4. Lights should flash, showing activity

### 2.3 Remote Access via SSH

**From your laptop:**

```bash
ssh pi@smartbin.local
# If that doesn't work, try:
ssh pi@<raspberry-pi-ip>
```

**On first login:**
- Accept the SSH key prompt (type "yes")
- Enter your password

**Update system:**
```bash
sudo apt update
sudo apt upgrade -y
```

This takes 5-10 minutes. Go grab coffee!

---

## Part 3: Software Installation

### 3.1 Install Core Dependencies

```bash
# Camera libraries
sudo apt install -y python3-picamera2 libcamera-tools python3-opencv

# Python packages
pip install --upgrade pip
pip install opencv-python numpy scipy RPi.GPIO flask flask-cors
```

**Verification:**
```bash
python3 -c "import picamera2, cv2, numpy; print('✓ All imports OK')"
```

### 3.2 Clone SmartBin Code

```bash
cd ~
git clone <your-repo-url> smartbin_v4
cd smartbin_v4
```

Or if already present:
```bash
cd ~/smartbin_v4
git pull origin main
```

### 3.3 Install SmartBin Dependencies

```bash
cd ~/smartbin_v4
pip install -r requirements.txt 2>/dev/null || echo "No requirements.txt"
```

If requirements.txt doesn't exist, manually install:
```bash
pip install opencv-python numpy scipy pigpio
```

---

## Part 4: Hardware Verification

### 4.1 Test GPIO (Motor Control)

```bash
python3 << 'PYTHON'
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Test pins
test_pins = [17, 27, 23, 24, 12, 13]

print("Testing GPIO pins...")
for pin in test_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH)
    print(f"✓ Pin {pin} set HIGH")
    time.sleep(0.1)
    GPIO.output(pin, GPIO.LOW)
    print(f"  Pin {pin} set LOW")

GPIO.cleanup()
print("\n✓ GPIO test passed")
PYTHON
```

Expected output: All pins toggle without errors

### 4.2 Test Camera (TOF)

```bash
libcamera-hello --timeout 3000
```

Should show camera preview for 3 seconds. If not:
- Check CSI ribbon is fully seated
- Try unplugging/replugging ribbon

### 4.3 Run Full Diagnostic

```bash
cd ~/smartbin_v4
python3 tools/diagnose_camera.py
```

Should see:
```
✓ Raspberry Pi Camera Detection
✓ libcamera Support
✓ Picamera2 Library
✓ SmartBin Camera Module
✓ All checks passed!
```

If any fails, see "Troubleshooting" section.

### 4.4 Test Motor Driver

```bash
python3 << 'PYTHON'
from src.motors_real import RealMotors
from config.sim_settings import SimSettings

settings = SimSettings()
motors = RealMotors(settings=settings)

print("Testing motors...")

# Test each motor direction
print("Motor A forward...")
motors.motor_a(0.5)  # 50% speed
time.sleep(1)
motors.motor_a(0)    # Stop

print("Motor B forward...")
motors.motor_b(0.5)
time.sleep(1)
motors.motor_b(0)

print("Motor A backward...")
motors.motor_a(-0.5)
time.sleep(1)
motors.motor_a(0)

print("Motor B backward...")
motors.motor_b(-0.5)
time.sleep(1)
motors.motor_b(0)

motors.stop()
motors.cleanup()
print("✓ Motor test complete")
PYTHON
```

Expected behavior: Motors spin in each direction for 1 second

---

## Part 5: Configuration & Tuning

### 5.1 Verify Motor Wiring

If motors don't spin or spin wrong direction:

**Check L298N connections:**
```bash
# Test IN1, IN2 directly
python3 << 'PYTHON'
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)  # IN1
GPIO.setup(27, GPIO.OUT)  # IN2

# Forward (IN1=HIGH, IN2=LOW)
GPIO.output(17, GPIO.HIGH)
GPIO.output(27, GPIO.LOW)
print("Motor should go forward")
input("Press Enter...")

# Backward (IN1=LOW, IN2=HIGH)
GPIO.output(17, GPIO.LOW)
GPIO.output(27, GPIO.HIGH)
print("Motor should go backward")
input("Press Enter...")

# Stop (both LOW)
GPIO.output(17, GPIO.LOW)
GPIO.output(27, GPIO.LOW)

GPIO.cleanup()
PYTHON
```

If motor doesn't move:
- Check L298N power (12V LED should be on)
- Test with motor directly connected to 12V battery
- Check wiring to motor terminals

If motor direction is wrong:
- Swap the motor leads on L298N output

### 5.2 Tune Camera Depth Detection

```bash
cd ~/smartbin_v4
python3 tools/tune_tof.py
```

**Interactive tuning:**
1. Place object at typical working distance
2. Press ↑↓ to adjust `TOF_OBJECT_DEPTH`
3. Press ←→ to adjust `TOF_DEPTH_TOLERANCE`
4. Goal: Green circle on object, red zone around it
5. Note the values when done

**Update settings:**
```bash
nano config/sim_settings.py
```

Find and update:
```python
TOF_OBJECT_DEPTH = 0.5    # Your measured value
TOF_DEPTH_TOLERANCE = 0.3  # Your tolerance value
```

Save (Ctrl+X, Y, Enter)

### 5.3 Test Motor Speed Control (PWM)

Some motors may be too fast. Adjust PWM frequency:

```bash
nano src/motors_real.py
```

Look for PWM initialization. Adjust frequency if needed:
```python
self.pwm_a = GPIO.PWM(self.ENA, 1000)  # 1000 Hz frequency
```

Try: 500, 1000, 2000 Hz depending on motor response

---

## Part 6: Running SmartBin

### 6.1 First Test Run (Manual)

```bash
cd ~/smartbin_v4
python3 main_pi.py
```

**Expected output:**
```
[CAMERA] ArduCAM TOF initialized via CSI (320x240 @ 10fps)
[DETECT] TOF depth range: 0.5m ±0.3m
[RUNNING] Frames: 30, Catches: 0
[RUNNING] Frames: 60, Catches: 0
```

**Test interaction:**
1. Move hand near camera
2. Should see: `[DETECT] Ball at (xxx, yyy)`
3. Should see: `[PREDICT] Landing X = xxx px`
4. Motors should move toward predicted position

**Stop:** Press Ctrl+C

### 6.2 Run with Data Collection (Optional)

Collect throw data for ML training:

```bash
cd ~/smartbin_v4
python3 main_pi.py --collect-data
```

Data saved to `data/throws.csv`

### 6.3 Run with ML Predictor (Optional)

```bash
cd ~/smartbin_v4
python3 main_pi.py --ml
```

Uses trained ML model instead of Kalman filter

---

## Part 7: Production Deployment

### 7.1 Auto-Start on Boot

Create systemd service:

```bash
sudo nano /etc/systemd/system/smartbin.service
```

Paste:
```ini
[Unit]
Description=SmartBin Catch Robot
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/smartbin_v4
ExecStart=/usr/bin/python3 /home/pi/smartbin_v4/main_pi.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable smartbin.service
sudo systemctl start smartbin.service
```

Check status:
```bash
sudo systemctl status smartbin.service
journalctl -u smartbin.service -f  # View logs
```

### 7.2 Logging Setup

Send logs to file:

Edit `src/logger.py`:
```python
log_file = "/home/pi/smartbin_v4/logs/smartbin.log"
```

Create logs directory:
```bash
mkdir -p ~/smartbin_v4/logs
chmod 777 ~/smartbin_v4/logs
```

### 7.3 Performance Tuning

**Monitor CPU usage:**
```bash
top -bn1 | head -20
vcgencmd measure_temp  # Check temperature
vcgencmd measure_clock arm  # Check CPU frequency
```

**If slow (< 5 fps):**
1. Check thermal throttling: `vcgencmd measure_temp`
2. Add heatsink/fan if temp > 80°C
3. Reduce resolution (currently 320x240, minimum for TOF)
4. Check CPU load: `top`

**If motors jerky:**
1. Increase PWM frequency in `src/motors_real.py`
2. Reduce PID gains in `config/sim_settings.py`
3. Add capacitors across motor leads to reduce noise

### 7.4 Safety Shutdown

Create safe shutdown script:

```bash
cat > ~/shutdown.sh << 'SCRIPT'
#!/bin/bash
echo "Shutting down SmartBin..."
sudo systemctl stop smartbin.service
echo "Saving logs..."
sudo journalctl -u smartbin.service -n 100 > ~/smartbin_v4/logs/final_log.txt
echo "Done. Safe to remove power."
SCRIPT

chmod +x ~/shutdown.sh
```

Run: `./shutdown.sh`

---

## Part 8: Testing Checklist

### 8.1 Hardware Tests

- [ ] Raspberry Pi boots and shows login
- [ ] SSH access works
- [ ] CSI camera detected and working
- [ ] All GPIO pins respond
- [ ] L298N has 12V power (LED on)
- [ ] Motors spin in correct directions
- [ ] PWM speed control works

### 8.2 Software Tests

- [ ] `python3 tools/diagnose_camera.py` passes
- [ ] `python3 tools/tune_tof.py` shows depth visualization
- [ ] `python3 main_pi.py` runs without errors
- [ ] Object detection works (see position printed)
- [ ] Motor movement responds to detected objects
- [ ] Can stop with Ctrl+C cleanly

### 8.3 Integration Tests

- [ ] Place object at working distance
- [ ] See detection: `[DETECT] Ball at (x, y)`
- [ ] See prediction: `[PREDICT] Landing X = x px`
- [ ] Motors move to predicted position
- [ ] Repeat 10 times, smooth operation

### 8.4 Real-World Tests

- [ ] Start with slow throws (1-2 m/s)
- [ ] Increase speed gradually
- [ ] Test from different distances (0.5m - 2m)
- [ ] Test in different lighting conditions
- [ ] Test with various objects (same size/weight as ball)

---

## Part 9: Troubleshooting

### Problem: Camera not detected

**Symptoms:** `[CAMERA] Failed to initialize TOF camera`

**Solutions:**
1. Check CSI ribbon physically:
   ```bash
   libcamera-hello  # Should show preview
   ```

2. Verify CSI0 port:
   ```bash
   vcgencmd get_camera  # Should show: supported=1 detected=1
   ```

3. Check Pi configuration:
   ```bash
   sudo raspi-config
   # Interface Options → Camera → Enable
   # Reboot
   ```

4. Try different CSI port (CSI1):
   Edit `src/camera_real.py`, change camera index

### Problem: Motors don't move

**Symptoms:** Motors silent, no movement

**Solutions:**
1. Check L298N power:
   - Should have 12V across +12V and GND
   - Red LED should be on
   - Use multimeter if uncertain

2. Test GPIO directly:
   ```bash
   python3 << 'PYTHON'
   import RPi.GPIO as GPIO
   GPIO.setmode(GPIO.BCM)
   GPIO.setup(17, GPIO.OUT)
   GPIO.output(17, GPIO.HIGH)
   # Use multimeter on L298N IN1 pin - should read ~3.3V
   GPIO.cleanup()
   PYTHON
   ```

3. Check wiring:
   - Verify all 6 GPIO pins connected
   - Verify GND is shared between Pi and motor power
   - Verify motor leads are connected to L298N output

4. Test motor directly:
   - Connect motor leads directly to 12V battery
   - Motor should spin
   - If not, motor may be defective

### Problem: Object not detected

**Symptoms:** `[DETECT] No object in frame`

**Solutions:**
1. Run tuning tool:
   ```bash
   python3 tools/tune_tof.py
   ```
   - Check depth visualization
   - See min/max/mean depth values

2. Adjust parameters:
   - Is object at expected depth?
   - Increase `TOF_DEPTH_TOLERANCE` if needed
   - Try `find_object_by_proximity()` instead

3. Check camera is working:
   ```bash
   python3 << 'PYTHON'
   from src.camera_real import RealCamera
   from config.sim_settings import SimSettings
   
   camera = RealCamera(settings=SimSettings())
   depth = camera.get_depth_frame()
   print(f"Depth shape: {depth.shape}")
   print(f"Range: {depth.min():.2f}m - {depth.max():.2f}m")
   camera.cleanup()
   PYTHON
   ```

### Problem: Slow performance (< 5 fps)

**Symptoms:** Jerky movement, laggy detection

**Solutions:**
1. Check temperature:
   ```bash
   vcgencmd measure_temp
   ```
   - If > 80°C, add heatsink/fan
   - If thermal throttled, reduce load

2. Check CPU usage:
   ```bash
   top -bn1 | grep "Cpu(s)"
   ```
   - Should be < 80% idle
   - If high, profile with: `python3 -m cProfile main_pi.py`

3. Optimize:
   - Reduce detection area
   - Skip frames (process every Nth frame)
   - Use `find_object_by_proximity()` instead of `find_object()`

### Problem: Motors erratic/jerky

**Symptoms:** Motors stop/start, don't move smoothly

**Solutions:**
1. Check power supply:
   - 12V supply should be stable
   - Use scope/multimeter to check for ripple
   - Try different battery if available

2. Check wiring:
   - Add capacitor (100µF) across motor leads
   - Check for loose connections
   - Verify GND is solid

3. Reduce PID gains:
   ```python
   # config/sim_settings.py
   PID_KP = 5.0   # Reduce from 7.0
   PID_KI = 0.05  # Reduce from 0.1
   PID_KD = 0.5   # Reduce from 1.0
   ```

### Problem: Can't SSH into Pi

**Symptoms:** `Connection refused` or `Host unreachable`

**Solutions:**
1. Check network:
   ```bash
   # On Pi directly (with keyboard/monitor)
   hostname -I
   # Should show IP address
   ```

2. Find Pi's IP:
   ```bash
   # On laptop
   arp-scan --localnet | grep -i raspberry
   nmap -p 22 192.168.1.0/24  # Adjust subnet
   ```

3. Enable SSH in raspi-config:
   ```bash
   sudo raspi-config
   # Interface Options → SSH → Enable
   ```

### Problem: Import errors at startup

**Symptoms:** `ModuleNotFoundError: No module named...`

**Solutions:**
```bash
# Reinstall all dependencies
pip install --upgrade opencv-python numpy scipy pigpio

# Verify imports
python3 -c "import cv2, numpy, pigpio; print('OK')"
```

---

## Part 10: Maintenance & Monitoring

### 10.1 Regular Checks

**Daily:**
- [ ] Robot powers on cleanly
- [ ] Camera detects objects
- [ ] Motors respond to commands
- [ ] No error messages in logs

**Weekly:**
- [ ] Check temperature: `vcgencmd measure_temp`
- [ ] Review logs: `journalctl -u smartbin.service -n 50`
- [ ] Clean camera lens
- [ ] Check motor bearings for noise

**Monthly:**
- [ ] Update OS: `sudo apt update && sudo apt upgrade`
- [ ] Check disk space: `df -h`
- [ ] Backup logs and training data
- [ ] Test full catch sequence

### 10.2 Monitoring Script

Create health check:

```bash
cat > ~/healthcheck.sh << 'SCRIPT'
#!/bin/bash
echo "SmartBin Health Check - $(date)"

echo ""
echo "=== System ==="
vcgencmd measure_temp
vcgencmd get_clock arm | grep frequency

echo ""
echo "=== Storage ==="
df -h / | tail -1

echo ""
echo "=== Service ==="
sudo systemctl is-active smartbin.service

echo ""
echo "=== Network ==="
hostname -I

echo ""
echo "=== Processes ==="
ps aux | grep python3 | grep -v grep
SCRIPT

chmod +x ~/healthcheck.sh
./healthcheck.sh
```

### 10.3 Logging and Debugging

View live logs:
```bash
journalctl -u smartbin.service -f
```

Save debug logs:
```bash
python3 main_pi.py 2>&1 | tee ~/smartbin_v4/logs/debug_$(date +%s).log
```

---

## Part 11: Optimization Tips

### 11.1 Speed Optimization

If catching requires faster response:

```python
# config/sim_settings.py
KALMAN_Q = 0.1   # Increase process noise (trust sensor more)
KALMAN_R = 0.002 # Decrease measurement noise
PID_KP = 8.0     # Increase proportional gain (faster response)
```

### 11.2 Accuracy Optimization

If catching misses frequently:

```python
# config/sim_settings.py
TOF_DEPTH_TOLERANCE = 0.5  # Increase detection range
MIN_OBJECT_AREA = 30       # Decrease if detecting noise
POSITION_TOL = 0.02        # Tighter dead zone
```

### 11.3 Power Optimization

If running on limited battery:

1. Reduce frame rate: Modify main loop `time.sleep()`
2. Reduce motor speed (less current draw)
3. Use ML predictor (fewer frames needed)
4. Disable verbose logging (reduces file I/O)

---

## Part 12: Advanced Features

### 12.1 Web Dashboard (Optional)

Monitor remotely via web interface:

```bash
pip install flask flask-cors
```

Create `tools/web_dashboard.py` (basic version):

```python
from flask import Flask, jsonify
from src.camera_real import RealCamera
from src.detect_real import RealDetector
from config.sim_settings import SimSettings

app = Flask(__name__)
camera = RealCamera(settings=SimSettings())
detector = RealDetector(settings=SimSettings())

@app.route('/status')
def status():
    depth = camera.get_depth_frame()
    if depth is None:
        return jsonify({"error": "No camera"})
    
    obj = detector.find_object(depth)
    stats = detector.get_depth_stats(depth)
    
    return jsonify({
        "detected": obj is not None,
        "position": obj,
        "depth_stats": stats
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

Run: `python3 tools/web_dashboard.py`

Access from laptop: `http://smartbin.local:5000/status`

### 12.2 Data Logging for Analysis

Save detection data for analysis:

```python
# In main_pi.py, add:
import csv
with open('logs/detections.csv', 'a', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([time.time(), cx, cy, predicted_x])
```

Later analyze with pandas/matplotlib:
```bash
python3 << 'PYTHON'
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('logs/detections.csv')
plt.plot(df['predicted_x'])
plt.show()
PYTHON
```

---

## Summary Checklist

### Before First Run
- [ ] Hardware fully assembled and tested
- [ ] Raspberry Pi OS installed and updated
- [ ] All dependencies installed
- [ ] Camera verified working
- [ ] Motors verified working
- [ ] GPIO pins responding
- [ ] Configuration tuned

### Before Production Deployment
- [ ] All tests passing (Section 8)
- [ ] Real-world test successful
- [ ] Auto-start service enabled
- [ ] Logging configured
- [ ] Shutdown procedure tested
- [ ] Thermal management adequate

### Ongoing
- [ ] Daily health checks
- [ ] Weekly log reviews
- [ ] Monthly updates
- [ ] Quarterly performance analysis

---

## Emergency Contacts & Resources

**Raspberry Pi:**
- Official docs: https://www.raspberrypi.com/documentation/
- Troubleshooting: https://www.raspberrypi.com/forums/

**ArduCAM TOF:**
- GitHub: https://github.com/ArduCAM/Arducam_tof_camera
- Wiki: Check product documentation

**Motor Driver L298N:**
- Datasheet: Search "L298N datasheet" online
- Typical pinout and operation

**SmartBin Code:**
- Main script: `main_pi.py`
- Motor control: `src/motors_real.py`
- Camera: `src/camera_real.py`
- Detection: `src/detect_real.py`

---

## Final Notes

This deployment should get SmartBin operational in 2-3 hours. The most common issues are:

1. **CSI ribbon not fully seated** → Reseat firmly
2. **GND not shared between Pi and motor power** → Add jumper
3. **Camera parameters not tuned** → Run `tools/tune_tof.py`
4. **Motor direction wrong** → Swap motor leads

Once working, it's quite reliable. The main maintenance is keeping the camera lens clean and monitoring thermal performance.

Good luck deploying! 🚀
