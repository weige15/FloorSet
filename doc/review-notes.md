# Review Notes

## Review Scope

- Fresh-context review of `doc/tasks/progress.md` against `doc/tasks/hard-constraint-preflight-checker.md`.
- Scope covered the Hard-Constraint Preflight Checker behavior in `iccad2026contest/my_optimizer.py`, focused differential smoke coverage in `iccad2026contest/optimizer_preflight_smoke.py`, and Candidate Manager/final-return integration that uses preflight reports.
- Broader solver modules were reviewed only where they feed expected areas, immutable geometry, dimensions, or candidate retention into preflight.

## Files Reviewed

- `doc/problem-brief.md`
- `doc/proposal.md`
- `doc/high-level-design.md`
- `doc/test-plan.md`
- `doc/detailed-design.md`
- `doc/tasks/progress.md`
- `doc/tasks/hard-constraint-preflight-checker.md`
- `doc/review-notes.md`
- `iccad2026contest/iccad2026_evaluate.py`
- `iccad2026contest/my_optimizer.py`
- `iccad2026contest/optimizer_preflight_smoke.py`

## Commands Run

- `sed -n '1,260p' /home/kuotzuwei15/.codex/skills/review-and-repair/SKILL.md` - pass; reviewed the required skill workflow.
- `pwd` - pass; confirmed workspace `/home/kuotzuwei15/pda/FloorSet`.
- `git status --short --branch` - pass; branch `main...origin/main`; reviewed docs/source/smoke files are untracked.
- `rg --files doc iccad2026contest | sort` - pass; discovered required docs, task files, optimizer file, evaluator, and smoke files.
- `git diff --stat` - pass; no output because reviewed implementation files are untracked.
- `git diff --cached --stat` - pass; no staged changes.
- `wc -l doc/problem-brief.md doc/proposal.md doc/high-level-design.md doc/test-plan.md doc/detailed-design.md doc/tasks/progress.md doc/tasks/hard-constraint-preflight-checker.md doc/review-notes.md iccad2026contest/my_optimizer.py iccad2026contest/optimizer_preflight_smoke.py` - pass; recorded line counts for required review inputs.
- `sed -n '1,260p' doc/problem-brief.md` - pass; reviewed contest requirements.
- `sed -n '1,280p' doc/proposal.md` - pass; reviewed feasibility-first and preflight intent.
- `sed -n '1,280p' doc/high-level-design.md` - pass; reviewed module boundaries.
- `sed -n '1,320p' doc/test-plan.md` - pass; reviewed preflight test expectations.
- `sed -n '1,140p' doc/detailed-design.md`, `sed -n '141,340p' doc/detailed-design.md`, `sed -n '341,620p' doc/detailed-design.md`, `sed -n '621,900p' doc/detailed-design.md`, and `sed -n '901,1265p' doc/detailed-design.md` - pass; reviewed the full detailed design.
- `sed -n '1,120p' doc/tasks/progress.md` - pass; reviewed task status and checkpoint claims.
- `sed -n '1,120p' doc/tasks/hard-constraint-preflight-checker.md` - pass; reviewed scoped checklist.
- `sed -n '1,220p' doc/review-notes.md` - pass; reviewed prior notes before replacing them for this scope.
- `rg -n "preflight|Preflight|overlap|area_violations|dimension_violations|hard_feasible|malformed|check_overlap|check_area_tolerance|check_dimension_hard_constraints|IMMUTABLE|AREA|OVERLAP|TOL" iccad2026contest/my_optimizer.py` - pass; located preflight implementation and related report fields.
- `rg -n "def check_overlap|def check_area_tolerance|def check_dimension_hard_constraints|overlap_width|overlap_height|1e-6|0.01|1e-4|fixed|preplaced" iccad2026contest/iccad2026_evaluate.py` - pass; located evaluator hard-check semantics.
- `sed -n '1,340p' iccad2026contest/optimizer_preflight_smoke.py` - pass; reviewed focused smoke fixtures.
- `sed -n '1,260p' iccad2026contest/my_optimizer.py`, `sed -n '260,520p' iccad2026contest/my_optimizer.py`, `sed -n '520,720p' iccad2026contest/my_optimizer.py`, `sed -n '720,980p' iccad2026contest/my_optimizer.py`, `sed -n '980,1260p' iccad2026contest/my_optimizer.py`, `sed -n '1260,1580p' iccad2026contest/my_optimizer.py`, and `sed -n '1980,2095p' iccad2026contest/my_optimizer.py` - pass; reviewed source context, preflight, Candidate Manager, construction/search preflight calls, and final return.
- `sed -n '200,320p' iccad2026contest/iccad2026_evaluate.py`, `sed -n '370,410p' iccad2026contest/iccad2026_evaluate.py`, and `sed -n '410,570p' iccad2026contest/iccad2026_evaluate.py` - pass; reviewed evaluator hard and soft violation computation.
- `rg -n "def _finalize_positions|def _emergency_positions|best_feasible_or_fallback|_finalize_positions" iccad2026contest/my_optimizer.py` - pass; located finalization path.
- `nl -ba iccad2026contest/my_optimizer.py | sed -n '600,690p'` - pass; captured preflight line references.
- `nl -ba iccad2026contest/my_optimizer.py | sed -n '860,925p'` - pass; captured Candidate Manager line references.
- `nl -ba iccad2026contest/my_optimizer.py | sed -n '1970,2070p'` - pass; captured final-return line references.
- `nl -ba iccad2026contest/optimizer_preflight_smoke.py | sed -n '1,300p'` - pass; captured smoke-test line references.
- `nl -ba doc/tasks/progress.md | sed -n '1,80p'` - pass; captured progress line references.
- `nl -ba doc/tasks/hard-constraint-preflight-checker.md | sed -n '1,90p'` - pass; captured task line references.
- `nl -ba iccad2026contest/iccad2026_evaluate.py | sed -n '210,320p'` and `nl -ba iccad2026contest/iccad2026_evaluate.py | sed -n '370,410p'` - pass; captured evaluator hard-check line references.
- `python -B iccad2026contest/optimizer_preflight_smoke.py` - pass; printed `optimizer-preflight smoke passed`. It also printed the known Matplotlib temporary-cache warning because `/home/kuotzuwei15/.config/matplotlib` is not writable and a `/tmp` cache was used.
- `find iccad2026contest -maxdepth 2 -type d -name __pycache__ -o -name '*.pyc'` - pass; confirmed existing ignored Python cache artifacts are present after smoke execution.
- `cd iccad2026contest && python -B iccad2026_evaluate.py --validate my_optimizer.py --quick` - skipped; evaluator command requires explicit approval under repository rules.
- `cd iccad2026contest && python -B iccad2026_evaluate.py --validate my_optimizer.py` - skipped; evaluator command requires explicit approval under repository rules.
- `cd iccad2026contest && python -B iccad2026_evaluate.py --evaluate my_optimizer.py --test-id 0` - skipped; evaluation can write results and access validation data, so it requires explicit approval.
- `apply_patch` update to `doc/review-notes.md` - pass; replaced the prior review scope with this hard-preflight review.
- `test -f doc/review-notes.md` - pass; confirmed review notes exist after update.
- `rg -n "^(# Review Notes|## Review Scope|## Files Reviewed|## Commands Run|## Summary|## Requirement Match|## Module Boundary Check|## Test Coverage Check|## Edge Cases|## Performance Concerns|## Bugs Found|## Repairs Made|## Remaining Issues|## Recommended Next Steps|## Final Readiness)$" doc/review-notes.md` - pass; confirmed every required top-level section is present.
- `rg -n '\`fixed\`|\`unresolved\`|\`needs-user-decision\`|Ready with caveats|skipped|pass|fail' doc/review-notes.md` - pass; confirmed issue categories, skipped commands, command result visibility, and readiness status.
- `sed -n '1,180p' doc/review-notes.md` - pass; reviewed updated notes.
- `git status --short --branch` - pass after review-notes update; scoped files remain untracked local changes.

