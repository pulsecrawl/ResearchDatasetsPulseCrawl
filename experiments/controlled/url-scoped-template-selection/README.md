# URL-scoped template selection and contamination

**Experiment ID:** `url-scoped-template-selection`

**Research area:** Template policy and extraction

**Acceptance result:** PASS

## Question answered

Can website-specific templates populate one shared schema without a template
written for one website adding values to another website's records?

The controlled workload contains 300 generated pages from 15 fictional
websites across news, jobs, and products. It compares generic extraction,
site-specific routing, URL-scoped templates with generic fallback, and an
unsafe comparison in which every website template can apply to every page.

## Result at a glance

| Strategy | Field accuracy | Record coverage | Wrong-site records |
|---|---:|---:|---:|
| Generic | 60% | 100% | 0 of 300 |
| Routed | 100% | 100% | 0 of 300 |
| Scoped | 100% | 100% | 0 of 300 |
| Unscoped | 100% | 100% | 280 of 300 |

The scoped policy preserved all expected fields and record coverage while
producing no wrong-site record. The unscoped comparison produced 280
wrong-site records out of 300.

Open the completed execution below for the readable comparison table, file
guide, exact configuration, authoritative measurements, and checksums.

| Completed execution | Original execution ID | Status |
|---|---|---|
| [`run-001`](runs/run-001/) | `20261026T061323Z-t01-4e841c4c` | completed |
