from __future__ import annotations

import json
import hashlib
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

import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field


ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
SUMMARY_DIR = ROOT / "data" / "simulations"
REPORT_PATH = ROOT / "reports" / "latest_report.md"
DASHBOARD_PATH = ROOT / "reports" / "dashboard_summary.md"
API_RUNTIME_DB = ROOT / "data" / "api_runtime.db"
MAX_API_SIMULATIONS = int(os.getenv("MAX_API_SIMULATIONS", "250000"))
DEFAULT_API_SIMULATIONS = min(int(os.getenv("DEFAULT_API_SIMULATIONS", "5000")), MAX_API_SIMULATIONS)
DEFAULT_MULTIFRAME_SIMULATIONS = min(int(os.getenv("DEFAULT_MULTIFRAME_SIMULATIONS", "2000")), MAX_API_SIMULATIONS)
DEFAULT_MULTIFRAME_HORIZONS = [7, 30, 90, 180, 365]
RATE_LIMIT_RUNS_PER_MINUTE = int(os.getenv("RATE_LIMIT_RUNS_PER_MINUTE", "12"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "45"))
API_VERSION = "1.3.3"
MODEL_VERSION = os.getenv("MODEL_VERSION", "quant_btc_model_v1")
SCHEMA_VERSION = "gpt_action_schema_v1.3.3"


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
from market_data import load_fundamental_features, load_market_prices  # noqa: E402
from position_sizing import position_sizing_summary  # noqa: E402
from risk_metrics import compute_risk_metrics  # noqa: E402
from simulation_utils import seed_for, summarize_simulation  # noqa: E402
from stress_tests import run_stress_tests  # noqa: E402


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
    version="1.0.0",
    description=(
        "Probabilistic Bitcoin quantitative model API. Outputs are scenarios, "
        "probabilities, distributions and risk metrics, never deterministic predictions."
    ),
)


def init_runtime_db() -> None:
    API_RUNTIME_DB.parent.mkdir(parents=True, exist_ok=True)
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
        conn.execute("CREATE INDEX IF NOT EXISTS idx_rate_limit_client_time ON rate_limit_events (client_key, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_response_cache_expires ON response_cache (expires_at)")
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

    return {
        "status": status,
        "real_fields": sorted(values),
        "absent_fields": sorted(absent_fields),
        "values": values,
        "field_status": field_status,
        "sources": sources,
        "timestamp": str(latest.get("timestamp")) if latest.get("timestamp") is not None else None,
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
            "expires_at": datetime.fromtimestamp(float(row[2]), tz=timezone.utc).isoformat(),
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
        "expires_at": datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
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
        "api_version": API_VERSION,
        "model_version": MODEL_VERSION,
        "schema_version": SCHEMA_VERSION,
        "git_commit": GIT_COMMIT,
        "execution_environment": os.getenv("RENDER_SERVICE_NAME", "local_or_custom"),
        "max_api_simulations": MAX_API_SIMULATIONS,
        "default_api_simulations": DEFAULT_API_SIMULATIONS,
        "default_multiframe_simulations": DEFAULT_MULTIFRAME_SIMULATIONS,
        "default_multiframe_horizons": DEFAULT_MULTIFRAME_HORIZONS,
        "rate_limit_runs_per_minute": RATE_LIMIT_RUNS_PER_MINUTE,
        "rate_limit_window_seconds": RATE_LIMIT_WINDOW_SECONDS,
        "cache_ttl_seconds": CACHE_TTL_SECONDS,
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
        return {
            "price": price,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(timestamp_ms / 1000)),
            "source": "bitget_btcusdt_spot_ticker_realtime_snapshot",
        }
    except Exception:
        return None


def format_price(value: float | None) -> str | None:
    if value is None:
        return None
    return f"${float(value):,.2f}"


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
    returns = daily_returns(price_frame)
    spot = float(price_frame["close"].dropna().iloc[-1])
    latest_row = price_frame.tail(1).to_dict("records")[0]
    reference_spot = format_price(spot)
    reference_timestamp = str(latest_row.get("timestamp"))
    reference_source = str(latest_row.get("source"))
    model_name = payload.model
    simulate = FAST_MODEL_REGISTRY[model_name]
    frames: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for horizon in horizons:
        run_id = (
            f"{payload.asset.upper()}_{model_name}_{horizon}d_fast_"
            f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
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
                        "report_date": datetime.now(timezone.utc).isoformat(),
                        "model_run_id": run_id,
                        "reference_spot": reference_spot,
                        "reference_spot_timestamp": reference_timestamp,
                        "reference_spot_source": reference_source,
                        "market_source": ", ".join(sorted(set(price_frame["source"].dropna().astype(str)))),
                        "calculation_origin": "fast_in_memory_runtime",
                        "fresh_run": True,
                    },
                    "data_status": {
                        "market_prices": "real" if "real" in set(price_frame["statut"].astype(str)) else "mock_or_missing",
                        "simulation_outputs": "inferred",
                        "risk_metrics": "inferred",
                        "fundamental_variables": fundamental_inputs["status"],
                    },
                    "fundamental_inputs": fundamental_inputs,
                    "distribution": distribution,
                    "regime_distribution": regime_distribution(distribution),
                    "risk_metrics": risk,
                    "stress_tests": stress,
                    "confidence": confidence,
                    "position_sizing": position_sizing_summary(risk, distribution),
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
        "reference_source": reference_source,
    }


