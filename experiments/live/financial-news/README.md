# Financial and stock news live study

This category contains 20 websites in the thesis live-study universe.
Each website was scheduled four times at 30-minute intervals. An execution
could visit up to 1,500 URLs to depth five within a 1,680-second window.

| Website | Stable ID | Discovery entry URL |
|---|---|---|
| Business Insider Markets | `finance-business-insider` | https://www.businessinsider.com/markets |
| CNBC Markets | `finance-cnbc` | https://www.cnbc.com/markets/ |
| Fortune Finance | `finance-fortune` | https://fortune.com/finance/ |
| Kiplinger | `finance-kiplinger` | https://www.kiplinger.com/investing |
| The Motley Fool | `finance-motley-fool` | https://www.fool.com/investing-news/ |
| TradingView News | `finance-tradingview` | https://www.tradingview.com/news/ |
| Yahoo Finance | `finance-yahoo` | https://finance.yahoo.com/news/ |
| BNN Bloomberg | `finance-bnn-bloomberg` | https://www.bnnbloomberg.ca/markets/ |
| CBS MoneyWatch | `finance-cbs-moneywatch` | https://www.cbsnews.com/moneywatch/ |
| Economic Times Markets | `finance-economic-times` | https://economictimes.indiatimes.com/markets |
| FXStreet | `finance-fxstreet` | https://www.fxstreet.com/news |
| Financial Post | `finance-financial-post` | https://financialpost.com/category/investing/ |
| Finbold | `finance-finbold` | https://finbold.com/ |
| Fox Business Markets | `finance-fox-business` | https://www.foxbusiness.com/markets |
| Kitco News | `finance-kitco` | https://www.kitco.com/news |
| Mint Markets | `finance-mint` | https://www.livemint.com/market |
| The Daily Upside | `finance-daily-upside` | https://www.thedailyupside.com/investments/ |
| The Guardian Business | `finance-guardian-business` | https://www.theguardian.com/business |
| MoneyWeek | `finance-moneyweek` | https://moneyweek.com/investments |
| Sherwood Markets | `finance-sherwood` | https://sherwood.news/markets/ |

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
