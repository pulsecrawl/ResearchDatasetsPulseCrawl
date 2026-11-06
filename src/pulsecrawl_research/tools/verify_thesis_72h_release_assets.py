"""Stream-verify the complete 72-hour GitHub release asset set.

Verification does not extract the roughly 10 GB public form to disk.  It
decompresses each archive as a stream, hashes every tar member, compares all
14,215 values to ``thesis-72h-PUBLISHED-FILES.sha256``, and performs the
publication privacy checks while bytes pass through memory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
from typing import BinaryIO


EXPECTED_FILES = 14_215
EXPECTED_TRANSFORMED = 35
PRIVATE_HOME_PATTERN = re.compile(rb"/Users/[A-Za-z0-9_.-]+")
PUBLIC_ROOT = b"${PULSECRAWL_RESEARCH_ROOT}"
REDACTED_TOKEN = b"<redacted-transient-session-token>"
ORACLE_LOGOUT_TOKEN = re.compile(
    rb"(https://login-ext\.identity\.oraclecloud\.com/oauth2/v1/userlogout\?"
    rb"[^\s,\"']*?[?&]token=)([^&\s,\"']+)",
    re.IGNORECASE,
)
READ_SIZE = 1024 * 1024
SCAN_OVERLAP = 16 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(READ_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checksums(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        if name in result:
            raise ValueError(f"duplicate checksum entry: {name}")
        result[name] = digest
    return result


def inventory_transformations(path: Path, prefix: str) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            names = set(filter(None, row["publication_transformations"].split(";")))
            if names:
                member = f"{prefix}/{row['source_root']}/{row['relative_path']}"
                result[member] = names
    if len(result) != EXPECTED_TRANSFORMED:
        raise ValueError(f"expected {EXPECTED_TRANSFORMED} transformed files, got {len(result)}")
    return result


def has_unredacted_oracle_token(value: bytes) -> bool:
    return any(
        not match.group(2).startswith(REDACTED_TOKEN)
        for match in ORACLE_LOGOUT_TOKEN.finditer(value)
    )


class MemberVerifier:
    def __init__(
        self, handle: BinaryIO, transformations: set[str], member: str
    ) -> None:
        self.handle = handle
        self.transformations = transformations
        self.member = member
        self.digest = hashlib.sha256()
        self.bytes_read = 0
        self.tail = b""
        self.private_path_found = False
        self.unredacted_oracle_token_found = False
        self.public_root_found = False
        self.redacted_oracle_token_found = False
        self.parquet_capture = (
            tempfile.SpooledTemporaryFile(max_size=16 * 1024 * 1024, mode="w+b")
            if "transient-oracle-logout-token-redaction" in transformations
            and member.endswith(".parquet")
            else None
        )

    def consume(self) -> None:
        while True:
            chunk = self.handle.read(READ_SIZE)
            if not chunk:
                break
            self.digest.update(chunk)
            self.bytes_read += len(chunk)
            if self.parquet_capture is not None:
                self.parquet_capture.write(chunk)
            scanned = self.tail + chunk
            self.private_path_found |= bool(PRIVATE_HOME_PATTERN.search(scanned))
            self.unredacted_oracle_token_found |= has_unredacted_oracle_token(scanned)
            if "absolute-workstation-path-redaction" in self.transformations:
                self.public_root_found |= PUBLIC_ROOT in scanned
            if "transient-oracle-logout-token-redaction" in self.transformations:
                self.redacted_oracle_token_found |= REDACTED_TOKEN in scanned
            self.tail = scanned[-SCAN_OVERLAP:]

    def validate(self, member: str, expected_size: int, expected_hash: str) -> None:
        if self.bytes_read != expected_size:
            raise ValueError(f"size mismatch for {member}")
        if self.digest.hexdigest() != expected_hash:
            raise ValueError(f"checksum mismatch for {member}")
        if self.private_path_found:
            raise ValueError(f"private workstation path found in {member}")
        if self.unredacted_oracle_token_found:
            raise ValueError(f"unredacted Oracle logout token found in {member}")
        if (
            "absolute-workstation-path-redaction" in self.transformations
            and not self.public_root_found
        ):
            raise ValueError(f"public root marker absent from transformed file {member}")
        if self.parquet_capture is not None:
            import pyarrow.parquet as pq

            self.parquet_capture.seek(0)
            errors = pq.read_table(self.parquet_capture, columns=["error"])["error"]
            matches = [
                match
                for value in errors.to_pylist()
                if value is not None
                for match in ORACLE_LOGOUT_TOKEN.finditer(value.encode("utf-8"))
            ]
            if len(matches) != 72 or any(
                not match.group(2).startswith(REDACTED_TOKEN) for match in matches
            ):
                raise ValueError(
                    f"decoded Parquet redaction verification failed for {member}"
                )
            self.parquet_capture.close()
        elif (
            "transient-oracle-logout-token-redaction" in self.transformations
            and not self.redacted_oracle_token_found
        ):
            raise ValueError(f"Oracle redaction marker absent from transformed file {member}")


def open_zstd_stream(parts: list[Path]) -> tuple[subprocess.Popen[bytes], subprocess.Popen[bytes]]:
    concatenate = subprocess.Popen(
        ["cat", *[str(path) for path in parts]],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if concatenate.stdout is None:
        raise RuntimeError("cat stdout was not created")
    decompress = subprocess.Popen(
        ["zstd", "-dc", "--no-progress"],
        stdin=concatenate.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    concatenate.stdout.close()
    return concatenate, decompress


def verify_archive(
    parts: list[Path],
    expected: dict[str, str],
    transformations: dict[str, set[str]],
    observed: set[str],
) -> tuple[int, int]:
    concatenate, decompress = open_zstd_stream(parts)
    if decompress.stdout is None:
        raise RuntimeError("zstd stdout was not created")
    member_count = 0
    member_bytes = 0
    try:
        with tarfile.open(fileobj=decompress.stdout, mode="r|") as archive:
            for info in archive:
                if not info.isfile():
                    continue
                if info.name in observed:
                    raise ValueError(f"duplicate archive member: {info.name}")
                if info.name not in expected:
                    raise ValueError(f"unexpected archive member: {info.name}")
                handle = archive.extractfile(info)
                if handle is None:
                    raise ValueError(f"unable to read archive member: {info.name}")
                verifier = MemberVerifier(
                    handle, transformations.get(info.name, set()), info.name
                )
                verifier.consume()
                verifier.validate(info.name, info.size, expected[info.name])
                observed.add(info.name)
                member_count += 1
                member_bytes += info.size
    finally:
        decompress.stdout.close()
    decompress_error = (
        decompress.stderr.read().decode("utf-8", errors="replace")
        if decompress.stderr
        else ""
    )
    concatenate_error = (
        concatenate.stderr.read().decode("utf-8", errors="replace")
        if concatenate.stderr
        else ""
    )
    decompress_status = decompress.wait()
    concatenate_status = concatenate.wait()
    if decompress_status:
        raise RuntimeError(f"zstd exited {decompress_status}: {decompress_error}")
    if concatenate_status:
        raise RuntimeError(f"cat exited {concatenate_status}: {concatenate_error}")
    return member_count, member_bytes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-dir", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    args = parser.parse_args()

    asset_dir = args.asset_dir.resolve()
    asset_sums = checksums(asset_dir / "thesis-72h-SHA256SUMS")
    for name, expected_hash in asset_sums.items():
        path = asset_dir / name
        if not path.is_file() or sha256(path) != expected_hash:
            raise ValueError(f"release asset checksum mismatch: {name}")

    manifest_path = asset_dir / "thesis-72h-ASSET-MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = checksums(asset_dir / "thesis-72h-PUBLISHED-FILES.sha256")
    if len(expected) != EXPECTED_FILES:
        raise ValueError(f"expected {EXPECTED_FILES} published files, got {len(expected)}")
    transformations = inventory_transformations(
        args.inventory.resolve(), manifest["archivePrefix"]
    )

    observed: set[str] = set()
    archive_results: list[dict[str, object]] = []
    for description in manifest["archives"]:
        parts = [asset_dir / name for name in description["parts"]]
        count, byte_count = verify_archive(
            parts, expected, transformations, observed
        )
        if count != description["members"]:
            raise ValueError(f"member count mismatch for {description['group']}")
        if byte_count != description["uncompressedBytes"]:
            raise ValueError(f"byte count mismatch for {description['group']}")
        archive_results.append(
            {
                "group": description["group"],
                "members": count,
                "uncompressedBytes": byte_count,
            }
        )
        print(json.dumps(archive_results[-1], sort_keys=True), flush=True)

    missing = set(expected).difference(observed)
    if missing:
        raise ValueError(f"published files missing from archives: {sorted(missing)[:3]}")
    transformed_missing = set(transformations).difference(observed)
    if transformed_missing:
        raise ValueError(f"transformed files missing: {sorted(transformed_missing)[:3]}")

    print(
        json.dumps(
            {
                "verificationStatus": "passed",
                "assetChecksums": len(asset_sums),
                "archiveGroups": len(archive_results),
                "publishedFiles": len(observed),
                "publishedBytes": sum(item["uncompressedBytes"] for item in archive_results),
                "privacyChecks": {
                    "absoluteWorkstationPaths": 0,
                    "unredactedOracleLogoutTokens": 0,
                    "transformedFilesVerified": len(transformations),
                },
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
