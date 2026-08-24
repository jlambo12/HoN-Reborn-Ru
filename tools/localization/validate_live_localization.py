#!/usr/bin/env python3
"""Fast, archive-free validation for the live localization work queue."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from tools.localization.build_live_gameplay_queue import (
        ROOT,
        priority_tier,
        sha256_bytes,
        structural_signature,
    )
except ModuleNotFoundError:  # Direct invocation by file path.
    from build_live_gameplay_queue import (  # type: ignore[no-redef]
        ROOT,
        priority_tier,
        sha256_bytes,
        structural_signature,
    )


DEFAULT_QUEUE = ROOT / "translation" / "priority" / "live_gameplay_queue.jsonl"
DEFAULT_REPORT = ROOT / "translation" / "reports" / "live_quick_validation.json"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line]


def validate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    counts = Counter(row["logical_key"] for row in rows)
    for key, count in counts.items():
        if count != 1:
            errors.append({"code": "DUPLICATE_KEY", "key": key, "count": count})
    for row in rows:
        key = row["logical_key"]
        expected_hash = sha256_bytes(row["english"].encode("utf-8"))
        if row.get("english_hash") != expected_hash:
            errors.append({"code": "ENGLISH_HASH_MISMATCH", "key": key})
        expected_tier = priority_tier(row["status"], row["scope"])
        if row.get("priority_tier") != expected_tier:
            errors.append({"code": "PRIORITY_MISMATCH", "key": key, "expected": expected_tier})
        ru = row.get("existing_ru", "")
        if row["status"] == "DONE" and not ru:
            errors.append({"code": "DONE_WITHOUT_RUSSIAN", "key": key})
        if ru and structural_signature(row["english"]) != structural_signature(ru):
            errors.append({"code": "STRUCTURAL_TOKEN_MISMATCH", "key": key})
        if ru:
            missing = [span for span in row.get("protected_spans", []) if span not in ru]
            if missing:
                errors.append({"code": "PROTECTED_SPAN_LOST", "key": key, "spans": missing})
    return errors


def validate_batch(path: Path, queue_by_key: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in payload.get("entries", []):
        ru = entry.get("ru", "")
        for key in entry.get("keys", []):
            if key in seen:
                errors.append({"code": "DUPLICATE_BATCH_KEY", "key": key})
            seen.add(key)
            source = queue_by_key.get(key)
            if source is None:
                errors.append({"code": "KEY_NOT_IN_LIVE_SCOPE", "key": key})
                continue
            approved_hash = entry.get("english_hash")
            if approved_hash and approved_hash != source["english_hash"]:
                errors.append({"code": "BATCH_ENGLISH_HASH_MISMATCH", "key": key})
            if not ru:
                errors.append({"code": "EMPTY_RUSSIAN", "key": key})
            if structural_signature(source["english"]) != structural_signature(ru):
                errors.append({"code": "STRUCTURAL_TOKEN_MISMATCH", "key": key})
            missing = [span for span in source.get("protected_spans", []) if span not in ru]
            if missing:
                errors.append({"code": "PROTECTED_SPAN_LOST", "key": key, "spans": missing})
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--batch", type=Path)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--allow-review-blockers", action="store_true",
        help="Do not fail only because already classified P0 rows remain",
    )
    args = parser.parse_args()

    rows = load_jsonl(args.queue)
    queue_by_key = {row["logical_key"]: row for row in rows}
    errors = validate_rows(rows)
    if args.batch:
        errors.extend(validate_batch(args.batch, queue_by_key))
    if args.allow_review_blockers:
        p0 = {row["logical_key"] for row in rows if row["priority_tier"] == "P0"}
        errors = [error for error in errors if error.get("key") not in p0]
    report = {
        "schema_version": 1,
        "result": "PASS" if not errors else "FAIL",
        "queue_rows": len(rows),
        "priority_counts": dict(Counter(row["priority_tier"] for row in rows)),
        "status_counts": dict(Counter(row["status"] for row in rows)),
        "batch": str(args.batch) if args.batch else None,
        "errors": errors,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
