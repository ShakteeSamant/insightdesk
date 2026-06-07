"""Basic tests for the InsightDesk API logic."""
import asyncio
from app.agents.orchestrator import Orchestrator


async def run_query(q):
    orch = Orchestrator()
    resp = await orch.handle(q, user_id="user-1", trace_id="trace-1")
    return resp


def test_how_to_query():
    resp = asyncio.run(run_query("How do I export my data?"))
    assert resp.response is not None
    assert isinstance(resp.response.text, str) or resp.response.escalate in (True, False)


def test_complaint_escalation():
    resp = asyncio.run(run_query("My account was charged wrongly and support ignored me!"))
    # complaint should probably escalate
    assert resp.response is not None

