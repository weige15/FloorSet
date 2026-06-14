# Immutable Geometry Registry

## Goal

Extract and preserve exact fixed-shape dimensions and preplaced rectangles from `target_positions`, and expose preplaced blocks as placement obstacles.

## Inputs

- `doc/proposal.md`: Hard constraint requirement for exact fixed-shape dimensions and preplaced locations/dimensions.
- `doc/high-level-design.md`: Immutable Geometry Registry module and ownership of authoritative immutable geometry.
- `doc/detailed-design.md`: Registry contract, target extraction rules, obstacle ownership, invalid-target handling, and overlap limitations.
- `doc/test-plan.md`: Fixed/preplaced immutability fixtures and preplaced obstacle golden case.

## Write Scope

Immutable geometry helpers or records in `iccad2026contest/my_optimizer.py`; future fixed/preplaced geometry fixtures in the agreed test harness.

## Read Scope

Parsed constraint model, `target_positions` conventions in `iccad2026contest/iccad2026_evaluate.py`, evaluator hard dimension checks, and `doc/detailed-design.md` immutable geometry contract.

## Dependencies

Input Normalization and Constraint Parser. Provides data to Dimension Planner, Deterministic Legal Fallback, Constructive Initializer, Local Search and Repair, and Hard-Constraint Preflight Checker.

## Tasks

- [x] Build `fixed_dims` for fixed-shape blocks from target width and height without modifying or rotating those dimensions.
- [x] Build `preplaced_rects` for preplaced blocks from exact target `(x, y, width, height)` values.
- [x] Derive deterministic `obstacle_rects` and `movable_ids`, treating preplaced blocks as immutable output rectangles and packing obstacles.
- [x] Mark missing, nonfinite, or nonpositive fixed/preplaced target geometry as invalid so fallback and preflight can report the hard failure.
- [x] Detect overlapping preplaced obstacles as an unrecoverable input inconsistency for diagnostics.
- [x] Add mixed fixed/preplaced/free fixtures, including `target_positions=None` and preplaced-overlap negative cases.

## Tests and Quality Gates

- [x] Verify fixed-only, preplaced-only, mixed, and `target_positions=None` fixtures extract the expected records and obstacle sets.
- [x] Compare immutable dimension and coordinate preservation against evaluator hard-check tolerance expectations.

## Done When

- [x] Fixed and preplaced geometry is authoritative, immutable, and available by original block id.
- [x] Invalid immutable inputs are surfaced to preflight or diagnostics without silently repairing contest targets.

## Optimization Notes

- 2026-06-14: `_build_immutable_geometry()` extracts fixed/preplaced target data in one pass over constrained block ids and uses a deterministic x-sweep helper for preplaced-overlap diagnostics. Smoke coverage includes combined fixed+preplaced invalid-role reporting and block-id-sorted overlap diagnostics.
