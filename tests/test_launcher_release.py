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

    def test_release_discovery_uses_semantic_version_order(self):
        source = (LAUNCHER / "UpdateClient.cs").read_text(encoding="utf-8")
        self.assertIn("SemVersion.TryParse(release.TagName", source)
        self.assertIn("OrderByDescending(candidate => candidate.Version)", source)

    def test_release_check_is_bounded_and_offers_install_without_a_second_button(self):
        client = (LAUNCHER / "UpdateClient.cs").read_text(encoding="utf-8")
        form = (LAUNCHER / "MainForm.cs").read_text(encoding="utf-8")
        self.assertIn("ConnectTimeout = TimeSpan.FromSeconds(10)", client)
        self.assertIn("Timeout = TimeSpan.FromSeconds(30)", client)
        self.assertIn("deadline.CancelAfter(TimeSpan.FromSeconds(30))", client)
        self.assertNotIn("TimeSpan.FromMinutes(10)", client)
        self.assertNotIn("_installButton", form)
        self.assertIn('LauncherDialog.Confirm(this, "Обновление русификатора"', form)
        self.assertIn("await InstallOrUpdateAsync(_remote, cancellationToken)", form)

    def test_self_test_does_not_require_an_installed_game(self):
        source = (LAUNCHER / "SelfTest.cs").read_text(encoding="utf-8")
        self.assertNotIn("LocalApplicationData", source)
        self.assertNotIn("game discovery", source)

    def test_hon_plus_catalog_exposes_localization_as_first_module(self):
        modules = (LAUNCHER / "Modules.cs").read_text(encoding="utf-8")
        form = (LAUNCHER / "MainForm.cs").read_text(encoding="utf-8")
        self.assertIn("interface IHonPlusModule", modules)
        self.assertIn('ModuleId = "ru-localization"', modules)
        self.assertIn("class LocalizationModule : IHonPlusModule", modules)
        self.assertIn("ModuleCatalog.CreateDefault()", form)
        self.assertIn('Text = "HoN Plus"', form)
        self.assertNotIn("private readonly InstallService _installer", form)

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
        self.assertIn('new[] { "startup.cfg", "game_settings_local.cfg", "voice_config.cfg", "bindings/shared.json", "login.cfg" }', install_source)
        self.assertIn("Directory.CreateDirectory(Path.GetDirectoryName(target)!)", install_source)
        self.assertIn("var extension = Path.GetExtension(name)", install_source)
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

    def test_exact_official_archive_can_repair_stale_launcher_state(self):
        install_source = (LAUNCHER / "InstallService.cs").read_text(encoding="utf-8")
        self_test = (LAUNCHER / "SelfTest.cs").read_text(encoding="utf-8")
        self.assertIn("CanReconcileInstalledArchive", install_source)
        self.assertIn("currentHash.Equals(downloadedHash", install_source)
        self.assertIn("Adopting exact official translation archive", install_source)
        self.assertIn('CanReconcileInstalledArchive("target", "old", "target")', self_test)
        self.assertIn('CanReconcileInstalledArchive("unknown", "managed", "target")', self_test)

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
        directory = ROOT / "release-assets" / "0.1.0-beta.19"
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        archive = directory / manifest["file"]
        self.assertTrue(archive.is_file())
        self.assertEqual(archive.stat().st_size, manifest["size_bytes"])
        self.assertEqual("0.1.0-beta.19", manifest["version"])

    def test_website_download_points_to_current_beta_setup(self):
        site_config = (ROOT / "website" / "src" / "config" / "site.ts").read_text(encoding="utf-8")
        download_button = (ROOT / "website" / "src" / "components" / "DownloadButton.astro").read_text(encoding="utf-8")
        self.assertIn(
            "/releases/download/v0.1.0-beta.19/HoNRebornRU-Setup.exe",
            site_config,
        )
        self.assertIn("api.github.com/repos/jlambo12/HoN-Reborn-Ru/releases", download_button)
        self.assertIn("candidate.name === 'HoNRebornRU-Setup.exe'", download_button)

    def test_beta12_is_a_thin_current_ui_overlay_with_legacy_locale_aliases(self):
        archive_path = ROOT / "release-assets" / "0.1.0-beta.12" / "resources0.jz"
        with zipfile.ZipFile(archive_path) as archive:
            names = set(archive.namelist())
            interface = archive.read("stringtables/interface_ru.str").decode("utf-8")
            system_bar = archive.read("ui/fe3/sections/system_bar.package").decode("utf-8")
            main_ui = archive.read("ui/fe3/main.interface").decode("utf-8")
            matchmaking = archive.read("ui/scripts/fe3/matchmaking.lua").decode("utf-8")
            regions = archive.read("ui/scripts/fe3/regions.lua").decode("utf-8")
            boss_info = archive.read("ui/fe3/sections/boss_info.package").decode("utf-8")
            remote_motd = archive.read("preact-remote/dist/index.js").decode("utf-8")
            for domain in ("bot_messages", "client_messages", "entities", "game_messages", "interface"):
                self.assertEqual(
                    archive.read(f"stringtables/{domain}_ru.str"),
                    archive.read(f"stringtables/{domain}_en.str"),
                )
        self.assertNotIn("ui/fe3/sections/plinko_v2.package", names)
        self.assertFalse(any(name.startswith("ui/fe3/sections/matchmaking") for name in names))
        self.assertNotIn("ui/fe3/sections/store.package", names)
        self.assertIn("player_role_soloofflane\tСоло-оффлейн", interface)
        self.assertIn("boss_info_scaling_header\tУсиление с каждым возрождением", interface)
        self.assertIn("producst_header_emotes\tЭмоции", interface)
        self.assertIn("plinko_change_board\tСменить поле", interface)
        self.assertIn("warning_dismiss\tНажмите в любом месте, чтобы продолжить", interface)
        self.assertIn("lang_ru\tРусский", interface)
        self.assertIn("rolepick_foot_last_loss\tВ последнем матче вы потратили {delta} жетонов очереди ролей.", interface)
        self.assertIn("ui/fe3/sections/system_bar.package", names)
        self.assertIn("ui/fe3/sections/boss_info.package", names)
        self.assertIn("ui/scripts/fe3/matchmaking.lua", names)
        self.assertIn('label="ОБУЧЕНИЕ"', system_bar)
        self.assertIn("matchmaking:ПОИСК МАТЧА,game_list:СВОИ ИГРЫ", main_ui)
        self.assertIn("['Role Pick']='Выбор ролей'", matchmaking)
        self.assertIn("return {'en', 'ru', 'th'}", regions)
        self.assertNotIn('header_text="boss_info_scaling_header"', boss_info)
        self.assertIn("toLocaleLowerCase", remote_motd)
        self.assertIn("Купить Jade", remote_motd)

    def test_beta12_microfix_does_not_remove_or_modify_unreviewed_members(self):
        base_path = ROOT / "release-assets" / "0.1.0-beta.11" / "resources0.jz"
        candidate_path = ROOT / "release-assets" / "0.1.0-beta.12" / "resources0.jz"
        allowed = {
            "preact-remote/dist/index.js",
            "stringtables/interface_en.str",
            "stringtables/interface_ru.str",
            "ui/fe3/main.interface",
            "ui/fe3/sections/boss_info.package",
            "ui/fe3/sections/marketplace_announce.package",
            "ui/fe3/sections/system_bar.package",
            "ui/fe3/templates/matchmaking_templates.package",
            "ui/scripts/fe3/marketplace_announce.lua",
            "ui/scripts/fe3/matchmaking.lua",
            "ui/scripts/fe3/regions.lua",
            "ui/scripts/fe3/store_featured.lua",
        }
        with zipfile.ZipFile(base_path) as base, zipfile.ZipFile(candidate_path) as candidate:
            base_members = {name: base.read(name) for name in base.namelist()}
            candidate_members = {name: candidate.read(name) for name in candidate.namelist()}
        self.assertFalse(base_members.keys() - candidate_members.keys())
        actual = {
            name for name in candidate_members
            if name not in base_members or candidate_members[name] != base_members[name]
        }
        self.assertEqual(allowed, actual)

    def test_beta13_completes_reported_store_profile_and_notification_strings(self):
        archive_path = ROOT / "release-assets" / "0.1.0-beta.13" / "resources0.jz"
        with zipfile.ZipFile(archive_path) as archive:
            names = set(archive.namelist())
            interface = archive.read("stringtables/interface_ru.str").decode("utf-8")
            messages = archive.read("stringtables/game_messages_ru.str").decode("utf-8")
            preact = archive.read("preact/dist/index.js").decode("utf-8")
            store = archive.read("ui/fe3/templates/store_featured_templates.package").decode("utf-8")
            bottom_bar = archive.read("ui/fe3/sections/bottom_bar.package").decode("utf-8")
        self.assertIn("ui/fe3/sections/store.package", names)
        self.assertIn("store_cat_featured\tРЕКОМЕНДУЕМЫЕ ТОВАРЫ", interface)
        self.assertIn("vanity_cat_avatars\tОБЛИКИ", interface)
        self.assertIn("killstreak5\t{killer_color}{killer}^*^; ^848доминирует^*!!", messages)
        self.assertIn("client_disconnected\t{account_color}{player}^*^; отключился.", messages)
        self.assertIn("Система чести", preact)
        self.assertIn("История штрафных очков", preact)
        self.assertIn("Показать сведения о системе чести", preact)
        self.assertIn('content="ТОРГОВАЯ ПЛОЩАДКА"', store)
        self.assertIn('tooltip="Друзья"', bottom_bar)
        self.assertIn('tooltip="Сообщения"', bottom_bar)

    def test_beta13_microfix_does_not_remove_or_modify_unreviewed_members(self):
        base_path = ROOT / "release-assets" / "0.1.0-beta.12" / "resources0.jz"
        candidate_path = ROOT / "release-assets" / "0.1.0-beta.13" / "resources0.jz"
        allowed = {
            "preact/dist/index.js",
            "preact/dist/index.js.map",
            "stringtables/game_messages_en.str",
            "stringtables/game_messages_ru.str",
            "stringtables/interface_en.str",
            "stringtables/interface_ru.str",
            "ui/fe3/sections/bottom_bar.package",
            "ui/fe3/sections/store.package",
            "ui/fe3/templates/store_featured_templates.package",
        }
        with zipfile.ZipFile(base_path) as base, zipfile.ZipFile(candidate_path) as candidate:
            base_members = {name: base.read(name) for name in base.namelist()}
            candidate_members = {name: candidate.read(name) for name in candidate.namelist()}
        self.assertFalse(base_members.keys() - candidate_members.keys())
        actual = {
            name for name in candidate_members
            if name not in base_members or candidate_members[name] != base_members[name]
        }
        self.assertEqual(allowed, actual)

    def test_beta14_supports_hon_0126_and_succubus(self):
        archive_path = ROOT / "release-assets" / "0.1.0-beta.14" / "resources0.jz"
        with zipfile.ZipFile(archive_path) as archive:
            entities = archive.read("stringtables/entities_ru.str").decode("utf-8")
            preact = archive.read("preact/dist/index.js").decode("utf-8")
        self.assertIn("Hero_Succubus_description\t", entities)
        self.assertIn("Ability_Succubus4_description_simple\t", entities)
        self.assertIn("Staff of the Master", entities)
        self.assertIn("Новый герой: Succubus", preact)
        self.assertIn("Описание патча 0.12.6", preact)
        self.assertIn("Производительность и память", preact)

    def test_beta14_rebase_keeps_the_release_overlay_thin(self):
        base_path = ROOT / "release-assets" / "0.1.0-beta.13" / "resources0.jz"
        candidate_path = ROOT / "release-assets" / "0.1.0-beta.14" / "resources0.jz"
        allowed = {
            "preact-remote/dist/index.js",
            "preact/dist/assets/index.css",
            "preact/dist/index.js",
            "preact/dist/index.js.map",
            "stringtables/entities_en.str",
            "stringtables/entities_ru.str",
            "stringtables/interface_en.str",
            "stringtables/interface_ru.str",
            "ui/scripts/fe3/marketplace_announce.lua",
            "ui/scripts/fe3/store_featured.lua",
        }
        with zipfile.ZipFile(base_path) as base, zipfile.ZipFile(candidate_path) as candidate:
            base_members = {name: base.read(name) for name in base.namelist()}
            candidate_members = {name: candidate.read(name) for name in candidate.namelist()}
        self.assertEqual(base_members.keys(), candidate_members.keys())
        actual = {
            name for name in candidate_members
            if candidate_members[name] != base_members[name]
        }
        self.assertEqual(allowed, actual)

    def test_beta15_is_launcher_only_and_keeps_beta14_translation_exact(self):
        beta14 = ROOT / "release-assets" / "0.1.0-beta.14" / "resources0.jz"
        beta15 = ROOT / "release-assets" / "0.1.0-beta.15" / "resources0.jz"
        self.assertEqual(beta14.read_bytes(), beta15.read_bytes())

    def test_beta16_restores_cumulative_ui_and_0126_dynamic_strings(self):
        archive_path = ROOT / "release-assets" / "0.1.0-beta.16" / "resources0.jz"
        with zipfile.ZipFile(archive_path) as archive:
            preact = archive.read("preact/dist/index.js").decode("utf-8")
            remote = archive.read("preact-remote/dist/index.js").decode("utf-8")
            interface = archive.read("stringtables/interface_ru.str").decode("utf-8")
            main_ui = archive.read("ui/fe3/main.interface").decode("utf-8")
        for literal in ("Жалоба на игрока", "Избегание", "Матч завершён", "Правила поведения", "минуту"):
            self.assertIn(literal, preact)
        for literal in ("Патч 0.12.6 уже доступен", "Succubus пополняет список героев", "Повышение производительности"):
            self.assertIn(literal, remote)
        self.assertIn("mm_queue_btn_cost\tВстать в очередь — стоимость: {cost} жетон очереди ролей", interface)
        self.assertIn("rolepick_foot_cost\tЕсли не выбрать ни одну роль поддержки", interface)
        self.assertIn("matchmaking:ПОИСК МАТЧА,game_list:СВОИ ИГРЫ", main_ui)

    def test_beta17_is_launcher_only_and_keeps_beta16_translation_exact(self):
        beta16 = ROOT / "release-assets" / "0.1.0-beta.16" / "resources0.jz"
        beta17 = ROOT / "release-assets" / "0.1.0-beta.17" / "resources0.jz"
        self.assertEqual(beta16.read_bytes(), beta17.read_bytes())

    def test_beta18_contains_honplus_live_and_postmatch_ui(self):
        archive_path = ROOT / "release-assets" / "0.1.0-beta.19" / "resources0.jz"
        with zipfile.ZipFile(archive_path) as archive:
            names = set(archive.namelist())
            live = archive.read("ui/scripts/game/honplus_live.lua").decode("utf-8")
            preact = archive.read("preact/dist/index.js").decode("utf-8")
        self.assertIn("ui/hd_ui/sections/honplus_live.package", names)
        self.assertIn("ui/hd_ui/sections/ig_vanity_shop.package", names)
        self.assertIn("math.floor(values[4] + .5)", live)
        self.assertIn("HoN Plus", preact)

    def test_rebase_restores_safe_legacy_locale_aliases_without_stale_screens(self):
        source = (ROOT / "tools" / "localization" / "rebase_current_release.py").read_text(encoding="utf-8")
        self.assertIn("STRINGTABLE_DOMAINS", source)
        self.assertIn('members[f"stringtables/{domain}_en.str"] = members[ru_name]', source)
        self.assertIn("UI packages from the historical donor build are intentionally not", source)

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
