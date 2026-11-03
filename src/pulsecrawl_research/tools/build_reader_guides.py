"""Build the repetitive reviewer guides from checked-in manifests."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def url_scoped_template_guide(
    folder: Path,
    runs: list[Path],
    manifests: list[dict],
    resolved: dict,
) -> str:
    measurements = json.loads((runs[0] / "measurements.json").read_text())
    strategies = measurements["strategies"]
    scoped = strategies["scoped"]
    unscoped = strategies["unscoped"]
    verdict = (
        scoped["contaminated"] == 0
        and scoped["contaminationRate"] < unscoped["contaminationRate"]
        and scoped["fieldAccuracy"] >= unscoped["fieldAccuracy"]
        and scoped["recordCoverage"] >= unscoped["recordCoverage"]
    )
    result_rows = "\n".join(
        f"| {name.title()} | {values['fieldAccuracy']:.0%} | "
        f"{values['recordCoverage']:.0%} | {values['contaminated']} of {values['pages']} |"
        for name, values in strategies.items()
    )
    run_rows = "\n".join(
        f"| [`{run.name}`](runs/{run.name}/) | `{manifest['executionId']}` | {manifest['status']} |"
        for run, manifest in zip(runs, manifests)
    )
    return f"""# {resolved.get("title", folder.name)}

**Experiment ID:** `{folder.name}`

**Research area:** Template policy and extraction

**Acceptance result:** {"PASS" if verdict else "FAIL"}

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
{result_rows}

The scoped policy preserved all expected fields and record coverage while
producing no wrong-site record. The unscoped comparison produced {unscoped["contaminated"]}
wrong-site records out of {unscoped["pages"]}.

Open the completed execution below for the readable comparison table, file
guide, exact configuration, authoritative measurements, and checksums.

| Completed execution | Original execution ID | Status |
|---|---|---|
{run_rows}
"""


def build_live_guides() -> int:
    catalog = json.loads((ROOT / "experiments/live/catalog.json").read_text())
    written = 0
    for category in catalog["categories"]:
        folder = ROOT / "experiments/live" / category["id"]
        sites = json.loads((folder / "input/sites.json").read_text())["sites"]
        rows = [
            f"| {site['name']} | `{site['id']}` | {site['listingUrl']} |"
            for site in sites
        ]
        body = f"""# {category["name"]} live study

This category contains {len(sites)} websites in the thesis live-study universe.
Each website was scheduled four times at 30-minute intervals. An execution
could visit up to 1,500 URLs to depth five within a 1,680-second window.

| Website | Stable ID | Discovery entry URL |
|---|---|---|
{chr(10).join(rows)}

## Where to start

| Reviewer question | File or folder |
|---|---|
| Which websites and URL scopes were configured? | [`input/sites.json`](input/sites.json) |
| Which protocol and limits were used? | [`experiment.yaml`](experiment.yaml) |
| What did the completed study produce? | [`runs/thesis-universe-2h-2026-11-02/`](runs/thesis-universe-2h-2026-11-02/) |
| What are the site-level totals? | [`site-summary.csv`](runs/thesis-universe-2h-2026-11-02/readable-output/site-summary.csv) |
| What do representative target records look like? | [`records-preview.csv`](runs/thesis-universe-2h-2026-11-02/readable-output/records-preview.csv) |
| Which target records were published? | [`records.csv`](runs/thesis-universe-2h-2026-11-02/readable-output/records.csv) |
| How were representative fetched URLs classified? | [`pages-preview.csv`](runs/thesis-universe-2h-2026-11-02/readable-output/pages-preview.csv) |

## Code used

| Step | Public implementation |
|---|---|
| Build the shared schema and URL-scoped template stacks | [`live/profiles.py`](../../../src/pulsecrawl_research/live/profiles.py) |
| Review access, create the workspace, and execute scheduled cycles | [`live/runner.py`](../../../src/pulsecrawl_research/live/runner.py) |
| Start categories as isolated processes | [`live/supervisor.py`](../../../src/pulsecrawl_research/live/supervisor.py) |
| Core crawl, extraction, and dataset operations | [PulseCrawl public package](https://github.com/pulsecrawl/PulseCrawl) |

The source list supplies the website-specific URL scope, constants, limits,
and optional mapping overrides. The Python profile supplies the shared schema
and common extraction mappings; there is no hidden crawler implementation for
this category.
"""
        (folder / "README.md").write_text(body, encoding="utf-8")
        input_rows = [
            f"| {site['name']} | `{site['id']}` | {site['listingUrl']} | "
            f"{site['representativeDetailUrl']} |"
            for site in sites
        ]
        input_body = f"""# {category["name"]}

This directory defines the {len(sites)} public websites in this category. The
entry URL starts discovery and the validation URL is a known target page used
to review the website-specific scope and extraction mappings. No response
bodies are retained.

| Website | Stable ID | Discovery entry URL | Validation URL |
|---|---|---|---|
{chr(10).join(input_rows)}
"""
        (folder / "input/README.md").write_text(input_body, encoding="utf-8")
        written += 1
    return written


def build_controlled_guides() -> int:
    written = 0
    for folder in sorted((ROOT / "experiments/controlled").iterdir()):
        if not folder.is_dir():
            continue
        runs = sorted((folder / "runs").glob("run-*"))
        if not runs:
            continue
        resolved = json.loads((runs[0] / "resolved-experiment.json").read_text())
        manifests = [
            json.loads((run / "execution-manifest.json").read_text()) for run in runs
        ]
        if folder.name == "url-scoped-template-selection":
            (folder / "README.md").write_text(
                url_scoped_template_guide(folder, runs, manifests, resolved),
                encoding="utf-8",
            )
            written += 1
            continue
        body = f"""# {resolved.get("title", folder.name)}

**Experiment ID:** `{folder.name}`  
**Retained runs:** {len(runs)}

{resolved.get("description", "Controlled experiment with fixed registered inputs.")}

The registered acceptance rule is recorded in each run's
`resolved-experiment.json`. Direct measurements are authoritative in
`measurements.json` and available as a readable table in `measurements.csv`;
`summary.json` contains the run-level result used by the reviewed analysis.
When the run produced dataset rows, `readable-output/` contains checksum-linked
Parquet evidence and its matching complete or bounded CSV view.

| Public folder | Original execution ID | Status |
|---|---|---|
{chr(10).join(f"| [`{run.name}`](runs/{run.name}/) | `{manifest['executionId']}` | {manifest['status']} |" for run, manifest in zip(runs, manifests))}
"""
        (folder / "README.md").write_text(body, encoding="utf-8")
        written += 1
    return written


def main() -> int:
    print(
        json.dumps(
            {
                "liveGuides": build_live_guides(),
                "controlledGuides": build_controlled_guides(),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
