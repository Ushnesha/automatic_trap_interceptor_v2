"""
src/camera_real.py
Real ArduCAM TOF camera capture for Raspberry Pi 5.

Uses ArduCAM SDK (ArducamDepthCamera) for native depth sensing via CSI port.
Outputs raw depth data (distance in meters from camera lens).
"""

import numpy as np
import sys
import os

arducam_path = os.path.expanduser('~/Arducam_tof_camera-main')
if arducam_path not in sys.path:
    sys.path.insert(0, arducam_path)

try:
    import ArducamDepthCamera as ac
    ARDUCAM_AVAILABLE = True
except ImportError:
    ARDUCAM_AVAILABLE = False


class RealCamera:
    """Real ArduCAM TOF depth camera via CSI using ArducamDepthCamera SDK"""

    def __init__(self, settings):
        self.S = settings
        self.cam = None
        self.ac = ac if ARDUCAM_AVAILABLE else None

        if not ARDUCAM_AVAILABLE:
            raise RuntimeError("[CAMERA] ArducamDepthCamera SDK not found. Check ~/Arducam_tof_camera-main")

        self._init_camera()

        if self.cam is None:
            raise RuntimeError("[CAMERA] Failed to initialize ArduCAM TOF camera")

        # Warm up camera (discard first frames)
        for _ in range(5):
            self.get_depth_frame()

        info = self.cam.getCameraInfo()
        print(f"[CAMERA] ArduCAM TOF initialized via CSI ({info.width}x{info.height})")

    def _init_camera(self):
        """Initialize ArduCAM TOF camera using ArducamDepthCamera SDK"""
        try:
            self.cam = self.ac.ArducamCamera()

            ret = self.cam.open(self.ac.Connection.CSI, 0)
            if ret != 0:
                print(f"[CAMERA] Failed to open camera. Error code: {ret}")
                self.cam = None
                return

            ret = self.cam.start(self.ac.FrameType.DEPTH)
            if ret != 0:
                print(f"[CAMERA] Failed to start camera. Error code: {ret}")
                self.cam.close()
                self.cam = None
                return

            self.cam.setControl(self.ac.Control.RANGE, 4000)
            print("[CAMERA] ArduCAM TOF SDK initialized successfully")

        except Exception as e:
            print(f"[CAMERA] Failed to initialize camera: {e}")
            self.cam = None

    def get_depth_frame(self):
        """
        Capture depth frame from ArduCAM TOF camera.
        Returns numpy array of shape (H, W) with depth in meters.
        Returns None on failure.
        """
        if self.cam is None:
            return None

        try:
            frame = self.cam.requestFrame(2000)

            if frame is None:
                return None

            if isinstance(frame, self.ac.DepthData):
                depth_mm = frame.depth_data
                depth_m = depth_mm.astype(np.float32) / 1000.0
                self.cam.releaseFrame(frame)
                return depth_m

            self.cam.releaseFrame(frame)
            return None

        except Exception as e:
            print(f"[CAMERA] Failed to capture depth frame: {e}")
            return None

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
        if self.cam is not None:
            try:
                self.cam.stop()
                self.cam.close()
                print("[CAMERA] ArduCAM TOF stopped and closed")
            except Exception as e:
                print(f"[CAMERA] Error during cleanup: {e}")
