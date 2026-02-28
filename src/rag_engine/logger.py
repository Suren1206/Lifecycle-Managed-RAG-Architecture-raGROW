import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
import uuid


BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
DB_PATH = LOG_DIR / "rag_logs.db"


# ============================================================
# Database Initialization
# ============================================================

def _initialize_db() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # ----------------------------------------------------
        # Interactions Table
        # ----------------------------------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                interaction_id TEXT,
                timestamp TEXT NOT NULL,
                version_id TEXT,
                original_query TEXT NOT NULL,
                rephrased_query TEXT,
                answer_text TEXT,
                top_k INTEGER NOT NULL,
                top_score REAL,
                success_flag INTEGER NOT NULL,
                error_message TEXT,
                generated_answer INTEGER,
                generation_latency_ms REAL,
                generation_used_context_count INTEGER
            )
        """)

        # Safe migration (if DB already exists)
        cursor.execute("PRAGMA table_info(interactions)")
        columns = [row[1] for row in cursor.fetchall()]

        def add_column_if_missing(column_name: str, column_def: str):
            if column_name not in columns:
                cursor.execute(
                    f"ALTER TABLE interactions ADD COLUMN {column_name} {column_def}"
                )

        add_column_if_missing("generated_answer", "INTEGER")
        add_column_if_missing("generation_latency_ms", "REAL")
        add_column_if_missing("generation_used_context_count", "INTEGER")

        # ----------------------------------------------------
        # Version Registry
        # ----------------------------------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS version_registry (
                version_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                description TEXT,
                vector_store_path TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)
        # ----------------------------------------------------
        # Mutation Log Table
        # ----------------------------------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mutation_log (
                mutation_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                base_version_id TEXT,
                mutation_type TEXT NOT NULL,
                affected_chunk_id TEXT,
                new_version_id TEXT,
                description TEXT,
                executed_by TEXT,
                mutation_status TEXT
            )
        """)

        conn.commit()


# ============================================================
# Version Management
# ============================================================

def generate_version_id() -> str:
    _initialize_db()

    today_str = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"{today_str}_B"

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT version_id
            FROM version_registry
            WHERE version_id LIKE ?
        """, (f"{prefix}%",))
        rows = cursor.fetchall()

    builds = []
    for (vid,) in rows:
        try:
            builds.append(int(vid.split("_B")[1]))
        except Exception:
            continue

    next_build = max(builds) + 1 if builds else 1
    return f"{today_str}_B{str(next_build).zfill(2)}"


def register_version(
    version_id: str,
    description: Optional[str] = None,
    status: str = "STAGING"
) -> None:

    _initialize_db()
    relative_path = f"data/vector_store/{version_id}"

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO version_registry (
                version_id,
                created_at,
                description,
                vector_store_path,
                status
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            version_id,
            datetime.utcnow().isoformat(),
            description,
            relative_path,
            status
        ))
        conn.commit()


def promote_version(version_id: str) -> None:
    _initialize_db()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT status FROM version_registry
            WHERE version_id = ?
        """, (version_id,))
        row = cursor.fetchone()

        if row is None:
            raise ValueError(f"Version '{version_id}' not found.")

        if row[0] != "STAGING":
            raise ValueError("Only STAGING versions can be promoted.")

        cursor.execute("BEGIN")

        cursor.execute("""
            UPDATE version_registry
            SET status = 'STAGING'
            WHERE status = 'ACTIVE'
        """)

        cursor.execute("""
            UPDATE version_registry
            SET status = 'ACTIVE'
            WHERE version_id = ?
        """, (version_id,))

        conn.commit()


def force_activate(version_id: str) -> None:
    _initialize_db()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM version_registry
            WHERE version_id = ?
        """, (version_id,))
        exists = cursor.fetchone()[0]

        if exists == 0:
            raise ValueError(f"Version '{version_id}' not found.")

        cursor.execute("BEGIN")

        cursor.execute("""
            UPDATE version_registry
            SET status = 'STAGING'
            WHERE status = 'ACTIVE'
        """)

        cursor.execute("""
            UPDATE version_registry
            SET status = 'ACTIVE'
            WHERE version_id = ?
        """, (version_id,))

        conn.commit()


def get_active_version() -> Tuple[str, str]:
    _initialize_db()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT version_id, vector_store_path
            FROM version_registry
            WHERE status = 'ACTIVE'
        """)

        rows = cursor.fetchall()

    if len(rows) == 0:
        raise RuntimeError("No ACTIVE version set.")

    if len(rows) > 1:
        raise RuntimeError("Multiple ACTIVE versions detected.")

    return rows[0]


# ============================================================
# Interaction Logging (9.5D Extended)
# ============================================================

def log_interaction(
    session_id: str,
    retriever,
    original_query: str,
    rephrased_query: Optional[str],
    answer_text: Optional[str],
    top_k: int,
    top_score: Optional[float],
    success_flag: bool,
    error_message: Optional[str] = None,
    generated_answer: Optional[bool] = None,
    generation_latency_ms: Optional[float] = None,
    generation_used_context_count: Optional[int] = None
) -> None:

    """
    Phase I Logging Contract:

    success_flag reflects retrieval-level success only.
    It indicates whether a valid retrieval result was returned.

    It does NOT represent:
        - Semantic correctness of answer
        - LLM factual grounding
        - Human validation outcome

    Generation-grounded or semantic evaluation is explicitly
    deferred to Phase II.
    """

    _initialize_db()

    interaction_id = str(uuid.uuid4())

    version_id = None
    if retriever is not None:
        version_id = getattr(retriever, "version_id", None)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO interactions (
                session_id,
                interaction_id,
                timestamp,
                version_id,
                original_query,
                rephrased_query,
                answer_text,
                top_k,
                top_score,
                success_flag,
                error_message,
                generated_answer,
                generation_latency_ms,
                generation_used_context_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            interaction_id,
            datetime.utcnow().isoformat(),
            version_id,
            original_query,
            rephrased_query,
            answer_text,
            top_k,
            top_score,
            int(success_flag),
            error_message,
            int(generated_answer) if generated_answer is not None else None,
            generation_latency_ms,
            generation_used_context_count
        ))
        conn.commit()

# ============================================================
# Session Reconstruction
# ============================================================

def get_last_n_interactions(session_id: str, n: int = 3):

    _initialize_db()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
           SELECT original_query, rephrased_query, answer_text
           FROM interactions
           WHERE session_id = ?
           ORDER BY id DESC
           LIMIT ?
        """, (session_id, n))

        rows = cursor.fetchall()

    rows.reverse()
    return rows