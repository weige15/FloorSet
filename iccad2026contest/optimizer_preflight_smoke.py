#!/usr/bin/env python3
"""Synthetic fixtures for hard-constraint preflight parity.

Run from the repository root with:

    python -B iccad2026contest/optimizer_preflight_smoke.py
"""

import math
import random
from typing import List, Optional, Sequence, Tuple

import torch

from iccad2026_evaluate import (
    check_area_tolerance,
    check_dimension_hard_constraints,
    check_overlap,
)
from my_optimizer import (
    AREA_TOLERANCE,
    Candidate,
    IMMUTABLE_TOLERANCE,
    OVERLAP_TOLERANCE,
    _build_immutable_geometry,
    _count_overlap_violations,
    _parse_inputs,
    _plan_dimensions,
    _preflight,
)


Rect = Tuple[float, float, float, float]


def _constraints(rows: Sequence[Sequence[float]]) -> List[List[float]]:
    return [list(row) for row in rows]


def _context(
    areas: Sequence[float],
    constraints: Optional[Sequence[Sequence[float]]] = None,
    targets: Optional[Sequence[Sequence[float]]] = None,
):
    if constraints is None:
        constraints = [[0, 0, 0, 0, 0] for _ in areas]
    parsed = _parse_inputs(
        len(areas),
        list(areas),
        [],
        [],
        [],
        _constraints(constraints),
        targets,
    )
    immutable = _build_immutable_geometry(parsed)
    dimensions = _plan_dimensions(parsed, immutable)
    return parsed, immutable, dimensions


def _evaluator_counts(
    positions: Sequence[Rect],
    areas: Sequence[float],
    constraints: Sequence[Sequence[float]],
    targets: Optional[Sequence[Sequence[float]]] = None,
) -> Tuple[int, int, int]:
    fixed_or_preplaced = {
        i
        for i, row in enumerate(constraints)
        if len(row) > 0 and row[0] != 0 or len(row) > 1 and row[1] != 0
    }
    constraints_tensor = torch.tensor(constraints, dtype=torch.float32)
    areas_tensor = torch.tensor(list(areas), dtype=torch.float32)
    target_list = None if targets is None else [tuple(row) for row in targets]
    return (
        check_overlap(list(positions)),
        check_area_tolerance(
            list(positions),
            areas_tensor,
            skip_indices=fixed_or_preplaced,
        ),
        check_dimension_hard_constraints(
            list(positions),
            target_list,
            constraints_tensor,
            len(areas),
        ),
    )


def _assert_preflight_matches_evaluator(
    positions: Sequence[Rect],
    areas: Sequence[float],
    constraints: Optional[Sequence[Sequence[float]]] = None,
    targets: Optional[Sequence[Sequence[float]]] = None,
) -> None:
    if constraints is None:
        constraints = [[0, 0, 0, 0, 0] for _ in areas]
    parsed, immutable, dimensions = _context(areas, constraints, targets)
    candidate = Candidate(list(positions), "manual", 1)
    report = _preflight(candidate, parsed, immutable, dimensions)
    expected_overlap, expected_area, expected_dimension = _evaluator_counts(
        positions,
        areas,
        _constraints(constraints),
        targets,
    )

    assert report.malformed_violations == 0, report
    assert report.overlap_violations == expected_overlap, (report, expected_overlap)
    assert report.area_violations == expected_area, (report, expected_area)
    assert report.dimension_violations == expected_dimension, (report, expected_dimension)
    assert report.hard_feasible == (
        expected_overlap == 0 and expected_area == 0 and expected_dimension == 0
    )


def test_edge_touching_and_overlap_tolerance_match_evaluator() -> None:
    areas = [1.0, 1.0]
    _assert_preflight_matches_evaluator(
        [(0.0, 0.0, 1.0, 1.0), (1.0, 0.0, 1.0, 1.0)],
        areas,
    )
    _assert_preflight_matches_evaluator(
        [(0.0, 0.0, 1.0, 1.0), (1.0 - OVERLAP_TOLERANCE / 2.0, 0.0, 1.0, 1.0)],
        areas,
    )
    _assert_preflight_matches_evaluator(
        [(0.0, 0.0, 1.0, 1.0), (1.0 - OVERLAP_TOLERANCE * 2.0, 0.0, 1.0, 1.0)],
        areas,
    )


def test_positive_overlap_is_hard_infeasible() -> None:
    _assert_preflight_matches_evaluator(
        [(0.0, 0.0, 1.0, 1.0), (0.5, 0.0, 1.0, 1.0)],
        [1.0, 1.0],
    )


def test_overlap_sweep_matches_evaluator_on_sparse_layout() -> None:
    positions: List[Rect] = [
        (0.0, 0.0, 100.0, 1.0),
        (10.0, 0.25, 1.0, 1.0),
        (20.0, 2.0, 1.0, 1.0),
        (100.0 - OVERLAP_TOLERANCE / 2.0, 3.0, 1.0, 1.0),
        (100.0 - OVERLAP_TOLERANCE * 2.0, 0.0, 1.0, 1.0),
    ]
    positions.extend(
        (200.0 + idx * 10.0, 0.0, 1.0, 1.0)
        for idx in range(40)
    )
    areas = [w * h for _, _, w, h in positions]

    expected_overlap = check_overlap(positions)
    assert expected_overlap == 2
    assert _count_overlap_violations(positions) == expected_overlap
    _assert_preflight_matches_evaluator(positions, areas)


