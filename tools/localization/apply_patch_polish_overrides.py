#!/usr/bin/env python3
"""Apply a manually reviewed English-to-Russian polish map to an editorial batch."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
JOBS = (
    ("preact_runtime_batch_012_patch_0124_complete.json", "patch_0124_polish_overrides.json"),
    ("preact_runtime_batch_011_patch_0125_remaining.json", "patch_0125_polish_overrides.json"),
)


def main() -> int:
    total = 0
    for target_name, override_name in JOBS:
        target = ROOT / "translation" / "human" / target_name
        override_path = ROOT / "translation" / "human" / override_name
        if not override_path.is_file():
            continue
        payload = json.loads(target.read_text(encoding="utf-8-sig"))
        overrides = json.loads(override_path.read_text(encoding="utf-8-sig"))
        rows = {row["english"]: row for row in payload["rows"]}
        missing = sorted(set(overrides) - set(rows))
        if missing:
            raise SystemExit(f"Unknown polish keys in {override_name}: {missing}")
        for english, russian in overrides.items():
            rows[english]["russian"] = russian
            rows[english]["decision"] = "MANUAL_POLISH"
        payload["reviewed_by"] = "Machine draft with manual terminology and screenshot polish 2026-08-24"
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        total += len(overrides)
    print(json.dumps({"result": "PASS", "overrides": total}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
