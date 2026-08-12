import sys
from datetime import datetime

import os
import glob

import pygame
import numpy as np
import math
import random

BLACK = (0, 0, 0)
GRAY = (127, 127, 127)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class SimulationData:
    def __init__(self, fpt):
        self.frames_per_tick = fpt
        self.elapsed_frames = 0
        # set the view to (0, 0) in sim space as the ul and (1 pixel : 1 sim dist) for x and y
        self.origin = Point(0,0)
        self.scale = 5
        self.types = 2


class MapData:
    def __init__(self):
        self.dim = Point(140, 140)
        self.cell = np.zeros([140, 140], dtype=np.uint8)


class ModeData:
    def __init__(self, ups):
        self.ups = ups # simulation updates per second
        self.is_dragging = False
        self.is_playing = False
        self.drag_value = 0

class Simulation:
    def __init__(self, width, height, fps, ups):
        self.mode = ModeData(ups)
        self.map = MapData()
        self.sim = SimulationData(ups / fps)

        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.running = False

    def set_view(self, view):
        v = (view[0], view[1], (view[2] - view[0]) / self.screen.get_width(), (view[3] - view[1]) / self.screen.get_height())
        self.sim.metric = v

    def draw(self):
        self.screen.fill(BLACK)
        self.draw_grid()
        #self.draw_mouse_pos()

    def draw_grid(self):
        for col in range(self.map.dim.x):
            for row in range(self.map.dim.y):
                color = None
                if self.map.cell[col,row] == 1:
                    color = YELLOW
                if self.map.cell[col,row] == 2:
                    color = GREEN
                if color is not None:
                    pygame.draw.rect(self.screen, color, (col * self.sim.scale, row * self.sim.scale, self.sim.scale, self.sim.scale))

    def draw_mouse_pos(self):
        pos_pix = pygame.mouse.get_pos()
        pos_sim = (round(pos_pix[0] / self.sim.scale + self.sim.origin.x, 1), round(pos_pix[1] / self.sim.scale + self.sim.origin.y, 1))

        font = pygame.font.SysFont('Arial', 10)
        text = font.render(str(pos_sim), 1, RED)
        self.screen.blit(text, (self.screen.get_width() - 60, self.screen.get_height() - 20))

    def tick(self):
        i = 1

    def run(self):
        self.running = True
        while self.running:
            self.event_handler()
            self.clock.tick(self.mode.ups)
            self.sim.elapsed_frames += 1
            while self.sim.elapsed_frames > self.sim.frames_per_tick:
                self.sim.elapsed_frames -= self.sim.frames_per_tick
                if self.mode.is_playing:
                    self.tick()
            self.draw()

            pygame.display.update()
        pygame.quit()

    def get_cell_from_pixel(self, p):
        return Point(int(p[0]/self.sim.scale + self.sim.origin.x), int(p[1]/self.sim.scale + self.sim.origin.y))

    # Only get the window focus, no other events
    def get_window_focus(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
                sys.exit()


    # Go through all the events picked up by pygame
    def event_handler(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.mode.is_playing = not self.mode.is_playing

                if event.key == pygame.K_r and not self.mode.is_playing:
                    self.map.cell = np.zeros([140, 140], dtype=np.uint8)



            if event.type == pygame.MOUSEBUTTONDOWN:
                self.mode.is_dragging = True
                if event.button == pygame.BUTTON_LEFT:
                    if not self.mode.is_playing:
                        cell = self.get_cell_from_pixel(event.pos)
                        if self.map.cell[cell.x, cell.y] == 0:
                            self.map.cell[cell.x, cell.y] = 1
                        elif self.map.cell[cell.x, cell.y] == 1:
                            self.map.cell[cell.x, cell.y] = 0
                        self.mode.drag_value = self.map.cell[cell.x, cell.y]
            #     if event.button == pygame.BUTTON_MIDDLE:
            #
            #     if event.button == pygame.BUTTON_RIGHT:
            #
            if event.type == pygame.MOUSEBUTTONUP:
                self.mode.is_dragging = False
            #
            if event.type == pygame.MOUSEMOTION:
                if self.mode.is_dragging and pygame.mouse.get_pressed()[0]:
                    if not self.mode.is_playing:
                        cell = self.get_cell_from_pixel(event.pos)
                        self.map.cell[cell.x, cell.y] = self.mode.drag_value
            # if event.type == pygame.MOUSEWHEEL:
