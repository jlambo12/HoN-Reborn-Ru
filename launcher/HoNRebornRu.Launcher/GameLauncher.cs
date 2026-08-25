using System.Diagnostics;

namespace HoNRebornRu.Launcher;

internal sealed class GameLauncher
{
    private readonly string _juvioRoot = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Juvio");
    public string? FindOfficialShortcut()
    {
        var candidates = new[]
        {
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), "Heroes of Newerth Reborn.lnk"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs), "Juvio", "Heroes of Newerth.lnk"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonDesktopDirectory), "Heroes of Newerth Reborn.lnk"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonPrograms), "Juvio", "Heroes of Newerth.lnk")
        };
        return candidates.FirstOrDefault(File.Exists);
    }

    public string Launch(GameLaunchMode mode, LauncherSettings settings)
    {
        if (IsProcessRunning("juvio"))
            throw new InvalidOperationException("Heroes of Newerth Reborn уже запущена.");

        string status;
        switch (mode)
        {
            case GameLaunchMode.OfficialShortcut:
                _ = ResolveShortcut(settings.OfficialShortcutPath, FindOfficialShortcut(), "Официальный ярлык Heroes of Newerth Reborn не найден.");
                LaunchLocalizedJuvio();
                status = "Игра запущена через официальный Juvio с русским переводом.";
                break;
            case GameLaunchMode.Direct:
                LaunchLocalizedJuvio();
                status = "Игра запущена напрямую с русским переводом.";
                break;
            default:
                throw new ArgumentOutOfRangeException(nameof(mode));
        }
        AppStorage.Log($"Started launch mode {mode}.");
        return status;
    }

    private void LaunchLocalizedJuvio()
    {
        var translation = Path.Combine(_juvioRoot, "heroes of newerth", "resources_ru0.jz");
        if (!File.Exists(translation))
            throw new FileNotFoundException("Русский перевод не установлен. Сначала установите его в Launcher.", translation);
        var executable = Path.Combine(_juvioRoot, "bin", "juvio.exe");
        if (!File.Exists(executable)) throw new FileNotFoundException("Juvio не найден.", executable);
        Process.Start(new ProcessStartInfo
        {
            FileName = executable,
            // Keep the normal "Heroes of Newerth" mod active. Juvio then uses
            // the player's existing Documents\Juvio\Heroes of Newerth profile
            // instead of creating a separate, default "extensions" profile.
            Arguments = "-host_locale ru",
            WorkingDirectory = _juvioRoot,
            UseShellExecute = true
        });
    }

    private static bool IsProcessRunning(string processName)
    {
        var processes = Process.GetProcessesByName(processName);
        try { return processes.Length > 0; }
        finally
        {
            foreach (var process in processes) process.Dispose();
        }
    }

    private static string ResolveShortcut(string? configured, string? detected, string error)
    {
        if (!string.IsNullOrWhiteSpace(configured) && File.Exists(configured)) return configured;
        return detected ?? throw new FileNotFoundException(error);
    }

    public static void ShellOpen(string pathOrUrl)
    {
        Process.Start(new ProcessStartInfo { FileName = pathOrUrl, UseShellExecute = true });
    }
}
