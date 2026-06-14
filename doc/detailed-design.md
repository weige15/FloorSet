# Detailed Design

## Purpose

This document defines the implementation-level design for a contest-compliant FloorSet optimizer. It is a planning artifact only: it does not implement code, run evaluators, install dependencies, train models, or create generated result files.

The target implementation remains a copied optimizer file such as `iccad2026contest/my_optimizer.py`. The design preserves the module names and boundaries from `doc/high-level-design.md` and expands them into responsibilities, data contracts, algorithms, failure handling, and independently testable work packages.

## Source Proposal Summary

The proposal calls for a best-available practical optimizer for the ICCAD 2026 FloorSet Challenge. The optimizer must expose `solve()` and return exactly one `(x, y, width, height)` tuple per active block.

The implementation priority is:

1. Preserve hard feasibility: no overlaps, soft-block area within 1%, exact fixed-shape dimensions, and exact preplaced positions/dimensions.
2. Reduce HPWL, bounding-box area, soft-constraint violations, and official runtime.
3. Keep work isolated from shared contest framework files.
4. Use deterministic legalization as the correctness path, with optional ML guidance only as a later initializer.

The proposal identifies three solver layers:

- a deterministic legal fallback;
- a constraint-aware constructive initializer;
- a bounded local search and repair loop that always retains the best feasible candidate.

## HLD Summary

The HLD defines a single optimizer entry point with logical internal modules. The design is intended to be implemented inside `iccad2026contest/my_optimizer.py` unless final packaging rules allow helper files.

The HLD modules are:

- Optimizer Entry
- Input Normalization and Constraint Parser
- Immutable Geometry Registry
- Dimension Planner
- Deterministic Legal Fallback
- Macro and Soft-Constraint Planner
- Constraint-Aware Constructive Initializer
- Candidate Manager
- Local Search and Repair
- Proxy Scoring
- Hard-Constraint Preflight Checker
- Optional ML Initializer

Dependency direction is one-way from input parsing toward geometry planning, candidate construction, search, preflight, and final return. No module should depend on persisted files, global mutable solver state, downloaded datasets, or generated artifacts.

## Design Goals

- Implement the evaluator-facing `solve()` contract exactly.
- Make a feasible fallback available for every internally consistent input case.
- Treat fixed-shape and preplaced target geometry as immutable facts.
- Preserve original block ids and output ordering through every internal representation.
- Keep hard feasibility checks separate from score-improvement heuristics.
- Prefer deterministic behavior for fallback, parsing, dimension planning, and preflight.
- Keep local search bounded by an explicit policy, with exact local time or iteration thresholds still unresolved.
- Keep all internal modules independently testable with synthetic fixtures where possible.
- Use evaluator helper behavior as the oracle for overlap, area tolerance, immutable geometry, HPWL, bounding-box area, and soft-constraint semantics.

## Non-Goals

- Do not modify `iccad2026contest/iccad2026_evaluate.py`, dataset loaders, validation data, or `optimizer_template.py`.
- Do not depend on training data, downloads, generated JSON, or model weights for correctness.
- Do not reverse-engineer the dataset generator.
- Do not define final contest packaging beyond the documented optimizer-file interface.
- Do not add external services, databases, queues, APIs, or persistent state.
- Do not treat local runtime score as official runtime competitiveness; local evaluation uses neutral `RuntimeFactor = 1.0`.
- Do not make soft-constraint repair override hard constraints.

## Architecture Overview

The optimizer runs one case per `solve()` call:

1. Optimizer Entry receives evaluator tensors and `block_count`.
2. Input Normalization and Constraint Parser converts active slices into internal block, edge, pin, and constraint records.
3. Immutable Geometry Registry extracts fixed-shape dimensions and preplaced rectangles from `target_positions`.
4. Dimension Planner assigns one `(width, height)` pair per block.
5. Deterministic Legal Fallback builds a known non-overlapping candidate using planned dimensions and immutable obstacles.
6. Macro and Soft-Constraint Planner builds placement units for grouping, MIB, and boundary intents.
7. Constraint-Aware Constructive Initializer generates candidate layouts from units, connectivity, dimensions, and obstacles.
8. Candidate Manager scores and retains feasible candidates.
9. Local Search and Repair applies bounded repairable moves and sends accepted states back through scoring and preflight.
10. Hard-Constraint Preflight Checker gates final eligibility.
11. Optimizer Entry returns the best feasible candidate, or the fallback if no optimized candidate is feasible.

The Optional ML Initializer, if later approved, may provide seed orderings, centers, or aspect ratios. It cannot bypass dimension planning, legalization, or preflight.

## Shared Data Contracts

The following contracts describe logical records. Exact Python symbol names are not fixed by this document; they may be implemented as private helpers, dataclasses, dictionaries, tuples, or lightweight classes inside `my_optimizer.py`.

### Rect Contract

- Shape: `(x, y, width, height)`.
- Coordinates are lower-left rectangle coordinates.
- `width` and `height` must be finite positive floats.
- Rectangle `i` occupies `[x_i, x_i + width_i] x [y_i, y_i + height_i]`.
- Edge-touching is legal; positive-area overlap is illegal.

### Solve Input Contract

- `block_count` is the number of active blocks.
- `area_targets` is sliced to active block ids `[0, block_count)`.
- `b2b_connectivity` edges have `(block_i, block_j, weight)`.
- `p2b_connectivity` edges have `(pin_idx, block_idx, weight)`.
- `pins_pos` gives fixed pin coordinates.
- `constraints` active columns are `[fixed, preplaced, mib, cluster, boundary]`.
- `target_positions` has `(x, y, w, h)` per active block. Free values may be `-1`; fixed blocks have target dimensions; preplaced blocks have full target rectangles.
- Connectivity rows with first field `-1` are inactive and ignored, matching evaluator helpers.

### Constraint Model Contract

The parser owns a per-case constraint model containing:

