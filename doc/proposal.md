# Proposal: Best-Available FloorSet Contest Optimizer

## Objective

Implement a contest-compliant Python optimizer for the ICCAD 2026 FloorSet Challenge that returns one `(x, y, width, height)` tuple per block from `solve()`. The implementation should aim for the best practical score by prioritizing hard-constraint feasibility first, then reducing HPWL, bounding-box area, soft constraint violations, and official runtime.

The implementation target should be a copied optimizer file such as `iccad2026contest/my_optimizer.py`, not direct edits to `iccad2026contest/optimizer_template.py`.

## Source Inputs

- User objective: propose a best-available implementation plan for the FloorSet/ICCAD 2026 optimizer.
- `doc/problem-brief.md`: existing contest summary, constraints, scoring, data, assumptions, and open questions.
- `doc/repo-map.md`: existing repository map and current project-state notes.
- `doc/quality-gates.md`: existing validation and evaluator command inventory.
- `iccad2026contest/README.md`: contest guide, scoring formula, commands, dataset notes, and v10 changelog.
- `iccad2026contest/FloorplanningContest_ICCAD_2026_v10.pdf`: problem statement and objective-function specification.
- `iccad2026contest/iccad2026_evaluate.py`: evaluator behavior, hard and soft constraint checks, total-score weighting, optimizer loading, and `target_positions` passing.
- `iccad2026contest/optimizer_template.py`: expected optimizer class pattern and baseline B*-tree simulated annealing implementation.

## Current Project State

The repository is a Python project with the contest framework under `iccad2026contest/`. Existing planning docs are present in `doc/`; this proposal adds `doc/proposal.md`.

The evaluator loads an optimizer Python file, finds an optimizer class, and calls:

```python
solve(block_count, area_targets, b2b_connectivity, p2b_connectivity,
      pins_pos, constraints, target_positions)
```

`target_positions` is important: fixed-shape blocks receive required `(w, h)`, while preplaced blocks receive required `(x, y, w, h)`. The existing template baseline uses fixed/preplaced dimensions for initialization but does not fully handle preplaced locations, boundary constraints, MIB, or grouping.

Local validation data is present under `LiteTensorDataTest/`. Full training data availability in this workspace is unknown; the user has reported lab-server availability.

## Problem Summary

Each case has 21 to 120 rectangular blocks, weighted block-to-block connectivity, weighted pin-to-block connectivity, fixed pin locations, and per-block constraint columns `[fixed, preplaced, mib, cluster, boundary]`.

The scoring model makes feasibility the first-order requirement. Any overlap, soft-block area violation above 1%, fixed-shape dimension mismatch, or preplaced location/dimension mismatch gives cost `10.0`. Any feasible solution is capped below `10.0`, so a weak but feasible layout beats an infeasible one.

Among feasible layouts, lower score comes from lower relative HPWL gap, lower bounding-box area gap, fewer soft violations, and better official runtime. Local evaluation sets runtime factor to `1.0`, so local score primarily measures layout quality and soft-constraint handling.

## Constraints

- Hard constraints:
  - no block overlaps;
  - soft-block `w * h` within 1% of target area;
  - fixed-shape block dimensions exactly match `target_positions`;
  - preplaced block location and dimensions exactly match `target_positions`.
- Soft constraints:
  - boundary blocks touch all requested bbox edge bits;
  - grouping blocks form one connected component through edge sharing;
  - MIB blocks share identical `(w, h)` where compatible with hard area requirements.
- Scoring constraints:
  - HPWL and bbox gaps are clamped from below, so beating the baseline gives no extra local score bonus;
  - large cases dominate final score through `exp(n / 12)` weighting;
  - official runtime can help, but the speed bonus is capped at 30% and slowness is uncapped.
- Workflow constraints:
  - avoid generated result files and datasets in commits;
  - ask before commands that install, download, evaluate, train, visualize, or write generated outputs.

## Proposed Approach

Use a hybrid, legality-preserving optimizer with three layers:

