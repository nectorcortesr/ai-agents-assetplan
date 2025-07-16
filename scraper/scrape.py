import json
import time
import logging
import argparse

from uuid import uuid5, NAMESPACE_URL
from typing import List, Dict
from pydantic import BaseModel
from playwright.sync_api import sync_playwright, Browser

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Pydantic Model ---
class PropertyListing(BaseModel):
    id: str
    title: str
    location: str
    url: str
    images: List[str]
    typologies: List[Dict]
    timestamp: str = time.strftime("%Y-%m-%d %H:%M:%S")

# --- Utilities ---
def get_text(element, selector: str) -> str:
    el = element.query_selector(selector)
    return el.inner_text().strip() if el else ""

def get_attr(element, selector: str, attr: str) -> str:
    el = element.query_selector(selector)
    return el.get_attribute(attr) or "" if el else ""

# --- Detail Extraction ---
def extract_building_detail(browser: Browser, url: str) -> Dict:
    page = browser.new_page()
    # retry on connection issues
    for attempt in range(2):
        try:
            page.goto(url, timeout=45000, wait_until="domcontentloaded")
            break
        except Exception as e:
            logger.warning(f"Detail load failed (attempt {attempt+1}): {e}")
    # Title and location
    title = get_text(page, 'a.block.overflow-hidden.text-lg.font-bold') or get_text(page, 'nav.breadcrumbs li:last-child a')
    location = get_text(page, 'span.text-neutral-500')

    # Images
    images = [img.get_attribute('src') for img in page.query_selector_all('img.gallery__img') if img.get_attribute('src')]

    # Typologies
    typologies = []
    # select correct block pattern
    blocks = page.query_selector_all('div.flex.w-full.lg\\:w-\\[174px\\] + div.flex.flex-col')
    for block in blocks:
        cells = block.query_selector_all('div.inline-flex.items-center')
        bd = " ".join(p.inner_text().strip() for p in cells[0].query_selector_all('p')) if len(cells) > 0 else ""
        ba = " ".join(p.inner_text().strip() for p in cells[1].query_selector_all('p')) if len(cells) > 1 else ""
        size_range = get_text(block, 'p:has-text("m² útiles")')
        price_range = get_text(block, 'div.mt-2 p.text-lg.font-semibold')
        available = get_text(block, 'a:has-text("Ver")').replace('Ver', '').replace('disponibles', '').strip()
        promos = [span.inner_text().strip() for span in block.query_selector_all('div.badge_promos span')]
        typologies.append({
            'bedrooms': bd,
            'bathrooms': ba,
            'size_range': size_range,
            'price_range': price_range,
            'available': available,
            'promotions': promos
        })
    page.close()
    return { 'title': title, 'location': location, 'images': images, 'typologies': typologies }

# --- Scraper Logic ---
def scrape_assetplan(min_props: int = 50, max_pages: int = 50) -> List[PropertyListing]:
    results: List[PropertyListing] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # block heavy resources for speed
        page.route("**/*", lambda route, req: route.abort() if req.resource_type in ["stylesheet","font"] else route.continue_())

        page_num = 1
        while len(results) < min_props and page_num <= max_pages:
            list_url = f"https://www.assetplan.cl/arriendo/departamento?page={page_num}"
            logger.info(f"Loading list page {page_num}")
            # retry on connection errors
            for attempt in range(2):
                try:
                    page.goto(list_url, timeout=30000, wait_until="networkidle")
                    break
                except Exception as e:
                    logger.warning(f"List page load failed (attempt {attempt+1}): {e}")
            cards = page.query_selector_all('article.building-card')
            logger.info(f"Found {len(cards)} cards")
            for idx, card in enumerate(cards, 1):
                logger.info(f"Processing card {idx}")
                card_title = get_text(card, 'a.text-neutral-800.text-lg')
                card_location = get_text(card, 'span.text-neutral-500.text-sm')
                href = get_attr(card, 'a.text-neutral-800.text-lg', 'href')
                detail_url = href if href.startswith('http') else f"https://www.assetplan.cl{href}"

                detail = extract_building_detail(browser, detail_url)
                listing = PropertyListing(
                    id=str(uuid5(NAMESPACE_URL, detail_url)),
                    title=detail['title'] or card_title,
                    location=detail['location'] or card_location,
                    url=detail_url,
                    images=detail['images'],
                    typologies=detail['typologies']
                )
                results.append(listing)
                logger.info(f"Collected {len(results)} listings")
                if len(results) >= min_props:
                    break
            page_num += 1
        page.close()
        browser.close()
    return results

# --- Save to JSON ---
def save_to_json(listings: List[PropertyListing], filename_base: str = "data/assetplan_properties") -> str:
    ts = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_base}_{ts}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump([l.model_dump() for l in listings], f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(listings)} listings to {filename}")
    return filename

# --- CLI ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Assetplan scraper")
    parser.add_argument('--min', type=int, default=50, help='Minimum properties')
    parser.add_argument('--max', type=int, default=50, help='Max pages')
    args = parser.parse_args()

    listings = scrape_assetplan(min_props=args.min, max_pages=args.max)
    out_file = save_to_json(listings)
    print(f"Done. File: {out_file}")
