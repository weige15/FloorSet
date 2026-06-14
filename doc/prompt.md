# Implementation Prompt

## Objective

Implement a contest-compliant FloorSet optimizer for ICCAD 2026 CAD Contest Problem C in `iccad2026contest/my_optimizer.py`.

The optimizer must expose a discoverable optimizer class with:

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

Return exactly one `(x, y, width, height)` tuple per active block, ordered by original block id. The implementation priority is hard feasibility first, then lower HPWL, lower bounding-box area, fewer soft-constraint violations, and bounded runtime.

## Inputs to Read First

Read these before editing code:

- `AGENTS.md`: repository rules, approval requirements, dataset cautions, and current contest assumptions.
- `doc/problem-brief.md`: present optional context; contest objective, inputs, outputs, constraints, scoring, data, and open questions.
- `doc/repo-map.md`: present optional context; repository structure, current implementation status, CLIs, dependencies, missing test infrastructure, and data notes.
- `doc/quality-gates.md`: present optional context; discovered commands, missing gates, commands not run, and recommended done criteria.
- `doc/proposal.md`: primary product intent and feasibility-first solver strategy.
- `doc/high-level-design.md`: architecture, module list, data flow, dependencies, and quality-gate alignment.
- `doc/detailed-design.md`: implementation contracts, module responsibilities, tolerances, failure handling, and cross-module contracts.
- `doc/test-plan.md`: synthetic fixtures, golden cases, randomized/property checks, integration gates, evaluator commands, and done criteria.
- `doc/tasks/progress.md`: module checklist to maintain during implementation.
- `doc/tasks/optimizer-entry.md`
- `doc/tasks/input-normalization-and-constraint-parser.md`
- `doc/tasks/immutable-geometry-registry.md`
- `doc/tasks/dimension-planner.md`
- `doc/tasks/deterministic-legal-fallback.md`
- `doc/tasks/macro-and-soft-constraint-planner.md`
- `doc/tasks/constraint-aware-constructive-initializer.md`
- `doc/tasks/candidate-manager.md`
- `doc/tasks/local-search-and-repair.md`
- `doc/tasks/proxy-scoring.md`
- `doc/tasks/hard-constraint-preflight-checker.md`
- `doc/tasks/optional-ml-initializer.md`
- `iccad2026contest/README.md`: authoritative contest guide and command reference.
- `iccad2026contest/iccad2026_evaluate.py`: evaluator oracle for loading, validation, target-position passing, hard/soft checks, cost, and CLI behavior.
- `iccad2026contest/optimizer_template.py`: class pattern and B*-tree baseline limitations.

## Current Implementation

At prompt-generation time, `iccad2026contest/my_optimizer.py` does not exist. Create it as the contestant-owned implementation file; do not edit `iccad2026contest/optimizer_template.py` unless explicitly asked.

The current contest framework is:

- `iccad2026contest/iccad2026_evaluate.py`: defines `FloorplanOptimizer`, evaluator helpers `calculate_hpwl_b2b`, `calculate_hpwl_p2b`, `calculate_bbox_area`, `check_overlap`, `check_area_tolerance`, `check_dimension_hard_constraints`, `compute_cost`, `evaluate_solution`, `compute_total_score`, dataloaders, visualization, scoring, baseline generation, validation, and CLI `main()`.
- `iccad2026contest/optimizer_template.py`: defines `BStarTree` and `MyOptimizer(FloorplanOptimizer)` baseline. The template claims overlap-free and area-valid behavior but does not fully handle preplaced locations, boundary constraints, MIB, or grouping.
- `iccad2026contest/training_example.py`: training-loss example. It may access or download training data; it is not required for the heuristic correctness path.
- `LiteTensorDataTest/`: local validation tensor data is present with `config_21` through `config_120`.
- `requirements.txt` and `iccad2026contest/requirements.txt`: pip dependency files. Contest requirements include `torch`, `numpy`, `shapely`, `matplotlib`, `tqdm`, and `requests`.

