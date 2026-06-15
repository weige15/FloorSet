# Performance Diagnosis

## Purpose

Diagnose why the current `iccad2026contest/my_optimizer.py` validation score is
`4.3887` despite `100/100` feasible cases, and identify the next optimization
most likely to move the score toward `2.0` or below.

This is diagnosis only. No optimizer implementation code was changed.

## Diagnosis Scope

Scope covers the current saved local validation result:

```bash
cd iccad2026contest
python3 iccad2026_evaluate.py --evaluate my_optimizer.py
```

The evaluator was not rerun during this diagnosis. I used the user-provided
terminal output, parsed `iccad2026contest/my_optimizer_results.json` read-only,
compared it with prior result JSONs under `/tmp`, and inspected the current
optimizer/evaluator source.

Prior comparison artifacts used:

- `/tmp/my_optimizer_boundary_skyline_results.json`
- `/tmp/my_optimizer_boundary_skyline_connected_results.json`
- `/tmp/my_optimizer_ripup_repack_results.json`
- `/tmp/my_optimizer_frame_compaction_large_results.json`

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
- prior `doc/performance-diagnosis.md`
- `iccad2026contest/README.md`
- `iccad2026contest/iccad2026_evaluate.py`
- `iccad2026contest/my_optimizer.py`
- `iccad2026contest/my_optimizer_results.json`

## Current Correctness Status

The saved evaluator result reports `100/100` feasible cases. All
`test_results[*].is_feasible` values are true, so hard correctness is stable
enough for optimization.

Known passing checks from `doc/tasks/progress.md` include all optimizer smoke
scripts and:

```bash
python -B iccad2026_evaluate.py --validate my_optimizer.py
```

Checks not rerun in this diagnosis:

- `python3 iccad2026_evaluate.py --validate my_optimizer.py`
- `python3 iccad2026_evaluate.py --evaluate my_optimizer.py`
- The full smoke-test batch
- Memory profiling

The remaining issue is layout quality, not feasibility.

## Current Performance Baseline

| Metric | Value | Command | Verified? |
|---|---:|---|---|
| Score | 4.3887 | `cd iccad2026contest && python3 iccad2026_evaluate.py --evaluate my_optimizer.py` | User-provided run; saved JSON parsed read-only |
| Runtime | avg 0.3620 s/case; max 3.9774 s/case | Same evaluator command | Saved JSON parsed; local runtime factor is neutral |
| Memory | Unknown | Not measured | Missing |

Additional baseline details from `my_optimizer_results.json`:

- Feasible: `100/100`
- Average cost: `4.3428`
- Average HPWL gap: `1.7845`; weighted HPWL gap: `1.6416`
- Average area gap: `1.5889`; weighted area gap: `1.6645`
- Average violations relative: `0.2378`; weighted violations relative: `0.2486`
- Cases with `101-120` blocks carry `81.13%` of total score weight.
- Cases with `81-100` blocks carry `15.32%` of total score weight.
- Cases with `21-80` blocks together carry only `3.54%` of total score weight.

## Expected Performance Target

The current user target is score around `2.0` or below.

Current gap:

- Current score: `4.3887`
- Target score: `<= 2.0`
- Required reduction: at least `2.3887` score points, or about `54.4%`

Sensitivity projections from the current saved cases:

- Zero all soft violations, current HPWL/area: projected score `2.6531`
- Zero HPWL and area gaps only, current soft violations: projected score `1.6511`
- Half HPWL, half area, and half soft: projected score `2.3461`

Therefore, score `<= 2.0` requires simultaneous improvement in HPWL,
bounding-box area, and soft violations. Soft cleanup alone is insufficient, and
small local improvements are now too weak.

## Gap Analysis

Recent changes show clear diminishing returns:

| Attempt | Score | Weighted HPWL Gap | Weighted Area Gap | Weighted V_rel | Avg Runtime |
|---|---:|---:|---:|---:|---:|
| `boundary_skyline` | 4.5564 | 1.8390 | 1.6547 | 0.2499 | 0.0871 s |
| `boundary_skyline_connected` | 4.5063 | 1.7766 | 1.6621 | 0.2499 | 0.1536 s |
| `ripup_repack` | 4.4080 | 1.6665 | 1.6621 | 0.2486 | 0.2680 s |
| `frame_compaction_large` | 4.3887 | 1.6416 | 1.6645 | 0.2486 | 0.3514-0.3620 s |

