# ============================================
# Milestone 9.5 – Controlled Generation Layer
# generator.py
# ============================================

import requests
import time
from typing import List, Dict


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"

TEMPERATURE = 0
TOP_P = 1
MAX_TOKENS = 300


def _build_prompt(query: str, retrieved_chunks: List[str]) -> str:
    """
    Build deterministic, governed prompt.
    """

    instruction_block = (
    "Answer the question using only the information provided in the context below.\n"
    "Do not mention the word 'context', do not refer to source sections, and do not explain your reasoning.\n"
    "If the answer is not found in the context, reply exactly: not available.\n\n"
    )

    context_block = ""
    for idx, chunk in enumerate(retrieved_chunks, start=1):
        context_block += (
            f"--- Context {idx} ---\n"
            f"{chunk.strip()}\n\n"
        )

    question_block = f"Question:\n{query.strip()}"

    return instruction_block + context_block + question_block


def generate_answer(query: str, retrieved_chunks: List[str]) -> Dict:
    """
    Pure generation layer.
    No routing logic.
    No DB logic.
    No threshold logic.
    """

    # ----------------------------
    # Input Validation
    # ----------------------------
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be a non-empty string.")

    if not isinstance(retrieved_chunks, list):
        raise ValueError("retrieved_chunks must be a list of strings.")

    cleaned_chunks = [
        chunk.strip()
        for chunk in retrieved_chunks
        if isinstance(chunk, str) and chunk.strip()
    ]

    if len(cleaned_chunks) == 0:
        return {
            "answer": "not available",
            "used_context_count": 0,
            "latency_ms": 0.0
        }

    prompt = _build_prompt(query, cleaned_chunks)

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "num_predict": MAX_TOKENS
        }
    }

    # ----------------------------
    # Model Invocation
    # ----------------------------
    try:
        start_time = time.time()

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120
        )

        response.raise_for_status()
        result = response.json()
        latency_ms = (time.time() - start_time) * 1000

        if not isinstance(result, dict):
            raise ValueError("Malformed generation response.")
        
        raw_answer = result.get("response", "")
        if not isinstance(raw_answer, str):
            raw_answer = ""

        raw_answer = raw_answer.strip()      

        
        if not raw_answer:
            final_answer = "not available"
        else:
            normalized = raw_answer.strip().lower().rstrip(".").strip()

            if normalized == "not available":
                final_answer = "not available"
            else:
                final_answer = raw_answer.strip()

        return {
            "answer": final_answer,
            "used_context_count": len(cleaned_chunks),
            "latency_ms": round(latency_ms, 2)
        }

    except Exception:
        return {
            "answer": "generation_error",
            "used_context_count": len(cleaned_chunks),
            "latency_ms": 0.0
        }