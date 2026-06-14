# Submission Check

## Required Deliverables

- `iccad2026contest/my_optimizer.py` - required. Contest optimizer file implementing a discoverable optimizer class and `solve()` returning one `(x, y, width, height)` tuple per active block.
- `MyOptimizer` in `iccad2026contest/my_optimizer.py` - required. Present and discovered by the evaluator.
- `solve(block_count, area_targets, b2b_connectivity, p2b_connectivity, pins_pos, constraints, target_positions=None)` - required. Present and accepted by evaluator validation.
- `LiteTensorDataTest/` - generated/local validation data, not a contestant optimizer deliverable. Present locally and used for evaluator runs via `--data-path ../`.
- `/tmp/my_optimizer_test0_results.json` - generated local evaluator output, not a submission deliverable.
- `/tmp/my_optimizer_full_results.json` - generated local evaluator output, not a submission deliverable.
- Final official upload/archive layout - unknown from the read README/PDF/evaluator sources. Inference: single-file submission of `iccad2026contest/my_optimizer.py` is the safest contest artifact unless official rules say otherwise.

## Present Files

- `iccad2026contest/my_optimizer.py` exists and is currently untracked in git.
- `iccad2026contest/optimizer_template.py` exists and remains the reference template.
- `iccad2026contest/iccad2026_evaluate.py`, `iccad2026contest/README.md`, and `iccad2026contest/FloorplanningContest_ICCAD_2026_v10.pdf` exist.
- `doc/problem-brief.md`, `doc/test-plan.md`, and `doc/quality-gates.md` exist and were read.
- `LiteTensorDataTest/` exists with 100 config directories, 200 `.pth` files, and size `256M`.
- `git ls-files LiteTensorDataTest | wc -l` reports 200 tracked validation-data files.
- Development/planning files are untracked: `doc/*.md`, `doc/tasks/*.md`, `iccad2026contest/my_optimizer.py`, `iccad2026contest/optimizer_*_smoke.py`, and `iccad2026contest/validation_case_33.png`.
- Ignored generated files are present: root `__pycache__/`, `iccad2026contest/__pycache__/`, and `iccad2026contest/my_optimizer_results.json`.

## Missing Files

- No required optimizer file is missing.
- No local validation data is missing for the evaluator path used in this check.
- Missing or unknown: official final packaging rules beyond an optimizer Python file.
- Missing: repository-defined build, lint, format, type-check, static-analysis, CI, or unit-test runner commands.

## Format Checks

- `iccad2026contest/my_optimizer.py` passed Python bytecode compilation with `python`.
- `iccad2026contest/my_optimizer.py` passed evaluator syntax/import/class-discovery validation.
- The evaluator discovered optimizer class `MyOptimizer`.
- The evaluator dummy `solve()` check passed and returned the correct list format.
- Static risk: `MyOptimizer` does not visibly subclass `FloorplanOptimizer`, unlike `optimizer_template.py`; the local evaluator accepts common class names and validation passed.
- Secret-pattern scan over source/docs excluding `.git`, `LiteTensorDataTest/`, and `data/*.tar.gz` found only policy/report text mentioning secret/token terms, not concrete credentials.

## Commands Run

