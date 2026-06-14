# Test Plan

## Purpose

This plan defines how to verify a contest-compliant FloorSet optimizer before detailed implementation and tuning. "Done" means verification is based on observable pass/fail checks: the optimizer interface loads, hard constraints are preserved, soft-constraint behavior is measured, integration with `iccad2026_evaluate.py` works, and performance is bounded by an explicit implementation budget.

The plan is intentionally a planning artifact only. It does not implement tests, run evaluators, install dependencies, train models, or create generated result files.

Status labels used below:

- `Existing`: behavior or check already exists in the repository or evaluator.
- `Planned`: test or check should be implemented for the optimizer.
- `Missing`: no repository support or test currently exists.
- `Unknown`: source material does not define the needed command, threshold, or rule.

## Source Requirements

Sources read for this plan:

- `doc/proposal.md`: optimizer objective, feasibility-first strategy, module candidates, validation plan, risks, and open questions.
- `doc/high-level-design.md`: authoritative HLD module list, data flow, interfaces, contracts, and quality-gate alignment.
- `doc/problem-brief.md`: contest inputs, outputs, constraints, scoring formula, data scale, and assumptions.
- `doc/repo-map.md`: repository structure, source files, existing test status, CLI entry points, and data notes.
- `doc/quality-gates.md`: discovered commands, commands not run, missing quality gates, and recommended done criteria.
- `iccad2026contest/optimizer_template.py`: optimizer class pattern, `solve()` signature, return shape, and baseline limitations.
- `iccad2026contest/iccad2026_evaluate.py`: evaluator functions for HPWL, bounding-box area, overlap, area tolerance, fixed/preplaced hard constraints, cost, total score, and submission validation.

Requirements extracted:

- `solve()` must return exactly `block_count` `(x, y, width, height)` tuples.
- Returned values must be finite numbers with positive dimensions.
- Hard constraints are no overlap, soft-block area within 1%, exact fixed-shape dimensions, and exact preplaced position/dimensions.
- Soft constraints are boundary contact, grouping edge connectivity, and MIB equal dimensions.
- Feasible candidates must be retained over later infeasible search states.
- The implementation target is a copied optimizer file such as `iccad2026contest/my_optimizer.py`.
- Contest validation and evaluation commands are known but were not run.

Ambiguities and missing source material:

- Final submission packaging beyond the optimizer interface is `Unknown`.
- Official runtime competitiveness target is `Unknown`.
- Conventional unit-test, lint, format, type-check, static-analysis, and CI commands are `Missing`.
- Whether helper modules or model weights are allowed in final submission is `Unknown`.

## Test Scope

Covered scope:

- Optimizer interface and return format for `iccad2026contest/my_optimizer.py`.
- Input normalization for tensors, Python lists, active block slicing, padded `-1` sentinels, and constraint columns.
- Constraint parsing for fixed, preplaced, MIB, grouping/cluster, and boundary bitmask fields.
- Immutable target handling for fixed-shape and preplaced blocks.
- Dimension planning for ordinary soft blocks, fixed/preplaced blocks, and compatible/incompatible MIB groups.
- Deterministic legal fallback placement with preplaced obstacles.
- Macro and soft-constraint planning for grouping, MIB, and boundary constraints.
- Constraint-aware constructive initialization.
- Candidate retention and best-feasible selection.
- Local search moves, repair, boundary snapping, MIB synchronization, and compaction.
- Proxy scoring for HPWL, bounding-box area, soft violations, and infeasibility barriers.
- Hard-constraint preflight behavior compared with evaluator hard checks.
- Integration with `iccad2026_evaluate.py` validation and evaluation paths.
- Runtime behavior on 21-block, mid-size, and 120-block cases.

## Non-Tested Scope

Out of scope for this phase:

- Correctness of `iccad2026_evaluate.py`, dataset loaders, PyTorch, NumPy, Shapely, or Matplotlib.
- Training-data download, training jobs, ML model quality, and model-weight packaging.
- Reverse-engineering or validating the dataset generator.
- Final hidden-test performance, because hidden data is unavailable.
- GUI/display behavior from visualization commands.
- Generated result JSON, solution JSON, PNG, logs, caches, and dataset artifacts, except as outputs from approved future evaluator runs.
- Broad refactors of evaluator, loader, dataset, visualization, or utility code.