- `n`: active block count.
- `fixed_ids`: blocks whose fixed column is nonzero.
- `preplaced_ids`: blocks whose preplaced column is nonzero.
- `mib_groups`: positive MIB group id to block-id list.
- `cluster_groups`: positive cluster group id to block-id list.
- `boundary_masks`: block id to nonzero boundary bitmask.
- `fixed_or_preplaced_ids`: union of fixed and preplaced ids.
- `b2b_edges`: active B2B edges with valid block ids.
- `p2b_edges`: active P2B edges with valid pin and block ids.
- `pins`: active pin positions as finite numeric pairs.

Boundary bitmasks follow evaluator semantics: `1 = left`, `2 = right`, `4 = top`, `8 = bottom`, with corners represented by sums.

### Immutable Geometry Contract

The immutable geometry registry owns:

- `fixed_dims`: block id to `(width, height)` for fixed-shape blocks.
- `preplaced_rects`: block id to exact `(x, y, width, height)` for preplaced blocks.
- `obstacle_rects`: preplaced rectangles treated as placement obstacles.
- `movable_ids`: blocks not preplaced. Fixed-shape blocks can move but cannot change dimensions.

For fixed and preplaced blocks, dimension tolerance must match evaluator hard checks: absolute dimension difference greater than `1e-4` is a violation. For preplaced blocks, coordinate difference greater than `1e-4` is also a violation.

### Dimension Plan Contract

The dimension plan owns:

- `widths[i]` and `heights[i]` for every active block id.
- `source[i]`: one of immutable preplaced, immutable fixed, MIB-synchronized soft, ordinary soft, or fallback repair.
- `mib_notes`: compatibility notes for MIB groups whose blocks can or cannot share one shape without breaking hard area feasibility.

Soft blocks must satisfy `abs(width * height - area_targets[i]) / area_targets[i] <= 0.01`. Fixed and preplaced blocks are excluded from soft-block area tolerance in evaluator hard checks and are instead checked against immutable target dimensions.

### Placement Unit Contract

A placement unit is an internal construction object that expands back to one or more original block ids:

- `block_ids`: original block ids in the unit.
- `local_rects`: per-block offsets and dimensions inside the unit, when the unit is a macro.
- `bbox_width` and `bbox_height`: unit footprint.
- `movable`: false for preplaced units.
- `boundary_intent`: required boundary mask when any unit block has a boundary constraint.
- `soft_links`: associated MIB or grouping metadata.

Every unit must expand to one rectangle per original block before scoring, preflight, or final return.

### Candidate Contract

A candidate owns:

- `positions`: list of `Rect` values, length exactly `block_count`, ordered by original block id.
- `hard_report`: preflight result, if evaluated.
- `soft_report`: soft-constraint estimate, if evaluated.
- `proxy_score`: online ranking score, if evaluated.
- `source`: fallback, constructive seed, local-search move, ML seed, or repaired state.

An infeasible candidate may be inspected for diagnostics but must not replace the best feasible candidate.

### Violation Report Contract

Violation reports should use evaluator-aligned fields:

- `overlap_violations`
- `area_violations`
- `dimension_violations`
- `boundary_violations`
- `grouping_violations`
- `mib_violations`
- `total_soft_violations`
- `max_possible_violations`
- `violations_relative`

Hard feasibility is true only when overlap, soft-block area, and dimension violations are all zero.

## Module Designs

### Optimizer Entry

#### Responsibility

Expose the evaluator-facing optimizer class and `solve()` method. Orchestrate all internal modules for one case and return the final list of rectangles.

#### Non-Responsibility

- Does not implement packing details, scoring formulas, or geometric hard checks directly.
- Does not load datasets, write files, train models, or call evaluator CLI commands.
- Does not mutate evaluator input tensors.

#### Inputs and Outputs

- Inputs: `block_count`, `area_targets`, `b2b_connectivity`, `p2b_connectivity`, `pins_pos`, `constraints`, and optional `target_positions`.
- Output: list of exactly `block_count` `(x, y, width, height)` tuples.

#### Public Interface

Evaluator-visible interface:

```python
solve(
    block_count,
    area_targets,
    b2b_connectivity,
    p2b_connectivity,
    pins_pos,
    constraints,
    target_positions=None,
)
```

Internal module interfaces are logical and may remain private inside `my_optimizer.py`.

#### Data Structures

- Per-call solver context containing normalized inputs, constraint model, immutable geometry, dimension plan, fallback candidate, candidate manager, and budget policy.
- No cross-call persistent mutable state is required.

#### Internal Design

The entry point should:

1. Initialize a deterministic per-case context.
2. Normalize inputs and parse constraints.
3. Build immutable geometry.
4. Build the dimension plan.
5. Build and preflight the fallback candidate.
6. Build constructive candidates and run bounded search when the fallback is available.
7. Return the best feasible candidate retained by the candidate manager.

If any quality layer raises an exception or returns malformed output, the entry point should fall back to the deterministic candidate when available.

#### Algorithm Details

High-level orchestration pseudocode:

```text
model = parse_inputs(...)
immutable = build_immutable_geometry(model, target_positions)
dimensions = plan_dimensions(model, immutable, area_targets)
fallback = build_fallback(model, immutable, dimensions)
manager = CandidateManager()
manager.consider(fallback)

units = plan_macros_and_soft_constraints(model, dimensions, immutable)
for seed in construct_candidates(model, immutable, dimensions, units):
    manager.consider(seed)

for refined in local_search(manager.best_available(), budget):
    manager.consider(refined)

return manager.best_feasible_or_fallback()
```

Exact local-search budget values remain an open question.

#### Dependencies

Depends on every internal module. No module should depend on Optimizer Entry except through call order and shared context values.

#### Failure Handling

- If parsing fails, return a simple all-soft fallback only if enough area and target data exists; otherwise return a safe malformed-output diagnostic is not available through the contest interface, so this remains an open implementation concern.
- If optimized construction or search fails, return the preflighted fallback.
- If fallback fails because inputs are internally inconsistent, return the least-bad candidate and ensure the failure is diagnosable in internal tests.

#### Independent Test Plan

