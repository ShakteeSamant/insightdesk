"""Orchestrator: routes queries through the LangGraph runner.

This orchestrator uses the actual LangGraph runner and shared knowledge agent.
"""
from ..agents.knowledge_agent import KnowledgeAgent
from ..models import ProcessResponse, AgentResponse
from ..langgraph_runner import LangGraphRunner
from ..rag.ingest import ingest_agent


class Orchestrator:
    def __init__(self):
        self.knowledge_agent = KnowledgeAgent()
        ingest_agent(self.knowledge_agent)
        self.runner = LangGraphRunner(self.knowledge_agent)

    async def handle(self, query: str, user_id: str, trace_id: str) -> ProcessResponse:
        ticket_payload = {"id": trace_id, "text": query, "priority": "normal"}
        final_answer = await self.runner.run(ticket_payload, user_id=user_id, trace_id=trace_id)

        response = AgentResponse(
            success=not final_answer.escalated,
            text=final_answer.text,
            citations=final_answer.citations,
            escalate=final_answer.escalated,
            escalation_packet=final_answer.escalation_packet,
        )
        return ProcessResponse(trace_id=trace_id, response=response)
