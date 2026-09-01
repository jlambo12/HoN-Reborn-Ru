import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


audit = load_module("audit", ROOT / "tools" / "audit.py")
builder = load_module("build_locale", ROOT / "tools" / "build_locale.py")
phase16 = load_module("phase16_hardening", ROOT / "tools" / "phase16_hardening.py")
TOKEN_POLICY = phase16.load_token_policy(ROOT / "catalog" / "technical_tokens.json")


def sample_row(english: str, russian: str, protected_terms=None, locked_spans=None):
    return {
        "id": "test:key",
        "key": "key",
        "english": english,
        "russian": russian,
        "status": "TRANSLATE",
        "runtime_role": "DISPLAY_TEXT",
        "protected_terms": protected_terms or [],
        "locked_spans": locked_spans or [],
        "english_hash": hashlib.sha256(english.encode("utf-8")).hexdigest(),
    }


class ClassifierUnitTests(unittest.TestCase):
    def assert_classification(self, namespace, key, english, status, category, runtime_role="DISPLAY_TEXT"):
        result = audit.classify(namespace, key, english)
        self.assertEqual((result[2], result[0], result[4]), (status, category, runtime_role))

    def test_parse_stringtable_comments_empty_and_values(self):
        rows, malformed = audit.parse_stringtable("// comment\nkey\tValue with spaces\nempty_key\n")
        self.assertEqual(malformed, [])
        self.assertEqual([(row.key, row.value) for row in rows], [("key", "Value with spaces"), ("empty_key", "")])

    def test_announcer_settings_and_ui_translate(self):
        self.assert_classification("interface", "options_newannouncervolume", "Event Announcer Volume (%)", "TRANSLATE", "settings_ui")
        self.assert_classification("interface", "vanity_cat_announcer", "Announcers", "TRANSLATE", "functional_ui")
        self.assert_classification("interface", "store2_gamevanity_announcers", "Announcers", "TRANSLATE", "functional_ui")

    def test_announcer_event_identity_is_contextual(self):
        self.assert_classification("interface", "announcement_doubletap", "Double Tap", "KEEP_EN", "announcer_event")
        self.assert_classification("interface", "announcement_victory", "Victory", "KEEP_EN", "announcer_event")
        self.assert_classification("interface", "match_history_victory", "VICTORY", "TRANSLATE", "profile_competitive_ui")

    def test_immortal_pride_name_description_and_metadata(self):
        self.assert_classification("entities", "Item_ImmortalPride_name", "Immortal Pride", "KEEP_EN", "item_name")
        self.assert_classification("entities", "Item_ImmortalPride_description_simple", "Activate to gain Strength.", "TRANSLATE", "item_description")
        self.assert_classification("entities", "Item_ImmortalPride_search_terms", "immortal,pride", "REVIEW", "search_metadata", "SEARCH_METADATA")
        self.assert_classification("entities", "Item_ImmortalPride_shop_categories", "Filter_Damage", "REVIEW", "shop_metadata", "INTERNAL_ID")

    def test_structural_token_boundaries_for_cosmetics(self):
        self.assert_classification("entities", "Hero_EmeraldWarden_name", "Emerald Warden", "KEEP_EN", "hero_name")
        result = audit.classify("interface", "boss_info_kongor_reward1_name", "Gold & Experience")
        self.assertNotEqual(result[0], "cosmetic_name")

    def test_name_variants_are_protected(self):
        self.assert_classification("entities", "Ability_Aluna4_name:ult_boost", "Emerald Red", "KEEP_EN", "ability_name")
        self.assert_classification("entities", "Item_Bottle_name:bottle_3", "Bottle (3/3)", "KEEP_EN", "item_name")

    def test_hero_role_is_description(self):
        self.assert_classification("entities", "Hero_Accursed_role", "Accursed is a support hero.", "TRANSLATE", "hero_description")

    def test_command_token_and_help_are_separate(self):
        self.assert_classification("client_messages", "chat_command_whisper", "/w", "REVIEW", "chat_command_token", "COMMAND_TOKEN")
        self.assert_classification("client_messages", "chat_command_whisper_info", "^279*^707 /w <name> <message>.", "TRANSLATE", "chat_command_help")

    def test_escape_only_value_is_structural(self):
        self.assert_classification("entities", "Ability_Test_description2:x", r"\r\n", "KEEP_EN", "structural_value", "STRUCTURAL")


class CatalogRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.all_rows = [json.loads(line) for line in (ROOT / "catalog" / "strings.jsonl").read_text(encoding="utf-8").splitlines()]
        cls.rows = {row["key"]: row for row in cls.all_rows}

    def assert_catalog(self, key, status, category, runtime_role="DISPLAY_TEXT"):
        row = self.rows[key]
        self.assertEqual((row["status"], row["category"], row["runtime_role"]), (status, category, runtime_role))

    def test_known_catalog_regressions(self):
        cases = [
            ("options_newannouncervolume", "TRANSLATE", "settings_ui", "DISPLAY_TEXT"),
            ("announcement_doubletap", "KEEP_EN", "announcer_event", "DISPLAY_TEXT"),
            ("Item_ImmortalPride_name", "KEEP_EN", "item_name", "DISPLAY_TEXT"),
            ("Item_ImmortalPride_description_simple", "TRANSLATE", "item_description", "DISPLAY_TEXT"),
            ("Hero_EmeraldWarden_name", "KEEP_EN", "hero_name", "DISPLAY_TEXT"),
            ("Ability_Aluna4_name:ult_boost", "KEEP_EN", "ability_name", "DISPLAY_TEXT"),
            ("Item_Bottle_name:bottle_3", "KEEP_EN", "item_name", "DISPLAY_TEXT"),
            ("Hero_Accursed_role", "TRANSLATE", "hero_description", "DISPLAY_TEXT"),
            ("Item_ImmortalPride_shop_categories", "REVIEW", "shop_metadata", "INTERNAL_ID"),
            ("Item_ImmortalPride_search_terms", "REVIEW", "search_metadata", "SEARCH_METADATA"),
        ]
        for case in cases:
            with self.subTest(key=case[0]):
                self.assert_catalog(*case)
        self.assertNotEqual(self.rows["boss_info_kongor_reward1_name"]["category"], "cosmetic_name")

    def test_silenced_status_is_translatable_without_lock(self):
        row = self.rows["silenced_title"]
        self.assertEqual((row["status"], row["protected_terms"]), ("TRANSLATE", []))

    def test_state_bramble_ward_is_not_cosmetic(self):
        row = self.rows["State_Bramble_Ward_Attack_name"]
        self.assertEqual((row["status"], row["category"]), ("TRANSLATE", "state_status_label"))

    def test_interface_test_suite_is_dev_test(self):
        row = self.rows["test_suite_title"]
        self.assertEqual((row["status"], row["runtime_role"], row["category"]), ("KEEP_EN", "DEV_TEST", "test_suite"))

    def test_boss_name_and_ability_policy(self):
        self.assert_catalog("Neutral_Kongor_name", "KEEP_EN", "boss_name")
        self.assert_catalog("Ability_Kongor1_name", "KEEP_EN", "ability_name")
        self.assert_catalog("Ability_Kongor1_description", "TRANSLATE", "ability_description")

    def test_game_ping_danger_is_translatable(self):
        self.assert_catalog("ping_ext_ground_danger_here_generic", "TRANSLATE", "game_ping")

    def test_match_history_victory_is_translatable(self):
        self.assert_catalog("matchmaking_victory_cap", "TRANSLATE", "functional_ui")

    def test_preact_match_history_victory_and_defeat_translate(self):
        rows = [json.loads(line) for line in (ROOT / "catalog" / "preact_ui.jsonl").read_text(encoding="utf-8").splitlines() if line]
        results = {(row["english"], row["status"], row["category"]) for row in rows if row["english"] in {"Victory", "Defeat"}}
        self.assertEqual(results, {("Victory", "TRANSLATE", "match_result"), ("Defeat", "TRANSLATE", "match_result")})

    def test_catalog_phase16_schema_and_unique_ids(self):
        rows = self.all_rows
        roles = {"DISPLAY_TEXT", "COMMAND_TOKEN", "INTERNAL_ID", "RESOURCE_PATH", "SEARCH_METADATA", "STRUCTURAL", "DYNAMIC_DATA", "DEV_TEST", "TECHNICAL_COPY", "KEYCAP"}
        self.assertEqual(len({row["id"] for row in rows}), len(rows))
        self.assertTrue(all(row["runtime_role"] in roles and "locked_spans" in row for row in rows))


