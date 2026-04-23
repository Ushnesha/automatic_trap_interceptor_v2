# SmartBin Deployment Quick Card

## 📋 Pre-Deployment Checklist

### Hardware Assembled
- [ ] Raspberry Pi 5 + heatsink
- [ ] ArduCAM TOF camera connected to CSI0
- [ ] 4x Mecanum wheels on motors
- [ ] 4x DC motors (12V, ~200-300 RPM)
- [ ] L298N motor driver
- [ ] 5V/3A power supply (Pi)
- [ ] 12V battery pack (motors, 5A+ capacity)
- [ ] Wiring complete per WIRING_REFERENCE.md
- [ ] Common GND between Pi and motor power ✓ CRITICAL

### Tools & Materials
- [ ] Multimeter (for testing)
- [ ] USB-C power cable
- [ ] Jumper wires and breadboard
- [ ] Laptop with SSH access
- [ ] microSD card (32GB+)

---

## 🚀 Deployment Steps

### Phase 1: OS Setup (30 min)

```bash
# On laptop, use Raspberry Pi Imager:
# Device: Raspberry Pi 5
# OS: Raspberry Pi OS (64-bit) Bookworm
# Settings: hostname=smartbin, SSH enabled, WiFi configured
# Write to microSD card
```

Insert SD card → Power on Pi → Wait 2 min

### Phase 2: SSH Access (5 min)

```bash
# From laptop:
ssh pi@smartbin.local
# or: ssh pi@<ip-address>

# Update system:
sudo apt update && sudo apt upgrade -y
# Takes ~10 minutes
```

### Phase 3: Install Dependencies (10 min)

```bash
# On Pi:
sudo apt install -y python3-picamera2 libcamera-tools python3-opencv
pip install --upgrade pip
pip install opencv-python numpy scipy RPi.GPIO flask
```

### Phase 4: Setup Code (5 min)

```bash
cd ~
git clone <your-repo> smartbin_v4
# or: git pull if already present
cd smartbin_v4
```

### Phase 5: Hardware Verification (15 min)

```bash
# Test GPIO:
python3 << 'PYTHON'
import RPi.GPIO as GPIO, time
GPIO.setmode(GPIO.BCM)
for pin in [17, 27, 23, 24, 12, 13]:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH); time.sleep(0.1)
GPIO.cleanup()
print("✓ GPIO OK")
PYTHON

# Test Camera:
libcamera-hello --timeout 3000

# Run Diagnostic:
python3 tools/diagnose_camera.py
# Should show all ✓ checks passing
```

### Phase 6: Configuration Tuning (20 min)

```bash
# Tune camera parameters:
python3 tools/tune_tof.py

# Interactive:
# 1. Place object at working distance
# 2. Adjust ↑↓ for TOF_OBJECT_DEPTH
# 3. Adjust ←→ for TOF_DEPTH_TOLERANCE
# 4. Target: green circle on object
# 5. Note the values

# Edit config:
nano config/sim_settings.py
# Update TOF_OBJECT_DEPTH and TOF_DEPTH_TOLERANCE
# Save: Ctrl+X, Y, Enter
```

### Phase 7: First Test Run (10 min)

```bash
# Start SmartBin:
cd ~/smartbin_v4
python3 main_pi.py

# Expected output:
# [CAMERA] ArduCAM TOF initialized...
# [DETECT] TOF depth range: 0.5m ±0.3m
# [RUNNING] Frames: 30, Catches: 0

# Test interaction:
# 1. Move hand near camera
# 2. Should see: [DETECT] Ball at (xxx, yyy)
# 3. Should see: [PREDICT] Landing X = xxx
# 4. Motors should move

# Stop: Ctrl+C
```

### Phase 8: Production Setup (5 min)

```bash
# Auto-start on boot:
sudo nano /etc/systemd/system/smartbin.service
```

Paste:
```ini
[Unit]
Description=SmartBin Robot
After=network.target pigpiod.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/smartbin_v4
ExecStart=/usr/bin/python3 /home/pi/smartbin_v4/main_pi.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable smartbin.service
sudo systemctl start smartbin.service

# Verify:
sudo systemctl status smartbin.service

# View logs:
journalctl -u smartbin.service -f
```

---

## ⚡ Quick Test Commands

