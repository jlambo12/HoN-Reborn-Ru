#!/usr/bin/env python3
"""Curated runtime-visible English cleanup over the accepted Pass B catalog."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


UI = {
    "-Selected-": "— Выбрано —",
    "^oArmor:^* {armor}": "^oБроня:^* {armor}",
    "^oAtk Range:^* {range}": "^oДальность атаки:^* {range}",
    "^oAtk Speed:^* {speed}": "^oСкорость атаки:^* {speed}",
    "^oDamage:^* {damage}": "^oУрон:^* {damage}",
    "^oMagic Armor:^* {armor}": "^oМагическая броня:^* {armor}",
    "^oMove Speed:^* {mvspeed}": "^oСкорость передвижения:^* {mvspeed}",
    "Accessories": "Аксессуары", "Account Icons": "Значки аккаунта",
    "Account Vanity": "Оформление аккаунта", "ADD ITEMS": "ДОБАВИТЬ ПРЕДМЕТЫ",
    "Agility": "Ловкость", "ALL HEROES": "ВСЕ ГЕРОИ", "All Items": "Все предметы",
    "An assortment of the most powerful and expensive base components.": "Набор самых мощных и дорогих базовых компонентов.",
    "Announcers": "Комментаторы", "Armor Items": "Предметы на броню", "Attack type": "Тип атаки",
    "Avatar Name Asc": "Имя аватара: А–Я", "Avatar Name Desc": "Имя аватара: Я–А",
    "Avatars": "Аватары", "Basic": "Базовые", "BASIC ITEMS": "БАЗОВЫЕ ПРЕДМЕТЫ",
    "Basic items for Heroes first starting their adventures.": "Базовые предметы для героев, начинающих свой путь.",
    "Boots": "Обувь", "BUILDS INTO": "СОБИРАЕТСЯ В", "Bundle": "Набор", "Bundles": "Наборы",
    "Buy Item": "Купить предмет", "Buy Remaining": "Купить оставшееся", "Categories": "Категории",
    "Close": "Закрыть", "Combative": "Боевые", "CONSUMABLE ITEMS": "РАСХОДУЕМЫЕ ПРЕДМЕТЫ",
    "Consumables": "Расходуемые", "Couriers": "Курьеры", "Creep": "Крипы", "Damage": "Урон",
    "Damage Items": "Предметы на урон", "Default": "По умолчанию", "Defense": "Защита",
    "Difficulty High To Low": "Сложность: по убыванию", "Difficulty Low To High": "Сложность: по возрастанию",
    "Discount Bundle": "Набор со скидкой", "Enchantment": "Зачарование", "Game Vanity": "Игровое оформление",
    "Hero Name Asc": "Имя героя: А–Я", "Hero Name Desc": "Имя героя: Я–А", "Heroes": "Герои",
    "History": "История", "Home to many goods and potions that are generally consumed upon use.": "Здесь продаются различные припасы и зелья, которые обычно расходуются при использовании.",
    "Initiation": "Инициация", "Intelligence": "Интеллект", "Internal error.": "Внутренняя ошибка.",
    "Items for SBT testing enviroment.": "Предметы для тестовой среды SBT.",
    "Items that contain a unique modifier effect.": "Предметы с уникальным эффектом-модификатором.",
    "Items that increase the frequency at which you attack.": "Предметы, повышающие скорость атаки.",
    "Items that increase your Agility statistic.\\n\\nAgility increases your attack speed and armor.": "Предметы, повышающие ловкость.\\n\\nЛовкость увеличивает скорость атаки и броню.",
    "Items that increase your attack damage.": "Предметы, увеличивающие урон от атаки.",
    "Items that increase your health or mana pool.": "Предметы, увеличивающие запас здоровья или маны.",
    "Items that increase your Intelligence statistic.\\n\\nIntelligence increases your mana and mana regeneration.": "Предметы, повышающие интеллект.\\n\\nИнтеллект увеличивает запас и восстановление маны.",
    "Items that increase your movement speed and speed of travel.": "Предметы, повышающие скорость передвижения.",
    "Items that increase your physical or magic damage mitigation.": "Предметы, снижающие получаемый физический или магический урон.",
    "Items that increase your rate of health or mana regeneration.": "Предметы, ускоряющие восстановление здоровья или маны.",
    "Items that increase your Strength statistic.\\n\\nStrength increases your health and health regeneration.": "Предметы, повышающие силу.\\n\\nСила увеличивает запас и восстановление здоровья.",
    "Items that may be activated.": "Предметы с активируемым эффектом.",
    "Items with that are consumed after activation.": "Предметы, расходуемые после активации.",
    "Latest": "Последние", "Legendary": "Легендарные", "Lucky Bundle": "Случайный набор",
    "Magic Items": "Магические предметы", "Match Items": "Предметы матча", "MAX": "МАКС.",
    "Melee": "Ближний бой", "Morph Attack": "Изменение атаки", "Name Asc": "Название: А–Я",
    "Name Colors": "Цвета имени", "New Hero: {name}": "Новый герой: {name}", "Observatory": "Обсерватория",
    "Other": "Прочее", "Outpost": "Аванпост", "Owned": "Получено", "Owned: {count}": "Получено: {count}",
    "Patch Notes": "Список изменений", "Phoenix Rewards": "Награды Fluffylumps",
    "Possible Grab Bag Rewards": "Возможные награды", "Price High To Low": "Цена: по убыванию",
    "Price Low To High": "Цена: по возрастанию", "Primary Attribute": "Основной атрибут",
    "Protective": "Защитные", "Purchase Next Item": "Купить следующий предмет",
    "Purchase to get all products!": "Купите набор, чтобы получить все товары!", "QUICK BUY": "БЫСТРАЯ ПОКУПКА",
    "Ranged": "Дальний бой", "Recipe": "Рецепт", "RECIPE ITEMS": "ПРЕДМЕТЫ ПО РЕЦЕПТУ",
    "Recipes for items that add to a Hero's combat prowess, improving damage output.": "Рецепты предметов, повышающих боевую мощь героя и наносимый урон.",
    "Recipes for items that are useful for helping your team.": "Рецепты предметов для поддержки команды.",
    "Recipes for items that generally increase survivability.": "Рецепты предметов, повышающих выживаемость.",
    "Recipes for items that modify or add various properties to a Hero's attack.": "Рецепты предметов, изменяющих или дополняющих свойства атаки героя.",
    "Recommended": "Рекомендуемые", "Recommended Items are always reliable and can be put to good use against the enemy.": "Рекомендуемые предметы надёжны и полезны против большинства противников.",
    "Release Date Asc": "Дата выхода: сначала ранние", "Release Date Desc": "Дата выхода: сначала новые",
    "Relics": "Реликвии", "REMOVE ITEMS": "УДАЛИТЬ ПРЕДМЕТЫ", "REQUIRED ITEMS": "НЕОБХОДИМЫЕ ПРЕДМЕТЫ",
    "Role": "Роль героя", "Save ^960{gold}!": "Экономия: ^960{gold}!", "Search Store...": "Поиск в магазине...",
    "Search...": "Поиск...", "Select an item to see it's components and assemblies.": "Выберите предмет, чтобы увидеть его компоненты и дальнейшие улучшения.",
    "Selection Circles": "Круги выделения", "Shady and mysterious, the Secret Shop contains many rare and powerful artifacts. One must venture into the woods to find the reclusive Secret Shop's location.": "В таинственной секретной лавке продаются редкие и могущественные артефакты. Чтобы найти её, придётся отправиться в лес.",
    "show all {count} results": "показать все результаты: {count}", "Sort Basic/Recipes": "Сортировать: базовые/рецепты",
    "Sort Gold Highest/Lowest": "Сортировать по стоимости", "Store": "Магазин", "Strength": "Сила",
    "Supplies": "Припасы", "Supportive": "Поддержка", "Switch Category Type (Basic/Legacy)": "Сменить набор категорий (базовый/классический)",
    "Symbols": "Символы", "Taunt": "Насмешки", "Taunt Badges": "Значки насмешек",
    "The chosen statistics have been successfully reset.  You must now log out in order to refresh your stats.": "Выбранные показатели сброшены. Выйдите из аккаунта, чтобы обновить статистику.",
    "The password is incorrect.": "Неверный пароль.", "Toggle Grid/List Item View": "Переключить вид: сетка/список",
    "Toggle QuickBuy Visibility": "Показать или скрыть быструю покупку", "Toggle Shop Keybinds": "Показать или скрыть клавиши магазина",
    "TP Effects": "Эффекты телепортации", "Trinkets and treasures that primarily provide a boost to basic stats.": "Безделушки и сокровища, главным образом повышающие основные характеристики.",
    "Upgrades": "Улучшения", "Utility Items": "Вспомогательные предметы",
    "Various armor and weapons that generally increase damage or armor.": "Различные доспехи и оружие, обычно повышающие урон или броню.",
    "Various basic (non-recipe) items that are often useful if they are part of a recipe you plan on creating.": "Различные базовые предметы, необходимые для сборки более сложных предметов.",
    "Various rare artifacts that have many different effects.": "Редкие артефакты с разнообразными эффектами.",
    "Vault": "Хранилище", "WARDS": "ВАРДЫ", "Wards": "Варды", "Weapons": "Оружие",
    "You have {chance} chances to purchase to get {count} products": "Шансов получить {count} товаров: {chance}",
    "You need to buy the stats rest first.": "Сначала необходимо приобрести сброс статистики.",
}

KEYCAP_VALUES = {"SHIFT + LMB", "SHIFT + RMB"}

MIXED_REPLACEMENTS = (
    ("Magic DoT", "магический периодический урон"),
    ("Mana Drain", "похищение маны"),
    ("0.2 second Stun", "оглушение на 0,2 секунды"),
    ("and applies a ", "и накладывает "),
    ("^oland beside it^*. If targeting a Volcano, Draconis instantly flies to it.", "^oприземлиться рядом^*. При выборе Volcano Draconis мгновенно перелетает к нему."),
    ("True Damage", "чистый урон"),
    ("Grinex'S Stealth", "невидимость Grinex"),
    ("Speed Boost", "Ускорение"),
    ("UnitWalking", "проход сквозь юнитов"),
    ("unitwalking", "проход сквозь юнитов"),
    ("Clearvision", "беспрепятственный обзор"),
    ("Truestrike", "точные атаки"),
    ("Ally Well", "союзный колодец"),
    ("Superior Magic", "усиленный магический"),
    ("Magic Damage", "магический урон"),
    ("give Mana with", "восполнять ману с помощью"),
    ("Lifesteal", "вампиризмом"),
    ("Lane Creeps", "линейных крипов"),
    ("Lane Creep", "линейного крипа"),
    ("Sights & Reveals", "обнаруживает и раскрывает"),
    ("Allied Heroes", "союзных героев"),
    ("PLAY", "ИГРАТЬ"),
)

INQUISITOR_ID = "entities:Item_InquisitorsFlail_FRAME_effect"
INQUISITOR_RU = "\\nПолучив от врага не менее ^o60 ед. урона от заклинания^* за один раз, если цель не обладает иммунитетом к магии, поразите атакующего: нанесите ему ^o150 магического урона^* и наложите ^oбезмолвие^* на 1,5 секунды."

EXACT_REPAIRS = {
    "entities:State_Gladiator_Ability4_Damage_FRAME_effect": 'Наносит Gladiator урон, накопленный способностью "Call to Arms", в виде прямого снятия HP.',
    "entities:Ability_Kane3_description2": "Пассивно: ваши автоатаки и Waylay накладывают на цель заряд Kane's Anguish на 4 секунды. Максимум — ^o{1,2,3,4} заряда^*.\\n\\nЭтот эффект снижает урон от атак цели на ^o{20}%^* за каждый заряд. Когда Kane атакует цель, она также получает урон в размере ^o5% от своего урона атаки за каждый заряд^*.\\n\\nСпособность действует на башни.",
    "entities:Ability_Tempest1_description2": "^gЭту способность можно усилить Staff of the Master.^*\\n\\n^gЭффект посоха:^* тип урона изменяется на чистый.",
    "entities:Ability_Tempest2_description2": "^gЭту способность можно усилить Staff of the Master.^*\\n\\n^gЭффект посоха:^* тип урона изменяется на чистый.",
    "entities:Ability_Tempest1_IMPACT_effect": "Поражает вражеского юнита ледяным взрывом ^o3 раза^*. Каждый взрыв наносит ^o{30,50,70,90} магического урона^* и ^oоглушает на {0.25,0.5,0.75,1} секунды^*. Взрывы происходят с ^oинтервалом 2 секунды^*.\\n\\n^gЭффект Staff of the Master:^* тип урона изменяется на чистый.",
    "entities:Item_Striders_FRAME_effect:movespeed": "Если вы ^oне участвуете в бою^* 6 секунд, за 2 секунды вы получаете ^o80 к скорости передвижения^* и ^o2 к восстановлению здоровья^*.\\n\\nДополнительные скорость передвижения и восстановление уменьшаются, если в радиусе 900 находится вражеский герой, и полностью исчезают на расстоянии 750. Бонусы снимаются при вступлении в бой.\\n\\nВы считаетесь не участвующим в бою, если не атаковали, не применяли способности, не получали урон и не становились целью вражеской способности. Использование любого предмета, кроме вардов, Blight Stones, Health Potion, Bottle или Lex Talionis, также снимает бонусы.",
    "entities:Shop_Recipes5_description": "Рецепты изменения атаки позволяют создавать предметы, которые изменяют или добавляют различные свойства атаке героя.",
    "interface:tutorial_slide_bans_desc_bottom": "Приоритет идёт сверху вниз.\\nЧем выше позиция, тем больше вероятность бана.",
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")


def main() -> int:
    path = ROOT / "catalog" / "strings.jsonl"
    rows = read_jsonl(path)
    review_source = {row["id"]: row for row in read_jsonl(ROOT / "reports" / "pass_b_review.jsonl")}
    review_ids = set(review_source)
    selected: set[str] = set()
    inventory: list[dict] = []
    inventoried_ids: set[str] = set()
    translated = 0
    technical_tokens = {"KrosMode", "nTwitch", "ipush", "iPushing", "iPush", "ElitePet", "GadgetImmunity", "PBAoE", "ElementUser", "Shrinetower", "FauxAccount", "DivA", "wza", "MacroHard", "DMG", "AoE-", "NPC-", "description", "simple"}
    keep_tokens = {"Burning", "Ember", "Frostbite", "Snotter", "Fulcrum", "Aura", "Electric", "Frosted", "Ablaze", "Whirlpool", "Undying", "Vaulted", "Bile", "Fed", "DOOM", "Javelin", "Charged", "Antlore", "Carapace", "Hardened", "Spine", "Vulnerability", "Shell", "Drain", "Shredder", "Spirit", "Sawblade", "Soul", "Tainted", "Volcano", "Flared", "Glove", "Empowered", "Fire", "Ice", "Light", "Boost", "Boil", "Death", "Anguish", "Animate", "Axed", "Mauler", "Skyve", "Venomous", "Ball", "Chain", "Crazy", "Puppet", "Pound", "Spore'd", "Blink", "Coeurl", "Shiver", "Bad", "Harsh", "Winds", "Superior", "krieg", "Flare", "Blast", "Riftstalker", "Madman's", "Arms", "Master", "Touch", "Wrath", "Greater", "Rhino", "Coterie", "Divine", "The", "Heart", "Hammer", "HyperXewl", "Ioyn", "DangerousDan", "Pandaroohoo", "Strider", "Milkfat", "eSports", "Posthaste", "Biiiig", "Pimpin'", "Chaosbrand", "Perplex", "Nullstone", "Mid", "Wars", "JamesTowN", "AceJR"}

    for row in rows:
        key = row.get("key", "")
        if row["id"] == "interface:Shop_Supplies_description":
            # "Home" is an ordinary sentence opener here, not a canonical entity.
            row["locked_spans"] = [span for span in row.get("locked_spans", []) if span.get("canonical_text") != "Home"]
            row["protected_terms"] = [term for term in row.get("protected_terms", []) if term != "Home"]
        if row["id"] == "entities:Ability_GroundFamiliar1_IMPACT_effect":
            # These are ability names inside the description, not prose labels.
            row["russian"] = row.get("russian", "").replace("способности Ускорение (", "способности Speed Boost (").replace("и Щит курьера (", "и Courier Shield (")
        runtime_ui = (
            row.get("namespace") == "interface"
            and (key.startswith(("shop_", "Shop_", "store2_", "patchnotes_")) or key == "enstasts_label_hero_info_agi")
            and row.get("english") in (set(UI) | KEYCAP_VALUES)
        )
        if runtime_ui:
            english = row["english"]
            if english in KEYCAP_VALUES:
                row["status"] = "KEEP_EN"
                row["russian"] = english
                classification = "KEEP_EN"
            else:
                if english not in UI:
                    raise SystemExit(f"Missing curated UI translation: {row['id']} {english!r}")
                row["russian"] = UI[english]
                row["translation_phase"] = "Visible UI Pass C"
                selected.add(row["id"])
                translated += 1
                classification = "TRANSLATE"
            inventory.append({"id": row["id"], "source": "EMPTY_RUNTIME_LABEL", "english": english, "classification": classification, "russian": row["russian"]})
            inventoried_ids.add(row["id"])

        if row["id"] == INQUISITOR_ID:
            row["status"] = "TRANSLATE"
            row["runtime_role"] = "DISPLAY_TEXT"
            row["category"] = "item_description"
            row["russian"] = INQUISITOR_RU
            row["notes"] = "Pass C: verified runtime-visible tooltip paragraph; canonical item name remains KEEP_EN."
            row["translation_phase"] = "Visible UI Pass C"
            selected.add(row["id"])
            translated += 1
            inventory.append({"id": row["id"], "source": "CONFIRMED_SCREENSHOT_TOOLTIP", "english": row["english"], "classification": "TRANSLATE", "russian": row["russian"]})
            inventoried_ids.add(row["id"])

        if row["id"] in review_ids:
            before = row.get("russian", "")
            after = EXACT_REPAIRS.get(row["id"], before)
            if row["id"] in {"entities:Ability_Kraken3_ATTACK_IMPACT_effect:ult_boost", "entities:Ability_Kraken3_description_simple:ult_boost"}:
                after = after.replace("Release the. Kraken", "Release the Kraken").replace("Release the Kraken.^*", "Release the Kraken.^*")
            for old, new in MIXED_REPLACEMENTS:
                after = after.replace(old, new)
            was_cleaned = after != before or row.get("translation_phase") == "Visible UI Pass C mixed cleanup"
            if after != before:
                row["russian"] = after
                row["translation_phase"] = "Visible UI Pass C mixed cleanup"
                selected.add(row["id"])
            if was_cleaned:
                selected.add(row["id"])
                translated += 1
                classification = "TRANSLATE"
            else:
                tokens = set(review_source[row["id"]].get("tokens", []))
                if tokens and tokens <= technical_tokens:
                    classification = "TECHNICAL"
                elif tokens and tokens <= keep_tokens:
                    classification = "KEEP_EN"
                else:
                    classification = "REVIEW"
            if row["id"] not in inventoried_ids:
                inventory.append({"id": row["id"], "source": "PASS_B_MIXED_REVIEW", "english": row["english"], "classification": classification, "before": before, "russian": row.get("russian", ""), "tokens": review_source[row["id"]].get("tokens", [])})
                inventoried_ids.add(row["id"])

    # Two verified native hardcoded placeholders are patched as isolated archive
    # members, not represented by the AST catalog.
    for source_file in ("ui/avoid_player.interface", "ui/fe3/templates/ban_select_templates.package"):
        inventory.append({"id": "native:" + source_file + ":Search", "source": "HARDCODED_RUNTIME_LABEL", "english": "Search...", "classification": "TRANSLATE", "russian": "Поиск..."})
        translated += 1

    write_jsonl(path, rows)
    classification_counts = {}
    for item in inventory:
        classification_counts[item["classification"]] = classification_counts.get(item["classification"], 0) + 1
    scope = {
        "version": 1,
        "scope": "Pass C runtime-visible English and mixed-language cleanup",
        "baseline_sha256": "d71f85e3321c3954e877f2ccfa516c1e87f2006371499d491c83fd565fb1cb3d",
        "selection": {"catalog": sorted(selected), "native": ["ui/avoid_player.interface", "ui/fe3/templates/ban_select_templates.package"]},
        "counts": {"inventory_records": len(inventory), "translated_records": translated, "catalog_rows": len(selected), "native_literals": 2, "classifications": classification_counts},
    }
    (ROOT / "catalog" / "pass_c_scope.json").write_text(json.dumps(scope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (ROOT / "reports" / "pass_c_inventory.jsonl").open("w", encoding="utf-8") as handle:
        for item in inventory:
            handle.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(json.dumps(scope["counts"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
