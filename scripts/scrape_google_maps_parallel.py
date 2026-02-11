#!/usr/bin/env python3
"""
Google Maps Parallel Scraper for NYC Restaurant Cuisine Enrichment

Optimized version with:
- Multiple parallel browser contexts (5 workers by default)
- Disabled images/CSS for faster page loads
- Reduced delays
- Progress tracking with ETA

Usage:
    python scrape_google_maps_parallel.py --workers 5 --sample 500
    python scrape_google_maps_parallel.py --workers 5 --all
    python scrape_google_maps_parallel.py --resume
"""

import asyncio
import json
import random
import re
import argparse
import time
from pathlib import Path
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from urllib.parse import quote_plus
from collections import deque

from playwright.async_api import async_playwright
from playwright_stealth import Stealth


# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
INPUT_FILE = DATA_DIR / "restaurants.json"
OUTPUT_FILE = DATA_DIR / "google_maps_raw.json"
PROGRESS_FILE = DATA_DIR / "scrape_progress_parallel.json"


# Optimized rate limiting settings
MIN_DELAY = 1.5  # Reduced from 3.0
MAX_DELAY = 2.5  # Reduced from 6.0
DEFAULT_WORKERS = 5  # Parallel browser contexts


class ProgressTracker:
    """Track scraping progress with ETA calculation."""

    def __init__(self, total):
        self.total = total
        self.completed = 0
        self.found = 0
        self.failed = 0
        self.start_time = time.time()
        self.recent_times = deque(maxlen=50)  # Last 50 request times

    def update(self, found=True, duration=0):
        self.completed += 1
        if found:
            self.found += 1
        else:
            self.failed += 1
        self.recent_times.append(duration)

    def get_eta(self):
        if not self.recent_times or self.completed == 0:
            return "calculating..."

        avg_time = sum(self.recent_times) / len(self.recent_times)
        remaining = self.total - self.completed
        eta_seconds = remaining * avg_time

        if eta_seconds < 60:
            return f"{int(eta_seconds)}s"
        elif eta_seconds < 3600:
            return f"{int(eta_seconds / 60)}m"
        else:
            hours = int(eta_seconds / 3600)
            mins = int((eta_seconds % 3600) / 60)
            return f"{hours}h {mins}m"

    def get_rate(self):
        if not self.recent_times:
            return 0
        return 60 / (sum(self.recent_times) / len(self.recent_times))  # requests/min

    def print_status(self):
        elapsed = time.time() - self.start_time
        elapsed_str = str(timedelta(seconds=int(elapsed)))
        rate = self.get_rate()
        eta = self.get_eta()

        print(f"\r[{self.completed}/{self.total}] "
              f"Found: {self.found} | Failed: {self.failed} | "
              f"Rate: {rate:.1f}/min | ETA: {eta} | Elapsed: {elapsed_str}",
              end="", flush=True)


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
        json.dump(progress, f)


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
    name = re.sub(r'\s+', ' ', name).strip()
    query = f'"{name}" {address} {boro} NYC'
    return query


