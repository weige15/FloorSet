# Repository Map

## Repository Summary

- FloorSet is a Python repository for VLSI floorplanning datasets and utilities.
- The repository also contains the ICCAD 2026 CAD Contest Problem C framework under `iccad2026contest/`.
- The primary contest implementation target is an optimizer Python file that defines a class with `solve()` returning `(x, y, width, height)` tuples.
- The contest behavior is documented in `iccad2026contest/README.md`, `iccad2026contest/FloorplanningContest_ICCAD_2026_v10.pdf`, and implemented in `iccad2026contest/iccad2026_evaluate.py`.
- Local validation data is present in `LiteTensorDataTest/` with `config_21` through `config_120` directories discovered.
- This map was created from read-only inspection of repository files and command output. No dependency installation, evaluation, training, visualization, or dataset download was run.

## Directory Structure

- `iccad2026contest/`: contest-specific framework, requirements, template optimizer, training example, and v10 problem PDF.
- `LiteTensorDataTest/`: local FloorSet-Lite validation/test tensor files. Discovered directories include `config_21` through `config_120`, each containing `.pth` data and label files.
- `data/`: contains `PrimeTensorDataTest.tar.gz`.
- `images/`: dataset and README images, histograms, layout examples, and GIFs.
- `inteltest_layouts/`: 100 Intel test layout PNG images plus a local README.
- `notebooks/`: contains `testLoader.ipynb`, `primeLoader.ipynb`, and `liteLoader.ipynb`.
- `.ipynb_checkpoints/`: Jupyter checkpoint files for loaders, datasets, utilities, validation, visualization, and notebooks.
- `doc/`: documentation workspace. `doc/problem-brief.md` existed before this map; `doc/repo-map.md` is this generated reconnaissance artifact.
- `.agents/` and `.codex/`: local agent-related directories discovered by directory listing. They were not inspected as project source.
- `.git/`: Git repository metadata.

## Main Source Files

- `iccad2026contest/iccad2026_evaluate.py`: main contest framework. It defines scoring data classes, HPWL and bounding-box helpers, hard and soft constraint checks, `FloorplanOptimizer`, baseline optimizers, `ContestEvaluator`, submission validation, baseline generation, training losses, dataloader helpers, visualization, saved-solution scoring, contest info printing, and the CLI `main()`.
- `iccad2026contest/optimizer_template.py`: contestant template and B*-tree simulated annealing baseline. Defines `BStarTree` and `MyOptimizer(FloorplanOptimizer)`.
- `iccad2026contest/training_example.py`: executable example showing use of `get_training_dataloader()` and `compute_training_loss_differentiable()`.
- `lite_dataset.py`: FloorSet-Lite training dataset class, Hugging Face download helper, dataset presence check, and collate function for padded tensors.
- `lite_dataset_test.py`: FloorSet-Lite test/validation dataset class, download helper, dataset presence check, polygon padding, and collate function.
- `prime_dataset.py`: FloorSet-Prime training dataset class, download helper, dataset presence check, polygon padding, and collate function.
- `prime_dataset_test.py`: FloorSet-Prime test dataset class, download helper, dataset presence check, polygon padding, and collate function.
- `liteLoader.py`, `litetestLoader.py`, `primeLoader.py`, `primetestLoader.py`: example loader scripts with `main()` functions that construct DataLoaders, print tensor shapes, and visualize one sample.
- `cost.py`: weighted block-to-block and pin-to-block wirelength helpers plus `estimate_cost()` for polygon solutions.
- `utils.py`: tensor unpadding, tolerance difference, polygon normalization, shape comparison, and fixed/preplaced/MIB/cluster/boundary constraint checks.
- `visualize.py`: visualization helpers for Lite and Prime layouts, constraint coloring, connectivity drawing, and placement visualization.
- `validate.py`: script-style validation example that loads `FloorplanDataset`, estimates cost for one Prime batch/sample, and prints results.

## Existing Tests

- No conventional unit-test directory or test runner configuration was discovered.
- `prime_dataset_test.py` and `lite_dataset_test.py` are dataset loader modules for test datasets, not unit test files in the usual test-runner sense.
- Contest validation is implemented by `validate_submission()` in `iccad2026contest/iccad2026_evaluate.py` and exposed through `python iccad2026_evaluate.py --validate OPTIMIZER`.
- Local contest evaluation is exposed through `python iccad2026_evaluate.py --evaluate OPTIMIZER`, but this writes result JSON by default and was not run during reconnaissance.

## Build System

- The repository is Python-based and pip-oriented.
- Root dependency file: `requirements.txt`.
- Contest dependency file: `iccad2026contest/requirements.txt`.
- No `pyproject.toml`, `setup.py`, `setup.cfg`, `tox.ini`, `noxfile.py`, `Makefile`, `package.json`, `Cargo.toml`, `go.mod`, or Java/Kotlin build files were discovered by `rg --files`.
- Automated lint, format, type-check, and unit-test commands were not discovered.

## Runtime or CLI Entry Points

- Main contest CLI: `iccad2026contest/iccad2026_evaluate.py`.
- Documented contest CLI modes:
  - `--evaluate OPTIMIZER`
  - `--score SOLUTIONS_JSON`
  - `--validate OPTIMIZER`
  - `--baseline`
  - `--visualize`
  - `--training`
  - `--info`
- Common contest CLI options include `--data-path`, `--output`, `--test-id`, `--verbose`, `--quick`, and `--save-solutions`.
- Contest commands are documented as running from `iccad2026contest/`.
- Training example entry point: `python iccad2026contest/training_example.py`.
- Loader example entry points: `python liteLoader.py`, `python litetestLoader.py`, `python primeLoader.py`, and `python primetestLoader.py`.
- `validate.py` is also executable as a script-style example, but it runs code at import time rather than through a guarded `main()`.

