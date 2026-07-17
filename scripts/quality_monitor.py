from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

CF_BASE = os.getenv("CF_BASE", "https://quant-btc-model-lite.mdl-bitcoin-analyst.workers.dev").rstrip("/")
RENDER_BASE = os.getenv("RENDER_BASE", "https://quant-btc-model-api.onrender.com").rstrip("/")
MIN_API_VERSION = os.getenv("MIN_API_VERSION", "2.0.0")
EXPECTED_HORIZONS = [7, 30, 90, 180, 365]
PARIS_TZ = ZoneInfo("Europe/Paris")
REQUIRED_REAL_FIELDS = {
    item.strip()
    for item in os.getenv(
        "REQUIRED_REAL_FIELDS",
        "etf_flows,funding_rate,open_interest,hash_rate,exchange_reserves,stablecoins_supply,dxy,us_rates,nasdaq",
    ).split(",")
    if item.strip()
}
ALLOWED_ABSENT_FIELDS = {
    item.strip() for item in os.getenv("ALLOWED_ABSENT_FIELDS", "liquidations").split(",") if item.strip()
}


class MonitorFailure(RuntimeError):
    pass


def version_tuple(value: str) -> tuple[int, ...]:
    parts: list[int] = []
    for part in str(value).split("."):
        digits = "".join(char for char in part if char.isdigit())
        parts.append(int(digits or "0"))
    return tuple(parts)


def fetch_json(
    url: str,
    timeout: int = 180,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=True).encode() if payload is not None else None
    headers = {"User-Agent": "quant-btc-monitor/2.0", "Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, method=method, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def paris_now_iso() -> str:
    return datetime.now(UTC).astimezone(PARIS_TZ).isoformat()


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
        "report_date_utc": provenance.get("report_date_utc"),
        "report_date_paris": provenance.get("report_date_paris"),
        "reference_spot": provenance.get("reference_spot"),
        "reference_spot_timestamp": provenance.get("reference_spot_timestamp"),
        "reference_spot_timestamp_utc": provenance.get("reference_spot_timestamp_utc"),
        "reference_spot_timestamp_paris": provenance.get("reference_spot_timestamp_paris"),
        "p10_return": distribution.get("p10_return"),
        "median_return": distribution.get("median_return"),
        "p90_return": distribution.get("p90_return"),
        "prob_up": distribution.get("prob_up"),
        "var_95": risk.get("var_95"),
        "cvar_95": risk.get("cvar_95"),
        "max_drawdown": risk.get("max_drawdown"),
        "mean_simulated_max_drawdown": risk.get("mean_simulated_max_drawdown"),
        "median_max_drawdown": risk.get("median_max_drawdown"),
        "p95_max_drawdown": risk.get("p95_max_drawdown"),
        "worst_sample_drawdown": risk.get("worst_sample_drawdown"),
        "confidence_score": confidence.get("score"),
        "regime_distribution": frame.get("regime_distribution"),
        "monte_carlo_error": frame.get("monte_carlo_error"),
        "multi_seed_stability": frame.get("multi_seed_stability"),
    }


