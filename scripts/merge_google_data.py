#!/usr/bin/env python3
"""
Merge Google Maps data with original DOHMH restaurant data.

This script takes the scraped Google Maps data and merges it with the
original preprocessed restaurant data, using Google's more specific
cuisine categories where available.

Usage:
    python merge_google_data.py
    python merge_google_data.py --dry-run  # Preview changes without saving
"""

import json
import argparse
from pathlib import Path
from collections import Counter
from difflib import SequenceMatcher
from category_mapping import map_google_category, get_improvement_stats, determine_final_categories


def similarity(a, b):
    """Calculate string similarity ratio (case-insensitive)."""
    if not a or not b:
        return 0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def normalize_address(addr):
    """
    Normalize address for comparison.
    - Lowercase
    - Remove city/state/zip (everything after first comma)
    - Normalize common abbreviations
    """
    if not addr:
        return ''

    # Lowercase
    addr = addr.lower()

    # Remove city/state/zip (after first comma)
    if ',' in addr:
        addr = addr.split(',')[0]

    # Normalize common abbreviations
    replacements = [
        ('street', 'st'),
        ('avenue', 'ave'),
        ('boulevard', 'blvd'),
        ('road', 'rd'),
        ('drive', 'dr'),
        ('place', 'pl'),
        ('court', 'ct'),
        ('lane', 'ln'),
        ('  ', ' '),  # double spaces
    ]
    for old, new in replacements:
        addr = addr.replace(old, new)

    return addr.strip()


def address_similarity(addr1, addr2):
    """Calculate similarity between two addresses after normalization."""
    norm1 = normalize_address(addr1)
    norm2 = normalize_address(addr2)
    return similarity(norm1, norm2)

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
ORIGINAL_FILE = DATA_DIR / "restaurants.json"
GOOGLE_FILE = DATA_DIR / "google_maps_raw.json"
OUTPUT_FILE = DATA_DIR / "restaurants_enriched.json"


def load_json(filepath):
    """Load a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data, filepath):
    """Save data to a JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def create_lookup_key(name, address):
    """Create a lookup key from name and address."""
    return f"{name}|{address}"


def merge_data(original_data, google_data, dry_run=False, limit=None):
    """
    Merge Google Maps data with original restaurant data.

    Args:
        original_data: Original preprocessed restaurant data
        google_data: Scraped Google Maps data
        dry_run: If True, don't save, just report what would change
        limit: If set, only process first N restaurants

    Returns:
        Merged data and statistics
    """
    restaurants = original_data.get('restaurants', [])
    google_results = google_data.get('results', [])

    # Apply limit if specified
    if limit:
        restaurants = restaurants[:limit]

    # Create lookup from Google data
    google_lookup = {}
    for result in google_results:
        key = create_lookup_key(
            result.get('original_name', ''),
            result.get('original_address', '')
        )
        google_lookup[key] = result

    # Track changes
    stats = {
        'total_restaurants': len(restaurants),
        'google_matches': 0,
        'confident_matches': 0,
        'low_confidence_skipped': 0,
        'no_google_category': 0,
        'matches': []
    }

    # Merge
    for restaurant in restaurants:
        key = create_lookup_key(
            restaurant.get('name', ''),
            restaurant.get('address', '')
        )

        if key in google_lookup:
            google_result = google_lookup[key]
            stats['google_matches'] += 1

            # Calculate name similarity
            name_sim = google_result.get('name_similarity', 0)

            # Calculate address similarity (normalized)
            addr_sim = 0
            google_addr = google_result.get('google_address', '')
            original_addr = restaurant.get('address', '')
            if google_addr and original_addr:
                addr_sim = address_similarity(original_addr, google_addr)

            # Matching: (name_sim > 0.8 AND addr_sim > 0.7) OR (name_sim > 0.5 AND addr_sim > 0.9)
            is_confident = (name_sim > 0.8 and addr_sim > 0.7) or (name_sim > 0.5 and addr_sim > 0.9)

            if not is_confident:
                stats['low_confidence_skipped'] += 1
                continue

            stats['confident_matches'] += 1

            # Get Google category
            google_cat = google_result.get('google_category', '')
            if not google_cat:
                stats['no_google_category'] += 1
                continue

            # Map Google category to our system
            mapped_category = map_google_category(google_cat)

            original_cat = restaurant.get('category', '')

            # Determine final categories (specific and general)
            final_specific, final_general = determine_final_categories(original_cat, mapped_category)

            # Track the match
            stats['matches'].append({
                'name': restaurant.get('name'),
                'address': restaurant.get('address'),
                'original_category': original_cat,
                'google_category': google_cat,
                'mapped_category': mapped_category,
                'final_cat_specific': final_specific,
                'final_cat_general': final_general,
                'name_similarity': round(name_sim, 2),
                'address_similarity': round(addr_sim, 2)
            })

            # Add Google data to restaurant (keep both original and Google)
            if not dry_run:
                restaurant['google_name'] = google_result.get('google_name')
                restaurant['google_address'] = google_addr
                restaurant['google_category'] = google_cat
                restaurant['google_category_mapped'] = mapped_category
                restaurant['final_cat_specific'] = final_specific
                restaurant['final_cat_general'] = final_general
                restaurant['name_similarity'] = round(name_sim, 2)
                restaurant['address_similarity'] = round(addr_sim, 2)

    # Update restaurants list if limited
    if limit:
        original_data['restaurants'] = restaurants

    return original_data, stats


