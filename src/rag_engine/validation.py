import math


# ============================================
# M3.10 + M3.11 – Deterministic Retrieval Check
# ============================================

def validate_deterministic_retrieval(
    retriever,
    query: str,
    top_k: int = 5,
    score_threshold: float = 0.0,
    tolerance: float = 1e-6
):
    """
    Calls retrieve() twice and validates deterministic behavior.
    """

    print("\n--- Deterministic Retrieval Validation ---")

    # First call
    result_1 = retriever.retrieve(
        query,
        top_k=top_k,
        score_threshold=score_threshold
    )

    # Second call
    result_2 = retriever.retrieve(
        query,
        top_k=top_k,
        score_threshold=score_threshold
    )

    r1 = result_1.get("results", [])
    r2 = result_2.get("results", [])

    # ----------------------------------
    # Length check
    # ----------------------------------
    if len(r1) != len(r2):
        print("FAIL: Result length mismatch.")
        return False

    # ----------------------------------
    # Rank / chunk_id / score checks
    # ----------------------------------
    for i in range(len(r1)):

        # Rank ordering
        if r1[i]["rank"] != r2[i]["rank"]:
            print(f"FAIL: Rank mismatch at position {i}.")
            return False

        # Chunk ID sequence
        if r1[i]["chunk_id"] != r2[i]["chunk_id"]:
            print(f"FAIL: chunk_id mismatch at position {i}.")
            return False

        # Score stability
        if not math.isclose(
            r1[i]["score"],
            r2[i]["score"],
            rel_tol=0.0,
            abs_tol=tolerance
        ):
            print(f"FAIL: Score mismatch at position {i}.")
            return False

    print("PASS: Deterministic retrieval confirmed.")
    return True