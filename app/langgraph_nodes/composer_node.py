from ..agents.answer_composer import AnswerComposer
from ..langgraph_nodes.schemas import Ticket, IntentResult
from ..models import AgentResponse
from typing import List
from ..models import RetrievalItem


class ComposerNode:
    def __init__(self):
        self.composer = AnswerComposer()

    async def run(self, ticket: Ticket, citations: List[RetrievalItem], intent: IntentResult) -> AgentResponse:
        return await self.composer.compose(ticket.text, citations)
