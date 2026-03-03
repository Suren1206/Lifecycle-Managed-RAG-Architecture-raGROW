import shutil
import faiss
import json
import numpy as np
import requests

from pathlib import Path
from rag_engine.logger import generate_version_id, register_version
from rag_engine.chunking import _sentence_chunk_text, diagnostic_chunk_report


EMBED_MODEL = "mxbai-embed-large:335m"
OLLAMA_URL = "http://localhost:11434/api/embeddings"
VECTOR_DIMENSION = 1024


# ============================================================
# Embedding
# ============================================================

def _embed_text(text: str) -> np.ndarray:
    response = requests.post(
        OLLAMA_URL,
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=120
    )
    response.raise_for_status()

    vector = np.array(response.json()["embedding"], dtype=np.float32)
    norm = np.linalg.norm(vector)

    if norm == 0:
        raise ValueError("Zero-norm embedding encountered.")

    return vector / norm


# ============================================================
# Header Parser (V2.1)
# ============================================================

def header_parser(text: str):

    lines = text.splitlines()

    structured_blocks = {}
    current_header = None
    collecting_rules = False

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            continue

        if (
            line.isupper()
            and any(c.isalpha() for c in line)
            and line not in {"POLICY STATEMENT", "OPERATIONAL COVERAGE", "RULES"}
        ):
            current_header = line
            structured_blocks[current_header] = []
            collecting_rules = False
            continue

        if line == "Rules":
            collecting_rules = True
            continue

        if collecting_rules and current_header:
            structured_blocks[current_header].append(line)

    return structured_blocks


# ============================================================
# Build Pipeline
# ============================================================

def build_new_version(description: str = None) -> str:

    version_id = generate_version_id()
    staging_dir = Path("data/vector_store") / version_id

    try:
        print("\n--- Starting Batch Build ---")

        staging_dir.mkdir(parents=True, exist_ok=False)

        index_path = staging_dir / f"{version_id}.index"
        index_map_path = staging_dir / "index_to_chunk_id.json"
        meta_map_path = staging_dir / "chunk_id_to_metadata.json"
        embeddings_path = staging_dir / "embeddings.npy"

        corpus_file = Path("data/master_corpus.txt")

        if not corpus_file.exists():
            raise FileNotFoundError("master_corpus.txt not found.")

        full_text = corpus_file.read_text(encoding="utf-8", errors="ignore")

        header_map = header_parser(full_text)

        embeddings = []
        index_to_chunk_id = {}
        chunk_id_to_metadata = {}

        chunk_counter = 0
        all_chunks_for_diagnostics = []

        for header, rule_lines in header_map.items():

            combined_text = " ".join(rule_lines)

            chunks = _sentence_chunk_text(combined_text)

            for chunk in chunks:

                print(f"Embedding chunk {chunk_counter + 1}")

                vec = _embed_text(chunk)
                embeddings.append(vec)

                chunk_id = f"chunk_{chunk_counter}"
                index_to_chunk_id[str(chunk_counter)] = chunk_id

                chunk_id_to_metadata[chunk_id] = {
                    "chunk_index": chunk_counter,
                    "header": header,
                    "text": chunk
                }

                all_chunks_for_diagnostics.append(chunk)
                chunk_counter += 1

        if not embeddings:
            raise RuntimeError("No chunks generated.")

        embeddings_array = np.vstack(embeddings).astype(np.float32)

        index = faiss.IndexFlatIP(VECTOR_DIMENSION)
        index.add(embeddings_array)

        faiss.write_index(index, str(index_path))
        np.save(embeddings_path, embeddings_array)

        index_map_path.write_text(
            json.dumps(index_to_chunk_id, indent=2),
            encoding="utf-8"
        )

        meta_map_path.write_text(
            json.dumps(chunk_id_to_metadata, indent=2),
            encoding="utf-8"
        )

        print("Registering version as STAGING...")

        register_version(
            version_id=version_id,
            description=description,
            status="STAGING"
        )

        diagnostic_chunk_report(all_chunks_for_diagnostics)

        print(f"\n--- Build Complete: {version_id} ---\n")

        return version_id

    except Exception:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        raise


if __name__ == "__main__":
    version_id = build_new_version(description="V2 Header + Sentence Chunking")
    print(f"Version created: {version_id}")
