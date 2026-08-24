#!/usr/bin/env python3
"""Build the deterministic multi-source candidate architecture.

This tool indexes and prioritizes existing text only. It never translates,
builds a game archive, installs a pass, or writes outside the project tree.
"""

from __future__ import annotations

import collections
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.localization.pre_d_donor_audit import (  # noqa: E402
    language_class,
    structural_comparison,
)


PASS_C_SHA = "3d5ee66b9507c342d92b0be886d2918ea959e9beffb2126e6a7f77604142e301"
UPSTREAM_SHA = "a518f760c7bdebcfb2f9258dbfcfe7e2bf81881938e4653b0b1c725e04099762"
DONOR_COMMIT = "9f276bf86037bffe9e6d208dacd99d19b4e666eb"
SCHEMA_VERSION = 1
QUEUE_NAMES = (
    "modern_ui",
    "items_semantic",
    "abilities_semantic",
    "bosses_semantic",
    "terminology",
    "mixed_language",
    "structural_risk",
    "names_policy",
)

MODERN_PATTERNS = re.compile(
    r"(?:learn|ladder|store2|store_|profile|match_history|collection|award|honor|"
    r"most_played|preparing|battlefield|search_options|matchmaking|account_|compendium)",
    re.I,
)
TERMINOLOGY_RE = re.compile(
    r"(?:\bCarry\b|\bSilence\b|\bPerplex\b|Staff of the Master|Movement Speed|"
    r"Attack Speed|Magic Damage|True Damage|Courier Stash|Tier (?:I|II|III|IV))",
    re.I,
)
RUNTIME_KEY_HINTS = {
    "game_messages:filter_carry",
    "interface:store2_hero_role",
    "interface:tutorial_slide_top_center_creeps_denied",
    "interface:stash_title",
    "interface:options_simple_activate_courier_stash",
}
RUNTIME_ENTITY_HINTS = (
    "hellflower",
    "genjuro",
    "crimsonguard",
    "helmofThefirelands".lower(),
    "lagunaorb",
    "gauntlet",
    "kongor",
    "phoenixboss",
    "fluffylumps",
    "pegasusboots",
    "animateforest",
)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def infer_entity(key: str) -> str | None:
    match = re.match(r"^(Hero|Ability|Item|State|Unit)_([^_:]+)", key, re.I)
    if not match:
        return None
    owner = match.group(2)
    if match.group(1).lower() == "ability":
        owner = re.sub(r"\d+[A-Za-z]?$", "", owner)
    return f"{match.group(1).title()}_{owner}"


def is_item_semantic(key: str, category: str) -> bool:
    low = key.lower()
    return low.startswith("item_") and category not in {"item_name", "search_metadata", "shop_metadata"}


def is_ability_semantic(key: str, category: str) -> bool:
    low = key.lower()
    return low.startswith("ability_") and category not in {"ability_name", "search_metadata"}


def is_boss_semantic(logical_key: str, category: str) -> bool:
    low = logical_key.lower()
    return any(term in low for term in ("kongor", "phoenixboss", "fluffylumps", "boss_info", "boss_")) and category not in {"item_name", "ability_name", "boss_name"}


def is_mechanic(key: str, category: str, logical_key: str) -> bool:
    return (
        is_item_semantic(key, category)
        or is_ability_semantic(key, category)
        or is_boss_semantic(logical_key, category)
        or category in {"item_description", "ability_description", "state_description", "mechanic_text"}
    )


def is_modern_ui(domain: str, key: str, category: str, current: str) -> bool:
    if domain != "interface":
        return False
    if MODERN_PATTERNS.search(key) or MODERN_PATTERNS.search(current):
        return True
    return category in {"profile_competitive_ui", "matchmaking_ui", "modern_reborn_ui"}


def runtime_confirmed(logical_key: str) -> bool:
    low = logical_key.lower()
    return logical_key in RUNTIME_KEY_HINTS or logical_key.startswith("interface:game_menu_") or any(
        term in low for term in RUNTIME_ENTITY_HINTS
    )


def meaningful_candidate(current: str, value: str | None) -> bool:
    return value is not None and value != "" and value != current


