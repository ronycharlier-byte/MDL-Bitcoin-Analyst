from __future__ import annotations

from pathlib import Path

import yaml
from openapi_spec_validator import validate

ROOT = Path(__file__).resolve().parents[1]
OPENAPI_PATH = ROOT / "gpt" / "actions" / "openapi.yaml"
STATE_CHANGING_GETS = {
    "/analyze",
    "/analyze-deep",
    "/run",
    "/multi-run",
    "/trading/approve",
    "/telegram/setup-webhook",
}


def validate_canonical_openapi() -> None:
    document = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))
    validate(document)
    operation_ids: list[str] = []
    for path, path_item in document["paths"].items():
        assert not (path in STATE_CHANGING_GETS and "get" in path_item), f"State-changing GET forbidden: {path}"
        for method in {"get", "post", "put", "patch", "delete"} & set(path_item):
            operation_id = path_item[method].get("operationId")
            assert operation_id, f"Missing operationId: {method.upper()} {path}"
            operation_ids.append(operation_id)
    assert len(operation_ids) == len(set(operation_ids)), "operationId values must be unique"
    assert all(server["url"].startswith("https://") for server in document["servers"])


if __name__ == "__main__":
    validate_canonical_openapi()
    print(f"Valid canonical OpenAPI: {OPENAPI_PATH.relative_to(ROOT)}")
