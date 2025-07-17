import chromadb
from chromadb.config import Settings

# Clase que maneja el almacenamiento y consulta de vectores en ChromaDB
class ChromaDBStore:
    def __init__(self, collection_name="assetplan_collection", db_path="./chroma_db"):
        # Inicializa un cliente persistente de ChromaDB en el path especificado
        self.client = chromadb.PersistentClient(path=db_path, settings=Settings())
        try:
            self.collection = self.client.get_collection(collection_name)
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )

    # Método para agregar documentos al vector store
    def add_documents(self, documents, embeddings, metadatas, ids):
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

    # Método para consultar documentos similares a un embedding dado
    def query(self, query_embedding, n_results=5):
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        return (
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
            results["ids"][0]
        )

    # Método que retorna la cantidad total de documentos en la colección
    def count(self):
        return self.collection.count()