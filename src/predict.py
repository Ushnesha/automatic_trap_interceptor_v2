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
        cx, cy, depth = position
        S = self.S

        # Pixel → world meters
        wx = (cx - S.FRAME_WIDTH/2) * (depth / S.FOCAL_LENGTH_X)
        wy = S.CAMERA_HEIGHT_METERS - ((cy - S.FRAME_HEIGHT/2) * (depth / S.FOCAL_LENGTH_Y))
        wz = depth

        self._history.append({'x': wx, 'y': wy, 'z': wz, 't': time.time()})

        # Kalman update
        self._kalman_update(wx, wy, wz)
        self._updates += 1

    def get_predicted_landing_x(self):
        if self._updates < self.S.MIN_POINTS_TO_PREDICT or self._kx is None:
            return None

        # Unpack Kalman states (Position and Velocity)
        # x, y, z are positions; vx, vy, vz are velocities
        x0, y0, z0, vx, vy, vz = self._kx.flatten()
        g = self.S.GRAVITY

        # If the ball is already on the floor, don't predict
        if y0 <= self.S.FLOOR_Y + 0.02:
            return self._last_x

        # 1. Solve for Time to Impact (landing_t)
        # Equation: y0 + vy*t - 0.5*g*t^2 = 0 (Floor level)
        # This is a standard quadratic: at^2 + bt + c = 0
        a = -0.5 * g
        b = vy
        c = y0 - self.S.FLOOR_Y

        disc = b**2 - 4*a*c
        if disc < 0:
            return self._last_x

        # We want the positive root (future time)
        t_impact = (-b - math.sqrt(disc)) / (2*a)

        # 2. Calculate Landing X and Z
        # Project forward using linear velocity
        landing_x_m = x0 + vx * t_impact
        landing_z_m = z0 + vz * t_impact # Where it hits relative to the can's depth

        # 3. Convert Landing X back to pixels for motor control
        # Map meters to the motor's coordinate system
        landing_x_px = (landing_x_m + self.S.ARENA_W/2) * self._ppm_x
        
        # Clamp to frame
        landing_x_px = max(0.0, min(float(self.S.FRAME_WIDTH), landing_x_px))

        self._last_x = landing_x_px
        return landing_x_px

    def get_velocity(self):
        if self._kx is None:
            return (0, 0)
        return (float(self._kx[2,0]), float(self._kx[3,0]))

    # ── Kalman internals ──────────────────────────────────────────

    def _kalman_update(self, wx, wy, wz):
        dt = self._dt
        g  = self.S.GRAVITY

        # 1. State Transition Matrix (F)
        # [x, y, z, vx, vy, vz]
        F = np.array([
            [1, 0, 0, dt, 0,  0],  # x = x + vx*dt
            [0, 1, 0, 0,  dt, 0],  # y = y + vy*dt
            [0, 0, 1, 0,  0,  dt], # z = z + vz*dt
            [0, 0, 0, 1,  0,  0],  # vx = vx
            [0, 0, 0, 0,  1,  0],  # vy = vy
            [0, 0, 0, 0,  0,  1],  # vz = vz
        ], dtype=float)

        # 2. Gravity Control Input (B)
        # Only the vertical axis (y) and its velocity (vy) are affected by g
        # y = y - 0.5*g*dt^2
        # vy = vy - g*dt
        B = np.zeros((6, 1))
        B[1, 0] = 0.5 * g * dt**2
        B[4, 0] = g * dt

        # 3. Observation Matrix (H)
        # We observe x, y, and z positions directly from the sensor
        H = np.array([
            [1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0]
        ], dtype=float)

        # 4. Noise Covariance Matrices
        q = self.S.KALMAN_Q
        # Lower noise for position, higher for velocity estimation
        Q = np.diag([q*0.1, q*0.1, q*0.1, q, q, q])

        r = self.S.KALMAN_R
        R = np.eye(3) * r

        # 5. Measurement Vector
        z = np.array([[wx], [wy], [wz]])

        # 6. Initialization
        if self._kx is None:
            # Initial state: positions from camera, velocities start at 0
            self._kx = np.array([[wx], [wy], [wz], [0.0], [0.0], [0.0]])
            self._kP = np.eye(6) * 1.0
            return

        # 7. Predict Phase
        # xp = F*x - B (pulling down on y)
        xp = F @ self._kx - B
        Pp = F @ self._kP @ F.T + Q

        # 8. Update Phase (Correction)
        y_err = z - H @ xp
        S_inv = np.linalg.inv(H @ Pp @ H.T + R)
        K = Pp @ H.T @ S_inv
        
        self._kx = xp + K @ y_err
        self._kP = (np.eye(6) - K @ H) @ Pp
