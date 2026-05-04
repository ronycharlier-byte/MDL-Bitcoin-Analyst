from __future__ import annotations

import json
import csv
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from config import FUNDAMENTAL_COLUMNS, PROCESSED_DIR, RAW_DIR, STATUS_MISSING, STATUS_MOCK, STATUS_REAL
from logging_utils import log_missing, log_mock


def _standardize_price_frame(df: pd.DataFrame, asset: str, source: str, statut: str) -> pd.DataFrame:
    rename_map = {}
    for column in df.columns:
        key = str(column).strip().lower()
        if key in {"date", "time", "datetime"}:
            rename_map[column] = "timestamp"
        elif key in {"price", "close", "adj close", "adj_close"}:
            rename_map[column] = "close"
        elif key == "open":
            rename_map[column] = "open"
        elif key == "high":
            rename_map[column] = "high"
        elif key == "low":
            rename_map[column] = "low"
        elif key in {"volume", "vol"}:
            rename_map[column] = "volume"
    frame = df.rename(columns=rename_map).copy()
    if "timestamp" not in frame.columns:
        frame["timestamp"] = pd.date_range(end=pd.Timestamp.utcnow(), periods=len(frame), freq="D")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    frame = frame.dropna(subset=["timestamp"]).sort_values("timestamp")

    for column in ["open", "high", "low", "close", "volume"]:
        if column not in frame.columns:
            frame[column] = np.nan
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame["asset"] = asset.upper()
    frame["source"] = source
    frame["statut"] = statut
    frame = frame[["timestamp", "asset", "open", "high", "low", "close", "volume", "source", "statut"]]
    frame["timestamp"] = frame["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return frame.drop_duplicates(subset=["timestamp", "asset"], keep="last")


def load_prices_from_csv(asset: str, logger) -> pd.DataFrame | None:
    candidates = [
        RAW_DIR / f"{asset.upper()}_prices.csv",
        RAW_DIR / f"{asset.lower()}_prices.csv",
        RAW_DIR / "market_prices.csv",
    ]
    for path in candidates:
        if path.exists():
            try:
                raw = pd.read_csv(path)
                frame = _standardize_price_frame(raw, asset, str(path.name), STATUS_REAL)
                logger.info("market_prices_loaded | source=%s | rows=%s", path, len(frame))
                return frame
            except Exception as exc:
                logger.exception("market_prices_csv_error | path=%s | error=%s", path, exc)
    return None


def fetch_coingecko_prices(asset: str, logger, days: int = 1095) -> pd.DataFrame | None:
    coin_id = {"BTC": "bitcoin"}.get(asset.upper())
    if not coin_id:
        logger.warning("coingecko_unsupported_asset | asset=%s", asset)
        return None
    url = (
        f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        f"?vs_currency=usd&days={days}&interval=daily"
    )
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "quant-btc-model/1.0"})
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
        prices = payload.get("prices", [])
        volumes = dict(payload.get("total_volumes", []))
        rows = []
        for ms, close in prices:
            ts = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
            rows.append(
                {
                    "timestamp": ts,
                    "close": close,
                    "volume": volumes.get(ms),
                }
            )
        if not rows:
            return None
        frame = _standardize_price_frame(pd.DataFrame(rows), asset, "coingecko_market_chart", STATUS_REAL)
        logger.info("market_prices_loaded | source=coingecko | rows=%s", len(frame))
        return frame
    except Exception as exc:
        logger.warning("coingecko_fetch_failed | error=%s", exc)
        return None


