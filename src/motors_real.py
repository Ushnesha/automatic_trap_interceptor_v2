"""
src/motors_real.py
Real L298N motor control for Raspberry Pi 5 + Mecanum chassis.
Replaces src/sim_motors.py for real hardware deployment.

GPIO Pinout:
  IN1 (GPIO 17)  → Motor A direction
  IN2 (GPIO 27)  → Motor A direction
  IN3 (GPIO 22)  → Motor B direction
  IN4 (GPIO 23)  → Motor B direction
  ENA (GPIO 12)  → PWM Motor A speed
  ENB (GPIO 13)  → PWM Motor B speed
"""

from gpiozero import DigitalOutputDevice, PWMLED
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
        self.IN1 = 17   # Motor A direction 1
        self.IN2 = 27   # Motor A direction 2
        self.IN3 = 22   # Motor B direction 1
        self.IN4 = 23   # Motor B direction 2
        self.ENA = 12   # PWM Motor A (speed)
        self.ENB = 13   # PWM Motor B (speed)

        # Setup GPIO using gpiozero
        self.in1 = DigitalOutputDevice(self.IN1)
        self.in2 = DigitalOutputDevice(self.IN2)
        self.in3 = DigitalOutputDevice(self.IN3)
        self.in4 = DigitalOutputDevice(self.IN4)
        self.pwm_a = PWMLED(self.ENA, frequency=1000)
        self.pwm_b = PWMLED(self.ENB, frequency=1000)

        self.pwm_a.value = 0
        self.pwm_b.value = 0

        print(f"[MOTOR] Real L298N motors initialized")
        print(f"[MOTOR] Max speed: {settings.CAN_MAX_SPEED} m/s")
        print(f"[MOTOR] KP={settings.PID_KP} KI={settings.PID_KI} KD={settings.PID_KD}")

    def move_to_x(self, target_x_pixels):
        """Move can to target X using PID control"""
        self._target_px = target_x_pixels
        S = self.S
        dt = S.SIM_TIMESTEP

        # Pixel → world meters
        target_m = (target_x_pixels / self._ppm_x) - S.ARENA_W / 2
        # TODO: Get actual position from encoder/IMU instead of assuming center
        current_m = 0.0
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
        """Convert velocity to PWM signals for motors"""
        max_speed = self.S.CAN_MAX_SPEED
        duty = abs(velocity) / max_speed
        duty = max(0.0, min(1.0, duty))

        if velocity > 0.1:
            # Strafe right: Motor A forward, Motor B backward
            self.in1.on()
            self.in2.off()
            self.in3.off()
            self.in4.on()
        elif velocity < -0.1:
            # Strafe left: Motor A backward, Motor B forward
            self.in1.off()
            self.in2.on()
            self.in3.on()
            self.in4.off()
        else:
            # Stop all motors
            self.in1.off()
            self.in2.off()
            self.in3.off()
            self.in4.off()
            duty = 0.0

        self.pwm_a.value = duty
        self.pwm_b.value = duty

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
        self.pwm_a.close()
        self.pwm_b.close()
        self.in1.close()
        self.in2.close()
        self.in3.close()
        self.in4.close()
        print("[MOTOR] GPIO cleaned up")

    @property
    def vx(self):
        return self._vx

    @property
    def target_px(self):
        return self._target_px
