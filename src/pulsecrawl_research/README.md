# Research code map

This package contains the code that turns a public experiment definition into
measurements and retained evidence. The PulseCrawl application itself is
installed from the separately published Python package; its implementation is
not copied into this repository.

## From a thesis question to a result

| Thesis area | Implementation | Public definitions | Retained evidence |
|---|---|---|---|
| Crawling policies and recovery | [`policy/`](policy/) | [`experiments/controlled/`](../../experiments/controlled/) policy and recovery studies | Completed run folders selected by the controlled release |
| Schemas and URL-scoped templates | [`extraction/`](extraction/) | Controlled template studies and generated labelled HTML | Template measurements, comparisons, and readable CSV files |
| Versioned dataset publication | [`datasets/`](datasets/) | Publication, replay, query, and compaction studies | Row checks, Parquet files, version checks, and query measurements |
| Current public websites | [`live/`](live/) | [`experiments/live/`](../../experiments/live/) category definitions and source lists | CSV, Parquet, access reviews, per-site summaries, and per-cycle summaries |
| Comparison systems | [`comparisons/`](comparisons/) and [`runners/`](../../runners/) | Recorded Scrapy, Crawlee, Firecrawl, and PulseCrawl profiles | Normalized measurements with unavailable cases kept separate from failures |

The common trace is:

```text
experiment definition
        -> domain runner
        -> PulseCrawl or comparison adapter
        -> direct measurements
        -> immutable run directory
        -> reviewed release
        -> thesis table or figure
```

## Package structure

```text
pulsecrawl_research/
├── cli.py                  command-line entry point
├── runner.py               dispatches one registered experiment
├── suites.py               groups controlled experiments
├── analysis.py             builds cross-run analysis tables
│
├── common/                 code shared by every study family
│   ├── models.py           stable experiment data structures
│   ├── environment.py      software and machine metadata
│   ├── metrics.py          shared measurement calculations
│   ├── registry.py         experiment-definition lookup
│   ├── reports.py          readable aggregate reports
│   ├── store.py            immutable run folders and checksums
│   └── validation.py       static artifact validation
│
├── policy/                 policy enforcement and recovery
│   ├── experiments.py      budgets, recovery, pacing, robots, and redelivery
│   ├── webbench.py         observable local HTTP websites
│   └── state_model.py      executable state-transition checks
│
├── extraction/             schema and template evaluation
│   ├── experiments.py      controlled extraction comparisons
│   └── maintenance.py      template integration and change measurements
│
├── datasets/               versioned dataset evaluation
│   └── experiments.py      publication, replay, query, and compaction studies
│
├── live/                   bounded public-website studies
│   ├── profiles.py         shared schemas and extraction mappings
│   ├── runner.py           access review, workspace setup, and repeated runs
│   ├── supervisor.py       isolated multi-category process supervisor
│   └── analysis.py         per-category and per-site summaries
│
├── comparisons/            normalized external-system integrations
│   ├── adapters.py         common crawler interface
│   ├── governed_datasets.py
│   └── site_patterns.py
│
└── tools/                  fixture generators, evidence publishers, and verifier
```

The small modules retained at the package root, such as `live_profiles.py` and
`datalake.py`, are compatibility imports. Existing commands and third-party
links continue to work, while the implementation now lives in the descriptive
subpackages above.

## How live schemas and templates are built

Live studies do not contain a separate Python crawler for every website. They
combine common code with public category data:

1. [`live/profiles.py`](live/profiles.py) defines the shared `article`,
   `product`, and `advisory` schemas used by the published live universe.
2. A category's `input/sites.json` supplies website URLs, allowed hosts, URL
   patterns, constant fields, crawl limits, and optional mapping overrides.
3. `templates_for()` combines the shared profile with that website-specific
   configuration to produce URL-scoped JSON-LD, metadata, and CSS templates.
4. [`live/runner.py`](live/runner.py) creates the local workspace, performs the
   access review, registers the resolved schema and templates, runs the
   scheduled cycles, and records the results.
5. The evidence publisher exports a reviewer-readable CSV and a matching
   Parquet view without publishing third-party response bodies.

This separation avoids duplicating common extraction rules while preserving
website-specific scope and overrides in files that reviewers can inspect.

## Compatibility imports

The previous flat imports remain supported. For example, both imports refer to
the same implementation:

```python
from pulsecrawl_research.live_profiles import templates_for
from pulsecrawl_research.live.profiles import templates_for
```

New code should use the organized subpackage path.
