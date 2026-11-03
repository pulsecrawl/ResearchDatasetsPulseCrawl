# Reviewed executions

This release contains 116 controlled execution directories that passed
public-artifact review. Each directory includes the resolved experiment,
direct measurements, summary, sanitized execution manifest, and checksums.

Use [`INDEX.md`](INDEX.md) to see the experiment names and number of retained
executions. Each experiment then contains readable `run-001`, `run-002`, and
similar folders. The original timestamped execution ID remains inside
`execution-manifest.json` for traceability.

## How to read one execution

| File | Meaning |
| --- | --- |
| `execution-manifest.json` | Execution ID, descriptive experiment ID, timestamps, software versions, source checksum, public checksum paths, and reconstructed registered command |
| `resolved-experiment.json` | The workload, measurements, and acceptance rule applied to that execution |
| `measurements.json` | Direct measurements retained by the experiment harness |
| `measurements.csv` | The same retained measurements flattened into a GitHub-readable table |
| `summary.json` | Run-level summary used by the frozen analysis |
| `readable-output/` | Parquet evidence and matching CSV for runs that produced dataset rows |
| `checksums.sha256` | Integrity hashes for every published evidence file in the run |

The descriptive parent folder answers “what was tested.” The `run-###` folder
answers “which repetition is this.” The execution manifest preserves the
original immutable execution identity.

## Code used

| Experiment family | Public implementation |
|---|---|
| Policy limits, pacing, robots, recovery, and redelivery | [`policy/`](../../src/pulsecrawl_research/policy/) |
| Schemas, template selection, fallback, and maintenance | [`extraction/`](../../src/pulsecrawl_research/extraction/) |
| Dataset publication, replay, query, and compaction | [`datasets/`](../../src/pulsecrawl_research/datasets/) |
| Scrapy, Crawlee, Firecrawl, and integration comparisons | [`comparisons/`](../../src/pulsecrawl_research/comparisons/) and [`runners/`](../../runners/) |
| Definition dispatch and immutable run creation | [`runner.py`](../../src/pulsecrawl_research/runner.py) |

The `kind` and descriptive experiment ID in `resolved-experiment.json` identify
the branch selected by `runner.py`. Domain README files then explain the code
used by that family.

The retained runs were sanitized and materialized before publication. They
contain bounded evidence, not entire workspaces. Parquet is present only for
experiments whose retained source run contained dataset output. The verifier
checks every run's readable files and checksum manifest directly.

