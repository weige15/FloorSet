#!/usr/bin/env python3
"""Synthetic fixtures for bounded local search and repair.

Run from the repository root with:

    python -B iccad2026contest/optimizer_local_search_smoke.py
"""

from typing import Optional, Sequence

from my_optimizer import (
    Candidate,
    CandidateManager,
    MyOptimizer,
    SolverContext,
    _bbox_area,
    _build_fallback,
    _build_immutable_geometry,
    _compact_candidate,
    _local_search_frame_compaction_trials,
    _local_search_budget,
    _parse_inputs,
    _plan_dimensions,
    _plan_soft_units,
    _preflight,
    _run_local_search,
    _snap_boundary_candidate,
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


def _manager_with_fallback(context):
    manager = CandidateManager(context)
    fallback = _build_fallback(context.parsed, context.immutable, context.dimensions)
    manager.consider(fallback)
    assert fallback.hard_report is not None
    assert fallback.hard_report.hard_feasible
    return manager


def _local_candidates(context):
    manager = _manager_with_fallback(context)
    return manager, list(_run_local_search(context, manager))


def _assert_hard_feasible(context, candidate) -> None:
    report = _preflight(candidate, context.parsed, context.immutable, context.dimensions)
    assert report.hard_feasible, (candidate.source, report)
    assert report.overlap_violations == 0
    assert report.area_violations == 0
    assert report.dimension_violations == 0


def test_budget_policy_is_block_count_bounded() -> None:
    assert _local_search_budget(1).max_trials == 0
    assert _local_search_budget(21).max_trials == 20
    assert _local_search_budget(60).max_trials == 25
    assert _local_search_budget(80).ripup_trials == 4
    assert _local_search_budget(120).max_trials == 38
    assert _local_search_budget(120).ripup_trials == 6
    assert _local_search_budget(120).frame_compaction_trials == 2
    assert _local_search_budget(120).max_trials < 40


def test_swap_relocation_aspect_and_compaction_trials_are_feasible() -> None:
    context = _context([4.0, 9.0, 16.0, 25.0])
    manager, candidates = _local_candidates(context)
    sources = {candidate.source for candidate in candidates}

    assert len(candidates) <= _local_search_budget(context.parsed.n).max_trials
    assert any(source.startswith("local:swap:") for source in sources)
    assert any(source.startswith("local:relocate:") for source in sources)
    assert any(source.startswith("local:shelf_width:") for source in sources)
    assert any(source.startswith("local:aspect:") for source in sources)
    assert "local:compact" in sources

    for candidate in candidates:
        _assert_hard_feasible(context, candidate)
        manager.consider(candidate)
    assert manager.best_feasible_or_fallback().hard_report is not None
    assert manager.best_feasible_or_fallback().hard_report.hard_feasible


def test_shelf_width_trial_can_reduce_bbox_area() -> None:
    context = _context([100.0, 1.0, 1.0, 1.0])
    manager = _manager_with_fallback(context)
    fallback = manager.best_feasible_or_fallback()
    candidates = list(_run_local_search(context, manager))
    shelf_trials = [
        candidate for candidate in candidates
        if candidate.source.startswith("local:shelf_width:")
    ]

    assert shelf_trials
    for candidate in shelf_trials:
        _assert_hard_feasible(context, candidate)
    assert min(_bbox_area(candidate.positions) for candidate in shelf_trials) < _bbox_area(fallback.positions)


def test_compaction_uses_refreshed_best_candidate() -> None:
    class RefreshingManager:
        def __init__(self, initial, refreshed):
            self.initial = initial
            self.refreshed = refreshed
            self.calls = 0

        def best_feasible_or_fallback(self):
            self.calls += 1
            if self.calls == 1:
                return self.initial
            return self.refreshed

    context = _context([4.0, 4.0, 4.0])
    initial = Candidate(
        [(0.0, 0.0, 2.0, 2.0), (2.0, 0.0, 2.0, 2.0), (4.0, 0.0, 2.0, 2.0)],
        "initial",
        1,
    )
    refreshed = Candidate(
        [(4.0, 0.0, 2.0, 2.0), (2.0, 0.0, 2.0, 2.0), (0.0, 0.0, 2.0, 2.0)],
        "refreshed",
        2,
    )

    candidates = list(_run_local_search(context, RefreshingManager(initial, refreshed)))
    compacted = next(candidate for candidate in candidates if candidate.source == "local:compact")

    _assert_hard_feasible(context, compacted)
    assert compacted.positions[0] == (4.0, 0.0, 2.0, 2.0)
    assert compacted.positions[1] == (2.0, 0.0, 2.0, 2.0)
    assert compacted.positions[2] == (0.0, 0.0, 2.0, 2.0)


def test_immutable_geometry_is_repaired_after_local_moves() -> None:
    context = _context(
        [8.0, 10.0, 9.0, 16.0],
        constraints=[
            [0, 1, 0, 0, 0],
            [1, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ],
        targets=[
            [10.0, 3.0, 4.0, 2.0],
            [-1.0, -1.0, 2.0, 5.0],
            [-1.0, -1.0, -1.0, -1.0],
            [-1.0, -1.0, -1.0, -1.0],
        ],
    )
    _, candidates = _local_candidates(context)

    assert candidates
    for candidate in candidates:
        _assert_hard_feasible(context, candidate)
        assert candidate.positions[0] == (10.0, 3.0, 4.0, 2.0)
        assert candidate.positions[1][2:] == (2.0, 5.0)


def test_compatible_mib_sync_yields_hard_feasible_equal_shapes() -> None:
    context = _context(
        [4.0, 4.0, 9.0],
        constraints=[
            [0, 0, 1, 0, 0],
            [0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0],
        ],
    )
    _, candidates = _local_candidates(context)
    mib_sync = [
        candidate for candidate in candidates
        if candidate.source == "local:mib_sync:1"
    ]

    assert mib_sync
    _assert_hard_feasible(context, mib_sync[0])
    report = _preflight(mib_sync[0], context.parsed, context.immutable, context.dimensions)
    assert report.mib_violations == 0


def test_incompatible_mib_search_preserves_area_feasibility() -> None:
    context = _context(
        [4.0, 9.0, 16.0],
        constraints=[
            [0, 0, 1, 0, 0],
            [0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0],
        ],
    )
    _, candidates = _local_candidates(context)

    assert not any(candidate.source == "local:mib_sync:1" for candidate in candidates)
    for candidate in candidates:
        _assert_hard_feasible(context, candidate)


def test_boundary_snap_after_compaction_and_outside_overlap_repair() -> None:
    context = _context(
        [4.0, 4.0],
        constraints=[
            [0, 0, 0, 0, 9],
            [0, 0, 0, 0, 0],
        ],
    )
    start = Candidate(
        [(0.0, 0.0, 2.0, 2.0), (5.0, 5.0, 2.0, 2.0)],
        "manual",
        1,
    )
    compacted = _compact_candidate(context, start, "local:compact:test", 2)
    assert compacted is not None
    snapped = _snap_boundary_candidate(context, compacted, "local:boundary_snap:test", 3)
    assert snapped is not None
    _assert_hard_feasible(context, snapped)
    assert snapped.hard_report is not None
    assert snapped.hard_report.boundary_violations == 0

    reject_context = _context(
        [4.0, 4.0],
        constraints=[
            [0, 0, 0, 0, 2],
            [0, 0, 0, 0, 0],
        ],
    )
    outside_snap = _snap_boundary_candidate(
        reject_context,
        Candidate(
            [(0.0, 0.0, 2.0, 2.0), (5.0, 0.0, 2.0, 2.0)],
            "manual",
            1,
        ),
        "local:boundary_snap:overlap",
        2,
    )
    assert outside_snap is not None
    _assert_hard_feasible(reject_context, outside_snap)
    assert outside_snap.positions[0] == (7.0, 0.0, 2.0, 2.0)
    assert outside_snap.hard_report is not None
    assert outside_snap.hard_report.boundary_violations == 0


def test_candidate_manager_keeps_feasible_when_later_local_trial_is_bad() -> None:
    context = _context([1.0, 1.0])
    manager = _manager_with_fallback(context)
    fallback = manager.best_feasible_or_fallback()
    manager.consider(
        Candidate(
            [(0.0, 0.0, 1.0, 1.0), (0.5, 0.0, 1.0, 1.0)],
            "local:forced_overlap",
            999,
        )
    )

    assert manager.best_feasible_or_fallback() is fallback
    assert manager.best_feasible_or_fallback().hard_report is not None
    assert manager.best_feasible_or_fallback().hard_report.hard_feasible


def test_large_case_ripup_repack_trials_are_feasible_and_freeze_boundary_units() -> None:
    areas = [1.0 for _ in range(85)]
    constraints = [[0, 0, 0, 0, 0] for _ in areas]
    constraints[0][4] = 1
    context = _context(
        areas,
        constraints=constraints,
        b2b=[
            [10, 84, 100.0],
            [11, 83, 80.0],
            [12, 82, 60.0],
        ],
    )
    manager = _manager_with_fallback(context)
    fallback = manager.best_feasible_or_fallback()
    candidates = list(_run_local_search(context, manager))
    ripup_trials = [
        candidate for candidate in candidates
        if candidate.source.startswith("local:ripup_repack:")
    ]

    assert ripup_trials
    assert len(ripup_trials) <= _local_search_budget(context.parsed.n).ripup_trials
    for candidate in ripup_trials:
        _assert_hard_feasible(context, candidate)
        assert candidate.positions[0] == fallback.positions[0]


def test_large_boundary_frame_compaction_slides_rails_and_reduces_bbox() -> None:
    areas = [1.0 for _ in range(105)]
    constraints = [[0, 0, 0, 0, 0] for _ in areas]
    constraints[0][4] = 1
    constraints[1][4] = 2
    constraints[2][4] = 4
    constraints[3][4] = 8
    context = _context(
        areas,
        constraints=constraints,
        b2b=[
            [0, 4, 10.0],
            [1, 104, 10.0],
            [2, 40, 10.0],
            [3, 41, 10.0],
        ],
    )
    start_positions = [
        (0.0, 9.0, 1.0, 1.0),
        (39.0, 9.0, 1.0, 1.0),
        (18.0, 19.0, 1.0, 1.0),
        (18.0, 0.0, 1.0, 1.0),
    ]
    start_positions.extend(
        (float((idx - 4) * 2), 2.0, 1.0, 1.0)
        for idx in range(4, 105)
    )
    start = Candidate(start_positions, "manual:wide_frame", 1)
    start.hard_report = _preflight(
        start,
        context.parsed,
        context.immutable,
        context.dimensions,
    )
    assert start.hard_report.hard_feasible

    unit_set = _plan_soft_units(context)
    candidates = list(
        _local_search_frame_compaction_trials(
            context,
            unit_set,
            start,
            _local_search_budget(context.parsed.n),
            500,
        )
    )

    assert candidates
    assert len(candidates) <= _local_search_budget(context.parsed.n).frame_compaction_trials
    best = min(candidates, key=lambda candidate: _bbox_area(candidate.positions))
    _assert_hard_feasible(context, best)
    assert best.hard_report is not None
    assert best.hard_report.boundary_violations == 0
    assert _bbox_area(best.positions) < _bbox_area(start.positions) * 0.5


def test_synthetic_21_60_120_cases_stay_within_trial_budget() -> None:
    for block_count in (21, 60, 120):
        areas = [float((idx % 7) + 1) for idx in range(block_count)]
        context = _context(areas)
        manager, candidates = _local_candidates(context)
        assert len(candidates) <= _local_search_budget(block_count).max_trials
        for candidate in candidates:
            manager.consider(candidate)
        best = manager.best_feasible_or_fallback()
        _assert_hard_feasible(context, best)

        result = MyOptimizer().solve(
            block_count,
            areas,
            [],
            [],
            [],
            [[0, 0, 0, 0, 0] for _ in areas],
            None,
        )
        _assert_hard_feasible(
            context,
            Candidate(result, f"solve:{block_count}", 1),
        )


def run_smoke() -> None:
    test_budget_policy_is_block_count_bounded()
    test_swap_relocation_aspect_and_compaction_trials_are_feasible()
    test_shelf_width_trial_can_reduce_bbox_area()
    test_compaction_uses_refreshed_best_candidate()
    test_immutable_geometry_is_repaired_after_local_moves()
    test_compatible_mib_sync_yields_hard_feasible_equal_shapes()
    test_incompatible_mib_search_preserves_area_feasibility()
    test_boundary_snap_after_compaction_and_outside_overlap_repair()
    test_candidate_manager_keeps_feasible_when_later_local_trial_is_bad()
    test_large_case_ripup_repack_trials_are_feasible_and_freeze_boundary_units()
    test_large_boundary_frame_compaction_slides_rails_and_reduces_bbox()
    test_synthetic_21_60_120_cases_stay_within_trial_budget()


if __name__ == "__main__":
    run_smoke()
    print("optimizer-local-search smoke passed")
