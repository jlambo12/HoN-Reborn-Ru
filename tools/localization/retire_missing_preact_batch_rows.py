#!/usr/bin/env python3
"""Mark reviewed legacy Preact rows retired when CURRENT removed their source."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "catalog" / "preact_ui.jsonl"
BATCH_DIR = ROOT / "translation" / "human"


def main() -> int:
    rows = [json.loads(line) for line in CATALOG.read_text(encoding="utf-8-sig").splitlines() if line]
    ids = {row["id"] for row in rows}
    retired = 0
    for path in sorted(BATCH_DIR.glob("preact_batch_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        changed = False
        for item in payload.get("rows", []):
            row_id = item.get("id")
            if row_id:
                present = row_id in ids
            else:
                prefix = item.get("source_prefix", "")
                english = item.get("english")
                present = any(
                    row.get("source_file", "").startswith(prefix) and row.get("english") == english
                    for row in rows
                )
            if not present and item.get("retired") is not True:
                item["retired"] = True
                changed = True
                retired += 1
        if changed:
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"result": "PASS", "newly_retired": retired}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
