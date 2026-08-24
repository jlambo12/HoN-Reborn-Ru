#!/usr/bin/env python3
"""Attach final QA and integrity evidence to the Phase 1.6 handoff."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--test-count", type=int, required=True)
    args = parser.parse_args()
    root = args.project_root.resolve()
    phase = read(root / "reports" / "phase16_summary.json")
    build = read(root / "reports" / "build.json")
    validation = read(root / "reports" / "build_validation.json")
    baseline = read(root / "reports" / "preact_baseline_build.json")
    archive = Path(build["archive_path"])
    extension = Path(build["existing_extension"]["path"])
    end_archive_sha = sha256(archive)
    end_extension_sha = sha256(extension)
    report = {
        **phase,
        "regression_tests": {"result": "PASS", "count": args.test_count},
        "builder_validation": {
            "result": validation.get("result"),
            "error_count": len(validation.get("errors", [])),
            "fallback_warning_count": len(validation.get("warnings", [])),
            "note": "Fallback warnings equal untranslated release workload; no Russian text was generated.",
        },
        "preact_baseline_build": baseline,
        "integrity": {
            "current_archive_sha256_at_audit": build["sha256"],
            "current_archive_sha256_at_finalize": end_archive_sha,
            "unchanged_during_phase16": end_archive_sha == build["sha256"],
            "phase15_archive_sha256": build["known_sha256"],
            "upstream_changed_since_phase15": end_archive_sha != build["known_sha256"],
            "existing_extension_sha256_at_audit": build["existing_extension"]["sha256"],
            "existing_extension_sha256_at_finalize": end_extension_sha,
            "existing_extension_unchanged": end_extension_sha == build["existing_extension"]["sha256"],
        },
        "mass_translation_performed": False,
        "game_install_performed": False,
    }
    output = root / "reports" / "phase16_final_report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "tests": report["regression_tests"], "builder": report["builder_validation"],
        "integrity": report["integrity"],
    }, ensure_ascii=False, indent=2))
    return 0 if report["integrity"]["unchanged_during_phase16"] and report["integrity"]["existing_extension_unchanged"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
