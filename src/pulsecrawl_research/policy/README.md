# Crawling policy and recovery studies

This package contains the controlled code used to evaluate crawling limits,
robots decisions, shared-origin timing, interruption recovery, queue behavior,
and duplicate delivery.

| File | Role |
|---|---|
| `experiments.py` | Executes the registered policy and recovery cases |
| `webbench.py` | Provides observable local HTTP websites and request logs |
| `state_model.py` | Checks selected state transitions independently of HTTP |

Public definitions and retained runs are under
[`experiments/controlled/`](../../../experiments/controlled/). The policy study
catalog in that directory maps descriptive experiment names to their accepted
run folders.
