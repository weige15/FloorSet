#!/usr/bin/env python3
"""Synthetic fixtures for deterministic legal fallback placement.

Run from the repository root with:

    python -B iccad2026contest/optimizer_fallback_smoke.py
"""

import math
import random
from typing import List, Optional, Sequence, Tuple

from my_optimizer import (
    Candidate,
    CandidateManager,
    SolverContext,
    _bbox_area,
    _build_fallback,
    _build_immutable_geometry,
    _parse_inputs,
    _plan_dimensions,
    _preflight,
    _rects_overlap,
)


Rect = Tuple[float, float, float, float]


def _constraints(rows: Sequence[Sequence[float]]) -> List[List[float]]:
    return [list(row) for row in rows]


def _parsed(
    areas: Sequence[float],
    constraints: Optional[Sequence[Sequence[float]]] = None,
    targets: Optional[Sequence[Sequence[float]]] = None,
):
    if constraints is None:
        constraints = [[0, 0, 0, 0, 0] for _ in areas]
    return _parse_inputs(
        len(areas),
        list(areas),
        [],
        [],
        [],
        _constraints(constraints),
        targets,
    )


def _fallback_for(parsed):
    immutable = _build_immutable_geometry(parsed)
    dimensions = _plan_dimensions(parsed, immutable)
    return immutable, dimensions, _build_fallback(parsed, immutable, dimensions)


def _assert_hard_feasible(parsed, immutable, dimensions, candidate: Candidate) -> None:
    assert candidate.hard_report is not None
    assert candidate.hard_report.hard_feasible, candidate.hard_report
    report = _preflight(candidate, parsed, immutable, dimensions)
    assert report.hard_feasible, report
    assert report.malformed_violations == 0
    assert report.overlap_violations == 0
    assert report.area_violations == 0
    assert report.dimension_violations == 0

    for rect in candidate.positions:
        x, y, width, height = rect
        assert math.isfinite(x) and math.isfinite(y)
        assert math.isfinite(width) and math.isfinite(height)
        assert width > 0.0 and height > 0.0


def test_two_all_soft_blocks_use_horizontal_id_order() -> None:
    parsed = _parsed([4.0, 9.0])
    immutable, dimensions, fallback = _fallback_for(parsed)

    assert fallback.positions == [
        (0.0, 0.0, 2.0, 2.0),
        (2.0, 0.0, 3.0, 3.0),
    ]
    assert _bbox_area(fallback.positions) == 15.0
    _assert_hard_feasible(parsed, immutable, dimensions, fallback)