The latest frame-compaction pass improved only `5/100` cases, worsened none,
and reduced score by `0.0192`. It lowered weighted HPWL but slightly increased
weighted area and did not change weighted soft violations.

The current worst weighted contributors are large cases:

- test 98, 119 blocks: contribution `0.4037`, cost `5.4866`
- test 99, 120 blocks: contribution `0.3154`, cost `3.9441`
- test 95, 116 blocks: contribution `0.2946`, cost `5.1402`
- test 97, 118 blocks: contribution `0.2684`, cost `3.9642`
- test 94, 115 blocks: contribution `0.2368`, cost `4.4913`
- test 89, 110 blocks: contribution `0.2249`, cost `6.4711`
- test 92, 113 blocks: contribution `0.2249`, cost `5.0388`

High-cost cases are broad, not isolated:

- `100/100` cases have cost above `2.0`.
- `95/100` cases have cost above `3.0`.
- `95/100` cases have HPWL gap above `1.0`.
- `87/100` cases have area gap above `1.0`.
- `81/100` cases have `V_rel` above `0.2`.

This is why the final score is not converging under `2`: the current solver is
feature-complete and legal, but its placement representation is still a greedy
constructive frame plus small repair moves. That representation is not finding
layouts close enough to the provided HPWL/area baselines.

## Benchmark or Evaluator Details

The evaluator computes feasible cost as:

```text
(1 + 0.5 * (max(0, HPWL_gap) + max(0, Area_gap)))
* exp(2 * V_rel)
* max(0.7, RuntimeFactor ** 0.3)
```

Infeasible cases cost exactly `10.0`. Feasible cases are capped at `9.999999`.
Local evaluation resets every runtime factor to `1.0`, so local score is driven
by HPWL gap, area gap, and normalized soft violations.

The current optimizer does not receive baseline HPWL or baseline area in
`solve()`. It ranks candidates with raw HPWL, raw bbox area, and soft-violation
counts:

```text
PROXY_HPWL_WEIGHT = 1.0
PROXY_BBOX_WEIGHT = 0.01
PROXY_SOFT_WEIGHT = 1000.0
PROXY_SOFT_EXPONENT = 2.0
```

Relevant implementation points in `iccad2026contest/my_optimizer.py`:

- `CandidateManager` retains only hard-feasible candidates as best candidates.
- `_pack_boundary_skyline_candidate()` preserves boundary rails and packs the
  frame interior with bottom-left skyline variants.
- `_pack_connected_bottom_left_origins()` uses placed-neighbor and pin
  attraction, but remains one-pass greedy.
- `_run_local_search()` tries bounded local move families, then bounded
  rip-up/repack, compaction, boundary snapping, and frame compaction.
- `_pack_ripup_repack_candidate()` freezes non-window units and cannot compress
  the current bbox unless selected windows include useful extremes.
- `_local_search_frame_compaction_trials()` is already present, but it is gated
  to large boundary cases and only yielded five observed improvements.

## Observed Bottlenecks

- The current candidate set is too shallow for `<= 2.0`. Recent quality passes
  safely improve a few cases but do not change the score regime.
- Weighted area gap is effectively stuck around `1.66`; frame compaction did
  not reduce it.
- Weighted soft violations are stuck around `0.2486`; current boundary, grouping,
  and MIB handling is not enough to remove the exponential multiplier.
- HPWL is still high even after connectivity-aware placement and rip-up. A
  weighted HPWL gap of `1.6416` means the layouts remain far from baseline
  connectivity quality.
- Runtime is not the local bottleneck, but it is now large enough that any next
  search pass must be bounded and targeted at high-weight large cases.

## Likely Causes

### Cause 1: Greedy Frame/Skyline Representation Has Hit Its Ceiling

- Type: Algorithmic limitation.
- Evidence: The largest gains came from introducing boundary frames and skyline
  packing. Subsequent connectivity, rip-up, and frame-compaction passes improved
  score only from `4.5564` to `4.3887`; the latest pass changed just `5/100`
  cases.
