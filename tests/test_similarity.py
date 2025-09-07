from pathlib import Path

import json

from locus.core import orchestrator
from locus.models import TargetSpecifier
from locus.similarity import run as run_similarity
from locus.similarity.search import SimilarityConfig


def _analyze_with_similarity(project_root: Path):
    result = orchestrator.analyze(
        project_path=str(project_root),
        target_specs=[TargetSpecifier(path=str(project_root / "src"))],
        max_depth=-1,
        include_patterns=None,
        exclude_patterns=None,
    )
    sim_result = run_similarity(result, SimilarityConfig(strategy="exact"))
    return sim_result


def test_exact_duplicates_found(project_structure: Path):
    src = project_structure / "src"
    (src / "dup_a.py").write_text(
        """
def foo():
    x = 1
    return x
""".strip()
    )
    # Identical content
    (src / "dup_b.py").write_text(
        """
def foo():
    x = 1
    return x
""".strip()
    )

    sim = _analyze_with_similarity(project_structure)

    # Expect at least one cluster containing both files' foo
    member_paths = []
    for c in sim.clusters:
        ids = set(c.member_ids)
        units = [u for u in sim.units if u.id in ids]
        rels = {u.rel_path.replace("\\", "/") for u in units}
        if {"src/dup_a.py", "src/dup_b.py"}.issubset(rels):
            member_paths = list(rels)
            break

    assert {"src/dup_a.py", "src/dup_b.py"}.issubset(set(member_paths))


def test_exact_duplicates_whitespace_variation(project_structure: Path):
    src = project_structure / "src"
    (src / "ws_a.py").write_text(
        """
def foo():
    x   =   1
    return    x
""".strip()
    )
    # Same logic, different whitespace
    (src / "ws_b.py").write_text(
        """
def foo():
    x = 1
    return x
""".strip()
    )

    sim = _analyze_with_similarity(project_structure)

    # Should still cluster under exact normalized text strategy
    found = False
    for c in sim.clusters:
        ids = set(c.member_ids)
        units = [u for u in sim.units if u.id in ids]
        rels = {u.rel_path.replace("\\", "/") for u in units}
        if {"src/ws_a.py", "src/ws_b.py"}.issubset(rels):
            found = True
            break
    assert found


def test_exact_duplicates_small_change_not_grouped(project_structure: Path):
    src = project_structure / "src"
    (src / "chg_a.py").write_text(
        """
def foo():
    x = 1
    return x
""".strip()
    )
    # Change a literal; exact strategy should not match
    (src / "chg_b.py").write_text(
        """
def foo():
    x = 2
    return x
""".strip()
    )

    sim = _analyze_with_similarity(project_structure)

    # Ensure there is no cluster that includes both files together
    for c in sim.clusters:
        ids = set(c.member_ids)
        units = [u for u in sim.units if u.id in ids]
        rels = {u.rel_path.replace("\\", "/") for u in units}
        assert not {"src/chg_a.py", "src/chg_b.py"}.issubset(rels)


def test_similarity_json_dump_basic(project_structure: Path, tmp_path: Path):
    # Create an exact duplicate to ensure non-empty output
    src = project_structure / "src"
    (src / "jd_a.py").write_text("def f():\n    return 1\n")
    (src / "jd_b.py").write_text("def f():\n    return    1\n")

    result = orchestrator.analyze(
        project_path=str(project_structure),
        target_specs=[TargetSpecifier(path=str(project_structure / "src"))],
        max_depth=-1,
        include_patterns=None,
        exclude_patterns=None,
    )
    sim = run_similarity(result, SimilarityConfig(strategy="exact"))
    result.similarity = sim

    # Serialize to JSON structure similar to CLI helper
    payload = {
        "units": [
            {"id": u.id, "rel_path": u.rel_path, "qualname": u.qualname, "span": list(u.span)}
            for u in sim.units
        ],
        "clusters": [
            {"id": c.id, "member_ids": list(c.member_ids), "strategy": c.strategy}
            for c in sim.clusters
        ],
    }
    out = tmp_path / "sim.json"
    out.write_text(json.dumps(payload))
    # Basic sanity check
    data = json.loads(out.read_text())
    assert "units" in data and "clusters" in data
    assert any(len(c["member_ids"]) >= 2 for c in data["clusters"])  # at least one duplicate cluster


# Future, strategy-agnostic tests to include:
# - test_similarity_ignores_non_python_files
# - test_similarity_handles_syntax_errors_gracefully
# - test_similarity_scales_with_many_small_functions (performance budget)
# - test_similarity_reports_spans_and_qualnames_correctly
# - test_similarity_no_false_positives_across_different_functions
