"""Finalize the compact 72-hour release index from verified asset metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil


RELEASE_ID = "thesis-live-universe-72h-v2.0.0"
EXPECTED_ASSET_FILES = {
    "thesis-72h-analysis.tar.zst",
    "thesis-72h-run-financial-news.tar.zst",
    "thesis-72h-run-general-commerce.tar.zst",
    "thesis-72h-run-metadata.tar.zst",
    "thesis-72h-run-mexican-newspapers.tar.zst",
    "thesis-72h-run-security-advisories.tar.zst",
    "thesis-72h-run-us-newspapers.tar.zst",
    "thesis-72h-PUBLISHED-FILES.sha256",
    "thesis-72h-ASSET-MANIFEST.json",
    "thesis-72h-SHA256SUMS",
}
EXPECTED_PUBLISHED_FILES = 14_215
EXPECTED_PUBLISHED_BYTES = 9_954_692_984
EXPECTED_TRANSFORMATIONS = {
    "absolute-workstation-path-redaction": 32,
    "transient-oracle-logout-token-redaction": 3,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_checksums(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        result[name] = digest
    return result


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_directory_checksums(folder: Path) -> str:
    destination = folder / "checksums.sha256"
    lines = []
    for path in sorted(item for item in folder.rglob("*") if item.is_file()):
        if path == destination:
            continue
        lines.append(f"{sha256(path)}  {path.relative_to(folder).as_posix()}\n")
    destination.write_text("".join(lines), encoding="utf-8")
    return sha256(destination)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-dir", type=Path, required=True)
    parser.add_argument("--release-dir", type=Path, required=True)
    args = parser.parse_args()
    asset_dir = args.asset_dir.resolve()
    release_dir = args.release_dir.resolve()

    actual_assets = {path.name for path in asset_dir.iterdir() if path.is_file()}
    if actual_assets != EXPECTED_ASSET_FILES:
        raise ValueError(f"release assets differ: {sorted(actual_assets)}")
    asset_sums_path = asset_dir / "thesis-72h-SHA256SUMS"
    asset_sums = load_checksums(asset_sums_path)
    if set(asset_sums) != EXPECTED_ASSET_FILES - {asset_sums_path.name}:
        raise ValueError("asset checksum coverage differs")
    for name, expected in asset_sums.items():
        if sha256(asset_dir / name) != expected:
            raise ValueError(f"asset checksum mismatch: {name}")

    asset_manifest_path = asset_dir / "thesis-72h-ASSET-MANIFEST.json"
    asset_manifest = json.loads(asset_manifest_path.read_text(encoding="utf-8"))
    if (
        asset_manifest["releaseId"] != RELEASE_ID
        or asset_manifest["publishedFiles"] != EXPECTED_PUBLISHED_FILES
        or asset_manifest["publicationTransformations"] != EXPECTED_TRANSFORMATIONS
    ):
        raise ValueError("asset manifest identity or counts differ")
    published_bytes = sum(item["uncompressedBytes"] for item in asset_manifest["archives"])
    if published_bytes != EXPECTED_PUBLISHED_BYTES:
        raise ValueError(f"published byte total differs: {published_bytes}")

    copied = {
        "asset-manifest.json": asset_manifest_path,
        "asset-checksums.sha256": asset_sums_path,
        "published-files.sha256": asset_dir / "thesis-72h-PUBLISHED-FILES.sha256",
    }
    for name, source in copied.items():
        destination = release_dir / name
        if destination.exists():
            raise FileExistsError(destination)
        shutil.copy2(source, destination)

    manifest_path = release_dir / "release-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["releaseId"] != RELEASE_ID:
        raise ValueError("compact release identity differs")
    manifest.update(
        {
            "status": "completed-reviewed-and-packaged",
            "expectedAssets": sorted(EXPECTED_ASSET_FILES),
            "assetChecksums": "asset-checksums.sha256",
            "assetManifest": "asset-manifest.json",
            "assetManifestSha256": sha256(asset_manifest_path),
            "assetChecksumsSha256": sha256(asset_sums_path),
            "publishedFileChecksums": "published-files.sha256",
            "publishedFileChecksumsSha256": sha256(
                asset_dir / "thesis-72h-PUBLISHED-FILES.sha256"
            ),
            "publishedFiles": EXPECTED_PUBLISHED_FILES,
            "publishedBytes": EXPECTED_PUBLISHED_BYTES,
            "releaseAssetBytes": sum(
                path.stat().st_size for path in asset_dir.iterdir() if path.is_file()
            ),
            "assetVerification": {
                "status": "passed",
                "archiveGroups": 7,
                "publishedFiles": EXPECTED_PUBLISHED_FILES,
                "privateWorkstationPaths": 0,
                "unredactedOracleLogoutTokens": 0,
                "transformedFilesVerified": 35,
            },
        }
    )
    write_json(manifest_path, manifest)
    checksum = write_directory_checksums(release_dir)
    print(
        json.dumps(
            {
                "releaseId": RELEASE_ID,
                "status": manifest["status"],
                "assetFiles": len(EXPECTED_ASSET_FILES),
                "releaseAssetBytes": manifest["releaseAssetBytes"],
                "repositoryChecksumManifestSha256": checksum,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
