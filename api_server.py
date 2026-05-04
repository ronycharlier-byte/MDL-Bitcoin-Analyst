from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


ROOT = Path(__file__).resolve().parent
SUMMARY_DIR = ROOT / "data" / "simulations"
REPORT_PATH = ROOT / "reports" / "latest_report.md"
DASHBOARD_PATH = ROOT / "reports" / "dashboard_summary.md"
MAX_API_SIMULATIONS = int(os.getenv("MAX_API_SIMULATIONS", "250000"))
DEFAULT_API_SIMULATIONS = min(int(os.getenv("DEFAULT_API_SIMULATIONS", "5000")), MAX_API_SIMULATIONS)
DEFAULT_MULTIFRAME_SIMULATIONS = min(int(os.getenv("DEFAULT_MULTIFRAME_SIMULATIONS", "2000")), MAX_API_SIMULATIONS)
DEFAULT_MULTIFRAME_HORIZONS = [7, 30, 90, 180, 365]


app = FastAPI(
    title="Quant BTC Model API",
    version="1.0.0",
    description=(
        "Probabilistic Bitcoin quantitative model API. Outputs are scenarios, "
        "probabilities, distributions and risk metrics, never deterministic predictions."
    ),
)


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
    distribution: dict[str, Any]
    regime_distribution: dict[str, Any]
    risk_metrics: dict[str, Any]
    stress_tests: list[dict[str, Any]]
    confidence: dict[str, Any]
    position_sizing: dict[str, Any]
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
        distribution=distribution,
        regime_distribution=regime_distribution(distribution),
        risk_metrics=risk,
        stress_tests=summary.get("stress_tests", []),
        confidence=summary.get("confidence", {}),
        position_sizing=summary.get("position_sizing", {}),
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
    }


@app.post("/run", response_model=RunResponse, dependencies=[Depends(require_api_key)])
def run_model(payload: RunRequest) -> RunResponse:
    return build_run_response(payload)


@app.post("/multi-run", dependencies=[Depends(require_api_key)])
def run_multi_frame(payload: MultiFrameRunRequest) -> dict[str, Any]:
    horizons = normalized_horizons(payload.horizons)
    results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for horizon in horizons:
        run_payload = RunRequest(
            asset=payload.asset,
            horizon=horizon,
            simulations=payload.simulations,
            model=payload.model,
            skip_corpus=payload.skip_corpus,
            no_online=payload.no_online,
        )
        try:
            result = build_run_response(run_payload)
            results.append(result.model_dump() if hasattr(result, "model_dump") else result.dict())
        except HTTPException as exc:
            errors.append({"horizon": horizon, "status_code": exc.status_code, "detail": exc.detail})
        except Exception as exc:
            errors.append({"horizon": horizon, "status_code": 500, "detail": str(exc)})

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

    return {
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
            "fresh_run": True,
        },
        "data_status": {
            "market_prices": "real_or_mock_per_frame",
            "simulation_outputs": "inferred",
            "risk_metrics": "inferred",
            "fundamental_variables": "absent_unless_supplied",
        },
        "warning": (
            "Multi-frame output is probabilistic only. Compare horizons as scenario distributions, "
            "not as deterministic price paths or financial advice."
        ),
    }


@app.get("/latest", dependencies=[Depends(require_api_key)])
def latest() -> dict[str, Any]:
    return {
        "report_markdown": read_text(REPORT_PATH),
        "dashboard_markdown": read_text(DASHBOARD_PATH),
        "warning": "Latest local artifact only; call POST /run for a fresh run.",
    }