The evaluator loads a submitted optimizer file, finds a subclass of `FloorplanOptimizer` or common class names such as `MyOptimizer`, and calls `solve()`. During evaluation it constructs `target_positions` so preplaced blocks receive `(x, y, w, h)`, fixed-shape blocks receive `w, h`, and free values remain `-1`.

No conventional build system, unit-test runner, lint command, formatter, type checker, static-analysis tool, or CI workflow was discovered. Files named `lite_dataset_test.py` and `prime_dataset_test.py` are dataset loader modules, not configured unit tests.

## Hard Constraints

Preserve these behavior constraints exactly:

- `solve()` must return a Python list with exactly `block_count` entries.
- Each entry must be finite numeric `(x, y, width, height)` with positive width and height.
- Output order must be original block id order `[0, block_count)`.
- Rectangles use lower-left coordinates and occupy `[x, x + width] x [y, y + height]`.
- Edge-touching is legal; positive-area overlap is illegal.
- Overlap violation uses evaluator tolerance: overlap width and height both greater than `1e-6`.
- Soft-block area must satisfy `abs(width * height - area_targets[i]) / area_targets[i] <= 0.01`.
- Fixed-shape blocks must match target width and height from `target_positions` within evaluator dimension tolerance `1e-4`.
- Preplaced blocks must match target x, y, width, and height from `target_positions` within evaluator coordinate/dimension tolerance `1e-4`.
- Fixed and preplaced blocks are skipped by the soft-block area tolerance check and are instead checked by immutable target geometry.
- Constraint columns are `[fixed, preplaced, mib, cluster, boundary]`.
- Boundary bitmask semantics are `1 = left`, `2 = right`, `4 = top`, `8 = bottom`; corners are sums such as `5` and `10`.
- Soft constraints are boundary, grouping, and MIB only. They affect cost but must never override hard feasibility.
- Any hard violation makes a case infeasible with cost `10.0`; any feasible solution is capped below `10.0`.
- Local evaluation uses neutral `RuntimeFactor = 1.0`; do not treat local runtime score as official runtime competitiveness.
- Do not depend on training data, downloads, generated JSON, model weights, external services, or persistent state for correctness.
- Do not modify `iccad2026contest/iccad2026_evaluate.py`, dataset loaders, validation data, or `optimizer_template.py` unless the user explicitly requests it.
- Do not reverse-engineer the dataset generator.

## Non-Goals

- Do not implement an ML-only solver.
- Do not add model weights or training workflows unless final packaging and data access are explicitly approved.
- Do not add services, databases, queues, APIs, or nonlocal persistent state.
- Do not create generated result JSON, solution JSON, PNGs, logs, caches, or copied datasets without approval.
- Do not invent lint, format, type-check, static-analysis, or unit-test commands that are not configured.
- Do not chase optimal exact floorplanning with MIP/SMT unless separately approved; prioritize a robust heuristic legalizer.
- Do not broaden the work into dataset loader, evaluator, visualization, or training refactors.

## Execution Model

Start with read-only orientation:

1. Run `git status --short --branch`.
2. Read all docs listed in `Inputs to Read First`.
3. Inspect `iccad2026contest/iccad2026_evaluate.py` and `iccad2026contest/optimizer_template.py` for current evaluator behavior.
4. Confirm whether `iccad2026contest/my_optimizer.py` already exists. If it exists, read it and preserve any user or prior-agent work.

Implementation rules:

- Maintain `doc/tasks/progress.md` as work starts, completes, blocks, and verifies. Add timestamped checkpoint notes after each module or small workstream.
- Implement one module or small workstream at a time.
- Prefer a self-contained `iccad2026contest/my_optimizer.py` unless the user confirms helper modules are allowed.
- Keep write scopes disjoint if using subagents. Avoid concurrent uncoordinated edits to `iccad2026contest/my_optimizer.py`.
- Avoid reverting edits made by the user or other agents.
- Use deterministic parsing, dimension planning, fallback placement, preflight, and tie-breaking.
- Run module-specific synthetic checks after each module when feasible.
- Run full quality gates at the end, with approval where commands write outputs, install dependencies, load datasets, download data, train, visualize, or run long evaluations.
- Summarize command outputs as evidence; do not assume the user saw terminal output.
- Stop and ask only when truly blocked by conflicting authoritative docs, missing destructive permissions, credentials, external services, packaging rules, or an unresolvable evaluator mismatch.

