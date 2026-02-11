#!/usr/bin/env python3
"""
Create a test dataset with just the scraped restaurants for visualization.
"""

import json
from pathlib import Path
from category_mapping import map_google_category

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"

# Load data
with open(DATA_DIR / "restaurants.json", 'r', encoding='utf-8') as f:
    original_data = json.load(f)

with open(DATA_DIR / "google_maps_raw.json", 'r', encoding='utf-8') as f:
    google_data = json.load(f)

# Get the colors from original data
colors = original_data.get('colors', {})

# Create lookup for original restaurants
original_lookup = {}
for r in original_data['restaurants']:
    key = f"{r['name']}|{r['address']}"
    original_lookup[key] = r

# Build test dataset with enriched categories
test_restaurants = []
attribute_table = []

for result in google_data['results']:
    key = f"{result['original_name']}|{result['original_address']}"

    if key not in original_lookup:
        continue

    orig = original_lookup[key]

    # Determine final category
    google_cat = result.get('google_category', '')
    mapped = map_google_category(google_cat)
    similarity = result.get('name_similarity', 0)

    # Use mapped category if confident and improves
    if mapped and similarity >= 0.6 and 'Unspecified' in result['original_category']:
        final_category = mapped
        category_source = 'Google Maps'
    else:
        final_category = result['original_category']
        category_source = 'DOHMH'

    # Build restaurant record
    restaurant = {
        'name': orig['name'],
        'address': orig['address'],
        'boro': orig['boro'],
        'position': orig['position'],
        'category': final_category,
        'original_category': result['original_category'],
        'google_category': google_cat,
        'category_source': category_source,
        'name_similarity': similarity,
        'google_reviews': result.get('google_reviews'),
        'google_rating': result.get('google_rating')
    }
    test_restaurants.append(restaurant)

    # Build attribute table row
    attr_row = {
        'name': orig['name'],
        'address': orig['address'],
        'boro': orig['boro'],
        'original_category': result['original_category'],
        'google_category': google_cat if google_cat else 'N/A',
        'final_category': final_category,
        'source': category_source,
        'confidence': f"{similarity:.0%}" if similarity else 'N/A',
        'improved': 'Yes' if category_source == 'Google Maps' and 'Unspecified' not in final_category else 'No'
    }
    attribute_table.append(attr_row)

# Add any new categories to colors
for r in test_restaurants:
    cat = r['category']
    if cat not in colors:
        # Generate a color for new categories
        import hashlib
        hash_val = int(hashlib.md5(cat.encode()).hexdigest()[:6], 16)
        colors[cat] = [
            (hash_val >> 16) & 0xFF,
            (hash_val >> 8) & 0xFF,
            hash_val & 0xFF
        ]

# Save test dataset
test_data = {
    'restaurants': test_restaurants,
    'colors': colors,
    'count': len(test_restaurants),
    'description': 'Test dataset with 100 scraped restaurants'
}

with open(DATA_DIR / "restaurants_test.json", 'w', encoding='utf-8') as f:
    json.dump(test_data, f, indent=2)

# Print attribute table
print("=" * 120)
print("ATTRIBUTE TABLE - 100 Scraped Restaurants")
print("=" * 120)
print(f"{'Name':<35} {'Original Category':<28} {'Google Category':<25} {'Final':<20} {'Improved'}")
print("-" * 120)

for row in attribute_table:
    name = row['name'][:33] + '..' if len(row['name']) > 35 else row['name']
    orig = row['original_category'][:26] + '..' if len(row['original_category']) > 28 else row['original_category']
    google = row['google_category'][:23] + '..' if len(row['google_category']) > 25 else row['google_category']
    final = row['final_category'][:18] + '..' if len(row['final_category']) > 20 else row['final_category']
    print(f"{name:<35} {orig:<28} {google:<25} {final:<20} {row['improved']}")

print("-" * 120)

# Summary
improved_count = sum(1 for r in attribute_table if r['improved'] == 'Yes')
print(f"\nTotal: {len(attribute_table)} restaurants")
print(f"Improved: {improved_count} ({improved_count/len(attribute_table)*100:.1f}%)")
print(f"\nTest data saved to: {DATA_DIR / 'restaurants_test.json'}")