- Working directory: repository root. Passed. `sed -n '1,260p' /home/kuotzuwei15/.codex/skills/submission-check/SKILL.md`
- Working directory: repository root. Passed. `git status --short --branch`
- Working directory: repository root. Passed. `rg --files doc iccad2026contest LiteTensorDataTest`
- Working directory: repository root. Passed. `sed -n '1,280p' doc/problem-brief.md`
- Working directory: repository root. Passed. `sed -n '1,320p' doc/test-plan.md`
- Working directory: repository root. Passed. `sed -n '1,260p' doc/quality-gates.md`
- Working directory: repository root. Passed. `sed -n '1,390p' iccad2026contest/README.md`
- Working directory: repository root. Passed. `rg -n "data_path|LiteTensorDataTest|--output|--validate|--evaluate|--test-id|results|argparse|def main" iccad2026contest/iccad2026_evaluate.py`
- Working directory: repository root. Passed. `sed -n '1840,1948p' iccad2026contest/iccad2026_evaluate.py`
- Working directory: repository root. Passed. `python3 -V`
- Working directory: repository root. Passed. `python -V`
- Working directory: repository root. Failed. `python3 -B -c "import sys; print(sys.executable); import numpy, torch, shapely, tqdm; print('deps-ok')"`
- Working directory: repository root. Passed. `python -B -c "import sys; print(sys.executable); import numpy, torch, shapely, tqdm; print('deps-ok')"`
- Working directory: repository root. Passed. `sed -n '1,260p' doc/submission-check.md`
- Working directory: repository root. Passed. `python -B -m py_compile iccad2026contest/my_optimizer.py iccad2026contest/optimizer_entry_smoke.py iccad2026contest/optimizer_parser_smoke.py iccad2026contest/optimizer_immutable_smoke.py iccad2026contest/optimizer_dimension_smoke.py iccad2026contest/optimizer_fallback_smoke.py iccad2026contest/optimizer_macro_smoke.py iccad2026contest/optimizer_constructive_smoke.py iccad2026contest/optimizer_candidate_manager_smoke.py iccad2026contest/optimizer_local_search_smoke.py iccad2026contest/optimizer_proxy_scoring_smoke.py iccad2026contest/optimizer_preflight_smoke.py`
- Working directory: repository root. Passed. `python -B iccad2026contest/optimizer_entry_smoke.py`
- Working directory: repository root. Passed. `python -B iccad2026contest/optimizer_parser_smoke.py`
- Working directory: repository root. Passed. `python -B iccad2026contest/optimizer_immutable_smoke.py`
- Working directory: repository root. Passed. `python -B iccad2026contest/optimizer_dimension_smoke.py`
- Working directory: repository root. Passed. `python -B iccad2026contest/optimizer_fallback_smoke.py`
- Working directory: repository root. Passed. `python -B iccad2026contest/optimizer_macro_smoke.py`
- Working directory: repository root. Passed. `python -B iccad2026contest/optimizer_constructive_smoke.py`
- Working directory: repository root. Passed. `python -B iccad2026contest/optimizer_candidate_manager_smoke.py`
- Working directory: repository root. Passed. `python -B iccad2026contest/optimizer_local_search_smoke.py`
- Working directory: repository root. Passed with Matplotlib cache warning. `python -B iccad2026contest/optimizer_proxy_scoring_smoke.py`
- Working directory: repository root. Passed with Matplotlib cache warning. `python -B iccad2026contest/optimizer_preflight_smoke.py`
- Working directory: `iccad2026contest/`. Passed with Matplotlib cache warning. `python -B iccad2026_evaluate.py --validate my_optimizer.py`
- Working directory: `iccad2026contest/`. Passed with Matplotlib cache warning. `python -B iccad2026_evaluate.py --evaluate my_optimizer.py --test-id 0 --data-path ../ --output /tmp/my_optimizer_test0_results.json`
- Working directory: `iccad2026contest/`. Passed with Matplotlib cache warning. `python -B iccad2026_evaluate.py --evaluate my_optimizer.py --data-path ../ --output /tmp/my_optimizer_full_results.json`
- Working directory: repository root. Passed. `python -B - <<'PY' ... /tmp/my_optimizer_full_results.json summary ... PY`
- Working directory: repository root. Passed. `du -sh LiteTensorDataTest`
- Working directory: repository root. Passed. `find LiteTensorDataTest -mindepth 1 -maxdepth 1 -type d | wc -l`
- Working directory: repository root. Passed. `find LiteTensorDataTest -maxdepth 2 -type f | wc -l`
- Working directory: repository root. Passed. `git diff --name-only`
- Working directory: repository root. Passed. `git status --ignored --short --untracked-files=all`
- Working directory: repository root. Passed. `find . -path ./.git -prune -o -type f -size +10M -print`
- Working directory: repository root. Passed. `find . -path ./.git -prune -o -type d -name __pycache__ -print`
- Working directory: repository root. Passed. `find . -path ./.git -prune -o -type f \( -name '*.json' -o -name '*.log' -o -name '*.tmp' -o -name '.env' -o -name '*.pyc' -o -name '*results*.json' -o -name '*solutions*.json' \) -print`
- Working directory: repository root. Passed. `rg -n --hidden -g '!.git/**' -g '!LiteTensorDataTest/**' -g '!data/*.tar.gz' -i "(api[_-]?key|secret|token|password|private key|begin rsa|aws_access|ghp_|hf_)"`
- Working directory: repository root. Passed. `git ls-files LiteTensorDataTest | wc -l`
- Working directory: repository root. Passed. `git ls-files LiteTensorDataTest | sed -n '1,20p'`
- Working directory: repository root. Passed. `git check-ignore -v LiteTensorDataTest/config_21/litedata_1.pth iccad2026contest/my_optimizer_results.json iccad2026contest/__pycache__/my_optimizer.cpython-312.pyc`
- Working directory: repository root. Passed. `du -h iccad2026contest/my_optimizer_results.json`
- Working directory: repository root. Passed. `wc -l iccad2026contest/my_optimizer.py iccad2026contest/optimizer_*_smoke.py doc/submission-check.md`