def test_soft_area_tolerance_boundary_matches_evaluator() -> None:
    _assert_preflight_matches_evaluator(
        [(0.0, 0.0, 101.0, 1.0)],
        [100.0],
    )
    _assert_preflight_matches_evaluator(
        [(0.0, 0.0, 101.0 + AREA_TOLERANCE, 1.0)],
        [100.0],
    )


def test_fixed_and_preplaced_immutability_match_evaluator() -> None:
    areas = [100.0, 100.0, 4.0]
    constraints = [
        [1, 0, 0, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    targets = [
        [-1.0, -1.0, 2.0, 5.0],
        [10.0, 3.0, 4.0, 2.0],
        [-1.0, -1.0, -1.0, -1.0],
    ]
    exact = [
        (0.0, 0.0, 2.0, 5.0),
        (10.0, 3.0, 4.0, 2.0),
        (14.0, 0.0, 2.0, 2.0),
    ]
    _assert_preflight_matches_evaluator(exact, areas, constraints, targets)

    fixed_within_tolerance = list(exact)
    fixed_within_tolerance[0] = (0.0, 0.0, 2.0 + IMMUTABLE_TOLERANCE / 2.0, 5.0)
    _assert_preflight_matches_evaluator(
        fixed_within_tolerance,
        areas,
        constraints,
        targets,
    )

    fixed_violation = list(exact)
    fixed_violation[0] = (0.0, 0.0, 2.0 + IMMUTABLE_TOLERANCE * 2.0, 5.0)
    _assert_preflight_matches_evaluator(fixed_violation, areas, constraints, targets)

    preplaced_coordinate_violation = list(exact)
    preplaced_coordinate_violation[1] = (
        10.0 + IMMUTABLE_TOLERANCE * 2.0,
        3.0,
        4.0,
        2.0,
    )
    _assert_preflight_matches_evaluator(
        preplaced_coordinate_violation,
        areas,
        constraints,
        targets,
    )


def test_malformed_candidates_fail_preflight_without_throwing() -> None:
    parsed, immutable, dimensions = _context([1.0, 1.0])
    malformed_cases = [
        Candidate([(0.0, 0.0, 1.0, 1.0)], "short", 1),
        Candidate([None, (1.0, 0.0, 1.0, 1.0)], "none-rect", 2),
        Candidate([(math.nan, 0.0, 1.0, 1.0), (1.0, 0.0, 1.0, 1.0)], "nan", 3),
        Candidate([(0.0, 0.0, -1.0, 1.0), (1.0, 0.0, 1.0, 1.0)], "negative", 4),
    ]

    for candidate in malformed_cases:
        report = _preflight(candidate, parsed, immutable, dimensions)
        assert not report.hard_feasible
        assert report.malformed_violations > 0, (candidate.source, report)


def test_randomized_preflight_matches_evaluator_helpers() -> None:
    for seed in range(40):
        rng = random.Random(seed)
        block_count = rng.randint(2, 8)
        areas = [rng.uniform(1.0, 25.0) for _ in range(block_count)]
        constraints = [[0, 0, 0, 0, 0] for _ in range(block_count)]
        targets = [[-1.0, -1.0, -1.0, -1.0] for _ in range(block_count)]
        positions: List[Rect] = []
        x_cursor = 0.0

        for block_id, area in enumerate(areas):
            if seed % 5 == 0 and block_id == 0:
                width = rng.uniform(1.0, 6.0)
                height = rng.uniform(1.0, 6.0)
                constraints[block_id][0] = 1
                targets[block_id] = [-1.0, -1.0, width, height]
                positions.append((x_cursor, 0.0, width, height))
            elif seed % 7 == 0 and block_id == 1:
                width = rng.uniform(1.0, 6.0)
                height = rng.uniform(1.0, 6.0)
                constraints[block_id][1] = 1
                targets[block_id] = [x_cursor, 3.0, width, height]
                positions.append((x_cursor, 3.0, width, height))
            else:
                width = math.sqrt(area)
                height = width
                positions.append((x_cursor, 0.0, width, height))
            x_cursor += positions[-1][2] + 0.25

        if seed % 3 == 0:
            x, y, w, h = positions[-1]
            positions[-1] = (positions[0][0] + 0.5, y, w, h)
        if seed % 4 == 0:
            x, y, w, h = positions[-1]
            positions[-1] = (x, y, w * 1.02, h)
        if seed % 6 == 0 and constraints[0][0] != 0:
            x, y, w, h = positions[0]
            positions[0] = (x, y, w + IMMUTABLE_TOLERANCE * 3.0, h)

        _assert_preflight_matches_evaluator(positions, areas, constraints, targets)


def run_smoke() -> None:
    test_edge_touching_and_overlap_tolerance_match_evaluator()
    test_positive_overlap_is_hard_infeasible()
    test_overlap_sweep_matches_evaluator_on_sparse_layout()
    test_soft_area_tolerance_boundary_matches_evaluator()
    test_fixed_and_preplaced_immutability_match_evaluator()
    test_malformed_candidates_fail_preflight_without_throwing()
    test_randomized_preflight_matches_evaluator_helpers()


if __name__ == "__main__":
    run_smoke()
    print("optimizer-preflight smoke passed")
