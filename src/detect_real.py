"""
src/detect_real.py
Real orange ball detection using OpenCV for Raspberry Pi.
Replaces src/detect.py for real hardware deployment.

Uses HSV color space filtering with morphological operations.
"""

import cv2
import numpy as np


class RealDetector:
    """Real orange ball detection using OpenCV and HSV"""

    def __init__(self, settings):
        self.S = settings
        self.lower = np.array(settings.HSV_LOWER, dtype=np.uint8)
        self.upper = np.array(settings.HSV_UPPER, dtype=np.uint8)
        print(f"[DETECT] HSV range: {settings.HSV_LOWER} -> {settings.HSV_UPPER}")

    def find_object(self, frame):
        """
        Find orange ball in real camera frame.
        Returns (cx, cy) pixel center or None.
        """
        if frame is None:
            return None

        # Convert BGR to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Create mask based on HSV range
        mask = cv2.inRange(hsv, self.lower, self.upper)

        # Morphological operations to reduce noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        # Find largest contour (ball)
        largest = max(contours, key=cv2.contourArea)

        # Check minimum area
        if cv2.contourArea(largest) < self.S.MIN_OBJECT_AREA:
            return None

        # Calculate centroid using moments
        M = cv2.moments(largest)
        if M["m00"] == 0:
            return None

        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        return (cx, cy)

    def find_object_fast(self, frame):
        """
        Fast BGR-based detection (alternative, no HSV conversion).
        Use if performance is critical.
        """
        if frame is None:
            return None

        # Extract BGR channels
        b = frame[:, :, 0].astype(np.int16)
        g = frame[:, :, 1].astype(np.int16)
        r = frame[:, :, 2].astype(np.int16)

        # Orange detection in BGR space
        orange_mask = (r > 150) & (g > 60) & (g < 180) & (b < 80) & (r > g + 40)

        ys, xs = np.where(orange_mask)
        if len(xs) < self.S.MIN_OBJECT_AREA:
            return None

        return int(np.mean(xs)), int(np.mean(ys))
