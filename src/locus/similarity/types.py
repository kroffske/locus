from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CodeUnit:
    id: int
    file: str
    rel_path: str
    qualname: str
    span: Tuple[int, int]
    source: str


@dataclass
class Match:
    a_id: int
    b_id: int
    score: float
    strategy: str
    evidence: Optional[Dict[str, Any]] = None


@dataclass
class Cluster:
    id: int
    member_ids: List[int] = field(default_factory=list)
    strategy: str = "exact"
    score_min: float = 1.0
    score_max: float = 1.0


@dataclass
class SimilarityResult:
    units: List[CodeUnit]
    clusters: List[Cluster]
    matches: List[Match]
    meta: Dict[str, Any] = field(default_factory=dict)
