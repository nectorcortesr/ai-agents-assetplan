import json
import time
import logging
from typing import List
from pydantic import BaseModel
from playwright.sync_api import sync_playwright

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Pydantic Model ---
class PropertyListing(BaseModel):
    id: str
    title: str
    price: str
    location: str
    url: str
    property_type: str
    bedrooms: str
    available: str
    features: dict = {}
    images: List[str] = []
    timestamp: str = time.strftime("%Y-%m-%d %H:%M:%S")

# --- Utilities ---
def get_text(element, selector):
    el = element.query_selector(selector)
    return el.inner_text().strip() if el else ""

def get_attr(element, selector, attr):
    el = element.query_selector(selector)
    return el.get_attribute(attr) if el else ""

def process_property_types(property_types):
    bedrooms, available = [], []
    for prop in property_types:
        if "|" in prop:
            bed_count, avail = prop.split("|", 1)
            bedrooms.append(bed_count.strip())
            available.append(avail.strip())
        else:
            bedrooms.append(prop.strip())
            available.append("")
    return bedrooms, available

# --- Scraper Logic ---
def extract_property_data(card):
    try:
        title = get_text(card, 'a.text-neutral-800.text-lg') or "Sin título"
        location = get_text(card, 'span.text-neutral-500.text-sm') or "Ubicación desconocida"
        price = get_text(card, 'p.text-neutral-800.text-lg') or "Precio no disponible"
        url = get_attr(card, 'a.text-neutral-800.text-lg', 'href') or "#"
        if url and not url.startswith('http'):
            url = f"https://www.assetplan.cl{url}"

        property_types = [el.inner_text().strip() for el in card.query_selector_all('a.text-neutral-800.bg-white.border')]
        property_types = [p for p in property_types if "Dormitorio" in p or "Estudio" in p]
        bedrooms, available = process_property_types(property_types)

        images = [img.get_attribute('src') for img in card.query_selector_all('img.rounded-t-md') 
                if img.get_attribute('src') and not img.get_attribute('src').startswith('data:')]

        promotions = [el.inner_text().strip() for el in card.query_selector_all('div.badge_promos span')]

        return PropertyListing(
            id=str(uuid5(NAMESPACE_URL, title + location + url)),
            title=title,
            price=price,
            location=location,
            url=url,
            property_type=", ".join(bedrooms),
            bedrooms=", ".join(bedrooms),
            available=", ".join(available),
            features={"promotions": promotions},
            images=images
        )
    except Exception as e:
        logger.error(f"Error extrayendo datos: {e}")
        return None