# SmartBin Hardware Wiring Reference

## Quick GPIO Pinout

```
Raspberry Pi 5 GPIO Layout (BCM numbering)

Pin Physical Layout:
┌─────────────────────────┐
│ Pi 5 GPIO Header (40-pin)│
├─────────────────────────┤
│ 3V3  ■ ■  5V            │
│ GPIO2 (SDA) ■ ■ 5V      │
│ GPIO3 (SCL) ■ ■ GND     │
│ GPIO4 ■ ■ GPIO17 → [IN1]│
│ GND ■ ■ GPIO27 → [IN2]  │
│ GPIO22 ■ ■ GPIO23 → [IN3]
│ GPIO10 ■ ■ GPIO24 → [IN4]
│ GPIO9 ■ ■ GND          │
│ GPIO11 ■ ■ GPIO8        │
│ GPIO7 ■ ■ GPIO25        │
│ GND ■ ■ GPIO12 → [ENA]  │
│ GPIO26 ■ ■ GPIO13 → [ENB]
│ GPIO19 ■ ■ GND          │
│ GPIO6 ■ ■ GPIO5         │
│ GPIO12 ■ ■ GPIO12       │
│ GPIO16 ■ ■ GPIO20       │
│ GPIO26 ■ ■ GND          │
│ GPIO21 ■ ■ GPIO26       │
│ GND ■ ■ GPIO3           │
└─────────────────────────┘

Pin details (relevant for SmartBin):
Pin  GPIO  Function
────────────────────────────────
11   17    L298N IN1 (Motor A forward)
13   27    L298N IN2 (Motor A backward)
16   23    L298N IN3 (Motor B forward)
18   24    L298N IN4 (Motor B backward)
32   12    L298N ENA (Motor A PWM)
33   13    L298N ENB (Motor B PWM)
GND  GND   L298N GND (common ground)
CSI0 --    ArduCAM TOF (ribbon cable)
```

## Wiring Connection Summary

### Camera (ArduCAM TOF)

```
ArduCAM TOF → Raspberry Pi CSI0
├─ CSI ribbon → CSI0 port
│  (Contacts face inward, fully seated)
└─ No separate power/GND needed
   (CSI port provides power)
```

### Motor Driver (L298N)

```
L298N Inputs (from Raspberry Pi GPIO):
┌──────────────────────────────┐
│ Input Pins (Signal)          │
├──────────────────────────────┤
│ IN1 ← GPIO 17 (pin 11)      │
│ IN2 ← GPIO 27 (pin 13)      │
│ IN3 ← GPIO 23 (pin 16)      │
│ IN4 ← GPIO 24 (pin 18)      │
│ ENA ← GPIO 12 (pin 32)      │ PWM
│ ENB ← GPIO 13 (pin 33)      │ PWM
│ GND ← Pi GND (any pin)      │
└──────────────────────────────┘

L298N Power:
┌──────────────────────────────┐
│ Power Pins                   │
├──────────────────────────────┤
│ +12V ← Battery+ (12V)        │
│ GND  ← Battery- (must share  │
│         common GND with Pi!) │
└──────────────────────────────┘

L298N Output:
┌──────────────────────────────┐
│ Motor Connections            │
├──────────────────────────────┤
│ OUT1, OUT2 ← Motor A (left)  │
│ OUT3, OUT4 ← Motor B (right) │
└──────────────────────────────┘
```

## Motor Connections to L298N

```
L298N Output Pins:
OUT1 ─┐
      ├─ Motor A (Left side)
OUT2 ─┘
      Both to same motor or
      LF + LR in parallel

OUT3 ─┐
      ├─ Motor B (Right side)
OUT4 ─┘
      Both to same motor or
      RF + RR in parallel
```

### Motor Parallel Configuration

If you have 4 motors total:

```
        Front
    [LF] [RF]
    [LR] [RR]
        Back

Connection:
L298N OUT1 ──┬─ LF motor
             └─ LR motor (parallel)

L298N OUT2 ──┬─ LF motor return
             └─ LR motor return

L298N OUT3 ──┬─ RF motor
             └─ RR motor (parallel)

L298N OUT4 ──┬─ RF motor return
             └─ RR motor return
```

**In code (`src/motors_real.py`):**
- Motor A = Left side (LF + LR)
- Motor B = Right side (RF + RR)

## Complete Wiring Diagram

```
POWER DISTRIBUTION:
┌─────────────────┐
│  5V USB Supply  │──── Raspberry Pi 5 (USB-C)
└─────────────────┘

┌─────────────────┐
│  12V Battery    │──┬─── L298N +12V input
│  Pack           │  └─── GND (common with Pi!)
└─────────────────┘

SIGNAL WIRING (Pi to L298N):
┌──────────────────┐
│ Raspberry Pi 5   │
├──────────────────┤
│ GPIO 17 (pin 11) ├──→ L298N IN1
│ GPIO 27 (pin 13) ├──→ L298N IN2
│ GPIO 23 (pin 16) ├──→ L298N IN3
│ GPIO 24 (pin 18) ├──→ L298N IN4
│ GPIO 12 (pin 32) ├──→ L298N ENA (PWM)
│ GPIO 13 (pin 33) ├──→ L298N ENB (PWM)
│ GND              ├──→ L298N GND
│ CSI0             ├──→ ArduCAM TOF
└──────────────────┘

MOTOR OUTPUT (L298N to Motors):
┌──────────────────┐
│    L298N         │
├──────────────────┤
│ OUT1, OUT2       ├──→ Motor A (Left)
│ OUT3, OUT4       ├──→ Motor B (Right)
└──────────────────┘
```

