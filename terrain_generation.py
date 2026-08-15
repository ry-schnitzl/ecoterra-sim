import math
import random

import numpy as np
from noise import snoise2, snoise3

def clamp(value, low=-1, high=1):
    return max(low, min(high, value))

def point_segment_distance(px, py, x1, y1, x2, y2):
    # Vector from segment start to end
    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        # Segment is actually a point
        return math.hypot(px - x1, py - y1)

    # Project point onto the line, parametrized as t (0 = start, 1 = end)
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)

    # Clamp t to [0, 1] so we stay within the segment
    t = max(0, min(1, t))

    # Closest point on the segment
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy

    return math.hypot(px - closest_x, py - closest_y)

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

    def nx(self, c, incr):
        return (c + incr + self.width) % self.width


    def ny(self, c, incr):
        return (c + incr + self.height) % self.height


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
                    map[int(self.nx(ix, 0)), int(self.ny(iy, 0))] = line_value
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
                if map[self.nx(qx, 1), qy] == edge_tile:
                    map[self.nx(qx, 1), qy] = f
                if map[self.nx(qx, 1), qy] == c:
                    q.append((self.nx(qx, 1), qy))
                    map[self.nx(qx, 1), qy] = -2

                if map[self.nx(qx, -1), qy] == edge_tile:
                    map[self.nx(qx, -1), qy] = f
                if map[self.nx(qx, -1), qy] == c:
                    q.append((self.nx(qx, -1), qy))
                    map[self.nx(qx, -1), qy] = -2

                if map[qx, self.ny(qy, 1)] == edge_tile:
                    map[qx, self.ny(qy, 1)] = f
                if map[qx, self.ny(qy, 1)] == c:
                    q.append((qx, self.ny(qy, 1)))
                    map[qx, self.ny(qy, 1)] = -2

                if map[qx, self.ny(qy, -1)] == edge_tile:
                    map[qx, self.ny(qy, -1)] = f
                if map[qx, self.ny(qy, -1)] == c:
                    q.append((qx, self.ny(qy, -1)))
                    map[qx, self.ny(qy, -1)] = -2
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
                        x = self.nx(x, dx)
                        y = self.ny(y, dy)
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

    def choose_land_plates(self, plates, land_ocean_ratio):
        land_plates = [True] * (len(plates) + 2)
        land = 1
        ocean = 1
        pl = list(range(len(plates)))
        while pl:
            n = random.choice(pl)
            if land / ocean > land_ocean_ratio:
                land_plates[n + 1] = False
                ocean += plates[n][1]
            else:
                land += plates[n][1]
            pl.remove(n)
        return land_plates

    # Size 400: scale=0.25, lines=10, alt_lacun=3, ang_lacun=1
    # Size 1000: scale=0.1, lines=20, alt_lacun=5, ang_lacun=3
    def continental(self, map, plate_map, land_plates, height, volc_tile, scale=0.25):

        ocean_multiplier = 0.5
        smooth_range = 10
        lateral_scale = 0.5

        self.loading_bar_reset()

        for x in range(self.width):
            self.loading_bar_update()
            for y in range(self.height):
                plate = plate_map[x][y]
                if plate == volc_tile:
                    plate = 0
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

    def tectonics(self, tect_map, plate_map):
        check_range = 3

        self.loading_bar_reset()
        for x in range(self.width):
            self.loading_bar_update()
            for y in range(self.height):
                this_plate = plate_map[x][y]

                dx, dy = self.plate_dir(this_plate)

                next_plate = this_plate
                prev_plate = this_plate

                for d in range(check_range, -1, -1):
                    forward = plate_map[int(x + dx * d) % self.width, int(y + dy * d) % self.height]
                    if forward != this_plate:
                        next_plate = forward
                    backward = plate_map[
                        int(x - dx * d + self.width) % self.width, int(y - dy * d + self.height) % self.height]
                    if backward != this_plate:
                        prev_plate = backward

                if next_plate != this_plate:
                    nx, ny = self.plate_dir(next_plate)
                    ang = dx * nx + dy * ny

                    # Plates moving together
                    if ang < 0:
                        tect_map[x][y] = -1
                    # Plates moving in the same direction
                    # elif ang > 0.5:
                    #     map[x][y] = 100 + next_plate_dist*5

                if prev_plate != this_plate:
                    nx, ny = self.plate_dir(prev_plate)
                    ang = dx * nx + dy * ny

                    # Plates moving apart
                    if ang < 0:
                        tect_map[x][y] = 1

                    # Plates moving in the same direction
                    # elif ang > 0.5:
                    #     map[x][y] = 100 + prev_plate_dist * 5

        for x in range(self.width):
            for y in range(self.height):
                if (tect_map[x][y] == -1) and tect_map[self.nx(x, 1)][y] == -1 and tect_map[self.nx(x, -1)][y] == -1 and tect_map[x][self.ny(y, 1)] == -1 and tect_map[x][self.ny(y, -1)] == -1:
                    tect_map[x][y] = -2
                if (tect_map[x][y] == 1) and tect_map[self.nx(x, 1)][y] == 1 and tect_map[self.nx(x, -1)][y] == 1 and tect_map[x][self.ny(y, 1)] == 1 and tect_map[x][self.ny(y, -1)] == 1:
                    tect_map[x][y] = 2


    def identify_mnt_ranges(self, tect_map):
        def get_closest_alt(target_x, target_y, input_x, input_y):
            w = self.width
            h = self.height
            alt_x = input_x - w * (input_x - target_x > w / 2) + w * (target_x - input_x > w / 2)
            alt_y = input_y - h * (input_y - target_y > h / 2) + h * (target_y - input_y > h / 2)
            return alt_x, alt_y

        def get_mnt_chain(x, y):
            endpoint = [(x,y)]
            tect_map[x][y] = -4
            q = [(self.nx(x,1),y),(self.nx(x,-1),y),(x, self.ny(y,-1)),(x, self.ny(y,1))]
            while q:
                qx, qy = q.pop(0)
                if tect_map[qx][qy] != -1 and tect_map[qx][qy] != -2:
                    continue

                nx = self.nx(qx, 1)
                nnx = self.nx(qx, -1)
                ny = self.ny(qy, 1)
                nny = self.ny(qy, -1)
                q.append((nx, qy))
                q.append((nnx,qy))
                q.append((qx,ny))
                q.append((qx,nny))
                q.append((nx, ny))
                q.append((nnx, ny))
                q.append((nx,nny))
                q.append((nnx,nny))

                if tect_map[qx][qy] == -1:
                    tect_map[qx][qy] = -3
                else:
                    tect_map[qx][qy] = -4

                    if len(endpoint) == 1:
                        endpoint.append((qx,qy))
                        continue

                    front_x, front_y = get_closest_alt(qx, qy, endpoint[0][0], endpoint[0][1])
                    back_x, back_y = get_closest_alt(qx, qy, endpoint[-1][0], endpoint[-1][1])
                    dist_front = (qx - front_x)**2 + (qy - front_y)**2
                    dist_back = (qx - back_x) ** 2 + (qy - back_y) ** 2

                    if dist_front < dist_back:
                        px, py = get_closest_alt(qx, qy, endpoint[1][0], endpoint[1][1])
                        dsqr2 = math.sqrt((qx - px)**2 + (qy - py)**2/2)
                        t = 0
                        new_pt = False
                        while t < 1:
                            t += 1/dsqr2
                            tx = int(self.nx(px * t , qx * (1-t)))
                            ty = int(self.ny(py * t , qy * (1-t)))

                            if not(-4 <= tect_map[tx][ty] <= -1):
                                endpoint.insert(0, (qx,qy))
                                new_pt = True
                                break

                        if new_pt: continue
                        tect_map[endpoint[0][0]][endpoint[0][1]] = -3
                        endpoint[0] = (qx, qy)
                    else:
                        px, py = get_closest_alt(qx, qy, endpoint[-2][0], endpoint[-2][1])
                        dsqr2 = math.sqrt(((qx - px) ** 2 + (qy - py) ** 2) * 2 )
                        t = 0
                        new_pt = False
                        while t < 1:
                            t += 1 / dsqr2
                            tx = int(self.nx(px * t, qx * (1 - t)))
                            ty = int(self.ny(py * t, qy * (1 - t)))

                            if not (-4 <= tect_map[tx][ty] <= -1):
                                endpoint.append((qx, qy))
                                new_pt = True
                                break

                        if new_pt: continue

                        tect_map[endpoint[-1][0]][endpoint[-1][1]] = -3
                        endpoint[-1] = (qx, qy)
            return endpoint

        mnt_range = []
        for x in range(self.width):
            for y in range(self.height):
                if tect_map[x][y] == -2:
                    m = get_mnt_chain(x, y)
                    if len(m) < 3: continue
                    use = True
                    # for i in range(len(m) - 1):
                    #     if abs(m[i+1][0] - m[i][0]) > self.width / 2 or abs(m[i+1][1] - m[i][1]) > self.height / 2:
                    #         use = False
                    if use: mnt_range.append(m)

        return mnt_range

    def identify_vly_ranges(self, tect_map):
        def get_closest_alt(target_x, target_y, input_x, input_y):
            w = self.width
            h = self.height
            alt_x = input_x - w * (input_x - target_x > w / 2) + w * (target_x - input_x > w / 2)
            alt_y = input_y - h * (input_y - target_y > h / 2) + h * (target_y - input_y > h / 2)
            return alt_x, alt_y

        def get_vly_chain(x, y):
            endpoint = [(x,y)]
            tect_map[x][y] = 4
            q = [(self.nx(x,1),y),(self.nx(x,-1),y),(x, self.ny(y,-1)),(x, self.ny(y,1))]
            while q:
                qx, qy = q.pop(0)
                if tect_map[qx][qy] != 1 and tect_map[qx][qy] != 2:
                    continue

                nx = self.nx(qx, 1)
                nnx = self.nx(qx, -1)
                ny = self.ny(qy, 1)
                nny = self.ny(qy, -1)
                q.append((nx, qy))
                q.append((nnx,qy))
                q.append((qx,ny))
                q.append((qx,nny))
                q.append((nx, ny))
                q.append((nnx, ny))
                q.append((nx,nny))
                q.append((nnx,nny))

                if tect_map[qx][qy] == 1:
                    tect_map[qx][qy] = 3
                else:
                    tect_map[qx][qy] = 4

                    if len(endpoint) == 1:
                        endpoint.append((qx,qy))
                        continue

                    front_x, front_y = get_closest_alt(qx, qy, endpoint[0][0], endpoint[0][1])
                    back_x, back_y = get_closest_alt(qx, qy, endpoint[-1][0], endpoint[-1][1])
                    dist_front = (qx - front_x)**2 + (qy - front_y)**2
                    dist_back = (qx - back_x) ** 2 + (qy - back_y) ** 2

                    if dist_front < dist_back:
                        px, py = get_closest_alt(qx, qy, endpoint[1][0], endpoint[1][1])
                        dsqr2 = math.sqrt((qx - px)**2 + (qy - py)**2/2)
                        t = 0
                        new_pt = False
                        while t < 1:
                            t += 1/dsqr2
                            tx = int(self.nx(px * t , qx * (1-t)))
                            ty = int(self.ny(py * t , qy * (1-t)))

                            if not(1 <= tect_map[tx][ty] <= 4):
                                endpoint.insert(0, (qx,qy))
                                new_pt = True
                                break

                        if new_pt: continue
                        tect_map[endpoint[0][0]][endpoint[0][1]] = 3
                        endpoint[0] = (qx, qy)
                    else:
                        px, py = get_closest_alt(qx, qy, endpoint[-2][0], endpoint[-2][1])
                        dsqr2 = math.sqrt(((qx - px) ** 2 + (qy - py) ** 2) * 2 )
                        t = 0
                        new_pt = False
                        while t < 1:
                            t += 1 / dsqr2
                            tx = int(self.nx(px * t, qx * (1 - t)))
                            ty = int(self.ny(py * t, qy * (1 - t)))

                            if not (1 <= tect_map[tx][ty] <= 4):
                                endpoint.append((qx, qy))
                                new_pt = True
                                break

                        if new_pt: continue

                        tect_map[endpoint[-1][0]][endpoint[-1][1]] = 3
                        endpoint[-1] = (qx, qy)
            return endpoint

        vly_range = []
        for x in range(self.width):
            for y in range(self.height):
                if tect_map[x][y] == 2:
                    v = get_vly_chain(x, y)
                    if len(v) < 3: continue
                    use = True
                    # for i in range(len(m) - 1):
                    #     if abs(m[i+1][0] - m[i][0]) > self.width / 2 or abs(m[i+1][1] - m[i][1]) > self.height / 2:
                    #         use = False
                    if use: vly_range.append(v)

        return vly_range


    def generate_all_mnt_ranges(self, map, mnt_ranges, height):
        total = len(mnt_ranges)
        n = 0
        for m in mnt_ranges:
            self.loading_bar(n/total)
            n += 1
            for i in range(1,len(m)):
                amplitude = int(clamp(random.normalvariate(15, 10), 5, 40))
                self.generate_mnt_range(map, m[i - 1], m[i], height, max_effect=amplitude,
                                        max_offset=int(0.6 * amplitude), magnitude=int(0.5 * amplitude))

    def generate_mnt_range(self, map, a, b, height, max_effect=20, max_offset=10, magnitude=20, sea_erosion=0.75, scale=0.05):

        def get_closest_alt(target_x, target_y, input_x, input_y):
            w = self.width
            h = self.height
            alt_x = input_x - w * (input_x - target_x > w/2) + w * (target_x - input_x > w/2)
            alt_y = input_y - h * (input_y - target_y > h/2) + h * (target_y - input_y > h/2)
            return alt_x, alt_y

        b_alt = get_closest_alt(a[0], a[1], b[0], b[1])

        def closeness_to_line(x1, y1):
            px = x1 + max_offset * snoise2(x1 / self.width / scale, y1 / self.height / scale, 4, 0.4, 2, 1 / scale, 1 / scale,
                            base=self.seed % 256)
            py = y1 + max_offset * snoise2(x1 / self.width / scale, y1 / self.height / scale, 4, 0.4, 2, 1 / scale, 1 / scale,
                              base=(self.seed + 1) % 256)
            px_alt, py_alt = get_closest_alt(a[0],a[1], px, py)
            return point_segment_distance(px_alt, py_alt, a[0], a[1], b_alt[0], b_alt[1])

        dy = b_alt[1] - a[1]
        dx = b_alt[0] - a[0]
        d = math.sqrt(dx*dx + dy*dy)
        sq2d = math.sqrt(2) * d
        sq2eff = int(math.sqrt(2) * max_effect)
        dy /= sq2d
        dx /= sq2d

        strict_effect = max_effect - max_offset
        amplitude = height / strict_effect

        last_cache = []
        cache = []
        for l in range(-sq2eff, sq2eff + 1 + int(sq2d)):
            last_cache = cache
            cache = []
            for w in range(-sq2eff, sq2eff + 1):
                x = (int(a[0] + l * dx - w * dy) + self.width) % self.width
                y = (int(a[1] + l * dy + w * dx) + self.height) % self.height
                if (x, y) in cache or (x,y) in last_cache: continue
                cache.append((x, y))

                mag = magnitude
                if map[x][y] < 30:
                    mag *= sea_erosion
                mnt = mag * (max(strict_effect - closeness_to_line(x, y), 0) / strict_effect)**2
                map[x][y] = min(map[x][y] + mnt * (clamp(snoise2(x / self.width / scale, y / self.height / scale, 4, 0.4, 2, 1 / scale, 1 / scale,
                                base=(self.seed + 2) % 256))+1)/2, height)

    def generate_all_vly_ranges(self, map, vly_ranges, depth):
        total = len(vly_ranges)
        n = 0
        for v in vly_ranges:
            self.loading_bar(n/total)
            n += 1
            for i in range(1,len(v)):
                amplitude = int(clamp(random.normalvariate(20, 10), 5, 40))
                self.generate_vly_range(map, v[i-1], v[i], depth, max_effect=amplitude, max_offset=int(0.7*amplitude), magnitude=int(0.5*amplitude))

    def generate_vly_range(self, map, a, b, depth, max_effect=30, max_offset=20, magnitude=15, scale=0.05):

        def get_closest_alt(target_x, target_y, input_x, input_y):
            w = self.width
            h = self.height
            alt_x = input_x - w * (input_x - target_x > w/2) + w * (target_x - input_x > w/2)
            alt_y = input_y - h * (input_y - target_y > h/2) + h * (target_y - input_y > h/2)
            return alt_x, alt_y

        b_alt = get_closest_alt(a[0], a[1], b[0], b[1])

        def closeness_to_line(x1, y1):
            px = x1 + max_offset * snoise2(x1 / self.width / scale, y1 / self.height / scale, 4, 0.4, 2, 1 / scale, 1 / scale,
                            base=self.seed % 256)
            py = y1 + max_offset * snoise2(x1 / self.width / scale, y1 / self.height / scale, 4, 0.4, 2, 1 / scale, 1 / scale,
                              base=(self.seed + 1) % 256)
            px_alt, py_alt = get_closest_alt(a[0],a[1], px, py)
            return point_segment_distance(px_alt, py_alt, a[0], a[1], b_alt[0], b_alt[1])

        dy = b_alt[1] - a[1]
        dx = b_alt[0] - a[0]
        d = math.sqrt(dx*dx + dy*dy)
        sq2d = math.sqrt(2) * d
        sq2eff = int(math.sqrt(2) * max_effect)
        dy /= sq2d
        dx /= sq2d

        strict_effect = max_effect - max_offset
        amplitude = depth / strict_effect

        last_cache = []
        cache = []
        for l in range(-sq2eff, sq2eff + 1 + int(sq2d)):
            last_cache = cache
            cache = []
            for w in range(-sq2eff, sq2eff + 1):
                x = (int(a[0] + l * dx - w * dy) + self.width) % self.width
                y = (int(a[1] + l * dy + w * dx) + self.height) % self.height
                if (x, y) in cache or (x,y) in last_cache: continue
                cache.append((x, y))

                vly = magnitude*(max(strict_effect - closeness_to_line(x, y), 0) / strict_effect)**2
                map[x][y] = max(map[x][y] - vly * (clamp(snoise2(x / self.width / scale, y / self.height / scale, 4, 0.4, 2, 1 / scale, 1 / scale,
                                base=(self.seed + 2) % 256))+1) / 2, depth)



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
                ang = (clamp(snoise2(x/self.width, y/self.height, 5, 0.5, 2, 1, 1, base=(self.seed+2)%256)))
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