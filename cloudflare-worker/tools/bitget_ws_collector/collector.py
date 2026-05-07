#!/usr/bin/env python3
"""
Bitget realtime collector for Quant BTC Model.

Purpose:
- keep a compact Bitget-only realtime stream outside Cloudflare Workers;
- post snapshots to the Worker /realtime/ingest endpoint;
- never invent missing fields.

Example:
  python collector.py \
    --worker-url https://quant-btc-model-lite.mdl-bitcoin-analyst.workers.dev \
    --secret "$REALTIME_INGEST_SECRET"
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
import urllib.request
from datetime import datetime, timezone
from typing import Any

try:
    import websockets
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Install dependency first: pip install websockets") from exc


BITGET_SPOT_WS = "wss://ws.bitget.com/v2/ws/public"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def to_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def post_snapshot(worker_url: str, secret: str, payload: dict[str, Any]) -> None:
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        f"{worker_url.rstrip('/')}/realtime/ingest",
        data=data,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-ingest-secret": secret,
            "user-agent": "quant-btc-bitget-ws-collector/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        response.read()


def normalize_ticker(message: dict[str, Any]) -> dict[str, Any] | None:
    data = message.get("data")
    if not isinstance(data, list) or not data:
        return None
    item = data[0] if isinstance(data[0], dict) else {}
    bid = to_float(item.get("bidPr") or item.get("bid"))
    ask = to_float(item.get("askPr") or item.get("ask"))
    last = to_float(item.get("lastPr") or item.get("last"))
    price = last or ((bid + ask) / 2 if bid is not None and ask is not None else None)
    return {
        "asset": "BTC",
        "source": "bitget_spot_ws_ticker",
        "kind": "websocket_ticker",
        "price": price,
        "bid": bid,
        "ask": ask,
        "spread_bps": ((ask - bid) / price * 10000) if bid is not None and ask is not None and price else None,
        "liquidations_status": "absent",
        "observed_at_utc": utc_now(),
        "raw_channel": "ticker",
    }


async def run(args: argparse.Namespace) -> None:
    subscribe = {
        "op": "subscribe",
        "args": [
            {
                "instType": "SPOT",
                "channel": "ticker",
                "instId": "BTCUSDT",
            }
        ],
    }
    last_post = 0.0
    while True:
        try:
            async with websockets.connect(BITGET_SPOT_WS, ping_interval=20, ping_timeout=20) as ws:
                await ws.send(json.dumps(subscribe))
                async for raw in ws:
                    message = json.loads(raw)
                    snapshot = normalize_ticker(message)
                    if not snapshot:
                        continue
                    now = time.time()
                    if now - last_post < args.min_interval_seconds:
                        continue
                    post_snapshot(args.worker_url, args.secret, snapshot)
                    last_post = now
                    print(f"{utc_now()} posted {snapshot['source']} price={snapshot.get('price')}", flush=True)
        except Exception as exc:
            print(f"{utc_now()} collector error: {exc}; reconnecting in {args.reconnect_seconds}s", flush=True)
            await asyncio.sleep(args.reconnect_seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bitget WebSocket collector for Quant BTC Model")
    parser.add_argument("--worker-url", required=True, help="Worker origin, for example https://quant-btc-model-lite...workers.dev")
    parser.add_argument("--secret", required=True, help="REALTIME_INGEST_SECRET configured on the Worker")
    parser.add_argument("--min-interval-seconds", type=float, default=15.0, help="Minimum delay between ingested snapshots")
    parser.add_argument("--reconnect-seconds", type=float, default=5.0, help="Delay before reconnect after an error")
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
