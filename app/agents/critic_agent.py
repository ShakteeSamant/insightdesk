"""Critic agent: self-checks the answer for groundedness and confidence.

It returns the (possibly mutated) answer with a decision on whether to escalate.
In production these heuristics would be replaced with model-based checks for PII
and groundedness.
"""
import os

from ..models import AgentResponse

# Relevance scores are in (0, 1] where higher is better. Below this threshold the
# best supporting citation is considered too weak to trust the answer.
MIN_SCORE = float(os.getenv("CRITIC_MIN_SCORE", "0.2"))


class CriticAgent:
    """Simple heuristic critic for the demo."""

    async def critique(self, answer: AgentResponse) -> AgentResponse:
        # No supporting evidence -> not grounded -> escalate.
        if not answer.citations:
            answer.escalate = True
            answer.escalation_packet = {"reason": "no_citations", "confidence": 0.1}
            return answer

        # The strongest citation is still too weak to be confident.
        best_score = max(c.score for c in answer.citations)
        if best_score < MIN_SCORE:
            answer.escalate = True
            answer.escalation_packet = {"reason": "low_confidence", "confidence": round(best_score, 3)}
            return answer

        answer.escalate = False
        return answer
