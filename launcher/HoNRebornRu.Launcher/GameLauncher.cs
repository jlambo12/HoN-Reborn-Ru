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

    public string? FindGearUpShortcut()
    {
        var candidates = new[]
        {
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), "GearUP.lnk"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonDesktopDirectory), "GearUP.lnk"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonPrograms), "GearUP.lnk")
        };
        return candidates.FirstOrDefault(File.Exists);
    }

    public void Launch(GameLaunchMode mode, LauncherSettings settings)
    {
        if (mode != GameLaunchMode.GearUp && Process.GetProcessesByName("juvio").Length > 0)
            throw new InvalidOperationException("Heroes of Newerth Reborn уже запущена.");

        switch (mode)
        {
            case GameLaunchMode.OfficialShortcut:
                ShellOpen(ResolveShortcut(settings.OfficialShortcutPath, FindOfficialShortcut(), "Официальный ярлык Heroes of Newerth Reborn не найден."));
                break;
            case GameLaunchMode.GearUp:
                ShellOpen(ResolveShortcut(settings.GearUpShortcutPath, FindGearUpShortcut(), "Ярлык GearUP не найден."));
                break;
            case GameLaunchMode.Direct:
                var executable = Path.Combine(_juvioRoot, "bin", "juvio.exe");
                if (!File.Exists(executable)) throw new FileNotFoundException("Juvio не найден.", executable);
                Process.Start(new ProcessStartInfo
                {
                    FileName = executable,
                    Arguments = "-mod \"heroes of newerth;extensions\" -host_locale ru",
                    WorkingDirectory = _juvioRoot,
                    UseShellExecute = true
                });
                break;
        }
        AppStorage.Log($"Started launch mode {mode}.");
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
