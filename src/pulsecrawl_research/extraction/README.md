# Schema and template studies

This package contains the controlled extraction comparisons. It evaluates URL
scope, ordered fallback, expected field values, markup changes, mapping
ambiguity, and the size of generated integration artifacts.

| File | Role |
|---|---|
| `experiments.py` | Runs controlled extraction strategies against labelled HTML |
| `maintenance.py` | Measures template changes, ambiguity, and integration artifacts |

Live schemas and mappings are kept in `../live/profiles.py` because they are
the definitions used by the current-website workflow. The controlled template
evidence remains separate so changing public websites cannot change its known
answers.
