**raGROW** is a governed Retrieval-Augmented Generation (RAG) system designed to support disciplined, version-controlled evolution of HR policy knowledge bases through structured human review.
Unlike typical RAG implementations that prioritize flexibility, raGROW is built around **governance, lifecycle integrity, and controlled growth**. Knowledge expansion occurs only when validated retrieval gaps are observed, ensuring that corpus evolution remains need-driven and evidence-based.
raGROW treats knowledge not as static content but as a managed asset that must evolve under oversight.

# Project Philosophy
Most RAG systems operate as utilities. raGROW was designed as a **governed knowledge engine**.
Core principles:
- Growth must be intentional
- Retrieval must be measurable
- Generation must be gated
- Mutation must be governed
The system does not self-learn and does not mutate its corpus autonomously.
Every change is human-reviewed, version-controlled, and auditable.

# Phase I Capabilities
Phase I establishes the governance and lifecycle foundation.
Core features include:
- Sentence-boundary chunking (minimum 300 characters, no overlap)
- FAISS cosine similarity retrieval (IndexFlatIP)
- Similarity band routing (0.75 / 0.60 thresholds)
- Controlled generation limited to HIGH similarity band
- Version lifecycle governance (STAGING → ACTIVE)
- Maker–Checker mutation approval workflow
- Batch mutation engine supporting ADD / MODIFY / DELETE
- Automatic full rebuild after approved mutation batches
- Single ACTIVE version enforcement
- SQL-based interaction logging and analytics
- Rollback-safe activation
- Role-separated Streamlit interface
Supported roles:
  - Employee
  - Maker
  - Checker
  - Admin

# Architecture Principles
raGROW follows strict operational constraints:
• No in-place vector mutation
• No uncontrolled memory injection
• No generation without retrieval authority
• No automatic corpus growth
• Full version traceability
These constraints ensure predictable lifecycle behavior and auditability.

# Repository Structure
```
app.py                         # Streamlit role-based UI
rag_engine/
    retriever.py              # FAISS retrieval logic
    generator.py              # Controlled generation
    mutation_batch.py         # Batch mutation processor
    logger.py                 # Version registry + interaction logging
    build_pipeline.py         # Corpus rebuild and vector creation
data/
    master_corpus.txt         # Canonical mutable corpus
    vector_store/             # Versioned FAISS indices
logs/
    rag_logs.db               # Governance database							
```
Note: Replace master_corpus_sample.txt with your own policy corpus and rename it to master_corpus.txt.

# Running the System
**Prerequisites**

• Python 3.10+

• Ollama running locally

• Embedding model available (mxbai-embed-large)


## Step 1 — Build Initial Version
```
python -m rag_engine.build_pipeline

```
This creates:
```
data/vector_store/<version_id>

```
The version is registered as STAGING.

## Step 2 — Start the Interface
```
streamlit run app.py

```

## Step 3 — Role Workflows
**Checker**
- Activate STAGING version
- Review pending mutation batches
- Approve or reject mutations
- Promote STAGING → ACTIVE
  
**Employee**
- Submit HR questions
- Retrieval thresholds determine response behavior
  
HIGH similarity → answer generated

MID similarity → rephrase request

LOW similarity → regret response

**Maker**
- Submit corpus mutations
- ADD / MODIFY / DELETE policy blocks
  
**Admin**
- View registry overview
- Monitor analytics and interaction logs
  

# Trinity Goals Behind raGROW
raGROW was developed with three objectives:
##    1. Deep Technical Mastery
Understanding RAG internals beyond abstraction — chunking behavior, embedding structure, lifecycle governance, and retrieval calibration.
##    2. Governed Knowledge Infrastructure
Demonstrating that RAG can function as structured Business-As-Usual infrastructure rather than experimental automation.
##    3. Professional Engineering Discipline
Building a system that reflects lifecycle thinking, architecture integrity, and operational governance.

## Phase II (Planned)

Phase II will extend raGROW in three directions:

1. Emergency controlled incremental update mode
2. Retrieval accuracy calibration experiments
3. Cloud-native deployment architecture

# Closing Note

raGROW began with a simple question:

**What if RAG could grow — but with discipline?**

The result is a lifecycle-governed system capable of controlled mutation, version integrity, and measurable oversight.

It is not built for demonstration.

It is built for sustainable knowledge growth.


