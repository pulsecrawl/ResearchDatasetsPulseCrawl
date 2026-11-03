# URL-scoped template selection: completed execution

**Execution:** `20261026T061323Z-t01-4e841c4c`  
**Status:** completed  
**Acceptance result:** PASS

## Question answered

Can website-specific extraction templates populate a shared schema without a
template written for one website adding values to records from another website?

This execution supports the thesis template-policy hypothesis by comparing the
URL-scoped PulseCrawl policy with an unscoped comparison.

## Controlled workload

The deterministic workload contained 15 fictional websites: five news sites,
five job sites, and five product sites. Each site supplied 20 pages, for 300
pages in total. Every page had two expected fields, `title` and `body`,
producing 600 expected field values.

## Strategies compared

| Strategy | Meaning |
|---|---|
| Generic | Uses only general metadata mappings that are not specific to one website. |
| Routed | Uses only the templates assigned to the current website. |
| Scoped | Uses the current website's templates followed by the generic fallback. This is the PulseCrawl policy. |
| Unscoped | Makes every website template available to every page. This is the unsafe comparison. |

## Result at a glance

| Strategy | Field accuracy | Record coverage | Wrong-site records |
|---|---:|---:|---:|
| Generic | 60% | 100% | 0 of 300 |
| Routed | 100% | 100% | 0 of 300 |
| Scoped | 100% | 100% | 0 of 300 |
| Unscoped | 100% | 100% | 280 of 300 |

The scoped strategy produced every expected field, retained a record for every
page, and produced no wrong-site record. The unscoped strategy retained the
expected fields but added a value from the wrong website to 280 of 300 records
(93.3%). The registered acceptance rule therefore passed.

### Why can an unscoped record be accurate and contaminated?

Field accuracy checks the expected `title` and `body`. Contamination is a
separate check for the website-specific `site` value. An unscoped record can
contain the correct title and body while also carrying a site value contributed
by another website's template.

## Files in this directory

| File | Plain-language purpose |
|---|---|
| `results-by-strategy.csv` | Direct comparison of the four strategies; start here. |
| `measurements.json` | Authoritative structured measurements. |
| `measurements.csv` | Generic flattened view of `measurements.json`. |
| `summary.json` | Run result consumed by the reviewed analysis. |
| `resolved-experiment.json` | Registered workload, measurements, seed, and acceptance rule. |
| `execution-manifest.json` | Execution time, command, software, configuration, and source identity. |
| `checksums.sha256` | Integrity hashes for the published evidence files. |

This experiment produces comparison measurements rather than a versioned
output dataset, so no Parquet file is expected. The original execution
retained aggregate measurements, not page-level extracted records; no
page-level evidence has been reconstructed or invented for this public view.
