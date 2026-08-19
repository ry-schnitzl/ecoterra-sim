import sys
from datetime import datetime

import os
import glob

import pygame
import numpy as np
import math
import random

from pygame import Surface
import cfg
from cfg import is_different_biome, get_height
from cfg import get_biome
from cfg import get_biome

from terrain_generation import TerrainGenerator
from terrain_generation import clamp as clamp

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class SimulationData:
    def __init__(self, fpt):
        self.frames_per_tick = fpt
        self.elapsed_frames = 0
        # set the view to (0, 0) in sim space as the ul and (1 pixel per sim dist) for x and y
        self.origin = Point(0,0)
        self.scale = 5
        self.types = 2

class GraphicData:
    def __init__(self):
        self.color = [cfg.WHITE]
        self.region_size = 10
        self.region = []
        self.region_prepared = False
        self.allowed_scale_range = (1, 150)
        self.loading_bar_rect = (100, 600, 500, 50)
        self.loading_bar_fill = 0
        self.loading_bar = Surface((500, 50))


class MapData:
    def __init__(self):
        self.range = (0, 63)
        self.dim = Point(140, 140)
        self.tile = np.zeros([140, 140], dtype=int)
        self.generator = TerrainGenerator(140, 140)
        self.is_generated = False
        self.chunk_size = 10
        self.chunk = []


class ModeData:
    def __init__(self, ups):
        self.ups = ups # simulation updates per second
        self.is_dragging = False
        self.is_playing = False
        self.drag_value = 0

