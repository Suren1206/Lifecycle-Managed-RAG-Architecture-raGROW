from typing import List


MIN_CHUNK_SIZE = 300


def _sentence_chunk_text(text: str) -> List[str]:
    """
    Sentence-based chunking.

    Rules:
    - Sentence boundary = "."
    - Minimum chunk size = 300 characters
    - Chunk ends at first "." after >= 300 chars
    - No overlap
    """

    chunks = []
    start = 0
    length = len(text)

    while start < length:

        if length - start <= MIN_CHUNK_SIZE:
            chunk = text[start:].strip()
            if chunk:
                chunks.append(chunk)
            break

        candidate_end = start + MIN_CHUNK_SIZE

        # Find first full stop after minimum size
        period_index = text.find(".", candidate_end)

        if period_index == -1:
            chunk = text[start:].strip()
            if chunk:
                chunks.append(chunk)
            break

        end = period_index + 1
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start = end

    return chunks


def diagnostic_chunk_report(chunks: List[str]) -> None:
    sizes = sorted([len(c) for c in chunks], reverse=True)

    print("\n--- Chunk Size Report (Descending) ---")
    for size in sizes:
        print(size)
