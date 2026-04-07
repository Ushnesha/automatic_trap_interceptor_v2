"""
src/sim_motors.py
PID motor controller for L298N + Mecanum chassis.
Same interface as original sim_motors.py:
    move_to_x(predicted_pixel_x)
    center()
    stop()

On real Raspberry Pi: swap this file for motors.py
which sends GPIO PWM signals to L298N instead of
directly updating world._can_x.
"""


class SimMotors:

    def __init__(self, world, settings):
        self.world = world
        self.S     = settings
        self._vx   = 0.0
        self._target_px  = None
        self._integral   = 0.0
        self._prev_err   = None
        self._ppm_x      = settings.FRAME_WIDTH / settings.ARENA_W

        print(f"[MOTOR] PID motors ready. Max speed: {settings.CAN_MAX_SPEED} m/s")
        print(f"[MOTOR] KP={settings.PID_KP} KI={settings.PID_KI} KD={settings.PID_KD}")

    def move_to_x(self, target_x_pixels):
        """
        Move can to target pixel X using PID control.
        Same signature as original sim_motors.py.
        """
        self._target_px = target_x_pixels
        S  = self.S
        dt = S.SIM_TIMESTEP

        # Pixel → world meters
        target_m  = (target_x_pixels / self._ppm_x) - S.ARENA_W / 2
        current_m = self.world._can_x
        error     = target_m - current_m

        # Dead zone
        if abs(error) < S.POSITION_TOL:
            self._vx       = 0.0
            self._integral = 0.0
            self._apply()
            return

        # PID
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
        self._apply()

    def _apply(self):
        """Move the can by current velocity."""
        S     = self.S
        dt    = S.SIM_TIMESTEP
        new_x = self.world._can_x + self._vx * dt
        hw    = S.ARENA_W / 2 - S.CAN_WIDTH / 2
        new_x = max(-hw, min(hw, new_x))
        if new_x <= -hw or new_x >= hw:
            self._vx = 0.0
        self.world._can_x = new_x

    def center(self):
        """Reset can to center."""
        self.world._can_x = self.S.CAN_START_X
        self._vx          = 0.0
        self._integral    = 0.0
        self._prev_err    = None
        print("[MOTOR] Centered.")

    def stop(self):
        self._vx = 0.0

    def reset(self):
        self._vx         = 0.0
        self._target_px  = None
        self._integral   = 0.0
        self._prev_err   = None

    @property
    def vx(self):
        return self._vx

    @property
    def target_px(self):
        return self._target_px