class ImperialGame:
    def ix(self, x):
        return int(x + self.map.dim.x) % self.map.dim.x
    def iy(self, y):
        return int(y + self.map.dim.y) % self.map.dim.y
    def nx(self, x, incr):
        return (x + incr + self.map.dim.x) % self.map.dim.x
    def ny(self, y, incr):
        return (y + incr + self.map.dim.y) % self.map.dim.y

    def r(self, pt):
        return self.map.tile[self.ix(pt[0])][self.iy(pt[1])]
    def rn(self, pt, incr=(0,0)):
        return self.map.tile[int(self.nx(pt[0], incr[0]))][int(self.ny(pt[1], incr[1]))]
    def rx(self, pt, incr):
        return self.map.tile[self.nx(pt[0], incr)][pt[1]]
    def ry(self, pt, incr):
        return self.map.tile[pt[0]][self.ny(pt[1], incr)]

    def set(self, pt, val):
        self.map.tile[self.ix(pt[0])][self.iy(pt[1])] = val
    def setn(self, pt, incr, val):
        self.map.tile[int(self.nx(pt[0], incr[0]))][int(self.ny(pt[1], incr[1]))] = val
    def setx(self, pt, incr, val):
        self.map.tile[self.nx(pt[0], incr)][pt[1]] = val
    def sety(self, pt, incr, val):
        self.map.tile[pt[0]][self.ny(pt[1], incr)] = val

    def __init__(self, width, height, fps, ups):
        self.mode = ModeData(ups)
        self.map = MapData()
        self.sim = SimulationData(ups / fps)
        self.graphics = GraphicData()
        self.create_loading_bar_cache()

        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        self.screen.fill(cfg.SKY_BLUE)
        pygame.display.update()
        self.clock = pygame.time.Clock()
        self.running = False

    def generate(self):
        self.map.generator.loading_bar = lambda completed: self.update_with_loading_bar(completed)

        # Create the plate map first
        volc_tile = -1
        plate_map = np.zeros([self.map.dim.x, self.map.dim.y], dtype=int)
        self.map.generator.lines(plate_map, 10, volc_tile)
        plates = self.map.generator.plates(plate_map, volc_tile, 500)
        land_plates = self.map.generator.choose_land_plates(plates, 0.3)

        # Generate the main continents
        self.map.generator.continental(self.map.tile, plate_map, land_plates, 80, volc_tile)

        # Create the tectonic map, and add tectonic effects to the continental map
        tectonic_map = np.zeros([self.map.dim.x, self.map.dim.y], dtype=int)
        self.map.generator.tectonics(tectonic_map, plate_map)
        self.map.generator.apply_tectonic_effects(self.map.tile, tectonic_map, 0, 80)

        self.map.is_generated = True

    def generate_testing(self):
        self.map.generator.loading_bar = lambda completed: self.update_with_loading_bar(completed)

        # Create the plate map first
        volc_tile = -1
        plate_map = np.zeros([self.map.dim.x, self.map.dim.y], dtype=int)
        self.map.generator.lines(plate_map, 10, volc_tile)
        plates = self.map.generator.plates(plate_map, volc_tile, 500)
        land_plates = self.map.generator.choose_land_plates(plates, 0.25)

        # Generate the main continents
        self.map.generator.continental(self.map.tile, plate_map, land_plates, 96, volc_tile)

        # Create the tectonic map, and add tectonic effects to the continental map
        tectonic_map = np.zeros([self.map.dim.x, self.map.dim.y], dtype=int)
        self.map.generator.tectonics(tectonic_map, plate_map)
        self.map.generator.apply_tectonic_effects(self.map.tile, tectonic_map, 0, 96)

        #self.map.generator.outline(self.map.tile, 201)
        # Todo: River Generation
        river_map = np.zeros([self.map.dim.x, self.map.dim.y], dtype=int)
        self.map.generator.river(self.map.tile, river_map)

        # Todo: Biome Generation
        biome_map = np.zeros([self.map.dim.x, self.map.dim.y], dtype=int)
        self.map.generator.create_biome_map(self.map.tile, biome_map)

        self.map.is_generated = True

    def set_map_size(self, width, height, seed=None):
        self.map.dim = Point(width, height)
        self.map.tile = np.zeros([width, height], dtype=int)
        self.map.generator = TerrainGenerator(width, height, seed)

    def set_view(self, view):
        v = (view[0], view[1], (view[2] - view[0]) / self.screen.get_width(), (view[3] - view[1]) / self.screen.get_height())
        self.sim.metric = v

    def use_color_scheme_terrain(self):
        self.set_color_stages([[0, (15, 35, 120)],    # Basal Ocean
                            [22, (18, 46, 184)],            # Shallow Ocean
                            [29,(12, 240, 217)],
                            [30,(235, 232, 174)],           # Beach
                            [40,(62, 161, 55)],             # Vegetation
                            [55,(56, 47, 38)],              # Low Mountains
                            [65, (220, 220, 220)],          # Rockies
                            [80, (255,255,255)],            # Snowy
                            [99,(148, 161, 235)],           # Undefined; Currently blue snowy
                            [100, (18, 46, 184)],           # River Variants
                            [130, (67, 244, 202)],
                            [140, (92, 159, 167)],
                            [155, (55, 70, 86)],
                            [165, (119, 119, 180)],
                            [180, (186, 221, 219)],
                            [201, (0, 0, 0)],               # Testing Regions
                            [501, (255, 255, 255)],
                            [502, (242, 56, 10)],
                            [600, (97, 145, 105)],
                            [700, (88, 22, 219)],
                            [800, (148, 115, 37)],
                            [900, (77, 240, 188)],
                            [1000, (138, 12, 136)],],
                         (25,40))

    def use_color_scheme_biomes(self):
        self.set_color_stages(cfg.biome_color_stages, (25,40))

    def use_color_scheme_diagnostic(self):
        self.set_color_stages([[0, (0, 0, 0)],
                              [5, (255, 0, 0)],
                              [10, (242, 219, 12)],
                              [15, (8, 196, 17)],
                              [20,(61, 227, 242)],
                              [25, (29, 18, 181)],
                              [30, (169, 16, 224)]],
                             (10, 25))

    # stage is an array. Each stage is an index with a color
    def set_color_stages(self, stage, loading_bar_range=None):
        self.graphics.color = []
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
        if not loading_bar_range: loading_bar_range = (0, len(self.graphics.color) - 1)
        self.create_loading_bar_cache(loading_bar_range)

    def draw(self):
        self.draw_regions()
        if not self.map.is_generated: self.screen.fill(cfg.SKY_BLUE)

        self.draw_mouse_info()

    def create_region_cache(self):
        for region_x in range(math.ceil(self.map.dim.x / self.graphics.region_size)):
            region_row = []
            for region_y in range(math.ceil(self.map.dim.y / self.graphics.region_size)):
                region_map = pygame.Surface((self.graphics.region_size, self.graphics.region_size))
                for col in range(min(self.graphics.region_size, self.map.dim.x - self.graphics.region_size*region_x)):
                    for row in range(min(self.graphics.region_size, self.map.dim.y - self.graphics.region_size*region_y)):
                        x = self.graphics.region_size*region_x + col
                        y = self.graphics.region_size*region_y + row

                        north = self.ry((x, y), -1)
                        east = self.rx((x, y), 1)
                        south = self.ry((x, y), 1)
                        west = self.rx((x, y), -1)

                        here = self.map.tile[x][y]
                        total = 0
                        total_red = 0
                        total_green = 0
                        total_blue = 0
                        if is_different_biome(here, north):
                            total_red += self.graphics.color[north][0]
                            total_green += self.graphics.color[north][1]
                            total_blue += self.graphics.color[north][2]
                            total += 1
                        if is_different_biome(here, east):
                            total_red += self.graphics.color[east][0]
                            total_green += self.graphics.color[east][1]
                            total_blue += self.graphics.color[east][2]
                            total += 1
                        if is_different_biome(here, south):
                            total_red += self.graphics.color[south][0]
                            total_green += self.graphics.color[south][1]
                            total_blue += self.graphics.color[south][2]
                            total += 1
                        if is_different_biome(here, west):
                            total_red += self.graphics.color[west][0]
                            total_green += self.graphics.color[west][1]
                            total_blue += self.graphics.color[west][2]
                            total += 1
                        total_red += (total + 1) * self.graphics.color[here][0]
                        total_green += (total + 1) * self.graphics.color[here][1]
                        total_blue += (total + 1) * self.graphics.color[here][2]
                        total = 2*total + 1
                        color = (total_red // total, total_green // total, total_blue // total)
                        pygame.draw.rect(region_map, color,(col, row, 1, 1))
                region_row.append(region_map)
            self.graphics.region.append(region_row)

    def create_loading_bar_cache(self, color_range=(0,0)):
        cache = pygame.Surface((self.graphics.loading_bar_rect[2], self.graphics.loading_bar_rect[3]))
        cache.fill(self.graphics.color[color_range[0]])
        total_c = color_range[1] - color_range[0] + 1
        for c in range(color_range[0] + 1, color_range[1]):
            stage = (c - color_range[0] - 0.5) / total_c
            start_x = stage * cache.get_width()
            pygame.draw.polygon(cache, self.graphics.color[c], (
                (start_x, cache.get_height()),
                (start_x + cache.get_height(), 0),
                (cache.get_width(), 0),
                (cache.get_width(), cache.get_height())))
        self.graphics.loading_bar = cache

    def draw_regions(self):
        if self.graphics.region_prepared:
            size = (self.graphics.region_size * self.sim.scale, self.graphics.region_size * self.sim.scale)
            pixel_x = 0
            while pixel_x <= self.screen.get_width() + size[0]:
                tile_x = pixel_x / self.sim.scale + self.sim.origin.x
                x = ((tile_x // self.graphics.region_size) * self.graphics.region_size - self.sim.origin.x) * self.sim.scale
                region_x = int(((tile_x + self.map.dim.x) % self.map.dim.x ) // self.graphics.region_size)
                pixel_y = 0
                while pixel_y <= self.screen.get_height() + size[1]:
                    tile_y = pixel_y / self.sim.scale + self.sim.origin.y
                    y = ((tile_y // self.graphics.region_size) * self.graphics.region_size - self.sim.origin.y) * self.sim.scale
                    region_y = int(((tile_y + self.map.dim.y) % self.map.dim.y) // self.graphics.region_size)

                    transformed_region = pygame.transform.scale(self.graphics.region[region_x][region_y], (size[0] + 1, size[1] + 1))
                    self.screen.blit(transformed_region, (x, y))
                    pixel_y += size[1]
                pixel_x += size[0]
        else:
            self.create_region_cache()
            self.graphics.region_prepared = True

    def draw_mouse_info(self):
        pos_pix = pygame.mouse.get_pos()
        pos_sim = (round(pos_pix[0] / self.sim.scale + self.sim.origin.x, 1), round(pos_pix[1] / self.sim.scale + self.sim.origin.y, 1))

        font = pygame.font.SysFont('Arial', 10)
        biome = get_biome(self.r(pos_sim))
        height = get_height(self.r(pos_sim))
        text = font.render(f"{pos_sim} {cfg.biome_name[biome]}<{height}>", 1, cfg.WHITE)
        self.screen.blit(text, (self.screen.get_width() - 150, self.screen.get_height() - 20))

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

    def update_with_loading_bar(self, set_completion):
        self.get_window_focus()
        self.graphics.loading_bar_fill = clamp(set_completion, 0, 1)

        pygame.draw.rect(self.screen, cfg.LIGHT_GRAY, self.graphics.loading_bar_rect)
        area = (0, 0, self.graphics.loading_bar.get_width() * self.graphics.loading_bar_fill, self.graphics.loading_bar.get_height())
        self.screen.blit(self.graphics.loading_bar, self.graphics.loading_bar_rect[0:2], area=area)
        pygame.display.update(self.graphics.loading_bar_rect)


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
                scroll = max(-9, event.y)
                if (scroll > 0 or self.sim.scale >= self.graphics.allowed_scale_range[0]) and (scroll < 0 or self.sim.scale <= self.graphics.allowed_scale_range[1]):
                    ul_sim_old = (self.sim.origin.x, self.sim.origin.y)
                    delta_pix = pygame.mouse.get_pos()
                    delta_sim_old = (delta_pix[0] / self.sim.scale, delta_pix[1] / self.sim.scale)
                    center_sim = (ul_sim_old[0] + delta_sim_old[0], ul_sim_old[1] + delta_sim_old[1])

                    delta_sim_new = (delta_sim_old[0] / (1 + 0.1 * event.y), delta_sim_old[1] / (1 + 0.1 * event.y))
                    ul_sim_new = (center_sim[0] - delta_sim_new[0], center_sim[1] - delta_sim_new[1])
                    self.sim.origin.x = ul_sim_new[0]
                    self.sim.origin.y = ul_sim_new[1]

                    self.sim.scale *= 1 + 0.1 * event.y