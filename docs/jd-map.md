# Job description and evidence map

Target: **Data Engineer, Fleet Data, Self-Driving — Tesla AI — Palo Alto — Req. 279540**. The appendix preserves the posting captured on 2026-08-25. Its current availability has not been checked.

Updated scope: 2026-09-28. The [roadmap](roadmap.md) owns milestone sequencing; this document owns the relationship between responsibilities and evidence. Descriptions below are paraphrases; the appendix is the captured source text.

## Evidence mapping

Most rows remain **planned / unproven**. Row 9 now has partial local evidence from the Python foundation; hosted Windows/Linux CI passes; broader automation remains unbuilt. Documentation alone does not close a row.

| Row | Responsibility | Milestone / artifact | Required evidence | Status |
|---|---|---|---|---|
| 1 | Manage fleet inflow while preserving diverse data | M3 admission-policy comparison | Equal-byte comparison, yield/coverage, budget accounting, observable features, selection limitations | Planned |
| 2 | Make fleet data discoverable and queryable | M1 ClickHouse + explorer; M2 assets | Schema rationale, working bounded queries, latency at stated size, visible lineage/quality | Planned |
| 3 | Define driving-performance metrics that inform decisions | M1 event rate; M2 methodology report | Hand-computed fixture, exposure/gap policy, stratification, uncertainty/completeness, supported interpretation | Planned |
| 4 | Surface valuable scenarios for training/evaluation | M1 hard-brake discovery; M3 selection; M4 real-image curation | Frozen truth/matching rules, precision/recall, threshold sensitivity, explicit synthetic/real limits | Planned |
| 5 | Evaluate effectiveness of new datasets | M4 controlled curation experiment | Disjoint evaluation, equal training conditions, per-slice delta and variability, negative results | Planned |
| 6 | Deliver interactive visualizations and useful tooling | M1 explorer; M5 polish | Inspectable event with source trace, bounded payloads, usability walkthrough, measured interaction latency | Planned |
| 7 | Build agentic tools for analysis | Optional semantic tool interface | Bounded read-only contracts, provenance, evaluation of success and failure cases | Planned / optional |
| 8 | Work across data engineering, analytics, and data science | M1–M4 related data products | End-to-end telemetry demo and separate controlled ML experiment; explicit boundary between them | Planned |
| 9 | Build automation and internal libraries | M0 packaging/tests; M2 automation | Reproducible setup, shared contracts, CI, useful run tooling | Partial: [contracts and 59 passing cases](walkthroughs/01-python-foundation.md), [CI](../.github/workflows/ci.yml) passing on Windows/Linux; M2 automation pending |
| 10 | Own ingestion through visualization | M1 demo; M2 reliability | Source-to-surface traceability, reproducible run, known exclusions, recovery demonstration | Planned |
| 11 | Monitor and maintain infrastructure health | M2 operations; M3 streaming if added | Run metadata, quality/freshness checks, injected failure, diagnosis and recovery runbook | Planned |

## Qualifications and learning evidence

| Qualification | How to demonstrate it |
|---|---|
| Python and SQL proficiency | Explain, debug, and modify actual transforms/queries; focused independent practice alongside AI implementation |
| Data models, performant queries, ETL | Defend grain/ordering, benchmark an actual query, prove replay and reconciliation |
| Technologies named as examples | ClickHouse and Dagster serve concrete milestones; Postgres/PySpark are optional until justified, not a checklist |
| Full data lifecycle | A usable source-to-explorer workflow and operational investigation |
| End-to-end ownership under ambiguity | Recorded requirements, alternatives, decisions, failures, and changes based on evidence |
| Education | Existing profile records CSULB CS, May 2026; this project does not create new credential evidence |

Learning assessment lives in [learning/README.md](learning/README.md), independently of engineering completion. AI implementation is allowed. No claim of professional team experience follows from a solo AI-assisted project.

## Turning evidence into application material

Use: "Implemented [specific behavior] on [honestly scoped dataset]; verified [result] under [conditions]." Fill in only actual results. A benchmark on generated data must say so. A planned experiment is not a resume achievement.

A closed telemetry-to-model loop requires validated sample linkage; unrelated synthetic telemetry and BDD100K experiments do not establish it. Keep optional gaps visible rather than claiming every role responsibility is proven.

## Appendix — verbatim posting

*Captured 2026-08-25.*

**Data Engineer, Fleet Data, Self-Driving**

| | |
|---|---|
| Job Category | Tesla AI |
| Location | Palo Alto, California |
| Req. ID | 279540 |
| Job Type | Full-time |

### What to Expect

> Help power the future of Full Self-Driving by unlocking the immense potential of data from millions of Tesla vehicles worldwide.
>
> On the Self-Driving Fleet Data team, you'll work at the intersection of data engineering, analytics, and data science: building reliable pipelines and critical infrastructure for FSD model evaluation and improvements. This role owns critical data pipelines that feed landmark projects like the Full Self-Driving Vehicle Safety Report and surfaces the most valuable real-world scenarios from the fleet for training and evaluation. It builds the data foundation for setting priorities, measuring progress, and curating diverse datasets, work that has tangible impact on making scalable autonomy a reality.

### What You'll Do

> - Design and maintain data platforms that make it easy for teams across the org to discover, query, and explore fleet data
> - Design and implement data pipelines from ingestion to visualization to unlock the full potential of Tesla's fleet data by sourcing, transforming, and serving new datasets
> - Define and build metrics that measure Self-Driving performance and specific driving events, then turn them into insights that drive decisions
> - Monitor and maintain infrastructure health with robust alerting, logging, and automation for scale and reliability
> - Build automation, developer tools, internal libraries, and agentic tools that accelerate analysis and visualization across the company
> - Manage inflow rate of fleet data to ensure consumers have a high volume of diverse data
> - Iterate with AI engineering partners on effectiveness of new datasets
> - Deliver world class, interactive visualizations and tooling that turns complex data into actionable insights

### What You'll Bring

> - Bachelor's Degree in Computer Science, Engineering, Physics, Math, proof of exceptional skills in related field, or equivalent experience
> - Proficient in Python and SQL with experience building data models, performant queries, and ETLs at scale (e.g. PostgreSQL, Clickhouse, Pyspark, Dagster)
> - Experience across the data lifecycle including sourcing, ingestion, transformation, analytics, and visualization
> - Ability to own projects end-to-end from defining the right data to collect, building robust pipelines, to delivering actionable metrics and tooling
> - Ability to thrive in a rapidly changing environment with high ambiguity; self-starter mentality
> - Passion for the future of transportation and AI technologies
