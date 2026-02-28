# ============================================
# Milestone 4 – Phase A
# Deterministic Query Rephrase Layer
# ============================================

def rephrase_query(query: str) -> str:
    """
    Deterministic normalization rule:
    - Strip leading/trailing whitespace
    - Collapse internal multiple spaces
    - Capitalize first letter
    - Ensure trailing question mark
    """

    if not isinstance(query, str):
        raise ValueError("Query must be a string.")

    # Strip whitespace
    cleaned = query.strip()

    if not cleaned:
        raise ValueError("Query cannot be empty.")

    # Collapse multiple spaces
    cleaned = " ".join(cleaned.split())

    # Capitalize first letter (only first character)
    cleaned = cleaned[0].upper() + cleaned[1:]

    # Ensure trailing question mark
    if not cleaned.endswith("?"):
        cleaned = cleaned + "?"

    return cleaned