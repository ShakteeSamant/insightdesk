import os
import pytest
from app.langgraph_runner import run_flow_sync
from app.langgraph_nodes.schemas import Ticket


@pytest.fixture(autouse=True)
def set_mock_env(monkeypatch):
    # Ensure mock LLM path is used by composer
    monkeypatch.setenv("MOCK_LLM", "true")


def test_flow_happy_path(monkeypatch):
    # mock retrieval to return two docs
    def fake_retrieve(self, query, top_k=3):
        from app.models import RetrievalItem
        return [RetrievalItem(doc_id="doc1", score=1.0, excerpt="This is doc1 about how to export"),
                RetrievalItem(doc_id="doc2", score=0.8, excerpt="Doc2 has billing info")]

    monkeypatch.setattr("app.agents.knowledge_agent.KnowledgeAgent.retrieve", fake_retrieve)

    ticket = {"id": "t1", "text": "How do I export my data?", "priority": "normal"}
    final = run_flow_sync(ticket)
    assert final is not None
    assert final.escalated is False
    assert final.text is not None
    assert len(final.citations) >= 1


def test_flow_no_docs(monkeypatch):
    def fake_retrieve(self, query, top_k=3):
        return []

    monkeypatch.setattr("app.agents.knowledge_agent.KnowledgeAgent.retrieve", fake_retrieve)
    ticket = {"id": "t2", "text": "Some obscure question with no docs", "priority": "normal"}
    final = run_flow_sync(ticket)
    # Critic should escalate when no citations
    assert final.escalated is True
    assert final.escalation_packet is not None


def test_flow_hallucination_triggers_escalation(monkeypatch):
    # retrieval returns a doc, but composer will mock produce a short/no-citation answer
    def fake_retrieve(self, query, top_k=3):
        from app.models import RetrievalItem
        return [RetrievalItem(doc_id="doc1", score=1.0, excerpt="Relevant doc content")]

    monkeypatch.setattr("app.agents.knowledge_agent.KnowledgeAgent.retrieve", fake_retrieve)

    # Force AnswerComposer to produce no citations by ensuring MOCK_LLM path produces short text
    monkeypatch.setenv("MOCK_LLM", "true")

    ticket = {"id": "t3", "text": "Tell me a fact not in docs", "priority": "normal"}
    final = run_flow_sync(ticket)
    # Critic should flag escalation if no citations or low confidence
    assert final.escalated is True
    assert final.escalation_packet is not None


def test_flow_urgent_intent_escapes_normal_flow(monkeypatch):
    # set intent classifier to return high urgency
    async def fake_classify(self, query: str):
        from app.models import IntentMessage
        return IntentMessage(intent="general", urgency="high", metadata={})

    monkeypatch.setattr("app.agents.intent_classifier.IntentClassifier.classify", fake_classify)

    ticket = {"id": "t4", "text": "Help! urgent issue now", "priority": "normal"}
    final = run_flow_sync(ticket)
    assert final.escalated is True
    assert final.escalation_packet is not None


def test_flow_partial_citations(monkeypatch):
    # retrieval returns one doc with low score
    def fake_retrieve(self, query, top_k=3):
        from app.models import RetrievalItem
        return [RetrievalItem(doc_id="doc1", score=0.0, excerpt="partial info")]

    monkeypatch.setattr("app.agents.knowledge_agent.KnowledgeAgent.retrieve", fake_retrieve)
    ticket = {"id": "t5", "text": "Question with partial match", "priority": "normal"}
    final = run_flow_sync(ticket)
    # Because score is zero, critic sets escalate -> escalated True
    assert final.escalated is True
    assert final.escalation_packet is not None

