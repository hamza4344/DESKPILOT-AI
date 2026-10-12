"""Modified for DeskPilot AI: bounded uploads and correlated API errors."""

import hashlib
import logging
import secrets
import tempfile
import time
from pathlib import Path

from fastapi import APIRouter, Depends, File, Header, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field, field_validator
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.rag.vectorstore import add_documents
from app.rag.workflow import ask
from app.services.audit import write_audit
from app.services.ingestion import SUPPORTED, chunk_documents, load_file

router = APIRouter(prefix="/api")
settings = get_settings()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=3000)
    allow_web: bool = False

    @field_validator("question", mode="before")
    @classmethod
    def strip_question(cls, value):
        return value.strip() if isinstance(value, str) else value


class Citation(BaseModel):
    title: str
    url: str = ""
    type: str


class ChatResponse(BaseModel):
    answer: str
    source_used: str
    trace: list[str]
    citations: list[Citation]
    rewritten_query: str
    request_id: str
    latency_ms: int
    retry_count: int


def require_admin(x_admin_key: str = Header(default="")):
    configured = settings.admin_api_key
    if not configured or configured in {"change-me", "change-me-in-production"}:
        raise HTTPException(status_code=503, detail="Document ingestion is not configured")
    if not secrets.compare_digest(x_admin_key.encode(), configured.encode()):
        raise HTTPException(status_code=401, detail="Invalid admin key")


@router.get("/health")
def health():
    """Liveness only: does not contact remote providers."""
    return {"status": "ok", "service": settings.app_name, "version": "0.2.0"}


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request):
    start = time.perf_counter()
    request_id = request.state.request_id
    try:
        result = ask(payload.question, allow_web=payload.allow_web)
        elapsed = int((time.perf_counter() - start) * 1000)
        write_audit(
            payload.question,
            result["source_used"],
            result.get("trace", []),
            request_id=request_id,
            latency_ms=elapsed,
            retry_count=result.get("retry_count", 0),
        )
        return ChatResponse(
            answer=result["answer"],
            source_used=result["source_used"],
            trace=result.get("trace", []),
            citations=result.get("citations", []),
            rewritten_query=result.get("current_query", payload.question),
            request_id=request_id,
            latency_ms=elapsed,
            retry_count=result.get("retry_count", 0),
        )
    except Exception as exc:
        logger.error("chat_failed request_id=%s error_type=%s", request_id, type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail=f"Unable to complete the support request. Reference: {request_id}",
        ) from exc


@router.post("/ingest", dependencies=[Depends(require_admin)])
async def ingest(request: Request, file: UploadFile = File(...)):
    filename = (file.filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED:
        raise HTTPException(status_code=400, detail=f"Supported: {', '.join(sorted(SUPPORTED))}")
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = None
    try:
        digest = hashlib.sha256()
        total = 0
        with tempfile.NamedTemporaryFile(dir=upload_dir, suffix=suffix, delete=False) as stream:
            dest = Path(stream.name)
            while block := await file.read(64 * 1024):
                total += len(block)
                if total > settings.max_upload_bytes:
                    raise HTTPException(
                        status_code=413, detail="Document exceeds the configured upload limit"
                    )
                digest.update(block)
                stream.write(block)
        if total == 0:
            raise HTTPException(status_code=400, detail="Document is empty")
        docs = await run_in_threadpool(load_file, dest)
        document_id = digest.hexdigest()
        for doc in docs:
            doc.metadata["source"] = filename
            doc.metadata["document_id"] = document_id
        chunks = await run_in_threadpool(chunk_documents, docs)
        if not chunks:
            raise HTTPException(
                status_code=422, detail="No extractable text found; scanned PDFs require OCR"
            )
        ids = await run_in_threadpool(add_documents, chunks)
        return {
            "message": "Document indexed",
            "file": filename,
            "document_id": document_id,
            "chunks": len(chunks),
            "ids_created": len(ids),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "ingestion_failed request_id=%s error_type=%s",
            request.state.request_id,
            type(exc).__name__,
        )
        raise HTTPException(status_code=502, detail="Unable to parse or index document") from exc
    finally:
        if dest is not None:
            dest.unlink(missing_ok=True)
        await file.close()
