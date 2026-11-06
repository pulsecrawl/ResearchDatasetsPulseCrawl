# PulseCrawl thesis live universe — completed 72-hour evidence

This release publishes the reviewed evidence from the registered three-day
PulseCrawl thesis study. It used the public index-installed
`pulsecrawl[workspace]==0.4.0` distribution.

## Completion result

- 75 websites in five registered categories;
- 72 hourly occurrences for every website;
- 5,400 successful terminal site executions;
- zero missed occurrences and zero scheduler errors;
- 6,971,063 pages fetched;
- 78,668 failed requests;
- 28,437 robots-blocked decisions;
- 466,141 exported rows.

## Evidence layout

The repository directory
`experiments/releases/thesis-live-universe-72h-v2.0.0/` contains the compact
reviewer index, all exact site definitions, summaries, provenance, limitations,
and three checksum layers. The ten assets attached here total about 1.04 GB and
reconstruct the complete 9.95 GB public evidence mirror:

- one archive for the analysis output;
- one archive for suite metadata and logs;
- one archive for each of the five category run directories;
- the asset manifest and both release checksum files.

See `download-and-verify.md` in the repository release directory for exact
download, extraction, and streaming-verification commands.

## Interpretation note

Apple remains in the registered 75-site universe. Its numeric Apple Support URL
scope also admitted ordinary support pages, so Apple security-advisory rows
should not be treated as uniformly semantically precise. This is a bounded
template-scope limitation; it does not change the scheduling, robots, pacing,
execution-completion, persistence, or checksum results. No rerun was used to
hide or replace the observation.

## Publication transformations

No third-party response bodies are included. The public mirror replaces 32
absolute workstation-path occurrences and the same transient Oracle logout
credential in its SQLite, CSV, and Parquet representations. The original local
suite remained checksum-verifiable; all 14,004 original suite-manifest entries
passed, and all 14,215 public archive members passed reconstruction and privacy
verification.
