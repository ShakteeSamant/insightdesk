"""LangGraph runner that compiles the node wrappers into a real StateGraph.

This implementation uses `langgraph` to build a graph of stateful nodes that
execute the same intent, retrieval, composition, critic, and escalation flow.
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Any, List, Optional, TypedDict

from langgraph.graph import START, StateGraph
from langgraph.runtime import Runtime

from .langgraph_nodes import IntentNode, RetrievalNode, ComposerNode, CriticNode, EscalatorNode
from .langgraph_nodes.schemas import Ticket, FinalAnswer, IntentResult
from .agents.knowledge_agent import KnowledgeAgent
from .models import AgentResponse, RetrievalItem


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

    def _build_graph(self) -> StateGraph[LangGraphState, dict, Ticket, LangGraphState]:
        graph = StateGraph(
            state_schema=LangGraphState,
            input_schema=Ticket,
            context_schema=dict,
        )
 
        async def intent_node(state: LangGraphState) -> dict[str, dict]:
            ticket = self._ticket_from_state(state)
            intent = await self.intent.run(ticket)
            return {"intent_result": intent.model_dump()}

        def retrieval_node(state: LangGraphState) -> dict[str, List[dict]]:
            citations = self.retrieval.run(state["text"], top_k=3)
            return {"citations": [citation.model_dump() for citation in citations]}

        async def compose_node(state: LangGraphState) -> dict[str, dict]:
            ticket = self._ticket_from_state(state)
            return {
                "draft": (
                    await self.composer.run(
                        ticket,
                        [RetrievalItem(**citation) for citation in state.get("citations", [])],
                        IntentResult(**state["intent_result"]),
                    )
                ).model_dump()
            }

        async def critic_node(state: LangGraphState) -> dict[str, dict]:
            return {"critic": (await self.critic.run(AgentResponse(**state["draft"]))).model_dump()}

        async def final_node(state: LangGraphState, runtime: Runtime[dict]) -> dict[str, Any]:
            draft = AgentResponse(**state["draft"])
            critic = AgentResponse(**state["critic"])
            final = FinalAnswer(
                text=draft.text,
                escalated=False,
                citations=draft.citations,
                escalation_packet=None,
            )

            if critic.escalate:
                final.escalated = True
                final.escalation_packet = (
                    draft.escalation_packet
                    if draft.escalation_packet is not None
                    else {"reason": "critic_escalated"}
                )
                final = await self.escalator.run(
                    self._ticket_from_state(state),
                    final,
                    trace_id=runtime.context.get("trace_id", ""),
                    user_id=runtime.context.get("user_id", "user"),
                )

            return {
                "answer_text": final.text,
                "answer_escalated": final.escalated,
                "answer_citations": [citation.model_dump() for citation in final.citations],
                "answer_escalation_packet": final.escalation_packet,
            }

        graph.add_node(intent_node)
        graph.add_node(retrieval_node)
        graph.add_node(compose_node)
        graph.add_node(critic_node)
        graph.add_node(final_node)

        graph.add_edge(START, "intent_node")
        graph.add_edge("intent_node", "retrieval_node")
        graph.add_edge("retrieval_node", "compose_node")
        graph.add_edge("compose_node", "critic_node")
        graph.add_edge("critic_node", "final_node")
        graph.set_entry_point("intent_node")
        graph.set_finish_point("final_node")

        return graph

    async def run(self, ticket: Ticket | dict, user_id: str = "user", trace_id: Optional[str] = None) -> FinalAnswer:
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
            citations=[RetrievalItem(**citation) for citation in result.get("answer_citations", [])],
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
