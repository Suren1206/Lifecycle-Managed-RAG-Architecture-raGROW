# Rationale of Technical Decisions

---

# 1. SQLite for Metadata (Instead of JSON)

### Chosen
**SQLite**

### Why

- Supports relational mapping *(Document → Chunk → Version → Interaction)*
- Transaction-safe *(ACID)*
- Clean audit capability
- Required for lifecycle governance
- Container-friendly *(single-file database)*

### Not JSON because

- No structured querying
- No transaction safety
- Harder to maintain referential integrity
- Weak support for version lifecycle control

---

# 2. FAISS-First Strategy

### Chosen

**Raw FAISS as primary vector index**

### Why

- Deep understanding of vector mechanics
- Full control over lifecycle behavior
- Clean separation from governance layer
- Educational value aligned with **Trinity Goal**

### Not Chroma-first because

- Abstracts internal mechanics
- Reduces architectural learning depth
- CRUD simplicity is not the primary goal

Chroma may be used later **for comparison purposes**.

---

# 3. Hybrid Staging  
*(Metadata in SQLite + Filesystem Content)*

### Chosen

**Hybrid Architecture**

### Why

- Clear separation of **governance and content**
- Cleaner audit trail
- Avoid database bloat
- Enterprise-aligned architecture
- Easier debugging and inspection

### Not DB-only because

- Monolithic design
- Harder to separate lifecycle logic from content

### Not File-only because

- Weak transactional integrity
- Harder to audit

---

# 4. Timestamp-Based Versioning

### Chosen

```
<timestamp>_<sequence>
Example:
20260320_01
20260320_02

```

### Why

- Instant governance visibility
- BAU accountability signaling
- Audit clarity
- No additional architectural complexity

### Not Sequential Numbering because

- No visible activation timing
- Weak governance transparency

---

# 5. Separate FAISS Index Per Version

### Chosen

**New index created per activation**

### Why

- Clean rollback capability
- Eliminates in-place mutation risk
- Governance-aligned lifecycle control
- Simplifies auditability

### Not In-Place Mutation because

- Harder rollback
- Higher corruption risk

---

# 6. Batch Activation for Modifications

### Chosen

- **Periodic batch version builds** for modifications
- **Emergency activation** allowed for Add/Delete only

### Why

- Resource control
- Realistic BAU operational behavior
- Reduced index churn
- Clear governance model

### Not Per-Change Versioning because

- Operational noise
- Excessive version proliferation

---

# 7. Embedding & LLM (Local Deployment)

### Embedding Model

**mxbai-embed-large**

### LLM

**llama3.2:3b**

### Why

- Economical
- Container-ready
- Strong semantic performance
- Suitable for structured policy editing

### Not API-Based because

- Cost sensitivity
- Deployment independence

---

# 8. Chunking Strategy  
*(Superseded in Milestone 6)*

### Original Design

- 500 token chunk size
- 150 token overlap

### Rationale at the Time

- Semantic coherence
- Good modification granularity
- Stable similarity behavior
- Suitable for policy text structure

### Current Design

Token-based chunking was **superseded**.

Character-based deterministic slicing adopted in **Milestone 6** to align chunking with:

- Lifecycle determinism
- Atomic batch rebuild semantics

### v2 Refinement

- Sentence boundary = **period (.) only**
- Minimum chunk size = **300 characters**
- Chunk ends at **first full stop after ≥ 300 characters**
- **No overlap**

Modified based on empirical analysis.

Reference file:

```
raGROW_test_cases_v2.ods
```

---

# 9. Conversational Memory Handling

### Phase I Implementation

The system **does not maintain conversational memory for retrieval**.

Each query is processed independently after rephrasing.

This design improves:

- Retrieval stability
- Debugging clarity during foundational system development

### Retrieval Input

**Rephrased latest query only**

### Transcript Handling

Conversation transcripts are stored only for:

- Logging
- Analytics
- UI display

They are **not used as retrieval context**.

### Future Consideration (Phase II)

Structured conversational summaries may be introduced:

- Topic
- Intent
- Keywords
- Condensed text

Purpose:

Support **multi-turn contextual retrieval** after the retrieval layer stabilizes.

---

# 10. Re-ranking Policy

### Chosen

**No re-ranking in Phase I**

### Why

- Simpler architecture
- Observe empirical behavior first
- Escalate only if justified

### Not Immediate Cross-Encoder because

- Unnecessary complexity
- Resource overhead

---

# 11. Streamlit UI

### Chosen

**Streamlit**

### Why

- Rapid development
- Python-native environment
- Simple administrative interface
- Container-friendly

### Not Heavy Frontend because

- Not a Phase I goal

---

# 12. Controlled Generation Gating  

### Chosen

Generation invoked **only for High-confidence retrieval**

- Similarity ≥ **0.75**
- **Rank-1 chunk only**
- **Temperature = 0**
- **max_tokens = 300**

### Why

- Prevent hallucination drift
- Preserve governance authority
- Ensure deterministic lifecycle analytics
- Maintain retrieval-first architecture

### Not Allowed

- No generation in **MID band**
- No multi-chunk concatenation
- No speculative answering


