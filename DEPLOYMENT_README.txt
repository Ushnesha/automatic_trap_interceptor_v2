╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                     SmartBin v4: REAL-WORLD DEPLOYMENT GUIDE                ║
║                                                                              ║
║               Complete system for catching objects with a robot             ║
║          using ArduCAM TOF camera, Kalman prediction, and GPIO motors       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

📋 START HERE
═════════════════════════════════════════════════════════════════════════════

1. Read: DEPLOYMENT_START_HERE.md (quick overview, 5 min)
2. Read: REAL_WORLD_DEPLOYMENT.md (complete guide, 30 min)
3. Execute: Parts 1-5 of guide (assembly, setup, verification)
4. Success: SmartBin catches objects!


📚 DOCUMENTATION STRUCTURE
═════════════════════════════════════════════════════════════════════════════

For Quick Reference:
  → DEPLOYMENT_START_HERE.md      (5 min read)
  → DEPLOYMENT_QUICK_CARD.md      (10 min read)

For Complete Setup:
  → REAL_WORLD_DEPLOYMENT.md      (30 min read) ⭐ MAIN GUIDE
    Part 1: Hardware Assembly (60-90 min)
    Part 2: Software Setup (30-40 min)
    Part 3: Hardware Verification (20-30 min)
    Part 4: Configuration Tuning (20-30 min)
    Part 5: First Test Run (10-15 min)
    Part 6: Data Collection & ML (optional)
    Part 7: Auto-Start Setup (optional)
    Part 8: Performance Optimization (optional)
    Part 9: Field Testing (validation)

For Hardware Details:
  → WIRING_REFERENCE.md           (GPIO pinouts and electrical)
  → TOF_CSI_CHANGES.md            (ArduCAM TOF specific)

For Understanding the System:
  → EXECUTION_FLOW.md             (data flow, algorithms, tuning)
  → main_pi.py                    (entry point - read the structure)

For Deployment Checklists:
  → DEPLOYMENT_GUIDE_FULL.md      (comprehensive reference)
  → SETUP_CHECKLIST.md            (interactive checklist)


🔧 QUICK COMMAND REFERENCE
═════════════════════════════════════════════════════════════════════════════

Connect to Pi:
  ssh pi@smartbin.local

Run SmartBin:
  python3 main_pi.py

Tune Camera (interactive):
  python3 tools/tune_tof.py

Check Diagnostics:
  python3 tools/diagnose_camera.py

View Auto-Start Logs:
  sudo journalctl -u smartbin.service -f

Check Temperature:
  vcgencmd measure_temp


⚡ TYPICAL DEPLOYMENT TIMELINE
═════════════════════════════════════════════════════════════════════════════

Total Time: 2-3 hours

Hardware Assembly            | 60-90 min
├─ Mount motors & wheels     | 30 min
├─ Mount Pi & drivers        | 15 min
├─ Electrical wiring         | 30 min
└─ Safety checks             | 15 min

Software Setup              | 30-40 min
├─ Raspberry Pi OS           | 5 min
├─ SSH & system update       | 10 min
├─ Install dependencies      | 10 min
├─ Clone code                | 5 min
└─ Install ArduCAM SDK       | 10 min

Hardware Verification       | 20-30 min
├─ GPIO test                 | 5 min
├─ Camera test               | 5 min
├─ Motor test (no wheels!)   | 5 min
└─ Full diagnostic           | 10 min

Camera Tuning               | 20-30 min
├─ Run tune_tof.py           | 15 min
├─ Update config             | 5 min
└─ Verify settings           | 5 min

First Test                  | 10-15 min
├─ Start main_pi.py          | 2 min
├─ Manual interaction test   | 8 min
└─ Troubleshoot              | 5 min

TOTAL                       | 2-3 hours


🎯 WHAT HAPPENS WHEN YOU RUN IT
═════════════════════════════════════════════════════════════════════════════

$ python3 main_pi.py

[CAMERA] ArduCAM TOF initialized via CSI (320x240)
[DETECT] TOF depth range: 0.5m ±0.3m
[MOTOR] Real L298N motors initialized
[SUCCESS] All modules loaded. Ready to catch!

[Place object in camera view]

[DETECT] Ball at (160, 120)        ← Object detected
[PREDICT] Landing X = 150.5px      ← Prediction calculated
[MOTOR] RIGHT velocity=0.45        ← Robot moves right

[Object lands in bin]

[RUNNING] Frames: 30, Catches: 0
[RUNNING] Frames: 60, Catches: 1   ← Catch recorded!


📦 WHAT YOU NEED
═════════════════════════════════════════════════════════════════════════════

Hardware:
  ✓ Raspberry Pi 5 + heatsink
  ✓ ArduCAM TOF camera module
  ✓ 4x 12V DC motors (~200-300 RPM)
  ✓ 4x Mecanum wheels
  ✓ L298N motor driver
  ✓ 12V battery pack (5A+)
  ✓ 5V/3A USB-C power supply
  ✓ Jumper wires & breadboard
  ✓ Multimeter (for testing)

Software (all included):
  ✓ main_pi.py (entry point)
  ✓ src/camera_real.py (ArduCAM interface)
  ✓ src/detect_real.py (depth-based detection)
  ✓ src/predict.py (Kalman + physics)
  ✓ src/motors_real.py (GPIO control)
  ✓ config/sim_settings.py (tunable parameters)
  ✓ tools/tune_tof.py (camera calibration)


🔑 KEY CONCEPTS
═════════════════════════════════════════════════════════════════════════════

