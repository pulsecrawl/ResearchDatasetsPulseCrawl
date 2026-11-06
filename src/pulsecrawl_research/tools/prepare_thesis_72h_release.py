"""Prepare the browser-readable metadata for the 72-hour thesis evidence release.

The immutable source run is never modified.  Large workspaces and readable
tables are packaged separately as GitHub release assets; this tool publishes
the compact evidence index, exact configurations, checksums, and reviewer
guides that belong in Git.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[3]
RELEASE_ID = "thesis-live-universe-72h-v2.0.0"
RELEASE_DIR = ROOT / "experiments" / "releases" / RELEASE_ID
PRIVATE_ROOT = ""
PUBLIC_ROOT = "${PULSECRAWL_RESEARCH_ROOT}"
EXPECTED_CATEGORIES = {
    "financial-news": 20,
    "general-commerce": 8,
    "mexican-newspapers": 19,
    "security-advisories": 8,
    "us-newspapers": 20,
}
EXPECTED_TOTALS = {
    "sites": 75,
    "executions": 5400,
    "successfulExecutions": 5400,
    "pagesFetched": 6971063,
    "pagesFailed": 78668,
    "robotsBlocked": 28437,
    "publishedRows": 466141,
    "summedSiteUniqueSourceUrls": 100098,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace(PRIVATE_ROOT, PUBLIC_ROOT)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, dict):
        return {key: redact_value(item) for key, item in value.items()}
    return value


def copy_json_redacted(source: Path, destination: Path) -> None:
    write_json(destination, redact_value(json.loads(source.read_text(encoding="utf-8"))))


def combine_csv(sources: Iterable[Path], destination: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    fieldnames: list[str] | None = None
    for source in sources:
        with source.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if fieldnames is None:
                fieldnames = list(reader.fieldnames or [])
            elif list(reader.fieldnames or []) != fieldnames:
                raise ValueError(f"CSV columns differ: {source}")
            rows.extend(reader)
    if not fieldnames:
        raise ValueError(f"no CSV columns for {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return rows


def integer(row: dict[str, str], name: str) -> int:
    return int(row[name])


def category_summary(site_rows: list[dict[str, str]]) -> list[dict[str, int | str]]:
    columns = {
        "executions": "executions",
        "successfulExecutions": "successful_executions",
        "publishedRows": "published_rows",
        "summedSiteUniqueSourceUrls": "unique_published_urls",
        "completeRows": "complete_rows",
        "pagesFetched": "pages_fetched",
        "pagesFailed": "pages_failed",
        "pagesDiscovered": "pages_discovered",
        "recordsExtracted": "records_extracted",
        "recordPages": "record_pages",
        "navigationPages": "navigation_pages",
        "ignoredPages": "ignored_pages",
        "unmatchedPages": "unmatched_pages",
        "robotsBlocked": "robots_blocked",
    }
    output: list[dict[str, int | str]] = []
    for category in EXPECTED_CATEGORIES:
        selected = [row for row in site_rows if row["study"] == category]
        if len(selected) != EXPECTED_CATEGORIES[category]:
            raise ValueError(f"site count differs for {category}: {len(selected)}")
        result: dict[str, int | str] = {"category": category, "sites": len(selected)}
        for public_name, source_name in columns.items():
            result[public_name] = sum(integer(row, source_name) for row in selected)
        output.append(result)
    return output


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty table: {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run_directories(run_root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for category in EXPECTED_CATEGORIES:
        matches = sorted(run_root.glob(f"*-live-{category}-*"))
        if len(matches) != 1:
            raise ValueError(f"expected one run directory for {category}, got {matches}")
        result[category] = matches[0]
    return result


def verify_source_suite(run_root: Path) -> dict[str, Any]:
    manifest = run_root / "suite-checksums.sha256"
    verified = 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        target = run_root / relative
        if not target.is_file() or sha256(target) != expected:
            raise ValueError(f"source checksum mismatch: {relative}")
        verified += 1
    if verified != 14004:
        raise ValueError(f"source checksum entry count differs: {verified}")
    return {
        "manifest": "original-suite-checksums.sha256",
        "manifestSha256": sha256(manifest),
        "verifiedEntries": verified,
        "verificationStatus": "passed",
    }


def copy_site_definitions(runs: dict[str, Path]) -> dict[str, int]:
    counts = {"manifests": 0, "jobs": 0, "templates": 0, "fields": 0, "schedulerPlans": 0}
    for category, run in runs.items():
        study = run / "artifacts" / "live-study"
        copy_json_redacted(
            study / "resolved-site-manifest.json",
            RELEASE_DIR / "site-definitions" / "manifests" / f"{category}.json",
        )
        counts["manifests"] += 1
        copy_json_redacted(
            study / "native-scheduler-plan.json",
            RELEASE_DIR / "site-definitions" / "scheduler-plans" / f"{category}.json",
        )
        counts["schedulerPlans"] += 1
        for site in sorted((study / "sites").iterdir()):
            workspace = site / "workspace"
            jobs = sorted((workspace / "jobs").glob("*.json"))
            if len(jobs) != 1:
                raise ValueError(f"expected one job for {site.name}")
            copy_json_redacted(
                jobs[0], RELEASE_DIR / "site-definitions" / "jobs" / f"{site.name}.json"
            )
            counts["jobs"] += 1
            for source in sorted((workspace / "templates" / "custom").glob("*.json")):
                copy_json_redacted(
                    source, RELEASE_DIR / "templates" / site.name / source.name
                )
                counts["templates"] += 1
            for source in sorted((workspace / "fields").glob("*.json")):
                copy_json_redacted(
                    source, RELEASE_DIR / "schemas" / site.name / source.name
                )
                counts["fields"] += 1
    return counts


def inventory(run_root: Path, analysis_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    oracle_suffix = (
        "sites/security-oracle/workspace/state/pulsecrawl.sqlite"
    )
    sensitive_analysis = {
        "readable-output/security-advisories/pages.csv",
        "readable-output/security-advisories/pages.parquet",
    }
    for source_name, source_root in (("run", run_root), ("analysis", analysis_root)):
        for path in sorted(item for item in source_root.rglob("*") if item.is_file()):
            relative = path.relative_to(source_root).as_posix()
            transformations: list[str] = []
            if path.suffix in {".json", ".log", ".txt", ".md"}:
                if PRIVATE_ROOT.encode() in path.read_bytes():
                    transformations.append("absolute-workstation-path-redaction")
            if (source_name == "run" and relative.endswith(oracle_suffix)) or (
                source_name == "analysis" and relative in sensitive_analysis
            ):
                transformations.append("transient-oracle-logout-token-redaction")
            rows.append(
                {
                    "source_root": source_name,
                    "relative_path": relative,
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256(path),
                    "publication_transformations": ";".join(transformations),
                }
            )
    return rows


def provenance(runs: dict[str, Path]) -> dict[str, Any]:
    environments = [
        json.loads((run / "environment.json").read_text(encoding="utf-8"))
        for run in runs.values()
    ]
    versions = {item["pulsecrawlDistributionVersion"] for item in environments}
    source_hashes = {item["researchSourceSha256"] for item in environments}
    if versions != {"0.4.0"} or len(source_hashes) != 1:
        raise ValueError("category environments do not share package/source provenance")
    first = environments[0]
    return {
        "pulseCrawl": {
            "distribution": "pulsecrawl",
            "version": "0.4.0",
            "installation": "public index-installed distribution",
            "importKind": "site-packages",
        },
        "researchHarness": {
            "gitBranch": first["gitBranch"],
            "gitCommit": first["gitCommit"],
            "gitDirty": first["gitDirty"],
            "sourceSha256": first["researchSourceSha256"],
            "sourceFiles": first["researchSourceFiles"],
        },
        "runtime": {
            "python": first["python"],
            "platform": first["platform"],
            "architecture": first["machine"],
        },
    }


def write_guides() -> None:
    readme = """# Thesis live-study universe: 72-hour retained run

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

