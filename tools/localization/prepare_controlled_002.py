#!/usr/bin/env python3
"""Prepare Controlled Batch 002 candidates and source-resolution evidence.

This script is intentionally read-only with respect to Pass C and the upstream
archive.  It creates reports/candidates only; it does not build or install a mod.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PASS_C = ROOT / "build" / "pass-c" / "resources0.jz"
EXPECTED_PASS_C_SHA = "3d5ee66b9507c342d92b0be886d2918ea959e9beffb2126e6a7f77604142e301"
EXPECTED_UPSTREAM_SHA = "a518f760c7bdebcfb2f9258dbfcfe7e2bf81881938e4653b0b1c725e04099762"
BATCH_ID = "CONTROLLED_002_TERMINOLOGY"
BAD_STAFF_ALIAS = "Персонал Мастера"
STAFF_CANONICAL = "Staff of the Master"

BATCH_PATH = ROOT / "translation" / "batches" / "controlled_002_terminology.jsonl"
RESOLUTION_PATH = ROOT / "translation" / "reports" / "controlled_002_source_resolution.json"
VALIDATION_PATH = ROOT / "translation" / "reports" / "controlled_002_validation.json"
REPORT_PATH = ROOT / "translation" / "reports" / "CONTROLLED_002_CANDIDATE_REPORT.md"

ROLE_CANDIDATES = {
    "game_messages:filter_carry": "Керри",
    "interface:player_role_carry": "Керри",
    "interface:player_role_mid": "Мид",
    "interface:player_role_softsupport": "Поддержка",
    "interface:player_role_hardsupport": "Основная поддержка",
}
ROLE_COMPLIANCE = {"interface:player_role_offlane": "Оффлейн"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line]


def parse_table(data: bytes) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in data.decode("utf-8-sig").splitlines():
        if "\t" not in line or line.lstrip().startswith("//"):
            continue
        key, value = line.split("\t", 1)
        result[key] = value
    return result


def candidate_row(
    ordinal: int,
    source: dict[str, Any],
    baseline: str,
    proposed: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "batch_id": BATCH_ID,
        "ordinal": ordinal,
        "logical_key": source["logical_key"],
        "domain": source["domain"],
        "key": source["key"],
        "category": source["category"],
        "runtime_role": source["runtime_role"],
        "context": source["context"],
        "current_source": source["current_source_value"],
        "current_source_hash": source["current_source_hash"],
        "pass_c_baseline": baseline,
        "pass_c_baseline_hash": hash_text(baseline),
        "proposed_ru": proposed,
        "reason": reason,
        "status": "HUMAN_APPROVED",
        "approval_state": "HUMAN_APPROVED_PENDING_RUNTIME",
        "human_review_state": "APPROVED",
        "applied": False,
        "runtime_verified": False,
        "validation": {
            "source_hash_match": hash_text(source["current_source_value"]) == source["current_source_hash"],
            "baseline_changed": baseline != proposed,
            "placeholders_unchanged": sorted(re.findall(r"\{[^{}]+\}", baseline)) == sorted(re.findall(r"\{[^{}]+\}", proposed)),
            "hon_color_codes_unchanged": sorted(re.findall(r"\^(?:[!*]|[A-Za-z]|\d{3})", baseline)) == sorted(re.findall(r"\^(?:[!*]|[A-Za-z]|\d{3})", proposed)),
            "numbers_unchanged": re.findall(r"\d+(?:\.\d+)?", baseline) == re.findall(r"\d+(?:\.\d+)?", proposed),
        },
    }


def main() -> int:
    if sys.version_info < (3, 14):
        raise SystemExit("Python 3.14+ is required to read ZIP Zstandard members")
    pass_c_sha = sha256_file(PASS_C)
    if pass_c_sha != EXPECTED_PASS_C_SHA:
        raise SystemExit(f"Pass C baseline mismatch: {pass_c_sha}")

    sources = {row["logical_key"]: row for row in load_jsonl(ROOT / "translation" / "source_index.jsonl")}
    if {row["source_identity"] for row in sources.values()} != {f"upstream@{EXPECTED_UPSTREAM_SHA}"}:
        raise SystemExit("Source index is not pinned exclusively to accepted upstream")

    with zipfile.ZipFile(PASS_C) as archive:
        if archive.testzip() is not None:
            raise SystemExit("Pass C CRC validation failed")
        tables = {
            "interface": parse_table(archive.read("stringtables/interface_ru.str")),
            "game_messages": parse_table(archive.read("stringtables/game_messages_ru.str")),
            "entities": parse_table(archive.read("stringtables/entities_ru.str")),
        }

    candidates: list[dict[str, Any]] = []
    ordinal = 1
    for logical_key, proposed in ROLE_CANDIDATES.items():
        source = sources[logical_key]
        baseline = tables[source["domain"]][source["key"]]
        candidates.append(candidate_row(ordinal, source, baseline, proposed, "user_directed_role_terminology"))
        ordinal += 1

    staff_inventory: dict[str, list[str]] = {}
    for alias in (BAD_STAFF_ALIAS, "Посох Мастера", "Стафф", "Аганим", "Аганимский скипетр"):
        staff_inventory[alias] = sorted(key for key, value in tables["entities"].items() if alias.casefold() in value.casefold())

    for key in staff_inventory[BAD_STAFF_ALIAS]:
        logical_key = f"entities:{key}"
        source = sources[logical_key]
        baseline = tables["entities"][key]
        proposed = re.sub(re.escape(BAD_STAFF_ALIAS), STAFF_CANONICAL, baseline, flags=re.IGNORECASE)
        if STAFF_CANONICAL.casefold() not in source["current_source_value"].casefold():
            raise SystemExit(f"Cannot prove Staff source span for {logical_key}")
        candidates.append(candidate_row(ordinal, source, baseline, proposed, "restore_exact_keep_en_span"))
        ordinal += 1

    errors: list[dict[str, Any]] = []
    if len(candidates) != 33 or len({row["logical_key"] for row in candidates}) != 33:
        errors.append({"code": "UNEXPECTED_BATCH_SIZE", "count": len(candidates)})
    for row in candidates:
        if not all(row["validation"].values()):
            errors.append({"code": "ROW_VALIDATION_FAILED", "key": row["logical_key"], "validation": row["validation"]})
        if row["logical_key"] in ROLE_CANDIDATES and row["proposed_ru"].casefold() in {"нести", "переносить"}:
            errors.append({"code": "FORBIDDEN_CARRY_LITERAL", "key": row["logical_key"]})
        if BAD_STAFF_ALIAS.casefold() in row["proposed_ru"].casefold():
            errors.append({"code": "BAD_STAFF_ALIAS_REMAINS", "key": row["logical_key"]})

    offlane_source = sources["interface:player_role_offlane"]
    offlane_value = tables["interface"][offlane_source["key"]]
    if offlane_value != ROLE_COMPLIANCE["interface:player_role_offlane"]:
        errors.append({"code": "OFFLANE_NOT_COMPLIANT", "value": offlane_value})

    mixed_leading_enter = [
        {"logical_key": f"interface:{key}", "pass_c_value": value, "classification": "TRANSLATE_LATER_LIVE_STRINGTABLE"}
        for key, value in sorted(tables["interface"].items())
        if re.search(r"[А-Яа-яЁё]", value) and re.match(r"Enter\b", value)
    ]
    mixed_interface_count = sum(
        1 for value in tables["interface"].values()
        if re.search(r"[А-Яа-яЁё]", value) and re.search(r"[A-Za-z]", value)
    )

    resolution = {
        "schema_version": 1,
        "batch_id": BATCH_ID,
        "baseline": {"path": str(PASS_C), "sha256": pass_c_sha, "unchanged": True},
        "upstream": {"sha256": EXPECTED_UPSTREAM_SHA, "unchanged": True},
        "records": [
            {
                "visible_text": "Gameplay role labels (Preact)",
                "classification": "PREACT_LOCAL_ENUM_LABELS",
                "source": "preact/src/types/global.ts:23-28",
                "proposed_mapping": {
                    "Carry": "Керри",
                    "Mid": "Мид",
                    "Offlane": "Оффлейн",
                    "Soft Support": "Поддержка",
                    "Hard Support": "Основная поддержка",
                },
                "review": ["Solo Offlane is present in the same map but was not assigned a Russian term in this task."],
                "candidate_action": "ADD_CODE_LITERAL_OR_I18N_OVERRIDE_ONLY_AFTER_HUMAN_REVIEW",
            },
            {
                "visible_text": "Call Vote",
                "classification": "REVIEW_SOURCE_UNRESOLVED",
                "evidence": [
                    "Exact text occurs only in XML comment ui/hd_ui/templates/menu_vote_templates.package:179.",
                    "The dialog header is a runtime parameter {header}; no instantiation or exact player-facing literal exists in extracted resources.",
                    "interface:game_menu_vote resolves Vote/Голосовать, but is not proof that it controls the observed Call Vote header.",
                ],
                "candidate_action": "NONE_UNTIL_RUNTIME_PRODUCER_IS_TRACED",
            },
            {
                "visible_text": "MISSING",
                "classification": "NATIVE_HARDCODED_LITERAL",
                "source": "ui/hd_ui/templates/heroframe_templates.package:291",
                "evidence": ["label content is the literal MISSING, not a stringtable lookup"],
                "candidate_action": "LATER_NATIVE_OVERRIDE_OR_NEW_LOCALIZATION_KEY",
            },
            {
                "visible_text": "Teleportation Stone",
                "classification": "KEEP_EN_CANONICAL_ITEM_REFERENCE",
                "live_keys": [
                    "interface:options_simple_activate_tp",
                    "interface:options_simple_activate_tp_text",
                    "interface:options_simple_self_activate_tp",
                    "interface:options_simple_self_activate_tp_text",
                    "interface:smartcasting_Ability_TP",
                    "entities:Item_TeleportationStone_name",
                    "entities:Item_TeleportationStone_MidWars_name",
                ],
                "evidence": ["The surrounding settings labels are local stringtable text; the item-name span is canonical/protected."],
                "candidate_action": "KEEP_ITEM_NAME_EN; REVIEW_RUSSIAN_SURROUNDING_WORDING_SEPARATELY",
            },
            {
                "visible_text": "Profile",
                "classification": "PREACT_LOCAL_LABELS_PLUS_REMOTE_API_DATA",
                "source": "preact/src/layers/profile/**/*.tsx",
                "remote_data_source": ["/v1/stats/getprofilestats", "/v1/stats/getplayerstats"],
                "candidate_action": "LOCALIZE_LOCAL_TSX_LABELS_LATER; DO_NOT_REWRITE_API_VALUES",
            },
            {
                "visible_text": "MOTD",
                "classification": "REMOTE_CONTAINER_WITH_LOCAL_CHROME",
                "source": "ui/fe3/sections/motd.package",
                "remote_container": "https://hon-public.juvio.com/motd/remote-ul.zip",
                "remote_data_source": "https://<community-host>/v1/community/motd",
                "local_source": "preact-remote/src/components/motd.tsx",
                "candidate_action": "LOCALIZE_STATIC_CHROME_LATER; DO_NOT_HARDCODE_REMOTE_TITLE_BODY_OR_CTA_DATA",
            },
            {
                "visible_text": "Patch Notes",
                "classification": "BUNDLED_PREACT_EDITORIAL_CONTENT",
                "source": ["preact/src/layers/patch-notes/**", "preact/src/layers/patch-notes-v2/**"],
                "evidence": ["patchRegistry and patch TSX components are bundled; no fetch/http client is used by the patch-notes layers"],
                "candidate_action": "LOCALIZE_CHROME_SEPARATELY; REVIEW_EDITORIAL_CORPUS_AS_OWN_BATCH",
            },
            {
                "visible_text": "ATTENTION overlay",
                "classification": "NATIVE_LOCAL_STRINGTABLE",
                "live_keys": ["interface:warning_title", "interface:warning_text1", "interface:warning_text2"],
                "evidence": ["English and Thai locale tables contain localized key triplets; Pass C leaves the English values unchanged."],
                "candidate_action": "SAFE_LOCAL_STRINGTABLE_BATCH_LATER",
            },
        ],
        "mixed_language_inventory": {
            "interface_rows_with_cyrillic_and_latin": mixed_interface_count,
            "warning": "This raw count includes protected names, brands, keycaps, commands, URLs and placeholders; it is not a translation count.",
            "obvious_leading_enter_candidates": mixed_leading_enter,
        },
        "candidate_applied": False,
        "archive_built": False,
        "archive_installed": False,
        "runtime_verified": False,
    }

    validation = {
        "schema_version": 1,
        "batch_id": BATCH_ID,
        "result": "PASS" if not errors else "FAIL",
        "errors": errors,
        "selected_entries": len(candidates),
        "role_changes": len(ROLE_CANDIDATES),
        "role_already_compliant": {"interface:player_role_offlane": offlane_value},
        "staff_exact_alias_repairs": len(staff_inventory[BAD_STAFF_ALIAS]),
        "staff_deferred_inventory": {alias: len(keys) for alias, keys in staff_inventory.items() if alias != BAD_STAFF_ALIAS},
        "checks": {
            "pass_c_sha_pinned": "PASS",
            "upstream_source_index_pinned": "PASS",
            "pass_c_crc": "PASS",
            "candidate_only": "PASS",
            "no_build": "PASS",
            "no_install": "PASS",
            "no_duplicate_keys": "PASS" if len({r["logical_key"] for r in candidates}) == len(candidates) else "FAIL",
            "carry_literal_forbidden": "PASS" if not any(
                r["logical_key"] in ROLE_CANDIDATES and r["proposed_ru"].casefold() in {"нести", "переносить"}
                for r in candidates
            ) else "FAIL",
            "staff_keep_en_restored": "PASS" if all(BAD_STAFF_ALIAS.casefold() not in r["proposed_ru"].casefold() for r in candidates) else "FAIL",
            "structure_preserved": "PASS" if all(all(r["validation"].values()) for r in candidates) else "FAIL",
        },
        "baseline_modified": False,
        "upstream_modified": False,
        "candidate_applied": False,
        "runtime_verified": False,
    }

    BATCH_PATH.parent.mkdir(parents=True, exist_ok=True)
    batch_text = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in candidates)
    BATCH_PATH.write_text(batch_text, encoding="utf-8", newline="\n")
    RESOLUTION_PATH.write_text(json.dumps(resolution, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    VALIDATION_PATH.write_text(json.dumps(validation, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    staff_deferred = len(staff_inventory["Посох Мастера"])
    report = f"""# Controlled Batch 002 — terminology candidate and source resolution

