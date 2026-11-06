"""Package the complete 72-hour thesis evidence as audited release assets.

The immutable run and analysis directories are read-only inputs.  Files are
streamed into deterministic tar+zstd archives, with narrowly scoped public
release transformations applied in a temporary overlay:

* absolute workstation paths become ``${PULSECRAWL_RESEARCH_ROOT}``;
* transient Oracle logout credentials are replaced with a fixed marker.

The resulting asset manifest records every archive, part, member count, byte
count, checksum, and transformation.  The published-file checksum list covers
the extracted public form of all source files.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import tarfile
import tempfile
from typing import BinaryIO, Iterable


RELEASE_ID = "thesis-live-universe-72h-v2.0.0"
PRIVATE_ROOT = b""
PUBLIC_ROOT = b"${PULSECRAWL_RESEARCH_ROOT}"
REDACTED_TOKEN = "<redacted-transient-session-token>"
MAX_ASSET_BYTES = 1_900_000_000
READ_SIZE = 1024 * 1024
EXPECTED_FILES = 14_215
EXPECTED_BYTES = 9_959_537_072
EXPECTED_TRANSFORMATIONS = {
    "absolute-workstation-path-redaction": 32,
    "transient-oracle-logout-token-redaction": 3,
}
EXPECTED_CATEGORIES = {
    "financial-news",
    "general-commerce",
    "mexican-newspapers",
    "security-advisories",
    "us-newspapers",
}

# This expression intentionally targets only the Oracle identity logout URL.
# It does not redact ordinary public CDN parameters such as image access tokens.
ORACLE_LOGOUT_TOKEN = re.compile(
    rb"(https://login-ext\.identity\.oraclecloud\.com/oauth2/v1/userlogout\?"
    rb"[^\s,\"']*?[?&]token=)([^&\s,\"']+)",
    re.IGNORECASE,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(READ_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class HashingReader:
    """File-like reader that computes SHA-256 while tarfile consumes it."""

    def __init__(self, handle: BinaryIO) -> None:
        self.handle = handle
        self.digest = hashlib.sha256()

    def read(self, size: int = -1) -> bytes:
        value = self.handle.read(size)
        self.digest.update(value)
        return value

    def hexdigest(self) -> str:
        return self.digest.hexdigest()


def redact_oracle_token_bytes(value: bytes) -> tuple[bytes, int]:
    count = 0

    def replacement(match: re.Match[bytes]) -> bytes:
        nonlocal count
        count += 1
        return match.group(1) + REDACTED_TOKEN.encode("ascii")

    return ORACLE_LOGOUT_TOKEN.sub(replacement, value), count


def has_unredacted_oracle_token(value: bytes) -> bool:
    marker = REDACTED_TOKEN.encode("ascii")
    # Binary containers may place non-text page bytes immediately after the
    # marker, so prefix recognition is required for whole-file scans.
    return any(
        not match.group(2).startswith(marker)
        for match in ORACLE_LOGOUT_TOKEN.finditer(value)
    )


def load_inventory(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != EXPECTED_FILES:
        raise ValueError(f"expected {EXPECTED_FILES} inventory rows, got {len(rows)}")
    total_bytes = sum(int(row["size_bytes"]) for row in rows)
    if total_bytes != EXPECTED_BYTES:
        raise ValueError(f"expected {EXPECTED_BYTES} source bytes, got {total_bytes}")
    observed: dict[str, int] = {}
    for row in rows:
        for name in filter(None, row["publication_transformations"].split(";")):
            observed[name] = observed.get(name, 0) + 1
    if observed != EXPECTED_TRANSFORMATIONS:
        raise ValueError(f"unexpected transformation inventory: {observed}")
    return rows


def source_path(row: dict[str, str], run_root: Path, analysis_root: Path) -> Path:
    root = run_root if row["source_root"] == "run" else analysis_root
    path = root / row["relative_path"]
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def assert_original_hash(path: Path, expected: str) -> None:
    actual = sha256(path)
    if actual != expected:
        raise ValueError(f"source changed after inventory: {path}")


def create_text_overlay(source: Path, destination: Path, expected_hash: str) -> None:
    original = source.read_bytes()
    actual = hashlib.sha256(original).hexdigest()
    if actual != expected_hash:
        raise ValueError(f"source changed after inventory: {source}")
    if PRIVATE_ROOT not in original:
        raise ValueError(f"expected private root was not found: {source}")
    public = original.replace(PRIVATE_ROOT, PUBLIC_ROOT)
    if PRIVATE_ROOT in public:
        raise ValueError(f"private root remains after transformation: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(public)


def create_csv_overlay(source: Path, destination: Path, expected_hash: str) -> None:
    original = source.read_bytes()
    actual = hashlib.sha256(original).hexdigest()
    if actual != expected_hash:
        raise ValueError(f"source changed after inventory: {source}")
    public, count = redact_oracle_token_bytes(original)
    if count != 72:
        raise ValueError(f"expected 72 Oracle CSV token occurrences, got {count}")
    if has_unredacted_oracle_token(public):
        raise ValueError("Oracle token remains in transformed CSV")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(public)


def create_parquet_overlay(source: Path, destination: Path, expected_hash: str) -> None:
    assert_original_hash(source, expected_hash)
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq

    table = pq.read_table(source)
    if "error" not in table.column_names:
        raise ValueError("security pages parquet has no error column")
    errors = table["error"]
    pattern = ORACLE_LOGOUT_TOKEN.pattern.decode("ascii")
    replacement = rf"\1{REDACTED_TOKEN}"
    matches = pc.match_substring_regex(errors, pattern=pattern)
    count = pc.sum(pc.cast(pc.fill_null(matches, False), pa.int64())).as_py()
    if count != 72:
        raise ValueError(f"expected 72 Oracle parquet token rows, got {count}")
    transformed = pc.replace_substring_regex(errors, pattern=pattern, replacement=replacement)
    table = table.set_column(table.schema.get_field_index("error"), "error", transformed)
    destination.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        table,
        destination,
        compression="zstd",
        use_dictionary=True,
        write_statistics=True,
        row_group_size=64 * 1024,
    )
    check = pq.read_table(destination, columns=["error"])["error"]
    if any(
        value is not None and has_unredacted_oracle_token(value.encode("utf-8"))
        for value in check.to_pylist()
    ):
        raise ValueError("Oracle token remains in transformed parquet")


def create_sqlite_overlay(source: Path, destination: Path, expected_hash: str) -> None:
    assert_original_hash(source, expected_hash)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    connection = sqlite3.connect(destination)
    try:
        rows = connection.execute(
            "SELECT rowid, error FROM visited WHERE error LIKE '%token=%'"
        ).fetchall()
        updates: list[tuple[str, int]] = []
        replacements = 0
        for rowid, error in rows:
            public, count = redact_oracle_token_bytes(error.encode("utf-8"))
            if count:
                updates.append((public.decode("utf-8"), rowid))
                replacements += count
        if replacements != 72:
            raise ValueError(f"expected 72 Oracle SQLite token rows, got {replacements}")
        connection.executemany("UPDATE visited SET error = ? WHERE rowid = ?", updates)
        connection.commit()
        connection.execute("VACUUM")
        connection.commit()
        remaining = connection.execute(
            "SELECT error FROM visited WHERE error LIKE '%token=%'"
        ).fetchall()
        if any(
            has_unredacted_oracle_token(value.encode("utf-8"))
            for (value,) in remaining
        ):
            raise ValueError("Oracle token remains in transformed SQLite rows")
    finally:
        connection.close()
    if has_unredacted_oracle_token(destination.read_bytes()):
        raise ValueError("Oracle token remains in transformed SQLite file pages")


def build_overlays(
    rows: list[dict[str, str]],
    run_root: Path,
    analysis_root: Path,
    overlay_root: Path,
) -> dict[tuple[str, str], Path]:
    overlays: dict[tuple[str, str], Path] = {}
    for row in rows:
        transformations = set(filter(None, row["publication_transformations"].split(";")))
        if not transformations:
            continue
        source = source_path(row, run_root, analysis_root)
        destination = overlay_root / row["source_root"] / row["relative_path"]
        key = (row["source_root"], row["relative_path"])
        if transformations == {"absolute-workstation-path-redaction"}:
            create_text_overlay(source, destination, row["sha256"])
        elif transformations == {"transient-oracle-logout-token-redaction"}:
            if source.suffix == ".csv":
                create_csv_overlay(source, destination, row["sha256"])
            elif source.suffix == ".parquet":
                create_parquet_overlay(source, destination, row["sha256"])
            elif source.suffix == ".sqlite":
                create_sqlite_overlay(source, destination, row["sha256"])
            else:
                raise ValueError(f"unsupported credential-bearing file: {source}")
        else:
            raise ValueError(f"unsupported transformation set for {source}: {transformations}")
        overlays[key] = destination
    if len(overlays) != sum(EXPECTED_TRANSFORMATIONS.values()):
        raise ValueError(f"expected 35 overlays, got {len(overlays)}")
    return overlays


def archive_groups(
    rows: list[dict[str, str]], run_root: Path
) -> dict[str, list[dict[str, str]]]:
    category_directories: dict[str, str] = {}
    for category in EXPECTED_CATEGORIES:
        matches = list(run_root.glob(f"*-live-{category}-*"))
        if len(matches) != 1:
            raise ValueError(f"expected one run directory for {category}, got {matches}")
        category_directories[category] = matches[0].name

    groups = {"run-metadata": [], "analysis": []}
    groups.update({f"run-{category}": [] for category in sorted(EXPECTED_CATEGORIES)})
    for row in rows:
        if row["source_root"] == "analysis":
            groups["analysis"].append(row)
            continue
        first = row["relative_path"].split("/", 1)[0]
        category = next(
            (name for name, directory in category_directories.items() if directory == first),
            None,
        )
        groups["run-metadata" if category is None else f"run-{category}"].append(row)
    if any(not value for value in groups.values()):
        raise ValueError("one or more archive groups are empty")
    return groups


def archive_member_name(row: dict[str, str]) -> str:
    return f"{RELEASE_ID}/{row['source_root']}/{row['relative_path']}"


def tar_info(path: Path, member_name: str) -> tarfile.TarInfo:
    stat = path.stat()
    info = tarfile.TarInfo(member_name)
    info.size = stat.st_size
    info.mode = stat.st_mode & 0o777
    info.mtime = 0
    info.uid = 0
    info.gid = 0
    info.uname = "root"
    info.gname = "root"
    return info


def stream_archive(
    group: str,
    rows: list[dict[str, str]],
    run_root: Path,
    analysis_root: Path,
    overlays: dict[tuple[str, str], Path],
    output_dir: Path,
) -> tuple[Path, dict[str, str], int]:
    destination = output_dir / f"thesis-72h-{group}.tar.zst.partial"
    if destination.exists():
        raise FileExistsError(destination)
    published_hashes: dict[str, str] = {}
    uncompressed_bytes = 0
    with destination.open("xb") as compressed:
        process = subprocess.Popen(
            ["zstd", "-T0", "-10", "--no-progress", "-c"],
            stdin=subprocess.PIPE,
            stdout=compressed,
            stderr=subprocess.PIPE,
        )
        if process.stdin is None:
            raise RuntimeError("zstd stdin was not created")
        try:
            with tarfile.open(fileobj=process.stdin, mode="w|", format=tarfile.PAX_FORMAT) as archive:
                for row in sorted(rows, key=lambda item: item["relative_path"]):
                    key = (row["source_root"], row["relative_path"])
                    path = overlays.get(key) or source_path(row, run_root, analysis_root)
                    member = archive_member_name(row)
                    info = tar_info(path, member)
                    with path.open("rb") as raw:
                        reader = HashingReader(raw)
                        archive.addfile(info, reader)
                    actual = reader.hexdigest()
                    if key not in overlays and actual != row["sha256"]:
                        raise ValueError(f"source changed while packaging: {path}")
                    published_hashes[member] = actual
                    uncompressed_bytes += info.size
        except Exception:
            process.kill()
            process.wait()
            raise
        finally:
            process.stdin.close()
        stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
        status = process.wait()
        if status:
            raise RuntimeError(f"zstd exited {status}: {stderr}")
    return destination, published_hashes, uncompressed_bytes


def split_or_finalize(partial: Path) -> list[Path]:
    base = partial.with_suffix("")
    if base.exists():
        raise FileExistsError(base)
    if partial.stat().st_size <= MAX_ASSET_BYTES:
        partial.rename(base)
        return [base]

    parts: list[Path] = []
    with partial.open("rb") as source:
        index = 1
        while True:
            first = source.read(READ_SIZE)
            if not first:
                break
            part = Path(f"{base}.part{index:03d}")
            if part.exists():
                raise FileExistsError(part)
            written = 0
            with part.open("xb") as destination:
                destination.write(first)
                written += len(first)
                while written < MAX_ASSET_BYTES:
                    chunk = source.read(min(READ_SIZE, MAX_ASSET_BYTES - written))
                    if not chunk:
                        break
                    destination.write(chunk)
                    written += len(chunk)
            parts.append(part)
            index += 1
    partial.unlink()
    return parts


def asset_record(path: Path, group: str, part: int, part_count: int) -> dict[str, object]:
    return {
        "file": path.name,
        "group": group,
        "part": part,
        "partCount": part_count,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def write_published_checksums(path: Path, hashes: dict[str, str]) -> None:
    if len(hashes) != EXPECTED_FILES:
        raise ValueError(f"expected {EXPECTED_FILES} published hashes, got {len(hashes)}")
    with path.open("x", encoding="utf-8") as handle:
        for member in sorted(hashes):
            handle.write(f"{hashes[member]}  {member}\n")


def write_asset_checksums(path: Path, assets: Iterable[Path]) -> None:
    with path.open("x", encoding="utf-8") as handle:
        for asset in sorted(assets, key=lambda item: item.name):
            handle.write(f"{sha256(asset)}  {asset.name}\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--analysis-root", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    run_root = args.run_root.resolve()
    analysis_root = args.analysis_root.resolve()
    output_dir = args.output_dir.resolve()
    global PRIVATE_ROOT
    # Derive the project root from research/results/runs/<suite> rather than
    # embedding a private workstation path in this public tool.
    PRIVATE_ROOT = str(run_root.parents[3]).encode("utf-8")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"refusing to overwrite non-empty output directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = load_inventory(args.inventory.resolve())
    groups = archive_groups(rows, run_root)
    all_published_hashes: dict[str, str] = {}
    archive_descriptions: list[dict[str, object]] = []
    asset_records: list[dict[str, object]] = []

    with tempfile.TemporaryDirectory(prefix="thesis-72h-public-overlay-", dir=output_dir) as temp:
        overlays = build_overlays(rows, run_root, analysis_root, Path(temp))
        for group in sorted(groups):
            partial, hashes, uncompressed_bytes = stream_archive(
                group,
                groups[group],
                run_root,
                analysis_root,
                overlays,
                output_dir,
            )
            overlap = set(all_published_hashes).intersection(hashes)
            if overlap:
                raise ValueError(f"archive members duplicated: {sorted(overlap)[:3]}")
            all_published_hashes.update(hashes)
            parts = split_or_finalize(partial)
            for index, part in enumerate(parts, start=1):
                asset_records.append(asset_record(part, group, index, len(parts)))
            archive_descriptions.append(
                {
                    "group": group,
                    "members": len(hashes),
                    "uncompressedBytes": uncompressed_bytes,
                    "parts": [part.name for part in parts],
                }
            )
            print(
                json.dumps(
                    {
                        "group": group,
                        "members": len(hashes),
                        "uncompressedBytes": uncompressed_bytes,
                        "assets": [part.name for part in parts],
                    },
                    sort_keys=True,
                ),
                flush=True,
            )

    published_checksums = output_dir / "thesis-72h-PUBLISHED-FILES.sha256"
    write_published_checksums(published_checksums, all_published_hashes)
    asset_records.append(asset_record(published_checksums, "published-checksums", 1, 1))

    manifest = {
        "schemaVersion": 1,
        "releaseId": RELEASE_ID,
        "sourceFiles": EXPECTED_FILES,
        "sourceBytes": EXPECTED_BYTES,
        "publishedFiles": len(all_published_hashes),
        "publicationTransformations": EXPECTED_TRANSFORMATIONS,
        "archivePrefix": RELEASE_ID,
        "archives": archive_descriptions,
        "assets": asset_records,
        "reconstruction": {
            "singlePart": "zstd -dc ASSET.tar.zst | tar -xf -",
            "multipleParts": "cat ASSET.tar.zst.part* | zstd -dc | tar -xf -",
        },
    }
    manifest_path = output_dir / "thesis-72h-ASSET-MANIFEST.json"
    write_json(manifest_path, manifest)
    assets_for_sum = [path for path in output_dir.iterdir() if path.is_file()]
    sums_path = output_dir / "thesis-72h-SHA256SUMS"
    write_asset_checksums(sums_path, assets_for_sum)

    result = {
        "outputDirectory": str(output_dir),
        "sourceFiles": EXPECTED_FILES,
        "publishedFiles": len(all_published_hashes),
        "archiveGroups": len(groups),
        "releaseAssets": len([path for path in output_dir.iterdir() if path.is_file()]),
        "releaseAssetBytes": sum(
            path.stat().st_size for path in output_dir.iterdir() if path.is_file()
        ),
        "assetManifestSha256": sha256(manifest_path),
        "assetChecksumsSha256": sha256(sums_path),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
