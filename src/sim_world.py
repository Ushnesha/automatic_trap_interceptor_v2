"""
src/sim_world.py
Physics world — same interface as original PyBullet SimWorld.
Uses pure Python physics instead of PyBullet (no install needed).

Same public methods:
    throw_object()
    object_in_flight()
    check_catch()       → 'catch' | 'miss' | None
    get_ball_position() → (x, y, z) or None
    get_can_position()  → (x, y, z)
    draw_prediction_line(x)
    get_key_press()     → 'space' | 'r' | 'q' | None
    reset()
    step()
    disconnect()
"""

import math
import random
import pygame


class SimWorld:

    def __init__(self, headless, settings):
        self.S        = settings
        self.headless = headless

        # Ball state
        self._ball_x  = 0.0
        self._ball_z  = 0.0
        self._ball_vx = 0.0
        self._ball_vz = 0.0
        self._ball_alive   = False
        self._ball_landed  = False
        self._ball_trail   = []

        # Can state
        self._can_x  = settings.CAN_START_X

        # Result
        self._result          = None
        self._result_checked  = False
        self._predicted_x     = None

        # Pygame (GUI mode)
        self._screen = None
        self._clock  = None
        self._keys   = set()
        self._key_triggered = set()

        if not headless:
            pygame.init()
            self._screen = pygame.display.set_mode(
                (settings.SCREEN_W, settings.SCREEN_H)
            )
            pygame.display.set_caption(
                "SmartBin — Pi4 + Mecanum + L298N + Kalman + PID"
            )
            self._clock = pygame.time.Clock()
            print("[WORLD] Pygame window opened")
        else:
            print("[WORLD] Headless mode — no window")

        print(f"[WORLD] Arena {settings.ARENA_W}m × {settings.ARENA_H}m")
        print(f"[WORLD] Can start x={settings.CAN_START_X}")

    # ── Throwing ──────────────────────────────────────────────────

    def throw_object(self):
        S = self.S
        self._ball_x  = random.uniform(*S.THROW_X_RANGE)
        self._ball_z  = random.uniform(S.THROW_Z_MIN, S.THROW_Z_MAX)
        self._ball_vx = random.uniform(*S.THROW_VX_RANGE)
        self._ball_vz = random.uniform(*S.THROW_VZ_UP) if random.random() < 0.6 \
                        else random.uniform(-0.3, 0.4)
        self._ball_alive  = True
        self._ball_landed = False
        self._ball_trail  = []
        self._result         = None
        self._result_checked = False
        self._predicted_x    = None
        print(f"[WORLD] Ball thrown x={self._ball_x:.2f} "
              f"vx={self._ball_vx:.2f} vz={self._ball_vz:.2f}")
        return (self._ball_x, self._ball_z)

    def object_in_flight(self):
        return self._ball_alive and not self._ball_landed

    def get_ball_position(self):
        if not self._ball_alive:
            return None
        return (self._ball_x, 0.0, self._ball_z)

    def get_can_position(self):
        return (self._can_x, 0.0, 0.0)

    # ── Catch detection ───────────────────────────────────────────

    def check_catch(self):
        if self._result_checked:
            return None
        if not self._ball_alive:
            return None
        if self._ball_z <= self.S.FLOOR_Y + 0.10:
            self._result_checked = True
            self._ball_alive  = False
            self._ball_landed = True
            S   = self.S
            tol = S.CAN_WIDTH / 2 + S.CATCH_BONUS_X
            if abs(self._ball_x - self._can_x) <= tol:
                self._result = 'catch'
            else:
                self._result = 'miss'
            return self._result
        return None

    # ── Can movement ──────────────────────────────────────────────

    def set_can_x(self, x):
        hw = self.S.ARENA_W / 2 - self.S.CAN_WIDTH / 2
        self._can_x = max(-hw, min(hw, x))

    def get_can_x(self):
        return self._can_x

    # ── Debug visualization ───────────────────────────────────────

    def draw_prediction_line(self, predicted_x):
        self._predicted_x = predicted_x

    # ── Input (GUI mode) ──────────────────────────────────────────

    def get_key_press(self):
        triggered = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'q'
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:  triggered = 'space'
                if event.key == pygame.K_r:       triggered = 'r'
                if event.key == pygame.K_q:       triggered = 'q'
                if event.key == pygame.K_a:       triggered = 'a'
        return triggered

    # ── Physics step ──────────────────────────────────────────────

    def step(self):
        if not self._ball_alive or self._ball_landed:
            return
        S  = self.S
        dt = S.SIM_TIMESTEP

        # Air drag
        speed = math.hypot(self._ball_vx, self._ball_vz)
        if speed > 0:
            drag = S.AIR_DRAG * speed
            self._ball_vx -= drag * (self._ball_vx / speed) * dt
            self._ball_vz -= drag * (self._ball_vz / speed) * dt

        # Gravity
        self._ball_vz -= S.GRAVITY * dt

        # Move
        self._ball_x += self._ball_vx * dt
        self._ball_z += self._ball_vz * dt

        # Trail
        self._ball_trail.append((self._ball_x, self._ball_z))
        if len(self._ball_trail) > 90:
            self._ball_trail.pop(0)

    # ── Render ────────────────────────────────────────────────────

    def render(self, camera, detector, tracker, predictor, motors,
               catches, misses, attempts):
        """Draw the full simulation frame."""
        if self.headless or self._screen is None:
            return

        from src.sim_renderer import SimRenderer
        SimRenderer.draw(
            self._screen, self, camera, detector, tracker,
            predictor, motors, catches, misses, attempts, self.S
        )
        pygame.display.flip()
        self._clock.tick(self.S.FPS)

    # ── Lifecycle ─────────────────────────────────────────────────

    def reset(self):
        self._ball_alive  = False
        self._ball_landed = False
        self._ball_trail  = []
        self._can_x       = self.S.CAN_START_X
        self._result      = None
        self._result_checked = False
        self._predicted_x = None

    def disconnect(self):
        if not self.headless:
            pygame.quit()
        print("[WORLD] Disconnected.")