- Affected modules: `iccad2026contest/my_optimizer.py` functions
  `_constructive_seed_orders()`, `_pack_boundary_skyline_candidate()`,
  `_pack_connected_bottom_left_origins()`, `_run_local_search()`.
- Risk: Medium-high. A stronger global representation can improve quality, but
  must keep hard preflight and runtime bounds.
- Confidence: High.

### Cause 2: Local Search Freezes Too Much Geometry

- Type: Algorithmic limitation.
- Evidence: Rip-up/repack improved weighted HPWL but left weighted area
  unchanged. Frame compaction only improved five cases and increased weighted
  area slightly. Current repair moves are too local to reorganize rails,
  grouped macros, and interior units together.
- Affected modules: `iccad2026contest/my_optimizer.py` functions
  `_eligible_ripup_unit_ids()`, `_ripup_windows()`,
  `_pack_ripup_repack_candidate()`, `_local_search_frame_compaction_trials()`.
- Risk: Medium. Relaxing anchors can regress boundary or grouping unless every
  candidate remains preflight-gated.
- Confidence: High.

### Cause 3: Soft Constraints Are Treated More As Penalties Than Construction Goals

- Type: Algorithmic limitation and proxy mismatch.
- Evidence: Weighted `V_rel` stayed `0.2486` across rip-up and frame compaction.
  Zeroing all soft violations would still not reach `2.0`, but the exponential
  term is large enough that persistent violations block convergence.
- Affected modules: `iccad2026contest/my_optimizer.py` functions
  `_plan_soft_units()`, grouping macro construction, boundary-frame packing,
  `_score_candidate()`, `_local_search_mib_sync_trials()`.
- Risk: Medium. Aggressive soft repair can worsen HPWL/area if not jointly
  optimized.
- Confidence: Medium-high.

### Cause 4: Proxy Scoring Cannot See Official Relative Baselines

- Type: Evaluator-proxy mismatch.
- Evidence: Official score uses relative gaps against dataset baselines that are
  not passed into `solve()`, while the optimizer uses raw HPWL and raw bbox
  with fixed weights. This can rank candidates incorrectly, especially across
  cases with different area/pin scales.
- Affected modules: `iccad2026contest/my_optimizer.py` constants `PROXY_*` and
  `_score_candidate()`.
- Risk: Medium. Retuning proxy weights alone is unlikely to beat the current
  representation ceiling.
- Confidence: Medium.

## Optimization Hypotheses

| Priority | Hypothesis | Expected Impact | Risk | Affected Files | Verification |
|---:|---|---|---|---|---|
| 1 | Add a bounded unit-level sequence-pair or B*-tree style global search for large cases, seeded from the current best candidate, with boundary snapping, immutable repair, and hard preflight after every decoded state. Use it only for high-weight `block_count >= 90` or `>= 100` cases at first. | High. This is the first change that directly addresses the greedy representation ceiling and can jointly reduce HPWL/area/soft violations. | High | `iccad2026contest/my_optimizer.py`, `optimizer_local_search_smoke.py`, possibly a new global-search smoke | Smokes, `--validate`, full `--evaluate`; compare score against `4.3887`, weighted HPWL `1.6416`, weighted area `1.6645`, weighted V_rel `0.2486`, avg runtime `0.3620 s`. |
| 2 | Add a soft-constraint assembly pass before global placement: construct compatible grouping/MIB/boundary units as explicit connected mini-layouts, then allow the global search to move those units instead of fixing rail-heavy geometry too early. | Medium-high. Could reduce the exponential soft multiplier while preserving search freedom. | Medium | `iccad2026contest/my_optimizer.py`, macro/constructive/local-search smokes | Reject if soft improves but HPWL/area regress enough to worsen score. |
| 3 | Normalize proxy scoring by case scale and add more area-preserving shape/aspect variants for high-connectivity soft blocks. | Medium. Helps candidate ranking after richer candidates exist. | Medium | `iccad2026contest/my_optimizer.py`, proxy/dimension/local-search smokes | Reject if local proxy improves but full evaluator score does not. |

