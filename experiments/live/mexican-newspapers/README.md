# Mexican newspapers live study

This category contains 19 websites in the thesis live-study universe.
Each website was scheduled four times at 30-minute intervals. An execution
could visit up to 1,500 URLs to depth five within a 1,680-second window.

| Website | Stable ID | Discovery entry URL |
|---|---|---|
| El Economista | `mx-el-economista` | https://www.eleconomista.com.mx/politica |
| El Financiero | `mx-el-financiero` | https://www.elfinanciero.com.mx/nacional/ |
| El Heraldo de México | `mx-el-heraldo` | https://heraldodemexico.com.mx/nacional/ |
| El Imparcial | `mx-el-imparcial` | https://www.elimparcial.com/mexico/ |
| El Informador | `mx-el-informador` | https://www.informador.mx/mexico/ |
| Excélsior | `mx-excelsior` | https://www.excelsior.com.mx/nacional |
| La Crónica de Hoy | `mx-la-cronica` | https://www.cronica.com.mx/nacional/ |
| La Opción de Chihuahua | `mx-la-opcion` | https://laopcion.com.mx/ |
| La Razón de México | `mx-la-razon` | https://www.razon.com.mx/mexico/ |
| Noroeste | `mx-noroeste` | https://www.noroeste.com.mx/nacional/ |
| Norte Digital | `mx-norte-digital` | https://nortedigital.mx/ |
| Proceso | `mx-proceso` | https://www.proceso.com.mx/nacional/ |
| Pulso de San Luis | `mx-pulso-slp` | https://pulsoslp.com.mx/nacional |
| Raíchali | `mx-raichali` | https://raichali.com/ |
| SDP Noticias | `mx-sdp-noticias` | https://www.sdpnoticias.com/mexico/ |
| El Horizonte | `mx-el-horizonte` | https://www.elhorizonte.mx/nacional/ |
| El Porvenir | `mx-el-porvenir` | https://elporvenir.mx/nacional/ |
| La Silla Rota | `mx-la-silla-rota` | https://lasillarota.com/nacion/ |
| El Mañana de Nuevo Laredo | `mx-el-manana-nuevo-laredo` | https://elmanana.com.mx/ |

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
