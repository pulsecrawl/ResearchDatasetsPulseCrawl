"""Validate the public research package, inputs, evidence, links, and privacy."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pulsecrawl_research.tools import verify

from .registry import experiments, registry


def _registered_experiments() -> set[str]:
    value = registry()
    return {
        identifier
        for question in value.get("researchQuestions", {}).values()
        for identifier in question.get("experiments", [])
    }


def validate_artifact() -> dict[str, Any]:
    """Run the same checks used by the public repository workflow."""
    errors: list[str] = []
    checks: dict[str, Any] = {}
    defined = set(experiments())
    registered = _registered_experiments()
    if defined != registered:
        errors.append(
            f"registry mismatch: defined={sorted(defined)} registered={sorted(registered)}"
        )

    validators: tuple[tuple[str, Callable[[], Any]], ...] = (
        ("datasets", verify.verify_manifests),
        ("metadata", verify.verify_research_metadata),
        ("controlledEvidence", verify.verify_controlled_evidence),
        ("liveRelease", verify.verify_live_release),
        ("documentation", verify.verify_documentation),
    )
    for name, validator in validators:
        try:
            checks[name] = validator()
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
    try:
        verify.privacy_scan()
        checks["publicationScan"] = "passed"
    except (OSError, ValueError) as exc:
        errors.append(f"publicationScan: {type(exc).__name__}: {exc}")

    return {
        "valid": not errors,
        "errors": errors,
        "definedExperiments": len(defined),
        "checks": checks,
    }
