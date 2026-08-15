import math
import random

import numpy as np
from noise import snoise2, snoise3

def clamp(value, low=-1, high=1):
    return max(low, min(high, value))

class TerrainGenerator:
    def __init__(self, width, height, seed=None, loading_bar_provider=lambda x: None):
        self.width = width
        self.height = height
        self.seed = seed
        if seed is None:
            self.seed = random.randint(1,1000000)

        self.loading_bar = loading_bar_provider
        self.update_every = 10000
        self.batch = 0
        self.completed = 0
        self.total = self.width * self.height

    def loading_bar_reset(self):
        self.batch = 0
        self.completed = 0

    def loading_bar_update(self):
        if self.batch > self.update_every:
            self.batch %= self.update_every
            self.loading_bar(self.completed / self.total)
        self.completed += self.height
        self.batch += self.height

    def lines(self, map, count, line_value, scale=0.8):
        for c in range(count):
            p = (random.randint(0,self.width-1),random.randint(0,self.height-1))
            length = 500

            prev_x = snoise2(0, 0, 5, 0.2, 6, 1 / scale, 1 / scale, base=p[1] % 256) * self.width + p[0]
            prev_y = snoise2(0, 0, 5, 0.2, 6, 1 / scale, 1 / scale, base=p[0] % 256) * self.height + p[1]
            for l in range(1,length + 1):
                x = snoise2(l / length / scale, 0, 5, 0.2, 6, 1 / scale, 1 / scale, base=p[1] % 256) * self.width + \
                         p[0]
                y = snoise2(l / length / scale, 0, 5, 0.2, 6, 1 / scale, 1 / scale, base=p[0] % 256) * self.height + \
                         p[1]
                dx = abs(x - prev_x)
                dy = abs(y - prev_y)
                dl = math.ceil(dx+dy+2)
                for i in range(dl):
                    ix = i/dl*prev_x + (1-i/dl)*x
                    iy = i/dl*prev_y + (1-i/dl)*y
                    map[int((ix + self.width) % self.width), int((iy + self.height) % self.height)] = line_value
                prev_x = x
                prev_y = y



    def plates(self, map, edge_tile, min_size=0):
        def fill(f_x, f_y, f, c=0):
            affected = 0
            q = [(f_x, f_y)]
            while q:
                qx, qy = q.pop()
                affected += 1
                map[qx][qy] = f
                if map[(qx + 1) % self.width, qy] == edge_tile:
                    map[(qx + 1) % self.width, qy] = f
                if map[(qx + 1) % self.width, qy] == c:
                    q.append(((qx + 1) % self.width, qy))
                    map[(qx + 1) % self.width, qy] = -2

                if map[(qx - 1 + self.width) % self.width, qy] == edge_tile:
                    map[(qx - 1 + self.width) % self.width, qy] = f
                if map[(qx - 1 + self.width) % self.width, qy] == c:
                    q.append(((qx - 1 + self.width) % self.width, qy))
                    map[(qx - 1 + self.width) % self.width, qy] = -2

                if map[qx, (qy + 1) % self.height] == edge_tile:
                    map[qx, (qy + 1) % self.height] = f
                if map[qx, (qy + 1) % self.height] == c:
                    q.append((qx, (qy + 1) % self.height))
                    map[qx, (qy + 1) % self.height] = -2

                if map[qx, (qy - 1 + self.height) % self.height] == edge_tile:
                    map[qx, (qy - 1 + self.height) % self.height] = f
                if map[qx, (qy - 1 + self.height) % self.height] == c:
                    q.append((qx, (qy - 1 + self.height) % self.height))
                    map[qx, (qy - 1 + self.height) % self.height] = -2
            return affected


        plates = []
        p = 1
        self.loading_bar_reset()
        for x in range(self.width):
            self.loading_bar_update()
            for y in range(self.height):
                if map[x][y] != 0: continue
                aff = fill(x,y,p)
                plates += [[p, aff, (x,y)]]
                p += 1
                # if aff > min_size or p == 1:
                #     plates += [[p,aff]]
                #     p += 1
                # else:
                #     fill(x,y,p-1)
                #     plates[-1][1] += aff

        removal = []
        if p > 2:
            for plate in plates:
                if plate[1] < min_size:

                    removal.append(plate[0] - 1)
                    x,y = plate[2]
                    dx,dy = 0, 0
                    while not (dx or dy):
                        dx = random.randint(-1,1)
                        dy = random.randint(-1,1)
                    n = plate[0]
                    while n == plate[0] or n == edge_tile:
                        x = (x + dx + self.width) % self.width
                        y = (y + dy + self.height) % self.height
                        n = map[x][y]

                    aff = fill(plate[2][0], plate[2][1], map[x][y], c=plate[0])
                    plates[map[x][y] - 1][1] += aff

        for i in reversed(removal):
            plates.pop(i)

        for i, plate in enumerate(plates):
            n = plate[0]
            if i+1 == n: continue
            plates[i][0] = i+1
            fill(plate[2][0], plate[2][1], i+1, c=n)

        p = len(plates)
        last_safe = 1
        for x in range(self.width):
            for y in range(self.height):

                if map[x][y] > p: map[x][y] = last_safe
                else: last_safe = map[x][y]

        return plates

    # Size 400: scale=0.25, lines=10, alt_lacun=3, ang_lacun=1
    # Size 1000: scale=0.1, lines=20, alt_lacun=5, ang_lacun=3
    def continental(self, map, plate_map, plates, land_ocean_ratio, height, volc_tile, scale=0.25):
        land_plates = [True] * (len(plates) + 2)
        land = 1
        ocean = 1
        pl = list(range(len(plates)))
        while pl:
            n = random.choice(pl)
            if land/ocean > land_ocean_ratio:
                land_plates[n + 1] = False
                ocean += plates[n][1]
            else:
                land += plates[n][1]
            pl.remove(n)

        ocean_multiplier = 0.5
        smooth_range = 10
        lateral_scale = 0.5

        self.loading_bar_reset()

        for x in range(self.width):
            self.loading_bar_update()
            for y in range(self.height):
                plate = plate_map[x][y]
                if plate == volc_tile:
                    map[x][y] = volc_tile
                    continue
                # if not land_plates[plate]:
                #     map[x][y] = 98
                #     continue

                random.seed(int(plate) * self.seed)
                dx = math.cos(random.uniform(0, 2 * math.pi))
                dy = math.sin(random.uniform(0, 2 * math.pi))

                multiplier = land_plates[plate]

                for d in range(smooth_range):
                    multiplier += land_plates[plate_map[int(x + dx*d) % self.width, int(y + dy*d) % self.height]]
                    multiplier += land_plates[plate_map[int(x - lateral_scale*dy*d + self.width) % self.width, int(y + lateral_scale*dx*d) % self.height]]
                    multiplier += land_plates[plate_map[int(x - dx*d + self.width) % self.width, int(y - dy*d + self.height) % self.height]]
                    multiplier += land_plates[plate_map[int(x + lateral_scale*dy*d) % self.width, int(y - lateral_scale*dx*d + self.height) % self.height]]

                multiplier /= smooth_range * 4 + 1
                multiplier = (1-multiplier) * ocean_multiplier + multiplier

                alt = (clamp(snoise2(x / self.width, y / self.height, 5, 0.5, 3, 1, 1, base=(self.seed + 1) % 256)))
                ang = (clamp(snoise2(x / self.width, y / self.height, 5, 0.8, 1, 1, 1, base=(self.seed + 2) % 256)))

                map[x][y] += multiplier * int(((clamp(1.2*snoise2(
                    x / self.width / scale + alt * math.cos(ang),
                    y / self.height / scale + alt * math.sin(ang),
                    5,
                    0.5,
                    2,
                    1 / scale,
                    1 / scale,
                    base=self.seed % 256))
                                  + 1) / 2 ) * (height - 1))
        return land_plates

    def devolcanize(self, map, volc_tile, perc=0.96):
        for x in range(self.width):
            for y in range(self.height):
                if map[x][y] != volc_tile: continue
                if random.random() < perc:
                    h = 0
                    used = 0
                    if map[(x + 1) % self.width, y] != volc_tile:
                        h += map[(x + 1) % self.width, y]
                        used += 1

                    if map[(x - 1 + self.width) % self.width, y] != volc_tile:
                        h += map[(x - 1 + self.width) % self.width, y]
                        used += 1

                    if map[x, (y + 1) % self.height] != volc_tile:
                        h += map[x, (y + 1) % self.height]
                        used += 1

                    if map[x, (y - 1 + self.height) % self.height] != volc_tile:
                        h += map[x, (y - 1 + self.height) % self.height]
                        used += 1
                    if not used:
                        h = volc_tile
                    else:
                        h = h // used

                    map[x, y] = h

    # Div o-o -> shallow
    # Div o-l -> shallow, volcanoes (64)
    # Div l-l -> valleys, oceans
    # Con o-o -> volcanic islands, trenches
    # Con o-l -> tall mountains w/ trenches, volcanoes
    # Con l-l -> tall mountains
    # Trn o-o
    # Trn o-l
    # Trn l-l

    def plate_dir(self, plate):
        random.seed(int(plate) * self.seed)
        dx = math.cos(random.uniform(0, 2 * math.pi))
        dy = math.sin(random.uniform(0, 2 * math.pi))
        return dx, dy

    def tectonics(self, map, plate_map, land_plates):
        check_range = 10

        self.loading_bar_reset()
        for x in range(self.width):
            self.loading_bar_update()
            for y in range(self.height):
                this_plate = plate_map[x][y]

                dx, dy = self.plate_dir(this_plate)

                next_plate = this_plate
                prev_plate = this_plate

                next_plate_dist = math.inf
                prev_plate_dist = math.inf

                for d in range(check_range, -1, -1):
                    forward = plate_map[int(x + dx * d) % self.width, int(y + dy * d) % self.height]
                    if forward != this_plate:
                        next_plate = forward
                        next_plate_dist = d
                    backward = plate_map[
                        int(x - dx * d + self.width) % self.width, int(y - dy * d + self.height) % self.height]
                    if backward != this_plate:
                        prev_plate = backward
                        prev_plate_dist = d

                if next_plate != this_plate:
                    nx, ny = self.plate_dir(next_plate)
                    ang = dx * nx + dy * ny
                    if ang < 0.5:
                        map[x][y] = 99 - next_plate_dist
                    elif ang > 0.5:
                        map[x][y] = 100 + next_plate_dist*5
                    else:
                        map[x][y] = 199 - next_plate_dist*5

                if prev_plate != this_plate:
                    nx, ny = self.plate_dir(prev_plate)
                    ang = dx * nx + dy * ny
                    if ang < 0.5:
                        map[x][y] = 81 + prev_plate_dist
                    elif ang > 0.5:
                        map[x][y] = 100 + prev_plate_dist * 5
                    else:
                        map[x][y] = 199 - prev_plate_dist * 5


    # filamentous
    def fractal(self, map, rnge, scale=0.1):
        minimum = rnge[0]
        maximum = rnge[1]
        delta = maximum - minimum

        self.loading_bar_reset()
        for x in range(self.width):
            self.loading_bar_update()
            for y in range(self.height):
                alt = (clamp(snoise2(x/self.width, y/self.height, 5, 0.5, 2.5, 1, 1, base=(self.seed+1)%256)))
                ang = (clamp(snoise2(x/self.width, y/self.height, 5, 0.8, 2, 1, 1, base=(self.seed+2)%256)))
                map[x][y] += int((clamp(-0.7 + 3*snoise2(
                    x/self.width/scale + alt*math.cos(ang),
                    y/self.height/scale + alt*math.sin(ang),
                    5,
                    0.5,
                    2,
                    1/scale,
                    1/scale,
                    base=self.seed%256))
                    + 1) / 2 * delta + minimum)

    def testing(self, map, rnge, scale_r=0.2, scale_h=0.03):
        minimum = rnge[0]
        maximum = rnge[1]
        delta = maximum - minimum

        step = 0.1
        strength = 0.5

        self.loading_bar_reset()
        for x in range(self.width):
            self.loading_bar_update()
            for y in range(self.height):
                r1 = 3*math.pi*clamp(snoise2(x / self.width / scale_r, y / self.height / scale_r, 2, 0.5, 25, 1 / scale_r, 1 / scale_r,
                             base=(self.seed + 1) % 256))
                r2 = 3*math.pi*clamp(snoise2(x / self.width / scale_r, y / self.height / scale_r, 2, 0.5, 25, 1 / scale_r, 1 / scale_r,
                             base=(self.seed + 2) % 256))
                r3 = 3*math.pi * clamp(
                    snoise2(x / self.width / scale_r, y / self.height / scale_r, 2, 0.5, 25, 1 / scale_r, 1 / scale_r,
                            base=(self.seed + 3) % 256))

                f = snoise2(x / self.width / scale_h, y / self.height / scale_h, 5, 0.5, 2, 1 / scale_h, 1 / scale_h,
                            base=self.seed % 256)
                fx = snoise2((x + step * math.cos(r1)) / self.width / scale_h,
                             (y + step * math.sin(r1)) / self.height / scale_h, 5, 0.5, 2, 1 / scale_h, 1 / scale_h,
                             base=self.seed % 256)
                f_x = snoise2((x - step * math.cos(r1)) / self.width / scale_h,
                             (y - step * math.sin(r1)) / self.height / scale_h, 5, 0.5, 2, 1 / scale_h, 1 / scale_h,
                             base=self.seed % 256)
                fy = snoise2((x + step * math.cos(r2)) / self.width / scale_h,
                             (y + step * math.sin(r2)) / self.height / scale_h, 5, 0.5, 2, 1 / scale_h, 1 / scale_h,
                             base=self.seed % 256)
                f_y = snoise2((x - 0.1 * math.cos(r2)) / self.width / scale_h,
                             (y - 0.1 * math.sin(r2)) / self.height / scale_h, 5, 0.5, 2, 1 / scale_h, 1 / scale_h,
                             base=self.seed % 256)
                fz = snoise2((x + step * math.cos(r2)) / self.width / scale_h,
                             (y + step * math.sin(r2)) / self.height / scale_h, 5, 0.5, 2, 1 / scale_h, 1 / scale_h,
                             base=self.seed % 256)
                f_z = snoise2((x - 0.1 * math.cos(r3)) / self.width / scale_h,
                              (y - 0.1 * math.sin(r3)) / self.height / scale_h, 5, 0.5, 2, 1 / scale_h, 1 / scale_h,
                              base=self.seed % 256)

                steep_f = f - strength * ( abs(fx - f_x) + abs(fy - f_y) + abs(fz - f_z))
                map[x][y] += int((clamp(-0.7 + 3 * steep_f) + 1) / 2 * delta + minimum)