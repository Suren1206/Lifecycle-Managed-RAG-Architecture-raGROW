import shutil
import faiss
import json
import numpy as np
import requests

from pathlib import Path
from rag_engine.logger import generate_version_id, register_version


EMBED_MODEL = "mxbai-embed-large:335m"
OLLAMA_URL = "http://localhost:11434/api/embeddings"
VECTOR_DIMENSION = 1024
CHUNK_SIZE = 800


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


def _chunk_text(text: str):
    return [
        text[i:i + CHUNK_SIZE]
        for i in range(0, len(text), CHUNK_SIZE)
        if text[i:i + CHUNK_SIZE].strip()
    ]


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

        chunks = _chunk_text(full_text)

        if not chunks:
            raise RuntimeError("No chunks generated from corpus.")

        print(f"Total chunks to embed: {len(chunks)}")

        embeddings = []
        index_to_chunk_id = {}
        chunk_id_to_metadata = {}

        for idx, chunk in enumerate(chunks):

            print(f"Embedding chunk {idx + 1}/{len(chunks)}")

            vec = _embed_text(chunk)
            embeddings.append(vec)

            chunk_id = f"chunk_{idx}"
            index_to_chunk_id[str(idx)] = chunk_id

            chunk_id_to_metadata[chunk_id] = {
                "chunk_index": idx,
                "text": chunk
            }

        embeddings_array = np.vstack(embeddings).astype(np.float32)

        index = faiss.IndexFlatIP(VECTOR_DIMENSION)
        index.add(embeddings_array)

        if index.ntotal == 0:
            raise RuntimeError("FAISS index has zero vectors.")

        print("Writing FAISS index...")
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

        print(f"\n--- Build Complete: {version_id} ---\n")

        return version_id

    except Exception:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        raise