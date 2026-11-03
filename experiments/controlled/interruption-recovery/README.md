# Recovery at durable crawl boundaries

**Experiment ID:** `interruption-recovery`  
**Retained runs:** 3

Controlled experiment with fixed registered inputs.

The registered acceptance rule is recorded in each run's
`resolved-experiment.json`. Direct measurements are authoritative in
`measurements.json` and available as a readable table in `measurements.csv`;
`summary.json` contains the run-level result used by the reviewed analysis.
When the run produced dataset rows, `readable-output/` contains checksum-linked
Parquet evidence and its matching complete or bounded CSV view.

| Public folder | Original execution ID | Status |
|---|---|---|
| [`run-001`](runs/run-001/) | `20261026T054115Z-s02-285ce346` | completed |
| [`run-002`](runs/run-002/) | `20261026T054247Z-s02-f0854781` | completed |
| [`run-003`](runs/run-003/) | `20261026T054417Z-s02-b60d580e` | completed |