The run used the public index-installed PulseCrawl 0.4.0 distribution. Raw
third-party HTML bodies were not retained.

## Reading order

1. `methodology.md`
2. `category-summary.csv` and `site-summary.csv`
3. `limitations.md`
4. `provenance.json` and `source-verification.json`
5. `RELEASE-FILES.csv` for the complete source inventory
6. The GitHub release assets for workspaces, SQLite state, Parquet, CSV, logs,
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
Release assets have a separate `SHA256SUMS` file and can be checked with the
provided verification script.
"""
    methodology = """# Methodology

The suite scheduled five category workers against a fixed 75-site universe.
Each site received exactly 72 hourly occurrences, a maximum depth of five, up
to 1,500 URL attempts per occurrence, and a 3,300-second execution window.
Workers respected robots.txt and used the longer of the applicable robots
delay or one second between same-origin requests. First observations and
recurring observations were retained without storing raw response bodies.

The public release separates three evidence layers:

1. Compact summaries, configurations, templates, and manifests in Git.
2. Reviewed full-evidence archives attached to the GitHub release.
3. Publication transformation records for private workstation paths and one
   transient third-party logout token. The immutable local originals are not
   modified.

All five categories completed normally. The original suite checksum manifest
was verified before publication, followed by release-asset reconstruction and
published-file checksum verification.
"""
    limitations = """# Limitations and interpretation

