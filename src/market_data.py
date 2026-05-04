from __future__ import annotations

import json
import csv
import os
import re
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from html import unescape
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
    allow_non_bitget_fallback = os.getenv("ALLOW_NON_BITGET_MARKET_FALLBACK", "0").strip().lower() in {"1", "true", "yes"}
    if frame is None and allow_online and allow_non_bitget_fallback:
        frame = fetch_coingecko_prices(asset, logger, days=days)
    elif frame is None and allow_online:
        logger.warning("non_bitget_market_fallback_disabled | source=coingecko_market_chart | policy=bitget_required")
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


def _fetch_bitget_liquidations(logger) -> tuple[float | None, str | None]:
    timeout_seconds = float(os.getenv("BITGET_LIQUIDATION_WS_TIMEOUT_SECONDS", "6"))
    source_name = "bitget_uta_liquidation_ws_btcusdt_quote_observed_window"
    if timeout_seconds <= 0:
        logger.warning("liquidations_absent | source=%s | reason=websocket_disabled", source_name)
        return None, None
    try:
        import websocket  # type: ignore
    except Exception as exc:
        logger.warning("liquidations_absent | source=%s | reason=websocket_client_unavailable | error=%s", source_name, exc)
        return None, None

    ws = None
    try:
        ws = websocket.create_connection("wss://ws.bitget.com/v3/ws/public", timeout=min(timeout_seconds, 10))
        ws.settimeout(max(1.0, timeout_seconds))
        ws.send(
            json.dumps(
                {
                    "op": "subscribe",
                    "args": [{"instType": "usdt-futures", "topic": "liquidation"}],
                }
            )
        )
        deadline = time.monotonic() + timeout_seconds
        total_quote_amount = 0.0
        btc_events = 0
        observed_push = False
        last_error = None
        while time.monotonic() < deadline:
            ws.settimeout(max(0.5, deadline - time.monotonic()))
            try:
                payload = json.loads(ws.recv())
            except Exception as exc:
                last_error = exc
                break
            if payload.get("event") == "error":
                logger.warning(
                    "liquidations_absent | source=%s | reason=bitget_subscription_error | msg=%s",
                    source_name,
                    payload.get("msg"),
                )
                return None, None
            rows = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(rows, list):
                continue
            observed_push = True
            for row in rows:
                if not isinstance(row, dict) or str(row.get("symbol", "")).upper() != "BTCUSDT":
                    continue
                amount = pd.to_numeric(pd.Series([row.get("amount")]), errors="coerce").iloc[0]
                if pd.notna(amount):
                    total_quote_amount += float(amount)
                    btc_events += 1
            break
        if observed_push:
            logger.info(
                "fundamental_loaded | field=liquidations | source=%s | value=%s | unit=USDT_quote | events=%s",
                source_name,
                total_quote_amount,
                btc_events,
            )
            return total_quote_amount, source_name
        logger.warning(
            "liquidations_absent | source=%s | reason=no_bitget_push_within_timeout | timeout_seconds=%s | last_error=%s",
            source_name,
            timeout_seconds,
            last_error,
        )
    except Exception as exc:
        logger.warning("liquidations_fetch_failed | source=%s | error=%s", source_name, exc)
    finally:
        try:
            if ws is not None:
                ws.close()
        except Exception:
            pass
    return None, None


def _fetch_bitget_exchange_reserves(logger) -> tuple[float | None, str | None]:
    url = "https://api.bitget.com/api/v3/market/proof-of-reserves"
    source_name = "bitget_proof_of_reserves_btc_platform_assets"
    try:
        payload = _request_json(url, timeout=15)
        if not payload or payload.get("code") != "00000":
            logger.warning(
                "exchange_reserves_absent | source=%s | payload_code=%s | msg=%s",
                source_name,
                (payload or {}).get("code"),
                (payload or {}).get("msg"),
            )
            return None, None
        reserve_data = (payload.get("data") or {}).get("list") or []
        for row in reserve_data:
            if str(row.get("coin", "")).upper() != "BTC":
                continue
            platform_assets = float(row["platformAssets"])
            logger.info(
                "fundamental_loaded | field=exchange_reserves | source=%s | value=%s | unit=BTC | reserve_ratio=%s | merkle_root=%s",
                source_name,
                platform_assets,
                row.get("reserveRatio"),
                (payload.get("data") or {}).get("merkleRootHash"),
            )
            return platform_assets, source_name
        logger.warning("exchange_reserves_absent | source=%s | reason=btc_row_missing", source_name)
    except Exception as exc:
        logger.warning("exchange_reserves_fetch_failed | source=%s | error=%s", source_name, exc)
    return None, None


