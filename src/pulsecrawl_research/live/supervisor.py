"""Run all public live-study categories as isolated local processes.

The supervisor contains the scientific orchestration used by a multi-category
study. Platform-specific service managers may keep this process alive, but do
not change its experiment definitions, worker commands, or retained evidence.
"""

from __future__ import annotations

import hashlib
import json
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pulsecrawl_research.common.registry import RESEARCH_ROOT
from pulsecrawl_research.common.store import atomic_json

CATALOG_PATH = RESEARCH_ROOT / "experiments" / "live" / "catalog.json"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def category_experiments() -> tuple[str, ...]:
    """Return the public live experiment identifiers in catalog order."""
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return tuple(f"live-{item['id']}" for item in catalog["categories"])


def worker_command(experiment: str, output_root: Path, phase: str) -> list[str]:
    """Build the portable public command for one category."""
    return [
        "python",
        "-m",
        "pulsecrawl_research.cli",
        "run",
        experiment,
        "--phase",
        phase,
        "--output-root",
        str(output_root),
    ]


def _runtime_worker_command(
    experiment: str, output_root: Path, phase: str
) -> list[str]:
    command = worker_command(experiment, output_root, phase)
    return [sys.executable, *command[1:]]


def _progress(output_root: Path, experiment: str) -> dict[str, Any] | None:
    candidates = sorted(
        output_root.glob(f"*-{experiment}-*/live-progress.json"),
        key=lambda path: path.stat().st_mtime,
    )
    if not candidates:
        return None
    path = candidates[-1]
    value = json.loads(path.read_text(encoding="utf-8"))
    executions = list(value.get("executions") or [])
    sites = [site for execution in executions for site in execution.get("sites", [])]
    return {
        "runDirectory": str(path.parent.relative_to(output_root)),
        "status": value.get("status"),
        "completedCycles": sum(
            execution.get("status", "completed") == "completed"
            for execution in executions
        ),
        "plannedCycles": (value.get("settings") or {}).get("executions"),
        "siteExecutions": len(sites),
        "failedSiteExecutions": sum(
            site.get("status") not in {"completed", "succeeded"} for site in sites
        ),
        "lastCompletedAt": max(
            (execution.get("finishedAt", "") for execution in executions),
            default=None,
        ),
    }


def _state(
    output_root: Path,
    phase: str,
    started_at: str,
    workers: dict[str, subprocess.Popen[Any]],
    status: str,
) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "status": status,
        "phase": phase,
        "startedAt": started_at,
        "updatedAt": _now(),
        "workers": {
            experiment: {
                "pid": process.pid,
                "running": process.poll() is None,
                "exitCode": process.poll(),
                "progress": _progress(output_root, experiment),
            }
            for experiment, process in workers.items()
        },
    }


def _checksums(output_root: Path) -> Path:
    destination = output_root / "suite-checksums.sha256"
    lines: list[str] = []
    for path in sorted(output_root.rglob("*")):
        if path.is_file() and path != destination:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            lines.append(f"{digest}  {path.relative_to(output_root).as_posix()}")
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination


def run_live_suite(
    output_root: Path,
    *,
    phase: str,
    heartbeat_seconds: int = 20,
) -> dict[str, Any]:
    """Execute every catalogued live category and preserve supervisor evidence."""
    output_root = output_root.resolve()
    if output_root.exists() and any(output_root.iterdir()):
        raise ValueError(f"output root is not empty: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    logs = output_root / "logs"
    logs.mkdir()
    experiments = category_experiments()
    started_at = _now()
    atomic_json(
        output_root / "suite-plan.json",
        {
            "schemaVersion": 1,
            "phase": phase,
            "experiments": list(experiments),
            "workerCommands": {
                experiment: worker_command(experiment, Path("<output-root>"), phase)
                for experiment in experiments
            },
            "startedAt": started_at,
        },
    )

    stop_requested = False

    def request_stop(_signum: int, _frame: Any) -> None:
        nonlocal stop_requested
        stop_requested = True

    previous_term = signal.signal(signal.SIGTERM, request_stop)
    previous_int = signal.signal(signal.SIGINT, request_stop)
    workers: dict[str, subprocess.Popen[Any]] = {}
    streams: dict[str, Any] = {}
    try:
        for experiment in experiments:
            stream = (logs / f"{experiment}.log").open("w", encoding="utf-8")
            streams[experiment] = stream
            workers[experiment] = subprocess.Popen(
                _runtime_worker_command(experiment, output_root, phase),
                cwd=RESEARCH_ROOT,
                stdout=stream,
                stderr=subprocess.STDOUT,
                text=True,
            )

        while True:
            running = [
                process for process in workers.values() if process.poll() is None
            ]
            status = (
                "stopping"
                if stop_requested
                else ("running" if running else "finishing")
            )
            atomic_json(
                output_root / "supervisor.json",
                _state(output_root, phase, started_at, workers, status),
            )
            if stop_requested or not running:
                break
            time.sleep(max(1, heartbeat_seconds))

        if stop_requested:
            for process in workers.values():
                if process.poll() is None:
                    process.terminate()

        for process in workers.values():
            process.wait()

        exit_codes = {name: process.returncode for name, process in workers.items()}
        if stop_requested:
            final_status = "interrupted"
        elif all(code == 0 for code in exit_codes.values()):
            final_status = "completed"
        else:
            final_status = "failed"
        final = _state(output_root, phase, started_at, workers, final_status)
        final["finishedAt"] = _now()
        final["exitCodes"] = exit_codes
        atomic_json(output_root / "supervisor.json", final)
        atomic_json(output_root / f"suite-{final_status}.json", final)
        _checksums(output_root)
        return final
    finally:
        signal.signal(signal.SIGTERM, previous_term)
        signal.signal(signal.SIGINT, previous_int)
        for stream in streams.values():
            stream.close()
