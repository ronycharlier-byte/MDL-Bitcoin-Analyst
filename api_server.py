from __future__ import annotations

import json
import hashlib
import math
import os
import sqlite3
import subprocess
import sys
import time
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field


ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
SUMMARY_DIR = ROOT / "data" / "simulations"
REPORT_PATH = ROOT / "reports" / "latest_report.md"
DASHBOARD_PATH = ROOT / "reports" / "dashboard_summary.md"
API_RUNTIME_DB = ROOT / "data" / "api_runtime.db"
API_ARCHIVE_DIR = ROOT / "reports" / "archive"
MAX_API_SIMULATIONS = int(os.getenv("MAX_API_SIMULATIONS", "250000"))
DEFAULT_API_SIMULATIONS = min(int(os.getenv("DEFAULT_API_SIMULATIONS", "5000")), MAX_API_SIMULATIONS)
DEFAULT_MULTIFRAME_SIMULATIONS = min(int(os.getenv("DEFAULT_MULTIFRAME_SIMULATIONS", "2000")), MAX_API_SIMULATIONS)
DEFAULT_MULTIFRAME_HORIZONS = [7, 30, 90, 180, 365]
RATE_LIMIT_RUNS_PER_MINUTE = int(os.getenv("RATE_LIMIT_RUNS_PER_MINUTE", "12"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "45"))
MAX_SPOT_AGE_SECONDS = int(os.getenv("MAX_SPOT_AGE_SECONDS", "180"))
MAX_FUNDAMENTAL_AGE_SECONDS = int(os.getenv("MAX_FUNDAMENTAL_AGE_SECONDS", "21600"))
MAX_RUN_AGE_SECONDS = int(os.getenv("MAX_RUN_AGE_SECONDS", "21600"))
MULTI_SEED_RUNS = max(1, int(os.getenv("MULTI_SEED_RUNS", "5")))
MULTI_SEED_SIMULATIONS = max(100, int(os.getenv("MULTI_SEED_SIMULATIONS", "250")))
API_VERSION = "1.8.1"
MODEL_VERSION = os.getenv("MODEL_VERSION", "quant_btc_model_v1")
SCHEMA_VERSION = "gpt_action_schema_v1.8.0"
SOURCE_POLICY = "bitget_required_no_exchange_fallback"
USER_DISPLAY_TIMEZONE = "Europe/Paris"
PARIS_TZ = ZoneInfo(USER_DISPLAY_TIMEZONE)
TIMEZONE_POLICY = (
    "Source timestamps are UTC. User-facing GPT answers must show both UTC and Europe/Paris "
    "when a report date or spot timestamp is cited."
)
REQUIRED_AUDIT_REAL_FIELDS = [
    "etf_flows",
    "funding_rate",
    "open_interest",
    "hash_rate",
    "exchange_reserves",
    "stablecoins_supply",
    "dxy",
    "us_rates",
    "nasdaq",
]
ALLOWED_AUDIT_ABSENT_FIELDS = ["liquidations"]


def resolve_git_commit() -> str:
    for key in ("RENDER_GIT_COMMIT", "GIT_COMMIT", "SOURCE_VERSION"):
        value = os.getenv(key)
        if value:
            return value[:12]
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        if completed.returncode == 0 and completed.stdout.strip():
            return completed.stdout.strip()
    except Exception:
        pass
    return "unknown"


GIT_COMMIT = resolve_git_commit()
_RATE_LIMIT_BUCKETS: dict[str, list[float]] = {}

import correlation_model  # noqa: E402
import ensemble_model  # noqa: E402
import garch_model  # noqa: E402
import jump_diffusion  # noqa: E402
import liquidation_model  # noqa: E402
import monte_carlo  # noqa: E402
import regime_switching  # noqa: E402
import student_t_model  # noqa: E402
from confidence_score import compute_confidence_score  # noqa: E402
from features import daily_returns  # noqa: E402
from logging_utils import setup_logger  # noqa: E402
from market_data import fetch_farside_etf_flow_history, load_fundamental_features, load_market_prices  # noqa: E402
from position_sizing import position_sizing_summary  # noqa: E402
from risk_metrics import compute_risk_metrics  # noqa: E402
from simulation_utils import seed_for, summarize_simulation  # noqa: E402
from stress_tests import run_stress_tests  # noqa: E402
from backtest import run_backtest  # noqa: E402


FAST_MODEL_REGISTRY = {
    "monte_carlo": monte_carlo.simulate,
    "student_t": student_t_model.simulate,
    "student_t_model": student_t_model.simulate,
    "jump_diffusion": jump_diffusion.simulate,
    "garch": garch_model.simulate,
    "garch_model": garch_model.simulate,
    "regime_switching": regime_switching.simulate,
    "liquidation": liquidation_model.simulate,
    "liquidation_model": liquidation_model.simulate,
    "correlation": correlation_model.simulate,
    "correlation_model": correlation_model.simulate,
    "ensemble": ensemble_model.simulate,
}


app = FastAPI(
    title="Quant BTC Model API",
    version=API_VERSION,
    description=(
        "Probabilistic Bitcoin quantitative model API. Outputs are scenarios, "
        "probabilities, distributions and risk metrics, never deterministic predictions."
    ),
)


def init_runtime_db() -> None:
    API_RUNTIME_DB.parent.mkdir(parents=True, exist_ok=True)
    API_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(API_RUNTIME_DB) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rate_limit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_key TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS response_cache (
                cache_key TEXT PRIMARY KEY,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                response_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS run_archive (
                archive_id TEXT PRIMARY KEY,
                endpoint TEXT NOT NULL,
                asset TEXT,
                model TEXT,
                horizons_json TEXT,
                run_ids_json TEXT,
                report_date TEXT,
                reference_spot TEXT,
                api_version TEXT,
                git_commit TEXT,
                status TEXT,
                archive_json_path TEXT,
                archive_markdown_path TEXT,
                response_json TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_rate_limit_client_time ON rate_limit_events (client_key, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_response_cache_expires ON response_cache (expires_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_run_archive_created_at ON run_archive (created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_run_archive_asset ON run_archive (asset, created_at)")
        conn.commit()


init_runtime_db()


class RunRequest(BaseModel):
    asset: str = Field(default="BTC", pattern="^[A-Za-z0-9_-]{2,12}$")
    horizon: int = Field(default=365, ge=1, le=3650)
    simulations: int = Field(default=DEFAULT_API_SIMULATIONS, ge=100, le=MAX_API_SIMULATIONS)
    model: str = Field(
        default="ensemble",
        pattern=(
            "^(ensemble|monte_carlo|student_t|student_t_model|jump_diffusion|"
            "garch|garch_model|regime_switching|liquidation|liquidation_model|"
            "correlation|correlation_model)$"
        ),
    )
    skip_corpus: bool = Field(default=True)
    no_online: bool = Field(default=False)
    spot_override_price: float | None = Field(default=None, exclude=True)
    spot_override_timestamp: str | None = Field(default=None, exclude=True)
    spot_override_source: str | None = Field(default=None, exclude=True)


class MultiFrameRunRequest(BaseModel):
    asset: str = Field(default="BTC", pattern="^[A-Za-z0-9_-]{2,12}$")
    horizons: list[int] = Field(default_factory=lambda: DEFAULT_MULTIFRAME_HORIZONS.copy(), min_length=1, max_length=8)
    simulations: int = Field(default=DEFAULT_MULTIFRAME_SIMULATIONS, ge=100, le=MAX_API_SIMULATIONS)
    model: str = Field(
        default="ensemble",
        pattern=(
            "^(ensemble|monte_carlo|student_t|student_t_model|jump_diffusion|"
            "garch|garch_model|regime_switching|liquidation|liquidation_model|"
            "correlation|correlation_model)$"
        ),
    )
    skip_corpus: bool = Field(default=True)
    no_online: bool = Field(default=False)


class RunResponse(BaseModel):
    run_id: str
    asset: str
    horizon: int
    simulations: int
    model: str
    provenance: dict[str, Any]
    data_status: dict[str, str]
    fundamental_inputs: dict[str, Any] | None = None
    distribution: dict[str, Any]
    regime_distribution: dict[str, Any]
    risk_metrics: dict[str, Any]
    stress_tests: list[dict[str, Any]]
    confidence: dict[str, Any]
    position_sizing: dict[str, Any]
    version: dict[str, Any]
    archive: dict[str, Any] | None = None
    cache: dict[str, Any] | None = None
    report_markdown: str
    dashboard_markdown: str
    warning: str


def normalized_horizons(horizons: list[int]) -> list[int]:
    cleaned = []
    for horizon in horizons:
        value = int(horizon)
        if value < 1 or value > 3650:
            raise HTTPException(status_code=400, detail=f"Invalid horizon: {value}. Use 1..3650 days.")
        if value not in cleaned:
            cleaned.append(value)
    return cleaned


def summarize_fundamental_inputs(fundamentals: pd.DataFrame | None) -> dict[str, Any]:
    metadata_columns = {"timestamp", "asset", "source", "statut"}
    if fundamentals is None or fundamentals.empty:
        return {
            "status": "absent",
            "real_fields": [],
            "absent_fields": [],
            "values": {},
            "sources": [],
            "timestamp": None,
            "statut": "missing",
            "note": "No fundamental snapshot was loaded.",
        }

    latest = fundamentals.tail(1).iloc[0]
    field_columns = [column for column in fundamentals.columns if column not in metadata_columns]
    values: dict[str, float] = {}
    absent_fields: list[str] = []
    field_status: dict[str, str] = {}
    for column in field_columns:
        numeric_value = pd.to_numeric(pd.Series([latest.get(column)]), errors="coerce").iloc[0]
        if pd.notna(numeric_value):
            values[column] = float(numeric_value)
            field_status[column] = "real"
        else:
            absent_fields.append(column)
            field_status[column] = "absent"

    source_text = str(latest.get("source") or "")
    sources = sorted({part.strip() for part in source_text.split(",") if part.strip() and part.strip() != "no_fundamental_source"})
    status = "absent"
    if values and absent_fields:
        status = "partial_real_absent"
    elif values:
        status = "real"

    latest_timestamp = str(latest.get("timestamp")) if latest.get("timestamp") is not None else None
    return {
        "status": status,
        "real_fields": sorted(values),
        "absent_fields": sorted(absent_fields),
        "values": values,
        "field_status": field_status,
        "sources": sources,
        "timestamp": latest_timestamp,
        "timestamp_utc": timestamp_utc_iso(latest_timestamp),
        "timestamp_paris": timestamp_paris_iso(latest_timestamp),
        "statut": str(latest.get("statut") or "missing"),
        "note": "Point-in-time fundamental snapshot, not a complete historical series.",
    }


def load_processed_fundamental_inputs(asset: str) -> dict[str, Any]:
    path = ROOT / "data" / "processed" / f"{asset.upper()}_fundamental_features.csv"
    try:
        if path.exists():
            return summarize_fundamental_inputs(pd.read_csv(path))
    except Exception:
        pass
    return summarize_fundamental_inputs(None)


def require_api_key(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
) -> None:
    expected = os.getenv("QUANT_API_KEY")
    if not expected:
        return
    bearer = None
    if authorization and authorization.lower().startswith("bearer "):
        bearer = authorization.split(" ", 1)[1].strip()
    supplied = bearer or x_api_key
    if supplied != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


def client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def require_rate_limit(request: Request) -> None:
    if RATE_LIMIT_RUNS_PER_MINUTE <= 0:
        return
    key = client_key(request)
    now = time.time()
    window = max(1, RATE_LIMIT_WINDOW_SECONDS)
    endpoint = request.url.path
    try:
        with sqlite3.connect(API_RUNTIME_DB) as conn:
            conn.execute("DELETE FROM rate_limit_events WHERE created_at < ?", (now - window,))
            count = conn.execute(
                "SELECT COUNT(*) FROM rate_limit_events WHERE client_key = ? AND created_at >= ?",
                (key, now - window),
            ).fetchone()[0]
            if count >= RATE_LIMIT_RUNS_PER_MINUTE:
                raise HTTPException(
                    status_code=429,
                    detail=(
                        f"Rate limit exceeded. Maximum {RATE_LIMIT_RUNS_PER_MINUTE} run requests "
                        f"per {window} seconds."
                    ),
                )
            conn.execute(
                "INSERT INTO rate_limit_events (client_key, endpoint, created_at) VALUES (?, ?, ?)",
                (key, endpoint, now),
            )
            conn.commit()
    except HTTPException:
        raise
    except Exception:
        # Fallback for read-only or transient SQLite errors.
        monotonic_now = time.monotonic()
        bucket = [item for item in _RATE_LIMIT_BUCKETS.get(key, []) if monotonic_now - item < window]
        if len(bucket) >= RATE_LIMIT_RUNS_PER_MINUTE:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Rate limit exceeded. Maximum {RATE_LIMIT_RUNS_PER_MINUTE} run requests "
                    f"per {window} seconds."
                ),
            )
        bucket.append(monotonic_now)
        _RATE_LIMIT_BUCKETS[key] = bucket


def pydantic_payload(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_iso(value: datetime | None = None) -> str:
    return (value or utc_now()).astimezone(timezone.utc).isoformat()


def paris_iso(value: datetime | None = None) -> str:
    return (value or utc_now()).astimezone(PARIS_TZ).isoformat()


def parse_utc_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.isdigit():
            try:
                number = int(text)
                if number > 10_000_000_000:
                    number = number / 1000
                parsed = datetime.fromtimestamp(float(number), tz=timezone.utc)
                return parsed.astimezone(timezone.utc)
            except Exception:
                return None
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            try:
                parsed = pd.to_datetime(text, utc=True).to_pydatetime()
            except Exception:
                return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def timestamp_utc_iso(value: Any) -> str | None:
    parsed = parse_utc_timestamp(value)
    return parsed.isoformat() if parsed else None


def timestamp_paris_iso(value: Any) -> str | None:
    parsed = parse_utc_timestamp(value)
    return parsed.astimezone(PARIS_TZ).isoformat() if parsed else None


def freshness_status(label: str, timestamp: Any, max_age_seconds: int) -> dict[str, Any]:
    checked_at = utc_now()
    parsed = parse_utc_timestamp(timestamp)
    if parsed is None:
        return {
            "label": label,
            "status": "absent",
            "is_fresh": False,
            "timestamp_utc": None,
            "timestamp_paris": None,
            "age_seconds": None,
            "max_age_seconds": max_age_seconds,
            "checked_at_utc": checked_at.isoformat(),
            "checked_at_paris": paris_iso(checked_at),
        }
    age_seconds = max(0.0, (checked_at - parsed).total_seconds())
    is_fresh = age_seconds <= max_age_seconds
    return {
        "label": label,
        "status": "fresh" if is_fresh else "stale",
        "is_fresh": is_fresh,
        "timestamp_utc": parsed.isoformat(),
        "timestamp_paris": parsed.astimezone(PARIS_TZ).isoformat(),
        "age_seconds": int(age_seconds),
        "max_age_seconds": max_age_seconds,
        "checked_at_utc": checked_at.isoformat(),
        "checked_at_paris": paris_iso(checked_at),
    }


def freshness_policy_payload() -> dict[str, Any]:
    return {
        "spot_max_age_seconds": MAX_SPOT_AGE_SECONDS,
        "fundamental_max_age_seconds": MAX_FUNDAMENTAL_AGE_SECONDS,
        "run_max_age_seconds": MAX_RUN_AGE_SECONDS,
        "spot_gate": "block_live_run_if_stale_or_absent",
        "fundamental_gate": "warn_if_stale_or_absent",
        "run_gate": "warn_if_latest_archive_stale",
    }


def assert_live_spot_fresh(asset: str, spot_snapshot: dict[str, Any] | None) -> dict[str, Any]:
    check = freshness_status("bitget_spot_snapshot", (spot_snapshot or {}).get("timestamp"), MAX_SPOT_AGE_SECONDS)
    if spot_snapshot is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "bitget_spot_absent",
                "asset": asset.upper(),
                "freshness": check,
                "policy": freshness_policy_payload(),
                "data_status": {"market_prices": "absent", "bitget_required": "absent"},
                "warning": "Live run blocked. No deterministic prediction was produced and no non-Bitget fallback was used.",
            },
        )
    if not check["is_fresh"]:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "bitget_spot_stale",
                "asset": asset.upper(),
                "spot_snapshot": spot_snapshot,
                "freshness": check,
                "policy": freshness_policy_payload(),
                "data_status": {"market_prices": "stale", "bitget_required": "stale"},
                "warning": "Live run blocked because the Bitget spot timestamp is stale.",
            },
        )
    return check


