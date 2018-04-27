
# Weights for households
# low_residential = 8
# medium_residential = 9
# high_residential = 10
# commercial = 4
# industrial = 1
# education = 0
# open_land = 0

# Weights for firms
# low_residential = 1
# medium_residential = 1.5
# high_residential = 2
# commercial = 10
# industrial = 5
# education = 3
# open_land = 1

# Weights for education
# low_residential = 0
# medium_residential = 0
# high_residential = 0
# commercial = 0
# industrial = 0
# education = 1
# open_land = 0

def set_weights(
        sparse_residential='sparse_residential',
        low_residential='low_residential',
        medium_residential='medium_residential',
        high_residential='high_residential',
        commercial='commercial',
        industrial='industrial',
        education='education',
        agriculture='agriculture',
        urban_open_land='urban_open_land',
        forest='forest',
        water='water',
        open_land='open_land',
        transportation='transportation'):
    return {
    0: open_land,
    # urban land uses
    11: low_residential, # low-density residential
    12: medium_residential, # Medium-density residential
    13: high_residential, # High-denstiy residential
    14: commercial, # Commercial
    15: industrial, # Industrial
    16: education, # Institutional
    17: open_land,
    18: urban_open_land, # road closed area
    191: sparse_residential,
    192: sparse_residential,
    # Agriculture
    21: agriculture,
    22: agriculture,
    23: agriculture,
    24: agriculture,
    241: agriculture,
    242: agriculture,
    25: agriculture,
    # Forest
    41: forest, # deciduous forest
    42: forest, # evergeen forest
    43: forest, # midex forest
    44: forest, # brush
    # water
    50: water, #open_land,
    #wetlands
    60: water, #open_land, # forested or non-forested wetlands
    # Barren land
    70: open_land, # barren land
    71: open_land, # beaches
    72: open_land, # bare exposed rock
    73: open_land, # bare ground
    # transportation
    80: transportation
    }

EDU_WEIGHTS = set_weights(
        sparse_residential=0,
        low_residential=0,
        medium_residential=0,
        high_residential=0,
        commercial=0,
        industrial=0,
        education=1,
        agriculture=0,
        urban_open_land=0,
        forest=0,
        water=0,
        open_land=0,
        transportation=0)

FIRM_WEIGHTS = set_weights(
        sparse_residential=0,
        low_residential=0,
        medium_residential=0,
        high_residential=0,
        commercial=0,
        industrial=0,
        education=1,
        agriculture=0,
        urban_open_land=0,
        forest=0,
        water=0,
        open_land=0,
        transportation=0)

HH_WEIGHTS = set_weights(
        sparse_residential=0,
        low_residential=0,
        medium_residential=0,
        high_residential=0,
        commercial=0,
        industrial=0,
        education=1,
        agriculture=0,
        urban_open_land=0,
        forest=0,
        water=0,
        open_land=0,
        transportation=0)

CLASSIFICATION = set_weights(
        sparse_residential=1,
        low_residential=2,
        medium_residential=3,
        high_residential=4,
        commercial=5,
        industrial=6,
        education=7,
        agriculture=8,
        urban_open_land=9,
        forest=10,
        water=11,
        open_land=12,
        transportation=13)

CLASSIFICATION_STR = set_weights(
        sparse_residential='sparseR',
        low_residential='lowR',
        medium_residential='mediumR',
        high_residential='highR',
        commercial='commer',
        industrial='indust',
        education='edu',
        agriculture='agricul',
        urban_open_land='urbanOL',
        forest='forest',
        water='water',
        open_land='openLand',
        transportation='trans')

# CLASSIFICATION_STR = set_weights()
