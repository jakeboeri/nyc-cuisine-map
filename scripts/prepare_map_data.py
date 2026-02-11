#!/usr/bin/env python3
"""
Prepare enriched restaurant data for the map visualization.

Uses the restaurants_enriched.json and creates a properly structured
output with geographic region-based colors and hierarchy for the
collapsible legend.
"""

import json
from pathlib import Path
from category_mapping import get_general_category, get_top_level_category, get_category_chain, SPECIFIC_TO_GENERAL

# Neon color scheme — bright, saturated colors optimized for dark backgrounds
# Each general category has a distinct neon hue with subcategory variations

# Color families by geographic region (RGB values)
GEOGRAPHIC_COLORS = {
    # === ASIAN (top-level) - Hot Pink / Magenta neon ===
    "Asian": {
        "_base": [255, 50, 130],
        "Asian": [255, 50, 130],
        "Asian Fusion": [255, 100, 160],
        "Pan-Asian": [255, 70, 145],
        "Asian (Unspecified)": [255, 50, 130],
        "Chinese-Japanese": [255, 60, 135],
        "Chinese-Cuban": [245, 55, 125],
    },

    # Chinese subfamily - Neon Red / Crimson
    "Chinese": {
        "_base": [255, 55, 70],
        "Chinese": [255, 55, 70],
        "Cantonese": [255, 85, 95],
        "Sichuan": [240, 40, 55],
        "Hunan": [225, 35, 50],
        "Shanghainese": [255, 110, 120],
        "Beijing": [210, 30, 45],
        "Hong Kong": [255, 130, 140],
        "Taiwanese": [255, 100, 130],
        "Chinese Bakery": [255, 145, 155],
    },

    # Japanese subfamily - Neon Deep Pink
    "Japanese": {
        "_base": [255, 50, 150],
        "Japanese": [255, 50, 150],
        "Sushi": [255, 80, 170],
        "Ramen": [235, 30, 130],
    },

    # Korean subfamily - Neon Orchid / Violet-Pink
    "Korean": {
        "_base": [200, 60, 255],
        "Korean": [200, 60, 255],
        "Korean BBQ": [215, 90, 255],
    },

    # Southeast Asian subfamily - Neon Orange
    "Southeast Asian": {
        "_base": [255, 160, 0],
        "Southeast Asian": [255, 160, 0],
        "Southeast Asian (Unspecified)": [255, 160, 0],
        "Vietnamese": [255, 175, 30],
        "Thai": [255, 190, 60],
        "Filipino": [255, 145, 0],
        "Indonesian": [250, 130, 0],
        "Malaysian": [245, 115, 0],
        "Singaporean": [240, 100, 0],
        "Burmese": [255, 120, 0],
        "Cambodian": [255, 150, 0],
        "Laotian": [255, 135, 0],
        "Tibetan": [240, 135, 30],
    },

    # South Asian subfamily - Neon Gold / Yellow
    "South Asian": {
        "_base": [255, 210, 0],
        "South Asian": [255, 210, 0],
        "Pakistani": [255, 195, 0],
        "Bangladeshi": [255, 225, 50],
        "Nepalese": [255, 230, 30],
        "Sri Lankan": [255, 240, 50],
        "Afghan": [255, 205, 30],
    },

    # Indian subfamily - Neon Amber / Warm Orange
    "Indian": {
        "_base": [255, 150, 0],
        "Indian": [255, 150, 0],
        "South Indian": [255, 170, 30],
        "North Indian": [245, 120, 0],
        "Punjabi": [240, 100, 0],
        "Gujarati": [250, 135, 0],
    },

    # === WESTERN EUROPEAN (top-level) - Neon Blue / Royal ===
    "Western European": {
        "_base": [80, 100, 255],
        "Western European": [80, 100, 255],
        "Continental European": [110, 125, 255],
        "Mediterranean": [0, 210, 255],
        "Mediterranean (Unspecified)": [0, 210, 255],
    },

    # English subfamily - Neon Cobalt
    "English": {
        "_base": [70, 90, 255],
        "English": [70, 90, 255],
        "British": [70, 90, 255],
        "Fish & Chips": [95, 110, 255],
        "British Pub": [60, 80, 240],
    },

    # Irish/Scottish
    "Irish": {
        "_base": [55, 75, 235],
        "Irish": [55, 75, 235],
        "Irish Pub": [50, 70, 225],
    },
    "Scottish": {
        "_base": [45, 60, 220],
        "Scottish": [45, 60, 220],
    },

    # French subfamily - Neon Sky Blue
    "French": {
        "_base": [30, 180, 255],
        "French": [30, 180, 255],
        "Bistro": [20, 160, 245],
        "Brasserie": [10, 145, 235],
        "Patisserie": [80, 205, 255],
    },

    # Spanish subfamily - Neon Teal
    "Spanish": {
        "_base": [0, 220, 210],
        "Spanish": [0, 220, 210],
        "Basque": [0, 190, 180],
        "Catalan": [30, 230, 220],
        "Spanish Tapas": [60, 240, 230],
        "Tapas": [60, 240, 230],
    },

    # Italian subfamily - Neon Cyan
    "Italian": {
        "_base": [0, 230, 255],
        "Italian": [0, 230, 255],
        "Sicilian": [0, 200, 225],
        "Tuscan": [60, 240, 255],
    },

    # Pizza Shop subfamily - Neon Deep Orange
    "Pizza Shop": {
        "_base": [255, 100, 30],
        "Pizza Shop": [255, 100, 30],
        "Pizza": [255, 120, 50],
        "Neapolitan Pizza": [250, 90, 25],
    },

    # Other Western European
    "Portuguese": {
        "_base": [0, 180, 190],
        "Portuguese": [0, 180, 190],
    },
    "Greek": {
        "_base": [40, 170, 255],
        "Greek": [40, 170, 255],
    },
    "German": {
        "_base": [110, 130, 255],
        "German": [110, 130, 255],
    },
    "Austrian": {
        "_base": [135, 150, 255],
        "Austrian": [135, 150, 255],
    },
    "Swiss": {
        "_base": [160, 170, 255],
        "Swiss": [160, 170, 255],
    },
    "Belgian": {
        "_base": [90, 150, 220],
        "Belgian": [90, 150, 220],
    },
    "Dutch": {
        "_base": [100, 165, 235],
        "Dutch": [100, 165, 235],
    },
    "Scandinavian": {
        "_base": [130, 220, 255],
        "Scandinavian": [130, 220, 255],
        "Swedish": [145, 225, 255],
        "Danish": [160, 230, 255],
        "Norwegian": [175, 235, 255],
        "Finnish": [190, 240, 255],
        "Icelandic": [140, 215, 255],
    },

    # === EASTERN EUROPEAN (top-level) - Neon Periwinkle / Lavender Blue ===
    "Eastern European": {
        "_base": [120, 140, 255],
        "Eastern European": [120, 140, 255],
        "Eastern European (Unspecified)": [120, 140, 255],
        "Polish": [170, 180, 255],
        "Russian": [120, 140, 255],
        "Ukrainian": [100, 130, 255],
        "Hungarian": [85, 120, 255],
        "Czech": [75, 110, 250],
        "Romanian": [65, 100, 240],
        "Serbian": [55, 90, 235],
        "Croatian": [50, 80, 225],
        "Bosnian": [70, 85, 230],
        "Bulgarian": [95, 115, 240],
        "Moldovan": [105, 125, 250],
    },

    # === MIDDLE EASTERN (top-level) - Neon Amber / Warm Gold ===
    "Middle Eastern": {
        "_base": [255, 180, 40],
        "Middle Eastern": [255, 180, 40],
        "Middle Eastern (Unspecified)": [255, 180, 40],
        "Lebanese": [255, 160, 25],
        "Syrian": [245, 175, 15],
        "Turkish": [255, 195, 30],
        "Persian": [255, 185, 80],
        "Iranian": [255, 185, 80],
        "Israeli": [255, 200, 70],
        "Moroccan": [255, 210, 90],
        "Egyptian": [255, 215, 100],
        "Yemeni": [250, 170, 60],
        "Palestinian": [255, 190, 85],
        "Jordanian": [250, 195, 75],
        "Iraqi": [245, 185, 65],
        "Armenian": [235, 150, 30],
        "Georgian": [225, 145, 25],
        "Azerbaijani": [240, 160, 20],
        "Uzbek": [235, 170, 15],
        "Cypriot": [255, 190, 55],
    },

    # === AFRICAN (top-level) - Neon Burnt Sienna / Terracotta ===
    "African": {
        "_base": [255, 120, 70],
        "African": [255, 120, 70],
        "African (Unspecified)": [255, 120, 70],
        "Ethiopian": [240, 100, 55],
        "Eritrean": [245, 110, 60],
        "Nigerian": [255, 135, 80],
        "Ghanaian": [255, 145, 90],
        "Senegalese": [255, 155, 105],
        "Ivorian": [230, 90, 45],
        "Cameroonian": [235, 95, 50],
        "Somali": [225, 85, 40],
        "Kenyan": [220, 80, 35],
        "Ugandan": [215, 75, 30],
        "Tanzanian": [240, 105, 55],
        "South African": [250, 115, 65],
        "West African": [235, 100, 50],
        "East African": [230, 95, 48],
        "North African": [255, 140, 85],
    },

    # === CARIBBEAN (top-level) - Neon Turquoise / Aqua ===
    "Caribbean": {
        "_base": [0, 255, 200],
        "Caribbean": [0, 255, 200],
        "Caribbean (Unspecified)": [0, 255, 200],
        "Jamaican": [0, 240, 185],
        "Cuban": [30, 255, 210],
        "Puerto Rican": [60, 255, 220],
        "Dominican": [0, 225, 175],
        "Haitian": [0, 210, 165],
        "Trinidadian": [80, 255, 230],
        "Guyanese": [0, 245, 240],
    },

    # === LATIN AMERICAN (top-level) - Neon Green / Emerald ===
    "Latin American": {
        "_base": [50, 255, 100],
        "Latin American": [50, 255, 100],
        "Latin American (Unspecified)": [50, 255, 100],
        "Brazilian": [40, 240, 90],
        "Peruvian": [70, 255, 120],
        "Colombian": [90, 255, 140],
        "Argentinian": [30, 225, 80],
        "Venezuelan": [20, 210, 70],
        "Chilean": [110, 255, 160],
        "Ecuadorian": [130, 255, 175],
        "Bolivian": [15, 195, 60],
        "Uruguayan": [60, 235, 85],
        "Paraguayan": [75, 245, 95],
        "Salvadoran": [85, 250, 105],
        "Guatemalan": [95, 255, 115],
        "Honduran": [105, 255, 130],
        "Nicaraguan": [115, 255, 145],
        "Costa Rican": [125, 255, 155],
        "Panamanian": [130, 255, 165],
        "Brazilian Steakhouse": [25, 200, 65],
        "Argentinian Steakhouse": [35, 220, 80],
    },

    # Mexican subfamily - Neon Lime / Chartreuse
    "Mexican": {
        "_base": [200, 255, 0],
        "Mexican": [200, 255, 0],
        "Tex-Mex": [210, 255, 40],
        "Oaxacan": [180, 240, 0],
        "Yucatecan": [165, 230, 0],
    },

    # === AMERICAN (top-level) - Neon Purple / Violet ===
    "American": {
        "_base": [150, 80, 255],
        "American": [150, 80, 255],
        "Southern": [165, 100, 255],
        "Cajun": [180, 120, 255],
        "Creole": [200, 90, 255],
        "Cajun-Creole": [210, 110, 255],
        "Soul Food": [175, 60, 245],
        "Texas BBQ": [160, 50, 235],
        "New American": [135, 70, 250],
        "BBQ": [155, 45, 230],
        "Steakhouse": [140, 65, 240],
        "Juice Bar": [170, 110, 255],
        "Diner": [185, 135, 255],
        "Brunch": [175, 115, 255],
        "Breakfast": [180, 125, 255],
        "Burgers": [155, 90, 250],
        "Health Food": [190, 145, 255],
        "Vegan": [195, 155, 255],
        "Vegetarian": [200, 160, 255],
        "Seafood": [140, 75, 245],
        "Hotel Food": [170, 105, 255],
        "Bar & Grill": [155, 95, 250],
        "Deli": [180, 120, 255],
        "Hot Dogs": [150, 85, 245],
        "Sandwiches": [185, 130, 255],
        "Salads": [190, 140, 255],
        "Acai": [195, 150, 255],
        "Pancakes": [205, 165, 255],
        "Fine Dining": [130, 60, 235],
        "Southwestern": [160, 95, 255],
        "Buffet": [145, 80, 245],
    },

    # === PIZZA SHOP (top-level) - Neon Deep Orange ===
    "Pizza Shop": {
        "_base": [255, 100, 30],
        "Pizza Shop": [255, 100, 30],
        "Pizza": [255, 120, 50],
        "Neapolitan Pizza": [250, 90, 25],
    },

    # === JEWISH/KOSHER (top-level) - Neon Fuchsia ===
    "Jewish/Kosher": {
        "_base": [220, 60, 255],
        "Jewish/Kosher": [220, 60, 255],
        "Jewish": [220, 60, 255],
        "Kosher": [230, 90, 255],
        "Jewish Deli": [235, 110, 255],
    },

    # === BAR (top-level) - Neon Steel / Ice Blue ===
    "Bar": {
        "_base": [140, 180, 255],
        "Bar": [140, 180, 255],
        "Cocktail Bar": [120, 165, 255],
        "Wine Bar": [170, 200, 255],
        "Sports Bar": [180, 210, 255],
        "Pub": [130, 170, 255],
        "Gastropub": [155, 190, 255],
        "Beer Hall": [160, 195, 255],
        "Beer Garden": [165, 200, 255],
        "Brewery": [145, 185, 255],
        "Brewpub": [150, 188, 255],
    },

    # === CAFE (top-level) - Neon Peach / Coral ===
    "Cafe": {
        "_base": [255, 140, 105],
        "Cafe": [255, 140, 105],
        "Coffee Shop": [255, 155, 120],
        "Tea House": [255, 125, 90],
        "Bubble Tea": [255, 170, 140],
    },

    # === BAKERY (top-level) - Neon Rose / Salmon ===
    "Bakery": {
        "_base": [255, 110, 150],
        "Bakery": [255, 110, 150],
        "Pastry Shop": [255, 130, 165],
        "Dessert Shop": [255, 145, 180],
        "Ice Cream": [255, 160, 195],
        "Donuts": [255, 135, 170],
        "Bagels": [255, 120, 155],
    },

    # === OTHER (top-level) ===
    "Fast Food": {
        "_base": [200, 200, 255],  # Neon Lavender
        "Fast Food": [200, 200, 255],
    },
    "Fine Dining": {
        "_base": [255, 215, 0],  # Neon Gold
        "Fine Dining": [255, 215, 0],
    },
    "Buffet": {
        "_base": [180, 180, 255],  # Neon Soft Violet
        "Buffet": [180, 180, 255],
    },
    "Food Truck": {
        "_base": [0, 255, 160],  # Neon Mint
        "Food Truck": [0, 255, 160],
        "Street Food": [0, 240, 150],
    },
    "Noodles": {
        "_base": [255, 200, 60],  # Neon Marigold
        "Noodles": [255, 200, 60],
    },
}

