"""Intent node: classifies a ticket into intent + urgency.

Delegates to :class:`IntentClassifier` so classification logic lives in exactly
one place and can be patched/extended independently of the graph wiring.
"""
from ..agents.intent_classifier import IntentClassifier
from ..langgraph_nodes.schemas import IntentResult, Ticket


class IntentNode:
    def __init__(self):
        self.classifier = IntentClassifier()

    async def run(self, ticket: Ticket) -> IntentResult:
        msg = await self.classifier.classify(ticket.text)
        return IntentResult(intent=msg.intent, urgency=msg.urgency, metadata=msg.metadata)
