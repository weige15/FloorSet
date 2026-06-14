#!/usr/bin/env python3
"""Synthetic fixtures for immutable geometry and dimension planning.

Run from the repository root with:

    python -B iccad2026contest/optimizer_dimension_smoke.py
"""

from typing import Any, List, Optional, Sequence

from my_optimizer import (
    AREA_TOLERANCE,
    Candidate,
    _build_fallback,
    _build_immutable_geometry,
    _parse_inputs,
    _plan_dimensions,
    _preflight,
)


def _assert_close(actual: float, expected: float, tol: float = 1e-9) -> None:
    assert abs(actual - expected) <= tol, f"expected {expected}, got {actual}"


def _constraints(rows: Sequence[Sequence[float]]) -> List[List[float]]:
    return [list(row) for row in rows]


def _parsed(
    areas: Sequence[float],
    constraints: Optional[Sequence[Sequence[float]]] = None,
    targets: Any = None,
):
    block_count = len(areas)
    if constraints is None:
        constraints = [[0, 0, 0, 0, 0] for _ in areas]
    return _parse_inputs(
        block_count,
        list(areas),
        [],
        [],
        [],
        _constraints(constraints),
        targets,
    )


def test_ordinary_soft_square_dimensions() -> None:
    parsed = _parsed([4.0, 9.0])
    immutable = _build_immutable_geometry(parsed)
    dimensions = _plan_dimensions(parsed, immutable)

    assert dimensions.sources == ["ordinary_soft", "ordinary_soft"]
    assert dimensions.invalid_reasons == []
    _assert_close(dimensions.widths[0], 2.0)
    _assert_close(dimensions.heights[0], 2.0)
    _assert_close(dimensions.widths[1], 3.0)
    _assert_close(dimensions.heights[1], 3.0)

    fallback = _build_fallback(parsed, immutable, dimensions)
    report = _preflight(fallback, parsed, immutable, dimensions)
    assert report.hard_feasible
    assert report.area_violations == 0


