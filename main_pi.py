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

    log.header("SmartBin — Raspberry Pi 5")
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

        log.success("All modules loaded. Ready to catch!")
        log.info("Press Ctrl+C to stop")

        frame_count = 0
        catch_count = 0

        # Main loop
        while True:
            loop_start = time.time()
            frame_count += 1

            # ── SENSE: Capture frame ──────────────────────────────
            frame = camera.get_frame()
            if frame is None:
                log.warn("[SENSE] Camera returned None")
                continue

            # ── DETECT: Find orange ball ──────────────────────────
            position = detector.find_object(frame)
            if position is None:
                log.debug("[DETECT] No object in frame")
            else:
                cx, cy = position
                log.debug(f"[DETECT] Ball at ({cx}, {cy})")

                # Collect position for ML training
                if collector and position:
                    throw_positions.append(position)

                # ── PREDICT: Kalman + ballistic solver ────────────
                predictor.add_point(position)
                predicted_x = predictor.get_predicted_landing_x()

                if predicted_x is not None:
                    log.debug(f"[PREDICT] Landing X = {predicted_x:.1f}px")

                    # ── ACT: Move motors to landing spot ──────────
                    motors.move_to_x(predicted_x)

            # ── Periodic status ───────────────────────────────────
            if frame_count % 30 == 0:
                log.info(f"[RUNNING] Frames: {frame_count}, Catches: {catch_count}")

            # ── Timing: ~30 FPS ───────────────────────────────────
            elapsed = time.time() - loop_start
            target_delay = 1.0 / 30  # 30 FPS
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

        log.header(f"FINAL: {catch_count} catches, {frame_count} frames processed")


if __name__ == '__main__':
    main()
