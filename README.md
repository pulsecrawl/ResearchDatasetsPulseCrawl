# PulseCrawl research experiments and evidence

This is the public reproducibility companion for
[PulseCrawl](https://github.com/pulsecrawl/PulseCrawl). It contains the
controlled inputs, experiment definitions, runnable research code, comparison
runners, reviewed evidence, and analysis used to evaluate the local
open-source package.

The thesis PDF is intentionally not stored here. This repository contains the
research material needed to inspect how results were produced.

## Start here

The research flow is:

```text
Input data -> Experiment definition -> One or more runs -> Reviewed evidence -> Analysis
Public URL -> Access review         -> Bounded live run -> Versioned dataset -> Summary
```

These terms are deliberately separate:

| Term | Meaning | Location |
|---|---|---|
| Input data | Generated pages or records with known answers | [`datasets/`](datasets/) |
| Experiment | The question, settings, measurements, and acceptance rule | [`experiments/`](experiments/) |
| Run | One execution with resolved settings, measurements, and checksums | `experiments/controlled/<experiment>/runs/` or `experiments/live/<category>/runs/` |
| Evidence release | A reviewed collection of runs and derived results | [`experiments/releases/`](experiments/releases/) |
| Research code | Runners, metrics, storage helpers, and verification tools | [`src/pulsecrawl_research/`](src/pulsecrawl_research/) |

An input file or experiment definition is not proof that a run occurred.
Completed runs contain their own manifests and checksums.

## Repository map

```text
ResearchDatasetsPulseCrawl/
├── README.md                       this guide and the reviewer reading order
├── CITATION.cff                    citation metadata
├── LICENSE, NOTICE, PRIVACY.md     licensing and publication boundaries
├── pyproject.toml                  reproducible research package
├── registry.yaml                  runnable public experiment registry
│
├── docs/
│   ├── protocols/                  evaluation procedures and decision rules
│   ├── environment/                package pins and compatibility information
│   └── images/                     previews of generated, non-live fixtures
│
├── datasets/
│   ├── fixed-html/                 60 generated pages with expected answers
│   ├── site-pattern-html/          100 scoped-template pages
│   ├── commerce-html/              fictional recurring price observations
│   ├── storage/                    generated versioned-dataset inputs
│   └── webbench/                   local controlled HTTP website generator
│
├── experiments/
│   ├── catalog.json                descriptive controlled experiment catalog
│   ├── controlled/
│   │   └── <experiment-name>/
│   │       └── runs/run-001/       guide, JSON evidence, readable CSV, checksums
│   ├── live/
│   │   ├── catalog.json            five live categories and source counts
│   │   └── <category>/
│   │       ├── README.md           category purpose and schedule
│   │       ├── experiment.yaml     current two-hour protocol
│   │       ├── input/sites.json    exact reviewed URLs and limits
│   │       └── runs/               published bounded-run evidence
│   └── releases/
│       └── <release>/              analysis, evidence index, and checksums
│
├── runners/
│   ├── pulsecrawl/                 PulseCrawl controlled runner
│   ├── scrapy/                     Scrapy controlled runner
│   ├── crawlee/                    Crawlee controlled runner
│   ├── firecrawl/                  pinned optional self-hosted profile
│   └── live/                       multi-category live-study supervisor
│
├── src/pulsecrawl_research/
│   ├── README.md                   thesis-question-to-code map
│   ├── common/                     shared models, metrics, storage, validation
│   ├── policy/                     budgets, pacing, robots, and recovery
│   ├── extraction/                 schemas and template experiments
│   ├── datasets/                   publication, replay, query, and compaction
│   ├── live/                       live profiles, runner, supervisor, analysis
│   ├── comparisons/                external-system adapters and comparisons
│   ├── runner.py                   one-experiment orchestration
│   └── tools/                      generators, publishers, and verifier
│
└── tests/                          repository and research-code checks
```

Folder names use full experiment names. Historical opaque identifiers remain
only inside immutable source manifests where changing them would break
traceability.

## Install and verify

Python 3.11 or newer:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[all]'
python src/pulsecrawl_research/tools/verify.py
python -m unittest discover -s tests -v
```

The research package pins the separately published local package:

```sh
python -m pip install 'pulsecrawl[workspace]==0.4.0'
```

The PulseCrawl implementation is not copied into this repository.

## Controlled inputs and evidence

| Collection | Scope | Purpose |
|---|---:|---|
| Fixed HTML | 60 generated pages | Basic extraction against known values |
| Scoped site patterns | 100 pages across 20 fictional configurations | Template selection, fallback, and markup changes |
| Fictional commerce | 20 documents from ten fictional stores | Repeated product and price observations |
| Storage reference | Deterministic 1,000-row sample plus larger generator settings | Dataset versions, compaction, and temporal queries |
| WebBench | Generated local HTTP websites | Budgets, robots rules, pacing, failures, and recovery |

Generated inputs use fictional names and reserved `.example` URLs. They are
not presented as real website observations. Reviewed controlled evidence is
organized by descriptive experiment name under
[`experiments/controlled/`](experiments/controlled/).

## Live study

The thesis live-study universe contains 75 websites in five categories:

| Category | Websites | Output schema | Executions per website |
|---|---:|---|---:|
| Mexican newspapers | 19 | Article | 4 |
| United States newspapers | 20 | Article | 4 |
| Financial and stock news | 20 | Article | 4 |
| General commerce | 8 | Product | 4 |
| Security advisories | 8 | Security advisory | 4 |
| **Total** | **75** |  | **300 site executions** |

The two-hour study used actual raw HTTP requests and the public PulseCrawl
0.4.0 package. Every website was scheduled four times at 30-minute intervals.
Each execution allowed up to 1,500 URLs, crawl depth five, and 1,680 seconds,
while respecting the longer of the applicable robots delay or a 0.5-second
same-origin interval.

All 300 site executions succeeded. The release contains 374,395 fetched pages,
68,367 published rows, and 53,381 unique target-record URLs. Start with the
[`thesis-live-universe-v1.0.0` release](experiments/releases/thesis-live-universe-v1.0.0/)
for category totals, website-level measurements, and matching CSV/Parquet
evidence.

## Dataset and publication boundary

- Third-party HTML bodies are processed in memory and are not published.
- Published live evidence may contain source URLs, HTTP status, response
  checksums, extracted records, local workspace validation, Parquet parts, and
  dataset-version manifests.
- Every controlled run includes `measurements.csv`, a reviewer-readable view of
  its authoritative JSON measurements. Dataset-producing controlled runs also
  include checksum-linked Parquet evidence and a matching complete or bounded
  CSV view.
- Every published live table has matching CSV and Parquet views. Source URLs
  and extracted public-page values are preserved so reviewers can audit the
  classifications and records.
- No credentials, browser profiles, workstation paths, or private author
  metadata are permitted in a release.
- Every published run has a checksum file. Every release has a separate
  release manifest; releases are never overwritten.

See [`PRIVACY.md`](PRIVACY.md) for the complete boundary.

## Reviewer reading order

1. This README.
2. [`experiments/catalog.json`](experiments/catalog.json) for controlled tests.
3. [`experiments/live/catalog.json`](experiments/live/catalog.json) for live categories.
4. [`docs/protocols/`](docs/protocols/) for evaluation procedures.
5. [`experiments/releases/`](experiments/releases/) for reviewed findings.
6. A named experiment's `runs/` directory for direct measurements and checksums.
