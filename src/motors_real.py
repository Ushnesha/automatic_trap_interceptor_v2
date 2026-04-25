

"""
src/motors_real.py - Using working gpiozero Motor class
GPIO Pinout:
  FL: forward=17, backward=18
  FR: forward=22, backward=23
  BL: forward=5,  backward=6
  BR: forward=19, backward=26

NOTE: rotate_right() from mecanum_gpiozero.py = actual strafe right
      rotate_left()  from mecanum_gpiozero.py = actual strafe left
"""
from gpiozero import Motor
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device

Device.pin_factory = LGPIOFactory(chip=4)

class RealMotors:
    def __init__(self, settings):
        self.S = settings
        self._vx = 0.0
        self._target_px = None
        self._integral = 0.0
        self._prev_err = None
        self._ppm_x = settings.FRAME_WIDTH / settings.ARENA_W
        self.current_m = 0.0

        self.front_left  = Motor(forward=17, backward=18)
        self.front_right = Motor(forward=22, backward=23)
        self.back_left   = Motor(forward=5,  backward=6)
        self.back_right  = Motor(forward=19, backward=26)

        self.stop()
        print("[MOTOR] Real motors initialized using gpiozero Motor class")
        print(f"[MOTOR] Max speed: {settings.CAN_MAX_SPEED} m/s")
        print(f"[MOTOR] KP={settings.PID_KP} KI={settings.PID_KI} KD={settings.PID_KD}")

    def _strafe_right(self, speed):
        """Strafe right - uses rotate_right pattern from working test"""
        self.front_left.forward(speed)
        self.front_right.backward(speed)
        self.back_left.forward(speed)
        self.back_right.backward(speed)

    def _strafe_left(self, speed):
        """Strafe left - uses rotate_left pattern from working test"""
        self.front_left.backward(speed)
        self.front_right.forward(speed)
        self.back_left.backward(speed)
        self.back_right.forward(speed)

    def stop(self):
        self.front_left.stop()
        self.front_right.stop()
        self.back_left.stop()
        self.back_right.stop()

    def move_to_x(self, target_x_pixels):
        """Move can to target X position using PID control with position estimation"""
        self._target_px = target_x_pixels
        S = self.S
        dt = S.SIM_TIMESTEP

        """# 1. Update estimated position based on previous velocity"""
        """# This creates the feedback loop so 'error' eventually reaches zero"""
        self.current_m += self._vx * dt 

        """# 2. Convert pixel target to meters relative to center"""
        target_m = (target_x_pixels / self._ppm_x) - S.ARENA_W / 2
        error = target_m - self.current_m

        """# 3. DEADZONE: Stop if we are within the tolerance"""
        if abs(error) < S.POSITION_TOL:
            self._vx = 0.0
            self._integral = 0.0
            self._prev_err = None
            self.stop()
            return

        """# 4. PID: INTEGRAL (Accumulate error over time)"""
        self._integral += error * dt
        """# Anti-windup: limit the integral to prevent runaway speed"""
        max_i = S.CAN_MAX_SPEED / max(S.PID_KI, 0.001)
        self._integral = max(-max_i, min(max_i, self._integral))

        """# 5. PID: DERIVATIVE (Rate of change of error)"""
        deriv = 0.0
        if self._prev_err is not None and dt > 0:
            deriv = (error - self._prev_err) / dt
        self._prev_err = error

        """# 6. CALCULATE COMMANDED VELOCITY"""
        cmd = S.PID_KP * error + S.PID_KI * self._integral + S.PID_KD * deriv 
        """# Limit speed to settings"""
        cmd = max(-S.CAN_MAX_SPEED, min(S.CAN_MAX_SPEED, cmd))

        """ # 7. ACCELERATION LIMITING (Smooths out the movement)"""
        max_delta = S.CAN_ACCEL * dt
        if cmd > self._vx + max_delta:
            cmd = self._vx + max_delta
        elif cmd < self._vx - max_delta:
            cmd = self._vx - max_delta

        self._vx = cmd
        self._apply_velocity(self._vx)
    def _apply_velocity(self, velocity):
        """Convert velocity to motor commands"""
        max_speed = self.S.CAN_MAX_SPEED
        duty = abs(velocity) / max_speed
        duty = max(0.0, min(1.0, duty))

        if velocity > 0.01:
            self._strafe_right(duty)
            direction = "RIGHT"
        elif velocity < -0.01:
            self._strafe_left(duty)
            direction = "LEFT"
        else:
            self.stop()
            direction = "STOP"
            duty = 0.0

        print(f"[MOTOR] {direction} velocity={velocity:.2f} duty={duty:.2f}")

    def center(self):
        self._vx = 0.0
        self._integral = 0.0
        self._prev_err = None
        self.stop()
        print("[MOTOR] Centered")

    def reset(self):
        self._vx = 0.0
        self._target_px = None
        self._integral = 0.0
        self._prev_err = None

    def cleanup(self):
        self.stop()
        self.front_left.close()
        self.front_right.close()
        self.back_left.close()
        self.back_right.close()
        print("[MOTOR] GPIO cleaned up")

    @property
    def vx(self):
        return self._vx

    @property
    def target_px(self):
        return self._target_px