def fetch_bitget_prices(asset: str, logger, days: int = 1095) -> pd.DataFrame | None:
    if asset.upper() != "BTC":
        return None
    rows = []
    end = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=days)
    end_ms = int(end.timestamp() * 1000)
    try:
        while True:
            url = (
                "https://api.bitget.com/api/v2/spot/market/history-candles"
                f"?symbol=BTCUSDT&granularity=1Dutc&endTime={end_ms}&limit=200"
            )
            request = urllib.request.Request(url, headers={"User-Agent": "quant-btc-model/1.0"})
            with urllib.request.urlopen(request, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if payload.get("code") != "00000":
                logger.warning("bitget_fetch_failed | code=%s | msg=%s", payload.get("code"), payload.get("msg"))
                return None
            data = payload.get("data", [])
            if not data:
                break
            timestamps = []
            for item in data:
                if len(item) < 6:
                    continue
                ts_ms, open_, high, low, close, volume = item[:6]
                ts = datetime.fromtimestamp(int(ts_ms) / 1000, tz=timezone.utc)
                timestamps.append(int(ts_ms))
                if ts < start:
                    continue
                rows.append(
                    {
                        "timestamp": ts,
                        "open": open_,
                        "high": high,
                        "low": low,
                        "close": close,
                        "volume": volume,
                    }
                )
            if not timestamps:
                break
            earliest = min(timestamps)
            if datetime.fromtimestamp(earliest / 1000, tz=timezone.utc) <= start:
                break
            next_end = earliest - 1
            if next_end >= end_ms:
                break
            end_ms = next_end
        if not rows:
            return None
        frame = _standardize_price_frame(pd.DataFrame(rows), asset, "bitget_btcusdt_spot_candles", STATUS_REAL)
        logger.info("market_prices_loaded | source=bitget | rows=%s", len(frame))
        return frame
    except Exception as exc:
        logger.warning("bitget_fetch_failed | error=%s", exc)
        return None


def _request_json(url: str, timeout: int = 10) -> dict | None:
    request = urllib.request.Request(url, headers={"User-Agent": "quant-btc-model/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_bitget_spot_quote(asset: str, logger) -> pd.DataFrame | None:
    if asset.upper() != "BTC":
        return None
    url = "https://api.bitget.com/api/v2/spot/market/tickers?symbol=BTCUSDT"
    try:
        payload = _request_json(url, timeout=10)
        if payload.get("code") != "00000":
            logger.warning("bitget_spot_fetch_failed | code=%s | msg=%s", payload.get("code"), payload.get("msg"))
            return None
        data = payload.get("data") or []
        if not data:
            logger.warning("bitget_spot_fetch_empty | symbol=BTCUSDT")
            return None
        ticker = data[0]
        timestamp_ms = int(ticker.get("ts") or payload.get("requestTime"))
        last_price = float(ticker.get("lastPr"))
        if not np.isfinite(last_price) or last_price <= 0:
            logger.warning("bitget_spot_invalid_last_price | value=%s", ticker.get("lastPr"))
            return None
        row = {
            "timestamp": datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc),
            "open": ticker.get("open"),
            "high": ticker.get("high24h"),
            "low": ticker.get("low24h"),
            "close": last_price,
            "volume": ticker.get("baseVolume") or ticker.get("quoteVolume"),
        }
        frame = _standardize_price_frame(
            pd.DataFrame([row]),
            asset,
            "bitget_btcusdt_spot_ticker_realtime",
            STATUS_REAL,
        )
        logger.info(
            "market_spot_loaded | source=bitget_spot_ticker | price=%s | timestamp=%s",
            last_price,
            frame["timestamp"].iloc[-1],
        )
        return frame
    except Exception as exc:
        logger.warning("bitget_spot_fetch_failed | error=%s", exc)
        return None


def spot_override_frame(
    asset: str,
    price: float | None,
    timestamp: str | None,
    source: str | None,
    logger,
) -> pd.DataFrame | None:
    if price is None:
        return None
    try:
        numeric_price = float(price)
        if not np.isfinite(numeric_price) or numeric_price <= 0:
            return None
        ts = pd.to_datetime(timestamp, errors="coerce", utc=True) if timestamp else pd.Timestamp.utcnow()
        if pd.isna(ts):
            ts = pd.Timestamp.utcnow()
        frame = _standardize_price_frame(
            pd.DataFrame(
                [
                    {
                        "timestamp": ts,
                        "open": np.nan,
                        "high": np.nan,
                        "low": np.nan,
                        "close": numeric_price,
                        "volume": np.nan,
                    }
                ]
            ),
            asset,
            source or "api_spot_snapshot_override",
            STATUS_REAL,
        )
        logger.info(
            "market_spot_override_loaded | source=%s | price=%s | timestamp=%s",
            frame["source"].iloc[-1],
            numeric_price,
            frame["timestamp"].iloc[-1],
        )
        return frame
    except Exception as exc:
        logger.warning("spot_override_invalid | error=%s", exc)
        return None


def append_realtime_spot(
    price_frame: pd.DataFrame,
    asset: str,
    logger,
    allow_online: bool = True,
    spot_override: dict | None = None,
) -> pd.DataFrame:
    if not allow_online:
        return price_frame
    spot_frame = None
    if spot_override:
        spot_frame = spot_override_frame(
            asset,
            spot_override.get("price"),
            spot_override.get("timestamp"),
            spot_override.get("source"),
            logger,
        )
    if spot_frame is None:
        spot_frame = fetch_bitget_spot_quote(asset, logger)
    if spot_frame is None or spot_frame.empty:
        logger.warning("realtime_spot_absent | keeping_latest_available_close")
        return price_frame
    if price_frame is None or price_frame.empty:
        return spot_frame

    combined = pd.concat([price_frame, spot_frame], ignore_index=True)
    combined["timestamp_sort"] = pd.to_datetime(combined["timestamp"], errors="coerce", utc=True)
    combined = combined.dropna(subset=["timestamp_sort"]).sort_values("timestamp_sort")
    combined = combined.drop_duplicates(subset=["timestamp", "asset"], keep="last")
    combined = combined.drop(columns=["timestamp_sort"])
    logger.info(
        "realtime_spot_appended | source=%s | latest_close=%s",
        spot_frame["source"].iloc[-1],
        spot_frame["close"].iloc[-1],
    )
    return combined


def generate_mock_prices(asset: str, logger, days: int = 1095, seed: int = 42) -> pd.DataFrame:
    log_mock(logger, "market_prices", "no local real CSV and online fetch unavailable")
    rng = np.random.default_rng(seed)
    mu_daily = 0.00025
    sigma_daily = 0.035
    jumps = rng.choice([0.0, -0.12, 0.10], size=days, p=[0.975, 0.015, 0.010])
    returns = rng.normal(mu_daily, sigma_daily, days) + jumps
    close = 65000.0 * np.exp(np.cumsum(returns))
    open_ = np.r_[close[0], close[:-1]]
    spread = np.abs(rng.normal(0.0, 0.015, days))
    high = np.maximum(open_, close) * (1 + spread)
    low = np.minimum(open_, close) * (1 - spread)
    volume = rng.lognormal(mean=22.0, sigma=0.35, size=days)
    timestamps = pd.date_range(end=pd.Timestamp.utcnow().normalize(), periods=days, freq="D", tz="UTC")
    raw = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )
    return _standardize_price_frame(raw, asset, "synthetic_market_generator", STATUS_MOCK)


def load_market_prices(
    asset: str,
    logger,
    days: int = 1095,
    allow_online: bool = True,
    spot_override: dict | None = None,
) -> pd.DataFrame:
    frame = load_prices_from_csv(asset, logger)
    if frame is None and allow_online:
        frame = fetch_bitget_prices(asset, logger, days=days)
    if frame is None and allow_online:
        frame = fetch_coingecko_prices(asset, logger, days=days)
    if frame is None or frame.empty:
        frame = generate_mock_prices(asset, logger, days=days)
    frame = append_realtime_spot(frame, asset, logger, allow_online=allow_online, spot_override=spot_override)

    for column in ["open", "high", "low", "close", "volume"]:
        if frame[column].isna().all():
            log_missing(logger, f"market_prices.{column}", frame["source"].iloc[-1])

    out = PROCESSED_DIR / f"{asset.upper()}_market_prices.csv"
    frame.to_csv(out, index=False)
    return frame


def _latest_price_timestamp(price_frame: pd.DataFrame) -> str:
    if price_frame is None or price_frame.empty:
        return pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    timestamps = pd.to_datetime(price_frame["timestamp"], errors="coerce", utc=True).dropna()
    if timestamps.empty:
        return pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    return timestamps.iloc[-1].strftime("%Y-%m-%dT%H:%M:%SZ")


def _fetch_bitget_funding_rate(logger) -> tuple[float | None, str | None]:
    url = "https://api.bitget.com/api/v2/mix/market/current-fund-rate?symbol=BTCUSDT&productType=usdt-futures"
    try:
        payload = _request_json(url, timeout=10)
        if payload and payload.get("code") == "00000" and payload.get("data"):
            value = float(payload["data"][0]["fundingRate"])
            logger.info("fundamental_loaded | field=funding_rate | source=bitget_current_fund_rate | value=%s", value)
            return value, "bitget_current_fund_rate"
        logger.warning("funding_rate_absent | source=bitget_current_fund_rate | payload_code=%s", (payload or {}).get("code"))
    except Exception as exc:
        logger.warning("funding_rate_fetch_failed | source=bitget_current_fund_rate | error=%s", exc)
    return None, None


def _fetch_bitget_open_interest(logger) -> tuple[float | None, str | None]:
    url = "https://api.bitget.com/api/v2/mix/market/open-interest?symbol=BTCUSDT&productType=usdt-futures"
    try:
        payload = _request_json(url, timeout=10)
        if payload and payload.get("code") == "00000" and payload.get("data"):
            values = payload["data"].get("openInterestList") or []
            if values:
                value = float(values[0]["size"])
                logger.info("fundamental_loaded | field=open_interest | source=bitget_open_interest | value=%s", value)
                return value, "bitget_open_interest"
        logger.warning("open_interest_absent | source=bitget_open_interest | payload_code=%s", (payload or {}).get("code"))
    except Exception as exc:
        logger.warning("open_interest_fetch_failed | source=bitget_open_interest | error=%s", exc)
    return None, None


def _fetch_stooq_quote(symbol: str, field_name: str, source_name: str, logger) -> tuple[float | None, str | None]:
    url = f"https://stooq.com/q/l/?s={symbol}&i=d"
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "quant-btc-model/1.0"})
        with urllib.request.urlopen(request, timeout=10) as response:
            text = response.read().decode("utf-8", errors="ignore").strip()
        rows = list(csv.reader(text.splitlines()))
        if not rows:
            return None, None
        row = rows[-1]
        if len(row) < 7 or row[1].upper() == "N/D":
            logger.warning("%s_absent | source=%s | raw=%s", field_name, source_name, text[:200])
            return None, None
        value = float(row[6])
        logger.info("fundamental_loaded | field=%s | source=%s | value=%s", field_name, source_name, value)
        return value, source_name
    except Exception as exc:
        logger.warning("%s_fetch_failed | source=%s | error=%s", field_name, source_name, exc)
    return None, None


