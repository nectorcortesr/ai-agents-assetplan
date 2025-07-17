from fastapi import FastAPI
from pydantic import BaseModel
from llm.rag_agent import RAGAgent
from contextlib import asynccontextmanager
import os
import json
from glob import glob
import re
from datetime import datetime

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Carga las propiedades en ChromaDB al iniciar la aplicación si la base de datos está vacía."""
    if agent.vector_store.count() == 0:
        agent.load_properties()
        print("Properties loaded into ChromaDB at startup")
    yield

app = FastAPI(title="Assetplan Agent API", lifespan=lifespan)
agent = RAGAgent()

class QueryRequest(BaseModel):
    query: str

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/ask")
async def ask_question(request: QueryRequest):
    """Procesa una consulta y devuelve la respuesta generada por el agente."""
    response = agent.search_and_generate(request.query)
    return response

@app.get("/changes")
async def get_changes():
    """Devuelve los cambios detectados en los precios de las propiedades."""
    change_files = glob("data/changes_*.json")
    if not change_files:
        return {"changes": [], "message": "No se han detectado cambios"}
    def extract_dt(f: str):
        m = re.search(r'(\d{8}_\d{6})', f)
        return datetime.strptime(m.group(1), "%Y%m%d_%H%M%S") if m else datetime.min
    latest_changes = max(change_files, key=extract_dt)
    with open(latest_changes, 'r', encoding='utf-8') as f:
        changes = json.load(f)
    return {"changes": changes, "message": f"{len(changes)} cambios detectados", "file": latest_changes}