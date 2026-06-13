# Problem Brief

## Source Documents

- `iccad2026contest/README.md` - read. Primary contest README, including changelog, task interface, constraints, scoring, datasets, commands, and local runtime normalization.
- `iccad2026contest/FloorplanningContest_ICCAD_2026_v10.pdf` - read. ICCAD 2026 FloorSet Challenge problem statement, 13 pages; relevant sections include Problem Statement, Inputs, Expected Output, Objective Function, Dataset, and Total Score.
- `iccad2026contest/iccad2026_evaluate.py` - read as repository implementation reference named authoritative by the user-provided repository instructions. Confirms hard and soft constraint checks, cost computation, total score weighting, data loading, optimizer loading, and validation behavior.
- `iccad2026contest/optimizer_template.py` - read as implementation interface reference. Confirms expected optimizer subclass pattern and `solve()` return shape.
- `iccad2026contest/requirements.txt` and root `requirements.txt` - read for implementation environment dependencies.
- User-provided repository instructions in the prompt - read. Provide local workflow rules, dataset availability notes, and caution that README, PDF, and evaluator are authoritative contest references.

## Assignment Objective

Implement a contestant optimizer for the ICCAD 2026 FloorSet Challenge, Problem C, "The FloorSet Challenge: Data-Driven SoC Floorplanning." The optimizer must place rectangular SoC floorplanning blocks on a 2D plane and return one `(x, y, width, height)` tuple per block. The goal is to minimize the contest cost while satisfying all hard constraints and reducing wirelength, bounding-box area, soft constraint violations, and official runtime impact.

The sources allow any effective algorithmic paradigm. The PDF motivates ML-guided optimization and data-driven methods, but explicitly frames the contest as performance-oriented rather than methodologically restrictive.

## Required Inputs

- A Python optimizer file loaded by `iccad2026_evaluate.py`.
- An optimizer class discoverable by the evaluator, normally a subclass of `FloorplanOptimizer`.
- A `solve()` method receiving contest tensors. The evaluator/template signature is:

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

- `block_count`: number of active blocks in the case.
- `area_targets`: target area per block.
- `b2b_connectivity`: weighted block-to-block connectivity edges of the form `(block_i, block_j, weight)`.
- `p2b_connectivity`: weighted pin-to-block connectivity edges of the form `(pin_idx, block_idx, weight)`.
- `pins_pos`: fixed terminal or pin coordinates.
- `constraints`: per-block tensor with columns interpreted by the evaluator as `[fixed, preplaced, mib, cluster, boundary]`.
- `target_positions`: evaluator-provided `(x, y, w, h)` targets. For fixed-shape blocks, width and height are set; for preplaced blocks, all four fields are set; otherwise fields default to `-1`.

## Required Outputs

- `solve()` must return a Python list with exactly `block_count` entries.
- Each entry must be a tuple or tuple-like value `(x, y, width, height)`.
- Coordinates are floating point values; integer coordinates are not required.
- Any aspect ratio is allowed for soft blocks, provided area tolerance is met.
- The returned rectangle for block `i` occupies `[x_i, x_i + w_i] x [y_i, y_i + h_i]`.
- Saved JSON solution output is supported by `--save-solutions`, but the primary contestant implementation target is the optimizer Python file.

## Constraints

- Hard constraints. Any violation makes the test case infeasible and gives cost `M = 10.0`:
  - No overlaps between any pair of blocks. Touching edges is allowed.
  - Soft-block area must satisfy `abs(w_i * h_i - a_i) / a_i <= 0.01`.
  - Fixed-shape block dimensions must exactly match evaluator-provided target width and height, within evaluator tolerance.
  - Preplaced blocks must exactly match evaluator-provided target `x`, `y`, `width`, and `height`, within evaluator tolerance.
