#!/usr/bin/env python3
"""Prepare a conservative, cumulative large-scale player-facing candidate pack.

CURRENT English is the semantic identity. Donor and Pass C are accepted only as
translation candidates. The script classifies every indexed CURRENT key and
auto-approves only structurally exact, simple player-facing donor translations.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PASS_C = ROOT / "build" / "pass-c" / "resources0.jz"
EXPECTED_PASS_C_SHA = "3d5ee66b9507c342d92b0be886d2918ea959e9beffb2126e6a7f77604142e301"
EXPECTED_UPSTREAM_SHA = "a518f760c7bdebcfb2f9258dbfcfe7e2bf81881938e4653b0b1c725e04099762"
BATCH_ID = "CONTROLLED_003_LARGE_SCALE_PLAYER_FACING"
MEMBERS = {
    "interface": "stringtables/interface_ru.str",
    "game_messages": "stringtables/game_messages_ru.str",
    "client_messages": "stringtables/client_messages_ru.str",
    "entities": "stringtables/entities_ru.str",
}

OUT_BATCH = ROOT / "translation" / "batches" / "controlled_003_consolidated.jsonl"
OUT_DECISIONS = ROOT / "translation" / "reports" / "controlled_003_all_current_decisions.jsonl"
OUT_REVIEW = ROOT / "translation" / "reports" / "controlled_003_review.jsonl"
OUT_UNRESOLVED = ROOT / "translation" / "reports" / "controlled_003_unresolved_sources.json"
OUT_VALIDATION = ROOT / "translation" / "reports" / "controlled_003_validation.json"
OUT_REPORT = ROOT / "translation" / "reports" / "CONTROLLED_003_LARGE_SCALE_REPORT.md"
OUT_CATEGORIES = ROOT / "translation" / "batches" / "controlled_003_categories"

AUTO_DOMAINS = {"interface", "game_messages", "client_messages"}
AUTO_CATEGORIES = {
    "functional_ui", "settings_ui", "profile_competitive_ui",
    "game_event_feed", "help_tutorial", "gameplay_description",
}
SEMANTIC_CATEGORIES = {
    "ability_description", "item_description", "hero_description",
    "boss_description", "gameplay_description",
}
NAME_CATEGORIES = {"hero_name", "item_name", "ability_name", "boss_name", "cosmetic_name"}
BLOCK_QUEUES = {
    "abilities_semantic", "items_semantic", "bosses_semantic",
    "structural_risk", "names_policy", "terminology", "mixed_language",
}
BLOCK_FLAGS = {
    "MECHANIC_TEXT", "STRUCTURAL_RISK", "FORBIDDEN_TRANSLATION",
    "POSSIBLY_STALE", "LOW_PRIORITY_TECHNICAL",
}
BLOCK_KEY_PREFIXES = ("tpp_", "mode_", "pickmode_", "hero_tip_")
BAD_RU = (
    "персонал мастера", "посох мастера", "без звука", "в недоумении",
    "юнитволкинг", "нести", "переносить", "применяется ", " нацеливаться ",
    " второе время", "\ufffd",
)


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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8", newline="\n")


def parse_table(data: bytes) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in data.decode("utf-8-sig").splitlines():
        if "\t" not in line or line.lstrip().startswith("//"):
            continue
        key, value = line.split("\t", 1)
        result[key] = value
    return result


def structures(value: str) -> dict[str, list[str]]:
    return {
        "placeholders": sorted(re.findall(r"\{[^{}]+\}|%\d*\$?[sdif]|#[A-Za-z0-9_]+#", value)),
        "colors": sorted(re.findall(r"\^(?:[!*]|[A-Za-z]|\d{3})", value)),
        "numbers": re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?", value),
        "markup": sorted(re.findall(r"</?[A-Za-z][^>]*>", value)),
    }


def latin_outside_protected(value: str) -> bool:
    clean = re.sub(r"\{[^{}]+\}|%\d*\$?[sdif]|#[A-Za-z0-9_]+#|\^(?:[!*]|[A-Za-z]|\d{3})|</?[A-Za-z][^>]*>", "", value)
    return bool(re.search(r"[A-Za-z]", clean))


def simple_candidate(source: dict[str, Any], candidate: dict[str, Any], comparison: dict[str, Any], consensus: dict[str, str]) -> tuple[bool, str]:
    current = source["current_source_value"]
    proposed = comparison.get("donor_value")
    pass_c = comparison.get("pass_c_value")
    if source["domain"] not in AUTO_DOMAINS or source["runtime_role"] != "DISPLAY_TEXT":
        return False, "NON_AUTOMATIC_SOURCE_LAYER"
    if source["category"] not in AUTO_CATEGORIES:
        return False, "CATEGORY_REQUIRES_CONTEXT"
    if source["key"].casefold().startswith(BLOCK_KEY_PREFIXES):
        return False, "DEBUG_MAP_OR_CONTEXTUAL_KEY"
    if source["category"] in SEMANTIC_CATEGORIES:
        return False, "MECHANIC_OR_NARRATIVE_REVIEW"
    if candidate.get("recommended_status") != "DONOR_CANDIDATE":
        return False, "NO_HIGH_CONFIDENCE_DONOR_STATUS"
    if set(candidate.get("flags", [])) & BLOCK_FLAGS:
        return False, "BLOCKING_CANDIDATE_FLAG"
    if set(candidate.get("review_queues", [])) & BLOCK_QUEUES:
        return False, "SPECIALIST_REVIEW_QUEUE"
    if comparison.get("donor_language") != "RUSSIAN" or not comparison.get("donor_structure_safe"):
        return False, "DONOR_NOT_SAFE_RUSSIAN"
    if comparison.get("donor_forbidden_hits") or not proposed or proposed == current:
        return False, "DONOR_FORBIDDEN_OR_NOOP"
    if comparison.get("current_sha256") != source["current_source_hash"]:
        return False, "CURRENT_IDENTITY_MISMATCH"
    if pass_c != proposed:
        if pass_c not in (None, "", current):
            return False, "TRANSLATION_SOURCES_DISAGREE"
        if consensus.get(current) != proposed:
            return False, "UNCONFIRMED_SINGLE_SOURCE_TRANSLATION"
    if len(current) > 90 or len(proposed) > 130:
        return False, "LONG_CONTEXTUAL_TEXT"
    if not re.search(r"[А-Яа-яЁё]", proposed) or latin_outside_protected(proposed):
        return False, "MIXED_OR_NON_RUSSIAN_CANDIDATE"
    if any(fragment in proposed.casefold() for fragment in BAD_RU):
        return False, "KNOWN_UNNATURAL_OR_FORBIDDEN_RUSSIAN"
    if structures(current) != structures(proposed):
        return False, "TOKENS_MARKUP_NUMBERS_CHANGED"
    return True, "HIGH_CONFIDENCE_SIMPLE_DONOR"


def make_row(source: dict[str, Any], baseline: str, proposed: str, reason: str, origin: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "batch_id": BATCH_ID,
        "logical_key": source["logical_key"],
        "domain": source["domain"],
        "key": source["key"],
        "category": source["category"],
        "runtime_role": source["runtime_role"],
        "context": source.get("context", ""),
        "current_source": source["current_source_value"],
        "current_source_hash": source["current_source_hash"],
        "pass_c_baseline": baseline,
        "pass_c_baseline_hash": hash_text(baseline),
        "proposed_ru": proposed,
        "reason": reason,
        "origin": origin,
        "status": "AUTO_APPROVED_HIGH_CONFIDENCE" if origin == "NEW_AUTO" else "PRIOR_APPROVED_REUSED",
        "approval_state": "APPROVED_FOR_CONTROLLED_RUNTIME_QA",
        "applied": False,
        "runtime_verified": False,
        "validation": {
            "source_hash_match": hash_text(source["current_source_value"]) == source["current_source_hash"],
            "baseline_changed": baseline != proposed,
            "structures_match_current": structures(source["current_source_value"]) == structures(proposed),
        },
    }


def main() -> int:
    if sys.version_info < (3, 14):
        raise SystemExit("Python 3.14+ is required for ZIP Zstandard members")
    if sha256_file(PASS_C) != EXPECTED_PASS_C_SHA:
        raise SystemExit("Pass C baseline mismatch")

    sources_list = load_jsonl(ROOT / "translation" / "source_index.jsonl")
    sources = {row["logical_key"]: row for row in sources_list}
    candidates = {row["logical_key"]: row for row in load_jsonl(ROOT / "translation" / "candidate_index.jsonl")}
    comparisons: dict[str, dict[str, Any]] = {}
    for row in load_jsonl(ROOT / "translation" / "reports" / "pre_d_key_comparison.jsonl"):
        logical = f"{row['domain']}:{row['key']}"
        if logical in sources and row.get("current_sha256") == sources[logical]["current_source_hash"]:
            comparisons[logical] = row
    if len(sources) != len(sources_list) or len(sources) != 19538:
        raise SystemExit(f"Unexpected CURRENT index cardinality: {len(sources_list)}/{len(sources)}")
    if {row["source_identity"] for row in sources_list} != {f"upstream@{EXPECTED_UPSTREAM_SHA}"}:
        raise SystemExit("CURRENT source index is not pinned to accepted upstream")

    with zipfile.ZipFile(PASS_C) as archive:
        if archive.testzip() is not None:
            raise SystemExit("Pass C CRC failed")
        tables = {domain: parse_table(archive.read(member)) for domain, member in MEMBERS.items()}

    # Translation-memory consensus is intentionally derived only from exact
    # donor==Pass-C agreements for the same unchanged CURRENT English text.
    # A unique consensus may be propagated to duplicate live keys; a lone donor
    # proposal is never enough for automatic approval.
    memory: dict[str, set[str]] = {}
    for comparison in comparisons.values():
        current = comparison.get("current_en", "")
        proposed = comparison.get("donor_value")
        if (
            proposed and comparison.get("pass_c_value") == proposed
            and comparison.get("donor_language") == "RUSSIAN"
            and comparison.get("donor_structure_safe") and comparison.get("pass_c_structure_safe")
            and not comparison.get("donor_forbidden_hits")
            and re.search(r"[А-Яа-яЁё]", proposed) and not latin_outside_protected(proposed)
            and not any(fragment in proposed.casefold() for fragment in BAD_RU)
            and structures(current) == structures(proposed)
        ):
            memory.setdefault(current, set()).add(proposed)
    consensus = {current: next(iter(values)) for current, values in memory.items() if len(values) == 1}

    approved: dict[str, dict[str, Any]] = {}
    decisions: list[dict[str, Any]] = []
    review: list[dict[str, Any]] = []

    # Reuse completed controlled batches without re-translating them.
    for prior_name in ("controlled_001_modern_ui.jsonl", "controlled_002_terminology.jsonl"):
        for prior in load_jsonl(ROOT / "translation" / "batches" / prior_name):
            logical = prior["logical_key"]
            source = sources[logical]
            baseline = tables[source["domain"]][source["key"]]
            approved[logical] = make_row(source, baseline, prior["proposed_ru"], f"reuse_{prior['batch_id'].lower()}", "PRIOR_APPROVED")

    # Restore every remaining provable Russian alias of the protected Staff name.
    for logical, source in sources.items():
        if source["domain"] != "entities" or source["key"] not in tables["entities"]:
            continue
        baseline = tables["entities"][source["key"]]
        if "Посох Мастера" not in baseline:
            continue
        if "Staff of the Master" not in source["current_source_value"]:
            review.append({"logical_key": logical, "reason": "STAFF_SOURCE_SPAN_NOT_PROVABLE", "current_source": source["current_source_value"], "pass_c": baseline})
            continue
        proposed = baseline.replace("Посох Мастера", "Staff of the Master")
        approved[logical] = make_row(source, baseline, proposed, "restore_protected_staff_exact_span", "NEW_AUTO")

    for logical, source in sorted(sources.items()):
        if logical in approved:
            decision = "PRIOR_APPROVED_REUSED" if approved[logical]["origin"] == "PRIOR_APPROVED" else "AUTO_APPROVED_HIGH_CONFIDENCE"
            reason = approved[logical]["reason"]
        elif source["category"] in NAME_CATEGORIES:
            decision, reason = "KEEP_EN", "CANONICAL_OR_PROPER_NAME_POLICY"
        elif source["domain"] == "bot_messages" or source["runtime_role"] != "DISPLAY_TEXT":
            decision, reason = "TECHNICAL", "NON_PLAYER_FACING_OR_BOT_LAYER"
        else:
            candidate = candidates.get(logical, {})
            comparison = comparisons.get(logical, {})
            ok, reason = simple_candidate(source, candidate, comparison, consensus)
            if ok and source["key"] in tables.get(source["domain"], {}):
                baseline = tables[source["domain"]][source["key"]]
                approved[logical] = make_row(source, baseline, comparison["donor_value"], reason, "NEW_AUTO")
                decision = "AUTO_APPROVED_HIGH_CONFIDENCE"
            else:
                decision = "REVIEW"
                review.append({
                    "logical_key": logical, "domain": source["domain"], "key": source["key"],
                    "category": source["category"], "current_source": source["current_source_value"],
                    "candidate_ru": comparison.get("donor_value"), "pass_c": comparison.get("pass_c_value"),
                    "reason": reason,
                })
        decisions.append({
            "logical_key": logical, "domain": source["domain"], "key": source["key"],
            "category": source["category"], "runtime_role": source["runtime_role"],
            "decision": decision, "reason": reason,
        })

    batch = sorted(approved.values(), key=lambda row: row["logical_key"])
    for ordinal, row in enumerate(batch, 1):
        row["ordinal"] = ordinal
    if len({row["logical_key"] for row in batch}) != len(batch):
        raise SystemExit("Duplicate approved logical keys")

    write_jsonl(OUT_BATCH, batch)
    write_jsonl(OUT_DECISIONS, decisions)
    write_jsonl(OUT_REVIEW, sorted(review, key=lambda row: row["logical_key"]))
    OUT_CATEGORIES.mkdir(parents=True, exist_ok=True)
    for old in OUT_CATEGORIES.glob("*.jsonl"):
        old.unlink()
    category_rows: dict[str, list[dict[str, Any]]] = {}
    for row in batch:
        category_rows.setdefault(row["category"], []).append(row)
    for category, rows in sorted(category_rows.items()):
        write_jsonl(OUT_CATEGORIES / f"{category}.jsonl", rows)

    unresolved = {
        "schema_version": 1, "batch_id": BATCH_ID,
        "classes": [
            {"class": "REMOTE_DYNAMIC_HTML", "sources": ["MOTD/community API", "remote-ul.zip"], "action": "REPORT_ONLY_NO_HARDCODE"},
            {"class": "BUNDLED_HTML_PREACT", "sources": ["preact/src/layers/profile", "preact/src/layers/patch-notes"], "action": "LOCAL_CHROME_REQUIRES_SEPARATE_SOURCE_BUILD; API/editorial data unchanged"},
            {"class": "NATIVE_HARDCODED", "sources": ["ui/hd_ui/templates/heroframe_templates.package:MISSING", "runtime Call Vote header producer unresolved"], "action": "REPORT_OR_TRACE; NO_GUESSED_STRINGTABLE_FIX"},
            {"class": "IMAGE_TEXT", "sources": ["reports/help_image_assets.jsonl", "reports/image_text_review.json", "promo PATCH NOTES images"], "action": "ASSET-LEVEL REVIEW; NOT MODIFIED"},
            {"class": "DEBUG_UI", "sources": ["Test+++ practice/debug panel"], "action": "OUTSIDE NORMAL PLAYER-FACING PASS"},
        ],
    }
    OUT_UNRESOLVED.write_text(json.dumps(unresolved, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    counts = Counter(row["decision"] for row in decisions)
    changed = [row for row in batch if row["pass_c_baseline"] != row["proposed_ru"]]
    reasons = Counter(row["reason"] for row in review)
    errors: list[dict[str, Any]] = []
    if sum(counts.values()) != len(sources):
        errors.append({"code": "INCOMPLETE_CURRENT_CLASSIFICATION"})
    for row in batch:
        if not row["validation"]["source_hash_match"]:
            errors.append({"code": "SOURCE_HASH_MISMATCH", "key": row["logical_key"]})
        if row["origin"] == "NEW_AUTO" and row["reason"] != "restore_protected_staff_exact_span" and not row["validation"]["structures_match_current"]:
            errors.append({"code": "STRUCTURE_CHANGED", "key": row["logical_key"]})
        low = row["proposed_ru"].casefold()
        if "персонал мастера" in low or "посох мастера" in low:
            errors.append({"code": "STAFF_ALIAS_REMAINS", "key": row["logical_key"]})
    validation = {
        "schema_version": 1, "batch_id": BATCH_ID,
        "result": "PASS" if not errors else "FAIL", "errors": errors,
        "current_keys_processed": len(sources), "decision_counts": dict(sorted(counts.items())),
        "candidate_entries": len(batch), "actual_changes_vs_pass_c": len(changed),
        "prior_approved_reused": sum(row["origin"] == "PRIOR_APPROVED" for row in batch),
        "new_auto_approved": sum(row["origin"] == "NEW_AUTO" for row in batch),
        "review_reason_counts": dict(reasons.most_common()),
        "checks": {
            "pass_c_sha": "PASS", "upstream_identity": "PASS", "pass_c_crc": "PASS",
            "all_current_classified": "PASS" if sum(counts.values()) == len(sources) else "FAIL",
            "unique_candidate_keys": "PASS", "staff_keep_en": "PASS" if not any(e["code"] == "STAFF_ALIAS_REMAINS" for e in errors) else "FAIL",
            "no_install": "PASS", "no_upstream_write": "PASS",
        },
    }
    OUT_VALIDATION.write_text(json.dumps(validation, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    category_counts = Counter(row["category"] for row in changed)
    report = f"""# Controlled 003 — large-scale player-facing localization