class Phase16PolicyTests(unittest.TestCase):
    def test_technical_mmr(self):
        self.assertEqual(phase16.technical_kind("MMR", TOKEN_POLICY), "stat_abbreviation")

    def test_short_ui_play_is_not_technical(self):
        self.assertIsNone(phase16.technical_kind("Play", TOKEN_POLICY))

    def test_ctrl_keycap(self):
        self.assertEqual(phase16.technical_kind("Ctrl", TOKEN_POLICY), "keycap")

    def test_enter_keycap(self):
        self.assertEqual(phase16.technical_kind("Enter", TOKEN_POLICY), "keycap")

    def test_region_codes(self):
        self.assertEqual(phase16.technical_kind("EU", TOKEN_POLICY), "region_code")
        self.assertEqual(phase16.technical_kind("USW", TOKEN_POLICY), "region_code")

    def test_country_name_is_not_code(self):
        self.assertIsNone(phase16.technical_kind("United States", TOKEN_POLICY))

    def test_punctuation_only(self):
        self.assertEqual(phase16.nontext_kind("-"), "punctuation")

    def test_markup_only(self):
        self.assertEqual(phase16.nontext_kind("^279"), "markup_only")

    def test_numeric_only(self):
        self.assertEqual(phase16.nontext_kind("1"), "number")

    def test_game_message_announcer_event(self):
        self.assertEqual(phase16.classify_game_message("multikill0", "Double Tap")[0], "KEEP_EN")

    def test_phase17_combat_feed_is_kept(self):
        for key in ("teamkillstreak", "teamwipe", "humiliation", "payback", "rival"):
            with self.subTest(key=key):
                self.assertEqual(phase16.classify_game_message(key, "event")[0], "KEEP_EN")

    def test_phase17_leave_feed_is_kept(self):
        for key in ("client_disconnected", "client_reconnected", "client_timedout"):
            with self.subTest(key=key):
                self.assertEqual(phase16.classify_game_message(key, "event")[0], "KEEP_EN")

    def test_disconnect_diagnostic_is_translatable(self):
        status, _, _ = phase16.classify_game_message("bad_snapshot", "You have been disconnected because your client's files do not match")
        self.assertEqual(status, "TRANSLATE")

    def test_popup_deny_catalog_policy(self):
        row = {"id": "entities:Popup_deny", "key": "Popup_deny", "english": "Denied!", "namespace": "entities", "source_file": "stringtables/entities_en.str", "status": "REVIEW", "runtime_role": "DISPLAY_TEXT", "category": "entity_review", "russian": ""}
        phase16.apply_catalog_policy([row], TOKEN_POLICY)
        self.assertEqual(row["status"], "KEEP_EN")

    def test_game_message_ping(self):
        status, category, _ = phase16.classify_game_message("ping_ext_ground_danger_here_generic", "Danger!")
        self.assertEqual((status, category), ("TRANSLATE", "game_ping"))

    def test_game_message_legacy(self):
        self.assertEqual(phase16.classify_game_message("unused_lanes", "not used.")[0], "REVIEW")

    def canonical_dictionary(self, terms):
        groups = {key: [] for key in ("heroes", "abilities", "items", "bosses", "avatars_cosmetics", "announcer_events", "technical_tokens")}
        for term, source_key, strength in terms:
            groups["abilities"].append({
                "canonical_text": term, "type": "ABILITY", "source_key": source_key,
                "source_file": "stringtables/entities_en.str", "aliases": [],
                "case_policy": "EXACT", "protection_policy": "IMMUTABLE_VISIBLE_TEXT",
                "protection_strength": strength,
            })
        return groups

    def protected_row(self, key, english):
        return {"id": "entities:" + key, "key": key, "english": english, "status": "TRANSLATE", "runtime_role": "DISPLAY_TEXT", "category": "ability_description", "protected_terms": [], "locked_spans": []}

    def test_markup_webbed_shot_span(self):
        row = self.protected_row("Ability_Arachna1_description", "Applies ^oWebbed Shot^* now.")
        phase16.assign_locked_spans([row], self.canonical_dictionary([("Webbed Shot", "Ability_Arachna1_name", "EXACT")]))
        self.assertEqual((row["locked_spans"][0]["canonical_text"], row["locked_spans"][0]["markup_prefix"], row["locked_spans"][0]["markup_suffix"]), ("Webbed Shot", "^o", "^*"))

    def test_numeric_markup_arcane_bolts_span(self):
        row = self.protected_row("Ability_Artesia2_description", "Fires ^494Arcane Bolts^* now.")
        phase16.assign_locked_spans([row], self.canonical_dictionary([("Arcane Bolts", "Ability_Artesia2_name", "EXACT")]))
        self.assertEqual(row["locked_spans"][0]["markup_prefix"], "^494")

    def test_unmarked_contextual_sear_span(self):
        row = self.protected_row("Ability_Accursed3_description", "Applies Sear to enemies.")
        phase16.assign_locked_spans([row], self.canonical_dictionary([("Sear", "Ability_Accursed3_name", "CONTEXTUAL")]))
        self.assertEqual(row["protected_terms"], ["Sear"])

    def test_multiple_protected_terms(self):
        row = self.protected_row("Ability_Arachna1_description", "Webbed Shot then Hardened Carapace.")
        dictionary = self.canonical_dictionary([("Webbed Shot", "Ability_Arachna1_name", "EXACT"), ("Hardened Carapace", "Ability_Arachna2_name", "EXACT")])
        phase16.assign_locked_spans([row], dictionary)
        self.assertEqual(row["protected_terms"], ["Webbed Shot", "Hardened Carapace"])

    def test_controlled_announcer_aliases_are_locked(self):
        source_rows = []
        for key, text in (("doubletap", "Double Tap"), ("smackdown", "Smackdown"),
                          ("annihilation", "Annihilation"), ("humiliation", "Humiliation"),
                          ("quadkill", "Quad Kill")):
            source_rows.append({"key": "announcement_" + key, "english": text, "namespace": "interface", "source_file": "stringtables/interface_en.str"})
        dictionary = phase16.build_canonical_dictionary(source_rows, TOKEN_POLICY)
        aliases = ("Double Taps", "Smackdowns", "Annihilations", "Humiliations", "Quad Kills")
        row = self.protected_row("profile_record", " / ".join(aliases))
        row["category"] = "preact_ui"
        phase16.assign_locked_spans([row], dictionary)
        self.assertEqual(row["protected_terms"], list(aliases))

    def test_preact_branded_stats_and_tooltip(self):
        source = [{"key": "announcement_smackdown", "english": "Smackdown", "namespace": "interface", "source_file": "stringtables/interface_en.str"}]
        dictionary = phase16.build_canonical_dictionary(source, TOKEN_POLICY)
        standalone = {"english": "Smackdowns", "source_file": "preact/src/layers/profile/records.tsx", "context": "Display property label", "status": "TRANSLATE", "runtime_role": "DISPLAY_TEXT"}
        tooltip = {"english": "Smackdowns are a measure of skill.", "source_file": "preact/src/layers/profile/records.tsx", "context": "Display property tooltip", "status": "TRANSLATE", "runtime_role": "DISPLAY_TEXT"}
        phase16.classify_preact([standalone, tooltip], TOKEN_POLICY, dictionary)
        self.assertEqual(standalone["status"], "KEEP_EN")
        self.assertEqual((tooltip["status"], tooltip["protected_terms"]), ("TRANSLATE", ["Smackdowns"]))

    def test_preact_victory_context_split(self):
        dictionary = self.canonical_dictionary([])
        dictionary["announcer_events"] = [{"canonical_text": "Victory", "type": "ANNOUNCER_EVENT", "source_key": "announcement_victory", "source_file": "interface", "aliases": [], "case_policy": "EXACT", "protection_policy": "IMMUTABLE_VISIBLE_TEXT", "protection_strength": "CONTEXTUAL"}]
        history = {"english": "Victory", "source_file": "preact/src/layers/profile/matchhistory.tsx", "context": "Match result", "status": "TRANSLATE", "runtime_role": "DISPLAY_TEXT"}
        preview = {"english": "Victory", "source_file": "preact/src/layers/announcer/preview.tsx", "context": "Preview", "status": "TRANSLATE", "runtime_role": "DISPLAY_TEXT"}
        phase16.classify_preact([history, preview], TOKEN_POLICY, dictionary)
        self.assertEqual((history["status"], preview["status"]), ("TRANSLATE", "KEEP_EN"))

    def test_english_change_merge_empty_translation(self):
        row = {"status": "TRANSLATE", "english": "New", "russian": "", "protected_reason": "", "notes": ""}
        audit.merge_english_changed(row, {"status": "TRANSLATE", "russian": "", "notes": ""})
        self.assertEqual(row["status"], "TRANSLATE")

    def test_english_change_merge_existing_translation(self):
        row = {"status": "TRANSLATE", "english": "New", "russian": "", "protected_reason": "", "notes": ""}
        audit.merge_english_changed(row, {"status": "TRANSLATE", "russian": "Старый", "notes": ""})
        self.assertEqual((row["status"], row["russian"]), ("REVIEW", "Старый"))

    def test_unchanged_review_does_not_drift_with_global_dictionary(self):
        row = {"status": "KEEP_EN", "category": "ability_name", "classification_version": 2, "protected_terms": ["Teleport"], "locked_spans": [{"canonical_text": "Teleport"}]}
        previous = {"status": "TRANSLATE", "category": "ability_description", "classification_version": 3, "protected_terms": [], "locked_spans": [], "russian": "Телепортируется"}
        audit.preserve_unchanged_review(row, previous)
        self.assertEqual((row["status"], row["category"], row["protected_terms"], row["locked_spans"], row["russian"]), ("TRANSLATE", "ability_description", [], [], "Телепортируется"))

    def test_longest_overlapping_canonical_name(self):
        row = self.protected_row("Ability_Artesia2_description", "Arcane Bolts are fired.")
        dictionary = self.canonical_dictionary([("Arcane Bolt", "Ability_Artesia2_name", "EXACT"), ("Arcane Bolts", "Ability_Artesia2_name", "EXACT")])
        phase16.assign_locked_spans([row], dictionary)
        self.assertEqual(row["protected_terms"], ["Arcane Bolts"])

    def test_state_is_not_a_canonical_dictionary_source(self):
        rows = [
            {"key": "Ability_Arachna1_name", "english": "Webbed Shot", "namespace": "entities", "source_file": "stringtables/entities_en.str"},
            {"key": "State_Test_name", "english": "Silenced", "namespace": "entities", "source_file": "stringtables/entities_en.str"},
        ]
        dictionary = phase16.build_canonical_dictionary(rows, TOKEN_POLICY)
        self.assertNotIn("Silenced", {entry["canonical_text"] for entry in dictionary["abilities"]})

    def test_preact_country_policy(self):
        row = {"english": "United States", "source_file": "preact/src/config/flags.ts", "context": "COUNTRY_MAP display name", "status": "TRANSLATE", "runtime_role": "DISPLAY_TEXT", "protected_terms": []}
        phase16.classify_preact([row], TOKEN_POLICY, self.canonical_dictionary([]))
        self.assertEqual((row["status"], row["category"]), ("TRANSLATE", "country_display_name"))