def resolve_candidate(
    comparison: dict[str, Any],
    catalog: dict[str, Any],
    approved: dict[str, Any] | None,
    forbidden_phrases: list[str],
) -> dict[str, Any]:
    domain = comparison["domain"]
    key = comparison["key"]
    logical_key = f"{domain}:{key}"
    current = comparison["current_en"]
    donor = comparison.get("donor_value")
    pass_c = comparison.get("pass_c_value")
    category = comparison.get("category") or catalog.get("category", "unknown")
    runtime_role = comparison.get("runtime_role") or catalog.get("runtime_role", "UNKNOWN")
    source_hash = comparison["current_sha256"]
    donor_candidate = meaningful_candidate(current, donor)
    pass_candidate = meaningful_candidate(current, pass_c)
    approved_compatible = bool(approved and approved.get("source_hash") == source_hash)

    flags: set[str] = set()
    conflicts: set[str] = set()
    queues: set[str] = set()
    mechanic = is_mechanic(key, category, logical_key)
    modern = is_modern_ui(domain, key, category, current)
    item_semantic = is_item_semantic(key, category)
    ability_semantic = is_ability_semantic(key, category)
    boss_semantic = is_boss_semantic(logical_key, category)

    if runtime_role == "DISPLAY_TEXT":
        flags.add("PLAYER_FACING")
    if runtime_confirmed(logical_key):
        flags.add("RUNTIME_CONFIRMED")
    if logical_key.startswith("interface:game_menu_"):
        flags.add("RAW_KEY_RUNTIME_HISTORY")
    if mechanic:
        flags.update(("MECHANIC_TEXT", "SEMANTIC_REVIEW_REQUIRED"))
    if modern:
        flags.add("MODERN_REBORN_UI")
        queues.add("modern_ui")
    if item_semantic:
        queues.add("items_semantic")
    if ability_semantic:
        queues.add("abilities_semantic")
    if boss_semantic:
        queues.add("bosses_semantic")
        flags.add("POSSIBLY_STALE")
    if TERMINOLOGY_RE.search(current) or any(
        term in logical_key.lower() for term in ("carry", "silence", "perplex", "courier_stash")
    ):
        queues.add("terminology")
        flags.add("TERMINOLOGY_REVIEW")
    if comparison.get("donor_language") == "MIXED" or comparison.get("pass_c_language") == "MIXED":
        queues.add("mixed_language")
        flags.add("MIXED_LANGUAGE")
    donor_safe = bool(comparison.get("donor_structure_safe"))
    pass_safe = bool(comparison.get("pass_c_structure_safe"))
    if donor_candidate and not donor_safe:
        queues.add("structural_risk")
        flags.add("DONOR_STRUCTURAL_RISK")
    if pass_candidate and not pass_safe:
        queues.add("structural_risk")
        flags.add("PASS_C_STRUCTURAL_RISK")
    if queues & {"structural_risk"}:
        flags.add("STRUCTURAL_RISK")
    if category in {"hero_name", "ability_name", "item_name", "boss_name", "cosmetic_name"}:
        flags.add("PROPER_NAME")
        if category in {"ability_name", "boss_name"}:
            queues.add("names_policy")
    if "animateforest" in logical_key.lower():
        queues.add("names_policy")
        flags.add("NAME_POLICY_OPEN")
    if any(term in current for term in ("Legion", "Hellbourne")):
        queues.add("names_policy")
        flags.add("FACTION_NAME_POLICY_OPEN")

    for phrase in forbidden_phrases:
        if donor and phrase.casefold() in donor.casefold():
            conflicts.add(f"DONOR_FORBIDDEN:{phrase}")
        if pass_c and phrase.casefold() in pass_c.casefold():
            conflicts.add(f"PASS_C_FORBIDDEN:{phrase}")
    if conflicts:
        flags.add("FORBIDDEN_TRANSLATION")
        queues.add("terminology")
    if category == "item_name" and donor_candidate:
        conflicts.add("DONOR_CHANGES_SEARCHABLE_ITEM_NAME")
    if "staff of the master" in current.casefold() and donor and "посох мастера" in donor.casefold():
        conflicts.add("KEEP_EN_STAFF_OF_THE_MASTER")
    if comparison.get("audit_status") == "KEEP_EN":
        flags.add("KEEP_EN_POLICY")

    if mechanic and donor_candidate:
        if not donor_safe or boss_semantic:
            flags.add("DONOR_STYLE_ONLY")
        else:
            flags.add("DONOR_SEMANTICS_UNVERIFIED")

    if approved_compatible:
        status = "APPROVED_EXISTING"
    elif comparison.get("audit_status") == "KEEP_EN":
        status = "KEEP_EN"
    elif "STRUCTURAL_RISK" in flags:
        status = "STRUCTURAL_RISK"
    elif mechanic and (donor_candidate or pass_candidate):
        status = "SEMANTIC_REVIEW_REQUIRED"
    elif not donor_candidate and not pass_candidate:
        status = "NEW_CURRENT_CONTENT" if donor is None else "REVIEW"
    elif donor_candidate and not pass_candidate:
        status = "DONOR_CANDIDATE"
    elif pass_candidate and not donor_candidate:
        status = "PASS_C_CANDIDATE"
    elif modern:
        status = "PASS_C_CANDIDATE"
    elif donor == pass_c:
        status = "DONOR_CANDIDATE"
    else:
        status = "BOTH_SUSPICIOUS"

    score = 0
    score += 20 if "PLAYER_FACING" in flags else 0
    score += 50 if "RUNTIME_CONFIRMED" in flags else 0
    score += 45 if "RAW_KEY_RUNTIME_HISTORY" in flags else 0
    score += 40 if "STRUCTURAL_RISK" in flags else 0
    score += 35 if "MECHANIC_TEXT" in flags else 0
    score += 30 if "MODERN_REBORN_UI" in flags else 0
    score += 25 if "MIXED_LANGUAGE" in flags else 0
    score += 25 if "FORBIDDEN_TRANSLATION" in flags else 0
    score += 20 if "POSSIBLY_STALE" in flags else 0
    score += 15 if "TERMINOLOGY_REVIEW" in flags else 0
    if runtime_role != "DISPLAY_TEXT" or "test" in key.lower() or "debug" in key.lower():
        score -= 40
        flags.add("LOW_PRIORITY_TECHNICAL")

    return {
        "schema_version": SCHEMA_VERSION,
        "logical_key": logical_key,
        "source_ref": f"translation/source_index.jsonl#{logical_key}",
        "current_source_hash": source_hash,
        "candidates": {
            "approved": {
                "available": approved is not None,
                "memory_id": approved.get("id") if approved else None,
                "value_hash": sha256_text(approved["approved_ru"]) if approved else None,
                "source_hash_compatible": approved_compatible,
                "approval_state": approved.get("approval_status") if approved else None,
            },
            "donor": {
                "available": donor is not None,
                "is_translation_candidate": donor_candidate,
                "value_hash": comparison.get("donor_sha256"),
                "language": comparison.get("donor_language", "ABSENT"),
                "source_identity": f"hon_ru_pack@{DONOR_COMMIT}:{domain}",
                "value_ref": f"translation/reports/pre_d_key_comparison.jsonl#{logical_key}:donor_value",
                "structural_compatible": donor_safe,
            },
            "pass_c": {
                "available": pass_c is not None,
                "is_translation_candidate": pass_candidate,
                "value_hash": comparison.get("pass_c_sha256"),
                "language": comparison.get("pass_c_language", "ABSENT"),
                "source_identity": f"pass_c@{PASS_C_SHA}:{domain}",
                "value_ref": f"translation/reports/pre_d_key_comparison.jsonl#{logical_key}:pass_c_value",
                "structural_compatible": pass_safe,
            },
        },
        "recommended_status": status,
        "flags": sorted(flags),
        "policy_conflicts": sorted(conflicts),
        "structural_differences": {
            "donor": comparison.get("donor_structure_differences", []),
            "pass_c": comparison.get("pass_c_structure_differences", []),
        },
        "review_queues": sorted(queues),
        "priority_score": score,
        "auto_approved": status in {"APPROVED_EXISTING", "KEEP_EN"},
    }


