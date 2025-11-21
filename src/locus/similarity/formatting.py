# Complete code content here - do not skip any lines
"""Formatting utilities for similarity search results."""

from typing import Optional

from ..formatting.colors import print_header, print_info
from ..models import AnalysisResult  # Import for serialize_similarity
from .types import SimilarityResult


def serialize_similarity(result: AnalysisResult) -> dict:
    """Serializes a SimilarityResult object to a JSON-friendly dictionary."""
    sim = getattr(result, "similarity", None)
    if not sim:
        return {}
    # Convert dataclasses to JSON-friendly structures
    return {
        "meta": getattr(sim, "meta", {}),
        "units": [
            {
                "id": u.id,
                "file": u.file,
                "rel_path": u.rel_path,
                "qualname": u.qualname,
                "span": list(u.span),
            }
            for u in sim.units
        ],
        "clusters": [
            {
                "id": c.id,
                "member_ids": list(c.member_ids),
                "strategy": c.strategy,
                "score_min": c.score_min,
                "score_max": c.score_max,
            }
            for c in sim.clusters
        ],
        "matches": [
            {
                "a_id": m.a_id,
                "b_id": m.b_id,
                "score": m.score,
                "strategy": m.strategy,
            }
            for m in sim.matches
        ],
    }


def print_similarity_summary(
    sim: Optional[SimilarityResult],
    strategy: str,
    show_members: bool = True,
    member_bullet: str = "·",
) -> None:
    """Print a concise similarity summary consistently across commands.

    - Prints header and either a no-results message or a summary with optional members.
    - ``member_bullet`` controls the bullet used for member lines (e.g., "·" or "-").
    """
    print_header("Similar or Duplicate Functions")
    if not sim or not getattr(sim, "clusters", None):
        print_info(f"No duplicates found (strategy: {strategy}).")
        return
    print_info(
        f"Strategy: {strategy} · Units: {len(sim.units)} · Clusters: {len(sim.clusters)}"
    )
    if not show_members:
        return
    for cluster in sim.clusters:
        print(f"- Cluster {cluster.id} (size {len(cluster.member_ids)}):")
        ids = set(cluster.member_ids)
        members = [u for u in sim.units if u.id in ids]
        for u in sorted(members, key=lambda x: (x.rel_path, x.span[0])):
            print(
                f"    {member_bullet} {u.rel_path}:{u.span[0]}-{u.span[1]}  {u.qualname}"
            )
