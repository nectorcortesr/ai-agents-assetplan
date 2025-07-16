import json
import os
import logging
import argparse
import re

from typing import List, Dict, Any

from sentence_transformers import SentenceTransformer
from langchain.chat_models import ChatOpenAI
from vectorStorage.chromadb import ChromaDBStore

from glob import glob
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

class OpenAILLM(ChatOpenAI):
    def __init__(self, model_name="gpt-3.5-turbo", temperature=0.7, **kwargs):
        super().__init__(
            model_name=model_name,
            temperature=temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            **kwargs
        )

class RAGAgent:
    def __init__(self, db_path="./chroma_db", json_file=None):
        self.db_path = db_path
        self.properties = []
        self.vector_store = ChromaDBStore(collection_name="property_listings", db_path=db_path)
        self.embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        self.json_file = json_file or self._get_latest_json_file()
        self._load_json_properties()

    def _get_latest_json_file(self):
        json_files = glob("data/assetplan_properties_*.json")
        if not json_files:
            raise FileNotFoundError("❌ No se encontró ningún archivo JSON en la carpeta 'data/'")
        def extract_dt(f):
            m = re.search(r'(\d{8}_\d{6})', f)
            return datetime.strptime(m.group(1), "%Y%m%d_%H%M%S") if m else datetime.min
        latest = max(json_files, key=extract_dt)
        logger.info(f"📂 Usando el archivo más reciente: {latest}")
        return latest

    def _load_json_properties(self):
        if not os.path.exists(self.json_file):
            logger.error(f"❌ JSON no encontrado: {self.json_file}")
            return
        with open(self.json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # new JSON is a list of listings
        self.properties = data
        logger.info(f"📑 {len(self.properties)} propiedades cargadas desde {self.json_file}")

    def _create_document(self, prop: Dict[str, Any]) -> str:
        # Summarize main fields
        parts = [f"Title: {prop.get('title', '')}", f"Location: {prop.get('location', '')}"]
        # Include each typology as a bullet
        for typ in prop.get('typologies', []):
            t = (
                f"{typ.get('bedrooms','')} | {typ.get('bathrooms','')} | "
                f"{typ.get('size_range','')} | {typ.get('price_range','')} | "
                f"Disponibles: {typ.get('available','')}"
            )
            promos = typ.get('promotions', [])
            if promos:
                t += " | Promociones: " + ", ".join(promos)
            parts.append(t)
        if prop.get('url'):
            parts.append(f"Link: {prop['url']}")
        return "\n".join(parts)

    def load_properties(self):
        docs, metas, ids = [], [], []
        for prop in self.properties:
            text = self._create_document(prop)
            metas.append({
                "id": prop.get("id"),
                "title": prop.get("title"),
                "location": prop.get("location"),
                "url": prop.get("url")
            })
            docs.append(text)
            ids.append(str(prop.get("id")))
        if docs:
            embeddings = self.embedder.encode(docs).tolist()
            self.vector_store.add_documents(docs, embeddings, metas, ids)
            logger.info(f"✅ {len(docs)} propiedades indexadas")

    def search_and_generate(self, query: str, n: int = 5) -> str:
        query_emb = self.embedder.encode(query).tolist()
        docs, metas = self.vector_store.query(query_emb, n_results=n)
        context = ""
        for i, (doc, meta) in enumerate(zip(docs, metas), 1):
            context += f"[{i}] {meta.get('title')} - {meta.get('location')}\n{doc}\nURL: {meta.get('url')}\n\n"
        prompt = (
            "Responde a la siguiente pregunta basándote exclusivamente en las propiedades listadas más abajo. "
            "Por cada propiedad que menciones, incluye el link (URL) original al final del párrafo. "
            f"Pregunta: {query}\n\nPropiedades disponibles:\n\n{context}"
        )
        llm = OpenAILLM()
        res = llm.invoke(prompt)
        return res.content

    def cli(self, args):
        if self.vector_store.count() == 0 or args.load:
            self.load_properties()
            print("📊 Indexación completada.")
        query = args.query or input("🔍 Ingresa tu consulta: ")
        print(self.search_and_generate(query, n=args.n))

if __name__ == "__main__":
    p = argparse.ArgumentParser("RAG Agent")
    p.add_argument("--load", action="store_true")
    p.add_argument("--query", type=str)
    p.add_argument("--n", type=int, default=5)
    p.add_argument("--json_file", type=str)
    args = p.parse_args()
    agent = RAGAgent(json_file=args.json_file)
    agent.cli(args)
