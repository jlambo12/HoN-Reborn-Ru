#!/usr/bin/env python3
"""Prepare the reviewed Visible UI Localization Pass B catalog changes.

The pass is deliberately catalog-only: it never installs an archive and never
touches the upstream snapshot. Canonical spans and HoN markup are protected by
the existing Phase 2A masking/validation pipeline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase2a_translate import read_jsonl, translate_unique, write_jsonl  # noqa: E402


TARGET_CATEGORIES = {
    "hero_description",
    "ability_description",
    "item_description",
    "state_effect_description",
    "state_status_label",
    "gameplay_description",
}

INTERFACE_PREFIXES = ("boss_info_", "compendium_", "heroinfo_")

MANUAL = {
    # Help navigation and prominent titles.
    "Pre-Game": "Перед игрой",
    "Bans": "Баны",
    "Role Priority": "Приоритет ролей",
    "Game Modes": "Режимы игры",
    "Matchmaking Tuning": "Настройка поиска матча",
    "Invite Teammates": "Приглашение союзников",
    "Limited Hero Pool": "Ограниченный выбор героев",
    "Honor Rating": "Рейтинг чести",
    "Custom Game": "Своя игра",
    "Custom Games": "Свои игры",
    "Custom Lobby": "Свое лобби",
    "Gameplay": "Игровой процесс",
    "Game Info": "Сведения об игре",
    "Hero Interface": "Интерфейс героя",
    "Hero Attributes": "Атрибуты героя",
    "Hero Stats": "Характеристики героя",
    "Hero Abilities": "Способности героя",
    "Teleport": "Телепортация",
    "Ravens": "Вороны",
    "Gold": "Золото",
    "Bosses": "Боссы",
    "Statistics": "Характеристики",
    "Abilities": "Способности",
    "Rewards": "Награды",
    "Scaling": "Усиление",
    "King of Apes": "Король обезьян",
    "The Phoenix": "Феникс",
    "Boss: Kongor": "Босс: Kongor",
    "BOSS: Kongor": "БОСС: Kongor",
    "Boss: Phoenix": "Босс: Fluffylumps",
    "BOSS: Phoenix": "БОСС: Fluffylumps",
    # Encyclopedia labels.
    "Hero Compendium": "Энциклопедия героев",
    "Hero Role": "Роль героя",
    "Role": "Роль",
    "Range:": "Дальность:",
    "Mana": "Мана",
    "Melee/Range": "Ближний/дальний бой",
    "Ranged": "Дальний бой",
    "^cRange:^*": "^cДальность:^*",
    "^cMana cost:^*": "^cРасход маны:^*",
    "^cCD:^* {time} seconds": "^cПерезарядка:^* {time} с",
    "^oHealth:^* 4000": "^oЗдоровье:^* 4000",
    "^oArmor:^* 10": "^oБроня:^* 10",
    "^oArmor:^* 15": "^oБроня:^* 15",
    "^oMagic Armor:^* 30": "^oМагическая броня:^* 30",
    "^oMagic Armor:^* 25": "^oМагическая броня:^* 25",
    "^oDamage:^* 125": "^oУрон:^* 125",
    "^oDamage:^* 150": "^oУрон:^* 150",
    "^oMove Speed:^* 270": "^oСкорость передвижения:^* 270",
    "^oMove Speed:^* 350": "^oСкорость передвижения:^* 350",
    "^oAttack Range:^* 128 (Melee)": "^oДальность атаки:^* 128 (ближний бой)",
    "^oAttack Range:^* 200 (Melee)": "^oДальность атаки:^* 200 (ближний бой)",
    "^oAttack Cooldown:^* 1s": "^oИнтервал атаки:^* 1 с",
    "^oAttack Cooldown:^* 1.55s": "^oИнтервал атаки:^* 1,55 с",
    "^oHP Regen:^* 10/s": "^oВосстановление здоровья:^* 10/с",
    "^oHP Regen:^* 15/s": "^oВосстановление здоровья:^* 15/с",
    # Explicit acceptance examples and mixed-language cleanup.
    "All Heroes": "Все герои",
    "Press ^t{hotkey}^* to disassemble.": "Нажмите ^t{hotkey}^*, чтобы разобрать.",
    "Toggle Extra Ability 1 Autocast": "Переключить автоприменение дополнительной способности 1",
    "Toggle Extra Ability 2 Autocast": "Переключить автоприменение дополнительной способности 2",
    "Toggle Extra Ability 3 Autocast": "Переключить автоприменение дополнительной способности 3",
    "Toggle Extra Ability 4 Autocast": "Переключить автоприменение дополнительной способности 4",
    "Toggle Extra Ability 5 Autocast": "Переключить автоприменение дополнительной способности 5",
    "Toggle Replay Controls Visibility": "Показать или скрыть управление повтором",
    "Toggle Sharing Courier With Team": "Разрешить или запретить команде управлять курьером",
    "Press ^o{key}^* to show": "Нажмите ^o{key}^*, чтобы показать",
    # Local MOTD shell. API title/body/CTA remain dynamic.
    "Latest Updates": "Последние новости",
    "Couldn't load news": "Не удалось загрузить новости",
    "We couldn't reach the news service. Check your connection and try again.": "Не удалось подключиться к службе новостей. Проверьте соединение и повторите попытку.",
    "Retry": "Повторить",
    "No news right now": "Сейчас новостей нет",
    "Check back soon for the latest patches, events, and updates.": "Загляните позже, чтобы узнать о новых патчах, событиях и обновлениях.",
    "Message of the Day": "Новости дня",
    "Refresh": "Обновить",
    "Quick Links": "Полезные ссылки",
    "Discord": "Discord",
    "Join the community": "Присоединиться к сообществу",
    "Website": "Сайт",
    "heroesofnewerth.com": "heroesofnewerth.com",
    "Support": "Поддержка",
    "Get help": "Получить помощь",
    "&copy; 2026 Kongor Studios. All rights reserved.": "&copy; 2026 Kongor Studios. Все права защищены.",
}

EXPLICIT_FIX_IDS = {
    "entities:TargetScheme_all_heroes",
    "entities:Option_AllHeroes",
    "interface:general_mode_all_heroes",
    "interface:mainlobby_gamelist_allheroes_title",
    "interface:ui_item_can_be_disassembled",
    "interface:game_scores_label_hotkey_tip",
    "interface:game_replay_tip_Controls",
    "interface:tooltip_teamshare",
    *(f"interface:options_label_acti_extra_ab_{i}_sec_keybind" for i in range(1, 6)),
}


def source_text(row: dict) -> str:
    return str(row.get("english", row.get("literal", "")))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_root.resolve()
    catalog_path = root / "catalog" / "strings.jsonl"
    native_path = root / "catalog" / "native_extended_ui.jsonl"
    preact_path = root / "catalog" / "preact_ui.jsonl"
    help_rows = read_jsonl(root / "reports" / "help_topics_inventory.jsonl")
    help_ids = {row["id"] for row in help_rows if row.get("status") == "TRANSLATE" and not row.get("russian")}

    catalog = read_jsonl(catalog_path)
    native = read_jsonl(native_path)
    preact = read_jsonl(preact_path)

    for row in catalog:
        if row["id"] in {"entities:TargetScheme_all_heroes", "entities:Option_AllHeroes"}:
            row["status"] = "TRANSLATE"
            row["category"] = "functional_ui"
            row["notes"] = "Visible UI Localization Pass B: user-facing aggregate label, not an entity name."

    selected_catalog = []
    for row in catalog:
        is_target = (
            row["id"] in help_ids
            or row.get("category") in TARGET_CATEGORIES
            or (row.get("namespace") == "interface" and row.get("key", "").startswith(INTERFACE_PREFIXES))
            or row["id"] in EXPLICIT_FIX_IDS
        )
        if is_target and row.get("status") == "TRANSLATE" and row.get("runtime_role", "DISPLAY_TEXT") == "DISPLAY_TEXT":
            selected_catalog.append(row)

    selected_native = [row for row in native if row.get("status") == "TRANSLATE"]
    selected_preact = [row for row in preact if row.get("status") == "TRANSLATE" and row.get("layer") == "motd_remote"]
    selected = selected_catalog + selected_native + selected_preact

    representative = {}
    for row in selected:
        representative.setdefault(source_text(row), row)
    memory_path = root / "translations" / "pass_b_memory.jsonl"
    cache = {row["english"]: row["russian"] for row in read_jsonl(memory_path)} if memory_path.exists() else {}
    cache.update(MANUAL)
    missing = [row for english, row in representative.items() if english not in cache]
    if missing:
        cache = translate_unique(missing, cache)

    changed = Counter()
    for group_name, rows in (("catalog", catalog), ("native", native), ("preact_motd", preact)):
        selected_ids = {row["id"] for row in ({"catalog": selected_catalog, "native": selected_native, "preact_motd": selected_preact}[group_name])}
        for row in rows:
            if row["id"] not in selected_ids:
                continue
            new_value = cache[source_text(row)]
            if row.get("russian") != new_value:
                row["russian"] = new_value
                changed[group_name] += 1
            row["translation_phase"] = "Visible UI Pass B"

    write_jsonl(catalog_path, catalog)
    write_jsonl(native_path, native)
    write_jsonl(preact_path, preact)
    write_jsonl(memory_path, [
        {"english": english, "russian": cache[english], "english_hash": hashlib.sha256(english.encode()).hexdigest()}
        for english in sorted({source_text(row) for row in selected}, key=str.casefold)
    ])

    scope = {
        "version": 1,
        "scope": "Visible UI Localization Pass B",
        "selection": {
            "catalog": sorted(row["id"] for row in selected_catalog),
            "native": sorted(row["id"] for row in selected_native),
            "preact_motd": sorted(row["id"] for row in selected_preact),
        },
        "counts": {
            "help_topics": len(help_ids),
            "hero_descriptions": sum(row.get("category") == "hero_description" for row in selected_catalog),
            "ability_descriptions": sum(row.get("category") == "ability_description" for row in selected_catalog),
            "item_descriptions": sum(row.get("category") == "item_description" for row in selected_catalog),
            "state_tooltip_text": sum(row.get("category") in {"state_effect_description", "state_status_label"} for row in selected_catalog),
            "boss_ui": sum(row.get("namespace") == "interface" and row.get("key", "").startswith("boss_info_") for row in selected_catalog),
            "encyclopedia_labels": sum(row.get("namespace") == "interface" and row.get("key", "").startswith(("compendium_", "heroinfo_")) for row in selected_catalog),
            "settings_controls_fixes": sum(row["id"] in EXPLICIT_FIX_IDS for row in selected_catalog),
            "native_ui": len(selected_native),
            "motd_local_shell": len(selected_preact),
        },
        "changed": dict(changed),
        "immutable": ["canonical entity names", "keycap values", "Help IMAGE_TEXT assets", "remote MOTD/API content"],
    }
    (root / "catalog" / "pass_b_scope.json").write_text(json.dumps(scope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(scope["counts"] | {"unique_english": len(representative), "changed_total": sum(changed.values())}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
