# Optional ML Initializer

## Goal

Optionally provide advisory learned seed data for constructive initialization only after training-data access, model artifacts, and final packaging rules are approved.

## Inputs

- `doc/proposal.md`: ML-guided initializer is optional, advisory, and never the correctness path.
- `doc/high-level-design.md`: Optional ML Initializer module, seed-only contract, and unresolved packaging questions.
- `doc/detailed-design.md`: Optional ML responsibility, dependencies, failure handling, and open questions about model weights and data access.
- `doc/test-plan.md`: Optional ML tests are missing until packaging is resolved; required checks are missing artifact fallback, invalid prediction rejection, and hard-preflight enforcement.

## Write Scope

No initial correctness-critical write scope. If approved later: optional ML seed-loading, feature normalization, prediction validation, and seed handoff helpers in `iccad2026contest/my_optimizer.py`; optional artifact paths only if final packaging rules allow them.

## Read Scope

Input Normalization and Constraint Parser, Constructive Initializer seed interface, Candidate Manager, Hard-Constraint Preflight Checker, final contest packaging rules when available, and approved training-data workflow when available.

## Dependencies

Input Normalization and Constraint Parser; Constraint-Aware Constructive Initializer; Candidate Manager; Hard-Constraint Preflight Checker. External model artifacts and PyTorch are unresolved and optional.

## Tasks

- [ ] Leave ML disabled by default until final submission packaging, model-weight limits, and approved data access are known.
- [ ] Define an advisory `MLSeed` shape only after constructive initializer seed inputs are stable.
- [ ] If approved, implement missing-artifact and model-load failures as silent fallback to heuristic construction.
- [ ] If approved, validate prediction shape, finite values, block ordering, and seed dimensions before passing any ML output to constructive initialization.
- [ ] Ensure every ML seed passes through dimension planning, legalization, Candidate Manager, and hard preflight before it can affect final output.
- [ ] Add fixtures for missing artifact fallback, invalid prediction rejection, and ML seed inability to bypass preflight.

## Tests and Quality Gates

- [ ] Verify no baseline solver path requires training data, downloads, generated artifacts, model weights, or external services.
- [ ] If ML is approved later, verify missing or invalid ML artifacts fall back to the heuristic path and never block `solve()`.

## Done When

- [ ] The initial optimizer remains correct with ML absent.
- [ ] Any future ML initializer is advisory only and cannot bypass legalization or hard preflight.
