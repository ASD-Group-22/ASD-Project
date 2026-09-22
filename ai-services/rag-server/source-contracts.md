# RAG Source Contracts

Each feature contributes trusted application data to the single shared Release 1
RAG service.

## Source Boundary

Feature data should be obtained through the owning feature's backend/API.

Shared RAG infrastructure and feature source adapters should not directly
access feature database files or tables.

## Source Interface

Each `sources/studentX.py` module exposes:

`get_documents()`

The function returns a list of document dictionaries suitable for ingestion by
the shared RAG pipeline.

A document should eventually contain enough information to identify:

- the content used for retrieval
- the owning feature
- the source record or source identifier
- metadata required for grounding/citations

The exact shared document schema should remain consistent across all five
features once agreed by the team.

## Ownership

Students should primarily modify their own feature-specific source module.
Changes to the common source contract should be coordinated with the team.
