import json
from llm.rag_agent import RAGAgent
from scraper.scrape import scrape_assetplan

def test_vector_store_insertion(tmp_path):
    """Prueba que las propiedades se inserten correctamente en ChromaDB."""
    json_file = str(tmp_path / "test_properties.json")
    listings = scrape_assetplan(min_props=1, max_pages=1)  # Limitar para la prueba
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump([l.model_dump() for l in listings], f)
    agent = RAGAgent(db_path=str(tmp_path), json_file=json_file)
    agent.load_properties()
    assert agent.vector_store.count() > 0, "No se insertaron documentos en ChromaDB"