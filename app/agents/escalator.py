"""Escalator agent: packages a handoff bundle for a human agent.

Creates a JSON-ready packet containing the query, user context, retrieved docs,
and explanation from the critic.
"""
from ..models import AgentResponse, RetrievalItem


class Escalator:
    async def create_packet(self, query: str, user_id: str, answer: AgentResponse, trace_id: str) -> dict:
        packet = {
            "trace_id": trace_id,
            "query": query,
            "user_id": user_id,
            "answer_text": answer.text,
            "citations": [c.model_dump() for c in (answer.citations or [])],
            "reason": answer.escalation_packet,
        }
        # In a real system we might call a tool to create a ticket or notify a queue.
        return packet
