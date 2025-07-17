import json
import os
import re
from glob import glob
from datetime import datetime

def test_scraper_minimum_properties():
    """Prueba que el scraper extraiga al menos 50 propiedades."""
    json_files = glob("data/assetplan_properties_*.json")
    assert json_files, "No se encontró ningún archivo JSON en la carpeta 'data/'"
    def extract_dt(f: str):
        m = re.search(r'(\d{8}_\d{6})', f)
        return datetime.strptime(m.group(1), "%Y%m%d_%H%M%S") if m else datetime.min
    latest_file = max(json_files, key=extract_dt)
    with open(latest_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list), "El JSON no contiene una lista de propiedades"
    assert len(data) >= 50, f"Se esperaban al menos 50 propiedades, pero se encontraron {len(data)}"