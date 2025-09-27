from __future__ import annotations

from typing import List


class EmbeddingComponent:
    """Adapter for HuggingFace SentenceTransformer models using lazy imports."""

    def __init__(self, model_name: str, trust_remote_code: bool = True):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "SentenceTransformers is not installed. Please install with: pip install 'locus-analyzer[mcp]'"
            )
        self.model = SentenceTransformer(
            model_name, trust_remote_code=trust_remote_code
        )
        self.query_prefix = "Represent this query for searching relevant code: "

    def embed_chunks(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()

    def embed_query(self, query: str) -> List[float]:
        return self.model.encode(
            [self.query_prefix + query], normalize_embeddings=True
        )[0].tolist()
