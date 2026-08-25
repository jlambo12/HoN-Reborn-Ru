using System.Reflection;

namespace HoNRebornRu.Launcher;

internal static class Program
{
    public static string LauncherVersion => Assembly.GetExecutingAssembly().GetName().Version?.ToString(3) ?? "1.0.0";

    [STAThread]
    private static int Main(string[] args)
    {
        if (args.Length > 0 && args[0].Equals("--self-test", StringComparison.OrdinalIgnoreCase))
            return SelfTest.Run();
        if (args.Length > 0 && args[0].Equals("--uninstall-silent", StringComparison.OrdinalIgnoreCase))
            return UninstallSilent();
        if (args.Length > 0 && args[0].Equals("--restore", StringComparison.OrdinalIgnoreCase))
            return Restore();
        if (args.Length > 0 && args[0].Equals("--install-latest", StringComparison.OrdinalIgnoreCase))
            return InstallLatest(args.Length > 1 && args[1].Equals("stable", StringComparison.OrdinalIgnoreCase)
                ? ReleaseChannel.Stable
                : ReleaseChannel.Beta);
        if (args.Length > 0 && args[0].Equals("--launch-game", StringComparison.OrdinalIgnoreCase))
            return LaunchGame();
        if (args.Length > 0 && args[0].Equals("--create-play-shortcut", StringComparison.OrdinalIgnoreCase))
            return CreatePlayShortcut();

        ApplicationConfiguration.Initialize();
        try { ShortcutService.EnsurePlayShortcutForInstalledBuild(); }
        catch (Exception exception) { AppStorage.Log("Shortcut creation failed: " + exception); }
        Application.Run(new MainForm());
        return 0;
    }

    private static int UninstallSilent()
    {
        try
        {
            var installer = new InstallService();
            if (installer.ReadState() is not null) installer.RestoreAsync(CancellationToken.None).GetAwaiter().GetResult();
            ShortcutService.RemoveUserPlayShortcut();
            return 0;
        }
        catch (Exception exception)
        {
            AppStorage.Log("Uninstall restore failed: " + exception);
            return 1;
        }
    }

    private static int LaunchGame()
    {
        try
        {
            var settings = AppStorage.Load<LauncherSettings>(AppStorage.SettingsPath);
            new GameLauncher().Launch(GameLaunchMode.Direct, settings);
            return 0;
        }
        catch (Exception exception)
        {
            AppStorage.Log("Shortcut game launch failed: " + exception);
            MessageBox.Show(exception.Message, "HoN Reborn RU", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }

    private static int CreatePlayShortcut()
    {
        try
        {
            var executable = Environment.ProcessPath ?? throw new InvalidOperationException("Не удалось определить путь лаунчера.");
            ShortcutService.CreateUserPlayShortcut(executable);
            return 0;
        }
        catch (Exception exception)
        {
            AppStorage.Log("Shortcut creation failed: " + exception);
            return 1;
        }
    }

    private static int Restore()
    {
        try
        {
            new InstallService().RestoreAsync(CancellationToken.None).GetAwaiter().GetResult();
            return 0;
        }
        catch (Exception exception)
        {
            AppStorage.Log("Restore failed: " + exception);
            return 1;
        }
    }

    private static int InstallLatest(ReleaseChannel channel)
    {
        var temporary = Path.Combine(Path.GetTempPath(), $"HoN-Reborn-RU-{Guid.NewGuid():N}.jz");
        try
        {
            using var client = new UpdateClient();
            var remote = client.FindReleaseAsync(channel, CancellationToken.None).GetAwaiter().GetResult();
            if (!remote.AssetUrls.TryGetValue(remote.Manifest.Translation.Name, out var url))
                throw new InvalidDataException("Файл перевода отсутствует в GitHub Release.");
            client.DownloadAsync(url, temporary, null, CancellationToken.None).GetAwaiter().GetResult();
            new InstallService().InstallAsync(temporary, remote.Manifest, CancellationToken.None).GetAwaiter().GetResult();
            return 0;
        }
        catch (Exception exception)
        {
            AppStorage.Log("Headless install failed: " + exception);
            return 1;
        }
        finally
        {
            if (File.Exists(temporary)) File.Delete(temporary);
        }
    }
}
