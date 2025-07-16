import json
import os
from glob import glob
from datetime import datetime

def test_scraper_output_exists():
    json_files = glob("data/assetplan_properties_*.json")
    assert json_files, "No se encontró ningún archivo JSON en la carpeta 'data/'"
    latest_file = max(json_files, key=lambda x: datetime.strptime('_'.join(x.split('_')[-2:]).split('.')[0], "%Y%m%d_%H%M%S"))
    assert os.path.exists(latest_file), f"No se encontró el archivo JSON más reciente: {latest_file}"

def test_scraper_minimum_properties():
    json_files = glob("data/assetplan_properties_*.json")
    assert json_files, "No se encontró ningún archivo JSON en la carpeta 'data/'"
    latest_file = max(json_files, key=lambda x: datetime.strptime('_'.join(x.split('_')[-2:]).split('.')[0], "%Y%m%d_%H%M%S"))
    with open(latest_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list), "El JSON no contiene una lista de propiedades."
    assert len(data) >= 50, f"Se esperaban al menos 50 propiedades, pero se encontraron {len(data)}."