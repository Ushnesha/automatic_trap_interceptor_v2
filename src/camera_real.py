"""
src/camera_real.py - Fixed with confidence filtering
"""
import numpy as np
import ArducamDepthCamera as ac

class RealCamera:
    def __init__(self, settings):
        self.S = settings
        self.cam = None
        self._init_camera()
        if self.cam is None:
            raise RuntimeError("[CAMERA] Failed to initialize camera")
        # Warmup
        for _ in range(5):
            self.get_depth_frame()
        print("[CAMERA] ArduCAM TOF ready!")

    def _init_camera(self):
        try:
            self.cam = ac.ArducamCamera()
            ret = self.cam.open(ac.Connection.CSI, 0)
            print(f"[CAMERA] Open: {ret}")
            ret = self.cam.start(ac.FrameType.DEPTH)
            print(f"[CAMERA] Start: {ret}")
            self.cam.setControl(ac.Control.RANGE, 4000)
            print("[CAMERA] Initialized successfully")
        except Exception as e:
            print(f"[CAMERA] Error: {e}")
            self.cam = None

    def get_depth_frame(self):
        if self.cam is None:
            return None
        try:
            frame = self.cam.requestFrame(2000)
            if frame is None:
                return None
            depth_mm = np.array(frame.depth_data).astype(np.float32)
            confidence = np.array(frame.confidence_data).astype(np.float32)
            self.cam.releaseFrame(frame)

            # Filter low confidence pixels
            bad = (confidence < 30) | (depth_mm < 100) | (depth_mm > 2000)
            depth_mm[bad] = 0

            # Convert to meters
            depth_m = depth_mm / 1000.0
            return depth_m
        except Exception as e:
            print(f"[CAMERA] Capture error: {e}")
            return None

    def get_frame(self):
        return self.get_depth_frame()

    def world_to_pixel_x(self, world_x):
        ppm_x = self.S.FRAME_WIDTH / self.S.ARENA_W
        return int((world_x + self.S.ARENA_W / 2) * ppm_x)

    def cleanup(self):
        if self.cam is not None:
            try:
                self.cam.stop()
                self.cam.close()
                print("[CAMERA] ArduCAM TOF stopped and closed")
            except Exception as e:
                print(f"[CAMERA] Cleanup error: {e}")
