# Quality Gates

## Environment Summary

- Repository root: `/home/kuotzuwei15/pda/FloorSet`.
- Primary contest working directory: `/home/kuotzuwei15/pda/FloorSet/iccad2026contest`.
- Project type: Python repository with pip requirements.
- Dependency files discovered:
  - `requirements.txt`
  - `iccad2026contest/requirements.txt`
- No `pyproject.toml`, `setup.py`, `setup.cfg`, `tox.ini`, `noxfile.py`, `pytest.ini`, `Makefile`, `justfile`, `package.json`, `Cargo.toml`, `CMakeLists.txt`, or CI workflow files were discovered by metadata search.
- Local validation tensor data is present under `LiteTensorDataTest/`, but dataset loaders may still auto-download data if expected data is missing.
- Environment setup commands discovered:
  - Status: `Discovered`
  - Working directory: repository root
  - Command: `python -m venv venv`
  - Source: `iccad2026contest/README.md`
  - Notes: creates a local virtual environment.
  - Status: `Discovered`
  - Working directory: repository root
  - Command: `source venv/bin/activate`
  - Source: `iccad2026contest/README.md`
  - Notes: shell-specific activation command.
  - Status: `Discovered`
  - Working directory: repository root
  - Command: `pip install -r iccad2026contest/requirements.txt`
  - Source: `iccad2026contest/README.md`, `AGENTS.md`
  - Notes: package-manager command; may require network and writes to the active environment.
  - Status: `Discovered`
  - Working directory: repository root
  - Command: `pip install -r requirements.txt`
  - Source: `README.md`, `AGENTS.md`
  - Notes: package-manager command; may require network and writes to the active environment.

## Build Commands

- Status: `Missing`
- No repository-defined build command was discovered.
- The project appears to be run directly from Python source after dependency installation.

## Unit Test Commands

- Status: `Missing`
- No conventional unit test command was discovered.
- No `pytest`, `unittest`, `tox`, `nox`, or test-runner configuration was discovered.
- Files named `prime_dataset_test.py` and `lite_dataset_test.py` are dataset loader modules, not discovered unit-test entry points.

## Integration Test Commands

- Status: `Discovered`
- Working directory: `iccad2026contest/`
- Command: `python iccad2026_evaluate.py --validate my_optimizer.py`
- Source: `iccad2026contest/README.md`, `AGENTS.md`, `iccad2026contest/iccad2026_evaluate.py`
- Notes: validates optimizer file existence, syntax, module load, optimizer class discovery, and non-quick dummy `solve()` execution. Requires a contestant optimizer file. Imports project dependencies. Not run.

- Status: `Discovered`
- Working directory: `iccad2026contest/`
- Command: `python iccad2026_evaluate.py --validate my_optimizer.py --quick`
- Source: `iccad2026contest/iccad2026_evaluate.py`
- Notes: quick submission validation; skips dummy `solve()` execution. Requires a contestant optimizer file. Imports project dependencies. Not run.

- Status: `Discovered`
- Working directory: `iccad2026contest/`
- Command: `python iccad2026_evaluate.py --evaluate my_optimizer.py --test-id 0`
- Source: `iccad2026contest/README.md`, `AGENTS.md`, `iccad2026contest/iccad2026_evaluate.py`
- Notes: single validation-case integration/evaluator run. Writes a results JSON by default. Loads validation data from `../LiteTensorDataTest/` and may auto-download if missing. Runtime depends on optimizer. Not run.

- Status: `Discovered`
- Working directory: `iccad2026contest/`
- Command: `python iccad2026_evaluate.py --evaluate my_optimizer.py --test-id 0 --verbose`
- Source: `iccad2026contest/iccad2026_evaluate.py`
- Notes: verbose variant of the single validation-case integration/evaluator run. Writes a results JSON by default. Not run.

## Lint Commands

- Status: `Missing`
- No repository-defined lint command was discovered.
- No Ruff, Flake8, Pylint, or equivalent lint configuration was discovered.

## Format Commands

- Status: `Missing`
- No repository-defined format or format-check command was discovered.
- No Black, Ruff format, isort, Prettier, or equivalent formatter configuration was discovered.

## Type-Check Commands

- Status: `Missing`
- No repository-defined type-check command was discovered.
- No mypy, pyright, pyre, or equivalent type-check configuration was discovered.

## Static Analysis Commands

- Status: `Missing`
- No repository-defined static-analysis command was discovered.
- No Bandit, Semgrep, CodeQL workflow, clang-tidy, cppcheck, or equivalent static-analysis configuration was discovered.

## Benchmark or Evaluator Commands

- Status: `Discovered`
- Working directory: `iccad2026contest/`
- Command: `python iccad2026_evaluate.py --evaluate my_optimizer.py`
- Source: `README.md`, `iccad2026contest/README.md`, `AGENTS.md`, `iccad2026contest/optimizer_template.py`, `iccad2026contest/iccad2026_evaluate.py`
- Notes: evaluates an optimizer on the validation set and computes score. Writes `<submission_name>_results.json` by default. Loads validation data and may auto-download if missing. Runtime depends on optimizer and all 100 validation cases. Not run.

