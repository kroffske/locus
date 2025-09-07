import hashlib
from collections import defaultdict
from typing import Dict, List, Iterable, Tuple

from .normalize import normalize_text
from .types import CodeUnit, Match, Cluster


class SimilarityStrategy:
    name = "base"

    def prepare(self, units: List[CodeUnit]):
        raise NotImplementedError

    def find_clusters(self, units: List[CodeUnit]) -> Tuple[List[Cluster], List[Match]]:
        raise NotImplementedError


class ExactHashStrategy(SimilarityStrategy):
    name = "exact"

    def __init__(self):
        self.map: Dict[str, List[int]] = defaultdict(list)

    def _key(self, unit: CodeUnit) -> str:
        text = normalize_text(unit.source)
        return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()

    def prepare(self, units: List[CodeUnit]):
        for u in units:
            self.map[self._key(u)].append(u.id)

    def find_clusters(self, units: List[CodeUnit]):
        clusters: List[Cluster] = []
        matches: List[Match] = []
        cid = 0
        for key, ids in self.map.items():
            if len(ids) <= 1:
                continue
            clusters.append(Cluster(id=cid, member_ids=list(ids), strategy=self.name, score_min=1.0, score_max=1.0))
            # Generate pairwise matches (score 1.0)
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    matches.append(Match(a_id=ids[i], b_id=ids[j], score=1.0, strategy=self.name))
            cid += 1
        return clusters, matches

