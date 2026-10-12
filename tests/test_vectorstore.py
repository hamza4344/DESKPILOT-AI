from types import SimpleNamespace

import pytest
from langchain_core.documents import Document

from app.rag import vectorstore as vs


@pytest.mark.parametrize("dimension,metric", [(384, "cosine"), (1536, "dotproduct")])
def test_incompatible_index_is_never_deleted(monkeypatch, dimension, metric):
    class FakePinecone:
        def list_indexes(self):
            return SimpleNamespace(names=lambda: [vs.settings.pinecone_index_name])

        def describe_index(self, name):
            return SimpleNamespace(dimension=dimension, metric=metric, status={"ready": True})

        def delete_index(self, **kwargs):
            pytest.fail("existing data must never be deleted")

    monkeypatch.setattr(vs.settings, "pinecone_api_key", "test")
    monkeypatch.setattr(vs, "Pinecone", lambda **kwargs: FakePinecone())
    with pytest.raises(ValueError):
        vs.ensure_index()


def test_index_wait_is_bounded(monkeypatch):
    fake = SimpleNamespace(
        list_indexes=lambda: SimpleNamespace(names=lambda: [vs.settings.pinecone_index_name]),
        describe_index=lambda name: SimpleNamespace(
            dimension=1536, metric="cosine", status={"ready": False}
        ),
    )
    monkeypatch.setattr(vs.settings, "pinecone_api_key", "test")
    monkeypatch.setattr(vs, "Pinecone", lambda **kwargs: fake)
    ticks = iter([0, 100])
    monkeypatch.setattr(vs.time, "monotonic", lambda: next(ticks))
    with pytest.raises(TimeoutError):
        vs.ensure_index()


def test_repeated_document_uploads_use_stable_ids(monkeypatch):
    calls = []

    def add(chunks, *, ids):
        calls.append(ids)
        return ids

    monkeypatch.setattr(vs, "get_vectorstore", lambda: SimpleNamespace(add_documents=add))
    docs = [Document(page_content="VPN guide", metadata={"document_id": "file-hash"})]
    vs.add_documents(docs)
    vs.add_documents(docs)
    assert calls[0] == calls[1]
    docs[0].page_content = "Changed guide"
    vs.add_documents(docs)
    assert calls[0] != calls[2]
