#!/usr/bin/env python3
"""
Fallback-first optimizer for the ICCAD 2026 FloorSet Challenge.

The implementation prioritizes the evaluator-facing contract and a deterministic
hard-feasible fallback, then runs bounded constructive and local-search quality
layers without changing the public solve() interface.
"""

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple


AREA_TOLERANCE = 0.01
OVERLAP_TOLERANCE = 1e-6
IMMUTABLE_TOLERANCE = 1e-4
HARD_BARRIER = 1e30
FALLBACK_OBSTACLE_GAP = 1.0
CONSTRUCTIVE_SHELF_ASPECT = 1.5
BOUNDARY_SKYLINE_ASPECTS = (0.9, 1.15, 1.45, 1.8)
CONSTRUCTIVE_SOURCE_BASE = 100
LOCAL_SEARCH_SOURCE_BASE = 200
LOCAL_SEARCH_ASPECT_RATIO = 1.25
PROXY_HPWL_WEIGHT = 1.0
PROXY_BBOX_WEIGHT = 0.01
PROXY_SOFT_WEIGHT = 1000.0
PROXY_SOFT_EXPONENT = 2.0

Rect = Tuple[float, float, float, float]


@dataclass
class ParsedInput:
    n: int
    areas: List[float]
    invalid_area_ids: set
    fixed_ids: set
    preplaced_ids: set
    fixed_or_preplaced_ids: set
    mib_groups: Dict[int, List[int]]
    cluster_groups: Dict[int, List[int]]
    boundary_masks: Dict[int, int]
    b2b_edges: List[Tuple[int, int, float]]
    p2b_edges: List[Tuple[int, int, float]]
    pins: List[Tuple[float, float]]
    target_positions: Optional[List[Rect]]
    diagnostics: List[str] = field(default_factory=list)


@dataclass
class ImmutableGeometry:
    fixed_dims: Dict[int, Tuple[float, float]]
    preplaced_rects: Dict[int, Rect]
    obstacle_rects: List[Tuple[int, Rect]]
    movable_ids: List[int]
    invalid_reasons: List[str]


@dataclass
class DimensionPlan:
    widths: List[float]
    heights: List[float]
    sources: List[str]
    invalid_reasons: List[str]
    mib_notes: Dict[int, str]


@dataclass
class PlacementUnit:
    unit_id: str
    kind: str
    block_ids: Tuple[int, ...]
    local_rects: Dict[int, Rect]
    bbox_width: float
    bbox_height: float
    movable: bool
    boundary_intent: int
    soft_links: Dict[str, Any] = field(default_factory=dict)
    fixed_origin: Optional[Tuple[float, float]] = None


@dataclass
class PlacementUnitSet:
    units: List[PlacementUnit]
    group_macros: Dict[int, PlacementUnit]
    mib_metadata: Dict[int, Dict[str, Any]]
    boundary_intents: Dict[str, int]
    block_to_unit: Dict[int, str]
    diagnostics: List[str] = field(default_factory=list)


@dataclass
class PreflightReport:
    hard_feasible: bool
    malformed_violations: int = 0
    overlap_violations: int = 0
    area_violations: int = 0
    dimension_violations: int = 0
    boundary_violations: int = 0
    grouping_violations: int = 0
    mib_violations: int = 0
    total_soft_violations: int = 0
    max_possible_violations: int = 0
    violations_relative: float = 0.0
    messages: List[str] = field(default_factory=list)


@dataclass
class ProxyScore:
    score: float
    hpwl_total: float
    bbox_area: float
    soft_relative: float
    hard_barrier: float
    hpwl_b2b: float = 0.0
    hpwl_p2b: float = 0.0
    boundary_violations: int = 0
    grouping_violations: int = 0
    mib_violations: int = 0
    total_soft_violations: int = 0
    max_possible_violations: int = 0


@dataclass
class Candidate:
    positions: List[Rect]
    source: str
    source_order: int
    hard_report: Optional[PreflightReport] = None
    proxy_score: Optional[ProxyScore] = None


@dataclass
class SolverContext:
    parsed: ParsedInput
    immutable: ImmutableGeometry
    dimensions: DimensionPlan


@dataclass
class LocalSearchBudget:
    max_trials: int
    swap_trials: int
    relocation_trials: int
    shelf_width_trials: int
    aspect_trials: int
    mib_sync_trials: int
    boundary_trials: int
    compaction_trials: int


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if hasattr(value, "item"):
            value = value.item()
        result = float(value)
    except Exception:
        return default
    return result if math.isfinite(result) else default


def _as_int(value: Any, default: int = 0) -> int:
    return int(_as_float(value, float(default)))


def _length(value: Any) -> int:
    if value is None:
        return 0
    try:
        return len(value)
    except Exception:
        return 0


def _row(value: Any, idx: int) -> Any:
    try:
        return value[idx]
    except Exception:
        return None


def _cell(value: Any, row: int, col: int, default: float = 0.0) -> float:
    raw_value = _raw_cell(value, row, col)
    if raw_value is None:
        return default
    return _as_float(raw_value, default)


def _raw_cell(value: Any, row: int, col: int) -> Any:
    record = _row(value, row)
    if record is None:
        return None
    try:
        return record[col]
    except Exception:
        return None


def _column_count(value: Any) -> int:
    if value is None:
        return 0
    shape = getattr(value, "shape", None)
    if shape is not None and len(shape) >= 2:
        return int(shape[1])
    first = _row(value, 0)
    return _length(first)


def _rects_overlap(a: Rect, b: Rect, tol: float = OVERLAP_TOLERANCE) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    overlap_x = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    overlap_y = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    return overlap_x > tol and overlap_y > tol


def _count_overlap_violations(
    positions: Sequence[Rect],
    tol: float = OVERLAP_TOLERANCE,
) -> int:
    if not positions:
        return 0

    sweep_rects = []
    for rect in positions:
        x, y, w, h = rect
        if not all(math.isfinite(value) for value in rect) or w <= 0.0 or h <= 0.0:
            return _count_overlap_violations_pairwise(positions, tol)
        sweep_rects.append((x, x + w, y, y + h))

    sweep_rects.sort(key=lambda item: (item[0], item[2], item[1], item[3]))
    violations = 0
    for i, (_, x_max, y_min, y_max) in enumerate(sweep_rects):
        for x2_min, x2_max, y2_min, y2_max in sweep_rects[i + 1:]:
            if x2_min >= x_max - tol:
                break
            overlap_x = min(x_max, x2_max) - x2_min
            overlap_y = min(y_max, y2_max) - max(y_min, y2_min)
            if overlap_x > tol and overlap_y > tol:
                violations += 1
    return violations


def _count_overlap_violations_pairwise(
    positions: Sequence[Rect],
    tol: float = OVERLAP_TOLERANCE,
) -> int:
    violations = 0
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            if _rects_overlap(positions[i], positions[j], tol):
                violations += 1
    return violations


def _bbox_area(positions: Sequence[Rect]) -> float:
    if not positions:
        return 0.0
    x_min = min(x for x, _, _, _ in positions)
    y_min = min(y for _, y, _, _ in positions)
    x_max = max(x + w for x, _, w, _ in positions)
    y_max = max(y + h for _, y, _, h in positions)
    return max(0.0, x_max - x_min) * max(0.0, y_max - y_min)


def _center(rect: Rect) -> Tuple[float, float]:
    x, y, w, h = rect
    return x + w / 2.0, y + h / 2.0


def _finite_metric(value: float, fallback: float = HARD_BARRIER / 2.0) -> float:
    return value if math.isfinite(value) else fallback


def _score_positions(positions: Sequence[Rect], expected_count: int) -> Optional[List[Rect]]:
    if len(positions) != expected_count:
        return None

    clean_positions: List[Rect] = []
    for rect in positions:
        if _length(rect) != 4:
            return None
        values = tuple(_as_float(value, float("nan")) for value in rect)
        x, y, w, h = values
        if not all(math.isfinite(v) for v in values) or w <= 0.0 or h <= 0.0:
            return None
        clean_positions.append((x, y, w, h))
    return clean_positions


def _hpwl_b2b(positions: Sequence[Rect], edges: Sequence[Tuple[int, int, float]]) -> float:
    total = 0.0
    for i, j, weight in edges:
        if not (0 <= i < len(positions) and 0 <= j < len(positions)):
            continue
        x1, y1 = _center(positions[i])
        x2, y2 = _center(positions[j])
        total += weight * (abs(x2 - x1) + abs(y2 - y1))
    return _finite_metric(total)


def _hpwl_p2b(
    positions: Sequence[Rect],
    edges: Sequence[Tuple[int, int, float]],
    pins: Sequence[Tuple[float, float]],
) -> float:
    total = 0.0
    for pin_idx, block_idx, weight in edges:
        if not (0 <= block_idx < len(positions) and 0 <= pin_idx < len(pins)):
            continue
        px, py = pins[pin_idx]
        bx, by = _center(positions[block_idx])
        total += weight * (abs(px - bx) + abs(py - by))
    return _finite_metric(total)


def _parse_inputs(
    block_count: int,
    area_targets: Any,
    b2b_connectivity: Any,
    p2b_connectivity: Any,
    pins_pos: Any,
    constraints: Any,
    target_positions: Any,
) -> ParsedInput:
    n = max(0, int(block_count))
    diagnostics: List[str] = []

    areas = []
    invalid_area_ids = set()
    for i in range(n):
        area = _as_float(_row(area_targets, i), float("nan"))
        if not math.isfinite(area) or area <= 0.0:
            diagnostics.append(f"invalid area for block {i}")
            invalid_area_ids.add(i)
            area = 1.0
        areas.append(area)

    ncols = _column_count(constraints)
    fixed_ids = set()
    preplaced_ids = set()
    mib_groups: Dict[int, List[int]] = {}
    cluster_groups: Dict[int, List[int]] = {}
    boundary_masks: Dict[int, int] = {}

    for i in range(n):
        if ncols > 0 and _cell(constraints, i, 0) != 0:
            fixed_ids.add(i)
        if ncols > 1 and _cell(constraints, i, 1) != 0:
            preplaced_ids.add(i)
        if ncols > 2:
            group_id = _as_int(_cell(constraints, i, 2))
            if group_id > 0:
                mib_groups.setdefault(group_id, []).append(i)
        if ncols > 3:
            group_id = _as_int(_cell(constraints, i, 3))
            if group_id > 0:
                cluster_groups.setdefault(group_id, []).append(i)
        if ncols > 4:
            mask = _as_int(_cell(constraints, i, 4))
            if mask != 0:
                boundary_masks[i] = mask

    pins: List[Tuple[float, float]] = []
    invalid_pin_ids = set()
    for pin_idx in range(_length(pins_pos)):
        px = _as_float(_raw_cell(pins_pos, pin_idx, 0), float("nan"))
        py = _as_float(_raw_cell(pins_pos, pin_idx, 1), float("nan"))
        if px == -1.0:
            pins.append((0.0, 0.0))
            invalid_pin_ids.add(pin_idx)
            diagnostics.append(f"inactive pin position {pin_idx}")
        elif math.isfinite(px) and math.isfinite(py):
            pins.append((px, py))
        else:
            pins.append((0.0, 0.0))
            invalid_pin_ids.add(pin_idx)
            diagnostics.append(f"invalid pin position {pin_idx}")

    b2b_edges: List[Tuple[int, int, float]] = []
    for idx in range(_length(b2b_connectivity)):
        if _cell(b2b_connectivity, idx, 0, -1.0) == -1:
            continue
        i = _as_int(_cell(b2b_connectivity, idx, 0, -1.0), -1)
        j = _as_int(_cell(b2b_connectivity, idx, 1, -1.0), -1)
        weight = _as_float(_raw_cell(b2b_connectivity, idx, 2), float("nan"))
        if 0 <= i < n and 0 <= j < n and math.isfinite(weight):
            b2b_edges.append((i, j, weight))
        else:
            diagnostics.append(f"ignored invalid B2B edge {idx}")

    p2b_edges: List[Tuple[int, int, float]] = []
    for idx in range(_length(p2b_connectivity)):
        if _cell(p2b_connectivity, idx, 0, -1.0) == -1:
            continue
        pin_idx = _as_int(_cell(p2b_connectivity, idx, 0, -1.0), -1)
        block_idx = _as_int(_cell(p2b_connectivity, idx, 1, -1.0), -1)
        weight = _as_float(_raw_cell(p2b_connectivity, idx, 2), float("nan"))
        if (0 <= pin_idx < len(pins)
                and pin_idx not in invalid_pin_ids
                and 0 <= block_idx < n
                and math.isfinite(weight)):
            p2b_edges.append((pin_idx, block_idx, weight))
        else:
            diagnostics.append(f"ignored invalid P2B edge {idx}")

    target_list: Optional[List[Rect]] = None
    if target_positions is not None:
        target_list = []
        for i in range(n):
            target_list.append((
                _cell(target_positions, i, 0, -1.0),
                _cell(target_positions, i, 1, -1.0),
                _cell(target_positions, i, 2, -1.0),
                _cell(target_positions, i, 3, -1.0),
            ))

    return ParsedInput(
        n=n,
        areas=areas,
        invalid_area_ids=invalid_area_ids,
        fixed_ids=fixed_ids,
        preplaced_ids=preplaced_ids,
        fixed_or_preplaced_ids=fixed_ids | preplaced_ids,
        mib_groups=mib_groups,
        cluster_groups=cluster_groups,
        boundary_masks=boundary_masks,
        b2b_edges=b2b_edges,
        p2b_edges=p2b_edges,
        pins=pins,
        target_positions=target_list,
        diagnostics=diagnostics,
    )


