"""
Employee State Machine – Phase I Implementation

This module contains the controlled routing logic for the Employee role.
Retained intentionally to isolate state transition logic from UI layer.

Refactor candidate for Milestone 9 if architectural consolidation is required.
"""


# ============================================================
# EMPLOYEE STATE MACHINE (PURE LOGIC – NO STREAMLIT)
# ============================================================

def employee_transition(state, retry_count, similarity, decision=None):
    """
    state: "IDLE" | "CONFIRM"
    retry_count: 0 or 1
    similarity: "HIGH" | "MID" | "LOW"
    decision: None | "YES" | "NO"

    Returns:
        new_state,
        new_retry_count,
        action

    action:
        "LOG_SUCCESS"
        "LOG_FAILURE"
        "ASK_CONFIRM"
        "ALLOW_RETRY"
        "SHOW_FAILURE"
    """

    # HIGH similarity → immediate success
    if similarity == "HIGH":
        return "IDLE", 0, "LOG_SUCCESS"

    # LOW similarity → immediate failure
    if similarity == "LOW":
        return "IDLE", 0, "LOG_FAILURE"

    # MID similarity
    if similarity == "MID":

        # If coming from CONFIRM state
        if state == "CONFIRM":

            if decision == "YES":
                return "IDLE", 0, "LOG_SUCCESS"

            if decision == "NO":
                return "IDLE", 1, "ALLOW_RETRY"

        # If retry already used → failure
        if retry_count == 1:
            return "IDLE", 0, "LOG_FAILURE"

        # First MID encounter
        return "CONFIRM", 0, "ASK_CONFIRM"

    # Default safe fallback
    return "IDLE", 0, "SHOW_FAILURE"