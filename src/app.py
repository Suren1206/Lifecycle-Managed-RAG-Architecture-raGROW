from rag_engine.employee_state import employee_transition
import streamlit as st
import uuid
from pathlib import Path
import sqlite3

from rag_engine.retriever import Retriever
from rag_engine.rephrase import rephrase_query
from rag_engine.logger import (
    log_interaction,
    get_last_n_interactions,
    promote_version,
    force_activate
)
from rag_engine.build_pipeline import build_new_version
from rag_engine.generator import generate_answer   # ✅ Added


# ---------------------------------
# Threshold Configuration
# ---------------------------------
HIGH_THRESHOLD = 0.75
MID_THRESHOLD = 0.60


def get_governance_report():
    import sqlite3
    from pathlib import Path

    db_path = Path("logs/rag_logs.db")

    if not db_path.exists():
        return None

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM interactions")
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT 
                SUM(CASE WHEN success_flag = 1 THEN 1 ELSE 0 END),
                SUM(CASE WHEN success_flag = 0 THEN 1 ELSE 0 END)
            FROM interactions
        """)
        success, failure = cursor.fetchone()
        success = success or 0
        failure = failure or 0

        success_ratio = "0.00%"
        if total > 0:
            success_ratio = f"{(success/total)*100:.2f}%"

        cursor.execute("""
            SELECT AVG(top_score)
            FROM interactions
            WHERE top_score IS NOT NULL
        """)
        avg_score = cursor.fetchone()[0]
        avg_score = round(avg_score, 4) if avg_score else 0.0

        cursor.execute("""
            SELECT version_id, COUNT(*)
            FROM interactions
            GROUP BY version_id
            ORDER BY COUNT(*) DESC
        """)
        version_distribution = cursor.fetchall()

    return {
        "total": total,
        "success": success,
        "failure": failure,
        "ratio": success_ratio,
        "avg_score": avg_score,
        "versions": version_distribution
    }


st.set_page_config(
    page_title="raGROW – Interface",
    layout="wide"
)

st.title("raGROW")
st.divider()

role = st.sidebar.selectbox(
    "Select Role",
    ["Employee", "Maker", "Checker", "Admin"]
)

st.sidebar.divider()


# ============================================================
# ROLE ROUTING
# ============================================================

if role == "Employee":

    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    if "turn_counter" not in st.session_state:
        st.session_state.turn_counter = 0

    if "awaiting_rephrase" not in st.session_state:
        st.session_state.awaiting_rephrase = False

    session_id = st.session_state.session_id
    retriever = Retriever()

    if st.session_state.turn_counter >= 3:
        lock = True
    else:
        lock = False

    query = st.text_input("Ask your question", disabled=lock)
    submit = st.button("Submit", disabled=lock)

    if lock:
        st.info("Maximum 3 turns reached. Please refresh to start a new session.")

    if submit:

        if not query.strip():
            st.warning("Please enter a valid query.")
            st.stop()

        original_query = query
        rephrased_query = rephrase_query(original_query)

        result = retriever.retrieve(query=rephrased_query, top_k=5)
        results = result.get("results", [])

        failure_msg = "This information is not available in the current policy corpus."

        if not results:
            similarity = "LOW"
            top_score = None
        else:

            top = results[0]
            score_value = top.get("score")

            if isinstance(score_value, (int, float)):
                top_score = float(score_value)
            else:
                top_score = None
            if top_score is None:
                similarity = "LOW"
            elif top_score >= HIGH_THRESHOLD:
                similarity = "HIGH"
            elif MID_THRESHOLD <= top_score < HIGH_THRESHOLD:
                similarity = "MID"
            else:
                similarity = "LOW"            

        # =========================
        # HIGH BAND (GENERATION)
        # =========================
        if similarity == "HIGH":

            top_chunk = results[0]["text"]

            generation_result = generate_answer(rephrased_query, [top_chunk])

            generated_answer_text = generation_result["answer"]
            generation_latency = generation_result["latency_ms"]
            generation_context_count = generation_result["used_context_count"]

            log_interaction(
                session_id=session_id,
                retriever=retriever,
                original_query=original_query,
                rephrased_query=rephrased_query,
                answer_text=generated_answer_text,
                top_k=1,
                top_score=top_score,
                success_flag=True,  # similarity-based
                error_message=None,
                generated_answer=True,
                generation_latency_ms=generation_latency,
                generation_used_context_count=generation_context_count
            )

            st.session_state.turn_counter += 1
            st.session_state.awaiting_rephrase = False
            st.rerun()

        # =========================
        # MID BAND
        # =========================
        elif similarity == "MID":

            if not st.session_state.awaiting_rephrase:
                st.session_state.awaiting_rephrase = True
                st.info("Please rephrase your question for better clarity.")
                st.stop()
            else:
                log_interaction(
                    session_id=session_id,
                    retriever=retriever,
                    original_query=original_query,
                    rephrased_query=rephrased_query,
                    answer_text=failure_msg,
                    top_k=5,
                    top_score=top_score,
                    success_flag=False,
                    error_message=None,
                    generated_answer=False,
                    generation_latency_ms=None,
                    generation_used_context_count=0
                )

                st.session_state.turn_counter += 1
                st.session_state.awaiting_rephrase = False
                st.rerun()

        # =========================
        # LOW BAND
        # =========================
        else:

            log_interaction(
                session_id=session_id,
                retriever=retriever,
                original_query=original_query,
                rephrased_query=rephrased_query,
                answer_text=failure_msg,
                top_k=5,
                top_score=top_score,
                success_flag=False,
                error_message=None,
                generated_answer=False,
                generation_latency_ms=None,
                generation_used_context_count=0
            )

            st.session_state.turn_counter += 1
            st.session_state.awaiting_rephrase = False
            st.rerun()

    # -------------------------
    # HISTORY AT BOTTOM
    # -------------------------
    history = get_last_n_interactions(session_id, n=100)

    if history:
        st.divider()
        st.subheader("Conversation")
        for row in history[-3:]:
            st.markdown(f"**You:** {row[0]}")
            st.markdown(f"**System:** {row[2] or 'No response recorded.'}")

# ============================================================
# MAKER INTERFACE
# ============================================================

elif role == "Maker":

    st.subheader("Maker Interface")
    st.divider()

    conn = sqlite3.connect("logs/rag_logs.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT version_id
        FROM version_registry
        WHERE status = 'ACTIVE'
        LIMIT 1
    """)
    active = cursor.fetchone()
    conn.close()

    active_version = active[0] if active else None

    # ============================================================
    # REQUIRE ACTIVE VERSION
    # ============================================================
    if not active_version:
        st.warning("No ACTIVE version found.")
        st.stop()

    # ============================================================
    # ADD SECTION
    # ============================================================
    st.markdown("### Add New Policy Block")

    from rag_engine.mutation_engine import append_block, finalize_add_mutation

    new_block_text = st.text_area("Enter full new policy block")

    if st.button("Append Block & Rebuild"):
        if not new_block_text.strip():
            st.warning("Block text cannot be empty.")
        else:
            try:
                append_block(
                    new_text=new_block_text,
                    base_version_id=active_version,
                    description="ADD via Maker UI"
                )

                new_version = build_new_version()

                finalize_add_mutation(
                    base_version_id=active_version,
                    new_version_id=new_version
                )

                st.success(f"New STAGING version created: {new_version}")

            except Exception as e:
                st.error(str(e))

    # ============================================================
    # MODIFY SECTION
    # ============================================================
    st.divider()
    st.markdown("### Modify Existing Policy Block")

    MASTER_FILE_PATH = "data/master_corpus.txt"

    def load_blocks():
        import os

        if not os.path.exists(MASTER_FILE_PATH):
            return []

        with open(MASTER_FILE_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        blocks = []
        current_block = []
        inside_block = False

        for line in content.splitlines():
            if line.strip() == "--- BLOCK START ---":
                inside_block = True
                current_block = [line]
            elif line.strip() == "--- BLOCK END ---":
                current_block.append(line)
                blocks.append("\n".join(current_block))
                inside_block = False
            elif inside_block:
                current_block.append(line)

        return blocks

    blocks = load_blocks()

    if blocks:
        selected_block = st.selectbox("Select Block to Modify", blocks)

        if selected_block:
            st.text_area(
                "Current Block Content",
                value=selected_block,
                height=300,
                disabled=True
            )

            modified_block = st.text_area(
                "Edit Block Content",
                value=selected_block,
                height=300
            )

            from rag_engine.mutation_engine import replace_block_by_exact_text, finalize_modify_mutation

            if st.button("Submit Modification"):
                try:
                    replace_block_by_exact_text(
                        old_block_text=selected_block,
                        new_block_text=modified_block,
                        base_version_id=active_version
                    )

                    new_version = build_new_version()

                    finalize_modify_mutation(
                        base_version_id=active_version,
                        new_version_id=new_version
                    )

                    st.success(f"New STAGING version created: {new_version}")

                except Exception as e:
                    st.error(str(e))
    else:
        st.info("No blocks found in master corpus.")

    # ============================================================
    # DELETE SECTION
    # ============================================================
    st.divider()
    st.markdown("### Delete Policy Block")

    from rag_engine.mutation_engine import delete_block_by_exact_text, finalize_delete_mutation

    blocks_for_delete = load_blocks()

    if blocks_for_delete:
        block_to_delete = st.selectbox(
            "Select Block to Delete",
            blocks_for_delete,
            key="delete_select"
        )

        if st.button("Confirm Delete & Rebuild"):
            try:
                delete_block_by_exact_text(
                    old_block_text=block_to_delete,
                    base_version_id=active_version
                )

                new_version = build_new_version()

                finalize_delete_mutation(
                    base_version_id=active_version,
                    new_version_id=new_version
                )

                st.success(f"New STAGING version created: {new_version}")

            except Exception as e:
                st.error(str(e))
    else:
        st.info("No blocks available for deletion.")

    # ============================================================
    # MANUAL BUILD
    # ============================================================
    st.divider()

    if st.button("Build New Version"):
        try:
            new_version = build_new_version()
            st.success(f"New STAGING version created: {new_version}")
        except Exception as e:
            st.error(str(e))

    # ============================================================
    # VERSION REGISTRY
    # ============================================================
    st.divider()
    st.subheader("Version Registry")

    conn = sqlite3.connect("logs/rag_logs.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT version_id, status, created_at
        FROM version_registry
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    if rows:
        for r in rows:
            version_id, status, created_at = r

            if status == "ACTIVE":
                st.success(f"{version_id} | {created_at} | CURRENT")
            elif status == "STAGING":
                st.info(f"{version_id} | {created_at} | STAGING")
            else:
                st.write(f"{version_id} | {created_at} | {status}")
    else:
        st.info("No versions found.")

# ============================================================
# CHECKER INTERFACE
# ============================================================

elif role == "Checker":

    st.subheader("Checker Interface")

    conn = sqlite3.connect("logs/rag_logs.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT version_id FROM version_registry WHERE status='STAGING'"
    )
    staging_versions = cursor.fetchall()

    if staging_versions:
        version_ids = [v[0] for v in staging_versions]

        selected_version = st.selectbox(
            "Select STAGING version to promote",
            version_ids
        )

        if st.button("Promote Version"):
            try:
                promote_version(selected_version)
                st.success(f"{selected_version} promoted to ACTIVE.")
            except Exception as e:
                st.error(str(e))
    else:
        st.info("No staging versions available for promotion.")

    st.divider()

    st.subheader("Interaction Logs")

    cursor.execute(
        "SELECT timestamp, original_query, answer_text, success_flag "
        "FROM interactions ORDER BY id DESC LIMIT 50"
    )

    logs = cursor.fetchall()
    conn.close()

    if logs:
        for log in logs:
            status = "Success" if log[3] else "Failure"
            st.write(f"{log[0]} | {status}")
            st.write(f"Q: {log[1]}")
            st.write(f"A: {log[2]}")
            st.divider()
    else:
        st.info("No interaction logs available.")


# ============================================================
# ADMIN INTERFACE
# ============================================================

elif role == "Admin":

    st.subheader("Admin Dashboard")

    conn = sqlite3.connect("logs/rag_logs.db")
    cursor = conn.cursor()

    # =========================
    # CURRENT ACTIVE VERSION
    # =========================
    cursor.execute("""
        SELECT version_id
        FROM version_registry
        WHERE status = 'ACTIVE'
        LIMIT 1
    """)
    active = cursor.fetchone()
    active_version = active[0] if active else "None"
    st.success(f"Current ACTIVE version: {active_version}")

    st.divider()

    # =========================
    # VERSION REGISTRY
    # =========================
    st.markdown("### Version Registry")

    cursor.execute("""
        SELECT version_id, status, created_at
        FROM version_registry
        ORDER BY created_at DESC
    """)
    registry = cursor.fetchall()

    for r in registry:
        st.write(f"{r[0]} | {r[1]} | {r[2]}")

    st.divider()

    # =========================
    # GOVERNANCE ANALYTICS
    # =========================
    st.markdown("## Governance Analytics")

    num_batches = st.number_input(
        "Number of latest batches to analyze",
        min_value=1,
        value=3,
        step=1
    )

    # =========================
    # AGGREGATED FAILURE SUMMARY (PER VERSION)
    # =========================
    with st.expander("📌 Aggregated Failure Summary (Per Version)", expanded=False):

        cursor.execute(f"""
            SELECT
                v.version_id,
                COUNT(i.id) AS total_interactions,
                COALESCE(SUM(CASE WHEN i.success_flag = 0 THEN 1 ELSE 0 END), 0) AS failure_count,
                ROUND(
                    CASE 
                        WHEN COUNT(i.id) = 0 THEN 0
                        ELSE (SUM(CASE WHEN i.success_flag = 0 THEN 1 ELSE 0 END) * 100.0) / COUNT(i.id)
                    END,
                    2
                ) AS failure_ratio
            FROM (
                SELECT version_id
                FROM version_registry
                ORDER BY created_at DESC
                LIMIT {num_batches}
            ) v
            LEFT JOIN interactions i
                ON v.version_id = i.version_id
            GROUP BY v.version_id
            ORDER BY v.version_id;
        """)

        rows = cursor.fetchall()

        for row in rows:
            st.markdown(f"**{row[0]}**")
            st.write(f"Total Interactions : {row[1] or 0}")
            st.write(f"Failure Count      : {row[2] or 0}")
            st.write(f"Failure Ratio      : {row[3] or 0.0}%")
            st.divider()

    # =========================
    # OVERALL SUCCESS / FAILURE SUMMARY
    # =========================
    with st.expander("📈 Overall Success / Failure Summary", expanded=False):

        cursor.execute(f"""
            SELECT
                COUNT(*) AS total_interactions,
                SUM(CASE WHEN success_flag = 0 THEN 1 ELSE 0 END) AS total_failures
            FROM interactions
            WHERE version_id IN (
                SELECT version_id
                FROM version_registry
                ORDER BY created_at DESC
                LIMIT {num_batches}
            );
        """)

        result = cursor.fetchone()

        total = result[0] or 0
        failures = result[1] or 0
        successes = total - failures

        success_percent = round((successes / total) * 100, 2) if total > 0 else 0.0
        failure_percent = round((failures / total) * 100, 2) if total > 0 else 0.0

        st.write(f"Total Interactions : {total}")
        st.write(f"Successful         : {successes} ({success_percent}%)")
        st.write(f"Failed             : {failures} ({failure_percent}%)")

    # =========================
    # DETAILED FAILURES
    # =========================
    with st.expander("❌ Detailed Failures", expanded=False):

        cursor.execute(f"""
            SELECT
                timestamp,
                version_id,
                original_query,
                top_score
            FROM interactions
            WHERE success_flag = 0
            AND version_id IN (
                SELECT version_id
                FROM version_registry
                ORDER BY created_at DESC
                LIMIT {num_batches}
            )
            ORDER BY timestamp DESC
        """)

        failures = cursor.fetchall()

        if failures:
            for idx, row in enumerate(failures, start=1):

                score_display = round(row[3], 4) if row[3] is not None else "N/A"

                score_display = round(row[3], 4) if row[3] is not None else "N/A"

                st.write(
                    f"{idx}. {row[0]} | {row[1]} | Score: {round(row[3],4)}"
                )
                st.write(f"Query: {row[2]}")
                st.divider()
        else:
            st.info("No failures found.")

    # =========================
    # REPEATED FAILED QUERIES
    # =========================
    with st.expander("🔁 Repeated Failed Queries", expanded=False):

        top_k = st.radio(
            "Show Top Repeated Failures",
            options=[10, 20],
            horizontal=True
        )

        cursor.execute(f"""
            SELECT
                original_query,
                COUNT(*) AS failure_count
            FROM interactions
            WHERE success_flag = 0
            AND version_id IN (
                SELECT version_id
                FROM version_registry
                ORDER BY created_at DESC
                LIMIT {num_batches}
            )
            GROUP BY original_query
            ORDER BY failure_count DESC
            LIMIT {top_k}
        """)

        repeated = cursor.fetchall()

        if repeated:
            for idx, row in enumerate(repeated, start=1):
                st.write(f"{idx}. {row[0]}")
                st.write(f"Failures: {row[1]}")
                st.divider()
        else:
            st.info("No repeated failures found.")

    conn.close()