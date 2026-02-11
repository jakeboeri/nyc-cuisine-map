#!/usr/bin/env python3
"""
Preprocess NYC Restaurant Inspection GeoJSON data for pointillism map visualization.

This script:
1. Loads the 352MB DOHMH GeoJSON file
2. Filters out records with invalid geometry
3. Deduplicates by camis (unique restaurant ID)
4. Maps each cuisine to its specific ethnicity/country category
5. Parses restaurant names for country clues when category is "Unspecified"
6. Outputs a minimal JSON file for web visualization
"""

import json
import os
import re
import random
import math
from pathlib import Path
from collections import defaultdict
import colorsys

# Country/ethnicity keywords to look for in restaurant names
# Maps keyword patterns to category names
NAME_TO_CATEGORY_PATTERNS = {
    # Middle Eastern / North African
    r'\byemen\w*\b': 'Yemeni',
    r'\bleban\w*\b': 'Lebanese',
    r'\bsyri\w*\b': 'Syrian',
    r'\bjordan\w*\b': 'Jordanian',
    r'\bpalestini\w*\b': 'Palestinian',
    r'\bisrael\w*\b': 'Israeli',
    r'\bkurdish\b': 'Kurdish',
    r'\biraq\w*\b': 'Iraqi',
    r'\bpersian\b': 'Iranian',
    r'\btunis\w*\b': 'Tunisian',
    r'\balger\w*\b': 'Algerian',
    r'\begypt\w*\b': 'Egyptian',
    r'\bmorocc\w*\b': 'Moroccan',
    r'\bturk\w*\b': 'Turkish',
    r'\barmen\w*\b': 'Armenian',
    r'\bgeorgia\w*\b': 'Georgian',
    r'\bazerbaijan\w*\b': 'Azerbaijani',
    r'\bafghan\w*\b': 'Afghan',
    r'\bubek\w*\b': 'Uzbek',
    r'\btajik\w*\b': 'Tajik',
    r'\bkazakh\w*\b': 'Kazakh',

    # South Asian
    r'\bindia\w*\b': 'Indian',
    r'\bpakistan\w*\b': 'Pakistani',
    r'\bbangladesh\w*\b': 'Bangladeshi',
    r'\bnepale*s*\w*\b': 'Nepali',
    r'\bsri\s*lank\w*\b': 'Sri Lankan',
    r'\btibetan\b': 'Tibetan',
    r'\bbhutan\w*\b': 'Bhutanese',

    # Southeast Asian
    r'\bvietnam\w*\b': 'Vietnamese',
    r'\bpho\b': 'Vietnamese',
    r'\bbanh\s*mi\b': 'Vietnamese',
    r'\bcambodi\w*\b': 'Cambodian',
    r'\bkhmer\b': 'Cambodian',
    r'\blaos\b|\blaoti\w*\b': 'Laotian',
    r'\bmyanmar\b|\bburm\w*\b': 'Burmese',
    r'\bmalay\w*\b': 'Malaysian',
    r'\bsingapore\w*\b': 'Singaporean',
    r'\bfilipino\b|\bpinoy\b|\bmanila\b': 'Filipino',
    r'\bindonesia\w*\b': 'Indonesian',
    r'\bthai\b': 'Thai',

    # East Asian
    r'\btaiwan\w*\b': 'Taiwanese',
    r'\bhong\s*kong\b': 'Hong Kong',
    r'\bcantonese\b': 'Cantonese',
    r'\bszechuan\b|\bsichuan\b': 'Sichuan',
    r'\bshanghai\b': 'Shanghainese',
    r'\bbeijing\b|\bpeking\b': 'Beijing',
    r'\bhunan\b': 'Hunanese',
    r'\bmongoli\w*\b': 'Mongolian',

    # Caribbean
    r'\bjamaica\w*\b': 'Jamaican',
    r'\bhaiti\w*\b': 'Haitian',
    r'\btrinidad\w*\b': 'Trinidadian',
    r'\bbarbad\w*\b': 'Barbadian',
    r'\bbahama\w*\b': 'Bahamian',
    r'\bcuba\w*\b': 'Cuban',
    r'\bpuerto\s*ric\w*\b': 'Puerto Rican',
    r'\bdomini\w*\b': 'Dominican',
    r'\bguyan\w*\b': 'Guyanese',

    # Latin American
    r'\bcolomb\w*\b': 'Colombian',
    r'\bvenezuel\w*\b': 'Venezuelan',
    r'\becuador\w*\b': 'Ecuadorian',
    r'\bbolivia\w*\b': 'Bolivian',
    r'\bparaguay\w*\b': 'Paraguayan',
    r'\buruguay\w*\b': 'Uruguayan',
    r'\bargentin\w*\b': 'Argentinian',
    r'\bchile\w*\b': 'Chilean',
    r'\bperu\w*\b': 'Peruvian',
    r'\bbrazil\w*\b': 'Brazilian',
    r'\bpanama\w*\b': 'Panamanian',
    r'\bcosta\s*ric\w*\b': 'Costa Rican',
    r'\bnicaragua\w*\b': 'Nicaraguan',
    r'\bhondur\w*\b': 'Honduran',
    r'\bguatemal\w*\b': 'Guatemalan',
    r'\bel\s*salvador\w*\b|\bsalvador\w*\b': 'Salvadoran',
    r'\boaxaca\w*\b': 'Oaxacan',
    r'\byucatan\b': 'Yucatecan',

    # African
    r'\bethiopi\w*\b': 'Ethiopian',
    r'\beritrea\w*\b': 'Eritrean',
    r'\bsomali\w*\b': 'Somali',
    r'\bsenegal\w*\b': 'Senegalese',
    r'\bnigeri\w*\b': 'Nigerian',
    r'\bghan\w*\b': 'Ghanaian',
    r'\bivorian\b|\bivory\s*coast\b': 'Ivorian',
    r'\bsouth\s*africa\w*\b': 'South African',
    r'\bkeny\w*\b': 'Kenyan',
    r'\bugand\w*\b': 'Ugandan',
    r'\btanzani\w*\b': 'Tanzanian',

    # Eastern European
    r'\bmoldov\w*\b': 'Moldovan',
    r'\bukrain\w*\b': 'Ukrainian',
    r'\bbelarus\w*\b': 'Belarusian',
    r'\blithuani\w*\b': 'Lithuanian',
    r'\blatvi\w*\b': 'Latvian',
    r'\bestoni\w*\b': 'Estonian',
    r'\bpolish\b|\bpoland\b|\bpolska\b': 'Polish',
    r'\brussia\w*\b': 'Russian',
    r'\bczech\w*\b': 'Czech',
    r'\bslovak\w*\b': 'Slovak',
    r'\bhungar\w*\b': 'Hungarian',
    r'\bromani\w*\b': 'Romanian',
    r'\bbulgar\w*\b': 'Bulgarian',
    r'\bserbia\w*\b': 'Serbian',
    r'\bcroat\w*\b': 'Croatian',
    r'\bsloven\w*\b': 'Slovenian',
    r'\bbosnia\w*\b': 'Bosnian',
    r'\bmacedon\w*\b': 'Macedonian',
    r'\balban\w*\b': 'Albanian',
    r'\bkosovo\b': 'Kosovar',

    # Western European
    r'\bbelg\w*\b': 'Belgian',
    r'\bdutch\b|\bnetherland\w*\b|\bholland\b': 'Dutch',
    r'\bswiss\b|\bswitzerland\b': 'Swiss',
    r'\baustria\w*\b': 'Austrian',

    # Mediterranean
    r'\bcypr\w*\b': 'Cypriot',
    r'\bmalta\w*\b': 'Maltese',

    # Other
    r'\baustrali\w*\b': 'Australian',
    r'\bnew\s*zealand\b|\bkiwi\b': 'New Zealander',
}

