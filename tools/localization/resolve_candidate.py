#!/usr/bin/env python3
"""Show current text and all existing candidates for one localization key."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def load_row(path: Path, predicate) -> dict[str, Any] | None:
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if predicate(row):
                    return row
    return None


def resolve(logical_key: str, root: Path = ROOT) -> dict[str, Any]:
    if ":" not in logical_key:
        raise KeyError("Use namespace:key, for example interface:Shop_Search_Shop")
    domain, key = logical_key.split(":", 1)
    source = load_row(root / "translation" / "source_index.jsonl", lambda row: row["logical_key"] == logical_key)
    candidate = load_row(root / "translation" / "candidate_index.jsonl", lambda row: row["logical_key"] == logical_key)
    comparison = load_row(
        root / "translation" / "reports" / "pre_d_key_comparison.jsonl",
        lambda row: row["domain"] == domain and row["key"] == key,
    )
    approved = load_row(
        root / "translation" / "translation_memory.jsonl",
        lambda row: row.get("logical_key") == logical_key and row.get("approval_status") == "APPROVED",
    )
    if source is None or candidate is None or comparison is None:
        raise KeyError(f"Unknown current localization key: {logical_key}")
    if hashlib.sha256(source["current_source_value"].encode("utf-8")).hexdigest() != source["current_source_hash"]:
        raise RuntimeError(f"Source index hash mismatch: {logical_key}")
    values = {
        "donor": comparison.get("donor_value"),
        "pass_c": comparison.get("pass_c_value"),
        "approved": approved.get("approved_ru") if approved else None,
    }
    for origin in ("donor", "pass_c"):
        value = values[origin]
        expected = candidate["candidates"][origin]["value_hash"]
        if value is not None and hashlib.sha256(value.encode("utf-8")).hexdigest() != expected:
            raise RuntimeError(f"{origin} candidate hash mismatch: {logical_key}")
    return {
        "key": logical_key,
        "current_source": source["current_source_value"],
        "current_source_hash": source["current_source_hash"],
        "category": source["category"],
        "entity": source["entity"],
        "candidates": values,
        "candidate_metadata": candidate["candidates"],
        "recommended_status": candidate["recommended_status"],
        "flags": candidate["flags"],
        "policy_conflicts": candidate["policy_conflicts"],
        "review_queues": candidate["review_queues"],
        "priority_score": candidate["priority_score"],
        "warning": "Candidate resolution is not approval and does not prove semantic freshness.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("key", help="namespace:key")
    args = parser.parse_args()
    try:
        result = resolve(args.key)
    except (KeyError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
