# Downloading and verifying the full evidence

The compact files in this directory are the browser-readable evidence index.
The complete public evidence mirror is attached to the GitHub release tagged
`thesis-live-universe-72h-v2.0.0`:

<https://github.com/pulsecrawl/ResearchDatasetsPulseCrawl/releases/tag/thesis-live-universe-72h-v2.0.0>

The ten assets total 1,044,445,423 bytes. Seven `.tar.zst` archives reconstruct
14,215 files and 9,954,692,984 bytes beneath one
`thesis-live-universe-72h-v2.0.0/` directory. The remaining three assets are the
asset manifest, archive checksums, and extracted-file checksums.

## Download

With the GitHub CLI:

```sh
gh release download thesis-live-universe-72h-v2.0.0 \
  --repo pulsecrawl/ResearchDatasetsPulseCrawl \
  --dir thesis-72h-assets
```

## Verify the downloads

```sh
cd thesis-72h-assets
shasum -a 256 -c thesis-72h-SHA256SUMS
```

## Extract everything

Create an empty destination with at least 10 GB available, then run:

```sh
for archive in thesis-72h-*.tar.zst; do
  zstd -dc "$archive" | tar -xf -
done
```

Verify every extracted file from the parent of the reconstructed release
directory:

```sh
shasum -a 256 -c thesis-72h-assets/thesis-72h-PUBLISHED-FILES.sha256
```

## Verify without extracting

From a clone of this repository with `zstd`, Python, and PyArrow installed:

```sh
python src/pulsecrawl_research/tools/verify_thesis_72h_release_assets.py \
  --asset-dir thesis-72h-assets \
  --inventory experiments/releases/thesis-live-universe-72h-v2.0.0/RELEASE-FILES.csv
```

That verifier streams all seven archives, checks every member against the
published-file manifest, rejects private workstation paths, and decodes the
credential-redacted Parquet member for a semantic redaction check.

## What is included

- the complete five category run directories;
- all 75 site workspaces, registered jobs, templates, fields, state, and run
  evidence;
- suite metadata, supervisor state, service/worker logs, and scheduler plans;
- all readable CSV and Parquet exports and the full analysis directory;
- original-source, public-extracted-file, and release-asset checksum layers.

No third-party response bodies are retained. Apple is included with the other
74 sites; its documented security-template scope limitation is described in
`limitations.md`.
