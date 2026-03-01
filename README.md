raGROW is a governed Retrieval-Augmented Generation (RAG) system designed to enable disciplined, version-controlled evolution of HR policy knowledge bases through structured human review.
Unlike generic RAG implementations that prioritize flexibility, raGROW is built around governance, lifecycle integrity, and controlled growth.
Growth is initiated only when user interactions reveal validated retrieval gaps, ensuring expansion is need-driven and evidence-based.
raGROW treats knowledge not as static content — but as an asset that must evolve need-based and  under oversight.

# Project Philosophy
Most RAG systems are deployed as utilities.
raGROW was designed as a regulated knowledge engine.
Its core premise is simple:
Growth must be intentional.
Retrieval must be measurable.
Generation must be gated.
Mutation must be governed.
This system is not a chatbot.
It is not autonomous.
It does not self-learn.
Every expansion is human-reviewed.
Every activation is versioned.
Every interaction is auditable.

# Phase I Capabilities
Phase I establishes the structural foundation:

    • Deterministic chunking (800-character fixed window)
    
    • Cosine similarity retrieval (FAISS IndexFlatIP)
    
    • Threshold-based routing (0.75 / 0.60)
    
    • Controlled generation (HIGH band only)
    
    • Version lifecycle governance (STAGING → ACTIVE)
    
    • Maker–Checker approval discipline
    
    • Full rebuild mutation engine (ADD / MODIFY / DELETE)
    
    • Single ACTIVE invariance enforcement
    
    • Governance analytics via SQL-backed reporting
    
    • Rollback-safe activation
    
    • Streamlit-based role-separated UI
    
The system supports:
Employee
Maker
Checker
Admin
with strict isolation and lifecycle discipline.

# Architecture Principles
    • No in-place vector mutation
    • No uncontrolled memory injection
    • No generation without retrieval authority
    • No automatic knowledge growth
    • No hard-coded environment assumptions
    • Full version traceability

## Folder Structure (Key Components)

```text
app.py                         # Streamlit UI (role-based routing)

rag_engine/
    retriever.py              # FAISS retrieval logic
    generator.py              # Controlled generation layer
    mutation_engine.py        # Corpus mutation (ADD/MODIFY/DELETE)
    logger.py                 # Version registry + interaction logging
    build_pipeline.py         # Vector rebuild process

data/
    master_corpus.txt         # Canonical mutable corpus
    vector_store/             # Versioned FAISS indices

logs/
    rag_logs.db               # Governance database

## Note : Replace master_corpus_sample.txt with your own HR policy corpus and rename to master_corpus.txt before running.

```


## How to Run
______________________________________________________

### 1) Pre-requisites
        a) Install dependencies (Python 3.10+ recommended)
        b) Ensure Ollama is running locally
        c) Make sure the embedding model is available (mxbai-embed-large:335m)

### 2) To start using the tools
Step 1 : Run 
```text
python -m rag_engine.build_pipeline
```
This creates:
    data/vector_store/<version_id>/
    
    Registers the version as STAGING in logs
    
    This file needs to run if we want to start a FRESH batch
    
Step 2 : Run 
```text
streamlit run app.py
```

#### Step 3 : 
    a) Select role from sidebar: Maker
    Activate Batch number shown by the tool
    Confirmation message on new batch shown.
    b) Choose role from sidebar : Employee
    Start asking your HR questions (3 independent questions at a time)
         Can refresh (^R) and ask more questions
    Maker option helps for mutation - ADD, MODIFY and DELETE
    Checker option helps to promote a new batch (after running rag_engine.build_pipleine.py); 
        We can also observe the logging here for quick monitoring
    Admin option gives Dashboad,Overview of Registry and Analytics
____________________________________________________________
# Trinity Goals Behind raGROW
raGROW was developed under three simultaneous intentions:

    1. Deep Technical Mastery
    
To understand RAG internals beyond abstraction — chunking mechanics, embedding behavior, lifecycle integrity, similarity calibration, governance analytics.

    2. Production-Ready Governance Tool
    
To demonstrate that RAG can operate as structured Business-As-Usual infrastructure rather than experimental automation.

    3. Professional Differentiation
    
To build a system that reflects architectural rigor, lifecycle thinking, and engineering discipline beyond typical prototype implementations.


# Phase II (Planned)

Phase II will extend raGROW in three focused directions:

    1. Emergency Controlled Incremental Mode
    
    2. Optimization of accuracy through calibration experiments
    
    3. Cloud-native deployment architecture
    
No additional scope is planned under Phase II.


# Follow-Up Research Track
A separate precision-first research initiative will build on lessons from raGROW.

That project will focus on:
    • Objective retrieval optimization frameworks
    
    • Chunking strategy evaluation
    
    • Embedding structure analysis
    
    • Semantic validation methodologies
    
    • Corpus-independent design principles
    
Where raGROW is governance-first, 

the next research track will be precision-first.

# Closing Note
raGROW began as a simple idea:

What if RAG could grow — but with discipline?

It evolved into a lifecycle-governed system capable of controlled mutation, version integrity, and measurable oversight.

It is not built to impress a demo.

It is built to endure growth.
