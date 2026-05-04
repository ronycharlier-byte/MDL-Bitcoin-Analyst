from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import os
import subprocess

import numpy as np
import pandas as pd

from config import FUNDAMENTAL_COLUMNS, REPORTS_DIR, STATUS_MOCK


def _fmt_pct(value) -> str:
    if value is None or not np.isfinite(value):
        return "NULL"
    return f"{100 * float(value):.2f}%"


def _fmt_num(value) -> str:
    if value is None or not np.isfinite(value):
        return "NULL"
    return f"{float(value):,.2f}"


def _fmt_price(value) -> str:
    if value is None or not np.isfinite(value):
        return "NULL"
    return f"${float(value):,.2f}"


def _code_version() -> str:
    for key in ("RENDER_GIT_COMMIT", "GIT_COMMIT", "SOURCE_VERSION"):
        value = os.getenv(key)
        if value:
            return value[:12]
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=Path(__file__).resolve().parents[1],
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


def _missing_data(price_frame: pd.DataFrame, fundamentals: pd.DataFrame) -> list[str]:
    missing = []
    for column in ["open", "high", "low", "close", "volume"]:
        if column in price_frame.columns and pd.to_numeric(price_frame[column], errors="coerce").isna().all():
            missing.append(f"market_prices.{column}")
    for column in FUNDAMENTAL_COLUMNS:
        if column in fundamentals.columns and pd.to_numeric(fundamentals[column], errors="coerce").isna().all():
            missing.append(f"fundamental_features.{column}")
    return missing


def _regime_breakdown(distribution: dict) -> dict:
    bull = float(distribution.get("prob_bull", 0.0) or 0.0)
    bear = float(distribution.get("prob_bear", 0.0) or 0.0)
    range_ = float(distribution.get("prob_range", 0.0) or 0.0)
    total = bull + bear + range_
    unclassified = max(0.0, 1.0 - total)
    close_to_complete = abs(total - 1.0) <= 0.01
    return {
        "bull": bull,
        "bear": bear,
        "range": range_,
        "classified_total": total,
        "unclassified": unclassified,
        "close_to_complete": close_to_complete,
    }


def _regime_note(regimes: dict) -> str:
    if regimes["close_to_complete"]:
        return "The bull/bear/range regime probabilities are close to 100%."
    gap = abs(1.0 - regimes["classified_total"])
    return (
        f"The bull/bear/range probabilities sum to {_fmt_pct(regimes['classified_total'])}, "
        f"leaving {_fmt_pct(gap)} as non-classified / transition. "
        "Do not present the bull/bear/range split as complete."
    )


def _dominant_scenario(distribution: dict) -> str:
    values = {
        "bull": distribution.get("prob_bull", 0.0),
        "bear": distribution.get("prob_bear", 0.0),
        "range": distribution.get("prob_range", 0.0),
    }
    return max(values, key=values.get)


def _market_bias(distribution: dict, confidence: dict | None = None, risk: dict | None = None) -> str:
    median = distribution.get("median_return", 0.0)
    bull = distribution.get("prob_bull", 0.0)
    bear = distribution.get("prob_bear", 0.0)
    score = (confidence or {}).get("score")
    drawdown = abs((risk or {}).get("max_drawdown") or 0.0)
    qualifier = ""
    if score is not None and score < 50:
        qualifier = " with low-to-moderate confidence"
    if drawdown >= 0.25:
        qualifier += " and material drawdown risk"
    if median > 0.10 and bull > bear:
        return f"probabilistic bullish bias{qualifier}"
    if median < -0.10 and bear > bull:
        return f"probabilistic bearish bias{qualifier}"
    return "range / uncertain bias"


