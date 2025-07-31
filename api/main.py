import os
import logging

from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager

from llm.rag_agent import RAGAgent
from vectorStorage.chromadb import ChromaDBStore

# Configuración logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# Inicializar agente
agent = RAGAgent(pdf_dir="data/pdfs", excel_dir="data/excels")

@asynccontextmanager
async def lifespan(app: FastAPI):
    if agent.vector_store.count() == 0:
        agent.load_into_vectorstore()
        logging.info("⚡ PDFs y Excels indexados en ChromaDB al iniciar")
    else:
        logging.info("✅ Vector store ya contiene datos, no se vuelve a indexar")
    yield

app = FastAPI(
    title="PDF‑RAG Agent API",
    lifespan=lifespan
)

# 🧠 Definición del modelo con history incluido
class QueryRequest(BaseModel):
    query: str
    history: list[str] = []

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/ask")
async def ask(request: QueryRequest):
    # 💬 Llamada con historial incluido
    return agent.search_and_generate(request.query, request.history)
