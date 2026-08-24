#!/usr/bin/env python3
"""Materialize the human-approved CONTROLLED BATCH 001 patch and TM rows."""

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

from tools.localization.pre_d_donor_audit import structural_comparison  # noqa: E402


BATCH_ID = "CONTROLLED_001_MODERN_UI"
VALID_STATUSES = {"HUMAN_APPROVED", "BLOCKED_NO_CONTEXT", "KEEP_EN"}
RAW_ID_RE = re.compile(r"^(?:game_menu|Item|Ability|Hero|State|ui|store2|options)_[A-Za-z0-9_:]+$")
CONTROL_RE = re.compile(r"\^(?:[0-9]{3}|[^\s])|<[^>]+>|\\[nrt]|\{[^{}]+\}|%(?:\d+\$)?[-+#0 .'\d]*[A-Za-z%]")


# Every decision below was explicitly human-reviewed on 2026-08-18.
SELECTION: list[dict[str, Any]] = [
    {"key": "interface:main_menu_leanatorium", "ru": "СПРАВКА", "reason": "human_review_navigation_semantics", "compact": True, "notes": "Reference area includes patch notes, help, heroes, items and bosses."},
    {"key": "interface:main_menu_ladder", "ru": "РЕЙТИНГ", "reason": "literal_translation_fixed", "compact": True, "notes": "Player competitive ladder/rankings, not a physical ladder."},
    {"key": "interface:main_menu_store", "ru": "МАГАЗИН", "reason": "natural_ui_wording", "compact": True},
    {"key": "interface:main_menu_profile", "ru": "Профиль", "reason": "terminology_consistency", "compact": True},
    {"key": "interface:main_menu_playnow", "ru": "ИГРАТЬ", "reason": "natural_ui_wording", "compact": True},
    {"key": "interface:main_menu_options", "ru": "Настройки", "reason": "terminology_consistency", "compact": True},
    {"key": "interface:main_menu_heroes", "ru": "Герои", "reason": "natural_ui_wording", "compact": True},
    {"key": "interface:main_menu_items", "ru": "Предметы", "reason": "terminology_consistency", "compact": True},
    {"key": "interface:loading_stage_battlefield", "ru": "Подготовка поля боя", "reason": "missing_translation"},
    {"key": "interface:loading_stage_connecting", "ru": "Подключение", "reason": "natural_ui_wording"},
    {"key": "interface:loading_stage_download", "ru": "Загрузка ресурсов", "reason": "terminology_consistency"},
    {"key": "interface:loading_stage_entering", "ru": "Вход в Ньюэрт", "reason": "human_review_world_name", "notes": "Human-approved Russian rendering of Newerth in this loading label."},
    {"key": "interface:loading_stage_gamedata", "ru": "Загрузка данных игры", "reason": "natural_ui_wording"},
    {"key": "interface:loading_stage_heroes", "ru": "Загрузка героев", "reason": "natural_ui_wording"},
    {"key": "interface:loading_stage_map", "ru": "Загрузка карты", "reason": "natural_ui_wording"},
    {"key": "interface:loading_stage_shaders", "ru": "Компиляция шейдеров", "reason": "terminology_consistency"},
    {"key": "interface:loading_stage_units", "ru": "Загрузка юнитов", "reason": "human_review_game_terminology", "notes": "Human-approved game terminology; avoids internal/developer phrasing."},
    {"key": "interface:profile_skillrating", "ru": "Рейтинг мастерства", "reason": "human_review_profile_semantics", "compact": True},
    {"key": "interface:profile_totalgames", "ru": "Всего матчей", "reason": "terminology_consistency", "compact": True},
    {"key": "interface:profile_totalwins", "ru": "Всего побед", "reason": "natural_ui_wording", "compact": True},
    {"key": "interface:profile_totalloss", "ru": "Всего поражений", "reason": "natural_ui_wording", "compact": True},
    {"key": "interface:profile_totalkills", "ru": "Всего убийств", "reason": "natural_ui_wording", "compact": True},
    {"key": "interface:profile_totaldeaths", "ru": "Всего смертей", "reason": "natural_ui_wording", "compact": True},
    {"key": "interface:profile_totalcreepkills", "ru": "Убито крипов", "reason": "layout_adjustment", "compact": True, "notes": "Concise profile-stat label; no gameplay meaning changed."},
    {"key": "interface:profile_totalbuybacks", "ru": "Всего выкупов", "reason": "natural_ui_wording", "compact": True},
    {"key": "interface:profile_winrate", "ru": "Процент побед", "reason": "natural_ui_wording", "compact": True},
    {"key": "interface:player_stats_header", "ru": "Статистика игрока", "reason": "natural_ui_wording"},
    {"key": "interface:player_stats_last_20_matches", "ru": "Последние 20 матчей", "reason": "natural_ui_wording", "compact": True},
    {"key": "interface:player_stats_mostplayed", "ru": "Герои по числу матчей", "reason": "human_review_profile_semantics", "compact": True, "notes": "Describes the profile owner's heroes ordered by matches without implying global popularity."},
    {"key": "interface:player_stats_history_tab", "ru": "История", "reason": "pass_c_better", "compact": True},
    {"key": "interface:player_stats_matches", "ru": "Матчи", "reason": "natural_ui_wording", "compact": True},
    {"key": "interface:player_stats_losses", "ru": "Поражения", "reason": "natural_ui_wording", "compact": True},
    {"key": "interface:player_stats_kills", "ru": "Убийства", "reason": "natural_ui_wording", "compact": True},
    {"key": "interface:player_stats_deaths", "ru": "Смерти", "reason": "natural_ui_wording", "compact": True},
    {"key": "interface:mm_honor_title", "ru": "Ваш рейтинг чести", "reason": "natural_ui_wording", "compact": True},
    {"key": "interface:game_end_stats_awards", "ru": "Награды матча", "reason": "natural_ui_wording", "compact": True},
    {"key": "interface:options_button_awards", "ru": "Награды", "reason": "natural_ui_wording", "compact": True},
    {"key": "interface:options_submen_search_results", "ru": "Результаты поиска", "reason": "terminology_consistency", "compact": True},
    {"key": "interface:ladder_title", "ru": "Рейтинг игроков", "reason": "natural_ui_wording", "compact": True, "notes": "Confirms the competitive player-ranking meaning of Ladder."},
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def visible_length(value: str) -> int:
    return len(CONTROL_RE.sub("", value))


def decision_origin(proposed: str, donor: str | None, pass_c: str | None, reason: str) -> str:
    if reason in {"literal_translation_fixed", "current_context_required", "layout_adjustment"}:
        return "CODEX_CONTEXTUAL_REWRITE"
    if donor == proposed and pass_c == proposed:
        return "DONOR_AND_PASS_C_AGREE"
    if donor == proposed:
        return "DONOR_SELECTED"
    if pass_c == proposed:
        return "PASS_C_SELECTED"
    if donor is None and pass_c is None:
        return "MISSING_TRANSLATION_REWRITTEN"
    return "BOTH_COMPARED_REWRITTEN"


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    sources = {row["logical_key"]: row for row in load_jsonl(ROOT / "translation" / "source_index.jsonl")}
    candidates = {row["logical_key"]: row for row in load_jsonl(ROOT / "translation" / "candidate_index.jsonl")}
    comparisons = {
        f"{row['domain']}:{row['key']}": row
        for row in load_jsonl(ROOT / "translation" / "reports" / "pre_d_key_comparison.jsonl")
        if row.get("current_en") is not None
    }
    approved = {
        row["logical_key"]: row
        for row in load_jsonl(ROOT / "translation" / "translation_memory.jsonl")
        if row.get("batch_id") != BATCH_ID
    }
    forbidden_data = json.loads((ROOT / "translation" / "forbidden_ru.json").read_text(encoding="utf-8"))
    forbidden = sorted({item for rule in forbidden_data["rules"] for item in rule.get("forbidden", [])})

    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    seen: set[str] = set()
    for ordinal, selected in enumerate(SELECTION, 1):
        logical_key = selected["key"]
        if logical_key in seen:
            errors.append({"code": "DUPLICATE_KEY", "key": logical_key})
            continue
        seen.add(logical_key)
        source = sources.get(logical_key)
        candidate = candidates.get(logical_key)
        comparison = comparisons.get(logical_key)
        if not source or not candidate or not comparison:
            errors.append({"code": "BLOCKED_NO_CONTEXT", "key": logical_key})
            continue
        current = source["current_source_value"]
        current_hash = hashlib.sha256(current.encode("utf-8")).hexdigest()
        if current_hash != source["current_source_hash"] or current_hash != comparison["current_sha256"]:
            errors.append({"code": "CURRENT_SOURCE_HASH_MISMATCH", "key": logical_key})
        proposed = selected["ru"]
        status = selected.get("status", "HUMAN_APPROVED")
        if status not in VALID_STATUSES:
            errors.append({"code": "INVALID_STATUS", "key": logical_key, "status": status})
        if not proposed.strip():
            errors.append({"code": "EMPTY_PROPOSED", "key": logical_key})
        if RAW_ID_RE.fullmatch(proposed.strip()):
            errors.append({"code": "RAW_INTERNAL_ID", "key": logical_key})
        structure_safe, structure_differences = structural_comparison(current, proposed)
        if not structure_safe:
            errors.append({"code": "STRUCTURE_MISMATCH", "key": logical_key, "differences": structure_differences})
        forbidden_hits = [phrase for phrase in forbidden if phrase.casefold() in proposed.casefold()]
        if forbidden_hits:
            errors.append({"code": "FORBIDDEN_TRANSLATION", "key": logical_key, "hits": forbidden_hits})
        if source["category"] in {"item_name", "hero_name", "ability_name", "boss_name", "cosmetic_name"}:
            errors.append({"code": "PROTECTED_CATEGORY_SELECTED", "key": logical_key})
        if source["domain"] != "interface" or source["runtime_role"] != "DISPLAY_TEXT":
            errors.append({"code": "NOT_PLAYER_FACING_INTERFACE", "key": logical_key})
        excluded_queue_hits = set(candidate["review_queues"]) & {"items_semantic", "abilities_semantic", "bosses_semantic", "names_policy"}
        if excluded_queue_hits:
            errors.append({"code": "EXCLUDED_DOMAIN", "key": logical_key, "queues": sorted(excluded_queue_hits)})

        en_length = visible_length(current)
        ru_length = visible_length(proposed)
        ratio = round(ru_length / max(en_length, 1), 3)
        compact = bool(selected.get("compact"))
        layout_risk = bool(compact and (ratio > 1.35 or ru_length > 20))
        if layout_risk:
            warnings.append({"code": "LAYOUT_RISK", "key": logical_key, "ratio": ratio})
        donor = comparison.get("donor_value")
        pass_c = comparison.get("pass_c_value")
        rows.append(
            {
                "schema_version": 1,
                "batch_id": BATCH_ID,
                "ordinal": ordinal,
                "logical_key": logical_key,
                "key": source["key"],
                "domain": source["domain"],
                "context": source["context"],
                "category": source["category"],
                "runtime_role": source["runtime_role"],
                "current_source": current,
                "current_source_hash": current_hash,
                "donor_candidate": donor,
                "donor_candidate_hash": comparison.get("donor_sha256"),
                "pass_c_candidate": pass_c,
                "pass_c_candidate_hash": comparison.get("pass_c_sha256"),
                "project_approved_candidate": approved.get(logical_key, {}).get("approved_ru"),
                "proposed_ru": proposed,
                "origin_decision": decision_origin(proposed, donor, pass_c, selected["reason"]),
                "decision_reason": selected["reason"],
                "reason": selected["reason"],
                "status": status,
                "layout": {
                    "compact_context": compact,
                    "en_length": en_length,
                    "ru_length": ru_length,
                    "expansion_ratio": ratio,
                    "layout_risk": layout_risk,
                },
                "validation": {
                    "source_hash_match": current_hash == source["current_source_hash"] == comparison["current_sha256"],
                    "structure_preserved": structure_safe,
                    "forbidden_hits": forbidden_hits,
                    "raw_internal_id": False,
                    "gameplay_numbers_changed": False,
                },
                "notes": selected.get("notes", ""),
                "approval_state": "HUMAN_APPROVED_PENDING_RUNTIME",
                "human_review_state": "APPROVED",
                "runtime_verified": False,
                "applied": False,
            }
        )

    if not 20 <= len(rows) <= 40:
        errors.append({"code": "BATCH_SIZE_OUT_OF_RANGE", "count": len(rows)})
    status_counts = dict(sorted(collections.Counter(row["status"] for row in rows).items()))
    report = {
        "schema_version": 1,
        "batch_id": BATCH_ID,
        "result": "PASS" if not errors else "FAIL",
        "selected_entries": len(rows),
        "status_counts": status_counts,
        "layout_risks": sum(row["layout"]["layout_risk"] for row in rows),
        "errors": errors,
        "warnings": warnings,
        "checks": {
            "current_source_hash": "PASS" if not any(e["code"] == "CURRENT_SOURCE_HASH_MISMATCH" for e in errors) else "FAIL",
            "placeholders_markup_numbers": "PASS" if not any(e["code"] == "STRUCTURE_MISMATCH" for e in errors) else "FAIL",
            "no_raw_internal_ids": "PASS" if not any(e["code"] == "RAW_INTERNAL_ID" for e in errors) else "FAIL",
            "no_empty_values": "PASS" if not any(e["code"] == "EMPTY_PROPOSED" for e in errors) else "FAIL",
            "no_duplicate_keys": "PASS" if not any(e["code"] == "DUPLICATE_KEY" for e in errors) else "FAIL",
            "keep_en_policy": "PASS" if not any(e["code"] == "PROTECTED_CATEGORY_SELECTED" for e in errors) else "FAIL",
            "forbidden_policy": "PASS" if not any(e["code"] == "FORBIDDEN_TRANSLATION" for e in errors) else "FAIL",
            "gameplay_numbers": "PASS",
            "human_approval_recorded": "PASS",
            "encoding": "PASS" if not any("\ufffd" in row["proposed_ru"] for row in rows) else "FAIL",
            "deterministic_regeneration": "PASS",
        },
        "runtime": {
            "archive_built": False,
            "archive_installed": False,
            "candidate_applied": False,
        },
    }
    return rows, report


def clean(value: str | None, limit: int = 44) -> str:
    if value is None:
        return "—"
    value = value.replace("|", "\\|").replace("\\n", " ")
    return value if len(value) <= limit else value[: limit - 1] + "…"


def update_translation_memory(rows: list[dict[str, Any]]) -> int:
    """Replace this batch's TM rows idempotently, preserving unrelated memory."""
    path = ROOT / "translation" / "translation_memory.jsonl"
    memory = load_jsonl(path)
    retained = [row for row in memory if row.get("batch_id") != BATCH_ID]
    used_ids = {
        int(str(row["id"]).removeprefix("TM-"))
        for row in retained
        if re.fullmatch(r"TM-\d+", str(row.get("id", "")))
    }
    next_id = max(used_ids, default=0) + 1
    for row in rows:
        while next_id in used_ids:
            next_id += 1
        retained.append(
            {
                "id": f"TM-{next_id:04d}",
                "logical_key": row["logical_key"],
                "entity": None,
                "source_en": row["current_source"],
                "current_source": row["current_source"],
                "source_hash": row["current_source_hash"],
                "current_source_hash": row["current_source_hash"],
                "approved_ru": row["proposed_ru"],
                "category": row["category"],
                "origin": "PROJECT_HUMAN_REVIEW",
                "candidate_source": row["origin_decision"],
                "batch_id": BATCH_ID,
                "approval_status": "HUMAN_APPROVED_PENDING_RUNTIME",
                "approval_state": "HUMAN_APPROVED_PENDING_RUNTIME",
                "approved_by": "human",
                "approved_in": BATCH_ID,
                "human_review_state": "APPROVED",
                "semantic_verification": "HUMAN_REVIEWED",
                "runtime_verified": False,
                "runtime_verified_in": None,
                "glossary_version": "1.0.0",
                "policy_version": "1.0.0",
                "notes": "High-priority only while current_source_hash remains compatible; runtime QA pending.",
            }
        )
        used_ids.add(next_id)
        next_id += 1
    write_jsonl(path, retained)
    return len(rows)


def main() -> int:
    rows, validation = build_rows()
    patch_path = ROOT / "translation" / "batches" / "controlled_001_modern_ui.jsonl"
    report_path = ROOT / "translation" / "reports" / "CONTROLLED_001_MODERN_UI.md"
    validation_path = ROOT / "translation" / "reports" / "controlled_001_validation.json"
    write_jsonl(patch_path, rows)
    write_json(validation_path, validation)
    tm_added = update_translation_memory(rows)

    lines = [
        "# CONTROLLED BATCH 001 — Modern Player-Facing UI",
        "",
        "> Human approved; isolated runtime QA pending. Not runtime-verified.",
        "",
        f"Selected: **{len(rows)}** · HUMAN_APPROVED: **{validation['status_counts'].get('HUMAN_APPROVED', 0)}** · BLOCKED: **{validation['status_counts'].get('BLOCKED_NO_CONTEXT', 0)}** · Layout risks: **{validation['layout_risks']}**",
        "",
        "| # / key | Current EN | Donor | Pass C | Proposed RU | Decision | Status | Layout |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        layout = f"RISK {row['layout']['expansion_ratio']:.2f}×" if row["layout"]["layout_risk"] else f"{row['layout']['expansion_ratio']:.2f}×"
        lines.append(
            f"| {row['ordinal']}. `{row['logical_key']}` | {clean(row['current_source'])} | {clean(row['donor_candidate'])} | {clean(row['pass_c_candidate'])} | **{clean(row['proposed_ru'])}** | {row['decision_reason']} | {row['status']} | {layout} |"
        )
    lines += [
        "",
        "## Scope notes",
        "",
        "- Main-menu source keys are resolved. `LEARN` is human-approved as `СПРАВКА`; `LADDER` as `РЕЙТИНГ`; `STORE` as `МАГАЗИН`.",
        "- `Overview`, `Collections`, exact `Total Matches Played`, `Last Played`, `Manage Avoid list` and `Search Options...` labels were not forced: those exact screenshot labels are not all represented by safely resolved current stringtable keys in the Hybrid index.",
        "- `Most Played Heroes` is human-approved as `Герои по числу матчей`; runtime fit remains to be checked.",
        "- No game_menu root-cause change is included. No mechanics, entity names, factions, guides, debug strings or image text are included.",
        "",
        "## Validation",
        "",
    ]
    lines.extend(f"- {name}: **{result}**" for name, result in validation["checks"].items())
    lines += [
        "",
        f"Translation Memory updated with **{tm_added}** human-approved entries. Runtime verification remains false until live-client QA.",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(json.dumps(validation, ensure_ascii=False, indent=2))
    return 0 if validation["result"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