def _target_has_valid_dimensions(target: Rect) -> bool:
    _, _, width, height = target
    return (
        math.isfinite(width)
        and math.isfinite(height)
        and width > 0.0
        and height > 0.0
    )


def _target_has_valid_rect(target: Rect) -> bool:
    x, y, width, height = target
    return (
        math.isfinite(x)
        and math.isfinite(y)
        and math.isfinite(width)
        and math.isfinite(height)
        and width > 0.0
        and height > 0.0
    )


def _preplaced_overlap_messages(obstacles: Sequence[Tuple[int, Rect]]) -> List[str]:
    if len(obstacles) < 2:
        return []

    overlap_pairs = set()
    active: List[Tuple[int, Rect]] = []
    for block_id, rect in sorted(obstacles, key=lambda item: (item[1][0], item[0])):
        x, _, _, _ = rect
        active = [
            (other_id, other)
            for other_id, other in active
            if other[0] + other[2] > x + OVERLAP_TOLERANCE
        ]
        for other_id, other in active:
            if _rects_overlap(rect, other):
                first_id, second_id = sorted((block_id, other_id))
                overlap_pairs.add((first_id, second_id))
        active.append((block_id, rect))

    return [
        f"overlapping preplaced targets {first_id} and {second_id}"
        for first_id, second_id in sorted(overlap_pairs)
    ]


def _build_immutable_geometry(parsed: ParsedInput) -> ImmutableGeometry:
    fixed_dims: Dict[int, Tuple[float, float]] = {}
    preplaced_rects: Dict[int, Rect] = {}
    invalid_reasons: List[str] = []

    for block_id in sorted(parsed.fixed_ids | parsed.preplaced_ids):
        is_fixed = block_id in parsed.fixed_ids
        is_preplaced = block_id in parsed.preplaced_ids
        if parsed.target_positions is None or block_id >= len(parsed.target_positions):
            if is_fixed:
                invalid_reasons.append(f"missing fixed target for block {block_id}")
            if is_preplaced:
                invalid_reasons.append(f"missing preplaced target for block {block_id}")
            continue

        target = parsed.target_positions[block_id]
        if is_fixed:
            if _target_has_valid_dimensions(target):
                fixed_dims[block_id] = (target[2], target[3])
            else:
                invalid_reasons.append(f"invalid fixed target for block {block_id}")
        if is_preplaced:
            if _target_has_valid_rect(target):
                preplaced_rects[block_id] = target
            else:
                invalid_reasons.append(f"invalid preplaced target for block {block_id}")

    obstacles = sorted(preplaced_rects.items())
    invalid_reasons.extend(_preplaced_overlap_messages(obstacles))

    movable_ids = [i for i in range(parsed.n) if i not in parsed.preplaced_ids]
    return ImmutableGeometry(
        fixed_dims=fixed_dims,
        preplaced_rects=preplaced_rects,
        obstacle_rects=obstacles,
        movable_ids=movable_ids,
        invalid_reasons=invalid_reasons,
    )


def _same_shape(first: Tuple[float, float], second: Tuple[float, float]) -> bool:
    return (
        abs(first[0] - second[0]) <= IMMUTABLE_TOLERANCE
        and abs(first[1] - second[1]) <= IMMUTABLE_TOLERANCE
    )


def _shape_matches_area(width: float, height: float, target_area: float) -> bool:
    actual_area = width * height
    if not (
        math.isfinite(width)
        and math.isfinite(height)
        and math.isfinite(actual_area)
        and math.isfinite(target_area)
        and width > 0.0
        and height > 0.0
        and target_area > 0.0
    ):
        return False
    relative_error = abs(actual_area - target_area) / target_area
    return relative_error <= AREA_TOLERANCE + 1e-12


def _common_soft_mib_shape(parsed: ParsedInput, members: Sequence[int]) -> Optional[Tuple[float, float]]:
    if not members:
        return None

    lower_area = 0.0
    upper_area = float("inf")
    for block_id in members:
        if block_id in parsed.invalid_area_ids:
            return None
        area = parsed.areas[block_id]
        if not math.isfinite(area) or area <= 0.0:
            return None
        lower_area = max(lower_area, area * (1.0 - AREA_TOLERANCE))
        upper_area = min(upper_area, area * (1.0 + AREA_TOLERANCE))

    if lower_area > upper_area + 1e-12:
        return None

    common_area = (lower_area + upper_area) / 2.0
    if not math.isfinite(common_area) or common_area <= 0.0:
        return None
    side = math.sqrt(common_area)
    return side, side


def _plan_dimensions(parsed: ParsedInput, immutable: ImmutableGeometry) -> DimensionPlan:
    widths = [1.0] * parsed.n
    heights = [1.0] * parsed.n
    sources = ["ordinary_soft"] * parsed.n
    invalid_reasons = list(immutable.invalid_reasons)
    mib_notes: Dict[int, str] = {}

    for block_id, (_, _, w, h) in immutable.preplaced_rects.items():
        widths[block_id] = w
        heights[block_id] = h
        sources[block_id] = "immutable_preplaced"

    for block_id, (w, h) in immutable.fixed_dims.items():
        if block_id in immutable.preplaced_rects:
            continue
        widths[block_id] = w
        heights[block_id] = h
        sources[block_id] = "immutable_fixed"

    for block_id in range(parsed.n):
        if block_id in immutable.preplaced_rects or block_id in immutable.fixed_dims:
            continue
        area = parsed.areas[block_id]
        if block_id in parsed.invalid_area_ids:
            invalid_reasons.append(f"invalid soft area for block {block_id}")
            sources[block_id] = "fallback_repair"
            area = 1.0
        if area <= 0.0 or not math.isfinite(area):
            invalid_reasons.append(f"invalid soft area for block {block_id}")
            area = 1.0
            sources[block_id] = "fallback_repair"
        side = math.sqrt(area)
        widths[block_id] = side
        heights[block_id] = side

    for group_id, raw_members in parsed.mib_groups.items():
        members = [i for i in raw_members if 0 <= i < parsed.n]
        if len(members) <= 1:
            mib_notes[group_id] = "single-member"
            continue

        soft_members = [i for i in members if i not in parsed.fixed_or_preplaced_ids]
        immutable_members = [i for i in members if i in parsed.fixed_or_preplaced_ids]

        common_shape: Optional[Tuple[float, float]] = None
        if immutable_members:
            immutable_shape = (widths[immutable_members[0]], heights[immutable_members[0]])
            immutable_shapes_match = all(
                _same_shape(immutable_shape, (widths[block_id], heights[block_id]))
                for block_id in immutable_members[1:]
            )
            if immutable_shapes_match and all(
                block_id not in parsed.invalid_area_ids
                and _shape_matches_area(immutable_shape[0], immutable_shape[1], parsed.areas[block_id])
                for block_id in soft_members
            ):
                common_shape = immutable_shape
        else:
            common_shape = _common_soft_mib_shape(parsed, soft_members)

        if common_shape is not None:
            common_width, common_height = common_shape
            for block_id in soft_members:
                widths[block_id] = common_width
                heights[block_id] = common_height
                if sources[block_id] != "fallback_repair":
                    sources[block_id] = "mib_synchronized_soft"
            if soft_members:
                mib_notes[group_id] = "synchronized"
            else:
                mib_notes[group_id] = "synchronized-immutable"
        else:
            mib_notes[group_id] = "incompatible-hard-area-preserved"

    return DimensionPlan(
        widths=widths,
        heights=heights,
        sources=sources,
        invalid_reasons=invalid_reasons,
        mib_notes=mib_notes,
    )


def _build_fallback(
    parsed: ParsedInput,
    immutable: ImmutableGeometry,
    dimensions: DimensionPlan,
) -> Candidate:
    candidates = [
        _build_fallback_with_shelf_width(parsed, immutable, dimensions, None, 0)
    ]
    compact_shelf_width = _fallback_compact_shelf_width(parsed, dimensions)
    if compact_shelf_width is not None:
        candidates.append(
            _build_fallback_with_shelf_width(
                parsed,
                immutable,
                dimensions,
                compact_shelf_width,
                1,
            )
        )

    return min(candidates, key=lambda candidate: _fallback_selection_key(candidate, parsed))


def _build_fallback_with_shelf_width(
    parsed: ParsedInput,
    immutable: ImmutableGeometry,
    dimensions: DimensionPlan,
    shelf_width: Optional[float],
    source_order: int,
) -> Candidate:
    positions: List[Optional[Rect]] = [None] * parsed.n

    for block_id, rect in immutable.preplaced_rects.items():
        positions[block_id] = rect

    x_origin, y_cursor = _fallback_shelf_origin(immutable)
    x_cursor = x_origin
    row_height = 0.0

    for block_id in range(parsed.n):
        if positions[block_id] is not None:
            continue
        w = dimensions.widths[block_id]
        h = dimensions.heights[block_id]
        if not math.isfinite(w) or w <= 0.0:
            w = 1.0
        if not math.isfinite(h) or h <= 0.0:
            h = 1.0
        if (
            shelf_width is not None
            and row_height > 0.0
            and x_cursor > x_origin
            and x_cursor + w > x_origin + shelf_width + OVERLAP_TOLERANCE
        ):
            x_cursor = x_origin
            y_cursor += row_height
            row_height = 0.0
        positions[block_id] = (x_cursor, y_cursor, w, h)
        x_cursor += w
        row_height = max(row_height, h)

    candidate = Candidate(
        positions=[rect if rect is not None else (0.0, 0.0, 1.0, 1.0)
                   for rect in positions],
        source="fallback",
        source_order=source_order,
    )
    candidate.hard_report = _preflight(candidate, parsed, immutable, dimensions)
    try:
        candidate.proxy_score = _score_candidate(candidate, parsed)
    except Exception:
        candidate.proxy_score = None
    return candidate


def _fallback_compact_shelf_width(
    parsed: ParsedInput,
    dimensions: DimensionPlan,
) -> Optional[float]:
    movable_ids = [
        block_id for block_id in range(parsed.n)
        if block_id not in parsed.preplaced_ids
    ]
    if len(movable_ids) <= 2:
        return None

    total_area = 0.0
    max_width = 0.0
    one_row_width = 0.0
    for block_id in movable_ids:
        width = dimensions.widths[block_id]
        height = dimensions.heights[block_id]
        if not (
            math.isfinite(width)
            and math.isfinite(height)
            and width > 0.0
            and height > 0.0
        ):
            return None
        total_area += width * height
        max_width = max(max_width, width)
        one_row_width += width

    if total_area <= 0.0 or one_row_width <= 0.0:
        return None
    shelf_width = max(max_width, math.sqrt(total_area) * CONSTRUCTIVE_SHELF_ASPECT)
    if shelf_width >= one_row_width - OVERLAP_TOLERANCE:
        return None
    return shelf_width


def _fallback_selection_key(candidate: Candidate, parsed: ParsedInput) -> Tuple[int, float, float, float, int]:
    report = candidate.hard_report
    hard_violations = HARD_BARRIER
    if report is not None:
        hard_violations = (
            report.malformed_violations
            + report.overlap_violations
            + report.area_violations
            + report.dimension_violations
        )
    proxy = candidate.proxy_score
    if proxy is not None:
        return (
            int(hard_violations),
            proxy.score,
            proxy.bbox_area,
            proxy.hpwl_total,
            candidate.source_order,
        )
    return (
        int(hard_violations),
        HARD_BARRIER,
        _bbox_area(candidate.positions),
        _hpwl_b2b(candidate.positions, parsed.b2b_edges)
        + _hpwl_p2b(candidate.positions, parsed.p2b_edges, parsed.pins),
        candidate.source_order,
    )


def _fallback_shelf_origin(immutable: ImmutableGeometry) -> Tuple[float, float]:
    if not immutable.obstacle_rects:
        return 0.0, 0.0

    min_y = min(y for _, (_, y, _, _) in immutable.obstacle_rects)
    max_x = max(x + w for _, (x, _, w, _) in immutable.obstacle_rects)
    # Conservative convention: place every movable block in one horizontal
    # shelf strictly to the right of the preplaced-obstacle bounding box.
    return max(0.0, max_x + FALLBACK_OBSTACLE_GAP), min(0.0, min_y)