def probability_error(estimate: Any, simulations: int, z: float = 1.96) -> dict[str, Any]:
    try:
        p = float(estimate)
    except (TypeError, ValueError):
        return {"estimate": None, "status": "absent"}
    if not np.isfinite(p):
        return {"estimate": None, "status": "absent"}
    n = max(1, int(simulations))
    bounded = min(max(p, 0.0), 1.0)
    standard_error = math.sqrt(max(bounded * (1.0 - bounded), 0.0) / n)
    margin = z * standard_error
    return {
        "estimate": bounded,
        "sample_size": n,
        "standard_error": standard_error,
        "margin_95": margin,
        "ci95_low": max(0.0, bounded - margin),
        "ci95_high": min(1.0, bounded + margin),
        "status": "inferred_sampling_error",
    }


def monte_carlo_error_summary(distribution: dict[str, Any], regimes: dict[str, Any], simulations: int) -> dict[str, Any]:
    keys = ["prob_up", "prob_down_10", "prob_down_30", "prob_up_30", "prob_bull", "prob_bear", "prob_range"]
    probabilities = {key: probability_error(distribution.get(key), simulations) for key in keys}
    probabilities["non_classified_transition"] = probability_error(regimes.get("non_classified_transition"), simulations)
    tail_counts = {
        key: None if probabilities[key].get("estimate") is None else int(round(probabilities[key]["estimate"] * simulations))
        for key in probabilities
    }
    rare_tail_warnings = [
        f"{key} has only {count} simulated paths; treat as order of magnitude."
        for key, count in tail_counts.items()
        if count is not None and count < 30
    ]
    return {
        "status": "inferred",
        "method": "binomial_standard_error_from_simulation_count",
        "probabilities": probabilities,
        "tail_counts": tail_counts,
        "warnings": rare_tail_warnings,
    }


def metric_stats(values: list[float]) -> dict[str, Any]:
    arr = np.asarray([value for value in values if value is not None and np.isfinite(value)], dtype=float)
    if arr.size == 0:
        return {"mean": None, "std": None, "min": None, "max": None}
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0,
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def build_multi_seed_stability(
    *,
    simulate,
    model_name: str,
    returns,
    spot: float,
    horizon: int,
    simulations: int,
    fundamentals: pd.DataFrame,
    base_run_id: str,
) -> dict[str, Any]:
    seed_runs = min(max(MULTI_SEED_RUNS, 1), 10)
    sims_per_seed = min(max(100, MULTI_SEED_SIMULATIONS), max(100, int(simulations)))
    rows: list[dict[str, Any]] = []
    for index in range(seed_runs):
        stability_run_id = f"{base_run_id}_seed{index + 1}"
        kwargs = {
            "returns": returns,
            "spot": spot,
            "horizon": horizon,
            "simulations": sims_per_seed,
            "seed": seed_for(stability_run_id),
        }
        if model_name in {"correlation", "correlation_model"}:
            kwargs["fundamentals"] = fundamentals
        if model_name == "ensemble":
            kwargs["fundamentals"] = fundamentals
            kwargs["backtest_rows"] = []
        result = simulate(**kwargs)
        distribution = summarize_simulation(result["terminal_prices"], spot)
        regimes = regime_distribution(distribution)
        risk = compute_risk_metrics(result["terminal_returns"], historical_returns=returns, sample_paths=result.get("sample_paths"))
        rows.append(
            {
                "seed_index": index + 1,
                "seed_run_id": stability_run_id,
                "prob_up": distribution.get("prob_up"),
                "median_return": distribution.get("median_return"),
                "p10_return": distribution.get("p10_return"),
                "p90_return": distribution.get("p90_return"),
                "var_95": risk.get("var_95"),
                "cvar_95": risk.get("cvar_95"),
                "mean_simulated_max_drawdown": risk.get("mean_simulated_max_drawdown") or risk.get("max_drawdown"),
                "bull": regimes.get("bull"),
                "bear": regimes.get("bear"),
                "range": regimes.get("range"),
                "transition": regimes.get("non_classified_transition"),
            }
        )
    metric_names = [
        "prob_up",
        "median_return",
        "p10_return",
        "p90_return",
        "var_95",
        "cvar_95",
        "mean_simulated_max_drawdown",
        "bull",
        "bear",
        "range",
        "transition",
    ]
    stats = {metric: metric_stats([row.get(metric) for row in rows]) for metric in metric_names}
    directional_flags = [
        bool((row.get("prob_up") or 0.0) >= 0.5 and (row.get("median_return") or 0.0) >= 0.0)
        for row in rows
    ]
    stability_score = float(np.mean(directional_flags)) if directional_flags else None
    return {
        "status": "inferred",
        "seed_runs": seed_runs,
        "simulations_per_seed": sims_per_seed,
        "metrics": stats,
        "directional_stability": stability_score,
        "bias_stability_label": (
            "stable" if stability_score is not None and stability_score >= 0.8 else
            "mixed" if stability_score is not None and stability_score >= 0.4 else
            "unstable"
        ),
        "sample": rows,
        "note": "Multi-seed stability is an internal simulation robustness diagnostic, not an observed market fact.",
    }