def load_online_fundamental_snapshot(price_frame: pd.DataFrame, logger) -> tuple[dict[str, float], list[str]]:
    values: dict[str, float] = {}
    sources: list[str] = []

    funding_rate, source = _fetch_bitget_funding_rate(logger)
    if funding_rate is not None:
        values["funding_rate"] = funding_rate
        sources.append(source or "bitget_current_fund_rate")

    open_interest, source = _fetch_bitget_open_interest(logger)
    if open_interest is not None:
        values["open_interest"] = open_interest
        sources.append(source or "bitget_open_interest")

    dxy, source = _fetch_stooq_quote("dx.f", "dxy", "stooq_dx_f_quote", logger)
    if dxy is not None:
        values["dxy"] = dxy
        sources.append(source or "stooq_dx_f_quote")

    nasdaq, source = _fetch_stooq_quote("%5Endx", "nasdaq", "stooq_ndx_quote", logger)
    if nasdaq is not None:
        values["nasdaq"] = nasdaq
        sources.append(source or "stooq_ndx_quote")

    return values, sorted(set(sources))


def load_fundamental_features(asset: str, price_frame: pd.DataFrame, logger) -> pd.DataFrame:
    candidates = [
        RAW_DIR / f"{asset.upper()}_fundamentals.csv",
        RAW_DIR / f"{asset.lower()}_fundamentals.csv",
        RAW_DIR / "fundamental_features.csv",
    ]
    for path in candidates:
        if path.exists():
            try:
                raw = pd.read_csv(path)
                frame = raw.copy()
                if "timestamp" not in frame.columns:
                    logger.warning("fundamentals_missing_timestamp | path=%s", path)
                    frame["timestamp"] = price_frame["timestamp"].tail(len(frame)).values
                frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
                frame["asset"] = asset.upper()
                for column in FUNDAMENTAL_COLUMNS:
                    if column not in frame.columns:
                        frame[column] = np.nan
                        log_missing(logger, f"fundamental_features.{column}", path.name)
                    frame[column] = pd.to_numeric(frame[column], errors="coerce")
                frame["source"] = path.name
                frame["statut"] = STATUS_REAL
                frame["timestamp"] = frame["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                return frame[["timestamp", "asset", *FUNDAMENTAL_COLUMNS, "source", "statut"]]
            except Exception as exc:
                logger.exception("fundamentals_csv_error | path=%s | error=%s", path, exc)

    frame = pd.DataFrame(
        {
            "timestamp": price_frame["timestamp"],
            "asset": asset.upper(),
            **{column: np.nan for column in FUNDAMENTAL_COLUMNS},
            "source": "no_fundamental_source",
            "statut": STATUS_MISSING,
        }
    )
    if asset.upper() == "BTC":
        snapshot, sources = load_online_fundamental_snapshot(price_frame, logger)
        if snapshot:
            latest_timestamp = _latest_price_timestamp(price_frame)
            if frame.empty:
                frame = pd.DataFrame(
                    {
                        "timestamp": [latest_timestamp],
                        "asset": [asset.upper()],
                        **{column: [np.nan] for column in FUNDAMENTAL_COLUMNS},
                        "source": ["no_fundamental_source"],
                        "statut": [STATUS_MISSING],
                    }
                )
            latest_index = frame.index[-1]
            frame.loc[latest_index, "timestamp"] = latest_timestamp
            for column, value in snapshot.items():
                frame.loc[latest_index, column] = value
            frame.loc[latest_index, "source"] = ",".join(sources)
            frame.loc[latest_index, "statut"] = STATUS_REAL
            logger.info(
                "fundamentals_partial_snapshot_loaded | fields=%s | sources=%s",
                sorted(snapshot),
                sources,
            )

    for column in FUNDAMENTAL_COLUMNS:
        if pd.to_numeric(frame[column], errors="coerce").isna().all():
            log_missing(logger, f"fundamental_features.{column}", "no_online_or_local_source")
    if frame[FUNDAMENTAL_COLUMNS].isna().all().all():
        logger.warning("fundamentals_absent | all required fields left NULL | statut=missing")
    else:
        logger.warning("fundamentals_partial | unavailable_fields_left_NULL | statut=mixed_real_missing")
    out = PROCESSED_DIR / f"{asset.upper()}_fundamental_features.csv"
    frame.to_csv(out, index=False)
    return frame
