from ..langgraph_nodes.schemas import Ticket, IntentResult


class IntentNode:
    async def run(self, ticket: Ticket) -> IntentResult:
        q = ticket.text.lower()
        if any(k in q for k in ["error", "failed", "broke", "bug"]):
            intent = "bug"
        elif any(k in q for k in ["billing", "charge", "invoice"]):
            intent = "billing"
        elif any(k in q for k in ["export", "download", "backup"]):
            intent = "how_to"
        elif any(k in q for k in ["angry", "complaint", "not happy", "refund"]):
            intent = "complaint"
        else:
            intent = "general"

        if any(k in q for k in ["urgent", "asap", "now", "immediately"]):
            urgency = "high"
        elif intent == "complaint":
            urgency = "high"
        else:
            urgency = "normal"

        return IntentResult(intent=intent, urgency=urgency, metadata={})