def test_fixed_shape_plus_soft_uses_planned_dimensions() -> None:
    parsed = _parsed(
        [10.0, 4.0],
        constraints=[
            [1, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ],
        targets=[
            [-1, -1, 2.0, 5.0],
            [-1, -1, -1, -1],
        ],
    )
    immutable, dimensions, fallback = _fallback_for(parsed)

    assert fallback.positions == [
        (0.0, 0.0, 2.0, 5.0),
        (2.0, 0.0, 2.0, 2.0),
    ]
    _assert_hard_feasible(parsed, immutable, dimensions, fallback)


def test_preplaced_obstacle_is_exact_and_movable_shelf_is_to_the_right() -> None:
    parsed = _parsed(
        [8.0, 9.0],
        constraints=[
            [0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ],
        targets=[
            [10.0, 3.0, 4.0, 2.0],
            [-1, -1, -1, -1],
        ],
    )
    immutable, dimensions, fallback = _fallback_for(parsed)

    assert fallback.positions == [
        (10.0, 3.0, 4.0, 2.0),
        (15.0, 0.0, 3.0, 3.0),
    ]
    assert not _rects_overlap(fallback.positions[0], fallback.positions[1])
    _assert_hard_feasible(parsed, immutable, dimensions, fallback)


def test_one_row_fallback_is_kept_when_wrapping_would_hurt_bbox() -> None:
    parsed = _parsed([1.0] * 12)
    immutable, dimensions, fallback = _fallback_for(parsed)

    assert fallback.source_order == 0
    assert fallback.positions[-1] == (11.0, 0.0, 1.0, 1.0)
    assert _bbox_area(fallback.positions) == 12.0
    _assert_hard_feasible(parsed, immutable, dimensions, fallback)


def test_compact_fallback_variant_is_used_when_proxy_improves() -> None:
    parsed = _parsed([100.0] + [1.0] * 11)
    immutable, dimensions, fallback = _fallback_for(parsed)

    assert fallback.source_order == 1
    assert fallback.positions[0] == (0.0, 0.0, 10.0, 10.0)
    assert fallback.positions[6] == (0.0, 10.0, 1.0, 1.0)
    assert _bbox_area(fallback.positions) == 165.0
    _assert_hard_feasible(parsed, immutable, dimensions, fallback)


def test_edge_touching_is_legal_and_positive_overlap_is_illegal() -> None:
    parsed = _parsed([1.0, 1.0])
    immutable = _build_immutable_geometry(parsed)
    dimensions = _plan_dimensions(parsed, immutable)

    edge_touching = Candidate(
        [(0.0, 0.0, 1.0, 1.0), (1.0, 0.0, 1.0, 1.0)],
        "manual",
        1,
    )
    edge_report = _preflight(edge_touching, parsed, immutable, dimensions)
    assert edge_report.hard_feasible
    assert edge_report.overlap_violations == 0

    positive_overlap = Candidate(
        [(0.0, 0.0, 1.0, 1.0), (0.5, 0.0, 1.0, 1.0)],
        "manual",
        2,
    )
    overlap_report = _preflight(positive_overlap, parsed, immutable, dimensions)
    assert not overlap_report.hard_feasible
    assert overlap_report.overlap_violations == 1


def test_candidate_manager_retains_preflighted_fallback() -> None:
    parsed = _parsed([4.0, 9.0])
    immutable, dimensions, fallback = _fallback_for(parsed)
    manager = CandidateManager(SolverContext(parsed, immutable, dimensions))

    retained = manager.consider(fallback)

    assert retained.hard_report is not None
    assert retained.hard_report.hard_feasible
    assert manager.best_feasible_or_fallback() is retained


def test_randomized_hard_feasibility_properties() -> None:
    for seed in range(20):
        rng = random.Random(seed)
        block_count = rng.randint(2, 8)
        areas = [rng.uniform(1.0, 100.0) for _ in range(block_count)]
        constraints = [[0, 0, 0, 0, 0] for _ in range(block_count)]
        targets = [[-1, -1, -1, -1] for _ in range(block_count)]

        if seed % 2 == 0:
            width = rng.uniform(1.0, 8.0)
            height = rng.uniform(1.0, 8.0)
            constraints[0][1] = 1
            targets[0] = [
                rng.uniform(-20.0, 20.0),
                rng.uniform(-10.0, 10.0),
                width,
                height,
            ]

        parsed = _parsed(areas, constraints=constraints, targets=targets)
        immutable, dimensions, fallback = _fallback_for(parsed)
        _assert_hard_feasible(parsed, immutable, dimensions, fallback)


def run_smoke() -> None:
    test_two_all_soft_blocks_use_horizontal_id_order()
    test_fixed_shape_plus_soft_uses_planned_dimensions()
    test_preplaced_obstacle_is_exact_and_movable_shelf_is_to_the_right()
    test_one_row_fallback_is_kept_when_wrapping_would_hurt_bbox()
    test_compact_fallback_variant_is_used_when_proxy_improves()
    test_edge_touching_is_legal_and_positive_overlap_is_illegal()
    test_candidate_manager_retains_preflighted_fallback()
    test_randomized_hard_feasibility_properties()


if __name__ == "__main__":
    run_smoke()
    print("optimizer-fallback smoke passed")
