# Architectural Gaurdrails

1. No hard-coded absolute paths.
2. All thresholds defined in config file.
3. Embedding model configurable.
4. All file storage within defined data directory.
5. No hidden global state.
6. Version change required before activation.
7. No automatic policy generation.
8. All lifecycle actions logged.
9. Retrieval and version registry logically separated.
10. Notebook experiments must migrate reusable logic to core modules.
11. Docker-ready structure (no OS assumptions).
12. Single application entry point.
13. Generation must not execute outside HIGH threshold band.
14. Mutation must rebuild full index — no partial FAISS mutation.
15. Success flag derived from retrieval outcome, not generation result.