- Soft constraints. Violations do not make a solution infeasible, but increase cost through `exp(beta * V_rel)`:
  - Grouping or cluster constraints: blocks in each group should abut and form one connected component through shared edges.
  - MIB constraints: blocks in each group should have identical dimensions.
  - Boundary constraints: constrained blocks should touch specified bounding-box edge or corner.
- Boundary constraint encoding in `constraints[:, 4]` is a bitmask:
  - `1`: left edge.
  - `2`: right edge.
  - `4`: top edge.
  - `8`: bottom edge.
  - Corners are represented by sums, such as `5` for top-left and `10` for bottom-right.
- Relaxed contest constraints:
  - Aspect ratio is not constrained.
  - Fixed outline is removed for contest scoring; compactness is optimized through bounding-box area and pin-to-block HPWL.
  - Floating-point coordinates are allowed.
- The sources state that submissions found to be reverse-engineering the dataset generator rather than developing genuine algorithmic solutions are disqualified.

## Evaluation or Grading Criteria

- Per-case feasible cost:

```text
Cost = (1 + 0.5 * (HPWL_gap + Area_gap)) * exp(2 * V_rel) * max(0.7, RuntimeFactor^0.3)
```

- Infeasible case cost is exactly `10.0`.
- Feasible costs are capped at `9.999999`, so any feasible solution scores strictly better than any infeasible solution.
- `HPWL_gap` is the relative gap between achieved total HPWL and the baseline HPWL.
- Total HPWL is the sum of weighted block-to-block centroid Manhattan distance and weighted pin-to-block Manhattan distance.
- `Area_gap` is the relative gap between achieved bounding-box area and baseline bounding-box area.
- The evaluator clamps negative HPWL and area gaps to zero in the quality factor, so beating the baseline gives no additional local score bonus.
- `V_rel = (V_boundary + V_grouping + V_mib) / N_soft`, where `N_soft = |B_boundary| + sum(|G_p| - 1) + sum(|M_q| - 1)`.
- `RuntimeFactor` is your runtime divided by the per-test-case median runtime of all submissions; lower is faster and better. Local evaluation sets `RuntimeFactor = 1.0` for all validation cases because cross-submission medians are unavailable.
- Final Total Score is an exponentially weighted average across 100 cases:

```text
Total Score = sum_i Cost[i] * exp(n_i / 12) / sum_j exp(n_j / 12)
```

- Larger block-count cases receive more weight. The README states that cases with 116 to 120 blocks account for about 34% of total score.
- Lower score is better. A perfect-quality solution at median runtime has Total Score about `1.0`; the speed-bonus floor can make the theoretical minimum about `0.70`.

## Required Deliverables

- A Python optimizer file, typically copied from `iccad2026contest/optimizer_template.py` into a contestant-owned file such as `iccad2026contest/my_optimizer.py`.
- An implemented optimizer class and `solve()` method that the evaluator can import and execute.
- Before submission, the README recommends validating with:

```bash
cd iccad2026contest
python iccad2026_evaluate.py --validate my_optimizer.py
```

- Local scoring and debugging are supported with:

```bash
cd iccad2026contest
python iccad2026_evaluate.py --evaluate my_optimizer.py
python iccad2026_evaluate.py --evaluate my_optimizer.py --test-id 0
```

- Official final upload or packaging instructions beyond repository validation are not fully specified in the read sources.

## Relevant Methods From Papers

- No method is required by the sources.
- The PDF motivates ML-guided optimization, data-driven methods, and hybrid approaches as promising for reducing floorplanning time from manual multi-day iteration toward automated minute-scale or sub-minute cycles.
- The PDF also allows stochastic, data-driven, or hybrid algorithmic paradigms.
- The provided training utilities include differentiable proxy losses for ML training, but the README and evaluator warn that training losses are approximations and do not include all final evaluation constraints.

## Data, Benchmarks, or Test Cases