Live websites change independently of the crawler, so availability, markup,
robots policies, redirects, and content vary during the observation period.
The retained evidence represents the observed three-day window rather than a
permanent characterization of any source.

## Apple Support template scope

The Apple source used a numeric Apple Support URL scope that also matched
general support articles. This produced confirmed semantic false positives for
that source, including ordinary Apple Vision Pro support instructions labeled
with the study's Apple security-release vendor constant. All Apple evidence is
retained as part of the registered 75-site study.

This finding affects an unqualified claim that every Apple output row is a
security advisory. It does not affect Apple scheduling, robots compliance,
request pacing, execution completion, workspace persistence, dataset
publication, or checksum evidence. Future qualification should derive Apple
detail URLs from the security-release listing and include negative support-page
examples before long-running scheduling.

## Publication transformations

The public evidence mirror replaces absolute workstation path prefixes and a
transient Oracle logout redirect token. These changes remove private or
session-like strings without changing measurements. Every transformed path is
listed in `RELEASE-FILES.csv`; the original source-manifest verification and
the public release checksums are reported separately.
"""
    (RELEASE_DIR / "README.md").write_text(readme, encoding="utf-8")
    (RELEASE_DIR / "methodology.md").write_text(methodology, encoding="utf-8")
    (RELEASE_DIR / "limitations.md").write_text(limitations, encoding="utf-8")


def write_checksums(folder: Path) -> str:
    checksum_path = folder / "checksums.sha256"
    lines = []
    for path in sorted(item for item in folder.rglob("*") if item.is_file()):
        if path == checksum_path:
            continue
        lines.append(f"{sha256(path)}  {path.relative_to(folder).as_posix()}\n")
    checksum_path.write_text("".join(lines), encoding="utf-8")
    return sha256(checksum_path)


def prepare(run_root: Path, analysis_root: Path) -> None:
    global PRIVATE_ROOT
    # The project root is derived at runtime so no private workstation path is
    # embedded in the public preparation tool.
    PRIVATE_ROOT = str(run_root.parents[3])
    if RELEASE_DIR.exists():
        raise FileExistsError(f"release directory already exists: {RELEASE_DIR}")
    RELEASE_DIR.mkdir(parents=True)
    runs = run_directories(run_root)
    source_verification = verify_source_suite(run_root)

    copy_json_redacted(run_root / "suite-plan.json", RELEASE_DIR / "suite-plan.json")
    copy_json_redacted(
        run_root / "suite-completion.json", RELEASE_DIR / "suite-completion.json"
    )
    copy_json_redacted(run_root / "supervisor.json", RELEASE_DIR / "supervisor-final.json")
    shutil.copy2(
        run_root / "suite-checksums.sha256",
        RELEASE_DIR / "original-suite-checksums.sha256",
    )
    write_json(RELEASE_DIR / "source-verification.json", source_verification)
    write_json(RELEASE_DIR / "provenance.json", provenance(runs))
    shutil.copy2(
        analysis_root / "readable-output" / "export-summary.json",
        RELEASE_DIR / "export-summary.json",
    )
    shutil.copy2(
        analysis_root / "live-quality-review.csv",
        RELEASE_DIR / "quality-review-sample.csv",
    )

    readable = analysis_root / "readable-output"
    site_rows = combine_csv(
        [readable / category / "site-summary.csv" for category in EXPECTED_CATEGORIES],
        RELEASE_DIR / "site-summary.csv",
    )
    execution_rows = combine_csv(
        [readable / category / "execution-summary.csv" for category in EXPECTED_CATEGORIES],
        RELEASE_DIR / "execution-summary.csv",
    )
    if len(site_rows) != 75 or len(execution_rows) != 5400:
        raise ValueError("site or execution summary count differs")
    categories = category_summary(site_rows)
    write_rows(RELEASE_DIR / "category-summary.csv", categories)

    totals = {
        "sites": sum(int(row["sites"]) for row in categories),
        "executions": sum(int(row["executions"]) for row in categories),
        "successfulExecutions": sum(int(row["successfulExecutions"]) for row in categories),
        "pagesFetched": sum(int(row["pagesFetched"]) for row in categories),
        "pagesFailed": sum(int(row["pagesFailed"]) for row in categories),
        "robotsBlocked": sum(int(row["robotsBlocked"]) for row in categories),
        "publishedRows": sum(int(row["publishedRows"]) for row in categories),
        "summedSiteUniqueSourceUrls": sum(
            int(row["summedSiteUniqueSourceUrls"]) for row in categories
        ),
    }
    if totals != EXPECTED_TOTALS:
        raise ValueError(f"release totals differ: {totals}")

    definition_counts = copy_site_definitions(runs)
    inventory_rows = inventory(run_root, analysis_root)
    write_rows(RELEASE_DIR / "RELEASE-FILES.csv", inventory_rows)
    transformations: dict[str, int] = {}
    for row in inventory_rows:
        for name in str(row["publication_transformations"]).split(";"):
            if name:
                transformations[name] = transformations.get(name, 0) + 1

    assets = [
        "thesis-72h-run-metadata.tar.zst",
        "thesis-72h-run-financial-news.tar.zst",
        "thesis-72h-run-general-commerce.tar.zst",
        "thesis-72h-run-mexican-newspapers.tar.zst",
        "thesis-72h-run-security-advisories.tar.zst",
        "thesis-72h-run-us-newspapers.tar.zst",
        "thesis-72h-analysis.tar.zst",
        "thesis-72h-ASSET-MANIFEST.json",
        "thesis-72h-PUBLISHED-FILES.sha256",
        "thesis-72h-SHA256SUMS",
    ]
    manifest = {
        "schemaVersion": 1,
        "releaseId": RELEASE_ID,
        "release": "2.0.0",
        "phase": "three-day",
        "status": "prepared-awaiting-asset-verification",
        "sourceRun": run_root.name,
        "analysisRun": analysis_root.name,
        "categories": categories,
        "totals": totals,
        "missedRunCount": 0,
        "schedulerErrors": 0,
        "requiredPackage": "pulsecrawl[workspace]==0.4.0",
        "retainsRawHtml": False,
        "appleEvidenceRetained": True,
        "knownSemanticLimitations": ["apple-support-template-scope"],
        "definitionCounts": definition_counts,
        "sourceFiles": len(inventory_rows),
        "sourceBytes": sum(int(row["size_bytes"]) for row in inventory_rows),
        "publicationTransformations": transformations,
        "expectedAssets": assets,
        "assetChecksums": "populated after package creation",
    }
    write_json(RELEASE_DIR / "release-manifest.json", manifest)
    write_guides()
    checksum_sha = write_checksums(RELEASE_DIR)
    print(
        json.dumps(
            {
                "release": RELEASE_ID,
                "releaseDirectory": str(RELEASE_DIR),
                "repositoryChecksumManifestSha256": checksum_sha,
                "sourceVerification": source_verification,
                "totals": totals,
                "definitions": definition_counts,
                "inventoryFiles": len(inventory_rows),
                "inventoryBytes": sum(int(row["size_bytes"]) for row in inventory_rows),
                "publicationTransformations": transformations,
            },
            indent=2,
            sort_keys=True,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--analysis-root", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.run_root.resolve(), args.analysis_root.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
