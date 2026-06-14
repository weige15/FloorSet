# Hard-Constraint Preflight Checker

## Goal

Mirror evaluator hard checks before final return and produce diagnostics for candidate rejection without optimizing layouts.

## Inputs

- `doc/proposal.md`: Correctness strategy requiring exact immutable geometry, no overlaps, positive dimensions, and 1% soft-block area tolerance.
- `doc/high-level-design.md`: Hard-Constraint Preflight Checker module, feasibility gate role, and evaluator-aligned hard semantics.
- `doc/detailed-design.md`: Preflight outline, tolerances, fixed/preplaced skip behavior for soft area checks, and conflict-resolution rule.
- `doc/test-plan.md`: Edge-touching, positive-overlap, area tolerance, fixed/preplaced immutability, evaluator differential, and randomized hard-feasibility tests.

## Write Scope

Preflight validation, overlap checks, soft area checks, immutable geometry checks, violation reports, and optional soft-report hook in `iccad2026contest/my_optimizer.py`; future preflight differential fixtures in the agreed test harness.

## Read Scope

Evaluator helpers `check_overlap`, `check_area_tolerance`, `check_dimension_hard_constraints`, parsed input model, Immutable Geometry Registry, Dimension Plan, and Candidate contract.

## Dependencies

Input Normalization and Constraint Parser; Immutable Geometry Registry; Dimension Planner data where needed for expected areas and immutable ids.

## Tasks

- [x] Validate candidate length equals `block_count`, each rectangle has finite numeric fields, and width/height are positive.
- [x] Count pairwise overlap violations using evaluator tolerance: overlap width and height both greater than `1e-6`.
- [x] Count soft-block area tolerance violations when relative error is greater than `0.01`, skipping fixed and preplaced blocks.
- [x] Count fixed/preplaced dimension violations when width or height differs from immutable target by more than `1e-4`.
- [x] Count preplaced coordinate violations when x or y differs from immutable target by more than `1e-4`.
- [x] Produce a violation report with hard-feasibility verdict and evaluator-aligned fields for Candidate Manager and diagnostics.
- [x] Add differential fixtures against evaluator helpers for edge-touching, positive overlap, area tolerance boundary, fixed/preplaced immutability, malformed candidates, and randomized cases.

## Tests and Quality Gates

- [x] Verify internal preflight agrees with evaluator hard-check helpers on all golden and randomized fixtures.
- [x] Stop implementation and resolve the conflict if evaluator helpers and local preflight disagree.

## Done When

- [x] Every final-return candidate is gated by preflight or is explicitly a least-bad diagnostic candidate for unrecoverable invalid inputs.
- [x] Preflight fixtures cover overlap, edge-touching, area tolerance, immutable geometry, malformed candidates, and evaluator differential checks.
