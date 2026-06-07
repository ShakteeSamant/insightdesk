"""Pydantic models (v2) for inter-agent messages and API contracts."""
from pydantic import BaseModel, Field
from typing import List, Optional, Any


class ProcessRequest(BaseModel):
    query: str = Field(..., description="User question")
    user_id: Optional[str] = Field(None, description="Optional user id")


class Doc(BaseModel):
    id: str
    title: str
    content: str
    source: Optional[str] = None


class RetrievalItem(BaseModel):
    doc_id: str
    score: float
    excerpt: str


class IntentMessage(BaseModel):
    intent: str
    urgency: str
    metadata: dict = {}


class AgentResponse(BaseModel):
    success: bool
    text: Optional[str]
    citations: Optional[List[RetrievalItem]] = []
    escalate: bool = False
    escalation_packet: Optional[dict] = None


class ProcessResponse(BaseModel):
    trace_id: str
    response: AgentResponse
