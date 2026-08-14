from simulation import Simulation

if __name__ == '__main__':
    sim = Simulation(700, 700, 60, 60)
    sim.set_color_stages([[0, (15, 35, 120)],
                          [22, (18, 46, 184)],
                          [29,(12, 240, 217)],
                          [30,(235, 232, 174)],
                          [40,(62, 161, 55)],
                          [60,(56, 47, 38)],
                          [70, (220, 220, 220)],
                          [80, (255,255,255)],
                          [81, (255, 255, 0)],
                          [99, (255, 0, 0)]])
    sim.set_map_size(400, 400)
    sim.generate()
    sim.run()