using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Cryptography;

namespace HoNRebornRu.Updater;

internal static class Program
{
    private const int MoveFileDelayUntilReboot = 0x4;

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int MessageBoxW(nint hWnd, string text, string caption, uint type);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool MoveFileExW(string existingFileName, string? newFileName, int flags);

    private static int Main(string[] args)
    {
        if (args.Length == 7 && args[0].Equals("--replace", StringComparison.OrdinalIgnoreCase))
            return Replace(args[1], args[2], args[3], args[4], args[5], args[6]);
        return 2;
    }

    private static int Replace(
        string launcherTargetArgument,
        string launcherSourceArgument,
        string launcherSha256,
        string updaterTargetArgument,
        string updaterSha256,
        string processIdArgument)
    {
        try
        {
            if (!int.TryParse(processIdArgument, out var processId)) throw new ArgumentException("Некорректный идентификатор процесса.");
            var launcherTarget = Path.GetFullPath(launcherTargetArgument);
            var launcherSource = Path.GetFullPath(launcherSourceArgument);
            var updaterTarget = Path.GetFullPath(updaterTargetArgument);
            var updaterSource = Environment.ProcessPath ?? throw new InvalidOperationException("Не удалось определить путь Updater.");
            Verify(launcherSource, launcherSha256, "Launcher");
            Verify(updaterSource, updaterSha256, "Updater");
            try { Process.GetProcessById(processId).WaitForExit(30_000); } catch (ArgumentException) { }
            AtomicReplace(launcherSource, launcherTarget);
            AtomicReplace(updaterSource, updaterTarget);
            Process.Start(new ProcessStartInfo { FileName = launcherTarget, UseShellExecute = true });
            try { File.Delete(launcherSource); } catch { }
            MoveFileExW(updaterSource, null, MoveFileDelayUntilReboot);
            return 0;
        }
        catch (Exception exception)
        {
            MessageBoxW(0, "Не удалось обновить лаунчер:\n" + exception.Message, "HoN Reborn RU", 0x10);
            return 1;
        }
    }

    private static void Verify(string path, string expectedSha256, string label)
    {
        if (!File.Exists(path)) throw new FileNotFoundException($"Загруженный {label} не найден.", path);
        var actual = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant();
        if (!actual.Equals(expectedSha256, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException($"SHA-256 {label} не совпадает.");
    }

    private static void AtomicReplace(string source, string target)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(target)!);
        var temporary = target + ".updating";
        File.Copy(source, temporary, true);
        File.Move(temporary, target, true);
    }
}