def _fetch_stooq_quote(symbol: str, field_name: str, source_name: str, logger) -> tuple[float | None, str | None]:
    url = f"https://stooq.com/q/l/?s={symbol}&i=d"
    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "quant-btc-model/1.0",
                "Accept": "text/csv",
                "Accept-Encoding": "identity",
                "Connection": "close",
            },
        )
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


def _fetch_blockchain_hash_rate(logger) -> tuple[float | None, str | None]:
    url = "https://api.blockchain.info/charts/hash-rate?timespan=30days&format=json"
    source_name = "blockchain_info_hash_rate_chart"
    try:
        payload = _request_json(url, timeout=10)
        values = (payload or {}).get("values") or []
        for row in reversed(values):
            value = row.get("y")
            if value is not None:
                numeric_value = float(value)
                logger.info("fundamental_loaded | field=hash_rate | source=%s | value=%s", source_name, numeric_value)
                return numeric_value, source_name
        logger.warning("hash_rate_absent | source=%s | reason=no_numeric_value", source_name)
    except Exception as exc:
        logger.warning("hash_rate_fetch_failed | source=%s | error=%s", source_name, exc)
    return None, None


def _fetch_defillama_stablecoins_supply(logger) -> tuple[float | None, str | None]:
    url = "https://stablecoins.llama.fi/stablecoins?includePrices=true"
    source_name = "defillama_stablecoins_total_pegged_usd"
    try:
        payload = _request_json(url, timeout=15)
        assets = (payload or {}).get("peggedAssets") or []
        total = 0.0
        count = 0
        for asset in assets:
            value = (asset.get("circulating") or {}).get("peggedUSD")
            if value is None:
                continue
            try:
                total += float(value)
                count += 1
            except (TypeError, ValueError):
                continue
        if count and total > 0:
            logger.info(
                "fundamental_loaded | field=stablecoins_supply | source=%s | value=%s | assets=%s",
                source_name,
                total,
                count,
            )
            return total, source_name
        logger.warning("stablecoins_supply_absent | source=%s | reason=no_numeric_supply", source_name)
    except Exception as exc:
        logger.warning("stablecoins_supply_fetch_failed | source=%s | error=%s", source_name, exc)
    return None, None


def _parse_farside_number(value) -> float | None:
    raw = str(value).strip()
    if not raw or raw.lower() == "nan" or raw == "-":
        return None
    negative = raw.startswith("(") and raw.endswith(")")
    cleaned = raw.strip("()").replace(",", "")
    try:
        number = float(cleaned)
    except ValueError:
        return None
    return -number if negative else number


def _strip_html_cell(value: str) -> str:
    return " ".join(unescape(re.sub(r"<[^>]+>", "", value)).split())


def _extract_farside_flow_rows(html: str) -> list[dict[str, str]]:
    for table in re.findall(r"<table\b.*?</table>", html, flags=re.IGNORECASE | re.DOTALL):
        parsed_rows: list[list[str]] = []
        for row_html in re.findall(r"<tr\b.*?</tr>", table, flags=re.IGNORECASE | re.DOTALL):
            cells = re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", row_html, flags=re.IGNORECASE | re.DOTALL)
            if cells:
                parsed_rows.append([_strip_html_cell(cell) for cell in cells])
        if not parsed_rows:
            continue
        header = parsed_rows[0]
        if "Date" not in header or "Total" not in header:
            continue
        rows: list[dict[str, str]] = []
        for cells in parsed_rows[1:]:
            padded = cells + [""] * max(0, len(header) - len(cells))
            rows.append(dict(zip(header, padded[: len(header)])))
        return rows
    return []


