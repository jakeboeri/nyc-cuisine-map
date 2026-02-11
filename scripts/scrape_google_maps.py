#!/usr/bin/env python3
"""
Google Maps Scraper for NYC Restaurant Cuisine Enrichment

Scrapes Google Maps to get more accurate cuisine/category data for restaurants.
Uses Playwright for browser automation with stealth mode to avoid detection.

Usage:
    python scrape_google_maps.py --sample 10    # Test with 10 restaurants
    python scrape_google_maps.py --sample 100   # Sample of 100
    python scrape_google_maps.py --all          # Full dataset (use with caution)
    python scrape_google_maps.py --resume       # Resume from last progress
"""

import asyncio
import json
import random
import re
import argparse
import time
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher
from urllib.parse import quote_plus

from playwright.async_api import async_playwright
from playwright_stealth import Stealth


# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
INPUT_FILE = DATA_DIR / "restaurants.json"
OUTPUT_FILE = DATA_DIR / "google_maps_raw.json"
PROGRESS_FILE = DATA_DIR / "scrape_progress.json"


# Rate limiting settings (conservative for no proxies)
MIN_DELAY = 3.0  # Minimum seconds between requests
MAX_DELAY = 6.0  # Maximum seconds between requests
BATCH_SIZE = 50  # Requests before longer pause
BATCH_PAUSE = 60  # Seconds to pause between batches


def load_restaurants():
    """Load preprocessed restaurant data."""
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('restaurants', [])