## Data and Assets

- `LiteTensorDataTest/` is present locally and contains discovered `config_*` directories from `config_21` through `config_120` with `litedata_1.pth` and `litelabel_1.pth` style files.
- `data/PrimeTensorDataTest.tar.gz` is present.
- `images/` contains dataset flow images, Prime/Lite layout examples, histograms, and GIFs referenced by the root README.
- `inteltest_layouts/` contains `intel_p1.png` through `intel_p100.png`, `test_layouts_noconst.gif`, and a README describing layout images for 100 validation test cases.
- `notebooks/` contains loader notebooks for test, Prime, and Lite data.
- The training data directory `floorset_lite/` or `LiteTensorData/` was not discovered by `rg --files` or the shallow directory listing in this workspace.
- Dataset loader code can download archives from Hugging Face if expected local data is missing; no download command was run.

## Existing Documentation

- `README.md`: top-level FloorSet dataset README with ICCAD contest pointers, dataset overview, format, Intel test dataset notes, citation, license, and contact.
- `iccad2026contest/README.md`: authoritative contest guide with changelog, dataset terminology, constraints, downloads, getting started, optimizer task, training data, final evaluation, saving/re-scoring, scoring, runtime normalization, and command reference.
- `iccad2026contest/FloorplanningContest_ICCAD_2026_v10.pdf`: contest problem statement PDF.
- `intel_testsuite.md` and `intel_testsuite_lite.md`: Intel test-suite metric documentation files discovered at repository root.
- `inteltest_layouts/README.md`: describes the layout-image directory and references Intel test metrics and data loader assets.
- `doc/problem-brief.md`: existing problem brief summarizing contest sources, objective, inputs, outputs, constraints, scoring, data, environment, confirmed facts, assumptions, and open questions.
- `AGENTS.md`: untracked repository guidance file with project context, command rules, coding rules, and uncertainty protocol.

## Detected Dependencies

- Root `requirements.txt` lists `matplotlib==3.9.0`, `numpy>=1.24.0`, `Requests==2.32.4`, `Shapely==2.0.5`, `torch>=2.0.0`, and `tqdm==4.66.4`.
- `iccad2026contest/requirements.txt` lists `torch>=2.0.0`, `numpy>=1.24.0`, `shapely>=2.0.0`, `matplotlib>=3.7.0`, `tqdm>=4.60.0`, and `requests>=2.28.0`.
- Python imports observed include `argparse`, `copy`, `dataclasses`, `datetime`, `glob`, `importlib.util`, `itertools`, `json`, `math`, `os`, `pathlib`, `random`, `sys`, `tarfile`, `time`, `typing`, `urllib.request`, `matplotlib`, `numpy`, `requests`, `shapely`, `torch`, and `tqdm`.

## Important Scripts

- `iccad2026contest/iccad2026_evaluate.py`: official local evaluation, validation, scoring, baseline generation, training exploration, visualization, and info CLI.
- `iccad2026contest/optimizer_template.py`: template to copy for contestant optimizer implementation.
- `iccad2026contest/training_example.py`: differentiable training-loss example.
- `liteLoader.py` and `primeLoader.py`: training dataset loader examples.
- `litetestLoader.py` and `primetestLoader.py`: test/validation dataset loader examples.
- `validate.py`: example cost-estimation script for Prime data.
- `visualize.py`: plotting helper module used by loader scripts and dataset visualization paths.

## Current Git State

- Repository path: `/home/kuotzuwei15/pda/FloorSet`.
- Branch status at reconnaissance start: `main` tracking `origin/main`.
- `git status --short --branch` reported untracked `AGENTS.md` and untracked `doc/`.
- `doc/problem-brief.md` was present inside the untracked `doc/` directory before this map was written.
- This generated `doc/repo-map.md` is an approved new documentation artifact.

## Missing or Ambiguous Areas

- Preferred Python version was not discovered.
- Existing virtual environment location was not discovered.
- Official lint, format, type-check, and unit-test commands were not discovered.
- No conventional unit tests were discovered.
- Final submission packaging rules beyond the contest README/PDF/evaluator validation were not discovered.
- The full 1M-sample training dataset was not discovered locally during shallow inspection; local or lab-server availability and access path remain unknown from repository files.
- Some dataset loader code may auto-download data if local directories are absent; future commands that instantiate those loaders should be treated as potentially downloading data.
- The local `inteltest_layouts/README.md` references `testdataloader.py`, but no `testdataloader.py` was discovered by `rg --files`.
- `validate.py` imports `FloorplanDataset` from `prime_dataset`, while the inspected `prime_dataset.py` defines `FloorplanDatasetPrime`; this mismatch was observed but not tested.

## Notes for Future Skills

- For contest behavior, use `iccad2026contest/README.md`, `iccad2026contest/FloorplanningContest_ICCAD_2026_v10.pdf`, and `iccad2026contest/iccad2026_evaluate.py` as the key references.
- Keep optimizer experiments isolated in a copied optimizer file such as `iccad2026contest/my_optimizer.py` unless the user explicitly requests shared framework changes.
- Ask before running commands that install dependencies, download datasets, train, evaluate, visualize, write result files, or change Git state.
- Feasibility is the first implementation priority: no overlaps, soft-block area within 1%, exact fixed-shape dimensions, and exact preplaced position/dimensions.
- Soft constraints in the contest evaluator are boundary, grouping, and MIB; fixed-shape and preplaced constraints are hard constraints.
- Local evaluation writes result JSON by default. Use user approval and choose output paths deliberately.
