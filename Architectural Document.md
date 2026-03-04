# raGROW Architecture Document

## 1. System Boundary

raGROW is a governed Retrieval-Augmented Generation system designed for **controlled, versioned knowledge growth of HR policy documents** through **human-reviewed updates triggered by validated retrieval failures**.

### Phase I Scope

- Domain: **HR policy documents only**
- Source type: **Word or PDF documents only**
- **Single-domain deployment**
- **No autonomous growth**
- LLM acts only as **editorial assistant**
- Conversational interface with **controlled memory**
- **Dual-layer approval (Maker–Checker)**
- **Version-controlled lifecycle**

### raGROW is NOT

- A general chatbot
- A multi-domain ingestion engine
- A self-learning system
- A sentiment or analytics tool *(Phase II only)*

---

# 2. Actors

## 2.1 Employee User

- Submits queries
- Sees session history
- Confirms doubtful responses
- Does **not see version metadata**

## 2.2 Maker (Level 1 Reviewer)

- Reviews captured failures
- Drafts content updates
- Uses LLM for **structured refinement**
- Submits updates for approval

## 2.3 Checker (Level 2 Approver)

- Approves / Rejects / Requests modification
- Timestamped actions
- Required for **activation**

## 2.4 raGROW Core System

- Handles retrieval
- Applies similarity thresholds
- Logs interactions
- Maintains version registry
- Executes controlled re-embedding
- Activates approved versions

---

# 3. Core Logical Modules

## 3.1 Ingestion Module

Responsibilities:

- Parse documents
- Chunk content
- Generate embeddings
- Store vectors + metadata
- Assign **Version ID**

---

## 3.2 Retrieval Module

Processes:

- Query embedding
- Similarity search
- Threshold routing

Retrieval insufficiency defined as:

- **Low similarity score**, or
- **Negative user confirmation**

### Similarity Thresholds

*(Recalibrated during Milestone 9.5 after empirical embedding score analysis)*

- **High ≥ 0.75**
- **Mid 0.60 – 0.74**
- **Low < 0.60**

---

## 3.3 Output Module

Three response pathways:

- **Confirmed Response** (High similarity only)
- **Rephrase Required** (Mid similarity)
- **Regret Response** (Low similarity)

---

## 3.4 Conversational Memory Module

- **Session-based memory**
- Maximum **3 user turns per session**
- Session reset after turn limit
- Internal metadata **hidden from user**

Phase I retrieval uses **latest query only**.  
Transcript stored for display purposes.

Structured summarization deferred to **Phase II**.

---

## 3.5 Failure Capture Module

Captured metadata:

- Interaction ID
- Query text
- Similarity score
- Retrieved chunk references
- User confirmation
- Version ID
- Timestamp

---

## 3.6 Review & Growth Module

Lifecycle:

```
Failure Log
→ Maker Draft
→ LLM Refinement
→ Checker Approval
→ Version Update
```

No automatic growth permitted.

---

## 3.7 Version Registry Module  
*(Background Service + Audit View)*

Stores:

- Version ID
- Change type *(Add / Modify / Delete)*
- Affected documents
- Approval chain
- Timestamp
- Active version pointer

Provides:

- Version history view
- Rollback capability
- Active version indicator

---

## 3.8 Controlled Re-Embedding Module

Supports:

- Incremental addition
- Selective modification *(remove + re-embed chunks)*
- Selective deletion
- Scheduled refresh if required

Old versions are **preserved**.

Mutation engine performs **full version rebuild**.

No incremental vector patching in **Phase I**.

---

## 3.9 Reporting Module

Tracks:

- Total interactions
- High-confidence responses
- Rephrase opportunities
- Regret responses
- Version-based activity

---

# Lifecycle Flow

```
Query
  ↓
Retrieval
  ↓
Output
  ↓
Failure Capture
  ↓
Review Cycle
  ↓
Version Update
  ↓
Controlled Re-Embedding
  ↓
New Version Activated
```

