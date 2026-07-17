from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def repository_files() -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return sorted({line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()})


def classify(path: str) -> tuple[str, str, str, str]:
    lower = path.lower()
    suffix = Path(path).suffix.lower()
    if lower.startswith("gpt_custom_upload_bundle/") or lower.startswith("governance_export/"):
        return (
            "GPT compatibility",
            "legacy_deprecated",
            "GPT governance",
            "Retained for traceability; not a production source.",
        )
    if lower in {
        "gpt_action_openapi.yaml",
        "cloudflare-worker/gpt_action_openapi.cloudflare.yaml",
        "cloudflare-worker/gpt_action_openapi.cloudflare.deployed.json",
    }:
        return "GPT compatibility", "legacy_deprecated", "GPT governance", "Superseded by gpt/actions/openapi.yaml."
    if lower.startswith("external_archive/live_runs/"):
        return (
            "immutable archive",
            "historical_reference",
            "Model governance",
            "Historical evidence; do not rewrite in place.",
        )
    if lower.startswith("tests/") or "/test/" in lower:
        return "test", "current", "Quality", "Automated regression coverage."
    if lower.startswith("contracts/"):
        return "contract", "current_canonical", "Data governance", "Canonical machine-readable contract or fixture."
    if lower.startswith("gpt/actions/") or lower.startswith("gpt/instructions/"):
        return "GPT source", "current_canonical", "GPT governance", "Canonical production source."
    if lower == "api_server.py" or lower == "cloudflare-worker/src/index.ts":
        return (
            "runtime facade",
            "current_migration",
            "Platform",
            "Active compatibility monolith; progressive split planned.",
        )
    if lower.startswith("cloudflare-worker/migrations/"):
        return (
            "database migration",
            "current_append_only",
            "Platform",
            "Apply in numeric order; never edit after production use.",
        )
    if lower.startswith(".github/workflows/"):
        return "CI/operations", "current", "Platform", "Pinned automation; deployment still requires approval."
    if lower.startswith("docs/") or suffix == ".md":
        return "documentation", "current", "Repository maintainers", "Human-readable guidance or historical report."
    if lower.startswith("src/"):
        return "Python domain/adapter", "current", "Quant engineering", "Production Python source."
    if lower.startswith("cloudflare-worker/src/"):
        return "Worker source", "current", "Platform", "Edge runtime source."
    if lower.startswith("scripts/") or lower.startswith("tools/"):
        return "tooling", "current", "Platform", "Operational/development tool; review before external effects."
    if lower.startswith("data/") or lower.startswith("reports/") or lower.startswith("knowledge_base/"):
        return (
            "data/artifact scaffold",
            "reference_or_generated",
            "Model governance",
            "Generated/placeholder policy applies.",
        )
    if suffix in {".yml", ".yaml", ".toml", ".json", ".sql"}:
        return "configuration", "current", "Platform", "Configuration or structured metadata."
    if suffix in {".py", ".ts", ".js", ".ps1"}:
        return "source/tool", "current", "Platform", "Executable source; validate before use."
    return "repository support", "current", "Repository maintainers", "Supporting file."


