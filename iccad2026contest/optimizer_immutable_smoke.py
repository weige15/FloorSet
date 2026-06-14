#!/usr/bin/env python3
"""Synthetic fixtures for immutable fixed/preplaced geometry extraction.

Run from the repository root with:

    python -B iccad2026contest/optimizer_immutable_smoke.py
"""

from my_optimizer import (
    _build_fallback,
    _build_immutable_geometry,
    _parse_inputs,
    _plan_dimensions,
    _preflight,
)


def _parsed(block_count, constraints, target_positions):
    return _parse_inputs(
        block_count,
        [4.0, 9.0, 16.0, 25.0, 36.0][:block_count],
        [],
        [],
        [],
        constraints,
        target_positions,
    )


def test_mixed_fixed_preplaced_and_free_records() -> None:
    parsed = _parsed(
        4,
        [
            [1, 0, 0, 0, 0],
            [0, 1, 0, 0, 0],
            [1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ],
        [
            [-1, -1, 2, 5],
            [10, 3, 4, 2],
            [1, 2, 6, 7],
            [-1, -1, -1, -1],
        ],
    )

    immutable = _build_immutable_geometry(parsed)

    assert immutable.fixed_dims == {0: (2.0, 5.0), 2: (6.0, 7.0)}
    assert immutable.preplaced_rects == {
        1: (10.0, 3.0, 4.0, 2.0),
        2: (1.0, 2.0, 6.0, 7.0),
    }
    assert immutable.obstacle_rects == [
        (1, (10.0, 3.0, 4.0, 2.0)),
        (2, (1.0, 2.0, 6.0, 7.0)),
    ]
    assert immutable.movable_ids == [0, 3]
    assert immutable.invalid_reasons == []


def test_fixed_only_and_preplaced_only_records() -> None:
    fixed_only = _build_immutable_geometry(_parsed(
        2,
        [[1, 0, 0, 0, 0], [1, 0, 0, 0, 0]],
        [[-1, -1, 2, 5], [-1, -1, 3, 7]],
    ))
    assert fixed_only.fixed_dims == {0: (2.0, 5.0), 1: (3.0, 7.0)}
    assert fixed_only.preplaced_rects == {}
    assert fixed_only.obstacle_rects == []
    assert fixed_only.movable_ids == [0, 1]
    assert fixed_only.invalid_reasons == []

    preplaced_only = _build_immutable_geometry(_parsed(
        2,
        [[0, 1, 0, 0, 0], [0, 1, 0, 0, 0]],
        [[0, 0, 2, 5], [3, 0, 3, 7]],
    ))
    assert preplaced_only.fixed_dims == {}
    assert preplaced_only.preplaced_rects == {
        0: (0.0, 0.0, 2.0, 5.0),
        1: (3.0, 0.0, 3.0, 7.0),
    }
    assert preplaced_only.obstacle_rects == [
        (0, (0.0, 0.0, 2.0, 5.0)),
        (1, (3.0, 0.0, 3.0, 7.0)),
    ]
    assert preplaced_only.movable_ids == []
    assert preplaced_only.invalid_reasons == []


def test_target_positions_none_without_immutable_constraints() -> None:
    parsed = _parsed(
        3,
        [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
        None,
    )

    immutable = _build_immutable_geometry(parsed)

    assert immutable.fixed_dims == {}
    assert immutable.preplaced_rects == {}
    assert immutable.obstacle_rects == []
    assert immutable.movable_ids == [0, 1, 2]
    assert immutable.invalid_reasons == []


def test_missing_and_invalid_immutable_targets_are_reported() -> None:
    missing = _build_immutable_geometry(_parsed(
        2,
        [[1, 0, 0, 0, 0], [0, 1, 0, 0, 0]],
        None,
    ))
    assert "missing fixed target for block 0" in missing.invalid_reasons
    assert "missing preplaced target for block 1" in missing.invalid_reasons
    assert missing.movable_ids == [0]

    invalid = _build_immutable_geometry(_parsed(
        2,
        [[1, 0, 0, 0, 0], [0, 1, 0, 0, 0]],
        [[-1, -1, 0, 4], [0, 0, 3, -1]],
    ))
    assert "invalid fixed target for block 0" in invalid.invalid_reasons
    assert "invalid preplaced target for block 1" in invalid.invalid_reasons


def test_fixed_preplaced_target_reports_both_invalid_roles() -> None:
    immutable = _build_immutable_geometry(_parsed(
        1,
        [[1, 1, 0, 0, 0]],
        [[0, 0, 0, 4]],
    ))

    assert immutable.fixed_dims == {}
    assert immutable.preplaced_rects == {}
    assert "invalid fixed target for block 0" in immutable.invalid_reasons
    assert "invalid preplaced target for block 0" in immutable.invalid_reasons


def test_overlapping_preplaced_obstacles_are_reported() -> None:
    parsed = _parsed(
        3,
        [[0, 1, 0, 0, 0], [0, 1, 0, 0, 0], [0, 0, 0, 0, 0]],
        [[0, 0, 3, 3], [2, 2, 3, 3], [-1, -1, -1, -1]],
    )

    immutable = _build_immutable_geometry(parsed)

    assert immutable.preplaced_rects == {
        0: (0.0, 0.0, 3.0, 3.0),
        1: (2.0, 2.0, 3.0, 3.0),
    }
    assert "overlapping preplaced targets 0 and 1" in immutable.invalid_reasons


def test_preplaced_overlap_diagnostics_are_block_id_sorted() -> None:
    parsed = _parsed(
        4,
        [
            [0, 1, 0, 0, 0],
            [0, 1, 0, 0, 0],
            [0, 1, 0, 0, 0],
            [0, 1, 0, 0, 0],
        ],
        [
            [10, 0, 5, 5],
            [0, 0, 5, 5],
            [3, 3, 5, 5],
            [12, 2, 2, 2],
        ],
    )

    immutable = _build_immutable_geometry(parsed)
    overlap_messages = [
        message for message in immutable.invalid_reasons
        if message.startswith("overlapping preplaced targets ")
    ]

    assert overlap_messages == [
        "overlapping preplaced targets 0 and 3",
        "overlapping preplaced targets 1 and 2",
    ]


def test_fallback_preserves_valid_immutable_geometry() -> None:
    parsed = _parsed(
        3,
        [[1, 0, 0, 0, 0], [0, 1, 0, 0, 0], [0, 0, 0, 0, 0]],
        [[-1, -1, 2, 5], [10, 3, 4, 2], [-1, -1, -1, -1]],
    )
    immutable = _build_immutable_geometry(parsed)
    dimensions = _plan_dimensions(parsed, immutable)
    fallback = _build_fallback(parsed, immutable, dimensions)
    report = _preflight(fallback, parsed, immutable, dimensions)

    assert fallback.positions[0][2:] == (2.0, 5.0)
    assert fallback.positions[1] == (10.0, 3.0, 4.0, 2.0)
    assert report.hard_feasible
    assert report.dimension_violations == 0


def test_immutable_tolerance_matches_evaluator_expectation() -> None:
    parsed = _parsed(
        2,
        [[1, 0, 0, 0, 0], [0, 1, 0, 0, 0]],
        [[-1, -1, 2, 5], [10, 3, 4, 2]],
    )
    immutable = _build_immutable_geometry(parsed)
    dimensions = _plan_dimensions(parsed, immutable)
    candidate = _build_fallback(parsed, immutable, dimensions)

    within_tolerance = list(candidate.positions)
    within_tolerance[0] = (within_tolerance[0][0], within_tolerance[0][1], 2.00005, 5.0)
    report = _preflight(candidate.__class__(within_tolerance, "within", 1), parsed, immutable, dimensions)
    assert report.dimension_violations == 0

    outside_tolerance = list(candidate.positions)
    outside_tolerance[1] = (10.0002, 3.0, 4.0, 2.0)
    report = _preflight(candidate.__class__(outside_tolerance, "outside", 2), parsed, immutable, dimensions)
    assert report.dimension_violations == 1


def run_smoke() -> None:
    test_mixed_fixed_preplaced_and_free_records()
    test_fixed_only_and_preplaced_only_records()
    test_target_positions_none_without_immutable_constraints()
    test_missing_and_invalid_immutable_targets_are_reported()
    test_fixed_preplaced_target_reports_both_invalid_roles()
    test_overlapping_preplaced_obstacles_are_reported()
    test_preplaced_overlap_diagnostics_are_block_id_sorted()
    test_fallback_preserves_valid_immutable_geometry()
    test_immutable_tolerance_matches_evaluator_expectation()


if __name__ == "__main__":
    run_smoke()
    print("optimizer-immutable smoke passed")
