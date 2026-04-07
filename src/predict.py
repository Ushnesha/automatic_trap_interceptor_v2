"""
src/predict.py
Kalman filter + ballistic predictor.
Same interface as original predict.py:
    add_point((cx, cy))
    get_predicted_landing_x() → float (pixels) or None
    reset()

Fixes the original:
  - Kalman filter smooths noisy detections
  - Works from frame 2 (not frame 4+)
  - All math stays in world-meters, converts back to pixels at end
  - Uses FRAME_HEIGHT/ARENA_H for vertical scale (not ARENA_W)
"""

import math
import time
import numpy as np


class Predictor:

    def __init__(self, settings):
        self.S = settings
        self._history  = []      # list of {x, z, t} in world meters
        self._last_x   = None    # last predicted landing pixel X
        self._updates  = 0

        # Kalman state [x, z, vx, vz]
        self._kx  = None
        self._kP  = np.eye(4) * 1.0
        self._dt  = settings.SIM_TIMESTEP

        # pixels → meters conversion
        self._ppm_x = settings.FRAME_WIDTH  / settings.ARENA_W
        self._ppm_z = settings.FRAME_HEIGHT / settings.ARENA_H

        print(f"[PREDICT] Min points: {settings.MIN_POINTS_TO_PREDICT}")
        print(f"[PREDICT] ppm_x={self._ppm_x:.1f}  ppm_z={self._ppm_z:.1f}")

    def reset(self):
        self._history  = []
        self._last_x   = None
        self._updates  = 0
        self._kx       = None
        self._kP       = np.eye(4) * 1.0

    def add_point(self, position):
        """
        Feed a camera detection (pixel cx, cy).
        Converts to world meters and runs Kalman update.
        """
        cx, cy = position
        S = self.S

        # Pixel → world meters
        wx = (cx / self._ppm_x) - S.ARENA_W / 2
        wz = S.ARENA_H - (cy / self._ppm_z)

        self._history.append({'x': wx, 'z': wz, 't': time.time()})

        # Kalman update
        self._kalman_update(wx, wz)
        self._updates += 1

    def get_predicted_landing_x(self):
        """
        Returns predicted landing X in PIXEL coordinates.
        Same return type as original predict.py.
        """
        if self._updates < self.S.MIN_POINTS_TO_PREDICT:
            return None
        if self._kx is None:
            return None

        x0  = float(self._kx[0, 0])
        z0  = float(self._kx[1, 0])
        vx  = float(self._kx[2, 0])
        vz  = float(self._kx[3, 0])
        g   = self.S.GRAVITY

        if z0 <= self.S.FLOOR_Y + 0.05:
            return self._last_x

        # Solve: z0 + vz*t - 0.5*g*t² = 0
        a =  0.5 * g
        b = -vz
        c = -z0
        disc = b*b - 4*a*c

        if disc < 0:
            return self._last_x

        t1 = (-b + math.sqrt(disc)) / (2*a)
        t2 = (-b - math.sqrt(disc)) / (2*a)

        landing_t = None
        for t in [t1, t2]:
            if t > 0.01:
                if landing_t is None or t < landing_t:
                    landing_t = t

        if landing_t is None:
            return self._last_x

        # Landing X in world meters
        landing_x_m = x0 + vx * landing_t

        # Clamp to arena
        hw = self.S.ARENA_W / 2
        landing_x_m = max(-hw, min(hw, landing_x_m))

        # Convert back to pixel X (same as original)
        landing_x_px = (landing_x_m + self.S.ARENA_W/2) * self._ppm_x
        landing_x_px = max(0.0, min(float(self.S.FRAME_WIDTH), landing_x_px))

        self._last_x = landing_x_px
        return landing_x_px

    def get_velocity(self):
        if self._kx is None:
            return (0, 0)
        return (float(self._kx[2,0]), float(self._kx[3,0]))

    # ── Kalman internals ──────────────────────────────────────────

    def _kalman_update(self, wx, wz):
        dt = self._dt
        g  = self.S.GRAVITY

        # State transition
        F = np.array([
            [1, 0, dt,  0],
            [0, 1,  0, dt],
            [0, 0,  1,  0],
            [0, 0,  0,  1],
        ], dtype=float)

        # Gravity input
        B = np.array([[0], [0.5*g*dt*dt], [0], [g*dt]])

        # Observation (see x and z)
        H = np.array([[1,0,0,0],[0,1,0,0]], dtype=float)

        q = self.S.KALMAN_Q
        Q = np.diag([q*0.1, q*0.1, q, q])

        r = self.S.KALMAN_R
        R = np.eye(2) * r

        z = np.array([[wx], [wz]])

        if self._kx is None:
            # Initialize on first detection
            self._kx = np.array([[wx],[wz],[0.0],[0.0]])
            self._kP = np.eye(4) * 0.5
            return

        # Predict
        xp = F @ self._kx - B          # minus = gravity pulls down
        Pp = F @ self._kP @ F.T + Q

        # Update
        y  = z - H @ xp
        S_ = H @ Pp @ H.T + R
        K  = Pp @ H.T @ np.linalg.inv(S_)
        self._kx = xp + K @ y
        self._kP = (np.eye(4) - K @ H) @ Pp
