import json
import os
import logging
import re

from typing import List, Dict, Any
from glob import glob
from datetime import datetime

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from langchain.chat_models import ChatOpenAI
from vectorStorage.chromadb import ChromaDBStore

# Carga las variables de entorno (OPENAI_API_KEY, etc.)
load_dotenv()

# Configuración de logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

class OpenAILLM(ChatOpenAI):
    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0.7, **kwargs):
        super().__init__(
            model_name=model_name,
            temperature=temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            **kwargs
        )

class RAGAgent:
    def __init__(self, db_path: str = "./chroma_db", json_file: str = None):
        self.db_path = db_path
        self.vector_store = ChromaDBStore(collection_name="property_listings", db_path=db_path)
        self.embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        self.json_file = json_file or self._get_latest_json_file()
        self.properties = self._load_json_properties()

    def _get_latest_json_file(self) -> str:
        """Encuentra el JSON más reciente en data/ con timestamp en el nombre."""
        json_files = glob("data/assetplan_properties_*.json")
        if not json_files:
            raise FileNotFoundError("No se encontró ningún archivo JSON en la carpeta 'data/'")
        def extract_dt(f: str):
            m = re.search(r'(\d{8}_\d{6})', f)
            return datetime.strptime(m.group(1), "%Y%m%d_%H%M%S") if m else datetime.min
        latest = max(json_files, key=extract_dt)
        logger.info(f"Usando el archivo más reciente: {latest}")
        return latest

    def _load_json_properties(self) -> List[Dict[str, Any]]:
        """Carga el contenido del JSON en memoria."""
        if not os.path.exists(self.json_file):
            logger.error(f"JSON no encontrado: {self.json_file}")
            return []
        with open(self.json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"{len(data)} propiedades cargadas desde {self.json_file}")
        return data

    def _create_document(self, prop: Dict[str, Any]) -> str:
        """Convierte un diccionario de propiedad en un string para embedding."""
        parts = [
            f"Title: {prop.get('title','')}",
            f"Location: {prop.get('location','')}"
        ]
        for typ in prop.get('typologies', []):
            segment = (
                f"{typ.get('bedrooms','')} | {typ.get('bathrooms','')} | "
                f"{typ.get('size_range','')} | {typ.get('price_range','')} | "
                f"Disponibles: {typ.get('available','')}"
            )
            promos = typ.get('promotions', [])
            if promos:
                segment += " | Promociones: " + ", ".join(promos)
            parts.append(segment)
        if prop.get('url'):
            parts.append(f"Link: {prop['url']}")
        return "\n".join(parts)

    def load_properties(self):
        """Indexa todas las propiedades en ChromaDB."""
        docs, metas, ids = [], [], []
        for prop in self.properties:
            doc = self._create_document(prop)
            docs.append(doc)
            metas.append({
                "id": prop.get("id"),
                "title": prop.get("title"),
                "location": prop.get("location"),
                "url": prop.get("url")
            })
            ids.append(str(prop.get("id")))
        if docs:
            embeddings = self.embedder.encode(docs).tolist()
            self.vector_store.add_documents(docs, embeddings, metas, ids)
            logger.info(f"{len(docs)} propiedades indexadas")

    def search_and_generate(self, query: str, n: int = 5) -> str:
        """Realiza la búsqueda semántica y genera la respuesta con el LLM."""
        # 1) Embed la query
        query_emb = self.embedder.encode(query).tolist()
        # 2) Recupera top-n documentos
        docs, metas = self.vector_store.query(query_emb, n_results=n)
        # 3) Construye el contexto
        context = ""
        for i, (doc, meta) in enumerate(zip(docs, metas), start=1):
            context += (
                f"[{i}] {meta.get('title')} - {meta.get('location')}\n"
                f"{doc}\nURL: {meta.get('url')}\n\n"
            )
        # 4) Construye el prompt
        prompt = (
            "Responde a la siguiente pregunta basándote exclusivamente en las propiedades listadas más abajo. "
            "Por cada propiedad que menciones, incluye el link (URL) original al final del párrafo. "
            f"Pregunta: {query}\n\nPropiedades disponibles:\n\n{context}"
        )
        # 5) Llamada al LLM
        llm = OpenAILLM()
        response = llm.invoke(prompt)
        return response.content
