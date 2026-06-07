"""Ingest data into the KnowledgeAgent (ChromaDB optional)."""
import json
import os
from pathlib import Path
from .generate_data import OUT_DIR
from ..agents.knowledge_agent import KnowledgeAgent


def load(path):
    with open(path, encoding="utf8") as f:
        return json.load(f)


def ingest_agent(agent: KnowledgeAgent) -> int:
    docs_path = Path(OUT_DIR) / "docs.json"
    tickets_path = Path(OUT_DIR) / "tickets.json"

    if not docs_path.exists():
        return 0

    docs = load(docs_path)
    tickets = load(tickets_path) if tickets_path.exists() else []
    docs_ext = docs + [
        {"id": t["id"], "title": t["customer_question"], "content": t["resolution"], "source": "ticket"}
        for t in tickets
    ]
    agent.ingest(docs_ext)
    return len(docs_ext)


if __name__ == "__main__":
    agent = KnowledgeAgent()
    count = ingest_agent(agent)
    print(f"Ingested {count} docs into knowledge agent.")
