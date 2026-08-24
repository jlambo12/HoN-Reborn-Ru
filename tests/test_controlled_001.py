import hashlib
import json
import sys
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.localization.pre_d_donor_audit import structural_comparison


def load_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]


class ControlledBatch001Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch = load_jsonl(ROOT / "translation" / "batches" / "controlled_001_modern_ui.jsonl")
        cls.by_key = {row["logical_key"]: row for row in cls.patch}
        cls.sources = {
            row["logical_key"]: row
            for row in load_jsonl(ROOT / "translation" / "source_index.jsonl")
        }
        cls.validation = json.loads(
            (ROOT / "translation" / "reports" / "controlled_001_validation.json").read_text(encoding="utf-8")
        )
        cls.build_report = json.loads(
            (ROOT / "translation" / "reports" / "controlled_001_runtime_build.json").read_text(encoding="utf-8")
        )

    def test_batch_size_and_unique_keys(self):
        self.assertEqual(len(self.patch), 39)
        self.assertEqual(len(self.by_key), len(self.patch))
        self.assertGreaterEqual(len(self.patch), 20)
        self.assertLessEqual(len(self.patch), 40)

    def test_all_entries_are_human_approved_pending_runtime(self):
        statuses = [row["status"] for row in self.patch]
        self.assertEqual(statuses.count("HUMAN_APPROVED"), 39)
        self.assertEqual(statuses.count("BLOCKED_NO_CONTEXT"), 0)
        self.assertTrue(all(not row["applied"] and not row["runtime_verified"] for row in self.patch))
        self.assertTrue(all(row["approval_state"] == "HUMAN_APPROVED_PENDING_RUNTIME" for row in self.patch))
        self.assertTrue(all(row["human_review_state"] == "APPROVED" for row in self.patch))

    def test_main_menu_natural_wording(self):
        expected = {
            "interface:main_menu_leanatorium": "СПРАВКА",
            "interface:main_menu_ladder": "РЕЙТИНГ",
            "interface:main_menu_store": "МАГАЗИН",
            "interface:main_menu_profile": "Профиль",
            "interface:main_menu_playnow": "ИГРАТЬ",
            "interface:main_menu_options": "Настройки",
            "interface:main_menu_heroes": "Герои",
            "interface:main_menu_items": "Предметы",
        }
        for key, value in expected.items():
            self.assertEqual(self.by_key[key]["proposed_ru"], value)
        self.assertNotIn("УЗНАТЬ", {row["proposed_ru"] for row in self.patch})
        self.assertNotIn("ОБУЧЕНИЕ", {row["proposed_ru"] for row in self.patch})
        self.assertNotIn("ЛЕСТНИЦА", {row["proposed_ru"] for row in self.patch})

    def test_five_human_revisions_are_exact(self):
        expected = {
            "interface:main_menu_leanatorium": "СПРАВКА",
            "interface:loading_stage_entering": "Вход в Ньюэрт",
            "interface:loading_stage_units": "Загрузка юнитов",
            "interface:profile_skillrating": "Рейтинг мастерства",
            "interface:player_stats_mostplayed": "Герои по числу матчей",
        }
        for key, value in expected.items():
            self.assertEqual(self.by_key[key]["proposed_ru"], value)

    def test_current_source_hashes_match_authoritative_index(self):
        for row in self.patch:
            source = self.sources[row["logical_key"]]
            actual = hashlib.sha256(row["current_source"].encode("utf-8")).hexdigest()
            self.assertEqual(actual, row["current_source_hash"])
            self.assertEqual(actual, source["current_source_hash"])

    def test_placeholders_markup_and_numbers_preserved(self):
        for row in self.patch:
            safe, differences = structural_comparison(row["current_source"], row["proposed_ru"])
            self.assertTrue(safe, (row["logical_key"], differences))
            self.assertTrue(row["validation"]["structure_preserved"])
            self.assertFalse(row["validation"]["gameplay_numbers_changed"])

    def test_no_protected_or_mechanical_domains(self):
        protected = {"item_name", "hero_name", "ability_name", "boss_name", "cosmetic_name"}
        for row in self.patch:
            self.assertEqual(row["domain"], "interface")
            self.assertEqual(row["runtime_role"], "DISPLAY_TEXT")
            self.assertNotIn(row["category"], protected)
            self.assertFalse(row["logical_key"].startswith(("entities:Item_", "entities:Ability_", "entities:Hero_")))

    def test_forbidden_forms_and_raw_ids_absent(self):
        forbidden = ("нести", "переносить", "без звука", "в недоумении", "юнитволкинг", "Посох Мастера", "Аганим")
        for row in self.patch:
            folded = row["proposed_ru"].casefold()
            self.assertFalse(any(term.casefold() in folded for term in forbidden))
            self.assertFalse(row["validation"]["raw_internal_id"])

    def test_layout_metrics_and_risks(self):
        risks = [row for row in self.patch if row["layout"]["layout_risk"]]
        self.assertEqual(len(risks), self.validation["layout_risks"])
        self.assertTrue(all(row["layout"]["compact_context"] for row in risks))
        self.assertTrue(all(row["layout"]["en_length"] > 0 and row["layout"]["ru_length"] > 0 for row in self.patch))

    def test_most_played_review_is_resolved(self):
        row = self.by_key["interface:player_stats_mostplayed"]
        self.assertEqual(row["status"], "HUMAN_APPROVED")
        self.assertEqual(row["proposed_ru"], "Герои по числу матчей")

    def test_translation_memory_contains_approved_batch(self):
        memory = load_jsonl(ROOT / "translation" / "translation_memory.jsonl")
        batch = [row for row in memory if row.get("batch_id") == "CONTROLLED_001_MODERN_UI"]
        self.assertEqual(len(batch), 39)
        self.assertTrue(all(row["approval_state"] == "HUMAN_APPROVED_PENDING_RUNTIME" for row in batch))
        self.assertTrue(all(row["human_review_state"] == "APPROVED" for row in batch))
        self.assertTrue(all(not row["runtime_verified"] for row in batch))
        for row in batch:
            self.assertEqual(row["approved_ru"], self.by_key[row["logical_key"]]["proposed_ru"])
            self.assertEqual(row["current_source_hash"], self.by_key[row["logical_key"]]["current_source_hash"])

    def test_validation_report_passes(self):
        self.assertEqual(self.validation["result"], "PASS")
        self.assertEqual(self.validation["errors"], [])
        self.assertTrue(all(value == "PASS" for value in self.validation["checks"].values()))
        self.assertTrue(self.validation["runtime"]["archive_built"])
        self.assertFalse(self.validation["runtime"]["archive_installed"])
        self.assertTrue(self.validation["runtime"]["isolated_test_deployed"])
        self.assertFalse(self.validation["runtime"]["runtime_verified"])

    def test_runtime_resolution_fix_is_exact(self):
        expected = sorted([
            "stringtables/interface_ru.str",
            "ui/fe3/sections/system_bar.package",
            "ui/hd_ui/templates/menu_vote_templates.package",
        ])
        self.assertEqual(self.build_report["archive_delta"]["changed"], expected)
        self.assertEqual(self.build_report["archive_delta"]["added"], [])
        self.assertEqual(self.build_report["archive_delta"]["removed"], [])
        archive_path = Path(self.build_report["output"]["path"])
        if not archive_path.is_file():
            self.skipTest("isolated runtime archive is a local QA artifact")
        with zipfile.ZipFile(archive_path) as archive:
            system_bar = archive.read("ui/fe3/sections/system_bar.package").decode("utf-8-sig")
            game_menu = archive.read("ui/hd_ui/templates/menu_vote_templates.package").decode("utf-8-sig")
        self.assertIn('label="СПРАВКА"', system_bar)
        self.assertIn('label="РЕЙТИНГ"', system_bar)
        self.assertNotIn('label="УЗНАТЬ"', system_bar)
        self.assertNotIn('label="ЛЕСТНИЦА"', system_bar)
        self.assertIn('label="game_menu_{btnName}_button"', game_menu)
        self.assertNotIn('game_menu_{btnName}_кнопка', game_menu)


if __name__ == "__main__":
    unittest.main()
