#!/usr/bin/env python3
"""Fail if the public artifact contains common operational identifiers/secrets."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()
TEXT_SUFFIXES = {".cff", ".csv", ".json", ".jsonl", ".md", ".py", ".txt", ".sha256"}

PATTERNS = {
    "IPv4 address": re.compile(r"(?<![\d.])(?:10|127|169\.254|172\.(?:1[6-9]|2\d|3[01])|192\.168)(?:\.\d{1,3}){2}(?![\d.])"),
    "UUID": re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b"),
    "macOS private path": re.compile(r"/Users/[^/\s]+/"),
    "Linux private path": re.compile(r"/(?:home|root)/[^/\s]+/"),
    "Windows private path": re.compile(r"\b[A-Za-z]:\\(?:Users|Documents and Settings)\\"),
    "private key material": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "credential assignment": re.compile(r"(?i)\b(?:password|passwd|api[_-]?key|access[_-]?token|secret)\s*[:=]\s*[^\s,;]{6,}"),
    "raw campaign identifier": re.compile(r"\b(?:cs|live_qkd|acsac)_[a-z0-9_]*20\d{6,}\b", re.IGNORECASE),
    "known internal account marker": re.compile(r"\b(?:qms|cs517|real_lab_demo_user)\b", re.IGNORECASE),
}


def iter_text_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path == SELF or ".git" in path.parts or ".venv" in path.parts:
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in {"LICENSE", ".gitignore"}:
            files.append(path)
    return sorted(files)


def main() -> None:
    findings = []
    for path in iter_text_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                excerpt = match.group(0)[:80]
                findings.append((str(path.relative_to(ROOT)), line, label, excerpt))
    if findings:
        for path, line, label, excerpt in findings:
            print(f"FAIL {path}:{line}: {label}: {excerpt}")
        raise SystemExit(f"public-artifact audit failed with {len(findings)} finding(s)")
    print(f"public-artifact audit passed across {len(iter_text_files())} text files")


if __name__ == "__main__":
    main()
