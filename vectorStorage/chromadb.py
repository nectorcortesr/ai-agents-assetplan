import chromadb
from chromadb.config import Settings

class ChromaDBStore:
    def __init__(self, collection_name="assetplan_collection", db_path="./chroma_db"):
        self.client = chromadb.PersistentClient(path=db_path, settings=Settings())
        try:
            self.collection = self.client.get_collection(collection_name)
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )

    def add_documents(self, documents, embeddings, metadatas, ids):
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

    def query(self, query_embedding, n_results=5):
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results["documents"][0], results["metadatas"][0]

    def count(self):
        return self.collection.count()