# Cuisine to Category mapping - as specific as possible
CUISINE_TO_CATEGORY = {
    # Specific countries/ethnicities - use as-is
    "Afghan": "Afghan",
    "African": "African (Unspecified)",
    "Armenian": "Armenian",
    "Bangladeshi": "Bangladeshi",
    "Basque": "Basque",
    "Brazilian": "Brazilian",
    "Chilean": "Chilean",
    "Chinese": "Chinese",
    "Chinese/Cuban": "Chinese-Cuban",
    "Chinese/Japanese": "Chinese-Japanese",
    "Czech": "Czech",
    "Egyptian": "Egyptian",
    "English": "English",
    "Ethiopian": "Ethiopian",
    "Filipino": "Filipino",
    "French": "French",
    "New French": "French",
    "German": "German",
    "Greek": "Greek",
    "Hawaiian": "Hawaiian",
    "Indian": "Indian",
    "Indonesian": "Indonesian",
    "Iranian": "Iranian",
    "Irish": "Irish",
    "Italian": "Italian",
    "Japanese": "Japanese",
    "Korean": "Korean",
    "Lebanese": "Lebanese",
    "Mexican": "Mexican",
    "Moroccan": "Moroccan",
    "Pakistani": "Pakistani",
    "Peruvian": "Peruvian",
    "Polish": "Polish",
    "Polynesian": "Polynesian",
    "Portuguese": "Portuguese",
    "Russian": "Russian",
    "Scandinavian": "Scandinavian",
    "Spanish": "Spanish",
    "Thai": "Thai",
    "Turkish": "Turkish",

    # General/regional categories - add (Unspecified)
    "Latin American": "Latin American (Unspecified)",
    "Caribbean": "Caribbean (Unspecified)",
    "Middle Eastern": "Middle Eastern (Unspecified)",
    "Mediterranean": "Mediterranean (Unspecified)",
    "Eastern European": "Eastern European (Unspecified)",
    "Southeast Asian": "Southeast Asian (Unspecified)",
    "Asian/Asian Fusion": "Asian Fusion",

    # American varieties - merge Californian into American
    "American": "American",
    "New American": "American",
    "Californian": "American",
    "Southwestern": "Southwestern",
    "Tex-Mex": "Tex-Mex",
    "Soul Food": "Soul Food",
    "Cajun": "Cajun",
    "Creole": "Creole",
    "Creole/Cajun": "Cajun-Creole",

    # Special categories
    "Pizza": "Pizza Shop",
    "Coffee/Tea": "Cafe",

    # European misc - Continental needs hotel check
    "Continental": "Continental European",
    "Haute Cuisine": "Haute Cuisine",
    "Tapas": "Tapas",

    # Jewish
    "Jewish/Kosher": "Jewish/Kosher",
}

