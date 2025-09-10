from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Literal, Optional

from ..models import AnalysisResult
from .extractor import extract_code_units
from .strategies import ASTCanonicalHashStrategy, ExactHashStrategy
from .types import SimilarityResult

if TYPE_CHECKING:
    from .types import CodeUnit


StrategyName = Literal["exact", "ast"]


@dataclass
class SimilarityConfig:
    strategy: StrategyName = "exact"
    threshold: float = 1.0
    max_candidates: int = 0  # unused in MVP
    include_init: bool = False  # exclude __init__ by default


def _filter_units(units: List["CodeUnit"], include_init: bool) -> List["CodeUnit"]:
    if include_init:
        return units
    filtered = []
    for u in units:
        q = u.qualname or ""
        if q.endswith(".__init__") or q == "__init__":
            continue
        filtered.append(u)
    return filtered


def run(result: AnalysisResult, config: Optional[SimilarityConfig] = None) -> SimilarityResult:
    cfg = config or SimilarityConfig()
    units = extract_code_units(result)
    units = _filter_units(units, include_init=cfg.include_init)
    # Select strategy
    if cfg.strategy == "ast":
        strat = ASTCanonicalHashStrategy()
    else:
        strat = ExactHashStrategy()
    strat.prepare(units)
    clusters, matches = strat.find_clusters(units)
    return SimilarityResult(units=units, clusters=clusters, matches=matches, meta={"strategy": strat.name})
