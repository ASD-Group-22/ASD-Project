"""Shared Release 1 RAG retrieval pipeline.

This module contains common retrieval and grounding infrastructure shared
across the five student features.

Feature-specific data acquisition belongs in sources/student1.py through
sources/student5.py.

Shared responsibilities may include:
- corpus construction
- chunk preparation
- indexing
- retrieval
- grounding context preparation
- citation metadata
- confidence handling
"""

import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import chromadb
import requests

from sources.student1 import build_chunks as build_student1_chunks


BASE_DIR = Path(__file__).resolve().parent

CORPUS_PATH = (
    BASE_DIR
    / "corpus"
    / "corpus.jsonl"
)

AUDIT_PATH = (
    BASE_DIR
    / "rag-audit.jsonl"
)

CHROMA_PATH = (
    BASE_DIR
    / "chroma"
)

COLLECTION_NAME = os.getenv(
    "RAG_COLLECTION_NAME",
    "shared_enterprise_context"
)

EMBED_VECTOR_SIZE = 256


_collection = None
_last_corpus_chunks = []


# =========================================================
# GENERAL
# =========================================================

def now_iso():

    return datetime.now(
        timezone.utc
    ).isoformat()


# =========================================================
# EMBEDDINGS
# =========================================================

def embed_texts(
    texts: list[str]
) -> list[list[float]]:

    vectors = []

    for text in texts:

        values = [
            0.0
        ] * EMBED_VECTOR_SIZE

        tokens = (
            text or ""
        ).lower().split()

        if not tokens:
            vectors.append(values)
            continue

        for token in tokens:

            digest = hashlib.sha256(
                token.encode("utf-8")
            ).digest()

            for i, byte in enumerate(digest):

                index = (
                    i % EMBED_VECTOR_SIZE
                )

                values[index] += (
                    byte / 255.0
                ) - 0.5

        norm = sum(
            value * value
            for value in values
        ) ** 0.5

        if norm > 0:

            values = [
                value / norm
                for value in values
            ]

        vectors.append(values)

    return vectors


# =========================================================
# CHROMA
# =========================================================

def get_collection():

    global _collection

    if _collection is None:

        client = chromadb.PersistentClient(
            path=str(CHROMA_PATH)
        )

        _collection = (
            client.get_or_create_collection(
                name=COLLECTION_NAME
            )
        )

    return _collection


def reset_collection():

    global _collection

    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH)
    )

    try:

        client.delete_collection(
            name=COLLECTION_NAME
        )

    except Exception:

        pass

    _collection = (
        client.get_or_create_collection(
            name=COLLECTION_NAME
        )
    )


# =========================================================
# AUDIT
# =========================================================

def append_audit(
    tool_name: str,
    tool_input: dict[str, Any],
    tool_output: dict[str, Any],
    validation_status: str,
    outcome: str,
    start_time: float
):

    AUDIT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    duration_ms = int(
        (time.time() - start_time) * 1000
    )

    record = {
        "request_id": str(
            uuid.uuid4()
        ),
        "trace_id": str(
            uuid.uuid4()
        ),
        "tool_name": tool_name,
        "tool_input": tool_input,
        "tool_output": tool_output,
        "timestamp": now_iso(),
        "duration_ms": duration_ms,
        "validation_status": validation_status,
        "outcome": outcome
    }

    with AUDIT_PATH.open(
        "a",
        encoding="utf-8"
    ) as file:

        file.write(
            json.dumps(record)
            + "\n"
        )


# =========================================================
# CORPUS
# =========================================================

def build_corpus():

    chunks = []

    student1 = (
        build_student1_chunks()
    )

    if student1.get("status") == "success":

        chunks.extend(
            student1.get(
                "chunks",
                []
            )
        )

    else:

        chunks.append({
            "chunk_id": "student1_source_error",
            "source_id": "student1",
            "authority_tier": "tier_1",
            "text": (
                "Student 1 source is "
                "currently unavailable: "
                f"{student1.get('error')}"
            ),
            "metadata": {
                "source_type": "database_service",
                "student": "student1",
                "error": True
            },
            "indexed_at": now_iso()
        })

    return chunks


def write_corpus(chunks):

    CORPUS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with CORPUS_PATH.open(
        "w",
        encoding="utf-8"
    ) as file:

        for chunk in chunks:

            file.write(
                json.dumps(chunk)
                + "\n"
            )


