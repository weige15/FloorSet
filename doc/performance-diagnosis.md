# Performance Diagnosis

## Status Update

The recommended first optimization in this diagnosis has been implemented. The current recorded local validation result is attempt 3 in `doc/performance-log.md`: score `4.5564`, `100/100` feasible, avg runtime `0.0871` s/case, output `/tmp/my_optimizer_boundary_skyline_results.json`. This document remains useful as the rationale for that change, but its `5.3511` baseline is now historical.

## Purpose

Diagnose why the current `iccad2026contest/my_optimizer.py` validation score remains at `5.3511` and has not converged below the user's target score of `3.0`, despite 100/100 feasible validation cases.

This is diagnosis only. No optimizer, evaluator, dataset, or smoke-test source code was changed.

## Diagnosis Scope

Scope covers the current saved local validation result:

```bash
cd iccad2026contest
python3 iccad2026_evaluate.py --evaluate my_optimizer.py
```

The evaluator was not rerun. I parsed `iccad2026contest/my_optimizer_results.json`, read the optimizer and evaluator source, and recomputed soft-violation family counts from saved positions plus local validation tensors in read-only mode.

The previous diagnosis in this file targeted the older `7.1293` score and recommended the boundary-frame constructive seed. That optimization has already been implemented and logged in `doc/performance-log.md`; this diagnosis supersedes it.

## Source Documents Read

- `/home/kuotzuwei15/.codex/skills/optimization-diagnosis/SKILL.md`
- `doc/problem-brief.md`
- `doc/proposal.md`
- `doc/high-level-design.md`
- `doc/detailed-design.md`
- `doc/test-plan.md`
- `doc/quality-gates.md`
- `doc/tasks/progress.md`
- `doc/performance-log.md`
- Prior `doc/performance-diagnosis.md`
- `iccad2026contest/README.md`
- `iccad2026contest/iccad2026_evaluate.py`
- `iccad2026contest/my_optimizer.py`
- `iccad2026contest/my_optimizer_results.json`
- Local validation tensors under `LiteTensorDataTest/config_*/`, read directly for soft-family recomputation.

Markdown files to check first when resuming:

1. `doc/performance-log.md` for the score history and what has already been tried.
2. `doc/performance-diagnosis.md` for the current bottleneck analysis and the next recommended attempt.
3. `doc/tasks/progress.md` for implemented modules, smoke coverage, and known evaluator runs.
4. `doc/detailed-design.md` for unresolved design choices, especially packing representation, proxy weights, and local-search budget.
5. `doc/test-plan.md` and `doc/quality-gates.md` before changing code or running evaluator commands.

## Current Correctness Status

The current saved evaluator result reports `100/100` feasible cases. All `test_results[*].is_feasible` values are true, so hard correctness is stable enough for optimization.

Known passing checks from `doc/tasks/progress.md` include smoke scripts for parser, optimizer entry, immutable geometry, dimension planning, fallback, macro planning, constructive initialization, candidate manager, proxy scoring, local search, and preflight. The progress log also records a passed `python -B iccad2026_evaluate.py --validate my_optimizer.py` after the boundary-frame optimization.

Checks not rerun in this diagnosis:

- `python3 iccad2026_evaluate.py --validate my_optimizer.py`
- `python3 iccad2026_evaluate.py --evaluate my_optimizer.py`
- Any full smoke-test batch
- Memory profiling

The remaining issue is quality, not basic correctness.

## Current Performance Baseline

| Metric | Value | Command | Verified? |
|---|---:|---|---|
| Score | 5.3511 | `cd iccad2026contest && python3 iccad2026_evaluate.py --evaluate my_optimizer.py` | User-provided run; saved JSON parsed and weighted score recomputed |
| Runtime | avg 0.0489 s/case; weighted avg 0.1048 s/case | Same evaluator command | Saved JSON parsed; local runtime factor is neutral |
| Memory | Unknown | Not measured | Missing |

Additional baseline details:

- Feasible: `100/100`
- Average cost: `5.0067`
- Weighted HPWL gap: `2.2538`
- Weighted area gap: `2.1630`
- Weighted violations relative: `0.2534`
- Weighted boundary violations: `12.2668`
- Weighted grouping violations: `2.5741`
- Weighted MIB violations: `0.0000`
- Weighted geometry density: `0.3107`
- Weighted approximate row count: `35.8660`
- No feasible cases are cost-capped at `9.999999`.

## Expected Performance Target

The current user target is local total score below `3.0`.

