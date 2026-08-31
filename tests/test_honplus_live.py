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
        self.assertEqual(".5h", root_panel.attrib["x"])
        self.assertEqual("4.0h", root_panel.attrib["y"])

    def test_live_lua_is_local_and_uses_native_match_watches(self):
        source = (ROOT / "src" / "honplus_native" / "ui" / "scripts" / "game" / "honplus_live.lua").read_text(encoding="utf-8")
        for watch in ("PlayerScore", "MatchTime", "AlliesAndEnemiesHeroInfo", "AlliesAndEnemiesPlayerInfo"):
            self.assertIn(watch, source)
        for forbidden in ("http://", "https://", "127.0.0.1", "benchmarks.json"):
            self.assertNotIn(forbidden, source)
        self.assertIn("local slot = index", source)

    def test_native_preparer_patches_a_game_interface_and_copies_assets(self):
        base = """<?xml version=\"1.0\"?><interface>
<lua file=\"/ui/scripts/game/damagebar.lua\" />
<panel onloadlua=\"noop\" />
\t\t\tIGVanity_Shop:Init()
\t<!-- Vanity Shop -->
</interface>"""
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory) / "project"
            shutil.copytree(ROOT / "src" / "honplus_native", temp_root / "src" / "honplus_native")
            archive = Path(directory) / "resources0.jz"
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("ui/game_hd.interface", base)
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "prepare_honplus_native.py"), "--project-root", str(temp_root), "--archive", str(archive)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            patched = (temp_root / "src" / "extended_ru" / "ui" / "game_hd.interface").read_text(encoding="utf-8")
            self.assertIn("honplus_live_data.lua", patched)
            self.assertIn("HoNPlusLive:Init()", patched)
            self.assertLess(patched.index("honplus_live.package"), patched.index("<!-- Vanity Shop -->"))

    def test_release_builds_prepare_native_hud(self):
        for name in ("build_phase2a.ps1", "build_pass_b.ps1"):
            source = (ROOT / "scripts" / name).read_text(encoding="utf-8")
            self.assertIn("prepare_honplus_native.py", source)


if __name__ == "__main__":
    unittest.main()
