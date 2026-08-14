import math
import random

import numpy as np
from noise import snoise2, snoise3

def clamp(value, low=-1, high=1):
    return max(low, min(high, value))

class TerrainGenerator:
    def __init__(self, width, height, seed=None):
        self.width = width
        self.height = height
        self.seed = seed
        if seed is None:
            self.seed = random.randint(1,1000000)

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
        for x in range(self.width):
            for y in range(self.height):
                if map[x][y] != 0: continue
                aff = fill(x,y,p)
                if aff > min_size or p == 1:
                    plates += [[p,aff]]
                    p += 1
                else:
                    fill(x,y,p-1)
                    plates[-1][1] += aff
        return plates

# Div o-o -> shallow
# Div o-l -> shallow, volcanoes (64)
# Div l-l -> valleys, oceans
# Con o-o -> volcanic islands, trenches
# Con o-l -> tall mountains w/ trenches, volcanoes
# Con l-l -> tall mountains
# Trn o-o
# Trn o-l
# Trn l-l

    # Size 400: scale=0.25, lines=10, alt_lacun=3, ang_lacun=1
    # Size 1000: scale=0.1, lines=20, alt_lacun=5, ang_lacun=3
    def continental(self, map, plate_map, plates, land_ocean_ratio, height, volc_tile, scale=0.25, loading_bar_provider=lambda x: None):
        land_plates = [True] * (len(plates) + 2)
        land = 1
        ocean = 1
        while plates:
            n, aff = random.choice(plates)
            if land/ocean > land_ocean_ratio:
                land_plates[n] = False
                ocean += aff
            else:
                land += aff
            plates.remove([n,aff])

        ocean_multiplier = 0.5
        smooth_range = 10
        lateral_scale = 0.5

        update_every = 10000
        batch = 0
        completed = 0
        total = self.width * self.height

        for x in range(self.width):
            if batch > update_every:
                batch %= update_every
                loading_bar_provider(completed/total)
            completed += self.height
            batch += self.height
            for y in range(self.height):
                plate = plate_map[x][y]
                if plate == volc_tile:
                    map[x][y] = volc_tile
                    continue
                # if not land_plates[plate]:
                #     map[x][y] = 98
                #     continue
                dx = math.cos(plate/height*4*math.pi)
                dy = math.sin(plate/height*4*math.pi)

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

    # filamentous
    def fractal(self, map, rnge, scale=0.1):
        minimum = rnge[0]
        maximum = rnge[1]
        delta = maximum - minimum
        for x in range(self.width):
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