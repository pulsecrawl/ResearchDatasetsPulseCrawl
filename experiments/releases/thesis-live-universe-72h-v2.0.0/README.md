# Thesis live-study universe: 72-hour retained run

This release indexes the completed three-day thesis-universe study. The
immutable source evidence contains 75 websites in five categories, 72 hourly
scheduled executions per website, and 5,400 successful terminal site
executions. The complete workspaces and readable outputs are distributed as
assets of the matching GitHub release; compact reviewer-facing evidence is
kept here in Git.

## Result at a glance

| Measure | Result |
|---|---:|
| Websites | 75 |
| Categories | 5 |
| Scheduled executions per website | 72 |
| Successful terminal executions | 5,400 |
| Missed occurrences | 0 |
| Pages fetched | 6,971,063 |
| Failed requests | 78,668 |
| Robots-blocked decisions | 28,437 |
| Exported rows | 466,141 |
| Source files inventoried | 14,215 |
| Full public evidence after extraction | 9,954,692,984 bytes |
| Complete release download | 1,044,445,423 bytes |

The run used the public index-installed PulseCrawl 0.4.0 distribution. Raw
third-party HTML bodies were not retained.

## Reading order

1. `methodology.md`
2. `category-summary.csv` and `site-summary.csv`
3. `limitations.md`
4. `provenance.json` and `source-verification.json`
5. `RELEASE-FILES.csv` for the complete source inventory
6. `download-and-verify.md` and `asset-manifest.json`
7. The GitHub release assets for workspaces, SQLite state, Parquet, CSV, logs,
   execution records, and analysis

## Apple scope finding

All Apple evidence remains part of the registered 75-site study. Its URL scope
also admitted general Apple Support articles, creating semantic false
positives for that source. This does not change the execution, policy,
persistence, or publication measurements; see `limitations.md`.

## Integrity

`source-verification.json` records successful verification of the immutable
14,004-entry source suite manifest. `RELEASE-FILES.csv` records every source
file, byte size, SHA-256 digest, and any publication-only transformation.
`asset-checksums.sha256` records the download hashes and
`published-files.sha256` records every extracted public file. The streaming
verification tool checks the archives without requiring a second 10 GB copy on
disk.
