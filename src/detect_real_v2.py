import numpy as np
import time
 
class RealDetector:
    def __init__(self, settings):
        self.S = settings
        self.bg = None
        self.bg_frames = []
        self.calibrated = False
        self.CALIB_FRAMES = 100
        self.MIN_PIXELS = 100      # Lowered from 400 (sensor is sparse)
        self.MAX_PIXELS = 2000     # Raised from 1500
        self.calib_start_time = time.time()
        
        print("[DETECT] Calibration mode: collecting background frames")
        print(f"[DETECT] Target: {self.CALIB_FRAMES} frames at ~20fps = ~5 seconds")
        print("[DETECT] Keep the area clear - no objects in frame")
 
    def find_object(self, depth_frame):
        if depth_frame is None:
            return None
 
        # ─────────────────────────────────────────────────────────
        # CALIBRATION PHASE
        # ─────────────────────────────────────────────────────────
        if not self.calibrated:
            # Only accept frames with sufficient valid data
            valid_pixels = np.count_nonzero(depth_frame > 0)
            
            if valid_pixels < 50:
                # Frame is mostly empty - don't use it
                return None
            
            # Frame is valid - add to calibration set
            self.bg_frames.append(depth_frame.copy())
            progress = len(self.bg_frames)
            
            # Log progress every 10 frames
            if progress % 10 == 0:
                elapsed = time.time() - self.calib_start_time
                fps = progress / max(elapsed, 0.1)
                print(f"[DETECT] Calibration {progress}/{self.CALIB_FRAMES} "
                      f"({100*progress//self.CALIB_FRAMES}%) - {fps:.1f} fps, "
                      f"{valid_pixels} pixels/frame")
            
            # Calibration complete
            if len(self.bg_frames) >= self.CALIB_FRAMES:
                # ─────────────────────────────────────────────────
                # FIX: Use MEAN instead of MEDIAN for noisy sensors
                # ─────────────────────────────────────────────────
                # Convert all frames to float for averaging
                bg_frames_array = np.array(self.bg_frames, dtype=np.float32)
                # Average across all frames (axis 0)
                self.bg = np.mean(bg_frames_array, axis=0)
                
                # Threshold: only keep pixels that were valid in >50% of frames
                # This handles noise by requiring consistency
                valid_in_frames = np.sum(bg_frames_array > 0, axis=0)
                threshold_count = self.CALIB_FRAMES // 2
                self.bg[valid_in_frames < threshold_count] = 0
                
                self.calibrated = True
                self.bg_frames = []
                
                # Verify calibration result
                bg_valid = np.count_nonzero(self.bg > 0)
                print(f"[DETECT] ✓ Calibration done! Background: {bg_valid} valid pixels")
                print("[DETECT] Ready to detect objects")
            
            return None
 
        # ─────────────────────────────────────────────────────────
        # DETECTION PHASE (after calibration)
        # ─────────────────────────────────────────────────────────
        
        # Safety check: if background is still invalid, can't detect
        if self.bg is None or np.count_nonzero(self.bg > 0) < 50:
            return None
        
        # ─────────────────────────────────────────────────────────
        # FIX: Improved depth difference detection
        # ─────────────────────────────────────────────────────────
        # Find pixels that are:
        # 1. Valid in current frame
        # 2. Valid in background
        # 3. Significantly closer than background (8cm threshold)
        new_obj = (
            (depth_frame > 0) &           # Current frame has valid data
            (self.bg > 0) &               # Background has valid data
            ((self.bg - depth_frame) > 0.08) &  # At least 8cm closer
            ((self.bg - depth_frame) < 2.0)     # But not more than 2m closer (sensor noise)
        )
        
        n = int(np.sum(new_obj))
        
        # Reject if too few or too many pixels
        if n < self.MIN_PIXELS or n > self.MAX_PIXELS:
            return None
        
        # Calculate centroid
        rows, cols = np.where(new_obj)
        if len(rows) == 0:
            return None
        
        cx = int(cols.mean())
        cy = int(rows.mean())
        
        # Sanity check: object should be in reasonable image region
        if cx < 0 or cx >= depth_frame.shape[1] or cy < 0 or cy >= depth_frame.shape[0]:
            return None
        
        return (cx, cy)
 
    def get_calibration_status(self):
        """For diagnostics: return current calibration progress"""
        if self.calibrated:
            return "ready"
        else:
            return f"calibrating {len(self.bg_frames)}/{self.CALIB_FRAMES}"
