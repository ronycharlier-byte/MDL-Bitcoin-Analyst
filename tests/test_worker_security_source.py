from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER_SOURCE = (ROOT / "cloudflare-worker" / "src" / "index.ts").read_text(encoding="utf-8")


def test_worker_contains_no_private_exchange_execution_credentials_or_order_function() -> None:
    forbidden = ["BITGET_API_SECRET", "BITGET_API_PASSPHRASE", "placeBitgetSpotOrder", "/api/v2/spot/trade/place-order"]
    assert all(token not in WORKER_SOURCE for token in forbidden)


def test_worker_requires_telegram_secret_and_disables_live_approval() -> None:
    assert "x-telegram-bot-api-secret-token" in WORKER_SOURCE.lower()
    assert "TELEGRAM_WEBHOOK_SECRET" in WORKER_SOURCE
    assert "stableError(" in WORKER_SOURCE
    assert '"EXECUTION_FORBIDDEN"' in WORKER_SOURCE


def test_worker_read_routes_do_not_hide_known_mutations() -> None:
    mutation_routes = {
        "/ops/monitor",
        "/model-alerts/refresh",
        "/trading/paper-report/refresh",
        "/strategies/performance/refresh",
    }
    for route in mutation_routes:
        assert f'url.pathname === "{route}" && request.method === "GET"' not in WORKER_SOURCE
        assert f'url.pathname === "{route}" && request.method === "POST"' in WORKER_SOURCE

    assert 'reason: "GET status endpoints are strictly cache-only"' in WORKER_SOURCE
    assert 'reason: "cache_only_read"' in WORKER_SOURCE
    assert "no_realtime_refresh: true" in WORKER_SOURCE
    assert "no_persist: true" in WORKER_SOURCE


def test_worker_external_fetches_are_centralized_behind_timeout_helper() -> None:
    assert WORKER_SOURCE.count("await fetch(") == 1
    assert "async function fetchWithTimeout" in WORKER_SOURCE
