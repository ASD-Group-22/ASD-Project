# Shared RAG Server

Release 1 uses one shared local Retrieval-Augmented Generation (RAG) server for
all five student features.

Feature-specific trusted data integration is separated into:

- `sources/student1.py`
- `sources/student2.py`
- `sources/student3.py`
- `sources/student4.py`
- `sources/student5.py`

The shared RAG infrastructure is responsible for common retrieval, indexing and
grounded-response behaviour.

## Grounding Requirements

A grounded answer should be based on retrieved trusted application context.

Supported responses should provide source/citation information and confidence
information where required by the Release 1 design.

If relevant supporting context cannot be retrieved, the system should return an
insufficient-context result rather than inventing unsupported information.

## Ownership

Each student primarily maintains their own `sources/studentX.py` module.

Changes to shared retrieval behaviour should be coordinated with the team.
