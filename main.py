import math
import random

from game import ImperialGame

if __name__ == '__main__':
    sim = ImperialGame(700, 700, 60, 60)

    sim.use_color_scheme_biomes()
    sim.set_map_size(500, 500)
    sim.generate_testing()
    sim.run()