# Cuisines to exclude (generic food types, not ethnic cuisines)
EXCLUDED_CUISINES = {
    "Bakery Products/Desserts",
    "Bagels/Pretzels",
    "Donuts",
    "Frozen Desserts",
    "Pancakes/Waffles",
    "Sandwiches",
    "Sandwiches/Salads/Mixed Buffet",
    "Salads",
    "Soups",
    "Soups/Salads/Sandwiches",
    "Seafood",
    "Hamburgers",
    "Hotdogs",
    "Hotdogs/Pretzels",
    "Chicken",
    "Steakhouse",
    "Barbecue",
    "Vegetarian",
    "Vegan",
    "Juice/Smoothies/Fruit Salads",
    "Fruits/Vegetables",
    "Bottled Beverages",
    "Nuts/Confectionary",
    "Not Listed/Not Applicable",
    "Other",
    "Fusion",  # Too generic
}

# Hotel patterns
HOTEL_PATTERNS = [
    r'\bhotel\b',
    r'\binn\b',
    r'\bresort\b',
    r'\blodge\b',
    r'\bsuites?\b',
    r'\bmarriott\b',
    r'\bhilton\b',
    r'\bhyatt\b',
    r'\bsheraton\b',
    r'\bwyndham\b',
    r'\bradisson\b',
    r'\bfairfield\b',
    r'\bhampton\b',
    r'\bcourtyard\b',
    r'\britz\b',
    r'\bfour\s*seasons\b',
    r'\bwaldorf\b',
    r'\bplaza\b',
]