## Recommended First Optimization

Implement only hypothesis 1 first: a bounded unit-level global-search pass for
large cases.

The current local approach has already used the obvious cheap moves:
connectivity-aware skyline packing, large-case rip-up/repack, and boundary-frame
compaction. The marginal gain from the last pass was only `0.0192`, so another
small frame tweak is unlikely to close a `2.3887` score gap.

Recommended design:

- Gate the first version to `block_count >= 100` to target `81.13%` of weighted
  score and contain runtime risk.
- Start from `manager.best_feasible_or_fallback()` after existing local search.
- Build a unit-level representation over current placement units, not raw
  blocks, so grouping and compatible MIB decisions stay intact.
- Decode a small set of sequence-pair or B*-tree perturbations into legal
  rectangular placements using existing dimensions.
- Seed the initial order from current `(y, x)` and connectivity order; try only
  a bounded number of deterministic perturbations first.
- After each decoded candidate, run immutable repair, boundary snapping, MIB
  repair where compatible, and hard preflight.
- Submit only hard-feasible candidates to `CandidateManager`.
- Keep runtime caps conservative. The first target is quality signal, not an
  exhaustive annealer.

Initial success target:

- Keep `100/100` feasible.
- Improve total score below `4.3887`.
- Improve at least one high-weight large case without worsening any case, or
  improve weighted HPWL and area together.
- Keep weighted `V_rel <= 0.2486`.
- Keep average runtime under about `0.60 s/case` for the first version unless
  the score gain is substantial.

Rollback condition:

- Full local evaluation score is not lower than `4.3887`.
- Feasibility drops below `100/100`.
- Weighted HPWL/area improve in proxy only but not in evaluator output.
- Runtime rises materially without score improvement.
- Existing smoke tests or `--validate` fail.

Why not proxy tuning first:

- Proxy tuning cannot create better layouts; it can only select among existing
  candidates. The current candidate family has plateaued.
- The score projection shows the target requires large structural improvement,
  not small changes in candidate ranking.

## Exact Prompt for Implementation Loop

```text
Use [$implementation-loop-manager] in optimization mode.

Read:
- doc/performance-diagnosis.md
- doc/performance-log.md if present
- doc/test-plan.md
- doc/quality-gates.md
- relevant source and test files

Implement only the first recommended optimization hypothesis:
bounded unit-level global search for large cases.

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

- Stop if any hard-correctness check becomes unstable or any evaluator run
  reports fewer than `100/100` feasible cases.
- Stop if the global-search decoder changes fixed dimensions, preplaced
  positions, or preplaced dimensions.
- Stop if boundary or grouping repair improves soft counts by simply expanding
  bbox enough to worsen total score.
- Stop if the implementation depends on validation result files, saved
  solutions, baseline metrics, or dataset files inside `solve()`.
- Stop if the implementation optimizes specific validation `test_id` values
  instead of general block/count/connectivity/constraint structure.
- Stop if runtime growth dominates score improvement.
- Stop if local evaluation cannot be run with an approved output-file plan.

## Risks and Warnings

- A score around `2.0` is a large jump from `4.3887`; it likely requires
  multiple measured iterations.
- The next optimization should target large cases first because cases with
  `101-120` blocks account for `81.13%` of total score weight.
- Soft cleanup alone is insufficient: zeroing all current soft violations still
  projects `2.6531`.
- Half-sized improvements across HPWL, area, and soft violations still project
  only `2.3461`, so the eventual implementation needs stronger than half-way
  progress in at least one major term.
- Local runtime is neutral, but official runtime can penalize extra search.
- Generated result JSON files, PNGs, logs, caches, and datasets should remain
  local artifacts unless explicitly requested for version control.

## Open Questions

- What official runtime increase is acceptable if a global-search pass improves
  score?
- Should the first global-search decoder use sequence pair, B*-tree, or a
  simpler two-order bottom-left decoder?
- Should source attribution be added to saved diagnostics so future analysis can
  identify which candidate family won each test case?
- Should soft-constraint macro assembly happen before or after the first global
  representation pass?
- Are model weights allowed in final submission, and what size/path limits
  apply?
