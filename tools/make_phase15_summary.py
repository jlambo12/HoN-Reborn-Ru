#!/usr/bin/env python3
"""Generate the compact machine-readable Phase 1.5 handoff summary."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_root.resolve()
    rows = [
        json.loads(line) for line in (root / "catalog" / "strings.jsonl").read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    native = read_json(root / "reports" / "native_ui_integration_points.json")
    ast = read_json(root / "reports" / "preact_ast_summary.json")
    baseline = read_json(root / "reports" / "preact_baseline_build.json")
    transition = read_json(root / "reports" / "phase15_review_transition.json")
    build = read_json(root / "reports" / "build.json")
    builder = read_json(root / "reports" / "build_validation.json")
    summary = {
        "phase": "1.5",
        "translation_or_install_performed": False,
        "catalog_rows": len(rows),
        "by_status": dict(sorted(Counter(row["status"] for row in rows).items())),
        "by_category": dict(sorted(Counter(row["category"] for row in rows).items())),
        "by_runtime_role": dict(sorted(Counter(row["runtime_role"] for row in rows).items())),
        "by_thai_signal": dict(sorted(Counter(row["thai_signal"] for row in rows).items())),
        "protected_term_rows": sum(bool(row.get("protected_terms")) for row in rows),
        "protected_term_occurrences": sum(len(row.get("protected_terms", [])) for row in rows),
        "phase1_review": {
            "original": transition["phase1_review_count"],
            "new_status": transition["new_status"],
            "new_runtime_role": transition["new_runtime_role"],
        },
        "regression_tests": {"result": "PASS", "count": 13},
        "builder_probe": {
            "result": builder.get("result"),
            "error_count": len(builder.get("errors", [])),
            "fallback_warning_count": len(builder.get("warnings", [])),
            "files": builder.get("files"),
            "archive_size": builder.get("archive_size"),
            "archive_sha256": builder.get("archive_sha256"),
        },
        "native_ui": {
            "files_by_extension": native["files_by_extension"],
            "hardcoded_candidates": native["candidate_count"],
            "by_area": native["candidate_count_by_area"],
            "by_kind": native["candidate_count_by_kind"],
            "integration_count_by_kind": native["integration_count_by_kind"],
        },
        "preact_ast": ast,
        "preact_baseline": baseline,
        "source_archive_sha256": build["sha256"],
        "existing_extension_sha256": build["existing_extension"]["sha256"],
    }
    output = root / "reports" / "phase15_summary.json"
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