def cache_key_for(endpoint: str, payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        {
            "endpoint": endpoint,
            "payload": payload,
            "api_version": API_VERSION,
            "model_version": MODEL_VERSION,
            "git_commit": GIT_COMMIT,
        },
        ensure_ascii=True,
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def cache_get(cache_key: str) -> dict[str, Any] | None:
    if CACHE_TTL_SECONDS <= 0:
        return None
    now = time.time()
    try:
        with sqlite3.connect(API_RUNTIME_DB) as conn:
            row = conn.execute(
                "SELECT response_json, created_at, expires_at FROM response_cache WHERE cache_key = ? AND expires_at > ?",
                (cache_key, now),
            ).fetchone()
        if not row:
            return None
        payload = json.loads(row[0])
        payload["cache"] = {
            "hit": True,
            "cache_key": cache_key[:12],
            "created_at": datetime.fromtimestamp(float(row[1]), tz=timezone.utc).isoformat(),
            "created_at_utc": datetime.fromtimestamp(float(row[1]), tz=timezone.utc).isoformat(),
            "created_at_paris": paris_iso(datetime.fromtimestamp(float(row[1]), tz=timezone.utc)),
            "expires_at": datetime.fromtimestamp(float(row[2]), tz=timezone.utc).isoformat(),
            "expires_at_utc": datetime.fromtimestamp(float(row[2]), tz=timezone.utc).isoformat(),
            "expires_at_paris": paris_iso(datetime.fromtimestamp(float(row[2]), tz=timezone.utc)),
            "ttl_seconds": CACHE_TTL_SECONDS,
        }
        return payload
    except Exception:
        return None


def cache_set(cache_key: str, payload: dict[str, Any]) -> None:
    if CACHE_TTL_SECONDS <= 0:
        return
    now = time.time()
    expires_at = now + CACHE_TTL_SECONDS
    stored = dict(payload)
    stored["cache"] = {
        "hit": False,
        "cache_key": cache_key[:12],
        "created_at": datetime.fromtimestamp(now, tz=timezone.utc).isoformat(),
        "created_at_utc": datetime.fromtimestamp(now, tz=timezone.utc).isoformat(),
        "created_at_paris": paris_iso(datetime.fromtimestamp(now, tz=timezone.utc)),
        "expires_at": datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
        "expires_at_utc": datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
        "expires_at_paris": paris_iso(datetime.fromtimestamp(expires_at, tz=timezone.utc)),
        "ttl_seconds": CACHE_TTL_SECONDS,
    }
    try:
        with sqlite3.connect(API_RUNTIME_DB) as conn:
            conn.execute("DELETE FROM response_cache WHERE expires_at <= ?", (now,))
            conn.execute(
                """
                INSERT OR REPLACE INTO response_cache (cache_key, created_at, expires_at, response_json)
                VALUES (?, ?, ?, ?)
                """,
                (cache_key, now, expires_at, json.dumps(stored, ensure_ascii=True, default=str)),
            )
            conn.commit()
    except Exception:
        return


def _response_horizons(payload: dict[str, Any]) -> list[int]:
    if isinstance(payload.get("horizons"), list):
        return [int(item) for item in payload["horizons"]]
    if payload.get("horizon") is not None:
        return [int(payload["horizon"])]
    frames = payload.get("frames") if isinstance(payload.get("frames"), list) else []
    return [int(frame["horizon"]) for frame in frames if frame.get("horizon") is not None]


def _response_run_ids(payload: dict[str, Any]) -> list[str]:
    if payload.get("run_id"):
        return [str(payload["run_id"])]
    frames = payload.get("frames") if isinstance(payload.get("frames"), list) else []
    return [str(frame["run_id"]) for frame in frames if frame.get("run_id")]


def _response_reference_spot(payload: dict[str, Any]) -> str | None:
    provenance = payload.get("provenance") if isinstance(payload.get("provenance"), dict) else {}
    if provenance.get("reference_spot"):
        return str(provenance["reference_spot"])
    summary = payload.get("provenance_summary") if isinstance(payload.get("provenance_summary"), dict) else {}
    reference_spots = summary.get("reference_spots")
    if isinstance(reference_spots, list) and reference_spots:
        return str(reference_spots[0])
    return None


def _response_report_date(payload: dict[str, Any]) -> str | None:
    provenance = payload.get("provenance") if isinstance(payload.get("provenance"), dict) else {}
    if provenance.get("report_date"):
        return str(provenance["report_date"])
    summary = payload.get("provenance_summary") if isinstance(payload.get("provenance_summary"), dict) else {}
    if summary.get("report_date"):
        return str(summary["report_date"])
    frames = payload.get("frames") if isinstance(payload.get("frames"), list) else []
    for frame in frames:
        frame_provenance = frame.get("provenance") if isinstance(frame.get("provenance"), dict) else {}
        if frame_provenance.get("report_date"):
            return str(frame_provenance["report_date"])
    return None


def _archive_markdown(payload: dict[str, Any], archive: dict[str, Any]) -> str:
    version = payload.get("version") if isinstance(payload.get("version"), dict) else {}
    fundamentals = payload.get("fundamental_inputs") if isinstance(payload.get("fundamental_inputs"), dict) else {}
    if not fundamentals and isinstance(payload.get("frames"), list) and payload["frames"]:
        fundamentals = payload["frames"][0].get("fundamental_inputs") or {}
    return "\n".join(
        [
            "# API Run Archive",
            "",
            f"- Archive ID: `{archive['archive_id']}`",
            f"- Endpoint: {archive['endpoint']}",
            f"- Created at UTC: {archive['created_at']}",
            f"- Created at Europe/Paris: {archive.get('created_at_paris') or 'unknown'}",
            f"- Asset: {archive.get('asset') or 'unknown'}",
            f"- Model: {archive.get('model') or 'unknown'}",
            f"- Horizons: {archive.get('horizons')}",
            f"- Run IDs: {archive.get('run_ids')}",
            f"- Report date UTC: {archive.get('report_date') or 'unknown'}",
            f"- Report date Europe/Paris: {archive.get('report_date_paris') or 'unknown'}",
            f"- Reference spot: {archive.get('reference_spot') or 'unknown'}",
            f"- API version: {version.get('api_version') or API_VERSION}",
            f"- Git commit: {version.get('git_commit') or GIT_COMMIT}",
            f"- Data status: {payload.get('data_status')}",
            f"- Fundamental status: {fundamentals.get('status') or 'unknown'}",
            f"- Fundamental real fields: {fundamentals.get('real_fields') or []}",
            f"- Fundamental absent fields: {fundamentals.get('absent_fields') or []}",
            "",
            "This archive stores the API response payload for auditability. It is probabilistic output only, not financial advice and not a deterministic prediction.",
            "",
        ]
    )


def attach_archive(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    created = utc_now()
    safe_endpoint = endpoint.strip("/").replace("/", "_") or "root"
    asset = str(payload.get("asset") or "unknown").upper()
    archive_id = f"{created.strftime('%Y%m%dT%H%M%SZ')}_{safe_endpoint}_{asset}_{uuid.uuid4().hex[:8]}"
    archive_dir = API_ARCHIVE_DIR / created.strftime("%Y%m%d")
    archive_json_path = archive_dir / f"{archive_id}.json"
    archive_markdown_path = archive_dir / f"{archive_id}.md"
    archive = {
        "status": "stored",
        "archive_id": archive_id,
        "endpoint": endpoint,
        "created_at": created.isoformat(),
        "created_at_utc": created.isoformat(),
        "created_at_paris": paris_iso(created),
        "asset": asset,
        "model": payload.get("model"),
        "horizons": _response_horizons(payload),
        "run_ids": _response_run_ids(payload),
        "report_date": _response_report_date(payload),
        "report_date_utc": _response_report_date(payload),
        "report_date_paris": timestamp_paris_iso(_response_report_date(payload)),
        "reference_spot": _response_reference_spot(payload),
        "timezone_policy": TIMEZONE_POLICY,
        "sqlite_db": str(API_RUNTIME_DB),
        "sqlite_table": "run_archive",
        "json_path": str(archive_json_path),
        "markdown_path": str(archive_markdown_path),
        "storage_note": "Runtime archive on the API host; persistence depends on the hosting filesystem.",
    }
    if isinstance(payload.get("provenance_summary"), dict):
        payload["provenance_summary"]["archive_id"] = archive_id
    payload["archive"] = archive
    try:
        archive_dir.mkdir(parents=True, exist_ok=True)
        response_json = json.dumps(payload, ensure_ascii=True, indent=2, default=str)
        archive_json_path.write_text(response_json, encoding="utf-8")
        archive_markdown_path.write_text(_archive_markdown(payload, archive), encoding="utf-8")
        version = payload.get("version") if isinstance(payload.get("version"), dict) else {}
        with sqlite3.connect(API_RUNTIME_DB) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO run_archive (
                    archive_id, endpoint, asset, model, horizons_json, run_ids_json,
                    report_date, reference_spot, api_version, git_commit, status,
                    archive_json_path, archive_markdown_path, response_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    archive_id,
                    endpoint,
                    asset,
                    str(payload.get("model") or ""),
                    json.dumps(archive["horizons"], ensure_ascii=True),
                    json.dumps(archive["run_ids"], ensure_ascii=True),
                    archive.get("report_date"),
                    archive.get("reference_spot"),
                    str(version.get("api_version") or API_VERSION),
                    str(version.get("git_commit") or GIT_COMMIT),
                    str(payload.get("status") or "ok"),
                    str(archive_json_path),
                    str(archive_markdown_path),
                    response_json,
                    created.timestamp(),
                ),
            )
            conn.commit()
    except Exception as exc:
        archive.update({"status": "failed", "error": str(exc)})
    return archive


def latest_runtime_archive() -> dict[str, Any]:
    try:
        with sqlite3.connect(API_RUNTIME_DB) as conn:
            row = conn.execute(
                """
                SELECT archive_id, endpoint, asset, model, horizons_json, run_ids_json,
                       report_date, reference_spot, api_version, git_commit, status,
                       archive_json_path, archive_markdown_path, created_at
                FROM run_archive
                ORDER BY created_at DESC
                LIMIT 1
                """
            ).fetchone()
        if not row:
            return {"status": "absent", "reason": "No runtime archive row found."}
        created_at = float(row[13])
        return {
            "status": "stored" if row[10] else "unknown",
            "archive_id": row[0],
            "endpoint": row[1],
            "asset": row[2],
            "model": row[3],
            "horizons": json.loads(row[4] or "[]"),
            "run_ids": json.loads(row[5] or "[]"),
            "report_date": row[6],
            "report_date_utc": row[6],
            "report_date_paris": timestamp_paris_iso(row[6]),
            "reference_spot": row[7],
            "api_version": row[8],
            "git_commit": row[9],
            "run_status": row[10],
            "json_path": row[11],
            "markdown_path": row[12],
            "created_at": datetime.fromtimestamp(created_at, tz=timezone.utc).isoformat(),
            "created_at_utc": datetime.fromtimestamp(created_at, tz=timezone.utc).isoformat(),
            "created_at_paris": paris_iso(datetime.fromtimestamp(created_at, tz=timezone.utc)),
            "timezone_policy": TIMEZONE_POLICY,
            "age_seconds": max(0, int(time.time() - created_at)),
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def latest_external_archive() -> dict[str, Any]:
    archive_root = ROOT / "external_archive" / "live_runs"
    try:
        candidates = sorted(archive_root.rglob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
        if not candidates:
            return {"status": "absent", "reason": "No bundled external archive snapshot found."}
        path = candidates[0]
        payload = json.loads(path.read_text(encoding="utf-8"))
        return {
            "status": "present",
            "path": str(path),
            "archive_id": payload.get("archive_id"),
            "created_at": payload.get("created_at"),
            "created_at_utc": payload.get("created_at"),
            "created_at_paris": timestamp_paris_iso(payload.get("created_at")),
            "api_version": payload.get("api_version"),
            "git_commit": payload.get("git_commit"),
            "horizons": payload.get("horizons"),
            "fundamental_real_fields": (payload.get("fundamental_inputs") or {}).get("real_fields"),
            "fundamental_absent_fields": (payload.get("fundamental_inputs") or {}).get("absent_fields"),
            "note": "Bundled GitHub archive snapshot; may lag the live runtime archive.",
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def list_runtime_archives(asset: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
    try:
        query = """
            SELECT archive_id, endpoint, asset, model, horizons_json, run_ids_json,
                   report_date, reference_spot, api_version, git_commit, status,
                   archive_json_path, archive_markdown_path, created_at, response_json
            FROM run_archive
        """
        params: list[Any] = []
        if asset:
            query += " WHERE asset = ?"
            params.append(asset.upper())
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(max(1, int(limit)))
        with sqlite3.connect(API_RUNTIME_DB) as conn:
            rows = conn.execute(query, params).fetchall()
        archives = []
        for row in rows:
            created_at = float(row[13])
            archives.append(
                {
                    "archive_id": row[0],
                    "endpoint": row[1],
                    "asset": row[2],
                    "model": row[3],
                    "horizons": json.loads(row[4] or "[]"),
                    "run_ids": json.loads(row[5] or "[]"),
                    "report_date_utc": row[6],
                    "report_date_paris": timestamp_paris_iso(row[6]),
                    "reference_spot": row[7],
                    "api_version": row[8],
                    "git_commit": row[9],
                    "status": row[10],
                    "json_path": row[11],
                    "markdown_path": row[12],
                    "created_at_utc": datetime.fromtimestamp(created_at, tz=timezone.utc).isoformat(),
                    "created_at_paris": paris_iso(datetime.fromtimestamp(created_at, tz=timezone.utc)),
                    "age_seconds": max(0, int(time.time() - created_at)),
                }
            )
        return archives
    except Exception:
        return []


def load_runtime_archive_payload(archive_id: str) -> dict[str, Any] | None:
    try:
        with sqlite3.connect(API_RUNTIME_DB) as conn:
            row = conn.execute("SELECT response_json FROM run_archive WHERE archive_id = ?", (archive_id,)).fetchone()
        if row:
            return json.loads(row[0])
    except Exception:
        pass
    return None


def parse_money(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace("$", "").replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def frame_by_horizon(payload: dict[str, Any]) -> dict[int, dict[str, Any]]:
    frames = payload.get("frames") if isinstance(payload.get("frames"), list) else []
    return {int(frame.get("horizon")): frame for frame in frames if frame.get("horizon") is not None}


def _delta(new_value: Any, old_value: Any) -> float | None:
    try:
        if new_value is None or old_value is None:
            return None
        return float(new_value) - float(old_value)
    except (TypeError, ValueError):
        return None


def compare_run_payload(current: dict[str, Any], previous: dict[str, Any]) -> dict[str, Any]:
    current_archive = current.get("archive") or {}
    previous_archive = previous.get("archive") or {}
    current_spot = parse_money(_response_reference_spot(current))
    previous_spot = parse_money(_response_reference_spot(previous))
    current_frames = frame_by_horizon(current)
    previous_frames = frame_by_horizon(previous)
    horizons = sorted(set(current_frames) & set(previous_frames))
    frame_changes = []
    for horizon in horizons:
        cur = current_frames[horizon]
        prev = previous_frames[horizon]
        cur_dist, prev_dist = cur.get("distribution") or {}, prev.get("distribution") or {}
        cur_risk, prev_risk = cur.get("risk_metrics") or {}, prev.get("risk_metrics") or {}
        cur_conf, prev_conf = cur.get("confidence") or {}, prev.get("confidence") or {}
        cur_reg, prev_reg = cur.get("regime_distribution") or {}, prev.get("regime_distribution") or {}
        frame_changes.append(
            {
                "horizon": horizon,
                "current_run_id": cur.get("run_id"),
                "previous_run_id": prev.get("run_id"),
                "median_return_delta": _delta(cur_dist.get("median_return"), prev_dist.get("median_return")),
                "prob_up_delta": _delta(cur_dist.get("prob_up"), prev_dist.get("prob_up")),
                "var_95_delta": _delta(cur_risk.get("var_95"), prev_risk.get("var_95")),
                "cvar_95_delta": _delta(cur_risk.get("cvar_95"), prev_risk.get("cvar_95")),
                "confidence_delta": _delta(cur_conf.get("score"), prev_conf.get("score")),
                "bull_delta": _delta(cur_reg.get("bull"), prev_reg.get("bull")),
                "bear_delta": _delta(cur_reg.get("bear"), prev_reg.get("bear")),
                "range_delta": _delta(cur_reg.get("range"), prev_reg.get("range")),
                "transition_delta": _delta(cur_reg.get("non_classified_transition"), prev_reg.get("non_classified_transition")),
            }
        )
    return {
        "status": "ok",
        "comparison_type": "current_vs_previous_archive",
        "current_archive_id": current_archive.get("archive_id"),
        "previous_archive_id": previous_archive.get("archive_id"),
        "current_report_date_utc": _response_report_date(current),
        "previous_report_date_utc": _response_report_date(previous),
        "current_reference_spot": _response_reference_spot(current),
        "previous_reference_spot": _response_reference_spot(previous),
        "spot_delta": _delta(current_spot, previous_spot),
        "spot_delta_pct": ((current_spot / previous_spot) - 1.0) if current_spot and previous_spot else None,
        "frames": frame_changes,
        "version": version_payload(),
        "warning": "Run comparison is diagnostic only. It is not a deterministic prediction.",
    }


def build_alerts_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    freshness = payload.get("freshness") if isinstance(payload.get("freshness"), dict) else {}
    stored_spot_freshness = freshness.get("spot") if isinstance(freshness.get("spot"), dict) else {}
    stored_fundamental_freshness = freshness.get("fundamentals") if isinstance(freshness.get("fundamentals"), dict) else {}
    provenance = payload.get("provenance_summary") if isinstance(payload.get("provenance_summary"), dict) else {}
    reference_timestamps = provenance.get("reference_spot_timestamps") if isinstance(provenance.get("reference_spot_timestamps"), list) else []
    spot_timestamp = stored_spot_freshness.get("timestamp_utc") or (reference_timestamps[0] if reference_timestamps else None)
    fundamentals = payload.get("fundamental_inputs") if isinstance(payload.get("fundamental_inputs"), dict) else {}
    fundamental_timestamp = stored_fundamental_freshness.get("timestamp_utc") or fundamentals.get("timestamp")
    spot_freshness = freshness_status("reference_spot", spot_timestamp, MAX_SPOT_AGE_SECONDS)
    fundamental_freshness = freshness_status("fundamental_snapshot", fundamental_timestamp, MAX_FUNDAMENTAL_AGE_SECONDS)
    if spot_freshness and not spot_freshness.get("is_fresh"):
        alerts.append({"level": "blocker", "type": "spot_stale", "message": "Bitget spot snapshot is stale.", "details": spot_freshness})
    if fundamental_freshness and not fundamental_freshness.get("is_fresh"):
        alerts.append({"level": "warning", "type": "fundamentals_stale", "message": "Fundamental snapshot is stale or absent.", "details": fundamental_freshness})
    for frame in payload.get("frames") or []:
        horizon = frame.get("horizon")
        risk = frame.get("risk_metrics") or {}
        confidence = frame.get("confidence") or {}
        regimes = frame.get("regime_distribution") or {}
        if (risk.get("var_95") or 0.0) > 0.30:
            alerts.append({"level": "warning", "type": "var95_above_30pct", "horizon": horizon, "value": risk.get("var_95")})
        if (confidence.get("score") is not None) and float(confidence.get("score")) < 50:
            alerts.append({"level": "warning", "type": "confidence_below_50", "horizon": horizon, "value": confidence.get("score")})
        if (regimes.get("non_classified_transition") or 0.0) > 0.25:
            alerts.append({"level": "warning", "type": "transition_above_25pct", "horizon": horizon, "value": regimes.get("non_classified_transition")})
    return alerts


def backtest_summary_payload(asset: str = "BTC") -> dict[str, Any]:
    try:
        logger = setup_logger()
        price_frame = load_market_prices(asset, logger, days=1500, allow_online=True)
        rows = run_backtest(price_frame, asset, "benchmark_walk_forward", horizons=tuple(DEFAULT_MULTIFRAME_HORIZONS))
        return {
            "status": "ok",
            "asset": asset.upper(),
            "rows": rows,
            "benchmark": "rolling_normal_random_walk_style_baseline",
            "metrics": ["hit_rate", "brier_score", "calibration_error", "mean_absolute_error", "interval_coverage"],
            "limitations": [
                "Backtest summary is a visible baseline diagnostic, not proof of future calibration.",
                "Full model walk-forward calibration should be expanded before institutional use.",
            ],
            "version": version_payload(),
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc), "rows": [], "version": version_payload()}


def dashboard_html() -> str:
    return """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Quant BTC Model Dashboard</title>
  <style>
    body { margin: 0; font-family: Arial, sans-serif; background: #f7f8fb; color: #101114; }
    header { padding: 18px 22px; background: #101114; color: white; display: flex; gap: 16px; align-items: center; justify-content: space-between; }
    main { max-width: 1180px; margin: 0 auto; padding: 20px; }
    button { border: 0; background: #1f6feb; color: white; padding: 10px 14px; border-radius: 6px; cursor: pointer; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
    .card { background: white; border: 1px solid #d8dee8; border-radius: 8px; padding: 14px; }
    .muted { color: #687385; font-size: 13px; }
    table { width: 100%; border-collapse: collapse; background: white; border: 1px solid #d8dee8; }
    th, td { padding: 10px; border-bottom: 1px solid #e6eaf0; text-align: right; }
    th:first-child, td:first-child { text-align: left; }
    .warn { color: #a15c00; }
    .bad { color: #b42318; }
  </style>
</head>
<body>
  <header>
    <div>
      <strong>Quant BTC Model</strong>
      <div class="muted">Dashboard probabiliste live, source Bitget</div>
    </div>
    <button onclick="loadRun()">Actualiser</button>
  </header>
  <main>
    <section class="grid" id="summary"></section>
    <h3>Multi-frame</h3>
    <div id="frames"></div>
    <h3>Alertes</h3>
    <div id="alerts" class="grid"></div>
  </main>
  <script>
    const fmtPct = v => v == null ? "absent" : (v * 100).toFixed(2) + "%";
    const fmtUsd = v => v == null ? "absent" : "$" + Number(v).toLocaleString(undefined, {maximumFractionDigits: 0});
    async function loadRun() {
      document.getElementById("summary").innerHTML = "<div class='card'>Chargement...</div>";
      const response = await fetch("/multi-run", { method: "POST", headers: {"content-type": "application/json"}, body: JSON.stringify({asset: "BTC"}) });
      const data = await response.json();
      const prov = data.provenance_summary || {};
      const archive = data.archive || {};
      document.getElementById("summary").innerHTML = [
        ["Spot", (prov.reference_spots || ["absent"])[0]],
        ["Archive", archive.archive_id || "absent"],
        ["Date UTC", prov.report_date_utc || "absent"],
        ["Statut", data.status || "absent"]
      ].map(([k,v]) => `<div class='card'><div class='muted'>${k}</div><strong>${v}</strong></div>`).join("");
      document.getElementById("frames").innerHTML = `<table><tr><th>Horizon</th><th>Médiane</th><th>P10</th><th>P90</th><th>P(up)</th><th>VaR95</th><th>CVaR95</th><th>Conf.</th></tr>${(data.frames || []).map(f => {
        const d = f.distribution || {}, r = f.risk_metrics || {}, c = f.confidence || {};
        return `<tr><td>${f.horizon}j</td><td>${fmtUsd(d.median_price)}</td><td>${fmtUsd(d.p10_price)}</td><td>${fmtUsd(d.p90_price)}</td><td>${fmtPct(d.prob_up)}</td><td>${fmtPct(r.var_95)}</td><td>${fmtPct(r.cvar_95)}</td><td>${c.score ?? "absent"}/100</td></tr>`;
      }).join("")}</table>`;
      document.getElementById("alerts").innerHTML = (data.alerts || []).map(a => `<div class='card ${a.level === "blocker" ? "bad" : "warn"}'><strong>${a.type}</strong><div>${a.message || ""}</div></div>`).join("") || "<div class='card'>Aucune alerte.</div>";
    }
    loadRun();
  </script>
</body>
</html>"""


def simple_pdf_bytes(title: str, lines: list[str]) -> bytes:
    escaped_lines = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")[:110] for line in [title, "", *lines]]
    content_lines = ["BT", "/F1 11 Tf", "50 780 Td", "14 TL"]
    for index, line in enumerate(escaped_lines):
        if index:
            content_lines.append("T*")
        content_lines.append(f"({line}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii"))
    return bytes(pdf)


def audit_payload() -> dict[str, Any]:
    fundamentals = load_processed_fundamental_inputs("BTC")
    real_fields = set(fundamentals.get("real_fields") or [])
    absent_fields = set(fundamentals.get("absent_fields") or [])
    missing_required = sorted(set(REQUIRED_AUDIT_REAL_FIELDS) - real_fields)
    unexpected_absent = sorted(absent_fields - set(ALLOWED_AUDIT_ABSENT_FIELDS))
    runtime_archive = latest_runtime_archive()
    external_archive = latest_external_archive()

    blockers: list[str] = []
    warnings: list[str] = []
    if missing_required:
        warnings.append(f"Required live fundamental fields missing from latest processed snapshot: {missing_required}")
    if unexpected_absent:
        warnings.append(f"Unexpected absent fundamental fields in latest processed snapshot: {unexpected_absent}")
    if runtime_archive.get("status") != "stored":
        warnings.append("No stored runtime archive is available yet; run /multi-run to create one.")
    if runtime_archive.get("age_seconds") is not None and int(runtime_archive.get("age_seconds") or 0) > MAX_RUN_AGE_SECONDS:
        warnings.append(f"Latest runtime archive is older than {MAX_RUN_AGE_SECONDS} seconds.")
    fundamental_freshness = freshness_status("fundamental_snapshot", fundamentals.get("timestamp"), MAX_FUNDAMENTAL_AGE_SECONDS)
    if not fundamental_freshness["is_fresh"]:
        warnings.append("Latest processed fundamental snapshot is stale or absent.")
    runtime_freshness = freshness_status("latest_runtime_archive", runtime_archive.get("created_at_utc"), MAX_RUN_AGE_SECONDS)

    checked_at = utc_now()
    return {
        "status": "ok" if not blockers else "blocked",
        "service": "quant-btc-model",
        "audit_kind": "preflight_governance_audit",
        "checked_at": checked_at.isoformat(),
        "checked_at_utc": checked_at.isoformat(),
        "checked_at_paris": paris_iso(checked_at),
        "user_display_timezone": USER_DISPLAY_TIMEZONE,
        "timezone_policy": TIMEZONE_POLICY,
        "ready_for_gpt_live_analysis": not blockers,
        "can_attempt_live_run": True,
        "latest_outputs_auditable": runtime_archive.get("status") == "stored",
        "blockers": blockers,
        "warnings": warnings,
        "required_gpt_flow": [
            "Call this /audit endpoint before analysis.",
            "If ready_for_gpt_live_analysis is true, call /multi-run or Cloudflare /run for the fresh multi-frame run.",
            "Never reuse numbers from /audit as model forecasts; /audit is health/provenance only.",
            "One analysis must use one fresh run/archive_id. Do not mix numbers from separate run responses unless the user asks for a comparison.",
            "For every precise model number, cite model_run_id, report_date, reference_spot, source and status.",
            "Show every report date and spot timestamp in UTC and Europe/Paris user time.",
        ],
        "source_policy": SOURCE_POLICY,
        "default_frames": DEFAULT_MULTIFRAME_HORIZONS,
        "required_real_fields": REQUIRED_AUDIT_REAL_FIELDS,
        "allowed_absent_fields": ALLOWED_AUDIT_ABSENT_FIELDS,
        "freshness_policy": freshness_policy_payload(),
        "freshness": {
            "fundamentals": fundamental_freshness,
            "latest_runtime_archive": runtime_freshness,
        },
        "fundamental_snapshot": fundamentals,
        "latest_runtime_archive": runtime_archive,
        "latest_external_archive": external_archive,
        "monitoring": {
            "github_workflows": {
                "monitor": ".github/workflows/monitor-api.yml",
                "archive": ".github/workflows/archive-live-run.yml",
                "ci": ".github/workflows/ci.yml",
            },
            "visible_alert_issue_marker": "[quant-btc-monitor-alert]",
            "monitor_rule": "If the monitor fails, GitHub Actions opens or updates a visible alert issue.",
        },
        "data_status_policy": {
            "prices": "must be real from Bitget for live conclusions",
            "simulations": "inferred",
            "risk_metrics": "inferred",
            "liquidations": "real only when Bitget WebSocket push is observed; otherwise absent",
            "non_bitget_exchange_fallback": "forbidden",
        },
        "version": version_payload(),
        "warning": "Audit output is not a market forecast. It only tells the GPT whether a live probabilistic run is governance-ready.",
    }


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def regime_distribution(distribution: dict[str, Any]) -> dict[str, Any]:
    bull = float(distribution.get("prob_bull") or 0.0)
    bear = float(distribution.get("prob_bear") or 0.0)
    range_ = float(distribution.get("prob_range") or 0.0)
    total = bull + bear + range_
    residual = max(0.0, 1.0 - total)
    return {
        "bull": bull,
        "bear": bear,
        "range": range_,
        "classified_total": total,
        "non_classified_transition": residual,
        "is_complete": abs(total - 1.0) <= 0.01,
        "note": (
            "Regime split is complete."
            if abs(total - 1.0) <= 0.01
            else "Regime split is incomplete; include non_classified_transition."
        ),
    }


def extract_report_date(report_markdown: str) -> str | None:
    for line in report_markdown.splitlines():
        if line.startswith("Generated: "):
            return line.replace("Generated: ", "", 1).strip()
    return None


def extract_reference_spot(report_markdown: str) -> str | None:
    for line in report_markdown.splitlines():
        if line.startswith("- Reference spot price: "):
            return line.replace("- Reference spot price: ", "", 1).strip()
        if line.startswith("- Latest spot used: "):
            return line.replace("- Latest spot used: ", "", 1).strip()
    return None


def extract_report_bullet(report_markdown: str, label: str) -> str | None:
    prefix = f"- {label}: "
    for line in report_markdown.splitlines():
        if line.startswith(prefix):
            return line.replace(prefix, "", 1).strip()
    return None


def extract_bullet_value(report_markdown: str, label: str) -> str | None:
    prefix = f"- {label}: "
    for line in report_markdown.splitlines():
        if line.startswith(prefix):
            return line.replace(prefix, "", 1).strip()
    return None


def run_cli(payload: RunRequest) -> dict[str, Any]:
    command = [
        sys.executable,
        str(ROOT / "src" / "main.py"),
        "--asset",
        payload.asset.upper(),
        "--horizon",
        str(payload.horizon),
        "--simulations",
        str(payload.simulations),
        "--model",
        payload.model,
    ]
    if payload.skip_corpus:
        command.append("--skip-corpus")
    if payload.no_online:
        command.append("--no-online")
    if payload.spot_override_price is not None:
        command.extend(["--spot-override-price", str(payload.spot_override_price)])
        if payload.spot_override_timestamp:
            command.extend(["--spot-override-timestamp", payload.spot_override_timestamp])
        if payload.spot_override_source:
            command.extend(["--spot-override-source", payload.spot_override_source])

    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=int(os.getenv("RUN_TIMEOUT_SECONDS", "280")),
        check=False,
    )
    stdout = completed.stdout.strip().splitlines()
    parsed = {}
    if stdout:
        try:
            parsed = json.loads(stdout[-1])
        except json.JSONDecodeError:
            parsed = {}
    if completed.returncode != 0 or "error" in parsed:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Model run failed.",
                "stdout": completed.stdout[-4000:],
                "stderr": completed.stderr[-4000:],
                "parsed": parsed,
            },
        )
    run_id = parsed.get("run_id")
    if not run_id:
        raise HTTPException(status_code=500, detail="Model run did not return a run_id.")
    summary_path = SUMMARY_DIR / f"{run_id}_summary.json"
    if not summary_path.exists():
        raise HTTPException(status_code=500, detail=f"Run summary not found for {run_id}.")
    return json.loads(summary_path.read_text(encoding="utf-8"))


def version_payload() -> dict[str, Any]:
    return {
        "status": "ok",
        "api_version": API_VERSION,
        "model_version": MODEL_VERSION,
        "schema_version": SCHEMA_VERSION,
        "git_commit": GIT_COMMIT,
        "execution_environment": os.getenv("RENDER_SERVICE_NAME", "local_or_custom"),
        "user_display_timezone": USER_DISPLAY_TIMEZONE,
        "timezone_policy": TIMEZONE_POLICY,
        "max_api_simulations": MAX_API_SIMULATIONS,
        "default_api_simulations": DEFAULT_API_SIMULATIONS,
        "default_multiframe_simulations": DEFAULT_MULTIFRAME_SIMULATIONS,
        "default_multiframe_horizons": DEFAULT_MULTIFRAME_HORIZONS,
        "rate_limit_runs_per_minute": RATE_LIMIT_RUNS_PER_MINUTE,
        "rate_limit_window_seconds": RATE_LIMIT_WINDOW_SECONDS,
        "cache_ttl_seconds": CACHE_TTL_SECONDS,
        "freshness_policy": freshness_policy_payload(),
        "multi_seed_runs": MULTI_SEED_RUNS,
        "multi_seed_simulations": MULTI_SEED_SIMULATIONS,
        "new_capabilities": [
            "data_freshness_gate",
            "monte_carlo_error_margins",
            "multi_seed_stability",
            "expanded_drawdown_metrics",
            "compare_runs",
            "alerts",
            "dashboard_html",
            "pdf_report",
            "liquidity_options_etf_explainability_diagnostics",
        ],
    }


def fetch_realtime_spot_snapshot(asset: str) -> dict[str, Any] | None:
    if asset.upper() != "BTC":
        return None
    url = "https://api.bitget.com/api/v2/spot/market/tickers?symbol=BTCUSDT"
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "quant-btc-model/1.0"})
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        data = payload.get("data") or []
        if payload.get("code") != "00000" or not data:
            return None
        ticker = data[0]
        price = float(ticker["lastPr"])
        timestamp_ms = int(ticker.get("ts") or payload.get("requestTime"))
        timestamp_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(timestamp_ms / 1000))
        snapshot = {
            "price": price,
            "timestamp": timestamp_utc,
            "timestamp_utc": timestamp_utc,
            "timestamp_paris": timestamp_paris_iso(timestamp_utc),
            "source": "bitget_btcusdt_spot_ticker_realtime_snapshot",
            "bid": float(ticker["bidPr"]) if ticker.get("bidPr") is not None else None,
            "ask": float(ticker["askPr"]) if ticker.get("askPr") is not None else None,
            "high_24h": float(ticker["high24h"]) if ticker.get("high24h") is not None else None,
            "low_24h": float(ticker["low24h"]) if ticker.get("low24h") is not None else None,
            "base_volume_24h": float(ticker["baseVolume"]) if ticker.get("baseVolume") is not None else None,
            "quote_volume_24h": float(ticker["quoteVolume"]) if ticker.get("quoteVolume") is not None else None,
        }
        snapshot["freshness"] = freshness_status("bitget_spot_snapshot", timestamp_utc, MAX_SPOT_AGE_SECONDS)
        return snapshot
    except Exception:
        return None


