"""
sim_main.py — SmartBin Simulator Entry Point
=============================================
Autonomous Interceptor Trash Can
Raspberry Pi 4 | Pi Camera | L298N | Mecanum Chassis

Same flags as original:
    python sim_main.py                         # GUI, manual
    python sim_main.py --headless              # no window (faster)
    python sim_main.py --slow                  # slow motion
    python sim_main.py --auto 20               # auto-throw 20 objects
    python sim_main.py --ml                    # use ML predictor
    python sim_main.py --collect-data          # save training data
    python sim_main.py --auto 500 --headless --collect-data  # collect fast

Install:
    pip install pygame numpy
    pip install scikit-learn   (for --ml training only)

Train ML model:
    python sim_main.py --auto 500 --headless --collect-data
    python tools/train_model.py
    python sim_main.py --ml
"""

import argparse
import time
import sys

from src.sim_world    import SimWorld
from src.sim_camera   import SimCamera
from src.sim_motors   import SimMotors
from src.predict      import Predictor
from src.ml_predictor import MLPredictor, ThrowDataCollector
from src.detect       import Detector
from src.logger       import Logger
from config.sim_settings import SimSettings


def parse_args():
    parser = argparse.ArgumentParser(description='SmartBin Simulator')
    parser.add_argument('--headless',     action='store_true',
                        help='No GUI window (faster, use for data collection)')
    parser.add_argument('--slow',         action='store_true',
                        help='Slow motion')
    parser.add_argument('--auto',         type=int, default=0,
                        help='Auto-throw N objects and report score')
    parser.add_argument('--ml',           action='store_true',
                        help='Use ML predictor instead of Kalman physics')
    parser.add_argument('--collect-data', action='store_true',
                        help='Save throw data to data/throws.csv for ML training')
    return parser.parse_args()


def main():
    args     = parse_args()
    settings = SimSettings()
    log      = Logger()

    log.header("SmartBin — Autonomous Interceptor Trash Can")
    log.info(f"Mode      : {'HEADLESS' if args.headless else 'GUI'}")
    log.info(f"Speed     : {'SLOW' if args.slow else 'NORMAL'}")
    log.info(f"Auto      : {args.auto} throws" if args.auto else "Auto      : OFF (press SPACE)")
    log.info(f"Predictor : {'ML MODEL' if args.ml else 'Kalman + Physics'}")
    log.info(f"Data coll : {'ON → data/throws.csv' if args.collect_data else 'OFF'}")
    log.info(f"Hardware  : Raspberry Pi 4 | L298N | Mecanum | Pi Camera")

    # ── Boot modules (same order as original) ──────────────────────
    world     = SimWorld(headless=args.headless, settings=settings)
    camera    = SimCamera(world=world, settings=settings)
    motors    = SimMotors(world=world, settings=settings)
    predictor = MLPredictor(settings=settings) if args.ml \
                else Predictor(settings=settings)
    detector  = Detector(settings=settings)

    # Data collector
    collector       = ThrowDataCollector() if args.collect_data else None
    throw_positions = []

    log.success("All modules loaded. Simulator ready.")
    if not args.headless:
        log.info("Controls: SPACE = throw | R = reset | A = auto×500 | Q = quit")

    # ── Stats ──────────────────────────────────────────────────────
    score       = 0
    attempts    = 0
    auto_thrown = 0

    try:
        while True:
            loop_start = time.time()

            # ── Auto-throw mode ────────────────────────────────────
            if args.auto > 0 and not world.object_in_flight():
                if world._result is not None:
                    # Wait one frame for result to clear
                    pass
                elif auto_thrown >= args.auto:
                    break
                else:
                    world.throw_object()
                    predictor.reset()
                    motors.reset()
                    throw_positions = []
                    auto_thrown += 1
                    attempts    += 1
                    log.info(f"[AUTO] Throw #{attempts}")

            # ── Manual key controls (GUI mode) ─────────────────────
            if not args.headless:
                key = world.get_key_press()
                if key == 'space' and not world.object_in_flight():
                    world.throw_object()
                    predictor.reset()
                    motors.reset()
                    throw_positions = []
                    attempts += 1
                    log.info(f"[THROW] Attempt #{attempts}")
                elif key == 'r':
                    world.reset()
                    predictor.reset()
                    motors.center()
                    throw_positions = []
                    log.info("[RESET] World reset")
                elif key == 'q':
                    break
                elif key == 'a':
                    args.auto    = 500
                    auto_thrown  = 0
                    log.info("[AUTO] Starting 500 auto throws")

            # ══════════════════════════════════════════════════════
            #  PIPELINE: ① Sense → ② Detect → ③ Predict → ④ Act
            # ══════════════════════════════════════════════════════

            frame    = None
            position = None

            # ── ① SENSE: Pi Camera renders frame ──────────────────
            if world.object_in_flight():
                frame = camera.get_frame()
                if frame is None:
                    log.warn("[SENSE] Camera returned None")

            # ── ② DETECT: HSV → blob → centroid ───────────────────
                if frame is not None:
                    position = detector.find_object(frame)
                    if position is None:
                        log.debug("[DETECT] No object in frame")

                # Collect position for ML training
                if collector and position:
                    throw_positions.append(position)

            # ── ③ PREDICT: Kalman + ballistic solver ───────────────
            predicted_x = None
            if position:
                predictor.add_point(position)
                predicted_x = predictor.get_predicted_landing_x()
                if predicted_x is not None:
                    world.draw_prediction_line(predicted_x)
                    log.debug(f"[PREDICT] landing_x = {predicted_x:.1f}px")

            # ── ④ ACT: PID motors strafe to landing spot ───────────
            if predicted_x is not None:
                motors.move_to_x(predicted_x)

            # ── CHECK CATCH ────────────────────────────────────────
            result = world.check_catch()
            if result == 'catch':
                score += 1
                log.success(f"CATCH!  Score: {score}/{attempts}")
                predictor.reset()
                motors.reset()

                # Save training data
                if collector and throw_positions:
                    lx_px = camera.world_to_pixel_x(world._ball_x)
                    collector.record(throw_positions, lx_px)
                throw_positions = []

                if not args.auto:
                    time.sleep(0.9)
                world._result = None

            elif result == 'miss':
                log.warn(f"MISS.   Score: {score}/{attempts}")
                predictor.reset()
                motors.reset()

                if collector and throw_positions:
                    lx_px = camera.world_to_pixel_x(world._ball_x)
                    collector.record(throw_positions, lx_px)
                throw_positions = []

                if not args.auto:
                    time.sleep(0.5)
                world._result = None

            # ── Step physics ───────────────────────────────────────
            for _ in range(settings.PHYSICS_SUBSTEPS):
                world.step()

            # ── Render (GUI only) ──────────────────────────────────
            if not args.headless:
                world.render(camera, detector, None,
                             predictor, motors,
                             score, attempts-score, attempts)

            # ── Timing ─────────────────────────────────────────────
            if args.slow:
                time.sleep(0.05)
            elif args.headless:
                pass   # run as fast as possible
            else:
                delay   = settings.SIM_TIMESTEP * settings.PHYSICS_SUBSTEPS
                elapsed = time.time() - loop_start
                if delay > elapsed:
                    time.sleep(delay - elapsed)

    except KeyboardInterrupt:
        log.info("Interrupted.")

    finally:
        # Save training data
        if collector:
            collector.save()
            log.info("[DATA] Now train: python tools/train_model.py")

        pct = int(score/attempts*100) if attempts else 0
        log.header(f"FINAL SCORE: {score}/{attempts}  ({pct}%)")
        world.disconnect()


if __name__ == '__main__':
    main()