def resolver_view(
    logical_key: str,
    comparison: dict[str, Any],
    resolution: dict[str, Any],
    approved: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "key": logical_key,
        "current_source": comparison["current_en"],
        "current_source_hash": comparison["current_sha256"],
        "candidates": {
            "donor": comparison.get("donor_value"),
            "pass_c": comparison.get("pass_c_value"),
            "approved": approved.get("approved_ru") if approved else None,
        },
        "recommended_status": resolution["recommended_status"],
        "flags": resolution["flags"],
        "policy_conflicts": resolution["policy_conflicts"],
        "review_queues": resolution["review_queues"],
        "priority_score": resolution["priority_score"],
    }


def runtime_observations() -> list[dict[str, Any]]:
    observations = [
        ("DT0-OBS-001", "STRENGTH", "Item_Genjuro", "Genjuro tooltip is significantly more readable than Pass C."),
        ("DT0-OBS-002", "STRENGTH", "Item_Hellflower", "Hellflower tooltip is significantly more readable than Pass C."),
        ("DT0-OBS-003", "STRENGTH", "PhoenixRewards", "Phoenix/Fluffylumps item descriptions are substantially more complete."),
        ("DT0-OBS-004", "STRENGTH", "Hero_Gauntlet", "Some timing/mechanical wording is clearer than Pass C."),
        ("DT0-OBS-005", "STRENGTH", None, "Cosmetics and Emotes appear as «Косметика» and «Эмоции»."),
        ("DT0-OBS-006", "STRENGTH", None, "In-game game_menu_* identifiers resolve to labels; voting menu is localized."),
        ("DT0-OBS-007", "STRENGTH", "Plinko", "Plinko is partly/well localized."),
        ("DT0-OBS-008", "WEAKNESS", None, "Modern Reborn UI remains substantially English: LEARN, LADDER, STORE, profile, collections, awards and honor UI."),
        ("DT0-OBS-009", "WEAKNESS", None, "Preparing Battlefield and settings/Search Options fragments remain English."),
        ("DT0-OBS-010", "RISK", "Boss_Kongor", "Good donor wording may describe older Kongor mechanics; current game data must decide semantics."),
        ("DT0-OBS-011", "ISSUE", "Item_Hellflower", "Perplex appears as «Озадачен»; terminology remains unresolved."),
        ("DT0-OBS-012", "ISSUE", "Item_Genjuro", "Mixed Master Assassin's Stealth and fade/stealth wording remain."),
        ("DT0-OBS-013", "ISSUE", None, "Staff of the Master is rendered as «Посох Мастера», conflicting with searchable KEEP_EN policy."),
        ("DT0-OBS-014", "STYLE", None, "Abbreviations such as «Скор. движ.», «маг. урон» and «чист. урон» need layout-aware review."),
        ("DT0-OBS-015", "ISSUE", None, "Courier Stash remains English in player-facing runtime text."),
        ("DT0-OBS-016", "ISSUE", "Item_PegasusBoots", "Mixed/malformed tooltip contains apparent technical P1 fragments."),
        ("DT0-OBS-017", "OPEN_QUESTION", "Ability_AnimateForest", "Ability name remains English while description is Russian; name policy is unresolved."),
        ("DT0-OBS-018", "ISSUE", None, "Preparing Battlefield remains English on the loading screen."),
        ("DT0-OBS-019", "OPEN_QUESTION", None, "Legion/Hellbourne remain English; faction-name policy is unresolved."),
    ]
    return [
        {
            "id": ident,
            "observed_in": "donor_test_0",
            "type": kind,
            "entity": entity,
            "description": description,
            "runtime_verified": True,
            "localization_key": None,
            "confidence": "CONFIRMED_RUNTIME_OBSERVATION",
        }
        for ident, kind, entity, description in observations
    ]