## Summary

- Hard-Constraint Preflight Checker matches the scoped task for normal contest-shaped inputs: it validates candidate length, finite positive geometry, pairwise overlap tolerance, soft-block area tolerance, fixed/preplaced area skips, immutable fixed dimensions, exact preplaced rectangles, and evaluator-aligned soft diagnostic fields.
- Candidate Manager calls preflight for every considered candidate before retention, and final `solve()` returns the manager-selected best feasible candidate or fallback/diagnostic candidate.
- The focused preflight smoke passed in this review.
- No source-code repair was needed.

## Requirement Match

- `iccad2026contest/my_optimizer.py:612` through `iccad2026contest/my_optimizer.py:689` implements `_preflight()` with candidate length checks, malformed rectangle handling, `1e-6` overlap tolerance, `0.01` soft-block area tolerance, fixed/preplaced area skips, `1e-4` immutable geometry checks, hard-feasibility verdict, and soft diagnostic report fields.
- `iccad2026contest/iccad2026_evaluate.py:210` through `iccad2026contest/iccad2026_evaluate.py:303` defines the evaluator hard-check helpers mirrored by the local preflight implementation.
- `iccad2026contest/iccad2026_evaluate.py:374` through `iccad2026contest/iccad2026_evaluate.py:397` confirms the hard-feasibility conjunction: no overlaps, no soft-area violations, and no dimension/preplaced violations.
- `iccad2026contest/my_optimizer.py:880` through `iccad2026contest/my_optimizer.py:904` preflights and scores every Candidate Manager input before feasible retention or infeasible diagnostics.
- `iccad2026contest/my_optimizer.py:2061` through `iccad2026contest/my_optimizer.py:2064` returns the manager-selected candidate after the preflight-gated path.
- `doc/tasks/progress.md:15` and `doc/tasks/progress.md:40` are supported by the reviewed implementation and passing focused smoke.
- `doc/tasks/hard-constraint-preflight-checker.md:28` through `doc/tasks/hard-constraint-preflight-checker.md:44` are satisfied for the reviewed scope.