def _preflight(
    candidate: Candidate,
    parsed: ParsedInput,
    immutable: ImmutableGeometry,
    dimensions: DimensionPlan,
) -> PreflightReport:
    messages: List[str] = []
    malformed = 0
    positions = candidate.positions

    if len(positions) != parsed.n:
        malformed += 1
        messages.append("candidate length mismatch")

    clean_positions: List[Rect] = []
    for i in range(parsed.n):
        if i >= len(positions) or _length(positions[i]) != 4:
            malformed += 1
            clean_positions.append((0.0, 0.0, 1.0, 1.0))
            continue
        rect = tuple(_as_float(value, float("nan")) for value in positions[i])
        x, y, w, h = rect
        if not all(math.isfinite(v) for v in rect) or w <= 0.0 or h <= 0.0:
            malformed += 1
        clean_positions.append((x, y, w, h))

    overlap_violations = _count_overlap_violations(clean_positions)

    area_violations = 0
    for i, (_, _, w, h) in enumerate(clean_positions):
        if i in parsed.fixed_or_preplaced_ids:
            continue
        target_area = parsed.areas[i]
        if target_area <= 0.0:
            area_violations += 1
            continue
        if abs((w * h) - target_area) / target_area > AREA_TOLERANCE:
            area_violations += 1

    dimension_violations = len(immutable.invalid_reasons)
    dimension_violations += len(dimensions.invalid_reasons) - len(immutable.invalid_reasons)
    for block_id, (target_w, target_h) in immutable.fixed_dims.items():
        if block_id in immutable.preplaced_rects:
            continue
        _, _, w, h = clean_positions[block_id]
        if abs(w - target_w) > IMMUTABLE_TOLERANCE or abs(h - target_h) > IMMUTABLE_TOLERANCE:
            dimension_violations += 1

    for block_id, target_rect in immutable.preplaced_rects.items():
        rect = clean_positions[block_id]
        if any(abs(rect[k] - target_rect[k]) > IMMUTABLE_TOLERANCE for k in range(4)):
            dimension_violations += 1

    soft_report = _soft_violations(clean_positions, parsed)
    hard_feasible = (
        malformed == 0
        and overlap_violations == 0
        and area_violations == 0
        and dimension_violations == 0
    )
    return PreflightReport(
        hard_feasible=hard_feasible,
        malformed_violations=malformed,
        overlap_violations=overlap_violations,
        area_violations=area_violations,
        dimension_violations=dimension_violations,
        boundary_violations=soft_report["boundary"],
        grouping_violations=soft_report["grouping"],
        mib_violations=soft_report["mib"],
        total_soft_violations=soft_report["total"],
        max_possible_violations=soft_report["max_possible"],
        violations_relative=soft_report["relative"],
        messages=messages + immutable.invalid_reasons + dimensions.invalid_reasons,
    )


def _soft_violations(positions: Sequence[Rect], parsed: ParsedInput) -> Dict[str, float]:
    boundary = _boundary_violations(positions, parsed.boundary_masks)
    grouping = _grouping_violations(positions, parsed.cluster_groups)
    mib = _mib_violations(positions, parsed.mib_groups)

    max_possible = len(parsed.boundary_masks)
    max_possible += sum(max(0, len(members) - 1) for members in parsed.cluster_groups.values())
    max_possible += sum(max(0, len(members) - 1) for members in parsed.mib_groups.values())
    total = boundary + grouping + mib
    return {
        "boundary": boundary,
        "grouping": grouping,
        "mib": mib,
        "total": total,
        "max_possible": max_possible,
        "relative": total / max(max_possible, 1),
    }


def _boundary_violations(positions: Sequence[Rect], boundary_masks: Dict[int, int]) -> int:
    if not boundary_masks or not positions:
        return 0
    x_min = min(x for x, _, _, _ in positions)
    y_min = min(y for _, y, _, _ in positions)
    x_max = max(x + w for x, _, w, _ in positions)
    y_max = max(y + h for _, y, _, h in positions)

    violations = 0
    for block_id, mask in boundary_masks.items():
        if block_id >= len(positions):
            violations += 1
            continue
        x, y, w, h = positions[block_id]
        touches = {
            1: abs(x - x_min) < OVERLAP_TOLERANCE,
            2: abs(x + w - x_max) < OVERLAP_TOLERANCE,
            4: abs(y + h - y_max) < OVERLAP_TOLERANCE,
            8: abs(y - y_min) < OVERLAP_TOLERANCE,
        }
        if not all(touches[bit] for bit in (1, 2, 4, 8) if mask & bit):
            violations += 1
    return violations


def _grouping_violations(positions: Sequence[Rect], groups: Dict[int, List[int]]) -> int:
    violations = 0
    for members in groups.values():
        members = [i for i in members if i < len(positions)]
        if len(members) <= 1:
            continue
        adjacency = {i: set() for i in members}
        for i, first in enumerate(members):
            for second in members[i + 1:]:
                if _rects_share_edge(positions[first], positions[second]):
                    adjacency[first].add(second)
                    adjacency[second].add(first)

        seen = set()
        components = 0
        for member in members:
            if member in seen:
                continue
            components += 1
            stack = [member]
            seen.add(member)
            while stack:
                current = stack.pop()
                for neighbor in adjacency[current]:
                    if neighbor not in seen:
                        seen.add(neighbor)
                        stack.append(neighbor)
        violations += max(0, components - 1)
    return violations


def _rects_share_edge(a: Rect, b: Rect) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    vertical_touch = (
        abs((ax + aw) - bx) < OVERLAP_TOLERANCE
        or abs((bx + bw) - ax) < OVERLAP_TOLERANCE
    )
    vertical_overlap = min(ay + ah, by + bh) - max(ay, by) > OVERLAP_TOLERANCE
    horizontal_touch = (
        abs((ay + ah) - by) < OVERLAP_TOLERANCE
        or abs((by + bh) - ay) < OVERLAP_TOLERANCE
    )
    horizontal_overlap = min(ax + aw, bx + bw) - max(ax, bx) > OVERLAP_TOLERANCE
    return (vertical_touch and vertical_overlap) or (horizontal_touch and horizontal_overlap)


def _mib_violations(positions: Sequence[Rect], groups: Dict[int, List[int]]) -> int:
    violations = 0
    for members in groups.values():
        shapes = set()
        for block_id in members:
            if block_id < len(positions):
                _, _, w, h = positions[block_id]
                shapes.add((round(w, 4), round(h, 4)))
        violations += max(0, len(shapes) - 1)
    return violations


def _score_candidate(candidate: Candidate, parsed: ParsedInput) -> ProxyScore:
    report = candidate.hard_report
    score_positions = _score_positions(candidate.positions, parsed.n)
    hard_barrier = 0.0 if report is not None and report.hard_feasible else HARD_BARRIER

    if score_positions is None:
        soft_relative = report.violations_relative if report is not None else 0.0
        return ProxyScore(
            HARD_BARRIER,
            HARD_BARRIER / 2.0,
            HARD_BARRIER / 2.0,
            _finite_metric(soft_relative, 0.0),
            HARD_BARRIER,
            HARD_BARRIER / 2.0,
            HARD_BARRIER / 2.0,
            report.boundary_violations if report is not None else 0,
            report.grouping_violations if report is not None else 0,
            report.mib_violations if report is not None else 0,
            report.total_soft_violations if report is not None else 0,
            report.max_possible_violations if report is not None else 0,
        )

    hpwl_b2b = _hpwl_b2b(score_positions, parsed.b2b_edges)
    hpwl_p2b = _hpwl_p2b(score_positions, parsed.p2b_edges, parsed.pins)
    hpwl_total = hpwl_b2b + hpwl_p2b
    bbox = _finite_metric(_bbox_area(score_positions))

    if report is not None:
        boundary = report.boundary_violations
        grouping = report.grouping_violations
        mib = report.mib_violations
        total_soft = report.total_soft_violations
        max_possible = report.max_possible_violations
        soft_relative = report.violations_relative
    else:
        soft_report = _soft_violations(score_positions, parsed)
        boundary = int(soft_report["boundary"])
        grouping = int(soft_report["grouping"])
        mib = int(soft_report["mib"])
        total_soft = int(soft_report["total"])
        max_possible = int(soft_report["max_possible"])
        soft_relative = float(soft_report["relative"])

    hpwl_total = _finite_metric(hpwl_total)
    soft_relative = max(0.0, _finite_metric(soft_relative, 0.0))
    weighted_quality = (
        PROXY_HPWL_WEIGHT * hpwl_total
        + PROXY_BBOX_WEIGHT * bbox
        + PROXY_SOFT_WEIGHT * soft_relative
    )
    soft_factor = math.exp(min(50.0, PROXY_SOFT_EXPONENT * soft_relative))
    score = (
        hard_barrier
        + (1.0 + weighted_quality) * soft_factor
        - 1.0
    )
    score = _finite_metric(score, HARD_BARRIER)
    if hard_barrier > 0.0:
        score = max(score, hard_barrier)
    return ProxyScore(
        score,
        hpwl_total,
        bbox,
        soft_relative,
        hard_barrier,
        hpwl_b2b,
        hpwl_p2b,
        boundary,
        grouping,
        mib,
        total_soft,
        max_possible,
    )


def _proxy_score_is_finite(score: Any) -> bool:
    if not isinstance(score, ProxyScore):
        return False
    return all(math.isfinite(value) for value in (
        score.score,
        score.hpwl_total,
        score.bbox_area,
        score.soft_relative,
        score.hard_barrier,
        score.hpwl_b2b,
        score.hpwl_p2b,
    ))


class CandidateManager:
    def __init__(
        self,
        context: SolverContext,
        preflight_fn: Callable[[Candidate, ParsedInput, ImmutableGeometry, DimensionPlan], PreflightReport] = _preflight,
        score_fn: Callable[[Candidate, ParsedInput], ProxyScore] = _score_candidate,
    ):
        self.context = context
        self._preflight_fn = preflight_fn
        self._score_fn = score_fn
        self.fallback: Optional[Candidate] = None
        self.best_feasible: Optional[Candidate] = None
        self.best_infeasible: Optional[Candidate] = None
        self.diagnostics: List[str] = []

    def consider(self, candidate: Candidate) -> Candidate:
        report = self._preflight_fn(
            candidate,
            self.context.parsed,
            self.context.immutable,
            self.context.dimensions,
        )
        candidate.hard_report = report

        if candidate.source == "fallback" and self.fallback is None:
            self.fallback = candidate

        if report.malformed_violations > 0:
            candidate.proxy_score = None
            self.diagnostics.append(
                f"rejected malformed candidate {candidate.source}"
            )
            return candidate

        candidate.proxy_score = self._safe_score(candidate)

        if report.hard_feasible:
            if self.best_feasible is None or self._candidate_key(candidate) < self._candidate_key(self.best_feasible):
                self.best_feasible = candidate
        elif self.best_infeasible is None or self._infeasible_key(candidate) < self._infeasible_key(self.best_infeasible):
            self.best_infeasible = candidate
        return candidate

    def _safe_score(self, candidate: Candidate) -> ProxyScore:
        try:
            score = self._score_fn(candidate, self.context.parsed)
            if not _proxy_score_is_finite(score):
                raise ValueError("nonfinite proxy score")
            return score
        except Exception as exc:
            self.diagnostics.append(
                f"proxy scoring failed for {candidate.source}: {exc}"
            )
            return _conservative_proxy_score(candidate)

    def best_feasible_candidate(self) -> Optional[Candidate]:
        return self.best_feasible

    def best_feasible_or_fallback(self) -> Candidate:
        if self.best_feasible is not None:
            return self.best_feasible
        if self.fallback is not None:
            return self.fallback
        if self.best_infeasible is not None:
            return self.best_infeasible
        return Candidate([], "empty", HARD_BARRIER)

    @staticmethod
    def _candidate_key(candidate: Candidate) -> Tuple[float, float, float, int]:
        score = candidate.proxy_score
        if score is None:
            return (HARD_BARRIER, HARD_BARRIER, HARD_BARRIER, candidate.source_order)
        return (score.score, score.bbox_area, score.hpwl_total, candidate.source_order)

    @staticmethod
    def _infeasible_key(candidate: Candidate) -> Tuple[int, float, float, float, int]:
        report = candidate.hard_report
        hard_violations = HARD_BARRIER
        if report is not None:
            hard_violations = (
                report.overlap_violations
                + report.area_violations
                + report.dimension_violations
            )
        score_key = CandidateManager._candidate_key(candidate)
        return (int(hard_violations), score_key[0], score_key[1], score_key[2], score_key[3])


