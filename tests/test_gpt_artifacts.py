from scripts.validate_openapi import validate_canonical_openapi


def test_canonical_openapi_is_valid_and_governed() -> None:
    validate_canonical_openapi()
