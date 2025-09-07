from dataclasses import dataclass
from typing import Optional, Literal

from ..models import AnalysisResult
from .extractor import extract_code_units
from .strategies import ExactHashStrategy
from .types import SimilarityResult


StrategyName = Literal["exact"]  # MVP


@dataclass
class SimilarityConfig:
    strategy: StrategyName = "exact"
    threshold: float = 1.0
    max_candidates: int = 0  # unused in MVP


def run(result: AnalysisResult, config: Optional[SimilarityConfig] = None) -> SimilarityResult:
    cfg = config or SimilarityConfig()
    units = extract_code_units(result)
    # Select strategy (MVP: exact only)
    strat = ExactHashStrategy()
    strat.prepare(units)
    clusters, matches = strat.find_clusters(units)
    return SimilarityResult(units=units, clusters=clusters, matches=matches, meta={"strategy": strat.name})

