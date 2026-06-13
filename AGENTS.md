# AGENTS.md

## Project Context

- This repository is FloorSet, a VLSI floorplanning dataset and the basis for the ICCAD 2026 CAD Contest Problem C, "The FloorSet Challenge: Data-Driven SoC Floorplanning."
- The contest working directory is `iccad2026contest/`.
- Authoritative contest references:
  - `iccad2026contest/README.md`
  - `iccad2026contest/FloorplanningContest_ICCAD_2026_v10.pdf`
  - `iccad2026contest/iccad2026_evaluate.py`
- Primary implementation target for contestants is a Python optimizer implementing `solve()` and returning `(x, y, width, height)` tuples.
- Toolchain: Python with pip requirements. Verified requirement files are `requirements.txt` and `iccad2026contest/requirements.txt`.

## Repository Rules

- Treat contest behavior as specified by `iccad2026contest/README.md`, the v10 PDF, and `iccad2026contest/iccad2026_evaluate.py`.
- Prefer making a copied optimizer file, for example `iccad2026contest/my_optimizer.py`, instead of editing `iccad2026contest/optimizer_template.py` directly unless explicitly asked.
- Keep generated result files, logs, caches, and downloaded datasets out of commits unless the user explicitly asks to track them.
- Do not overwrite user optimizer files, saved solutions, generated reports, or local datasets without explicit permission.
- The user reports the full dataset is available on their lab server under `~/FloorSet/`:
  - training data: `floorset_lite/`, 100 `worker_*` directories, about 24 GB;
  - validation data: `LiteTensorDataTest/`, 100 `config_*` directories, about 256 MB.
- The lab-server dataset was populated using `get_training_dataloader` and `get_validation_dataloader` from `iccad2026contest/iccad2026_evaluate.py`.
- Large datasets may be present locally, mounted from the lab server, or auto-downloaded by evaluator/data loader code; ask before any command that may download, copy, or transform data.

## Read-Only Discovery Commands

These commands are safe for future agents to run without user approval:

```bash
pwd
git status --short --branch
git branch --show-current
git worktree list
rg --files
sed -n '1,220p' README.md
sed -n '1,260p' iccad2026contest/README.md
sed -n '1,220p' iccad2026contest/optimizer_template.py
sed -n '1,220p' iccad2026contest/iccad2026_evaluate.py
pdfinfo iccad2026contest/FloorplanningContest_ICCAD_2026_v10.pdf
pdftotext -layout -f 1 -l 2 iccad2026contest/FloorplanningContest_ICCAD_2026_v10.pdf -
```

## Commands Requiring Permission

Ask before running commands that create, modify, download, evaluate, train, visualize, install, or change git state, including:

```bash
pip install -r requirements.txt
pip install -r iccad2026contest/requirements.txt
cd iccad2026contest && cp optimizer_template.py my_optimizer.py
cd iccad2026contest && python iccad2026_evaluate.py --validate my_optimizer.py
cd iccad2026contest && python iccad2026_evaluate.py --evaluate my_optimizer.py
cd iccad2026contest && python iccad2026_evaluate.py --evaluate my_optimizer.py --test-id 0
cd iccad2026contest && python iccad2026_evaluate.py --evaluate my_optimizer.py --save-solutions
cd iccad2026contest && python iccad2026_evaluate.py --score my_optimizer_solutions.json
cd iccad2026contest && python iccad2026_evaluate.py --baseline
cd iccad2026contest && python iccad2026_evaluate.py --training
cd iccad2026contest && python iccad2026_evaluate.py --visualize --test-id 0
python iccad2026contest/training_example.py
```

Also ask before:

- Creating, editing, moving, deleting, or renaming files.
- Running formatters, linters, type checkers, tests, benchmarks, training jobs, or long evaluations.
- Running commands that may auto-download datasets from Hugging Face.
- Creating branches, switching branches, committing, stashing, rebasing, merging, pulling, or pushing.

## Forbidden Commands

Do not run these unless the user explicitly requests the exact action:

```bash
rm -rf
git reset --hard
git clean -fd
git checkout -- .
git restore .
git push --force
git push --force-with-lease
chmod -R
chown -R
sudo
```

## Build, Test, and Quality Gates

- Dependency installation is pip-based:

```bash
pip install -r iccad2026contest/requirements.txt
```

- Contest commands are run from `iccad2026contest/`.
- Verified evaluator modes include `--evaluate`, `--score`, `--validate`, `--baseline`, `--visualize`, `--training`, and `--info`.
- `python iccad2026_evaluate.py --info` prints contest information and does not intentionally write result files.
- `--evaluate` writes a results JSON by default and may load local validation data from `../LiteTensorDataTest/`.
- `--save-solutions`, `--score`, and `--baseline` can write JSON outputs.
- `training_example.py`, training data loaders, and validation data loaders may download datasets if data is missing.
- Automated lint, format, and type-check commands are unknown; do not invent them.
- Unit test commands are unknown; use contest validation/evaluation commands when the user approves.

## Documentation Rules

- Keep contest-facing documentation consistent with `iccad2026contest/README.md` and the v10 PDF.
- If scoring, constraints, or command behavior changes, update the contest README and code comments together.
- Mark unverified facts as unknown instead of guessing.
- Do not include secrets, tokens, private credentials, or environment-specific paths other than repository-relative paths.

## Coding Rules

- Use Python conventions already present in the repository.
- Keep optimizer experiments isolated in new files unless the user asks to modify shared contest framework files.
- Preserve hard constraint semantics from the contest framework:
  - no block overlaps;
  - soft-block area within 1% of target;
  - fixed-shape block dimensions are immutable;
  - preplaced block location and dimensions are immutable.
- Preserve soft constraint semantics for grouping, MIB, and boundary constraints.
- Avoid broad refactors of evaluator, loader, dataset, or utility code while working on a solver unless required and approved.
- Treat generated outputs and large datasets as local artifacts unless the user explicitly asks to version them.

## Git and Commit Rules

- Current branch at setup time: `main`.
- Worktree was clean at setup time.
- Do not commit, amend, branch, merge, rebase, stash, pull, or push without user approval.
- Before editing, check `git status --short --branch` and avoid overwriting unrelated user changes.
- If changes appear that were not made by the agent, preserve them and work around them.

## Uncertainty Protocol

- Unknown: preferred Python version.
- Unknown: whether a project virtual environment already exists.
- Unknown: official lint, format, type-check, and unit-test commands.
- Known from user report: the full 1M-sample training dataset is available on the user's lab server at `~/FloorSet/floorset_lite/`, with 100 `worker_*` directories and about 24 GB of data.
- Known from user report: validation data is available on the user's lab server at `~/FloorSet/LiteTensorDataTest/`, with 100 `config_*` directories and about 256 MB of data.
- Unknown: non-secret access method, mount path, or transfer workflow for the lab-server datasets from this workspace.
- Unknown: whether the full 1M-sample training dataset is available locally or mounted in this workspace.
- Unknown: final submission packaging rules beyond the contest README/PDF and evaluator validation.
- When contest documentation and code disagree, stop and ask the user which source to treat as authoritative before modifying behavior.
