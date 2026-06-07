from ..agents.escalator import Escalator
from ..langgraph_nodes.schemas import FinalAnswer, Ticket


class EscalatorNode:
    def __init__(self):
        self.escalator = Escalator()

    async def run(self, ticket: Ticket, final: FinalAnswer, trace_id: str, user_id: str) -> FinalAnswer:
        packet = await self.escalator.create_packet(ticket.text, user_id, final, trace_id)
        final.escalation_packet = packet
        return final
