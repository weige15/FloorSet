# Deterministic Legal Fallback

## Goal

Produce a deterministic non-overlapping candidate that can be returned whenever optimized construction or search cannot prove hard feasibility.

## Inputs

- `doc/proposal.md`: Baseline shelf or skyline legalizer that applies preplaced obstacles, fixed dimensions, square soft blocks, and safe fallback return.
- `doc/high-level-design.md`: Deterministic Legal Fallback module and correctness-critical role.
- `doc/detailed-design.md`: Fallback shelf behavior, preplaced obstacle handling, golden fixture expectations, and unresolved shelf convention choices.
- `doc/test-plan.md`: Two all-soft, fixed-shape, preplaced obstacle, edge-touching, overlap, and randomized fallback property tests.

## Write Scope

Fallback packing helpers in `iccad2026contest/my_optimizer.py`; future fallback fixtures and golden coordinate checks in the agreed test harness.

## Read Scope

Dimension Plan, Immutable Geometry Registry, Hard-Constraint Preflight Checker, and evaluator overlap and area tolerance helpers.

## Dependencies

Dimension Planner; Immutable Geometry Registry; Hard-Constraint Preflight Checker.

## Tasks

- [x] Implement deterministic id-order placement for no-obstacle cases so simple all-soft fixtures place adjacent horizontal rectangles.
- [x] Emit preplaced blocks exactly from immutable registry and skip them during movable block placement.
- [x] Choose and document the first obstacle-avoidance convention for preplaced cases, using a safe region outside the obstacle bounding box if direct shelf placement intersects obstacles.
- [x] Place fixed-shape and ordinary soft movable blocks using planned dimensions without introducing positive-area overlap.
- [x] Preflight the fallback and attach diagnostics for overlap, area, and immutable-geometry violations.
- [x] Add golden fixtures for two all-soft blocks, fixed-shape plus soft block, preplaced obstacle avoidance, legal edge-touching, and illegal positive overlap.

## Implementation Notes

- 2026-06-14: The preplaced-obstacle convention is a single horizontal movable shelf strictly to the right of the preplaced-obstacle bounding box, using a fixed gap. No-obstacle cases remain horizontal id-order shelves from `(0, 0)`.
- 2026-06-14: Optimization pass keeps the one-row fallback as the deterministic baseline, also tries a wrapped-shelf fallback for larger movable sets, and selects the wrapped variant only when the fallback proxy score improves. The returned fallback now carries preflight and proxy diagnostics before Candidate Manager retention.

## Tests and Quality Gates

- [x] Verify fallback fixtures have finite positive dimensions, zero overlaps, exact immutable geometry, and soft area relative error at or below `0.01`.
- [x] Verify randomized hard-feasibility fallback properties for approved deterministic seeds.

## Done When

- [x] Fallback produces one rectangle per active block and is hard feasible for internally consistent synthetic cases.
- [x] Candidate Manager can retain the fallback as the last-resort feasible candidate.
