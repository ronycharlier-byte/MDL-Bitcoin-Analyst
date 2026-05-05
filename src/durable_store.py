from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_EVENTS_DIR = ROOT / "external_archive" / "runtime_events"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def compact_run_payload(payload: dict[str, Any]) -> dict[str, Any]:
    archive = payload.get("archive") if isinstance(payload.get("archive"), dict) else {}
    provenance = payload.get("provenance_summary") if isinstance(payload.get("provenance_summary"), dict) else {}
    fundamentals = payload.get("fundamental_inputs") if isinstance(payload.get("fundamental_inputs"), dict) else {}
    return {
        "schema": "quant_btc_durable_run_v1",
        "stored_at_utc": utc_now(),
        "archive_id": archive.get("archive_id"),
        "asset": payload.get("asset"),
        "model": payload.get("model"),
        "horizons": payload.get("horizons"),
        "report_date_utc": provenance.get("report_date_utc"),
        "reference_spots": provenance.get("reference_spots"),
        "version": payload.get("version"),
        "data_status": payload.get("data_status"),
        "fundamental_status": fundamentals.get("status"),
        "fundamental_real_fields": fundamentals.get("real_fields"),
        "fundamental_absent_fields": fundamentals.get("absent_fields"),
        "alerts": payload.get("alerts"),
        "frames": [
            {
                "horizon": frame.get("horizon"),
                "run_id": frame.get("run_id"),
                "distribution": frame.get("distribution"),
                "regime_distribution": frame.get("regime_distribution"),
                "risk_metrics": frame.get("risk_metrics"),
                "confidence": frame.get("confidence"),
                "monte_carlo_error": frame.get("monte_carlo_error"),
                "multi_seed_stability": {
                    "status": (frame.get("multi_seed_stability") or {}).get("status"),
                    "bias_stability_label": (frame.get("multi_seed_stability") or {}).get("bias_stability_label"),
                    "directional_stability": (frame.get("multi_seed_stability") or {}).get("directional_stability"),
                    "seed_runs": (frame.get("multi_seed_stability") or {}).get("seed_runs"),
                    "simulations_per_seed": (frame.get("multi_seed_stability") or {}).get("simulations_per_seed"),
                },
            }
            for frame in payload.get("frames") or []
        ],
        "policy": "Compact durable run summary; raw simulation arrays are intentionally excluded.",
    }


def append_jsonl(kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    EXTERNAL_EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    path = EXTERNAL_EVENTS_DIR / f"{kind}.jsonl"
    line = json.dumps(payload, ensure_ascii=True, default=str)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    return {"status": "stored", "target": "local_jsonl", "path": str(path)}


def supabase_insert(table: str, row: dict[str, Any]) -> dict[str, Any]:
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        return {"status": "absent", "target": "supabase", "reason": "SUPABASE_URL or key not configured"}
    endpoint = f"{url}/rest/v1/{urllib.parse.quote(table)}"
    data = json.dumps(row, ensure_ascii=True, default=str).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=data,
        method="POST",
        headers={
            "apikey": key,
            "authorization": f"Bearer {key}",
            "content-type": "application/json",
            "prefer": "return=minimal",
            "user-agent": "quant-btc-model/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return {"status": "stored", "target": "supabase", "http_status": response.status, "table": table}
    except Exception as exc:
        return {"status": "error", "target": "supabase", "table": table, "error": str(exc)}


def webhook_send(kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = os.getenv("EXTERNAL_ARCHIVE_WEBHOOK_URL", "").strip()
    if not url:
        return {"status": "absent", "target": "external_webhook", "reason": "EXTERNAL_ARCHIVE_WEBHOOK_URL not configured"}
    body = json.dumps({"kind": kind, "payload": payload}, ensure_ascii=True, default=str).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"content-type": "application/json", "user-agent": "quant-btc-model/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return {"status": "stored", "target": "external_webhook", "http_status": response.status}
    except Exception as exc:
        return {"status": "error", "target": "external_webhook", "error": str(exc)}


def persist_run(payload: dict[str, Any]) -> dict[str, Any]:
    compact = compact_run_payload(payload)
    results = [
        append_jsonl("runs", compact),
        supabase_insert("quant_btc_runs", compact),
        webhook_send("run", compact),
    ]
    return {
        "status": "stored" if any(item.get("status") == "stored" for item in results) else "absent",
        "results": results,
        "note": "Configure Supabase or EXTERNAL_ARCHIVE_WEBHOOK_URL for off-host durable storage.",
    }


def persist_usage(row: dict[str, Any]) -> dict[str, Any]:
    payload = {"schema": "quant_btc_usage_event_v1", "created_at_utc": utc_now(), **row}
    results = [
        append_jsonl("usage", payload),
        supabase_insert("quant_btc_usage_events", payload),
        webhook_send("usage", payload),
    ]
    return {"status": "stored" if any(item.get("status") == "stored" for item in results) else "absent", "results": results}


def storage_status() -> dict[str, Any]:
    return {
        "local_jsonl": {
            "status": "present",
            "path": str(EXTERNAL_EVENTS_DIR),
            "note": "Durable if committed or mounted on persistent storage; otherwise host-runtime dependent.",
        },
        "github_archive": {
            "status": "present",
            "path": "external_archive/live_runs",
            "note": "Scheduled compact snapshots committed by GitHub Actions.",
        },
        "supabase": {
            "status": "configured" if os.getenv("SUPABASE_URL") else "absent",
            "required_env": ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"],
            "tables": ["quant_btc_runs", "quant_btc_usage_events"],
        },
        "neon_postgres": {
            "status": "configurable",
            "note": "Use EXTERNAL_ARCHIVE_WEBHOOK_URL or Supabase REST unless a direct Postgres worker is added.",
        },
        "cloudflare_d1_r2": {
            "status": "configurable",
            "note": "Best implemented in the Cloudflare Worker with D1/R2 bindings when account storage is enabled.",
        },
        "external_webhook": {
            "status": "configured" if os.getenv("EXTERNAL_ARCHIVE_WEBHOOK_URL") else "absent",
            "required_env": ["EXTERNAL_ARCHIVE_WEBHOOK_URL"],
        },
    }
