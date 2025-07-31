import os
import logging
from glob import glob
from typing import List, Dict, Any

import fitz  # PyMuPDF
import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chat_models import ChatOpenAI
from sentence_transformers import SentenceTransformer
from langdetect import detect
from dotenv import load_dotenv

from vectorStorage.chromadb import ChromaDBStore

# Carga las variables de entorno (OPENAI_API_KEY, etc.)
load_dotenv()

# Configuración de logging
debug_level = logging.INFO
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=debug_level)
logger = logging.getLogger(__name__)

class OpenAILLM(ChatOpenAI):
    def __init__(
        self,
        model_name: str = "gpt-4o",
        temperature: float = 0.7,
        **kwargs
    ):
        super().__init__(
            model_name=model_name,
            temperature=temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            **kwargs
        )

class RAGAgent:
    def __init__(
        self,
        db_path: str = "./chroma_db",
        pdf_dir: str = "data/pdfs",
        excel_dir: str = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        """
        Inicializa el agente RAG construyendo o cargando la base de datos vectorial
        y partiendo cada documento en 'chunks'.
        """
        self.vector_store = ChromaDBStore(
            collection_name="pdf_excel_collection",
            db_path=db_path
        )
        self.embedder = SentenceTransformer(
            "paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        # Carga de documentos
        pdf_docs, pdf_metas, pdf_ids = self._load_pdfs(pdf_dir)
        if excel_dir:
            excel_docs, excel_metas, excel_ids = self._load_excels(excel_dir)
        else:
            excel_docs, excel_metas, excel_ids = [], [], []
        self.documents = pdf_docs + excel_docs
        self.metadatas = pdf_metas + excel_metas
        self.ids = pdf_ids + excel_ids

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        doc = fitz.open(pdf_path)
        return "".join(page.get_text() for page in doc)

    def _load_pdfs(self, pdf_dir: str):
        docs, metas, ids = [], [], []
        paths = glob(os.path.join(pdf_dir, "*.pdf"))
        if not paths:
            logger.warning(f"No se encontraron PDF en {pdf_dir}")
        for path in paths:
            filename = os.path.basename(path)
            text = self._extract_text_from_pdf(path)
            chunks = self.text_splitter.split_text(text)
            for idx, chunk in enumerate(chunks):
                docs.append(chunk)
                metas.append({"source": filename, "chunk_index": idx})
                ids.append(f"{filename}_chunk{idx}")
        logger.info(f"{len(docs)} chunks extraídos de {len(paths)} PDFs.")
        return docs, metas, ids

    def _load_excel(self, excel_path: str) -> List[str]:
        df_dict = pd.read_excel(excel_path, sheet_name=None)
        rows = []
        for sheet, df in df_dict.items():
            for _, row in df.iterrows():
                rows.append(" | ".join(f"{col}: {row[col]}" for col in df.columns))
        return rows

    def _load_excels(self, excel_dir: str):
        docs, metas, ids = [], [], []
        paths = glob(os.path.join(excel_dir, "*.xlsx"))
        if not paths:
            logger.warning(f"No se encontraron Excel en {excel_dir}")
        for path in paths:
            filename = os.path.basename(path)
            for row_idx, text in enumerate(self._load_excel(path)):
                chunks = self.text_splitter.split_text(text)
                for chunk_idx, chunk in enumerate(chunks):
                    docs.append(chunk)
                    metas.append({
                        "source": filename,
                        "row_index": row_idx,
                        "chunk_index": chunk_idx
                    })
                    ids.append(f"{filename}_row{row_idx}_chunk{chunk_idx}")
        logger.info(f"{len(docs)} chunks extraídos de {len(paths)} Excels.")
        return docs, metas, ids

    def load_into_vectorstore(self) -> None:
        """
        Indexa todos los documentos cargados en la base vectorial.
        """
        if not self.documents:
            logger.error("No hay documentos para indexar en vector_store.")
            return
        embeddings = self.embedder.encode(self.documents).tolist()
        self.vector_store.add_documents(
            documents=self.documents,
            embeddings=embeddings,
            metadatas=self.metadatas,
            ids=self.ids
        )
        logger.info(f"{len(self.documents)} documentos indexados en ChromaDB.")

    def search_and_generate(self, query: str, history: List[str] = [], n: int = 5) -> Dict[str, Any]:
        # Detección de idioma
        try:
            lang = detect(query)
        except:
            lang = "es"
        if lang not in ("es", "en"):
            lang = "es"
        # Obtener embedding y consulta a vector_store
        query_emb = self.embedder.encode(query).tolist()
        docs, metas, distances, ids = self.vector_store.query(query_emb, n_results=n)

        # Definir keywords de troubleshooting
        troubleshooting_keys = [
            "problema", "falla", "error", "no funciona", "mal funcionamiento",
            "qué pasa", "que pasa", "qué ocurre", "nivel no ideal", "nivel alto", "nivel bajo",
            "fuera de rango", "alarma", "alerta", "parado", "detenido",
            "bloqueo", "obstrucción", "rebalse", "derrame", "pérdida",
            "cambios de densidad", "cómo solucionar", "qué hacer", "que hacer",
            "reactor", "estanque", "bomba", "válvula"
        ]
        is_trouble = any(k in query.lower() for k in troubleshooting_keys)

        # Filtrar documentos (Excel rows si troubleshooting)
        sel_docs, sel_metas = [], []
        for doc, meta in zip(docs, metas):
            if is_trouble and 'row_index' in meta:
                sel_docs.append(doc)
                sel_metas.append(meta)
            elif not is_trouble:
                sel_docs.append(doc)
                sel_metas.append(meta)
        if not sel_docs:
            sel_docs, sel_metas = docs, metas

        # Construir contexto
        context = []
        for doc, meta in zip(sel_docs, sel_metas):
            label = f"[Fila {meta['row_index']}]" if 'row_index' in meta else f"[PDF chunk {meta['chunk_index']}]"
            context.append(f"{label} {doc}")
        context_str = "\n".join(context)

        # Construir prompt
        if is_trouble:
            system_prompt = (
                "Eres un asistente experto en troubleshooting industrial. "
                "Extrae y presenta EXACTAMENTE los campos de la tabla de riesgo "
                "(Síntomas, Causas, Consecuencias, Salvaguardas, Impacto, Probabilidad, "
                "Clasificación, Recomendación, Explicación, Responsable) sin resumir."
            )
        else:
            system_prompt = (
                "Eres un asistente experto en operaciones industriales. "
                "Responde concretamente basándote en la documentación disponible."
            )
        prompt = f"{system_prompt}\n\nContexto:\n{context_str}\n\nConsulta: {query}"

        llm = OpenAILLM()
        resp = llm.invoke(prompt)
        return {
            "answer": resp.content,
            "sources": "chromadb",
            "source_ids": [m.get('row_index', '') for m in sel_metas]
        }
