# Publication boundary

This repository starts with fresh Git history and account-only commit attribution.

Git-tracked files may contain selected synthetic inputs, generators, expected
values, registered experiment configurations, sanitized execution manifests,
bounded measurements, derived analysis, exact templates and field definitions,
release inventories, and checksums. Original private commit history,
manuscripts, author metadata, workstation paths, hostnames, credentials,
downloaded third-party HTML, and sensitive headers are excluded.

Reviewed GitHub release assets may additionally contain the complete public
form of live-study workspaces, scheduler state, logs, SQLite state, CSV,
Parquet, and analysis outputs. These assets must have a complete file
inventory, per-file and per-asset SHA-256 manifests, a streaming reconstruction
check, and explicit records for every publication-only transformation. They are
release assets rather than ordinary Git blobs so a normal clone remains usable.

Pre-publication checks examine staged file contents, filenames, and Git
author/committer metadata for private author identifiers, absolute home paths,
credential patterns, and private service URLs. Public source pages can include
public contact strings as observed data; those values are not repository
authorship metadata.
Binary files committed directly to Git remain limited to reviewed PNG renders
and compact Parquet evidence already covered by repository verification.
Additional reviewed binary evidence is allowed only in checksum-covered GitHub
release assets under the controls above.

Public environment records contain only the package version, Python version,
and generic operating-system and architecture information; they must not
contain usernames, hostnames, or absolute paths. For the 72-hour release,
absolute project-root prefixes are replaced with
`${PULSECRAWL_RESEARCH_ROOT}`. A transient Oracle identity logout token is
replaced with a fixed redaction marker in its SQLite, CSV, and Parquet
representations. Public source URLs and ordinary CDN query parameters are
otherwise retained as observed data.

Checks reduce disclosure risk; they are not a guarantee against all possible indirect identification. The repository owner account and ordinary GitHub platform metadata remain public. Keep future contributions within this boundary.
