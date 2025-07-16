from fastapi import FastAPI
from pydantic import BaseModel
from llm.rag_agent import RAGAgent

app = FastAPI(title="Assetplan Agent API")
agent = RAGAgent()

class QueryRequest(BaseModel):
    query: str

@app.on_event("startup")
async def startup_event():
    """Carga las propiedades en ChromaDB al iniciar la aplicación si la base de datos está vacía."""
    if agent.vector_store.count() == 0:
        agent.load_properties()
        print("Properties loaded into ChromaDB at startup")

@app.post("/ask")
async def ask_question(request: QueryRequest):
    """Procesa una consulta y devuelve la respuesta generada por el agente."""
    response = agent.search_and_generate(request.query)
    return {
        "answer": response,
        "sources": "chromadb",
        "confidence": "high"
    }