"""Verify the public datasets, controlled runs, and thesis live release."""

from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import struct
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
LIVE_RELEASE = ROOT / "experiments/releases/thesis-live-universe-v1.0.0"
EXPECTED_DATASETS = {"fixed-html": 60, "site-pattern-html": 100, "commerce-html": 20}
EXPECTED_FAMILIES = {"policy-and-recovery", "template-extraction", "versioned-datasets"}
EXPECTED_LIVE_CATEGORIES = {
    "financial-news": 20,
    "general-commerce": 8,
    "mexican-newspapers": 19,
    "security-advisories": 8,
    "us-newspapers": 20,
}
EXPECTED_LIVE_TOTALS = {
    "categories": 5,
    "sites": 75,
    "siteExecutions": 300,
    "successfulSiteExecutions": 300,
    "pagesDiscovered": 444046,
    "pagesFetched": 374395,
    "pagesFailed": 4405,
    "publishedRows": 68367,
    "uniqueRecordUrls": 53381,
    "completeRows": 68367,
    "unmatchedPages": 527,
    "robotsBlocked": 1600,
}
LIVE_TABLES = {
    "execution-summary",
    "pages",
    "records",
    "site-summary",
    "suppressed-page-samples",
}
SHA256_PATTERN = re.compile(r"[a-f0-9]{64}")


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected an object in {path.relative_to(ROOT)}")
    return value


