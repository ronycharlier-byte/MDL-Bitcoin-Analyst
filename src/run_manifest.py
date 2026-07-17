from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
from datetime import UTC, datetime
from typing import Any, cast

RUNTIME_PACKAGES = ("fastapi", "numpy", "pandas", "pydantic", "scipy", "statsmodels")


def stable_input_hash(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def dependency_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for package in RUNTIME_PACKAGES:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "absent"
    return versions


def build_run_manifest(payload: dict[str, Any], endpoint: str) -> dict[str, Any]:
    frames = cast(list[Any], payload.get("frames")) if isinstance(payload.get("frames"), list) else []
    provenance = cast(dict[str, Any], payload.get("provenance")) if isinstance(payload.get("provenance"), dict) else {}
    spot = cast(dict[str, Any], provenance.get("spot")) if isinstance(provenance.get("spot"), dict) else {}
    inputs = {
        "endpoint": endpoint,
        "asset": payload.get("asset"),
        "model": payload.get("model"),
        "horizons": [frame.get("horizon_days") for frame in frames if isinstance(frame, dict)],
        "simulation_counts": [frame.get("simulation_count") for frame in frames if isinstance(frame, dict)],
        "spot": {
            "value": spot.get("value"),
            "source": spot.get("source"),
            "observed_at_utc": spot.get("observed_at_utc"),
        },
    }
    return {
        "manifest_version": "1.0.0",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "endpoint": endpoint,
        "archive_id": payload.get("archive_id"),
        "analysis_id": payload.get("analysis_id"),
        "run_ids": [frame.get("run_id") for frame in frames if isinstance(frame, dict)],
        "seeds": [frame.get("seed") for frame in frames if isinstance(frame, dict)],
        "input_sha256": stable_input_hash(inputs),
        "versions": {
            "python": platform.python_version(),
            "api": provenance.get("api_version"),
            "worker": provenance.get("worker_version"),
            "model": provenance.get("model_version"),
            "schema": provenance.get("schema_version"),
            "git_commit": provenance.get("git_commit"),
            "dependencies": dependency_versions(),
        },
        "time_bounds": {
            "report_generated_at_utc": provenance.get("report_generated_at_utc"),
            "spot_observed_at_utc": spot.get("observed_at_utc"),
        },
        "runtime_duration_ms": None,
        "limitations": [
            "Input hash covers canonical run parameters and shared spot provenance, not external provider response bodies.",
            "Runtime duration is unavailable for legacy execution paths and remains null rather than estimated.",
        ],
    }