- Signature and return-format tests with evaluator-like tensors.
- Dummy `block_count = 5` validation-shape test.
- Import smoke test with no file I/O or dataset access.
- Exception-path test where constructive initialization is forced to fail and fallback is still returned.

#### Open Questions

- Should the optimizer class name remain `MyOptimizer` from the template?
- Should exact Python helper names be fixed before implementation, or kept private and task-local?

### Input Normalization and Constraint Parser

#### Responsibility

Convert evaluator inputs into active, finite, per-case records and derive block sets for fixed, preplaced, MIB, grouping, and boundary constraints.

#### Non-Responsibility

- Does not choose dimensions.
- Does not place blocks.
- Does not decide feasibility beyond input shape and active-id filtering.

#### Inputs and Outputs

- Inputs: raw evaluator tensors/lists and `block_count`.
- Outputs: constraint model, active area values, active connectivity edges, and active pin positions.

#### Public Interface

Logical interface:

- `parse_inputs(raw_solve_args) -> ParsedInput`
- `ParsedInput.constraint_model -> ConstraintModel`

Exact symbol names are not fixed.

#### Data Structures

- `ParsedInput`
- `ConstraintModel`
- active edge lists for B2B and P2B connectivity
- active numeric arrays or lists for area targets and pin positions

#### Internal Design

The parser should:

- slice block-indexed tensors to `block_count`;
- ignore padded rows whose first connectivity field is `-1`;
- ignore group ids and boundary masks with value `0`;
- treat nonzero fixed and preplaced columns as active constraints;
- keep group ids positive and preserve original block ids;
- validate only enough numeric shape information to let downstream modules avoid crashes.

#### Algorithm Details

Parsing should be deterministic and should not reorder block ids. Connectivity filtering should preserve input order unless a later module explicitly builds derived adjacency structures.

When tensor APIs are available, normalization can use tensor operations; otherwise it should work with list-like values. This supports evaluator dummy validation and synthetic tests.

#### Dependencies

Depends only on evaluator input contracts and basic Python/numeric conversion.

#### Failure Handling

- Missing constraint columns default to no constraints for that column.
- `target_positions=None` is allowed and should produce empty immutable geometry for validation smoke paths.
- Invalid edges outside active block range are ignored or reported as diagnostics, not used for score calculations.
- Non-finite values should cause the associated candidate path to fail preflight rather than propagating NaNs into scores.

#### Independent Test Plan

- Synthetic tensors with padded `-1` rows.
- Inputs with missing optional columns.
- Fixed, preplaced, MIB, cluster, and boundary parsing fixtures.
- Empty B2B and P2B connectivity fixtures.

#### Open Questions

- Should malformed out-of-range connectivity be ignored silently or recorded in diagnostics for later debugging?

### Immutable Geometry Registry

#### Responsibility

Own exact fixed-shape dimensions and preplaced rectangles derived from constraints and `target_positions`.

#### Non-Responsibility

- Does not decide soft-block dimensions.
- Does not move preplaced blocks.
- Does not pack movable blocks around obstacles.

#### Inputs and Outputs

- Inputs: `ConstraintModel` and active `target_positions`.
- Outputs: `fixed_dims`, `preplaced_rects`, obstacle rectangles, and movable block ids.

#### Public Interface

Logical interface:

- `build_immutable_geometry(model, target_positions) -> ImmutableGeometry`
- accessors for fixed dimensions and preplaced rectangles by block id.

#### Data Structures

- mapping from block id to `(width, height)` for fixed-shape blocks;
- mapping from block id to `(x, y, width, height)` for preplaced blocks;
- list of obstacle rectangles in original block-id order or deterministic sorted order.

#### Internal Design

For each active block:

- if preplaced, read all four target fields and mark the rectangle immutable;
- else if fixed-shape, read target width and height and mark dimensions immutable;
- else leave position and dimensions to downstream modules.

Preplaced blocks are both output rectangles and obstacles for all movable placement modules.

#### Algorithm Details

Registry extraction must mirror evaluator target construction:

- preplaced blocks receive full `(x, y, w, h)`;
- fixed-shape blocks receive `w` and `h` only;
- free blocks may contain `-1` placeholders.

No attempt should be made to repair fixed or preplaced target dimensions in this module.

#### Dependencies

Depends on Input Normalization and Constraint Parser.

#### Failure Handling

- If a fixed or preplaced target value is missing or nonpositive, mark immutable geometry as invalid and let fallback/preflight report failure.
- If preplaced obstacles overlap each other, no legal movable placement can fix that hard violation; record it as an unrecoverable input inconsistency.

#### Independent Test Plan

- Fixed-only target fixtures.
- Preplaced-only target fixtures.
- Mixed fixed/preplaced/free fixtures.
- `target_positions=None` smoke fixture.
- Preplaced-overlap negative fixture.

#### Open Questions

- Should invalid immutable target geometry raise an internal exception or produce a failed preflight report only?

### Dimension Planner

#### Responsibility

Assign one `(width, height)` pair per active block before placement while preserving immutable target dimensions and hard soft-block area tolerance.

#### Non-Responsibility

- Does not choose final coordinates.
- Does not enforce boundary contact or grouping connectivity.
- Does not change preplaced or fixed dimensions.

#### Inputs and Outputs

- Inputs: active area targets, constraint model, immutable geometry, and MIB groups.
- Outputs: `DimensionPlan` with widths, heights, source labels, and MIB compatibility notes.

#### Public Interface

Logical interface:

- `plan_dimensions(parsed_input, immutable_geometry) -> DimensionPlan`

#### Data Structures

- arrays/lists `widths` and `heights`;
- `source` labels;
- MIB compatibility records with group id, block ids, area values, chosen common dimensions when feasible, and violation expectation when not feasible.

#### Internal Design

Dimension planning order:

1. Apply immutable dimensions for preplaced blocks.
2. Apply immutable dimensions for fixed-shape blocks.
3. For ordinary soft blocks, choose area-preserving dimensions.
4. For MIB groups, synchronize shapes only when doing so preserves every block's hard area tolerance.
5. Record unavoidable MIB soft violations for incompatible groups rather than breaking area tolerance.

