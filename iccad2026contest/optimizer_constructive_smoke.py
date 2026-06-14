#!/usr/bin/env python3
"""Synthetic fixtures for constraint-aware constructive initialization.

Run from the repository root with:

    python -B iccad2026contest/optimizer_constructive_smoke.py
"""

from typing import Optional, Sequence

from my_optimizer import (
    Candidate,
    CandidateManager,
    CONSTRUCTIVE_SOURCE_BASE,
    FALLBACK_OBSTACLE_GAP,
    SolverContext,
    _bbox_area,
    _build_fallback,
    _build_immutable_geometry,
    _construct_candidates,
    _constructive_seed_orders,
    _parse_inputs,
    _plan_dimensions,
    _plan_soft_units,
    _preflight,
    _rects_share_edge,
)


def _parsed(
    areas: Sequence[float],
    constraints: Optional[Sequence[Sequence[float]]] = None,
    targets: Optional[Sequence[Sequence[float]]] = None,
    b2b: Optional[Sequence[Sequence[float]]] = None,
    p2b: Optional[Sequence[Sequence[float]]] = None,
    pins: Optional[Sequence[Sequence[float]]] = None,
):
    block_count = len(areas)
    if constraints is None:
        constraints = [[0, 0, 0, 0, 0] for _ in areas]
    return _parse_inputs(
        block_count,
        list(areas),
        b2b or [],
        p2b or [],
        pins or [],
        [list(row) for row in constraints],
        targets,
    )


def _context(areas, constraints=None, targets=None, b2b=None, p2b=None, pins=None):
    parsed = _parsed(areas, constraints, targets, b2b, p2b, pins)
    immutable = _build_immutable_geometry(parsed)
    dimensions = _plan_dimensions(parsed, immutable)
    return SolverContext(parsed, immutable, dimensions)


def _constructive_candidates(context):
    units = _plan_soft_units(context)
    return units, list(_construct_candidates(context, units))


def _assert_constructive_hard_feasible(context, candidates) -> None:
    assert candidates, "expected at least one constructive candidate"
    for candidate in candidates:
        assert len(candidate.positions) == context.parsed.n
        report = _preflight(candidate, context.parsed, context.immutable, context.dimensions)
        assert report.hard_feasible, (candidate.source, report)
        assert report.overlap_violations == 0
        assert report.area_violations == 0
        assert report.dimension_violations == 0


def test_seed_orders_are_named_and_bounded() -> None:
    context = _context(
        [4.0, 9.0, 16.0],
        constraints=[
            [0, 0, 0, 2, 0],
            [0, 0, 0, 2, 1],
            [0, 0, 0, 0, 0],
        ],
        b2b=[[0, 1, 7.0], [1, 2, 3.0]],
    )
    units = _plan_soft_units(context)
    seed_orders = _constructive_seed_orders(context, units)

    assert [seed[0] for seed in seed_orders] == [
        "original_id",
        "descending_area",
        "connectivity_weight",
        "connectivity_greedy",
        "boundary_first",
        "boundary_frame",
        "grouping_macro_priority",
        "boundary_skyline",
    ]
    assert len(seed_orders) == 8
    assert all(len(order) == len(units.units) for _, order, _ in seed_orders)


def test_empty_connectivity_still_builds_hard_feasible_candidates() -> None:
    context = _context([4.0, 9.0, 16.0, 25.0])
    _, candidates = _constructive_candidates(context)

    _assert_constructive_hard_feasible(context, candidates)
    assert candidates[0].source == "constructive:original_id"
    assert candidates[0].source_order == CONSTRUCTIVE_SOURCE_BASE
    assert candidates[0].positions == _build_fallback(
        context.parsed,
        context.immutable,
        context.dimensions,
    ).positions


def test_preplaced_obstacle_is_exact_and_movable_units_are_to_the_right() -> None:
    context = _context(
        [8.0, 9.0, 16.0],
        constraints=[
            [0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ],
        targets=[
            [10.0, 3.0, 4.0, 2.0],
            [-1.0, -1.0, -1.0, -1.0],
            [-1.0, -1.0, -1.0, -1.0],
        ],
    )
    _, candidates = _constructive_candidates(context)
    _assert_constructive_hard_feasible(context, candidates)

    safe_x = 10.0 + 4.0 + FALLBACK_OBSTACLE_GAP
    for candidate in candidates:
        assert candidate.positions[0] == (10.0, 3.0, 4.0, 2.0)
        assert candidate.positions[1][0] >= safe_x
        assert candidate.positions[2][0] >= safe_x


def test_boundary_first_seed_places_boundary_unit_first() -> None:
    context = _context(
        [4.0, 9.0, 16.0],
        constraints=[
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 9],
            [0, 0, 0, 0, 0],
        ],
    )
    _, candidates = _constructive_candidates(context)
    boundary = next(candidate for candidate in candidates if candidate.source == "constructive:boundary_first")

    assert boundary.positions[1] == (0.0, 0.0, 3.0, 3.0)
    assert _preflight(boundary, context.parsed, context.immutable, context.dimensions).hard_feasible


def test_connectivity_greedy_seed_chains_strong_b2b_edges() -> None:
    context = _context(
        [4.0, 4.0, 4.0, 4.0],
        b2b=[
            [2, 1, 10.0],
            [1, 0, 8.0],
            [0, 3, 1.0],
        ],
    )
    _, candidates = _constructive_candidates(context)
    greedy = next(
        candidate for candidate in candidates
        if candidate.source == "constructive:connectivity_greedy"
    )

    placement_order = sorted(
        range(context.parsed.n),
        key=lambda block_id: (
            round(greedy.positions[block_id][1], 6),
            round(greedy.positions[block_id][0], 6),
            block_id,
        ),
    )
    assert placement_order == [1, 2, 0, 3]
    assert greedy.hard_report is not None
    assert greedy.hard_report.hard_feasible