def _conservative_proxy_score(candidate: Candidate) -> ProxyScore:
    report = candidate.hard_report
    hard_barrier = 0.0 if report is not None and report.hard_feasible else HARD_BARRIER
    soft_relative = report.violations_relative if report is not None else 1.0
    return ProxyScore(
        HARD_BARRIER / 2.0 + hard_barrier,
        HARD_BARRIER / 2.0,
        HARD_BARRIER / 2.0,
        soft_relative,
        hard_barrier,
        HARD_BARRIER / 2.0,
        HARD_BARRIER / 2.0,
        report.boundary_violations if report is not None else 0,
        report.grouping_violations if report is not None else 0,
        report.mib_violations if report is not None else 0,
        report.total_soft_violations if report is not None else 0,
        report.max_possible_violations if report is not None else 0,
    )


def _block_mib_groups(parsed: ParsedInput) -> Dict[int, Tuple[int, ...]]:
    groups_by_block: Dict[int, List[int]] = {}
    for group_id, members in parsed.mib_groups.items():
        for block_id in members:
            if 0 <= block_id < parsed.n:
                groups_by_block.setdefault(block_id, []).append(group_id)
    return {
        block_id: tuple(sorted(group_ids))
        for block_id, group_ids in groups_by_block.items()
    }


def _block_cluster_groups(parsed: ParsedInput) -> Dict[int, Tuple[int, ...]]:
    groups_by_block: Dict[int, List[int]] = {}
    for group_id, members in parsed.cluster_groups.items():
        for block_id in members:
            if 0 <= block_id < parsed.n:
                groups_by_block.setdefault(block_id, []).append(group_id)
    return {
        block_id: tuple(sorted(group_ids))
        for block_id, group_ids in groups_by_block.items()
    }