## Module Workstreams

Use these workstreams as implementation ownership boundaries. The expected primary write target is `iccad2026contest/my_optimizer.py`; optional synthetic checks may be added only if the test-harness decision is made.

1. Optimizer scaffold and entry
   - Files: `iccad2026contest/my_optimizer.py`, `doc/tasks/progress.md`.
   - Build class discovery, `solve()` signature, per-call context, final tuple conversion, exception fallback, and no side effects.
   - Verification: quick import/compile check if possible; later `python iccad2026_evaluate.py --validate my_optimizer.py --quick` with approval.

2. Input normalization and constraint parser
   - Files: parser section in `iccad2026contest/my_optimizer.py`; optional synthetic fixture file if added.
   - Normalize tensor/list-like inputs, active slices, padded `-1` connectivity rows, constraints, pins, and target positions.
   - Verification: synthetic parser fixtures for fixed, preplaced, MIB, cluster, boundary, empty connectivity, missing columns, and `target_positions=None`.

3. Immutable geometry and dimension planner
   - Files: immutable geometry and dimension sections in `iccad2026contest/my_optimizer.py`; optional synthetic fixtures.
   - Extract fixed/preplaced target geometry, obstacles, movable ids, soft-block square dimensions, MIB compatibility notes, and invalid-input diagnostics.
   - Verification: fixed-only, preplaced-only, mixed, all-soft, compatible MIB, incompatible MIB, and 1% area boundary fixtures.

4. Hard-constraint preflight and proxy scoring
   - Files: preflight and scoring sections in `iccad2026contest/my_optimizer.py`; optional synthetic fixtures.
   - Implement finite/positive checks, overlap, soft area tolerance, immutable geometry checks, HPWL, bbox area, soft-violation estimates, hard barrier, and deterministic tie-break fields.
   - Verification: differential checks against evaluator helpers where possible; hand-computed HPWL/bbox fixtures; edge-touching and positive-overlap fixtures.

5. Deterministic legal fallback
   - Files: fallback packing section in `iccad2026contest/my_optimizer.py`; optional synthetic fixtures.
   - Implement id-order no-obstacle shelf placement, exact preplaced emission, conservative obstacle avoidance, fallback preflight, and diagnostics.
   - Verification: golden two all-soft case `(0, 0, 2, 2)` and `(2, 0, 3, 3)`, fixed-shape case, preplaced obstacle case, randomized fallback properties.

6. Candidate manager
   - Files: candidate records and retention logic in `iccad2026contest/my_optimizer.py`; optional synthetic fixtures.
   - Retain best hard-feasible candidate, reject malformed candidates, keep infeasible diagnostics, and prevent infeasible lower proxy scores from replacing feasible states.
   - Verification: feasible-then-infeasible sequence, tie-breaking, fallback retention, malformed rejection.

7. Macro and soft-constraint planner
   - Files: placement unit and soft-intent sections in `iccad2026contest/my_optimizer.py`; optional synthetic fixtures.
   - Create units, fixed preplaced units, grouping macros, MIB metadata, boundary intents, and expansion guarantees.
   - Verification: movable groups, groups with preplaced members, boundary edges/corners, MIB metadata, unit expansion.

8. Constraint-aware constructive initializer
   - Files: constructive packing and seed-order sections in `iccad2026contest/my_optimizer.py`; optional synthetic fixtures.
   - Generate bounded seed orders and hard-feasible expanded candidates from preplaced obstacles, boundary units, grouping macros, and remaining units.
   - Verification: obstacle placement, boundary-first placement, grouping macro expansion, empty connectivity, exact `block_count` expansion.

