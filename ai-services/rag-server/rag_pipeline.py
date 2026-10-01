"""Shared Release 1 RAG retrieval pipeline.

This module contains the common RAG infrastructure shared across
the student features.

Feature-specific data acquisition belongs in:

    sources/student1.py
    sources/student2.py
    sources/student3.py
    sources/student4.py
    sources/student5.py

The shared RAG server indexes the trusted documents supplied by
each feature source into one shared Chroma collection.
"""

import hashlib
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import chromadb
import requests

from sources.student1 import (
    build_chunks as build_student1_chunks
)

from sources.student2 import (
    get_documents as get_student2_documents
)

from sources.student3 import (
    get_documents as get_student3_documents
)

from sources.student5 import (
    get_documents as get_student5_documents
)


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

            vectors.append(
                values
            )

            continue

        for token in tokens:

            digest = hashlib.sha256(
                token.encode("utf-8")
            ).digest()

            for i, byte in enumerate(
                digest
            ):

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

        vectors.append(
            values
        )

    return vectors


# =========================================================
# CHROMA
# =========================================================

def get_collection():

    global _collection

    client = chromadb.PersistentClient(
        path=str(
            CHROMA_PATH
        )
    )

    if _collection is None:

        _collection = (
            client.get_or_create_collection(
                name=COLLECTION_NAME
            )
        )

    return _collection


