import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.localization import build_hybrid_base as hybrid
from tools.localization.pre_d_donor_audit import structural_comparison
from tools.localization.resolve_candidate import resolve


def load_index(name):
    path = ROOT / "translation" / name
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


class HybridArchitectureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {row["logical_key"]: row for row in load_index("source_index.jsonl")}
        cls.candidates = {row["logical_key"]: row for row in load_index("candidate_index.jsonl")}

    def test_source_and_candidate_indexes_cover_current_keys_once(self):
        self.assertEqual(len(self.sources), 19538)
        self.assertEqual(set(self.sources), set(self.candidates))
        self.assertTrue(all(row["current_key_exists"] for row in self.sources.values()))

    def test_resolver_keeps_approved_separate_from_candidates(self):
        row = resolve("interface:Shop_Search_Shop", ROOT)
        self.assertEqual(row["recommended_status"], "APPROVED_EXISTING")
        self.assertEqual(row["candidates"]["approved"], "Поиск...")
        self.assertIsNotNone(row["candidates"]["donor"])
        self.assertIsNotNone(row["candidates"]["pass_c"])

    def test_keep_en_item_name(self):
        row = self.candidates["entities:Item_Hellflower_name"]
        self.assertEqual(row["recommended_status"], "KEEP_EN")
        self.assertIn("KEEP_EN_POLICY", row["flags"])
        self.assertTrue(row["auto_approved"])

    def test_forbidden_staff_translation_is_never_approved(self):
        row = self.candidates["entities:Ability_Accursed4_description_simple"]
        self.assertIn("FORBIDDEN_TRANSLATION", row["flags"])
        self.assertIn("KEEP_EN_STAFF_OF_THE_MASTER", row["policy_conflicts"])
        self.assertNotIn(row["recommended_status"], {"APPROVED_EXISTING", "KEEP_EN"})

    def test_structural_placeholder_comparison(self):
        safe, differences = structural_comparison("Deals {damage} for %d seconds", "Урон {damage} действует %d секунд")
        self.assertTrue(safe)
        self.assertEqual(differences, [])
        safe, differences = structural_comparison("Deals {damage} for %d seconds", "Наносит урон %d секунд")
        self.assertFalse(safe)
        self.assertIn("placeholders", differences)

    def test_approved_source_hash_must_match(self):
        comparison = {
            "domain": "interface", "key": "synthetic", "current_en": "Current",
            "current_sha256": hybrid.sha256_text("Current"), "donor_value": "Донор",
            "pass_c_value": "Pass", "donor_sha256": hybrid.sha256_text("Донор"),
            "pass_c_sha256": hybrid.sha256_text("Pass"), "donor_language": "RUSSIAN",
            "pass_c_language": "ENGLISH_ONLY", "donor_structure_safe": True,
            "pass_c_structure_safe": True, "donor_structure_differences": [],
            "pass_c_structure_differences": [], "audit_status": "TRANSLATE",
            "category": "functional_ui", "runtime_role": "DISPLAY_TEXT",
        }
        catalog = {"category": "functional_ui", "runtime_role": "DISPLAY_TEXT"}
        stale_memory = {"id": "TM-X", "approved_ru": "Одобрено", "source_hash": "stale", "approval_status": "APPROVED"}
        row = hybrid.resolve_candidate(comparison, catalog, stale_memory, [])
        self.assertNotEqual(row["recommended_status"], "APPROVED_EXISTING")
        current_memory = dict(stale_memory, source_hash=hybrid.sha256_text("Current"))
        row = hybrid.resolve_candidate(comparison, catalog, current_memory, [])
        self.assertEqual(row["recommended_status"], "APPROVED_EXISTING")

    def test_boss_donor_is_stale_semantic_review(self):
        row = self.candidates["interface:boss_info_kongor_desc"]
        self.assertEqual(row["recommended_status"], "SEMANTIC_REVIEW_REQUIRED")
        self.assertIn("POSSIBLY_STALE", row["flags"])
        self.assertIn("bosses_semantic", row["review_queues"])

    def test_domain_aware_modern_ui_priority(self):
        row = self.candidates["interface:store2_hero_role"]
        self.assertIn("MODERN_REBORN_UI", row["flags"])
        self.assertIn("modern_ui", row["review_queues"])
        self.assertEqual(row["recommended_status"], "PASS_C_CANDIDATE")

    def test_runtime_raw_menu_key_is_prioritized_but_not_approved(self):
        row = self.candidates["interface:game_menu_menu_button"]
        self.assertIn("RAW_KEY_RUNTIME_HISTORY", row["flags"])
        self.assertIn("RUNTIME_CONFIRMED", row["flags"])
        self.assertFalse(row["auto_approved"])

    def test_translation_memory_contains_only_explicit_approval(self):
        memory = load_index("translation_memory.jsonl")
        original = [row for row in memory if row.get("batch_id") is None]
        controlled = [row for row in memory if row.get("batch_id") == "CONTROLLED_001_MODERN_UI"]
        self.assertEqual(len(original), 1)
        self.assertEqual(original[0]["origin"], "PROJECT_APPROVED")
        self.assertEqual(original[0]["approval_status"], "APPROVED")
        self.assertEqual(len(controlled), 39)
        self.assertTrue(all(row["origin"] == "PROJECT_HUMAN_REVIEW" for row in controlled))
        self.assertTrue(all(row["approval_status"] == "HUMAN_APPROVED_PENDING_RUNTIME" for row in controlled))
        self.assertTrue(all(not row["runtime_verified"] for row in controlled))
        self.assertFalse(any(row["origin"] in {"DONOR", "PASS_C"} for row in memory))

    def test_every_declared_queue_has_a_deterministic_file(self):
        for queue in hybrid.QUEUE_NAMES:
            path = ROOT / "translation" / "review_queues" / f"{queue}.jsonl"
            self.assertTrue(path.is_file())
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
            self.assertEqual(rows, sorted(rows, key=lambda row: (-row["priority_score"], row["logical_key"])))


if __name__ == "__main__":
    unittest.main()
