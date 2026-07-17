from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from quality_monitor import compact_frame, evaluate

PARIS_TZ = ZoneInfo("Europe/Paris")


def safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")


def paris_iso(value: datetime) -> str:
    return value.astimezone(PARIS_TZ).isoformat()


def build_archive_summary(monitor_summary: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    fundamentals = run.get("fundamental_inputs") or {}
    archive = run.get("archive") or {}
    version = run.get("version") or {}
    created_at = datetime.now(UTC)
    return {
        "schema": "quant_btc_external_archive_v1",
        "created_at": created_at.isoformat(),
        "created_at_utc": created_at.isoformat(),
        "created_at_paris": paris_iso(created_at),
        "source": "Cloudflare Action endpoint routed to Render",
        "runtime_archive": {
            "archive_id": archive.get("archive_id"),
            "status": archive.get("status"),
            "endpoint": archive.get("endpoint"),
            "sqlite_table": archive.get("sqlite_table"),
            "created_at_utc": archive.get("created_at_utc"),
            "created_at_paris": archive.get("created_at_paris"),
        },
        "version": {
            "api_version": version.get("api_version"),
            "schema_version": version.get("schema_version"),
            "model_version": version.get("model_version"),
            "git_commit": version.get("git_commit"),
            "worker_version": (run.get("cloudflare_bridge") or {}).get("worker_version"),
        },
        "source_policy": (run.get("cloudflare_bridge") or {}).get("source_policy"),
        "asset": run.get("asset"),
        "model": run.get("model"),
        "horizons": run.get("horizons"),
        "data_status": run.get("data_status"),
        "fundamental_inputs": {
            "status": fundamentals.get("status"),
            "real_fields": fundamentals.get("real_fields"),
            "absent_fields": fundamentals.get("absent_fields"),
            "values": fundamentals.get("values"),
            "sources": fundamentals.get("sources"),
            "timestamp": fundamentals.get("timestamp"),
            "note": fundamentals.get("note"),
        },
        "provenance_summary": run.get("provenance_summary"),
        "quality_monitor": {
            "status": monitor_summary.get("status"),
            "fetched_at": monitor_summary.get("fetched_at"),
            "fetched_at_paris": monitor_summary.get("fetched_at_paris"),
            "frame_count": monitor_summary.get("frame_count"),
            "archive_id": monitor_summary.get("archive_id"),
        },
        "frames": [compact_frame(frame) for frame in run.get("frames") or []],
        "policy": {
            "user_effect": "information_only",
            "execution_authority": "none",
            "financial_advice": False,
            "paper_trading": "mock_only",
            "live_trading": "blocked",
        },
    }


def build_markdown(summary: dict[str, Any]) -> str:
    fundamentals = summary.get("fundamental_inputs") or {}
    version = summary.get("version") or {}
    return "\n".join(
        [
            "# Quant BTC External Run Archive",
            "",
            f"- Created at UTC: {summary.get('created_at_utc')}",
            f"- Created at Europe/Paris: {summary.get('created_at_paris')}",
            f"- Runtime archive ID: `{(summary.get('runtime_archive') or {}).get('archive_id')}`",
            f"- API version: {version.get('api_version')}",
            f"- Git commit: {version.get('git_commit')}",
            f"- Source policy: {summary.get('source_policy')}",
            f"- Asset: {summary.get('asset')}",
            f"- Model: {summary.get('model')}",
            f"- Horizons: {summary.get('horizons')}",
            f"- Data status: {summary.get('data_status')}",
            f"- Fundamental status: {fundamentals.get('status')}",
            f"- Fundamental real fields: {fundamentals.get('real_fields')}",
            f"- Fundamental absent fields: {fundamentals.get('absent_fields')}",
            "",
            "## Frame Summary",
            "",
            "| Horizon | Run ID | Median return | P10 | P90 | VaR95 | CVaR95 | Confidence |",
            "|---:|---|---:|---:|---:|---:|---:|---:|",
            *[
                (
                    f"| {frame.get('horizon')} | `{frame.get('run_id')}` | "
                    f"{frame.get('median_return')} | {frame.get('p10_return')} | {frame.get('p90_return')} | "
                    f"{frame.get('var_95')} | {frame.get('cvar_95')} | {frame.get('confidence_score')} |"
                )
                for frame in summary.get("frames") or []
            ],
            "",
            "This file is a compact external audit archive. It is not a deterministic forecast and not financial advice.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive a compact Quant BTC live run summary.")
    parser.add_argument("--output-dir", type=Path, default=Path("external_archive/live_runs"))
    args = parser.parse_args()

    monitor_summary, run = evaluate()
    summary = build_archive_summary(monitor_summary, run)
    created = datetime.now(UTC)
    archive_id = (summary.get("runtime_archive") or {}).get("archive_id") or created.strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir / created.strftime("%Y") / created.strftime("%m") / created.strftime("%d")
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_filename(f"{created.strftime('%Y%m%dT%H%M%SZ')}_{archive_id}")
    json_path = output_dir / f"{stem}.json"
    markdown_path = output_dir / f"{stem}.md"
    json_path.write_text(json.dumps(summary, ensure_ascii=True, indent=2, default=str), encoding="utf-8")
    markdown_path.write_text(build_markdown(summary), encoding="utf-8")
    print(
        json.dumps(
            {"json_path": str(json_path), "markdown_path": str(markdown_path), "archive_id": archive_id}, indent=2
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
