# Constraint-Aware Constructive Initializer

## Goal

Generate bounded hard-feasible candidate layouts better than the fallback by placing preplaced obstacles, boundary units, grouping macros, MIB-aware dimensions, and remaining blocks in deterministic seed orders.

## Inputs

- `doc/proposal.md`: Multi-start constructive strategy using obstacles, boundary blocks, MIB groups, grouping clusters, connectivity, and legality-preserving candidates.
- `doc/high-level-design.md`: Constructive Initializer module, data flow from units and dimensions, and candidate expansion requirement.
- `doc/detailed-design.md`: Seed orders, required behavior independent of packing representation, boundary repair note, and open packing-representation question.
- `doc/test-plan.md`: Constructive initializer integration tests for obstacle placement, boundary-first placement, grouping macro expansion, empty connectivity, and candidate length.

## Write Scope

Constructive candidate generation, unit packing, seed-order logic, and expansion helpers in `iccad2026contest/my_optimizer.py`; future constructive fixtures in the agreed test harness.

## Read Scope

Parsed input model, Immutable Geometry Registry, Dimension Plan, Placement Unit Set, Proxy Scoring, Hard-Constraint Preflight Checker, and fallback packing convention.

## Dependencies

Dimension Planner; Immutable Geometry Registry; Macro and Soft-Constraint Planner; Proxy Scoring; Hard-Constraint Preflight Checker; Candidate Manager.

## Tasks

- [x] Select the initial constructive packing representation for implementation, defaulting to deterministic shelves if no optimized representation is approved before coding.
- [x] Generate bounded seed orders including original id order, descending area order, connectivity-weight order, boundary-first order, and grouping macro priority order.
- [x] Place preplaced units exactly, then boundary-intent units and grouping macros, then remaining units without positive-area overlap.
- [x] Expand every placed unit to one rectangle per original block id before scoring, preflight, or return.
- [x] Send only expanded candidates to Candidate Manager so infeasible or malformed seeds cannot replace a feasible fallback.
- [x] Add fixtures for obstacle placement, boundary-first placement, grouping macro expansion, empty connectivity, and exact `block_count` candidate expansion.

## Implementation Notes

- 2026-06-14: The initial representation is deterministic shelf packing. The `original_id` seed is one-row and fallback-equivalent; the other four seeds use bounded compact shelves.
- 2026-06-14 optimization: Added a bounded `boundary_frame` seed that keeps left/bottom boundary units early while placing right/top-only boundary units late, improving simple right/top boundary satisfaction without changing fallback retention.
- 2026-06-14 optimization: Added a deterministic `connectivity_greedy` seed that builds unit-level B2B adjacency, starts from the strongest incident movable unit, and then appends units by strongest connection to the placed frontier. The seed reuses the existing shelf packer and hard-preflighted Candidate Manager path.
- 2026-06-14 optimization: Replaced the order-only `boundary_frame` behavior with a deterministic outer-rail packer. Boundary-constrained movable units are partitioned into left/right/top/bottom/corner rails, same-edge units are stacked without overlap, unconstrained units are packed in the interior, and the expanded candidate still goes through hard preflight and Candidate Manager scoring.
- 2026-06-14 optimization: Added a bounded `boundary_skyline` seed. It preserves the existing boundary-frame rail convention but tries bottom-left best-fit packing for frame interiors and for non-boundary movable units across a small fixed set of width hints, then keeps only the hard-feasible variant with the best proxy key.
- 2026-06-15 optimization: Added a bounded `boundary_skyline_connected` seed. It preserves the existing boundary-skyline rail convention but packs non-boundary/interior units with a connectivity-aware bottom-left chooser that prioritizes links to already placed blocks and fixed pins while still including bbox growth in the site key.

## Tests and Quality Gates

- [x] Verify every constructive candidate expands to exactly `block_count` rectangles and passes hard preflight before it can become best feasible.
- [x] Verify all constructive loops are bounded by explicit seed counts for small, medium, and large block counts.

## Done When

- [x] Constructive initialization can produce at least the fallback-equivalent candidate and additional deterministic candidate seeds where applicable.
- [x] Hard-feasible fallback retention is unaffected when all constructive seeds fail or have soft violations.
