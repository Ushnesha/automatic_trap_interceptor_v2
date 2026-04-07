"""
src/sim_camera.py
Fast synthetic Pi Camera — fully vectorized numpy. No pixel loops.
"""
import numpy as np

class SimCamera:
    def __init__(self, world, settings):
        self.world = world
        self.S     = settings
        self.W     = settings.CAM_WIDTH
        self.H     = settings.CAM_HEIGHT
        self.ppm_x = settings.CAM_WIDTH  / settings.ARENA_W
        self.ppm_z = settings.CAM_HEIGHT / settings.ARENA_H
        print(f"[CAMERA] Virtual camera: {self.W}x{self.H} ppm_x={self.ppm_x:.1f} ppm_z={self.ppm_z:.1f}")

    def get_frame(self):
        S=self.S; W,H=self.W,self.H; world=self.world
        frame=np.full((H,W,3),(25,22,18),dtype=np.uint8)

        # Floor
        fy=max(0,min(H-1,int((S.ARENA_H-S.FLOOR_Y)*self.ppm_z)))
        frame[max(0,fy-1):fy+2,:] = (40,70,45)

        # Can
        cx=int((world._can_x+S.ARENA_W/2)*self.ppm_x)
        cw=max(4,int(S.CAN_WIDTH*self.ppm_x))
        ch=max(4,int(S.CAN_HEIGHT*self.ppm_z*0.7))
        frame[max(0,fy-ch):min(H,fy), max(0,cx-cw//2):min(W,cx+cw//2)] = (100,70,25)

        # Ball — vectorized
        if world._ball_alive:
            bpx=int((world._ball_x+S.ARENA_W/2)*self.ppm_x)
            bpy=int((S.ARENA_H-world._ball_z)*self.ppm_z)
            r=max(5,int(S.BALL_RADIUS*self.ppm_x*1.3))
            rx1=max(0,bpx-r-2); rx2=min(W,bpx+r+3)
            ry1=max(0,bpy-r-2); ry2=min(H,bpy+r+3)
            if rx2>rx1 and ry2>ry1:
                gy,gx=np.ogrid[ry1:ry2,rx1:rx2]
                mask=(gx-bpx)**2+(gy-bpy)**2<=r*r
                region=frame[ry1:ry2,rx1:rx2]
                region[mask]=(20,110,225)
                frame[ry1:ry2,rx1:rx2]=region
        return frame

    def world_to_pixel(self, wx, wz=0):
        return int((wx+self.S.ARENA_W/2)*self.ppm_x), int((self.S.ARENA_H-wz)*self.ppm_z)

    def world_to_pixel_x(self, wx):
        return int((wx+self.S.ARENA_W/2)*self.ppm_x)

    def pixel_to_world(self, px, py=None):
        return (px/self.ppm_x)-self.S.ARENA_W/2