def format_price(value: float | None) -> str | None:
    if value is None:
        return None
    return f"${float(value):,.2f}"


def _request_json(url: str, timeout: int = 10) -> dict[str, Any] | None:
    request = urllib.request.Request(url, headers={"User-Agent": "quant-btc-model/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_bitget_liquidity_snapshot(asset: str) -> dict[str, Any]:
    if asset.upper() != "BTC":
        return {"status": "absent", "reason": "Only BTCUSDT liquidity is configured."}
    url = "https://api.bitget.com/api/v2/spot/market/orderbook?symbol=BTCUSDT&type=step0&limit=50"
    try:
        payload = _request_json(url, timeout=10) or {}
        data = payload.get("data") or {}
        bids = [(float(row[0]), float(row[1])) for row in data.get("bids", []) if len(row) >= 2]
        asks = [(float(row[0]), float(row[1])) for row in data.get("asks", []) if len(row) >= 2]
        if payload.get("code") != "00000" or not bids or not asks:
            return {"status": "absent", "source": "bitget_spot_orderbook", "error": payload.get("msg") or "empty_orderbook"}
        best_bid, best_ask = bids[0][0], asks[0][0]
        mid = (best_bid + best_ask) / 2.0
        spread_bps = ((best_ask - best_bid) / mid) * 10000.0 if mid > 0 else None

        def depth(side: list[tuple[float, float]], pct: float, direction: str) -> float:
            if direction == "bid":
                rows = [(price, size) for price, size in side if price >= mid * (1.0 - pct)]
            else:
                rows = [(price, size) for price, size in side if price <= mid * (1.0 + pct)]
            return float(sum(price * size for price, size in rows))

        bid_depth_1 = depth(bids, 0.01, "bid")
        ask_depth_1 = depth(asks, 0.01, "ask")
        bid_depth_2 = depth(bids, 0.02, "bid")
        ask_depth_2 = depth(asks, 0.02, "ask")
        imbalance_1 = (bid_depth_1 - ask_depth_1) / max(bid_depth_1 + ask_depth_1, 1e-9)
        return {
            "status": "real",
            "source": "bitget_spot_orderbook",
            "timestamp_utc": timestamp_utc_iso(data.get("ts")) or utc_iso(),
            "timestamp_paris": timestamp_paris_iso(data.get("ts")) or paris_iso(),
            "best_bid": best_bid,
            "best_ask": best_ask,
            "mid_price": mid,
            "spread_bps": spread_bps,
            "bid_depth_usdt_1pct": bid_depth_1,
            "ask_depth_usdt_1pct": ask_depth_1,
            "bid_depth_usdt_2pct": bid_depth_2,
            "ask_depth_usdt_2pct": ask_depth_2,
            "order_book_imbalance_1pct": imbalance_1,
            "estimated_slippage_note": "Depth is top-50 level not full market impact; use as liquidity proxy only.",
        }
    except Exception as exc:
        return {"status": "absent", "source": "bitget_spot_orderbook", "error": str(exc)}


def fetch_options_snapshot() -> dict[str, Any]:
    url = "https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option"
    try:
        payload = _request_json(url, timeout=12) or {}
        rows = payload.get("result") or []
        ivs: list[float] = []
        call_volume = 0.0
        put_volume = 0.0
        call_oi = 0.0
        put_oi = 0.0
        for row in rows:
            mark_iv = row.get("mark_iv")
            if mark_iv is not None:
                try:
                    ivs.append(float(mark_iv) / 100.0)
                except (TypeError, ValueError):
                    pass
            instrument = str(row.get("instrument_name") or "")
            volume = float(row.get("volume") or 0.0)
            open_interest = float(row.get("open_interest") or 0.0)
            if instrument.endswith("-C"):
                call_volume += volume
                call_oi += open_interest
            elif instrument.endswith("-P"):
                put_volume += volume
                put_oi += open_interest
        if not rows:
            return {"status": "absent", "source": "deribit_options_public_api", "reason": "empty_options_summary"}
        return {
            "status": "real",
            "source": "deribit_options_public_api",
            "timestamp_utc": utc_iso(),
            "timestamp_paris": paris_iso(),
            "implied_volatility_mean": float(np.mean(ivs)) if ivs else None,
            "implied_volatility_median": float(np.median(ivs)) if ivs else None,
            "put_call_volume_ratio": put_volume / call_volume if call_volume > 0 else None,
            "put_call_open_interest_ratio": put_oi / call_oi if call_oi > 0 else None,
            "max_pain": None,
            "max_pain_status": "absent_not_computed_without_full_chain_by_expiry",
            "note": "Options data are used as context only; BTC spot source policy remains Bitget-only.",
        }
    except Exception as exc:
        return {"status": "absent", "source": "deribit_options_public_api", "error": str(exc)}


def etf_flow_trends(logger) -> dict[str, Any]:
    frame = fetch_farside_etf_flow_history(logger, limit=60)
    if frame is None or frame.empty:
        return {"status": "absent", "source": "farside_bitcoin_etf_flow_total_usd_m_history"}
    values = pd.to_numeric(frame["etf_flow_usd_m"], errors="coerce").dropna()
    if values.empty:
        return {"status": "absent", "source": "farside_bitcoin_etf_flow_total_usd_m_history"}
    latest = float(values.iloc[-1])
    rolling_7 = float(values.tail(7).sum()) if len(values) >= 1 else None
    rolling_30 = float(values.tail(30).sum()) if len(values) >= 1 else None
    prev_7 = float(values.iloc[-14:-7].sum()) if len(values) >= 14 else None
    acceleration = rolling_7 - prev_7 if rolling_7 is not None and prev_7 is not None else None
    return {
        "status": "real",
        "source": "farside_bitcoin_etf_flow_total_usd_m_history",
        "timestamp_utc": str(frame["timestamp"].iloc[-1]),
        "timestamp_paris": timestamp_paris_iso(frame["timestamp"].iloc[-1]),
        "latest_1d_usd_m": latest,
        "flow_7d_usd_m": rolling_7,
        "flow_30d_usd_m": rolling_30,
        "flow_7d_acceleration_usd_m": acceleration,
        "rows": int(len(frame)),
        "unit": "USD millions",
    }


def build_explainability(distribution: dict[str, Any], risk: dict[str, Any], fundamentals: dict[str, Any], returns) -> dict[str, Any]:
    values = fundamentals.get("values") if isinstance(fundamentals, dict) else {}
    recent_returns = clean_numeric_returns(returns)
    momentum_30 = float(np.prod(1 + recent_returns[-30:]) - 1.0) if recent_returns.size >= 30 else None
    realized_vol_30 = float(np.std(recent_returns[-30:], ddof=1) * math.sqrt(365)) if recent_returns.size >= 30 else None
    prob_up = distribution.get("prob_up")
    median = distribution.get("median_return")
    contributors = {
        "momentum": {
            "status": "inferred",
            "score": momentum_30,
            "direction": "positive" if momentum_30 is not None and momentum_30 > 0 else "negative_or_absent",
        },
        "volatility": {
            "status": "inferred",
            "score": realized_vol_30,
            "risk_contribution": risk.get("conditional_volatility"),
        },
        "macro": {
            "status": "partial_real_absent",
            "dxy": values.get("dxy"),
            "us_rates": values.get("us_rates"),
            "nasdaq": values.get("nasdaq"),
        },
        "derivatives": {
            "status": "partial_real_absent",
            "funding_rate": values.get("funding_rate"),
            "open_interest": values.get("open_interest"),
            "liquidations": values.get("liquidations"),
        },
        "etf": {
            "status": "partial_real_absent",
            "etf_flows": values.get("etf_flows"),
        },
    }
    return {
        "status": "inferred",
        "method": "heuristic_feature_attribution_not_causal_explanation",
        "probability_context": {"prob_up": prob_up, "median_return": median},
        "contributors": contributors,
        "limitation": "These contributions explain model inputs heuristically; they are not causal proof and not a trading signal.",
    }


def clean_numeric_returns(returns) -> np.ndarray:
    arr = np.asarray(returns, dtype=float)
    return arr[np.isfinite(arr)]


def fast_multi_frame_results(payload: MultiFrameRunRequest, horizons: list[int], spot_snapshot: dict[str, Any] | None) -> dict[str, Any]:
    logger = setup_logger()
    spot_override = spot_snapshot if spot_snapshot else None
    price_frame = load_market_prices(
        payload.asset,
        logger,
        days=max(1095, max(horizons) + 500),
        allow_online=not payload.no_online,
        spot_override=spot_override,
    )
    fundamentals = load_fundamental_features(payload.asset, price_frame, logger)
    fundamental_inputs = summarize_fundamental_inputs(fundamentals)
    fundamental_freshness = freshness_status(
        "fundamental_snapshot",
        fundamental_inputs.get("timestamp"),
        MAX_FUNDAMENTAL_AGE_SECONDS,
    )
    returns = daily_returns(price_frame)
    sources = set(price_frame["source"].dropna().astype(str))
    statuses = set(price_frame["statut"].dropna().astype(str))
    if any("coingecko" in source.lower() for source in sources):
        raise HTTPException(
            status_code=503,
            detail={
                "error": "non_bitget_market_source_detected",
                "sources": sorted(sources),
                "source_policy": SOURCE_POLICY,
                "warning": "Live GPT run blocked because non-Bitget market fallback was detected.",
            },
        )
    if "mock" in statuses:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "mock_market_data_detected",
                "sources": sorted(sources),
                "source_policy": SOURCE_POLICY,
                "warning": "Live GPT run blocked because market data are mock.",
            },
        )
    spot = float(price_frame["close"].dropna().iloc[-1])
    latest_row = price_frame.tail(1).to_dict("records")[0]
    reference_spot = format_price(spot)
    reference_timestamp = str(latest_row.get("timestamp"))
    reference_source = str(latest_row.get("source"))
    spot_freshness = freshness_status("reference_spot", reference_timestamp, MAX_SPOT_AGE_SECONDS)
    if not payload.no_online and not spot_freshness["is_fresh"]:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "reference_spot_stale",
                "freshness": spot_freshness,
                "source_policy": SOURCE_POLICY,
                "warning": "Live GPT run blocked because the reference Bitget spot is stale.",
            },
        )
    model_name = payload.model
    simulate = FAST_MODEL_REGISTRY[model_name]
    frames: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    batch_started_at = utc_now()
    liquidity_snapshot = fetch_bitget_liquidity_snapshot(payload.asset)
    options_snapshot = fetch_options_snapshot()
    etf_trend_snapshot = etf_flow_trends(logger)
    backtest_diagnostics = run_backtest(price_frame, payload.asset, model_name, horizons=tuple(horizons))

    for horizon in horizons:
        frame_report_date = utc_now()
        run_id = (
            f"{payload.asset.upper()}_{model_name}_{horizon}d_fast_"
            f"{batch_started_at.strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
        )
        kwargs = {
            "returns": returns,
            "spot": spot,
            "horizon": horizon,
            "simulations": payload.simulations,
            "seed": seed_for(run_id),
        }
        if model_name in {"correlation", "correlation_model"}:
            kwargs["fundamentals"] = fundamentals
        if model_name == "ensemble":
            kwargs["fundamentals"] = fundamentals
            kwargs["backtest_rows"] = []
        try:
            simulation_result = simulate(**kwargs)
            distribution = summarize_simulation(simulation_result["terminal_prices"], spot)
            risk = compute_risk_metrics(
                simulation_result["terminal_returns"],
                historical_returns=returns,
                sample_paths=simulation_result.get("sample_paths"),
            )
            regimes = regime_distribution(distribution)
            mc_error = monte_carlo_error_summary(distribution, regimes, payload.simulations)
            stability = build_multi_seed_stability(
                simulate=simulate,
                model_name=model_name,
                returns=returns,
                spot=spot,
                horizon=horizon,
                simulations=payload.simulations,
                fundamentals=fundamentals,
                base_run_id=run_id,
            )
            stress = run_stress_tests(spot, simulation_result["terminal_prices"], simulation_result.get("sample_paths"))
            confidence = compute_confidence_score(price_frame, fundamentals, risk, distribution, [])
            frames.append(
                {
                    "run_id": run_id,
                    "asset": payload.asset.upper(),
                    "horizon": horizon,
                    "simulations": payload.simulations,
                    "model": model_name,
                    "provenance": {
                        "source": "fast_runtime_multi_frame",
                        "report_date": frame_report_date.isoformat(),
                        "report_date_utc": frame_report_date.isoformat(),
                        "report_date_paris": paris_iso(frame_report_date),
                        "model_run_id": run_id,
                        "reference_spot": reference_spot,
                        "reference_spot_timestamp": reference_timestamp,
                        "reference_spot_timestamp_utc": timestamp_utc_iso(reference_timestamp),
                        "reference_spot_timestamp_paris": timestamp_paris_iso(reference_timestamp),
                        "reference_spot_source": reference_source,
                        "market_source": ", ".join(sorted(set(price_frame["source"].dropna().astype(str)))),
                        "calculation_origin": "fast_in_memory_runtime",
                        "fresh_run": True,
                        "timezone_policy": TIMEZONE_POLICY,
                        "freshness": {
                            "spot": spot_freshness,
                            "fundamentals": fundamental_freshness,
                        },
                    },
                    "data_status": {
                        "market_prices": "real" if "real" in set(price_frame["statut"].astype(str)) else "mock_or_missing",
                        "simulation_outputs": "inferred",
                        "risk_metrics": "inferred",
                        "fundamental_variables": fundamental_inputs["status"],
                    },
                    "fundamental_inputs": fundamental_inputs,
                    "distribution": distribution,
                    "regime_distribution": regimes,
                    "risk_metrics": risk,
                    "monte_carlo_error": mc_error,
                    "multi_seed_stability": stability,
                    "stress_tests": stress,
                    "confidence": confidence,
                    "position_sizing": position_sizing_summary(risk, distribution),
                    "liquidity": liquidity_snapshot,
                    "options": options_snapshot,
                    "etf_flow_trends": etf_trend_snapshot,
                    "explainability": build_explainability(distribution, risk, fundamental_inputs, returns),
                    "version": version_payload(),
                    "warning": "Fast multi-frame runtime: probabilistic output only, no deterministic forecast.",
                }
            )
        except Exception as exc:
            errors.append({"horizon": horizon, "status_code": 500, "detail": str(exc)})

    return {
        "price_frame": price_frame,
        "fundamentals": fundamentals,
        "fundamental_inputs": fundamental_inputs,
        "frames": frames,
        "errors": errors,
        "reference_spot": reference_spot,
        "reference_timestamp": reference_timestamp,
        "reference_timestamp_utc": timestamp_utc_iso(reference_timestamp),
        "reference_timestamp_paris": timestamp_paris_iso(reference_timestamp),
        "reference_source": reference_source,
        "freshness": {
            "spot": spot_freshness,
            "fundamentals": fundamental_freshness,
            "policy": freshness_policy_payload(),
        },
        "liquidity": liquidity_snapshot,
        "options": options_snapshot,
        "etf_flow_trends": etf_trend_snapshot,
        "backtest_diagnostics": backtest_diagnostics,
        "batch_started_at": batch_started_at.isoformat(),
        "batch_started_at_paris": paris_iso(batch_started_at),
    }