## Module Boundary Check

- Preflight is implemented inside `iccad2026contest/my_optimizer.py`, consistent with the single-file optimizer design.
- The module consumes parsed inputs, immutable geometry, and dimension-plan diagnostics; it does not pack layouts, optimize score, write files, load datasets, or call evaluator CLI commands.
- Candidate Manager owns candidate retention. Preflight only reports feasibility and diagnostics, which matches the HLD/detailed-design boundary.
- Soft-constraint fields are included as diagnostics/proxy inputs while hard feasibility remains controlled only by malformed geometry, overlap, soft-block area, and immutable-geometry counts.

## Test Coverage Check

- `iccad2026contest/optimizer_preflight_smoke.py:117` through `iccad2026contest/optimizer_preflight_smoke.py:130` covers edge-touching and overlap tolerance parity with evaluator helpers.
- `iccad2026contest/optimizer_preflight_smoke.py:133` through `iccad2026contest/optimizer_preflight_smoke.py:137` covers positive overlap.
- `iccad2026contest/optimizer_preflight_smoke.py:140` through `iccad2026contest/optimizer_preflight_smoke.py:148` covers the 1% area-tolerance boundary.
- `iccad2026contest/optimizer_preflight_smoke.py:151` through `iccad2026contest/optimizer_preflight_smoke.py:195` covers fixed-shape dimensions and preplaced position/dimensions against evaluator helper counts.
- `iccad2026contest/optimizer_preflight_smoke.py:198` through `iccad2026contest/optimizer_preflight_smoke.py:210` covers malformed candidate rejection without throwing.
- `iccad2026contest/optimizer_preflight_smoke.py:213` through `iccad2026contest/optimizer_preflight_smoke.py:252` covers randomized differential checks against evaluator helpers.
- Focused smoke execution passed in this review. Contest evaluator quick/full validation and single-case evaluation remain unrun.

## Edge Cases

- Covered: exact edge-touching, overlap below and above `1e-6`, positive overlap, area error at and above `0.01`, fixed-shape tolerance, preplaced coordinate tolerance, short candidates, `None` rectangle entries, NaN coordinates, negative dimensions, and randomized fixed/preplaced/overlap/area combinations.
- Covered through source review: candidate length mismatch, fixed/preplaced exclusion from soft-block area checks, immutable invalid-target diagnostics, and final fallback/diagnostic return when no feasible candidate exists.
- Not covered by this focused review: official validation data cases, evaluator scoring output, malformed contest inputs with missing immutable targets, and full end-to-end validation under `iccad2026_evaluate.py`.

## Performance Concerns

- No hard-preflight performance issue was found in the scoped code. Pairwise overlap checking is `O(n^2)`, which is acceptable for the documented contest range of up to 120 blocks.
- `unresolved`: Full end-to-end evaluator timing remains unchecked because evaluator commands were not run in this review.

## Bugs Found

- No `fixed`, `unresolved`, or `needs-user-decision` hard-preflight implementation bugs were found in the scoped review.

## Repairs Made

- No source-code repairs were made.
- No `doc/tasks/progress.md` checklist changes were made because the Hard-Constraint Preflight Checker status is supported by implementation evidence and a passing focused smoke.
- Updated this `doc/review-notes.md` file for the requested Hard-Constraint Preflight Checker review scope.

## Remaining Issues

- `needs-user-decision`: Run `cd iccad2026contest && python -B iccad2026_evaluate.py --validate my_optimizer.py --quick` only after explicit approval for evaluator commands.
- `needs-user-decision`: Run `cd iccad2026contest && python -B iccad2026_evaluate.py --validate my_optimizer.py` only after explicit approval for evaluator commands.
- `needs-user-decision`: Run `cd iccad2026contest && python -B iccad2026_evaluate.py --evaluate my_optimizer.py --test-id 0` only after approval because evaluation can write results and access validation data.
- `unresolved`: Full-project gates in `doc/tasks/progress.md:20` through `doc/tasks/progress.md:25` remain unchecked; this review did not run full validation/evaluation, lint, format, type, build, or static-analysis gates.
- `unresolved`: End-to-end final returned layouts were not checked against official validation data in this review.

## Recommended Next Steps

- Approve evaluator quick/full validation when ready to refresh contest-facing evidence.
- Approve a single-case evaluator run with an explicit output plan when ready to measure feasibility and runtime on validation data.
- Keep full-project gates unchecked until corresponding commands are actually run or confirmed unavailable.

## Final Readiness

- Ready with caveats.
- The Hard-Constraint Preflight Checker task is ready by scoped review and focused smoke check, but contest evaluator validation, validation-data feasibility, and full-project gates remain outstanding.