def test_immutable_dimensions_are_preserved() -> None:
    parsed = _parsed(
        [10.0, 8.0, 9.0],
        constraints=[
            [1, 0, 0, 0, 0],
            [0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ],
        targets=[
            [-1, -1, 2.0, 5.0],
            [10.0, 3.0, 4.0, 2.0],
            [-1, -1, -1, -1],
        ],
    )
    immutable = _build_immutable_geometry(parsed)
    dimensions = _plan_dimensions(parsed, immutable)

    assert immutable.fixed_dims == {0: (2.0, 5.0)}
    assert immutable.preplaced_rects == {1: (10.0, 3.0, 4.0, 2.0)}
    assert dimensions.sources == ["immutable_fixed", "immutable_preplaced", "ordinary_soft"]
    assert dimensions.widths[:3] == [2.0, 4.0, 3.0]
    assert dimensions.heights[:3] == [5.0, 2.0, 3.0]

    fallback = _build_fallback(parsed, immutable, dimensions)
    report = _preflight(fallback, parsed, immutable, dimensions)
    assert report.hard_feasible
    assert fallback.positions[1] == (10.0, 3.0, 4.0, 2.0)


def test_equal_area_mib_soft_blocks_synchronize() -> None:
    parsed = _parsed(
        [4.0, 4.0],
        constraints=[
            [0, 0, 1, 0, 0],
            [0, 0, 1, 0, 0],
        ],
    )
    immutable = _build_immutable_geometry(parsed)
    dimensions = _plan_dimensions(parsed, immutable)

    assert dimensions.mib_notes == {1: "synchronized"}
    assert dimensions.sources == ["mib_synchronized_soft", "mib_synchronized_soft"]
    assert (dimensions.widths[0], dimensions.heights[0]) == (
        dimensions.widths[1],
        dimensions.heights[1],
    )
    _assert_close(dimensions.widths[0], 2.0)
    _assert_close(dimensions.heights[0], 2.0)


def test_near_equal_area_mib_uses_centered_common_area() -> None:
    parsed = _parsed(
        [100.0, 101.0],
        constraints=[
            [0, 0, 3, 0, 0],
            [0, 0, 3, 0, 0],
        ],
    )
    immutable = _build_immutable_geometry(parsed)
    dimensions = _plan_dimensions(parsed, immutable)

    lower_area = max(area * (1.0 - AREA_TOLERANCE) for area in parsed.areas)
    upper_area = min(area * (1.0 + AREA_TOLERANCE) for area in parsed.areas)
    expected_area = (lower_area + upper_area) / 2.0
    actual_area = dimensions.widths[0] * dimensions.heights[0]

    assert dimensions.mib_notes == {3: "synchronized"}
    assert dimensions.sources == ["mib_synchronized_soft", "mib_synchronized_soft"]
    assert (dimensions.widths[0], dimensions.heights[0]) == (
        dimensions.widths[1],
        dimensions.heights[1],
    )
    _assert_close(actual_area, expected_area)
    assert abs(actual_area - parsed.areas[0]) / parsed.areas[0] < AREA_TOLERANCE
    assert abs(actual_area - parsed.areas[1]) / parsed.areas[1] < AREA_TOLERANCE


def test_immutable_mib_shape_is_used_when_area_compatible() -> None:
    parsed = _parsed(
        [4.0, 4.0],
        constraints=[
            [1, 0, 1, 0, 0],
            [0, 0, 1, 0, 0],
        ],
        targets=[
            [-1, -1, 1.0, 4.0],
            [-1, -1, -1, -1],
        ],
    )
    immutable = _build_immutable_geometry(parsed)
    dimensions = _plan_dimensions(parsed, immutable)

    assert dimensions.mib_notes == {1: "synchronized"}
    assert dimensions.sources == ["immutable_fixed", "mib_synchronized_soft"]
    assert dimensions.widths == [1.0, 1.0]
    assert dimensions.heights == [4.0, 4.0]

    fallback = _build_fallback(parsed, immutable, dimensions)
    report = _preflight(fallback, parsed, immutable, dimensions)
    assert report.hard_feasible
    assert report.mib_violations == 0


def test_incompatible_mib_preserves_hard_area() -> None:
    parsed = _parsed(
        [4.0, 9.0],
        constraints=[
            [0, 0, 2, 0, 0],
            [0, 0, 2, 0, 0],
        ],
    )
    immutable = _build_immutable_geometry(parsed)
    dimensions = _plan_dimensions(parsed, immutable)

    assert dimensions.mib_notes == {2: "incompatible-hard-area-preserved"}
    assert dimensions.sources == ["ordinary_soft", "ordinary_soft"]
    assert dimensions.widths == [2.0, 3.0]
    assert dimensions.heights == [2.0, 3.0]

    fallback = _build_fallback(parsed, immutable, dimensions)
    report = _preflight(fallback, parsed, immutable, dimensions)
    assert report.hard_feasible
    assert report.area_violations == 0
    assert report.mib_violations == 1


def test_nonpositive_soft_area_is_invalid_but_repaired_for_shape() -> None:
    parsed = _parsed([0.0, -5.0])
    immutable = _build_immutable_geometry(parsed)
    dimensions = _plan_dimensions(parsed, immutable)

    assert parsed.invalid_area_ids == {0, 1}
    assert dimensions.sources == ["fallback_repair", "fallback_repair"]
    assert dimensions.widths == [1.0, 1.0]
    assert dimensions.heights == [1.0, 1.0]
    assert "invalid soft area for block 0" in dimensions.invalid_reasons
    assert "invalid soft area for block 1" in dimensions.invalid_reasons

    fallback = _build_fallback(parsed, immutable, dimensions)
    report = _preflight(fallback, parsed, immutable, dimensions)
    assert not report.hard_feasible
    assert report.dimension_violations == 2


def test_area_tolerance_boundary() -> None:
    parsed = _parsed([100.0])
    immutable = _build_immutable_geometry(parsed)
    dimensions = _plan_dimensions(parsed, immutable)

    accepted = Candidate([(0.0, 0.0, 10.1, 10.0)], "manual", 1)
    accepted_report = _preflight(accepted, parsed, immutable, dimensions)
    assert accepted_report.hard_feasible
    assert accepted_report.area_violations == 0

    rejected = Candidate([(0.0, 0.0, 10.1 + AREA_TOLERANCE, 10.0)], "manual", 2)
    rejected_report = _preflight(rejected, parsed, immutable, dimensions)
    assert not rejected_report.hard_feasible
    assert rejected_report.area_violations == 1


def run_smoke() -> None:
    test_ordinary_soft_square_dimensions()
    test_immutable_dimensions_are_preserved()
    test_equal_area_mib_soft_blocks_synchronize()
    test_near_equal_area_mib_uses_centered_common_area()
    test_immutable_mib_shape_is_used_when_area_compatible()
    test_incompatible_mib_preserves_hard_area()
    test_nonpositive_soft_area_is_invalid_but_repaired_for_shape()
    test_area_tolerance_boundary()


if __name__ == "__main__":
    run_smoke()
    print("optimizer-dimension smoke passed")
