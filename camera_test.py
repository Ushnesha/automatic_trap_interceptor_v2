"""
test_detection.py - Quick test to see if detector works
Run this INSTEAD of main_pi.py to test detection only
"""

import sys
import time
import cv2
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
    
    print("=" * 60)
    print("SMARTBIN - DETECTION TEST ONLY")
    print("=" * 60)
    print("\n1. Initializing camera...")
    
    try:
        camera = RealCamera(settings=settings)
        detector = RealDetector(settings=settings)
        
        print("2. Waiting for calibration (5 seconds)...")
        print("   KEEP AREA CLEAR - NO OBJECTS IN FRAME!\n")
        
        frame_count = 0
        detection_count = 0

        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter('output.avi', fourcc, 20.0, (320, 240))
        
        # Main loop
        while True:
            frame_count += 1
            
            # Get frame from camera
            frame = camera.get_frame()
            if frame is None:
                continue

            # Try to detect
            position = detector.find_object(frame)
            # if frame is not None:
            # 1. Normalize depth for display (0.3m to 2.0m range)
            # We map the depth to a 0-255 grayscale range
            depth_display = np.clip((frame - 0.3) / (2.0 - 0.3) * 255, 0, 255).astype(np.uint8)
            
            # 2. Apply a colormap so it looks like a "heat map" (Easier to see)
            color_map = cv2.applyColorMap(depth_display, cv2.COLORMAP_JET)
            
            # 3. Draw the detection if it exists
            if position is not None:
                detection_count += 1
                cx, cy, _ = position
                print(f"\n>>> DETECTION #{detection_count}: Object at ({cx}, {cy})\n")
                # Draw a bright white circle at the center of the object
                cv2.circle(color_map, (cx, cy), 15, (255, 255, 255), 2)
                cv2.putText(color_map, "OBJECT", (cx + 20, cy), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                out.write(color_map)

            # # 4. Show the window
            # cv2.imshow("Pi5 ToF Motion Monitor", color_map)
            
            # # Stop if 'q' is pressed
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break
                        
            
            
            # if position is not None:
            #     detection_count += 1
            #     cx, cy = position
            #     print(f"\n>>> DETECTION #{detection_count}: Object at ({cx}, {cy})\n")
            
            # Every 30 frames show status
            if frame_count % 30 == 0:
                status = detector.get_calibration_status()
                print(f"[{frame_count}] Status: {status}")
            
            # Timing
            time.sleep(1.0 / 20)  # 20 FPS
        out.release()   
    
    except KeyboardInterrupt:
        print(f"\n\nTest stopped by user")
        print(f"Total frames: {frame_count}")
        print(f"Total detections: {detection_count}")
        if detection_count > 0:
            print(f"✓ DETECTOR IS WORKING!")
        else:
            print(f"✗ No detections - check object size/distance")
    
    finally:
        if camera:
            camera.cleanup()


if __name__ == '__main__':
    main()