- Status: `Discovered`
- Working directory: `iccad2026contest/`
- Command: `python iccad2026_evaluate.py --evaluate my_optimizer.py --save-solutions`
- Source: `iccad2026contest/README.md`, `AGENTS.md`
- Notes: evaluates and writes both results JSON and `<submission_name>_solutions.json`. Loads validation data and may auto-download if missing. Runtime depends on optimizer. Not run.

- Status: `Discovered`
- Working directory: `iccad2026contest/`
- Command: `python iccad2026_evaluate.py --score my_optimizer_solutions.json`
- Source: `iccad2026contest/README.md`, `AGENTS.md`, `iccad2026contest/iccad2026_evaluate.py`
- Notes: re-scores saved solutions without rerunning the optimizer. Requires a solution JSON. Loads validation data and may auto-download if missing. Writes output only if `--output` is provided. Not run.

- Status: `Discovered`
- Working directory: `iccad2026contest/`
- Command: `python iccad2026_evaluate.py --baseline`
- Source: `iccad2026contest/README.md`, `AGENTS.md`, `iccad2026contest/iccad2026_evaluate.py`
- Notes: generates validation baseline metrics. Writes `baseline_metrics.json` by default. Loads validation data and may auto-download if missing. Not run.

- Status: `Discovered`
- Working directory: `iccad2026contest/`
- Command: `python iccad2026_evaluate.py --baseline --output baselines.json`
- Source: `iccad2026contest/iccad2026_evaluate.py`
- Notes: baseline generation with explicit output file. Loads validation data and may auto-download if missing. Not run.

- Status: `Discovered`
- Working directory: `iccad2026contest/`
- Command: `python iccad2026_evaluate.py --training`
- Source: `iccad2026contest/README.md`, `AGENTS.md`, `iccad2026contest/iccad2026_evaluate.py`
- Notes: explores FloorSet-Lite training data. May auto-download or touch the 1M-sample training dataset if missing locally. Potentially large data access. Not run.

- Status: `Discovered`
- Working directory: `iccad2026contest/`
- Command: `python training_example.py`
- Source: `iccad2026contest/README.md`
- Notes: differentiable training-loss example. May auto-download training data if missing. Not run.

- Status: `Discovered`
- Working directory: repository root
- Command: `python iccad2026contest/training_example.py`
- Source: `iccad2026contest/training_example.py`, `AGENTS.md`
- Notes: equivalent documented script invocation from repository root. May auto-download training data if missing. Not run.

## Smoke Test Commands

- Status: `Discovered`
- Working directory: `iccad2026contest/`
- Command: `python iccad2026_evaluate.py --info`
- Source: `iccad2026contest/README.md`, `AGENTS.md`, `iccad2026contest/iccad2026_evaluate.py`
- Notes: prints contest information and does not intentionally write result files. Still imports project dependencies. Not run.

- Status: `Discovered`
- Working directory: `iccad2026contest/`
- Command: `python iccad2026_evaluate.py --visualize --test-id 0`
- Source: `iccad2026contest/README.md`, `AGENTS.md`, `iccad2026contest/iccad2026_evaluate.py`
- Notes: visualizes a validation case, saves `validation_case_0.png`, and calls matplotlib display logic. Loads validation data and may auto-download if missing. Not run.

- Status: `Discovered`
- Working directory: repository root
- Command: `python liteLoader.py`
- Source: script entry point and `README.md` loader guidance
- Notes: loads FloorSet-Lite training data and visualizes a sample. May auto-download large Lite training data if missing and may open visualization UI. Not run.

- Status: `Discovered`
- Working directory: repository root
- Command: `python litetestLoader.py`
- Source: script entry point and `README.md` loader guidance
- Notes: loads FloorSet-Lite test/validation data and visualizes a sample. May auto-download validation data if missing and may open visualization UI. Not run.

- Status: `Discovered`
- Working directory: repository root
- Command: `python primeLoader.py`
- Source: script entry point and `README.md` loader guidance
- Notes: loads FloorSet-Prime training data and visualizes a sample. May auto-download large Prime training data if missing and may open visualization UI. Not run.

- Status: `Discovered`
- Working directory: repository root
- Command: `python primetestLoader.py`
- Source: script entry point and `README.md` loader guidance
- Notes: loads FloorSet-Prime test data and visualizes a sample. May auto-download data if missing and may open visualization UI. Not run.

- Status: `Inferred`
- Working directory: repository root
- Command: `python validate.py`
- Source: executable script-style file with top-level validation example; `README.md` references `estimate_cost` in `validate.py`
- Notes: not explicitly documented as a command. It imports Prime dataset utilities and estimates cost for one batch/sample. May auto-download Prime data if missing. `doc/repo-map.md` notes an observed import-name mismatch that was not tested. Not run.

## Verified Commands

- Status: `Missing`
- No quality-gate, evaluator, test, lint, format, type-check, static-analysis, benchmark, smoke-test, package-manager, or project script command was run during this session.
- Only read-only discovery commands were run to inspect files and metadata.

## Commands Not Run