def print_stats(stats, show_all=False):
    """Print merge statistics."""
    print("\n" + "=" * 60)
    print("MERGE STATISTICS")
    print("=" * 60)
    print(f"Total restaurants processed: {stats['total_restaurants']}")
    print(f"Found in Google data: {stats['google_matches']}")
    print(f"Confident matches: {stats['confident_matches']}")
    print(f"Low confidence skipped: {stats['low_confidence_skipped']}")
    print(f"No Google category: {stats['no_google_category']}")

    if stats['confident_matches'] > 0:
        print(f"\nConfident match rate: {stats['confident_matches'] / max(1, stats['google_matches']) * 100:.1f}%")

    if stats['matches']:
        print("\n" + "-" * 60)
        print(f"MATCHED RESTAURANTS ({len(stats['matches'])} total):")
        print("-" * 60)
        display_count = len(stats['matches']) if show_all else min(50, len(stats['matches']))
        for match in stats['matches'][:display_count]:
            print(f"\n  {match['name'][:40]}")
            print(f"    Address: {match['address'][:50]}")
            print(f"    Original category:  {match['original_category']}")
            print(f"    Google category:    {match['google_category']}")
            print(f"    Mapped category:    {match['mapped_category']}")
            print(f"    Final (specific):   {match['final_cat_specific']}")
            print(f"    Final (general):    {match['final_cat_general']}")
            print(f"    Name sim: {match['name_similarity']:.2f} | Addr sim: {match['address_similarity']:.2f}")
        if len(stats['matches']) > display_count:
            print(f"\n  ... and {len(stats['matches']) - display_count} more")


def main():
    parser = argparse.ArgumentParser(description='Merge Google Maps data with restaurant data')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without saving')
    parser.add_argument('--limit', type=int, help='Only process first N restaurants (for testing)')
    parser.add_argument('--show-all', action='store_true', help='Show all matches in output')
    args = parser.parse_args()

    print("Loading data...")

    # Check if files exist
    if not ORIGINAL_FILE.exists():
        print(f"Error: Original data file not found: {ORIGINAL_FILE}")
        return

    if not GOOGLE_FILE.exists():
        print(f"Error: Google Maps data file not found: {GOOGLE_FILE}")
        print("Run scrape_google_maps.py first to generate this file.")
        return

    original_data = load_json(ORIGINAL_FILE)
    google_data = load_json(GOOGLE_FILE)

    print(f"Original restaurants: {len(original_data.get('restaurants', []))}")
    print(f"Google results: {len(google_data.get('results', []))}")
    if args.limit:
        print(f"Processing limit: {args.limit}")

    # Merge
    merged_data, stats = merge_data(
        original_data,
        google_data,
        dry_run=args.dry_run,
        limit=args.limit
    )

    print_stats(stats, show_all=args.show_all)

    if not args.dry_run and stats['confident_matches'] > 0:
        # Save merged data
        save_json(merged_data, OUTPUT_FILE)
        print(f"\nMerged data saved to: {OUTPUT_FILE}")
    else:
        if args.dry_run:
            print("\n(Dry run - no files modified)")
        else:
            print("\nNo confident matches - original data unchanged")


if __name__ == '__main__':
    main()
