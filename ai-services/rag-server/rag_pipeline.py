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
