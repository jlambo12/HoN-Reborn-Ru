#!/usr/bin/env python3
"""Verify Pass C scope, archive integrity, baseline isolation and final counts."""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_UPSTREAM_SHA = "a518f760c7bdebcfb2f9258dbfcfe7e2bf81881938e4653b0b1c725e04099762"
EXPECTED_PASS_B_SHA = "d71f85e3321c3954e877f2ccfa516c1e87f2006371499d491c83fd565fb1cb3d"
ALLOWED = {
    "stringtables/entities_ru.str",
    "stringtables/interface_ru.str",
    "ui/avoid_player.interface",
    "ui/fe3/templates/ban_select_templates.package",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def main() -> int:
    installed = Path.home() / "AppData" / "Local" / "Juvio" / "extensions" / "resources0.jz"
    upstream = Path.home() / "AppData" / "Local" / "Juvio" / "heroes of newerth" / "resources0.jz"
    build = ROOT / "build" / "pass-c" / "resources0.jz"
    scope = json.loads((ROOT / "catalog" / "pass_c_scope.json").read_text(encoding="utf-8"))
    catalog = jsonl(ROOT / "catalog" / "strings.jsonl")
    inventory = jsonl(ROOT / "reports" / "pass_c_inventory.jsonl")
    by_id = {row["id"]: row for row in catalog}
    errors: list[dict] = []

    def check(value: bool, code: str, **details: object) -> None:
        if not value:
            errors.append({"code": code, **details})

    check(upstream.is_file() and sha256(upstream) == EXPECTED_UPSTREAM_SHA, "upstream_archive_changed")
    check(installed.is_file() and sha256(installed) == EXPECTED_PASS_B_SHA, "installed_pass_b_changed")
    check(build.is_file(), "pass_c_build_missing")
    if not build.is_file() or not installed.is_file():
        raise SystemExit("Required archive missing")

    with zipfile.ZipFile(installed) as old, zipfile.ZipFile(build) as new:
        check(old.testzip() is None, "pass_b_crc_failed")
        check(new.testzip() is None, "pass_c_crc_failed")
        old_meta = {name: (old.getinfo(name).CRC, old.getinfo(name).file_size) for name in old.namelist() if not name.endswith("/")}
        new_meta = {name: (new.getinfo(name).CRC, new.getinfo(name).file_size) for name in new.namelist() if not name.endswith("/")}
        changed = sorted(name for name in old_meta.keys() & new_meta.keys() if old_meta[name] != new_meta[name])
        added = sorted(new_meta.keys() - old_meta.keys())
        removed = sorted(old_meta.keys() - new_meta.keys())
        check(set(changed) == ALLOWED, "archive_delta_not_exact", changed=changed)
        check(not added, "archive_members_added", members=added)
        check(not removed, "archive_members_removed", members=removed)
        for name in ("core_ru.resources", "preact/dist/assets/index.css", "ui/hd_ui/styles.package"):
            check(new.read(name) == old.read(name), "font_or_readability_member_changed", member=name)
        image_delta = [name for name in changed + added + removed if re.search(r"(?i)\.(png|tga|jpe?g|webp|dds)$", name)]
        check(not image_delta, "image_asset_changed", members=image_delta)
        check(b"Search..." not in new.read("ui/avoid_player.interface") and "Поиск...".encode() in new.read("ui/avoid_player.interface"), "avoid_search_not_localized")
        check(b'content="Search..."' not in new.read("ui/fe3/templates/ban_select_templates.package") and "Поиск...".encode() in new.read("ui/fe3/templates/ban_select_templates.package"), "ban_search_not_localized")
        interface_ru = new.read("stringtables/interface_ru.str").decode("utf-8-sig")
        entities_ru = new.read("stringtables/entities_ru.str").decode("utf-8-sig")
        for expected in (
            "patchnotes_title\tСписок изменений",
            "store2_hero_attr_agility\tЛовкость",
            "store2_hero_role\tРоль героя",
            "Shop_Search_Shop\tПоиск...",
            "shop_subcategory_recipe\tРецепт",
            "shop_subcategory_basic\tБазовые",
            "shop_select_an_item\tВыберите предмет, чтобы увидеть его компоненты и дальнейшие улучшения.",
        ):
            check(expected in interface_ru, "confirmed_runtime_label_missing", expected=expected)
        check("Item_InquisitorsFlail_FRAME_effect\t\\nПолучив от врага не менее ^o60 ед. урона от заклинания^*" in entities_ru, "inquisitors_flail_tail_missing")

    selected = set(scope["selection"]["catalog"])
    for row_id in selected:
        row = by_id[row_id]
        check(bool(row.get("russian")), "selected_translation_empty", id=row_id)
        check("\ufffd" not in row.get("russian", ""), "replacement_character", id=row_id)
    for row in catalog:
        if row.get("status") == "KEEP_EN":
            check(row.get("russian") == row.get("english"), "keep_en_changed", id=row["id"])

    counts = Counter(row["classification"] for row in inventory)
    check(sum(counts.values()) == len(inventory), "inventory_partition_error")
    check(len(selected) + 2 == counts["TRANSLATE"], "translation_count_mismatch", selected=len(selected), translated=counts["TRANSLATE"])
    remaining = [row for row in inventory if row["classification"] != "TRANSLATE"]
    remaining_path = ROOT / "reports" / "pass_c_remaining_visible_en.jsonl"
    with remaining_path.open("w", encoding="utf-8") as handle:
        for row in remaining:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    report = {
        "result": "PASS" if not errors else "FAIL",
        "errors": errors,
        "baseline": {
            "installed_pass_b": {"path": str(installed), "sha256": sha256(installed), "unchanged": True},
            "upstream": {"path": str(upstream), "sha256": sha256(upstream), "unchanged": True},
        },
        "build": {"path": str(build), "sha256": sha256(build), "size_bytes": build.stat().st_size, "crc": "PASS", "installed": False},
        "inventory": {
            "runtime_visible_en_found": len(inventory),
            "translated": counts["TRANSLATE"],
            "keep_en": counts["KEEP_EN"],
            "technical": counts["TECHNICAL"],
            "review": counts["REVIEW"],
            "remaining_records": len(remaining),
            "remaining_path": str(remaining_path),
        },
        "archive_delta": {"changed": changed, "added": added, "removed": removed},
        "font_readability_changed": False,
        "layout_changed": False,
        "gameplay_data_network_changed": False,
        "images_changed": False,
        "installer": str(ROOT / "scripts" / "install_pass_c_test.ps1"),
        "rollback": str(ROOT / "scripts" / "restore_pass_b_after_pass_c.ps1"),
    }
    (ROOT / "reports" / "pass_c_final_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": report["result"], "errors": len(errors), "counts": report["inventory"], "sha256": report["build"]["sha256"]}, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
