# Methodology

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
