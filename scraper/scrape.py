import json
import time
import random
import logging
import argparse

from uuid import uuid5, NAMESPACE_URL
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

def scrape_assetplan_enhanced(min_properties=50, max_pages=50):
    properties = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = browser.new_context(viewport={"width": 1920, "height": 1080},
                                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        page_num = 1
        consecutive_empty_pages = 0

        while len(properties) < min_properties and page_num <= max_pages:
            logger.info(f"\nNavegando a página {page_num}...")
            url = f"https://www.assetplan.cl/arriendo/departamento?page={page_num}"
            try:
                page.goto(url, timeout=60000)
                page.wait_for_selector('div.bg-white.rounded-b-md', timeout=30000)
                for i in range(5):
                    page.evaluate(f"window.scrollTo(0, {i * 500})")
                    time.sleep(0.5)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error cargando página {page_num}: {e}")
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= 3:
                    logger.warning("Demasiadas páginas consecutivas con errores, deteniendo...")
                    break
                page_num += 1
                continue

            cards = page.query_selector_all('div.bg-white.rounded-b-md')
            if not cards:
                logger.warning(f"No se encontraron propiedades en página {page_num}")
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= 3:
                    break
                page_num += 1
                continue

            logger.info(f"{len(cards)} propiedades encontradas")
            consecutive_empty_pages = 0
            page_properties = 0

            for card in cards:
                property_data = extract_property_data(card)
                if property_data:
                    if not any(p['id'] == property_data.id for p in properties):
                        properties.append(property_data.model_dump())
                        page_properties += 1
                        logger.info(f"{len(properties)}. {property_data.title[:40]}... | {property_data.price}")
                time.sleep(random.uniform(0.1, 0.3))

            logger.info(f"Página {page_num}: {page_properties} nuevas")
            if len(properties) >= min_properties:
                break
            page_num += 1
            time.sleep(random.uniform(2, 4))

        browser.close()

    logger.info(f"Extracción finalizada. {len(properties)} propiedades de {page_num - 1} páginas")
    return properties

def save_properties_with_stats(properties, filename_base="data/assetplan_properties"):
    if not properties:
        logger.error("No hay propiedades para guardar")
        return None

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_base}_{timestamp}.json"
    stats = {
        "total_properties": len(properties),
        "extraction_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "locations": {},
        "property_types": {}
    }
    for prop in properties:
        location = prop.get('location', '').split(',')[-1].strip()
        stats["locations"][location] = stats["locations"].get(location, 0) + 1
        prop_type = prop.get('property_type', '')
        stats["property_types"][prop_type] = stats["property_types"].get(prop_type, 0) + 1

    output_data = {
        "stats": stats,
        "properties": properties
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Guardado en {filename}")
    return filename

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--min", type=int, default=50, help="Propiedades mínimas a extraer")
    parser.add_argument("--max", type=int, default=50, help="Páginas máximas a recorrer")
    args = parser.parse_args()

    props = scrape_assetplan_enhanced(min_properties=args.min, max_pages=args.max)
    file = save_properties_with_stats(props)

    if file:
        print(f"\nArchivo generado: {file}")
        print("Ahora puedes usar este archivo con el sistema RAG")
        print("Comando sugerido: python scripts/rag_chromadb.py --load")