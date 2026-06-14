# Macro and Soft-Constraint Planner

## Goal

Create placement units and soft-constraint intents for grouping clusters, MIB-linked shapes, and boundary-constrained blocks without compromising hard feasibility.

## Inputs

- `doc/proposal.md`: Grouping macro, boundary frame, MIB shape, and soft-constraint repair strategy.
- `doc/high-level-design.md`: Macro and Soft-Constraint Planner module, placement unit data flow, and soft constraint role.
- `doc/detailed-design.md`: Placement Unit contract, macro construction outline, boundary intents, and failure handling.
- `doc/test-plan.md`: Macro Planner tests for grouping, MIB metadata, boundary masks, unit expansion, and group-with-preplaced cases.

## Write Scope

Placement unit and soft-intent helpers in `iccad2026contest/my_optimizer.py`; future macro, MIB, grouping, and boundary fixtures in the agreed test harness.

## Read Scope

Constraint model, Dimension Plan, Immutable Geometry Registry, evaluator soft-constraint semantics, and grouping/MIB/boundary sections in the design docs.

## Dependencies

Input Normalization and Constraint Parser; Dimension Planner; Immutable Geometry Registry.

## Tasks

- [x] Create unit records that preserve original block ids, local rectangles, footprint dimensions, movability, boundary intent, and soft-link metadata.
- [x] Represent preplaced blocks as fixed units and avoid moving them to satisfy grouping or boundary soft constraints.
- [x] Build simple edge-connected grouping macros for movable cluster groups, starting with a deterministic local chain layout.
- [x] Attach MIB metadata from the dimension plan without changing incompatible hard-feasible dimensions.
- [x] Attach boundary bitmask intents to affected blocks or units for later construction and repair.
- [x] Add fixtures for single-block and multi-block groups, groups containing preplaced blocks, equal/unequal MIB metadata, boundary edge masks, boundary corner masks, and unit expansion.

## Tests and Quality Gates

- [x] Verify every placement unit expands back to exact original block ids with planned dimensions.
- [x] Verify grouping, MIB, and boundary intents are preserved even when soft satisfaction is impossible without moving immutable geometry.

## Done When

- [x] Constructive initialization and local search can consume placement units without rediscovering grouping, MIB, or boundary constraints.
- [x] Soft-constraint planner fixtures cover movable groups, preplaced members, MIB metadata, boundary edges, boundary corners, and unit expansion.
