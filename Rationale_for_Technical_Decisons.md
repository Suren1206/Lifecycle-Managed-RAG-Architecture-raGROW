# Rationale_of_Technical_Decisions.md
## 1. SQLite for Metadata (Instead of JSON)
Chosen:
SQLite

### Why:

    • Supports relational mapping (Document → Chunk → Version → Interaction).
    • Transaction-safe (ACID).
    • Clean audit capability.
    • Required for lifecycle governance.
    • Container-friendly (single file DB).
Not JSON because:
    • No structured querying.
    • No transaction safety.
    • Harder to maintain referential integrity.
    • Weak for version lifecycle control.

## 2. FAISS-First Strategy
Chosen:
Raw FAISS as primary vector index.

### Why:

    • Deep understanding of vector mechanics.
    • Full control over lifecycle behavior.
    • Clean separation from governance layer.
    • Educational value aligned with Trinity Goal.
Not Chroma-first because:
    • Abstracts internal mechanics.
    • Reduces architectural learning depth.
    • CRUD simplicity is not primary goal.
Chroma may be used later for comparison.

## 3. Hybrid Staging (Metadata in SQLite + Filesystem Content)
Chosen:
Hybrid.
### Why:

    • Clear separation of governance and content.
    • Cleaner audit trail.
    • Avoid DB bloat.
    • Enterprise-aligned architecture.
    • Easier debugging and inspection.
Not DB-only because:
    • Monolithic design.
    • Harder to separate lifecycle from content.
Not file-only because:
    • Weak transactional integrity.
    • Harder to audit.

## 4. Timestamp-Based Versioning
Chosen:
YYYYMMDD_B01 / YYYYMMDD_E01 format.
### Why:

    • Instant governance visibility.
    • BAU accountability signaling.
    • Audit clarity.
    • No added architectural complexity.
Not sequential numbering because:
    • No visible activation timing.
    • Weak governance transparency.

## 5. Separate FAISS Index Per Version
Chosen:
New index per activation.
### Why:

    • Clean rollback.
    • No in-place mutation risk.
    • Governance-aligned lifecycle.
    • Simplifies audit.
Not in-place mutation because:
    • Harder rollback.
    • Higher corruption risk.

## 6. Batch Activation for Modifications
Chosen:
Periodic batch version build for modifications.
Emergency activation for Add/Delete only.
### Why:

    • Resource control.
    • Realistic BAU behavior.
    • Reduced index churn.
    • Governance clarity.
Not per-change versioning because:
    • Operational noise.
    • Excessive version count.

## 7. Embedding & LLM (Local)
Embedding:
mxbai-embed-large
LLM:
llama3.2:3b
### Why:
    • Economical.
    • Container-ready.
    • Strong semantic performance.
    • Suitable for structured policy editing.
Not API-based because:
    • Cost sensitivity.
    • Deployment independence.

## 8. Chunking Strategy (Superseded in Milestone 6)

Original Design:
    • 500 token chunk size
    • 150 token overlap
Rationale at the time:
    • Semantic coherence
    • Good modification granularity
    • Stable similarity behavior
    • Suitable for policy text structure

Note: Token-based chunking as superseded; Character-based deterministic slicing adopted in Milestone 6 to align chunking with lifecycle determinism and atomic batch rebuild semantics.

## 9. Structured Conversational Summary
Chosen:
Structured summary (Topic / Intent / Keywords).
## Why:
    • Better retrieval stability.
    • Predictable context.
    • Future analytics capability.
    • Governance alignment.
Not free-text summary because:
    • Reduced control.
    • Harder debugging.

## 10. Re-ranking Policy
Chosen:
No re-ranking initially.
### Why:

    • Simpler system.
    • Observe empirical behavior first.
    • Escalate only if justified.
Not immediate cross-encoder because:
    • Unnecessary complexity.
    • Resource overhead.

## 11. Streamlit UI
Chosen:
Streamlit.
### Why:

    • Rapid development.
    • Python-native.
    • Easy admin interface.
    • Container-friendly.
Not heavy frontend because:
    • Not Phase I goal.


## 12. Controlled Generation Gating (Milestone 9.5)
Chosen:
Generation invoked only for High-confidence retrieval (≥ 0.75).
Rank-1 chunk only.
Temperature = 0.
max_tokens = 300.
Why:
    • Prevent hallucination drift.
    • Preserve governance authority.
    • Ensure deterministic lifecycle analytics.
    • Maintain retrieval-first architecture.
Not:
    • No generation in MID band.
    • No multi-chunk concatenation.
    • No free-form speculative answering.


