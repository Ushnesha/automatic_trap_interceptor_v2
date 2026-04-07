"""
src/sim_renderer.py
Full pygame visual display.
"""

import pygame
import math

# Colors
BG      = (10,  13,  20)
GRID    = (16,  22,  32)
FLOOR_C = (30,  60,  40)
BALL_C  = (255, 110,  20)
TRAIL_C = (200,  70,  10)
CAN_B   = (20,  55,  95)
CAN_R   = (0,  200, 255)
ARC_C   = (80, 170, 255)
LAND_C  = (180,  80, 255)
PANEL   = (12,  16,  24)
BORDER  = (25,  38,  58)
TEXT    = (170, 195, 215)
MUTED   = (65,  80, 100)
GREEN   = (0,  215, 105)
RED     = (255,  50,  65)
YELLOW  = (255, 210,  50)
CYAN    = (0,  200, 255)
ORANGE  = (255, 140,  20)
PURPLE  = (180,  80, 255)
WHITE   = (235, 242, 255)


def lerp(c1, c2, t):
    return tuple(int(c1[i]+(c2[i]-c1[i])*t) for i in range(3))


class SimRenderer:

    _fonts = {}

    @classmethod
    def _f(cls, size, bold=False):
        k = (size, bold)
        if k not in cls._fonts:
            cls._fonts[k] = pygame.font.SysFont('Consolas', size, bold=bold)
        return cls._fonts[k]

    @classmethod
    def draw(cls, screen, world, camera, detector, tracker,
             predictor, motors, catches, misses, attempts, S):

        screen.fill(BG)
        WR = pygame.Rect(0,   0, 760, S.SCREEN_H)
        PR = pygame.Rect(760, 0, 440, S.SCREEN_H)
        cls._world(screen, WR, world, predictor, motors, catches, misses, attempts, S)
        cls._panel(screen, PR, world, tracker, predictor, motors,
                   catches, misses, attempts, S)

    # ── World view ────────────────────────────────────────────────

    @classmethod
    def _wx(cls, wx, rect, S):
        return rect.left + int((wx + S.ARENA_W/2) / S.ARENA_W * rect.width)

    @classmethod
    def _wz(cls, wz, rect, S):
        return rect.top + int((1 - wz/S.ARENA_H) * rect.height * 0.87) + 22

    @classmethod
    def _world(cls, screen, rect, world, predictor, motors,
               catches, misses, attempts, S):
        pygame.draw.rect(screen, (8,11,18), rect)

        # Grid
        for x in range(rect.left, rect.right, 55):
            pygame.draw.line(screen, GRID, (x,rect.top),(x,rect.bottom))
        for y in range(rect.top, rect.bottom, 55):
            pygame.draw.line(screen, GRID, (rect.left,y),(rect.right,y))

        # Floor
        fy = cls._wz(S.FLOOR_Y, rect, S)
        pygame.draw.line(screen, FLOOR_C, (rect.left,fy),(rect.right,fy), 2)
        fs = pygame.Surface((rect.width, rect.bottom-fy), pygame.SRCALPHA)
        fs.fill((30,60,40,25))
        screen.blit(fs, (rect.left,fy))

        # Ball trail
        if world._ball_trail and len(world._ball_trail) > 1:
            for i in range(1, len(world._ball_trail)):
                t  = i/len(world._ball_trail)
                c  = lerp((40,20,5), TRAIL_C, t)
                x1 = cls._wx(world._ball_trail[i-1][0], rect, S)
                y1 = cls._wz(world._ball_trail[i-1][1], rect, S)
                x2 = cls._wx(world._ball_trail[i][0],   rect, S)
                y2 = cls._wz(world._ball_trail[i][1],   rect, S)
                pygame.draw.line(screen, c, (x1,y1),(x2,y2), max(1,int(t*3)))

        # Predicted arc
        if hasattr(predictor, '_last_x') and predictor._last_x is not None and \
           hasattr(predictor, '_kx') and predictor._kx is not None:
            x0  = float(predictor._kx[0,0])
            z0  = float(predictor._kx[1,0])
            vx  = float(predictor._kx[2,0])
            vz_ = float(predictor._kx[3,0])
            pts = []
            dt2 = 0.02
            for _ in range(80):
                sx = cls._wx(x0, rect, S)
                sy = cls._wz(z0, rect, S)
                if rect.left <= sx <= rect.right and rect.top <= sy <= rect.bottom:
                    pts.append((sx,sy))
                vz_ -= S.GRAVITY * dt2
                x0  += vx  * dt2
                z0  += vz_ * dt2
                if z0 <= S.FLOOR_Y: break
            if len(pts) > 1:
                for i in range(1, len(pts)):
                    t  = i/len(pts)
                    c  = lerp(ARC_C, PURPLE, t)
                    pygame.draw.line(screen, c, pts[i-1], pts[i], 1)

        # Landing marker
        if hasattr(predictor, '_last_x') and predictor._last_x is not None:
            ppm_x = S.FRAME_WIDTH / S.ARENA_W
            lx_m  = (predictor._last_x / ppm_x) - S.ARENA_W/2
            lsx   = cls._wx(lx_m, rect, S)
            lsy   = cls._wz(S.FLOOR_Y, rect, S)
            pulse = (math.sin(pygame.time.get_ticks()*0.006)+1)*0.5
            r2    = int(12 + pulse*7)
            surf  = pygame.Surface((r2*2+4,r2*2+4), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*PURPLE, int(60+pulse*100)),(r2+2,r2+2),r2,2)
            screen.blit(surf, (lsx-r2-2, lsy-r2-2))
            pygame.draw.line(screen, PURPLE,(lsx-16,lsy-3),(lsx+16,lsy-3),2)
            pygame.draw.line(screen, PURPLE,(lsx,lsy-14),(lsx,lsy+6),2)
            lbl = cls._f(9).render(f"LAND {lx_m:+.2f}m", True, PURPLE)
            screen.blit(lbl,(lsx+5,lsy-18))

        # Can
        cls._can(screen, rect, world, motors, S)

        # Ball
        if world._ball_alive:
            bsx = cls._wx(world._ball_x, rect, S)
            bsy = cls._wz(world._ball_z, rect, S)
            if rect.left-20 <= bsx <= rect.right+20:
                for gr in [22,15,9]:
                    a2 = max(0, 80-gr*3)
                    gs = pygame.Surface((gr*2,gr*2), pygame.SRCALPHA)
                    pygame.draw.circle(gs,(*BALL_C,a2),(gr,gr),gr)
                    screen.blit(gs,(bsx-gr,bsy-gr))
                pygame.draw.circle(screen, BALL_C,(bsx,bsy),10)
                pygame.draw.circle(screen, WHITE,(bsx-3,bsy-3),3)

        # Scan line
        sy2 = int((pygame.time.get_ticks()*0.04)%rect.height)+rect.top
        sc  = pygame.Surface((rect.width,50), pygame.SRCALPHA)
        for i,a2 in enumerate([0,4,8,4,0]):
            sc.fill((0,200,255,a2),(0,i*10,rect.width,10))
        screen.blit(sc,(rect.left,sy2-25))

        # Title
        t = cls._f(10).render(
            "SmartBin  |  Raspberry Pi 4 + Mecanum + L298N + Pi Camera + Kalman + PID",
            True, MUTED)
        screen.blit(t,(rect.left+10,rect.top+6))

        # Phase bar
        cls._phases(screen, rect, world, predictor, motors)

        # Result flash
        if world._result == 'catch':
            t2 = cls._f(32,True).render("✓  CATCH", True, GREEN)
            screen.blit(t2,(rect.width//2-t2.get_width()//2, rect.height//2-60))
        elif world._result == 'miss':
            t2 = cls._f(32,True).render("✗  MISS", True, RED)
            screen.blit(t2,(rect.width//2-t2.get_width()//2, rect.height//2-60))

    @classmethod
    def _can(cls, screen, rect, world, motors, S):
        cx  = cls._wx(world._can_x, rect, S)
        fy  = cls._wz(S.FLOOR_Y, rect, S)
        scl = rect.width / S.ARENA_W
        cw  = int(S.CAN_WIDTH  * scl)
        ch  = int(S.CAN_HEIGHT * scl * 0.68)
        bx  = cx - cw//2
        by  = fy - ch

        if abs(motors.vx) > 0.1:
            gs = pygame.Surface((cw+18,ch+8), pygame.SRCALPHA)
            gs.fill((*CAN_R,28))
            screen.blit(gs,(bx-9,by-4))

        pygame.draw.rect(screen, CAN_B, (bx,by+8,cw,ch-8), border_radius=4)
        for i in range(1,4):
            sy2 = by+8+(ch-8)*i//4
            pygame.draw.line(screen,(0,38,65),(bx+4,sy2),(bx+cw-4,sy2),1)
        pygame.draw.rect(screen, CAN_R, (bx-3,by,cw+6,11), border_radius=3)

        ey = by+ch//3
        ec = ORANGE if abs(motors.vx)>0.1 else CAN_R
        pygame.draw.circle(screen,ec,(bx+cw//4,ey),4)
        pygame.draw.circle(screen,ec,(bx+3*cw//4,ey),4)

        wy2 = fy+6
        for wx2 in [bx+cw//5, bx+4*cw//5]:
            pygame.draw.circle(screen,(14,28,46),(wx2,wy2),7)
            pygame.draw.circle(screen,CAN_R,(wx2,wy2),7,2)
            ang = pygame.time.get_ticks()*0.004*math.copysign(1,motors.vx or 1)
            for i in range(3):
                a2 = ang+i*math.pi*2/3
                pygame.draw.line(screen,CAN_R,(wx2,wy2),
                    (wx2+int(math.cos(a2)*4),wy2+int(math.sin(a2)*4)),1)

        lbl = cls._f(9,True).render("INTERCEPTOR", True, CAN_R)
        screen.blit(lbl,(cx-lbl.get_width()//2,by+ch//2-5))

    @classmethod
    def _phases(cls, screen, rect, world, predictor, motors):
        phases = [
            ("① SENSE",   world.object_in_flight(),                         CYAN),
            ("② DETECT",  world.object_in_flight(),                         YELLOW),
            ("③ PREDICT", hasattr(predictor,'_last_x') and predictor._last_x is not None, PURPLE),
            ("④ ACT",     motors.target_px is not None and world.object_in_flight(), GREEN),
        ]
        pw  = 130; gap = 6
        total = len(phases)*pw+(len(phases)-1)*gap
        sx  = rect.left + rect.width//2 - total//2
        sy  = rect.bottom - 38
        for i,(label,active,color) in enumerate(phases):
            x2 = sx+i*(pw+gap)
            s2 = pygame.Surface((pw,26), pygame.SRCALPHA)
            s2.fill((*color,28) if active else (*MUTED,12))
            screen.blit(s2,(x2,sy))
            pygame.draw.rect(screen, color if active else MUTED,(x2,sy,pw,26),1)
            t2 = cls._f(10).render(label, True, color if active else MUTED)
            screen.blit(t2,(x2+pw//2-t2.get_width()//2,sy+7))

    # ── Right panel ───────────────────────────────────────────────

    @classmethod
    def _panel(cls, screen, rect, world, tracker_unused, predictor, motors,
               catches, misses, attempts, S):
        pygame.draw.rect(screen, PANEL, rect)
        pygame.draw.line(screen, BORDER, rect.topleft, rect.bottomleft, 1)

        x = rect.left+12
        y = rect.top+10

        # Title
        t = cls._f(13,True).render("SmartBin", True, CYAN)
        screen.blit(t,(x,y)); y+=22
        t2= cls._f(9).render("Pi 4  |  Mecanum  |  L298N  |  Kalman + PID", True, MUTED)
        screen.blit(t2,(x,y)); y+=20
        pygame.draw.line(screen,BORDER,(x,y),(rect.right-12,y)); y+=10

        # Score
        cls._sec(screen,x,y,"SCORE"); y+=18
        bw = (rect.width-30)//3
        for i,(val,lbl,c) in enumerate([
            (str(catches),"Catches",GREEN),
            (str(misses), "Misses", RED),
            (f"{int(catches/attempts*100) if attempts else 0}%","Accuracy",CYAN)
        ]):
            bx2=x+i*(bw+5)
            pygame.draw.rect(screen,(14,19,30),(bx2,y,bw,52),border_radius=4)
            pygame.draw.rect(screen,BORDER,(bx2,y,bw,52),1,border_radius=4)
            tv=cls._f(20,True).render(val,True,c)
            screen.blit(tv,(bx2+bw//2-tv.get_width()//2,y+5))
            tl=cls._f(9).render(lbl,True,MUTED)
            screen.blit(tl,(bx2+bw//2-tl.get_width()//2,y+33))
        y+=60

        pygame.draw.line(screen,BORDER,(x,y),(rect.right-12,y)); y+=10

        # Predictor state
        cls._sec(screen,x,y,"PREDICTOR (Kalman)"); y+=18
        if hasattr(predictor,'_kx') and predictor._kx is not None:
            kx = predictor._kx
            rows=[
                (f"x  = {float(kx[0,0]):+.3f} m",  CYAN),
                (f"z  = {float(kx[1,0]):+.3f} m",  CYAN),
                (f"vx = {float(kx[2,0]):+.2f} m/s",YELLOW),
                (f"vz = {float(kx[3,0]):+.2f} m/s",YELLOW),
            ]
        else:
            rows=[("waiting for ball...",MUTED)]
        if hasattr(predictor,'_last_x') and predictor._last_x is not None:
            ppm_x = S.FRAME_WIDTH/S.ARENA_W
            lx_m  = (predictor._last_x/ppm_x)-S.ARENA_W/2
            rows.append((f"landing = {lx_m:+.3f} m", PURPLE))
        for txt,c in rows:
            screen.blit(cls._f(10).render(txt,True,c),(x+8,y)); y+=15
        y+=6

        pygame.draw.line(screen,BORDER,(x,y),(rect.right-12,y)); y+=10

        # Motors
        cls._sec(screen,x,y,"L298N MOTORS  (Mecanum strafe)"); y+=18
        sp_pct = abs(motors.vx)/S.CAN_MAX_SPEED
        bw2    = rect.width-30
        pygame.draw.rect(screen,(14,19,30),(x,y,bw2,16),border_radius=3)
        if sp_pct > 0:
            fw  = int(bw2/2*sp_pct)
            cx2 = x+bw2//2
            fc  = GREEN if motors.vx>0 else ORANGE
            rx  = cx2 if motors.vx>0 else cx2-fw
            pygame.draw.rect(screen,fc,(rx,y,fw,16),border_radius=3)
        pygame.draw.line(screen,MUTED,(x+bw2//2,y),(x+bw2//2,y+16),1)
        pygame.draw.rect(screen,BORDER,(x,y,bw2,16),1,border_radius=3)
        y+=22
        dt = "→ STRAFE RIGHT" if motors.vx>0.05 else "← STRAFE LEFT" if motors.vx<-0.05 else "■ STOPPED"
        dc = GREEN if motors.vx>0.05 else ORANGE if motors.vx<-0.05 else MUTED
        screen.blit(cls._f(10).render(f"{dt}  {motors.vx:+.2f} m/s",True,dc),(x+4,y)); y+=16
        duty = int(abs(motors.vx)/S.CAN_MAX_SPEED*100)
        screen.blit(cls._f(9).render(f"GPIO PWM duty = {duty}%",True,MUTED),(x+4,y)); y+=16
        y+=4

        pygame.draw.line(screen,BORDER,(x,y),(rect.right-12,y)); y+=10

        # Camera preview
        cls._sec(screen,x,y,"PI CAMERA  640×480"); y+=18
        pw2 = rect.width-24
        ph2 = int(pw2*480/640)
        cs  = pygame.Surface((pw2,ph2)); cs.fill((18,15,12))
        scx = pw2/S.ARENA_W; scz = ph2/S.ARENA_H
        fpy = ph2-4
        pygame.draw.line(cs,(35,70,45),(0,fpy),(pw2,fpy),1)

        # Can in camera
        cpx = int((world._can_x+S.ARENA_W/2)*scx)
        ccw = int(S.CAN_WIDTH*scx); cch=int(S.CAN_HEIGHT*scz*0.68)
        pygame.draw.rect(cs,(28,65,105),(cpx-ccw//2,fpy-cch,ccw,cch))
        pygame.draw.rect(cs,(0,115,170),(cpx-ccw//2-1,fpy-cch-1,ccw+2,6))

        # Ball in camera
        if world._ball_alive:
            bpx=int((world._ball_x+S.ARENA_W/2)*scx)
            bpz=int((S.ARENA_H-world._ball_z)*scz)
            if 0<=bpx<pw2 and 0<=bpz<ph2:
                pygame.draw.circle(cs,BALL_C,(bpx,bpz),8)
                pygame.draw.circle(cs,WHITE,(bpx-2,bpz-2),2)

        # Detection crosshair
        if hasattr(predictor,'_kx') and predictor._kx is not None:
            kx=predictor._kx
            dpx=int((float(kx[0,0])+S.ARENA_W/2)*scx)
            dpz=int((S.ARENA_H-float(kx[1,0]))*scz)
            if 0<=dpx<pw2 and 0<=dpz<ph2:
                pygame.draw.circle(cs,GREEN,(dpx,dpz),11,1)
                pygame.draw.line(cs,GREEN,(dpx-15,dpz),(dpx+15,dpz),1)
                pygame.draw.line(cs,GREEN,(dpx,dpz-15),(dpx,dpz+15),1)

        # Prediction line in camera
        if hasattr(predictor,'_last_x') and predictor._last_x is not None:
            ppm_x=S.FRAME_WIDTH/S.ARENA_W
            ppx=int((predictor._last_x/ppm_x+S.ARENA_W/2)*scx/S.ARENA_W*pw2)
            pygame.draw.line(cs,PURPLE,(ppx,0),(ppx,ph2),1)

        stxt = "TRACKING" if world.object_in_flight() else "STANDBY"
        sc2  = GREEN if world.object_in_flight() else MUTED
        cs.blit(cls._f(8).render(stxt,True,sc2),(3,3))
        screen.blit(cs,(x,y))
        pygame.draw.rect(screen,BORDER,(x-1,y-1,pw2+2,ph2+2),1)
        y+=ph2+10

        # Controls
        pygame.draw.line(screen,BORDER,(x,y),(rect.right-12,y)); y+=8
        ctrl="SPACE=throw  |  R=reset  |  A=auto×500  |  Q=quit"
        t3=cls._f(9).render(ctrl,True,MUTED)
        screen.blit(t3,(x+rect.width//2-12-t3.get_width()//2,y))

    @classmethod
    def _sec(cls, screen, x, y, title):
        screen.blit(cls._f(9).render(title,True,MUTED),(x,y))
