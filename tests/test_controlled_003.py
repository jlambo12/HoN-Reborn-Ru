import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PASS_C = ROOT / "build" / "pass-c" / "resources0.jz"
EXPECTED_PASS_C_SHA = "3d5ee66b9507c342d92b0be886d2918ea959e9beffb2126e6a7f77604142e301"


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line]


class Controlled003Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch = load_jsonl(ROOT / "translation" / "batches" / "controlled_003_consolidated.jsonl")
        cls.decisions = load_jsonl(ROOT / "translation" / "reports" / "controlled_003_all_current_decisions.jsonl")
        cls.validation = json.loads((ROOT / "translation" / "reports" / "controlled_003_validation.json").read_text(encoding="utf-8"))
        cls.build = json.loads((ROOT / "translation" / "reports" / "controlled_003_runtime_build.json").read_text(encoding="utf-8"))

    def test_every_current_key_has_one_decision(self):
        self.assertEqual(len(self.decisions), 19538)
        self.assertEqual(len({row["logical_key"] for row in self.decisions}), 19538)
        self.assertEqual(sum(self.validation["decision_counts"].values()), 19538)

    def test_candidate_is_unique_uninstalled_and_structurally_validated(self):
        self.assertEqual(len(self.batch), self.validation["candidate_entries"])
        self.assertEqual(len({row["logical_key"] for row in self.batch}), len(self.batch))
        self.assertTrue(all(not row["applied"] and not row["runtime_verified"] for row in self.batch))
        self.assertTrue(all(row["validation"]["source_hash_match"] for row in self.batch))
        self.assertFalse(self.build["installed"])
        self.assertFalse(self.build["runtime_verified"])

    def test_protected_terminology(self):
        values = {row["logical_key"]: row["proposed_ru"] for row in self.batch}
        self.assertEqual(values["interface:player_role_carry"], "Керри")
        self.assertEqual(values["interface:player_role_mid"], "Мид")
        self.assertEqual(values["interface:player_role_softsupport"], "Поддержка")
        self.assertEqual(values["interface:player_role_hardsupport"], "Основная поддержка")
        self.assertFalse(any("персонал мастера" in row["proposed_ru"].casefold() for row in self.batch))
        self.assertFalse(any("посох мастера" in row["proposed_ru"].casefold() for row in self.batch))
        self.assertFalse(any(row["proposed_ru"].casefold() in {"нести", "переносить"} for row in self.batch))

    def test_names_and_semantics_are_not_blindly_auto_translated(self):
        decisions = {row["logical_key"]: row for row in self.decisions}
        source = load_jsonl(ROOT / "translation" / "source_index.jsonl")
        for row in source:
            if row["category"] in {"hero_name", "item_name", "ability_name", "boss_name", "cosmetic_name"}:
                self.assertEqual(decisions[row["logical_key"]]["decision"], "KEEP_EN")
        for row in self.batch:
            if row["category"] in {"ability_description", "item_description", "hero_description", "boss_description"}:
                self.assertIn(row["reason"], {"reuse_controlled_002_terminology", "restore_protected_staff_exact_span"})

    def test_validation_and_build_pass(self):
        self.assertEqual(self.validation["result"], "PASS")
        self.assertEqual(self.build["result"], "PASS")
        self.assertEqual(self.build["output"]["crc"], "PASS")
        self.assertEqual(self.build["checks"]["deterministic_sha"], "PASS")
        if not PASS_C.is_file():
            self.skipTest("pass-c archive is a local generated artifact")
        self.assertEqual(hashlib.sha256(PASS_C.read_bytes()).hexdigest(), EXPECTED_PASS_C_SHA)


if __name__ == "__main__":
    unittest.main()
