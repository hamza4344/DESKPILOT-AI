"""Modified for DeskPilot AI: non-destructive indexes and stable vector IDs."""

import hashlib
import time

from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

from app.core.config import get_settings

settings = get_settings()
_embeddings = None
_vectorstore = None
EMBEDDING_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}


def get_embedding_dimension(model_name: str | None = None) -> int:
    name = (model_name or settings.embedding_model).strip()
    if name not in EMBEDDING_DIMENSIONS:
        raise ValueError(f"Unsupported OpenAI embedding model: {name}")
    return EMBEDDING_DIMENSIONS[name]


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is missing")
        _embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
            request_timeout=settings.provider_timeout_seconds,
            max_retries=1,
        )
    return _embeddings


def _field(obj, name):
    return obj.get(name) if isinstance(obj, dict) else getattr(obj, name)


def ensure_index():
    if not settings.pinecone_api_key:
        raise RuntimeError("PINECONE_API_KEY is missing")
    dimension = get_embedding_dimension()
    pc = Pinecone(api_key=settings.pinecone_api_key)
    names = pc.list_indexes().names()
    if settings.pinecone_index_name not in names:
        pc.create_index(
            name=settings.pinecone_index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud=settings.pinecone_cloud, region=settings.pinecone_region),
        )
    deadline = time.monotonic() + settings.index_ready_timeout_seconds
    while True:
        info = pc.describe_index(settings.pinecone_index_name)
        if _field(info, "dimension") != dimension:
            raise ValueError(
                "Pinecone dimension mismatch. Configure a NEW index name and re-ingest; "
                "the existing index has been preserved."
            )
        if _field(info, "metric") != "cosine":
            raise ValueError("Pinecone index must use cosine similarity; existing index preserved")
        if _field(_field(info, "status"), "ready"):
            return pc.Index(settings.pinecone_index_name)
        if time.monotonic() >= deadline:
            raise TimeoutError("Pinecone index did not become ready within the configured timeout")
        time.sleep(1)


def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = PineconeVectorStore(
            index=ensure_index(), embedding=get_embeddings(), namespace=settings.pinecone_namespace
        )
    return _vectorstore


def get_retriever():
    return get_vectorstore().as_retriever(search_kwargs={"k": settings.top_k})


def add_documents(chunks):
    # Identical documents produce stable IDs, so repeat ingestion is an upsert.
    ids = []
    for position, chunk in enumerate(chunks):
        fingerprint = str(
            chunk.metadata.get("document_id", chunk.metadata.get("source", "unknown"))
        )
        identity = f"{fingerprint}:{position}:{chunk.page_content}"
        ids.append(hashlib.sha256(identity.encode()).hexdigest())
    return get_vectorstore().add_documents(chunks, ids=ids)
