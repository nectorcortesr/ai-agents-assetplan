# Makefile para ejecutar scripts localmente usando uv

# Variables
PYTHONPATH := $(PYTHONPATH):$(shell pwd)
export PYTHONPATH

# Reglas
.PHONY: install scrape run test tests clean

# 1) Instalar dependencias usando pyproject.toml (asumiendo entorno ya creado y activado)
install:
	@echo "🛠️  Instalando dependencias con uv..."
	@uv pip install --upgrade pip
	@uv pip install -r pyproject.toml

# 2) Ejecutar scraper y guardar JSON
scrape:
	@echo "🕷️  Ejecutando scraper..."
	@python scraper/scrape.py --min 50 --max 50

# 3) Iniciar API localmente
run:
	@echo "🚀  Iniciando API local..."
	@uvicorn api.main:app --reload --host 127.0.0.1 --port 8000

# 4) Probar endpoint /ask (Arranque make apitest en otra terminal cuando tenga make run ejecutandose)
apitest:
	@echo "🔍  Probando endpoint /ask..."
	@curl -s -X POST http://127.0.0.1:8000/ask \
	    -H "Content-Type: application/json" \
	    -d '{"query":"Departamentos en Santiago con precio hasta $500.000"}' | jq .

# 5) Ejecutar suite de tests automáticos con pytest
tests:
	@echo "🧪 Ejecutando tests..."
	@pytest --maxfail=1 --disable-warnings -q

# 6) Limpiar entorno local
clean:
	@echo "🧹 Limpiando entorno local..."
	rm -rf .pytest_cache dist build __pycache__