def issue_additions() -> list[dict[str, Any]]:
    definitions = [
        ("HYB-ISSUE-001", "semantic_staleness", "Boss_Kongor", "Donor Kongor text may describe older mechanics; do not reuse without current-game validation.", "CRITICAL"),
        ("HYB-ISSUE-002", "terminology", "Item_Hellflower", "Perplex is shown as «Озадачен» but remains unresolved.", "HIGH"),
        ("HYB-ISSUE-003", "mixed_language", "Item_Genjuro", "Master Assassin's Stealth remains English inside a Russian tooltip.", "HIGH"),
        ("HYB-ISSUE-004", "keep_en_conflict", None, "Donor uses «Посох Мастера» instead of searchable Staff of the Master.", "HIGH"),
        ("HYB-ISSUE-005", "style_abbreviation", None, "Donor uses beginner-unfriendly abbreviations; review only with layout context.", "MEDIUM"),
        ("HYB-ISSUE-006", "missing_translation", None, "Courier Stash remains English in donor runtime.", "HIGH"),
        ("HYB-ISSUE-007", "structural_risk", "Item_PegasusBoots", "Mixed/malformed tooltip contains apparent P1 technical fragments.", "CRITICAL"),
        ("HYB-ISSUE-008", "name_policy", "Ability_AnimateForest", "Ability-name localization policy is unresolved.", "MEDIUM"),
        ("HYB-ISSUE-009", "missing_translation", None, "Preparing Battlefield remains English.", "HIGH"),
        ("HYB-ISSUE-010", "faction_name_policy", None, "Legion/Hellbourne policy remains open.", "MEDIUM"),
        ("HYB-ISSUE-011", "modern_ui_coverage", None, "Donor has weak coverage of modern Reborn navigation/profile/store UI.", "HIGH"),
        ("HYB-ISSUE-012", "raw_key_root_cause", None, "Donor en-locale resolves game_menu_* while Pass C ru-locale showed raw identifiers; locale/resource-path cause needs targeted runtime tracing.", "CRITICAL"),
    ]
    return [
        {
            "id": ident,
            "category": category,
            "entity": entity,
            "localization_key": None,
            "description": description,
            "reference": "DONOR TEST 0 runtime observation",
            "observed_in": "donor_test_0",
            "expected_behavior": "Resolve through controlled semantic/policy review; no automatic translation.",
            "status": "OPEN",
            "fixed_in_pass": None,
            "runtime_verified": True,
            "priority": priority,
        }
        for ident, category, entity, description, priority in definitions
    ]