9. Local search and repair
   - Files: local search, move, repair, boundary snap, MIB sync, compaction, and budget sections in `iccad2026contest/my_optimizer.py`; optional synthetic fixtures.
   - Start conservatively. Use explicit bounded iteration counts or disable expensive moves until a budget is set. Never mutate immutable geometry.
   - Verification: seeded move fixtures, search-never-loses-feasibility, boundary snap after compaction, incompatible MIB does not break area tolerance, synthetic 21/60/120 stress once budget exists.

10. Optional ML initializer
    - Files: none for initial correctness path unless approved.
    - Leave disabled by default. Any future ML seed is advisory only and must pass through dimension planning, legalization, candidate manager, and preflight.
    - Verification: baseline solver requires no training data, downloads, artifacts, or external services.

## Subagent Plan

Because the initial implementation target is a single file, use subagents carefully. The main agent should own integration and final edits to `iccad2026contest/my_optimizer.py` unless subagent tooling supports disjoint patch application reliably.

Good subagent candidates:

- Parser and geometry reviewer: read-only or isolated patch for parser, immutable geometry, and dimension planner sections. May edit only those named sections plus associated fixture snippets if a test harness exists.
- Preflight/scoring reviewer: read-only or isolated patch for evaluator-parity checks, proxy scoring, and hand-computed fixtures. May edit only preflight/scoring sections and related tests.
- Fallback/candidate reviewer: read-only or isolated patch for fallback and candidate manager logic. May edit only fallback/candidate manager sections and related tests.
- Soft-constraint/search reviewer: read-only or isolated patch for macro planning, constructive initialization, local search, and soft-violation logic. May edit only those sections after parser, geometry, preflight, and fallback are stable.

Shared or integration-only files:

- `iccad2026contest/my_optimizer.py`: main agent coordinates all edits and resolves conflicts.
- `doc/tasks/progress.md`: main agent updates progress after integrating subagent work.
- `iccad2026contest/iccad2026_evaluate.py`, `iccad2026contest/optimizer_template.py`, dataset loaders, validation data: read-only unless user explicitly approves changes.

Merge approach:

- Main agent creates section anchors in `my_optimizer.py` first.
- Subagents return small patches or concrete code snippets scoped to assigned sections.
- Main agent reads and integrates patches, runs relevant checks, updates progress, and records any blocked work.
- If write scopes would overlap heavily, do not spawn subagents for code edits; use them only for review and test-case design.

## Implementation Order

1. Create `iccad2026contest/my_optimizer.py` from the template pattern, not by editing `optimizer_template.py`.
   - Local check: Python syntax compile if dependencies are available; otherwise use `python -m py_compile iccad2026contest/my_optimizer.py` only after confirming it does not trigger dataset access.

2. Implement Optimizer Entry, input normalization, constraint parser, immutable geometry, and dimension planner.
   - Local check: synthetic direct calls for validator dummy input, all-soft 2-block input, fixed/preplaced target input, and parser fixtures.

3. Implement Hard-Constraint Preflight Checker and Proxy Scoring.
   - Local check: edge-touching legal, positive-overlap illegal, area tolerance boundary, immutable geometry, empty connectivity, HPWL/bbox hand checks, and evaluator helper differential checks if imports are available.

4. Implement Deterministic Legal Fallback and Candidate Manager.
   - Local check: two all-soft golden fixture, fixed-shape fixture, preplaced obstacle fixture, fallback retention, infeasible candidate rejection.

5. Wire `solve()` end to end with fallback-only behavior.
   - Gate with approval: from `iccad2026contest/`, run `python iccad2026_evaluate.py --validate my_optimizer.py --quick`, then `python iccad2026_evaluate.py --validate my_optimizer.py`.

6. Implement Macro and Soft-Constraint Planner plus Constraint-Aware Constructive Initializer.
   - Local check: grouping macro expansion, MIB metadata, boundary intent, obstacle placement, exact `block_count` expansion, hard preflight before candidate acceptance.

