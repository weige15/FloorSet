# Dimension Planner

## Goal

Assign a hard-feasible `(width, height)` pair for every active block while preserving immutable dimensions and synchronizing MIB shapes only when compatible with area constraints.

## Inputs

- `doc/proposal.md`: Dimension strategy for fixed/preplaced blocks, soft area preservation, and MIB hard-feasibility priority.
- `doc/high-level-design.md`: Dimension Planner module and placement-before-dimensions dependency order.
- `doc/detailed-design.md`: Dimension Plan contract, square baseline rule, MIB compatibility records, and failure handling.
- `doc/test-plan.md`: Dimension Planner unit tests for ordinary soft, immutable, compatible MIB, incompatible MIB, and 1% area boundary cases.

## Write Scope

Dimension planning helpers or records in `iccad2026contest/my_optimizer.py`; future dimension and MIB fixtures in the agreed test harness.

## Read Scope

Parsed input records, Immutable Geometry Registry records, evaluator area tolerance logic, and MIB semantics from contest docs and evaluator helpers.

## Dependencies

Input Normalization and Constraint Parser; Immutable Geometry Registry. Provides dimensions to Deterministic Legal Fallback, Macro and Soft-Constraint Planner, Constructive Initializer, Local Search and Repair, Proxy Scoring, and Preflight.

## Tasks

- [x] Populate per-block widths and heights for all active blocks, applying preplaced dimensions first and fixed-shape dimensions second.
- [x] Choose deterministic square dimensions `sqrt(area)` for ordinary soft blocks with positive target areas.
- [x] Synchronize equal-area compatible MIB soft blocks to identical dimensions without violating any hard area tolerance.
- [x] Preserve individual hard-feasible dimensions for incompatible MIB groups and record expected MIB soft violations.
- [x] Label dimension sources as immutable preplaced, immutable fixed, MIB-synchronized soft, ordinary soft, or fallback repair.
- [x] Add fixtures for ordinary soft areas, immutable dimensions, compatible and incompatible MIB groups, nonpositive areas, and area tolerance boundary values.

## Tests and Quality Gates

- [x] Verify all non-immutable soft blocks have relative area error at or below `0.01`.
- [x] Verify fixed and preplaced dimensions match immutable registry values within evaluator hard-check tolerance.
- [x] Verify equal-area MIB groups share shape and unequal-area MIB groups keep hard area feasibility.

## Done When

- [x] Every active block has positive finite planned dimensions unless the input is explicitly invalid.
- [x] Dimension fixtures cover ordinary soft, fixed, preplaced, MIB-compatible, MIB-incompatible, and area-boundary cases.