def main() -> int:
    catalog_rows = read_jsonl(ROOT / "catalog" / "strings.jsonl")
    catalog_by_id = {row["id"]: row for row in catalog_rows}
    comparisons_all = read_jsonl(ROOT / "translation" / "reports" / "pre_d_key_comparison.jsonl")
    comparisons = [row for row in comparisons_all if row.get("current_en") is not None]
    comparison_by_id = {f"{row['domain']}:{row['key']}": row for row in comparisons}
    memory_rows = read_jsonl(ROOT / "translation" / "translation_memory.jsonl")
    approved_by_id = {
        row["logical_key"]: row
        for row in memory_rows
        if row.get("approval_status") == "APPROVED"
    }
    forbidden_data = json.loads((ROOT / "translation" / "forbidden_ru.json").read_text(encoding="utf-8"))
    forbidden_phrases = sorted(set(forbidden_data.get("global_review_phrases", [])))

    missing_catalog = sorted(set(comparison_by_id) - set(catalog_by_id))
    if missing_catalog:
        raise SystemExit(f"Current keys missing from catalog: {missing_catalog[:10]}")

    source_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    resolver_rows: dict[str, dict[str, Any]] = {}
    for logical_key in sorted(comparison_by_id):
        comparison = comparison_by_id[logical_key]
        catalog = catalog_by_id[logical_key]
        source_rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "logical_key": logical_key,
                "domain": comparison["domain"],
                "key": comparison["key"],
                "current_source_value": comparison["current_en"],
                "current_source_hash": comparison["current_sha256"],
                "source_identity": f"upstream@{UPSTREAM_SHA}",
                "source_file": catalog.get("source_file"),
                "source_line": catalog.get("source_line"),
                "category": comparison.get("category") or catalog.get("category"),
                "context": catalog.get("context"),
                "runtime_role": comparison.get("runtime_role") or catalog.get("runtime_role"),
                "entity": infer_entity(comparison["key"]),
                "current_key_exists": True,
            }
        )
        approved = approved_by_id.get(logical_key)
        resolution = resolve_candidate(comparison, catalog, approved, forbidden_phrases)
        candidate_rows.append(resolution)
        resolver_rows[logical_key] = resolver_view(logical_key, comparison, resolution, approved)

    write_jsonl(ROOT / "translation" / "source_index.jsonl", source_rows)
    write_jsonl(ROOT / "translation" / "candidate_index.jsonl", candidate_rows)

    entity_groups: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for row in source_rows:
        if row["entity"]:
            entity_groups[row["entity"]].append(row)
    entity_rows = [
        {
            "schema_version": SCHEMA_VERSION,
            "entity": entity,
            "key_count": len(rows),
            "domains": sorted({row["domain"] for row in rows}),
            "categories": sorted({row["category"] for row in rows}),
            "source_refs": [f"translation/source_index.jsonl#{row['logical_key']}" for row in rows],
            "semantic_context_status": "CURRENT_STRING_CONTEXT_INDEXED",
            "gameplay_data_context_status": "REVIEW_REQUIRED",
        }
        for entity, rows in sorted(entity_groups.items())
    ]
    write_jsonl(ROOT / "translation" / "entity_context.jsonl", entity_rows)

    queue_root = ROOT / "translation" / "review_queues"
    combined_queue: list[dict[str, Any]] = []
    queue_counts: dict[str, int] = {}
    for queue in QUEUE_NAMES:
        queue_rows = [
            {
                "logical_key": row["logical_key"],
                "queue": queue,
                "priority_score": row["priority_score"],
                "recommended_status": row["recommended_status"],
                "flags": row["flags"],
                "candidate_ref": f"translation/candidate_index.jsonl#{row['logical_key']}",
            }
            for row in candidate_rows
            if queue in row["review_queues"]
        ]
        queue_rows.sort(key=lambda row: (-row["priority_score"], row["logical_key"]))
        write_jsonl(queue_root / f"{queue}.jsonl", queue_rows)
        queue_counts[queue] = len(queue_rows)
    for row in candidate_rows:
        if row["review_queues"]:
            combined_queue.append(
                {
                    "logical_key": row["logical_key"],
                    "queues": row["review_queues"],
                    "priority_score": row["priority_score"],
                    "recommended_status": row["recommended_status"],
                    "flags": row["flags"],
                    "candidate_ref": f"translation/candidate_index.jsonl#{row['logical_key']}",
                }
            )
    combined_queue.sort(key=lambda row: (-row["priority_score"], row["logical_key"]))
    write_jsonl(ROOT / "translation" / "review_queue.jsonl", combined_queue)
    write_jsonl(ROOT / "translation" / "runtime_observations.jsonl", runtime_observations())

    existing_issues = read_jsonl(ROOT / "translation" / "issues.jsonl")
    known_issue_ids = {row["id"] for row in existing_issues}
    merged_issues = existing_issues + [row for row in issue_additions() if row["id"] not in known_issue_ids]
    write_jsonl(ROOT / "translation" / "issues.jsonl", merged_issues)

    statuses = dict(sorted(collections.Counter(row["recommended_status"] for row in candidate_rows).items()))
    donor_candidates = sum(row["candidates"]["donor"]["is_translation_candidate"] for row in candidate_rows)
    pass_candidates = sum(row["candidates"]["pass_c"]["is_translation_candidate"] for row in candidate_rows)
    both = sum(
        row["candidates"]["donor"]["is_translation_candidate"]
        and row["candidates"]["pass_c"]["is_translation_candidate"]
        for row in candidate_rows
    )
    neither = sum(
        not row["candidates"]["donor"]["is_translation_candidate"]
        and not row["candidates"]["pass_c"]["is_translation_candidate"]
        for row in candidate_rows
    )
    semantic_risk = sum(
        "SEMANTIC_REVIEW_REQUIRED" in row["flags"] or "POSSIBLY_STALE" in row["flags"]
        for row in candidate_rows
    )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "result": "PASS",
        "phase": "HYBRID_MULTI_SOURCE_LOCALIZATION_BASE",
        "mode": "INDEX_AND_CANDIDATE_RESOLUTION_ONLY",
        "stable_baseline": {"name": "Pass C", "sha256": PASS_C_SHA},
        "sources": {
            "current_game": {"identity": f"upstream@{UPSTREAM_SHA}", "authority": "SEMANTIC_SOURCE_OF_TRUTH"},
            "project_approved": {"entries": len(approved_by_id), "authority": "HIGHEST_TRANSLATION_PRIORITY_IF_SOURCE_HASH_MATCHES"},
            "donor": {"identity": f"hon_ru_pack@{DONOR_COMMIT}", "approval": "CANDIDATE_ONLY"},
            "pass_c": {"identity": f"pass_c@{PASS_C_SHA}", "approval": "CANDIDATE_UNLESS_EXPLICITLY_APPROVED"},
        },
        "counts": {
            "current_keys": len(candidate_rows),
            "donor_candidates": donor_candidates,
            "pass_c_candidates": pass_candidates,
            "both_candidates": both,
            "neither_candidate": neither,
            "approved_existing": statuses.get("APPROVED_EXISTING", 0),
            "semantic_or_stale_risk": semantic_risk,
            "statuses": statuses,
            "review_queues": queue_counts,
            "combined_review_keys": len(combined_queue),
        },
        "resolution_rules": {
            "translation_priority": ["PROJECT_APPROVED", "DONOR", "PASS_C", "CURRENT_EN_FALLBACK", "FUTURE_MANUAL"],
            "semantic_authority": "CURRENT_GAME_SOURCE",
            "candidate_order_is_not_approval": True,
            "mechanic_text_requires_semantic_review": True,
            "approved_requires_current_source_hash_match": True,
        },
        "safety": {
            "game_archive_built": False,
            "game_pass_installed": False,
            "runtime_modified": False,
            "pass_d1_started": False,
        },
        "first_controlled_batch_recommendation": {
            "queue": "modern_ui",
            "size": "20-40 simple player-facing labels",
            "scope": "LEARN/profile/store/loading/Search Options labels confirmed in runtime; exclude entity/faction/ability names and mechanical prose.",
            "reason": "High visibility, weak donor coverage, low mechanic-staleness risk, and bounded runtime QA.",
        },
        "limitations": [
            "Candidate presence and structural compatibility do not prove semantic freshness or natural Russian.",
            "Current source hash is string-level evidence, not a full entity/gameplay data dependency graph.",
            "Modern UI detection is a deterministic review heuristic, not runtime reachability proof.",
            "Non-stringtable native UI, remote content, baked image text and debug UI are not fully represented in the key index.",
            "The game_menu root cause is a ranked hypothesis until a controlled locale/resource-loading trace is performed.",
        ],
    }
    write_json(ROOT / "translation" / "reports" / "hybrid_base_report.json", summary)

    game_menu_keys = [
        "interface:game_menu_menu_button",
        "interface:game_menu_options_button",
        "interface:game_menu_disconnect_button",
        "interface:game_menu_spec_button",
        "interface:game_menu_quit_button",
    ]
    evidence = []
    for logical_key in game_menu_keys:
        comparison = comparison_by_id.get(logical_key)
        if comparison:
            evidence.append(
                {
                    "logical_key": logical_key,
                    "current_exists": True,
                    "donor_exists": comparison.get("donor_value") is not None,
                    "pass_c_exists": comparison.get("pass_c_value") is not None,
                    "donor_hash": comparison.get("donor_sha256"),
                    "pass_c_hash": comparison.get("pass_c_sha256"),
                }
            )
    root_cause = {
        "result": "ROOT_CAUSE_CANDIDATE_ONLY",
        "observed": {"pass_c": "raw game_menu_* identifiers", "donor_test_0": "resolved labels"},
        "evidence": evidence,
        "key_count_in_all_three_sources": sum(
            row["logical_key"].startswith("interface:game_menu_")
            and row["candidates"]["donor"]["available"]
            and row["candidates"]["pass_c"]["available"]
            for row in candidate_rows
        ),
        "ruled_out_candidate": "Missing Pass C translations: the relevant keys and values exist in interface_ru data.",
        "leading_hypothesis": "The in-game menu path resolves the always-active English locale/resource table, while RU locale registration or this package's lookup path is incomplete/late for that UI path. DONOR TEST 0 overrides the active _en.str and therefore resolves it.",
        "alternatives": [
            "The menu package uses a hard-wired/default-locale lookup path for some labels.",
            "Load order or resource registration differs between core English and custom RU locale.",
        ],
        "required_next_evidence": "Controlled runtime trace comparing en/ru table registration and the exact menu package lookup; no runtime change was made in this phase.",
    }
    write_json(ROOT / "translation" / "reports" / "game_menu_root_cause_candidate.json", root_cause)

    lines = [
        "# Hybrid Multi-Source Localization Base",
        "",
        "> Architecture only: no translation batch, archive build, installation or runtime change.",
        "",
        "## Authority and candidate model",
        "",
        "Current game data is the semantic source of truth. Existing Russian text is indexed as a candidate from project-approved memory, pinned donor, or Pass C. Source order controls review presentation only; it never proves semantic correctness or approval.",
        "",
        "Approved project translations win only while their current source hash matches. Donor and Pass C remain candidates. Mechanically meaningful item, ability and boss text always carries semantic review flags.",
        "",
        "## Counts",
        "",
        f"- Current keys indexed: **{len(candidate_rows)}**",
        f"- Donor translation candidates: **{donor_candidates}**",
        f"- Pass C translation candidates: **{pass_candidates}**",
        f"- Keys with both candidates: **{both}**",
        f"- Keys with neither candidate: **{neither}**",
        f"- Explicitly approved and source-compatible: **{statuses.get('APPROVED_EXISTING', 0)}**",
        f"- Semantic/stale-risk keys: **{semantic_risk}**",
        "",
        "## Review queues",
        "",
        "| Queue | Keys | Purpose |",
        "|---|---:|---|",
    ]
    purposes = {
        "modern_ui": "Modern Reborn UI with weak donor coverage",
        "items_semantic": "Item mechanics validated against current game",
        "abilities_semantic": "Ability mechanics validated against current game",
        "bosses_semantic": "High stale-risk boss mechanics",
        "terminology": "Cross-game terms and forbidden forms",
        "mixed_language": "RU/EN mixed candidates",
        "structural_risk": "Placeholder/markup/number/control mismatches",
        "names_policy": "Ability/faction/boss/proper-name decisions",
    }
    for queue in QUEUE_NAMES:
        lines.append(f"| `{queue}` | {queue_counts[queue]} | {purposes[queue]} |")
    lines += [
        "",
        "## Runtime conclusions recorded",
        "",
        "DONOR TEST 0 confirms that donor text is valuable for legacy/gameplay wording and resolves the in-game menu labels, but has weak modern Reborn UI coverage. It also confirms mixed text, terminology conflicts, abbreviation style issues and material semantic-staleness risk. Good Russian wording is never treated as proof of current mechanics.",
        "",
        "## game_menu_* root-cause candidate",
        "",
        "Relevant labels exist in current English, donor English-locale overlay and Pass C Russian-locale data. This rules out a simple missing-value explanation. The leading candidate is a locale/resource registration or lookup-path difference: donor overrides the always-active `_en.str`, whereas the custom `_ru.str` path was not resolved by that menu at runtime. This remains a hypothesis pending a controlled trace.",
        "",
        "## Translation memory",
        "",
        "Candidate origin is separate from approval. Donor and Pass C records do not enter durable approved memory automatically. Only explicit project approval plus compatible current source hash can produce `APPROVED_EXISTING`.",
        "",
        "## Recommended first controlled batch",
        "",
        "Review 20–40 simple, high-visibility `modern_ui` labels confirmed by runtime (LEARN/profile/store/loading/Search Options areas). Exclude mechanics, ability/faction names and long prose. Do not start this batch automatically.",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in summary["limitations"])
    lines += ["", "**Pass D1 remains NOT STARTED.**", ""]
    (ROOT / "translation" / "reports" / "HYBRID_BASE_REPORT.md").write_text(
        "\n".join(lines), encoding="utf-8", newline="\n"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