def read_corpus():

    if not CORPUS_PATH.exists():
        return []

    chunks = []

    with CORPUS_PATH.open(
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            try:

                chunks.append(
                    json.loads(line)
                )

            except json.JSONDecodeError:

                continue

    return chunks


# =========================================================
# REFRESH
# =========================================================

def refresh_corpus(
    caller="student"
):

    global _last_corpus_chunks

    start = time.time()

    try:

        chunks = build_corpus()

        _last_corpus_chunks = chunks

        write_corpus(
            chunks
        )

        vector_store_status = (
            "ready"
        )

        vector_store_error = None

        try:

            reset_collection()

            collection = (
                get_collection()
            )

            if chunks:

                ids = [
                    chunk["chunk_id"]
                    for chunk in chunks
                ]

                documents = [
                    chunk["text"]
                    for chunk in chunks
                ]

                metadatas = [
                    {
                        "source_id": chunk[
                            "source_id"
                        ],
                        "authority_tier": chunk[
                            "authority_tier"
                        ],
                        "indexed_at": chunk[
                            "indexed_at"
                        ]
                    }
                    for chunk in chunks
                ]

                embeddings = embed_texts(
                    documents
                )

                collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas,
                    embeddings=embeddings
                )

        except Exception as exc:

            vector_store_status = (
                "degraded"
            )

            vector_store_error = str(
                exc
            )

        output = {
            "status": "success",
            "caller": caller,
            "chunk_count": len(chunks),
            "collection": COLLECTION_NAME,
            "corpus_path": str(
                CORPUS_PATH
            ),
            "vector_store_status":
                vector_store_status
        }

        if vector_store_error:

            output[
                "vector_store_error"
            ] = vector_store_error

        append_audit(
            "refresh_corpus",
            {
                "caller": caller
            },
            output,
            "pass",
            "corpus_refreshed",
            start
        )

        return output

    except Exception as exc:

        output = {
            "status": "error",
            "error": str(exc)
        }

        append_audit(
            "refresh_corpus",
            {
                "caller": caller
            },
            output,
            "fail",
            "error",
            start
        )

        return output


# =========================================================
# LEXICAL FALLBACK
# =========================================================

def lexical_fallback_retrieve(
    query,
    k
):

    corpus = (
        _last_corpus_chunks
        or read_corpus()
    )

    query_tokens = set(
        (query or "")
        .lower()
        .split()
    )

    tier_weight = {
        "tier_1": 3,
        "tier_2": 2,
        "tier_3": 1
    }

    scored = []

    for chunk in corpus:

        text = chunk.get(
            "text",
            ""
        )

        text_tokens = set(
            text.lower().split()
        )

        overlap = len(
            query_tokens
            & text_tokens
        )

        scored.append({
            "rank": 0,
            "chunk_id": chunk.get(
                "chunk_id"
            ),
            "source_id": chunk.get(
                "source_id"
            ),
            "authority_tier": chunk.get(
                "authority_tier"
            ),
            "distance": None,
            "text": text,
            "_score": overlap
        })

    scored.sort(
        key=lambda row: (
            tier_weight.get(
                row.get(
                    "authority_tier"
                ),
                0
            ),
            row.get(
                "_score",
                0
            )
        ),
        reverse=True
    )

    top = scored[
        :max(k, 1)
    ]

    for index, row in enumerate(
        top,
        start=1
    ):

        row["rank"] = index

        row.pop(
            "_score",
            None
        )

    return top


# =========================================================
# RETRIEVE
# =========================================================

def retrieve_context(
    query: str,
    k: int = 5,
    caller: str = "student"
):

    start = time.time()

    try:

        retrieval_mode = "vector"

        ranked = []

        try:

            collection = (
                get_collection()
            )

            if collection.count() == 0:

                refreshed = (
                    refresh_corpus(
                        caller="auto_refresh"
                    )
                )

                if refreshed.get(
                    "status"
                ) != "success":

                    raise RuntimeError(
                        "empty_collection"
                    )

            query_embedding = (
                embed_texts(
                    [query]
                )
            )

            results = collection.query(
                query_embeddings=query_embedding,
                n_results=k
            )

            ids = (
                results.get("ids")
                or [[]]
            )[0]

            documents = (
                results.get(
                    "documents"
                )
                or [[]]
            )[0]

            metadatas = (
                results.get(
                    "metadatas"
                )
                or [[]]
            )[0]

            distances = (
                results.get(
                    "distances"
                )
                or [[]]
            )[0]

            for index, chunk_id in enumerate(
                ids
            ):

                metadata = (
                    metadatas[index]
                    if index < len(metadatas)
                    else {}
                )

                ranked.append({
                    "rank": index + 1,
                    "chunk_id": chunk_id,
                    "source_id": metadata.get(
                        "source_id"
                    ),
                    "authority_tier": metadata.get(
                        "authority_tier"
                    ),
                    "distance": (
                        distances[index]
                        if index < len(distances)
                        else None
                    ),
                    "text": (
                        documents[index]
                        if index < len(documents)
                        else ""
                    )
                })

            tier_weight = {
                "tier_1": 3,
                "tier_2": 2,
                "tier_3": 1
            }

            ranked.sort(
                key=lambda row: (
                    tier_weight.get(
                        row.get(
                            "authority_tier"
                        ),
                        0
                    ),
                    -(
                        row.get(
                            "distance"
                        )
                        if isinstance(
                            row.get(
                                "distance"
                            ),
                            (int, float)
                        )
                        else 1e9
                    )
                ),
                reverse=True
            )

        except Exception:

            retrieval_mode = (
                "lexical_fallback"
            )

            if (
                not _last_corpus_chunks
                and not CORPUS_PATH.exists()
            ):

                refreshed = (
                    refresh_corpus(
                        caller="auto_refresh"
                    )
                )

                if refreshed.get(
                    "status"
                ) != "success":

                    return {
                        "status": "error",
                        "error":
                            "corpus_unavailable"
                    }

            ranked = (
                lexical_fallback_retrieve(
                    query,
                    k
                )
            )

        output = {
            "status": "success",
            "query": query,
            "caller": caller,
            "k": k,
            "retrieval_mode":
                retrieval_mode,
            "results": ranked
        }

        append_audit(
            "retrieve_context",
            {
                "query": query,
                "k": k,
                "caller": caller
            },
            {
                "result_count":
                    len(ranked),
                "chunk_ids": [
                    row["chunk_id"]
                    for row in ranked
                ]
            },
            "pass",
            "context_retrieved",
            start
        )

        return output

    except Exception as exc:

        output = {
            "status": "error",
            "error": str(exc),
            "query": query
        }

        append_audit(
            "retrieve_context",
            {
                "query": query,
                "k": k,
                "caller": caller
            },
            output,
            "fail",
            "error",
            start
        )

        return output