def generate_reports(
    *,
    asset: str,
    horizon: int,
    simulations: int,
    selected_model: str,
    run_id: str,
    price_frame: pd.DataFrame,
    fundamentals: pd.DataFrame,
    technical_features: pd.DataFrame,
    simulation_result: dict,
    distribution: dict,
    risk: dict,
    stress_results: list[dict],
    backtests: list[dict],
    confidence: dict,
    position_sizing: dict,
    corpus_summary: dict,
) -> dict[str, Path]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    ordered_prices = price_frame.copy()
    ordered_prices["_timestamp_sort"] = pd.to_datetime(ordered_prices["timestamp"], errors="coerce", utc=True)
    ordered_prices = ordered_prices.dropna(subset=["_timestamp_sort"]).sort_values("_timestamp_sort")
    spot_row = ordered_prices[pd.to_numeric(ordered_prices["close"], errors="coerce").notna()].iloc[-1]
    spot = float(spot_row["close"])
    spot_timestamp = str(spot_row["timestamp"])
    spot_source = str(spot_row["source"])
    statuses = sorted(set(price_frame["statut"].dropna().astype(str)))
    data_tag = "MOCK" if STATUS_MOCK in statuses else ",".join(statuses)
    missing = _missing_data(price_frame, fundamentals)
    fundamental_missing = [item for item in missing if item.startswith("fundamental_features.")]
    fundamental_columns = [column for column in FUNDAMENTAL_COLUMNS if column in fundamentals.columns]
    available_fundamental_columns = [
        column
        for column in fundamental_columns
        if pd.to_numeric(fundamentals[column], errors="coerce").notna().any()
    ]
    if not available_fundamental_columns:
        fundamentals_status = "absent"
    elif fundamental_missing:
        fundamentals_status = "partial_real_absent"
    else:
        fundamentals_status = ",".join(sorted(set(fundamentals["statut"].dropna().astype(str))))
    regimes = _regime_breakdown(distribution)
    report_source_name = "reports/latest_report.md"
    weights = simulation_result.get("weights", {})
    component_lines = []
    if weights:
        for name, weight in sorted(weights.items(), key=lambda item: item[1], reverse=True):
            component_lines.append(f"- {name}: {100 * weight:.2f}%")
    else:
        component_lines.append(f"- {selected_model}: 100.00%")

    backtest_lines = []
    for row in backtests:
        backtest_lines.append(
            "| {horizon_days} | {hit} | {brier} | {calib} | {mae} | {cover} | {obs} |".format(
                horizon_days=row.get("horizon_days"),
                hit=_fmt_pct(row.get("hit_rate")),
                brier=_fmt_num(row.get("brier_score")),
                calib=_fmt_num(row.get("calibration_error")),
                mae=_fmt_pct(row.get("mean_absolute_error")),
                cover=_fmt_pct(row.get("interval_coverage")),
                obs=row.get("observations"),
            )
        )

    stress_lines = []
    for row in stress_results:
        stress_lines.append(
            f"| {row['scenario']} | {_fmt_pct(row['instant_return'])} | "
            f"{_fmt_price(row['price_after_instant_shock'])} | "
            f"{_fmt_price(row['median_terminal_after_shock'])} |"
        )

    report = f"""# Quant BTC Model - Latest Report

Generated: {timestamp}
Run ID: `{run_id}`
Asset: {asset.upper()}
Horizon: {horizon} days
Simulations: {simulations}
Model: {selected_model}
Data status: {data_tag}

This report is probabilistic infrastructure output, not a deterministic forecast and not financial advice.

## Provenance des chiffres

- Report source: {report_source_name}
- Report date: {timestamp}
- Model run ID: `{run_id}`
- Model version: source-code snapshot in `quant_btc_model/src`
- Code version / git commit: {_code_version()}
- Reference spot price: {_fmt_price(spot)}
- Reference spot timestamp: {spot_timestamp}
- Reference spot source: {spot_source}
- Market prices status: {data_tag}
- Simulation outputs status: inferred
- Risk metrics status: inferred
- Fundamental variables status: {fundamentals_status}
- Fundamental variables with real values: {", ".join(available_fundamental_columns) if available_fundamental_columns else "none"}
- Rule: no precise quantitative figure should be reused without this source, report date, run ID, reference spot, and status context.

## Donnees utilisees

- Market rows: {len(price_frame)}
- Latest spot used: {_fmt_price(spot)}
- Latest spot timestamp: {spot_timestamp}
- Market sources: {", ".join(sorted(set(price_frame["source"].dropna().astype(str))))}
- Fundamental rows: {len(fundamentals)}
- Technical feature rows: {len(technical_features)}
- Corpus documents copied: {corpus_summary.get("copied_documents", 0)}
- Corpus chunks: {corpus_summary.get("chunks", 0)}
- Corpus claims: {corpus_summary.get("claims", 0)}

## Donnees manquantes

{chr(10).join(f"- {item}: NULL, warning logged" for item in missing) if missing else "- None detected in required fields."}

## Hypotheses

- All outputs are distributions, probabilities, or risk measures.
- MOCK data are explicitly tagged when real market data cannot be loaded.
- Fundamental fields remain NULL unless supplied through CSV files in `data/raw`.
- Historical stationarity is a working assumption and can fail during structural regime changes.
- Stress tests are scenario shocks, not predictions.

## Resultats par modele

{chr(10).join(component_lines)}

## Distribution horizon {horizon} jours

- P10 return: {_fmt_pct(distribution.get("p10_return"))}
- Median return: {_fmt_pct(distribution.get("median_return"))}
- P90 return: {_fmt_pct(distribution.get("p90_return"))}
- P10 price: {_fmt_price(distribution.get("p10_price"))}
- Median price: {_fmt_price(distribution.get("median_price"))}
- P90 price: {_fmt_price(distribution.get("p90_price"))}

## Probabilites seuils

- P(return > 0): {_fmt_pct(distribution.get("prob_up"))}
- P(return <= -10%): {_fmt_pct(distribution.get("prob_down_10"))}
- P(return <= -30%): {_fmt_pct(distribution.get("prob_down_30"))}
- P(return >= +30%): {_fmt_pct(distribution.get("prob_up_30"))}

## Repartition des regimes

- Bull: {_fmt_pct(regimes["bull"])}
- Bear: {_fmt_pct(regimes["bear"])}
- Range: {_fmt_pct(regimes["range"])}
- Non classe / transition: {_fmt_pct(regimes["unclassified"])}
- Controle de coherence: {_regime_note(regimes)}

## VaR / CVaR

- VaR 95 du rendement simule, exprimee comme perte positive: {_fmt_pct(risk.get("var_95"))}
- VaR 99 du rendement simule, exprimee comme perte positive: {_fmt_pct(risk.get("var_99"))}
- CVaR 95 du rendement simule, exprimee comme perte moyenne de queue positive: {_fmt_pct(risk.get("cvar_95"))}
- CVaR 99 du rendement simule, exprimee comme perte moyenne de queue positive: {_fmt_pct(risk.get("cvar_99"))}
- Interpretation VaR 95: under model assumptions, the worst 5% simulated scenarios begin around this loss threshold or worse.
- Interpretation CVaR 95: this estimates the average loss inside scenarios worse than VaR 95.
- Skewness: {_fmt_num(risk.get("skewness"))}
- Kurtosis: {_fmt_num(risk.get("kurtosis"))}
- Expected max drawdown: {_fmt_pct(risk.get("max_drawdown"))}
- Conditional volatility: {_fmt_pct(risk.get("conditional_volatility"))}

## Stress tests

| Scenario | Instant shock | Shocked spot | Shocked median terminal |
|---|---:|---:|---:|
{chr(10).join(stress_lines)}

## Position sizing

- Risk budget: {_fmt_pct(position_sizing.get("risk_budget"))}
- VaR based fraction: {_fmt_pct(position_sizing.get("var_based_fraction"))}
- CVaR based fraction: {_fmt_pct(position_sizing.get("cvar_based_fraction"))}
- Kelly fraction: {_fmt_pct(position_sizing.get("kelly_fraction"))}
- Drawdown limited fraction: {_fmt_pct(position_sizing.get("drawdown_limited_fraction"))}

## Confidence score

- Score: {confidence.get("score", 0)}/100
- Components: {confidence.get("components", {})}
- Notes: {"; ".join(confidence.get("notes", [])) if confidence.get("notes") else "No major notes."}

## Backtest

| Horizon | Hit rate | Brier | Calibration error | MAE | Interval coverage | Obs |
|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(backtest_lines)}

## Limites explicites

- The model never emits certainty.
- Results depend on input data quality and may be MOCK if no real data source is available.
- Every precise quantitative figure must be traceable to an export file, report, run ID, connected database, or explicit user-provided result.
- If confidence score is below 50/100, any directional conclusion must be described as weak or fragile.
- Structural breaks, exchange outages, regulatory events, and liquidity gaps can invalidate historical calibration.
- NULL fundamental fields reduce confidence and should be replaced with audited data sources before production capital use.
"""

    latest_report = REPORTS_DIR / "latest_report.md"
    latest_report.write_text(report, encoding="utf-8")

    dominant = _dominant_scenario(distribution)
    dashboard = f"""# Dashboard Summary

- Source: reports/latest_report.md
- Report date: {timestamp}
- Model run ID: `{run_id}`
- Reference spot: {_fmt_price(spot)}
- Status mix: price data {data_tag}; simulation results inferred; fundamental variables {fundamentals_status}
- Biais marche: {_market_bias(distribution, confidence=confidence, risk=risk)}
- Risque court terme: VaR95 loss {_fmt_pct(risk.get("var_95"))}, CVaR95 tail loss {_fmt_pct(risk.get("cvar_95"))}
- Risque long terme: P10 {_fmt_pct(distribution.get("p10_return"))}, expected drawdown {_fmt_pct(risk.get("max_drawdown"))}
- Scenario dominant: {dominant}; non classe / transition {_fmt_pct(regimes["unclassified"])}
- Niveau d'invalidation: {_fmt_price(distribution.get("p10_price"))} on horizon distribution P10
- Confidence score: {confidence.get("score", 0)}/100
"""
    dashboard_summary = REPORTS_DIR / "dashboard_summary.md"
    dashboard_summary.write_text(dashboard, encoding="utf-8")
    return {"latest_report": latest_report, "dashboard_summary": dashboard_summary}
