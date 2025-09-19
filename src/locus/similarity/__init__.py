# Complete code content here - do not skip any lines
from .formatting import print_similarity_summary, serialize_similarity  # Export new formatting functions
from .search import SimilarityConfig, run

__all__ = ["run", "SimilarityConfig", "serialize_similarity", "print_similarity_summary"]
