#!/usr/bin/env python3
"""Pass D1 curated item-tooltip semantics and screenshot-confirmed UI cleanup."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE_SHA = "3d5ee66b9507c342d92b0be886d2918ea959e9beffb2126e6a7f77604142e301"

REPAIRS = {
    "game_messages:filter_carry": "Керри",
    "interface:player_role_carry": "Керри",
    "game_messages:action_target_self": "На себя",
    "entities:TargetScheme_self": "На себя",
    "entities:TargetScheme_enemy_units": "Вражеские юниты",
    "game_messages:stealth_bonus": "Скрытность; переход в невидимость — {value} с",
    "game_messages:unitwalking_bonus": "Проход сквозь юнитов",
    "game_messages:silenced_bonus": "Безмолвие",
    "game_messages:silenced_immunity_bonus": "Иммунитет к безмолвию",
    "interface:silenced_title": "Безмолвие",
    "interface:producst_header_emotes": "Эмоции",
    "interface:producst_header_cosmetics": "Косметика",
    "interface:vanity_cat_emotes": "ЭМОЦИИ",
    "interface:tutorial_slide_top_center_creeps_denied": "Добито союзных крипов",

    "entities:Item_Hellflower_description_simple": "Примените к врагу, чтобы на 5 секунд наложить Безмолвие и Perplex, а также увеличить получаемый им урон на 15%.",
    "entities:Item_Hellflower_effect_header": "Эффекты Hellflower",
    "entities:Item_Hellflower_IMPACT_effect": "Накладывает ^oHellflower^* на цель на ^o5 секунд^*.",
    "entities:State_Hellflower_FRAME_effect": "За поражённой целью остаётся видимый след.",

    "entities:Item_Genjuro_description": "При использовании расходует один заряд. Пока предмет не активен, он восстанавливает ^c1 заряд каждые 16 секунд^*, максимум — ^c2 заряда^*.\\n\\n^rПредмет нельзя выбросить^*, но можно продать.",
    "entities:Item_Genjuro_description_simple": "Активируйте, чтобы войти в скрытность. Предмет хранит до 2 зарядов. Первая атака из скрытности наносит дополнительный урон и замедляет цель.",
    "entities:Item_Genjuro_shop_flavor": "Этот мистический клинок создан мастером-убийцей. Кажется, он что-то вам нашёптывает.",
    "entities:Item_Genjuro_IMPACT_effect": "Накладывает на владельца ^oСкрытность мастера-убийцы^* на ^o11 секунд^*.",
    "entities:State_Genjuro_FRAME_effect": "Следующая атака наносит 125 дополнительного урона и замедляет скорость передвижения цели на 55% на 3 секунды.",

    "entities:Item_FluffyFleetingFeather_IMPACT_effect": "^oТелепортируетесь^* к выбранному союзнику и на 2 секунды увеличиваете его и свою ^oскорость передвижения на 10%^*.",
    "entities:Item_PhoenixVeil_IMPACT_effect": "Наносит всем врагам в радиусе 600 ^oмагический урон^*, равный 90 плюс накопленный урон. После этого накопленный урон обнуляется.",
    "entities:Item_FlamekeeperOath_IMPACT_effect": "Выберите союзника в радиусе 600, чтобы восстановить ему 300 здоровья. Все юниты в радиусе 400 от цели отталкиваются от неё на расстояние до 400.",
    "entities:Item_FluffyFletchingArrows_IMPACT_effect": "+100 к дальности атаки\\n\\nПри активации на 4 секунды даёт ^o+500/250 к дальности атаки^*, но на это время снижает ^oскорость передвижения на 50%^*.",
    "entities:Item_MagmaGauntlet_IMPACT_effect": "^oТелепортирует^* в выбранную точку. При приземлении замедляет врагов в радиусе 600 на 50% на 2 секунды, а вы в течение 3 секунд получаете на 50% меньше урона.\\n\\nПри получении урона от вражеского игрока предмет уходит на перезарядку на 3 секунды.",
    "entities:Item_HolyHandGrenade_IMPACT_effect": "Тратит половину ^oтекущей маны^* и бросает бомбу в выбранную точку. Через 2,5 секунды бомба взрывается и наносит всем врагам в радиусе 500 ^oмагический урон^*, равный 100% потраченной маны.",
    "entities:Item_PhoenixTalon_IMPACT_effect": "^oТелепортирует^* в выбранную точку. Враги в радиусе 1000 получают на 20% больше урона от подконтрольных вам источников. Через 4 секунды вы ^oвозвращаетесь в точку применения^*.",

    "entities:Item_BoundEye_FRAME_effect": "\\n^oПредмет выпадает при смерти.^*",
    "entities:Item_NullStone_FRAME_effect": "\\nЕсли предмет не на перезарядке, он ^oблокирует одно направленное заклинание^*.",
    "entities:Item_SpellSunder_FRAME_effect": "\\nКогда вы ^oнаносите магический урон^* подконтрольному игроку юниту, на него на 3 секунды накладывается отрицательный эффект: он ежесекундно наносит магический урон в размере ^o4% от текущего здоровья цели^* и ^oснижает восстановление здоровья на 75%^*.\\n\\nЕсли эффект вызван периодическим уроном, его урон снижается до 33%.\\n\\nЭффекты Spell Sunder не суммируются и не срабатывают от собственного периодического урона.",
    "entities:Item_DoomBringer_FRAME_effect": "\\n^oПредмет выпадает при смерти, если героя убил вражеский игрок.^*",
    "entities:Item_ProtectiveTalisman_FRAME_effect": "\\nЕсли владельца атакует герой, предмет с вероятностью 80% блокирует 20 урона для героя ближнего боя или 10 урона для героя дальнего боя.\\n\\nПри атаке со стороны не-героя вероятность блокирования составляет 50%.",
    "entities:Item_ShieldOfHonor_FRAME_effect": "\\n^oПосле получения атаки^* даёт ^o3 к урону и скорости атаки^* на 5 секунд. Эффект суммируется до 10 раз.",
    "entities:Item_PhoenixVeil_FRAME_effect": "\\nНакапливает 12% полученного урона, но не более 360.",
    "entities:Item_GoldenReach_FRAME_effect": "\\nПолучение урона от любого источника отключает бонус к ^oскорости передвижения^* на 5 секунд.\\n\\nЗа убийство вражеского юнита вы получаете дополнительно 5 золота.",
    "entities:Item_ObsidianSpear_FRAME_effect": "\\n^oПри убийстве героя или участии в убийстве^* оставшееся время восстановления основных способностей сокращается на 4 секунды.",
    "entities:Item_BrimstonePlate_FRAME_effect": "\\n^oПри получении атаки^* выпускает снаряд в атакующего. Снаряд наносит ^oмагический урон^*, равный 30 + 2% от вашего максимального здоровья, и на 2 секунды снижает получаемое атакующим лечение на 25%.",
    "entities:Item_EmberstoneBracers_FRAME_effect": "\\nКогда вы наносите непериодический урон, на цель накладывается эффект, который снижает ^oскорость передвижения^* на 40% с постепенным ослаблением за 0,5 секунды. На одной цели эффект может ^oсработать не чаще одного раза в 2 секунды^*.",
    "entities:Item_LastWail_FRAME_effect": "\\nЕсли вас убивает ^oвражеский герой^*, он получает ^oчистый урон^* в размере 250 + 10% от своего максимального здоровья. Если этот эффект убивает врага, вы возрождаетесь с 250 + 10% здоровья.",
    "entities:Item_CrimsonGuard_FRAME_effect": "\\nЕсли после получения урона ваше здоровье опускается до 30% от максимального или ниже, вы на 5 секунд получаете щит, поглощающий 1000 урона.",
    "entities:Item_LagunaOrb_FRAME_effect": "\\nКаждая 6-я атака наносит дополнительно ^o100 чистого урона^*, снимает с цели все положительные эффекты и снижает её ^oскорость передвижения на 100%^* с постепенным ослаблением за 1 секунду.",
    "entities:Item_BurningTemper_FRAME_effect": "\\nВаши атаки наносят дополнительный ^oфизический урон^* в размере 2% от вашего ^oмаксимального здоровья^*.",
    "entities:Item_TwinTikiMask_FRAME_effect": "\\n^oВ выключенном состоянии^*: вы наносите и получаете на 15% меньше урона от всех источников (10% для героев дальнего боя).\\n\\n^oВо включённом состоянии^*: вы наносите и получаете на 15% больше урона от всех источников (10% для героев дальнего боя).",
    "entities:Item_HelmOfTheFirelands_FRAME_effect": "\\nКаждая ^o5-я атака^* создаёт иллюзию на 5 секунд. Иллюзия наносит 35% урона, получает 300% урона и ^oне может активировать^* эффект этого предмета.",
    "entities:Item_Chaosbrand_FRAME_effect": "\\nСлучайно переключается между четырьмя стихийными режимами. ^oКаждую секунду и при каждой вашей атаке^* есть ^o5% вероятности^* сменить стихию; каждая даёт свой эффект:\\n\\n^oEmberfrost^*: атаки снижают ^oскорость передвижения^* на 40% на 2 секунды.\\n^oStarborn^*: непериодический урон дополнительно наносит ^o75 магического урона^* за 2 секунды.\\n^oDuskwrath^*: 27% непериодического урона также наносится ^oмане^* врага; если мана закончилась, этот урон наносится здоровью.\\n^oIronroot^*: атаки снижают ^oскорость атаки^* на 25% на 2 секунды.\\n\\nАктивируйте, чтобы на 10 секунд получить ^oвсе^* эффекты одновременно.",
    "entities:Item_Chaosbrand_FRAME_effect:chaosbrand_emberfrost": "\\nАтаки снижают ^oскорость передвижения^* на 40% на 2 секунды.\\n\\n^oКаждую секунду и при каждой вашей атаке^* есть ^o5% вероятности^* сменить стихию предмета и получить другой эффект.\\n\\nАктивируйте, чтобы на 10 секунд получить все возможные эффекты Chaosbrand.",
    "entities:Item_Chaosbrand_FRAME_effect:chaosbrand_starborn": "\\nНепериодический урон дополнительно наносит ^o75 магического урона^* за 2 секунды.\\n\\n^oКаждую секунду и при каждой вашей атаке^* есть ^o5% вероятности^* сменить стихию предмета и получить другой эффект.\\n\\nАктивируйте, чтобы на 10 секунд получить все возможные эффекты Chaosbrand.",
    "entities:Item_Chaosbrand_FRAME_effect:chaosbrand_duskwrath": "\\n27% нанесённого непериодического урона также наносится мане врага. Если мана закончилась, дополнительный урон наносится здоровью.\\n\\n^oКаждую секунду и при каждой вашей атаке^* есть ^o5% вероятности^* сменить стихию предмета и получить другой эффект.\\n\\nАктивируйте, чтобы на 10 секунд получить все возможные эффекты Chaosbrand.",
    "entities:Item_Chaosbrand_FRAME_effect:chaosbrand_ironroot": "\\nАтаки снижают ^oскорость атаки^* на 25% на 2 секунды.\\n\\n^oКаждую секунду и при каждой вашей атаке^* есть ^o5% вероятности^* сменить стихию предмета и получить другой эффект.\\n\\nАктивируйте, чтобы на 10 секунд получить все возможные эффекты Chaosbrand.",
    "entities:Item_Chaosbrand_FRAME_effect:chaosbrand_active": "\\nВременно даёт все эффекты ^oChaosbrand^*.\\n\\n- Атаки снижают ^oскорость передвижения^* на 40% на 2 секунды.\\n- Непериодический урон дополнительно наносит ^o75 магического урона^* за 2 секунды.\\n- 27% непериодического урона также наносится мане врага; если мана закончилась, дополнительный урон наносится здоровью.\\n- Атаки снижают ^oскорость атаки^* на 25% на 2 секунды.",
}

BASE_LORE_EN = "A relic scorched into existence by the death of the eternal ^rFirebird^*."
BASE_LORE_RU = "Реликвия, рождённая в пламени после гибели вечной ^rЖар-птицы^*."
MAGIC_ARMOR_EN = BASE_LORE_EN + "\\n\\nThis item contains a passive ^yMagic Armor^* bonus which does not stack with other ^yMagic Armor^* items."
MAGIC_ARMOR_RU = BASE_LORE_RU + "\\n\\nПредмет даёт пассивный бонус к ^yмагической броне^*, который не суммируется с бонусами других предметов на ^yмагическую броню^*."
CDR_EN = BASE_LORE_EN + "\\n\\nThis item contains a passive ^yAbility Cooldown Reduction Modifier^* bonus which does not stack with other ^yAbility Cooldown Reduction Modifier^* items."
CDR_RU = BASE_LORE_RU + "\\n\\nПредмет даёт пассивное ^yсокращение времени восстановления способностей^*, которое не суммируется с другими бонусами на ^yсокращение времени восстановления^*."

PHOENIX_IMPACT_IDS = {
    "entities:Item_FluffyFleetingFeather_IMPACT_effect",
    "entities:Item_PhoenixVeil_IMPACT_effect",
    "entities:Item_FlamekeeperOath_IMPACT_effect",
    "entities:Item_FluffyFletchingArrows_IMPACT_effect",
    "entities:Item_MagmaGauntlet_IMPACT_effect",
    "entities:Item_HolyHandGrenade_IMPACT_effect",
    "entities:Item_PhoenixTalon_IMPACT_effect",
}

SUSPICIOUS_PATTERNS = {
    "APPLIES_TARGET_GRAMMAR": r"Применяется.+(?:нацеливаться|себе ради)",
    "LITERAL_CHARGE": r"\b(?:обвинени|расходы)\w*\b",
    "LITERAL_DEAL": r"\b(?:Сделка|сделки|имеет дело)\b",
    "UNITWALKING": r"Юнитволкинг",
    "PERPLEX_LITERAL": r"(?:в недоумении|недоумения)",
    "SILENCE_LITERAL": r"Без звука",
    "BROKEN_DURATION_CONSTRUCTION": r"\b(?:для|ради)\s+\^?[a-z]?\d+(?:[.,]\d+)?\s+секунд",
    "BROKEN_TARGET": r"\bнацеливать\b",
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def main() -> int:
    catalog_path = ROOT / "catalog" / "strings.jsonl"
    rows = read_jsonl(catalog_path)
    prior_changes_path = ROOT / "reports" / "pass_d1_changes.jsonl"
    prior_changes = {row["id"]: row for row in read_jsonl(prior_changes_path)} if prior_changes_path.exists() else {}
    selected: set[str] = set()
    changes: list[dict] = []

    # The engine data only exposes perplexed="true"; its player-facing semantics
    # are not defined in the available source. Preserve the safe English term.
    unresolved_perplex = {"game_messages:perplexed_bonus", "game_messages:perplexed_immunity_bonus"}
    for row in rows:
        row_id = row["id"]
        old = row.get("russian", "")
        if row.get("english") == BASE_LORE_EN and row_id.startswith("entities:Item_"):
            REPAIRS[row_id] = BASE_LORE_RU
        elif row.get("english") == MAGIC_ARMOR_EN:
            REPAIRS[row_id] = MAGIC_ARMOR_RU
        elif row.get("english") == CDR_EN:
            REPAIRS[row_id] = CDR_RU

        if row_id in unresolved_perplex:
            row["status"] = "REVIEW"
            row["russian"] = row["english"]
            row["notes"] = "Pass D1 REVIEW: engine state confirms perplexed=true, but available data does not define the user-facing restriction."
            selected.add(row_id)
            if old != row["russian"]:
                changes.append({"id": row_id, "english": row["english"], "old": old, "new": row["russian"], "reason": "SAFE_SOURCE_VALUE_PENDING_PERPLEX_SEMANTICS"})
            elif row_id in prior_changes:
                changes.append(prior_changes[row_id])
            continue

        if row_id == "interface:tutorial_slide_top_center_creeps_denied":
            row["locked_spans"] = [span for span in row.get("locked_spans", []) if span.get("canonical_text") != "Denied"]
            row["protected_terms"] = [term for term in row.get("protected_terms", []) if term != "Denied"]

        if row_id in REPAIRS:
            row["russian"] = REPAIRS[row_id]
            row["status"] = "TRANSLATE"
            row["runtime_role"] = "DISPLAY_TEXT"
            if row.get("category") == "resource_path":
                row["category"] = "item_description"
                row["context"] = "Runtime-visible item passive/effect tooltip"
                row["notes"] = "Pass D1: leading literal newline was misclassified as a resource path."
            row["translation_phase"] = "Pass D1 semantic cleanup"
            selected.add(row_id)
            if old != row["russian"]:
                changes.append({"id": row_id, "english": row["english"], "old": old, "new": row["russian"], "reason": "CURATED_SEMANTIC_REWRITE"})
            elif row_id in prior_changes:
                changes.append(prior_changes[row_id])

    # Tier labels are part of protected item names and remain byte-for-byte EN.
    tier_keep = []
    for row in rows:
        if row.get("category") == "item_name" and re.search(r"\\n\^vTier (?:I|II|III|IV)\^\*$", row.get("english", "")):
            row["status"] = "KEEP_EN"
            row["russian"] = row["english"]
            tier_keep.append(row["id"])

    write_jsonl(catalog_path, rows)

    item_rows = [row for row in rows if row.get("namespace") == "entities" and row.get("key", "").startswith("Item_") and row.get("category") in {"item_description", "resource_path"}]
    changed_ids = {item["id"] for item in changes}
    item_inventory = []
    for row in item_rows:
        flags = [name for name, pattern in SUSPICIOUS_PATTERNS.items() if re.search(pattern, row.get("russian", ""), re.I)]
        if row["id"] in changed_ids:
            action = "CHANGED"
        elif flags or not row.get("russian"):
            action = "REVIEW"
        else:
            action = "NO_AUTOMATED_ISSUE_DETECTED"
        item_inventory.append({"id": row["id"], "english": row["english"], "russian": row.get("russian", ""), "audit_action": action, "flags": flags})

    review = [row for row in item_inventory if row["audit_action"] == "REVIEW"]
    review.extend([
        {"id": "game_messages:perplexed_bonus", "reason": "PERPLEX_ENGINE_SEMANTICS_UNDEFINED", "source_evidence": "items/recipes/hellflower/state.entity: perplexed=true"},
        {"id": "game_messages:perplexed_immunity_bonus", "reason": "PERPLEX_ENGINE_SEMANTICS_UNDEFINED", "source_evidence": "engine property only"},
        {"id": "native:0058", "reason": "MAIN_NAVIGATION_SEMANTICS", "key": "main_menu_leanatorium", "current": "УЗНАТЬ"},
        {"id": "native:0059", "reason": "MAIN_NAVIGATION_SEMANTICS", "key": "main_menu_ladder", "current": "ЛЕСТНИЦА"},
        {"id": "runtime:hero_role", "reason": "SCREENSHOT_RUNTIME_DISCREPANCY", "key": "store2_hero_role", "catalog_value": "Роль героя", "note": "No hardcoded 'Hero Role' exists in the Pass C archive."},
        {"id": "image:patch_notes_promo", "reason": "IMAGE_TEXT", "action": "UNCHANGED"},
    ])

    debug_rows = [row for row in rows if row.get("namespace") == "interface_test_suite" and row.get("runtime_role") == "DEV_TEST"]
    keep = [
        {"id": row["id"], "english": row["english"], "reason": "CANONICAL_ITEM_NAME"}
        for row in rows if row.get("category") == "item_name" and row.get("status") == "KEEP_EN"
    ]
    keep.extend({"id": row_id, "english": next(r["english"] for r in rows if r["id"] == row_id), "reason": "TIER_LABEL_KEEP_EN"} for row_id in tier_keep)

    native = ["ui/hd_ui/templates/menu_vote_templates.package", "ui/scripts/game/game_shop_hd.lua"]
    scope = {
        "version": 1,
        "scope": "Pass D1 item tooltip semantic cleanup and screenshot-confirmed UI fixes",
        "baseline_sha256": BASELINE_SHA,
        "selection": {"catalog": sorted(selected), "native": native},
        "counts": {
            "item_tooltip_rows_audited": len(item_inventory),
            "catalog_rows_changed": len(selected),
            "native_files_changed": len(native),
            "item_rows_changed": sum(row["id"].startswith("entities:Item_") for row in changes),
            "item_review_rows": sum(row["audit_action"] == "REVIEW" for row in item_inventory),
            "debug_ui_rows_deferred": len(debug_rows),
            "keep_en_records": len(keep),
        },
    }
    (ROOT / "catalog" / "pass_d1_scope.json").write_text(json.dumps(scope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_jsonl(ROOT / "reports" / "pass_d1_item_tooltip_inventory.jsonl", item_inventory)
    write_jsonl(ROOT / "reports" / "pass_d1_changes.jsonl", changes)
    write_jsonl(ROOT / "reports" / "pass_d1_review.jsonl", review)
    write_jsonl(ROOT / "reports" / "pass_d1_keep_en.jsonl", keep)
    write_jsonl(ROOT / "reports" / "pass_d1_debug_ui_inventory.jsonl", [
        {"id": row["id"], "key": row["key"], "english": row["english"], "source_file": row["source_file"], "disposition": "DEFER_DEBUG_UI_PASS"}
        for row in debug_rows
    ])
    print(json.dumps(scope["counts"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
