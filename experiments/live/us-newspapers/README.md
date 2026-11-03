# United States newspapers live study

This category contains 20 websites in the thesis live-study universe.
Each website was scheduled four times at 30-minute intervals. An execution
could visit up to 1,500 URLs to depth five within a 1,680-second window.

| Website | Stable ID | Discovery entry URL |
|---|---|---|
| Chicago Tribune | `us-chicago-tribune` | https://www.chicagotribune.com/news/ |
| Houston Chronicle | `us-houston-chronicle` | https://www.houstonchronicle.com/news/houston-texas/ |
| Los Angeles Times | `us-los-angeles-times` | https://www.latimes.com/california |
| Newsday | `us-newsday` | https://www.newsday.com/news/ |
| NOLA.com | `us-nola` | https://www.nola.com/news/ |
| San Diego Union-Tribune | `us-san-diego-union-tribune` | https://www.sandiegouniontribune.com/news/ |
| San Francisco Chronicle | `us-san-francisco-chronicle` | https://www.sfchronicle.com/bayarea/ |
| Tampa Bay Times | `us-tampa-bay-times` | https://www.tampabay.com/news/ |
| The Atlanta Journal-Constitution | `us-atlanta-journal-constitution` | https://www.ajc.com/news/ |
| The Baltimore Sun | `us-baltimore-sun` | https://www.baltimoresun.com/news/ |
| The Boston Globe | `us-boston-globe` | https://www.bostonglobe.com/metro/ |
| The Dallas Morning News | `us-dallas-morning-news` | https://www.dallasnews.com/news/ |
| The Denver Post | `us-denver-post` | https://www.denverpost.com/news/ |
| The Philadelphia Inquirer | `us-philadelphia-inquirer` | https://www.inquirer.com/news/ |
| The Salt Lake Tribune | `us-salt-lake-tribune` | https://www.sltrib.com/news/ |
| The Seattle Times | `us-seattle-times` | https://www.seattletimes.com/seattle-news/ |
| Boston Herald | `us-boston-herald` | https://www.bostonherald.com/news/ |
| Orange County Register | `us-orange-county-register` | https://www.ocregister.com/news/ |
| Albuquerque Journal | `us-albuquerque-journal` | https://www.abqjournal.com/news/ |
| Anchorage Daily News | `us-anchorage-daily-news` | https://www.adn.com/alaska-news/ |

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
