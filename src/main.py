from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import correlation_model
import ensemble_model
import garch_model
import jump_diffusion
import liquidation_model
import monte_carlo
import regime_switching
import student_t_model
from confidence_score import compute_confidence_score
from config import BACKTESTS_DIR, DATA_DIR, DB_PATH, SIMULATIONS_DIR, STATUS_MISSING, STATUS_MOCK, STATUS_REAL, ensure_directories
from corpus_pipeline import run_corpus_pipeline
from database import as_json, init_database, insert_dataframe, insert_row, utc_now
from features import compute_technical_features, daily_returns
from logging_utils import setup_logger
from market_data import load_fundamental_features, load_market_prices
from position_sizing import position_sizing_summary
from report import generate_reports
from risk_metrics import compute_risk_metrics
from simulation_utils import seed_for, summarize_simulation
from stress_tests import run_stress_tests
from walk_forward import walk_forward_backtest


MODEL_REGISTRY = {
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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probabilistic quantitative decision engine for Bitcoin.")
    parser.add_argument("--asset", default="BTC", help="Asset symbol, default BTC.")
    parser.add_argument("--horizon", type=int, default=365, help="Forecast horizon in days.")
    parser.add_argument("--simulations", type=int, default=200000, help="Total simulation count.")
    parser.add_argument("--model", default="ensemble", choices=sorted(MODEL_REGISTRY.keys()))
    parser.add_argument("--skip-corpus", action="store_true", help="Skip corpus copy/chunk/claim pipeline.")
    parser.add_argument("--no-online", action="store_true", help="Do not attempt online market data fetch.")
    parser.add_argument("--max-corpus-docs", type=int, default=100, help="Maximum relevant corpus files to copy.")
    parser.add_argument("--spot-override-price", type=float, default=None, help="Optional externally captured spot price snapshot.")
    parser.add_argument("--spot-override-timestamp", default=None, help="Timestamp for --spot-override-price.")
    parser.add_argument("--spot-override-source", default=None, help="Source label for --spot-override-price.")
    return parser.parse_args(argv)


def _status_from_inputs(price_frame: pd.DataFrame) -> str:
    if price_frame is None or price_frame.empty:
        return STATUS_MISSING
    if price_frame["statut"].eq(STATUS_MOCK).any():
        return STATUS_MOCK
    if price_frame["statut"].eq(STATUS_REAL).any():
        return STATUS_REAL
    return STATUS_MISSING


def _clean_for_json(obj):
    if isinstance(obj, dict):
        return {k: _clean_for_json(v) for k, v in obj.items() if k not in {"terminal_prices", "terminal_returns", "sample_paths", "component_results"}}
    if isinstance(obj, list):
        return [_clean_for_json(v) for v in obj]
    if hasattr(obj, "item"):
        return obj.item()
    return obj


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ensure_directories()
    logger = setup_logger()
    logger.info("run_started | asset=%s | horizon=%s | simulations=%s | model=%s", args.asset, args.horizon, args.simulations, args.model)
    init_database(DB_PATH)

    try:
        corpus_summary = {"copied_documents": 0, "chunks": 0, "claims": 0, "skipped": True}
        if not args.skip_corpus:
            corpus_summary = run_corpus_pipeline(logger, max_docs=args.max_corpus_docs)

        price_frame = load_market_prices(
            args.asset,
            logger,
            days=max(1095, args.horizon + 500),
            allow_online=not args.no_online,
            spot_override={
                "price": args.spot_override_price,
                "timestamp": args.spot_override_timestamp,
                "source": args.spot_override_source,
            }
            if args.spot_override_price is not None
            else None,
        )
        input_status = _status_from_inputs(price_frame)
        insert_dataframe("market_prices", price_frame)

        fundamentals = load_fundamental_features(args.asset, price_frame, logger)
        insert_dataframe("fundamental_features", fundamentals)

        technical = compute_technical_features(price_frame, args.asset)
        insert_dataframe("technical_features", technical)

        returns = daily_returns(price_frame)
        spot_series = pd.to_numeric(price_frame["close"], errors="coerce").dropna()
        if spot_series.empty:
            logger.error("no_close_price_available | aborting_model_run_without_crash")
            return 1
        spot = float(spot_series.iloc[-1])
        run_id = f"{args.asset.upper()}_{args.model}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"

        base_backtests = []
        if args.model == "ensemble":
            for model_name in ensemble_model.MODEL_REGISTRY:
                base_backtests.extend(walk_forward_backtest(price_frame, args.asset, model_name, horizons=(30, 90, 365)))

        simulate = MODEL_REGISTRY[args.model]
        kwargs = {
            "returns": returns,
            "spot": spot,
            "horizon": args.horizon,
            "simulations": args.simulations,
            "seed": seed_for(run_id),
        }
        if args.model in {"correlation", "correlation_model"}:
            kwargs["fundamentals"] = fundamentals
        if args.model == "ensemble":
            kwargs["fundamentals"] = fundamentals
            kwargs["backtest_rows"] = base_backtests
        simulation_result = simulate(**kwargs)

        distribution = summarize_simulation(simulation_result["terminal_prices"], spot)
        risk = compute_risk_metrics(
            simulation_result["terminal_returns"],
            historical_returns=returns,
            sample_paths=simulation_result.get("sample_paths"),
        )
        stress = run_stress_tests(spot, simulation_result["terminal_prices"], simulation_result.get("sample_paths"))
        selected_backtests = walk_forward_backtest(price_frame, args.asset, args.model, horizons=(30, 90, 365))
        backtest_artifact = {
            "run_id": run_id,
            "asset": args.asset.upper(),
            "model": args.model,
            "rows": selected_backtests,
        }
        (BACKTESTS_DIR / f"{run_id}_backtest.json").write_text(
            json.dumps(backtest_artifact, ensure_ascii=True, indent=2, default=str),
            encoding="utf-8",
        )
        (BACKTESTS_DIR / "latest_backtest.json").write_text(
            json.dumps(backtest_artifact, ensure_ascii=True, indent=2, default=str),
            encoding="utf-8",
        )
        confidence = compute_confidence_score(price_frame, fundamentals, risk, distribution, selected_backtests)
        sizing = position_sizing_summary(risk, distribution)

        now = utc_now()
        insert_row(
            "model_runs",
            {
                "run_id": run_id,
                "timestamp": now,
                "asset": args.asset.upper(),
                "horizon_days": args.horizon,
                "simulations": args.simulations,
                "model": args.model,
                "input_status": input_status,
                "parameters_json": as_json(_clean_for_json(simulation_result.get("parameters", {}))),
                "metrics_json": as_json({"confidence": confidence, "distribution": distribution}),
                "source": "src/main.py",
                "statut": input_status,
            },
        )
        insert_row(
            "simulation_results",
            {
                "timestamp": now,
                "run_id": run_id,
                "model": args.model,
                "asset": args.asset.upper(),
                "horizon_days": args.horizon,
                "simulations": args.simulations,
                **distribution,
                "source": "simulation_engine",
                "statut": input_status,
            },
        )
        insert_row(
            "risk_metrics",
            {
                "timestamp": now,
                "run_id": run_id,
                "asset": args.asset.upper(),
                "horizon_days": args.horizon,
                **risk,
                "source": "risk_metrics.py",
                "statut": input_status,
            },
        )
        for row in selected_backtests:
            insert_row(
                "backtest_results",
                {
                    "timestamp": now,
                    "run_id": run_id,
                    **row,
                    "statut": input_status if row.get("statut") != STATUS_MISSING else STATUS_MISSING,
                },
            )

        artifact = {
            "run_id": run_id,
            "asset": args.asset.upper(),
            "model": args.model,
            "horizon": args.horizon,
            "simulations": args.simulations,
            "distribution": distribution,
            "risk_metrics": risk,
            "stress_tests": stress,
            "confidence": confidence,
            "position_sizing": sizing,
            "corpus_summary": corpus_summary,
            "parameters": _clean_for_json(simulation_result.get("parameters", {})),
        }
        artifact_path = SIMULATIONS_DIR / f"{run_id}_summary.json"
        artifact_path.write_text(json.dumps(artifact, ensure_ascii=True, indent=2, default=str), encoding="utf-8")

        reports = generate_reports(
            asset=args.asset,
            horizon=args.horizon,
            simulations=args.simulations,
            selected_model=args.model,
            run_id=run_id,
            price_frame=price_frame,
            fundamentals=fundamentals,
            technical_features=technical,
            simulation_result=simulation_result,
            distribution=distribution,
            risk=risk,
            stress_results=stress,
            backtests=selected_backtests,
            confidence=confidence,
            position_sizing=sizing,
            corpus_summary=corpus_summary,
        )
        logger.info("run_completed | run_id=%s | report=%s", run_id, reports["latest_report"])
        print(json.dumps({"run_id": run_id, "report": str(reports["latest_report"]), "dashboard": str(reports["dashboard_summary"])}, ensure_ascii=True))
        return 0
    except Exception as exc:
        logger.exception("run_failed_without_uncaught_crash | error=%s", exc)
        error_report = Path(DATA_DIR) / "last_error.json"
        error_report.write_text(json.dumps({"error": str(exc), "timestamp": utc_now()}, ensure_ascii=True, indent=2), encoding="utf-8")
        print(json.dumps({"error": str(exc), "error_report": str(error_report)}, ensure_ascii=True))
        return 1


if __name__ == "__main__":
    sys.exit(run())
