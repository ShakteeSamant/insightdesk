"""Knowledge (RAG) agent.

Responsible for ingestion and retrieval using ChromaDB and sentence-transformers.
"""
from typing import List, Dict, Optional
import os
import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from ..models import RetrievalItem, Doc
from ..utils import register_doc


class KnowledgeAgent:
    def __init__(self, persist_dir: Optional[str] = None):
        self._persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
        os.makedirs(self._persist_dir, exist_ok=True)
        self._docs: Dict[str, Doc] = {}
        self._embedder = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self._client = chromadb.Client(Settings(persist_directory=self._persist_dir))
        self._collection = self._client.get_or_create_collection(
            name="insightdesk",
            embedding_function=self._embedder,
        )

    def ingest(self, docs: List[Dict]):
        ids = []
        texts = []
        metadatas = []
        for d in docs:
            doc = Doc(**d)
            self._docs[doc.id] = doc
            register_doc(doc.model_dump())
            ids.append(doc.id)
            texts.append(doc.content)
            metadatas.append({"id": doc.id, "title": doc.title, "source": doc.source})

        if ids:
            try:
                self._collection.delete(ids=ids)
            except Exception:
                pass
            self._collection.add(documents=texts, metadatas=metadatas, ids=ids)

    def retrieve(self, query: str, top_k: int = 3) -> List[RetrievalItem]:
        if not self._docs:
            return []
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=top_k,
                # include=["metadatas", "distances", "ids"],
            )
        except Exception:
            return []

        citations = []
        for doc_id, distance, metadata in zip(results["ids"][0], results["distances"][0], results["metadatas"][0]):
            excerpt = self._docs.get(doc_id).content[:200] if doc_id in self._docs else ""
            citations.append(RetrievalItem(doc_id=doc_id, score=float(distance), excerpt=excerpt))
        return citations

    def get_doc(self, doc_id: str):
        doc = self._docs.get(doc_id)
        return doc.dict() if doc else None