1. A deterministic legalizer that can always produce a feasible layout when fixed and preplaced inputs are internally consistent.
2. A constraint-aware constructive initializer that builds better candidates than the template baseline by honoring preplaced obstacles, fixed dimensions, boundary blocks, MIB shape groups, and grouping clusters.
3. A bounded local search/refinement loop that mutates only through repairable moves and always returns the best feasible candidate found.

This should be the primary implementation because it is robust on hidden cases and does not depend on training-data access or model-packaging rules. A PyTorch learned initializer should be treated as an enhancement path: useful for best score if training data and final submission packaging allow model weights, but not required for a valid solver.

## Algorithm Strategy

### Baseline Method

Implement a simple, guaranteed-feasible shelf or skyline packer:

- apply exact preplaced rectangles first as fixed obstacles;
- assign fixed-shape block dimensions from `target_positions`;
- assign soft block dimensions as area-preserving squares;
- place movable blocks outside or beside the preplaced obstacle bounding box in non-overlapping shelves;
- return the shelf result if all optimized candidates fail validation.

This baseline is expected to have poor HPWL and area, but it should avoid cost `10.0` and give a reliable fallback.

### Intended Optimized Method

Build a multi-start solver around legality-preserving candidates:

- Parse constraints once into block sets, MIB groups, cluster groups, and boundary bitmasks.
- Choose dimensions before placement:
  - fixed/preplaced dimensions are immutable;
  - soft blocks use area-preserving dimensions;
  - compatible MIB groups share one shape;
  - incompatible MIB groups preserve hard area feasibility and accept the unavoidable soft violation.
- Assemble connected grouping clusters as small macro layouts where possible, then treat each macro as a movable unit during global placement.
- Place boundary-constrained blocks on an outer frame so required edge or corner contact can be preserved after compaction.
- Pack remaining movable units with a skyline, sequence-pair, or B*-tree-style representation that treats preplaced blocks as obstacles.
- Refine with bounded moves:
  - swap order;
  - move a block or macro to another packing location;
  - rotate or change a soft block aspect ratio while preserving area;
  - synchronize compatible MIB shapes;
  - snap boundary blocks back to required bbox edges;
  - compact whitespace without introducing overlaps.
- Score candidate moves with a contest-shaped proxy: weighted HPWL, bbox area, overlap/area infeasibility barriers, and soft-constraint penalties. Since baseline metrics are not passed into `solve()`, raw HPWL and bbox area are the available online proxies for score gaps.
- Keep the best feasible candidate across restarts and return it even if the last search state is worse.

### Optional ML-Guided Initializer

If training data access and final submission packaging are resolved, train a PyTorch model to predict normalized block centers, order, or aspect ratios from areas, connectivity, pin positions, and constraint features. Use model output only as an initializer; the deterministic legalizer remains mandatory before returning a solution.

This avoids depending on the model for correctness and keeps the online solver robust on hidden cases. It also aligns with the contest motivation for data-driven methods without reverse-engineering the dataset generator.

### Correctness Strategy

Every returned candidate should pass an internal preflight check equivalent to the evaluator's hard constraints:

- exact fixed/preplaced dimensions and preplaced positions within evaluator tolerance;
- positive finite dimensions;
- soft-block area relative error at or below 1%;
- pairwise non-overlap with edge-touching allowed.

If the optimized path cannot prove feasibility, return the deterministic fallback. Soft constraints should never be fixed at the expense of hard constraints.

### Performance Strategy

Use block-count-aware time budgets because cases with 101 to 120 blocks dominate final weighted score, but official runtime penalties still matter. The solver should avoid unbounded annealing and use a fixed number of restarts or iterations scaled by `block_count`.

Use incremental scoring for local moves where practical, especially for HPWL and bbox estimates. Keep geometry checks simple for rectangles; avoid Shapely inside the tight optimization loop unless profiling shows it is acceptable.

## Alternatives Considered

