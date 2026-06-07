from __future__ import annotations

from pydantic import BaseModel
from typing import List, Optional

from ..models import RetrievalItem


class Ticket(BaseModel):
    id: str
    text: str
    priority: str = "normal"
    metadata: dict = {}


class IntentResult(BaseModel):
    intent: str
    urgency: str
    metadata: dict = {}


class FinalAnswer(BaseModel):
    text: Optional[str] = None
    escalated: bool = False
    citations: List[RetrievalItem] = []
    escalation_packet: Optional[dict] = None
