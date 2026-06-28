"""LangGraph runner that compiles the node wrappers into a real StateGraph.

The graph executes the intent -> retrieval -> composition -> critic -> finalize
flow. Tickets classified as high urgency are routed straight to escalation,
skipping retrieval and composition entirely.
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Any, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime

from .langgraph_nodes import ComposerNode, CriticNode, EscalatorNode, IntentNode, RetrievalNode
from .langgraph_nodes.schemas import FinalAnswer, IntentResult, Ticket
from .agents.knowledge_agent import KnowledgeAgent
from .models import AgentResponse, RetrievalItem

TOP_K = 3


class LangGraphState(TypedDict, total=False):
    id: str
    text: str
    priority: str
    metadata: dict
    intent_result: dict
    citations: List[dict]
    draft: dict
    critic: dict
    answer_text: str
    answer_escalated: bool
    answer_citations: List[dict]
    answer_escalation_packet: dict


class LangGraphRunner:
    def __init__(self, knowledge_agent: KnowledgeAgent):
        self.intent = IntentNode()
        self.retrieval = RetrievalNode(knowledge_agent)
        self.composer = ComposerNode()
        self.critic = CriticNode()
        self.escalator = EscalatorNode()
        self.graph = self._build_graph().compile()

    def _ticket_from_state(self, state: LangGraphState) -> Ticket:
        return Ticket(
            id=state["id"],
            text=state["text"],
            priority=state.get("priority", "normal"),
            metadata=state.get("metadata", {}),
        )

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(
            state_schema=LangGraphState,
            input_schema=Ticket,
            context_schema=dict,
        )

        async def intent_node(state: LangGraphState) -> dict[str, Any]:
            intent = await self.intent.run(self._ticket_from_state(state))
            return {"intent_result": intent.model_dump()}

        def retrieval_node(state: LangGraphState) -> dict[str, Any]:
            citations = self.retrieval.run(state["text"], top_k=TOP_K)
            return {"citations": [c.model_dump() for c in citations]}

        async def compose_node(state: LangGraphState) -> dict[str, Any]:
            draft = await self.composer.run(
                self._ticket_from_state(state),
                [RetrievalItem(**c) for c in state.get("citations", [])],
                IntentResult(**state["intent_result"]),
            )
            return {"draft": draft.model_dump()}

        async def critic_node(state: LangGraphState) -> dict[str, Any]:
            critic = await self.critic.run(AgentResponse(**state["draft"]))
            return {"critic": critic.model_dump()}

        async def finalize_node(state: LangGraphState, runtime: Runtime[dict]) -> dict[str, Any]:
            draft = AgentResponse(**state["draft"])
            critic = AgentResponse(**state["critic"])
            final = FinalAnswer(
                text=draft.text,
                escalated=False,
                citations=draft.citations or [],
                escalation_packet=None,
            )

            if critic.escalate:
                final.escalated = True
                final.escalation_packet = critic.escalation_packet or {"reason": "critic_escalated"}
                final = await self._build_handoff(state, final, runtime)

            return self._answer_fields(final)

        async def early_escalation_node(state: LangGraphState, runtime: Runtime[dict]) -> dict[str, Any]:
            intent = IntentResult(**state["intent_result"])
            final = FinalAnswer(
                text=(
                    "This request was flagged as high urgency and has been routed "
                    "directly to a human support agent."
                ),
                escalated=True,
                citations=[],
                escalation_packet={"reason": "urgent_intent", "intent": intent.intent, "urgency": intent.urgency},
            )
            final = await self._build_handoff(state, final, runtime)
            return self._answer_fields(final)

        def route_after_intent(state: LangGraphState) -> str:
            return "escalate" if state.get("intent_result", {}).get("urgency") == "high" else "retrieve"

        graph.add_node("intent_node", intent_node)
        graph.add_node("retrieval_node", retrieval_node)
        graph.add_node("compose_node", compose_node)
        graph.add_node("critic_node", critic_node)
        graph.add_node("finalize_node", finalize_node)
        graph.add_node("early_escalation_node", early_escalation_node)

        graph.add_edge(START, "intent_node")
        graph.add_conditional_edges(
            "intent_node",
            route_after_intent,
            {"escalate": "early_escalation_node", "retrieve": "retrieval_node"},
        )
        graph.add_edge("retrieval_node", "compose_node")
        graph.add_edge("compose_node", "critic_node")
        graph.add_edge("critic_node", "finalize_node")
        graph.add_edge("finalize_node", END)
        graph.add_edge("early_escalation_node", END)

        return graph

    async def _build_handoff(
        self, state: LangGraphState, final: FinalAnswer, runtime: Runtime[dict]
    ) -> FinalAnswer:
        return await self.escalator.run(
            self._ticket_from_state(state),
            final,
            trace_id=runtime.context.get("trace_id", ""),
            user_id=runtime.context.get("user_id", "user"),
        )

    @staticmethod
    def _answer_fields(final: FinalAnswer) -> dict[str, Any]:
        return {
            "answer_text": final.text,
            "answer_escalated": final.escalated,
            "answer_citations": [c.model_dump() for c in final.citations],
            "answer_escalation_packet": final.escalation_packet,
        }

    async def run(
        self, ticket: Ticket | dict, user_id: str = "user", trace_id: Optional[str] = None
    ) -> FinalAnswer:
        trace_id = trace_id or str(uuid.uuid4())
        if isinstance(ticket, dict):
            ticket = Ticket(**ticket)

        state: LangGraphState = {
            "id": ticket.id,
            "text": ticket.text,
            "priority": ticket.priority,
            "metadata": ticket.metadata,
        }

        result = await self.graph.ainvoke(state, context={"user_id": user_id, "trace_id": trace_id})

        return FinalAnswer(
            text=result.get("answer_text"),
            escalated=result.get("answer_escalated", False),
            citations=[RetrievalItem(**c) for c in result.get("answer_citations", [])],
            escalation_packet=result.get("answer_escalation_packet"),
        )


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
