# Security advisories live study

This category contains 8 websites in the thesis live-study universe.
Each website was scheduled four times at 30-minute intervals. An execution
could visit up to 1,500 URLs to depth five within a 1,680-second window.

| Website | Stable ID | Discovery entry URL |
|---|---|---|
| Apple Security Releases | `security-apple` | https://support.apple.com/en-us/100100 |
| Ubuntu Security Notices | `security-ubuntu` | https://ubuntu.com/security/notices |
| Chrome Releases | `security-chrome-releases` | https://chromereleases.googleblog.com/ |
| Mozilla Security Advisories | `security-mozilla` | https://www.mozilla.org/en-US/security/advisories/ |
| Oracle Security Alerts | `security-oracle` | https://www.oracle.com/security-alerts/ |
| GitHub Security Advisories | `security-github` | https://github.com/advisories |
| GitLab Releases | `security-gitlab` | https://docs.gitlab.com/releases/ |
| Node.js Security Releases | `security-nodejs` | https://nodejs.org/en/blog/vulnerability |

## Where to start

| Reviewer question | File or folder |
|---|---|
| Which websites and URL scopes were configured? | [`input/sites.json`](input/sites.json) |
| Which protocol and limits were used? | [`experiment.yaml`](experiment.yaml) |
| What did the completed study produce? | [`runs/thesis-universe-2h-2026-11-02/`](runs/thesis-universe-2h-2026-11-02/) |
| What are the site-level totals? | [`site-summary.csv`](runs/thesis-universe-2h-2026-11-02/readable-output/site-summary.csv) |
| What do representative target records look like? | [`records-preview.csv`](runs/thesis-universe-2h-2026-11-02/readable-output/records-preview.csv) |
| Which target records were published? | [`records.csv`](runs/thesis-universe-2h-2026-11-02/readable-output/records.csv) |
| How were representative fetched URLs classified? | [`pages-preview.csv`](runs/thesis-universe-2h-2026-11-02/readable-output/pages-preview.csv) |

## Code used

| Step | Public implementation |
|---|---|
| Build the shared schema and URL-scoped template stacks | [`live/profiles.py`](../../../src/pulsecrawl_research/live/profiles.py) |
| Review access, create the workspace, and execute scheduled cycles | [`live/runner.py`](../../../src/pulsecrawl_research/live/runner.py) |
| Start categories as isolated processes | [`live/supervisor.py`](../../../src/pulsecrawl_research/live/supervisor.py) |
| Core crawl, extraction, and dataset operations | [PulseCrawl public package](https://github.com/pulsecrawl/PulseCrawl) |

The source list supplies the website-specific URL scope, constants, limits,
and optional mapping overrides. The Python profile supplies the shared schema
and common extraction mappings; there is no hidden crawler implementation for
this category.
