"""
src/camera_real.py
Real ArduCAM TOF camera capture for Raspberry Pi 5.

Supports TOF depth sensing at 320x240 resolution via CSI port.
Outputs raw depth data (distance in mm from camera lens).
"""

import numpy as np
import time


class RealCamera:
    """Real ArduCAM TOF depth camera via CSI"""

    def __init__(self, settings):
        self.S = settings
        self.cap = None
        self._init_camera()

        if self.cap is None:
            raise RuntimeError("[CAMERA] Failed to initialize TOF camera")

        # Warm up camera (discard first frames)
        for _ in range(5):
            self.cap.read()

        print("[CAMERA] ArduCAM TOF initialized via CSI (320x240 @ 10fps)")

    def _init_camera(self):
        """Initialize ArduCAM TOF camera via CSI port"""
        try:
            import cv2
            from picamera2 import Picamera2
            
            # Use Picamera2 for CSI camera on Pi 5
            self.picam2 = Picamera2()
            config = self.picam2.create_preview_configuration(
                main={"format": "RGB888", "size": (self.S.FRAME_WIDTH, self.S.FRAME_HEIGHT)}
            )
            self.picam2.configure(config)
            self.picam2.start()
            
            self.use_picamera2 = True
            print("[CAMERA] TOF camera initialized via CSI (Picamera2)")
            return
            
        except ImportError:
            print("[CAMERA] Picamera2 not available, trying libcamera...")
            self._init_libcamera()
        except Exception as e:
            print(f"[CAMERA] Picamera2 init failed: {e}")
            self._init_libcamera()

    def _init_libcamera(self):
        """Fallback: Initialize via libcamera GStreamer pipeline"""
        try:
            import cv2
            
            # libcamera pipeline for TOF depth output
            pipeline = (
                "libcamerasrc camera-name=arducam_tof ! "
                "video/x-raw,width=320,height=240,format=BGR ! "
                "videoconvert ! "
                "video/x-raw,format=BGR ! appsink"
            )
            
            self.cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
            
            if self.cap.isOpened():
                self.use_picamera2 = False
                print("[CAMERA] TOF camera initialized via libcamera")
                return
                
        except Exception as e:
            print(f"[CAMERA] libcamera init failed: {e}")

        self.cap = None
        self.use_picamera2 = False

    def get_depth_frame(self):
        """
        Capture depth frame from TOF camera via CSI.
        Returns numpy array of shape (H, W) with depth in meters.
        Returns None on failure.
        """
        if self.use_picamera2:
            try:
                frame = self.picam2.capture_array()
                if frame is None:
                    return None
                
                # Convert RGB to depth (depends on camera output format)
                # ArduCAM TOF typically outputs depth in first channel or as grayscale
                if frame.ndim == 3 and frame.shape[2] == 3:
                    # Use first channel as depth (in mm), convert to meters
                    depth = frame[:, :, 0].astype(np.float32) / 1000.0
                else:
                    depth = frame.astype(np.float32) / 1000.0
                
                return depth
                
            except Exception as e:
                print(f"[CAMERA] Picamera2 capture failed: {e}")
                return None

        else:
            # Fallback to OpenCV
            if self.cap is None:
                return None

            ret, frame = self.cap.read()
            if not ret:
                print("[CAMERA] Failed to read depth frame")
                return None

            # Convert BGR to depth (first channel)
            if frame.ndim == 3:
                depth = frame[:, :, 0].astype(np.float32) / 1000.0
            else:
                depth = frame.astype(np.float32) / 1000.0

            return depth

    def get_frame(self):
        """Wrapper for compatibility — returns depth frame"""
        return self.get_depth_frame()

    def world_to_pixel_x(self, world_x):
        """Convert world meters to pixel X coordinate"""
        ppm_x = self.S.FRAME_WIDTH / self.S.ARENA_W
        pixel_x = (world_x + self.S.ARENA_W / 2) * ppm_x
        return int(pixel_x)

    def cleanup(self):
        """Release camera resources"""
        if self.use_picamera2:
            try:
                self.picam2.stop()
                print("[CAMERA] Picamera2 stopped")
            except:
                pass
        elif self.cap is not None:
            self.cap.release()
            print("[CAMERA] TOF camera released")
