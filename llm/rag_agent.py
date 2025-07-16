from vectorStore.chromadb_store import ChromaDBStore
from sentence_transformers import SentenceTransformer

class RAGAgent:
    def __init__(self):
        self.vector_store = ChromaDBStore()
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

    def process_documents(self, documents):
        embeddings = self.embedder.encode(documents).tolist()
        self.vector_store.add_documents(documents, embeddings)

    def answer_query(self, query):
        query_embedding = self.embedder.encode(query).tolist()
        retrieved_docs = self.vector_store.query(query_embedding)
        # Aquí iría la lógica para combinar los documentos y generar una respuesta
        return "Respuesta basada en: " + " ".join(retrieved_docs)