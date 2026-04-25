#!/usr/bin/env python3
"""
Quick TOF depth diagnostic — print what the camera actually sees.
Run: python3 tools/diagnose_tof_depth.py
"""

import sys
import time
import numpy as np

try:
    from src.camera_real import RealCamera
    from src.detect_real import RealDetector
    from config.sim_settings import SimSettings
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    sys.exit(1)


def main():
    settings = SimSettings()
    
    print("[TOF-DIAG] Initializing camera...")
    try:
        camera = RealCamera(settings)
    except Exception as e:
        print(f"[ERROR] Camera failed: {e}")
        sys.exit(1)
    
    print("[TOF-DIAG] Initializing detector...")
    detector = RealDetector(settings)
    
    print("[TOF-DIAG] Capturing depth frames — place object in view")
    print(f"[TOF-DIAG] Current depth range: {settings.TOF_OBJECT_DEPTH - settings.TOF_DEPTH_TOLERANCE:.2f}m to {settings.TOF_OBJECT_DEPTH + settings.TOF_DEPTH_TOLERANCE:.2f}m")
    print("-" * 70)
    
    frame_count = 0
    
    try:
        while frame_count < 30:
            frame_count += 1
            
            # Get raw depth frame
            depth_frame = camera.get_depth_frame()
            if depth_frame is None:
                print(f"[Frame {frame_count}] Camera returned None")
                continue
            
            # Get depth statistics
            stats = detector.get_depth_stats(depth_frame)
            
            print(f"[Frame {frame_count:2d}]", end=" ")
            if stats:
                print(f"Mean: {stats['mean']:.2f}m | Min: {stats['min']:.2f}m | Max: {stats['max']:.2f}m | Std: {stats['std']:.2f}m", end="")
                
                # Check if object is in detection range
                obj_min = settings.TOF_OBJECT_DEPTH - settings.TOF_DEPTH_TOLERANCE
                obj_max = settings.TOF_OBJECT_DEPTH + settings.TOF_DEPTH_TOLERANCE
                
                if stats['min'] >= obj_min and stats['max'] <= obj_max:
                    print(" ✓ Object in range")
                else:
                    print(f" ✗ Out of range [{obj_min:.2f}-{obj_max:.2f}]")
            else:
                print("No valid depth data")
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n[TOF-DIAG] Interrupted")
    
    finally:
        camera.cleanup()
        print("[TOF-DIAG] Done")


if __name__ == '__main__':
    main()
