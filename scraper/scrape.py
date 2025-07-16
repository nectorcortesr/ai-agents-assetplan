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