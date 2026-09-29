# Metric definitions and methodology

No metric computation is implemented yet. Start with versioned definitions in files; a Postgres registry is deferred until mutable control-plane requirements justify it.

Each metric definition must name:
- Purpose, owner, version/change history, and restatement policy.
- Input snapshot and normalization versions, output grain, eligible population.
- Event/numerator definition (including episode boundaries) and denominator with units.
- Time window, exclusions, missing-data policy, and zero-exposure behavior.
- Stratification dimensions, completeness/ascertainment limitations, and uncertainty method.
- Computation/query, hand-computed fixture, and relevant reconciliation checks.

The initial metric is a **hard-braking episode rate per valid distance**, with its threshold/duration and integration/gap rules to be fixed before implementation. Do not count every below-threshold sample as a separate event.

Exposure is computed independently of expensive clip admission. Missing event ascertainment must still be reported; knowing exposure does not recover unobserved events. Synthetic event rates do not measure real autonomous-driving safety.

The methodology report accompanies the result and explains assumptions and uncorrected biases. A new query, changed definition, or backfill that changes published values must identify what was restated and why. Experimental comparisons follow [../experiments.md](../experiments.md).
