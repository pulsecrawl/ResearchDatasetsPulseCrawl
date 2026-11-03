# Live website studies

This package executes the bounded studies of current public websites. The
workflow uses actual requests and does not publish third-party response bodies.

## Shared code and website-specific data

| Information | Location |
|---|---|
| Shared schemas and common JSON-LD, metadata, and CSS mappings | `profiles.py` |
| Website URLs, hosts, URL scope, constants, limits, and optional overrides | `experiments/live/<category>/input/sites.json` |
| Access review, workspace construction, template registration, and cycles | `runner.py` |
| Isolated multi-category process execution | `supervisor.py` |
| Per-run and per-site summaries | `analysis.py` |

The final templates are built as:

```text
shared schema profile
    + website URL scope
    + website constants
    + optional website mapping overrides
    = resolved URL-scoped template stack
```

The profile-to-category mapping is:

| Profile | Live categories |
|---|---|
| `article` | Mexican newspapers, United States newspapers, financial news |
| `product` | General commerce |
| `advisory` | Security advisories |

Run all categories with the public supervisor documented in
[`runners/live/`](../../../runners/live/), or run one category directly:

```sh
pulsecrawl-research run live-us-newspapers \
  --phase two-hour \
  --output-root ./live-output
```

Each published category folder links its definition, exact source list,
resolved schema and per-site template stacks, readable records, matching
Parquet file, summaries, access review, and checksums.