# Bar patterns
BAR_PATTERNS = [
    r'\bbar\b',
    r'\bpub\b',
    r'\btavern\b',
    r'\bbrewery\b',
    r'\bbrewpub\b',
    r'\bale\s*house\b',
    r'\bbeer\s*hall\b',
    r'\bwine\s*bar\b',
    r'\bcocktail\b',
    r'\blounge\b',
    r'\bsaloon\b',
    r'\btaproom\b',
    r'\bdrinking\b',
]


def generate_colors(n):
    """Generate n visually distinct colors using HSL color space."""
    colors = {}
    golden_ratio = 0.618033988749895
    h = 0.0

    for i in range(n):
        s = 0.65 + (i % 3) * 0.1
        l = 0.45 + (i % 2) * 0.1
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        colors[i] = [int(r * 255), int(g * 255), int(b * 255)]
        h = (h + golden_ratio) % 1.0

    return colors


def get_building_number(address):
    """Extract the building number from an address string."""
    if not address:
        return None
    # Match leading digits (building number)
    match = re.match(r'^(\d+)', address.strip())
    if match:
        return int(match.group(1))
    return None


def get_street_name(address):
    """Extract the street name from an address string (everything after the building number)."""
    if not address:
        return None
    # Remove building number and get the rest
    match = re.match(r'^\d+\s+(.+)$', address.strip())
    if match:
        return match.group(1).strip()
    return address.strip()


def get_street_orientation(street_name):
    """
    Determine if a street runs East-West or North-South based on its name.

    Returns:
        'EW' for East-West streets (apply N/S offset)
        'NS' for North-South streets (apply E/W offset)
        'DIAG' for diagonal streets (skip offset)
        None if orientation cannot be determined
    """
    if not street_name:
        return None

    street_lower = street_name.lower()

    # Diagonal streets - skip offset entirely
    diagonal_patterns = [
        r'\bbroadway\b',
        r'\bbowery\b',
        r'\bpark\s+ave\s+south\b',
    ]
    for pattern in diagonal_patterns:
        if re.search(pattern, street_lower):
            return 'DIAG'

    # North-South streets (Avenues)
    # These get E/W offset based on odd/even
    ns_patterns = [
        r'\bavenue\b', r'\bave\b', r'\bav\b',
        r'\bboulevard\b', r'\bblvd\b',
        r'\b\d+(st|nd|rd|th)\s+ave',  # "5th Ave" etc
        r'^[a-z]\b',  # Single letter avenues (A, B, C, D in Manhattan)
    ]
    for pattern in ns_patterns:
        if re.search(pattern, street_lower):
            return 'NS'

    # East-West streets (Streets, Roads, etc.)
    # These get N/S offset based on odd/even
    ew_patterns = [
        r'\bstreet\b', r'\bst\b',
        r'\bplace\b', r'\bpl\b',
        r'\broad\b', r'\brd\b',
        r'\bway\b',
        r'\blane\b', r'\bln\b',
        r'\bdrive\b', r'\bdr\b',
        r'\bcourt\b', r'\bct\b',
        r'\bterrace\b', r'\bter\b',
        r'^\d+(st|nd|rd|th)\s+st',  # "42nd St" etc
        r'\b(east|west|e|w)\s+\d+',  # "East 42nd", "W 23rd"
    ]
    for pattern in ew_patterns:
        if re.search(pattern, street_lower):
            return 'EW'

    # Check for numbered streets without explicit suffix (common in address data)
    # If it's just a number like "42" or "EAST 42", assume it's a street (E-W)
    if re.match(r'^(east|west|e|w)?\s*\d+$', street_lower.strip()):
        return 'EW'

    return None


