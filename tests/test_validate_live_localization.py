import unittest

from tools.localization.build_live_gameplay_queue import sha256_bytes
from tools.localization.validate_live_localization import validate_rows


class FastLiveValidatorTests(unittest.TestCase):
    def test_valid_row_passes(self):
        english = "Deals ^o{10,20} damage^*."
        rows = [{
            "logical_key": "entities:Ability_Test_description",
            "english": english,
            "english_hash": sha256_bytes(english.encode("utf-8")),
            "existing_ru": "Наносит ^o{10,20} урона^*.",
            "scope": "hero_ability",
            "status": "DONE",
            "priority_tier": "P1",
            "protected_spans": [],
        }]
        self.assertEqual(validate_rows(rows), [])

    def test_missing_token_and_bad_tier_fail(self):
        english = "Deals {10,20} damage."
        rows = [{
            "logical_key": "entities:Item_Test_description",
            "english": english,
            "english_hash": sha256_bytes(english.encode("utf-8")),
            "existing_ru": "Наносит урон.",
            "scope": "item",
            "status": "DONE",
            "priority_tier": "P1",
            "protected_spans": [],
        }]
        codes = {error["code"] for error in validate_rows(rows)}
        self.assertEqual(codes, {"PRIORITY_MISMATCH", "STRUCTURAL_TOKEN_MISMATCH"})


if __name__ == "__main__":
    unittest.main()
