# Proxy Scoring

## Goal

Provide deterministic online candidate ranking using evaluator-aligned HPWL, bounding-box area, soft-violation estimates, and hard-infeasibility barriers.

## Inputs

- `doc/proposal.md`: Contest-shaped proxy terms and note that official baseline gaps are unavailable inside `solve()`.
- `doc/high-level-design.md`: Proxy Scoring module, online ranking role, and non-official-score contract.
- `doc/detailed-design.md`: Proxy score fields, formula shape, empty-connectivity handling, and import-versus-duplicate helper open question.
- `doc/test-plan.md`: Hand-computed HPWL/bbox fixtures, empty connectivity fixture, hard-barrier fixture, and evaluator differential tests.

## Write Scope

HPWL, bbox, soft-violation estimate, hard barrier, aggregate proxy score, and term-breakdown helpers in `iccad2026contest/my_optimizer.py`; future proxy scoring fixtures in the agreed test harness.

## Read Scope

Parsed connectivity and pins, Candidate positions, Hard-Constraint Preflight Checker reports, evaluator helper semantics for HPWL and bbox, and soft-constraint semantics for boundary, grouping, and MIB.

## Dependencies

Input Normalization and Constraint Parser; geometry helper routines; optional soft-report helpers; Hard-Constraint Preflight Checker reports.

## Tasks

- [x] Implement evaluator-aligned B2B HPWL using weighted Manhattan distance between block centers.
- [x] Implement evaluator-aligned P2B HPWL using weighted Manhattan distance between pin coordinates and block centers.
- [x] Implement bounding-box area over all active rectangles and return zero HPWL for empty connectivity.
- [x] Estimate boundary, grouping, and MIB soft violations without allowing missing soft reports to affect hard feasibility claims.
- [x] Add a hard-infeasibility barrier so infeasible candidates cannot rank above feasible candidates in Candidate Manager.
- [x] Record initial proxy weights for HPWL, bbox area, soft violations, and hard barrier before tuning.
- [x] Add hand-computed B2B, P2B, bbox, empty-connectivity, soft-violation, and hard-barrier fixtures.

## Tests and Quality Gates

- [x] Verify proxy HPWL and bbox terms match evaluator helpers on small fixtures within tolerance.
- [x] Verify nonfinite coordinates and hard-infeasible reports produce barrier scores.

## Optimization Notes

- 2026-06-14: Proxy scoring now keeps exact no-soft scores while applying an evaluator-inspired `PROXY_SOFT_EXPONENT = 2.0` factor to soft-violating candidates. This makes normalized soft violations harder to trade away for raw HPWL or bbox gains, matching the official cost direction without requiring hidden baseline metrics.

## Done When

- [x] Candidate Manager can compare feasible candidates deterministically using proxy score and tie-break fields.
- [x] Proxy fixtures cover HPWL, bbox, soft violations, empty connectivity, and hard-infeasibility barriers.
