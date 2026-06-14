#!/usr/bin/env python3
"""Synthetic fixtures for candidate manager retention behavior.

Run from the repository root with:

    python -B iccad2026contest/optimizer_candidate_manager_smoke.py
"""

from typing import Callable, List, Optional

import math

from my_optimizer import (
    Candidate,
    CandidateManager,
    ProxyScore,
    SolverContext,
    _build_fallback,
    _build_immutable_geometry,
    _parse_inputs,
    _plan_dimensions,
)


def _context(areas: Optional[List[float]] = None) -> SolverContext:
    if areas is None:
        areas = [1.0, 1.0]
    parsed = _parse_inputs(
        len(areas),
        areas,
        [],
        [],
        [],
        [[0, 0, 0, 0, 0] for _ in areas],
        None,
    )
    immutable = _build_immutable_geometry(parsed)
    dimensions = _plan_dimensions(parsed, immutable)
    return SolverContext(parsed, immutable, dimensions)


def _score_from_map(scores) -> Callable[[Candidate, object], ProxyScore]:
    def score_fn(candidate: Candidate, parsed) -> ProxyScore:
        del parsed
        score, bbox, hpwl = scores[candidate.source]
        return ProxyScore(score, hpwl, bbox, 0.0, 0.0)

    return score_fn


def test_infeasible_lower_score_cannot_replace_feasible() -> None:
    manager = CandidateManager(
        _context(),
        score_fn=_score_from_map({
            "feasible": (100.0, 100.0, 100.0),
            "overlap": (-100.0, 0.0, 0.0),
        }),
    )
    feasible = Candidate(
        [(0.0, 0.0, 1.0, 1.0), (1.0, 0.0, 1.0, 1.0)],
        "feasible",
        1,
    )
    overlap = Candidate(
        [(0.0, 0.0, 1.0, 1.0), (0.5, 0.0, 1.0, 1.0)],
        "overlap",
        2,
    )

    manager.consider(feasible)
    manager.consider(overlap)

    assert manager.best_feasible_or_fallback() is feasible
    assert manager.best_infeasible is overlap
    assert overlap.hard_report is not None
    assert not overlap.hard_report.hard_feasible


def test_feasible_tie_breaking_uses_score_bbox_hpwl_and_source_order() -> None:
    manager = CandidateManager(
        _context(),
        score_fn=_score_from_map({
            "first": (10.0, 50.0, 50.0),
            "better_score": (9.0, 90.0, 90.0),
            "better_bbox": (9.0, 80.0, 100.0),
            "better_hpwl": (9.0, 80.0, 70.0),
            "later_order": (9.0, 80.0, 70.0),
            "earlier_order": (9.0, 80.0, 70.0),
        }),
    )
    positions = [(0.0, 0.0, 1.0, 1.0), (1.0, 0.0, 1.0, 1.0)]
    first = Candidate(list(positions), "first", 10)
    better_score = Candidate(list(positions), "better_score", 11)
    better_bbox = Candidate(list(positions), "better_bbox", 12)
    better_hpwl = Candidate(list(positions), "better_hpwl", 13)
    later_order = Candidate(list(positions), "later_order", 14)
    earlier_order = Candidate(list(positions), "earlier_order", 1)

    manager.consider(first)
    assert manager.best_feasible_or_fallback() is first
    manager.consider(better_score)
    assert manager.best_feasible_or_fallback() is better_score
    manager.consider(better_bbox)
    assert manager.best_feasible_or_fallback() is better_bbox
    manager.consider(better_hpwl)
    assert manager.best_feasible_or_fallback() is better_hpwl
    manager.consider(later_order)
    assert manager.best_feasible_or_fallback() is better_hpwl
    manager.consider(earlier_order)
    assert manager.best_feasible_or_fallback() is earlier_order


