# Execution evidence

This directory stores reviewed evidence for completed experiment executions.
It does not store application source or downloaded third-party HTML.

For a plain-language explanation of datasets, experiments, executions,
evidence, and analysis, begin with the [repository guide](../../README.md).

## Two kinds of evidence

| Evidence | Location | Meaning |
| --- | --- | --- |
| Controlled executions | [This folder](./) | Direct measurements from repeatable tests with fixed inputs |
| Live studies | [`../live/`](../live/) | Bounded observations from current public pages |

Each published execution uses this layout:

```text
experiments/controlled/<experiment-name>/runs/run-###/
├── README.md
├── execution-manifest.json
├── resolved-experiment.json
├── measurements.json
├── measurements.csv
├── summary.json
├── readable-output/             # dataset-producing runs only
│   ├── records*.parquet
│   ├── records*.csv
│   ├── schema.json
│   └── export-manifest.json
└── checksums.sha256
```

`execution-manifest.json` must validate against
[`execution-manifest.schema.json`](../releases/execution-manifest.schema.json). It records
the public package version, experiment identifier, dataset revision, sanitized
environment, timestamps, command, status, and output paths.

The following material is not publishable here:

- credentials, tokens, cookies, or sensitive headers;
- usernames, hostnames, absolute workstation paths, or personal email;
- unreviewed notes or raw workspace databases;
- downloaded third-party HTML without redistribution permission;
- raw high-cardinality logs that are unnecessary for the stated measurement.

This repository contains 116 reviewed controlled executions across 27 named
experiments. Each run is independently checksum-linked and the public verifier
checks the complete set directly.

`measurements.csv` is derived directly from `measurements.json` so reviewers
can inspect the retained values in GitHub. A Parquet/CSV pair is added only when
the experiment actually produced dataset rows. For a large benchmark, the pair
is explicitly labeled as a bounded preview; it is never presented as the full
million-row output.

For a readable entry point, use the [controlled index](INDEX.md) and the
[live-study guide](../live/README.md). Neither controlled nor live evidence
contains downloaded third-party HTML bodies.

