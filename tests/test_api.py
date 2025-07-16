from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_query_response():
    payload = {"query": "Departamentos en Santiago con precio hasta $500.000"}
    response = client.post("/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert data["sources"] == "chromadb"
    assert data["confidence"] == "high"
    assert isinstance(data["answer"], str)