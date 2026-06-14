#!/usr/bin/env python3
"""Synthetic fixtures for macro and soft-constraint planning.

Run from the repository root with:

    python -B iccad2026contest/optimizer_macro_smoke.py
"""

from typing import Optional, Sequence

from my_optimizer import (
    _build_immutable_geometry,
    _expand_unit,
    _expand_units,
    _parse_inputs,
    _plan_dimensions,
    _plan_soft_units,
    _preflight,
    Candidate,
    SolverContext,
)


def _parsed(
    areas: Sequence[float],
    constraints: Optional[Sequence[Sequence[float]]] = None,
    targets: Optional[Sequence[Sequence[float]]] = None,
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
        [list(row) for row in constraints],
        targets,
    )


def _unit_set(areas, constraints=None, targets=None):
    parsed = _parsed(areas, constraints, targets)
    immutable = _build_immutable_geometry(parsed)
    dimensions = _plan_dimensions(parsed, immutable)
    return parsed, immutable, dimensions, _plan_soft_units(SolverContext(parsed, immutable, dimensions))


def test_single_block_units_expand_with_planned_dimensions() -> None:
    parsed, immutable, dimensions, units = _unit_set([4.0, 9.0])

    assert [unit.unit_id for unit in units.units] == ["block:0", "block:1"]
    expanded = _expand_units(units)
    assert set(expanded) == {0, 1}
    assert expanded[0] == (0.0, 0.0, 2.0, 2.0)
    assert expanded[1] == (0.0, 0.0, 3.0, 3.0)

    for block_id, rect in expanded.items():
        assert rect[2:] == (dimensions.widths[block_id], dimensions.heights[block_id])

    assert _preflight(
        Candidate([expanded[0], (2.0, 0.0, 3.0, 3.0)], "manual", 1),
        parsed,
        immutable,
        dimensions,
    ).hard_feasible


def test_movable_group_macro_is_edge_connected_chain() -> None:
    _, _, _, units = _unit_set(
        [4.0, 9.0, 16.0],
        constraints=[
            [0, 0, 0, 7, 0],
            [0, 0, 0, 7, 0],
            [0, 0, 0, 0, 0],
        ],
    )

    macro = units.group_macros[7]
    assert macro.kind == "cluster_macro"
    assert macro.block_ids == (0, 1)
    assert macro.movable
    assert macro.bbox_width == 5.0
    assert macro.bbox_height == 3.0
    assert macro.local_rects == {
        0: (0.0, 0.0, 2.0, 2.0),
        1: (2.0, 0.0, 3.0, 3.0),
    }
    assert macro.soft_links["cluster_id"] == 7
    assert macro.soft_links["cluster_members"] == (0, 1)

    expanded = _expand_unit(macro, (10.0, 20.0))
    assert expanded[0] == (10.0, 20.0, 2.0, 2.0)
    assert expanded[1] == (12.0, 20.0, 3.0, 3.0)


def test_four_block_group_uses_compact_connected_macro() -> None:
    parsed, immutable, dimensions, units = _unit_set(
        [4.0, 4.0, 4.0, 4.0],
        constraints=[
            [0, 0, 0, 9, 0],
            [0, 0, 0, 9, 0],
            [0, 0, 0, 9, 0],
            [0, 0, 0, 9, 0],
        ],
    )

    macro = units.group_macros[9]
    assert macro.block_ids == (0, 1, 2, 3)
    assert macro.bbox_width == 4.0
    assert macro.bbox_height == 4.0
    assert macro.local_rects == {
        0: (0.0, 0.0, 2.0, 2.0),
        1: (2.0, 0.0, 2.0, 2.0),
        2: (0.0, 2.0, 2.0, 2.0),
        3: (2.0, 2.0, 2.0, 2.0),
    }

    expanded = _expand_unit(macro)
    report = _preflight(
        Candidate([expanded[i] for i in range(4)], "macro", 1),
        parsed,
        immutable,
        dimensions,
    )
    assert report.hard_feasible
    assert report.grouping_violations == 0