def load_progress():
    """Load scraping progress if exists."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'scraped_ids': [],
        'results': [],
        'failed': [],
        'last_updated': None
    }


def save_progress(progress):
    """Save scraping progress."""
    progress['last_updated'] = datetime.now().isoformat()
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2)


def save_results(results):
    """Save final results."""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'scraped_at': datetime.now().isoformat(),
            'count': len(results),
            'results': results
        }, f, indent=2)


def similarity(a, b):
    """Calculate string similarity ratio."""
    if not a or not b:
        return 0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def build_search_query(restaurant):
    """Build Google Maps search query from restaurant data."""
    name = restaurant.get('name', '')
    address = restaurant.get('address', '')
    boro = restaurant.get('boro', '')

    # Clean up the name (remove extra spaces, special chars)
    name = re.sub(r'\s+', ' ', name).strip()

    # Build query: "Restaurant Name" address NYC
    query = f'"{name}" {address} {boro} NYC'
    return query


async def extract_place_info(page):
    """Extract place information from Google Maps result page."""
    info = {
        'found': False,
        'google_name': None,
        'google_address': None,
        'google_category': None,
        'google_rating': None,
        'google_reviews': None,
        'google_url': None
    }

    try:
        # Wait for the page to settle (don't use networkidle - Google Maps never stops)
        await asyncio.sleep(3)  # Give time for initial render

        # Get current URL
        info['google_url'] = page.url

        # Wait for any of these common Google Maps elements
        try:
            await page.wait_for_selector('h1, [role="main"], .fontHeadlineLarge', timeout=8000)
        except:
            pass  # Continue even if timeout

        await asyncio.sleep(1)  # Extra stabilization

        # Method 1: Look for the place title/name (h1 is the main place name)
        try:
            name_el = await page.query_selector('h1.fontHeadlineLarge, h1')
            if name_el:
                text = await name_el.inner_text()
                if text and len(text) < 200:  # Sanity check
                    info['google_name'] = text.strip()
        except:
            pass

        # Method 2: Look for category button (Google shows category as clickable button)
        # The category appears below the name, usually contains "restaurant", "cafe", etc.
        try:
            # Look for buttons in the header area that might be categories
            buttons = await page.query_selector_all('button[jsaction*="pane.rating.category"], button.DkEaL')
            for btn in buttons:
                text = await btn.inner_text()
                if text and len(text) < 100:
                    # Check if it looks like a category
                    text_lower = text.lower()
                    if any(keyword in text_lower for keyword in ['restaurant', 'cafe', 'food', 'cuisine', 'bar', 'grill', 'kitchen', 'diner', 'pizzeria', 'bakery', 'deli']):
                        info['google_category'] = text.strip()
                        break
        except:
            pass

        # Method 3: Look for category in span elements near the header
        if not info['google_category']:
            try:
                # Category often appears as a span with specific class
                spans = await page.query_selector_all('span.fontBodyMedium, span.DkEaL')
                for span in spans:
                    text = await span.inner_text()
                    if text and len(text) < 100:
                        text_lower = text.lower()
                        if any(keyword in text_lower for keyword in ['restaurant', 'cafe', 'food', 'cuisine', 'bar', 'grill', 'kitchen', 'diner', 'pizzeria', 'bakery', 'deli']):
                            info['google_category'] = text.strip()
                            break
            except:
                pass

        # Method 4: Check aria-labels for category info
        if not info['google_category']:
            try:
                els = await page.query_selector_all('[aria-label]')
                for el in els[:50]:  # Limit to first 50 to avoid too much processing
                    label = await el.get_attribute('aria-label')
                    if label and len(label) < 100:
                        label_lower = label.lower()
                        # Look for patterns like "Mexican restaurant" in aria-labels
                        for keyword in ['restaurant', 'cafe', 'cuisine']:
                            if keyword in label_lower:
                                # Extract the category part
                                match = re.search(r'([\w\s]+(?:restaurant|cafe|cuisine|food|bar|grill))', label, re.IGNORECASE)
                                if match:
                                    info['google_category'] = match.group(1).strip()
                                    break
                    if info['google_category']:
                        break
            except:
                pass

        # Method 5: Look for rating (aria-label containing stars)
        try:
            rating_el = await page.query_selector('[aria-label*="star"], span.ceNzKf, span.MW4etd')
            if rating_el:
                # Try aria-label first
                label = await rating_el.get_attribute('aria-label')
                if label:
                    match = re.search(r'([\d.]+)\s*star', label, re.IGNORECASE)
                    if match:
                        info['google_rating'] = float(match.group(1))
                else:
                    # Try inner text
                    text = await rating_el.inner_text()
                    try:
                        rating = float(text.strip())
                        if 1 <= rating <= 5:
                            info['google_rating'] = rating
                    except:
                        pass
        except:
            pass

        # Method 6: Look for review count
        try:
            review_el = await page.query_selector('[aria-label*="review"], span.UY7F9')
            if review_el:
                label = await review_el.get_attribute('aria-label')
                if label:
                    match = re.search(r'([\d,]+)\s*review', label, re.IGNORECASE)
                    if match:
                        info['google_reviews'] = int(match.group(1).replace(',', ''))
                else:
                    text = await review_el.inner_text()
                    # Often formatted as "(1,234)"
                    match = re.search(r'\(?([\d,]+)\)?', text)
                    if match:
                        info['google_reviews'] = int(match.group(1).replace(',', ''))
        except:
            pass

        # Method 7: Get address from the page
        try:
            address_el = await page.query_selector('[data-item-id="address"], button[data-tooltip="Copy address"]')
            if address_el:
                info['google_address'] = await address_el.inner_text()
        except:
            pass

        # Consider found if we have a name
        info['found'] = bool(info['google_name'])

    except Exception as e:
        info['error'] = str(e)

    return info


async def scrape_restaurant(page, restaurant, index, total):
    """Scrape Google Maps for a single restaurant."""
    query = build_search_query(restaurant)
    search_url = f'https://www.google.com/maps/search/{quote_plus(query)}'

    print(f"[{index+1}/{total}] Searching: {restaurant['name'][:40]}...")

    result = {
        'original_name': restaurant['name'],
        'original_address': restaurant['address'],
        'original_category': restaurant['category'],
        'original_boro': restaurant['boro'],
        'search_query': query,
        'scraped_at': datetime.now().isoformat()
    }

    try:
        # Navigate to search
        await page.goto(search_url, wait_until='domcontentloaded', timeout=30000)

        # Extract info
        info = await extract_place_info(page)
        result.update(info)

        # Calculate match confidence
        if info['google_name']:
            name_sim = similarity(restaurant['name'], info['google_name'])
            result['name_similarity'] = round(name_sim, 2)
            result['confident_match'] = name_sim > 0.7

    except Exception as e:
        result['error'] = str(e)
        result['found'] = False

    return result


async def run_scraper(sample_size=None, resume=False, prioritize_unspecified=True):
    """Main scraper function."""
    print("=" * 60)
    print("Google Maps Restaurant Scraper")
    print("=" * 60)

    # Load data
    print("\nLoading restaurant data...")
    restaurants = load_restaurants()
    print(f"Total restaurants: {len(restaurants)}")

    # Load progress if resuming
    progress = load_progress() if resume else {
        'scraped_ids': [],
        'results': [],
        'failed': [],
        'last_updated': None
    }

    if resume and progress['scraped_ids']:
        print(f"Resuming from previous session: {len(progress['scraped_ids'])} already scraped")

    # Filter out already scraped
    scraped_set = set(progress['scraped_ids'])
    remaining = [r for r in restaurants if f"{r['name']}|{r['address']}" not in scraped_set]

    # Prioritize "Unspecified" categories if requested
    if prioritize_unspecified:
        unspecified = [r for r in remaining if 'Unspecified' in r.get('category', '')]
        specified = [r for r in remaining if 'Unspecified' not in r.get('category', '')]
        remaining = unspecified + specified
        print(f"Prioritizing {len(unspecified)} 'Unspecified' category restaurants")

    # Apply sample size
    if sample_size:
        remaining = remaining[:sample_size]

    print(f"Restaurants to scrape: {len(remaining)}")

    if not remaining:
        print("No restaurants to scrape!")
        return

    # Start browser
    print("\nLaunching browser...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
            ]
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York'
        )

        page = await context.new_page()

        # Apply stealth
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        print("Browser ready. Starting scrape...\n")

        # Scrape loop
        total = len(remaining)
        for i, restaurant in enumerate(remaining):
            # Scrape
            result = await scrape_restaurant(page, restaurant, i, total)

            # Update progress
            restaurant_id = f"{restaurant['name']}|{restaurant['address']}"
            progress['scraped_ids'].append(restaurant_id)

            if result.get('found'):
                progress['results'].append(result)
                status = "FOUND" if result.get('confident_match') else "found (low confidence)"
                category = result.get('google_category', 'N/A')
                print(f"    -> {status}: {category}")
            else:
                progress['failed'].append(result)
                print(f"    -> NOT FOUND")

            # Save progress periodically
            if (i + 1) % 10 == 0:
                save_progress(progress)
                print(f"\n--- Progress saved: {len(progress['results'])} found, {len(progress['failed'])} not found ---\n")

            # Rate limiting
            if (i + 1) % BATCH_SIZE == 0:
                print(f"\n--- Batch pause ({BATCH_PAUSE}s) to avoid rate limiting ---\n")
                await asyncio.sleep(BATCH_PAUSE)
            else:
                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                await asyncio.sleep(delay)

        await browser.close()

    # Final save
    save_progress(progress)
    save_results(progress['results'])

    # Summary
    print("\n" + "=" * 60)
    print("SCRAPE COMPLETE")
    print("=" * 60)
    print(f"Total scraped: {len(progress['scraped_ids'])}")
    print(f"Found: {len(progress['results'])}")
    print(f"Not found: {len(progress['failed'])}")
    print(f"Match rate: {len(progress['results']) / len(progress['scraped_ids']) * 100:.1f}%")
    print(f"\nResults saved to: {OUTPUT_FILE}")
    print(f"Progress saved to: {PROGRESS_FILE}")


def main():
    parser = argparse.ArgumentParser(description='Scrape Google Maps for restaurant data')
    parser.add_argument('--sample', type=int, help='Number of restaurants to sample')
    parser.add_argument('--all', action='store_true', help='Scrape all restaurants')
    parser.add_argument('--resume', action='store_true', help='Resume from last progress')
    parser.add_argument('--no-prioritize', action='store_true', help='Do not prioritize Unspecified categories')

    args = parser.parse_args()

    if args.all:
        sample_size = None
    elif args.sample:
        sample_size = args.sample
    else:
        # Default to small sample for testing
        sample_size = 10
        print("No sample size specified. Using default of 10 for testing.")
        print("Use --sample N or --all for different amounts.\n")

    asyncio.run(run_scraper(
        sample_size=sample_size,
        resume=args.resume,
        prioritize_unspecified=not args.no_prioritize
    ))


if __name__ == '__main__':
    main()
