"""
src/camera_real.py
Real Pi Camera capture using OpenCV for Raspberry Pi 5.
Replaces src/sim_camera.py for real hardware deployment.

Supports:
  - libcamera backend (preferred for Pi 5)
  - Fallback to legacy camera interface
"""

import cv2
import numpy as np
import time


class RealCamera:
    """Real Pi Camera capture using OpenCV"""

    def __init__(self, settings):
        self.S = settings
        self.cap = None
        self._init_camera()

        if self.cap is None:
            raise RuntimeError("[CAMERA] Failed to initialize camera")

        # Warm up camera (discard first frames to stabilize)
        for _ in range(10):
            self.cap.read()

        print("[CAMERA] Real Pi Camera initialized (640x480 @ 30fps)")

    def _init_camera(self):
        """Initialize camera with libcamera backend, fallback to legacy"""
        try:
            # Try libcamera backend (preferred for Pi 5)
            self.cap = cv2.VideoCapture(
                "libcamerasrc ! video/x-raw,width=640,height=480 ! videoconvert ! "
                "video/x-raw,format=BGR ! appsink",
                cv2.CAP_GSTREAMER
            )
            if self.cap.isOpened():
                print("[CAMERA] Using libcamera backend")
                return
        except Exception as e:
            print(f"[CAMERA] libcamera init failed: {e}")

        # Fallback to legacy camera interface
        try:
            self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                print("[CAMERA] Using legacy camera interface")
                return
        except Exception as e:
            print(f"[CAMERA] Legacy camera init failed: {e}")

        self.cap = None

    def get_frame(self):
        """Capture frame from real camera"""
        if self.cap is None:
            return None

        ret, frame = self.cap.read()
        if not ret:
            print("[CAMERA] Failed to read frame")
            return None

        return frame

    def world_to_pixel_x(self, world_x):
        """Convert world meters to pixel X coordinate"""
        ppm_x = self.S.FRAME_WIDTH / self.S.ARENA_W
        pixel_x = (world_x + self.S.ARENA_W / 2) * ppm_x
        return int(pixel_x)

    def cleanup(self):
        """Release camera resources"""
        if self.cap is not None:
            self.cap.release()
            print("[CAMERA] Camera released")
