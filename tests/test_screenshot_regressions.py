"""Screenshot regressions: inspect isolated artifacts, never launch/install HoN."""
import hashlib
import json
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "build/human-ru-current/resources0.jz"


class TranslationPackets(unittest.TestCase):
    def test_no_duplicate_reviewed_keys(self):
        seen = set()
        for path in (ROOT / "translation/human").glob("batch_*.json"):
            for entry in json.loads(path.read_text(encoding="utf-8"))["entries"]:
                for key in entry["keys"]:
                    self.assertNotIn(key, seen, (path.name, key))
                    seen.add(key)


@unittest.skipUnless(ARTIFACT.is_file(), "Build cumulative overlay first")
class ScreenshotArtifacts(unittest.TestCase):
    def setUp(self):
        self.archive = zipfile.ZipFile(ARTIFACT)
        self.addCleanup(self.archive.close)

    def test_current_native_outputs_are_packaged_without_stale_replacements(self):
        report = json.loads((ROOT / "translation/reports/current_native_overrides.json").read_text(encoding="utf-8"))
        self.assertEqual(report["result"], "PASS")
        for row in report["files"]:
            self.assertEqual(hashlib.sha256(self.archive.read(row["source_file"])).hexdigest(), row["sha256"], row["source_file"])

    def test_store_keeps_current_dependencies_and_loading_widgets(self):
        store = self.archive.read("ui/fe3/sections/store.package").decode("utf-8-sig")
        for marker in ('/ui/scripts/fe3/store_listpool.lua', 'store_cache_stage_label', 'store_cache_step_label'):
            self.assertIn(marker, store)
        self.assertNotIn('name="store_cachehack"', store)

    def test_screenshot_strings_and_existing_doom_translation_survive(self):
        for filename in ("batch_231_screenshot_ui.json", "batch_203_items_four_row_group_b.json"):
            packet = json.loads((ROOT / "translation/human" / filename).read_text(encoding="utf-8"))
            for entry in packet["entries"]:
                for logical_key in entry["keys"]:
                    domain, key = logical_key.split(":", 1)
                    table = dict(line.split("\t", 1) for line in self.archive.read(f"stringtables/{domain}_ru.str").decode("utf-8-sig").splitlines() if "\t" in line)
                    self.assertEqual(table[key], entry["ru"], logical_key)

    def test_no_previous_release_members_lost(self):
        with zipfile.ZipFile(ROOT / "release-assets/0.1.0-beta.18/resources0.jz") as previous:
            self.assertFalse(set(previous.namelist()) - set(self.archive.namelist()))

    def test_existing_translation_base_changes_only_reviewed_keys(self):
        reviewed = set()
        for path in (ROOT / "translation/human").glob("batch_*.json"):
            for entry in json.loads(path.read_text(encoding="utf-8"))["entries"]:
                reviewed.update(entry["keys"])
        def parse(raw):
            return dict(line.split("\t", 1) for line in raw.decode("utf-8-sig").splitlines() if "\t" in line)
        with zipfile.ZipFile(ROOT / "release-assets/0.1.0-beta.18/resources0.jz") as previous:
            for name in previous.namelist():
                if not name.endswith("_ru.str"):
                    continue
                domain = Path(name).name.removesuffix("_ru.str")
                before, after = parse(previous.read(name)), parse(self.archive.read(name))
                self.assertFalse(before.keys() - after.keys(), name)
                for key, value in before.items():
                    if f"{domain}:{key}" not in reviewed:
                        self.assertEqual(after[key], value, f"{domain}:{key}")

    def test_localized_profile_css_and_hotfix_news(self):
        css = self.archive.read("preact/dist/assets/index.css").decode("utf-8")
        import re
        label = re.search(r"(?:^|})\.record-box \.label\{([^}]+)", css)
        self.assertIsNotNone(label)
        self.assertIn("text-wrap:wrap", label.group(1))
        self.assertIn("width:100%", label.group(1))
        remote = self.archive.read("preact-remote/dist/index.js").decode("utf-8")
        self.assertIn("Исправления патча 0.12.6.1", remote)
        self.assertIn("Загрузка повторов снова работает", remote)


if __name__ == "__main__":
    unittest.main()
