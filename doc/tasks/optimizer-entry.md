# Optimizer Entry

## Goal

Implement the evaluator-facing optimizer class and `solve()` method that orchestrate one FloorSet case and always return exactly one rectangle tuple per active block.

## Inputs

- `doc/proposal.md`: Objective, feasibility-first strategy, implementation target `iccad2026contest/my_optimizer.py`, and validation targets.
- `doc/high-level-design.md`: Optimizer Entry module, evaluator contract, data flow, and best-feasible fallback behavior.
- `doc/detailed-design.md`: Optimizer Entry responsibility, orchestration pseudocode, failure handling, and open class-name/budget questions.
- `doc/test-plan.md`: Optimizer Entry unit tests, import smoke, validator quick/full gates, and future done criteria.

## Write Scope

`iccad2026contest/my_optimizer.py` optimizer class, `solve()` orchestration, per-call context wiring, final return conversion, and future synthetic entrypoint tests if a test harness is added.

## Read Scope

`iccad2026contest/optimizer_template.py`, `iccad2026contest/iccad2026_evaluate.py`, `doc/proposal.md`, `doc/high-level-design.md`, `doc/detailed-design.md`, `doc/test-plan.md`, and all downstream task files in `doc/tasks/`.

## Dependencies

All internal module tasks: Input Normalization and Constraint Parser, Immutable Geometry Registry, Dimension Planner, Deterministic Legal Fallback, Macro and Soft-Constraint Planner, Constraint-Aware Constructive Initializer, Candidate Manager, Local Search and Repair, Proxy Scoring, Hard-Constraint Preflight Checker, and optionally Optional ML Initializer.

## Tasks

- [x] Create or update the copied optimizer file so it exposes an evaluator-discoverable optimizer class and the required `solve(block_count, area_targets, b2b_connectivity, p2b_connectivity, pins_pos, constraints, target_positions=None)` signature.
- [x] Build a per-call context that passes normalized inputs through immutable geometry, dimension planning, fallback construction, macro planning, constructive initialization, candidate management, local search, preflight, and final selection.
- [x] Ensure the entry path does not mutate evaluator inputs, load datasets, write files, train models, or depend on cross-call mutable state.
- [x] Add exception-path handling so constructive initialization, proxy scoring, local search, or optional ML failures return the preflighted fallback when available.
- [x] Convert the retained candidate into a Python list of exactly `block_count` finite `(x, y, width, height)` tuples ordered by original block id.
- [x] Add an entry-level smoke fixture for the validator dummy shape, including `target_positions=None`.

## Tests and Quality Gates

- [x] With user approval, run from `iccad2026contest/`: `python iccad2026_evaluate.py --validate my_optimizer.py --quick`.
- [x] With user approval, run from `iccad2026contest/`: `python iccad2026_evaluate.py --validate my_optimizer.py`.
- [x] Verify import has no file I/O, dataset access, generated output, or dependency on training data.
- [x] Run the entry-level smoke fixture without bytecode generation or evaluator dataset access.

## Done When

- [x] `solve()` accepts the evaluator arguments and returns exactly `block_count` valid rectangle tuples for synthetic and validator dummy inputs.
- [x] Entry-level fallback behavior is exercised when an optimized layer is forced to fail.
- [x] Expected validator gates pass when run with approval.

## Cycle Evidence

- 2026-06-14: Created `iccad2026contest/my_optimizer.py` with a class-name-discoverable `MyOptimizer`, fallback-first `solve()` orchestration, per-call context, preflighted candidate retention, and bounded no-op hooks for future macro, constructive, and local-search modules.
- 2026-06-14: `PYTHONDONTWRITEBYTECODE=1 python -c "... compile(...)"` passed for `iccad2026contest/my_optimizer.py`.
- 2026-06-14: Synthetic direct-call check passed for the 5-block validator dummy shape with `target_positions=None`, a preplaced target preservation case, and a forced quality-layer failure returning the fallback.
- 2026-06-14: Evaluator-style `importlib.util.spec_from_file_location(...)` load check passed without importing the evaluator or touching datasets.
- 2026-06-14: Evaluator `--validate` gates were not run in the initial scaffold cycle.
- 2026-06-14: Added `iccad2026contest/optimizer_entry_smoke.py`, a persisted validator-dummy entry smoke fixture using plain Python list inputs, `target_positions=None`, output-format checks, no-overlap checks, area checks, and forced quality-layer fallback coverage.
- 2026-06-14: `python -B iccad2026contest/optimizer_entry_smoke.py` passed and printed `optimizer-entry smoke passed`.
- 2026-06-14: A first source compile check failed because the shell one-liner was quoted incorrectly; rerun with `python -B -c "import pathlib; ... compile(...)"` passed for `iccad2026contest/my_optimizer.py` and `iccad2026contest/optimizer_entry_smoke.py`.
- 2026-06-14: From `iccad2026contest/`, `python -B iccad2026_evaluate.py --validate my_optimizer.py --quick` passed: file exists, syntax valid, module loads, and optimizer class `MyOptimizer` is discoverable.
- 2026-06-14: From `iccad2026contest/`, `python -B iccad2026_evaluate.py --validate my_optimizer.py` passed: quick checks passed, validator dummy solve returned the correct format, and sample runtime printed as `0.000s`.
- 2026-06-14: Optimized `solve()` orchestration to pass the already planned `PlacementUnitSet` into `_run_local_search()` instead of recomputing `_plan_soft_units()` after constructive initialization. `_run_local_search()` remains backward compatible when called directly without a unit set. `iccad2026contest/optimizer_entry_smoke.py` now monkeypatches `_plan_soft_units()` and asserts the entry path plans units exactly once per solve. `python -B iccad2026contest/optimizer_entry_smoke.py`, `python -B iccad2026contest/optimizer_local_search_smoke.py`, and a no-bytecode syntax compile for `iccad2026contest/my_optimizer.py` plus `iccad2026contest/optimizer_entry_smoke.py` passed. Contest evaluator validation was not run in this optimization cycle.