The proposal and test plan expect square dimensions for simple ordinary soft fixtures. For non-square aspect exploration, local search may later propose aspect changes while preserving area.

#### Algorithm Details

For ordinary soft block area `a`, the deterministic baseline shape is:

```text
width = sqrt(a)
height = sqrt(a)
```

For compatible equal-area MIB groups, use the same square dimensions for all soft members unless immutable member dimensions make a common hard-feasible shape impossible.

For incompatible MIB groups, preserve each block's hard area feasibility and record expected MIB violations for proxy scoring.

#### Dependencies

Depends on Input Normalization and Immutable Geometry Registry.

#### Failure Handling

- Nonpositive area for a soft block cannot produce positive dimensions; mark the plan invalid.
- If MIB synchronization conflicts with fixed/preplaced dimensions or unequal target areas, preserve hard feasibility first.
- Floating point drift must stay inside the evaluator's 1% area tolerance with margin where practical.

#### Independent Test Plan

- Ordinary all-soft area tests.
- Fixed-shape and preplaced dimension immutability tests.
- Equal-area MIB synchronization test.
- Unequal-area MIB hard-feasibility priority test.
- Area boundary test at exactly and just above 1% relative error.

#### Open Questions

- Should the first implementation allow non-square aspect choices during construction, or only during local search?

### Deterministic Legal Fallback

#### Responsibility

Produce a simple, deterministic, overlap-free candidate that can be returned when optimized construction or local search fails.

#### Non-Responsibility

- Does not optimize HPWL aggressively.
- Does not guarantee all soft constraints are satisfied.
- Does not repair internally inconsistent preplaced inputs.

#### Inputs and Outputs

- Inputs: dimension plan and immutable preplaced obstacles.
- Output: fallback `Candidate` with one rectangle per block.

#### Public Interface

Logical interface:

- `build_fallback(model, immutable_geometry, dimension_plan) -> Candidate`

#### Data Structures

- planned rectangle dimensions by block id;
- obstacle list from preplaced blocks;
- placed rectangle list ordered by block id.

#### Internal Design

The fallback should use a deterministic shelf-style placement for movable blocks. Preplaced blocks are emitted exactly at target positions. Movable blocks are placed in block-id order into a non-overlapping region that avoids all preplaced obstacles.

For simple no-obstacle fixtures, the test plan expects horizontal id-order placement:

- block 0 at `(0, 0, w0, h0)`;
- block 1 adjacent at `(w0, 0, w1, h1)`.

For cases with preplaced obstacles, the fallback may choose a conservative safe shelf outside the bounding box of all preplaced obstacles, or an obstacle-aware skyline. The exact obstacle-avoidance convention should be fixed during implementation and reflected in golden tests.

#### Algorithm Details

Conservative fallback outline:

```text
positions = exact preplaced rects
safe_origin = choose origin that does not intersect preplaced obstacle bbox
x_cursor, y_cursor = safe_origin
row_height = 0
for block in active block ids:
    if block is preplaced:
        continue
    rect = (x_cursor, y_cursor, width[block], height[block])
    if rect intersects any preplaced obstacle:
        advance cursor or start a new shelf until clear
    positions[block] = rect
    x_cursor += width[block]
    row_height = max(row_height, height[block])
preflight positions
```

The source docs do not specify a final shelf width, row-break rule, or obstacle-avoidance convention; those remain implementation choices to confirm or lock down when coding.

#### Dependencies

Depends on Dimension Planner and Immutable Geometry Registry. Uses Hard-Constraint Preflight Checker for validation.

#### Failure Handling

- If obstacle avoidance fails under the chosen shelf strategy, place all movable blocks in a region strictly outside the obstacle bounding box.
- If preplaced targets overlap each other, fallback cannot make the case feasible; return the least-bad deterministic layout for diagnostics.
- If dimensions are invalid, return a failed preflight report.

#### Independent Test Plan

- Two all-soft golden fixture.
- Fixed-shape golden fixture.
- Preplaced obstacle golden fixture.
- Random hard-feasibility fallback property tests.
- Edge-touching legal and positive-overlap illegal differential tests.

#### Open Questions

- What exact obstacle-avoidance convention should be used for preplaced fallback cases?
- Should the fallback use one long row, capped shelves, or skyline placement for large cases?

### Macro and Soft-Constraint Planner

#### Responsibility

Build placement units and intents for grouping clusters, MIB-linked shapes, and boundary-constrained blocks.

#### Non-Responsibility

- Does not perform final packing.
- Does not override immutable geometry.
- Does not accept soft-constraint satisfaction that breaks hard feasibility.

#### Inputs and Outputs

- Inputs: constraint model, dimension plan, and immutable geometry.
- Outputs: placement units, grouping macro records, MIB shape metadata, and boundary intents.

#### Public Interface

Logical interface:

- `plan_soft_constraint_units(model, dimensions, immutable_geometry) -> PlacementUnitSet`

#### Data Structures

- unit records with original block ids and local rectangles;
- grouping macro records keyed by cluster id;
- MIB metadata keyed by MIB group id;
- boundary-intent records keyed by block id or unit id.

#### Internal Design

The planner should:

- keep preplaced blocks as fixed units;
- form grouping macros only for movable blocks where local edge-sharing is possible without moving preplaced blocks;
- associate MIB shape equality with dimensions, not positions;
- attach boundary masks to the affected block or unit;
- preserve the ability to expand every unit back to original block ids.

Grouping macros should prefer simple edge-connected local layouts, such as a horizontal chain, unless implementation later chooses a more compact macro layout.

#### Algorithm Details

Grouping macro construction:

```text
for each cluster group with size > 1:
    collect movable group members
    build local edge-sharing layout using planned dimensions
    record local offsets and macro bbox
    leave preplaced members fixed and record that full soft satisfaction may be impossible
```

MIB planning is mostly metadata because dimensions are already planned. Boundary planning records requested edge/corner contact and allows later snapping after packing and compaction.

#### Dependencies

Depends on Input Normalization, Dimension Planner, and Immutable Geometry Registry.

#### Failure Handling