## Smoke Tests

| Status | Check | Command or Method | Pass/Fail Criteria |
| --- | --- | --- | --- |
| `Known, not run` | Contest info import smoke | From `iccad2026contest/`: `python iccad2026_evaluate.py --info` | Pass if command exits 0 and prints contest information without writing intended output files. |
| `Known, not run` | Quick submission validation | From `iccad2026contest/`: `python iccad2026_evaluate.py --validate my_optimizer.py --quick` | Pass if optimizer file exists, compiles, imports, and exposes a discoverable optimizer class. |
| `Known, not run` | Full submission validation dummy solve | From `iccad2026contest/`: `python iccad2026_evaluate.py --validate my_optimizer.py` | Pass if quick checks pass and the validator's 5-block dummy `solve()` returns a list of 5 tuples. |
| `Planned` | Local helper import smoke | Import `my_optimizer.py` in a test process. | Pass if importing has no side effects, no data access, no generated files, and no dependency on local training data. |
| `Planned` | Minimal fallback smoke | Call the deterministic fallback on a 2-block all-soft synthetic case. | Pass if it returns two finite positive rectangles, preserves area within 1%, and has zero overlaps. |
| `Missing` | Repository unit-test runner | Unknown. | No pass/fail command exists until a runner is added or approved. |

## Unit Tests by Module

| HLD Module | Verification Method | Status | Pass/Fail Criteria |
| --- | --- | --- | --- |
| Optimizer Entry | Constructor and `solve()` signature tests with tensors matching evaluator signature. | `Planned` | Pass if `solve(block_count, area_targets, b2b_connectivity, p2b_connectivity, pins_pos, constraints, target_positions)` accepts all arguments and returns exactly `block_count` tuples. |
| Input Normalization and Constraint Parser | Synthetic tensors with active rows, padded `-1` rows, empty connectivity, and all five constraint columns. | `Planned` | Pass if active block ids, fixed ids, preplaced ids, MIB group ids, cluster ids, and boundary masks match expected sets. |
| Immutable Geometry Registry | Fixed and preplaced synthetic targets. | `Planned` | Pass if fixed blocks own target `(w, h)` exactly and preplaced blocks own target `(x, y, w, h)` exactly. |
| Dimension Planner | Soft, fixed, preplaced, compatible MIB, and incompatible MIB cases. | `Planned` | Pass if ordinary soft areas are within 1%, fixed/preplaced dimensions are immutable, compatible MIB blocks share `(w, h)`, and incompatible MIB blocks preserve hard area feasibility. |
| Deterministic Legal Fallback | Shelf/skyline cases with and without preplaced obstacles. | `Planned` | Pass if returned fallback has positive finite dimensions, zero overlap violations under `check_overlap`, exact immutable geometry, and soft areas within 1%. |
| Macro and Soft-Constraint Planner | Grouping, MIB, and boundary fixture parsing. | `Planned` | Pass if macro/unit records preserve original block ids, dimensions, group membership, and boundary edge intents. |
| Constraint-Aware Constructive Initializer | Synthetic obstacle, boundary, group, and connectivity cases. | `Planned` | Pass if constructed candidates expand to one rectangle per block and do not violate hard constraints before local search. |
| Candidate Manager | Candidate sequences containing feasible, infeasible, and lower-proxy-score states. | `Planned` | Pass if best feasible candidate is retained and no infeasible candidate replaces it. |
| Local Search and Repair | Deterministic seeded move tests for swap, move, aspect update, MIB sync, boundary snap, and compaction. | `Planned` | Pass if each move either preserves hard feasibility or is rejected/repaired before candidate acceptance. |
| Proxy Scoring | Hand-computed HPWL, bbox area, and soft violation examples. | `Planned` | Pass if proxy HPWL and bbox terms match evaluator helpers on small cases within tolerance and hard infeasibility receives a barrier score. |
| Hard-Constraint Preflight Checker | Differential tests against evaluator helpers `check_overlap`, `check_area_tolerance`, and `check_dimension_hard_constraints`. | `Planned` | Pass if preflight feasibility agrees with evaluator hard checks on all golden and randomized cases. |
| Optional ML Initializer | Packaging and artifact checks. | `Missing` | Missing until final packaging and model-weight rules are resolved. If added later, pass only if ML output is advisory and legalizer/preflight still enforce hard constraints. |

