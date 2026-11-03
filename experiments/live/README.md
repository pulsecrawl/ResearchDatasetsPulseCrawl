# Live website studies

The thesis live-study universe contains 75 websites in five categories:
Mexican newspapers, United States newspapers, financial news, general
commerce, and security advisories.

Each category folder contains:

1. `input/sites.json`: the exact website definitions and URL-scoped templates;
2. `experiment.yaml`: the four-cycle, two-hour protocol; and
3. `runs/thesis-universe-2h-2026-11-02/`: the published evidence.

Every website was scheduled four times at 30-minute intervals. Each execution
allowed at most 1,500 URLs, crawl depth five, and 1,680 seconds. Requests used
the longer of the applicable robots delay or 0.5 seconds between requests to
the same origin. Third-party response bodies were processed in memory and were
not retained.

Start with [`catalog.json`](catalog.json), then open a category README or the
[release overview](../releases/thesis-live-universe-v1.0.0/).

## Implementation

Shared schemas and mappings are under
[`src/pulsecrawl_research/live/`](../../src/pulsecrawl_research/live/).
Website-specific scope remains in each category's `input/sites.json`, and the
multi-category process is documented under
[`runners/live/`](../../runners/live/).