## Command Results

- `/usr/bin/python3` is Python 3.12.3 and failed dependency import with `ModuleNotFoundError: No module named 'numpy'`.
- `python` is Python 3.12.8 at `/home/kuotzuwei15/miniconda3/envs/juicedrag/bin/python`; it imported `numpy`, `torch`, `shapely`, and `tqdm` successfully.
- All optimizer smoke scripts passed under `python`.
- `optimizer_proxy_scoring_smoke.py`, `optimizer_preflight_smoke.py`, and evaluator commands emitted a nonblocking Matplotlib warning because `/home/kuotzuwei15/.config/matplotlib` is not writable; Matplotlib used temporary cache directories under `/tmp`.
- `git diff --name-only` reported no tracked-file diffs.
- `git status --ignored --short --untracked-files=all` reports many untracked docs/smoke scripts plus ignored bytecode and `iccad2026contest/my_optimizer_results.json`.
- `find . -path ./.git -prune -o -type f -size +10M -print` found `./LiteTensorDataTest/config_120/litedata_1.pth`.
- `find` found `./__pycache__` and `./iccad2026contest/__pycache__`.
- `find` found ignored/generated files including `iccad2026contest/my_optimizer_results.json` and `*.pyc` bytecode files.
- `iccad2026contest/my_optimizer_results.json` is ignored by `.gitignore` via `*_results.json` and is `900K`.
- `LiteTensorDataTest/config_21/litedata_1.pth` is not ignored; all 200 validation `.pth` files are tracked.
- No repository-defined build, lint, format, type-check, static-analysis, CI, or unit-test runner command was discovered.

## Evaluator Results

- `python -B iccad2026_evaluate.py --validate my_optimizer.py` passed.
  - File exists: passed.
  - Python syntax: passed.
  - Module loads: passed.
  - Optimizer class discovery: passed, `MyOptimizer`.
  - Dummy `solve()` return format: passed.
  - Sample runtime: `0.002s`.
- `python -B iccad2026_evaluate.py --evaluate my_optimizer.py --test-id 0 --data-path ../ --output /tmp/my_optimizer_test0_results.json` passed.
  - Loaded 100 validation cases from `LiteTensorDataTest/`.
  - Tests: 1.
  - Feasible: 1.
  - Total score / average cost: `7.0956`.
  - Average runtime: `0.01s`.
  - Output written to `/tmp/my_optimizer_test0_results.json`.
