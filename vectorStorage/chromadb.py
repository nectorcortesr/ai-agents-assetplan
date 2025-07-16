import chromadb
from chromadb.config import Settings

class ChromaDBStore:
    def __init__(self, collection_name="assetplan_collection"):
        self.client = chromadb.Client(Settings())
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_documents(self, documents, embeddings):
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=[f"doc_{i}" for i in range(len(documents))]
        )

    def query(self, query_embedding, n_results=5):
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results["documents"][0]