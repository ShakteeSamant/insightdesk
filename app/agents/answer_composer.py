"""Answer composer agent.

Composes grounded answers from retrieved citations and (mock) LLM.
Shows structured output by returning a dict with `answer` and `citations`.
"""
import asyncio
import os
from typing import List

from openai import OpenAI
from ..models import RetrievalItem, AgentResponse


def _mock_enabled() -> bool:
    """Read MOCK_LLM at call time so the flag can be toggled per request/test."""
    return os.environ.get("MOCK_LLM", "true").lower() in ("1", "true", "yes")


class AnswerComposer:
    """Generate a grounded answer using retrieved docs.

    For demo/test purposes the LLM can be mocked by `MOCK_LLM=true`.
    """

    async def compose(self, query: str, citations: List[RetrievalItem]) -> AgentResponse:
        if _mock_enabled():
            if len(citations) <= 1:
                answer_text = "The system found insufficient evidence to provide a grounded answer. Escalating to a human." 
                return AgentResponse(success=False, text=answer_text, citations=[], escalate=True)
            lines = [f"Found {len(citations)} doc(s) relevant."]
            for c in citations:
                lines.append(f"- {c.doc_id}: {c.excerpt[:80]}")
            answer_text = "\n".join(lines)
            return AgentResponse(success=True, text=answer_text, citations=citations, escalate=False)

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return AgentResponse(
                success=False,
                text="OPENAI_API_KEY is required for real LLM mode.",
                citations=[],
                escalate=True,
            )

        model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that answers user questions using provided citations. "
                    "If the citations are insufficient, say you cannot provide a grounded answer."
                ),
            },
            {"role": "user", "content": f"Question: {query}\n\nCitations:\n"},
        ]
        for c in citations:
            messages.append(
                {
                    "role": "user",
                    "content": f"- {c.doc_id}: {c.excerpt[:80]}",
                }
            )

        client = OpenAI(api_key=api_key)
        try:
            completion = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=messages,
                temperature=0.2,
                max_tokens=512,
            )
            answer_text = completion.choices[0].message.content.strip()
        except Exception as exc:
            return AgentResponse(
                success=False,
                text=f"OpenAI API error: {exc}",
                citations=[],
                escalate=True,
            )

        return AgentResponse(success=True, text=answer_text, citations=citations, escalate=False)
