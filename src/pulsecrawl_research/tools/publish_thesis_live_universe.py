"""Publish the five-category thesis live-study universe.

The source suite remains immutable in the private research workspace.  This
tool publishes only the reviewer-readable, site-filtered evidence selected for
the thesis: Mexican newspapers, United States newspapers, financial news,
general commerce without Alo Yoga, and security advisories.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pacsv
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[3]
RELEASE = "1.0.0"
RELEASE_ID = "thesis-live-universe-v1.0.0"
RUN_FOLDER = "thesis-universe-2h-2026-11-02"
CATEGORIES = {
    "financial-news": "Financial and stock news",
    "general-commerce": "General commerce",
    "mexican-newspapers": "Mexican newspapers",
    "security-advisories": "Security advisories",
    "us-newspapers": "United States newspapers",
}
THESIS_COMMERCE_SITES = {
    "commerce-dsw",
    "commerce-fashion-nova",
    "commerce-gap",
    "commerce-nike",
    "commerce-puma",
    "commerce-quince",
    "commerce-spanx",
    "commerce-ulta-beauty",
}
TABLES = (
    "execution-summary",
    "pages",
    "records",
    "site-summary",
    "suppressed-page-samples",
)
SENSITIVE_MARKERS = (
    "/Users/",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected a JSON object: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_checksums(folder: Path) -> str:
    entries = []
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or path.name == "checksums.sha256":
            continue
        entries.append(f"{sha256(path)}  {path.relative_to(folder).as_posix()}")
    checksum_path = folder / "checksums.sha256"
    checksum_path.write_text("\n".join(entries) + "\n", encoding="utf-8")
    return sha256(checksum_path)


def verify_checksums(folder: Path, filename: str = "checksums.sha256") -> str:
    checksum_path = folder / filename
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        target = folder / relative
        if not target.is_file() or sha256(target) != digest:
            raise ValueError(f"source checksum differs: {target}")
    return sha256(checksum_path)


def source_runs(source_root: Path) -> dict[str, Path]:
    runs: dict[str, Path] = {}
    for path in source_root.iterdir():
        summary_path = path / "summary.json"
        if not path.is_dir() or not summary_path.is_file():
            continue
        summary = read_json(summary_path)
        study = summary.get("results", {}).get("study")
        if study:
            runs[str(study)] = path
    return runs


def filtered(table: pa.Table) -> pa.Table:
    if "site_id" not in table.column_names:
        return table
    site_ids = {str(value) for value in table["site_id"].to_pylist() if value is not None}
    if not any(site_id.startswith("commerce-") for site_id in site_ids):
        return table
    keep = pc.is_in(table["site_id"], value_set=pa.array(sorted(THESIS_COMMERCE_SITES)))
    return table.filter(keep)


def scan_table(table: pa.Table) -> None:
    for column in table.column_names:
        if not pa.types.is_string(table.schema.field(column).type):
            continue
        for value in table[column].to_pylist():
            if value is None:
                continue
            lowered = value.lower()
            for marker in SENSITIVE_MARKERS:
                matched = marker in value if marker == "/Users/" else marker.lower() in lowered
                if matched:
                    raise ValueError(f"sensitive marker found in {column}: {marker}")


def write_table_pair(source: Path, destination: Path) -> dict[str, Any]:
    table = filtered(pq.read_table(source))
    scan_table(table)
    destination.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, destination.with_suffix(".parquet"), compression="zstd")
    pacsv.write_csv(table, destination.with_suffix(".csv"))
    return {
        "rows": table.num_rows,
        "columns": table.num_columns,
        "csv": destination.with_suffix(".csv").name,
        "csvSha256": sha256(destination.with_suffix(".csv")),
        "parquet": destination.with_suffix(".parquet").name,
        "parquetSha256": sha256(destination.with_suffix(".parquet")),
    }


def int_value(value: Any) -> int:
    return int(float(value or 0))


def table_rows(path: Path) -> list[dict[str, Any]]:
    return filtered(pq.read_table(path)).to_pylist()


def filter_site_object(value: dict[str, Any]) -> dict[str, Any]:
    result = dict(value)
    result["sites"] = [
        {
            key: item
            for key, item in row.items()
            if not key.startswith("qualification") and not key.startswith("retained")
        }
        for row in value.get("sites", [])
        if not str(row.get("id", row.get("siteId"))).startswith("commerce-")
        or row.get("id", row.get("siteId")) in THESIS_COMMERCE_SITES
    ]
    return result


def category_summary(category_id: str, site_rows: list[dict[str, Any]]) -> dict[str, Any]:
    fields = (
        "executions",
        "successful_executions",
        "published_rows",
        "unique_published_urls",
        "complete_rows",
        "pages_fetched",
        "pages_failed",
        "pages_discovered",
        "records_extracted",
        "record_pages",
        "navigation_pages",
        "ignored_pages",
        "unmatched_pages",
        "robots_blocked",
    )
    totals = {field: sum(int_value(row.get(field)) for row in site_rows) for field in fields}
    return {
        "categoryId": category_id,
        "categoryName": CATEGORIES[category_id],
        "sites": len(site_rows),
        **totals,
    }


def publish_category(
    category_id: str,
    source_analysis: Path,
    source_run: Path,
    suite_checksum_sha256: str,
) -> dict[str, Any]:
    source_checksum_sha256 = verify_checksums(source_run)
    destination = ROOT / "experiments/live" / category_id / "runs" / RUN_FOLDER
    if destination.exists():
        raise FileExistsError(destination)
    readable = destination / "readable-output"
    readable.mkdir(parents=True)

    output_index = {
        stem: write_table_pair(
            source_analysis / "readable-output" / category_id / f"{stem}.parquet",
            readable / stem,
        )
        for stem in TABLES
    }
    for stem in ("records", "pages"):
        preview_path = readable / f"{stem}-preview.csv"
        preview = filtered(
            pq.read_table(
                source_analysis / "readable-output" / category_id / f"{stem}.parquet"
            )
        ).slice(0, 200)
        pacsv.write_csv(preview, preview_path)
        output_index[stem]["previewCsv"] = preview_path.name
        output_index[stem]["previewRows"] = preview.num_rows
        output_index[stem]["previewCsvSha256"] = sha256(preview_path)
    site_rows = table_rows(
        source_analysis / "readable-output" / category_id / "site-summary.parquet"
    )
    summary = category_summary(category_id, site_rows)
    summary.update(
        {
            "runId": str(site_rows[0]["run_id"]),
            "phase": "two-hour",
            "plannedCycles": 4,
            "completedCycles": 4,
            "intervalMinutes": 30,
            "maxUrlsPerSitePerExecution": 1500,
            "maxDepth": 5,
            "maxDurationSeconds": 1680,
            "minimumOriginDelaySeconds": 0.5,
            "requiredPackageVersion": "0.4.0",
            "status": "completed",
        }
    )
    write_json(destination / "summary.json", summary)
    write_json(readable / "output-index.json", output_index)

    experiment = read_json(source_run / "experiment.json")
    experiment["parameters"]["manifest"] = (
        f"experiments/live/{category_id}/input/sites.json"
    )
    experiment["parameters"]["phase"] = "two-hour"
    experiment["parameters"]["phases"] = {
        "two-hour": {
            "executions": 4,
            "intervalMinutes": 30,
            "maxUrlsPerSitePerExecution": 1500,
            "maxDepth": 5,
            "minimumOriginDelaySeconds": 0.5,
            "overrideSiteLimits": True,
            "nativeScheduler": True,
            "startAtNextMinute": True,
            "maxDurationSeconds": 1680,
            "schedulerPollSeconds": 5,
            "requiredPackageVersion": "0.4.0",
        }
    }
    write_json(destination / "resolved-experiment.json", experiment)

    resolved = filter_site_object(
        read_json(source_run / "artifacts/live-study/resolved-site-manifest.json")
    )
    access = filter_site_object(
        read_json(source_run / "artifacts/live-study/access-review.json")
    )
    write_json(destination / "resolved-site-manifest.json", resolved)
    write_json(
        ROOT / "experiments/live" / category_id / "input/sites.json",
        resolved,
    )
    write_json(destination / "access-review.json", access)
    write_json(
        destination / "source-provenance.json",
        {
            "sourceRunId": source_run.name,
            "sourceRunChecksumsSha256": source_checksum_sha256,
            "sourceSuiteChecksumsSha256": suite_checksum_sha256,
            "sourceResponseBodiesRetained": False,
            "publishedLocalState": False,
            "publishedProcessIdentifiers": False,
            "selection": "five-category thesis live universe",
        },
    )
    write_json(
        readable / "schema.json",
        {
            stem: [
                {"name": field.name, "type": str(field.type)}
                for field in filtered(
                    pq.read_table(
                        source_analysis
                        / "readable-output"
                        / category_id
                        / f"{stem}.parquet"
                    )
                ).schema
            ]
            for stem in TABLES
        },
    )

    (readable / "README.md").write_text(
        "# Readable evidence\n\n"
        "Every table is published as matching CSV and Parquet files. "
        "`records` contains target records, `pages` contains the complete URL-level "
        "crawl trace, `execution-summary` and `site-summary` explain the run totals, "
        "and `suppressed-page-samples` shows navigation or ignored examples. "
        "The `records-preview.csv` and `pages-preview.csv` files contain the "
        "first 200 rows for direct browser inspection; the unsuffixed files are "
        "the complete tables.\n",
        encoding="utf-8",
    )
    (destination / "README.md").write_text(
        f"# {CATEGORIES[category_id]}: two-hour thesis-universe run\n\n"
        "This evidence contains four scheduled site executions at 30-minute "
        "intervals. Each execution allowed up to 1,500 URLs, crawl depth five, "
        "and a 1,680-second execution window. The run used the public PulseCrawl "
        "0.4.0 package and the longer of the robots delay or 0.5 seconds between "
        "same-origin requests.\n\n"
        f"- Sites: {summary['sites']}\n"
        f"- Successful site executions: {summary['successful_executions']}/"
        f"{summary['executions']}\n"
        f"- Pages fetched: {summary['pages_fetched']}\n"
        f"- Published rows: {summary['published_rows']}\n"
        f"- Unique target-record URLs: {summary['unique_published_urls']}\n"
        f"- Complete rows: {summary['complete_rows']}\n\n"
        "Start with `readable-output/site-summary.csv`, then inspect "
        "`readable-output/records-preview.csv` and "
        "`readable-output/pages-preview.csv`. The unsuffixed CSV and Parquet "
        "files contain the complete tables.\n",
        encoding="utf-8",
    )
    summary["path"] = destination.relative_to(ROOT).as_posix()
    summary["checksumsSha256"] = write_checksums(destination)
    summary["recordsCsv"] = f"{summary['path']}/readable-output/records.csv"
    summary["recordsParquet"] = f"{summary['path']}/readable-output/records.parquet"
    return summary


def publish(source_root: Path, analysis_root: Path) -> dict[str, Any]:
    suite_checksum_sha256 = verify_checksums(source_root, "suite-checksums.sha256")
    runs = source_runs(source_root)
    missing = set(CATEGORIES).difference(runs)
    if missing:
        raise ValueError(f"missing completed source runs: {sorted(missing)}")

    rows = [
        publish_category(
            category_id,
            analysis_root,
            runs[category_id],
            suite_checksum_sha256,
        )
        for category_id in CATEGORIES
    ]
    release = ROOT / "experiments/releases" / RELEASE_ID
    if release.exists():
        raise FileExistsError(release)
    release.mkdir(parents=True)

    site_tables = [
        filtered(
            pq.read_table(
                analysis_root
                / "readable-output"
                / category_id
                / "site-summary.parquet"
            )
        )
        for category_id in CATEGORIES
    ]
    site_table = pa.concat_tables(site_tables, promote_options="default")
    pq.write_table(site_table, release / "site-summary.parquet", compression="zstd")
    pacsv.write_csv(site_table, release / "site-summary.csv")

    suite_table = pa.Table.from_pylist(rows)
    pq.write_table(suite_table, release / "suite-summary.parquet", compression="zstd")
    pacsv.write_csv(suite_table, release / "suite-summary.csv")

    total_fields = {
        "categories": len(rows),
        "sites": sum(row["sites"] for row in rows),
        "siteExecutions": sum(row["executions"] for row in rows),
        "successfulSiteExecutions": sum(row["successful_executions"] for row in rows),
        "pagesDiscovered": sum(row["pages_discovered"] for row in rows),
        "pagesFetched": sum(row["pages_fetched"] for row in rows),
        "pagesFailed": sum(row["pages_failed"] for row in rows),
        "publishedRows": sum(row["published_rows"] for row in rows),
        "uniqueRecordUrls": sum(row["unique_published_urls"] for row in rows),
        "completeRows": sum(row["complete_rows"] for row in rows),
        "unmatchedPages": sum(row["unmatched_pages"] for row in rows),
        "robotsBlocked": sum(row["robots_blocked"] for row in rows),
    }
    manifest = {
        "schemaVersion": 1,
        "release": RELEASE,
        "releaseId": RELEASE_ID,
        "study": "thesis-live-universe",
        "phase": "two-hour",
        "status": "completed-reviewed-and-published",
        "categories": rows,
        "totals": total_fields,
        "protocol": {
            "cyclesPerSite": 4,
            "intervalMinutes": 30,
            "maxUrlsPerSitePerExecution": 1500,
            "maxDepth": 5,
            "maxDurationSeconds": 1680,
            "minimumOriginDelaySeconds": 0.5,
            "requiredPackageVersion": "0.4.0",
        },
        "publicationBoundary": {
            "responseBodiesPublished": False,
            "localSqlitePublished": False,
            "processIdentifiersPublished": False,
            "workstationPathsPublished": False,
            "csvPublished": True,
            "parquetPublished": True,
        },
        "selectionBoundary": (
            "This release is the five-category, 75-site analytical universe used "
            "for the thesis. The immutable source suite was broader; categories "
            "outside this analytical universe are not published or used in the "
            "release totals."
        ),
    }
    write_json(release / "release-manifest.json", manifest)

    table_rows = "\n".join(
        f"| [{row['categoryName']}](../../live/{row['categoryId']}/runs/{RUN_FOLDER}/) "
        f"| {row['sites']} | {row['executions']} | {row['pages_fetched']} | "
        f"{row['published_rows']} | {row['unique_published_urls']} |"
        for row in rows
    )
    (release / "README.md").write_text(
        f"# Thesis live-study universe v{RELEASE}\n\n"
        "This is the reviewer-readable release used for the thesis live analysis. "
        "It contains five categories, 75 websites, and four scheduled executions "
        "per website. The source suite remains immutable; this release publishes "
        "only the defined thesis analytical universe.\n\n"
        "| Category | Sites | Executions | Pages fetched | Published rows | Unique record URLs |\n"
        "|---|---:|---:|---:|---:|---:|\n"
        f"{table_rows}\n"
        f"| **Total** | **{total_fields['sites']}** | **{total_fields['siteExecutions']}** "
        f"| **{total_fields['pagesFetched']}** | **{total_fields['publishedRows']}** "
        f"| **{total_fields['uniqueRecordUrls']}** |\n\n"
        "Open `suite-summary.csv` for category totals and `site-summary.csv` for "
        "website-level measurements. Each category link contains matching CSV and "
        "Parquet files for records, pages, executions, sites, and suppressed-page samples.\n",
        encoding="utf-8",
    )
    write_checksums(release)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--analysis-root", type=Path, required=True)
    args = parser.parse_args()
    result = publish(args.source_root, args.analysis_root)
    print(json.dumps(result["totals"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
