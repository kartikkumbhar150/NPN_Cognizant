"""RAG infrastructure: embeddings, Qdrant store, chunking, ingestion, retrieval.

Provider-neutral: Qdrant SDK types never leave ``qdrant_store``, and the
embedding backend never leaks outside ``embeddings``.
"""
