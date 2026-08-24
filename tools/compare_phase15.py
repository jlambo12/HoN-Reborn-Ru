#!/usr/bin/env python3
"""Compare the accepted phase-1 review catalog with the current catalog."""

from __future__ import annotations

import argparse
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


def load_jsonl_text(text: str) -> list[dict]:
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--phase1-bundle", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_root.resolve()
    with zipfile.ZipFile(args.phase1_bundle.resolve()) as zf:
        old_rows = load_jsonl_text(zf.read("catalog/strings.jsonl").decode("utf-8-sig"))
    new_rows = load_jsonl_text((root / "catalog" / "strings.jsonl").read_text(encoding="utf-8-sig"))
    old_by_id = {row["id"]: row for row in old_rows}
    new_by_id = {row["id"]: row for row in new_rows}

    phase1_review = [row for row in old_rows if row.get("status") == "REVIEW"]
    status = Counter()
    category = Counter()
    runtime_role = Counter()
    transitions = Counter()
    examples: dict[str, list[dict]] = defaultdict(list)
    missing = []
    for old in phase1_review:
        new = new_by_id.get(old["id"])
        if not new:
            missing.append(old["id"])
            continue
        new_status = new.get("status", "UNKNOWN")
        status[new_status] += 1
        category[new.get("category", "UNKNOWN")] += 1
        runtime_role[new.get("runtime_role", "UNKNOWN")] += 1
        key = f'{old.get("category", "UNKNOWN")} -> {new.get("category", "UNKNOWN")} / {new_status}'
        transitions[key] += 1
        if len(examples[new_status]) < 12:
            examples[new_status].append({
                "id": old["id"], "key": old.get("key"),
                "old_category": old.get("category"),
                "new_category": new.get("category"),
                "runtime_role": new.get("runtime_role"),
            })

    report = {
        "phase1_bundle": str(args.phase1_bundle.resolve()),
        "phase1_review_count": len(phase1_review),
        "resolved_count": sum(status.values()),
        "missing_from_current": missing,
        "new_status": dict(sorted(status.items())),
        "new_category": dict(sorted(category.items())),
        "new_runtime_role": dict(sorted(runtime_role.items())),
        "top_transitions": dict(transitions.most_common(40)),
        "examples_by_new_status": dict(sorted(examples.items())),
        "catalog_identity": {
            "phase1_rows": len(old_by_id), "current_rows": len(new_by_id),
            "shared_ids": len(old_by_id.keys() & new_by_id.keys()),
        },
    }
    output = root / "reports" / "phase15_review_transition.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