Status: **HUMAN APPROVED / RUNTIME QA PENDING**

## Scope

- Baseline: accepted Pass C `{pass_c_sha}` (read-only).
- Upstream identity: `{EXPECTED_UPSTREAM_SHA}` (read-only).
- Candidate rows: **{len(candidates)}** — {len(ROLE_CANDIDATES)} role-term corrections and {len(staff_inventory[BAD_STAFF_ALIAS])} exact `Персонал Мастера` → `Staff of the Master` span restorations.
- `Offlane = Оффлейн` is already correct in Pass C and therefore is recorded as compliant, not emitted as a no-op patch row.
- Candidate generation itself does not build or install an archive; runtime
  build/install state is recorded separately after approval.

## Approved terminology represented by the candidate

| English | Required Russian | Pass C live keys |
|---|---|---|
| Carry | Керри | `game_messages:filter_carry`, `interface:player_role_carry` |
| Mid | Мид | `interface:player_role_mid` |
| Offlane | Оффлейн | `interface:player_role_offlane` (already compliant) |
| Soft Support | Поддержка | `interface:player_role_softsupport` |
| Hard Support | Основная поддержка | `interface:player_role_hardsupport` |

Literal `Carry = Нести` is rejected by validation and glossary policy.

## Staff of the Master

- KEEP_EN policy remains authoritative.
- **{len(staff_inventory[BAD_STAFF_ALIAS])}** exact `Персонал Мастера` occurrences are safe span-only candidate repairs in this batch.
- **{staff_deferred}** `Посох Мастера` occurrences are inventoried but deliberately deferred to another controlled batch; rewriting all of them here would exceed the narrow review scope.
- No ability/item mechanics, numbers, placeholders or HoN color codes are changed.

