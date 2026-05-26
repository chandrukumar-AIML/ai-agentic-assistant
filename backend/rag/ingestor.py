import asyncio
import uuid
import logging
import hashlib
import numpy as np
from pathlib import Path
from typing import Literal

from langchain_community.document_loaders import PyPDFLoader, TextLoader, WebBaseLoader
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter, TokenTextSplitter
    TOKEN_SPLITTER_AVAILABLE = True
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    TOKEN_SPLITTER_AVAILABLE = False

from backend.rag.embedder    import embed_texts
from backend.rag.faiss_store import add_vectors as faiss_add
from backend.rag.chroma_store import add_documents as chroma_add
from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()


def _make_chunk_id(source: str, chunk_index: int) -> str:
    return hashlib.md5(f"{source}::{chunk_index}".encode()).hexdigest()


async def ingest(
    source:      str,
    source_type: Literal["pdf", "txt", "url"] = "txt",
    category:    str = "general",
    extra_meta:  dict | None = None,
) -> dict:
    """
    Ingest a document into FAISS + ChromaDB.
    Loaders are synchronous — wrapped in asyncio.to_thread to avoid blocking event loop.
    """
    logger.info(f"Ingesting {source_type}: {source}")

    if source_type == "pdf":
        loader = PyPDFLoader(source)
    elif source_type == "url":
        loader = WebBaseLoader(source)
    else:
        loader = TextLoader(source, encoding="utf-8")

    # Run blocking I/O in thread pool
    raw_docs = await asyncio.to_thread(loader.load)

    if TOKEN_SPLITTER_AVAILABLE:
        splitter = TokenTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
    else:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    chunks = await asyncio.to_thread(splitter.split_documents, raw_docs)

    if not chunks:
        logger.warning(f"No chunks extracted from {source}")
        return {"chunks_indexed": 0, "source": source}

    texts      = [c.page_content for c in chunks]
    embeddings = await embed_texts(texts)

    ids       = []
    metadatas = []
    for i, chunk in enumerate(chunks):
        chunk_id = _make_chunk_id(source, i)
        meta = {
            "source":    source,
            "category":  category,
            "chunk_idx": i,
            "page":      chunk.metadata.get("page", 0),
            **(extra_meta or {}),
        }
        ids.append(chunk_id)
        metadatas.append(meta)

    # add_vectors is now async (has asyncio.Lock)
    await faiss_add(embeddings.astype(np.float32), metadatas)

    chroma_add(
        ids=ids,
        embeddings=embeddings.tolist(),
        documents=texts,
        metadatas=metadatas,
    )

    logger.info(f"Ingested {len(chunks)} chunks from {source}")
    return {"chunks_indexed": len(chunks), "source": source}