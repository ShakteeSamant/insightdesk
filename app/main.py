"""FastAPI application entrypoint for InsightDesk.

Endpoints:
- POST /process: submit a user query for agent processing
- GET /health: basic liveness
- GET /docs/{doc_id}: retrieve an ingested document
- POST /ingest: load local document assets into the vector store
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from uuid import uuid4
import logging

from .agents.orchestrator import Orchestrator
from .models import ProcessRequest, ProcessResponse
from .utils import setup_logging
from .rag.ingest import ingest_agent

setup_logging()
logger = logging.getLogger("insightdesk")

app = FastAPI(title="InsightDesk")

orchestrator = Orchestrator()


@app.get("/health")
async def health():
    """Health endpoint."""
    return {"status": "ok"}


@app.post("/process", response_model=ProcessResponse)
async def process(req: ProcessRequest, request: Request):
    """Process a customer question through the agent pipeline."""
    trace_id = str(uuid4())
    logger.info("/process received", extra={"trace_id": trace_id, "query": req.query})
    result = await orchestrator.handle(req.query, req.user_id, trace_id)
    return JSONResponse(content=result.dict())


@app.get("/docs/{doc_id}")
async def get_doc(doc_id: str):
    """Retrieve an ingested document by id."""
    doc = orchestrator.knowledge_agent.get_doc(doc_id)
    if not doc:
        return JSONResponse(status_code=404, content={"error": "not found"})
    return doc


@app.post("/ingest")
async def ingest_docs():
    """Ingest documents from the local data folder into ChromaDB."""
    count = ingest_agent(orchestrator.knowledge_agent)
    return {"status": "ingested", "count": count}