def reset_collection():

    global _collection

    client = chromadb.PersistentClient(
        path=str(
            CHROMA_PATH
        )
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
        (time.time() - start_time)
        * 1000
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
        "validation_status":
            validation_status,
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
# SOURCE NORMALISATION
# =========================================================

def normalise_student2_document(
    document: dict
) -> dict:

    """Convert a Student 2 RAG document into the shared chunk format."""

    return {
        "chunk_id": document.get(
            "chunk_id"
        ),

        "source_id": document.get(
            "source_id",
            "student2"
        ),

        "authority_tier": document.get(
            "authority_tier",
            "tier_1"
        ),

        "text": document.get(
            "text",
            ""
        ),

        "metadata": {
            "source_type": "student2_api",
            "student": "student2",
            "feature": document.get(
                "feature",
                "student-2-skill-exchange"
            ),
            "record_type": document.get(
                "record_type",
                "listing"
            ),
            "listing_id": document.get(
                "listing_id"
            ),
            "student_id": document.get(
                "student_id",
                ""
            ),
            "student_name": document.get(
                "student_name",
                ""
            ),
            "skill_offered": document.get(
                "skill_offered",
                ""
            ),
            "skill_wanted": document.get(
                "skill_wanted",
                ""
            ),
            "availability": document.get(
                "availability",
                ""
            ),
            "status": document.get(
                "status",
                ""
            ),
            "error": False
        },

        "indexed_at": now_iso()
    }


def make_source_error_chunk(
    source_name: str,
    source_type: str,
    error
) -> dict:

    return {
        "chunk_id": (
            f"{source_name}_source_error"
        ),

        "source_id": source_name,

        "authority_tier": "tier_1",

        "text": (
            f"{source_name} source is currently "
            f"unavailable: {error}"
        ),

        "metadata": {
            "source_type": source_type,
            "student": source_name,
            "error": True
        },

        "indexed_at": now_iso()
    }


# =========================================================
# CORPUS
# =========================================================

def build_corpus():

    chunks = []

    # -----------------------------------------------------
    # Student 1
    # -----------------------------------------------------

    try:

        student1 = (
            build_student1_chunks()
        )

        if student1.get(
            "status"
        ) == "success":

            student1_chunks = (
                student1.get(
                    "chunks",
                    []
                )
            )

            chunks.extend(
                student1_chunks
            )

        else:

            chunks.append(
                make_source_error_chunk(
                    "student1",
                    "student1_api",
                    student1.get(
                        "error",
                        "unknown error"
                    )
                )
            )

    except Exception as exc:

        chunks.append(
            make_source_error_chunk(
                "student1",
                "student1_api",
                str(exc)
            )
        )

    # -----------------------------------------------------
    # Student 2
    # -----------------------------------------------------

    try:

        student2_documents = (
            get_student2_documents()
        )

        if not isinstance(
            student2_documents,
            list
        ):

            raise ValueError(
                "Student 2 source returned "
                "an invalid document list"
            )

        for document in (
            student2_documents
        ):

            if not isinstance(
                document,
                dict
            ):

                continue

            chunk = (
                normalise_student2_document(
                    document
                )
            )

            if not chunk.get(
                "chunk_id"
            ):

                continue

            if not chunk.get(
                "text"
            ):

                continue

            chunks.append(
                chunk
            )

    except Exception as exc:

        chunks.append(
            make_source_error_chunk(
                "student2",
                "student2_api",
                str(exc)
            )
        )

    # -----------------------------------------------------
    # Student 3
    # -----------------------------------------------------

    try:

        student3_documents = (
            get_student3_documents()
        )

        if not isinstance(
            student3_documents,
            list
        ):

            raise ValueError(
                "Student 3 source returned "
                "an invalid document list"
            )

        for document in (
            student3_documents
        ):

            if not isinstance(
                document,
                dict
            ):

                continue

            if not document.get(
                "chunk_id"
            ):

                continue

            if not document.get(
                "text"
            ):

                continue

            chunks.append(
                document
            )

    except Exception as exc:

        chunks.append(
            make_source_error_chunk(
                "student3",
                "student3_api",
                str(exc)
            )
        )


    # -----------------------------------------------------
    # Student 5
    # -----------------------------------------------------
    
    try:
        documents = get_student5_documents()

        for document in documents:
            source_id = document["source_id"]

            chunks.append({
                "chunk_id": f"student5_{source_id}",
                "source_id": source_id,
                "authority_tier": "tier_1",
                "text": document["content"],
                "metadata": {
                    "source_type": "student5_api",
                    "student": "student5",
                    "feature": "student-5-campus-space-finder",
                },
                "indexed_at": now_iso(),
            })

    except Exception as exc:
        chunks.append(
            make_source_error_chunk(
                "student5",
                "student5_api",
                str(exc),
            )
        )

    return chunks


def write_corpus(
    chunks
):

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
                    if chunk.get(
                        "chunk_id"
                    )
                ]

                documents = [
                    chunk["text"]
                    for chunk in chunks
                    if chunk.get(
                        "chunk_id"
                    )
                ]

                metadatas = [
                    {
                        "source_id":
                            chunk.get(
                                "source_id"
                            ),

                        "authority_tier":
                            chunk.get(
                                "authority_tier"
                            ),

                        "indexed_at":
                            chunk.get(
                                "indexed_at",
                                now_iso()
                            ),

                        "student":
                            chunk.get(
                                "metadata",
                                {}
                            ).get(
                                "student",
                                ""
                            ),

                        "source_type":
                            chunk.get(
                                "metadata",
                                {}
                            ).get(
                                "source_type",
                                ""
                            ),

                        "record_type":
                            chunk.get(
                                "metadata",
                                {}
                            ).get(
                                "record_type",
                                ""
                            )
                    }

                    for chunk in chunks
                    if chunk.get(
                        "chunk_id"
                    )
                ]

                embeddings = (
                    embed_texts(
                        documents
                    )
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

        student1_count = sum(
            1
            for chunk in chunks
            if chunk.get(
                "metadata",
                {}
            ).get(
                "student"
            ) == "student1"
            or str(
                chunk.get(
                    "source_id",
                    ""
                )
            ).startswith(
                "student1"
            )
        )

        student2_count = sum(
            1
            for chunk in chunks
            if chunk.get(
                "metadata",
                {}
            ).get(
                "student"
            ) == "student2"
            or str(
                chunk.get(
                    "source_id",
                    ""
                )
            ).startswith(
                "student-2"
            )
        )

        student3_count = sum(
            1
            for chunk in chunks
            if chunk.get(
                "metadata",
                {}
            ).get(
                "student"
            ) == "student3"
            or str(
                chunk.get(
                    "source_id",
                    ""
                )
            ).startswith(
                "student-3"
            )
        )

        output = {
            "status": "success",
            "caller": caller,
            "chunk_count": len(
                chunks
            ),
            "sources": {
                "student1": student1_count,
                "student2": student2_count,
                "student3": student3_count
            },
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

RELEVANCE_STOPWORDS = {
    "who", "what", "where", "when", "why", "how",
    "is", "are", "was", "were", "be", "been",
    "the", "a", "an", "of", "to", "for", "and", "or",
    "in", "on", "with", "do", "does", "can",
    "please", "show", "find", "tell", "give", "me"
}


def relevance_tokens(
    text
):

    return [
        token
        for token in re.findall(
            r"[a-z0-9+#]+",
            (text or "").lower()
        )
        if token not in RELEVANCE_STOPWORDS
    ]


def is_source_error(
    chunk_id,
    text,
    metadata=None
):

    metadata = metadata or {}

    return (
        bool(metadata.get("error"))
        or str(
            chunk_id or ""
        ).endswith(
            "_source_error"
        )
        or (
            "source is currently unavailable"
            in (text or "").lower()
        )
    )


def relevance_score(
    query,
    text
):

    query_tokens = relevance_tokens(
        query
    )

    text_tokens = relevance_tokens(
        text
    )

    if (
        not query_tokens
        or not text_tokens
    ):

        return 0.0

    query_unique = set(
        query_tokens
    )

    text_unique = set(
        text_tokens
    )

    overlap = len(
        query_unique
        & text_unique
    )

    if overlap == 0:

        return 0.0

    coverage = (
        overlap
        / len(query_unique)
    )

    query_bigrams = set(
        zip(
            query_tokens,
            query_tokens[1:]
        )
    )

    text_bigrams = set(
        zip(
            text_tokens,
            text_tokens[1:]
        )
    )

    bigram_matches = len(
        query_bigrams
        & text_bigrams
    )

    relationship_terms = {
        "offers",
        "wants"
    }

    relationship_query = any(
        token in relationship_terms
        for token in query_tokens
    )

    # For directional Skill Exchange questions such as
    # "wants Java" or "offers Python", require that
    # relationship to occur together rather than merely
    # finding both words somewhere in the same chunk.
    if (
        relationship_query
        and len(query_tokens) >= 2
        and bigram_matches == 0
    ):

        return 0.0

    # For normal multi-term queries, require meaningful
    # lexical coverage rather than accepting one accidental
    # shared word.
    if (
        len(query_unique) > 1
        and bigram_matches == 0
        and (
            overlap < 2
            or coverage < 0.5
        )
    ):

        return 0.0

    return (
        overlap
        + coverage
        + (3 * bigram_matches)
    )


def lexical_fallback_retrieve(
    query,
    k
):

    corpus = (
        _last_corpus_chunks
        or read_corpus()
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

        metadata = (
            chunk.get("metadata")
            or {}
        )

        if is_source_error(
            chunk.get("chunk_id"),
            text,
            metadata
        ):

            continue

        score = relevance_score(
            query,
            text
        )

        if score <= 0:

            continue

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
            "_score": score
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

                collection = (
                    get_collection()
                )

            collection_count = (
                collection.count()
            )

            # The shared coursework corpus is small enough to inspect
            # every indexed chunk before applying relevance filtering.
            # This prevents weak hash-based vector ranking from hiding
            # exact lexical matches as more student sources are added.
            candidate_count = collection_count

            query_embedding = (
                embed_texts(
                    [query]
                )
            )

            results = collection.query(
                query_embeddings=query_embedding,
                n_results=candidate_count
            )

            ids = (
                results.get(
                    "ids"
                )
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
                    if index < len(
                        metadatas
                    )
                    else {}
                )

                document = (
                    documents[index]
                    if index < len(
                        documents
                    )
                    else ""
                )

                if is_source_error(
                    chunk_id,
                    document,
                    metadata
                ):

                    continue

                score = relevance_score(
                    query,
                    document
                )

                if score <= 0:

                    continue

                ranked.append({
                    "rank": 0,

                    "chunk_id": chunk_id,

                    "source_id":
                        metadata.get(
                            "source_id"
                        ),

                    "authority_tier":
                        metadata.get(
                            "authority_tier"
                        ),

                    "distance": (
                        distances[index]
                        if index < len(
                            distances
                        )
                        else None
                    ),

                    "text": document,

                    "_relevance_score":
                        score
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

                    row.get(
                        "_relevance_score",
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

            # Remove substantially weaker lexical matches after
            # ranking. This keeps equally relevant evidence together while
            # preventing loosely related records from confusing generation.
            if ranked:

                best_relevance = max(
                    row.get(
                        "_relevance_score",
                        0
                    )
                    for row in ranked
                )

                if best_relevance > 0:

                    relevance_cutoff = (
                        best_relevance * 0.75
                    )

                    ranked = [
                        row
                        for row in ranked
                        if row.get(
                            "_relevance_score",
                            0
                        ) >= relevance_cutoff
                    ]

            ranked = ranked[
                :max(k, 1)
            ]

            for index, row in enumerate(
                ranked,
                start=1
            ):

                row["rank"] = index

                row.pop(
                    "_relevance_score",
                    None
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

    if (
        tier_1 >= 2
        and len(results) >= 3
    ):

        return "High"

    if (
        tier_1 >= 1
        or tier_2 >= 2
    ):

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
        "llama3.1:8b"
    )

    ollama_url = os.getenv(
        "OLLAMA_GENERATE_URL",
        "http://localhost:11434/api/generate"
    )

    prompt = f"""
You are a retrieval-grounded project management assistant.

Use ONLY the provided context.

Do not invent project or Skill Exchange information.

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

    if not results:

        output = {
            "status": "insufficient_context",
            "query": query,
            "answer": "Insufficient context.",
            "citations": [],
            "confidence_category": "Insufficient",
            "retrieval_summary": {
                "k": k,
                "retrieved_count": 0,
                "top_chunk": None
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
                    "Insufficient",
                "citation_count": 0
            },
            "pass",
            "insufficient_context",
            start
        )

        return output

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
        "confidence_category":
            confidence,
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


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    print(
        json.dumps(
            refresh_corpus(),
            indent=2
        )
    )