def apply_street_side_offset(restaurants):
    """
    Offset restaurants to the correct side of the street based on:
    1. Street orientation (E-W vs N-S)
    2. Odd/even building numbers

    NYC conventions:
    - E-W streets: odd numbers on NORTH side, even on SOUTH
    - N-S avenues: odd numbers on WEST side, even on EAST

    We apply a perpendicular offset of ~10 meters to move points
    from street centerline to building side.
    """
    # Offset amount: ~0.00010 degrees ≈ 10 meters at NYC latitude
    offset_amount = 0.00010

    offset_count = 0
    skipped_diagonal = 0
    skipped_unknown = 0

    for restaurant in restaurants:
        address = restaurant.get('address', '')
        building_num = get_building_number(address)
        street_name = get_street_name(address)
        orientation = get_street_orientation(street_name)

        if building_num is None:
            continue

        if orientation == 'DIAG':
            skipped_diagonal += 1
            continue

        if orientation is None:
            skipped_unknown += 1
            continue

        is_odd = building_num % 2 == 1

        if orientation == 'EW':
            # E-W street: offset in latitude (N/S direction)
            # Odd = North (+lat), Even = South (-lat)
            if is_odd:
                restaurant['position'][1] += offset_amount
            else:
                restaurant['position'][1] -= offset_amount
        else:  # NS
            # N-S avenue: offset in longitude (E/W direction)
            # Odd = West (-lon), Even = East (+lon)
            if is_odd:
                restaurant['position'][0] -= offset_amount
            else:
                restaurant['position'][0] += offset_amount

        offset_count += 1

    return offset_count, skipped_diagonal, skipped_unknown


def apply_jitter(restaurants):
    """
    Apply small spatial offsets to restaurants sharing the same coordinates.
    This prevents overlapping points and creates a cleaner pointillism effect.
    Called AFTER street-side offset.
    """
    # Group restaurants by coordinates (rounded to 6 decimal places)
    coord_groups = defaultdict(list)
    for i, r in enumerate(restaurants):
        # Round coordinates to group nearby points
        key = (round(r['position'][0], 6), round(r['position'][1], 6))
        coord_groups[key].append(i)

    # Apply jitter to groups with multiple restaurants
    # Jitter amount: ~0.00008 degrees ≈ 8 meters at NYC latitude
    jitter_amount = 0.00008
    jittered_count = 0

    for coord, indices in coord_groups.items():
        if len(indices) > 1:
            jittered_count += len(indices)
            # Arrange points in a circle around the original location
            n = len(indices)
            for j, idx in enumerate(indices):
                if n <= 6:
                    # For small groups, use evenly spaced circle
                    angle = (2 * math.pi * j) / n
                    offset_x = jitter_amount * math.cos(angle)
                    offset_y = jitter_amount * math.sin(angle)
                else:
                    # For larger groups, use spiral pattern
                    radius = jitter_amount * (1 + j / n)
                    angle = (2 * math.pi * j) / 6  # Golden spiral-ish
                    offset_x = radius * math.cos(angle)
                    offset_y = radius * math.sin(angle)

                restaurants[idx]['position'][0] += offset_x
                restaurants[idx]['position'][1] += offset_y

    return jittered_count