## Integration Tests

| Status | Integration Path | Pass/Fail Criteria |
| --- | --- | --- |
| `Planned` | `solve()` on synthetic all-soft inputs through internal preflight. | Pass if output format is valid, all soft areas are within 1%, and `check_overlap` reports 0. |
| `Planned` | `solve()` on synthetic fixed/preplaced inputs through internal preflight. | Pass if fixed dimensions and preplaced `(x, y, w, h)` match `target_positions` within evaluator tolerance. |
| `Planned` | `solve()` on synthetic boundary/grouping/MIB inputs through proxy soft-violation scoring. | Pass if hard constraints remain feasible and soft violation counts are measured without crashing. |
| `Known, not run` | Contest validator quick mode. | Pass if `python iccad2026_evaluate.py --validate my_optimizer.py --quick` exits 0. |
| `Known, not run` | Contest validator full mode. | Pass if `python iccad2026_evaluate.py --validate my_optimizer.py` exits 0. |
| `Known, not run` | Single validation-case evaluator. | Pass if `python iccad2026_evaluate.py --evaluate my_optimizer.py --test-id 0` exits 0 and reports a feasible result for case 0. This command writes results JSON by default. |
| `Known, not run` | Full local validation evaluator. | Pass if `python iccad2026_evaluate.py --evaluate my_optimizer.py` exits 0 and reports 100/100 feasible local validation cases. This command writes results JSON by default. |

## Golden Test Cases

Golden tests should be deterministic and small enough to audit by hand. If detailed design changes the exact fallback packing convention, update only the exact expected coordinates while preserving the pass/fail intent.

| Status | Case | Input Summary | Expected Output or Behavior |
| --- | --- | --- | --- |
| `Planned` | Two all-soft blocks | Areas `[4, 9]`, no constraints, no connectivity. | Deterministic fallback expected rectangles: block 0 `(0, 0, 2, 2)`, block 1 `(2, 0, 3, 3)`; area violations `0`; overlap violations `0`; bbox area `15`. |
| `Planned` | Edge-touching is legal | Rectangles `(0, 0, 1, 1)` and `(1, 0, 1, 1)`. | Evaluator `check_overlap` returns `0`; internal preflight accepts the layout. |
| `Planned` | Positive overlap is illegal | Rectangles `(0, 0, 1, 1)` and `(0.5, 0, 1, 1)`. | Evaluator `check_overlap` returns `1`; internal preflight rejects the layout. |
| `Planned` | Fixed-shape block | Block 0 fixed target `w=2`, `h=5`; block 1 soft area `4`. | Block 0 dimensions exactly `(2, 5)`; block 1 area within 1%; no overlaps. Fallback expected block 0 `(0, 0, 2, 5)`, block 1 `(2, 0, 2, 2)` if ordered by id. |
| `Planned` | Preplaced obstacle | Block 0 preplaced target `(10, 3, 4, 2)`; block 1 soft area `9`. | Block 0 exactly `(10, 3, 4, 2)`; block 1 does not overlap block 0; internal preflight and evaluator hard checks agree. |
| `Planned` | Boundary corner | Block 0 soft area `4`, boundary bitmask `5` for left+top; block 1 soft area `4`. | Final bbox satisfies `x0 == min_x` and `y0 + h0 == max_y` within tolerance; hard constraints remain feasible. |
| `Planned` | Compatible MIB | Blocks 0 and 1 both soft area `4`, same MIB group id. | Both blocks use identical dimensions, expected `(2, 2)` under square planner; MIB soft violations `0`; hard violations `0`. |
| `Planned` | Incompatible MIB | Blocks 0 and 1 areas `[4, 9]`, same MIB group id. | Areas remain within 1%; MIB equal-shape may be violated; hard feasibility has priority over MIB soft repair. |
| `Planned` | Grouping component | Three 1x1 blocks in the same cluster group. | Macro planner can produce edge-connected coordinates such as `(0,0)`, `(1,0)`, `(2,0)`; grouping connected components count is `1` when macro placement is enabled. |
| `Planned` | Empty connectivity | Valid area and constraints with zero B2B and P2B edges. | HPWL proxy returns `0`; construction and preflight do not require connectivity. |