def clean_address(text):
    """Clean address text from Google Maps (remove icons, clean whitespace)."""
    if not text:
        return None
    # Remove Google Maps icon characters (private use area unicode)
    text = re.sub(r'[\ue000-\uf8ff]', '', text)
    # Replace newlines with comma+space
    text = re.sub(r'\n+', ', ', text)
    # Clean up multiple spaces/commas
    text = re.sub(r',\s*,', ',', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip(' ,')
    return text if text else None


async def extract_place_info(page):
    """Extract place information from Google Maps result page."""
    info = {
        'found': False,
        'google_name': None,
        'google_address': None,
        'google_category': None,
        'google_url': None
    }

    try:
        # Reduced wait time
        await asyncio.sleep(1.5)
        info['google_url'] = page.url

        # Wait for main elements
        try:
            await page.wait_for_selector('h1, [role="main"]', timeout=5000)
        except:
            pass

        await asyncio.sleep(0.5)

        # Get name
        try:
            name_el = await page.query_selector('h1.fontHeadlineLarge, h1')
            if name_el:
                text = await name_el.inner_text()
                if text and len(text) < 200:
                    info['google_name'] = text.strip()
        except:
            pass

        # Get address - multiple strategies
        # Strategy 1: Button with data-item-id="address"
        try:
            addr_btn = await page.query_selector('button[data-item-id="address"]')
            if addr_btn:
                text = await addr_btn.inner_text()
                if text and len(text) < 200:
                    info['google_address'] = clean_address(text)
        except:
            pass

        # Strategy 2: Aria-label containing "Address:"
        if not info['google_address']:
            try:
                addr_el = await page.query_selector('[aria-label^="Address:"]')
                if addr_el:
                    label = await addr_el.get_attribute('aria-label')
                    if label:
                        # Extract address after "Address: "
                        addr = label.replace('Address:', '').strip()
                        if addr and len(addr) < 200:
                            info['google_address'] = clean_address(addr)
            except:
                pass

        # Strategy 3: Look for NYC address pattern in text content
        if not info['google_address']:
            try:
                # Look for elements containing NY address patterns
                all_text = await page.query_selector_all('[data-item-id], button.CsEnBe')
                for el in all_text[:20]:
                    text = await el.inner_text()
                    if text:
                        # Look for NYC address pattern (number + street + NY/NYC/borough)
                        if re.search(r'\d+.*(?:NY|New York|Manhattan|Brooklyn|Queens|Bronx|Staten)', text, re.IGNORECASE):
                            if len(text) < 200 and not any(kw in text.lower() for kw in ['hour', 'open', 'close', 'review', 'rating']):
                                info['google_address'] = clean_address(text)
                                break
            except:
                pass

        # Get category from buttons
        try:
            buttons = await page.query_selector_all('button[jsaction*="pane.rating.category"], button.DkEaL')
            for btn in buttons:
                text = await btn.inner_text()
                if text and len(text) < 100:
                    text_lower = text.lower()
                    if any(kw in text_lower for kw in ['restaurant', 'cafe', 'food', 'cuisine', 'bar', 'grill', 'kitchen', 'diner', 'pizzeria', 'bakery', 'deli']):
                        info['google_category'] = text.strip()
                        break
        except:
            pass

        # Get category from spans
        if not info['google_category']:
            try:
                spans = await page.query_selector_all('span.fontBodyMedium, span.DkEaL')
                for span in spans:
                    text = await span.inner_text()
                    if text and len(text) < 100:
                        text_lower = text.lower()
                        if any(kw in text_lower for kw in ['restaurant', 'cafe', 'food', 'cuisine', 'bar', 'grill', 'kitchen', 'diner', 'pizzeria', 'bakery', 'deli']):
                            info['google_category'] = text.strip()
                            break
            except:
                pass

        # Get category from aria-labels (limited search)
        if not info['google_category']:
            try:
                els = await page.query_selector_all('[aria-label]')
                for el in els[:30]:
                    label = await el.get_attribute('aria-label')
                    if label and len(label) < 100:
                        label_lower = label.lower()
                        for keyword in ['restaurant', 'cafe', 'cuisine']:
                            if keyword in label_lower:
                                match = re.search(r'([\w\s]+(?:restaurant|cafe|cuisine|food|bar|grill))', label, re.IGNORECASE)
                                if match:
                                    info['google_category'] = match.group(1).strip()
                                    break
                    if info['google_category']:
                        break
            except:
                pass

        info['found'] = bool(info['google_name'])

    except Exception as e:
        info['error'] = str(e)

    return info


async def scrape_restaurant(page, restaurant):
    """Scrape Google Maps for a single restaurant."""
    query = build_search_query(restaurant)
    search_url = f'https://www.google.com/maps/search/{quote_plus(query)}'

    result = {
        'original_name': restaurant['name'],
        'original_address': restaurant['address'],
        'original_category': restaurant['category'],
        'original_boro': restaurant['boro'],
        'search_query': query,
        'scraped_at': datetime.now().isoformat()
    }

    try:
        await page.goto(search_url, wait_until='domcontentloaded', timeout=15000)
        info = await extract_place_info(page)
        result.update(info)

        if info['google_name']:
            name_sim = similarity(restaurant['name'], info['google_name'])
            result['name_similarity'] = round(name_sim, 2)

            # Calculate address similarity if we have both addresses
            addr_sim = 0
            if info.get('google_address') and restaurant.get('address'):
                addr_sim = similarity(restaurant['address'], info['google_address'])
                result['address_similarity'] = round(addr_sim, 2)

            # Confident match: high name similarity OR (decent name + high address match)
            result['confident_match'] = name_sim > 0.9 or (name_sim > 0.5 and addr_sim > 0.8)

    except Exception as e:
        result['error'] = str(e)
        result['found'] = False

    return result


async def worker(worker_id, queue, progress, progress_lock, results_lock, progress_data):
    """Worker that processes restaurants from the queue."""
    async with async_playwright() as p:
        # Launch browser with optimizations
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
            ]
        )

        # Create context with resource blocking
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York'
        )

        # Block images, fonts, stylesheets for faster loading
        await context.route("**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf}", lambda route: route.abort())
        await context.route("**/*", lambda route: route.abort() if route.request.resource_type in ["stylesheet", "font", "image"] else route.continue_())

        page = await context.new_page()

        # Apply stealth
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        while True:
            try:
                restaurant = queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            start_time = time.time()

            # Scrape
            result = await scrape_restaurant(page, restaurant)
            duration = time.time() - start_time

            # Update progress
            restaurant_id = f"{restaurant['name']}|{restaurant['address']}"

            async with progress_lock:
                progress_data['scraped_ids'].append(restaurant_id)
                if result.get('found'):
                    progress_data['results'].append(result)
                else:
                    progress_data['failed'].append(result)

            async with results_lock:
                progress.update(found=result.get('found', False), duration=duration)
                progress.print_status()

            # Rate limiting delay
            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            await asyncio.sleep(delay)

        await browser.close()