def _fetch_farside_etf_flows(logger) -> tuple[float | None, str | None]:
    url = "https://farside.co.uk/bitcoin-etf-flow-all-data/"
    source_name = "farside_bitcoin_etf_flow_total_usd_m"
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "quant-btc-model/1.0"})
        with urllib.request.urlopen(request, timeout=20) as response:
            html = response.read().decode("utf-8", errors="ignore")
        rows = _extract_farside_flow_rows(html)
        if not rows:
            logger.warning("etf_flows_absent | source=%s | reason=no_flow_table", source_name)
            return None, None
        fund_columns = [column for column in rows[0] if str(column) not in {"Date", "Total"}]
        for row in reversed(rows):
            parsed_date = pd.to_datetime(row.get("Date"), format="%d %b %Y", errors="coerce", utc=True)
            if pd.isna(parsed_date):
                continue
            fund_values = [_parse_farside_number(row.get(column)) for column in fund_columns]
            # Skip placeholder rows where no fund has published a value yet.
            if not any(value is not None for value in fund_values):
                continue
            total_value = _parse_farside_number(row.get("Total"))
            if total_value is None:
                continue
            logger.info(
                "fundamental_loaded | field=etf_flows | source=%s | value=%s | unit=USD_m | date=%s",
                source_name,
                total_value,
                parsed_date.strftime("%Y-%m-%d"),
            )
            return total_value, source_name
        logger.warning("etf_flows_absent | source=%s | reason=no_published_total", source_name)
    except Exception as exc:
        logger.warning("etf_flows_fetch_failed | source=%s | error=%s", source_name, exc)
    return None, None


def fetch_farside_etf_flow_history(logger, limit: int = 60) -> pd.DataFrame:
    url = "https://farside.co.uk/bitcoin-etf-flow-all-data/"
    source_name = "farside_bitcoin_etf_flow_total_usd_m_history"
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "quant-btc-model/1.0"})
        with urllib.request.urlopen(request, timeout=20) as response:
            html = response.read().decode("utf-8", errors="ignore")
        rows = _extract_farside_flow_rows(html)
        parsed: list[dict] = []
        for row in rows:
            parsed_date = pd.to_datetime(row.get("Date"), format="%d %b %Y", errors="coerce", utc=True)
            total_value = _parse_farside_number(row.get("Total"))
            if pd.isna(parsed_date) or total_value is None:
                continue
            parsed.append(
                {
                    "timestamp": parsed_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "asset": "BTC",
                    "etf_flow_usd_m": float(total_value),
                    "source": source_name,
                    "statut": STATUS_REAL,
                }
            )
        if not parsed:
            logger.warning("etf_flow_history_absent | source=%s | reason=no_published_rows", source_name)
            return pd.DataFrame()
        frame = pd.DataFrame(parsed).drop_duplicates(subset=["timestamp"], keep="last").sort_values("timestamp")
        frame = frame.tail(max(1, int(limit))).reset_index(drop=True)
        out = PROCESSED_DIR / "BTC_etf_flow_history.csv"
        frame.to_csv(out, index=False)
        logger.info("etf_flow_history_loaded | source=%s | rows=%s", source_name, len(frame))
        return frame
    except Exception as exc:
        logger.warning("etf_flow_history_fetch_failed | source=%s | error=%s", source_name, exc)
        return pd.DataFrame()


def _fetch_fred_dgs10(logger) -> tuple[float | None, str | None]:
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10"
    source_name = "fred_dgs10_10y_treasury_rate"
    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "quant-btc-model/1.0",
                "Accept": "text/csv",
                "Accept-Encoding": "identity",
                "Connection": "close",
            },
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            text = response.read().decode("utf-8", errors="ignore").strip()
        rows = list(csv.DictReader(text.splitlines()))
        for row in reversed(rows):
            raw_value = (row.get("DGS10") or "").strip()
            if not raw_value or raw_value == ".":
                continue
            value = float(raw_value)
            logger.info(
                "fundamental_loaded | field=us_rates | source=%s | value=%s | date=%s",
                source_name,
                value,
                row.get("observation_date"),
            )
            return value, source_name
        logger.warning("us_rates_absent | source=%s | reason=no_numeric_dgs10", source_name)
    except Exception as exc:
        logger.warning("us_rates_fetch_failed | source=%s | error=%s", source_name, exc)
    return None, None


