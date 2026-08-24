import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PASS_C = ROOT / "build" / "pass-c" / "resources0.jz"
EXPECTED_PASS_C_SHA = "3d5ee66b9507c342d92b0be886d2918ea959e9beffb2126e6a7f77604142e301"


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line]


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ControlledBatch002Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch_path = ROOT / "translation" / "batches" / "controlled_002_terminology.jsonl"
        cls.batch = load_jsonl(cls.batch_path)
        cls.by_key = {row["logical_key"]: row for row in cls.batch}
        cls.validation = json.loads((ROOT / "translation" / "reports" / "controlled_002_validation.json").read_text(encoding="utf-8"))
        cls.resolution = json.loads((ROOT / "translation" / "reports" / "controlled_002_source_resolution.json").read_text(encoding="utf-8"))

    def test_candidate_is_narrow_and_unapplied(self):
        self.assertEqual(len(self.batch), 33)
        self.assertEqual(len(self.by_key), 33)
        self.assertTrue(all(row["status"] == "HUMAN_APPROVED" for row in self.batch))
        self.assertTrue(all(row["approval_state"] == "HUMAN_APPROVED_PENDING_RUNTIME" for row in self.batch))
        self.assertTrue(all(not row["applied"] and not row["runtime_verified"] for row in self.batch))
        self.assertFalse(self.validation["candidate_applied"])
        self.assertFalse(self.validation["runtime_verified"])

    def test_role_terminology_is_exact(self):
        expected = {
            "game_messages:filter_carry": "Керри",
            "interface:player_role_carry": "Керри",
            "interface:player_role_mid": "Мид",
            "interface:player_role_softsupport": "Поддержка",
            "interface:player_role_hardsupport": "Основная поддержка",
        }
        for key, value in expected.items():
            self.assertEqual(self.by_key[key]["proposed_ru"], value)
        self.assertEqual(self.validation["role_already_compliant"], {"interface:player_role_offlane": "Оффлейн"})
        self.assertFalse(any(row["proposed_ru"].casefold() in {"нести", "переносить"} for row in self.batch))

    def test_staff_repairs_are_span_only_and_keep_en(self):
        rows = [row for row in self.batch if row["reason"] == "restore_exact_keep_en_span"]
        self.assertEqual(len(rows), 28)
        for row in rows:
            self.assertIn("Staff of the Master", row["proposed_ru"])
            self.assertNotIn("персонал мастера", row["proposed_ru"].casefold())
            restored = row["proposed_ru"].replace("Staff of the Master", "Персонал Мастера")
            self.assertEqual(restored.casefold(), row["pass_c_baseline"].casefold())
            self.assertTrue(all(row["validation"].values()))

    def test_source_resolution_classes_are_explicit(self):
        records = {row["visible_text"]: row for row in self.resolution["records"]}
        self.assertEqual(records["Gameplay role labels (Preact)"]["classification"], "PREACT_LOCAL_ENUM_LABELS")
        self.assertEqual(records["Call Vote"]["classification"], "REVIEW_SOURCE_UNRESOLVED")
        self.assertEqual(records["MISSING"]["classification"], "NATIVE_HARDCODED_LITERAL")
        self.assertEqual(records["Teleportation Stone"]["classification"], "KEEP_EN_CANONICAL_ITEM_REFERENCE")
        self.assertEqual(records["Profile"]["classification"], "PREACT_LOCAL_LABELS_PLUS_REMOTE_API_DATA")
        self.assertEqual(records["MOTD"]["classification"], "REMOTE_CONTAINER_WITH_LOCAL_CHROME")
        self.assertEqual(records["Patch Notes"]["classification"], "BUNDLED_PREACT_EDITORIAL_CONTENT")
        self.assertEqual(records["ATTENTION overlay"]["classification"], "NATIVE_LOCAL_STRINGTABLE")

    def test_validation_passes(self):
        self.assertEqual(self.validation["result"], "PASS")
        self.assertEqual(self.validation["errors"], [])
        self.assertTrue(all(value == "PASS" for value in self.validation["checks"].values()))

    def test_pass_c_hash_is_unchanged(self):
        if not PASS_C.is_file():
            self.skipTest("pass-c archive is a local generated artifact")
        self.assertEqual(sha256(PASS_C), EXPECTED_PASS_C_SHA)
        self.assertEqual(self.resolution["baseline"]["sha256"], EXPECTED_PASS_C_SHA)
        self.assertTrue(self.resolution["baseline"]["unchanged"])

    def test_glossary_and_forbidden_policy(self):
        glossary = json.loads((ROOT / "translation" / "glossary_ru.json").read_text(encoding="utf-8"))
        terms = {row["source_term"]: row for row in glossary["entries"]}
        self.assertEqual(terms["Carry"]["approved_translation"], "Керри")
        self.assertEqual(terms["Mid"]["approved_translation"], "Мид")
        self.assertEqual(terms["Offlane"]["approved_translation"], "Оффлейн")
        self.assertEqual(terms["Soft Support"]["approved_translation"], "Поддержка")
        self.assertEqual(terms["Hard Support"]["approved_translation"], "Основная поддержка")
        forbidden = json.loads((ROOT / "translation" / "forbidden_ru.json").read_text(encoding="utf-8"))
        staff = next(row for row in forbidden["rules"] if row["id"] == "FORBID-STAFF-ALIASES")
        self.assertIn("Персонал Мастера", staff["forbidden"])

    def test_generator_is_deterministic(self):
        targets = [
            self.batch_path,
            ROOT / "translation" / "reports" / "controlled_002_source_resolution.json",
            ROOT / "translation" / "reports" / "controlled_002_validation.json",
            ROOT / "translation" / "reports" / "CONTROLLED_002_CANDIDATE_REPORT.md",
        ]
        before = {path: sha256(path) for path in targets}
        subprocess.run([sys.executable, str(ROOT / "tools" / "localization" / "prepare_controlled_002.py")], check=True)
        after = {path: sha256(path) for path in targets}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