## Runtime source resolution

| Visible area | Resolution | Action in Batch 002 |
|---|---|---|
| Gameplay roles in Preact | Local enum labels in `preact/src/types/global.ts:23-28`; `Solo Offlane` needs a separate terminology decision. | Source identified; code/i18n override deferred until approval |
| Call Vote | Exact text exists only as an XML comment. Dialog header is runtime `{{header}}`; `interface:game_menu_vote` is only a related `Vote` key, not proof. | REVIEW; no guessed patch |
| MISSING | Hardcoded literal in `ui/hd_ui/templates/heroframe_templates.package:291`. | Source identified; no change |
| Teleportation Stone | Canonical protected item name inside live interface keys and entity name keys. | KEEP_EN; surrounding Russian can be reviewed later |
| Profile | Static labels are local Preact TSX; statistics are API data. | Local labels may be localized later; API values untouched |
| MOTD | Native panel loads remote UI; content comes from community MOTD API, while some chrome/fallback labels are local TSX. | Do not hardcode dynamic content |
| Patch Notes | Bundled Preact registry/components, not a runtime fetch layer. | Separate chrome/editorial pass later |
| ATTENTION | Native `interface` stringtable triplet: `warning_title`, `warning_text1`, `warning_text2`. | Safe local source identified; not translated here |

The raw Pass C interface table has **{mixed_interface_count}** rows containing both Cyrillic and Latin. That number is an inventory signal only: it includes canonical names, brands, keycaps, commands, URLs and placeholders. The source-resolution JSON separately lists obvious leading-`Enter` candidates without applying them.

## Artifacts

- `translation/batches/controlled_002_terminology.jsonl`
- `translation/reports/controlled_002_source_resolution.json`
- `translation/reports/controlled_002_validation.json`

Candidate validation result: **{validation['result']}**. Runtime actions, if
approved later, are tracked in `controlled_002_runtime_build.json` and
`controlled_002_install_state.json`.
"""
    REPORT_PATH.write_text(report, encoding="utf-8", newline="\n")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
