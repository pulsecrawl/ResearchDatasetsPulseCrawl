# Comparison systems

This package keeps comparison-specific code separate from PulseCrawl's policy,
extraction, and dataset experiments.

| File | Role |
|---|---|
| `adapters.py` | Normalizes PulseCrawl, Scrapy, Crawlee, and Firecrawl outcomes |
| `site_patterns.py` | Compares generated site-pattern extraction integrations |
| `governed_datasets.py` | Compares native output with a common dataset contract |

System-specific launchers are under [`runners/`](../../../runners/). An
unavailable system is recorded as unavailable rather than converted into a
zero score.
