from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CF_BASE = os.getenv("CF_BASE", "https://quant-btc-model-lite.mdl-bitcoin-analyst.workers.dev").rstrip("/")
RENDER_BASE = os.getenv("RENDER_BASE", "https://quant-btc-model-api.onrender.com").rstrip("/")
MIN_API_VERSION = os.getenv("MIN_API_VERSION", "1.4.0")
EXPECTED_HORIZONS = [7, 30, 90, 180, 365]
REQUIRED_REAL_FIELDS = {
    item.strip()
    for item in os.getenv(
        "REQUIRED_REAL_FIELDS",
        "etf_flows,funding_rate,open_interest,hash_rate,stablecoins_supply,dxy,us_rates,nasdaq",
    ).split(",")
    if item.strip()
}
ALLOWED_ABSENT_FIELDS = {
    item.strip()
    for item in os.getenv("ALLOWED_ABSENT_FIELDS", "liquidations,exchange_reserves").split(",")
    if item.strip()
}


class MonitorFailure(RuntimeError):
    pass


def version_tuple(value: str) -> tuple[int, ...]:
    parts: list[int] = []
    for part in str(value).split("."):
        digits = "".join(char for char in part if char.isdigit())
        parts.append(int(digits or "0"))
    return tuple(parts)


def fetch_json(url: str, timeout: int = 180) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "quant-btc-monitor/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def require(condition: bool, message: str, context: Any = None) -> None:
    if condition:
        return
    detail = f"{message}: {json.dumps(context, ensure_ascii=True, default=str)[:1200]}"
    raise MonitorFailure(detail)


def compact_frame(frame: dict[str, Any]) -> dict[str, Any]:
    distribution = frame.get("distribution") or {}
    risk = frame.get("risk_metrics") or {}
    provenance = frame.get("provenance") or {}
    confidence = frame.get("confidence") or {}
    return {
        "horizon": frame.get("horizon"),
        "run_id": frame.get("run_id"),
        "report_date": provenance.get("report_date"),
        "reference_spot": provenance.get("reference_spot"),
        "reference_spot_timestamp": provenance.get("reference_spot_timestamp"),
        "p10_return": distribution.get("p10_return"),
        "median_return": distribution.get("median_return"),
        "p90_return": distribution.get("p90_return"),
        "prob_up": distribution.get("prob_up"),
        "var_95": risk.get("var_95"),
        "cvar_95": risk.get("cvar_95"),
        "max_drawdown": risk.get("max_drawdown"),
        "confidence_score": confidence.get("score"),
        "regime_distribution": frame.get("regime_distribution"),
    }


def evaluate() -> tuple[dict[str, Any], dict[str, Any]]:
    fetched_at = datetime.now(timezone.utc).isoformat()
    render_health = fetch_json(f"{RENDER_BASE}/health", timeout=60)
    render_version = fetch_json(f"{RENDER_BASE}/version", timeout=60)
    render_status = fetch_json(f"{RENDER_BASE}/status", timeout=60)
    cf_health = fetch_json(f"{CF_BASE}/health", timeout=60)
    cf_version = fetch_json(f"{CF_BASE}/version", timeout=60)
    cf_status = fetch_json(f"{CF_BASE}/status", timeout=60)
    run = fetch_json(f"{CF_BASE}/run?asset=BTC", timeout=240)

    require(render_health.get("status") == "ok", "Render health is not ok", render_health)
    require(cf_health.get("status") == "ok", "Cloudflare health is not ok", cf_health)

    backend_version = (run.get("version") or {}).get("api_version") or render_version.get("api_version")
    require(
        version_tuple(str(backend_version)) >= version_tuple(MIN_API_VERSION),
        f"Backend API version is below {MIN_API_VERSION}",
        {"backend_version": backend_version, "render_version": render_version, "run_version": run.get("version")},
    )

    render_sources = render_status.get("data_sources") or {}
    require("etf_flows" in render_sources, "Render status does not expose ETF flows source", render_sources)
    require("etf_flows" not in set(render_sources.get("absent_without_connector") or []), "ETF flows still marked absent", render_sources)

    horizons = run.get("horizons") or []
    frames = run.get("frames") or []
    require(horizons == EXPECTED_HORIZONS, "Unexpected horizons", horizons)
    require(len(frames) == len(EXPECTED_HORIZONS), "Unexpected frame count", {"count": len(frames), "horizons": horizons})

    data_status = run.get("data_status") or {}
    require(data_status.get("market_prices") == "real", "Market prices are not real", data_status)
    require(data_status.get("bitget_required") == "real", "Bitget-required status is not real", data_status)
    require(data_status.get("non_bitget_market_fallback") == "absent", "Non-Bitget fallback detected", data_status)

    bridge = run.get("cloudflare_bridge") or {}
    require(
        bridge.get("source_policy") == "bitget_required_no_exchange_fallback",
        "Unexpected Cloudflare source policy",
        bridge,
    )

    fundamentals = run.get("fundamental_inputs") or {}
    real_fields = set(fundamentals.get("real_fields") or [])
    absent_fields = set(fundamentals.get("absent_fields") or [])
    missing_required = sorted(REQUIRED_REAL_FIELDS - real_fields)
    unexpected_absent = sorted(absent_fields - ALLOWED_ABSENT_FIELDS)
    require(not missing_required, "Required fundamental fields are not real", {"missing": missing_required, "fundamentals": fundamentals})
    require(not unexpected_absent, "Unexpected absent fundamental fields", {"unexpected_absent": unexpected_absent, "fundamentals": fundamentals})

    archive = run.get("archive") or {}
    require(archive.get("status") == "stored", "Runtime archive was not stored", archive)
    require(bool(archive.get("archive_id")), "Runtime archive_id is missing", archive)

    for frame in frames:
        require(frame.get("run_id"), "Frame run_id missing", frame)
        require((frame.get("provenance") or {}).get("reference_spot"), "Frame reference spot missing", frame)
        require((frame.get("risk_metrics") or {}).get("var_95") is not None, "Frame VaR missing", frame)
        require((frame.get("risk_metrics") or {}).get("cvar_95") is not None, "Frame CVaR missing", frame)
        require((frame.get("confidence") or {}).get("score") is not None, "Frame confidence missing", frame)

    summary = {
        "status": "ok",
        "fetched_at": fetched_at,
        "render_api_version": render_version.get("api_version"),
        "live_api_version": backend_version,
        "git_commit": (run.get("version") or {}).get("git_commit"),
        "worker_version": cf_version.get("worker_version") or bridge.get("worker_version"),
        "source_policy": bridge.get("source_policy"),
        "horizons": horizons,
        "frame_count": len(frames),
        "archive_id": archive.get("archive_id"),
        "fundamental_status": fundamentals.get("status"),
        "fundamental_real_fields": sorted(real_fields),
        "fundamental_absent_fields": sorted(absent_fields),
        "reference_spots": (run.get("provenance_summary") or {}).get("reference_spots"),
        "frames": [compact_frame(frame) for frame in frames],
    }
    return summary, run


def main() -> int:
    parser = argparse.ArgumentParser(description="Quality monitor for Quant BTC live API.")
    parser.add_argument("--output", type=Path, help="Optional path for compact monitor summary JSON.")
    args = parser.parse_args()

    try:
        summary, _ = evaluate()
    except Exception as exc:
        failure = {
            "status": "failed",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "error": str(exc),
        }
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(failure, ensure_ascii=True, indent=2), encoding="utf-8")
        print(json.dumps(failure, ensure_ascii=True, indent=2), file=sys.stderr)
        return 1

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