7. Add conservative Local Search and Repair only after fallback and constructive paths are hard-feasible.
   - Local check: seeded move tests and bounded synthetic 21/60/120 stress checks.

8. Run contest evaluator gates after user approval and with an output-file plan.
   - Single case first, then full validation. Triage every infeasible cost `10.0` before score tuning.

9. Tune proxy weights, seed orders, and local-search budgets only after hard feasibility is stable.
   - Record tuning decisions in code comments or progress notes when they materially affect behavior.

## Testing and Quality Gates

Discovered commands:

- Environment setup, requires approval because it creates/writes environment state:
  - From repo root: `python -m venv venv`
  - From repo root: `pip install -r iccad2026contest/requirements.txt`
  - From repo root: `pip install -r requirements.txt`

- Contest smoke, run from `iccad2026contest/`; imports dependencies and does not intentionally write output files:
  - `python iccad2026_evaluate.py --info`

- Contest validation, run from `iccad2026contest/`; requires `my_optimizer.py`:
  - `python iccad2026_evaluate.py --validate my_optimizer.py --quick`
  - `python iccad2026_evaluate.py --validate my_optimizer.py`

- Contest evaluation, run from `iccad2026contest/`; writes JSON by default and may load or auto-download validation data if missing:
  - `python iccad2026_evaluate.py --evaluate my_optimizer.py --test-id 0`
  - `python iccad2026_evaluate.py --evaluate my_optimizer.py --test-id 0 --verbose`
  - `python iccad2026_evaluate.py --evaluate my_optimizer.py`
  - Prefer an explicit approved `--output` path when running evaluator commands.

- Saved-solution and baseline commands, run only when needed and approved:
  - `python iccad2026_evaluate.py --evaluate my_optimizer.py --save-solutions`
  - `python iccad2026_evaluate.py --score my_optimizer_solutions.json`
  - `python iccad2026_evaluate.py --baseline`
  - `python iccad2026_evaluate.py --baseline --output baselines.json`

- Commands that may access or download training data; do not run for the baseline heuristic implementation unless approved:
  - From `iccad2026contest/`: `python iccad2026_evaluate.py --training`
  - From `iccad2026contest/`: `python training_example.py`
  - From repo root: `python iccad2026contest/training_example.py`

- Visualization and loader examples may write PNGs, invoke display behavior, or auto-download data; run only with approval:
  - From `iccad2026contest/`: `python iccad2026_evaluate.py --visualize --test-id 0`
  - From repo root: `python liteLoader.py`
  - From repo root: `python litetestLoader.py`
  - From repo root: `python primeLoader.py`
  - From repo root: `python primetestLoader.py`
  - From repo root: `python validate.py` is inferred only and may have an import-name mismatch noted in `doc/repo-map.md`.

Missing commands:

- Build: no discovered build command.
- Unit tests: no discovered configured unit-test runner.
- Lint: no discovered lint command or configuration.
- Format: no discovered formatter or format-check command.
- Type check: no discovered type-check command.
- Static analysis: no discovered static-analysis command.
- CI: no discovered CI workflow.

Required local verification before evaluator gates:

- Synthetic all-soft, fixed, preplaced, boundary, grouping, MIB, empty-connectivity, edge-touching, positive-overlap, and 120-block stress fixtures.
- Internal preflight and evaluator helper agreement on golden and randomized cases where evaluator helpers can be imported.
- Candidate manager property: a later infeasible or malformed candidate never replaces an existing feasible candidate.
- Fallback is hard feasible for internally consistent synthetic inputs.

## Progress Tracking

Keep `doc/tasks/progress.md` current throughout the implementation:

- Mark a module as in progress when its first code edit starts.
- Add timestamped checkpoint notes after each module or small workstream, including what changed, what checks ran, and whether verification passed.
- Mark module task boxes complete only when the implementation and module-specific verification are both complete.
- Mark full-project gates only after the command or check has actually run and passed.
- Record blocked items with the blocking reason, exact command or file involved, and what user input or external state is needed.
- Preserve existing checked boxes when they still apply.

