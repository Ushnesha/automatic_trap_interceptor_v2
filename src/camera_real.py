import numpy as np
import ArducamDepthCamera as ac

class RealCamera:
    def __init__(self, settings):
        self.S = settings
        self.cam = None
        self.frame_count = 0
        self.valid_count = 0
        self._init_camera()
        if self.cam is None:
            raise RuntimeError("[CAMERA] Failed to initialize")
        print("[CAMERA] Warming up sensor...")
        for i in range(10):
            f = self.get_frame()
            if f is not None:
                valid = np.sum(f > 0)
                print(f"[CAMERA] Warmup {i+1}: {valid} valid pixels")
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

    def get_frame(self):
        if self.cam is None:
            return None
        try:
            frame = self.cam.requestFrame(2000)
            if frame is None:
                return None

            depth_mm = np.array(frame.depth_data).astype(np.float32)
            conf = np.array(frame.confidence_data).astype(np.float32)
            self.cam.releaseFrame(frame)

            self.frame_count += 1

            # Less aggressive filtering - keep more pixels
            bad = (depth_mm < 50) | (depth_mm > 5000)
            depth_mm[bad] = 0

            # Convert to meters
            depth_m = depth_mm / 1000.0

            valid = np.sum(depth_m > 0)
            self.valid_count += 1

            if self.frame_count % 30 == 0:
                rate = self.valid_count / self.frame_count * 100
                print(f"[CAMERA] Frames: {self.frame_count}, Valid: {self.valid_count} ({rate:.1f}%), Last frame: {valid} pixels")

            return depth_m

        except Exception as e:
            print(f"[CAMERA] Error: {e}")
            return None

    def get_depth_frame(self):
        return self.get_frame()

    def world_to_pixel_x(self, world_x):
        ppm_x = self.S.FRAME_WIDTH / self.S.ARENA_W
        return int((world_x + self.S.ARENA_W / 2) * ppm_x)

    def cleanup(self):
        if self.cam is not None:
            try:
                self.cam.stop()
                self.cam.close()
                print("[CAMERA] Stopped. Valid frame rate: "
                      f"{self.valid_count/max(self.frame_count,1)*100:.1f}%")
            except Exception as e:
                print(f"[CAMERA] Cleanup error: {e}")
