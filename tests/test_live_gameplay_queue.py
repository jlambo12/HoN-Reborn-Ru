import unittest

from tools.localization.build_live_gameplay_queue import (
    build_queue,
    is_gameplay_description_key,
    is_effectively_empty,
    is_noncontent_record,
    parse_stringtable,
    priority_tier,
    protected_spans,
    structural_signature,
    structural_tokens,
    translation_status,
)


class LiveGameplayQueueTests(unittest.TestCase):
    def test_stringtable_last_duplicate_wins(self):
        rows = parse_stringtable(b"key first\nkey second\nempty\n")
        self.assertEqual(rows["key"], "second")
        self.assertEqual(rows["empty"], "")

    def test_only_gameplay_description_fields_are_selected(self):
        self.assertTrue(is_gameplay_description_key("Ability_Test_description_simple"))
        self.assertTrue(is_gameplay_description_key("State_Test_FRAME_effect"))
        self.assertFalse(is_gameplay_description_key("Hero_Test_description"))
        self.assertFalse(is_gameplay_description_key("Ability_Test_tooltip_flavor"))
        self.assertFalse(is_gameplay_description_key("Item_Test_name"))
        self.assertFalse(is_gameplay_description_key("Item_Test_search_terms"))

    def test_escaped_whitespace_sentinels_are_empty(self):
        self.assertTrue(is_effectively_empty("\\r"))
        self.assertTrue(is_effectively_empty("\\n\\r"))
        self.assertFalse(is_effectively_empty("Actual text\\n"))
        self.assertTrue(is_noncontent_record("State_Test_effect_header", "None"))
        self.assertFalse(is_noncontent_record("State_Test_description", "None"))

    def test_structural_tokens_are_preserved_for_review(self):
        text = "^oDeals {10,20}% damage^* to #target# for %d seconds"
        self.assertEqual(structural_tokens(text), ["^o", "{10,20}", "^*", "#target#", "%d"])
        self.assertEqual(structural_signature("A\\n{v}"), structural_signature("Б\\n{v}"))
        self.assertNotEqual(structural_signature("A\\n{v}"), structural_signature("Б {v}"))

    def test_protected_names_are_found(self):
        text = "Staff of the Master improves Hellflower."
        self.assertEqual(protected_spans(text, {"Hellflower", "Staff of the Master"}), ["Staff of the Master", "Hellflower"])

    def test_changed_current_english_marks_manual_translation_stale(self):
        key = "entities:Ability_Test_description"
        manual = {key: {"ru": "Текст", "batch_id": "TEST"}}
        catalog = {key: {"english_hash": "not-current"}}
        self.assertEqual(translation_status(key, "Current", catalog, manual), "STALE_REVIEW")
        self.assertEqual(translation_status(key, "Current", catalog, {}), "TODO")

    def test_manual_current_hash_supersedes_lagging_catalog(self):
        key = "entities:Ability_Test_description"
        current_hash = __import__("hashlib").sha256(b"Current").hexdigest()
        manual = {key: {"ru": "Текст", "batch_id": "TEST", "english_hash": current_hash}}
        catalog = {key: {"english_hash": "old"}}
        self.assertEqual(translation_status(key, "Current", catalog, manual), "DONE")

    def test_priority_tiers(self):
        self.assertEqual(priority_tier("INVALID_REVIEW", "hero_ability"), "P0")
        self.assertEqual(priority_tier("STALE_REVIEW", "item"), "P0")
        self.assertEqual(priority_tier("TODO", "hero_ability_state"), "P1")
        self.assertEqual(priority_tier("TODO", "item"), "P2")
        self.assertEqual(priority_tier("TODO", "interface"), "P3")

    def test_ability_title_homonym_is_not_mechanically_locked(self):
        heroes = [{"name": "Hero_Test", "translatedName": "Tester", "id": 1}]
        strings = {
            "Ability_Test1_name": "Release",
            "Ability_Test1_description": "Release a wave with Staff of the Master.",
        }
        logical_key = "entities:Ability_Test1_description"
        english = strings["Ability_Test1_description"]
        catalog = {logical_key: {
            "english_hash": __import__("hashlib").sha256(english.encode()).hexdigest(),
            "locked_spans": [
                {"canonical_text": "Release", "type": "ABILITY"},
                {"canonical_text": "Staff of the Master", "type": "ITEM"},
            ],
        }}
        manual = {logical_key: {
            "ru": "Выпускает волну с Staff of the Master.", "batch_id": "TEST",
        }}
        row = build_queue(heroes, [], strings, catalog, manual)[0]
        self.assertEqual(row["protected_spans"], ["Staff of the Master"])
        self.assertEqual(row["status"], "DONE")


if __name__ == "__main__":
    unittest.main()