def domain_classification(path: str, status: str) -> str:
    lower = path.lower()
    if status == "legacy_deprecated":
        return "OBSOLETE_CANDIDATE"
    if status == "historical_reference" or lower.startswith("external_archive/"):
        return "ARCHIVE"
    if lower.startswith(".github/workflows/"):
        return "CI_CD"
    if lower.startswith("gpt/actions/") or "gpt_action" in lower:
        return "GPT_ACTION"
    if lower.startswith("gpt/") or lower.startswith("knowledge_base/"):
        return "GPT_KNOWLEDGE"
    if lower == "api_server.py":
        return "API"
    if lower.startswith("cloudflare-worker/migrations/") or lower.startswith("data/"):
        return "STORAGE"
    if lower.startswith("cloudflare-worker/"):
        return "CLOUDFLARE"
    if lower.startswith("src/"):
        if any(token in lower for token in ("backtest", "walk_forward")):
            return "BACKTEST"
        if any(token in lower for token in ("market_data", "corpus", "features")):
            return "DATA_PIPELINE"
        if any(
            token in lower
            for token in (
                "model",
                "monte_carlo",
                "garch",
                "jump_diffusion",
                "regime",
                "liquidation",
                "risk_metrics",
                "ensemble",
                "simulation",
                "confidence",
                "stress",
            )
        ):
            return "QUANT_MODEL"
        if any(token in lower for token in ("report", "visual")):
            return "REPORTING"
        if any(token in lower for token in ("database", "durable_store")):
            return "STORAGE"
        return "CORE_PYTHON"
    if lower.startswith("reports/"):
        return "REPORTING"
    if lower in {
        "dockerfile",
        "render.yaml",
        "fly.toml",
        "railway.json",
        "cloudrun-service.yaml",
        "deployment.md",
    }:
        return "DEPLOYMENT"
    if lower.startswith("docs/") or lower.endswith(".md") or lower in {"license"}:
        return "DOCUMENTATION"
    if lower.startswith("tests/"):
        return "CORE_PYTHON"
    if lower.startswith("scripts/scan_secrets") or "security" in lower:
        return "SECURITY"
    if lower.startswith("scripts/") or lower.startswith("tools/"):
        return "CORE_PYTHON"
    if lower.startswith(("data/", "reports/")):
        return "GENERATED"
    return "DOCUMENTATION" if Path(path).suffix.lower() == ".md" else "GENERATED"


def inventory_details(
    path: str,
    category: str,
    status: str,
    note: str,
) -> tuple[str, str, str, str, str, str, str, str, str]:
    lower = path.lower()
    suffix = Path(path).suffix.lower()
    domain = domain_classification(path, status)
    file_type = {
        ".py": "Python",
        ".ts": "TypeScript",
        ".js": "JavaScript",
        ".json": "JSON",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".toml": "TOML",
        ".sql": "SQL migration",
        ".md": "Markdown",
        ".ps1": "PowerShell",
    }.get(suffix, category)

    inputs = "Repository/configuration context"
    outputs = "Repository artifact"
    dependencies = "None at runtime"
    tests = "Manual review"
    risk = "Low - maintenance/staleness"
    action = "Maintain and review with related changes."

    if lower == "api_server.py":
        inputs = "HTTP, environment, Bitget/provider data, SQLite archives"
        outputs = "Canonical JSON/PDF/HTML responses; append-only runtime records"
        dependencies = "FastAPI, Pydantic, NumPy/Pandas, quant modules"
        tests = "tests/test_api_security.py; tests/test_contracts.py; pytest smoke"
        risk = "Critical - active compatibility monolith and external boundary"
        action = "Keep adapter-compatible; split by application/domain/adapter in P1."
    elif lower == "cloudflare-worker/src/index.ts":
        inputs = "HTTP/Telegram, environment secrets, D1, bounded external APIs"
        outputs = "Canonical JSON, D1 metadata, Telegram/alert delivery"
        dependencies = "Cloudflare Workers runtime; contracts.ts"
        tests = "cloudflare-worker/test/contracts.test.ts; tsc; ESLint"
        risk = "Critical - active edge/Telegram compatibility monolith"
        action = "Keep fail-closed controls; split routing/auth/storage/Telegram in P1."
    elif lower == "cloudflare-worker/src/contracts.ts":
        inputs = "Legacy or canonical analysis payloads; shared JSON fixture"
        outputs = "Canonical v2 payloads and stable validation issues"
        dependencies = "contracts/analysis.schema.json semantics"
        tests = "Shared fixture and invariant tests in Vitest/Python"
        risk = "High - cross-runtime contract boundary"
        action = "Version changes and test both runtimes before merge."
    elif lower.startswith("src/"):
        inputs = "Typed frames, run parameters, market/fundamental observations"
        outputs = "Quant/data/storage domain values"
        dependencies = "NumPy/Pandas/SciPy or local modules as imported"
        tests = "pytest invariant/property/contract suites; module coverage varies"
        risk = "High" if domain in {"QUANT_MODEL", "DATA_PIPELINE", "STORAGE"} else "Medium"
        action = "Preserve deterministic inputs, explicit status and compatibility adapters."
    elif lower.startswith("tests/") or "/test/" in lower:
        inputs = "Fixtures, generated cases and isolated runtime calls"
        outputs = "Pass/fail evidence and coverage"
        dependencies = "pytest/Hypothesis or Vitest"
        tests = "Executed directly by CI"
        risk = "Medium - false confidence if scope is overstated"
        action = "Extend for each regression and keep external side effects mocked."
    elif lower.startswith("cloudflare-worker/migrations/"):
        inputs = "Prior D1 schema"
        outputs = "Additive D1 schema version"
        dependencies = "Cloudflare D1/SQLite SQL"
        tests = "Syntax/manual staging migration; no production apply in this branch"
        risk = "High - persistent schema change"
        action = "Apply in numeric order in staging; backup and verify rollback path."
    elif lower.startswith(".github/workflows/"):
        inputs = "Git event, repository content, configured secrets"
        outputs = "CI/monitor/archive evidence or review artifact"
        dependencies = "SHA-pinned GitHub Actions"
        tests = "YAML parse plus local reproduction of invoked commands"
        risk = "High - privileged automation/external effects"
        action = "Keep minimal permissions and human deployment approval."
    elif domain in {"GPT_ACTION", "GPT_KNOWLEDGE"}:
        inputs = "Canonical contract, governance policy and API routes"
        outputs = "GPT instruction/action artifact"
        dependencies = "gpt/actions/openapi.yaml and canonical prompt"
        tests = "tests/test_gpt_artifacts.py; scripts/validate_openapi.py"
        risk = "High" if status != "legacy_deprecated" else "Medium - stale compatibility surface"
        action = "Use canonical source; retain legacy only through documented deprecation."
    elif domain == "ARCHIVE":
        inputs = "Historical run evidence"
        outputs = "Immutable reference"
        dependencies = "Original schema/version provenance"
        tests = "Inventory/digest/manual comparability review"
        risk = "Medium - integrity and schema drift"
        action = "Do not rewrite; compare only through version-aware adapters."
    elif category == "configuration" or suffix in {".yaml", ".yml", ".toml", ".json"}:
        inputs = "Environment-neutral configuration values"
        outputs = "Runtime/tool configuration"
        dependencies = "Owning platform/tool"
        tests = "Parser validation and owning tool check"
        risk = "Medium - configuration drift or accidental exposure"
        action = "Keep secrets external and validate before deployment."
    elif lower.startswith("docs/") or suffix == ".md":
        inputs = "Current code, contracts and validation evidence"
        outputs = "Human guidance/governance record"
        dependencies = "Referenced repository paths"
        tests = "Manual accuracy/link review; inventory regeneration"
        risk = "Low - misleading documentation if stale"
        action = "Update in the same change as behavior."

    if status == "legacy_deprecated":
        risk = "Medium - accidental reuse of a stale interface"
        action = "Retain for traceability; exclude from canonical production configuration pending deprecation."
    return domain, file_type, note, inputs, outputs, dependencies, tests, risk, action


