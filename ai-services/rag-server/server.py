"""Shared Release 1 RAG server.

Provides the local HTTP interface for shared RAG operations.

The final server is expected to coordinate operations such as:
- health/status checking
- corpus refresh/indexing
- retrieval
- grounded answer generation

Feature-specific trusted data is provided through the modules under sources/.
"""
