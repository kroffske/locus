"""
Run all similarity benchmark cases and print a pass/fail summary.

Usage:
  - Ensure the package is importable:
      pip install -e .[dev]
    or run with PYTHONPATH:
      PYTHONPATH=src python tests/benchmarks/run_benchmarks.py

  - Execute:
      python tests/benchmarks/run_benchmarks.py [--strategy exact|ast|all] [--json-out path]

Semantics:
  - Evaluates every case with the chosen strategy (or both with --strategy all).
  - Counts passes/fails; failures are informative (e.g., near-miss cases under exact hashing).
  - Reports per-strategy metrics (positives recall, negatives false positives, missing units).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

try:
    import yaml  # type: ignore
except Exception:
    print("PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

from locus.core import orchestrator
from locus.models import TargetSpecifier
from locus.similarity import run as run_similarity
from locus.similarity.search import SimilarityConfig


@dataclass
class CaseSpec:
    root: Path
    id: str
    type: str
    expected_strategy: str
    expected_threshold: float
    members: Dict[str, Tuple[str, str]]  # label -> (file, qualname)
    pairs: List[Tuple[str, str, str]]  # (left_label, right_label, relation)


def load_case_meta(meta_path: Path) -> CaseSpec:
    data = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
    members = {
        m["label"]: (m["file"], m.get("qualname", "")) for m in data.get("members", [])
    }
    pairs = [
        (p["left"], p["right"], p.get("relation", "similar"))
        for p in data.get("pairs", [])
    ]
    expected = data.get("expected", {})
    return CaseSpec(
        root=meta_path.parent,
        id=data.get("id", meta_path.parent.name),
        type=str(data.get("type", "T1")),
        expected_strategy=str(expected.get("strategy", "any")),
        expected_threshold=float(expected.get("threshold", 1.0)),
        members=members,
        pairs=pairs,
    )


def strategies_to_run(selection: str) -> Iterable[str]:
    if selection == "exact":
        return ("exact",)
    if selection == "ast":
        return ("ast",)
    return ("exact", "ast")


def run_case_with_strategy(case: CaseSpec, strat: str) -> Tuple[str, str, Dict]:
    """Return (status, message, details) for a single strategy. status: PASS|FAIL"""
    result = orchestrator.analyze(
        project_path=str(case.root),
        target_specs=[TargetSpecifier(path=str(case.root))],
        max_depth=-1,
        include_patterns=None,
        exclude_patterns=None,
    )
    sim = run_similarity(result, SimilarityConfig(strategy=strat))

    # Build lookup: (file_basename, qualname) -> unit id
    def key(rel_path: str, qualname: str) -> Tuple[str, str]:
        return (Path(rel_path).name.replace("\\", "/"), qualname)

    unit_by_key: Dict[Tuple[str, str], int] = {}
    for u in sim.units:
        unit_by_key[key(u.rel_path, u.qualname or "")] = u.id

    # Map id to cluster id
    cluster_of: Dict[int, int] = {}
    for c in sim.clusters:
        for mid in c.member_ids:
            cluster_of[mid] = c.id

    failures: List[str] = []
    missing_pairs = 0
    pos_expected = 0
    pos_detected = 0
    neg_expected = 0
    neg_fp = 0
    for left, right, relation in case.pairs:
        lf, lq = case.members[left]
        rf, rq = case.members[right]
        lid = unit_by_key.get(key(lf, lq))
        rid = unit_by_key.get(key(rf, rq))
        if relation in {"duplicate", "similar"}:
            pos_expected += 1
        elif relation == "negative":
            neg_expected += 1
        if lid is None or rid is None:
            missing_pairs += 1
            failures.append(f"Missing units: {left}={lf}:{lq} or {right}={rf}:{rq}")
            # Count as fail: missed positive or false-positive negative
            if relation in {"duplicate", "similar"}:
                # missed
                pass
            elif relation == "negative":
                neg_fp += 1
            continue
        same = cluster_of.get(lid) is not None and cluster_of.get(
            lid
        ) == cluster_of.get(rid)
        if relation in {"duplicate", "similar"}:
            if same:
                pos_detected += 1
            else:
                failures.append(f"Expected same cluster for {left}-{right}")
        elif relation == "negative":
            if same:
                neg_fp += 1
                failures.append(f"Expected different clusters for {left}-{right}")
        else:
            # Unknown relation; be conservative
            failures.append(f"Unknown relation '{relation}' for {left}-{right}")

    status = "PASS" if not failures else "FAIL"
    msg = f"strategy={strat} · pos {pos_detected}/{pos_expected} · neg_fp {neg_fp}/{neg_expected} · missing {missing_pairs}"
    return (
        status,
        msg,
        {
            "strategy": strat,
            "positives_expected": pos_expected,
            "positives_detected": pos_detected,
            "negatives_expected": neg_expected,
            "negatives_fp": neg_fp,
            "missing_pairs": missing_pairs,
            "failures": failures,
        },
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Run similarity benchmark cases and summarize results"
    )
    ap.add_argument(
        "--strategy",
        choices=["exact", "ast", "all"],
        default="all",
        help="Which strategy to evaluate against all cases",
    )
    ap.add_argument("--json-out", help="Optional path to write JSON summary")
    ap.add_argument(
        "--include-init",
        action="store_true",
        help="Include __init__ methods in similarity (default: excluded)",
    )
    args = ap.parse_args()
    base = Path(__file__).parent / "cases"
    metas = sorted(base.glob("case-*/meta.yaml"))
    if not metas:
        print("No benchmark cases found.")
        return 1
    results: List[Tuple[str, str, str]] = []  # (case_id, status, msg)
    strategies = list(strategies_to_run(args.strategy))
    grand_json: Dict[str, Dict] = {s: {"cases": [], "metrics": {}} for s in strategies}
    overall_exit = 0
    for strat in strategies:
        print("=" * 60)
        print(f"Strategy: {strat}")
        results: List[Tuple[str, str, str]] = []
        metrics = {
            "positives_expected": 0,
            "positives_detected": 0,
            "negatives_expected": 0,
            "negatives_fp": 0,
            "missing_pairs": 0,
            "cases_pass": 0,
            "cases_fail": 0,
        }
        for mp in metas:
            case = load_case_meta(mp)
            status, msg, det = run_case_with_strategy(case, strat)
            results.append((case.id, status, msg))
            print(f"[{status}] {case.id}: {msg}")
            metrics["positives_expected"] += det["positives_expected"]
            metrics["positives_detected"] += det["positives_detected"]
            metrics["negatives_expected"] += det["negatives_expected"]
            metrics["negatives_fp"] += det["negatives_fp"]
            metrics["missing_pairs"] += det["missing_pairs"]
            metrics["cases_pass"] += 1 if status == "PASS" else 0
            metrics["cases_fail"] += 1 if status == "FAIL" else 0
            grand_json[strat]["cases"].append(
                {"case": case.id, "status": status, "message": msg, **det}
            )
        print("-" * 60)
        print(
            "Summary:"
            f" cases PASS={metrics['cases_pass']} FAIL={metrics['cases_fail']} TOTAL={len(results)} |"
            f" pos {metrics['positives_detected']}/{metrics['positives_expected']}"
            f" neg_fp {metrics['negatives_fp']}/{metrics['negatives_expected']}"
            f" missing {metrics['missing_pairs']}"
        )
        grand_json[strat]["metrics"] = metrics
        if metrics["cases_fail"] > 0:
            overall_exit = 1
    if args.json_out:
        Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_out).write_text(
            json.dumps(grand_json, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Wrote JSON summary to {args.json_out}")
    return overall_exit


if __name__ == "__main__":
    sys.exit(main())
