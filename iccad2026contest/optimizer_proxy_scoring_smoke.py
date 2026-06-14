#!/usr/bin/env python3
"""Synthetic fixtures for proxy scoring terms.

Run from the repository root with:

    python -B iccad2026contest/optimizer_proxy_scoring_smoke.py
"""

import math
from typing import List, Optional, Sequence, Tuple

from iccad2026_evaluate import (
    calculate_bbox_area,
    calculate_hpwl_b2b,
    calculate_hpwl_p2b,
)
from my_optimizer import (
    Candidate,
    HARD_BARRIER,
    PROXY_BBOX_WEIGHT,
    PROXY_HPWL_WEIGHT,
    PROXY_SOFT_EXPONENT,
    PROXY_SOFT_WEIGHT,
    SolverContext,
    _build_immutable_geometry,
    _parse_inputs,
    _plan_dimensions,
    _preflight,
    _score_candidate,
)


Rect = Tuple[float, float, float, float]


def _assert_close(actual: float, expected: float, tol: float = 1e-9) -> None:
    assert abs(actual - expected) <= tol, (actual, expected)


def _context(
    areas: Sequence[float],
    constraints: Optional[Sequence[Sequence[float]]] = None,
    b2b_edges: Optional[Sequence[Sequence[float]]] = None,
    p2b_edges: Optional[Sequence[Sequence[float]]] = None,
    pins: Optional[Sequence[Sequence[float]]] = None,
) -> SolverContext:
    if constraints is None:
        constraints = [[0, 0, 0, 0, 0] for _ in areas]
    parsed = _parse_inputs(
        len(areas),
        list(areas),
        [] if b2b_edges is None else [list(edge) for edge in b2b_edges],
        [] if p2b_edges is None else [list(edge) for edge in p2b_edges],
        [] if pins is None else [list(pin) for pin in pins],
        [list(row) for row in constraints],
        None,
    )
    immutable = _build_immutable_geometry(parsed)
    dimensions = _plan_dimensions(parsed, immutable)
    return SolverContext(parsed, immutable, dimensions)


def _scored_candidate(context: SolverContext, positions: Sequence[Rect]):
    candidate = Candidate(list(positions), "manual", 1)
    candidate.hard_report = _preflight(
        candidate,
        context.parsed,
        context.immutable,
        context.dimensions,
    )
    return candidate, _score_candidate(candidate, context.parsed)


def test_hpwl_and_bbox_match_hand_calculation_and_evaluator_helpers() -> None:
    positions = [
        (0.0, 0.0, 2.0, 2.0),
        (4.0, 1.0, 2.0, 2.0),
        (1.0, 5.0, 2.0, 4.0),
    ]
    b2b_edges = [[0, 1, 2.0], [1, 2, 0.5], [-1, -1, -1.0]]
    p2b_edges = [[0, 2, 3.0], [1, 0, 0.25], [-1, -1, -1.0]]
    pins = [[1.0, 4.0], [10.0, 2.0]]
    context = _context(
        [4.0, 4.0, 8.0],
        b2b_edges=b2b_edges,
        p2b_edges=p2b_edges,
        pins=pins,
    )

    candidate, score = _scored_candidate(context, positions)

    assert candidate.hard_report is not None
    assert candidate.hard_report.hard_feasible
    _assert_close(score.hpwl_b2b, 14.0)
    _assert_close(score.hpwl_p2b, 14.5)
    _assert_close(score.hpwl_total, 28.5)
    _assert_close(score.bbox_area, 54.0)
    _assert_close(score.hpwl_b2b, calculate_hpwl_b2b(positions, b2b_edges))
    _assert_close(score.hpwl_p2b, calculate_hpwl_p2b(positions, p2b_edges, pins))
    _assert_close(score.bbox_area, calculate_bbox_area(positions))
    _assert_close(
        score.score,
        PROXY_HPWL_WEIGHT * 28.5 + PROXY_BBOX_WEIGHT * 54.0,
    )


def test_empty_connectivity_yields_zero_hpwl() -> None:
    context = _context([1.0, 4.0])
    _, score = _scored_candidate(
        context,
        [(0.0, 0.0, 1.0, 1.0), (1.0, 0.0, 2.0, 2.0)],
    )

    assert score.hpwl_b2b == 0.0
    assert score.hpwl_p2b == 0.0
    assert score.hpwl_total == 0.0