## Oracle or Reference Implementation Strategy

- `Existing`: Use evaluator helpers as the primary differential oracle for hard geometry and metrics where available: `check_overlap`, `check_area_tolerance`, `check_dimension_hard_constraints`, `calculate_hpwl_b2b`, `calculate_hpwl_p2b`, `calculate_bbox_area`, and `compute_cost`.
- `Planned`: Implement an internal hard-constraint preflight checker and compare its verdict with evaluator helpers on every golden and randomized fixture.
- `Planned`: For tiny all-soft cases with fixed square dimensions, use a simple brute-force reference over block orderings and shelf placements to confirm that candidate scoring and fallback feasibility are internally consistent.
- `Planned`: For grouping, MIB, and boundary soft constraints, compare internal soft-violation counts against evaluator soft-constraint behavior through `evaluate_solution` on synthetic cases when test harness access is implemented.
- `Missing`: No separate official reference solver exists for optimal HPWL or bounding-box area.
- `Unknown`: Exact hidden-test baseline metrics are unavailable inside `solve()`, so online proxy scoring cannot be judged against hidden official gaps during unit tests.

## Randomized or Property Tests

Randomized tests should use deterministic seeds and bounded instance sizes so failures are reproducible.

| Status | Property | Seeds and Bounds | Pass/Fail Criteria |
| --- | --- | --- | --- |
| `Planned` | Output shape and numeric validity | Seeds `0..49`, block counts `2..12` for helper tests and `21..30` for solve-level tests. | Pass if every output has exactly `n` finite numeric tuples and positive dimensions. |
| `Planned` | Hard feasibility fallback | Seeds `0..99`, random soft areas in `[1, 100]`, optional non-overlapping preplaced obstacles. | Pass if deterministic fallback has zero overlaps, soft area violations `0`, and exact immutable targets. |
| `Planned` | Fixed/preplaced immutability | Seeds `0..49`, random fixed/preplaced subsets with internally consistent targets. | Pass if dimensions/locations match target values within evaluator tolerance. |
| `Planned` | Boundary bitmask handling | Seeds `0..49`, boundary masks from `{1,2,4,8,5,6,9,10}`. | Pass if hard constraints remain feasible and boundary contact is either satisfied or counted as a soft violation, never hidden. |
| `Planned` | MIB compatibility handling | Seeds `0..49`, groups with equal and unequal target areas. | Pass if equal-area MIB groups share shape when planned compatible, and unequal-area groups do not break hard area feasibility. |
| `Planned` | Search never loses feasibility | Seeds `0..49`, random move sequences. | Pass if candidate manager returns the best feasible candidate even when later moves produce infeasible states. |
| `Planned` | Shrinking expectation | On failure, reduce seed case to fewer blocks, fewer constraints, then fewer connectivity edges. | Pass if the minimized failing fixture is saved as a regression case before marking the bug fixed. |

## Edge Cases

- `Planned`: Minimum contest-sized case, `block_count = 21`.
- `Planned`: Maximum contest-sized case, `block_count = 120`.
- `Planned`: Validator dummy size, `block_count = 5`, even though contest data starts at 21.
- `Planned`: Empty B2B connectivity and empty P2B connectivity.
- `Planned`: Padded tensors with `-1` rows after active block ids.
- `Planned`: Zero-weight connectivity edges.
- `Planned`: Very small and very large target areas within normal floating-point range.
- `Planned`: Negative coordinates in preplaced targets.
- `Planned`: Preplaced rectangles with gaps, far-away obstacles, and obstacles that force placement outside the initial shelf origin.
- `Planned`: Fixed/preplaced target values exactly at evaluator tolerance boundaries.
- `Planned`: Soft-block area relative error at `0.01` should pass; relative error greater than `0.01` should fail.
- `Planned`: Overlap thickness at exactly `1e-6` should not count as an evaluator overlap; greater than `1e-6` should count.
- `Planned`: Boundary masks for single edges and corners.
- `Planned`: Group ids with one block, multiple blocks, and multiple independent groups.
- `Planned`: MIB ids with one block, equal-area blocks, and incompatible-area blocks.
- `Unknown`: Behavior for malformed input where fixed/preplaced target data is internally inconsistent; detailed implementation should either return the least-bad fallback or surface diagnostics, but contest docs do not define a recovery contract.