- If a group contains preplaced blocks that prevent a connected movable macro, record likely grouping violations rather than moving preplaced blocks.
- If blocks in a macro have incompatible dimensions for a chosen local arrangement, fall back to a simpler chain or independent units.
- Boundary constraints that cannot be satisfied without breaking hard feasibility should be counted as soft violations.

#### Independent Test Plan

- Single-block and multi-block cluster fixtures.
- Group containing preplaced block fixture.
- Boundary single-edge and corner masks.
- MIB equal and unequal group metadata fixtures.
- Unit expansion preserves original ids and dimensions.

#### Open Questions

- Should cluster macro layout use a horizontal chain initially, or a compact row/column heuristic?

### Constraint-Aware Constructive Initializer

#### Responsibility

Generate candidate layouts better than fallback by placing immutable obstacles, boundary units, grouped macros, MIB-aware dimensions, and remaining blocks with connectivity-informed order.

#### Non-Responsibility

- Does not decide hard feasibility without preflight.
- Does not mutate immutable positions or dimensions.
- Does not retain final best candidate; that is Candidate Manager's responsibility.

#### Inputs and Outputs

- Inputs: parsed inputs, immutable geometry, dimension plan, placement units, connectivity.
- Outputs: one or more candidate layouts.

#### Public Interface

Logical interface:

- `construct_candidates(model, immutable_geometry, dimensions, units) -> Iterable[Candidate]`

#### Data Structures

- placement unit ordering;
- obstacle-aware packing state;
- expanded candidate positions.

#### Internal Design

Construction should be multi-start but bounded. Candidate seeds may vary by unit order:

- original block id order;
- descending area order;
- connectivity-weight order;
- boundary-first order;
- grouping macro priority order.

Each seed should place preplaced units exactly, then place boundary units and macros, then place remaining units. Every candidate must expand to block positions and go through preflight before it can become best feasible.

#### Algorithm Details

The source docs list skyline, sequence-pair, and B*-tree-style representations as possible packing methods. This detailed design does not silently choose one for the optimized initializer. The first implementation should either confirm a choice before coding or implement the simplest deterministic packer already used by fallback as a baseline initializer.

Required behavior independent of representation:

```text
for each seed_order:
    start with exact preplaced rectangles
    place boundary-intent units near requested frame edges when possible
    place grouping macros as indivisible units
    place remaining units without positive-area overlap
    expand units to per-block rectangles
    yield candidate
```

Boundary placement must be repaired after final bbox is known, because bbox edges are defined by the final layout.

#### Dependencies

Depends on Dimension Planner, Immutable Geometry Registry, Macro and Soft-Constraint Planner, and Proxy Scoring for ordering heuristics.

#### Failure Handling

- If a seed cannot be placed without overlap, discard or repair it before candidate acceptance.
- If a boundary or grouping soft intent fails, keep the candidate if hard feasible and expose the soft violation to scoring.
- If all constructive seeds fail, the fallback remains available.

#### Independent Test Plan

- Synthetic obstacle placement.
- Boundary-first placement fixture.
- Grouping macro expansion fixture.
- Empty connectivity fixture.
- Candidate expands to exactly `block_count` rectangles.

#### Open Questions

- Which optimized packing representation should be used first: skyline, sequence pair, B*-tree-style, or deterministic shelves?
- How many constructive seeds should be generated per block-count range?

### Candidate Manager

#### Responsibility

Track candidate layouts, evaluate hard feasibility and proxy quality, retain the best feasible candidate, and prevent infeasible states from replacing feasible states.

#### Non-Responsibility

- Does not generate moves or placement layouts.
- Does not compute low-level geometry checks itself.
- Does not write results to disk.

#### Inputs and Outputs

- Inputs: fallback, constructive candidates, local-search outputs, preflight checker, proxy scorer.
- Outputs: best feasible candidate, fallback candidate, and optional diagnostics.

#### Public Interface

Logical interface:

- `consider(candidate) -> CandidateDecision`
- `best_feasible() -> Candidate | None`
- `best_feasible_or_fallback() -> Candidate`

Exact API names may remain private.

#### Data Structures

- current fallback candidate;
- best feasible candidate;
- best infeasible diagnostic candidate, optional;
- candidate metadata with source, score, and violation reports.

#### Internal Design

When a candidate is considered:

1. Run hard preflight.
2. If hard feasible, compute or update proxy score and soft report.
3. If no feasible candidate exists, retain it.
4. If a feasible candidate exists, replace it only when proxy score is better under deterministic tie-breaking.
5. If hard infeasible, retain only for diagnostics and never return it while a feasible candidate exists.

Tie-breaking should be deterministic, such as lower proxy score, then lower bbox area, then lower HPWL, then earlier candidate source order.

#### Algorithm Details

Candidate retention invariant:

```text
if candidate.hard_feasible:
    if best_feasible is None or candidate.proxy_score < best_feasible.proxy_score:
        best_feasible = candidate
else:
    best_infeasible_diagnostic = useful_for_debug(candidate)
```

This invariant is critical because local search may temporarily find lower proxy scores that are infeasible.

#### Dependencies

Depends on Hard-Constraint Preflight Checker and Proxy Scoring. Called by Optimizer Entry, Constructive Initializer, and Local Search.

#### Failure Handling

- If proxy scoring fails for a hard-feasible candidate, use conservative fallback score fields and keep feasibility.
- If preflight fails due to malformed candidate shape, reject candidate.
- If fallback was invalid, return the least-bad candidate only because the contest interface has no exception-safe diagnostic channel.

#### Independent Test Plan

- Feasible candidate followed by infeasible lower-score candidate.
- Multiple feasible candidates with deterministic tie-breaking.
- Fallback retention when no optimized candidates pass.
- Malformed candidate rejection.

#### Open Questions

- Which proxy-score tie-breakers should be fixed before implementation?

### Local Search and Repair

#### Responsibility

Improve feasible or repairable candidates through bounded moves while preserving or restoring hard feasibility before acceptance.

#### Non-Responsibility