def test_boundary_frame_seed_places_right_top_units_late() -> None:
    context = _context(
        [4.0, 4.0],
        constraints=[
            [0, 0, 0, 0, 6],
            [0, 0, 0, 0, 0],
        ],
    )
    _, candidates = _constructive_candidates(context)

    boundary_first = next(
        candidate for candidate in candidates
        if candidate.source == "constructive:boundary_first"
    )
    boundary_frame = next(
        candidate for candidate in candidates
        if candidate.source == "constructive:boundary_frame"
    )

    assert boundary_first.hard_report is not None
    assert boundary_first.hard_report.boundary_violations == 1
    assert boundary_frame.positions[0] == (2.0, 0.0, 2.0, 2.0)
    assert boundary_frame.hard_report is not None
    assert boundary_frame.hard_report.hard_feasible
    assert boundary_frame.hard_report.boundary_violations == 0


def test_boundary_frame_seed_packs_non_overlapping_outer_rails() -> None:
    context = _context(
        [4.0, 4.0, 4.0, 4.0, 4.0, 4.0],
        constraints=[
            [0, 0, 0, 0, 1],
            [0, 0, 0, 0, 1],
            [0, 0, 0, 0, 2],
            [0, 0, 0, 0, 4],
            [0, 0, 0, 0, 8],
            [0, 0, 0, 0, 0],
        ],
    )
    _, candidates = _constructive_candidates(context)
    boundary_frame = next(
        candidate for candidate in candidates
        if candidate.source == "constructive:boundary_frame"
    )

    report = boundary_frame.hard_report
    assert report is not None
    assert report.hard_feasible
    assert report.overlap_violations == 0
    assert report.boundary_violations == 0

    x_min = min(x for x, _, _, _ in boundary_frame.positions)
    y_min = min(y for _, y, _, _ in boundary_frame.positions)
    x_max = max(x + w for x, _, w, _ in boundary_frame.positions)
    y_max = max(y + h for _, y, _, h in boundary_frame.positions)

    assert boundary_frame.positions[0][0] == x_min
    assert boundary_frame.positions[1][0] == x_min
    assert boundary_frame.positions[0][1] != boundary_frame.positions[1][1]
    assert boundary_frame.positions[2][0] + boundary_frame.positions[2][2] == x_max
    assert boundary_frame.positions[3][1] + boundary_frame.positions[3][3] == y_max
    assert boundary_frame.positions[4][1] == y_min


def test_boundary_skyline_seed_is_hard_feasible_and_can_reduce_bbox() -> None:
    context = _context(
        [4.0, 12.0, 8.0, 8.0, 4.0],
        constraints=[
            [0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0],
            [1, 0, 0, 0, 0],
            [1, 0, 0, 0, 0],
            [1, 0, 0, 0, 0],
        ],
        targets=[
            [-1.0, -1.0, -1.0, -1.0],
            [-1.0, -1.0, 6.0, 2.0],
            [-1.0, -1.0, 4.0, 2.0],
            [-1.0, -1.0, 2.0, 4.0],
            [-1.0, -1.0, 2.0, 2.0],
        ],
    )
    _, candidates = _constructive_candidates(context)
    boundary_frame = next(
        candidate for candidate in candidates
        if candidate.source == "constructive:boundary_frame"
    )
    boundary_skyline = next(
        candidate for candidate in candidates
        if candidate.source.startswith("constructive:boundary_skyline:")
    )

    assert boundary_skyline.hard_report is not None
    assert boundary_skyline.hard_report.hard_feasible
    assert boundary_skyline.hard_report.boundary_violations == 0
    assert _bbox_area(boundary_skyline.positions) < _bbox_area(boundary_frame.positions)


def test_grouping_macro_expands_as_edge_connected_unit() -> None:
    context = _context(
        [4.0, 9.0, 16.0],
        constraints=[
            [0, 0, 0, 5, 0],
            [0, 0, 0, 5, 0],
            [0, 0, 0, 0, 0],
        ],
    )
    _, candidates = _constructive_candidates(context)
    _assert_constructive_hard_feasible(context, candidates)

    for candidate in candidates:
        assert _rects_share_edge(candidate.positions[0], candidate.positions[1])
        assert candidate.hard_report is not None
        assert candidate.hard_report.grouping_violations == 0


def test_candidate_manager_retains_fallback_when_constructive_candidate_is_malformed() -> None:
    context = _context([4.0, 9.0])
    manager = CandidateManager(context)
    fallback = manager.consider(_build_fallback(context.parsed, context.immutable, context.dimensions))

    malformed = Candidate([(0.0, 0.0, 2.0, 2.0)], "constructive:malformed", 1)
    manager.consider(malformed)

    assert fallback.hard_report is not None
    assert fallback.hard_report.hard_feasible
    assert manager.best_feasible_or_fallback() is fallback


def run_smoke() -> None:
    test_seed_orders_are_named_and_bounded()
    test_empty_connectivity_still_builds_hard_feasible_candidates()
    test_preplaced_obstacle_is_exact_and_movable_units_are_to_the_right()
    test_boundary_first_seed_places_boundary_unit_first()
    test_connectivity_greedy_seed_chains_strong_b2b_edges()
    test_boundary_frame_seed_places_right_top_units_late()
    test_boundary_frame_seed_packs_non_overlapping_outer_rails()
    test_boundary_skyline_seed_is_hard_feasible_and_can_reduce_bbox()
    test_grouping_macro_expands_as_edge_connected_unit()
    test_candidate_manager_retains_fallback_when_constructive_candidate_is_malformed()


if __name__ == "__main__":
    run_smoke()
    print("optimizer-constructive smoke passed")