def build_run_response(payload: RunRequest) -> RunResponse:
    summary = run_cli(payload)
    report = read_text(REPORT_PATH)
    dashboard = read_text(DASHBOARD_PATH)
    distribution = summary.get("distribution", {})
    risk = summary.get("risk_metrics", {})
    run_id = summary.get("run_id", "")
    report_date = extract_report_date(report)
    reference_spot_timestamp = extract_report_bullet(report, "Reference spot timestamp")
    return RunResponse(
        run_id=run_id,
        asset=summary.get("asset", payload.asset.upper()),
        horizon=int(summary.get("horizon", payload.horizon)),
        simulations=int(summary.get("simulations", payload.simulations)),
        model=summary.get("model", payload.model),
        provenance={
            "source": "runtime_generated_report",
            "report_date": report_date,
            "report_date_utc": timestamp_utc_iso(report_date),
            "report_date_paris": timestamp_paris_iso(report_date),
            "model_run_id": run_id,
            "reference_spot": extract_reference_spot(report),
            "reference_spot_timestamp": reference_spot_timestamp,
            "reference_spot_timestamp_utc": timestamp_utc_iso(reference_spot_timestamp),
            "reference_spot_timestamp_paris": timestamp_paris_iso(reference_spot_timestamp),
            "reference_spot_source": extract_report_bullet(report, "Reference spot source"),
            "market_source": extract_bullet_value(report, "Market sources")
            or "bitget_btcusdt_spot_candles unless local CSV overrides it",
            "calculation_origin": "runtime_run",
            "fresh_run": True,
            "timezone_policy": TIMEZONE_POLICY,
        },
        data_status={
            "market_prices": extract_bullet_value(report, "Market prices status") or "real_or_mock_per_report",
            "simulation_outputs": extract_bullet_value(report, "Simulation outputs status") or "inferred",
            "risk_metrics": extract_bullet_value(report, "Risk metrics status") or "inferred",
            "fundamental_variables": extract_bullet_value(report, "Fundamental variables status")
            or "absent_unless_supplied",
        },
        fundamental_inputs=load_processed_fundamental_inputs(payload.asset),
        distribution=distribution,
        regime_distribution=regime_distribution(distribution),
        risk_metrics=risk,
        stress_tests=summary.get("stress_tests", []),
        confidence=summary.get("confidence", {}),
        position_sizing=summary.get("position_sizing", {}),
        version=version_payload(),
        report_markdown=report,
        dashboard_markdown=dashboard,
        warning=(
            "Probabilistic output only. Not financial advice. Never interpret this "
            "response as a deterministic prediction."
        ),
    )


