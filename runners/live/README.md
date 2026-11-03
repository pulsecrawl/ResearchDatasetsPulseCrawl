# Multi-category live runner

This runner starts one isolated process for every category in
`experiments/live/catalog.json`. Each worker executes the public
`pulsecrawl-research run` command and writes into the same new output root.

After installing the repository package, run the current two-hour protocol with:

```sh
python runners/live/run_suite.py \
  --phase two-hour \
  --output-root ./live-two-hour-output
```

The output root must be new or empty. The supervisor records the
exact worker commands in `suite-plan.json`, live status in `supervisor.json`,
separate worker logs, final exit codes, and `suite-checksums.sha256`.

A platform service manager may keep this foreground process alive, but is not
part of the research logic and does not change the recorded commands.