## Performance Benchmarks

Performance checks are separate from correctness checks. They must not be used to pass an infeasible layout.

| Status | Benchmark | Metrics | Pass/Fail Criteria |
| --- | --- | --- | --- |
| `Planned` | Synthetic 21-block solve | Wall time per `solve()`, hard feasibility, proxy score. | Pass if solve completes within the detailed-design budget and internal preflight is feasible. Exact seconds are `Unknown` until budget is set. |
| `Planned` | Synthetic 60-block solve | Wall time per `solve()`, hard feasibility, proxy score. | Pass if solve completes within the detailed-design budget and internal preflight is feasible. Exact seconds are `Unknown` until budget is set. |
| `Planned` | Synthetic 120-block stress | Wall time per `solve()`, hard feasibility, peak iteration count. | Pass if solve completes within the detailed-design budget, avoids unbounded annealing/search, and remains feasible. Exact seconds are `Unknown` until budget is set. |
| `Known, not run` | Single validation-case evaluator | `python iccad2026_evaluate.py --evaluate my_optimizer.py --test-id 0` | Pass if command exits 0, reports feasible case 0, and runtime is recorded for comparison. |
| `Known, not run` | Full validation evaluator | `python iccad2026_evaluate.py --evaluate my_optimizer.py` | Pass if command exits 0, reports 100/100 feasible cases, and records total score/runtime. |

Open performance threshold: official runtime target relative to other submissions is `Unknown`. The detailed design should define a concrete local per-case budget before implementation.

## Evaluator or Grading Commands

Known commands from `doc/quality-gates.md`; none were run while creating this plan.

| Status | Working Directory | Command | Notes |
| --- | --- | --- | --- |
| `Known, not run` | `iccad2026contest/` | `python iccad2026_evaluate.py --info` | Smoke command; imports dependencies and prints contest info. |
| `Known, not run` | `iccad2026contest/` | `python iccad2026_evaluate.py --validate my_optimizer.py --quick` | Validates file existence, syntax, import, and optimizer class discovery. |
| `Known, not run` | `iccad2026contest/` | `python iccad2026_evaluate.py --validate my_optimizer.py` | Also runs dummy `solve()` on sample data. |
| `Known, not run` | `iccad2026contest/` | `python iccad2026_evaluate.py --evaluate my_optimizer.py --test-id 0` | Runs single validation case; writes results JSON by default and may load validation data. |
| `Known, not run` | `iccad2026contest/` | `python iccad2026_evaluate.py --evaluate my_optimizer.py --test-id 0 --verbose` | Verbose single-case evaluator; writes results JSON by default. |
| `Known, not run` | `iccad2026contest/` | `python iccad2026_evaluate.py --evaluate my_optimizer.py` | Full 100-case validation evaluator; writes results JSON by default. |
| `Known, not run` | `iccad2026contest/` | `python iccad2026_evaluate.py --evaluate my_optimizer.py --save-solutions` | Writes results and solutions JSON. |
| `Known, not run` | `iccad2026contest/` | `python iccad2026_evaluate.py --score my_optimizer_solutions.json` | Scores saved solutions; requires a solution JSON. |
| `Known, not run` | `iccad2026contest/` | `python iccad2026_evaluate.py --baseline` | Writes baseline metrics JSON by default. |
| `Known, not run` | `iccad2026contest/` | `python iccad2026_evaluate.py --visualize --test-id 0` | Writes PNG and may invoke display behavior. |
| `Known, not run` | `iccad2026contest/` | `python iccad2026_evaluate.py --training` | May access or download large training data. |
| `Known, not run` | `iccad2026contest/` | `python training_example.py` | May access or download training data. |
| `Missing` | Unknown | Unit-test command | No conventional unit-test runner was discovered. |
| `Missing` | Unknown | Lint, format, type-check, static-analysis, CI commands | No repository-defined commands were discovered. |