def build_run_response(payload: RunRequest) -> RunResponse:
    summary = run_cli(payload)
    report = read_text(REPORT_PATH)
    dashboard = read_text(DASHBOARD_PATH)
    distribution = summary.get("distribution", {})
    risk = summary.get("risk_metrics", {})
    run_id = summary.get("run_id", "")
    return RunResponse(
        run_id=run_id,
        asset=summary.get("asset", payload.asset.upper()),
        horizon=int(summary.get("horizon", payload.horizon)),
        simulations=int(summary.get("simulations", payload.simulations)),
        model=summary.get("model", payload.model),
        provenance={
            "source": "runtime_generated_report",
            "report_date": extract_report_date(report),
            "model_run_id": run_id,
            "reference_spot": extract_reference_spot(report),
            "reference_spot_timestamp": extract_report_bullet(report, "Reference spot timestamp"),
            "reference_spot_source": extract_report_bullet(report, "Reference spot source"),
            "market_source": extract_bullet_value(report, "Market sources")
            or "bitget_btcusdt_spot_candles unless local CSV overrides it",
            "calculation_origin": "runtime_run",
            "fresh_run": True,
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
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "quant-btc-model",
        "mode": "probabilistic",
        "api_version": API_VERSION,
        "git_commit": GIT_COMMIT,
    }


@app.get("/version")
def version() -> dict[str, Any]:
    return version_payload()


@app.get("/status")
def status() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "quant-btc-model",
        "production_endpoint": "https://quant-btc-model-api.onrender.com",
        "privacy_policy": "https://raw.githubusercontent.com/ronycharlier-byte/MDL-Bitcoin-Analyst/main/PRIVACY_POLICY.md",
        "actions": {
            "single_horizon": "/run",
            "multi_frame": "/multi-run",
            "latest_artifact": "/latest",
            "version": "/version",
        },
        "default_frames": DEFAULT_MULTIFRAME_HORIZONS,
        "data_sources": {
            "btc_spot": "Bitget BTCUSDT spot ticker and candles",
            "funding_rate": "Bitget current funding rate when available",
            "open_interest": "Bitget open interest when available",
            "hash_rate": "Blockchain.com hash-rate chart when available",
            "dxy": "Stooq DX.F quote when available",
            "us_rates": "FRED DGS10 or U.S. Treasury 10Y rate when available",
            "nasdaq": "Stooq ^NDX quote when available",
            "stablecoins_supply": "DeFiLlama stablecoins peggedUSD total when available",
            "absent_without_connector": [
                "etf_flows",
                "liquidations",
                "exchange_reserves",
            ],
        },
        "runtime_controls": {
            "cache_ttl_seconds": CACHE_TTL_SECONDS,
            "rate_limit_runs_per_minute": RATE_LIMIT_RUNS_PER_MINUTE,
            "rate_limit_window_seconds": RATE_LIMIT_WINDOW_SECONDS,
        },
        "limits": [
            "Outputs are probabilistic, not deterministic predictions.",
            "This is not financial advice.",
            "Fundamental coverage is partial unless user-supplied audited data are connected.",
            "Render free hosting may sleep; Cloudflare no-sleep quant-lite deployment requires Wrangler login.",
        ],
        "version": version_payload(),
    }


@app.post("/run", response_model=RunResponse, dependencies=[Depends(require_api_key), Depends(require_rate_limit)])
def run_model(payload: RunRequest) -> RunResponse:
    key = cache_key_for("/run", pydantic_payload(payload))
    cached = cache_get(key)
    if cached:
        return cached
    response = build_run_response(payload)
    response_payload = response.model_dump() if hasattr(response, "model_dump") else response.dict()
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
            "reference_spots": reference_spots,
            "reference_spot_timestamps": reference_timestamps,
            "reference_spot_source": "bitget_btcusdt_spot_ticker_realtime unless a frame reports otherwise",
            "shared_spot_snapshot": spot_snapshot,
            "runtime": "fast_in_memory_multi_frame",
            "fresh_run": True,
        },
        "fundamental_inputs": fast_result["fundamental_inputs"],
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
    cache_set(key, response_payload)
    return response_payload


@app.get("/latest", dependencies=[Depends(require_api_key)])
def latest() -> dict[str, Any]:
    return {
        "report_markdown": read_text(REPORT_PATH),
        "dashboard_markdown": read_text(DASHBOARD_PATH),
        "warning": "Latest local artifact only; call POST /run for a fresh run.",
    }
