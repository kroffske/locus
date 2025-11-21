import hashlib
from collections import defaultdict
from typing import Dict, List, Tuple

from .ast_canonical import canonicalize_function_source
from .normalize import normalize_text
from .types import Cluster, CodeUnit, Match


class SimilarityStrategy:
    name = "base"

    def prepare(self, units: List[CodeUnit]):
        raise NotImplementedError

    def find_clusters(self, units: List[CodeUnit]) -> Tuple[List[Cluster], List[Match]]:
        raise NotImplementedError


class _HashSimilarityStrategy(SimilarityStrategy):
    """Common logic for hash-based grouping strategies.

    Subclasses must implement ``_key(unit) -> str`` and ``name``.
    """

    def __init__(self):
        self.map: Dict[str, List[int]] = defaultdict(list)

    def _key(self, unit: CodeUnit) -> str:  # pragma: no cover - abstract by convention
        raise NotImplementedError

    def prepare(self, units: List[CodeUnit]):
        for u in units:
            try:
                key = self._key(u)
            except Exception:
                # Skip units that fail key generation
                continue
            self.map[key].append(u.id)

    def find_clusters(self, units: List[CodeUnit]):
        clusters: List[Cluster] = []
        matches: List[Match] = []
        cid = 0
        for _, ids in self.map.items():
            if len(ids) <= 1:
                continue
            clusters.append(
                Cluster(
                    id=cid,
                    member_ids=list(ids),
                    strategy=self.name,
                    score_min=1.0,
                    score_max=1.0,
                )
            )
            # Generate pairwise matches (score 1.0)
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    matches.append(
                        Match(a_id=ids[i], b_id=ids[j], score=1.0, strategy=self.name)
                    )
            cid += 1
        return clusters, matches


class ExactHashStrategy(_HashSimilarityStrategy):
    name = "exact"

    def _key(self, unit: CodeUnit) -> str:
        text = normalize_text(unit.source)
        return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


class ASTCanonicalHashStrategy(_HashSimilarityStrategy):
    name = "ast"

    def _key(self, unit: CodeUnit) -> str:
        canon = canonicalize_function_source(unit.source)
        return hashlib.sha256(canon.encode("utf-8", errors="ignore")).hexdigest()
