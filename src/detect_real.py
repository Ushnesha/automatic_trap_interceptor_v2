"""
src/detect_real.py
Object detection using ArduCAM TOF depth data.

Instead of HSV color filtering, uses depth thresholding to find objects.
Objects are detected as connected regions within expected depth range.
"""

import cv2
import numpy as np
from scipy import ndimage


class RealDetector:
    """TOF depth-based object detection"""

    def __init__(self, settings):
        self.S = settings
        print(f"[DETECT] TOF depth range: {settings.TOF_OBJECT_DEPTH:.1f}m ±{settings.TOF_DEPTH_TOLERANCE:.1f}m")
        print(f"[DETECT] Valid depth: {settings.TOF_MIN_DEPTH:.1f}m - {settings.TOF_MAX_DEPTH:.1f}m")

    def find_object(self, depth_frame):
        """
        Find object in TOF depth frame.
        Returns (cx, cy) pixel center or None.

        Args:
            depth_frame: numpy array (H, W) with depth in meters

        Returns:
            (cx, cy) or None
        """
        if depth_frame is None:
            return None

        h, w = depth_frame.shape
        
        # Filter: keep only valid depth values in expected range
        min_d = self.S.TOF_OBJECT_DEPTH - self.S.TOF_DEPTH_TOLERANCE
        max_d = self.S.TOF_OBJECT_DEPTH + self.S.TOF_DEPTH_TOLERANCE
        
        mask = (depth_frame >= min_d) & (depth_frame <= max_d)
        mask = mask.astype(np.uint8) * 255

        # Morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Find connected components
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        # Find largest contour (object)
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

    def find_object_by_proximity(self, depth_frame):
        """
        Alternative: find closest object (minimum depth).
        Use if objects are well-separated from background.
        """
        if depth_frame is None:
            return None

        # Filter invalid/zero depth
        valid = (depth_frame > self.S.TOF_MIN_DEPTH) & (depth_frame < self.S.TOF_MAX_DEPTH)
        
        if not np.any(valid):
            return None

        # Find closest pixels
        min_depth = depth_frame[valid].min()
        closest_mask = (depth_frame == min_depth) & valid

        # Extract coordinates
        ys, xs = np.where(closest_mask)
        if len(xs) < self.S.MIN_OBJECT_AREA:
            return None

        return int(np.mean(xs)), int(np.mean(ys))

    def get_depth_stats(self, depth_frame):
        """Debug: get depth statistics for tuning"""
        if depth_frame is None:
            return None
        
        valid = (depth_frame > 0) & (depth_frame < 10)
        if not np.any(valid):
            return {"mean": 0, "min": 0, "max": 0}
        
        valid_depth = depth_frame[valid]
        return {
            "mean": float(np.mean(valid_depth)),
            "min": float(np.min(valid_depth)),
            "max": float(np.max(valid_depth)),
            "std": float(np.std(valid_depth))
        }
