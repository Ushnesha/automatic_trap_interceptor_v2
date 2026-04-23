"""
tools/tune_tof.py
Real-time TOF depth visualization and parameter tuning.

Run: python3 tools/tune_tof.py

Interactive tool to visualize depth and adjust detection thresholds.
Helps find optimal TOF_OBJECT_DEPTH and TOF_DEPTH_TOLERANCE.
"""

import sys
import cv2
import numpy as np

try:
    from src.camera_real import RealCamera
    from src.detect_real import RealDetector
    from config.sim_settings import SimSettings
except ImportError as e:
    print(f"Import failed: {e}")
    print("Make sure you're in the smartbin_v4 directory")
    sys.exit(1)


def visualize_depth(depth_frame, detector):
    """Create visualization of depth frame with detected object"""
    if depth_frame is None:
        return None

    h, w = depth_frame.shape

    # Normalize depth for display (0-255)
    valid = depth_frame > 0
    if np.any(valid):
        depth_min = depth_frame[valid].min()
        depth_max = depth_frame[valid].max()
        depth_norm = np.clip((depth_frame - depth_min) / (depth_max - depth_min + 1e-6) * 255, 0, 255)
    else:
        depth_norm = np.zeros_like(depth_frame)

    # Create RGB visualization
    vis = cv2.cvtColor(depth_norm.astype(np.uint8), cv2.COLOR_GRAY2BGR)

    # Overlay detection mask
    min_d = detector.S.TOF_OBJECT_DEPTH - detector.S.TOF_DEPTH_TOLERANCE
    max_d = detector.S.TOF_OBJECT_DEPTH + detector.S.TOF_DEPTH_TOLERANCE
    mask = ((depth_frame >= min_d) & (depth_frame <= max_d)).astype(np.uint8)

    # Red channel = detection zone
    vis[mask > 0, 2] = 255

    # Draw detected object center
    obj = detector.find_object(depth_frame)
    if obj:
        cx, cy = obj
        cv2.circle(vis, (cx, cy), 5, (0, 255, 0), -1)
        cv2.circle(vis, (cx, cy), 15, (0, 255, 0), 2)

    return vis, depth_min if np.any(valid) else 0, depth_max if np.any(valid) else 0


def main():
    settings = SimSettings()
    camera = RealCamera(settings)
    detector = RealDetector(settings)

    print("[TUNE] TOF Depth Tuning Tool")
    print("[TUNE] Press 'q' to quit")
    print("[TUNE] Use arrow keys to adjust parameters")
    print(f"[TUNE] Current: depth={settings.TOF_OBJECT_DEPTH:.2f}m ±{settings.TOF_DEPTH_TOLERANCE:.2f}m")

    try:
        while True:
            depth = camera.get_depth_frame()
            if depth is None:
                print("[TUNE] Failed to get depth frame")
                break

            stats = detector.get_depth_stats(depth)
            vis, d_min, d_max = visualize_depth(depth, detector)

            if vis is not None:
                # Display stats overlay
                text = f"Min: {d_min:.2f}m  Max: {d_max:.2f}m  Mean: {stats['mean']:.2f}m"
                cv2.putText(vis, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                text = f"Depth: {detector.S.TOF_OBJECT_DEPTH:.2f}m  Tol: ±{detector.S.TOF_DEPTH_TOLERANCE:.2f}m"
                cv2.putText(vis, text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                cv2.imshow("TOF Depth Tuning", vis)

            key = cv2.waitKey(30) & 0xFF
            if key == ord('q'):
                break
            elif key == 82:  # Up arrow
                detector.S.TOF_OBJECT_DEPTH += 0.05
                print(f"[TUNE] Depth → {detector.S.TOF_OBJECT_DEPTH:.2f}m")
            elif key == 84:  # Down arrow
                detector.S.TOF_OBJECT_DEPTH = max(0.1, detector.S.TOF_OBJECT_DEPTH - 0.05)
                print(f"[TUNE] Depth → {detector.S.TOF_OBJECT_DEPTH:.2f}m")
            elif key == 81:  # Left arrow
                detector.S.TOF_DEPTH_TOLERANCE = max(0.05, detector.S.TOF_DEPTH_TOLERANCE - 0.05)
                print(f"[TUNE] Tolerance → ±{detector.S.TOF_DEPTH_TOLERANCE:.2f}m")
            elif key == 83:  # Right arrow
                detector.S.TOF_DEPTH_TOLERANCE += 0.05
                print(f"[TUNE] Tolerance → ±{detector.S.TOF_DEPTH_TOLERANCE:.2f}m")

    except KeyboardInterrupt:
        print("[TUNE] Interrupted")

    finally:
        camera.cleanup()
        cv2.destroyAllWindows()
        print(f"[TUNE] Final settings: TOF_OBJECT_DEPTH={detector.S.TOF_OBJECT_DEPTH:.2f}")
        print(f"[TUNE] Final settings: TOF_DEPTH_TOLERANCE={detector.S.TOF_DEPTH_TOLERANCE:.2f}")


if __name__ == '__main__':
    main()
