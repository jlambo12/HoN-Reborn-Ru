#!/usr/bin/env python3
"""Create the cumulative CURRENT Preact scope from non-empty Russian rows."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "catalog" / "preact_ui.jsonl"
OUTPUT = ROOT / "translation" / "human" / "preact_scope.json"


def main() -> int:
    rows = [json.loads(line) for line in CATALOG.read_text(encoding="utf-8-sig").splitlines() if line]
    eligible = [row for row in rows if row.get("russian") and row.get("status") == "TRANSLATE"]
    # The current release overlay compiles the embedded `preact` application.
    # `preact-remote` is a separate project with its own build/deployment path and
    # must not be passed to prepare_phase2a_overrides as though it lived below
    # the embedded application's source root.
    selected = sorted(row["id"] for row in eligible if row.get("source_file", "").startswith("preact/"))
    remote = sorted(row["id"] for row in eligible if row.get("source_file", "").startswith("preact-remote/"))
    payload = {
        "schema_version": 1,
        "scope": "Cumulative CURRENT Preact Russian localization",
        "selection": {"preact": selected},
        "counts": {"preact": len(selected), "preact_remote_deferred": len(remote)},
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(payload["counts"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
