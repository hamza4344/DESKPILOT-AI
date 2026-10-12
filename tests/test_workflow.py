from types import SimpleNamespace

import pytest
from langchain_core.documents import Document

from app.rag import workflow as wf


class FakeLLM:
    def with_structured_output(self, schema, **kwargs):
        return self

    def invoke(self, prompt):
        text = str(prompt)
        if "route messages" in text:
            return SimpleNamespace(route="kb")
        if "grade evidence" in text:
            return SimpleNamespace(grade="good")
        if "Return good if" in text:
            return SimpleNamespace(grade="good")
        return SimpleNamespace(content="Use the approved VPN client.")


@pytest.fixture
def graph_dependencies(monkeypatch):
    monkeypatch.setattr(wf, "llm", lambda: FakeLLM())
    monkeypatch.setattr(wf.settings, "max_retries", 1)
    monkeypatch.setattr(wf.settings, "enable_web_search", False)


def test_private_evidence_wins_even_when_web_consented(graph_dependencies, monkeypatch):
    monkeypatch.setattr(wf.settings, "enable_web_search", True)
    monkeypatch.setattr(
        wf,
        "get_retriever",
        lambda: SimpleNamespace(
            invoke=lambda q: [
                Document(page_content="VPN steps", metadata={"source": "handbook.md"})
            ]
        ),
    )

    def fail():
        pytest.fail("web search must not run when private evidence is good")

    monkeypatch.setattr(wf, "web_search_tool", fail)
    result = wf.ask("How do I connect to the VPN?", allow_web=True)
    assert result["source_used"] == "private_kb"
    assert result["citations"][0]["title"] == "handbook.md"


@pytest.mark.parametrize("server_enabled,consent", [(False, False), (False, True), (True, False)])
def test_web_requires_both_gates(graph_dependencies, monkeypatch, server_enabled, consent):
    monkeypatch.setattr(wf.settings, "enable_web_search", server_enabled)
    monkeypatch.setattr(wf, "get_retriever", lambda: SimpleNamespace(invoke=lambda q: []))
    monkeypatch.setattr(wf, "web_search_tool", lambda: pytest.fail("unexpected external search"))
    result = wf.ask("VPN troubleshooting", allow_web=consent)
    assert result["source_used"] == "insufficient_evidence"
    assert result["retry_count"] == 1
    assert result["citations"] == []


def test_opted_in_web_fallback(graph_dependencies, monkeypatch):
    monkeypatch.setattr(wf.settings, "enable_web_search", True)
    monkeypatch.setattr(wf, "get_retriever", lambda: SimpleNamespace(invoke=lambda q: []))
    monkeypatch.setattr(
        wf,
        "web_search_tool",
        lambda: SimpleNamespace(
            invoke=lambda payload: {
                "results": [
                    {
                        "title": "Vendor guidance",
                        "url": "https://example.com",
                        "content": "VPN steps",
                    }
                ]
            }
        ),
    )
    assert wf.ask("Vendor VPN guidance", allow_web=True)["source_used"] == "web_search"


def test_weak_web_stops_without_stale_citations(graph_dependencies, monkeypatch):
    monkeypatch.setattr(wf.settings, "enable_web_search", True)
    monkeypatch.setattr(wf, "get_retriever", lambda: SimpleNamespace(invoke=lambda q: []))
    monkeypatch.setattr(
        wf, "web_search_tool", lambda: SimpleNamespace(invoke=lambda payload: {"results": []})
    )
    result = wf.ask("Unknown product", allow_web=True)
    assert result["source_used"] == "insufficient_evidence"
    assert result["retry_count"] == 1
    assert result["citations"] == []


def test_greeting_does_not_retrieve(graph_dependencies, monkeypatch):
    class GreetingLLM(FakeLLM):
        def invoke(self, prompt):
            if "route messages" in str(prompt):
                return SimpleNamespace(route="direct")
            return SimpleNamespace(content="Hello. How can I help?")

    monkeypatch.setattr(wf, "llm", lambda: GreetingLLM())
    monkeypatch.setattr(wf, "get_retriever", lambda: pytest.fail("greeting must not retrieve"))
    result = wf.ask("Hello")
    assert result["source_used"] == "direct"
    assert result["citations"] == []