@app.get("/health")
def health() -> dict[str, Any]:
    checked_at = utc_now()
    return {
        "status": "ok",
        "service": "quant-btc-model",
        "mode": "probabilistic",
        "api_version": API_VERSION,
        "git_commit": GIT_COMMIT,
        "timestamp_utc": checked_at.isoformat(),
        "timestamp_paris": paris_iso(checked_at),
        "timezone_policy": TIMEZONE_POLICY,
    }


@app.get("/version")
def version() -> dict[str, Any]:
    return version_payload()


@app.get("/status")
def status() -> dict[str, Any]:
    checked_at = utc_now()
    return {
        "status": "ok",
        "service": "quant-btc-model",
        "production_endpoint": "https://quant-btc-model-api.onrender.com",
        "privacy_policy": "https://raw.githubusercontent.com/ronycharlier-byte/MDL-Bitcoin-Analyst/main/PRIVACY_POLICY.md",
        "actions": {
            "single_horizon": "/run",
            "multi_frame": "/multi-run",
            "compare_runs": "/compare-runs",
            "history": "/history",
            "alerts": "/alerts",
            "backtest_summary": "/backtest-summary",
            "dashboard": "/dashboard",
            "pdf_report": "/pdf-report",
            "latest_artifact": "/latest",
            "version": "/version",
            "audit": "/audit",
        },
        "default_frames": DEFAULT_MULTIFRAME_HORIZONS,
        "timestamp_utc": checked_at.isoformat(),
        "timestamp_paris": paris_iso(checked_at),
        "timezone_policy": TIMEZONE_POLICY,
        "data_sources": {
            "btc_spot": "Bitget BTCUSDT spot ticker and candles",
            "etf_flows": "Farside Investors Bitcoin ETF Flow total net flow in USD millions when available",
            "funding_rate": "Bitget current funding rate when available",
            "open_interest": "Bitget open interest when available",
            "liquidations": (
                "Bitget UTA public liquidation WebSocket BTCUSDT observed quote amount. "
                "If no push is received during the configured observation window, the field remains absent."
            ),
            "hash_rate": "Blockchain.com hash-rate chart when available",
            "exchange_reserves": "Bitget Proof of Reserves BTC platform assets when available",
            "dxy": "Stooq DX.F quote when available",
            "us_rates": "FRED DGS10 or U.S. Treasury 10Y rate when available",
            "nasdaq": "Stooq ^NDX quote when available",
            "stablecoins_supply": "DeFiLlama stablecoins peggedUSD total when available",
            "order_book_liquidity": "Bitget BTCUSDT spot order book depth/spread snapshot when available",
            "options_implied_volatility": "Deribit public BTC options summary when available; contextual only, not a spot market fallback",
            "etf_flow_history": "Farside ETF flow table with 1d/7d/30d trend diagnostics when available",
            "absent_without_connector": [
                "liquidations",
            ],
        },
        "runtime_controls": {
            "cache_ttl_seconds": CACHE_TTL_SECONDS,
            "rate_limit_runs_per_minute": RATE_LIMIT_RUNS_PER_MINUTE,
            "rate_limit_window_seconds": RATE_LIMIT_WINDOW_SECONDS,
            "freshness_policy": freshness_policy_payload(),
            "multi_seed_runs": MULTI_SEED_RUNS,
            "multi_seed_simulations": MULTI_SEED_SIMULATIONS,
        },
        "limits": [
            "Outputs are probabilistic, not deterministic predictions.",
            "This is not financial advice.",
            "Fundamental coverage is partial unless user-supplied audited data are connected.",
            "Spot freshness is enforced for live Bitget runs; stale spot blocks the run.",
            "Runtime archive files on free hosts may be ephemeral; GitHub archive workflow stores compact durable snapshots.",
        ],
        "version": version_payload(),
    }