# Predefined colors for major categories
CATEGORY_COLORS = {
    # East Asian - Red/Pink family
    "Chinese": [229, 57, 53],
    "Chinese-Cuban": [211, 47, 47],
    "Chinese-Japanese": [244, 67, 54],
    "Japanese": [216, 27, 96],
    "Korean": [142, 36, 170],
    "Thai": [94, 53, 177],
    "Taiwanese": [255, 64, 129],
    "Hong Kong": [236, 64, 122],
    "Cantonese": [240, 98, 146],
    "Sichuan": [213, 0, 0],
    "Shanghainese": [197, 17, 98],
    "Beijing": [183, 28, 28],
    "Hunanese": [194, 24, 91],
    "Mongolian": [136, 14, 79],

    # Southeast Asian - Cyan family
    "Filipino": [0, 188, 212],
    "Indonesian": [0, 172, 193],
    "Vietnamese": [38, 198, 218],
    "Southeast Asian (Unspecified)": [77, 208, 225],
    "Polynesian": [0, 151, 167],
    "Hawaiian": [128, 222, 234],
    "Cambodian": [0, 131, 143],
    "Laotian": [0, 96, 100],
    "Burmese": [84, 110, 122],
    "Malaysian": [38, 166, 154],
    "Singaporean": [0, 121, 107],

    # South Asian - Orange family
    "Indian": [255, 111, 0],
    "Pakistani": [255, 143, 0],
    "Bangladeshi": [255, 167, 38],
    "Afghan": [239, 108, 0],
    "Nepali": [255, 171, 64],
    "Sri Lankan": [255, 183, 77],
    "Tibetan": [251, 140, 0],
    "Bhutanese": [245, 124, 0],

    # Middle Eastern - Gold/Yellow family
    "Middle Eastern (Unspecified)": [255, 179, 0],
    "Lebanese": [255, 193, 7],
    "Iranian": [255, 213, 79],
    "Egyptian": [253, 216, 53],
    "Armenian": [255, 238, 88],
    "Turkish": [251, 192, 45],
    "Moroccan": [245, 127, 23],
    "Yemeni": [255, 160, 0],
    "Syrian": [255, 202, 40],
    "Jordanian": [255, 224, 130],
    "Palestinian": [255, 241, 118],
    "Israeli": [255, 245, 157],
    "Kurdish": [255, 214, 0],
    "Iraqi": [255, 196, 0],
    "Tunisian": [245, 155, 30],
    "Algerian": [224, 130, 20],
    "Georgian": [255, 171, 0],
    "Azerbaijani": [255, 183, 0],
    "Uzbek": [255, 195, 0],
    "Tajik": [255, 207, 0],
    "Kazakh": [255, 219, 0],

    # Mediterranean/Southern European - Green family
    "Greek": [67, 160, 71],
    "Mediterranean (Unspecified)": [102, 187, 106],
    "Italian": [0, 137, 123],
    "Spanish": [38, 166, 154],
    "Portuguese": [0, 150, 136],
    "Basque": [77, 182, 172],
    "Tapas": [129, 199, 132],
    "Cypriot": [165, 214, 167],
    "Maltese": [200, 230, 201],

    # Western European - Blue family
    "French": [3, 155, 229],
    "Haute Cuisine": [2, 136, 209],
    "English": [30, 136, 229],
    "Irish": [25, 118, 210],
    "German": [63, 81, 181],
    "Scandinavian": [92, 107, 192],
    "Continental European": [121, 134, 203],
    "Belgian": [48, 63, 159],
    "Dutch": [40, 53, 147],
    "Swiss": [26, 35, 126],
    "Austrian": [69, 90, 100],

    # Eastern European - Violet family
    "Eastern European (Unspecified)": [103, 58, 183],
    "Russian": [126, 87, 194],
    "Polish": [149, 117, 205],
    "Czech": [171, 71, 188],
    "Ukrainian": [186, 104, 200],
    "Moldovan": [206, 147, 216],
    "Belarusian": [224, 177, 233],
    "Lithuanian": [179, 157, 219],
    "Latvian": [149, 117, 205],
    "Estonian": [179, 136, 255],
    "Slovak": [124, 77, 255],
    "Hungarian": [101, 31, 255],
    "Romanian": [98, 0, 234],
    "Bulgarian": [117, 117, 117],
    "Serbian": [158, 158, 158],
    "Croatian": [189, 189, 189],
    "Slovenian": [117, 117, 117],
    "Bosnian": [97, 97, 97],
    "Macedonian": [66, 66, 66],
    "Albanian": [33, 33, 33],
    "Kosovar": [48, 48, 48],

    # Jewish
    "Jewish/Kosher": [156, 39, 176],

    # Latin American - Red/Magenta family
    "Mexican": [198, 40, 40],
    "Tex-Mex": [229, 115, 115],
    "Latin American (Unspecified)": [173, 20, 87],
    "Brazilian": [194, 24, 91],
    "Peruvian": [136, 14, 79],
    "Chilean": [233, 30, 99],
    "Southwestern": [240, 98, 146],
    "Colombian": [255, 23, 68],
    "Venezuelan": [213, 0, 0],
    "Ecuadorian": [197, 17, 98],
    "Bolivian": [136, 14, 79],
    "Paraguayan": [173, 20, 87],
    "Uruguayan": [216, 27, 96],
    "Argentinian": [244, 67, 54],
    "Panamanian": [239, 83, 80],
    "Costa Rican": [229, 115, 115],
    "Nicaraguan": [239, 154, 154],
    "Honduran": [255, 205, 210],
    "Guatemalan": [255, 138, 128],
    "Salvadoran": [255, 82, 82],
    "Oaxacan": [176, 0, 32],
    "Yucatecan": [139, 0, 0],

    # Caribbean - Orange family
    "Caribbean (Unspecified)": [239, 108, 0],
    "Jamaican": [255, 109, 0],
    "Haitian": [230, 81, 0],
    "Trinidadian": [255, 145, 0],
    "Barbadian": [255, 172, 64],
    "Bahamian": [255, 183, 77],
    "Cuban": [255, 128, 0],
    "Puerto Rican": [255, 152, 0],
    "Dominican": [245, 124, 0],
    "Guyanese": [230, 126, 34],

    # African - Brown family
    "African (Unspecified)": [78, 52, 46],
    "Ethiopian": [93, 64, 55],
    "Eritrean": [109, 76, 65],
    "Somali": [121, 85, 72],
    "Senegalese": [141, 110, 99],
    "Nigerian": [161, 136, 127],
    "Ghanaian": [188, 170, 164],
    "Ivorian": [215, 204, 200],
    "South African": [62, 39, 35],
    "Kenyan": [74, 50, 43],
    "Ugandan": [87, 59, 51],
    "Tanzanian": [100, 68, 59],

    # American - Gray/Blue-Gray family
    "American": [55, 71, 79],
    "Soul Food": [109, 76, 65],
    "Cajun": [141, 110, 99],
    "Creole": [161, 136, 127],
    "Cajun-Creole": [121, 85, 72],

    # Special categories
    "Pizza Shop": [255, 87, 34],
    "Cafe": [121, 85, 72],
    "Bar": [33, 33, 33],
    "Hotel Food": [176, 190, 197],

    # Asian Fusion
    "Asian Fusion": [120, 144, 156],
}


