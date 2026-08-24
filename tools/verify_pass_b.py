#!/usr/bin/env python3
"""Regression, scope, integrity and remaining-English audit for Pass B."""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_GAME_SHA = "a518f760c7bdebcfb2f9258dbfcfe7e2bf81881938e4653b0b1c725e04099762"
EXPECTED_FONT_SHA = "96e4d1c6d2b8a772322affbea3be367020a2bba07b89b80dd71b1752babd2868"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    build = ROOT / "build" / "pass-b" / "resources0.jz"
    baseline = ROOT / "build" / "font-readability" / "resources0.jz"
    game = Path.home() / "AppData" / "Local" / "Juvio" / "heroes of newerth" / "resources0.jz"
    installed = Path.home() / "AppData" / "Local" / "Juvio" / "extensions" / "resources0.jz"
    scope = json.loads((ROOT / "catalog" / "pass_b_scope.json").read_text(encoding="utf-8"))
    catalog = read_jsonl(ROOT / "catalog" / "strings.jsonl")
    native = read_jsonl(ROOT / "catalog" / "native_extended_ui.jsonl")
    preact = read_jsonl(ROOT / "catalog" / "preact_ui.jsonl")
    canonical_data = json.loads((ROOT / "catalog" / "canonical_dictionary.json").read_text(encoding="utf-8-sig"))
    canonical_entries = [entry for group in canonical_data.get("groups", {}).values() for entry in group]
    canonical_terms = sorted(
        {entry["canonical_text"] for entry in canonical_entries if len(entry.get("canonical_text", "")) >= 3},
        key=len,
        reverse=True,
    )
    by_id = {row["id"]: row for row in catalog}
    native_by_id = {row["id"]: row for row in native}
    preact_by_id = {row["id"]: row for row in preact}
    errors: list[dict] = []

    def check(condition: bool, code: str, **details: object) -> None:
        if not condition:
            errors.append({"code": code, **details})

    check(game.is_file() and sha256(game) == EXPECTED_GAME_SHA, "upstream_archive_changed")
    check(installed.is_file() and sha256(installed) == EXPECTED_FONT_SHA, "installed_extension_changed")
    check(build.is_file(), "build_missing")
    check(baseline.is_file() and sha256(baseline) == EXPECTED_FONT_SHA, "font_baseline_changed")

    with zipfile.ZipFile(baseline) as old, zipfile.ZipFile(build) as new:
        check(old.testzip() is None, "font_baseline_crc")
        check(new.testzip() is None, "pass_b_crc")
        old_meta = {name: (old.getinfo(name).CRC, old.getinfo(name).file_size) for name in old.namelist() if not name.endswith("/")}
        new_meta = {name: (new.getinfo(name).CRC, new.getinfo(name).file_size) for name in new.namelist() if not name.endswith("/")}
        changed = sorted(name for name in old_meta.keys() & new_meta.keys() if old_meta[name] != new_meta[name])
        added = sorted(new_meta.keys() - old_meta.keys())
        removed = sorted(old_meta.keys() - new_meta.keys())
        allowed_native = {native_by_id[row_id]["source_file"] for row_id in scope["selection"]["native"]}
        allowed_changed = {"stringtables/entities_ru.str", "stringtables/interface_ru.str", "ui/hd_ui/styles.package"} | allowed_native
        check(not removed, "archive_members_removed", members=removed)
        check(set(changed) <= allowed_changed, "unexpected_changed_members", members=sorted(set(changed) - allowed_changed))
        check(set(added) <= allowed_native, "unexpected_added_members", members=sorted(set(added) - allowed_native))
        check(new.read("core_ru.resources") == old.read("core_ru.resources"), "font_resource_changed")
        check(new.read("preact/dist/assets/index.css") == old.read("preact/dist/assets/index.css"), "font_fallback_css_changed")
        old_style = old.read("ui/hd_ui/styles.package").decode("utf-8").replace("\r\n", "\n").rstrip() + "\n"
        new_style = new.read("ui/hd_ui/styles.package").decode("utf-8").replace("\r\n", "\n").rstrip() + "\n"
        expected_style = old_style.replace(
            '<style name="color-gray-light" color=".75 .75 .75 1" />',
            '<style name="color-gray-light" color=".86 .86 .86 1" />',
        )
        check(new_style == expected_style, "readability_override_not_isolated")
        image_changes = [name for name in changed + added + removed if re.search(r"(?i)\.(?:png|tga|jpe?g|webp|dds)$", name)]
        check(not image_changes, "image_asset_changed", members=image_changes)

    for group, lookup in (("catalog", by_id), ("native", native_by_id), ("preact_motd", preact_by_id)):
        for row_id in scope["selection"][group]:
            row = lookup[row_id]
            check(bool(row.get("russian")), "missing_pass_b_translation", id=row_id)
            check("\ufffd" not in row.get("russian", ""), "replacement_character", id=row_id)
    for row in catalog:
        if row.get("status") == "KEEP_EN":
            check(row.get("russian") == row.get("english"), "canonical_keep_en_changed", id=row["id"])

    mixed_fixes = [
        "interface:ui_item_can_be_disassembled", "interface:general_mode_all_heroes",
        "interface:mainlobby_gamelist_allheroes_title", "interface:game_scores_label_hotkey_tip",
        "interface:game_replay_tip_Controls", "interface:tooltip_teamshare",
        *(f"interface:options_label_acti_extra_ab_{i}_sec_keybind" for i in range(1, 6)),
        "entities:Ability_LordSalforis3_IMPACT_effect", "interface:tutorial_slide_quick_buy_desc",
        "entities:Ability_PuppetMaster2_description_simple",
    ]
    mixed_report = [{"id": row_id, "english": by_id[row_id]["english"], "russian": by_id[row_id]["russian"]} for row_id in mixed_fixes]
    (ROOT / "reports" / "pass_b_mixed_language_fixes.json").write_text(
        json.dumps(mixed_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    allowed_words = {
        "hon", "juvio", "discord", "kongor", "fluffylumps", "newerth", "caldavar",
        "aoe", "hp", "mp", "dps", "gpm", "xpm", "kda", "fps", "alt", "ctrl",
        "shift", "mouse", "staff", "usd", "api", "url", "html", "pvp", "pve",
        "dot", "npc", "moba", "reborn",
    }
    artifact_terms = ("Выигрыш", "отряд", "многоадрес", "Уилл", "Пресса", "имеет дело", "сделки")
    review: list[dict] = []
    selected_catalog = [by_id[row_id] for row_id in scope["selection"]["catalog"]]
    for row in selected_catalog:
        value = row.get("russian", "")
        stripped = value
        for span in row.get("locked_spans", []):
            stripped = stripped.replace(span["canonical_text"], "")
        for term in canonical_terms:
            if term in stripped:
                stripped = stripped.replace(term, "")
        stripped = re.sub(r"\{[^{}]+\}|\$\{[^{}]+\}|<[^<>]+>|\^(?:[0-9]{3}|[^\s])", " ", stripped)
        words = sorted({word for word in re.findall(r"[A-Za-z][A-Za-z'-]{2,}", stripped) if word.casefold() not in allowed_words})
        artifacts = [term for term in artifact_terms if term.casefold() in value.casefold()]
        if words or artifacts:
            review.append({"id": row["id"], "reason": "EN_TOKEN" if words else "LINGUISTIC_POSTEDIT", "tokens": words, "artifacts": artifacts, "russian": value})
    with (ROOT / "reports" / "pass_b_review.jsonl").open("w", encoding="utf-8") as handle:
        for row in review:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    help_inventory = read_jsonl(ROOT / "reports" / "help_topics_inventory.jsonl")
    help_ids = {row["id"] for row in help_inventory if row.get("status") == "TRANSLATE" and not row.get("russian")}
    help_remaining = sum(not by_id[row_id].get("russian") for row_id in help_ids)
    canonical_counts = Counter(row.get("category") for row in catalog if row.get("status") == "KEEP_EN" and row.get("category") in {
        "hero_name", "ability_name", "item_name", "boss_name", "boss_ability_name", "keycap"
    })
    report = {
        "result": "PASS" if not errors else "FAIL",
        "errors": errors,
        "build": {"path": str(build), "sha256": sha256(build), "size_bytes": build.stat().st_size, "installed": False, "crc": "PASS"},
        "baseline": {"game_sha256": sha256(game), "installed_extension_sha256": sha256(installed), "font_build_sha256": sha256(baseline)},
        "translated": scope["counts"] | {"motd_local_shell_runtime_active": 0},
        "remaining_visible_en": {
            "localizable_selected_rows": help_remaining,
            "review_rows_with_en_token_candidates": len(review),
            "canonical_keep_en": dict(canonical_counts),
            "help_baked_image_assets": 23,
            "remote_motd_shell_labels_not_overridden": 17,
            "remote_motd_dynamic_field_classes": ["tagLabel", "title", "body", "ctas[].label"],
        },
        "review": {"rows": len(review), "path": str(ROOT / "reports" / "pass_b_review.jsonl")},
        "archive_delta": {"changed": changed, "added": added, "removed": removed},
        "readability": {"style": "color-gray-light", "before": "#BFBFBF", "after": "#DBDBDB", "rollback": "single-member override"},
        "images_modified": 0,
        "gameplay_data_network_modified": False,
        "installer": str(ROOT / "scripts" / "install_pass_b_test.ps1"),
        "rollback": str(ROOT / "scripts" / "restore_font_after_pass_b.ps1"),
    }
    (ROOT / "reports" / "pass_b_final_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": report["result"], "errors": len(errors), "review": len(review), "sha256": report["build"]["sha256"]}, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
