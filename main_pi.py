"""
main_pi.py — SmartBin for Raspberry Pi 5
Real hardware deployment: Camera + L298N + Mecanum wheels.

Run: python3 main_pi.py [--ml] [--collect-data]

Uses real hardware modules:
  - src/camera_real.py (real camera)
  - src/motors_real.py (L298N GPIO control)
  - src/detect_real.py (OpenCV detection)
  - src/predict.py (Kalman filter or ML prediction)
"""

import argparse
import time
import sys
 
try:
    from src.camera_real import RealCamera
    from src.motors_real import RealMotors
    from src.detect_real import RealDetector
    from src.predict import Predictor
    from src.ml_predictor import MLPredictor, ThrowDataCollector
    from src.logger import Logger
    from config.sim_settings import SimSettings
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    print("[ERROR] Make sure you're in the smartbin_v4 directory")
    sys.exit(1)
 
 
def parse_args():
    parser = argparse.ArgumentParser(description='SmartBin on Raspberry Pi 5')
    parser.add_argument('--ml', action='store_true',
                        help='Use ML predictor instead of Kalman physics')
    parser.add_argument('--collect-data', action='store_true',
                        help='Collect throw data for ML training')
    return parser.parse_args()
 
 
def main():
    args = parse_args()
    settings = SimSettings()
    log = Logger()
 
    log.header("SmartBin — Raspberry Pi 5 (FIXED)")
    log.info(f"Predictor : {'ML MODEL' if args.ml else 'Kalman + Physics'}")
    log.info(f"Data coll : {'ON → data/throws.csv' if args.collect_data else 'OFF'}")
    log.info(f"Hardware  : Raspberry Pi 5 | Camera | L298N | Mecanum")
 
    camera = None
    motors = None
    detector = None
 
    try:
        # Initialize real hardware
        log.info("Initializing hardware...")
        camera = RealCamera(settings=settings)
        motors = RealMotors(settings=settings)
        detector = RealDetector(settings=settings)
 
        # Initialize predictor
        predictor = MLPredictor(settings=settings) if args.ml else Predictor(settings=settings)
 
        # Data collector
        collector = ThrowDataCollector() if args.collect_data else None
        throw_positions = []
 
        log.success("All modules loaded. Waiting for calibration...")
        log.info("Press Ctrl+C to stop")
 
        frame_count = 0
        catch_count = 0
        detection_count = 0
        last_status_frame = 0
        last_detection_time = time.time()
        is_moving = False
        active_throw = False
 
        # Main loop
        while True:
            loop_start = time.time()
            frame_count += 1
 
            # ── SENSE: Capture frame ──────────────────────────────
            frame = camera.get_frame()
            if frame is None:
                if frame_count == 1:
                    log.warn("[SENSE] Camera returned None on first frame - sensor warming up?")
                continue
 
            # ── DETECT: Find orange ball ──────────────────────────
            # FIX: Track detection attempts and results
            position = detector.find_object(frame)
            current_time = time.time()
            
            if position is not None:
                # ── WE SEE THE BALL ──
                if not active_throw:
                    log.info("NEW THROW DETECTED")
                    active_throw = True

                detection_count += 1
                last_detection_time = time.time() 
                is_moving = True
                
                cx, cy, depth = position
                log.debug(f"[DETECT] Ball at ({cx}, {cy}) Depth: {depth:.2f}m")
 
                if collector and position:
                    throw_positions.append(position)
 
                predictor.add_point(position)
                predicted_x = predictor.get_predicted_landing_x()
 
                if predicted_x is not None:
                    log.debug(f"[PREDICT] Landing X = {predicted_x:.1f}px")
                    motors.move_to_x(predicted_x)
            
            else:
                # ── NO BALL DETECTED (The Fix) ──
                if active_throw:
                    time_since_last_seen = current_time - last_detection_time

                    # 1. SUCCESS/FAILURE TIMEOUT: The throw is over
                    if time_since_last_seen > 3.0:
                        log.info("THROW COMPLETED: Resetting for next object...")
                        motors.stop()
                        motors.reset()      # Sets current_m = 0
                        predictor.reset()    # Clears Kalman history
                        active_throw = False # Allow new detection
                        is_moving = False
                    
                    # 2. MID-AIR PERSISTENCE: Lost sight but still moving to target
                    elif predictor._last_x is not None:
                        motors.move_to_x(predictor._last_x)

                # # 2. Periodic Status Logging
                # if frame_count % 30 == 0:
                #     status = detector.get_calibration_status()
                #     if status != "ready":
                #         log.info(f"[DETECT] {status}")
                #     else:
                #         log.debug(f"[DETECT] No object detected in frame {frame_count}")    
 
            # ── Periodic status ───────────────────────────────────
            if frame_count % 30 == 0:
                status = detector.get_calibration_status()
                log.info(f"[RUNNING] Frames: {frame_count}, "
                         f"Detections: {detection_count}, "
                         f"Catches: {catch_count} | Detector: {status}")
 
            # ── Timing: ~20 FPS (safer for calibration) ───────────
            elapsed = time.time() - loop_start
            target_delay = 1.0 / 20  # 20 FPS
            if elapsed < target_delay:
                time.sleep(target_delay - elapsed)
 
    except KeyboardInterrupt:
        log.info("Interrupted by user")
 
    except Exception as e:
        log.error(f"Runtime error: {e}")
        import traceback
        traceback.print_exc()
 
    finally:
        # Cleanup
        log.info("Cleaning up hardware...")
        if motors:
            motors.stop()
            motors.cleanup()
        if camera:
            camera.cleanup()
 
        # Save training data
        if collector:
            collector.save()
            log.info("[DATA] Train model: python3 tools/train_model.py")
 
        log.header(f"FINAL: {catch_count} catches, {detection_count} detections, "
                   f"{frame_count} frames processed")
 
 
if __name__ == '__main__':
    main()