- Training data: FloorSet-Lite training set, 1M samples, block counts from 21 to 120, available through Hugging Face and through `get_training_dataloader()`.
- Validation data: 100 samples, one per size from 21 to 120 blocks, available as `LiteTensorDataTest/` and through `get_validation_dataloader()`.
- Hidden test data: 100 samples, same format and same block range, used for final contest ranking.
- Baseline values for HPWL and bounding-box area are provided in the dataset and used to compute gap metrics.
- The repository currently contains local `LiteTensorDataTest/config_*` files discovered by `rg --files`; this supports local validation/evaluation if dependencies are installed.
- The user-provided repository instructions report that a fuller training dataset and validation dataset may also exist on the user's lab server under `~/FloorSet/`, but the access path from this workspace is unknown.
- Data loader functions may auto-download datasets from Hugging Face if local data is missing.

## Implementation Environment

- Language: Python.
- Package installation is pip-based.
- `iccad2026contest/requirements.txt` lists:
  - `torch>=2.0.0`
  - `numpy>=1.24.0`
  - `shapely>=2.0.0`
  - `matplotlib>=3.7.0`
  - `tqdm>=4.60.0`
  - `requests>=2.28.0`
- The root `requirements.txt` also lists PyTorch, NumPy, Shapely, Matplotlib, tqdm, and Requests versions.
- Contest commands are documented as running from `iccad2026contest/`.
- Validation data is expected at the repository root parent path used by the evaluator default `data_path="../"`.
- The evaluator imports repository modules from the parent directory and uses PyTorch tensors, NumPy, tqdm, and Shapely for geometric checks.

## Confirmed Facts

- FloorSet is the basis for ICCAD 2026 CAD Contest Problem C.
- The contest target is a Python optimizer implementing `solve()`.
- The output must contain one `(x, y, width, height)` tuple per block.
- The block-count range for train, validation, and test cases is 21 to 120.
- Validation has 100 cases and hidden final test has 100 cases.
- Hard constraints include overlap-free placement, soft-block area tolerance, fixed-shape dimension immutability, and preplaced position/dimension immutability.
- Soft constraints include boundary, grouping, and MIB constraints.
- The v10 README and evaluator use exponential total-score weighting with `exp(n / 12)`.
- Local runtime scoring is neutralized in the evaluator by setting `RuntimeFactor = 1.0`.
- The evaluator can validate optimizer format and evaluate either all validation cases or a single `--test-id`.
- Training helper losses are proxies and are not identical to final evaluation.

## Assumptions

- The intended immediate next artifact is a proposal or design document generated from this problem brief.
- A contestant optimizer file should be created separately from `optimizer_template.py`, following the repository instruction preference to avoid editing the template directly.
- The official hidden test format matches validation format as stated in the README and PDF.
- Local validation data found in the workspace can be used for evaluation only after the user approves commands that may write result files or run long evaluations.

## Open Questions

- The official final submission upload format and packaging process are not fully specified in the read README/PDF beyond the optimizer file interface and validation command.
- Preferred Python version and virtual environment location are unknown.
- It is unknown whether dependencies are already installed in this workspace.
- It is unknown whether the full 1M-sample training dataset is locally mounted in this workspace; the user reported lab-server availability, but access details are not specified.
- The README, PDF, and evaluator should remain the authority for contest behavior. If future proposal or implementation work finds a direct disagreement between documentation and evaluator behavior, the user should choose which source to follow before changing shared contest code.

## Notes for Proposal Generation

- Start from the confirmed optimizer interface, hard constraints, soft constraints, and scoring formula.
- Preserve the distinction between official scoring and local validation scoring, especially runtime normalization.
- Treat feasibility as the first-order requirement because any hard constraint violation costs `10.0`, while any feasible solution is capped below that.
- Do not assume an ML-only solution; the sources allow stochastic, data-driven, and hybrid approaches.
- Do not design around reverse-engineering the dataset generator.
- Keep experiments isolated in a copied optimizer file such as `iccad2026contest/my_optimizer.py`.
- Ask or verify before running commands that may download data, write outputs, run long evaluations, install dependencies, or modify git state.
