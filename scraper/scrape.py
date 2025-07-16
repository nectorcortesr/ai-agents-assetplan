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