Current gap:

- Current score: `5.3511`
- Target score: `< 3.0`
- Required reduction: at least `2.3511` score points, or about `43.9%`

Important sensitivity result: with current HPWL and area gaps, eliminating all remaining soft violations projects only about `3.2084`, still above `3.0`. Therefore, the next optimization cannot be boundary-only or soft-violation-only. It must reduce HPWL and bounding-box area while preserving the boundary-frame gain.

## Gap Analysis

The boundary-frame optimization moved the solver from a soft-violation bottleneck into a combined packing-quality bottleneck.

Current weighted cost drivers:

- HPWL gap is high: `2.2538`
- Area gap is high: `2.1630`
- Soft violations are still meaningful: `0.2534` relative, mostly boundary
- Runtime is not the local score bottleneck because local evaluation uses `RuntimeFactor=1.0`

Sensitivity projections from current saved cases:

- Zero all soft violations: score about `3.2084`
- Zero boundary violations only: score about `3.5104`
- Half boundary violations: score about `4.3315`
- Zero grouping violations only: score about `4.8846`
- Half HPWL gap only: score about `4.4114`
- Half area gap only: score about `4.4492`
- Half HPWL and half area with current soft: score about `3.5095`
- Half HPWL, half area, and half soft: score about `2.7142`

Large cases matter most. Cases with 101 to 120 blocks carry about `81.1%` of the total score weight, and cases 116 to 120 carry about `34.1%`.

Top weighted score contributors include:

- test 98, 119 blocks: cost `6.5084`, HPWL gap `2.0954`, area gap `2.1727`, `V_rel=0.3654`
- test 99, 120 blocks: cost `4.7489`, HPWL gap `1.8228`, area gap `2.0684`, `V_rel=0.2388`
- test 95, 116 blocks: cost `6.2041`, HPWL gap `3.4602`, area gap `2.4158`, `V_rel=0.2273`
- test 92, 113 blocks: cost `6.4900`, HPWL gap `3.0306`, area gap `3.1284`, `V_rel=0.2321`
- test 89, 110 blocks: cost `7.5461`, HPWL gap `3.2906`, area gap `2.6553`, `V_rel=0.3208`

## Benchmark or Evaluator Details

The evaluator computes feasible cost as:

```text
(1 + 0.5 * (max(0, HPWL_gap) + max(0, Area_gap)))
* exp(2 * V_rel)
* max(0.7, RuntimeFactor ** 0.3)
```

Infeasible cases cost exactly `10.0`. Feasible cases are capped at `9.999999`. Local evaluation then resets every runtime factor to `1.0`, so local score is driven by HPWL gap, area gap, and normalized soft violations.

The current optimizer does not receive baseline HPWL or baseline area in `solve()`. It ranks candidates with raw HPWL, raw bbox area, and soft-violation counts:

```text
PROXY_HPWL_WEIGHT = 1.0
PROXY_BBOX_WEIGHT = 0.01
PROXY_SOFT_WEIGHT = 1000.0
PROXY_SOFT_EXPONENT = 2.0
```

Relevant implementation points:

- `iccad2026contest/my_optimizer.py` uses shelf and rail packers for fallback and construction.
- `_pack_boundary_frame_candidate()` creates a boundary rail layout, then shelf-packs interior units.
- `_local_search_shelf_width_trials()` only tries a few shelf widths.
- `_compact_candidate()` flattens movable blocks into a single row, which can improve feasibility simplicity but is not a true 2D compactor.

## Observed Bottlenecks

- Soft violations are no longer enough to explain the score. Removing all of them projects `3.2084`, not `<3`.
- Boundary is still the dominant soft family: weighted boundary violations are `12.2668`, grouping `2.5741`, MIB `0.0`. Boundary is about `82.7%` of the weighted soft numerator.
- The layouts are sparse after boundary-frame packing. Weighted block density is about `0.3107`, meaning roughly 69% of the bounding box is whitespace.
- Large layouts have many shelf/rail rows. Weighted approximate row count is about `35.9`; for 116 to 120 block cases it is about `40.7`.
- HPWL and area are both high, not just one metric. Weighted HPWL gap is `2.2538`; weighted area gap is `2.1630`.
- The current construction model is still fundamentally order plus shelf/rail placement. It does not perform true 2D packing, skyline placement, sequence-pair packing, or coordinate-level connectivity refinement.
- MIB is solved on the saved validation result and should not be the next target.
- Runtime is acceptable locally, but official runtime remains unknown and should be watched if adding more search.