def test_soft_violation_terms_are_recorded_without_affecting_hard_feasibility() -> None:
    context = _context(
        [1.0, 4.0, 4.0],
        constraints=[
            [0, 0, 1, 2, 1],
            [0, 0, 1, 2, 0],
            [0, 0, 0, 0, 2],
        ],
    )
    candidate, score = _scored_candidate(
        context,
        [
            (1.0, 0.0, 1.0, 1.0),
            (4.0, 0.0, 2.0, 2.0),
            (0.0, 3.0, 2.0, 2.0),
        ],
    )

    assert candidate.hard_report is not None
    assert candidate.hard_report.hard_feasible
    assert score.boundary_violations == 2
    assert score.grouping_violations == 1
    assert score.mib_violations == 1
    assert score.total_soft_violations == 4
    assert score.max_possible_violations == 4
    assert score.soft_relative == 1.0
    assert score.score >= PROXY_SOFT_WEIGHT


def test_soft_violation_factor_can_dominate_large_raw_hpwl_savings() -> None:
    context = _context(
        [1.0, 1.0],
        constraints=[
            [0, 0, 0, 0, 1],
            [0, 0, 0, 0, 0],
        ],
        b2b_edges=[[0, 1, 1.0]],
    )

    soft_candidate, soft_score = _scored_candidate(
        context,
        [
            (1.0, 0.0, 1.0, 1.0),
            (0.0, 0.0, 1.0, 1.0),
        ],
    )
    clean_candidate, clean_score = _scored_candidate(
        context,
        [
            (0.0, 0.0, 1.0, 1.0),
            (5000.0, 0.0, 1.0, 1.0),
        ],
    )

    assert soft_candidate.hard_report is not None
    assert clean_candidate.hard_report is not None
    assert soft_candidate.hard_report.hard_feasible
    assert clean_candidate.hard_report.hard_feasible
    assert soft_score.total_soft_violations == 1
    assert clean_score.total_soft_violations == 0
    assert soft_score.hpwl_total < clean_score.hpwl_total
    assert soft_score.score > clean_score.score
    _assert_close(
        soft_score.score,
        (
            1.0
            + PROXY_HPWL_WEIGHT * soft_score.hpwl_total
            + PROXY_BBOX_WEIGHT * soft_score.bbox_area
            + PROXY_SOFT_WEIGHT * soft_score.soft_relative
        )
        * math.exp(PROXY_SOFT_EXPONENT * soft_score.soft_relative)
        - 1.0,
    )


def test_hard_infeasible_report_adds_barrier() -> None:
    context = _context([1.0, 1.0])
    candidate, score = _scored_candidate(
        context,
        [(0.0, 0.0, 1.0, 1.0), (0.5, 0.0, 1.0, 1.0)],
    )

    assert candidate.hard_report is not None
    assert not candidate.hard_report.hard_feasible
    assert score.hard_barrier == HARD_BARRIER
    assert score.score >= HARD_BARRIER


def test_nonfinite_geometry_produces_finite_barrier_score() -> None:
    context = _context([1.0, 1.0])
    candidate, score = _scored_candidate(
        context,
        [(math.nan, 0.0, 1.0, 1.0), (1.0, 0.0, 1.0, 1.0)],
    )

    assert candidate.hard_report is not None
    assert not candidate.hard_report.hard_feasible
    assert score.hard_barrier == HARD_BARRIER
    assert math.isfinite(score.score)
    assert not math.isnan(score.score)
    assert score.score >= HARD_BARRIER


def run_smoke() -> None:
    test_hpwl_and_bbox_match_hand_calculation_and_evaluator_helpers()
    test_empty_connectivity_yields_zero_hpwl()
    test_soft_violation_terms_are_recorded_without_affecting_hard_feasibility()
    test_soft_violation_factor_can_dominate_large_raw_hpwl_savings()
    test_hard_infeasible_report_adds_barrier()
    test_nonfinite_geometry_produces_finite_barrier_score()


if __name__ == "__main__":
    run_smoke()
    print("optimizer-proxy-scoring smoke passed")
