from pathlib import Path
from datetime import datetime
import shutil
import sqlite3
import uuid


MASTER_PATH = Path("data/master_corpus.txt")
BACKUP_DIR = Path("data/backups")
DB_PATH = Path("logs/rag_logs.db")


# ============================================================
# DELETE
# ============================================================

def delete_block_by_exact_text(old_block_text: str,
                               base_version_id: str,
                               description: str = None) -> str:

    if not MASTER_PATH.exists():
        raise FileNotFoundError("master_corpus.txt not found.")

    full_content = MASTER_PATH.read_text(encoding="utf-8")
    target_block = old_block_text.strip()

    if target_block not in full_content:
        raise ValueError("Exact block not found in master corpus.")

    # Backup
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"master_{timestamp}.txt"
    shutil.copy2(MASTER_PATH, backup_path)

    backup_files = sorted(
        BACKUP_DIR.glob("master_*.txt"),
        key=lambda p: p.stat().st_mtime
    )

    while len(backup_files) > 20:
        oldest = backup_files.pop(0)
        oldest.unlink()

    updated_content = full_content.replace(target_block, "").strip() + "\n"
    MASTER_PATH.write_text(updated_content, encoding="utf-8")

    mutation_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO mutation_log (
                mutation_id,
                timestamp,
                base_version_id,
                mutation_type,
                affected_chunk_id,
                new_version_id,
                description,
                executed_by,
                mutation_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mutation_id,
                now,
                base_version_id,
                "DELETE",
                None,
                "PENDING",
                description,
                "Maker",
                "PENDING"
            )
        )
        conn.commit()

    return mutation_id


def finalize_delete_mutation(base_version_id: str, new_version_id: str):

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE mutation_log
            SET new_version_id = ?
            WHERE mutation_id = (
                SELECT mutation_id
                FROM mutation_log
                WHERE base_version_id = ?
                  AND mutation_type = 'DELETE'
                  AND new_version_id = 'PENDING'
                ORDER BY timestamp DESC
                LIMIT 1
            )
            """,
            (new_version_id, base_version_id)
        )
        conn.commit()


# ============================================================
# ADD
# ============================================================

def append_block(new_text: str,
                 base_version_id: str,
                 description: str = None) -> str:

    if not new_text.strip():
        raise ValueError("Cannot append empty block.")

    if not MASTER_PATH.exists():
        raise FileNotFoundError("master_corpus.txt not found.")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"master_{timestamp}.txt"
    shutil.copy2(MASTER_PATH, backup_path)

    backup_files = sorted(
        BACKUP_DIR.glob("master_*.txt"),
        key=lambda p: p.stat().st_mtime
    )

    while len(backup_files) > 20:
        oldest = backup_files.pop(0)
        oldest.unlink()

    full_content = MASTER_PATH.read_text(encoding="utf-8")

    candidate_block = f"\n--- BLOCK START ---\n{new_text.strip()}\n--- BLOCK END ---\n"

    if candidate_block in full_content:
        raise ValueError("Duplicate block detected. ADD aborted.")

    with MASTER_PATH.open("a", encoding="utf-8") as f:
        f.write(candidate_block)

    mutation_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO mutation_log (
                mutation_id,
                timestamp,
                base_version_id,
                mutation_type,
                affected_chunk_id,
                new_version_id,
                description,
                executed_by,
                mutation_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mutation_id,
                now,
                base_version_id,
                "ADD",
                None,
                "PENDING",
                description,
                "Maker",
                "PENDING"
            )
        )
        conn.commit()

    return mutation_id


def finalize_add_mutation(base_version_id: str, new_version_id: str):

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE mutation_log
            SET new_version_id = ?
            WHERE mutation_id = (
                SELECT mutation_id
                FROM mutation_log
                WHERE mutation_type = 'ADD'
                  AND new_version_id = 'PENDING'
                ORDER BY timestamp DESC
                LIMIT 1
            )
            """,
            (new_version_id,)
        )
        conn.commit()


# ============================================================
# MODIFY
# ============================================================

def replace_block_by_exact_text(old_block_text: str,
                                new_block_text: str,
                                base_version_id: str,
                                description: str = None) -> str:

    if not old_block_text.strip():
        raise ValueError("Old block text cannot be empty.")

    if not new_block_text.strip():
        raise ValueError("New block text cannot be empty.")

    if not MASTER_PATH.exists():
        raise FileNotFoundError("master_corpus.txt not found.")

    full_content = MASTER_PATH.read_text(encoding="utf-8")

    old_block = old_block_text.strip()
    new_block = new_block_text.strip()

    if old_block == new_block:
        raise ValueError("No changes detected. MODIFY aborted.")

    if old_block not in full_content:
        raise RuntimeError("Exact block match not found. Mutation aborted.")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"master_{timestamp}.txt"
    shutil.copy2(MASTER_PATH, backup_path)

    backup_files = sorted(
        BACKUP_DIR.glob("master_*.txt"),
        key=lambda p: p.stat().st_mtime
    )

    while len(backup_files) > 20:
        oldest = backup_files.pop(0)
        oldest.unlink()

    updated_content = full_content.replace(old_block, new_block, 1)
    MASTER_PATH.write_text(updated_content, encoding="utf-8")

    mutation_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO mutation_log (
                mutation_id,
                timestamp,
                base_version_id,
                mutation_type,
                affected_chunk_id,
                new_version_id,
                description,
                executed_by,
                mutation_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mutation_id,
                now,
                base_version_id,
                "MODIFY",
                None,
                "PENDING",
                description,
                "Maker",
                "PENDING"
            )
        )
        conn.commit()

    return mutation_id


def finalize_modify_mutation(base_version_id: str, new_version_id: str):

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE mutation_log
            SET new_version_id = ?
            WHERE mutation_id = (
                SELECT mutation_id
                FROM mutation_log
                WHERE base_version_id = ?
                  AND mutation_type = 'MODIFY'
                  AND new_version_id = 'PENDING'
                ORDER BY timestamp DESC
                LIMIT 1
            )
            """,
            (new_version_id, base_version_id)
        )
        conn.commit()