- `python -m venv venv`
  - Reason: environment-creation command; not needed for discovery and not explicitly approved to execute.
- `source venv/bin/activate`
  - Reason: shell environment mutation; not needed for discovery.
- `pip install -r requirements.txt`
  - Reason: package-manager command; may require network and writes to environment.
- `pip install -r iccad2026contest/requirements.txt`
  - Reason: package-manager command; may require network and writes to environment.
- `python iccad2026_evaluate.py --info`
  - Working directory: `iccad2026contest/`
  - Reason: project smoke command; not run because no project tooling was approved for execution.
- `python iccad2026_evaluate.py --validate my_optimizer.py`
  - Working directory: `iccad2026contest/`
  - Reason: requires a contestant optimizer file and explicit approval.
- `python iccad2026_evaluate.py --validate my_optimizer.py --quick`
  - Working directory: `iccad2026contest/`
  - Reason: requires a contestant optimizer file and explicit approval.
- `python iccad2026_evaluate.py --evaluate my_optimizer.py --test-id 0`
  - Working directory: `iccad2026contest/`
  - Reason: evaluator command; writes result JSON by default and may load or auto-download validation data.
- `python iccad2026_evaluate.py --evaluate my_optimizer.py --test-id 0 --verbose`
  - Working directory: `iccad2026contest/`
  - Reason: evaluator command; writes result JSON by default and may load or auto-download validation data.
- `python iccad2026_evaluate.py --evaluate my_optimizer.py`
  - Working directory: `iccad2026contest/`
  - Reason: full evaluator command; writes result JSON by default and can be long depending on optimizer.
- `python iccad2026_evaluate.py --evaluate my_optimizer.py --save-solutions`
  - Working directory: `iccad2026contest/`
  - Reason: full evaluator command; writes results and solutions JSON.
- `python iccad2026_evaluate.py --score my_optimizer_solutions.json`
  - Working directory: `iccad2026contest/`
  - Reason: requires saved solutions JSON and explicit approval.
- `python iccad2026_evaluate.py --baseline`
  - Working directory: `iccad2026contest/`
  - Reason: writes `baseline_metrics.json` by default.
- `python iccad2026_evaluate.py --baseline --output baselines.json`
  - Working directory: `iccad2026contest/`
  - Reason: writes baseline output file.
- `python iccad2026_evaluate.py --training`
  - Working directory: `iccad2026contest/`
  - Reason: may access or auto-download large training data.
- `python training_example.py`
  - Working directory: `iccad2026contest/`
  - Reason: may access or auto-download training data.
- `python iccad2026contest/training_example.py`
  - Working directory: repository root
  - Reason: may access or auto-download training data.
- `python iccad2026_evaluate.py --visualize --test-id 0`
  - Working directory: `iccad2026contest/`
  - Reason: writes PNG output and may invoke GUI/display behavior.
- `python liteLoader.py`
  - Working directory: repository root
  - Reason: may access or auto-download large Lite training data and opens visualization.
- `python litetestLoader.py`
  - Working directory: repository root
  - Reason: may access or auto-download validation data and opens visualization.
- `python primeLoader.py`
  - Working directory: repository root
  - Reason: may access or auto-download large Prime training data and opens visualization.
- `python primetestLoader.py`
  - Working directory: repository root
  - Reason: may access or auto-download Prime test data and opens visualization.
- `python validate.py`
  - Working directory: repository root
  - Reason: inferred script command; may access or auto-download Prime data and was not approved for execution.

## Missing Quality Gates

- Build: no discovered build command.
- Unit tests: no discovered unit-test command or configuration.
- Lint: no discovered lint command or configuration.
- Format: no discovered formatter or format-check command.
- Type-check: no discovered type-check command or configuration.
- Static analysis: no discovered static-analysis command or configuration.
- CI: no discovered CI workflow or pipeline file.
- Conventional package/test task runner: no discovered Makefile, justfile, npm scripts, tox, nox, or pyproject task configuration.

## Recommended Minimum Done Criteria

- For contestant optimizer changes, use discovered contest gates first:
  - Run `python iccad2026_evaluate.py --validate my_optimizer.py` from `iccad2026contest/` after the optimizer file exists and dependencies are installed.
  - Run `python iccad2026_evaluate.py --evaluate my_optimizer.py --test-id 0` from `iccad2026contest/` for a single-case integration/evaluator check, with an approved output-file plan because evaluation writes JSON by default.
  - Run `python iccad2026_evaluate.py --evaluate my_optimizer.py` from `iccad2026contest/` before considering a solver ready for validation-set scoring, with approval for runtime and generated JSON output.
- For saved-solution workflows, run `python iccad2026_evaluate.py --score my_optimizer_solutions.json` from `iccad2026contest/` after producing a solutions JSON.
- For documentation-only changes, no project quality gate was discovered beyond reviewing the affected Markdown files.
- Because lint, format, type-check, static analysis, and unit-test gates are missing, do not cite generic commands as required gates until the repository adds explicit configuration or scripts.
- Future improvement recommendation: add a lightweight syntax/import smoke gate and explicit lint/format/type-check configuration if the project wants non-contest quality gates.
