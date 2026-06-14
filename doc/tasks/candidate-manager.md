# Candidate Manager

## Goal

Retain the best hard-feasible candidate across fallback, constructive initialization, and local search while preventing infeasible states from replacing valid solutions.

## Inputs

- `doc/proposal.md`: Best feasible candidate must be kept across restarts and returned even if later search states are worse.
- `doc/high-level-design.md`: Candidate Manager module, candidate contract, and best-feasible control of final output.
- `doc/detailed-design.md`: Candidate retention invariant, tie-breaking, diagnostics, and malformed-candidate failure handling.
- `doc/test-plan.md`: Candidate Manager unit and property tests for feasible/infeasible sequences, tie-breaking, fallback retention, and search-never-loses-feasibility.

## Write Scope

Candidate records, candidate decision logic, best-feasible retention, diagnostics, and tie-breaking helpers in `iccad2026contest/my_optimizer.py`; future candidate manager fixtures in the agreed test harness.

## Read Scope

Candidate contract, Hard-Constraint Preflight Checker, Proxy Scoring, fallback candidate shape, constructive candidate shape, and local-search output shape.

## Dependencies

Hard-Constraint Preflight Checker; Proxy Scoring. Called by Optimizer Entry, Deterministic Legal Fallback, Constructive Initializer, and Local Search and Repair.

## Tasks

- [x] Define the candidate metadata needed for positions, source, hard report, soft report, proxy score, and deterministic source order.
- [x] Implement `consider` behavior that preflights every candidate before scoring or retention.
- [x] Retain the first hard-feasible fallback and replace best feasible only with a strictly better feasible proxy score under deterministic tie-breaking.
- [x] Keep hard-infeasible candidates only as diagnostics and never return them while any feasible candidate exists.
- [x] Handle proxy scoring failures for feasible candidates by assigning conservative score fields without losing feasibility.
- [x] Add fixtures for feasible-then-infeasible sequences, multiple feasible candidates with ties, malformed candidate rejection, and no-optimized-candidate fallback.

## Tests and Quality Gates

- [x] Verify an infeasible candidate with a lower raw proxy score cannot replace an existing feasible candidate.
- [x] Verify deterministic tie-breaking by proxy score, bounding-box area, HPWL, and source order.

## Done When

- [x] `best_feasible_or_fallback()` returns a hard-feasible candidate whenever one has been considered.
- [x] Candidate manager fixtures prove local search and constructive failures cannot lose fallback feasibility.
