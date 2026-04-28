import numpy as np
import time
import scipy.ndimage as ndimage
 
class RealDetector:
    def __init__(self, settings):
        self.S = settings
        self.bg = None
        self.bg_frames = []
        self.calibrated = False
        self.CALIB_FRAMES = 100
        self.calib_start_time = time.time()
        
        # Background subtraction thresholds
        self.depth_diff_threshold = 0.08   # 8cm closer = new object
        self.min_object_pixels = 50       # Need 50+ pixels for detection
        self.max_object_pixels = 3000      # But not more than 3000
        
        # Distance filter
        self.MIN_DEPTH = 0.15
        self.MAX_DEPTH = 2.0
        
        print("[DETECT] === BACKGROUND SUBTRACTION DETECTOR ===")
        print("[DETECT] Only detects NEW objects appearing")
        print(f"[DETECT] Depth threshold: {self.depth_diff_threshold*100:.0f}cm")
        print(f"[DETECT] Min pixels: {self.min_object_pixels}, Max: {self.max_object_pixels}")
        print(f"[DETECT] Detection range: {self.MIN_DEPTH*100:.0f}cm to {self.MAX_DEPTH*100:.0f}cm")
        print("[DETECT] Calibrating for 5 seconds...")
        print("[DETECT] Keep area CLEAR - NO objects!")
 
    def find_object(self, depth_frame):
        if depth_frame is None:
            return None

        if not self.calibrated:
            # ... (keep your existing calibration)
            self.bg_frames.append(depth_frame.copy())
            progress = len(self.bg_frames)
            
            if progress % 10 == 0: # Faster feedback
                print(f"[DETECT] Calibrating... {progress}/100")
            
            if len(self.bg_frames) >= self.CALIB_FRAMES:
                # Use nanmedian to ignore 0s/nans if they exist
                bg_frames_array = np.array(self.bg_frames, dtype=np.float32)
                # Replace 0 with NaN so they don't mess up the median
                bg_frames_array[bg_frames_array == 0] = np.nan
                self.bg = np.nanmedian(bg_frames_array, axis=0)
                # Fill back NaNs with 0
                self.bg = np.nan_to_num(self.bg)
                
                self.calibrated = True
                self.bg_frames = []
                print(f"[DETECT] ✓ CALIBRATION COMPLETE!")
            return None

        # 1. Create a Diff Mask
        # Filter out anything further than the background or too close to the sensor
        diff = self.bg - depth_frame
        
        # 2. Binary Masking (The "Sweet Spot")
        # We only care about objects that are in front of the background 
        # but not closer than 0.3m (too close to lens)
        mask = (diff > 0.05) & (depth_frame > self.MIN_DEPTH) & (depth_frame < self.MAX_DEPTH)
        
        # 3. Clean up noise (Morphological Opening)
        # This removes tiny 1-2 pixel noise "speckles"
        mask = ndimage.binary_opening(mask, structure=np.ones((3,3)))
        
        # 4. Label connected components
        # This identifies "blobs" instead of just counting pixels
        labeled, num_features = ndimage.label(mask)
        
        if num_features > 0:
            # Find the largest blob (assumed to be the ball)
            sizes = ndimage.sum(mask, labeled, range(num_features + 1))
            max_label = np.argmax(sizes)
            
            # Check if the largest blob is within size constraints (e.g., 50 to 500 pixels)
            if 40 < sizes[max_label] < 800:
                # Get center of mass of the largest blob
                coords = ndimage.center_of_mass(mask, labeled, max_label)
                cy, cx = coords
                
                # Get the median depth of JUST that blob
                blob_depths = depth_frame[labeled == max_label]
                avg_depth = np.median(blob_depths)
                
                return (int(cx), int(cy), avg_depth)
                
        return None
 
    def get_calibration_status(self):
        if self.calibrated:
            return "ready"
        else:
            return f"calibrating {len(self.bg_frames)}/{self.CALIB_FRAMES}"