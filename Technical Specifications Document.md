# Technical_Specification_Phase_I.md
## 1. Retrieval Behavior
    • Similarity metric: Cosine
    • top_k: 5
    • Thresholds:
        ◦ High ≥ 0.75
        ◦ Mid 0.60–0.74
        ◦ Low < 0.64
    • Calibration required after empirical observation.
   
## 1A. Chunking Strategy
Chunking Strategy (v2 – Lifecycle Deterministic)
Character-based fixed window slicing (800 characters).***
No overlap.
Deterministic across builds.
Similarity Metric: Cosine similarity implemented via L2 normalization + FAISS IndexFlatIP.
Deterministic slicing required for lifecycle rebuild stability

## *** Refined during v2 with Sentence boundary = period (.) only 
Minimum chunk size = 300 characters. Chunk ends at first full stop after ≥ 300 chars. No overlap.
Modified based on empirical analysis (enclosed – raGROW_test_cases_v2.ods).


## 3. Rephrase Logic

    1. If similarity < 0.60:
        ◦ Request one rephrase.
        
    2. If revised query also < 0.60:    
        ◦ Log to Add Item registry.        
        ◦ Return regret message.
        
    3. No further retries allowed.

## 4. Conditional Confirmation (Mid-Range)

If similarity between 0.60–0.75:

    • Request one rephrase.
    
    • If rephrase fails → log and regret.

## 5. Session Management

    • Maximum 3 user turns per session.
    
    • After 3rd turn:
    
        ◦ Inform user to start a new query.
        
    • Session memory reset.

## 6. Conversational Memory

    • Phase I memory limited to UI transcript display.
    
    • Retrieval input: Latest Query only.
    
    • Structured summarization deferred to Phase II.
    
    • Transcript stored for display only.
    

## 7. Versioning Policy
Format
YYYYMMDD_BXX
YYYYMMDD_EXX
Activation
    • Modifications → Batch only.
    
    • Add/Delete → May trigger emergency activation.
    
    • Every activation creates new FAISS index.
    
    • No in-place FAISS mutation.
    
Retention
    • Active version retained.
    
    • Immediate previous retained.
    
    • Older archived.
    

## 8. Staging Policy

Hybrid:
    • Metadata in SQLite.
    
    • Content as staged files.
    
    • Batch activation builds new version from active + staged.

## 9. Re-ranking Escalation

Not implemented in Phase I.
Escalation only after empirical justification.

## 10. Governance Integrity

    • Dual Maker/Checker approval.
    
    • No automatic growth.
    
    • Active version pointer stored in SQLite.
    
    • Full version ID stored in interaction logs.
    

## 11. UI Layer (Streamlit)

Phase I UI implemented using Streamlit.

UI will include:

    1. Employee Interface
    
        ◦ Query input
        ◦ Response display
        ◦ Confirmation radio (mid-range)
        ◦ Session history        
    2. Maker Interface
    
        ◦ View Add Item entries
        ◦ Draft content
        ◦ Submit for approval
    3. Checker Interface
    
        ◦ Approve / Reject / Request modification
    4. Admin Dashboard
    
        ◦ Version history
        ◦ Active version indicator
        ◦ Activation log
        ◦ Rollback control

Streamlit chosen for:
    • Rapid iteration
    • Python-native integration
    • Container readiness
    • Governance dashboard ease
## 12. Data & Naming Conventions

    • Metadata database file: metadata.db
    
    • Vector indices stored under: data/vector_store/
    
    • Index filename format: <version_id>.index
    
    • Staging content directory: data/staging/
    
    • Raw document directory: data/raw_docs/
    
    • Processed document directory: data/processed/
    
    • Interaction logs table: interaction_logs
    
    • Version registry table: version_registry
    
## 13. Interaction Identity

    • Each session assigned a UUID session_id.
    
    • Each user turn assigned a UUID interaction_id.
    
    • Each interaction linked to:
    
        ◦ session_id
        
        ◦ version_id
        
        ◦ similarity score
        
        ◦ confirmation status
        
    • Interaction logs stored in interaction_logs table.