def _fetch_treasury_10y_rate(logger) -> tuple[float | None, str | None]:
    source_name = "treasury_daily_10y_yield_curve"
    current_year = datetime.now(timezone.utc).year
    for year in (current_year, current_year - 1):
        url = (
            "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
            f"daily-treasury-rates.csv/{year}/all?type=daily_treasury_yield_curve"
            f"&field_tdr_date_value={year}&page&_format=csv"
        )
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "quant-btc-model/1.0",
                    "Accept": "text/csv",
                    "Accept-Encoding": "identity",
                    "Connection": "close",
                },
            )
            with urllib.request.urlopen(request, timeout=20) as response:
                text = response.read().decode("utf-8", errors="ignore").strip()
            rows = list(csv.DictReader(text.splitlines()))
            for row in rows:
                raw_value = (row.get("10 Yr") or "").strip()
                if not raw_value:
                    continue
                value = float(raw_value)
                logger.info(
                    "fundamental_loaded | field=us_rates | source=%s | value=%s | date=%s",
                    source_name,
                    value,
                    row.get("Date"),
                )
                return value, source_name
            logger.warning("us_rates_absent | source=%s | year=%s | reason=no_numeric_10y", source_name, year)
        except Exception as exc:
            logger.warning("us_rates_fetch_failed | source=%s | year=%s | error=%s", source_name, year, exc)
    return None, None


def load_online_fundamental_snapshot(price_frame: pd.DataFrame, logger) -> tuple[dict[str, float], list[str]]:
    values: dict[str, float] = {}
    sources: list[str] = []

    etf_flows, source = _fetch_farside_etf_flows(logger)
    if etf_flows is not None:
        values["etf_flows"] = etf_flows
        sources.append(source or "farside_bitcoin_etf_flow_total_usd_m")

    funding_rate, source = _fetch_bitget_funding_rate(logger)
    if funding_rate is not None:
        values["funding_rate"] = funding_rate
        sources.append(source or "bitget_current_fund_rate")

    open_interest, source = _fetch_bitget_open_interest(logger)
    if open_interest is not None:
        values["open_interest"] = open_interest
        sources.append(source or "bitget_open_interest")

    liquidations, source = _fetch_bitget_liquidations(logger)
    if liquidations is not None:
        values["liquidations"] = liquidations
        sources.append(source or "bitget_uta_liquidation_ws_btcusdt_quote_observed_window")

    hash_rate, source = _fetch_blockchain_hash_rate(logger)
    if hash_rate is not None:
        values["hash_rate"] = hash_rate
        sources.append(source or "blockchain_info_hash_rate_chart")

    exchange_reserves, source = _fetch_bitget_exchange_reserves(logger)
    if exchange_reserves is not None:
        values["exchange_reserves"] = exchange_reserves
        sources.append(source or "bitget_proof_of_reserves_btc_platform_assets")

    stablecoins_supply, source = _fetch_defillama_stablecoins_supply(logger)
    if stablecoins_supply is not None:
        values["stablecoins_supply"] = stablecoins_supply
        sources.append(source or "defillama_stablecoins_total_pegged_usd")

    dxy, source = _fetch_stooq_quote("dx.f", "dxy", "stooq_dx_f_quote", logger)
    if dxy is not None:
        values["dxy"] = dxy
        sources.append(source or "stooq_dx_f_quote")

    us_rates, source = _fetch_fred_dgs10(logger)
    if us_rates is None:
        us_rates, source = _fetch_treasury_10y_rate(logger)
    if us_rates is not None:
        values["us_rates"] = us_rates
        sources.append(source or "official_10y_treasury_rate")

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
