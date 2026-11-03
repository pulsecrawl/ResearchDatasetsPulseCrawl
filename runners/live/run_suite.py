#!/usr/bin/env python3
"""Public entry point for the isolated multi-category live supervisor."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pulsecrawl_research.live.supervisor import run_live_suite


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--phase", choices=("two-hour",), default="two-hour")
    parser.add_argument("--heartbeat-seconds", type=int, default=20)
    args = parser.parse_args()
    result = run_live_suite(
        args.output_root,
        phase=args.phase,
        heartbeat_seconds=args.heartbeat_seconds,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
