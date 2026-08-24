#!/usr/bin/env python3
"""Repair Pass B rows rejected by strict token/canonical validation."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase2a_translate import google_translate, read_jsonl, write_jsonl  # noqa: E402


TOKEN_RE = re.compile(
    r"\^\\[rnt]"
    r"|%(?:\d+\$)?[-+#0 ]*(?:\d+|\*)?(?:\.\d+)?[A-Za-z%](?![A-Za-z])"
    r"|\$\{[^{}\r\n]+\}|\{[^{}\r\n]+\}|<[^<>\r\n]+>"
    r"|\^(?:[0-9]{3}|[^\s])|\\[rnt]"
)

MANUAL_REPAIR = {
    "entities:Ability_Blacksmith4_IMPACT_effect": "Даёт Fireball и Frenzy шанс сработать несколько раз — до {2,3,4}. Шанс двойного срабатывания — ^o{30,35,35}%^*, тройного — ^o{0,20,20}%^*, четырёхкратного — ^o{0,0,15}%^*.\\n\\n— Сокращает перезарядку Fireball на {1,2,3} с и увеличивает расход маны на {10,40,70}.\\n\\n— Увеличивает область действия Flaming Hammer на {100,200,300}.\\n\\n— Сокращает перезарядку Frenzy на {5,10,15} с.",
    "entities:Ability_Blacksmith4_IMPACT_effect:ult_boost": "^cДля применения требуется 30% максимального запаса маны.^*\\n\\n^gПрименяет к выбранному врагу Fireball 4-го уровня.^*\\n\\nПассивно даёт Fireball и Frenzy шанс сработать несколько раз — до {2,3,4}. Шанс двойного срабатывания — ^o{30,35,35}%^*, тройного — ^o{0,20,20}%^*, четырёхкратного — ^o{0,0,15}%^*.\\n\\n— Сокращает перезарядку Fireball на {1,2,3} с и увеличивает расход маны на {10,40,70}.\\n\\n— Увеличивает область действия Flaming Hammer на {100,200,300}.\\n\\n— Сокращает перезарядку Frenzy на {5,10,15} с.",
    "entities:Hero_Gauntlet_role": "Универсальный гибридный герой с высоким взрывным уроном от трёх атакующих способностей. Опытный игрок может с помощью Grapple переместить врага или союзника на большое расстояние, а точный Gauntlet Blast позволяет выхватывать отдельные цели.",
    "entities:Hero_Pharaoh_role": "Универсальный герой, способный атаковать издалека с помощью Tormented Soul и Wrath of the Pharaoh. Сблизившись с противником, он мешает ему действовать с помощью Hellfire и Wall of Mummies.",
    "entities:Hero_Ophelia_role": "Управляет нейтральными крипами с помощью Command. Вместе с прислужниками она поддерживает команду постоянными ганками и пушами, а Ophelia's Touch позволяет мгновенно исцелять союзников по всей карте.",
    "entities:Ability_Tempest3_Sub_description_simple": "Призывает метеорит в выбранную точку.\\n\\nПламя Meteor горит 8 секунд и каждую секунду наносит ^o{2,3,4,5}% от максимального здоровья врага чистым уроном^*. ^gStaff of the Master^* позволяет применять Meteor Strike, не прерывая поддерживаемую способность.",
    "entities:Item_BehemothsHeart_shop_flavor": "Вырванное из груди гиганта перед самой его гибелью, Behemoth's Heart дарует часть невероятной силы, здоровья и живучести этого существа.",
    "entities:Ability_Gemini2_description_simple": "Разделитесь на сущности ^rFire and Ice^*^b^* и переместитесь в выбранную точку. Каждая сущность наносит задетым врагам ^o{50,85,120,155} магического урона^*, после чего они воссоединяются и ^oоглушают врагов на {1.25,1.5,1.75,2} с^*.",
    "entities:Ability_Gemini4_description_simple": "Разделитесь на две сущности — ^rFire and Ice^*^b^*. ^oКаждая из них наследует^* вашу скорость передвижения, получает {5.5,7.5,9.5} магической брони и атрибуты, равные 100% ваших^*. Доля здоровья и маны остаётся такой же, как у героя. ^oГибель любой сущности убивает героя^*. ^rFire and Ice^*^b^* могут вновь объединиться в ^oGemini^*.\\n\\n^gЭффект Staff of the Master:^* сокращает перезарядку до 20 секунд и создаёт ^oтретью стихийную сущность — Light^*. Light получает собственные варианты первых двух способностей других сущностей, может после поддержания вернуться к Fire and Ice и обладает разведывательной пассивной способностью. ^rРядом одновременно с Fire и Ice Light наносит на 67% меньше урона.^*",
    "entities:Ability_LordSalforis3_IMPACT_effect": "При активации отключает пассивный урон.",
    "entities:Ability_PuppetMaster2_description_simple": "Заставляет выбранного врага атаковать ближайшего юнита в течение ^o{2,2.5,3,3.5} с^*.\\n\\nЦель ^oсначала выбирает вражеских героев и юнитов^*. ^oPuppet Show^* остаётся ^oактивной^*, даже если первая принудительно атакованная цель погибает.",
    "interface:tutorial_slide_quick_buy_desc": "Быстрая покупка позволяет заранее добавить предметы в очередь.\\n\\nЧтобы добавить предмет, нажмите Shift + левую кнопку мыши; чтобы удалить — Shift + правую кнопку мыши.\\n\\nЗатем нажмите горячую клавишу быстрой покупки, чтобы сразу купить предметы из очереди.",
}

POST_EDIT = (
    ("Специальные предложения", "Наносит"),
    ("специальные предложения", "наносит"),
    ("Гранты", "Даёт"),
    ("гранты", "даёт"),
    ("имеет дело", "наносит"),
    ("сделки", "наносит"),
    ("многоадресной рассылки", "мультикаста"),
    ("многоадресную рассылку", "мультикаст"),
    ("многоадресная рассылка", "мультикаст"),
    ("Многоадресная трансляция", "Мультикаст"),
    ("целевой вражеский отряд", "выбранного вражеского юнита"),
    ("целевой отряд", "выбранный юнит"),
    ("вражеский отряд", "вражеский юнит"),
    ("союзный отряд", "союзный юнит"),
    ("Пресса ", "Нажмите "),
    ("Unitwalking", "проход сквозь юнитов"),
    ("юнитвакинг", "проход сквозь юнитов"),
    ("Выигрыш", "Получает"),
    ("выигрыш", "получает"),
    ("отрядами", "юнитами"),
    ("отрядах", "юнитах"),
    ("отрядам", "юнитам"),
    ("отрядов", "юнитов"),
    ("отрядом", "юнитом"),
    ("отряду", "юниту"),
    ("отряда", "юнита"),
    ("отряды", "юниты"),
    ("отряд", "юнит"),
    ("Отряд", "Юнит"),
)


def protected_parts(row: dict) -> list[str | tuple[str, str]]:
    english = row["english"]
    regions: list[tuple[int, int, str]] = []
    for span in row.get("locked_spans", []):
        start, end = int(span["source_start"]), int(span["source_end"])
        # Preserve the exact source slice: span coordinates can encompass HoN
        # colour controls (for example Fire + Ice with distinct colours).
        replacement = english[start:end]
        regions.append((start, end, replacement))
    for match in TOKEN_RE.finditer(english):
        if not any(match.start() < end and match.end() > start for start, end, _ in regions):
            regions.append((match.start(), match.end(), match.group(0)))
    regions.sort()
    merged: list[tuple[int, int, str]] = []
    for region in regions:
        if merged and region[0] < merged[-1][1]:
            continue
        merged.append(region)
    parts: list[str | tuple[str, str]] = []
    cursor = 0
    for start, end, replacement in merged:
        if start > cursor:
            parts.append(("translate", english[cursor:start]))
        parts.append(replacement)
        cursor = end
    if cursor < len(english):
        parts.append(("translate", english[cursor:]))
    return parts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_root.resolve()
    validation = json.loads((root / "reports" / "build_validation.json").read_text(encoding="utf-8-sig"))
    error_ids = {error["id"] for error in validation.get("errors", [])}
    path = root / "catalog" / "strings.jsonl"
    rows = read_jsonl(path)

    # These are user-facing labels explicitly required to be Russian, not
    # canonical entity names or physical keycaps.
    unlock = {
        "interface:heroinfo_cooldown",
        "interface:boss_info_kongor_stat_hp_regen",
        "interface:boss_info_phoenix_stat_hp_regen",
    }
    for row in rows:
        if row["id"] in unlock:
            row["locked_spans"] = []
            row["protected_terms"] = []
            error_ids.discard(row["id"])

    targets = [row for row in rows if row["id"] in error_ids]
    layouts = [protected_parts(row) for row in targets]
    tasks: list[tuple[int, int, str, str, str]] = []
    for row_index, parts in enumerate(layouts):
        for part_index, part in enumerate(parts):
            if not isinstance(part, tuple):
                continue
            value = part[1]
            lead = re.match(r"^\s*", value).group(0)
            trail = re.search(r"\s*$", value).group(0)
            core = value[len(lead):len(value) - len(trail) if trail else None]
            if core and re.search(r"[A-Za-z]", core):
                tasks.append((row_index, part_index, lead, core, trail))
            else:
                layouts[row_index][part_index] = value
    while tasks:
        batch, chars = [], 0
        while tasks and len(batch) < 30:
            size = len(tasks[0][3]) + 20
            if batch and chars + size > 2800:
                break
            batch.append(tasks.pop(0))
            chars += size
        translated = google_translate([task[3] for task in batch])
        for (row_index, part_index, lead, _, trail), value in zip(batch, translated):
            layouts[row_index][part_index] = lead + value + trail
    by_id = {row["id"]: "".join(part if isinstance(part, str) else part[1] for part in layout).strip()
             for row, layout in zip(targets, layouts)}
    for row in rows:
        if row["id"] in by_id:
            row["russian"] = by_id[row["id"]]
            row["translation_phase"] = "Visible UI Pass B canonical repair"
        if row["id"] in MANUAL_REPAIR:
            row["russian"] = MANUAL_REPAIR[row["id"]]
            row["translation_phase"] = "Visible UI Pass B manual review"
        if row.get("translation_phase", "").startswith("Visible UI Pass B"):
            value = row.get("russian", "")
            for old, new in POST_EDIT:
                value = value.replace(old, new)
            row["russian"] = value
    write_jsonl(path, rows)
    print(json.dumps({"repaired": len(by_id), "unlocked_ui_labels": sorted(unlock)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