- Does not define the initial fallback.
- Does not mutate immutable preplaced rectangles or fixed dimensions.
- Does not accept moves directly into final output without Candidate Manager and preflight.

#### Inputs and Outputs

- Inputs: starting candidate, constraint model, immutable geometry, dimension plan, units, proxy scorer, preflight checker, and runtime or iteration budget.
- Outputs: refined candidate states for Candidate Manager.

#### Public Interface

Logical interface:

- `run_local_search(start_candidate, context, budget) -> Iterable[Candidate]`

#### Data Structures

- mutable search state with positions and unit placements;
- move records;
- repair records;
- best local states sent to Candidate Manager.

#### Internal Design

Supported move families from source docs:

- swap order of two movable units;
- move a block or macro to another packing location;
- rotate or adjust a soft block's aspect ratio while preserving area;
- synchronize compatible MIB shapes;
- snap boundary blocks back to required bbox edges;
- compact whitespace without introducing overlaps.

Every move should either:

- preserve hard feasibility by construction; or
- go through repair and preflight before Candidate Manager can accept it.

#### Algorithm Details

Search loop outline:

```text
state = start_candidate
for step in budget:
    move = propose_move(state)
    trial = apply_move(state, move)
    trial = repair_immutable_geometry(trial)
    trial = repair_area_and_mib_dimensions(trial)
    trial = repair_boundary_when_possible(trial)
    trial = compact_without_overlap(trial)
    yield trial for manager consideration
    if manager accepts trial:
        state = trial or accepted search policy state
```

Exact acceptance schedule, temperature policy, iteration counts, and time caps are unresolved. Until confirmed, local search must be bounded by conservative deterministic iteration counts or disabled after construction.

#### Dependencies

Depends on Candidate Manager, Proxy Scoring, Hard-Constraint Preflight Checker, Dimension Planner, Immutable Geometry Registry, and Macro Planner.

#### Failure Handling

- Reject moves that alter preplaced coordinates or immutable dimensions.
- Reject or repair aspect-ratio changes that violate soft-block area tolerance.
- Reject overlap-introducing moves unless compaction/repair removes the overlap.
- If the search budget is exhausted, return the best feasible candidate already retained by Candidate Manager.

#### Independent Test Plan

- Deterministic seeded tests for each move family.
- Immutability preservation tests.
- Search-never-loses-feasibility property tests.
- Boundary snap followed by compaction regression test.
- Incompatible MIB repair does not break area tolerance.

#### Open Questions

- What concrete local runtime or iteration budget should be used for 21, 60, and 120 block cases?
- Should acceptance be greedy, simulated annealing, or best-improving under proxy score?

### Proxy Scoring

#### Responsibility

Rank candidates during construction and local search using evaluator-aligned online proxy terms.

#### Non-Responsibility

- Does not determine hard feasibility.
- Does not compute official score exactly, because baseline HPWL/area and official runtime medians are not passed into `solve()`.
- Does not write or load baseline metrics.

#### Inputs and Outputs

- Inputs: candidate positions, connectivity, pin positions, constraint model, and violation reports.
- Output: deterministic proxy score and optional term breakdown.

#### Public Interface

Logical interface:

- `score_candidate(candidate, parsed_input, reports) -> ProxyScore`

#### Data Structures

- `hpwl_b2b`
- `hpwl_p2b`
- `hpwl_total`
- `bbox_area`
- `soft_violation_estimate`
- `hard_barrier`
- weighted aggregate `proxy_score`

#### Internal Design

Use evaluator helper semantics for:

- B2B HPWL: weighted Manhattan distance between block centers.
- P2B HPWL: weighted Manhattan distance from pins to block centers.
- BBox area: area of the bounding box covering all blocks.
- Soft violations: boundary, grouping, and MIB counts where available.

Hard-infeasible candidates should receive a barrier score so they cannot beat feasible candidates in Candidate Manager.

#### Algorithm Details

Proxy score form is implementation-tunable, but must be deterministic and monotonic with the intended objectives:

```text
score = hpwl_weight * raw_hpwl
      + area_weight * bbox_area
      + soft_weight * violations_relative
      + hard_barrier
```

Exact weights are not specified by source docs. They should be treated as implementation tuning parameters and recorded before coding.

#### Dependencies

Depends on Input Normalization, geometry helper routines, and optional soft-violation helpers. It may reuse evaluator helper functions if import behavior remains acceptable for a contestant optimizer.

#### Failure Handling

- Empty connectivity yields HPWL `0`.
- Non-finite coordinates produce a hard barrier.
- Missing soft-report information defaults to zero only for ranking diagnostics, not for final evaluator claims.

#### Independent Test Plan

- Hand-computed B2B and P2B HPWL fixtures.
- Hand-computed bounding-box area fixtures.
- Empty connectivity returns zero HPWL.
- Hard-infeasible candidate gets barrier score.
- Differential comparison with evaluator helpers on small cases.

#### Open Questions

- What proxy term weights should be used initially?
- Should implementation import evaluator helper functions or duplicate small helper logic to reduce dependency coupling?

### Hard-Constraint Preflight Checker

#### Responsibility

Mirror evaluator hard checks before final return and provide diagnostics for candidate rejection.

#### Non-Responsibility

- Does not optimize layouts.
- Does not compute official cost.
- Does not decide soft-constraint tradeoffs except reporting soft diagnostics if implemented nearby.

#### Inputs and Outputs

- Inputs: candidate positions, active area targets, constraint model, immutable geometry, and target positions.
- Outputs: hard feasibility verdict and violation report.

#### Public Interface

Logical interface:

- `preflight(candidate, parsed_input, immutable_geometry) -> ViolationReport`

#### Data Structures

- pairwise rectangle overlap checks;
- fixed/preplaced comparison fields;
- soft-block area comparison fields;
- diagnostic report.

#### Internal Design

Hard checks must align with evaluator behavior:

- positive finite dimensions are required by this optimizer's contract;
- overlap violation if overlap width and overlap height are both greater than `1e-6`;
- soft-block area violation if relative error is greater than `0.01`;
- fixed/preplaced dimension violation if absolute width or height difference is greater than `1e-4`;
- preplaced coordinate violation if absolute x or y difference is greater than `1e-4`.

