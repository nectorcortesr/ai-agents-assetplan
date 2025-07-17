# 🏠 Agente Conversacional Assetplan: Scraper + LangChain + FastAPI

Este proyecto implementa un **Agente Conversacional** inteligente para responder preguntas sobre propiedades publicadas en [Assetplan.cl](https://www.assetplan.cl). Combina scraping, generación de embeddings semánticos, búsqueda vectorial, y un modelo de lenguaje natural para entregar respuestas relevantes con fuentes citadas.

> ⏱️ **Desafío técnico**: solución instalable en menos de 60 segundos y capaz de responder preguntas en lenguaje natural sobre propiedades en venta o arriendo.

---

## 🧠 Tecnologías Utilizadas

- **Playwright**: para scraping automático y robusto.
- **LangChain** `>= 0.3`: framework para construir agentes conversacionales con LLMs.
- **OpenAI GPT-4o**: modelo de lenguaje optimizado para velocidad y costo.
- **ChromaDB**: almacenamiento vectorial embebido y eficiente.
- **SentenceTransformers**: generación de embeddings multilingües.
- **FastAPI**: servidor web para exponer la API REST.
- **uv**: gestor de entornos y dependencias ultrarrápido (reemplazo moderno de pip/venv).
- **Docker**: para contenerizar y ejecutar scraping y API fácilmente.

---

## 🚀 Características

- 🔎 **Scraping automatizado** de más de 50 propiedades desde `assetplan.cl`.
- 🧠 **Indexación semántica** en una base vectorial local (ChromaDB).
- 🤖 **Agente RAG** (Retrieval-Augmented Generation) con LangChain que responde preguntas en lenguaje natural.
- 🔗 **Cita fuentes** con URLs de propiedades relevantes.
- 🧪 **Pruebas automáticas** para scraping, vectorización y consulta.
- 🛠️ Soporte completo para ejecución vía `make` y/o Docker Compose.

---

assetplan-agent/
├── api/ # API REST con FastAPI
├── scraper/ # Web scraper con Playwright
├── vectorStorage/ # Módulo de almacenamiento ChromaDB
├── llm/ # Lógica de embeddings, recuperación y generación
├── tests/ # Pruebas automáticas
├── data/ # Archivos JSON generados por el scraper
├── Dockerfile # Imagen para API y scraper
├── docker-compose.yml # Orquestación de servicios
├── Makefile # Comandos para desarrollo local
├── .env # Variables de entorno
├── pyproject.toml # Configuración y dependencias del proyecto
└── README.md # Este archivo

---

## ⚙️ Requisitos Previos

- Python `>=3.12`
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Docker + Docker Compose](https://docs.docker.com/get-docker/)
- Clave de API de OpenAI (`OPENAI_API_KEY`)

---

## 🔐 Configuración del archivo .env

Antes de ejecutar el proyecto, asegúrate de crear un archivo .env en la raíz del repositorio con el siguiente contenido:

```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Reemplaza sk-xxxxxxxx... con tu clave real obtenida desde https://platform.openai.com/account/api-keys.

---

## 🛠️ Instalación y Uso

### 🔧 Opción 1: Local con `uv`

```bash
# 1. Clona el repositorio
git clone hhttps://github.com/nectorcortesr/ai-agents-assetplan.git
cd ai-agents-assetplan

# 2. Crea y activa el entorno
uv venv .venv
source .venv/bin/activate

# 3. Instala las dependencias
make install

# 4. Ejecuta el scraper (requiere Chromium headless)
make scrape

# 5. Inicia la API
make run

# 6. (En otra terminal) Prueba una consulta
make apitest

# 7. Limpiar entorno local
make clean
```

### 🔧 Opción 2: Docker

```bash
# Ejecutar comando para el build (instalación de librerías, dependencias y levantar entorno)
docker compose build

# Ejecutar comando para levantar proyecto (scraper y API)
docker compose up
```
---

## 🌐 Uso de la API vía Navegador o HTTP

Una vez que la API esté corriendo (make run o docker compose up), accede desde tu navegador a:

🔗 http://localhost:8000/docs

    Se abrirá la documentación automática (Swagger UI) de FastAPI.

    Busca el endpoint: POST /ask.

    Haz clic en "Try it out" y completa el campo query con una pregunta. Por ejemplo:

    {
        "query": "¿Qué departamentos de 2 dormitorios hay en Providencia por menos de 3000 UF?"
    }

    Haz clic en "Execute" y espera la respuesta del agente, que incluirá:

        Una descripción en lenguaje natural.

        Enlaces (URLs) a propiedades relevantes.

También puedes consumir el endpoint con herramientas como curl, Postman o Insomnia.

---

## 🧪 Pruebas unitarias

```bash
# Ejecutar test automaticos
make tests

```
---

## Diagrama 

graph TD
    A[Scraper (Playwright)] --> B[JSON con propiedades]
    B --> C[Embeddings (SentenceTransformers)]
    C --> D[ChromaDB (Vector Store)]
    E[Usuario] --> F[Pregunta /ask]
    F --> G[LangChain + GPT-4o]
    D --> G
    G --> H[Respuesta con citas y URLs]

---

## 📄 Licencia

MIT. Puedes usar, modificar y distribuir libremente este proyecto.