```bash
# Health check:
vcgencmd measure_temp
vcgencmd get_camera

# Camera test:
libcamera-hello --timeout 1000

# GPIO test:
python3 -c "import RPi.GPIO as GPIO; print('✓ GPIO')"

# Full diagnostic:
python3 tools/diagnose_camera.py

# Motor test:
python3 << 'PYTHON'
from src.motors_real import RealMotors
from config.sim_settings import SimSettings
m = RealMotors(SimSettings())
m.motor_a(0.5); import time; time.sleep(1); m.motor_a(0)
m.cleanup(); print("✓ Motors OK")
PYTHON

# Live logs:
journalctl -u smartbin.service -f

# Stop service:
sudo systemctl stop smartbin.service
```

---

## 🔧 Troubleshooting Quick Fixes

| Problem | Quick Fix |
|---------|-----------|
| Camera not found | `libcamera-hello` → reseat CSI ribbon |
| Motors silent | Check 12V LED on L298N, check GND |
| No detection | Run `tools/tune_tof.py`, adjust depth range |
| Slow performance | `vcgencmd measure_temp` → add heatsink |
| Can't SSH | `hostname -I` on Pi, check IP address |
| Import errors | `pip install --upgrade opencv-python numpy scipy` |

---

## 📊 Performance Targets

After successful deployment:

| Metric | Target | How to Check |
|--------|--------|--------------|
| Frame rate | 8-10 fps | `[RUNNING]` log line |
| Detection latency | < 150ms | Visual responsiveness |
| Motor response | < 200ms | See movement on detection |
| Temperature | < 75°C | `vcgencmd measure_temp` |
| Catch accuracy | > 70% | Real throws test |

---

## 📚 Documentation Index

| Document | Purpose | Read Time |
|----------|---------|-----------|
| DEPLOYMENT_GUIDE_FULL.md | Complete reference | 30 min |
| WIRING_REFERENCE.md | Hardware connections | 15 min |
| CSI_SETUP.md | CSI camera details | 15 min |
| TOF_MIGRATION.md | TOF detection info | 10 min |
| SETUP_CHECKLIST.md | Interactive checklist | 20 min |

---

## ⏱ Total Deployment Time

| Phase | Time |
|-------|------|
| OS setup | 30 min |
| SSH + updates | 10 min |
| Dependencies | 10 min |
| Code setup | 5 min |
| Hardware verification | 15 min |
| Tuning | 20 min |
| First test | 10 min |
| Production setup | 5 min |
| **Total** | **~2-3 hours** |

---

## 🎯 Success Criteria

After deployment, you should see:

✓ Pi boots and SSH works  
✓ Camera detected by `libcamera-hello`  
✓ All GPIO pins respond  
✓ Motors spin on command  
✓ SmartBin detects objects  
✓ Motors move to predicted position  
✓ Service auto-starts on reboot  
✓ Catches working (10+ catches in test)

---

## 🆘 Emergency Commands

```bash
# Stop everything:
sudo systemctl stop smartbin.service

# View recent errors:
journalctl -u smartbin.service --no-pager | tail -20

# Reset GPIO (if stuck):
python3 -c "import RPi.GPIO; RPi.GPIO.cleanup()"

# Restart service:
sudo systemctl restart smartbin.service

# SSH without password (optional):
ssh-keygen -t rsa -f ~/.ssh/smartbin_key
# Copy ~/.ssh/smartbin_key.pub to Pi ~/.ssh/authorized_keys
```

---

## 📞 Common Issues

**Q: "Failed to initialize TOF camera"**  
A: Check CSI ribbon is fully seated. Run: `libcamera-hello`

**Q: "Motors don't spin"**  
A: Check 12V power on L298N. Check GND connection between Pi and battery.

**Q: "Connection refused" on SSH**  
A: Find Pi's IP: `arp-scan --localnet | grep -i raspberry`

**Q: "No object detected"**  
A: Run `python3 tools/tune_tof.py` and adjust depth thresholds.

**Q: "Slow/jerky movement"**  
A: Check temp: `vcgencmd measure_temp`. Add heatsink if >80°C.

---

## 🎓 Learning Resources

- Raspberry Pi Docs: https://www.raspberrypi.com/documentation/
- ArduCAM TOF: https://github.com/ArduCAM/Arducam_tof_camera
- L298N Driver: Search "L298N datasheet" for pinout/operation
- SmartBin Code: See `main_pi.py` for execution flow

---

## ✅ Final Checklist

Before calling deployment complete:

- [ ] SmartBin boots automatically on power
- [ ] Camera detects objects reliably
- [ ] Motors respond to commands
- [ ] Service auto-restarts on crash
- [ ] Logs saved to `logs/` directory
- [ ] Can SSH in and view status
- [ ] Catch rate > 70% in testing
- [ ] No error messages at startup
- [ ] Temperature < 75°C under load

---

**Deployment Ready?** Start with Phase 1 above! 🚀

Good luck! 🎉