## Commit or Checkpoint Strategy

Do not commit, branch, stash, merge, rebase, pull, or push unless the user explicitly requests it.

If commits are requested later, make logical checkpoints in dependency order:

1. Optimizer scaffold, parser, immutable geometry, dimension planner.
2. Preflight, proxy scoring, fallback, candidate manager.
3. Macro planner and constructive initializer.
4. Local search and repair.
5. Tests/fixtures and documentation/progress updates.

If commits are not requested, keep the final diff clean and grouped by module in the final response. Keep generated outputs, logs, caches, datasets, result JSON, solution JSON, and visualizations untracked unless the user explicitly asks to track them.

## Acceptance Criteria

The implementation is done when:

- `iccad2026contest/my_optimizer.py` exists and is not a direct edit to `optimizer_template.py`.
- `solve()` implements the evaluator-facing signature and returns exactly `block_count` finite positive rectangle tuples ordered by original block id.
- Hard constraints are enforced or preflight-gated: no overlaps, soft-block area within 1%, exact fixed dimensions, exact preplaced position/dimensions.
- Soft constraints for boundary, grouping, and MIB are parsed, measured, and improved where possible without compromising hard feasibility.
- A deterministic legal fallback is available for every internally consistent input case.
- Candidate Manager retains the best feasible candidate and never returns an infeasible candidate while a feasible candidate exists.
- Local search, if enabled, is bounded and cannot mutate immutable geometry.
- Optional ML remains disabled unless packaging, weights, and data access are approved; baseline correctness does not require ML.
- Module tasks in `doc/tasks/` are completed or explicitly marked blocked with reasons.
- Tests or synthetic checks are added or updated as appropriate for the repository's missing unit-test infrastructure.
- Configured gates pass: because build, unit test, lint, format, type-check, static analysis, and CI are missing, do not claim them as passed unless added and run.
- Contest gates pass when run with approval:
  - `python iccad2026_evaluate.py --validate my_optimizer.py`
  - `python iccad2026_evaluate.py --evaluate my_optimizer.py --test-id 0`
  - `python iccad2026_evaluate.py --evaluate my_optimizer.py`
- Full local validation reports 100/100 feasible cases before score tuning is considered meaningful.
- Docs are updated only where needed.
- No unrelated files are changed.

## Uncertainty Protocol

Make conservative, documented assumptions when safe:

- Prefer single-file `iccad2026contest/my_optimizer.py` until packaging rules confirm helper modules.
- Prefer deterministic shelves or the fallback packer for first constructive placement if the optimized representation is not settled.
- Preserve hard feasibility over every soft constraint and quality metric.
- Use evaluator behavior as the oracle for hard checks and metrics.

Ask the user before proceeding when:

- Contest README/PDF and evaluator behavior conflict in a way that changes implementation behavior.
- Final packaging, helper modules, model artifacts, or training-data access affect the chosen design.
- A command may install dependencies, download data, train, evaluate, visualize, write generated outputs, or run for a long time without prior approval.
- A destructive action or git state change is needed.
- Credentials, external services, or lab-server access are required.
- Quality gates cannot be run and no local substitute is defensible.

If a command fails because of missing dependencies or sandbox/network restrictions and the command is important, request approval to run the appropriate install or rerun command with escalation rather than silently skipping the gate.

## Final Response Requirements

End with a concise implementation report that includes:

- What was implemented, grouped by workstream.
- Changed files, grouped by workstream.
- Tests, synthetic checks, and quality gates run, with command output summaries and pass/fail status.
- Evaluator results, including feasibility count, total score, runtime summary, and any generated output paths if evaluator commands ran.
- Known limitations, blocked items, or unresolved open questions.
- Confirmation that generated JSON/PNG/log/cache/dataset artifacts were not tracked unless explicitly requested.
- Any follow-up required before final contest submission.