SENSE (Camera)
  ArduCAM TOF captures depth frame at camera distance
  Output: 2D array of distances in meters

DETECT (Find Object)
  Filter depth by expected range (e.g., 0.5m ±0.3m)
  Find centroid of depth cluster
  Output: (x, y) pixel coordinates

PREDICT (Calculate Landing)
  Kalman filter smooths noisy detections
  Track velocity from position history
  Physics: solve ballistic trajectory
  Output: X coordinate where object will land

ACT (Move Robots)
  PID controller calculates motor command
  Accelerate/decelerate smoothly
  GPIO pins control direction & speed
  Result: Robot positioned to catch


⚠️ CRITICAL SAFETY POINTS
═════════════════════════════════════════════════════════════════════════════

1. REMOVE WHEELS before testing motors (spinning robot is dangerous!)
2. COMMON GROUND: Battery GND → L298N GND → Pi GND (critical!)
3. DO NOT SHARE POWER: Pi (5V) and motors (12V) must be separate supplies
4. CSI RIBBON: Push lever DOWN to lock ribbon in place
5. TEST FIRST: Verify each layer (GPIO, camera, motors) before full system


🐛 QUICK TROUBLESHOOTING
═════════════════════════════════════════════════════════════════════════════

Camera not found
  → Reseat CSI ribbon (contacts face inward, lever down)
  → Run: libcamera-hello
  → Reboot: sudo reboot

Motors don't move
  → Check 12V power LED on L298N (should be on)
  → Check GND continuity: Battery → L298N → Pi
  → Test GPIO directly with multimeter

No object detected
  → Run: python3 tools/tune_tof.py
  → Place object at working distance
  → Adjust depth thresholds until object highlighted green

Slow FPS (< 5 frames/sec)
  → Check temperature: vcgencmd measure_temp (should be < 75°C)
  → Reduce MIN_POINTS_TO_PREDICT from 4 to 2
  → Ensure heatsink is installed on Pi

Motors jerky or overshooting
  → Increase PID_KD (adds damping)
  → Decrease PID_KP if too oscillatory
  → Check battery voltage (should be ≥ 11V)


📊 SUCCESS METRICS
═════════════════════════════════════════════════════════════════════════════

Frame Rate:          Target 8-10 FPS on Pi 5
Detection Rate:      > 90% of objects in view
Latency:             < 200ms from throw to motor
Catch Accuracy:      > 70% with trained system
Temperature:         < 75°C under load
Power Draw:          < 5A total


🎓 LEARNING RESOURCES
═════════════════════════════════════════════════════════════════════════════

Raspberry Pi:
  https://www.raspberrypi.com/documentation/

ArduCAM TOF:
  https://github.com/ArduCAM/Arducam_tof_camera

L298N Motor Driver:
  Search "L298N datasheet" for pinout and operation

SmartBin Code Structure:
  See EXECUTION_FLOW.md for detailed algorithms


✅ FINAL CHECKLIST
═════════════════════════════════════════════════════════════════════════════

Before Power-On:
  [ ] All GPIO wires securely connected
  [ ] 12V power connected to L298N
  [ ] Common GND between Pi and battery
  [ ] CSI camera ribbon fully seated
  [ ] No loose wires or bent pins
  [ ] Wheels REMOVED from motors

After First Boot:
  [ ] Pi boots without errors
  [ ] L298N power LED on (12V present)
  [ ] Camera detected: libcamera-hello
  [ ] GPIO test passes
  [ ] Motor test spins (no wheels)
  [ ] Diagnostic tool passes all checks

Before Real Deployment:
  [ ] main_pi.py runs without crashes
  [ ] Objects detected when placed near camera
  [ ] Motors respond to detected positions
  [ ] Temperature stable < 75°C
  [ ] FPS meets target (8+ FPS)
  [ ] Manual test catches > 70%


🚀 NEXT STEPS
═════════════════════════════════════════════════════════════════════════════

1. Read DEPLOYMENT_START_HERE.md for overview
2. Read REAL_WORLD_DEPLOYMENT.md Part 1 for hardware assembly
3. Gather components
4. Follow guide step-by-step
5. Test each phase before moving on
6. Deploy and enjoy!


💡 PRO TIPS
═════════════════════════════════════════════════════════════════════════════

• Start with simulator (sim_main.py) to understand system before real hardware
• Test each layer independently (camera, detection, motors) before full system
• Collect real-world data and train ML model for better accuracy
• Run tune_tof.py whenever deploying to new environment
• Monitor temperature during operation (heatsink is important)
• Use SSH to monitor logs live while running: journalctl -u smartbin.service -f
• Save tuned configuration (TOF_OBJECT_DEPTH, etc.) for next deployment


📞 IF YOU GET STUCK
═════════════════════════════════════════════════════════════════════════════

1. Check EXECUTION_FLOW.md for algorithm details
2. Run tools/diagnose_camera.py for full system check
3. Test each layer independently (see debugging section)
4. Check console output for error messages
5. Verify wiring matches WIRING_REFERENCE.md exactly
6. Check that camera can see objects: libcamera-hello


═══════════════════════════════════════════════════════════════════════════════

YOUR SYSTEM IS PRODUCTION-READY

You have all the code, wiring, and configuration needed to deploy SmartBin v4.
Follow the guide step-by-step and you'll have a working object-catching robot
in 2-3 hours.

Good luck! 🎉

═══════════════════════════════════════════════════════════════════════════════
