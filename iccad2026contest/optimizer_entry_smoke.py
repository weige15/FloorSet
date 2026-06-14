#!/usr/bin/env python3
"""Smoke fixture for the FloorSet optimizer entry contract.

Run from the repository root with:

    python -B iccad2026contest/optimizer_entry_smoke.py
"""

import math
from typing import List, Sequence, Tuple

import my_optimizer
from my_optimizer import MyOptimizer


Rect = Tuple[float, float, float, float]


def _validator_dummy_inputs(target_positions=None):
    return {
        "block_count": 5,
        "area_targets": [100.0] * 5,
        "b2b_connectivity": [[0, 1, 1.0], [1, 2, 1.0], [-1, -1, -1.0]],
        "p2b_connectivity": [[0, 0, 1.0]],
        "pins_pos": [[0.0, 0.0]],
        "constraints": [[0.0] * 5 for _ in range(5)],
        "target_positions": target_positions,
    }


def _rects_overlap(first: Rect, second: Rect) -> bool:
    fx, fy, fw, fh = first
    sx, sy, sw, sh = second
    overlap_x = max(0.0, min(fx + fw, sx + sw) - max(fx, sx))
    overlap_y = max(0.0, min(fy + fh, sy + sh) - max(fy, sy))
    return overlap_x > 1e-6 and overlap_y > 1e-6


def _assert_valid_entry_result(positions: Sequence[Sequence[float]], expected_count: int) -> None:
    assert isinstance(positions, list), "solve() must return a list"
    assert len(positions) == expected_count, "solve() must return exactly block_count rectangles"

    rects: List[Rect] = []
    for idx, raw_rect in enumerate(positions):
        assert len(raw_rect) == 4, f"block {idx} rectangle must have 4 fields"
        rect = tuple(float(value) for value in raw_rect)
        x, y, width, height = rect
        assert math.isfinite(x) and math.isfinite(y), f"block {idx} coordinates must be finite"
        assert math.isfinite(width) and math.isfinite(height), f"block {idx} dimensions must be finite"
        assert width > 0.0 and height > 0.0, f"block {idx} dimensions must be positive"
        assert abs(width * height - 100.0) / 100.0 <= 0.01, (
            f"block {idx} area must stay within 1% of target"
        )
        rects.append(rect)

    for i, first in enumerate(rects):
        for j, second in enumerate(rects[i + 1:], i + 1):
            assert not _rects_overlap(first, second), f"blocks {i} and {j} must not overlap"


def run_smoke() -> None:
    inputs = _validator_dummy_inputs(target_positions=None)

    optimizer = MyOptimizer()
    _assert_valid_entry_result(optimizer.solve(**inputs), inputs["block_count"])

    fallback_optimizer = MyOptimizer()
    fallback_optimizer._debug_raise_quality_layer = True
    _assert_valid_entry_result(fallback_optimizer.solve(**inputs), inputs["block_count"])

    plan_calls = 0
    original_plan_soft_units = my_optimizer._plan_soft_units

    def counting_plan_soft_units(context):
        nonlocal plan_calls
        plan_calls += 1
        return original_plan_soft_units(context)

    my_optimizer._plan_soft_units = counting_plan_soft_units
    try:
        optimized_optimizer = MyOptimizer()
        _assert_valid_entry_result(
            optimized_optimizer.solve(**inputs),
            inputs["block_count"],
        )
    finally:
        my_optimizer._plan_soft_units = original_plan_soft_units

    assert plan_calls == 1, f"entry path should plan units once, saw {plan_calls}"


if __name__ == "__main__":
    run_smoke()
    print("optimizer-entry smoke passed")