@app.get("/audit")
def audit() -> dict[str, Any]:
    return audit_payload()


@app.post("/run", response_model=RunResponse, dependencies=[Depends(require_api_key), Depends(require_rate_limit)])
def run_model(payload: RunRequest) -> RunResponse:
    key = cache_key_for("/run", pydantic_payload(payload))
    cached = cache_get(key)
    if cached:
        return cached
    response = build_run_response(payload)
    response_payload = response.model_dump() if hasattr(response, "model_dump") else response.dict()
    attach_archive("/run", response_payload)
    cache_set(key, response_payload)
    return response_payload


@app.post("/multi-run", dependencies=[Depends(require_api_key), Depends(require_rate_limit)])
def run_multi_frame(payload: MultiFrameRunRequest) -> dict[str, Any]:
    horizons = normalized_horizons(payload.horizons)
    key = cache_key_for("/multi-run", {**pydantic_payload(payload), "horizons": horizons})
    cached = cache_get(key)
    if cached:
        return cached
    spot_snapshot = None if payload.no_online else fetch_realtime_spot_snapshot(payload.asset)
    spot_freshness = freshness_status("bitget_spot_snapshot", (spot_snapshot or {}).get("timestamp"), MAX_SPOT_AGE_SECONDS)
    if not payload.no_online:
        assert_live_spot_fresh(payload.asset, spot_snapshot)
    fast_result = fast_multi_frame_results(payload, horizons, spot_snapshot)
    results = fast_result["frames"]
    errors = fast_result["errors"]

    if not results:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "All multi-frame runs failed.",
                "errors": errors,
                "warning": "No deterministic prediction was produced.",
            },
        )

    reference_spots = [
        result.get("provenance", {}).get("reference_spot")
        for result in results
        if result.get("provenance", {}).get("reference_spot")
    ]
    reference_timestamps = [
        result.get("provenance", {}).get("reference_spot_timestamp")
        for result in results
        if result.get("provenance", {}).get("reference_spot_timestamp")
    ]
    response_report_date = utc_now()
    fundamental_statuses = {
        result.get("data_status", {}).get("fundamental_variables")
        for result in results
        if result.get("data_status", {}).get("fundamental_variables")
    }
    market_statuses = {
        result.get("data_status", {}).get("market_prices")
        for result in results
        if result.get("data_status", {}).get("market_prices")
    }

    response_payload = {
        "status": "ok" if not errors else "partial",
        "asset": payload.asset.upper(),
        "model": payload.model,
        "horizons": horizons,
        "simulations_per_horizon": payload.simulations,
        "frames": results,
        "errors": errors,
        "provenance_summary": {
            "source": "live runQuantBtcMultiFrame response",
            "operation": "runQuantBtcMultiFrame",
            "report_date": response_report_date.isoformat(),
            "report_date_utc": response_report_date.isoformat(),
            "report_date_paris": paris_iso(response_report_date),
            "reference_spots": reference_spots,
            "reference_spot_timestamps": reference_timestamps,
            "reference_spot_timestamps_utc": [timestamp_utc_iso(item) for item in reference_timestamps],
            "reference_spot_timestamps_paris": [timestamp_paris_iso(item) for item in reference_timestamps],
            "reference_spot_source": "bitget_btcusdt_spot_ticker_realtime unless a frame reports otherwise",
            "shared_spot_snapshot": spot_snapshot,
            "shared_spot_snapshot_timestamp_utc": timestamp_utc_iso((spot_snapshot or {}).get("timestamp")),
            "shared_spot_snapshot_timestamp_paris": timestamp_paris_iso((spot_snapshot or {}).get("timestamp")),
            "freshness": fast_result["freshness"],
            "runtime": "fast_in_memory_multi_frame",
            "fresh_run": True,
            "timezone_policy": TIMEZONE_POLICY,
            "analysis_consistency_policy": (
                "Use this response as one analysis unit. Do not mix its numbers with another archive_id/run response "
                "unless the user explicitly asks for a comparison."
            ),
        },
        "fundamental_inputs": fast_result["fundamental_inputs"],
        "freshness": fast_result["freshness"],
        "liquidity": fast_result["liquidity"],
        "options": fast_result["options"],
        "etf_flow_trends": fast_result["etf_flow_trends"],
        "backtest_diagnostics": fast_result["backtest_diagnostics"],
        "data_status": {
            "market_prices": "real" if market_statuses == {"real"} else "real_or_mock_per_frame",
            "simulation_outputs": "inferred",
            "risk_metrics": "inferred",
            "fundamental_variables": "partial_real_absent"
            if "partial_real_absent" in fundamental_statuses
            else "absent_unless_supplied",
        },
        "version": version_payload(),
        "warning": (
            "Multi-frame output is probabilistic only. Compare horizons as scenario distributions, "
            "not as deterministic price paths or financial advice."
        ),
    }
    response_payload["alerts"] = build_alerts_from_payload(response_payload)
    attach_archive("/multi-run", response_payload)
    cache_set(key, response_payload)
    return response_payload


