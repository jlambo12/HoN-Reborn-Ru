#!/usr/bin/env python3
"""Prove that every player-facing AST candidate in patches 0.12.4/0.12.5 is handled."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "translation" / "reports" / "patch_editorial_all.jsonl"
TARGETS = ("0124", "0125")
SKIP_RE = re.compile(r"^(?:https?://|/|[\d\s.,:+%()\-/]+)$")
INDIRECTLY_LOCALIZED = {
    ("preact/src/layers/patch-notes-v2/patches/patch0125.tsx", "Gameplay"),
}


def main() -> int:
    covered: dict[str, set[str]] = defaultdict(set)
    duplicate_rows: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for path in sorted((ROOT / "translation" / "human").glob("preact_runtime_batch_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        for row in payload.get("rows", []):
            source = row.get("source_file", "")
            if not any(source.endswith(f"patch{patch}.tsx") for patch in TARGETS):
                continue
            key = (source, row["english"])
            if key in seen:
                duplicate_rows.append({"file": path.name, "source": source, "english": row["english"]})
            seen.add(key)
            covered[source].add(row["english"])

    candidates: dict[str, set[str]] = defaultdict(set)
    for line in REPORT.read_text(encoding="utf-8-sig").splitlines():
        row = json.loads(line)
        source = row["source_file"]
        if any(source.endswith(f"patch{patch}.tsx") for patch in TARGETS) and not SKIP_RE.fullmatch(row["english"]):
            candidates[source].add(row["english"])

    missing = []
    for source, strings in sorted(candidates.items()):
        for english in sorted(strings - covered[source]):
            if (source, english) not in INDIRECTLY_LOCALIZED:
                missing.append({"source": source, "english": english})
    result = {
        "schema_version": 1,
        "result": "PASS" if not missing and not duplicate_rows else "FAIL",
        "patches": {
            patch: {
                "candidates": len(next((v for k, v in candidates.items() if k.endswith(f"patch{patch}.tsx")), set())),
                "covered": len(
                    next((v for k, v in candidates.items() if k.endswith(f"patch{patch}.tsx")), set())
                    & next((v for k, v in covered.items() if k.endswith(f"patch{patch}.tsx")), set())
                ) + sum(1 for source, _ in INDIRECTLY_LOCALIZED if source.endswith(f"patch{patch}.tsx")),
            }
            for patch in TARGETS
        },
        "missing": missing,
        "duplicate_rows": duplicate_rows,
    }
    output = ROOT / "translation" / "reports" / "patch_editorial_coverage.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["result"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