# Default color for unmapped categories
DEFAULT_COLOR = [128, 128, 128]


def get_color_for_category(specific, general):
    """Get the color for a specific category based on its general group."""
    # First try to find the specific category in its general group
    if general in GEOGRAPHIC_COLORS:
        group = GEOGRAPHIC_COLORS[general]
        if specific in group:
            return group[specific]
        # Return the base color for the group
        return group.get("_base", DEFAULT_COLOR)

    # Try to find the specific category directly
    for group_name, group in GEOGRAPHIC_COLORS.items():
        if specific in group:
            return group[specific]

    return DEFAULT_COLOR


def prepare_map_data(enriched_path, original_path, output_path):
    """
    Prepare map data from enriched restaurant data.
    """
    print(f"Loading enriched data from: {enriched_path}")
    with open(enriched_path, 'r', encoding='utf-8') as f:
        enriched_data = json.load(f)

    print(f"Loading original data from: {original_path}")
    with open(original_path, 'r', encoding='utf-8') as f:
        original_data = json.load(f)

    # Create a lookup for enriched data
    enriched_lookup = {}
    for r in enriched_data.get('restaurants', []):
        key = f"{r.get('name')}|{r.get('address')}"
        enriched_lookup[key] = r

    print(f"Enriched restaurants: {len(enriched_lookup)}")
    print(f"Original restaurants: {len(original_data.get('restaurants', []))}")

    # Pre-compute which categories have children (are parents in SPECIFIC_TO_GENERAL)
    categories_with_children = set()
    for cat, parent in SPECIFIC_TO_GENERAL.items():
        categories_with_children.add(parent)

    # Process restaurants
    restaurants = []
    # Track counts at every level of the hierarchy
    all_counts = {}  # {category: count} (includes descendants)
    colors = {}  # {category: color}

    for r in original_data.get('restaurants', []):
        key = f"{r.get('name')}|{r.get('address')}"

        # Get enriched data if available
        enriched = enriched_lookup.get(key, {})

        # Use final categories from enriched data, or fall back to original
        specific = enriched.get('final_cat_specific') or r.get('category')

        # If this category has children and doesn't already have "(Unspecified)",
        # rename it to "(Unspecified)" so it shows as a distinct entry
        if specific in categories_with_children and not specific.endswith('(Unspecified)'):
            unspecified_name = f"{specific} (Unspecified)"
            # Use the parent color for the unspecified variant
            immediate_parent = get_general_category(specific)
            color = get_color_for_category(specific, immediate_parent)
            colors[unspecified_name] = color
            # The restaurant gets the unspecified category
            display_specific = unspecified_name
        else:
            display_specific = specific

        # Get the full hierarchy chain and top-level category (using original specific)
        chain = get_category_chain(specific)
        top_level = get_top_level_category(specific)
        immediate_parent = get_general_category(specific)

        # Get color for this category
        color = get_color_for_category(specific, immediate_parent)
        colors[specific] = color
        if display_specific != specific:
            colors[display_specific] = color

        # Track counts for all levels in the chain
        for cat in chain:
            all_counts[cat] = all_counts.get(cat, 0) + 1
        # Also track the unspecified variant
        if display_specific != specific:
            all_counts[display_specific] = all_counts.get(display_specific, 0) + 1

        restaurant = {
            'position': r.get('position'),
            'name': r.get('name'),
            'address': r.get('address'),
            'boro': r.get('boro'),
            'category': display_specific,
            'general': top_level,  # Use top-level for filtering
        }
        restaurants.append(restaurant)

    def build_nested_hierarchy(parent_cat, depth=0, max_depth=3):
        """Recursively build nested hierarchy for a category."""
        if depth >= max_depth:
            return None

        # Find all direct children of this parent from SPECIFIC_TO_GENERAL
        children = {}
        for cat, parent in SPECIFIC_TO_GENERAL.items():
            if parent == parent_cat and cat in all_counts:
                children[cat] = all_counts[cat]

        # Only add "(Unspecified)" when there are other real children to differentiate from
        if children:
            unspecified_name = f"{parent_cat} (Unspecified)"
            if unspecified_name in all_counts:
                children[unspecified_name] = all_counts[unspecified_name]

        if not children:
            return None

        result = {}
        for child, count in sorted(children.items(), key=lambda x: -x[1]):
            child_color = colors.get(child, get_color_for_category(child, parent_cat))
            child_entry = {
                'count': count,
                'color': child_color,
            }
            # Recursively get children of this child (skip unspecified entries)
            if not child.endswith('(Unspecified)'):
                nested = build_nested_hierarchy(child, depth + 1, max_depth)
                if nested:
                    child_entry['children'] = nested
            result[child] = child_entry

        return result

    # Build hierarchy starting from top-level categories
    hierarchy = {}
    top_level_cats = set()

    # Find all top-level categories (skip generated "(Unspecified)" entries)
    for cat in all_counts:
        if cat.endswith('(Unspecified)') and cat not in SPECIFIC_TO_GENERAL:
            continue  # Skip generated unspecified entries
        top = get_top_level_category(cat)
        top_level_cats.add(top)

    for top_cat in top_level_cats:
        if top_cat not in all_counts:
            continue

        hierarchy[top_cat] = {
            'count': all_counts[top_cat],
            'color': get_color_for_category(top_cat, top_cat),
        }

        # Build nested children
        children = build_nested_hierarchy(top_cat)
        if children:
            hierarchy[top_cat]['children'] = children

    # Sort hierarchy by total count
    hierarchy = dict(sorted(hierarchy.items(), key=lambda x: -x[1]['count']))

    output_data = {
        'restaurants': restaurants,
        'colors': colors,
        'hierarchy': hierarchy,
    }

    print(f"\nWriting output to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f)

    import os
    file_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Output file size: {file_size:.2f} MB")

    def print_hierarchy(node, indent=0):
        """Recursively print the hierarchy."""
        children = node.get('children', {})
        items = list(children.items())[:5]
        for name, data in items:
            print(f"{'  ' * indent}- {name}: {data['count']}")
            if 'children' in data:
                print_hierarchy(data, indent + 1)
        if len(children) > 5:
            print(f"{'  ' * indent}... and {len(children) - 5} more")

    print(f"\n--- Category Hierarchy ---")
    for general, data in list(hierarchy.items())[:15]:
        print(f"\n{general} ({data['count']})")
        print_hierarchy(data, indent=1)

    return len(restaurants)


if __name__ == '__main__':
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"

    enriched_file = data_dir / "restaurants_enriched.json"
    original_file = data_dir / "restaurants.json"
    output_file = data_dir / "map_data.json"  # Output to data folder (Vite's publicDir)

    if not enriched_file.exists():
        print(f"ERROR: Enriched data file not found: {enriched_file}")
        print("Run merge_google_data.py first to generate this file.")
        exit(1)

    if not original_file.exists():
        print(f"ERROR: Original data file not found: {original_file}")
        print("Run preprocess_data.py first to generate this file.")
        exit(1)

    prepare_map_data(str(enriched_file), str(original_file), str(output_file))
    print("\nDone! Refresh the browser to see updated data.")