def evaluate() -> tuple[dict[str, Any], dict[str, Any]]:
    fetched_at = datetime.now(UTC).isoformat()
    fetched_at_paris = paris_now_iso()
    render_health = fetch_json(f"{RENDER_BASE}/health", timeout=60)
    render_version = fetch_json(f"{RENDER_BASE}/version", timeout=60)
    render_status = fetch_json(f"{RENDER_BASE}/status", timeout=60)
    cf_health = fetch_json(f"{CF_BASE}/health", timeout=60)
    cf_version = fetch_json(f"{CF_BASE}/version", timeout=60)
    fetch_json(f"{CF_BASE}/status", timeout=60)
    audit = fetch_json(f"{CF_BASE}/audit", timeout=120)
    run = fetch_json(
        f"{CF_BASE}/multi-run",
        timeout=240,
        method="POST",
        payload={"asset": "BTC", "horizons": EXPECTED_HORIZONS, "simulations": 2000, "model": "ensemble"},
    )
    alerts = fetch_json(f"{CF_BASE}/alerts?asset=BTC", timeout=120)
    history = fetch_json(f"{CF_BASE}/history?asset=BTC&limit=2", timeout=120)

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
    require(
        "etf_flows" not in set(render_sources.get("absent_without_connector") or []),
        "ETF flows still marked absent",
        render_sources,
    )
    require(
        "exchange_reserves" in render_sources, "Render status does not expose exchange reserves source", render_sources
    )
    require(
        "exchange_reserves" not in set(render_sources.get("absent_without_connector") or []),
        "Exchange reserves still marked absent",
        render_sources,
    )

    horizons = run.get("horizons") or []
    frames = run.get("frames") or []
    require(horizons == EXPECTED_HORIZONS, "Unexpected horizons", horizons)
    require(
        len(frames) == len(EXPECTED_HORIZONS), "Unexpected frame count", {"count": len(frames), "horizons": horizons}
    )

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

    require(audit.get("status") == "ok", "Audit endpoint status is not ok", audit)
    require(
        audit.get("ready_for_gpt_live_analysis") is True, "Audit endpoint is not ready for GPT live analysis", audit
    )
    require(
        audit.get("source_policy") == "bitget_required_no_exchange_fallback", "Audit source policy is unexpected", audit
    )
    require(
        (audit.get("version") or {}).get("api_version") == str(backend_version), "Audit API version mismatch", audit
    )
    require(bool(audit.get("checked_at_utc")), "Audit checked_at_utc is missing", audit)
    require(bool(audit.get("checked_at_paris")), "Audit checked_at_paris is missing", audit)
    require(bool(audit.get("timezone_policy")), "Audit timezone policy is missing", audit)
    require(
        bool((run.get("provenance_summary") or {}).get("report_date_utc")),
        "Run report_date_utc is missing",
        run.get("provenance_summary"),
    )
    require(
        bool((run.get("provenance_summary") or {}).get("report_date_paris")),
        "Run report_date_paris is missing",
        run.get("provenance_summary"),
    )
    freshness = run.get("freshness") or {}
    spot_freshness = freshness.get("spot") or {}
    require(spot_freshness.get("is_fresh") is True, "Run spot freshness gate is not fresh", freshness)

    fundamentals = run.get("fundamental_inputs") or {}
    real_fields = set(fundamentals.get("real_fields") or [])
    absent_fields = set(fundamentals.get("absent_fields") or [])
    missing_required = sorted(REQUIRED_REAL_FIELDS - real_fields)
    unexpected_absent = sorted(absent_fields - ALLOWED_ABSENT_FIELDS)
    require(
        not missing_required,
        "Required fundamental fields are not real",
        {"missing": missing_required, "fundamentals": fundamentals},
    )
    require(
        not unexpected_absent,
        "Unexpected absent fundamental fields",
        {"unexpected_absent": unexpected_absent, "fundamentals": fundamentals},
    )

    archive = run.get("archive") or {}
    require(archive.get("status") == "stored", "Runtime archive was not stored", archive)
    require(bool(archive.get("archive_id")), "Runtime archive_id is missing", archive)

    for frame in frames:
        require(frame.get("run_id"), "Frame run_id missing", frame)
        require((frame.get("provenance") or {}).get("reference_spot"), "Frame reference spot missing", frame)
        require((frame.get("provenance") or {}).get("report_date_utc"), "Frame report_date_utc missing", frame)
        require((frame.get("provenance") or {}).get("report_date_paris"), "Frame report_date_paris missing", frame)
        require(
            (frame.get("provenance") or {}).get("reference_spot_timestamp_utc"),
            "Frame spot timestamp UTC missing",
            frame,
        )
        require(
            (frame.get("provenance") or {}).get("reference_spot_timestamp_paris"),
            "Frame spot timestamp Paris missing",
            frame,
        )
        require((frame.get("risk_metrics") or {}).get("var_95") is not None, "Frame VaR missing", frame)
        require((frame.get("risk_metrics") or {}).get("cvar_95") is not None, "Frame CVaR missing", frame)
        require(
            (frame.get("risk_metrics") or {}).get("mean_simulated_max_drawdown") is not None,
            "Frame expanded drawdown missing",
            frame,
        )
        require(
            (frame.get("monte_carlo_error") or {}).get("status") == "inferred", "Frame Monte Carlo error missing", frame
        )
        require(
            (frame.get("multi_seed_stability") or {}).get("status") == "inferred",
            "Frame multi-seed stability missing",
            frame,
        )
        require((frame.get("confidence") or {}).get("score") is not None, "Frame confidence missing", frame)

    summary = {
        "status": "ok",
        "fetched_at": fetched_at,
        "fetched_at_paris": fetched_at_paris,
        "render_api_version": render_version.get("api_version"),
        "live_api_version": backend_version,
        "git_commit": (run.get("version") or {}).get("git_commit"),
        "worker_version": cf_version.get("worker_version") or bridge.get("worker_version"),
        "source_policy": bridge.get("source_policy"),
        "audit_status": audit.get("status"),
        "audit_checked_at_utc": audit.get("checked_at_utc"),
        "audit_checked_at_paris": audit.get("checked_at_paris"),
        "audit_ready": audit.get("ready_for_gpt_live_analysis"),
        "audit_latest_outputs_auditable": audit.get("latest_outputs_auditable"),
        "audit_warnings": audit.get("warnings"),
        "horizons": horizons,
        "frame_count": len(frames),
        "archive_id": archive.get("archive_id"),
        "archive_created_at_utc": archive.get("created_at_utc"),
        "archive_created_at_paris": archive.get("created_at_paris"),
        "freshness": freshness,
        "alerts_status": alerts.get("status"),
        "alert_count": len(alerts.get("alerts") or []),
        "history_status": history.get("status"),
        "history_count": len(history.get("archives") or []),
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
            "fetched_at": datetime.now(UTC).isoformat(),
            "fetched_at_paris": paris_now_iso(),
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