Fixed and preplaced blocks must be skipped by the soft-block area tolerance check, matching evaluator behavior.

#### Algorithm Details

Preflight outline:

```text
validate length == block_count
validate finite x, y, w, h and w > 0 and h > 0
count pairwise overlaps using evaluator tolerance
count soft-block area tolerance violations, skipping fixed/preplaced ids
count immutable dimension and preplaced coordinate violations
hard_feasible = all hard counts are zero
```

Soft-constraint checks can be included in the same report or delegated to Proxy Scoring as long as hard feasibility remains separate.

#### Dependencies

Depends on parsed inputs and immutable geometry. May reuse evaluator hard-check functions for differential parity or implement equivalent checks locally.

#### Failure Handling

- Malformed candidates fail preflight.
- Missing `target_positions` means immutable hard checks cannot be applied; validator dummy paths should still run.
- If evaluator and local preflight disagree during implementation, stop and resolve the conflict before changing shared contest behavior.

#### Independent Test Plan

- Edge-touching legal fixture.
- Positive-overlap illegal fixture.
- Area tolerance boundary fixture.
- Fixed and preplaced immutability fixtures.
- Differential tests against evaluator helpers.
- Randomized hard-feasibility fixtures.

#### Open Questions

- Should preflight report soft violations too, or should soft reporting remain entirely in Proxy Scoring?

### Optional ML Initializer

#### Responsibility

Optionally provide learned seed data such as ordering, centers, or aspect ratios after data access and final packaging rules are confirmed.

#### Non-Responsibility

- Does not guarantee correctness.
- Does not replace deterministic legalization or preflight.
- Does not require training data for the baseline solver.

#### Inputs and Outputs

- Inputs: model artifact if allowed, normalized areas, connectivity, pin positions, and constraints.
- Outputs: advisory seed ordering, centers, or aspect ratios.

#### Public Interface

Logical interface, only if approved later:

- `predict_seed(parsed_input) -> MLSeed`

No ML interface is required for the initial implementation.

#### Data Structures

- model artifact path, if allowed;
- normalized feature tensors;
- advisory predictions;
- seed metadata.

#### Internal Design

The ML initializer must run before constructive initialization and after parsing. Predictions must be fed into the same dimension planner, legalizer, and preflight path as heuristic seeds.

#### Algorithm Details

No algorithm is selected in this detailed design. The proposal suggests predicting normalized centers, order, or aspect ratios. Any chosen model must be optional and advisory.

#### Dependencies

Depends on Input Normalization and Constructive Initializer. May depend on PyTorch only if final packaging and artifact rules allow it.

#### Failure Handling

- If model load fails, continue without ML.
- If prediction shape is invalid, discard ML seed.
- If ML seed is infeasible after legalization, Candidate Manager rejects it.

#### Independent Test Plan

- Missing model artifact falls back to heuristic path.
- Invalid prediction shape is rejected.
- ML seed cannot bypass hard preflight.

#### Open Questions

- Are model weights allowed in final submission?
- What artifact size and path restrictions apply?
- Is the full training dataset accessible from this workspace through an approved workflow?

## Cross-Module Contracts

| Contract | Producer | Consumer | Requirement |
| --- | --- | --- | --- |
| Active block ids | Input Normalization and Constraint Parser | All modules | Preserve original ids and output order `[0, block_count)`. |
| Constraint model | Input Normalization and Constraint Parser | Dimension Planner, Macro Planner, Proxy Scoring, Preflight | Columns are interpreted as `[fixed, preplaced, mib, cluster, boundary]`. |
| Immutable geometry | Immutable Geometry Registry | Dimension Planner, Fallback, Constructive Initializer, Local Search, Preflight | Fixed dimensions and preplaced rectangles are authoritative and immutable. |
| Dimension plan | Dimension Planner | Fallback, Macro Planner, Constructive Initializer, Local Search | Every block has positive hard-feasible dimensions unless input is invalid. |
| Placement units | Macro and Soft-Constraint Planner | Constructive Initializer, Local Search | Units must expand back to exact original block ids. |
| Candidate positions | Fallback, Constructive Initializer, Local Search | Candidate Manager, Proxy Scoring, Preflight | Length equals `block_count`; entries are rect tuples by block id. |
| Hard feasibility report | Hard-Constraint Preflight Checker | Candidate Manager, Optimizer Entry | Only candidates with zero hard violations can be preferred over fallback. |
| Proxy score | Proxy Scoring | Candidate Manager, Local Search | Used for ranking only; not an official score. |
| Best feasible retention | Candidate Manager | Optimizer Entry | Final return must be best feasible candidate if one exists, otherwise fallback. |
| ML seed | Optional ML Initializer | Constructive Initializer | Advisory only and never correctness-critical. |

## End-to-End Workflow

1. Evaluator imports `my_optimizer.py`, discovers the optimizer class, and calls `solve()`.
2. `solve()` creates per-call state and normalizes active inputs.
3. Parser derives fixed, preplaced, MIB, cluster, and boundary constraints.
4. Immutable Geometry Registry extracts exact target dimensions and rectangles.
5. Dimension Planner assigns hard-feasible dimensions and records MIB compatibility.
6. Deterministic Legal Fallback creates a baseline candidate and sends it to Candidate Manager.
7. Macro and Soft-Constraint Planner creates grouping, MIB, and boundary unit intents.
8. Constructive Initializer creates one or more candidate layouts and sends each to Candidate Manager.
9. Candidate Manager preflights and scores each candidate while retaining best feasible.
10. Local Search and Repair refines candidates within budget and sends trial states to Candidate Manager.
11. Optimizer Entry asks Candidate Manager for the best feasible candidate or fallback.
12. `solve()` returns exactly `block_count` rect tuples.

## Test Strategy Mapping

