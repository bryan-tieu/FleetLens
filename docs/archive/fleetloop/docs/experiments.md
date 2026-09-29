> Archived FleetLoop reference. Commands, implementation claims, and agent rules here are historical, not active FleetLens instructions. See [migration context](../../../migration.md). Links have been relocated; source code remains in the original repository.

# Experiment and evidence contract

An implementation check asks whether a required behavior holds. An experiment asks whether a policy or design performs better under stated conditions. Keep them separate; a negative experimental result can be a successful investigation.

## Before running

Write the question, dataset/snapshot, population, hypothesis, comparator, budgets, primary measure, slice definitions, exclusions, seed plan, and protocol version. Fix thresholds/tolerances from the definition and numerical method, not from which result wins. Record changes to the protocol and rerun all affected comparators consistently.

Keep planted truth separate from observable policy features. Do not expose hidden event labels to admission or selection. Freeze evaluation partitions before tuning, grouping correlated drives/sequences where possible.

## Report fields

Every report includes:
- Command/configuration, code commit (or explicit dirty diff/snapshot), dependency versions, hardware, input manifest/hash, and seeds.
- Input/output/quarantine/duplicate accounting and applicable completeness checks.
- Baselines at equal relevant budgets, repeated runs where meaningful, slice sizes, uncertainty/variation, and negative findings.
- Raw result summaries sufficient to reproduce the table, with no restricted data or secrets.
- Conclusions limited to the measured population and conditions; open limitations and next decision.

Do not require commit creation simply to run an experiment; label a dirty tree honestly and preserve a reproducible patch or snapshot. Keep small reports in reports/ when results exist; large artifacts remain outside Git with a manifest.

## Project-specific checks

**Generator:** same-machine reproducibility and kinematic consistency are distinct from realism. Validate calibration on held-out real drives if claiming it. Cross-machine floating-point tolerance must be stated before comparison.

**Miner:** define an event-matching rule (time overlap/tolerance, one-to-one matching, duplicate predictions) before precision/recall. Include false positives, missed events, and threshold sensitivity. Synthetic success does not establish real-world detection performance.

**Admission:** identical ordered candidates and serialized byte costs; FIFO/random/coverage baselines; enforce budget on actual selected items; repeated stochastic runs. Report candidate observability and selection bias.

**Metric:** numerator and denominator share population, time window, and provenance. Missing intervals and zero exposure are explicit. Use suitable uncertainty assumptions and disclose within-drive dependence. Public incident counts and unrelated exposure cannot be combined into a defensible fleet rate without a justified population match.

**Curation:** disjoint grouped partitions, validation-only tuning, fixed model/training conditions and data budget, sealed final evaluation. Record repeated-seed variability where feasible and acknowledge limited compute when it is not.

**Storage:** fixed query/data, row and byte counts, hardware, cache conditions, repetitions, and correctness checks before speed claims.

**Agent interface (optional):** evaluate unsupported requests, wrong-grain requests, tool errors, and answer provenance, not only successful questions. Keep the harness if the feature ships.
