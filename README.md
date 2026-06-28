# InsightDesk — Agentic Customer Support

This project implements the InsightDesk use case using Python, FastAPI, a real
LangGraph `StateGraph` orchestration, and ChromaDB with sentence-transformer
embeddings. A Streamlit front-end provides a browser UI on top of the API.

## Features
- `POST /process` for customer support questions
- `GET /health` liveness check
- `GET /docs/{doc_id}` to read ingested content
- `POST /ingest` to load synthetic support docs and ticket resolutions into ChromaDB
- LangGraph multi-agent flow with intent, retrieval, answer composition, critic, and escalation
- High-urgency tickets are routed straight to human escalation, skipping retrieval/composition
- Mock tools and structured Pydantic output for safety and escalation
- Persistent ChromaDB vector store (survives restarts)

## Tech Stack
- Python 3.11+
- FastAPI + Uvicorn
- LangGraph (`StateGraph`) orchestration
- ChromaDB persistent vector store
- sentence-transformers/all-MiniLM-L6-v2 embeddings
- Pydantic v2
- Streamlit UI
- Docker + docker-compose

## Configuration

Copy `.env.example` to `.env` and adjust as needed. The backend loads it on
startup via `python-dotenv`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `MOCK_LLM` | `true` | When true, the answer composer uses a deterministic mock instead of calling OpenAI. |
| `OPENAI_API_KEY` | — | Required only when `MOCK_LLM=false`. |
| `OPENAI_MODEL` | `gpt-3.5-turbo` | Model used in real-LLM mode. |
| `CHROMA_PERSIST_DIR` | `./data/chroma` | On-disk location of the vector store. |
| `RAG_DATA_DIR` | `./data` | Folder containing `docs.json` / `tickets.json`. |
| `CRITIC_MIN_SCORE` | `0.2` | Minimum top relevance score before the critic escalates. |
| `INSIGHTDESK_API_BASE` | `http://127.0.0.1:8000` | Backend URL used by the Streamlit UI. |

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

Launch the Streamlit UI in a second terminal (with the API running):

```bash
streamlit run streamlit_app.py
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

## Testing

```bash
pytest -q
```

Tests run against the mock LLM (`MOCK_LLM=true`) and monkeypatch retrieval, so
they need no network access or API keys.

## Notes

The pipeline is a compiled LangGraph `StateGraph` with:
- Intent classification (intent + urgency)
- Conditional routing — high-urgency tickets escalate immediately
- RAG retrieval (returns a relevance score in `(0, 1]`, higher is better)
- Answer composition grounded in the retrieved citations
- Self-critique and human escalation with a structured handoff packet

The `CHROMA_PERSIST_DIR` environment variable controls where the persistent
vector store is written.
