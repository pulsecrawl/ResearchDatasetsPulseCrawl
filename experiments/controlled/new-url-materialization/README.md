# Append-all versus new-URL materialization

**Experiment ID:** `new-url-materialization`  
**Retained runs:** 1

Controlled experiment with fixed registered inputs.

The registered acceptance rule is recorded in each run's
`resolved-experiment.json`. Direct measurements are authoritative in
`measurements.json` and available as a readable table in `measurements.csv`;
`summary.json` contains the run-level result used by the reviewed analysis.
When the run produced dataset rows, `readable-output/` contains checksum-linked
Parquet evidence and its matching complete or bounded CSV view.

| Public folder | Original execution ID | Status |
|---|---|---|
| [`run-001`](runs/run-001/) | `20261026T061326Z-d02-b82cd01c` | completed |