def test_group_with_preplaced_member_keeps_fixed_unit() -> None:
    _, _, _, units = _unit_set(
        [4.0, 9.0, 16.0],
        constraints=[
            [0, 1, 0, 3, 0],
            [0, 0, 0, 3, 0],
            [0, 0, 0, 3, 0],
        ],
        targets=[
            [30.0, 40.0, 2.0, 2.0],
            [-1.0, -1.0, -1.0, -1.0],
            [-1.0, -1.0, -1.0, -1.0],
        ],
    )

    assert "cluster 3 contains preplaced members; immutable blocks kept fixed" in units.diagnostics
    macro = units.group_macros[3]
    assert macro.block_ids == (1, 2)
    assert macro.soft_links["preplaced_cluster_members"] == (0,)

    preplaced = next(unit for unit in units.units if unit.unit_id == "block:0")
    assert preplaced.kind == "preplaced"
    assert not preplaced.movable
    assert preplaced.fixed_origin == (30.0, 40.0)
    assert _expand_unit(preplaced)[0] == (30.0, 40.0, 2.0, 2.0)
    assert preplaced.soft_links["cluster_groups"] == (3,)


def test_boundary_intents_cover_edges_and_corners() -> None:
    _, _, _, units = _unit_set(
        [4.0, 9.0, 16.0],
        constraints=[
            [0, 0, 0, 5, 5],
            [0, 0, 0, 5, 2],
            [0, 0, 0, 0, 8],
        ],
    )

    macro = units.group_macros[5]
    assert macro.boundary_intent == 7
    assert macro.soft_links["boundary_masks"] == {0: 5, 1: 2}
    assert units.boundary_intents["cluster:5"] == 7
    assert units.boundary_intents["block:2"] == 8


def test_mib_metadata_and_unit_links_preserve_equal_and_unequal_groups() -> None:
    _, _, dimensions, units = _unit_set(
        [4.0, 4.0, 9.0, 16.0],
        constraints=[
            [0, 0, 1, 0, 0],
            [0, 0, 1, 0, 0],
            [0, 0, 2, 0, 0],
            [0, 0, 2, 0, 0],
        ],
    )

    assert dimensions.mib_notes == {
        1: "synchronized",
        2: "incompatible-hard-area-preserved",
    }
    assert units.mib_metadata[1]["block_ids"] == (0, 1)
    assert units.mib_metadata[1]["same_shape"]
    assert units.mib_metadata[2]["block_ids"] == (2, 3)
    assert not units.mib_metadata[2]["same_shape"]

    block0 = next(unit for unit in units.units if unit.unit_id == "block:0")
    block2 = next(unit for unit in units.units if unit.unit_id == "block:2")
    assert block0.soft_links["mib_groups"] == (1,)
    assert block2.soft_links["mib_groups"] == (2,)


def test_every_unit_maps_each_block_once() -> None:
    _, _, _, units = _unit_set(
        [4.0, 9.0, 16.0, 25.0],
        constraints=[
            [0, 0, 1, 1, 1],
            [0, 0, 1, 1, 0],
            [0, 0, 0, 0, 10],
            [0, 0, 0, 0, 0],
        ],
    )
    expanded = _expand_units(units)

    assert set(expanded) == {0, 1, 2, 3}
    assert units.block_to_unit == {
        0: "cluster:1",
        1: "cluster:1",
        2: "block:2",
        3: "block:3",
    }
    for unit in units.units:
        assert set(_expand_unit(unit)) == set(unit.block_ids)


def run_smoke() -> None:
    test_single_block_units_expand_with_planned_dimensions()
    test_movable_group_macro_is_edge_connected_chain()
    test_four_block_group_uses_compact_connected_macro()
    test_group_with_preplaced_member_keeps_fixed_unit()
    test_boundary_intents_cover_edges_and_corners()
    test_mib_metadata_and_unit_links_preserve_equal_and_unequal_groups()
    test_every_unit_maps_each_block_once()


if __name__ == "__main__":
    run_smoke()
    print("optimizer-macro smoke passed")
