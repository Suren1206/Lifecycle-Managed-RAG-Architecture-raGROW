import json
import requests
import numpy as np
import faiss
from pathlib import Path

from rag_engine.logger import get_active_version


class Retriever:

    def __init__(self, version_id: str = None):

        base_dir = Path(__file__).resolve().parent.parent

        if version_id is None:
            version_id, relative_path = get_active_version()
        else:
            relative_path = f"data/vector_store/{version_id}"

        self.vector_store_dir = base_dir / relative_path
        self.index_path = self.vector_store_dir / f"{version_id}.index"
        self.index_map_path = self.vector_store_dir / "index_to_chunk_id.json"
        self.meta_map_path = self.vector_store_dir / "chunk_id_to_metadata.json"

        self.embed_model = "mxbai-embed-large:335m"
        self.ollama_url = "http://localhost:11434/api/embeddings"

        self._load_artifacts()

    # -----------------------------------
    # Load Artifacts
    # -----------------------------------
    def _load_artifacts(self):

        if not self.index_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found at {self.index_path}"
            )

        self.index = faiss.read_index(str(self.index_path))

        self.index_to_chunk_id = json.loads(
            self.index_map_path.read_text(encoding="utf-8")
        )

        self.chunk_id_to_metadata = json.loads(
            self.meta_map_path.read_text(encoding="utf-8")
        )

        self.version_id = self.index_path.stem

    # -----------------------------------
    # Embed Query
    # -----------------------------------
    def embed_query(self, query: str):

        response = requests.post(
            self.ollama_url,
            json={"model": self.embed_model, "prompt": query},
            timeout=60
        )

        response.raise_for_status()
        vector = response.json()["embedding"]

        vector = np.array(vector, dtype=np.float32)
        norm = np.linalg.norm(vector)

        # -------------------------------
        # MS10A.1 Zero-Norm Guard
        # -------------------------------
        if norm == 0:
            # Return None to signal retrieval degradation
            return None

        normalized_vector = vector / norm
        return normalized_vector.reshape(1, -1)

    # -----------------------------------
    # Retrieve
    # -----------------------------------
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.0,
        return_metadata: bool = True,
        debug: bool = False
    ):

        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query must be a non-empty string.")

        if not isinstance(top_k, int) or top_k <= 0:
            raise ValueError("top_k must be a positive integer.")

        if self.index.ntotal == 0:
            return {
                "query": query,
                "results": [],
                "message": "Vector store is empty."
            }

        top_k = min(top_k, self.index.ntotal)

        query_vec = self.embed_query(query)

        # ---------------------------------
        # Handle Zero-Norm Embedding Case
        # ---------------------------------
        if query_vec is None:
            return {
                "query": query,
                "results": [],
                "message": "Embedding failure (zero-norm). Treated as LOW retrieval."
            }

        D, I = self.index.search(query_vec, top_k)

        results = []

        for rank, (score, idx) in enumerate(zip(D[0], I[0])):

            if idx == -1:
                continue

            if score < score_threshold:
                continue

            chunk_id = self.index_to_chunk_id.get(str(int(idx)))
            metadata = self.chunk_id_to_metadata.get(chunk_id)

            if not metadata:
                continue

            raw_text = metadata.get("text", "")
            cleaned_text = " ".join(raw_text.split())

            result = {
                "rank": rank + 1,
                "score": float(score),
                "chunk_id": chunk_id,
                "chunk_index": metadata.get("chunk_index"),
                "text": cleaned_text
            }

            if return_metadata:
                result["metadata"] = {
                    k: v for k, v in metadata.items() if k != "text"
                }

            results.append(result)

        if not results:
            return {
                "query": query,
                "results": [],
                "message": "No results above similarity threshold."
            }

        return {
            "query": query,
            "results": results
        }