from __future__ import annotations

import argparse
import asyncio
import json
import signal
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import websockets


BITGET_PUBLIC_WS = "wss://ws.bitget.com/v3/ws/public"
PARIS = ZoneInfo("Europe/Paris")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def stamp() -> dict[str, str]:
    now = utc_now()
    return {
        "timestamp_utc": now.isoformat(),
        "timestamp_paris": now.astimezone(PARIS).isoformat(),
    }


def liquidation_subscribe_message() -> str:
    return json.dumps({
        "op": "subscribe",
        "args": [
            {
                "instType": "usdt-futures",
                "topic": "liquidation",
            }
        ],
    })


async def write_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")


async def collect(asset: str, out: Path, stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            async with websockets.connect(BITGET_PUBLIC_WS, ping_interval=20, ping_timeout=20) as ws:
                await ws.send(liquidation_subscribe_message())
                await write_jsonl(out, {
                    "event": "connected",
                    "asset": asset,
                    "source": "bitget_public_ws_liquidation",
                    "status": "real",
                    **stamp(),
                })
                while not stop.is_set():
                    raw = await asyncio.wait_for(ws.recv(), timeout=60)
                    payload = {
                        "event": "message",
                        "asset": asset,
                        "source": "bitget_public_ws_liquidation",
                        "status": "real",
                        "raw": json.loads(raw) if isinstance(raw, str) and raw[:1] in "{[" else raw,
                        **stamp(),
                    }
                    await write_jsonl(out, payload)
        except asyncio.TimeoutError:
            await write_jsonl(out, {
                "event": "heartbeat_timeout",
                "asset": asset,
                "source": "bitget_public_ws_liquidation",
                "status": "stale",
                **stamp(),
            })
        except Exception as exc:
            await write_jsonl(out, {
                "event": "collector_error",
                "asset": asset,
                "source": "bitget_public_ws_liquidation",
                "status": "absent",
                "error": str(exc),
                **stamp(),
            })
            await asyncio.sleep(10)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Bitget WebSocket collector for Quant BTC Model.")
    parser.add_argument("--asset", default="BTC")
    parser.add_argument("--out", default="../../data/raw/bitget_ws_latest.jsonl")
    args = parser.parse_args()

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:
            pass

    await collect(args.asset.upper(), Path(args.out), stop)


if __name__ == "__main__":
    asyncio.run(main())
