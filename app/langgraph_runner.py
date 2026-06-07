"""Simple LangGraph-style runner that composes the node wrappers into flows.

This is a lightweight runner that does not require the full LangGraph runtime to be
installed to be useful in tests. It mirrors the orchestrator logic but uses the
new node wrappers.
"""
from .langgraph_nodes import IntentNode, RetrievalNode, ComposerNode, CriticNode, EscalatorNode
from .langgraph_nodes.schemas import Ticket, FinalAnswer
from .agents.knowledge_agent import KnowledgeAgent
import asyncio
import uuid
from typing import Optional


class LangGraphRunner:
    def __init__(self, knowledge_agent: KnowledgeAgent):
        self.intent = IntentNode()
        self.retrieval = RetrievalNode(knowledge_agent)
        self.composer = ComposerNode()
        self.critic = CriticNode()
        self.escalator = EscalatorNode()

    async def run(self, ticket: Ticket | dict, user_id: str = "user", trace_id: Optional[str] = None) -> FinalAnswer:
        trace_id = trace_id or str(uuid.uuid4())
        if isinstance(ticket, dict):
            ticket = Ticket(**ticket)

        # 1. intent
        intent_res = await self.intent.run(ticket)
        if intent_res.urgency == "high":
            fa = FinalAnswer(text=None, escalated=True, citations=[])
            fa = await self.escalator.run(ticket, fa, trace_id=trace_id, user_id=user_id)
            return fa

        # 2. retrieval
        retrieval_res = self.retrieval.run(ticket.text, top_k=3)

        # 3. compose
        draft = await self.composer.run(ticket, retrieval_res, intent_res)

        # 4. critic
        critic = await self.critic.run(draft)

        # 5. decide escalate
        final = FinalAnswer(text=draft.text, escalated=False, citations=draft.citations)
        if critic.escalate:
            final.escalated = True
            final.escalation_packet = draft.escalation_packet if hasattr(draft, 'escalation_packet') else {"reason": critic.metadata.get("escalation_packet")}
            final = await self.escalator.run(ticket, final, trace_id=trace_id, user_id=user_id)

        return final


# convenience sync wrapper for tests
def run_flow_sync(ticket_dict: dict, user_id: str = "user", trace_id: Optional[str] = None) -> FinalAnswer:
    agent = KnowledgeAgent()
    runner = LangGraphRunner(agent)
    ticket = Ticket(**ticket_dict)
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(runner.run(ticket, user_id=user_id, trace_id=trace_id))
    finally:
        loop.close()
