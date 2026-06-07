"""Critic agent: self-checks the answer for hallucinations, PII, and confidence.

It returns a decision whether to escalate.
"""
from ..models import AgentResponse, RetrievalItem


class CriticAgent:
    """Simple heuristic critic for demo.

    In production we need to replace with model-based checks for PII and groundedness.
    """

    async def critique(self, answer: AgentResponse) -> AgentResponse:
        # simple rule: if there are no citations and the text is short -> escalate
        if not answer.citations or len(answer.citations) == 0:
            answer.escalate = True
            answer.escalation_packet = {"reason": "no_citations", "confidence": 0.1}
            return answer

        # if any citation score is zero, be suspicious
        if any(c.score <= 0 for c in answer.citations):
            answer.escalate = True
            answer.escalation_packet = {"reason": "low_score"}
            return answer

        # otherwise, pass
        answer.escalate = False
        return answer
