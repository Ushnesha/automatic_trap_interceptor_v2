"""
config/sim_settings.py
All constants for your hardware:
  Raspberry Pi 4 | Pi Camera | L298N | Mecanum chassis
"""

class SimSettings:

    # ── Screen ────────────────────────────────────────────────────
    SCREEN_W = 1200
    SCREEN_H = 700
    FPS      = 60

    # ── Real-world arena (meters) ─────────────────────────────────
    ARENA_W  = 3.0
    ARENA_H  = 2.5

    # ── ArduCAM TOF Camera ────────────────────────────────────────
    FRAME_WIDTH  = 320
    FRAME_HEIGHT = 240
    CAM_WIDTH    = 320
    CAM_HEIGHT   = 240

    # ── TOF depth detection ───────────────────────────────────────
    TOF_MIN_DEPTH = 0.1    # meters — minimum distance
    TOF_MAX_DEPTH = 2.0    # meters — maximum distance
    TOF_OBJECT_DEPTH = 0.5 # meters — expected depth range for objects
    TOF_DEPTH_TOLERANCE = 0.3  # meters — ±tolerance around expected depth
    MIN_OBJECT_AREA = 50   # pixels² — minimum cluster size

    # ── Physics ───────────────────────────────────────────────────
    GRAVITY          = 9.81    # m/s²
    AIR_DRAG         = 0.008
    BOUNCE           = 0.20
    FLOOR_Y          = 0.0
    SIM_TIMESTEP     = 1.0 / 60
    PHYSICS_SUBSTEPS = 1

    # ── Throw parameters ──────────────────────────────────────────
    THROW_X_RANGE   = (-0.5,  0.5)
    THROW_Z_MIN     = 1.0
    THROW_Z_MAX     = 1.9
    THROW_VX_RANGE  = (-2.8,  2.8)
    THROW_VZ_UP     = (0.3,   2.2)
    BALL_RADIUS     = 0.06
    BALL_MASS       = 0.05
    BALL_COLOR_RGBA = (255, 110, 20, 255)   # orange RGBA

    # ── Trash can ─────────────────────────────────────────────────
    CAN_WIDTH    = 0.38
    CAN_HEIGHT   = 0.50
    CAN_START_X  = 0.0
    CATCH_BONUS_X = 0.10

    # ── L298N + Mecanum motors ─────────────────────────────────────
    CAN_MAX_SPEED = 4.5    # m/s  — must exceed max needed speed
    CAN_ACCEL     = 22.0   # m/s²
    CAN_DECEL     = 18.0   # m/s²
    POSITION_TOL  = 0.04   # m — dead zone

    # ── PID gains ─────────────────────────────────────────────────
    PID_KP = 7.0
    PID_KI = 0.1
    PID_KD = 1.0

    # ── Kalman filter ──────────────────────────────────────────────
    KALMAN_Q = 0.05   # process noise
    KALMAN_R = 0.004  # measurement noise

    # ── Predictor ─────────────────────────────────────────────────
    MIN_POINTS_TO_PREDICT = 4   # frames before prediction starts