# =========================================================
# CONFIDENCE
# =========================================================

def confidence_from_results(
    results
):

    if not results:
        return "Unknown"

    tier_1 = sum(
        1
        for result in results
        if result.get(
            "authority_tier"
        ) == "tier_1"
    )

    tier_2 = sum(
        1
        for result in results
        if result.get(
            "authority_tier"
        ) == "tier_2"
    )

    if tier_1 >= 2 and len(
        results
    ) >= 3:

        return "High"

    if tier_1 >= 1 or tier_2 >= 2:

        return "Medium"

    return "Low"


# =========================================================
# OLLAMA
# =========================================================

def generate_with_ollama(
    query,
    context
):

    model_name = os.getenv(
        "OLLAMA_MODEL",
        "qwen2.5:0.5b"
    )

    ollama_url = os.getenv(
        "OLLAMA_GENERATE_URL",
        "http://localhost:11434/api/generate"
    )

    prompt = f"""
You are a retrieval-grounded project management assistant.

Use ONLY the provided context.

Do not invent project information.

If the evidence does not contain enough information,
return exactly:

Insufficient evidence.

QUESTION:
{query}

CONTEXT:
{context}

Return:

Answer:
<answer>

Evidence:
<short evidence summary>
""".strip()

    try:

        response = requests.post(
            ollama_url,
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()

        return response.json().get(
            "response",
            "Insufficient evidence."
        )

    except Exception as exc:

        return (
            "Ollama unavailable: "
            f"{exc}"
        )


# =========================================================
# ANSWER
# =========================================================

def answer_question(
    query: str,
    k: int = 5,
    caller: str = "student"
):

    start = time.time()

    retrieval = retrieve_context(
        query=query,
        k=k,
        caller=caller
    )

    if retrieval.get(
        "status"
    ) != "success":

        output = {
            "status": "error",
            "query": query,
            "error": retrieval.get(
                "error",
                "retrieval_failed"
            )
        }

        append_audit(
            "answer_question",
            {
                "query": query,
                "k": k,
                "caller": caller
            },
            output,
            "fail",
            "retrieval_failed",
            start
        )

        return output

    results = retrieval.get(
        "results",
        []
    )

    context = "\n\n".join(
        result.get(
            "text",
            ""
        )
        for result in results
    )

    answer = generate_with_ollama(
        query,
        context
    )

    citations = [
        {
            "chunk_id": result.get(
                "chunk_id"
            ),
            "source_id": result.get(
                "source_id"
            ),
            "authority_tier": result.get(
                "authority_tier"
            )
        }
        for result in results
    ]

    confidence = (
        confidence_from_results(
            results
        )
    )

    output = {
        "status": "success",
        "query": query,
        "answer": answer,
        "citations": citations,
        "confidence_category": confidence,
        "retrieval_summary": {
            "k": k,
            "retrieved_count":
                len(results),
            "top_chunk": (
                results[0].get(
                    "chunk_id"
                )
                if results
                else None
            )
        }
    }

    append_audit(
        "answer_question",
        {
            "query": query,
            "k": k,
            "caller": caller
        },
        {
            "confidence_category":
                confidence,
            "citation_count":
                len(citations)
        },
        "pass",
        "answer_generated",
        start
    )

    return output


if __name__ == "__main__":

    print(
        json.dumps(
            refresh_corpus(),
            indent=2
        )
    )