def verify_manifests() -> dict[str, int]:
    counts: dict[str, int] = {}
    for name, expected in EXPECTED_DATASETS.items():
        folder = ROOT / "datasets" / name
        entries = [
            json.loads(line)
            for line in (folder / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        if len(entries) != expected or len({row["id"] for row in entries}) != expected:
            raise ValueError(f"invalid manifest count or IDs: {name}")
        listed: set[Path] = set()
        for row in entries:
            relative = Path(row["path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"unsafe manifest path: {name}/{relative}")
            target = folder / relative
            if hashlib.sha256(target.read_bytes()).hexdigest() != row["sha256"]:
                raise ValueError(f"HTML checksum mismatch: {name}/{relative}")
            listed.add(target)
        if listed != set(folder.rglob("*.html")):
            raise ValueError(f"unlisted HTML: {name}")
        counts[name] = len(entries)
    return counts


def verify_research_metadata() -> dict[str, object]:
    compatibility = _json(ROOT / "docs/environment/compatibility.json")
    catalog = _json(ROOT / "experiments/catalog.json")
    experiments = catalog["experiments"]
    identifiers = [entry["id"] for entry in experiments]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("controlled experiment identifiers must be unique")
    if any(not re.fullmatch(r"[a-z0-9][a-z0-9-]+", value) for value in identifiers):
        raise ValueError("controlled experiment identifiers must be readable slugs")
    families = {entry["family"] for entry in experiments}
    if families != EXPECTED_FAMILIES:
        raise ValueError(f"unexpected experiment families: {sorted(families)}")
    version = compatibility["pulsecrawl"]
    requirement = f"pulsecrawl[workspace]=={version}"
    requirements = (ROOT / "docs/environment/requirements.txt").read_text().splitlines()
    if requirement not in requirements or catalog["package"] != requirement:
        raise ValueError("PulseCrawl package pins are inconsistent")
    installed = importlib.metadata.version("pulsecrawl")
    if installed != version:
        raise ValueError(f"installed pulsecrawl {installed} does not match {version}")

    live = _json(ROOT / "experiments/live/catalog.json")
    observed = {row["id"]: row["sites"] for row in live["categories"]}
    if observed != EXPECTED_LIVE_CATEGORIES:
        raise ValueError(f"unexpected live-study universe: {observed}")
    for category_id, expected_sites in observed.items():
        folder = ROOT / "experiments/live" / category_id
        sites = _json(folder / "input/sites.json")["sites"]
        if len(sites) != expected_sites:
            raise ValueError(f"live site count differs: {category_id}")
        if not (folder / "README.md").is_file() or not (folder / "experiment.yaml").is_file():
            raise ValueError(f"live category lacks a reader guide: {category_id}")
    return {
        "controlledExperiments": len(experiments),
        "families": sorted(families),
        "liveCategories": len(observed),
        "liveWebsites": sum(observed.values()),
        "pulsecrawl": installed,
    }


def verify_directory_checksums(folder: Path) -> str:
    checksum_path = folder / "checksums.sha256"
    if not checksum_path.is_file():
        raise ValueError(f"missing checksum manifest: {folder.relative_to(ROOT)}")
    listed: set[Path] = set()
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        if not SHA256_PATTERN.fullmatch(digest):
            raise ValueError(f"invalid checksum in {checksum_path.relative_to(ROOT)}")
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(f"unsafe checksum path in {checksum_path.relative_to(ROOT)}")
        target = folder / relative_path
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError(f"evidence checksum mismatch: {target.relative_to(ROOT)}")
        listed.add(target)
    actual = {path for path in folder.rglob("*") if path.is_file() and path != checksum_path}
    unlisted = actual - listed
    if listed - actual or any(path.name != "README.md" for path in unlisted):
        raise ValueError(f"checksum coverage mismatch: {folder.relative_to(ROOT)}")
    return hashlib.sha256(checksum_path.read_bytes()).hexdigest()


def verify_controlled_evidence() -> dict[str, int]:
    executions = 0
    experiments = 0
    for experiment in sorted((ROOT / "experiments/controlled").iterdir()):
        if not experiment.is_dir():
            continue
        runs = sorted((experiment / "runs").glob("run-*"))
        if not runs:
            continue
        experiments += 1
        if not (experiment / "README.md").is_file():
            raise ValueError(f"controlled experiment lacks README: {experiment.name}")
        for run in runs:
            manifest = _json(run / "execution-manifest.json")
            resolved = _json(run / "resolved-experiment.json")
            if manifest["experimentId"] != experiment.name or manifest["status"] != "completed":
                raise ValueError(f"invalid controlled execution: {run.relative_to(ROOT)}")
            if not (run / "README.md").is_file() or not (run / "measurements.csv").is_file():
                raise ValueError(f"controlled execution lacks readable evidence: {run.relative_to(ROOT)}")
            with (run / "measurements.csv").open(encoding="utf-8", newline="") as handle:
                if next(csv.reader(handle), []) != ["measurement", "value", "type"]:
                    raise ValueError(f"invalid readable measurements: {run.relative_to(ROOT)}")
            if resolved.get("family") == "versioned-datasets":
                readable = run / "readable-output"
                csv_files = list(readable.glob("records*.csv"))
                parquet_files = list(readable.glob("records*.parquet"))
                if len(csv_files) != 1 or len(parquet_files) != 1:
                    raise ValueError(f"dataset execution lacks CSV/Parquet companions: {run.relative_to(ROOT)}")
                import pyarrow.parquet as pq

                with csv_files[0].open(encoding="utf-8", newline="") as handle:
                    csv_rows = sum(1 for _ in csv.reader(handle)) - 1
                if csv_rows != pq.read_metadata(parquet_files[0]).num_rows:
                    raise ValueError(f"dataset CSV/Parquet row counts differ: {run.relative_to(ROOT)}")
            verify_directory_checksums(run)
            executions += 1
    if executions != 116 or experiments != 27:
        raise ValueError(f"controlled evidence count differs: {executions}/{experiments}")
    return {"controlledExecutions": executions, "controlledExperimentsWithEvidence": experiments}


def verify_live_release() -> dict[str, int | str]:
    import pyarrow.parquet as pq

    manifest = _json(LIVE_RELEASE / "release-manifest.json")
    if (
        manifest.get("release") != "1.0.0"
        or manifest.get("phase") != "two-hour"
        or manifest.get("status") != "completed-reviewed-and-published"
    ):
        raise ValueError("live release identity or status differs")
    if manifest.get("totals") != EXPECTED_LIVE_TOTALS:
        raise ValueError("live release totals differ")
    categories = manifest.get("categories", [])
    observed = {row["categoryId"]: row["sites"] for row in categories}
    if observed != EXPECTED_LIVE_CATEGORIES:
        raise ValueError(f"live release categories differ: {observed}")

    measured_sites = measured_executions = measured_rows = measured_fetches = 0
    for row in categories:
        folder = ROOT / row["path"]
        if not folder.resolve().is_relative_to(ROOT) or not folder.is_dir():
            raise ValueError(f"unsafe live evidence path: {row['path']}")
        if verify_directory_checksums(folder) != row["checksumsSha256"]:
            raise ValueError(f"live checksum differs: {row['categoryId']}")
        summary = _json(folder / "summary.json")
        if summary.get("completedCycles") != 4 or summary.get("requiredPackageVersion") != "0.4.0":
            raise ValueError(f"live protocol differs: {row['categoryId']}")
        if _json(folder / "access-review.json").get("retainsHtml") is not False:
            raise ValueError(f"live publication includes HTML: {row['categoryId']}")
        readable = folder / "readable-output"
        output_index = _json(readable / "output-index.json")
        if set(output_index) != LIVE_TABLES:
            raise ValueError(f"live output tables differ: {row['categoryId']}")
        for stem, evidence in output_index.items():
            csv_path = readable / evidence["csv"]
            parquet_path = readable / evidence["parquet"]
            with csv_path.open(encoding="utf-8", newline="") as handle:
                csv_rows = sum(1 for _ in csv.reader(handle)) - 1
            parquet_rows = pq.read_metadata(parquet_path).num_rows
            if csv_rows != parquet_rows or csv_rows != evidence["rows"]:
                raise ValueError(f"live CSV/Parquet rows differ: {row['categoryId']}/{stem}")
            if hashlib.sha256(csv_path.read_bytes()).hexdigest() != evidence["csvSha256"]:
                raise ValueError(f"live CSV checksum differs: {row['categoryId']}/{stem}")
            if hashlib.sha256(parquet_path.read_bytes()).hexdigest() != evidence["parquetSha256"]:
                raise ValueError(f"live Parquet checksum differs: {row['categoryId']}/{stem}")
            if evidence.get("previewCsv"):
                preview_path = readable / evidence["previewCsv"]
                with preview_path.open(encoding="utf-8", newline="") as handle:
                    preview_rows = sum(1 for _ in csv.reader(handle)) - 1
                if preview_rows != evidence["previewRows"]:
                    raise ValueError(f"live preview rows differ: {row['categoryId']}/{stem}")
                if hashlib.sha256(preview_path.read_bytes()).hexdigest() != evidence["previewCsvSha256"]:
                    raise ValueError(f"live preview checksum differs: {row['categoryId']}/{stem}")
        measured_sites += row["sites"]
        measured_executions += row["successful_executions"]
        measured_rows += row["published_rows"]
        measured_fetches += row["pages_fetched"]
    if (measured_sites, measured_executions, measured_rows, measured_fetches) != (75, 300, 68367, 374395):
        raise ValueError("live category totals do not reconcile")
    verify_directory_checksums(LIVE_RELEASE)
    return {
        "release": manifest["release"],
        "categories": len(categories),
        "sites": measured_sites,
        "siteExecutions": measured_executions,
        "pagesFetched": measured_fetches,
        "publishedRows": measured_rows,
    }


def verify_documentation() -> dict[str, int]:
    required = {
        "README.md",
        "docs/README.md",
        "datasets/README.md",
        "experiments/README.md",
        "experiments/controlled/INDEX.md",
        "experiments/live/README.md",
        "experiments/releases/README.md",
        "runners/README.md",
        "src/pulsecrawl_research/README.md",
    }
    for relative in required:
        if not (ROOT / relative).is_file():
            raise ValueError(f"missing reader guide: {relative}")
    pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    checked = 0
    for path in ROOT.rglob("*.md"):
        if any(part in {".git", ".venv"} for part in path.relative_to(ROOT).parts):
            continue
        for raw in pattern.findall(path.read_text(encoding="utf-8")):
            target = raw.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            destination = (path.parent / target).resolve()
            if not destination.is_relative_to(ROOT) or not destination.exists():
                raise ValueError(f"broken local link in {path.relative_to(ROOT)}: {target}")
            checked += 1
    images = sorted((ROOT / "docs/images").glob("*.png"))
    for path in images:
        body = path.read_bytes()
        length = struct.unpack(">I", body[8:12])[0]
        width, height = struct.unpack(">II", body[16:24])
        if body[:8] != b"\x89PNG\r\n\x1a\n" or body[12:16] != b"IHDR" or length != 13 or (width, height) != (1000, 400):
            raise ValueError(f"invalid documentation image: {path.name}")
    return {"readerGuides": len(required), "localLinks": checked, "syntheticImages": len(images)}


def publication_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and not any(part in {".git", ".venv", "__pycache__"} for part in path.relative_to(ROOT).parts)
    )


def privacy_scan(deny: list[str] | None = None) -> None:
    rules = {
        "absolute home path": re.compile(r"/Users/[A-Za-z0-9_.-]+|[A-Za-z]:\\Users\\"),
        "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        "credential": re.compile(r"\b(?:ghp|gho|github_pat)_[A-Za-z0-9_]{20,}\b"),
    }
    for index, value in enumerate(deny or []):
        rules[f"reviewer deny rule {index + 1}"] = re.compile(value, re.I)
    for path in publication_files():
        relative = path.relative_to(ROOT).as_posix()
        try:
            body = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in rules.items():
            for match in pattern.finditer(relative + "\n" + body):
                raise ValueError(f"publication scan failed ({label}) in {relative}")


def main() -> int:
    result = {
        "datasets": verify_manifests(),
        "metadata": verify_research_metadata(),
        "controlledEvidence": verify_controlled_evidence(),
        "liveRelease": verify_live_release(),
        "documentation": verify_documentation(),
    }
    privacy_scan()
    result["publicationScan"] = "passed"
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