@app.get("/history", dependencies=[Depends(require_api_key)])
def history(asset: str = "BTC", limit: int = 10) -> dict[str, Any]:
    archives = list_runtime_archives(asset=asset, limit=limit)
    return {
        "status": "ok",
        "asset": asset.upper(),
        "archives": archives,
        "durable_storage": {
            "runtime_sqlite": "present",
            "local_json_archive": "present",
            "github_external_archive": "present_when_archive_workflow_commits_snapshots",
            "supabase_postgres": "absent_not_configured",
            "cloudflare_d1_r2": "absent_not_configured",
            "note": "Runtime files may be ephemeral on free hosts; GitHub archive workflow provides compact durable snapshots.",
        },
        "version": version_payload(),
    }


@app.get("/compare-runs", dependencies=[Depends(require_api_key)])
def compare_runs(asset: str = "BTC", current_archive_id: str | None = None, previous_archive_id: str | None = None) -> dict[str, Any]:
    if current_archive_id and previous_archive_id:
        current = load_runtime_archive_payload(current_archive_id)
        previous = load_runtime_archive_payload(previous_archive_id)
    else:
        candidates = list_runtime_archives(asset=asset, limit=12)
        multi_frame_candidates = [
            archive
            for archive in candidates
            if archive.get("endpoint") == "/multi-run" and len(archive.get("horizons") or []) >= 2
        ]
        archives = multi_frame_candidates[:2] if len(multi_frame_candidates) >= 2 else candidates[:2]
        if len(archives) < 2:
            return {
                "status": "absent",
                "message": "At least two runtime archives are required for comparison.",
                "archives_found": archives,
                "version": version_payload(),
            }
        current = load_runtime_archive_payload(archives[0]["archive_id"])
        previous = load_runtime_archive_payload(archives[1]["archive_id"])
    if not current or not previous:
        return {
            "status": "absent",
            "message": "Requested archive payload was not found in runtime SQLite.",
            "current_archive_id": current_archive_id,
            "previous_archive_id": previous_archive_id,
            "version": version_payload(),
        }
    return compare_run_payload(current, previous)


@app.get("/alerts", dependencies=[Depends(require_api_key)])
def alerts(asset: str = "BTC") -> dict[str, Any]:
    archives = list_runtime_archives(asset=asset, limit=1)
    payload = load_runtime_archive_payload(archives[0]["archive_id"]) if archives else None
    if not payload:
        return {"status": "absent", "alerts": [{"level": "warning", "type": "no_archive", "message": "No runtime archive available."}], "version": version_payload()}
    return {
        "status": "ok",
        "asset": asset.upper(),
        "archive_id": (payload.get("archive") or {}).get("archive_id"),
        "alerts": build_alerts_from_payload(payload),
        "freshness": payload.get("freshness"),
        "version": version_payload(),
    }


@app.get("/backtest-summary", dependencies=[Depends(require_api_key)])
def backtest_summary(asset: str = "BTC") -> dict[str, Any]:
    return backtest_summary_payload(asset=asset)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    return HTMLResponse(dashboard_html())


@app.get("/pdf-report", dependencies=[Depends(require_api_key)])
def pdf_report(asset: str = "BTC", archive_id: str | None = None) -> Response:
    payload = load_runtime_archive_payload(archive_id) if archive_id else None
    if payload is None:
        archives = list_runtime_archives(asset=asset, limit=1)
        payload = load_runtime_archive_payload(archives[0]["archive_id"]) if archives else None
    if payload is None:
        lines = ["No runtime archive is available. Run /multi-run first."]
    else:
        archive = payload.get("archive") or {}
        provenance = payload.get("provenance_summary") or {}
        lines = [
            f"Archive ID: {archive.get('archive_id')}",
            f"Report date UTC: {provenance.get('report_date_utc')}",
            f"Report date Europe/Paris: {provenance.get('report_date_paris')}",
            f"Asset: {payload.get('asset')}",
            f"Model: {payload.get('model')}",
            f"Reference spot: {(provenance.get('reference_spots') or ['absent'])[0]}",
            "Outputs are probabilistic scenarios, not deterministic predictions.",
            "",
            "Frames:",
        ]
        for frame in payload.get("frames") or []:
            distribution = frame.get("distribution") or {}
            risk = frame.get("risk_metrics") or {}
            confidence = frame.get("confidence") or {}
            lines.append(
                f"{frame.get('horizon')}d | median={distribution.get('median_return')} | "
                f"VaR95={risk.get('var_95')} | CVaR95={risk.get('cvar_95')} | confidence={confidence.get('score')}"
            )
    return Response(
        content=simple_pdf_bytes("Quant BTC Model Report", lines),
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=quant-btc-model-report.pdf"},
    )


@app.get("/latest", dependencies=[Depends(require_api_key)])
def latest() -> dict[str, Any]:
    return {
        "report_markdown": read_text(REPORT_PATH),
        "dashboard_markdown": read_text(DASHBOARD_PATH),
        "timezone_policy": TIMEZONE_POLICY,
        "warning": "Latest local artifact only; call POST /run for a fresh run.",
    }
