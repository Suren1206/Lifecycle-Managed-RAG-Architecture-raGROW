import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from rag_engine.guardrails import validate_header, validate_proposed_text

DB_PATH = Path("logs/rag_logs.db")


def add_to_queue(
    base_version_id: str,
    mutation_type: str,
    header: str,
    chunk_id: str,
    original_text: str,
    proposed_text: str,
    submitted_by: str
):
    if not base_version_id:
        raise ValueError("base_version_id is required.")

    if mutation_type not in {"ADD", "MODIFY", "DELETE"}:
        raise ValueError("Invalid mutation_type.")

    queue_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO mutation_queue (
                queue_id,
                timestamp,
                base_version_id,
                mutation_type,
                header,
                chunk_id,
                original_text,
                proposed_text,
                submitted_by,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            queue_id,
            timestamp,
            base_version_id,
            mutation_type,
            header,
            chunk_id,
            original_text,
            proposed_text,
            submitted_by,
            "PENDING"
        ))

        conn.commit()

def remove_from_queue(queue_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM mutation_queue
            WHERE queue_id = ?
        """, (queue_id,))
        conn.commit()

    return queue_id


def process_batch():

    import sqlite3
    from pathlib import Path
    from rag_engine.build_pipeline import build_new_version

    # 1. Fetch all pending mutations
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT queue_id, mutation_type, header, chunk_id,
                   original_text, proposed_text
            FROM mutation_queue
            WHERE status = 'PENDING'
            ORDER BY timestamp ASC
        """)
        pending = cursor.fetchall()

        # 2. Read master corpus
    master_path = Path("data/master_corpus.txt")

    if not master_path.exists():
        raise FileNotFoundError("master_corpus.txt not found.")

    full_text = master_path.read_text(encoding="utf-8")

    if not pending:
        raise ValueError("No pending mutations to process.")

    # 2. Apply mutations to master corpus
    # (implementation next step)

    updated_text = full_text

    for row in pending:
        mutation_type = row[1]
        header = row[2]
        validate_header(header)
        proposed_text = row[5]
        if mutation_type in ["ADD", "MODIFY"]:
            validate_proposed_text(proposed_text)

        if mutation_type == "ADD":

            lines = updated_text.splitlines()

            header_index = None
            next_header_index = None

            # Find current header line
            for i, line in enumerate(lines):
                if line.strip() == header.strip():
                    header_index = i
                    break

            if header_index is None:
                raise ValueError(f"Header not found: {header}")

            # Find next ALL-CAPS header after current header
            for j in range(header_index + 1, len(lines)):
                if lines[j].strip().isupper() and lines[j].strip() != "":
                    next_header_index = j
                    break

            if next_header_index is None:
                next_header_index = len(lines)

            insertion_line = next_header_index

            lines.insert(insertion_line, proposed_text.strip())

            updated_text = "\n".join(lines)


        elif mutation_type == "MODIFY":

            lines = updated_text.splitlines()

            header = row[2].strip()
            replacement_body = proposed_text.strip()

            header_index = None
            next_header_index = None

            # 1. Find header line
            for i, line in enumerate(lines):
                if line.strip() == header:
                    header_index = i
                    break

            if header_index is None:
                raise ValueError(f"Header not found for MODIFY: {header}")

            # 2. Find next ALL-CAPS header
            for j in range(header_index + 1, len(lines)):
                stripped = lines[j].strip()
                if stripped.isupper() and stripped != header:
                    next_header_index = j
                    break

            if next_header_index is None:
                next_header_index = len(lines)

            # 3. Replace only content between headers
            new_body_lines = replacement_body.splitlines()

            lines = (
                lines[:header_index + 1] +
                new_body_lines +
                lines[next_header_index:]
            )          
            
            updated_text = "\n".join(lines)
            
        elif mutation_type == "DELETE":            

            lines = updated_text.splitlines()

            header = row[2].strip()

            header_index = None
            next_header_index = None

            for i, line in enumerate(lines):
                if line.strip() == header:
                    header_index = i
                    break

            if header_index is None:
                raise ValueError(f"Header not found for DELETE: {header}")

            for j in range(header_index + 1, len(lines)):
                stripped = lines[j].strip()
                if stripped.isupper() and stripped != header:
                    next_header_index = j
                    break

            if next_header_index is None:
                next_header_index = len(lines)

            lines = lines[:header_index] + lines[next_header_index:]

            updated_text = "\n".join(lines)                              

    master_path.write_text(updated_text, encoding="utf-8")

    # 3. Trigger single rebuild
    new_version_id = build_new_version(description="Batch Mutation Build")

    # 4. Clear mutation queue
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM mutation_queue")
        conn.commit()

    return new_version_id
