import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from config import DB_PATH, ensure_directories


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS market_prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        asset TEXT NOT NULL,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume REAL,
        source TEXT NOT NULL,
        statut TEXT NOT NULL CHECK (statut IN ('real', 'mock', 'missing')),
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS technical_features (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        asset TEXT NOT NULL,
        return_1d REAL,
        return_7d REAL,
        return_30d REAL,
        return_90d REAL,
        return_365d REAL,
        rsi_14 REAL,
        macd REAL,
        macd_signal REAL,
        realized_vol_30d REAL,
        realized_vol_90d REAL,
        drawdown REAL,
        distance_ath REAL,
        source TEXT NOT NULL,
        statut TEXT NOT NULL CHECK (statut IN ('real', 'mock', 'missing')),
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fundamental_features (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        asset TEXT NOT NULL,
        etf_flows REAL,
        funding_rate REAL,
        open_interest REAL,
        liquidations REAL,
        hash_rate REAL,
        exchange_reserves REAL,
        stablecoins_supply REAL,
        dxy REAL,
        us_rates REAL,
        nasdaq REAL,
        source TEXT NOT NULL,
        statut TEXT NOT NULL CHECK (statut IN ('real', 'mock', 'missing')),
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS risk_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        run_id TEXT,
        asset TEXT NOT NULL,
        horizon_days INTEGER,
        var_95 REAL,
        var_99 REAL,
        cvar_95 REAL,
        cvar_99 REAL,
        skewness REAL,
        kurtosis REAL,
        max_drawdown REAL,
        mean_simulated_max_drawdown REAL,
        expected_max_drawdown REAL,
        median_max_drawdown REAL,
        p95_max_drawdown REAL,
        worst_sample_drawdown REAL,
        drawdown_definition TEXT,
        conditional_volatility REAL,
        source TEXT NOT NULL,
        statut TEXT NOT NULL CHECK (statut IN ('real', 'mock', 'missing')),
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS model_runs (
        run_id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        asset TEXT NOT NULL,
        horizon_days INTEGER NOT NULL,
        simulations INTEGER NOT NULL,
        model TEXT NOT NULL,
        input_status TEXT NOT NULL,
        parameters_json TEXT,
        metrics_json TEXT,
        source TEXT NOT NULL,
        statut TEXT NOT NULL CHECK (statut IN ('real', 'mock', 'missing')),
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS simulation_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        run_id TEXT NOT NULL,
        model TEXT NOT NULL,
        asset TEXT NOT NULL,
        horizon_days INTEGER NOT NULL,
        simulations INTEGER NOT NULL,
        p10_return REAL,
        median_return REAL,
        p90_return REAL,
        p10_price REAL,
        median_price REAL,
        p90_price REAL,
        prob_up REAL,
        prob_down_10 REAL,
        prob_down_30 REAL,
        prob_up_30 REAL,
        prob_bull REAL,
        prob_bear REAL,
        prob_range REAL,
        source TEXT NOT NULL,
        statut TEXT NOT NULL CHECK (statut IN ('real', 'mock', 'missing')),
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS backtest_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        run_id TEXT,
        asset TEXT NOT NULL,
        horizon_days INTEGER NOT NULL,
        model TEXT NOT NULL,
        hit_rate REAL,
        brier_score REAL,
        calibration_error REAL,
        mean_absolute_error REAL,
        interval_coverage REAL,
        observations INTEGER,
        source TEXT NOT NULL,
        statut TEXT NOT NULL CHECK (statut IN ('real', 'mock', 'missing')),
        created_at TEXT NOT NULL
    )
    """,
]


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    ensure_directories()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_database(db_path: Path = DB_PATH) -> Path:
    with connect(db_path) as conn:
        for statement in SCHEMA:
            conn.execute(statement)
        migrate_database(conn)
        conn.commit()
    return db_path


def migrate_database(conn: sqlite3.Connection) -> None:
    risk_columns = {row[1] for row in conn.execute("PRAGMA table_info(risk_metrics)").fetchall()}
    migrations = {
        "mean_simulated_max_drawdown": "ALTER TABLE risk_metrics ADD COLUMN mean_simulated_max_drawdown REAL",
        "expected_max_drawdown": "ALTER TABLE risk_metrics ADD COLUMN expected_max_drawdown REAL",
        "median_max_drawdown": "ALTER TABLE risk_metrics ADD COLUMN median_max_drawdown REAL",
        "p95_max_drawdown": "ALTER TABLE risk_metrics ADD COLUMN p95_max_drawdown REAL",
        "worst_sample_drawdown": "ALTER TABLE risk_metrics ADD COLUMN worst_sample_drawdown REAL",
        "drawdown_definition": "ALTER TABLE risk_metrics ADD COLUMN drawdown_definition TEXT",
    }
    for column, statement in migrations.items():
        if column not in risk_columns:
            conn.execute(statement)


def insert_dataframe(table: str, df: pd.DataFrame, db_path: Path = DB_PATH) -> int:
    if df is None or df.empty:
        return 0
    payload = df.copy()
    if "created_at" not in payload.columns:
        payload["created_at"] = utc_now()
    with connect(db_path) as conn:
        payload.to_sql(table, conn, if_exists="append", index=False)
    return len(payload)


def insert_row(table: str, row: dict[str, Any], db_path: Path = DB_PATH) -> None:
    payload = dict(row)
    payload.setdefault("created_at", utc_now())
    columns = ", ".join(payload.keys())
    placeholders = ", ".join(["?"] * len(payload))
    values = list(payload.values())
    with connect(db_path) as conn:
        conn.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values)
        conn.commit()


def insert_rows(table: str, rows: Iterable[dict[str, Any]], db_path: Path = DB_PATH) -> int:
    count = 0
    for row in rows:
        insert_row(table, row, db_path=db_path)
        count += 1
    return count


def as_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, default=str)


def latest_rows(table: str, limit: int = 5, db_path: Path = DB_PATH) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        cursor = conn.execute(
            f"SELECT * FROM {table} ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]
