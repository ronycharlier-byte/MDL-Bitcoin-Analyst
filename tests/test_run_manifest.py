from run_manifest import build_run_manifest, stable_input_hash


def test_input_hash_is_order_independent() -> None:
    assert stable_input_hash({"asset": "BTC", "horizon": 30}) == stable_input_hash({"horizon": 30, "asset": "BTC"})


def test_manifest_records_versions_seeds_and_time_bounds() -> None:
    payload = {
        "asset": "BTC",
        "model": "ensemble",
        "archive_id": "archive-1",
        "analysis_id": "archive-1",
        "provenance": {
            "api_version": "2",
            "model_version": "m1",
            "schema_version": "2",
            "report_generated_at_utc": "2026-07-17T12:00:00Z",
            "spot": {
                "value": 100000,
                "source": "bitget",
                "observed_at_utc": "2026-07-17T11:59:00Z",
            },
        },
        "frames": [{"horizon_days": 30, "simulation_count": 5000, "run_id": "run-1", "seed": 42}],
    }
    manifest = build_run_manifest(payload, "/multi-run")
    assert manifest["seeds"] == [42]
    assert manifest["versions"]["model"] == "m1"
    assert manifest["time_bounds"]["spot_observed_at_utc"].endswith("Z")
    assert len(manifest["input_sha256"]) == 64