## Regression Tests

Scenarios that should become stable regression checks after the first implementation:

- Template-style baseline ignores preplaced locations and can return a hard-constraint violation.
- A candidate with lower proxy score but an overlap replaces a feasible candidate.
- Boundary snapping succeeds before compaction but compaction moves the final bbox edge and breaks the boundary constraint.
- MIB synchronization for incompatible areas forces a soft block outside the 1% hard area tolerance.
- Fixed-shape rotation or aspect update changes immutable target dimensions.
- Preplaced obstacle is included in packing but later local search moves it.
- Edge-touching rectangles are incorrectly treated as overlaps.
- Slight positive overlaps below/above evaluator tolerance are classified differently by internal preflight and evaluator helpers.
- Empty connectivity causes division by zero or proxy-score NaN.
- Padded `-1` connectivity or target rows are treated as active blocks.
- `target_positions=None` breaks optimizer validation even though the signature defaults it.
- Full evaluator writes generated JSON files into the contest directory without an approved output-file plan.

## Manual Verification

- Review `doc/test-plan.md` against `doc/proposal.md` and `doc/high-level-design.md` before detailed design.
- After implementation, inspect a small set of generated layouts with boundary, preplaced, MIB, and grouping constraints to confirm violations are understandable.
- Review evaluator summaries for infeasible cases first; any cost `10.0` should be triaged before score tuning.
- Compare local total score against deterministic fallback and template baseline only after feasibility is stable.
- Confirm generated JSON, PNG, logs, caches, and datasets remain untracked unless explicitly requested.
- If an ML initializer is added later, manually verify that model files are allowed by final packaging rules and that the deterministic legalizer remains the correctness path.

## Minimum Done Criteria

Before detailed implementation is considered ready to proceed:

- `doc/test-plan.md` maps every proposal requirement category to at least one HLD module or explicit open question.
- Every major HLD module has a `Planned`, `Existing`, or `Missing` verification entry in `Unit Tests by Module`.
- Unknown or missing commands are labeled `Unknown` or `Missing`; known evaluator commands are labeled `Known, not run` unless actually executed later.
- Golden cases cover all hard constraints: no overlap, 1% soft-block area, fixed-shape dimensions, and preplaced position/dimensions.
- Golden or randomized cases cover each soft constraint family: boundary, grouping, and MIB.
- The oracle strategy includes differential comparison with evaluator hard-check helpers.
- Performance benchmarks are separated from correctness checks and do not allow infeasible layouts to pass.

Before a future optimizer implementation is considered complete:

- `iccad2026contest/my_optimizer.py` exists and is not a direct edit to `optimizer_template.py`.
- `python iccad2026_evaluate.py --validate my_optimizer.py` passes from `iccad2026contest/`.
- Internal preflight and evaluator hard checks agree on all golden and randomized fixtures.
- All golden tests pass.
- Randomized hard-feasibility properties pass for the agreed seed set.
- Single-case evaluator run on validation case 0 passes and reports a feasible solution.
- Full local validation run reports 100/100 feasible cases before quality tuning is treated as meaningful.
- Runtime benchmarks report local wall times for 21-block, 60-block, and 120-block workloads against the detailed-design budget.

## Open Questions

- What final submission packaging is allowed beyond one optimizer Python file?
- Are helper modules allowed, or should detailed implementation remain strictly single-file?
- Are model weights allowed in the final submission, and if so, what path and size limits apply?
- What concrete local runtime budget should define pass/fail performance for 21-block, 60-block, and 120-block cases?
- Should synthetic tests be implemented as a standalone script, a future `pytest` suite, or kept as ad hoc fixtures until repository test tooling exists?
- Which source should win if contest README/PDF behavior and evaluator behavior directly disagree during implementation?
- Should evaluator commands use explicit `--output` paths to keep generated results outside versioned files during future runs?
