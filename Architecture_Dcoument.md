# raGROW – Phase I Architectural Document 
## 1. System Boundary
raGROW is a governed Retrieval-Augmented Generation system designed for controlled, versioned knowledge growth of HR policy documents through human-reviewed updates triggered by validated retrieval failures.
Phase I Scope:
    • Domain: HR policy documents only
    • Source type: Word or PDF documents only
    • Single-domain deployment
    • No autonomous growth
    • LLM acts only as editorial assistant
    • Conversational interface with controlled memory
    • Dual-layer approval (Maker–Checker)
    • Version-controlled lifecycle
raGROW is not:
    • A general chatbot
    • A multi-domain ingestion engine
    • A self-learning system
    • A sentiment or analytics tool (Phase II only)

## 2. Actors
### 1. Employee User
    • Submits queries
    • Sees session history
    • Confirms doubtful responses
    • Does not see version metadata
### 2. Maker (Level 1 Reviewer)
    • Reviews captured failures
    • Drafts content updates
    • Uses LLM for structured refinement
    • Submits for approval
### 3. Checker (Level 2 Approver)
    • Approves / Rejects / Requests Modification
    • Timestamped actions
    • Required for activation
### 4. raGROW Core System
    • Handles retrieval
    • Applies thresholds
    • Logs interactions
    • Maintains version registry
    • Executes controlled re-embedding
    • Activates approved versions

## 3. Core Logical Modules
### 3.1 Ingestion Module
    • Parse documents
    • Chunk content
    • Embed
    • Store vector + metadata
    • Assign Version ID

### 3.2 Retrieval Module
    • Query embedding
    • Similarity search
    • Threshold routing
Retrieval insufficiency defined as:
    • Low similarity score OR
    • Negative user confirmation
Add note:
Thresholds recalibrated in Milestone 9.5 after empirical embedding score analysis
High ≥ 0.75 ; Mid 0.60–0.74; Low < 0.60

### 3.3 Output Module
Three pathways:
    • Confirmed Response (High only)
    • Rephrase Required (Mid)
    • Regret (Low)
       

### 3.4 Conversational Memory Module
    • Session-based
    • Max turn limit (3)
    • Reset after limit
    • Internal metadata hidden from user
Phase I retrieval uses latest query only. Transcript stored for display. Structured summarization deferred to Phase II

### 3.5 Failure Capture Module
Logs:
    • Interaction ID
    • Query text
    • Similarity score
    • Retrieved chunk references
    • User confirmation
    • Version ID
    • Timestamp

### 3.6 Review & Growth Module
Lifecycle:
Failure Log → Maker Draft → LLM Refinement → Checker Approval → Version Update
No automatic growth.

### 3.7 Version Registry Module (Background + Audit View)
Stores:
    • Version ID
    • Change type (Add/Modify/Delete)
    • Affected documents
    • Approval chain
    • Timestamp
    • Active version pointer
Provides:
    • Version history view
    • Rollback capability
    • Active version indicator

### 3.8 Controlled Re-Embedding Module
Supports:
    • Incremental addition
    • Selective modification (remove + re-embed chunks)
    • Selective deletion
    • Scheduled refresh if needed
Old versions preserved.
Mutation engine performs full version rebuild. No incremental vector patching in Phase I

### 3.9 Reporting Module
Tracks:
    • Total interactions
    • High-confidence responses
    • Conditional confirmations
    • Regret responses
    • Version-based activity

Lifecycle Flow
Query
→ Retrieval
→ Output
→ Failure Capture
→ Review Cycle
→ Version Update
→ Controlled Re-Embedding
→ New Version Activated
