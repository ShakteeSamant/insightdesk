"""Intent Classifier agent.

This agent classifies user queries into a structured `IntentMessage`.
It demonstrates structured output by returning a Pydantic model.
"""
from ..models import IntentMessage


class IntentClassifier:
    """Simple rule-based classifier for demo/testing."""

    async def classify(self, query: str) -> IntentMessage:
        """Classify `query` and return an `IntentMessage`.

        This is intentionally simple: keywords determine intent and urgency.
        """
        q = query.lower()
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

        return IntentMessage(intent=intent, urgency=urgency, metadata={})
