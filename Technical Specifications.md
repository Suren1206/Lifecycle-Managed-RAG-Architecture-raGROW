# raGROW Operational Specification

## 1. Retrieval Behavior

- **Similarity Metric:** Cosine  
- **top_k:** 5  

**Thresholds**

- High ≥ 0.75  
- Mid 0.60 – 0.74  
- Low < 0.60  

Calibration required after empirical observation.

---

## 1A. Chunking Strategy

**Chunking Strategy (v2 – Lifecycle Deterministic)**

- Character-based fixed window slicing (**800 characters**)  
- **No overlap**
- **Deterministic across builds**

**Similarity Metric**

Cosine similarity implemented via **L2 normalization + FAISS IndexFlatIP**

Deterministic slicing required for **lifecycle rebuild stability**

**Refinement introduced during v2**

- Sentence boundary = **period (.) only**
- Minimum chunk size = **300 characters**
- Chunk ends at **first full stop after ≥ 300 characters**
- **No overlap**

Modified based on empirical analysis  
*(Reference: raGROW_test_cases_v2.ods)*

---

## 2. Rephrase Logic

1. If similarity **< 0.60**
   - Request **one rephrase**

2. If revised query also **< 0.60**
   - Log to **Add Item registry**
   - Return **regret message**

3. **No further retries allowed**

---

## 3. Conditional Confirmation (Mid-Range)

If similarity between **0.60 – 0.75**

- Request **one rephrase**
- If rephrase fails
  - Log to registry
  - Return regret message

---

## 4. Session Management

- Maximum **3 user turns per session**

After the **3rd turn**

- Inform user to **start a new query**
- **Session memory reset**

---

## 5. Conversational Memory

- Phase I memory limited to **UI transcript display**
- Retrieval input uses **latest query only**
- **Structured summarization deferred to Phase II**
- Transcript stored for **display purposes only**

---

## 6. Versioning Policy

### Format

```
YYYYMMDD_BXX
YYYYMMDD_EXX
```

### Activation

- Modifications → **Batch only**
- Add/Delete → **May trigger emergency activation**
- Every activation creates **new FAISS index**
- **No in-place FAISS mutation**

### Retention

- **Active version retained**
- **Immediate previous retained**
- Older versions **archived**

---

## 7. Staging Policy

Hybrid staging model:

- **Metadata stored in SQLite**
- **Content stored as staged files**

Batch activation builds new version from:

```
Active Version + Staged Changes
```

---

## 8. Re-ranking Escalation

Not implemented in **Phase I**

Escalation allowed **only after empirical justification**

---

## 9. Governance Integrity

- **Dual Maker / Checker approval**
- **No automatic corpus growth**
- **Active version pointer stored in SQLite**
- **Full version ID recorded in interaction logs**

---

## 10. UI Layer (Streamlit)

Phase I UI implemented using **Streamlit**

### Employee Interface

- Query input
- Response display
- Confirmation radio (mid-range)
- Session history

### Maker Interface

- View **Add Item entries**
- Draft new content
- Submit mutation for approval

### Checker Interface

- Approve
- Reject
- Request modification

### Admin Dashboard

- Version history
- Active version indicator
- Activation logs
- Rollback control

**Streamlit chosen for**

- Rapid iteration
- Python-native integration
- Container readiness
- Governance dashboard simplicity

---

## 11. Data & Naming Conventions

- Metadata database: **metadata.db**
- Vector indices directory: `data/vector_store/`
- Index filename format: `<version_id>.index`
- Staging directory: `data/staging/`
- Raw document directory: `data/raw_docs/`
- Processed document directory: `data/processed/`

**Database Tables**

- `interaction_logs`
- `version_registry`

---

## 12. Interaction Identity

- Each session assigned a **UUID `session_id`**
- Each user turn assigned a **UUID `interaction_id`**

Each interaction records:

- `session_id`
- `version_id`
- similarity score
- confirmation status

All interaction records stored in **interaction_logs table**
