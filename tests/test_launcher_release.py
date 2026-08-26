import json
import itertools
import unittest
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "launcher" / "HoNRebornRu.Launcher"
UPDATER = ROOT / "launcher" / "HoNRebornRu.Updater"


def properties(project: Path) -> dict[str, str]:
    root = ET.parse(project).getroot()
    return {element.tag: (element.text or "").strip() for group in root.findall("PropertyGroup") for element in group}


class AutonomousLauncherTests(unittest.TestCase):
    def test_launcher_is_self_contained_single_file_win_x64(self):
        values = properties(LAUNCHER / "HoNRebornRu.Launcher.csproj")
        self.assertEqual("win-x64", values["RuntimeIdentifier"])
        self.assertEqual("true", values["SelfContained"])
        self.assertEqual("true", values["PublishSingleFile"])
        self.assertEqual("net8.0-windows", values["TargetFramework"])
        self.assertNotEqual("true", values.get("PublishTrimmed"))

    def test_updater_is_self_contained_single_file_win_x64(self):
        values = properties(UPDATER / "HoNRebornRu.Updater.csproj")
        self.assertEqual("win-x64", values["RuntimeIdentifier"])
        self.assertEqual("true", values["SelfContained"])
        self.assertEqual("true", values["PublishSingleFile"])

    def test_runtime_has_no_external_tool_dependency(self):
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in itertools.chain(LAUNCHER.glob("*.cs"), UPDATER.glob("*.cs"))
        )
        for executable in ("python.exe", "powershell.exe", "pwsh.exe", "node.exe", "curl.exe", "wget.exe", "7z.exe", "git.exe"):
            self.assertNotIn(executable, source.casefold())
        self.assertIn("HttpClient", source)
        self.assertIn("SHA256", source)

    def test_only_localized_official_and_direct_modes_exist(self):
        source = (LAUNCHER / "GameLauncher.cs").read_text(encoding="utf-8")
        self.assertIn("OfficialShortcut", source)
        self.assertIn("Direct", source)
        self.assertIn("Heroes of Newerth Reborn.lnk", source)
        self.assertNotIn("GearUpPrepared", source)
        self.assertNotIn("GearUP.lnk", source)
        self.assertIn('IsProcessRunning("juvio")', source)

    def test_headless_release_install_and_restore_hooks_exist(self):
        source = (LAUNCHER / "Program.cs").read_text(encoding="utf-8")
        self.assertIn('"--install-latest"', source)
        self.assertIn('"--restore"', source)
        self.assertIn("FindReleaseAsync", source)
        self.assertIn("InstallAsync", source)
        self.assertIn('"--launch-game"', source)
        self.assertIn('"--create-play-shortcut"', source)

    def test_self_test_does_not_require_an_installed_game(self):
        source = (LAUNCHER / "SelfTest.cs").read_text(encoding="utf-8")
        self.assertNotIn("LocalApplicationData", source)
        self.assertNotIn("game discovery", source)

    def test_locale_replacement_does_not_consume_the_next_line(self):
        source = (LAUNCHER / "InstallService.cs").read_text(encoding="utf-8")
        self.assertIn('[^\\\\r\\\\n]*', source)
        self.assertNotIn('.*(?:\\\\r?\\\\n)?', source)

    def test_localized_profile_is_prepared_safely_and_game_must_be_stopped(self):
        install_source = (LAUNCHER / "InstallService.cs").read_text(encoding="utf-8")
        launch_source = (LAUNCHER / "GameLauncher.cs").read_text(encoding="utf-8")
        install_body = install_source.split("public async Task InstallAsync", 1)[1].split("public async Task RestoreAsync", 1)[0]
        self.assertIn('SetLocale(LocalizedStartupPath, "ru"', install_body)
        self.assertIn("SeedLocalizedProfile()", install_body)
        self.assertIn('new[] { "startup.cfg", "game_settings_local.cfg", "voice_config.cfg", "login.cfg" }', install_source)
        self.assertIn('if (name.Equals("login.cfg", StringComparison.OrdinalIgnoreCase))', install_source)
        self.assertIn('sources.Add(Path.Combine(NormalProfileDirectory, "extensions", name))', install_source)
        self.assertIn("OrderByDescending(path => File.GetLastWriteTimeUtc(path))", install_source)
        self.assertIn('File.GetLastWriteTimeUtc(source) <= File.GetLastWriteTimeUtc(target)', install_source)
        self.assertIn('$"{safeName}-before-', install_source)
        self.assertIn("RollbackSeededProfile(seededProfile)", install_body)
        self.assertIn("RestoreLocales(rollbackLocales)", install_body)
        self.assertNotIn("SetRuntimeLocales", install_source)
        self.assertIn('GetProcessesByName("juvio")', install_source)
        self.assertIn('startInfo.ArgumentList.Add("-host_locale")', launch_source)
        self.assertIn('startInfo.ArgumentList.Add("ru")', launch_source)

    def test_every_game_mode_uses_the_verified_localized_launch(self):
        source = (LAUNCHER / "GameLauncher.cs").read_text(encoding="utf-8")
        self.assertEqual(2, source.count("LaunchLocalizedJuvio();"))
        self.assertIn('"extensions", "resources0.jz"', source)
        self.assertIn('startInfo.ArgumentList.Add("-mod")', source)
        self.assertIn('startInfo.ArgumentList.Add("heroes of newerth;extensions")', source)
        self.assertNotIn('startInfo.ArgumentList.Add("-config")', source)
        self.assertIn('startInfo.ArgumentList.Add("-host_locale")', source)
        self.assertIn('startInfo.ArgumentList.Add("ru")', source)
        self.assertIn("Русский перевод не установлен", source)

    def test_translation_uses_extension_resources_and_localized_settings_profile(self):
        source = (LAUNCHER / "InstallService.cs").read_text(encoding="utf-8")
        launch_source = (LAUNCHER / "GameLauncher.cs").read_text(encoding="utf-8")
        self.assertIn('Path.Combine(ExtensionDirectory, "resources0.jz")', source)
        self.assertIn("BackupCurrentExtensionAsync", source)
        self.assertIn("SchemaVersion = 3", source)
        self.assertNotIn('startInfo.ArgumentList.Add("-config")', launch_source)
        self.assertNotIn("SetLocale(", launch_source)

    def test_gearup_is_instruction_only_and_never_launched_by_launcher(self):
        game_source = (LAUNCHER / "GameLauncher.cs").read_text(encoding="utf-8")
        ui_source = (LAUNCHER / "MainForm.cs").read_text(encoding="utf-8")
        models_source = (LAUNCHER / "Models.cs").read_text(encoding="utf-8")
        self.assertNotIn("GameLaunchMode.GearUp", game_source + ui_source)
        self.assertNotIn("GearUpShortcutPath", game_source + ui_source + models_source)
        self.assertIn("сначала нажмите «Бустить»".casefold(), ui_source.casefold())

    def test_launcher_uses_the_custom_game_ui_without_standard_input_controls(self):
        ui_source = (LAUNCHER / "MainForm.cs").read_text(encoding="utf-8")
        theme_source = (LAUNCHER / "ThemeControls.cs").read_text(encoding="utf-8")
        self.assertIn('UiButton("ИГРАТЬ", LauncherButtonKind.Primary)', ui_source)
        self.assertIn("FormBorderStyle.None", ui_source)
        self.assertIn("AutoScaleMode.Dpi", ui_source)
        self.assertIn("LauncherRadioCard", ui_source + theme_source)
        self.assertIn("LauncherProgressBar", ui_source + theme_source)
        self.assertNotIn("new ComboBox", ui_source)
        self.assertNotIn("new ProgressBar", ui_source)

    def test_custom_painting_ignores_transient_zero_sized_windows(self):
        ui_source = (LAUNCHER / "MainForm.cs").read_text(encoding="utf-8")
        theme_source = (LAUNCHER / "ThemeControls.cs").read_text(encoding="utf-8")
        self.assertIn("ClientSize.Width <= 0 || ClientSize.Height <= 0", ui_source)
        self.assertIn("Width <= 1 || Height <= 1", ui_source)
        self.assertIn("bounds.Width <= 0 || bounds.Height <= 0", theme_source)
        self.assertGreaterEqual(theme_source.count("if (Width <="), 4)

    def test_redesign_keeps_shortcut_and_support_tools_in_the_main_window(self):
        ui_source = (LAUNCHER / "MainForm.cs").read_text(encoding="utf-8")
        self.assertIn("ВЫБРАТЬ ЯРЛЫК", ui_source)
        self.assertIn("_toolTip.SetToolTip", ui_source)
        self.assertIn("ВОССТАНОВЛЕНИЕ", ui_source)
        self.assertIn("ЖУРНАЛ", ui_source)
        self.assertIn("РЕЛИЗЫ", ui_source)

    def test_locale_repair_preserves_encoding_and_splits_joined_commands(self):
        source = (LAUNCHER / "InstallService.cs").read_text(encoding="utf-8")
        self.assertIn("ReadTextPreservingEncoding", source)
        self.assertIn("ConcatenatedLocaleCommandRegex", source)
        self.assertIn("File.WriteAllText(temporary, text, encoding)", source)

    def test_application_and_setup_icons_are_configured(self):
        icon = LAUNCHER / "Assets" / "app-icon.ico"
        self.assertTrue(icon.is_file())
        self.assertGreater(icon.stat().st_size, 10_000)
        self.assertEqual("Assets\\app-icon.ico", properties(LAUNCHER / "HoNRebornRu.Launcher.csproj")["ApplicationIcon"])
        setup = (ROOT / "installer" / "HoNRebornRU.iss").read_text(encoding="utf-8")
        self.assertIn("SetupIconFile=", setup)

    def test_theme_asset_is_embedded(self):
        asset = LAUNCHER / "Assets" / "launcher-background.png"
        self.assertTrue(asset.is_file())
        self.assertGreater(asset.stat().st_size, 100_000)
        project = (LAUNCHER / "HoNRebornRu.Launcher.csproj").read_text(encoding="utf-8")
        self.assertIn("EmbeddedResource", project)

    def test_beta_release_translation_manifest_matches_asset(self):
        directory = ROOT / "release-assets" / "0.1.0-beta.9"
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        archive = directory / manifest["file"]
        self.assertTrue(archive.is_file())
        self.assertEqual(archive.stat().st_size, manifest["size_bytes"])
        self.assertEqual("0.1.0-beta.9", manifest["version"])

    def test_beta9_is_a_thin_current_ui_overlay(self):
        archive_path = ROOT / "release-assets" / "0.1.0-beta.9" / "resources0.jz"
        with zipfile.ZipFile(archive_path) as archive:
            names = set(archive.namelist())
            interface = archive.read("stringtables/interface_ru.str").decode("utf-8")
        self.assertNotIn("ui/fe3/sections/plinko_v2.package", names)
        self.assertFalse(any(name.startswith("ui/fe3/sections/matchmaking") for name in names))
        self.assertNotIn("ui/fe3/sections/store.package", names)
        self.assertIn("player_role_soloofflane\tСоло-оффлейн", interface)
        self.assertIn("boss_info_scaling_header\tУсиление с каждым возрождением", interface)
        self.assertIn("producst_header_emotes\tЭмоции", interface)
        self.assertIn("plinko_change_board\tСменить поле", interface)

    def test_setup_contains_both_autonomous_binaries(self):
        script = (ROOT / "installer" / "HoNRebornRU.iss").read_text(encoding="utf-8")
        self.assertIn("HoNRebornRU.exe", script)
        self.assertIn("HoNRebornRU.Updater.exe", script)
        self.assertIn("{autopf}\\HoN Reborn RU", script)
        self.assertIn("HoN Reborn RU — Играть", script)
        self.assertIn('Parameters: "--launch-game"', script)

    def test_localized_play_shortcut_uses_embedded_windows_shell_api(self):
        source = (LAUNCHER / "ShortcutService.cs").read_text(encoding="utf-8")
        self.assertIn("IShellLinkW", source)
        self.assertIn('SetArguments(arguments)', source)
        self.assertIn('SetIconLocation(targetPath, 0)', source)
        self.assertNotIn("powershell", source.casefold())


if __name__ == "__main__":
    unittest.main()