class BuilderValidationTests(unittest.TestCase):
    def error_codes(self, row):
        errors, _ = builder.validate([row], allow_fallback=False)
        return {error["code"] for error in errors}

    def test_named_and_numeric_brace_tokens_preserved(self):
        english = "{killer_color}{killer} hit {player}: {75,110,145,180} ({attempt}/{maxattempts})"
        good = "{killer_color}{killer} атаковал {player}: {75,110,145,180} ({attempt}/{maxattempts})"
        self.assertEqual(self.error_codes(sample_row(english, good)), set())
        bad = good.replace("{maxattempts}", "{max_attempts}").replace("{75,110,145,180}", "{75,110}")
        self.assertIn("brace_token_mismatch", self.error_codes(sample_row(english, bad)))

    def test_full_hon_controls_and_literal_escapes_preserved(self):
        english = r"^279{name}^707 won^*\n^oOrange ^gGreen ^rRed ^yYellow ^vViolet"
        good = r"^279{name}^707 победил^*\n^oОранжевый ^gЗелёный ^rКрасный ^yЖёлтый ^vФиолетовый"
        self.assertEqual(self.error_codes(sample_row(english, good)), set())
        bad = good.replace("^279", "^27").replace(r"\n", r"\r")
        codes = self.error_codes(sample_row(english, bad))
        self.assertIn("hon_control_mismatch", codes)
        self.assertIn("literal_escape_mismatch", codes)

    def test_printf_template_angle_and_protected_terms(self):
        english = "%s ${player} used <ability> Smackdown"
        good = "%s ${player} применил <ability> Smackdown"
        self.assertEqual(self.error_codes(sample_row(english, good, ["Smackdown"])), set())
        bad = "%d ${hero} применил <skill> Смакдаун"
        codes = self.error_codes(sample_row(english, bad, ["Smackdown"]))
        self.assertTrue({"printf_token_mismatch", "template_token_mismatch", "angle_token_mismatch", "protected_term_mismatch"}.issubset(codes))

    def test_markup_locked_span_can_move(self):
        english = "Increases ^oWebbed Shot^* damage."
        start = english.index("Webbed Shot")
        span = {"canonical_text": "Webbed Shot", "type": "ABILITY", "source_start": start, "source_end": start + len("Webbed Shot"), "visible_start": 10, "visible_end": 21, "case_policy": "EXACT", "markup_prefix": "^o", "markup_suffix": "^*"}
        good = "Урон ^oWebbed Shot^* увеличивается."
        self.assertEqual(self.error_codes(sample_row(english, good, ["Webbed Shot"], [span])), set())

    def test_markup_locked_span_rejects_translation(self):
        english = "Increases ^494Arcane Bolts^* damage."
        start = english.index("Arcane Bolts")
        span = {"canonical_text": "Arcane Bolts", "type": "ABILITY", "source_start": start, "source_end": start + len("Arcane Bolts"), "visible_start": 10, "visible_end": 22, "case_policy": "EXACT", "markup_prefix": "^494", "markup_suffix": "^*"}
        bad = "Урон ^494Тайных зарядов^* увеличивается."
        self.assertIn("locked_visible_span_mismatch", self.error_codes(sample_row(english, bad, ["Arcane Bolts"], [span])))


if __name__ == "__main__":
    unittest.main(verbosity=2)