- `python -B iccad2026_evaluate.py --evaluate my_optimizer.py --data-path ../ --output /tmp/my_optimizer_full_results.json` passed.
  - Loaded 100 validation cases from `LiteTensorDataTest/`.
  - Tests: 100.
  - Feasible: 100.
  - Total score: `7.2186417012188`.
  - Average cost: `6.795066132229184`.
  - Average runtime: `0.04638771533966064s`.
  - Minimum case cost: `3.2655647606078695`.
  - Maximum case cost: `9.999999`; the worst-cost cases are still feasible because feasible cost is capped below `10.0`.
  - Errors: 0.
  - Output written to `/tmp/my_optimizer_full_results.json`.

## Packaging Notes

- The optimizer file passed validator and full local validation against `LiteTensorDataTest/`.
- If the official final submission is a single optimizer-file upload, submit `iccad2026contest/my_optimizer.py`.
- Do not package `/tmp/my_optimizer_test0_results.json` or `/tmp/my_optimizer_full_results.json`.
- Do not package local generated `iccad2026contest/my_optimizer_results.json`.
- Do not package `__pycache__/`, `*.pyc`, logs, temporary files, virtual environments, result JSON, or solution JSON.
- Do not package `LiteTensorDataTest/` unless the final instructions explicitly require bundling validation data; it is local/test data and 256M.
- If the final submission is made from git or a tracked-only archive, `iccad2026contest/my_optimizer.py` is currently untracked and would be omitted.
- If the final submission is a whole-worktree archive, untracked planning docs, smoke scripts, and `validation_case_33.png` may be included accidentally unless excluded.

## Files to Exclude

- `__pycache__/`
- `iccad2026contest/__pycache__/`
- `*.pyc`
- `iccad2026contest/my_optimizer_results.json`
- `/tmp/my_optimizer_test0_results.json`
- `/tmp/my_optimizer_full_results.json`
- `*_results.json`
- `*_solutions.json`
- `*.log`
- `.env`
- Virtual environments such as `venv/`, `.venv/`, `env/`, and conda environment directories.
- Large/local datasets unless final packaging explicitly requires them: `LiteTensorDataTest/`, `LiteTensorData/`, `floorset_lite/`, and other downloaded datasets.
- Development-only smoke scripts `iccad2026contest/optimizer_*_smoke.py` unless tests are explicitly part of the requested package.
- Planning docs under `doc/` unless the final package is a repository deliverable rather than a contest optimizer upload.
- `iccad2026contest/validation_case_33.png` unless explicitly needed as a report artifact.

## Risks

- Final official packaging/upload rules are not fully specified in the read contest README/PDF/evaluator sources.
- `iccad2026contest/my_optimizer.py` is untracked in git. This is blocking for git-based submission or any archive built only from tracked files.
- Many development artifacts are untracked and could be accidentally included in a manual whole-repository archive.
- Ignored bytecode and ignored `iccad2026contest/my_optimizer_results.json` exist locally and should not be submitted.
- Local validation is feasible (`100/100`) but not necessarily competitive: total score is `7.2186417012188`, and some feasible cases hit the cap `9.999999`.
- Official runtime competitiveness is unknown because local evaluator uses neutral `RuntimeFactor=1.0`.
- The command `python3` in this shell is missing dependencies. Use the `python` command from the `juicedrag` conda environment for local verification unless the environment is changed.
- `MyOptimizer` passed local class-name discovery but does not visibly subclass `FloorplanOptimizer`; if official tooling differs from the local evaluator, this could be a format risk.

## Final Submission Status

Blocked / needs user decision.

All required local optimizer deliverables are accounted for, and the validator plus full 100-case evaluator passed against `LiteTensorDataTest/` with `100/100` feasible cases. It is safe to submit only if the official final submission is the single file `iccad2026contest/my_optimizer.py`.

It is not unconditionally ready for a git-based or whole-repository/archive submission until the user confirms packaging rules and decides whether to track or exclude the untracked optimizer, smoke scripts, planning docs, image artifact, generated result JSON, and caches.