def _unit_soft_links(
    block_ids: Sequence[int],
    parsed: ParsedInput,
    extra_links: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    mib_by_block = _block_mib_groups(parsed)
    cluster_by_block = _block_cluster_groups(parsed)
    mib_groups = sorted({
        group_id
        for block_id in block_ids
        for group_id in mib_by_block.get(block_id, ())
    })
    cluster_groups = sorted({
        group_id
        for block_id in block_ids
        for group_id in cluster_by_block.get(block_id, ())
    })
    boundary_masks = {
        block_id: parsed.boundary_masks[block_id]
        for block_id in block_ids
        if block_id in parsed.boundary_masks
    }

    links: Dict[str, Any] = {
        "mib_groups": tuple(mib_groups),
        "cluster_groups": tuple(cluster_groups),
        "boundary_masks": boundary_masks,
    }
    if extra_links:
        links.update(extra_links)
    return links


def _make_single_block_unit(
    block_id: int,
    parsed: ParsedInput,
    immutable: ImmutableGeometry,
    dimensions: DimensionPlan,
) -> PlacementUnit:
    width = dimensions.widths[block_id]
    height = dimensions.heights[block_id]
    fixed_origin = None
    movable = block_id not in immutable.preplaced_rects
    kind = "block"

    if block_id in immutable.preplaced_rects:
        x, y, width, height = immutable.preplaced_rects[block_id]
        fixed_origin = (x, y)
        kind = "preplaced"

    boundary_intent = parsed.boundary_masks.get(block_id, 0)
    return PlacementUnit(
        unit_id=f"block:{block_id}",
        kind=kind,
        block_ids=(block_id,),
        local_rects={block_id: (0.0, 0.0, width, height)},
        bbox_width=width,
        bbox_height=height,
        movable=movable,
        boundary_intent=boundary_intent,
        soft_links=_unit_soft_links((block_id,), parsed),
        fixed_origin=fixed_origin,
    )


def _chain_cluster_layout(
    block_ids: Sequence[int],
    dimensions: DimensionPlan,
) -> Tuple[Dict[int, Rect], float, float]:
    x_cursor = 0.0
    bbox_height = 0.0
    local_rects: Dict[int, Rect] = {}

    for block_id in sorted(block_ids):
        width = dimensions.widths[block_id]
        height = dimensions.heights[block_id]
        local_rects[block_id] = (x_cursor, 0.0, width, height)
        x_cursor += width
        bbox_height = max(bbox_height, height)

    return local_rects, x_cursor, bbox_height


def _compact_cluster_layout(
    block_ids: Sequence[int],
    dimensions: DimensionPlan,
) -> Tuple[Dict[int, Rect], float, float]:
    blocks = sorted(
        block_ids,
        key=lambda block_id: (
            -dimensions.heights[block_id],
            -dimensions.widths[block_id],
            block_id,
        ),
    )
    total_area = sum(
        max(0.0, dimensions.widths[block_id] * dimensions.heights[block_id])
        for block_id in blocks
    )
    target_width = max(
        max((dimensions.widths[block_id] for block_id in blocks), default=0.0),
        math.sqrt(total_area) if total_area > 0.0 else 0.0,
    )

    rows: List[List[int]] = []
    current_row: List[int] = []
    current_width = 0.0
    for block_id in blocks:
        width = dimensions.widths[block_id]
        if (
            current_row
            and target_width > 0.0
            and current_width + width > target_width + OVERLAP_TOLERANCE
        ):
            rows.append(current_row)
            current_row = []
            current_width = 0.0
        current_row.append(block_id)
        current_width += width
    if current_row:
        rows.append(current_row)

    local_rects: Dict[int, Rect] = {}
    y_cursor = 0.0
    bbox_width = 0.0
    for row in rows:
        x_cursor = 0.0
        row_height = max(dimensions.heights[block_id] for block_id in row)
        for block_id in row:
            width = dimensions.widths[block_id]
            height = dimensions.heights[block_id]
            local_rects[block_id] = (x_cursor, y_cursor, width, height)
            x_cursor += width
        bbox_width = max(bbox_width, x_cursor)
        y_cursor += row_height

    return local_rects, bbox_width, y_cursor


def _cluster_layout_key(
    local_rects: Dict[int, Rect],
    bbox_width: float,
    bbox_height: float,
) -> Tuple[float, float, float, Tuple[Tuple[int, float, float], ...]]:
    return (
        bbox_width * bbox_height,
        max(bbox_width, bbox_height),
        bbox_width,
        tuple(
            (block_id, round(rect[0], 6), round(rect[1], 6))
            for block_id, rect in sorted(local_rects.items())
        ),
    )


def _cluster_macro_layout(
    block_ids: Sequence[int],
    dimensions: DimensionPlan,
) -> Tuple[Dict[int, Rect], float, float]:
    chain = _chain_cluster_layout(block_ids, dimensions)
    if len(block_ids) <= 2:
        return chain

    compact = _compact_cluster_layout(block_ids, dimensions)
    if _cluster_layout_key(*compact) < _cluster_layout_key(*chain):
        return compact
    return chain


def _make_cluster_macro(
    cluster_id: int,
    movable_members: Sequence[int],
    preplaced_members: Sequence[int],
    parsed: ParsedInput,
    dimensions: DimensionPlan,
) -> PlacementUnit:
    boundary_intent = 0
    local_rects, bbox_width, bbox_height = _cluster_macro_layout(
        movable_members,
        dimensions,
    )

    for block_id in sorted(movable_members):
        boundary_intent |= parsed.boundary_masks.get(block_id, 0)

    block_ids = tuple(sorted(movable_members))
    soft_links = _unit_soft_links(
        block_ids,
        parsed,
        {
            "cluster_id": cluster_id,
            "cluster_members": tuple(sorted(
                block_id for block_id in parsed.cluster_groups.get(cluster_id, [])
                if 0 <= block_id < parsed.n
            )),
            "preplaced_cluster_members": tuple(sorted(preplaced_members)),
        },
    )
    return PlacementUnit(
        unit_id=f"cluster:{cluster_id}",
        kind="cluster_macro",
        block_ids=block_ids,
        local_rects=local_rects,
        bbox_width=bbox_width,
        bbox_height=bbox_height,
        movable=True,
        boundary_intent=boundary_intent,
        soft_links=soft_links,
    )


def _build_mib_metadata(parsed: ParsedInput, dimensions: DimensionPlan) -> Dict[int, Dict[str, Any]]:
    metadata: Dict[int, Dict[str, Any]] = {}
    for group_id, raw_members in sorted(parsed.mib_groups.items()):
        members = tuple(sorted(block_id for block_id in raw_members if 0 <= block_id < parsed.n))
        shapes = {
            block_id: (dimensions.widths[block_id], dimensions.heights[block_id])
            for block_id in members
        }
        distinct_shapes = {
            (round(width, 4), round(height, 4))
            for width, height in shapes.values()
        }
        note = dimensions.mib_notes.get(group_id, "not-planned")
        metadata[group_id] = {
            "block_ids": members,
            "shapes": shapes,
            "note": note,
            "same_shape": len(distinct_shapes) <= 1,
        }
    return metadata


def _plan_soft_units(context: SolverContext) -> PlacementUnitSet:
    parsed = context.parsed
    immutable = context.immutable
    dimensions = context.dimensions
    units: List[PlacementUnit] = []
    group_macros: Dict[int, PlacementUnit] = {}
    block_to_unit: Dict[int, str] = {}
    diagnostics: List[str] = []
    macro_member_ids = set()

    for cluster_id, raw_members in sorted(parsed.cluster_groups.items()):
        members = [block_id for block_id in sorted(raw_members) if 0 <= block_id < parsed.n]
        movable_members = [block_id for block_id in members if block_id not in parsed.preplaced_ids]
        preplaced_members = [block_id for block_id in members if block_id in parsed.preplaced_ids]

        if len(movable_members) > 1:
            macro = _make_cluster_macro(
                cluster_id,
                movable_members,
                preplaced_members,
                parsed,
                dimensions,
            )
            group_macros[cluster_id] = macro
            units.append(macro)
            macro_member_ids.update(movable_members)
            for block_id in macro.block_ids:
                block_to_unit[block_id] = macro.unit_id

        if preplaced_members:
            diagnostics.append(
                f"cluster {cluster_id} contains preplaced members; immutable blocks kept fixed"
            )

    for block_id in range(parsed.n):
        if block_id in macro_member_ids:
            continue
        unit = _make_single_block_unit(block_id, parsed, immutable, dimensions)
        units.append(unit)
        block_to_unit[block_id] = unit.unit_id

    boundary_intents = {
        unit.unit_id: unit.boundary_intent
        for unit in units
        if unit.boundary_intent != 0
    }

    return PlacementUnitSet(
        units=units,
        group_macros=group_macros,
        mib_metadata=_build_mib_metadata(parsed, dimensions),
        boundary_intents=boundary_intents,
        block_to_unit=block_to_unit,
        diagnostics=diagnostics,
    )


def _expand_unit(
    unit: PlacementUnit,
    origin: Optional[Tuple[float, float]] = None,
) -> Dict[int, Rect]:
    if origin is None:
        origin = unit.fixed_origin if unit.fixed_origin is not None else (0.0, 0.0)
    origin_x, origin_y = origin
    expanded: Dict[int, Rect] = {}
    for block_id, (local_x, local_y, width, height) in unit.local_rects.items():
        expanded[block_id] = (
            origin_x + local_x,
            origin_y + local_y,
            width,
            height,
        )
    return expanded


def _expand_units(
    unit_set: PlacementUnitSet,
    origins: Optional[Dict[str, Tuple[float, float]]] = None,
) -> Dict[int, Rect]:
    origins = origins or {}
    expanded: Dict[int, Rect] = {}
    for unit in unit_set.units:
        origin = origins.get(unit.unit_id)
        for block_id, rect in _expand_unit(unit, origin).items():
            expanded[block_id] = rect
    return expanded


def _unit_min_block_id(unit: PlacementUnit) -> int:
    return min(unit.block_ids) if unit.block_ids else HARD_BARRIER


def _unit_area(unit: PlacementUnit) -> float:
    area = 0.0
    for _, _, width, height in unit.local_rects.values():
        if math.isfinite(width) and math.isfinite(height) and width > 0.0 and height > 0.0:
            area += width * height
    return area


def _unit_connectivity_weight(unit: PlacementUnit, parsed: ParsedInput) -> float:
    block_ids = set(unit.block_ids)
    weight_sum = 0.0
    for first, second, weight in parsed.b2b_edges:
        if first in block_ids or second in block_ids:
            weight_sum += abs(weight)
    for _, block_id, weight in parsed.p2b_edges:
        if block_id in block_ids:
            weight_sum += abs(weight)
    return weight_sum


def _seed_sort_key(unit: PlacementUnit) -> Tuple[int, str]:
    return _unit_min_block_id(unit), unit.unit_id


def _boundary_frame_sort_key(unit: PlacementUnit) -> Tuple[int, int, str]:
    mask = unit.boundary_intent
    if not mask:
        bucket = 1
    elif mask & (2 | 4) and not mask & (1 | 8):
        bucket = 2
    else:
        bucket = 0
    return bucket, _unit_min_block_id(unit), unit.unit_id


def _connectivity_greedy_order(
    parsed: ParsedInput,
    units: Sequence[PlacementUnit],
) -> List[PlacementUnit]:
    fixed_units = sorted(
        (unit for unit in units if not unit.movable),
        key=_seed_sort_key,
    )
    movable_units = sorted(
        (unit for unit in units if unit.movable),
        key=_seed_sort_key,
    )
    if len(movable_units) <= 1:
        return fixed_units + movable_units

    unit_by_id = {unit.unit_id: unit for unit in units}
    block_to_unit: Dict[int, str] = {}
    for unit in units:
        for block_id in unit.block_ids:
            block_to_unit[block_id] = unit.unit_id

    adjacency: Dict[str, Dict[str, float]] = {
        unit.unit_id: {} for unit in units
    }
    incident: Dict[str, float] = {
        unit.unit_id: 0.0 for unit in movable_units
    }
    for first, second, weight in parsed.b2b_edges:
        first_unit = block_to_unit.get(first)
        second_unit = block_to_unit.get(second)
        if (
            first_unit is None
            or second_unit is None
            or first_unit == second_unit
        ):
            continue
        edge_weight = abs(weight)
        if not math.isfinite(edge_weight) or edge_weight <= 0.0:
            continue
        adjacency[first_unit][second_unit] = (
            adjacency[first_unit].get(second_unit, 0.0) + edge_weight
        )
        adjacency[second_unit][first_unit] = (
            adjacency[second_unit].get(first_unit, 0.0) + edge_weight
        )
        if first_unit in incident:
            incident[first_unit] += edge_weight
        if second_unit in incident:
            incident[second_unit] += edge_weight

    placed = {unit.unit_id for unit in fixed_units}
    remaining = {unit.unit_id for unit in movable_units}
    ordered_movable: List[PlacementUnit] = []

    while remaining:
        def greedy_key(unit_id: str) -> Tuple[float, float, int, str]:
            frontier_weight = sum(
                adjacency[unit_id].get(placed_id, 0.0)
                for placed_id in placed
            )
            unit = unit_by_id[unit_id]
            return (
                -frontier_weight,
                -incident.get(unit_id, 0.0),
                _unit_min_block_id(unit),
                unit.unit_id,
            )

        next_unit_id = min(remaining, key=greedy_key)
        remaining.remove(next_unit_id)
        placed.add(next_unit_id)
        ordered_movable.append(unit_by_id[next_unit_id])

    return fixed_units + ordered_movable


def _constructive_seed_orders(
    context: SolverContext,
    unit_set: PlacementUnitSet,
) -> List[Tuple[str, List[PlacementUnit], bool]]:
    parsed = context.parsed
    units = list(unit_set.units)
    return [
        (
            "original_id",
            sorted(units, key=_seed_sort_key),
            False,
        ),
        (
            "descending_area",
            sorted(units, key=lambda unit: (-_unit_area(unit), _unit_min_block_id(unit), unit.unit_id)),
            True,
        ),
        (
            "connectivity_weight",
            sorted(units, key=lambda unit: (
                -_unit_connectivity_weight(unit, parsed),
                _unit_min_block_id(unit),
                unit.unit_id,
            )),
            True,
        ),
        (
            "connectivity_greedy",
            _connectivity_greedy_order(parsed, units),
            True,
        ),
        (
            "boundary_first",
            sorted(units, key=lambda unit: (
                0 if unit.boundary_intent else 1,
                _unit_min_block_id(unit),
                unit.unit_id,
            )),
            True,
        ),
        (
            "boundary_frame",
            sorted(units, key=_boundary_frame_sort_key),
            True,
        ),
        (
            "grouping_macro_priority",
            sorted(units, key=lambda unit: (
                0 if unit.kind == "cluster_macro" else 1,
                _unit_min_block_id(unit),
                unit.unit_id,
            )),
            True,
        ),
        (
            "boundary_skyline",
            sorted(units, key=_boundary_frame_sort_key),
            True,
        ),
    ]


def _constructive_shelf_width(units: Sequence[PlacementUnit], compact: bool) -> Optional[float]:
    if not compact:
        return None
    return _shelf_width_for_units(units, CONSTRUCTIVE_SHELF_ASPECT)


def _shelf_width_for_units(
    units: Sequence[PlacementUnit],
    aspect: float,
) -> Optional[float]:
    if not units:
        return 0.0

    total_area = sum(max(0.0, unit.bbox_width * unit.bbox_height) for unit in units)
    max_width = max(max(0.0, unit.bbox_width) for unit in units)
    if (
        total_area <= 0.0
        or not math.isfinite(total_area)
        or aspect <= 0.0
        or not math.isfinite(aspect)
    ):
        return max_width
    return max(max_width, math.sqrt(total_area) * aspect)


def _constructive_origin_for_unit(
    unit: PlacementUnit,
    x_cursor: float,
    y_cursor: float,
) -> Tuple[float, float]:
    if not unit.movable and unit.fixed_origin is not None:
        return unit.fixed_origin
    return x_cursor, y_cursor


def _candidate_from_expanded(
    parsed: ParsedInput,
    expanded: Dict[int, Rect],
    source: str,
    source_order: int,
) -> Optional[Candidate]:
    if any(block_id not in expanded for block_id in range(parsed.n)):
        return None
    return Candidate(
        positions=[expanded[block_id] for block_id in range(parsed.n)],
        source=source,
        source_order=source_order,
    )


def _pack_units_as_candidate(
    context: SolverContext,
    unit_set: PlacementUnitSet,
    ordered_units: Sequence[PlacementUnit],
    source: str,
    source_order: int,
    compact: bool,
    shelf_width_override: Optional[float] = None,
) -> Optional[Candidate]:
    origins: Dict[str, Tuple[float, float]] = {}

    for unit in ordered_units:
        if not unit.movable:
            origins[unit.unit_id] = _constructive_origin_for_unit(unit, 0.0, 0.0)

    movable_units = [unit for unit in ordered_units if unit.movable]
    shelf_width = (
        shelf_width_override
        if shelf_width_override is not None
        else _constructive_shelf_width(movable_units, compact)
    )
    x_origin, y_origin = _fallback_shelf_origin(context.immutable)
    x_cursor = x_origin
    y_cursor = y_origin
    row_height = 0.0

    for unit in movable_units:
        width = unit.bbox_width if math.isfinite(unit.bbox_width) and unit.bbox_width > 0.0 else 1.0
        height = unit.bbox_height if math.isfinite(unit.bbox_height) and unit.bbox_height > 0.0 else 1.0

        if (
            shelf_width is not None
            and row_height > 0.0
            and x_cursor > x_origin
            and x_cursor + width > x_origin + shelf_width + OVERLAP_TOLERANCE
        ):
            x_cursor = x_origin
            y_cursor += row_height
            row_height = 0.0

        origins[unit.unit_id] = _constructive_origin_for_unit(unit, x_cursor, y_cursor)
        x_cursor += width
        row_height = max(row_height, height)

    expanded = _expand_units(unit_set, origins)
    candidate = _candidate_from_expanded(
        context.parsed,
        expanded,
        source,
        source_order,
    )
    if candidate is None:
        return None

    report = _preflight(candidate, context.parsed, context.immutable, context.dimensions)
    candidate.hard_report = report
    if not report.hard_feasible:
        return None
    return candidate


def _valid_unit_width(unit: PlacementUnit) -> float:
    width = unit.bbox_width
    return width if math.isfinite(width) and width > 0.0 else 1.0


def _valid_unit_height(unit: PlacementUnit) -> float:
    height = unit.bbox_height
    return height if math.isfinite(height) and height > 0.0 else 1.0


def _pack_shelf_origins(
    units: Sequence[PlacementUnit],
    x_origin: float,
    y_origin: float,
    shelf_width: Optional[float],
) -> Tuple[Dict[str, Tuple[float, float]], float, float]:
    origins: Dict[str, Tuple[float, float]] = {}
    x_cursor = x_origin
    y_cursor = y_origin
    row_height = 0.0
    max_x = x_origin
    max_y = y_origin

    for unit in units:
        width = _valid_unit_width(unit)
        height = _valid_unit_height(unit)
        if (
            shelf_width is not None
            and row_height > 0.0
            and x_cursor > x_origin
            and x_cursor + width > x_origin + shelf_width + OVERLAP_TOLERANCE
        ):
            x_cursor = x_origin
            y_cursor += row_height
            row_height = 0.0

        origins[unit.unit_id] = (x_cursor, y_cursor)
        x_cursor += width
        row_height = max(row_height, height)
        max_x = max(max_x, x_cursor)
        max_y = max(max_y, y_cursor + height)

    return origins, max_x - x_origin, max_y - y_origin


def _bottom_left_x_positions(
    placed: Sequence[Rect],
    target_width: float,
    width: float,
) -> List[float]:
    x_limit = max(0.0, target_width - width)
    candidates = {0.0, x_limit}
    for x, _, placed_width, _ in placed:
        candidates.add(x)
        candidates.add(x + placed_width)
    return sorted(
        x
        for x in candidates
        if -OVERLAP_TOLERANCE <= x <= x_limit + OVERLAP_TOLERANCE
    )


def _bottom_left_y_at_x(
    x: float,
    width: float,
    height: float,
    placed: Sequence[Rect],
) -> float:
    y = 0.0
    while True:
        next_y = y
        for placed_x, placed_y, placed_width, placed_height in placed:
            horizontally_overlaps = (
                x < placed_x + placed_width - OVERLAP_TOLERANCE
                and x + width > placed_x + OVERLAP_TOLERANCE
            )
            vertically_overlaps = (
                y < placed_y + placed_height - OVERLAP_TOLERANCE
                and y + height > placed_y + OVERLAP_TOLERANCE
            )
            if horizontally_overlaps and vertically_overlaps:
                next_y = max(next_y, placed_y + placed_height)
        if next_y <= y + OVERLAP_TOLERANCE:
            return y
        y = next_y


def _skyline_unit_order(units: Sequence[PlacementUnit]) -> List[PlacementUnit]:
    return sorted(
        units,
        key=lambda unit: (
            -_valid_unit_height(unit),
            -_valid_unit_width(unit),
            -_unit_area(unit),
            _unit_min_block_id(unit),
            unit.unit_id,
        ),
    )


def _pack_bottom_left_origins(
    units: Sequence[PlacementUnit],
    target_width: float,
) -> Tuple[Dict[str, Tuple[float, float]], float, float]:
    origins: Dict[str, Tuple[float, float]] = {}
    if not units:
        return origins, 0.0, 0.0

    target_width = max(target_width, _max_unit_width(units), 1.0)
    placed: List[Rect] = []
    max_x = 0.0
    max_y = 0.0

    for unit in _skyline_unit_order(units):
        width = _valid_unit_width(unit)
        height = _valid_unit_height(unit)
        best_origin: Optional[Tuple[float, float]] = None
        best_key: Optional[Tuple[float, float, float, float, int, str]] = None

        for x in _bottom_left_x_positions(placed, target_width, width):
            y = _bottom_left_y_at_x(x, width, height, placed)
            key = (
                y + height,
                y,
                max(max_x, x + width),
                x,
                _unit_min_block_id(unit),
                unit.unit_id,
            )
            if best_key is None or key < best_key:
                best_key = key
                best_origin = (x, y)

        if best_origin is None:
            best_origin = (0.0, max_y)

        x, y = best_origin
        origins[unit.unit_id] = best_origin
        placed.append((x, y, width, height))
        max_x = max(max_x, x + width)
        max_y = max(max_y, y + height)

    return origins, max_x, max_y


def _candidate_from_origins(
    context: SolverContext,
    unit_set: PlacementUnitSet,
    origins: Dict[str, Tuple[float, float]],
    source: str,
    source_order: int,
) -> Optional[Candidate]:
    expanded = _expand_units(unit_set, origins)
    candidate = _candidate_from_expanded(
        context.parsed,
        expanded,
        source,
        source_order,
    )
    if candidate is None:
        return None

    report = _preflight(candidate, context.parsed, context.immutable, context.dimensions)
    candidate.hard_report = report
    if not report.hard_feasible:
        return None
    return candidate


def _best_constructive_candidate(candidates: Sequence[Candidate], parsed: ParsedInput) -> Optional[Candidate]:
    best: Optional[Candidate] = None
    best_key: Optional[Tuple[float, float, float, int]] = None
    for candidate in candidates:
        if candidate.proxy_score is None:
            candidate.proxy_score = _score_candidate(candidate, parsed)
        key = CandidateManager._candidate_key(candidate)
        if best_key is None or key < best_key:
            best_key = key
            best = candidate
    return best


def _boundary_frame_bucket(unit: PlacementUnit) -> str:
    mask = unit.boundary_intent
    if not mask:
        return "interior"

    wants_left = bool(mask & 1)
    wants_right = bool(mask & 2)
    wants_top = bool(mask & 4)
    wants_bottom = bool(mask & 8)

    if (wants_left or wants_right) and (wants_top or wants_bottom):
        horizontal = "left" if wants_left else "right"
        vertical = "bottom" if wants_bottom else "top"
        return f"{vertical}_{horizontal}"
    if wants_left:
        return "left"
    if wants_right:
        return "right"
    if wants_bottom:
        return "bottom"
    if wants_top:
        return "top"
    return "interior"


def _boundary_frame_groups(
    ordered_units: Sequence[PlacementUnit],
) -> Dict[str, List[PlacementUnit]]:
    groups: Dict[str, List[PlacementUnit]] = {
        "top_left": [],
        "top_right": [],
        "bottom_left": [],
        "bottom_right": [],
        "left": [],
        "right": [],
        "top": [],
        "bottom": [],
        "interior": [],
    }
    for unit in ordered_units:
        if not unit.movable:
            continue
        groups[_boundary_frame_bucket(unit)].append(unit)

    # Only one rectangle can satisfy the same exact corner without overlap.
    # Extra corner requests keep one requested side and remain score-visible.
    corner_extras = {
        "top_left": "left",
        "bottom_left": "left",
        "top_right": "right",
        "bottom_right": "right",
    }
    for corner, side in corner_extras.items():
        if len(groups[corner]) <= 1:
            continue
        groups[side].extend(groups[corner][1:])
        del groups[corner][1:]
    return groups


def _sum_unit_widths(units: Sequence[PlacementUnit]) -> float:
    return sum(_valid_unit_width(unit) for unit in units)


def _sum_unit_heights(units: Sequence[PlacementUnit]) -> float:
    return sum(_valid_unit_height(unit) for unit in units)


def _max_unit_width(units: Sequence[PlacementUnit]) -> float:
    return max((_valid_unit_width(unit) for unit in units), default=0.0)


def _max_unit_height(units: Sequence[PlacementUnit]) -> float:
    return max((_valid_unit_height(unit) for unit in units), default=0.0)


def _boundary_frame_x_origin(
    context: SolverContext,
    frame_width: float,
    movable_units: Sequence[PlacementUnit],
) -> float:
    if not context.immutable.obstacle_rects:
        return 0.0

    left_requests = sum(1 for unit in movable_units if unit.boundary_intent & 1)
    right_requests = sum(1 for unit in movable_units if unit.boundary_intent & 2)
    if left_requests > right_requests:
        min_x = min(x for _, (x, _, _, _) in context.immutable.obstacle_rects)
        return min(0.0, min_x) - frame_width - FALLBACK_OBSTACLE_GAP
    max_x = max(x + w for _, (x, _, w, _) in context.immutable.obstacle_rects)
    return max(0.0, max_x + FALLBACK_OBSTACLE_GAP)


def _boundary_frame_y_origin_and_height(
    context: SolverContext,
    frame_height: float,
) -> Tuple[float, float]:
    if not context.immutable.obstacle_rects:
        return 0.0, frame_height

    min_y = min(y for _, (_, y, _, _) in context.immutable.obstacle_rects)
    max_y = max(y + h for _, (_, y, _, h) in context.immutable.obstacle_rects)
    y_origin = min(0.0, min_y)
    return y_origin, max(frame_height, max_y - y_origin)


def _pack_boundary_frame_candidate(
    context: SolverContext,
    unit_set: PlacementUnitSet,
    ordered_units: Sequence[PlacementUnit],
    source: str,
    source_order: int,
) -> Optional[Candidate]:
    movable_units = [unit for unit in ordered_units if unit.movable]
    if not any(unit.boundary_intent for unit in movable_units):
        return _pack_units_as_candidate(
            context,
            unit_set,
            ordered_units,
            source,
            source_order,
            True,
        )

    groups = _boundary_frame_groups(ordered_units)
    corners = {
        name: values[0] if values else None
        for name, values in (
            ("top_left", groups["top_left"]),
            ("top_right", groups["top_right"]),
            ("bottom_left", groups["bottom_left"]),
            ("bottom_right", groups["bottom_right"]),
        )
    }
    left_column_units = groups["left"]
    right_column_units = groups["right"]
    top_row_units = groups["top"]
    bottom_row_units = groups["bottom"]
    interior_units = groups["interior"]

    left_width = max(
        _max_unit_width(left_column_units),
        _valid_unit_width(corners["top_left"]) if corners["top_left"] else 0.0,
        _valid_unit_width(corners["bottom_left"]) if corners["bottom_left"] else 0.0,
    )
    right_width = max(
        _max_unit_width(right_column_units),
        _valid_unit_width(corners["top_right"]) if corners["top_right"] else 0.0,
        _valid_unit_width(corners["bottom_right"]) if corners["bottom_right"] else 0.0,
    )
    top_height = _max_unit_height(top_row_units)
    bottom_height = _max_unit_height(bottom_row_units)

    interior_width_hint = _shelf_width_for_units(
        interior_units,
        CONSTRUCTIVE_SHELF_ASPECT,
    )
    rail_central_width = max(
        _sum_unit_widths(top_row_units),
        _sum_unit_widths(bottom_row_units),
    )
    central_width = max(interior_width_hint or 0.0, rail_central_width)
    if interior_units and central_width <= 0.0:
        central_width = _max_unit_width(interior_units)

    relative_interior_origins, interior_width, interior_height = _pack_shelf_origins(
        interior_units,
        0.0,
        0.0,
        central_width if central_width > 0.0 else None,
    )
    central_width = max(rail_central_width, interior_width)

    central_column_height = bottom_height + interior_height + top_height
    left_column_height = (
        (_valid_unit_height(corners["bottom_left"]) if corners["bottom_left"] else 0.0)
        + _sum_unit_heights(left_column_units)
        + (_valid_unit_height(corners["top_left"]) if corners["top_left"] else 0.0)
    )
    right_column_height = (
        (_valid_unit_height(corners["bottom_right"]) if corners["bottom_right"] else 0.0)
        + _sum_unit_heights(right_column_units)
        + (_valid_unit_height(corners["top_right"]) if corners["top_right"] else 0.0)
    )

    frame_width = max(left_width + central_width + right_width, 1.0)
    frame_height = max(central_column_height, left_column_height, right_column_height, 1.0)
    frame_x = _boundary_frame_x_origin(context, frame_width, movable_units)
    frame_y, frame_height = _boundary_frame_y_origin_and_height(context, frame_height)

    origins: Dict[str, Tuple[float, float]] = {}
    for unit in ordered_units:
        if not unit.movable:
            origins[unit.unit_id] = _constructive_origin_for_unit(unit, 0.0, 0.0)

    central_x = frame_x + left_width
    for unit_id, (local_x, local_y) in relative_interior_origins.items():
        origins[unit_id] = (central_x + local_x, frame_y + bottom_height + local_y)

    x_cursor = central_x
    for unit in bottom_row_units:
        origins[unit.unit_id] = (x_cursor, frame_y)
        x_cursor += _valid_unit_width(unit)

    x_cursor = central_x
    for unit in top_row_units:
        origins[unit.unit_id] = (
            x_cursor,
            frame_y + frame_height - _valid_unit_height(unit),
        )
        x_cursor += _valid_unit_width(unit)

    y_cursor = frame_y + (
        _valid_unit_height(corners["bottom_left"])
        if corners["bottom_left"] else 0.0
    )
    for unit in left_column_units:
        origins[unit.unit_id] = (frame_x, y_cursor)
        y_cursor += _valid_unit_height(unit)

    y_cursor = frame_y + (
        _valid_unit_height(corners["bottom_right"])
        if corners["bottom_right"] else 0.0
    )
    for unit in right_column_units:
        origins[unit.unit_id] = (
            frame_x + frame_width - _valid_unit_width(unit),
            y_cursor,
        )
        y_cursor += _valid_unit_height(unit)

    if corners["bottom_left"] is not None:
        origins[corners["bottom_left"].unit_id] = (frame_x, frame_y)
    if corners["bottom_right"] is not None:
        unit = corners["bottom_right"]
        origins[unit.unit_id] = (frame_x + frame_width - _valid_unit_width(unit), frame_y)
    if corners["top_left"] is not None:
        unit = corners["top_left"]
        origins[unit.unit_id] = (frame_x, frame_y + frame_height - _valid_unit_height(unit))
    if corners["top_right"] is not None:
        unit = corners["top_right"]
        origins[unit.unit_id] = (
            frame_x + frame_width - _valid_unit_width(unit),
            frame_y + frame_height - _valid_unit_height(unit),
        )

    expanded = _expand_units(unit_set, origins)
    candidate = _candidate_from_expanded(
        context.parsed,
        expanded,
        source,
        source_order,
    )
    if candidate is None:
        return None

    report = _preflight(candidate, context.parsed, context.immutable, context.dimensions)
    candidate.hard_report = report
    if not report.hard_feasible:
        return None
    return candidate


def _skyline_width_hints(
    units: Sequence[PlacementUnit],
    minimum_width: float,
) -> List[float]:
    if not units:
        return [max(0.0, minimum_width)]

    hints = {max(minimum_width, _max_unit_width(units))}
    for aspect in BOUNDARY_SKYLINE_ASPECTS:
        width = _shelf_width_for_units(units, aspect)
        if width is not None and math.isfinite(width) and width > 0.0:
            hints.add(max(minimum_width, width))
    return sorted(hints)


def _pack_skyline_units_as_candidate(
    context: SolverContext,
    unit_set: PlacementUnitSet,
    ordered_units: Sequence[PlacementUnit],
    source: str,
    source_order: int,
) -> Optional[Candidate]:
    fixed_origins = {
        unit.unit_id: _constructive_origin_for_unit(unit, 0.0, 0.0)
        for unit in ordered_units
        if not unit.movable
    }
    movable_units = [unit for unit in ordered_units if unit.movable]
    if not movable_units:
        return _candidate_from_origins(
            context,
            unit_set,
            fixed_origins,
            source,
            source_order,
        )

    candidates: List[Candidate] = []
    x_origin, y_origin = _fallback_shelf_origin(context.immutable)
    for variant_index, target_width in enumerate(_skyline_width_hints(movable_units, 0.0)):
        relative_origins, _, _ = _pack_bottom_left_origins(movable_units, target_width)
        origins = dict(fixed_origins)
        for unit_id, (local_x, local_y) in relative_origins.items():
            origins[unit_id] = (x_origin + local_x, y_origin + local_y)
        candidate = _candidate_from_origins(
            context,
            unit_set,
            origins,
            f"{source}:{variant_index}",
            source_order,
        )
        if candidate is not None:
            candidates.append(candidate)

    return _best_constructive_candidate(candidates, context.parsed)


def _pack_boundary_skyline_candidate(
    context: SolverContext,
    unit_set: PlacementUnitSet,
    ordered_units: Sequence[PlacementUnit],
    source: str,
    source_order: int,
) -> Optional[Candidate]:
    movable_units = [unit for unit in ordered_units if unit.movable]
    if not any(unit.boundary_intent for unit in movable_units):
        return _pack_skyline_units_as_candidate(
            context,
            unit_set,
            ordered_units,
            source,
            source_order,
        )

    groups = _boundary_frame_groups(ordered_units)
    corners = {
        name: values[0] if values else None
        for name, values in (
            ("top_left", groups["top_left"]),
            ("top_right", groups["top_right"]),
            ("bottom_left", groups["bottom_left"]),
            ("bottom_right", groups["bottom_right"]),
        )
    }
    left_column_units = groups["left"]
    right_column_units = groups["right"]
    top_row_units = groups["top"]
    bottom_row_units = groups["bottom"]
    interior_units = groups["interior"]

    left_width = max(
        _max_unit_width(left_column_units),
        _valid_unit_width(corners["top_left"]) if corners["top_left"] else 0.0,
        _valid_unit_width(corners["bottom_left"]) if corners["bottom_left"] else 0.0,
    )
    right_width = max(
        _max_unit_width(right_column_units),
        _valid_unit_width(corners["top_right"]) if corners["top_right"] else 0.0,
        _valid_unit_width(corners["bottom_right"]) if corners["bottom_right"] else 0.0,
    )
    top_height = _max_unit_height(top_row_units)
    bottom_height = _max_unit_height(bottom_row_units)
    rail_central_width = max(
        _sum_unit_widths(top_row_units),
        _sum_unit_widths(bottom_row_units),
    )

    candidates: List[Candidate] = []
    for variant_index, central_width_hint in enumerate(
        _skyline_width_hints(interior_units, rail_central_width)
    ):
        relative_interior_origins, interior_width, interior_height = _pack_bottom_left_origins(
            interior_units,
            central_width_hint,
        )
        central_width = max(rail_central_width, interior_width, central_width_hint)
        central_column_height = bottom_height + interior_height + top_height
        left_column_height = (
            (_valid_unit_height(corners["bottom_left"]) if corners["bottom_left"] else 0.0)
            + _sum_unit_heights(left_column_units)
            + (_valid_unit_height(corners["top_left"]) if corners["top_left"] else 0.0)
        )
        right_column_height = (
            (_valid_unit_height(corners["bottom_right"]) if corners["bottom_right"] else 0.0)
            + _sum_unit_heights(right_column_units)
            + (_valid_unit_height(corners["top_right"]) if corners["top_right"] else 0.0)
        )

        frame_width = max(left_width + central_width + right_width, 1.0)
        frame_height = max(central_column_height, left_column_height, right_column_height, 1.0)
        frame_x = _boundary_frame_x_origin(context, frame_width, movable_units)
        frame_y, frame_height = _boundary_frame_y_origin_and_height(context, frame_height)

        origins: Dict[str, Tuple[float, float]] = {}
        for unit in ordered_units:
            if not unit.movable:
                origins[unit.unit_id] = _constructive_origin_for_unit(unit, 0.0, 0.0)

        central_x = frame_x + left_width
        for unit_id, (local_x, local_y) in relative_interior_origins.items():
            origins[unit_id] = (central_x + local_x, frame_y + bottom_height + local_y)

        x_cursor = central_x
        for unit in bottom_row_units:
            origins[unit.unit_id] = (x_cursor, frame_y)
            x_cursor += _valid_unit_width(unit)

        x_cursor = central_x
        for unit in top_row_units:
            origins[unit.unit_id] = (
                x_cursor,
                frame_y + frame_height - _valid_unit_height(unit),
            )
            x_cursor += _valid_unit_width(unit)

        y_cursor = frame_y + (
            _valid_unit_height(corners["bottom_left"])
            if corners["bottom_left"] else 0.0
        )
        for unit in left_column_units:
            origins[unit.unit_id] = (frame_x, y_cursor)
            y_cursor += _valid_unit_height(unit)

        y_cursor = frame_y + (
            _valid_unit_height(corners["bottom_right"])
            if corners["bottom_right"] else 0.0
        )
        for unit in right_column_units:
            origins[unit.unit_id] = (
                frame_x + frame_width - _valid_unit_width(unit),
                y_cursor,
            )
            y_cursor += _valid_unit_height(unit)

        if corners["bottom_left"] is not None:
            origins[corners["bottom_left"].unit_id] = (frame_x, frame_y)
        if corners["bottom_right"] is not None:
            unit = corners["bottom_right"]
            origins[unit.unit_id] = (frame_x + frame_width - _valid_unit_width(unit), frame_y)
        if corners["top_left"] is not None:
            unit = corners["top_left"]
            origins[unit.unit_id] = (frame_x, frame_y + frame_height - _valid_unit_height(unit))
        if corners["top_right"] is not None:
            unit = corners["top_right"]
            origins[unit.unit_id] = (
                frame_x + frame_width - _valid_unit_width(unit),
                frame_y + frame_height - _valid_unit_height(unit),
            )

        candidate = _candidate_from_origins(
            context,
            unit_set,
            origins,
            f"{source}:{variant_index}",
            source_order,
        )
        if candidate is not None:
            candidates.append(candidate)

    return _best_constructive_candidate(candidates, context.parsed)


def _pack_constructive_seed(
    context: SolverContext,
    unit_set: PlacementUnitSet,
    seed_name: str,
    ordered_units: Sequence[PlacementUnit],
    compact: bool,
    source_order: int,
) -> Optional[Candidate]:
    if seed_name == "boundary_frame":
        return _pack_boundary_frame_candidate(
            context,
            unit_set,
            ordered_units,
            f"constructive:{seed_name}",
            source_order,
        )
    if seed_name == "boundary_skyline":
        return _pack_boundary_skyline_candidate(
            context,
            unit_set,
            ordered_units,
            f"constructive:{seed_name}",
            source_order,
        )
    return _pack_units_as_candidate(
        context,
        unit_set,
        ordered_units,
        f"constructive:{seed_name}",
        source_order,
        compact,
    )


def _construct_candidates(context: SolverContext, units: PlacementUnitSet) -> Iterable[Candidate]:
    for seed_index, (seed_name, ordered_units, compact) in enumerate(
        _constructive_seed_orders(context, units)
    ):
        candidate = _pack_constructive_seed(
            context,
            units,
            seed_name,
            ordered_units,
            compact,
            CONSTRUCTIVE_SOURCE_BASE + seed_index,
        )
        if candidate is not None:
            yield candidate


def _local_search_budget(block_count: int) -> LocalSearchBudget:
    if block_count <= 1:
        return LocalSearchBudget(0, 0, 0, 0, 0, 0, 0, 0)
    if block_count <= 21:
        return LocalSearchBudget(20, 4, 4, 2, 4, 3, 2, 1)
    if block_count <= 60:
        return LocalSearchBudget(25, 5, 5, 3, 4, 3, 3, 2)
    if block_count <= 100:
        return LocalSearchBudget(29, 7, 7, 3, 4, 4, 3, 3)
    return LocalSearchBudget(32, 8, 8, 4, 4, 4, 3, 3)


def _unit_origin_from_candidate(unit: PlacementUnit, candidate: Candidate) -> Tuple[float, float]:
    if not unit.movable and unit.fixed_origin is not None:
        return unit.fixed_origin
    for block_id in sorted(unit.block_ids):
        if block_id >= len(candidate.positions) or block_id not in unit.local_rects:
            continue
        local_x, local_y, _, _ = unit.local_rects[block_id]
        x, y, _, _ = candidate.positions[block_id]
        return x - local_x, y - local_y
    return 0.0, 0.0


def _unit_order_from_candidate(
    unit_set: PlacementUnitSet,
    candidate: Candidate,
) -> List[PlacementUnit]:
    return sorted(
        unit_set.units,
        key=lambda unit: (
            0 if not unit.movable else 1,
            round(_unit_origin_from_candidate(unit, candidate)[1], 6),
            round(_unit_origin_from_candidate(unit, candidate)[0], 6),
            _unit_min_block_id(unit),
            unit.unit_id,
        ),
    )


def _repair_immutable_geometry(
    positions: Sequence[Rect],
    context: SolverContext,
) -> List[Rect]:
    repaired: List[Rect] = []
    for block_id in range(context.parsed.n):
        if block_id < len(positions):
            x, y, w, h = positions[block_id]
            rect = (
                _as_float(x),
                _as_float(y),
                _as_float(w, context.dimensions.widths[block_id]),
                _as_float(h, context.dimensions.heights[block_id]),
            )
        else:
            rect = (
                0.0,
                0.0,
                context.dimensions.widths[block_id],
                context.dimensions.heights[block_id],
            )

        x, y, w, h = rect
        if not math.isfinite(x):
            x = 0.0
        if not math.isfinite(y):
            y = 0.0
        if not math.isfinite(w) or w <= 0.0:
            w = context.dimensions.widths[block_id]
        if not math.isfinite(h) or h <= 0.0:
            h = context.dimensions.heights[block_id]

        if block_id in context.immutable.preplaced_rects:
            repaired.append(context.immutable.preplaced_rects[block_id])
        elif block_id in context.immutable.fixed_dims:
            target_w, target_h = context.immutable.fixed_dims[block_id]
            repaired.append((x, y, target_w, target_h))
        else:
            repaired.append((x, y, w, h))
    return repaired


def _repair_area_and_mib_dimensions(
    positions: Sequence[Rect],
    context: SolverContext,
) -> List[Rect]:
    repaired = list(positions)
    parsed = context.parsed

    for block_id, (x, y, w, h) in enumerate(repaired):
        if block_id in parsed.fixed_or_preplaced_ids:
            continue
        target_area = parsed.areas[block_id]
        if not _shape_matches_area(w, h, target_area):
            repaired[block_id] = (
                x,
                y,
                context.dimensions.widths[block_id],
                context.dimensions.heights[block_id],
            )

    for group_id, members in parsed.mib_groups.items():
        if context.dimensions.mib_notes.get(group_id) not in {
            "synchronized",
            "synchronized-immutable",
        }:
            continue
        for block_id in members:
            if 0 <= block_id < parsed.n and block_id not in parsed.fixed_or_preplaced_ids:
                x, y, _, _ = repaired[block_id]
                repaired[block_id] = (
                    x,
                    y,
                    context.dimensions.widths[block_id],
                    context.dimensions.heights[block_id],
                )
    return repaired


def _repair_candidate_positions(
    positions: Sequence[Rect],
    context: SolverContext,
) -> List[Rect]:
    repaired = _repair_immutable_geometry(positions, context)
    repaired = _repair_area_and_mib_dimensions(repaired, context)
    repaired = _repair_immutable_geometry(repaired, context)
    return repaired


def _candidate_from_repaired_positions(
    context: SolverContext,
    positions: Sequence[Rect],
    source: str,
    source_order: int,
) -> Optional[Candidate]:
    candidate = Candidate(
        _repair_candidate_positions(positions, context),
        source,
        source_order,
    )
    report = _preflight(candidate, context.parsed, context.immutable, context.dimensions)
    candidate.hard_report = report
    if not report.hard_feasible:
        return None
    return candidate


def _unit_with_shape_overrides(
    unit: PlacementUnit,
    shape_overrides: Dict[int, Tuple[float, float]],
) -> PlacementUnit:
    if not any(block_id in shape_overrides for block_id in unit.block_ids):
        return unit

    local_rects: Dict[int, Rect] = {}
    x_cursor = 0.0
    bbox_width = 0.0
    bbox_height = 0.0
    ordered_blocks = sorted(
        unit.block_ids,
        key=lambda block_id: (
            unit.local_rects.get(block_id, (0.0, 0.0, 0.0, 0.0))[0],
            block_id,
        ),
    )

    for block_id in ordered_blocks:
        local_x, local_y, width, height = unit.local_rects[block_id]
        del local_x, local_y
        width, height = shape_overrides.get(block_id, (width, height))
        if unit.kind == "cluster_macro":
            local_rects[block_id] = (x_cursor, 0.0, width, height)
            x_cursor += width
            bbox_width = x_cursor
        else:
            local_rects[block_id] = (0.0, 0.0, width, height)
            bbox_width = max(bbox_width, width)
        bbox_height = max(bbox_height, height)

    return PlacementUnit(
        unit_id=unit.unit_id,
        kind=unit.kind,
        block_ids=unit.block_ids,
        local_rects=local_rects,
        bbox_width=bbox_width,
        bbox_height=bbox_height,
        movable=unit.movable,
        boundary_intent=unit.boundary_intent,
        soft_links=unit.soft_links,
        fixed_origin=unit.fixed_origin,
    )


def _unit_set_with_shape_overrides(
    unit_set: PlacementUnitSet,
    shape_overrides: Dict[int, Tuple[float, float]],
) -> PlacementUnitSet:
    if not shape_overrides:
        return unit_set

    updated_units = [
        _unit_with_shape_overrides(unit, shape_overrides)
        for unit in unit_set.units
    ]
    by_id = {unit.unit_id: unit for unit in updated_units}
    updated_group_macros = {
        cluster_id: by_id[macro.unit_id]
        for cluster_id, macro in unit_set.group_macros.items()
        if macro.unit_id in by_id
    }
    return PlacementUnitSet(
        units=updated_units,
        group_macros=updated_group_macros,
        mib_metadata=unit_set.mib_metadata,
        boundary_intents=unit_set.boundary_intents,
        block_to_unit=unit_set.block_to_unit,
        diagnostics=unit_set.diagnostics,
    )


def _pack_local_with_overrides(
    context: SolverContext,
    unit_set: PlacementUnitSet,
    ordered_units: Sequence[PlacementUnit],
    shape_overrides: Dict[int, Tuple[float, float]],
    source: str,
    source_order: int,
    compact: bool = True,
    shelf_width_override: Optional[float] = None,
) -> Optional[Candidate]:
    working_set = _unit_set_with_shape_overrides(unit_set, shape_overrides)
    working_by_id = {unit.unit_id: unit for unit in working_set.units}
    working_order = [
        working_by_id[unit.unit_id]
        for unit in ordered_units
        if unit.unit_id in working_by_id
    ]
    return _pack_units_as_candidate(
        context,
        working_set,
        working_order,
        source,
        source_order,
        compact,
        shelf_width_override,
    )


def _local_search_swap_trials(
    context: SolverContext,
    unit_set: PlacementUnitSet,
    ordered_units: Sequence[PlacementUnit],
    budget: LocalSearchBudget,
    next_source_order: int,
) -> Iterable[Candidate]:
    movable_indices = [
        idx for idx, unit in enumerate(ordered_units)
        if unit.movable
    ]
    trial_count = 0
    for left, right in zip(movable_indices, movable_indices[1:]):
        if trial_count >= budget.swap_trials:
            break
        swapped = list(ordered_units)
        swapped[left], swapped[right] = swapped[right], swapped[left]
        source = f"local:swap:{ordered_units[left].unit_id}:{ordered_units[right].unit_id}"
        candidate = _pack_local_with_overrides(
            context,
            unit_set,
            swapped,
            {},
            source,
            next_source_order + trial_count,
        )
        if candidate is not None:
            trial_count += 1
            yield candidate


def _local_search_relocation_trials(
    context: SolverContext,
    unit_set: PlacementUnitSet,
    ordered_units: Sequence[PlacementUnit],
    budget: LocalSearchBudget,
    next_source_order: int,
) -> Iterable[Candidate]:
    movable_indices = [
        idx for idx, unit in enumerate(ordered_units)
        if unit.movable
    ]
    trial_count = 0
    for idx in movable_indices:
        if trial_count >= budget.relocation_trials:
            break
        relocated = list(ordered_units)
        unit = relocated.pop(idx)
        first_movable = next(
            (pos for pos, current in enumerate(relocated) if current.movable),
            len(relocated),
        )
        relocated.insert(first_movable, unit)
        source = f"local:relocate:{unit.unit_id}:front"
        candidate = _pack_local_with_overrides(
            context,
            unit_set,
            relocated,
            {},
            source,
            next_source_order + trial_count,
        )
        if candidate is not None:
            trial_count += 1
            yield candidate


def _local_search_shelf_width_trials(
    context: SolverContext,
    unit_set: PlacementUnitSet,
    ordered_units: Sequence[PlacementUnit],
    budget: LocalSearchBudget,
    next_source_order: int,
) -> Iterable[Candidate]:
    movable_units = [unit for unit in ordered_units if unit.movable]
    if len(movable_units) <= 2:
        return

    trial_count = 0
    seen_widths = set()
    for aspect in (1.0, 1.25, 1.75, 2.25):
        if trial_count >= budget.shelf_width_trials:
            break
        shelf_width = _shelf_width_for_units(movable_units, aspect)
        if shelf_width is None:
            continue
        width_key = round(shelf_width, 6)
        if width_key in seen_widths:
            continue
        seen_widths.add(width_key)
        candidate = _pack_local_with_overrides(
            context,
            unit_set,
            ordered_units,
            {},
            f"local:shelf_width:{aspect:g}",
            next_source_order + trial_count,
            True,
            shelf_width,
        )
        if candidate is not None:
            trial_count += 1
            yield candidate


def _eligible_aspect_update_blocks(
    context: SolverContext,
    unit_set: PlacementUnitSet,
) -> List[int]:
    mib_blocks = {
        block_id
        for members in context.parsed.mib_groups.values()
        for block_id in members
    }
    result: List[int] = []
    unit_by_id = {unit.unit_id: unit for unit in unit_set.units}
    for block_id in range(context.parsed.n):
        unit_id = unit_set.block_to_unit.get(block_id)
        unit = unit_by_id.get(unit_id or "")
        if unit is None:
            continue
        if block_id in context.parsed.fixed_or_preplaced_ids:
            continue
        if block_id in context.parsed.invalid_area_ids or block_id in mib_blocks:
            continue
        if unit.kind != "block":
            continue
        result.append(block_id)
    return result


def _aspect_shape_for_area(area: float, ratio: float = LOCAL_SEARCH_ASPECT_RATIO) -> Optional[Tuple[float, float]]:
    if not math.isfinite(area) or area <= 0.0 or ratio <= 0.0:
        return None
    side = math.sqrt(area)
    width = side * ratio
    height = area / width
    if _shape_matches_area(width, height, area):
        return width, height
    return None


def _local_search_aspect_trials(
    context: SolverContext,
    unit_set: PlacementUnitSet,
    ordered_units: Sequence[PlacementUnit],
    budget: LocalSearchBudget,
    next_source_order: int,
) -> Iterable[Candidate]:
    trial_count = 0
    for block_id in _eligible_aspect_update_blocks(context, unit_set):
        if trial_count >= budget.aspect_trials:
            break
        shape = _aspect_shape_for_area(context.parsed.areas[block_id])
        if shape is None:
            continue
        candidate = _pack_local_with_overrides(
            context,
            unit_set,
            ordered_units,
            {block_id: shape},
            f"local:aspect:{block_id}",
            next_source_order + trial_count,
        )
        if candidate is not None:
            trial_count += 1
            yield candidate


def _local_search_mib_sync_trials(
    context: SolverContext,
    unit_set: PlacementUnitSet,
    ordered_units: Sequence[PlacementUnit],
    budget: LocalSearchBudget,
    next_source_order: int,
) -> Iterable[Candidate]:
    trial_count = 0
    for group_id, members in sorted(context.parsed.mib_groups.items()):
        if trial_count >= budget.mib_sync_trials:
            break
        if context.dimensions.mib_notes.get(group_id) not in {
            "synchronized",
            "synchronized-immutable",
        }:
            continue
        overrides: Dict[int, Tuple[float, float]] = {}
        for block_id in members:
            if 0 <= block_id < context.parsed.n and block_id not in context.parsed.fixed_or_preplaced_ids:
                overrides[block_id] = (
                    context.dimensions.widths[block_id],
                    context.dimensions.heights[block_id],
                )
        if not overrides:
            continue
        candidate = _pack_local_with_overrides(
            context,
            unit_set,
            ordered_units,
            overrides,
            f"local:mib_sync:{group_id}",
            next_source_order + trial_count,
        )
        if candidate is not None:
            trial_count += 1
            yield candidate


def _compact_candidate(
    context: SolverContext,
    candidate: Candidate,
    source: str,
    source_order: int,
) -> Optional[Candidate]:
    positions = _repair_candidate_positions(candidate.positions, context)
    compacted = list(positions)
    x_cursor, y_origin = _fallback_shelf_origin(context.immutable)
    movable_order = sorted(
        context.immutable.movable_ids,
        key=lambda block_id: (
            round(positions[block_id][1], 6),
            round(positions[block_id][0], 6),
            block_id,
        ),
    )

    for block_id in movable_order:
        _, _, width, height = compacted[block_id]
        compacted[block_id] = (x_cursor, y_origin, width, height)
        x_cursor += width

    return _candidate_from_repaired_positions(
        context,
        compacted,
        source,
        source_order,
    )


def _boundary_snapped_positions(
    context: SolverContext,
    positions: Sequence[Rect],
    expand_outside: bool,
) -> List[Rect]:
    x_min = min(x for x, _, _, _ in positions)
    y_min = min(y for _, y, _, _ in positions)
    x_max = max(x + w for x, _, w, _ in positions)
    y_max = max(y + h for _, y, _, h in positions)

    snapped = list(positions)
    for block_id, mask in sorted(context.parsed.boundary_masks.items()):
        if block_id in context.immutable.preplaced_rects or block_id >= len(snapped):
            continue
        x, y, width, height = snapped[block_id]

        if expand_outside:
            if mask & 1 and not mask & 2:
                x = x_min - width
            elif mask & 2 and not mask & 1:
                x = x_max
            elif mask & 2:
                x = x_max - width
            elif mask & 1:
                x = x_min

            if mask & 8 and not mask & 4:
                y = y_min - height
            elif mask & 4 and not mask & 8:
                y = y_max
            elif mask & 4:
                y = y_max - height
            elif mask & 8:
                y = y_min
        else:
            if mask & 1:
                x = x_min
            if mask & 2:
                x = x_max - width
            if mask & 8:
                y = y_min
            if mask & 4:
                y = y_max - height

        snapped[block_id] = (x, y, width, height)
    return snapped


def _snap_boundary_candidate(
    context: SolverContext,
    candidate: Candidate,
    source: str,
    source_order: int,
) -> Optional[Candidate]:
    if not context.parsed.boundary_masks:
        return None

    positions = _repair_candidate_positions(candidate.positions, context)
    inside = _candidate_from_repaired_positions(
        context,
        _boundary_snapped_positions(context, positions, False),
        source,
        source_order,
    )
    if inside is not None:
        return inside

    return _candidate_from_repaired_positions(
        context,
        _boundary_snapped_positions(context, positions, True),
        source,
        source_order,
    )


def _run_local_search(
    context: SolverContext,
    manager: CandidateManager,
    unit_set: Optional[PlacementUnitSet] = None,
) -> Iterable[Candidate]:
    budget = _local_search_budget(context.parsed.n)
    if budget.max_trials <= 0:
        return

    start = manager.best_feasible_or_fallback()
    if not start.positions:
        return

    if unit_set is None:
        unit_set = _plan_soft_units(context)
    ordered_units = _unit_order_from_candidate(unit_set, start)
    yielded = 0
    next_source_order = LOCAL_SEARCH_SOURCE_BASE

    families = [
        _local_search_swap_trials(
            context,
            unit_set,
            ordered_units,
            budget,
            next_source_order,
        ),
        _local_search_relocation_trials(
            context,
            unit_set,
            ordered_units,
            budget,
            next_source_order + 20,
        ),
        _local_search_shelf_width_trials(
            context,
            unit_set,
            ordered_units,
            budget,
            next_source_order + 40,
        ),
        _local_search_aspect_trials(
            context,
            unit_set,
            ordered_units,
            budget,
            next_source_order + 60,
        ),
        _local_search_mib_sync_trials(
            context,
            unit_set,
            ordered_units,
            budget,
            next_source_order + 80,
        ),
    ]

    for family in families:
        for candidate in family:
            if yielded >= budget.max_trials:
                return
            yielded += 1
            yield candidate

    if yielded < budget.max_trials and budget.compaction_trials > 0:
        compaction_source = manager.best_feasible_or_fallback()
        compacted = _compact_candidate(
            context,
            compaction_source,
            "local:compact",
            next_source_order + 100,
        )
        if compacted is not None:
            yielded += 1
            yield compacted

    if yielded < budget.max_trials and budget.boundary_trials > 0:
        boundary_source = manager.best_feasible_or_fallback()
        snapped = _snap_boundary_candidate(
            context,
            boundary_source,
            "local:boundary_snap",
            next_source_order + 110,
        )
        if snapped is not None:
            yield snapped


def _finalize_positions(candidate: Candidate, block_count: int) -> List[Rect]:
    result: List[Rect] = []
    for i in range(block_count):
        if i < len(candidate.positions):
            x, y, w, h = candidate.positions[i]
            rect = (_as_float(x), _as_float(y), _as_float(w, 1.0), _as_float(h, 1.0))
        else:
            rect = (float(i), 0.0, 1.0, 1.0)
        x, y, w, h = rect
        if not math.isfinite(w) or w <= 0.0:
            w = 1.0
        if not math.isfinite(h) or h <= 0.0:
            h = 1.0
        if not math.isfinite(x):
            x = 0.0
        if not math.isfinite(y):
            y = 0.0
        result.append((float(x), float(y), float(w), float(h)))
    return result


def _emergency_positions(block_count: int, area_targets: Any) -> List[Rect]:
    positions: List[Rect] = []
    x_cursor = 0.0
    for i in range(max(0, int(block_count))):
        area = _as_float(_row(area_targets, i), 1.0)
        if area <= 0.0:
            area = 1.0
        side = math.sqrt(area)
        positions.append((x_cursor, 0.0, side, side))
        x_cursor += side
    return positions


class MyOptimizer:
    """Contest-discoverable optimizer with a hard-feasible fallback path."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._debug_raise_quality_layer = False
        self.last_diagnostics: List[str] = []

    def solve(
        self,
        block_count: int,
        area_targets: Any,
        b2b_connectivity: Any,
        p2b_connectivity: Any,
        pins_pos: Any,
        constraints: Any,
        target_positions: Any = None,
    ) -> List[Rect]:
        """
        Return exactly one (x, y, width, height) tuple per active block.

        This entry path returns the best preflighted candidate from the
        fallback, constructive, and local-search layers.
        """
        self.last_diagnostics = []
        try:
            parsed = _parse_inputs(
                block_count,
                area_targets,
                b2b_connectivity,
                p2b_connectivity,
                pins_pos,
                constraints,
                target_positions,
            )
            immutable = _build_immutable_geometry(parsed)
            dimensions = _plan_dimensions(parsed, immutable)
            context = SolverContext(parsed, immutable, dimensions)

            manager = CandidateManager(context)
            fallback = _build_fallback(parsed, immutable, dimensions)
            manager.consider(fallback)

            try:
                if self._debug_raise_quality_layer:
                    raise RuntimeError("forced quality-layer failure")
                units = _plan_soft_units(context)
                for candidate in _construct_candidates(context, units):
                    manager.consider(candidate)
                for candidate in _run_local_search(context, manager, units):
                    manager.consider(candidate)
            except Exception as exc:
                self.last_diagnostics.append(f"quality layer failed: {exc}")

            best = manager.best_feasible_or_fallback()
            if best.hard_report is not None:
                self.last_diagnostics.extend(best.hard_report.messages)
            return _finalize_positions(best, parsed.n)
        except Exception as exc:
            self.last_diagnostics.append(f"entry failed: {exc}")
            return _emergency_positions(block_count, area_targets)


Optimizer = MyOptimizer
