"""Modified for DeskPilot AI: repeatable fictional-fixture ingestion."""

import hashlib
from pathlib import Path

from app.core.config import get_settings
from app.rag.vectorstore import add_documents
from app.services.ingestion import SUPPORTED, chunk_documents, load_file


def main():
    folder = Path(get_settings().sample_kb_dir)
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in SUPPORTED)
    chunks = []
    for path in files:
        docs = load_file(path)
        document_id = hashlib.sha256(path.read_bytes()).hexdigest()
        for doc in docs:
            doc.metadata.update(source=path.name, document_id=document_id)
        chunks.extend(chunk_documents(docs))
    if not chunks:
        raise SystemExit("No extractable knowledge found")
    ids = add_documents(chunks)
    print(f"Indexed {len(files)} files -> {len(chunks)} chunks -> {len(ids)} vector upserts")


if __name__ == "__main__":
    main()
