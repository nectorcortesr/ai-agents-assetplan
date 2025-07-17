from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

#Prueba que el endpoint /ask responda correctamente a una consulta en español sobre departamentos en Santiago.
def test_query_response_santiago():
    payload = {"query": "Departamentos en Santiago con precio hasta $500.000"}
    response = client.post("/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data, "La respuesta debe incluir 'answer'"
    assert "sources" in data, "La respuesta debe incluir 'sources'"
    assert "confidence" in data, "La respuesta debe incluir 'confidence'"
    assert "urls" in data, "La respuesta debe incluir 'urls'"
    assert "source_ids" in data, "La respuesta debe incluir 'source_ids'"
    assert data["sources"] == "chromadb", "Sources debe ser 'chromadb'"
    assert isinstance(data["urls"], list), "Urls debe ser una lista"
    assert all(isinstance(url, str) and url.startswith("https://") for url in data["urls"]), "Urls deben ser URLs válidas"
    assert isinstance(data["source_ids"], list), "Source_ids debe ser una lista"
    assert all(isinstance(id, str) for id in data["source_ids"]), "Source_ids deben ser cadenas"
    assert len(data["source_ids"]) == len(data["urls"]), "El número de source_ids debe coincidir con el número de urls"
    assert isinstance(data["answer"], str), "Answer debe ser una cadena"
    assert data["answer"] != "", "La respuesta no debe estar vacía"
    assert data["confidence"] in ["high", "medium", "low"], "Confidence debe ser 'high', 'medium' o 'low'"
    assert any("Santiago" in data["answer"] or url.endswith("santiago") for url in data["urls"]), "La respuesta debe mencionar propiedades en Santiago"

#Prueba que el endpoint /ask responda correctamente a una consulta en español sobre departamentos en Santiago.
def test_query_response_santiago():
    payload = {"query": "¿Qué departamentos de 2 dormitorios hay en Santiago bajo $500.000?"}
    response = client.post("/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data, "La respuesta debe incluir 'answer'"
    assert "sources" in data, "La respuesta debe incluir 'sources'"
    assert "confidence" in data, "La respuesta debe incluir 'confidence'"
    assert "urls" in data, "La respuesta debe incluir 'urls'"
    assert "source_ids" in data, "La respuesta debe incluir 'source_ids'"
    assert data["sources"] == "chromadb", "Sources debe ser 'chromadb'"
    assert isinstance(data["urls"], list), "Urls debe ser una lista"
    assert all(isinstance(url, str) and url.startswith("https://") for url in data["urls"]), "Urls deben ser URLs válidas"
    assert isinstance(data["source_ids"], list), "Source_ids debe ser una lista"
    assert all(isinstance(id, str) for id in data["source_ids"]), "Source_ids deben ser cadenas"
    assert len(data["source_ids"]) == len(data["urls"]), "El número de source_ids debe coincidir con el número de urls"
    assert isinstance(data["answer"], str), "Answer debe ser una cadena"
    assert data["answer"] != "", "La respuesta no debe estar vacía"
    assert data["confidence"] in ["high", "medium", "low"], "Confidence debe ser 'high', 'medium' o 'low'"
    assert any("Santiago" in data["answer"] or url.endswith("santiago") for url in data["urls"]), "La respuesta debe mencionar propiedades en Santiago"
    assert "2 dormitorios" in data["answer"] or "2 bedroom" in data["answer"], "La respuesta debe mencionar 2 dormitorios"

# Prueba que el endpoint /ask responda correctamente a una consulta en inglés.
def test_query_response_english():
    payload = {"query": "What 2-bedroom apartments are available in Santiago under $500.000?"}
    response = client.post("/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data, "La respuesta debe incluir 'answer'"
    assert "sources" in data, "La respuesta debe incluir 'sources'"
    assert "confidence" in data, "La respuesta debe incluir 'confidence'"
    assert "urls" in data, "La respuesta debe incluir 'urls'"
    assert "source_ids" in data, "La respuesta debe incluir 'source_ids'"
    assert data["sources"] == "chromadb", "Sources debe ser 'chromadb'"
    assert isinstance(data["urls"], list), "Urls debe ser una lista"
    assert all(isinstance(url, str) and url.startswith("https://") for url in data["urls"]), "Urls deben ser URLs válidas"
    assert isinstance(data["source_ids"], list), "Source_ids debe ser una lista"
    assert all(isinstance(id, str) for id in data["source_ids"]), "Source_ids deben ser cadenas"
    assert len(data["source_ids"]) == len(data["urls"]), "El número de source_ids debe coincidir con el número de urls"
    assert isinstance(data["answer"], str), "Answer debe ser una cadena"
    assert data["answer"] != "", "La respuesta no debe estar vacía"
    assert data["confidence"] in ["high", "medium", "low"], "Confidence debe ser 'high', 'medium' o 'low'"
    assert any("Santiago" in data["answer"] or url.endswith("santiago") for url in data["urls"]), "La respuesta debe mencionar propiedades en Santiago"
    assert any(s in data["answer"].lower() for s in ["2 bedroom", "2 dormitorios", "2-bedroom"]), "La respuesta debe mencionar 2 dormitorios"
