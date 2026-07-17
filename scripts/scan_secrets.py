from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws_access_key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "github_token": re.compile(r"\b(?:gh[opusr]_[A-Za-z0-9]{36,255}|github_pat_[A-Za-z0-9_]{60,255})\b"),
    "slack_token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "stripe_live_key": re.compile(r"\bsk_live_[A-Za-z0-9]{20,}\b"),
    "telegram_bot_token": re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b"),
}


def git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout


def scan_text(label: str, text: str) -> list[str]:
    findings: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for name, pattern in PATTERNS.items():
            if pattern.search(line):
                findings.append(f"{label}:{line_number}:{name}")
    return findings


def current_tree() -> list[str]:
    findings: list[str] = []
    for relative in git("ls-files").splitlines():
        path = ROOT / relative
        try:
            findings.extend(scan_text(relative, path.read_text(encoding="utf-8")))
        except (OSError, UnicodeError):
            continue
    return findings


def reachable_history() -> list[str]:
    findings: list[str] = []
    for commit in git("rev-list", "--all").splitlines():
        patch = git("show", "--format=", "--no-ext-diff", "--unified=0", commit)
        findings.extend(scan_text(f"commit:{commit[:12]}", patch))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan the repository for high-confidence credential patterns.")
    parser.add_argument("--history", action="store_true", help="Also scan patches for all reachable commits.")
    args = parser.parse_args()
    findings = current_tree()
    if args.history:
        findings.extend(reachable_history())
    if findings:
        print("Potential secrets found (values intentionally not printed):")
        print("\n".join(sorted(set(findings))))
        return 1
    print("No high-confidence secret patterns found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