| Test-plan requirement | Coverage |
| --- | --- |
| `solve()` returns exactly `block_count` tuples | Optimizer Entry unit tests and validator full dummy solve. |
| Finite numeric values and positive dimensions | Hard-Constraint Preflight Checker and Optimizer Entry smoke tests. |
| Input normalization for tensors, lists, active slicing, and padded sentinels | Input Normalization and Constraint Parser unit tests. |
| Constraint parsing for fixed, preplaced, MIB, grouping, and boundary | Input Normalization and Constraint Parser unit tests. |
| Fixed-shape exact dimensions | Immutable Geometry Registry, Dimension Planner, Preflight unit tests. |
| Preplaced exact location and dimensions | Immutable Geometry Registry, Fallback, Constructive Initializer, Local Search, Preflight tests. |
| Soft-block area within 1% | Dimension Planner and Preflight unit/property tests. |
| No overlap, edge-touching legal | Fallback, Constructive Initializer, Local Search, and Preflight differential tests. |
| Boundary soft constraints | Macro Planner, Constructive Initializer, Local Search boundary snap, Proxy Scoring soft-report tests. |
| Grouping soft constraints | Macro Planner grouping macro tests and Proxy Scoring soft-report tests. |
| MIB soft constraints | Dimension Planner, Macro Planner metadata, Local Search MIB sync, Proxy Scoring tests. |
| Candidate retention of best feasible state | Candidate Manager unit and property tests. |
| Local search repairable moves | Local Search seeded move tests and regression tests. |
| Proxy HPWL and bbox match evaluator helpers | Proxy Scoring hand-computed and differential tests. |
| Internal preflight agrees with evaluator hard checks | Hard-Constraint Preflight Checker differential tests. |
| Synthetic all-soft solve integration | Optimizer Entry, Fallback, Preflight integration path. |
| Synthetic fixed/preplaced solve integration | Immutable Geometry Registry, Dimension Planner, Fallback, Preflight integration path. |
| Synthetic boundary/grouping/MIB integration | Macro Planner, Constructive Initializer, Proxy Scoring integration path. |
| Contest validator quick/full | Known gates after `my_optimizer.py` exists and user approves. |
| Single validation case and full validation evaluator | Known gates after implementation and user approval because they write JSON and load validation data. |
| Golden tests | Mapped to relevant modules: all-soft and fixed to Fallback; edge/overlap to Preflight; preplaced to Immutable/Fallback; boundary/grouping/MIB to Macro/Dimension/Proxy. |
| Randomized/property tests | Parser, Fallback, Dimension Planner, Candidate Manager, Local Search, and Preflight. |
| Performance benchmarks | Optimizer Entry budget policy and Local Search bounded execution. Exact pass/fail seconds remain open. |
| Regression tests | Candidate Manager, Local Search, Boundary repair, MIB handling, Preflight, Parser. |

## Quality Gates

Documentation-only changes have no discovered executable quality gate beyond reviewing the affected Markdown file.

Known future gates for optimizer implementation, all requiring user approval before execution:

```bash
cd iccad2026contest
python iccad2026_evaluate.py --validate my_optimizer.py
python iccad2026_evaluate.py --evaluate my_optimizer.py --test-id 0
python iccad2026_evaluate.py --evaluate my_optimizer.py
```

Additional known commands exist for `--info`, `--validate --quick`, `--score`, `--baseline`, `--visualize`, `--training`, and `training_example.py`. Commands that evaluate, visualize, train, install dependencies, write JSON/PNG outputs, or may download datasets require explicit approval under repository rules.

No repository-defined build, unit-test, lint, format, type-check, static-analysis, or CI command was discovered.

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Fallback is feasible but poor quality | Treat fallback as correctness path only; improve with constructive seeds and bounded local search. |
| Preplaced obstacles make naive shelves overlap | Keep preplaced rectangles in immutable obstacle set; use preflight before accepting fallback or construction. |
| MIB equality conflicts with hard area targets | Preserve hard area feasibility and accept MIB soft violation. |
| Boundary snapping breaks after compaction | Run boundary repair after compaction or re-check boundary soft violations before scoring. |
| Local search replaces feasible state with infeasible lower proxy score | Candidate Manager invariant prevents infeasible replacement. |
| Proxy score diverges from official hidden score | Use evaluator-aligned HPWL, bbox, and soft semantics; treat proxy as ranking only. |
| Runtime grows on 120-block cases | Require bounded budget policy before implementation; keep fallback always available. |
| Helper modules or model artifacts are disallowed | Initial implementation remains single-file and heuristic/legalizer-first. |
| Evaluator and docs disagree | Stop and ask which source to treat as authoritative before changing contest behavior. |
| Commands write generated files or download data | Do not run them without explicit approval and output-file plan. |

## Assumptions

- The initial solver will be implemented in `iccad2026contest/my_optimizer.py`.
- Logical modules can be implemented as private helpers inside one file.
- `target_positions` is passed to `solve()` as shown in the evaluator.
- Hidden cases follow the validation format and block-count range from contest docs.
- Fixed and preplaced target geometry is internally consistent in official cases.
- The implementation may use Python standard library plus installed contest dependencies, but dependency installation status is unknown.
- Training data and model weights are not required for correctness.
- Exact local runtime budgets and optimized packing representation are intentionally left unresolved until implementation planning.

## Open Questions

- What final submission packaging is allowed beyond one optimizer Python file?
- Are helper modules allowed, or should implementation remain strictly single-file?
- Are model weights allowed in final submission, and what size/path limits apply?
- Is the full training dataset mounted in this workspace, only available on the lab server, or accessible through another approved workflow?
- What concrete local runtime or iteration budget should define pass/fail performance for 21-block, 60-block, and 120-block cases?
- Which optimized constructive packing representation should be implemented first: skyline, sequence pair, B*-tree-style, or deterministic shelves?
- What initial proxy-score weights should be used for HPWL, bounding-box area, and soft violations?
- Should synthetic tests be a standalone script, a future `pytest` suite, or ad hoc fixtures until repository test tooling exists?
- Should evaluator commands use explicit `--output` paths to keep generated results outside versioned files during future runs?
- If contest README/PDF and evaluator behavior disagree during implementation, which source should control the specific conflict?
