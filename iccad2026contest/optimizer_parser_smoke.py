#!/usr/bin/env python3
"""Synthetic fixtures for optimizer input normalization and constraint parsing.

Run from the repository root with:

    python -B iccad2026contest/optimizer_parser_smoke.py
"""

from typing import Any, Sequence

from my_optimizer import _parse_inputs


class _Scalar:
    def __init__(self, value: Any):
        self._value = value

    def item(self) -> Any:
        return self._value


class _TensorLike:
    def __init__(self, data: Any):
        self._data = data
        self.shape = self._shape(data)

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, tuple):
            value = self._data
            for part in key:
                value = value[part]
            return self._wrap(value)
        return self._wrap(self._data[key])

    @classmethod
    def _wrap(cls, value: Any) -> Any:
        if isinstance(value, (list, tuple)):
            return cls(value)
        return _Scalar(value)

    @classmethod
    def _shape(cls, value: Any) -> Sequence[int]:
        if isinstance(value, (list, tuple)):
            if value and isinstance(value[0], (list, tuple)):
                return (len(value), len(value[0]))
            return (len(value),)
        return ()


def _assert_common_all_columns(parsed) -> None:
    assert parsed.n == 4
    assert parsed.areas == [4.0, 9.0, 16.0, 25.0]
    assert parsed.fixed_ids == {0}
    assert parsed.preplaced_ids == {1}
    assert parsed.fixed_or_preplaced_ids == {0, 1}
    assert parsed.mib_groups == {1: [0, 1], 3: [3]}
    assert parsed.cluster_groups == {2: [1, 2]}
    assert parsed.boundary_masks == {0: 5, 2: 8}
    assert parsed.b2b_edges == [(0, 1, 2.5), (2, 3, 0.0)]
    assert parsed.p2b_edges == [(0, 0, 1.2), (2, 3, 3.4)]
    assert parsed.pins == [(10.0, 10.0), (11.0, 11.0), (12.0, 12.0)]
    assert parsed.target_positions is None
    assert "ignored invalid B2B edge 1" in parsed.diagnostics
    assert "ignored invalid B2B edge 4" in parsed.diagnostics
    assert "ignored invalid P2B edge 3" in parsed.diagnostics
    assert "ignored invalid P2B edge 4" in parsed.diagnostics
    assert "ignored invalid P2B edge 5" in parsed.diagnostics


def test_all_constraint_columns_list_like() -> None:
    parsed = _parse_inputs(
        4,
        [4.0, 9.0, 16.0, 25.0, 36.0],
        [[0, 1, 2.5], [1, 4, 1.0], [-1, -1, -1.0], [2, 3, 0.0], [0, 2, "nan"]],
        [[0, 0, 1.2], [2, 3, 3.4], [-1, -1, -1.0], [5, 1, 1.0], [1, 99, 1.0], [0, 2, "nan"]],
        [[10.0, 10.0], [11.0, 11.0], [12.0, 12.0]],
        [
            [1, 0, 1, 0, 5],
            [0, 1, 1, 2, 0],
            [0, 0, 0, 2, 8],
            [0, 0, 3, 0, 0],
        ],
        None,
    )
    _assert_common_all_columns(parsed)


def test_all_constraint_columns_tensor_like() -> None:
    parsed = _parse_inputs(
        4,
        _TensorLike([4.0, 9.0, 16.0, 25.0, 36.0]),
        _TensorLike([[0, 1, 2.5], [1, 4, 1.0], [-1, -1, -1.0], [2, 3, 0.0], [0, 2, "nan"]]),
        _TensorLike([[0, 0, 1.2], [2, 3, 3.4], [-1, -1, -1.0], [5, 1, 1.0], [1, 99, 1.0], [0, 2, "nan"]]),
        _TensorLike([[10.0, 10.0], [11.0, 11.0], [12.0, 12.0]]),
        _TensorLike([
            [1, 0, 1, 0, 5],
            [0, 1, 1, 2, 0],
            [0, 0, 0, 2, 8],
            [0, 0, 3, 0, 0],
        ]),
        None,
    )
    _assert_common_all_columns(parsed)


def test_missing_columns_empty_connectivity_and_no_targets() -> None:
    parsed = _parse_inputs(
        3,
        [1.0, 4.0, 9.0, 16.0],
        [],
        None,
        None,
        [[1], [0], [1]],
        None,
    )
    assert parsed.areas == [1.0, 4.0, 9.0]
    assert parsed.fixed_ids == {0, 2}
    assert parsed.preplaced_ids == set()
    assert parsed.mib_groups == {}
    assert parsed.cluster_groups == {}
    assert parsed.boundary_masks == {}
    assert parsed.b2b_edges == []
    assert parsed.p2b_edges == []
    assert parsed.pins == []
    assert parsed.target_positions is None


def test_target_positions_and_invalid_pin_diagnostics() -> None:
    parsed = _parse_inputs(
        3,
        _TensorLike([2.0, 3.0, 5.0]),
        _TensorLike([[-1, -1, -1.0]]),
        _TensorLike([[1, 2, 7.0], [2, 0, 8.0]]),
        _TensorLike([[0.0, 0.0], ["nan", 1.0], [5.0, 6.0]]),
        _TensorLike([[0, 0, 0, 0, 0], [0, 1, 0, 0, 0], [0, 0, 0, 0, 0]]),
        _TensorLike([[-1, -1, -1, -1], [4, 5, 6, 7], [8, 9, 10, 11]]),
    )
    assert parsed.b2b_edges == []
    assert parsed.p2b_edges == [(2, 0, 8.0)]
    assert parsed.pins == [(0.0, 0.0), (0.0, 0.0), (5.0, 6.0)]
    assert parsed.target_positions == [
        (-1.0, -1.0, -1.0, -1.0),
        (4.0, 5.0, 6.0, 7.0),
        (8.0, 9.0, 10.0, 11.0),
    ]
    assert "invalid pin position 1" in parsed.diagnostics
    assert "ignored invalid P2B edge 0" in parsed.diagnostics


def test_padded_pin_sentinel_rejects_p2b_edges() -> None:
    parsed = _parse_inputs(
        2,
        [4.0, 9.0],
        [],
        [[0, 0, 1.0], [1, 1, 2.0], [-1, -1, -1.0]],
        [[-1.0, -1.0], [7.0, 8.0]],
        [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
        None,
    )
    assert parsed.pins == [(0.0, 0.0), (7.0, 8.0)]
    assert parsed.p2b_edges == [(1, 1, 2.0)]
    assert "inactive pin position 0" in parsed.diagnostics
    assert "ignored invalid P2B edge 0" in parsed.diagnostics


def run_smoke() -> None:
    test_all_constraint_columns_list_like()
    test_all_constraint_columns_tensor_like()
    test_missing_columns_empty_connectivity_and_no_targets()
    test_target_positions_and_invalid_pin_diagnostics()
    test_padded_pin_sentinel_rejects_p2b_edges()


if __name__ == "__main__":
    run_smoke()
    print("optimizer-parser smoke passed")
