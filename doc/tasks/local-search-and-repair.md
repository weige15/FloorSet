# Local Search and Repair

## Goal

Improve feasible or repairable layouts with bounded moves while preserving immutable geometry and requiring repair plus preflight before candidate acceptance.

## Inputs

- `doc/proposal.md`: Bounded refinement moves, repair strategy, best-feasible retention, and runtime scaling by block count.
- `doc/high-level-design.md`: Local Search and Repair module, runtime budget dependency, and search role after candidate construction.
- `doc/detailed-design.md`: Move families, repair outline, budget open questions, and failure handling.
- `doc/test-plan.md`: Local search seeded move tests, search-never-loses-feasibility properties, boundary/compaction regression, MIB repair regression, and performance benchmarks.

## Write Scope

Local search state, move proposal/application, repair helpers, compaction helpers, boundary snapping, MIB synchronization, and budget policy in `iccad2026contest/my_optimizer.py`; future local-search fixtures and stress checks in the agreed test harness.

## Read Scope

Candidate Manager, Proxy Scoring, Hard-Constraint Preflight Checker, Dimension Plan, Immutable Geometry Registry, Placement Unit Set, and open budget questions in `doc/detailed-design.md`.

## Dependencies

Candidate Manager; Proxy Scoring; Hard-Constraint Preflight Checker; Dimension Planner; Immutable Geometry Registry; Macro and Soft-Constraint Planner.

## Tasks

- [x] Define a conservative initial budget policy by `block_count` or disable expensive moves until a concrete budget is approved.
- [x] Implement or stub bounded move families for unit order swaps, unit relocation, area-preserving soft aspect updates, compatible MIB synchronization, boundary snapping, and overlap-safe compaction.
- [x] Repair immutable geometry after every move so preplaced coordinates and fixed/preplaced dimensions cannot drift.
- [x] Reject or repair any aspect update, MIB synchronization, or compaction that violates hard area tolerance or introduces overlap.
- [x] Yield trial candidates only through Candidate Manager so preflight and best-feasible retention control acceptance.
- [x] Add deterministic seeded fixtures for each move family plus regressions for boundary snapping after compaction, incompatible MIB area preservation, and search-never-loses-feasibility.

## Tests and Quality Gates

- [x] Verify every local-search fixture either preserves hard feasibility by construction or is rejected before candidate acceptance.
- [x] Verify synthetic 21-block, 60-block, and 120-block stress cases complete inside the agreed budget once that budget is defined.

## Done When

- [x] Local search is bounded, deterministic enough for regression fixtures, and cannot mutate immutable geometry.
- [x] Candidate Manager still returns the best feasible candidate when later local moves become infeasible.