## Breadboard Layout (Optional)

If using a breadboard:

```
5V Power Rail        GND Rail
    ││                 ││
    ││                 ││
    ├─ Pi 5V          ├─ Pi GND
    ├─ L298N +5V(opt) ├─ L298N GND
    │                 ├─ Battery GND
    ││                 ││
```

## Voltage Levels

| Component | Voltage | Current |
|-----------|---------|---------|
| Raspberry Pi 5 | 5V | 3A |
| L298N Logic (GPIO) | 3.3V | ~20mA |
| L298N Motor Power | 12V | 2-4A (motor dependent) |
| Each DC Motor | 12V | 0.5-1A |

## Cable Types & Gauges

| Purpose | Wire Gauge | Notes |
|---------|-----------|-------|
| Pi Power (USB-C) | Built-in | Use quality cable |
| GPIO to L298N | 22-24 AWG | Solid jumper wires |
| Motor Power (+12V) | 16-18 AWG | Heavy current |
| Motor Return (GND) | 16-18 AWG | Heavy current |
| Motor Leads | 18-20 AWG | Motor dependent |

## Common Issues & Fixes

### Motors Don't Respond
```
Check:
1. GPIO connections to L298N IN pins
2. PWM connections to ENA/ENB
3. L298N has 12V power (LED on)
4. GND is common between Pi and battery
5. Test GPIO output directly with multimeter
```

### Motors Move Wrong Direction
```
Fix:
1. Swap motor leads on L298N OUT terminals
2. Or change direction logic in code:
   - motor_a(-0.5) instead of motor_a(0.5)
```

### Weak Motor Power
```
Check:
1. 12V battery voltage (should be 11.5V+)
2. Battery current capacity (need 3A+)
3. L298N connections are tight
4. No loose wires in power path
```

### Camera Not Detected
```
Check:
1. CSI ribbon fully inserted (contacts inward)
2. CSI0 port (not CSI1)
3. Pi camera interface enabled in raspi-config
```

## Testing Wiring

### Quick GPIO Test
```bash
python3 << 'PYTHON'
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.output(17, GPIO.HIGH)
# Measure pin 11 with multimeter - should read 3.3V
GPIO.cleanup()
PYTHON
```

### L298N Logic Test
```bash
# With multimeter on IN1 pin of L298N:
# Should jump between 0V and 3.3V when GPIO toggles
```

### Motor Test
```bash
# Run:
python3 << 'PYTHON'
from src.motors_real import RealMotors
from config.sim_settings import SimSettings
motors = RealMotors(SimSettings())
motors.motor_a(0.5)  # Should spin Motor A
import time; time.sleep(1)
motors.motor_a(0)
motors.cleanup()
PYTHON
```

## Power Supply Recommendations

**Raspberry Pi:**
- Minimum: 5V/2A USB-C
- Recommended: 5V/3A USB-C (with headroom)
- Quality: Use reputable brand (not cheap cables)

**Motors:**
- Minimum: 12V/2A (if 2 motors max)
- Recommended: 12V/5A battery (for 4 motors)
- Type: Lithium battery or lead-acid recommended
- Optional: Use separate battery from Pi (isolates noise)

**Total System:**
- If combined 5V+12V from one supply: Need ~8A total capacity
- Better: Separate 5V supply for Pi, 12V for motors

## Mechanical Considerations

### Motor Mounting
- Secure motors firmly to chassis
- Align axes parallel (not skewed)
- Use shock mounts if vibration is issue

### Wheel Alignment
- All 4 wheels same size
- Mecanum wheels oriented correctly (45° rollers)
- Tire pressure even (if pneumatic)

### Cable Management
- Keep power cables away from signal cables
- Secure power cables to prevent shorts
- Leave slack for vibration damping
- Label all connections

---

## Verification Checklist

Before power-on:
- [ ] All GPIO pins connected correctly
- [ ] 12V power connected to L298N
- [ ] GND jumper between Pi and motor power
- [ ] Motor leads connected to OUT pins
- [ ] CSI camera ribbon inserted fully
- [ ] No loose connections visible
- [ ] No bent pins on L298N or Pi
- [ ] Power supplies in OFF position

On first power:
- [ ] Pi boots without issues
- [ ] No magical smoke
- [ ] L298N LED turns on (12V present)
- [ ] Camera detected by libcamera
- [ ] GPIO pins respond to commands

---

End of Wiring Reference. For detailed assembly, see DEPLOYMENT_GUIDE_FULL.md
