"""Knowledge (RAG) agent.

Responsible for ingestion and retrieval using ChromaDB and sentence-transformers.

The vector store is persisted to disk (``CHROMA_PERSIST_DIR``) via a
``PersistentClient`` so embeddings survive process restarts. Retrieval returns a
normalised *relevance score* in the ``(0, 1]`` range where **higher is better**
(ChromaDB natively reports a distance where lower is better, so we convert it).
"""
from typing import Dict, List, Optional

import os

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from ..models import Doc, RetrievalItem
from ..utils import register_doc

EXCERPT_LENGTH = 200


def _distance_to_score(distance: float) -> float:
    """Convert a ChromaDB distance (lower = better) to a relevance score.

    Returns a value in ``(0, 1]`` where ``1.0`` is a perfect match. Using
    ``1 / (1 + distance)`` keeps the score strictly positive and monotonically
    decreasing in distance, which is what downstream consumers expect.
    """
    return 1.0 / (1.0 + max(distance, 0.0))


class KnowledgeAgent:
    def __init__(self, persist_dir: Optional[str] = None):
        self._persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
        os.makedirs(self._persist_dir, exist_ok=True)
        self._docs: Dict[str, Doc] = {}
        self._embedder = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        # PersistentClient writes the collection to disk so it survives restarts.
        self._client = chromadb.PersistentClient(path=self._persist_dir)
        self._collection = self._client.get_or_create_collection(
            name="insightdesk",
            embedding_function=self._embedder,
            metadata={"hnsw:space": "cosine"},
        )

    def ingest(self, docs: List[Dict]) -> int:
        """Upsert ``docs`` into the vector store. Returns the number ingested."""
        ids, texts, metadatas = [], [], []
        for d in docs:
            doc = Doc(**d)
            self._docs[doc.id] = doc
            register_doc(doc.model_dump())
            ids.append(doc.id)
            texts.append(doc.content)
            metadatas.append({"id": doc.id, "title": doc.title, "source": doc.source or ""})

        if ids:
            # upsert is idempotent: re-ingesting the same ids overwrites them.
            self._collection.upsert(documents=texts, metadatas=metadatas, ids=ids)
        return len(ids)

    def retrieve(self, query: str, top_k: int = 3) -> List[RetrievalItem]:
        if self._collection.count() == 0:
            return []

        n_results = min(top_k, self._collection.count())
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            return []

        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        documents = results.get("documents", [[]])[0]

        citations: List[RetrievalItem] = []
        for doc_id, distance, document in zip(ids, distances, documents):
            # Prefer the in-memory copy (full content) but fall back to the text
            # stored in Chroma so retrieval still works after a restart.
            cached = self._docs.get(doc_id)
            content = cached.content if cached else (document or "")
            citations.append(
                RetrievalItem(
                    doc_id=doc_id,
                    score=_distance_to_score(float(distance)),
                    excerpt=content[:EXCERPT_LENGTH],
                )
            )
        return citations

    def get_doc(self, doc_id: str) -> Optional[dict]:
        doc = self._docs.get(doc_id)
        if doc:
            return doc.model_dump()

        # Fall back to the persisted collection if the doc is not in memory.
        try:
            stored = self._collection.get(ids=[doc_id], include=["documents", "metadatas"])
        except Exception:
            return None
        if not stored.get("ids"):
            return None
        metadata = (stored.get("metadatas") or [{}])[0] or {}
        content = (stored.get("documents") or [""])[0] or ""
        return {
            "id": doc_id,
            "title": metadata.get("title", doc_id),
            "content": content,
            "source": metadata.get("source") or None,
        }