## Likely Causes

### Cause 1: Boundary Frame Trades Soft Violations for Sparse Geometry

- Type: Algorithmic limitation.
- Evidence: The boundary-frame pass reduced weighted boundary violations from the prior diagnosis's roughly `27.97` to `12.27`, but the current weighted HPWL and area gaps are `2.2538` and `2.1630`. Saved geometry has weighted density only `0.3107` and about `35.9` row levels. This matches the outer-rail construction in `_pack_boundary_frame_candidate()`, which reserves left/right/top/bottom rails and shelf-packs the interior.
- Affected modules: `iccad2026contest/my_optimizer.py` functions `_pack_boundary_frame_candidate()`, `_boundary_frame_groups()`, `_pack_shelf_origins()`, `_constructive_seed_orders()`.
- Risk: Medium. The boundary frame is valuable and should not be removed; it needs a better interior and frame-shape search.
- Confidence: High.

### Cause 2: Packing Representation Is Still Shelf-Based

- Type: Algorithmic limitation.
- Evidence: Fallback, ordinary constructive seeds, local repacking, and boundary-frame interior all route through shelf-width logic. The only geometry variants are order changes, a small set of shelf widths, and post-hoc snapping/compaction. That explains the high whitespace and high area gap. A score below `3` requires actual geometry improvement; score projections show that soft cleanup alone is insufficient.
- Affected modules: `iccad2026contest/my_optimizer.py` functions `_pack_units_as_candidate()`, `_pack_shelf_origins()`, `_fallback_compact_shelf_width()`, `_local_search_shelf_width_trials()`, `_compact_candidate()`.
- Risk: Medium-high. A real 2D packer increases geometry complexity and overlap risk; it must be introduced as an additional candidate seed, not by replacing fallback.
- Confidence: High.

### Cause 3: Proxy Ranking Is Not Calibrated to the New Regime

- Type: Parameter tuning and evaluator-proxy mismatch.
- Evidence: The current proxy heavily penalizes soft violations and uses raw HPWL plus `0.01 * bbox_area`, while official scoring uses relative gaps against hidden baselines and a multiplicative soft factor. This was useful when boundary violations dominated, but now zero-soft score is still above `3`, so candidate selection must care more about compactness and HPWL. Since `solve()` lacks official baselines, the proxy cannot be exact, but it can be better normalized by total block area, estimated density, and per-case connectivity scale.
- Affected modules: `iccad2026contest/my_optimizer.py` constants `PROXY_*` and function `_score_candidate()`.
- Risk: Medium. Retuning without adding better candidates may only reshuffle weak layouts, so proxy changes should follow or accompany a new geometry seed.
- Confidence: Medium.

## Optimization Hypotheses

| Priority | Hypothesis | Expected Impact | Risk | Affected Files | Verification |
|---:|---|---|---|---|---|
| 1 | Add a boundary-preserving skyline or best-fit interior packer as one new constructive seed. Keep boundary rails, but pack interior units into a denser 2D layout and try a small set of frame aspect ratios on large cases. | High. Targets both area gap and HPWL while preserving most boundary gains. A combined 50% reduction in HPWL/area and 50% soft reduction projects about `2.7142`. | Medium. New geometry can introduce overlap or hurt boundary; keep fallback and current boundary frame unchanged. | `iccad2026contest/my_optimizer.py`, `optimizer_constructive_smoke.py`, `optimizer_local_search_smoke.py`, possibly `optimizer_proxy_scoring_smoke.py` | Smokes, `--validate`, full `--evaluate`; compare score, feasibility, HPWL gap, area gap, boundary/grouping/MIB counts, density, and runtime against 5.3511. |
| 2 | Add connectivity-aware placement inside the boundary frame: order interior units by B2B/P2B attraction to already placed rails and pins, and place high-connectivity units near related boundary/cluster units. | Medium. Targets HPWL without discarding boundary rails. Prior connectivity-greedy ordering helped only slightly because geometry remained shelf-like; it should be stronger when combined with 2D placement. | Medium. More ordering logic may overfit validation if too specific. | `iccad2026contest/my_optimizer.py`, constructive/proxy smokes | Compare HPWL gap and total score, especially top contributors 98, 95, 92, 89. Roll back if HPWL improves but area/soft makes score worse. |
| 3 | Recalibrate proxy scoring after adding denser candidates: increase bbox/density influence and reduce soft dominance once boundary violations are already near the current level. | Medium. Better candidate choice can recover from the proxy favoring low-soft sparse layouts over slightly higher-soft compact layouts. | Medium. Proxy-only tuning without new candidates is unlikely to reach `<3`. | `iccad2026contest/my_optimizer.py`, `optimizer_proxy_scoring_smoke.py` | Run before/after evaluator; require improved total score without feasibility loss and inspect family metrics to avoid simply trading one term for another. |

