import sys
from datetime import datetime

import os
import glob

import pygame
import numpy as np
import math
import random

from terrain_generation import TerrainGenerator

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

class GraphicData:
    def __init__(self):
        self.color = []
        self.region_size = 100
        self.region = []
        self.region_prepared = False


class MapData:
    def __init__(self):
        self.range = (0, 63)
        self.dim = Point(140, 140)
        self.tile = np.zeros([140, 140], dtype=int)
        self.generator = TerrainGenerator(140, 140)


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
        self.graphics = GraphicData()

        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.running = False

    def generate(self):
        #self.map.generator.fractal(self.map.tile, self.map.range)
        plate_map = np.zeros([self.map.dim.x, self.map.dim.y], dtype=int)
        self.map.generator.lines(plate_map, 10)
        plates = self.map.generator.plates(plate_map)

        # p = [[i,0] for i in range(64)]
        # for plate in plates:
        #     p[plate[0]][1] += plate[1]

        #self.map.tile = plate_map
        self.map.generator.continental(self.map.tile, plate_map, plates, 0.5, (0,80))
        self.map.generator.devolcanize(self.map.tile, 1)

    def set_map_size(self, width, height, seed=None):
        self.map.dim = Point(width, height)
        self.map.tile = np.zeros([width, height], dtype=int)
        self.map.generator = TerrainGenerator(width, height, seed)

    def set_view(self, view):
        v = (view[0], view[1], (view[2] - view[0]) / self.screen.get_width(), (view[3] - view[1]) / self.screen.get_height())
        self.sim.metric = v

    # stage is an array. Each stage is an index with a color
    def set_color_stages(self, stage):
        prior_stage = stage[0]
        for next_stage in stage[1:]:
            start = prior_stage[0]
            rnge = next_stage[0] - prior_stage[0]
            for s in range(prior_stage[0], next_stage[0]):
                t = (s - start) / rnge
                color = ( int(prior_stage[1][0] * (1-t) + next_stage[1][0] * t),
                          int(prior_stage[1][1] * (1-t) + next_stage[1][1] * t),
                          int(prior_stage[1][2] * (1-t) + next_stage[1][2] * t))
                self.graphics.color.append(color)
            prior_stage = next_stage
        self.graphics.color.append(stage[-1][1])
        self.map.range = (stage[0][0], stage[-1][0])

    def draw(self):
        self.screen.fill(BLACK)
        self.draw_terrain()
        #self.draw_mouse_pos()

    def draw_map_megatiles(self):
        for region_x in range(math.ceil(self.map.dim.x / self.graphics.region_size)):
            region_row = []
            for region_y in range(math.ceil(self.map.dim.y / self.graphics.region_size)):
                region_map = pygame.Surface((self.graphics.region_size, self.graphics.region_size))
                for col in range(min(self.graphics.region_size, self.map.dim.x - self.graphics.region_size*region_x)):
                    for row in range(min(self.graphics.region_size, self.map.dim.y - self.graphics.region_size*region_y)):
                        x = self.graphics.region_size*region_x + col
                        y = self.graphics.region_size*region_y + row
                        color = self.graphics.color[self.map.tile[x][y]]
                        pygame.draw.rect(region_map, color,(col, row, 1, 1))
                region_row.append(region_map)
            self.graphics.region.append(region_row)

    def draw_terrain(self):
        if self.graphics.region_prepared:
            size = (self.graphics.region_size * self.sim.scale + 1, self.graphics.region_size * self.sim.scale + 1)
            for region_x in range(math.ceil(self.map.dim.x / self.graphics.region_size)):
                for region_y in range(math.ceil(self.map.dim.y / self.graphics.region_size)):
                    x = (self.graphics.region_size*region_x - self.sim.origin.x) * self.sim.scale
                    y = (self.graphics.region_size*region_y - self.sim.origin.y) * self.sim.scale
                    if (0 < x + self.graphics.region_size * self.sim.scale and x < self.screen.get_width()) and (0 < y + self.graphics.region_size * self.sim.scale and y < self.screen.get_height()):
                        terrain = pygame.transform.scale(self.graphics.region[region_x][region_y], size)
                        self.screen.blit(terrain, (x, y))
        else:
            self.draw_map_megatiles()
            self.graphics.region_prepared = True
        # for col in range(self.map.dim.x):
        #     for row in range(self.map.dim.y):
        #         color = self.graphics.color[self.map.tile[col][row]]
        #         pygame.draw.rect(self.screen, color,
        #                          ((col - self.sim.origin.x) * self.sim.scale,
        #                           (row - self.sim.origin.y) * self.sim.scale,
        #                           self.sim.scale + 1,
        #                           self.sim.scale + 1))

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



            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    self.mode.is_dragging = True
            #     if event.button == pygame.BUTTON_MIDDLE:
            #
            #     if event.button == pygame.BUTTON_RIGHT:
            #
            if event.type == pygame.MOUSEBUTTONUP:
                self.mode.is_dragging = False
            #
            if event.type == pygame.MOUSEMOTION:
                if self.mode.is_dragging:
                    self.sim.origin.x -= event.rel[0] / self.sim.scale
                    self.sim.origin.y -= event.rel[1] / self.sim.scale
            #     if self.mode.is_dragging and pygame.mouse.get_pressed()[0]:
            #         if not self.mode.is_playing:
            #             cell = self.get_cell_from_pixel(event.pos)
            #             self.map.cell[cell.x, cell.y] = self.mode.drag_value
            # if event.type == pygame.MOUSEWHEEL:
            if event.type == pygame.MOUSEWHEEL:
                ul_sim_old = (self.sim.origin.x, self.sim.origin.y)
                delta_pix = pygame.mouse.get_pos()
                delta_sim_old = (delta_pix[0] / self.sim.scale, delta_pix[1] / self.sim.scale)
                center_sim = (ul_sim_old[0] + delta_sim_old[0], ul_sim_old[1] + delta_sim_old[1])

                delta_sim_new = (delta_sim_old[0] / (1 + 0.1 * event.y), delta_sim_old[1] / (1 + 0.1 * event.y))
                ul_sim_new = (center_sim[0] - delta_sim_new[0], center_sim[1] - delta_sim_new[1])
                self.sim.origin.x = ul_sim_new[0]
                self.sim.origin.y = ul_sim_new[1]

                self.sim.scale *= 1 + 0.1 * event.y