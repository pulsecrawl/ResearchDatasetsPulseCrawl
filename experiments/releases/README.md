# Reviewed evidence releases

The current reviewed live evidence is the
[`thesis-live-universe-72h-v2.0.0`](thesis-live-universe-72h-v2.0.0/) release.
It contains five categories, 75 websites, exactly 72 successful hourly
executions per website, and 5,400 successful terminal site executions with no
missed occurrences. Compact summaries, configurations, templates, provenance,
limitations, and checksums are kept in Git. The matching GitHub release holds
the complete reviewed workspace and analysis archives.

The
[`thesis-live-universe-v1.0.0`](thesis-live-universe-v1.0.0/) release remains
the historical two-hour study with 300 successful site executions.

Controlled experiment evidence remains under
[`experiments/controlled/`](../controlled/). Every controlled run includes a
README, resolved configuration, direct measurements, and checksums; runs that
produce datasets also include CSV and Parquet companions.

Releases never contain third-party response bodies, private workstation paths,
or credentials. A reviewed full-evidence GitHub release may include sanitized
logs and local SQLite state when these are necessary for reproducibility and
covered by the release inventory and checksums.

