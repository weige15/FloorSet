# Input Normalization and Constraint Parser

## Goal

Convert evaluator tensors or list-like inputs into deterministic active records and derive constraint, connectivity, and pin models for downstream modules.

## Inputs

- `doc/proposal.md`: Algorithm strategy to parse constraints once into block sets, MIB groups, cluster groups, and boundary bitmasks.
- `doc/high-level-design.md`: Input Normalization and Constraint Parser module, solve input contract, and active data flow.
- `doc/detailed-design.md`: Parser responsibilities, data structures, filtering rules, failure handling, and malformed-edge open question.
- `doc/test-plan.md`: Parser unit tests for tensors, lists, active slicing, padded sentinels, all constraint columns, and empty connectivity.

## Write Scope

Parsing helpers and lightweight input/constraint records inside `iccad2026contest/my_optimizer.py`; future parser fixtures in the agreed synthetic test harness.

## Read Scope

`iccad2026contest/iccad2026_evaluate.py` input handling and helper semantics, `iccad2026contest/optimizer_template.py`, and the shared data contracts in `doc/detailed-design.md`.

## Dependencies

Optimizer Entry call contract and evaluator input format. No downstream module dependencies.

## Tasks

- [x] Normalize `area_targets`, connectivity arrays, pins, constraints, and `target_positions` from tensor-like or list-like values without reordering original block ids.
- [x] Slice block-indexed data to active ids `[0, block_count)` and ignore padded connectivity rows whose first field is `-1`.
- [x] Parse constraint columns `[fixed, preplaced, mib, cluster, boundary]`, defaulting missing optional columns to no active constraint.
- [x] Build `fixed_ids`, `preplaced_ids`, `mib_groups`, `cluster_groups`, `boundary_masks`, `fixed_or_preplaced_ids`, active B2B/P2B edges, and active pin positions.
- [x] Ignore or diagnostically record out-of-range connectivity so invalid edges cannot propagate into scoring or search.
- [x] Add parser fixtures for all five constraint columns, missing columns, empty connectivity, padded rows, and `target_positions=None`.

## Tests and Quality Gates

- [x] Run parser fixtures against tensor-like and list-like inputs and verify parsed sets, groups, masks, edges, and pins match expected values.
- [x] Verify empty B2B/P2B inputs produce valid zero-edge parsed models without NaN or division-by-zero risk.

## Done When

- [x] Downstream modules receive stable, finite, active-only models that preserve original block ordering.
- [x] Parser fixtures cover fixed, preplaced, MIB, grouping, boundary, padded sentinel, missing-column, and empty-connectivity cases.

## Cycle Evidence

- 2026-06-14: Hardened `_parse_inputs()` in `iccad2026contest/my_optimizer.py` to preserve pin-index alignment, diagnose invalid pin positions, and reject P2B edges that reference invalid pins.
- 2026-06-14: Added `iccad2026contest/optimizer_parser_smoke.py` with list-like and tensor-like fixtures covering all five constraint columns, active slicing, padded connectivity rows, invalid connectivity diagnostics, missing columns, empty connectivity, invalid pins, and `target_positions=None`.
- 2026-06-14: `python -B iccad2026contest/optimizer_parser_smoke.py` passed.
- 2026-06-14: `python -B iccad2026contest/optimizer_entry_smoke.py` passed after parser changes.
- 2026-06-14: `python -B -c "for path in ('iccad2026contest/my_optimizer.py', 'iccad2026contest/optimizer_parser_smoke.py', 'iccad2026contest/optimizer_entry_smoke.py'): compile(open(path).read(), path, 'exec')"` passed.
- 2026-06-14: Parser optimization pass hardened `_parse_inputs()` so padded `pins_pos` rows whose first coordinate is `-1` preserve pin-index alignment but are treated as inactive, causing P2B edges to those rows to be diagnostically ignored instead of scored against `(-1, -1)`.
- 2026-06-14: Added a parser smoke fixture for padded pin sentinels and reran all optimizer smoke checks plus `python -B -m py_compile iccad2026contest/my_optimizer.py iccad2026contest/optimizer_parser_smoke.py`; all passed. Evaluator-importing smokes produced the known Matplotlib temporary-cache warning because `/home/kuotzuwei15/.config/matplotlib` is not writable.
