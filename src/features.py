from __future__ import annotations

import numpy as np
import pandas as pd

from config import FEATURES_DIR, STATUS_MISSING, STATUS_MOCK, STATUS_REAL, TRADING_DAYS


def _rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _macd(close: pd.Series) -> tuple[pd.Series, pd.Series]:
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    macd = ema_12 - ema_26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal


def compute_technical_features(price_frame: pd.DataFrame, asset: str) -> pd.DataFrame:
    frame = price_frame.copy()
    frame["timestamp_dt"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    frame = frame.sort_values("timestamp_dt")
    close = pd.to_numeric(frame["close"], errors="coerce")
    returns = close.pct_change()

    result = pd.DataFrame(
        {
            "timestamp": frame["timestamp"],
            "asset": asset.upper(),
            "return_1d": close.pct_change(1),
            "return_7d": close.pct_change(7),
            "return_30d": close.pct_change(30),
            "return_90d": close.pct_change(90),
            "return_365d": close.pct_change(365),
            "rsi_14": _rsi(close),
            "realized_vol_30d": returns.rolling(30).std() * np.sqrt(TRADING_DAYS),
            "realized_vol_90d": returns.rolling(90).std() * np.sqrt(TRADING_DAYS),
        }
    )
    macd, signal = _macd(close)
    result["macd"] = macd
    result["macd_signal"] = signal
    ath = close.cummax()
    result["drawdown"] = close / ath - 1
    result["distance_ath"] = close / ath - 1
    result["source"] = "feature_engineering"
    if frame["statut"].eq(STATUS_REAL).all():
        result["statut"] = STATUS_REAL
    elif frame["statut"].eq(STATUS_MOCK).any():
        result["statut"] = STATUS_MOCK
    else:
        result["statut"] = STATUS_MISSING
    out = FEATURES_DIR / f"{asset.upper()}_technical_features.csv"
    result.to_csv(out, index=False)
    return result


def latest_feature_snapshot(features: pd.DataFrame) -> dict:
    if features is None or features.empty:
        return {}
    return features.dropna(how="all").tail(1).to_dict("records")[0]


def daily_returns(price_frame: pd.DataFrame) -> pd.Series:
    frame = price_frame.sort_values("timestamp").copy()
    close = pd.to_numeric(frame["close"], errors="coerce")
    return close.pct_change().dropna()