Status: **CANDIDATE PACK PREPARED / RUNTIME QA BUILD PENDING**

- CURRENT keys classified: **{len(sources)}**.
- Consolidated approved candidate rows: **{len(batch)}**.
- Actual stringtable value changes relative to Pass C: **{len(changed)}**.
- Prior Controlled 001/002 rows reused: **{validation['prior_approved_reused']}** (not re-translated).
- New high-confidence approvals: **{validation['new_auto_approved']}**.
- KEEP_EN: **{counts['KEEP_EN']}**.
- REVIEW: **{counts['REVIEW']}**.
- TECHNICAL/non-player-facing: **{counts['TECHNICAL']}**.

## Changed rows by category

""" + "\n".join(f"- `{key}`: {value}" for key, value in sorted(category_counts.items())) + f"""

## Safety boundary

CURRENT English hashes are the semantic identity. Donor/Pass C agreement is
used only for simple labels with exact placeholder, HoN color, markup and number
preservation. Hero/item/ability/boss/cosmetic names remain KEEP_EN. Semantic
descriptions and all ambiguous candidates remain in REVIEW.

Unresolved remote/HTML/hardcoded/image/debug sources are listed separately in
`controlled_003_unresolved_sources.json`; no remote content or image text is
hardcoded. Pass C and upstream remain unchanged.

Validation: **{validation['result']}**.
"""
    OUT_REPORT.write_text(report, encoding="utf-8", newline="\n")
    print(json.dumps({"result": validation["result"], "counts": validation["decision_counts"], "candidate_entries": len(batch), "actual_changes": len(changed)}, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
