from llm.rag_agent import RAGAgent

def test_vectorstore_insertion():
    rag = RAGAgent()
    rag.load_properties()
    count = rag.vector_store.count()
    assert count >= 50, f"Se esperaban al menos 50 documentos indexados, pero se encontraron {count}."