from __future__ import annotations

import socket

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import api_server

client = TestClient(api_server.app)


def valid_run_request() -> dict:
    return {
        "asset": "BTC",
        "horizon": 30,
        "simulations": 100,
        "model": "monte_carlo",
        "seed": 42,
    }


def test_liveness_is_public_but_protected_route_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("QUANT_API_KEY", raising=False)
    assert client.get("/live").status_code == 200
    response = client.post("/run", json=valid_run_request())
    assert response.status_code == 503
    assert response.json()["error_code"] == "AUTHENTICATION_REQUIRED"


def test_api_docs_are_not_exposed_by_default() -> None:
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_request_id_is_stable_sanitized_and_returned() -> None:
    supplied = client.get("/live", headers={"x-request-id": "test-request-123"})
    assert supplied.headers["x-request-id"] == "test-request-123"
    rejected = client.get("/live", headers={"x-request-id": "not safe\r\nheader"})
    assert rejected.headers["x-request-id"] != "not safe\r\nheader"


def test_oversized_request_is_rejected_before_processing() -> None:
    response = client.post("/run", content=b"{" + b'"padding":"' + b"x" * 70_000 + b'"}')
    assert response.status_code == 413


def test_webhook_ssrf_policy_rejects_non_allowlisted_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALERT_WEBHOOK_ALLOWED_HOSTS", "allowed.example")
    with pytest.raises(HTTPException) as exc_info:
        api_server._validate_webhook_target("https://not-allowed.example/hook")
    assert exc_info.value.status_code == 400


def test_webhook_ssrf_policy_rejects_private_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALERT_WEBHOOK_ALLOWED_HOSTS", "allowed.example")
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))],
    )
    with pytest.raises(HTTPException) as exc_info:
        api_server._validate_webhook_target("https://allowed.example/hook")
    assert exc_info.value.status_code == 400