## Recommended First Optimization

Implement only hypothesis 1 first: add a boundary-preserving skyline or best-fit interior constructive seed.

The goal is not to replace the current boundary frame. The first attempt should add one candidate family that:

- reuses existing fixed/preplaced handling, dimensions, grouping macros, MIB metadata, and preflight;
- keeps boundary-constrained units on outer rails where that is cheap;
- packs unconstrained and remaining boundary-overflow units with a simple 2D skyline/best-fit strategy instead of shelves only;
- tries a small bounded set of frame aspect ratios or target widths, with more attention to 101 to 120 block cases;
- preserves the current fallback, ordinary seeds, `connectivity_greedy`, and existing `boundary_frame` seed as rollback paths;
- lets `CandidateManager` choose only hard-feasible candidates that improve the proxy score.

Why this first:

- The current target `<3` cannot be reached by removing soft violations alone.
- The biggest remaining measured weaknesses are sparse bbox and HPWL, both caused by the shelf/rail geometry model.
- Adding one new candidate seed is smaller and easier to roll back than replacing local search or rewriting the solver.
- It aligns with the unresolved design question in `doc/detailed-design.md`: the optimized packing representation was never upgraded beyond deterministic shelves.

Rollback condition:

- Full local evaluation score is not lower than `5.3511`.
- Feasibility drops below `100/100`.
- Weighted area or HPWL improves but soft violations rise enough that total score worsens.
- Average or max runtime rises materially without score improvement.
- Existing smoke tests fail.

## Exact Prompt for Implementation Loop

```text
Use [$implementation-loop-manager] in optimization mode.

Read:
- doc/performance-diagnosis.md
- doc/performance-log.md if present
- doc/test-plan.md
- doc/quality-gates.md
- relevant source and test files

Implement only the first recommended optimization hypothesis.

Rules:
- Do not change unrelated modules.
- Preserve correctness.
- Add or update tests only if needed.
- Run correctness tests first.
- Run the benchmark or evaluator after the change.
- Compare before/after numbers.
- Keep the change only if the target metric improves without breaking correctness.
- If the result is worse, revert the optimization and record why.
- Update doc/performance-log.md.
- Report changed files, commands run, before/after metrics, and whether the change was kept.
```

## Stop Conditions

- Stop if any hard-correctness check becomes unstable or any evaluator run reports fewer than `100/100` feasible cases.
- Stop if a new packer changes fixed dimensions, preplaced positions, or preplaced dimensions.
- Stop if the new candidate depends on validation result files, baseline metrics, or dataset files inside `solve()`.
- Stop if the implementation tries to optimize validation-specific test ids or block counts beyond general contest-scale budget policies.
- Stop if local evaluation cannot be run with an approved output-file plan.

## Risks and Warnings

- The score below `3` target is substantially harder than the previous below-5 target. The current solver needs structural geometry improvement, not another tiny order tweak.
- Local runtime is neutral, but official runtime can penalize extra candidate generation. Keep the first skyline/best-fit seed bounded.
- Boundary constraints are still important. Removing the boundary frame would likely regress toward the old `7.1293` regime.
- Proxy score is not official score because baselines are not passed to `solve()`. Use evaluator runs, not proxy-only comparisons, to decide whether to keep the optimization.
- The Matplotlib cache warning observed during read-only analysis comes from importing evaluator dependencies with an unwritable `$HOME/.config/matplotlib`; it does not affect the score diagnosis.
- Generated result JSON files, PNGs, logs, caches, and datasets should remain local artifacts unless explicitly requested for version control.

## Open Questions

- What official runtime increase is acceptable if a denser boundary-preserving packer improves score?
- Should the new 2D packer be skyline/best-fit, guillotine, or sequence-pair-style for the first attempt?
- Should proxy retuning be allowed in the same implementation loop if the new seed generates better candidates but the current proxy rejects them?
- Should the next target be strict `<3.0`, or should the next implementation loop use an intermediate keep/rollback threshold such as `<5.0`, `<4.5`, then `<3.5`?
- Are helper modules allowed in final submission, or should all optimizer changes remain single-file?