async def run_scraper(sample_size=None, resume=False, num_workers=DEFAULT_WORKERS, prioritize_unspecified=True):
    """Main parallel scraper function."""
    print("=" * 70)
    print("Google Maps PARALLEL Restaurant Scraper")
    print(f"Workers: {num_workers}")
    print("=" * 70)

    # Load data
    print("\nLoading restaurant data...")
    restaurants = load_restaurants()
    print(f"Total restaurants: {len(restaurants)}")

    # Load progress if resuming
    progress_data = load_progress() if resume else {
        'scraped_ids': [],
        'results': [],
        'failed': [],
        'last_updated': None
    }

    if resume and progress_data['scraped_ids']:
        print(f"Resuming: {len(progress_data['scraped_ids'])} already scraped")

    # Filter out already scraped
    scraped_set = set(progress_data['scraped_ids'])
    remaining = [r for r in restaurants if f"{r['name']}|{r['address']}" not in scraped_set]

    # Prioritize "Unspecified" categories
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

    # Estimate time
    est_time = (len(remaining) / num_workers) * ((MIN_DELAY + MAX_DELAY) / 2 + 3)  # 3 sec per request + delay
    print(f"Estimated time: {timedelta(seconds=int(est_time))}")

    # Create queue
    queue = asyncio.Queue()
    for r in remaining:
        await queue.put(r)

    # Create progress tracker
    progress = ProgressTracker(len(remaining))
    progress_lock = asyncio.Lock()
    results_lock = asyncio.Lock()

    print(f"\nStarting {num_workers} workers...\n")

    # Start workers
    workers = [
        asyncio.create_task(worker(i, queue, progress, progress_lock, results_lock, progress_data))
        for i in range(num_workers)
    ]

    # Save progress periodically
    async def save_periodically():
        while not all(w.done() for w in workers):
            await asyncio.sleep(30)  # Save every 30 seconds
            save_progress(progress_data)

    save_task = asyncio.create_task(save_periodically())

    # Wait for all workers
    await asyncio.gather(*workers)
    save_task.cancel()

    # Final save
    save_progress(progress_data)
    save_results(progress_data['results'])

    # Summary
    print("\n\n" + "=" * 70)
    print("SCRAPE COMPLETE")
    print("=" * 70)
    elapsed = time.time() - progress.start_time
    print(f"Total time: {timedelta(seconds=int(elapsed))}")
    print(f"Total scraped: {len(progress_data['scraped_ids'])}")
    print(f"Found: {len(progress_data['results'])}")
    print(f"Not found: {len(progress_data['failed'])}")
    print(f"Match rate: {len(progress_data['results']) / max(1, len(progress_data['scraped_ids'])) * 100:.1f}%")
    print(f"Average rate: {len(progress_data['scraped_ids']) / max(1, elapsed) * 60:.1f} restaurants/min")
    print(f"\nResults saved to: {OUTPUT_FILE}")
    print(f"Progress saved to: {PROGRESS_FILE}")


def main():
    parser = argparse.ArgumentParser(description='Parallel Google Maps scraper')
    parser.add_argument('--sample', type=int, help='Number of restaurants to sample')
    parser.add_argument('--all', action='store_true', help='Scrape all restaurants')
    parser.add_argument('--resume', action='store_true', help='Resume from last progress')
    parser.add_argument('--workers', type=int, default=DEFAULT_WORKERS, help=f'Number of parallel workers (default: {DEFAULT_WORKERS})')
    parser.add_argument('--no-prioritize', action='store_true', help='Do not prioritize Unspecified categories')

    args = parser.parse_args()

    if args.all:
        sample_size = None
    elif args.sample:
        sample_size = args.sample
    else:
        sample_size = 100
        print("No sample size specified. Using default of 100 for testing.")
        print("Use --sample N or --all for different amounts.\n")

    asyncio.run(run_scraper(
        sample_size=sample_size,
        resume=args.resume,
        num_workers=args.workers,
        prioritize_unspecified=not args.no_prioritize
    ))


if __name__ == '__main__':
    main()
