#!/usr/bin/env python3
"""Restore Pass C catalog values while preserving aborted D1 evidence files."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    catalog_path = ROOT / "catalog" / "strings.jsonl"
    changes_path = ROOT / "reports" / "pass_d1_changes.jsonl"
    if not changes_path.exists():
        raise SystemExit("Aborted D1 change journal is missing; refusing an inferred rollback")

    original_bytes = catalog_path.read_bytes()
    rows = read_jsonl(catalog_path)
    changes = {row["id"]: row for row in read_jsonl(changes_path)}
    restored = 0
    metadata_restored = 0
    for row in rows:
        row_id = row["id"]
        if row_id in changes:
            expected_d1 = changes[row_id]["new"]
            if row.get("russian", "") not in {expected_d1, changes[row_id]["old"]}:
                raise SystemExit(f"Catalog diverged after aborted D1; refusing rollback for {row_id}")
            if row.get("russian", "") != changes[row_id]["old"]:
                row["russian"] = changes[row_id]["old"]
                restored += 1
            if row_id.startswith("entities:Item_") and "_FRAME_effect" in row_id and row.get("english", "").startswith("\\n") and changes[row_id]["old"] == "":
                row.update({
                    "status": "REVIEW",
                    "runtime_role": "RESOURCE_PATH",
                    "category": "resource_path",
                    "context": "Entity value previously classified as a structural/resource candidate; requires explicit runtime review",
                    "notes": "",
                })
                metadata_restored += 1
            elif row_id in {"entities:TargetScheme_self", "entities:TargetScheme_enemy_units"}:
                row.update({"status": "REVIEW", "category": "entity_review", "notes": ""})
                metadata_restored += 1
            elif row_id in {"game_messages:perplexed_bonus", "game_messages:perplexed_immunity_bonus"}:
                row.update({"status": "TRANSLATE", "runtime_role": "DISPLAY_TEXT", "category": "game_system_message", "notes": ""})
                metadata_restored += 1
        if row_id == "interface:tutorial_slide_top_center_creeps_denied":
            if "Denied" not in row.get("protected_terms", []):
                row["protected_terms"] = [*row.get("protected_terms", []), "Denied"]
                row["locked_spans"] = [{
                    "canonical_text": "Denied", "type": "ANNOUNCER_EVENT",
                    "source_start": 7, "source_end": 13, "visible_start": 7, "visible_end": 13,
                    "case_policy": "EXACT", "markup_prefix": "", "markup_suffix": "",
                }]
                metadata_restored += 1
        if row.get("translation_phase") == "Pass D1 semantic cleanup":
            row.pop("translation_phase", None)

    encoded = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows).encode("utf-8")
    catalog_path.write_bytes(encoded)
    report = {
        "result": "PASS",
        "purpose": "Quarantine aborted Pass D1 from the active catalog; D1 evidence files retained",
        "catalog": str(catalog_path),
        "before_sha256": digest(original_bytes),
        "after_sha256": digest(encoded),
        "russian_values_restored": restored,
        "metadata_records_restored": metadata_restored,
        "evidence": str(changes_path),
        "installed_extension_modified": False,
        "upstream_archive_modified": False,
    }
    out = ROOT / "translation" / "reports" / "aborted_d1_quarantine.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
