#!/usr/bin/env python3
"""Final Phase 1.6 policy pass over read-only discovery catalogs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


HON_CONTROL_RE = re.compile(r"\^(?:[0-9]{3}|[^\s])")
HTML_TAG_RE = re.compile(r"<[^<>\r\n]+>")
STRUCTURAL_ESCAPE_RE = re.compile(r"^(?:\\[rnt])+$")
NAME_FIELD_RE = re.compile(r"(?:^|_)(?:name|displayname|display_name)(?::[^:]*)?$", re.I)
LETTER_RE = re.compile(r"[A-Za-z]")


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def visible_text_with_map(source: str) -> tuple[str, list[int]]:
    """Return visible text and a visible-character -> source-offset map."""
    visible: list[str] = []
    offsets: list[int] = []
    cursor = 0
    while cursor < len(source):
        control = HON_CONTROL_RE.match(source, cursor)
        tag = HTML_TAG_RE.match(source, cursor)
        skipped = control or tag
        if skipped:
            cursor = skipped.end()
            continue
        visible.append(source[cursor])
        offsets.append(cursor)
        cursor += 1
    return "".join(visible), offsets


def visible_text(source: str) -> str:
    return visible_text_with_map(source)[0]


def normalized_visible(source: str) -> str:
    return re.sub(r"\s+", " ", visible_text(source)).strip(" *\t\r\n")


def load_token_policy(path: Path) -> dict:
    policy = json.loads(path.read_text(encoding="utf-8"))
    policy["_keycap_regexes"] = [re.compile(value, re.I) for value in policy.get("keycap_patterns", [])]
    return policy


def technical_kind(value: str, policy: dict) -> str | None:
    value = normalized_visible(value)
    unpunctuated = value.rstrip(":")
    if unpunctuated != value:
        value = unpunctuated
    slash_parts = value.split("/")
    if len(slash_parts) > 1 and all(part in policy["stat_abbreviations"] for part in slash_parts):
        return "stat_abbreviation"
    if value.casefold() in {token.casefold() for token in policy["keycaps"]} or any(pattern.fullmatch(value) for pattern in policy["_keycap_regexes"]):
        return "keycap"
    for key, category in (
        ("stat_abbreviations", "stat_abbreviation"),
        ("technical_abbreviations", "technical_abbreviation"),
        ("region_codes", "region_code"),
        ("currency_codes", "currency_code"),
    ):
        if value.casefold() in {token.casefold() for token in policy[key]}:
            return category
    return None


def nontext_kind(value: str) -> str | None:
    if not value or STRUCTURAL_ESCAPE_RE.fullmatch(value.strip()):
        return None
    visible = visible_text(value).strip()
    if LETTER_RE.search(visible):
        return None
    if not visible and HON_CONTROL_RE.search(value):
        return "markup_only"
    if re.fullmatch(r"[+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+)%?", visible):
        return "number"
    if re.fullmatch(r"[-+/,.;:!?_'\"()[\]{}]+", visible):
        return "punctuation"
    if visible:
        return "symbol"
    return "structural_value"


def canonical_entry(text: str, entity_type: str, row: dict, strength: str = "EXACT") -> dict:
    return {
        "canonical_text": normalized_visible(text),
        "type": entity_type,
        "source_key": row.get("key", ""),
        "source_file": row.get("source_file", ""),
        "aliases": [],
        "case_policy": "EXACT",
        "protection_policy": "IMMUTABLE_VISIBLE_TEXT",
        "protection_strength": strength,
    }


def unique_dictionary(entries: list[dict]) -> list[dict]:
    result: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for entry in entries:
        marker = (entry["type"], entry["canonical_text"], entry["source_key"])
        if not entry["canonical_text"] or marker in seen:
            continue
        seen.add(marker)
        result.append(entry)
    return sorted(result, key=lambda row: (row["canonical_text"].casefold(), row["source_key"]))


def build_canonical_dictionary(rows: list[dict], token_policy: dict) -> dict[str, list[dict]]:
    dictionary: dict[str, list[dict]] = {
        "heroes": [], "abilities": [], "items": [], "bosses": [],
        "avatars_cosmetics": [], "announcer_events": [], "technical_tokens": [],
    }
    common_contextual = {"Victory", "Defeat", "Immortal", "Nemesis", "Payback", "Sear", "Slam", "Rush", "Borrow"}
    for row in rows:
        key = row["key"]
        text = normalized_visible(row["english"])
        if not text:
            continue
        if re.match(r"^Hero_", key, re.I) and NAME_FIELD_RE.search(key):
            dictionary["heroes"].append(canonical_entry(text, "HERO", row, "EXACT"))
        elif re.match(r"^Ability_", key, re.I) and NAME_FIELD_RE.search(key):
            strength = "CONTEXTUAL" if text in common_contextual or " " not in text else "EXACT"
            dictionary["abilities"].append(canonical_entry(text, "ABILITY", row, strength))
        elif re.match(r"^Item_", key, re.I) and NAME_FIELD_RE.search(key):
            strength = "CONTEXTUAL" if text in common_contextual or " " not in text else "EXACT"
            dictionary["items"].append(canonical_entry(text, "ITEM", row, strength))
        elif key in {"Neutral_Kongor_name", "Neutral_PhoenixBoss_name"}:
            dictionary["bosses"].append(canonical_entry(text, "BOSS", row, "EXACT"))
        elif re.match(r"^Pet_.*_name:C_", key, re.I):
            dictionary["avatars_cosmetics"].append(canonical_entry(text, "COSMETIC", row, "EXACT"))
        elif row["namespace"] == "interface" and re.fullmatch(r"announcement_[a-z0-9_]+", key, re.I):
            strength = "CONTEXTUAL" if text in common_contextual else "EXACT"
            dictionary["announcer_events"].append(canonical_entry(text, "ANNOUNCER_EVENT", row, strength))
    synthetic = {"key": "catalog/technical_tokens.json", "source_file": "catalog/technical_tokens.json"}
    for group, entity_type in (
        ("stat_abbreviations", "STAT_ABBREVIATION"),
        ("technical_abbreviations", "TECH_ABBREVIATION"),
        ("region_codes", "REGION_CODE"),
        ("currency_codes", "CURRENCY_CODE"),
        ("keycaps", "KEYCAP"),
    ):
        for text in token_policy[group]:
            dictionary["technical_tokens"].append(canonical_entry(text, entity_type, synthetic, "EXACT"))
    announcer_aliases = {
        "Double Tap": ["Double Taps"], "Smackdown": ["Smackdowns"],
        "Annihilation": ["Annihilations"], "Humiliation": ["Humiliations"],
        "Quad Kill": ["Quad Kills"],
    }
    for entry in dictionary["announcer_events"]:
        entry["aliases"] = announcer_aliases.get(entry["canonical_text"], [])
    popup = next((row for row in rows if row.get("key") == "Popup_EmeraldWarden1"), None)
    if popup:
        for text, entity_type in (("Gawain", "GAMEPLAY_ENTITY"), ("Diving Strike", "ABILITY"),
                                  ("Forest's Touch", "ABILITY"), ("Emerald Storm", "ABILITY")):
            dictionary["abilities"].append(canonical_entry(text, entity_type, popup, "EXACT"))
    return {key: unique_dictionary(value) for key, value in dictionary.items()}


def true_ability_texts(dictionary: dict[str, list[dict]]) -> set[str]:
    return {entry["canonical_text"] for entry in dictionary["abilities"]}


def classify_game_message(key: str, english: str) -> tuple[str, str, str]:
    low = key.lower()
    if normalized_visible(english).lower() in {"not used.", "unused", "none"} and "weather" not in low:
        return "REVIEW", "game_message_legacy", "Legacy/unused marker; runtime relevance unresolved"
    combat_feed = {
        "teamkillstreak", "teamwipe", "humiliation", "rival", "payback",
        "teamkill", "neutralkill", "kongorkill", "bosskill", "suicide", "kill",
        "neutral_killboard", "team_killboard",
    }
    leave_feed = {
        "client_reconnected", "client_disconnected", "client_timedout", "client_terminated",
        "lobby_disconnect", "user_left_game_lobby_aborted", "player_left_game_lobby_aborted",
    }
    if (low in combat_feed or low in leave_feed or low.startswith("pre_firstblood_reconnect_")
            or re.match(r"^(?:deny|kill[0-9]+|first_kill|killstreak|streakend|multikill)", low)):
        return "KEEP_EN", "announcer_event", "Branded announcer/combat callout identity"
    if low.startswith("vanity_msg_"):
        return "KEEP_EN", "branded_vanity_callout", "Cosmetic vanity message is tied to its selected product/voice identity"
    if any(token in low for token in ("announcer", "smackdown", "bloodlust_callout")):
        return "KEEP_EN", "announcer_event", "Explicit announcer identity context"
    if low.startswith("ping_"):
        return "TRANSLATE", "game_ping", "Functional text ping/team communication; dynamic entity names remain placeholders"
    return "TRANSLATE", "game_system_message", "Functional gameplay/system message without branded announcer identity"


def apply_catalog_policy(rows: list[dict], token_policy: dict) -> tuple[dict[str, list[dict]], list[dict]]:
    # First pass establishes unambiguous whole-value and source-resource roles.
    for row in rows:
        row["locked_spans"] = []
        row["classification_version"] = 3
        namespace, key, english = row["namespace"], row["key"], row["english"]
        if namespace == "interface_test_suite":
            row.update(category="test_suite", context="Developer/test stringtable excluded from release workload", status="KEEP_EN", runtime_role="DEV_TEST", protected_reason="English test corpus copy")
            row["russian"] = english
            continue
        kind = nontext_kind(english)
        if kind:
            row.update(category=kind, context="Non-linguistic runtime value copied exactly", status="KEEP_EN", runtime_role="TECHNICAL_COPY", protected_reason="Non-text value copied exactly")
            row["russian"] = english
            continue
        tech = technical_kind(english, token_policy)
        if tech:
            role = "KEYCAP" if tech == "keycap" else "TECHNICAL_COPY"
            row.update(category=tech, context="Controlled technical-token policy", status="KEEP_EN", runtime_role=role, protected_reason=f"{tech} remains English")
            row["russian"] = english
            continue
        if namespace == "game_messages":
            status, category, reason = classify_game_message(key, english)
            row.update(category=category, context=reason, status=status, runtime_role="DISPLAY_TEXT", protected_reason=reason if status == "KEEP_EN" else "")
            row["russian"] = english if status == "KEEP_EN" else ""
        if re.match(r"^Pet_.*_name:C_", key, re.I):
            row.update(category="cosmetic_name", context="Courier cosmetic variant from structured :C_ product grammar", status="KEEP_EN", runtime_role="DISPLAY_TEXT", protected_reason="Cosmetic product names stay English")
            row["russian"] = english
        if key in {"Neutral_Kongor_name", "Neutral_PhoenixBoss_name", "tpp_kongor"} or re.fullmatch(r"boss_info_(?:kongor|phoenix)_name", key, re.I):
            row.update(category="boss_name", context="Canonical boss proper name", status="KEEP_EN", runtime_role="DISPLAY_TEXT", protected_reason="Boss proper names stay English")
            row["russian"] = english
        if re.fullmatch(r"boss_info_(?:kongor|phoenix)_ability\d+_name", key, re.I):
            row.update(category="boss_ability_name", context="Canonical boss ability name", status="KEEP_EN", runtime_role="DISPLAY_TEXT", protected_reason="Ability names stay English")
            row["russian"] = english

    dictionary = build_canonical_dictionary(rows, token_policy)
    ability_texts = true_ability_texts(dictionary)
    item_texts = {entry["canonical_text"] for entry in dictionary["items"]}
    state_rows: list[dict] = []
    for row in rows:
        key = row["key"]
        if not key.lower().startswith("state_"):
            continue
        state_rows.append(row)
        english = row["english"]
        if not english:
            continue
        if row["runtime_role"] in {"STRUCTURAL", "TECHNICAL_COPY", "RESOURCE_PATH"}:
            if row["runtime_role"] == "RESOURCE_PATH":
                row["category"] = "state_visual_internal"
            continue
        key_low = key.lower()
        text = normalized_visible(english)
        if "_ability" in key_low and text in ability_texts:
            row.update(category="state_source_ability_reference", context="State field exactly references a canonical Ability_* name", status="KEEP_EN", runtime_role="DISPLAY_TEXT", protected_reason="Canonical ability reference stays English", russian=english)
        elif NAME_FIELD_RE.search(key) and text in item_texts:
            row.update(category="state_source_item_reference", context="State label exactly references a canonical Item_* name", status="KEEP_EN", runtime_role="DISPLAY_TEXT", protected_reason="Canonical item reference stays English", russian=english)
        elif NAME_FIELD_RE.search(key):
            if "visual" in key_low:
                row.update(category="state_visual_internal", context="State visual/internal name; runtime display not proven", status="REVIEW", runtime_role="INTERNAL_ID", protected_reason="", russian="")
            else:
                row.update(category="state_status_label", context="User-visible gameplay state/status label", status="TRANSLATE", runtime_role="DISPLAY_TEXT", protected_reason="", russian="")
        elif any(token in key_low for token in ("description", "_effect", "tooltip", "_desc")):
            row.update(category="state_effect_description", context="User-visible state/effect explanation", status="TRANSLATE", runtime_role="DISPLAY_TEXT", protected_reason="", russian="")
        else:
            row.update(category="state_internal", context="State field without proven display semantics", status="REVIEW", runtime_role="INTERNAL_ID", protected_reason="", russian="")

    # The old substring cosmetic rules must not survive the state pass.
    for row in rows:
        if row["key"] == "store2_altavatars_default_name":
            row.update(category="functional_ui", context="Generic store UI option, not a cosmetic product name", status="TRANSLATE", runtime_role="DISPLAY_TEXT", protected_reason="", russian="")
        if (row.get("category") == "ability_description" and row.get("status") == "REVIEW"
                and not row.get("russian") and "English changed" in row.get("notes", "")):
            row.update(status="TRANSLATE", protected_reason="")
            row["notes"] = "English changed before translation; current classification retained"
        text = normalized_visible(row["english"])
        if re.match(r"^Ability_.*_effect_header", row["key"], re.I) and text in ability_texts:
            row.update(category="ability_name", context="Effect header exactly repeats the canonical ability name", status="KEEP_EN", runtime_role="DISPLAY_TEXT", protected_reason="Ability names stay English", russian=row["english"])
        if re.fullmatch(r"boss_info_(?:kongor|phoenix)_reward\d+_name", row["key"], re.I) and text in item_texts:
            row.update(category="item_name", context="Boss reward label exactly repeats a canonical item name", status="KEEP_EN", runtime_role="DISPLAY_TEXT", protected_reason="Item names stay English", russian=row["english"])
        if re.fullmatch(r"player_stats_(?:bloodlust|doubletap|hattrick|quadkill|annihilated|humiliated|retribution|smackdown|nemesis|payback|immortal)", row["key"], re.I):
            row.update(category="announcer_event", context="Announcer event identity shown in player statistics", status="KEEP_EN", runtime_role="DISPLAY_TEXT", protected_reason="Announcer event identities stay English", russian=row["english"])
        if row["key"] == "Popup_deny":
            row.update(category="announcer_event", context="Announcer-synchronized Denied callout", status="KEEP_EN", runtime_role="DISPLAY_TEXT", protected_reason="Announcer event identity stays English", russian=row["english"])
        if row["key"] in {"Roast_MMRBurglar_name", "Roast_MMRCalculator_name"}:
            row.update(category="cosmetic_name", context="Roast cosmetic/product display name", status="KEEP_EN", runtime_role="DISPLAY_TEXT", protected_reason="Cosmetic product names stay English", russian=row["english"])
        if row["key"] == "ImmunityType_BarrierImmunity":
            row.update(category="gameplay_status", context="Functional immunity label with protected item name", status="TRANSLATE", runtime_role="DISPLAY_TEXT", protected_reason="", russian="")
        if row["key"].startswith("Popup_EmeraldWarden"):
            row.update(category="gameplay_notification", context="Functional popup wrapper with protected gameplay entities", status="TRANSLATE", runtime_role="DISPLAY_TEXT", protected_reason="", russian="")
        if row["key"] == "Pet_KongorSummon_name":
            row.update(category="unit_name", context="Named summoned gameplay unit", status="KEEP_EN", runtime_role="DISPLAY_TEXT", protected_reason="Gameplay unit names stay English", russian=row["english"])
        if row["key"] == "Option_RapidFire":
            row.update(category="game_mode_option", context="Blitz Mode option; not a reference to Hero Blitz", status="TRANSLATE", runtime_role="DISPLAY_TEXT", protected_reason="", russian="")
    dictionary = build_canonical_dictionary(rows, token_policy)
    return dictionary, state_rows


def entity_owner(key: str) -> str:
    match = re.match(r"^(?:Hero|Ability|Item|State)_([^_:]+)", key, re.I)
    if not match:
        return ""
    owner = re.sub(r"\d+[a-z]?$", "", match.group(1), flags=re.I)
    return owner.casefold()


def flatten_dictionary(dictionary: dict[str, list[dict]]) -> list[dict]:
    flattened = []
    for group in dictionary.values():
        for entry in group:
            flattened.append(entry)
            for alias in entry.get("aliases", []):
                alias_entry = dict(entry)
                alias_entry["canonical_text"] = alias
                alias_entry["alias_of"] = entry["canonical_text"]
                alias_entry["aliases"] = []
                flattened.append(alias_entry)
    return flattened


def match_allowed(row: dict, entry: dict) -> bool:
    term = entry["canonical_text"]
    strength = entry["protection_strength"]
    if strength == "DISABLED_INLINE":
        return False
    if strength == "EXACT":
        return True
    if entry["type"] in {"TECH_ABBREVIATION", "STAT_ABBREVIATION", "REGION_CODE", "CURRENCY_CODE", "KEYCAP"}:
        return True
    if entry["type"] == "ANNOUNCER_EVENT":
        return row["category"] in {"announcer_event", "branded_vanity_callout"} or term not in {"Victory", "Immortal", "Nemesis", "Payback"}
    row_key = row.get("key", row.get("id", ""))
    return bool(entity_owner(row_key) and entity_owner(row_key) in entry["source_key"].casefold())


def adjacent_markup(source: str, start: int, end: int) -> tuple[str, str]:
    prefix_match = re.search(r"(?:\^(?:[0-9]{3}|[^\s]))+$", source[:start])
    suffix_match = re.match(r"(?:\^(?:[0-9]{3}|[^\s]))+", source[end:])
    return (prefix_match.group(0) if prefix_match else "", suffix_match.group(0) if suffix_match else "")


def assign_locked_spans(rows: list[dict], dictionary: dict[str, list[dict]]) -> None:
    entries_by_text: dict[str, list[dict]] = defaultdict(list)
    for entry in flatten_dictionary(dictionary):
        entries_by_text[entry["canonical_text"]].append(entry)
    alternatives = sorted(entries_by_text, key=lambda text: (-len(text), text.casefold()))
    matcher = re.compile("|".join(re.escape(text) for text in alternatives)) if alternatives else None
    for row in rows:
        row["protected_terms"] = []
        row["locked_spans"] = []
        if not matcher or row["runtime_role"] not in {"DISPLAY_TEXT", "KEYCAP", "TECHNICAL_COPY"} or row["status"] in {"DEPRECATED", "DYNAMIC"}:
            continue
        if row["status"] == "KEEP_EN":
            continue
        visible, offsets = visible_text_with_map(row["english"])
        occupied: list[tuple[int, int]] = []
        for match in matcher.finditer(visible):
            start, end = match.span()
            if any(not (end <= old_start or start >= old_end) for old_start, old_end in occupied):
                continue
            left = visible[start - 1] if start else ""
            right = visible[end] if end < len(visible) else ""
            if (left and left.isalnum()) or (right and right.isalnum()):
                continue
            entry = next((candidate for candidate in entries_by_text[match.group(0)] if match_allowed(row, candidate)), None)
            if not entry:
                continue
            # A whole-value generic label/status is not converted into a locked
            # entity merely because an entity happens to share the same words.
            if normalized_visible(row["english"]) == entry["canonical_text"]:
                continue
            source_start, source_end = offsets[start], offsets[end - 1] + 1
            prefix, suffix = adjacent_markup(row["english"], source_start, source_end)
            span = {
                "canonical_text": entry["canonical_text"], "type": entry["type"],
                "source_start": source_start, "source_end": source_end,
                "visible_start": start, "visible_end": end,
                "case_policy": entry["case_policy"],
                "markup_prefix": prefix, "markup_suffix": suffix,
            }
            row["locked_spans"].append(span)
            row["protected_terms"].append(entry["canonical_text"])
            occupied.append((start, end))
        row["protected_terms"] = list(dict.fromkeys(row["protected_terms"]))


def phase15_rows(bundle: Path | None) -> list[dict]:
    if not bundle or not bundle.is_file():
        return []
    with zipfile.ZipFile(bundle) as zf:
        return [json.loads(line) for line in zf.read("catalog/strings.jsonl").decode("utf-8-sig").splitlines() if line.strip()]


def state_protection_audit(old_rows: list[dict], new_rows: list[dict]) -> list[dict]:
    old_by_id = {row["id"]: row for row in old_rows}
    state_terms = {
        normalized_visible(row["english"]) for row in old_rows
        if row["key"].lower().startswith("state_") and row.get("category") == "ability_name"
    }
    true_terms = {
        normalized_visible(row["english"]) for row in old_rows
        if re.match(r"^(?:Hero|Ability|Item)_", row["key"], re.I) and row.get("category") in {"hero_name", "ability_name", "item_name"}
    }
    only_state = state_terms - true_terms
    audit: list[dict] = []
    for row in new_rows:
        old = old_by_id.get(row["id"])
        if not old:
            continue
        old_terms = old.get("protected_terms", [])
        implicated = [term for term in old_terms if normalized_visible(term) in only_state]
        if not implicated:
            continue
        new_terms = row.get("protected_terms", [])
        removed = [term for term in implicated if term not in new_terms]
        decision = "REMOVE_FALSE_STATE_LOCK" if removed else "RETAIN_FROM_TRUE_CANONICAL_SOURCE"
        audit.append({
            "key": row["key"], "english": row["english"],
            "old_protected_terms": old_terms, "new_protected_terms": new_terms,
            "decision": decision,
            "reason": "State_* is not a canonical Ability source" if removed else "Term is also backed by a true canonical entity",
        })
    return audit


def classify_native(candidates: list[dict], catalog: list[dict], token_policy: dict) -> list[dict]:
    exact: dict[str, list[dict]] = defaultdict(list)
    for row in catalog:
        exact[normalized_visible(row["english"])].append(row)
    result: list[dict] = []
    for index, candidate in enumerate(candidates, 1):
        row = dict(candidate)
        literal = row["literal"]
        source = row["source_file"].lower()
        tech = technical_kind(literal, token_policy)
        native_announcer = {
            "Victory", "Defeat", "First Blood", "Kongor Kill", "Team Wipe", "Tower Deny",
            "Double Tap", "Hat Trick", "Quad Kill", "Annihilation", "Rage Quit", "Smackdown",
            "Humiliation", "Payback", "Immortal", "Nemesis",
        }
        if "/dev/" in source or "/test" in source or "test_suite" in source:
            status, strategy, reason = "DEV_TEST", "DO_NOT_TOUCH", "Developer/test-only native UI"
        elif re.fullmatch(r":[a-z0-9_]+:", literal, re.I):
            status, strategy, reason = "INTERNAL", "DO_NOT_TOUCH", "Runtime icon/token syntax, not visible natural language"
        elif "marketplace_announce" in source and literal == "VRZO Thai Announcer":
            status, strategy, reason = "FALSE_POSITIVE", "DO_NOT_TOUCH", "Candidate occurs in a disabled commented product block"
        elif "marketplace_announce" in source and literal in {"Leo", "Katana"}:
            status, strategy, reason = "KEEP_EN", "DO_NOT_TOUCH", "Active structured HeroSkin product title"
        elif "store_config.lua" in source and (literal in native_announcer or literal.startswith("Killstreak ")):
            status, strategy, reason = "KEEP_EN", "DO_NOT_TOUCH", "Branded announcer/combat event identity"
        elif literal.upper() == "PLINKO":
            status, strategy, reason = "KEEP_EN", "DO_NOT_TOUCH", "Branded game feature name"
        elif tech:
            status, strategy, reason = "KEEP_EN", "DO_NOT_TOUCH", f"Controlled {tech}"
        else:
            matches = [item for item in exact.get(normalized_visible(literal), []) if item["namespace"] != "interface_test_suite"]
            translate_match = next((item for item in matches if item["status"] == "TRANSLATE"), None)
            status = "TRANSLATE"
            if translate_match:
                strategy, reason = "STRINGTABLE_KEY_EXISTS", f'Use existing key {translate_match["key"]} via source override'
            else:
                strategy, reason = "ADD_STRINGTABLE_KEY", "Add RU stringtable key and replace hardcoded literal in source override"
        row.update({
            "id": f"native:{index:04d}", "status": status, "integration_strategy": strategy,
            "reason": reason, "matched_key": translate_match["key"] if "translate_match" in locals() and translate_match else "",
            "russian": "",
        })
        result.append(row)
        if "translate_match" in locals():
            del translate_match
    return result


def classify_preact(rows: list[dict], token_policy: dict, dictionary: dict[str, list[dict]]) -> list[dict]:
    cosmetic_terms = {entry["canonical_text"] for entry in dictionary["avatars_cosmetics"]}
    announcer_terms = {entry["canonical_text"] for entry in dictionary["announcer_events"]}
    for row in rows:
        text = normalized_visible(row["english"])
        tech = technical_kind(text, token_policy)
        if tech:
            row.update(status="TECHNICAL", runtime_role="KEYCAP" if tech == "keycap" else "TECHNICAL_COPY", category=tech, reason="Controlled technical token")
        elif row.get("context") == "COUNTRY_MAP display name":
            row.update(status="TRANSLATE", runtime_role="DISPLAY_TEXT", category="country_display_name", reason="Full country name is user-facing; ISO/region codes remain English")
        elif text in cosmetic_terms:
            row.update(status="KEEP_EN", runtime_role="DISPLAY_TEXT", category="cosmetic_name", reason="Canonical cosmetic product name")
        else:
            low_context = (row.get("context", "") + " " + row["source_file"]).lower()
            if text in {"Smackdowns", "Annihilations"}:
                row.update(status="KEEP_EN", runtime_role="DISPLAY_TEXT", category="announcer_event", reason="Standalone branded statistic identity")
            elif text in {"Victory", "Defeat"} and any(token in low_context for token in ("match", "history", "stats", "profile")):
                row.update(status="TRANSLATE", runtime_role="DISPLAY_TEXT", category="match_result", reason="Match history/result UI")
            elif text in announcer_terms and ("announcer" in row["source_file"].lower() or text not in {"Victory", "Defeat", "Immortal", "Nemesis", "Payback"}):
                row.update(status="KEEP_EN", runtime_role="DISPLAY_TEXT", category="announcer_event", reason="Announcer preview/event identity")
            elif row.get("status") == "REVIEW":
                row.update(status="REVIEW", runtime_role="DISPLAY_TEXT", category="preact_review", reason="Dynamic/alt/user-message context requires review")
            else:
                row.update(status="TRANSLATE", runtime_role="DISPLAY_TEXT", category="preact_ui", reason="Generic user-facing Preact UI")
        row.setdefault("protected_terms", [])
        row.setdefault("locked_spans", [])
    assign_locked_spans(rows, dictionary)
    return rows


def completion_metrics(rows: list[dict]) -> dict:
    buckets: Counter[str] = Counter()
    release_rows = []
    for row in rows:
        role, status = row["runtime_role"], row["status"]
        if role == "DEV_TEST": bucket = "E_dev_test"
        elif status in {"DYNAMIC", "IMAGE_TEXT"} or role == "DYNAMIC_DATA": bucket = "F_dynamic_external"
        elif status == "REVIEW" and role == "DISPLAY_TEXT": bucket = "G_review_required"
        elif status == "TRANSLATE" and role == "DISPLAY_TEXT": bucket = "A_release_translatable"; release_rows.append(row)
        elif status == "KEEP_EN" and role == "DISPLAY_TEXT": bucket = "B_protected_keep_en"
        elif role in {"TECHNICAL_COPY", "KEYCAP", "STRUCTURAL"}: bucket = "C_technical_copy"
        elif role != "DISPLAY_TEXT": bucket = "D_internal_non_display"
        else: bucket = "G_review_required"
        buckets[bucket] += 1
    translated = sum(bool(row.get("russian")) and row["russian"] != row["english"] for row in release_rows)
    total = len(release_rows)
    return {
        "buckets": dict(sorted(buckets.items())),
        "russian_release_translation_coverage": {
            "translated": translated, "required": total,
            "percent": round((translated / total * 100), 4) if total else 100.0,
            "denominator_rule": "status=TRANSLATE and runtime_role=DISPLAY_TEXT only",
        },
    }


def make_review_queue(rows: list[dict]) -> list[dict]:
    queue = []
    for row in rows:
        if row["status"] != "REVIEW":
            continue
        if row.get("locked_spans"): priority = "P0"
        elif row["runtime_role"] == "DISPLAY_TEXT": priority = "P1"
        elif row["runtime_role"] == "DEV_TEST": priority = "P3"
        else: priority = "P2"
        suggested = "TRANSLATE" if row["runtime_role"] == "DISPLAY_TEXT" and row.get("thai_signal") == "DIFFERENT" else "REVIEW"
        queue.append({
            "priority": priority, "key": row["key"], "english": row["english"], "thai": row.get("thai", ""),
            "source_file": row["source_file"], "category": row["category"], "runtime_role": row["runtime_role"],
            "suggested_status": suggested, "reason": row["context"], "context": row["context"],
            "protected_terms": " | ".join(row.get("protected_terms", [])),
        })
    return sorted(queue, key=lambda row: (row["priority"], row["source_file"], row["key"]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--phase15-bundle", type=Path)
    args = parser.parse_args()
    root = args.project_root.resolve()
    catalog_path = root / "catalog" / "strings.jsonl"
    rows = read_jsonl(catalog_path)
    token_policy = load_token_policy(root / "catalog" / "technical_tokens.json")
    dictionary, state_rows = apply_catalog_policy(rows, token_policy)
    assign_locked_spans(rows, dictionary)

    contradictions = [
        {"id": row["id"], "key": row["key"], "english": row["english"], "protected_terms": row["protected_terms"]}
        for row in rows if row["status"] == "TRANSLATE" and normalized_visible(row["english"]) in row.get("protected_terms", [])
    ]
    if contradictions:
        raise SystemExit(f"Whole-value protected/TRANSLATE contradictions: {len(contradictions)}")

    old_rows = phase15_rows(args.phase15_bundle.resolve() if args.phase15_bundle else None)
    state_audit = state_protection_audit(old_rows, rows)
    write_jsonl(root / "reports" / "state_protection_audit.jsonl", state_audit)
    old_by_id = {row["id"]: row for row in old_rows}
    markup_spans = [
        {"id": row["id"], "key": row["key"], "english": row["english"], **span,
         "phase15_term_was_present": span["canonical_text"] in old_by_id.get(row["id"], {}).get("protected_terms", [])}
        for row in rows for span in row.get("locked_spans", [])
        if span.get("markup_prefix") or span.get("markup_suffix")
    ]
    write_json(root / "reports" / "markup_protection_audit.json", {
        "phase15_review_estimate": {"rows": 316, "occurrences": 368},
        "rechecked_rows": len({row["id"] for row in markup_spans}),
        "rechecked_occurrences": len(markup_spans),
        "newly_recognized_occurrences": sum(not row["phase15_term_was_present"] for row in markup_spans),
        "tokenizer": "visible-text map with source offsets; longest non-overlapping canonical match",
        "examples": markup_spans[:100],
    })
    write_json(root / "catalog" / "canonical_dictionary.json", {"version": 1, "groups": dictionary})
    write_jsonl(catalog_path, rows)
    fields = list(rows[0].keys()) if rows else []
    write_csv(root / "catalog" / "strings.csv", rows, fields)

    game_rows = [row for row in rows if row["namespace"] == "game_messages"]
    game_report = [{
        "key": row["key"], "english": row["english"], "status": row["status"],
        "category": row["category"], "reason": row["context"], "protected_terms": row["protected_terms"],
    } for row in game_rows]
    write_jsonl(root / "reports" / "game_messages_classification.jsonl", game_report)

    native = classify_native(read_jsonl(root / "reports" / "native_ui_string_candidates.jsonl"), rows, token_policy)
    write_jsonl(root / "catalog" / "native_extended_ui.jsonl", native)
    for row in native:
        if row["status"] == "KEEP_EN" and row["reason"] == "Active structured HeroSkin product title":
            dictionary["avatars_cosmetics"].append(canonical_entry(row["literal"], "COSMETIC", {
                "key": row["id"], "source_file": row["source_file"],
            }, "CONTEXTUAL"))
    dictionary["avatars_cosmetics"] = unique_dictionary(dictionary["avatars_cosmetics"])
    write_json(root / "catalog" / "canonical_dictionary.json", {"version": 1, "groups": dictionary})
    native_statuses = Counter(row["status"] for row in native)
    write_json(root / "reports" / "native_extended_ui_summary.json", {
        "total": len(native),
        "by_status": {status: native_statuses.get(status, 0) for status in ("TRANSLATE", "KEEP_EN", "REVIEW", "DEV_TEST", "INTERNAL", "FALSE_POSITIVE")},
        "by_strategy": dict(sorted(Counter(row["integration_strategy"] for row in native).items())),
        "by_area": dict(sorted(Counter(row["area"] for row in native).items())),
    })

    preact = classify_preact(read_jsonl(root / "catalog" / "extended_ui.jsonl"), token_policy, dictionary)
    write_jsonl(root / "catalog" / "preact_ui.jsonl", preact)
    preact_statuses = Counter(row["status"] for row in preact)
    write_json(root / "reports" / "preact_policy_summary.json", {
        "total": len(preact),
        "by_status": {status: preact_statuses.get(status, 0) for status in ("TRANSLATE", "KEEP_EN", "REVIEW", "TECHNICAL")},
        "by_runtime_role": dict(sorted(Counter(row["runtime_role"] for row in preact).items())),
        "by_category": dict(sorted(Counter(row["category"] for row in preact).items())),
    })

    review_queue = make_review_queue(rows)
    review_fields = ["priority", "key", "english", "thai", "source_file", "category", "runtime_role", "suggested_status", "reason", "context", "protected_terms"]
    write_csv(root / "reports" / "review_queue.csv", review_queue, review_fields)
    metrics = completion_metrics(rows)
    write_json(root / "reports" / "completion_metrics.json", metrics)

    state_summary = {
        "total": len(state_rows),
        "display_text": sum(row["runtime_role"] == "DISPLAY_TEXT" for row in state_rows),
        "translate": sum(row["status"] == "TRANSLATE" for row in state_rows),
        "keep_en": sum(row["status"] == "KEEP_EN" for row in state_rows),
        "internal_structural": sum(row["runtime_role"] in {"INTERNAL_ID", "STRUCTURAL", "TECHNICAL_COPY", "RESOURCE_PATH"} for row in state_rows),
        "canonical_sources_from_state": 0,
        "by_category": dict(sorted(Counter(row["category"] for row in state_rows).items())),
    }
    locked = [span for row in rows for span in row.get("locked_spans", [])]
    summary = {
        "catalog_rows": len(rows),
        "by_status": dict(sorted(Counter(row["status"] for row in rows).items())),
        "by_runtime_role": dict(sorted(Counter(row["runtime_role"] for row in rows).items())),
        "by_category": dict(sorted(Counter(row["category"] for row in rows).items())),
        "canonical_counts": {key: len(value) for key, value in dictionary.items()},
        "locked_occurrences": len(locked),
        "locked_rows": sum(bool(row.get("locked_spans")) for row in rows),
        "state": state_summary,
        "state_protection_audit_rows": len(state_audit),
        "markup_protection_audit": {
            "rows": len({row["id"] for row in markup_spans}),
            "occurrences": len(markup_spans),
            "newly_recognized_occurrences": sum(not row["phase15_term_was_present"] for row in markup_spans),
        },
        "game_messages": dict(sorted(Counter(row["status"] for row in game_rows).items())),
        "native": json.loads((root / "reports" / "native_extended_ui_summary.json").read_text(encoding="utf-8")),
        "preact": json.loads((root / "reports" / "preact_policy_summary.json").read_text(encoding="utf-8")),
        "review_queue": {priority: Counter(row["priority"] for row in review_queue).get(priority, 0) for priority in ("P0", "P1", "P2", "P3")},
        "completion_metrics": metrics,
        "contradictions": contradictions,
    }
    write_json(root / "reports" / "phase16_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