def escape_cell(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def main() -> None:
    rows = []
    counts: dict[str, int] = {}
    for path in repository_files():
        category, status, owner, note = classify(path)
        counts[status] = counts.get(status, 0) + 1
        domain, file_type, role, inputs, outputs, dependencies, tests, risk, action = inventory_details(
            path,
            category,
            status,
            note,
        )
        values = [
            f"`{path}`",
            domain,
            file_type,
            role,
            inputs,
            outputs,
            dependencies,
            tests,
            risk,
            action,
            status,
            owner,
        ]
        rows.append("| " + " | ".join(escape_cell(value) for value in values) + " |")
    summary = ", ".join(f"{key}: {value}" for key, value in sorted(counts.items()))
    output = "\n".join(
        [
            "# Repository inventory",
            "",
            "Generated by `scripts/generate_repository_inventory.py`. Regenerate after material file changes.",
            "",
            f"Files inventoried: **{len(rows)}**. Classification counts: {summary}.",
            "",
            "`legacy_deprecated` means retained for compatibility/traceability and excluded from canonical production configuration. No historical archive is silently deleted.",
            "",
            "| Path | Classification | Type | Role | Inputs | Outputs | Dependencies | Tests | Risk | Proposed action | Status | Owner |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|",
            *rows,
            "",
        ]
    )
    destination = ROOT / "docs" / "REPOSITORY_INVENTORY.md"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(output, encoding="utf-8")
    print(f"Wrote {destination.relative_to(ROOT)} with {len(rows)} files.")


if __name__ == "__main__":
    main()
