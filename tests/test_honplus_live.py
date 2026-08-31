import subprocess
import sys
import tempfile
import unittest
import zipfile
import shutil
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]


class HoNPlusLiveTests(unittest.TestCase):
    def test_native_package_is_well_formed_and_uses_expected_anchor(self):
        package = ROOT / "src" / "honplus_native" / "ui" / "hd_ui" / "sections" / "honplus_live.package"
        tree = ElementTree.parse(package)
        root_panel = tree.getroot().find("panel")
        self.assertEqual("honplus_live_root", root_panel.attrib["name"])
        self.assertEqual("5.2h", root_panel.attrib["x"])
        self.assertEqual("4.0h", root_panel.attrib["y"])
        self.assertEqual("20.0h", root_panel.attrib["width"])
        self.assertEqual("11.5h", root_panel.attrib["height"])
        self.assertIn('content="ИМПАКТ"', package.read_text(encoding="utf-8"))
        self.assertNotIn('font="dyn_bold_5"', package.read_text(encoding="utf-8"))
        self.assertNotIn('font="dyn_bold_6"', package.read_text(encoding="utf-8"))

    def test_live_lua_is_local_and_uses_native_match_watches(self):
        source = (ROOT / "src" / "honplus_native" / "ui" / "scripts" / "game" / "honplus_live.lua").read_text(encoding="utf-8")
        for watch in ("PlayerScore", "MatchTime", "AlliesAndEnemiesHeroInfo", "AlliesAndEnemiesPlayerInfo"):
            self.assertIn(watch, source)
        for forbidden in ("http://", "https://", "127.0.0.1", "benchmarks.json"):
            self.assertNotIn(forbidden, source)
        self.assertIn("local slot = index", source)

    def test_generated_benchmarks_are_split_for_the_legacy_lua_compiler(self):
        data_dir = ROOT / "src" / "honplus_native" / "ui" / "scripts" / "game"
        chunks = sorted(data_dir.glob("honplus_live_data_*.lua"))
        self.assertGreaterEqual(len(chunks), 16)
        self.assertLess(max(path.stat().st_size for path in chunks), 100_000)

    def test_native_preparer_patches_the_known_loaded_vanity_package(self):
        base = """<?xml version=\"1.0\"?><package>
<panel name=\"vanity_shop_header_tabs\" />
</package>"""
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory) / "project"
            shutil.copytree(ROOT / "src" / "honplus_native", temp_root / "src" / "honplus_native")
            archive = Path(directory) / "resources0.jz"
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("ui/hd_ui/sections/ig_vanity_shop.package", base)
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "prepare_honplus_native.py"), "--project-root", str(temp_root), "--archive", str(archive)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            patched = (temp_root / "src" / "extended_ru" / "ui" / "hd_ui" / "sections" / "ig_vanity_shop.package").read_text(encoding="utf-8")
            self.assertIn("honplus_live_data.lua", patched)
            self.assertIn('name="honplus_live_root"', patched)
            self.assertIn('onloadlua="HoNPlusLive:Init()"', patched)
            self.assertNotIn("honplus_live.package", patched)

    def test_release_builds_prepare_native_hud(self):
        for name in ("build_phase2a.ps1", "build_pass_b.ps1"):
            source = (ROOT / "scripts" / name).read_text(encoding="utf-8")
            self.assertIn("prepare_honplus_native.py", source)

    def test_post_match_players_use_hero_cards_ranked_by_impact(self):
        source = (ROOT / "src" / "honplus_preact" / "HoNPlusPanel.tsx").read_text(encoding="utf-8")
        self.assertIn("gamestorage.juvio.com/heroes/${heroId}/icon.webp", source)
        self.assertIn("useMatchStats(requestedMatchId)", source)
        self.assertIn(".sort((left, right) => right.impact - left.impact)", source)
        self.assertIn("ИМПАКТ", source)


if __name__ == "__main__":
    unittest.main()