def test_malformed_candidate_is_rejected_from_retention() -> None:
    manager = CandidateManager(_context())
    malformed = Candidate([(0.0, 0.0, 1.0, 1.0)], "malformed", 1)

    manager.consider(malformed)

    assert malformed.hard_report is not None
    assert malformed.hard_report.malformed_violations > 0
    assert manager.best_feasible_candidate() is None
    assert manager.best_infeasible is None
    assert any("rejected malformed candidate malformed" in msg for msg in manager.diagnostics)


def test_malformed_candidate_skips_proxy_scoring() -> None:
    calls = []

    def score_fn(candidate: Candidate, parsed) -> ProxyScore:
        del parsed
        calls.append(candidate.source)
        raise AssertionError("malformed candidates should not be scored")

    manager = CandidateManager(_context(), score_fn=score_fn)
    malformed = Candidate([(0.0, 0.0, 1.0, 1.0)], "malformed", 1)

    manager.consider(malformed)

    assert calls == []
    assert malformed.proxy_score is None
    assert manager.best_feasible_candidate() is None
    assert any("rejected malformed candidate malformed" in msg for msg in manager.diagnostics)


def test_no_optimized_candidate_falls_back_to_feasible_fallback() -> None:
    context = _context([4.0, 9.0])
    manager = CandidateManager(context)
    fallback = _build_fallback(context.parsed, context.immutable, context.dimensions)
    overlap = Candidate(
        [(0.0, 0.0, 2.0, 2.0), (1.0, 0.0, 3.0, 3.0)],
        "overlap",
        1,
    )

    manager.consider(fallback)
    manager.consider(overlap)

    assert fallback.hard_report is not None
    assert fallback.hard_report.hard_feasible
    assert manager.best_feasible_or_fallback() is fallback


def test_proxy_scoring_failure_keeps_feasible_candidate() -> None:
    def failing_score(candidate: Candidate, parsed) -> ProxyScore:
        del candidate, parsed
        raise RuntimeError("forced scoring failure")

    manager = CandidateManager(_context(), score_fn=failing_score)
    feasible = Candidate(
        [(0.0, 0.0, 1.0, 1.0), (1.0, 0.0, 1.0, 1.0)],
        "feasible",
        1,
    )

    manager.consider(feasible)

    assert manager.best_feasible_or_fallback() is feasible
    assert feasible.proxy_score is not None
    assert feasible.proxy_score.hard_barrier == 0.0
    assert any("proxy scoring failed for feasible" in msg for msg in manager.diagnostics)


def test_nonfinite_proxy_score_is_conservative_and_replaceable() -> None:
    def score_fn(candidate: Candidate, parsed) -> ProxyScore:
        del parsed
        if candidate.source == "nonfinite":
            return ProxyScore(math.nan, math.nan, math.inf, 0.0, 0.0)
        return ProxyScore(1.0, 1.0, 1.0, 0.0, 0.0)

    manager = CandidateManager(_context(), score_fn=score_fn)
    positions = [(0.0, 0.0, 1.0, 1.0), (1.0, 0.0, 1.0, 1.0)]
    nonfinite = Candidate(list(positions), "nonfinite", 1)
    finite = Candidate(list(positions), "finite", 2)

    manager.consider(nonfinite)
    assert manager.best_feasible_or_fallback() is nonfinite
    assert nonfinite.proxy_score is not None
    assert math.isfinite(nonfinite.proxy_score.score)
    assert any("proxy scoring failed for nonfinite" in msg for msg in manager.diagnostics)

    manager.consider(finite)
    assert manager.best_feasible_or_fallback() is finite


def run_smoke() -> None:
    test_infeasible_lower_score_cannot_replace_feasible()
    test_feasible_tie_breaking_uses_score_bbox_hpwl_and_source_order()
    test_malformed_candidate_is_rejected_from_retention()
    test_malformed_candidate_skips_proxy_scoring()
    test_no_optimized_candidate_falls_back_to_feasible_fallback()
    test_proxy_scoring_failure_keeps_feasible_candidate()
    test_nonfinite_proxy_score_is_conservative_and_replaceable()


if __name__ == "__main__":
    run_smoke()
    print("optimizer-candidate-manager smoke passed")