def is_hotel(name):
    """Check if the restaurant name indicates it's a hotel."""
    if not name:
        return False
    name_lower = name.lower()
    for pattern in HOTEL_PATTERNS:
        if re.search(pattern, name_lower):
            return True
    return False


def is_bar(name):
    """Check if the restaurant name indicates it's a bar."""
    if not name:
        return False
    name_lower = name.lower()
    for pattern in BAR_PATTERNS:
        if re.search(pattern, name_lower):
            return True
    return False


def extract_category_from_name(name, default_category):
    """
    Try to extract a more specific category from the restaurant name.
    Only used when the cuisine maps to an "(Unspecified)" category.
    """
    if not name or "(Unspecified)" not in default_category:
        return default_category

    name_lower = name.lower()

    for pattern, category in NAME_TO_CATEGORY_PATTERNS.items():
        if re.search(pattern, name_lower):
            return category

    return default_category


def preprocess_data(input_path: str, output_path: str):
    """
    Process the DOHMH GeoJSON file and output optimized JSON for visualization.
    """
    print(f"Loading GeoJSON from: {input_path}")
    print("This may take a moment for the 352MB file...")

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Loaded {len(data['features'])} features")

    seen_camis = set()
    restaurants = []
    excluded_count = 0
    invalid_geo_count = 0
    duplicate_count = 0
    unmapped_cuisines = set()
    category_counts = {}
    bar_count = 0
    hotel_count = 0
    name_extracted_count = 0

    for feature in data['features']:
        props = feature.get('properties', {})
        geom = feature.get('geometry')

        # Skip invalid geometry
        if not geom or geom.get('type') != 'Point':
            invalid_geo_count += 1
            continue

        coords = geom.get('coordinates')
        if not coords or len(coords) < 2:
            invalid_geo_count += 1
            continue

        lon, lat = coords[0], coords[1]
        if (lon == 0 and lat == 0) or lon is None or lat is None:
            invalid_geo_count += 1
            continue

        # NYC bounding box check
        if not (-74.3 < lon < -73.7 and 40.4 < lat < 41.0):
            invalid_geo_count += 1
            continue

        # Deduplicate by camis
        camis = props.get('camis')
        if camis in seen_camis:
            duplicate_count += 1
            continue
        seen_camis.add(camis)

        cuisine = props.get('cuisine_description')
        name = props.get('dba', 'Unknown')

        # Check if it's a bar first
        if is_bar(name):
            category = "Bar"
            bar_count += 1
        # Check if excluded cuisine
        elif not cuisine or cuisine in EXCLUDED_CUISINES:
            excluded_count += 1
            continue
        else:
            # Map cuisine to category
            category = CUISINE_TO_CATEGORY.get(cuisine)
            if not category:
                unmapped_cuisines.add(cuisine)
                excluded_count += 1
                continue

            # For Continental, check if it's a hotel
            if category == "Continental European" and is_hotel(name):
                category = "Hotel Food"
                hotel_count += 1

            # For Unspecified categories, try to extract from name
            if "(Unspecified)" in category:
                new_category = extract_category_from_name(name, category)
                if new_category != category:
                    name_extracted_count += 1
                    category = new_category

        # Track counts
        category_counts[category] = category_counts.get(category, 0) + 1

        restaurant = {
            'position': [lon, lat],
            'name': name,
            'cuisine': cuisine if cuisine else 'Bar',
            'category': category,
            'boro': props.get('boro', ''),
            'address': f"{props.get('building', '')} {props.get('street', '')}".strip(),
        }
        restaurants.append(restaurant)

    # Apply jitter to spread out overlapping restaurants
    jittered_count = apply_jitter(restaurants)

    print(f"\n--- Processing Summary ---")
    print(f"Total features processed: {len(data['features'])}")
    print(f"Invalid geometry: {invalid_geo_count}")
    print(f"Duplicates removed: {duplicate_count}")
    print(f"Excluded (non-ethnic or unmapped): {excluded_count}")
    print(f"Unique restaurants included: {len(restaurants)}")
    print(f"\n--- Special Processing ---")
    print(f"Bars detected: {bar_count}")
    print(f"Hotels moved to Hotel Food: {hotel_count}")
    print(f"Categories extracted from names: {name_extracted_count}")
    print(f"\n--- Spatial Adjustments ---")
    print(f"Points jittered (shared locations): {jittered_count}")

    if unmapped_cuisines:
        print(f"\n--- Unmapped Cuisines (skipped) ---")
        for c in sorted(unmapped_cuisines):
            print(f"  {c}")

    print(f"\n--- Category Distribution ({len(category_counts)} categories) ---")
    for category, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {category}: {count}")

    # Build color mapping
    all_categories = list(category_counts.keys())
    colors = {}
    missing_colors = []

    for cat in all_categories:
        if cat in CATEGORY_COLORS:
            colors[cat] = CATEGORY_COLORS[cat]
        else:
            missing_colors.append(cat)

    if missing_colors:
        print(f"\n--- Generating colors for {len(missing_colors)} new categories ---")
        generated = generate_colors(len(missing_colors))
        for i, cat in enumerate(missing_colors):
            colors[cat] = generated[i]
            print(f"  {cat}: {generated[i]}")

    output_data = {
        'restaurants': restaurants,
        'colors': colors,
        'categories': sorted(all_categories),
        'counts': category_counts,
    }

    print(f"\nWriting output to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f)

    file_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Output file size: {file_size:.2f} MB")

    return len(restaurants)


if __name__ == '__main__':
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent

    data_files = list(project_dir.glob('DOHMH*.geojson'))
    if not data_files:
        print("ERROR: No DOHMH GeoJSON file found in project directory")
        print(f"Looking in: {project_dir}")
        exit(1)

    input_file = data_files[0]
    output_file = project_dir / 'data' / 'restaurants.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)

    preprocess_data(str(input_file), str(output_file))
    print("\nDone! Refresh the browser to see updated data.")