- Template B*-tree simulated annealing only: useful as a starting point, but it does not fully handle preplaced locations, boundary constraints, MIB, or grouping, so it risks infeasible or high-violation results.
- Pure random or shelf packing: robust as a fallback, but too weak for HPWL and area.
- ML-only prediction: potentially fast, but unsafe because final evaluation uses exact hard constraints and hidden cases; legalization is still required.
- Full exact optimization or SMT/MIP: attractive for correctness on small cases, but likely too slow for 100 hidden cases up to 120 blocks under runtime-sensitive scoring.

## Module Candidates

- `iccad2026contest/my_optimizer.py`: primary implementation file. Prefer keeping the contest solver self-contained here unless final packaging rules support multiple files.
- Internal sections or classes inside `my_optimizer.py`:
  - constraint parser;
  - dimension planner;
  - legal shelf/skyline fallback;
  - boundary-frame placer;
  - cluster/MIB macro builder;
  - local search state and move operators;
  - hard-constraint preflight checker.
- Optional, only if packaging is confirmed:
  - `iccad2026contest/model_weights.pt` or similar for a learned initializer;
  - a training script outside the submission path for generating the model.

## Milestones

1. Create `my_optimizer.py` from the template and implement the deterministic legal fallback.
2. Add exact handling for fixed-shape and preplaced blocks, including internal hard-constraint preflight checks.
3. Add constraint-aware constructive placement for boundary, MIB, and grouping constraints.
4. Add local search with repair, best-feasible tracking, and block-count-aware budgets.
5. Run validation and single-case evaluations, inspect infeasible cases first, then tune quality.
6. If data and packaging allow it, add a PyTorch learned initializer and compare against the heuristic initializer.

## Validation Plan

Use small synthetic fixtures before contest evaluation:

- all-soft case with 2 to 5 blocks verifies area preservation and no overlap;
- fixed-shape case verifies exact `(w, h)`;
- preplaced case verifies exact `(x, y, w, h)` and obstacle avoidance;
- boundary edge and corner cases verify bbox contact semantics;
- compatible and incompatible MIB cases verify hard-area priority;
- grouping case verifies abutment and connected components;
- stress case with 120 blocks checks runtime and non-overlap.

Then use the contest gates, with approval because some commands write results or may load datasets:

```bash
cd iccad2026contest
python iccad2026_evaluate.py --validate my_optimizer.py
python iccad2026_evaluate.py --evaluate my_optimizer.py --test-id 0
python iccad2026_evaluate.py --evaluate my_optimizer.py
```

Primary measurable targets:

- `--validate` passes;
- 100/100 local validation cases feasible;
- no fixed/preplaced dimension violations;
- no overlaps;
- runtime remains bounded on large cases;
- local total score improves over the deterministic fallback and template baseline.

## Risks and Tradeoffs

- Strong soft-constraint handling can increase bbox area or HPWL; hard constraints and feasibility should win.
- MIB constraints may conflict with hard area targets if grouped blocks have incompatible areas; the solver should preserve hard feasibility and accept the soft penalty.
- Boundary constraints are sensitive because bbox edges are defined by the final layout; late compaction can accidentally break them unless boundary snapping is part of the repair step.
- Training-data access and model-weight packaging are unresolved, so an ML initializer should not be the only path to competitive behavior.
- Local runtime scoring is neutral, while official runtime scoring is relative to other submissions; local tuning should track wall time separately.

## Assumptions

- The optimizer may import from `iccad2026_evaluate.py` and use existing repository dependencies listed in the contest requirements.
- Hidden test cases follow the same format and block-count range as validation.
- A single optimizer file is the safest initial submission shape unless final contest packaging rules say otherwise.
- The best near-term path is a robust heuristic/legalizer first, with ML used as an initializer only after correctness is stable.

## Open Questions

- What final submission packaging is allowed beyond an optimizer Python file?
- Is the full training dataset available from this workspace, mounted locally, or only on the lab server?
- Are model weights allowed in the final submission, and if so, what size and path constraints apply?
- What official runtime target is acceptable for large hidden cases relative to expected competitors?
- Should the next implementation use a single-file optimizer only, or is a small helper-module layout acceptable?
