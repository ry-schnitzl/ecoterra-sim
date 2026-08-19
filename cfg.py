SKY_BLUE = (189, 239, 255)
WHITE = (255, 255, 255)
LIGHT_GRAY = (204, 208, 219)

basal = 0
shallow = 20
tides = 28
beach = 32
vegetation = 36
hills = 40
mountains = 56
rockies = 72
snowy = 96
biome_slice = 64

biome_name = ["Generic", "River",
              "Desert", "Scrubland", "Montane",
              "Mediterranean", "Steppe", "Tundra",
              "Savannah", "Thornforest", "Tiaga",
              "Tropics", "Rainforest", "Deciduous",
              "Ocean"]

def get_biome(tile):
    return (tile - beach) // biome_slice

def get_height(tile):
    if tile < beach + biome_slice: return tile
    else: return (tile - beach) % biome_slice + beach

def is_different_biome(tile_a, tile_b):
    a = get_biome(tile_a)
    b = get_biome(tile_b)
    if a == -1 or a == 1 or b == -1 or b == 1: return False
    return get_biome(tile_a) != get_biome(tile_b)

biome_color_stages = [
                    [0, (15, 35, 120)],             # Basal Ocean
                    [20, (18, 46, 184)],            # Shallow Ocean
                    [31,(12, 240, 217)],
                    [32,(235, 232, 174)],           # Beach  - - - Generic
                    [36,(62, 161, 55)],             # Vegetation
                    [56,(56, 47, 38)],              # Mountains
                    [72, (220, 220, 220)],          # Rockies
                    [95, (255,255,255)],            # Snowy
                    [96, (67, 244, 202)],          # River Variants (Starts at beach and works upward every 50)
                    [100, (92, 159, 167)],
                    [120, (55, 70, 86)],
                    [136, (119, 119, 180)],
                    [159, (186, 221, 219)],
                    [160, (235, 204, 164)],  # Beach --- Desert        # Dry Hot
                    [164, (235, 204, 109)],
                    [184, (196, 168, 82)],
                    [200, (150, 87, 53)],
                    [223, (237, 206, 201)],
                    [224, (237, 234, 158)],  # Beach --- Scrubland
                    [228, (154, 168, 47)],
                    [248, (148, 110, 52)],
                    [264, (69, 48, 28)],
                    [287, (130, 127, 109)],
                    [288, (235, 235, 209)],  # Beach --- Montane                    #             V
                    [292, (102, 148, 13)],
                    [312, (79, 150, 50)],
                    [328, (209, 178, 155)],
                    [351, (255, 255, 255)],
                    [352, (235, 200, 163)],  # Beach --- Mediterranean
                    [356, (71, 201, 6)],
                    [376, (128, 171, 65)],
                    [392, (201, 219, 176)],
                    [415, (255, 255, 255)],
                    [416, (235, 177, 114)],  # Beach --- Steppe
                    [420, (137, 196, 32)],
                    [440, (196, 186, 29)],
                    [452, (178, 199, 147)],
                    [456, (181, 100, 55)],
                    [479, (255, 255, 255)],
                    [480, (235, 202, 101)],  # Beach --- Tundra             # Dry Cold      # Livability  |
                    [484, (194, 219, 175)],
                    [504, (184, 167, 130)],
                    [516, (107, 51, 9)],
                    [520, (65, 82, 107)],
                    [528, (194, 218, 230)],
                    [543, (255, 255, 255)],
                    [544, (186, 102, 88)],  # Beach ---  Savannah          # Wet Hot
                    [548, (217, 157, 37)],
                    [556, (148, 186, 31)],
                    [578, (250, 149, 75)],
                    [594, (250, 215, 94)],
                    [607, (255, 255, 255)],
                    [608, (191, 167, 136)],  # Beach --- Thornforest       # Wet Cold
                    [612, (131, 224, 118)],
                    [632, (103, 140, 31)],
                    [648, (133, 100, 51)],
                    [671, (199, 193, 176)],
                    [672, (169, 184, 102)],    # Beach --- Tiaga                              #             |
                    [676, (67, 194, 41)],
                    [692, (16, 79, 23)],
                    [696, (12, 55, 61)],
                    [712, (195, 229, 237)],
                    [735, (255, 255, 255)],
                    [736, (133, 71, 17)],  # Beach --- Tropics
                    [740, (4, 179, 41)],
                    [760, (9, 125, 15)],
                    [776, (8, 84, 9)],
                    [799, (128, 153, 119)],
                    [800, (156, 145, 62)],  # Beach --- Rainforest
                    [804, (7, 168, 58)],
                    [824, (29, 120, 37)],
                    [840, (105, 121, 101)],
                    [863, (73, 71, 79)],
                    [864, (186, 130, 90)],  # Beach --- Deciduous
                    [868, (94, 196, 32)],
                    [888, (16, 157, 34)],
                    [904, (78, 107, 81)],
                    [927, (255, 255, 255)],
                    ]