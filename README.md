# InsightDesk — Agentic Customer Support

This project implements the InsightDesk use case using Python, FastAPI, LangChain, LangGraph-style orchestration, and ChromaDB with sentence-transformer embeddings.

## Features
- `POST /process` for customer support questions
- `GET /health` liveness check
- `GET /docs/{doc_id}` to read ingested content
- `POST /ingest` to load synthetic support docs and ticket resolutions into ChromaDB
- LangGraph-style multi-agent flow with intent, retrieval, answer composition, critic, and escalation
- Mock tools and structured output for safety and escalation

## Tech Stack
- Python 3.11+
- FastAPI + Uvicorn
- LangChain + LangGraph-style flow
- ChromaDB embedded vector store
- sentence-transformers/all-MiniLM-L6-v2 embeddings
- Pydantic v2
- Docker + docker-compose

## Quick start

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Generate the demo knowledge corpus:

```bash
python app/rag/generate_data.py
```

Ingest the corpus:

```bash
python -m app.rag.ingest
```

Run the API:

```bash
uvicorn app.main:app --reload
```

## API endpoints

- `GET /health` — returns service health
- `POST /process` — process a customer support query through the LangGraph-style agent pipeline
- `GET /docs/{doc_id}` — fetch an ingested document by its id
- `POST /ingest` — ingest synthetic docs and tickets into the vector store

### API payloads

`POST /process`

Request:
```json
{
  "query": "How do I export my data?",
  "user_id": "user-123"
}
```
```json
{
  "query": "How do I upgrade from Free to Pro?",
  "user_id": "user-123"
}
```

Response:
```json
{
  "trace_id": "...",
  "response": {
    "success": true,
    "text": "...",
    "citations": [
      {"doc_id": "doc-1", "score": 0.8, "excerpt": "..."}
    ],
    "escalate": false,
    "escalation_packet": null
  }
}
```

### Sample calls

```bash
curl http://127.0.0.1:8000/health
```

```bash
curl -X POST http://127.0.0.1:8000/ingest
```

```bash
curl -X POST http://127.0.0.1:8000/process \
  -H "Content-Type: application/json" \
  -d '{"query":"How do I export my data?", "user_id":"user-123"}'
```

```bash
curl http://127.0.0.1:8000/docs/doc-1
```

## Docker

```bash
docker compose up --build
```

## Notes

The pipeline uses a LangGraph-style orchestrator with:
- Intent classification
- RAG retrieval
- Answer composition
- Self-critique and escalation

The `CHROMA_PERSIST_DIR` environment variable can be set to control persistence.
