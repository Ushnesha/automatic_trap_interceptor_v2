"""
src/detect.py
HSV color detector.

In SIMULATION: reads ball position directly from world (fast, accurate).
On REAL Pi:    replace get_frame() + find_object() with real cv2 code below.

Real Pi code (drop-in):
    import cv2
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    hsv  = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower, upper)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        c = max(contours, key=cv2.contourArea)
        M = cv2.moments(c)
        cx = int(M['m10']/M['m00'])
        cy = int(M['m01']/M['m00'])
        return (cx, cy)
"""
import numpy as np

class Detector:
    def __init__(self, settings):
        self.S = settings
        self.lower = np.array(settings.HSV_LOWER, dtype=np.uint8)
        self.upper = np.array(settings.HSV_UPPER, dtype=np.uint8)
        print(f"[DETECT] HSV range: {settings.HSV_LOWER} -> {settings.HSV_UPPER}")

    def find_object(self, frame):
        """
        Find orange ball in BGR frame.
        Returns (cx, cy) pixel center or None.
        """
        if frame is None:
            return None

        # Fast path: find orange pixels using vectorized numpy
        # Extract channels
        b = frame[:,:,0].astype(np.int16)
        g = frame[:,:,1].astype(np.int16)
        r = frame[:,:,2].astype(np.int16)

        # Orange detection in BGR space (faster than full HSV conversion)
        # Orange: high R, medium G, low B
        orange_mask = (r > 150) & (g > 60) & (g < 180) & (b < 80) & (r > g + 40)

        ys, xs = np.where(orange_mask)
        if len(xs) < self.S.MIN_OBJECT_AREA:
            return None

        return int(np.mean(xs)), int(np.mean(ys))

    def find_object_hsv(self, frame):
        """Full HSV method — use this on real Pi with cv2."""
        if frame is None:
            return None
        hsv  = self._bgr_to_hsv(frame)
        mask = self._in_range(hsv, self.lower, self.upper)
        ys, xs = np.where(mask > 0)
        if len(xs) < self.S.MIN_OBJECT_AREA:
            return None
        return int(np.mean(xs)), int(np.mean(ys))

    def _bgr_to_hsv(self, bgr):
        rgb = bgr[:,:,::-1].astype(np.float32) / 255.0
        r,g,b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
        maxc = np.maximum(np.maximum(r,g),b)
        minc = np.minimum(np.minimum(r,g),b)
        diff = maxc - minc + 1e-8
        h = np.zeros_like(maxc)
        mr=maxc==r; mg=maxc==g; mb=maxc==b
        h[mr]=(60*(g[mr]-b[mr])/diff[mr])%360
        h[mg]=60*(b[mg]-r[mg])/diff[mg]+120
        h[mb]=60*(r[mb]-g[mb])/diff[mb]+240
        h = h/2
        s = np.where(maxc>0,(diff-1e-8)/maxc,0)*255
        v = maxc*255
        return np.stack([h,s,v],axis=2).astype(np.uint8)

    def _in_range(self, hsv, lower, upper):
        h,s,v=hsv[:,:,0],hsv[:,:,1],hsv[:,:,2]
        return (((h>=lower[0])&(h<=upper[0])) &
                ((s>=lower[1])&(s<=upper[1])) &
                ((v>=lower[2])&(v<=upper[2]))).astype(np.uint8)*255
