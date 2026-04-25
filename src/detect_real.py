"""
src/detect_real.py - Calibrated background detection
"""
import numpy as np
import time

class RealDetector:
    def __init__(self, settings):
        self.S = settings
        self.bg = None
        self.bg_frames = []
        self.calibrated = False
        self.CALIB_FRAMES = 100  # ~5 seconds at 20fps
        self.MIN_PIXELS = 400
        self.MAX_PIXELS = 1500
        print("[DETECT] Calibrating background - keep area clear for 5 seconds...")

    def find_object(self, depth_frame):
        if depth_frame is None:
            return None

        # Build background
        if not self.calibrated:
            valid = depth_frame.copy()
            self.bg_frames.append(valid)
            if len(self.bg_frames) >= self.CALIB_FRAMES:
                self.bg = np.median(self.bg_frames, axis=0)
                self.calibrated = True
                self.bg_frames = []
                print("[DETECT] Calibration done! Throw something!")
            return None

        # Detect object vs background
        new_obj = (
            (depth_frame > 0) &
            (self.bg > 0) &
            ((self.bg - depth_frame) > 0.08)  # 8cm closer than background
        )

        n = int(np.sum(new_obj))

        if n < self.MIN_PIXELS or n > self.MAX_PIXELS:
            return None

        rows, cols = np.where(new_obj)
        cx = int(cols.mean())
        cy = int(rows.mean())

        return (cx, cy)
