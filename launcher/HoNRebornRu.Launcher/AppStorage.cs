using System.Text.Json;

namespace HoNRebornRu.Launcher;

internal static class AppStorage
{
    internal static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        WriteIndented = true
    };

    public static string Root { get; } = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "HoN-Reborn-RU");
    public static string SettingsPath => Path.Combine(Root, "launcher-settings.json");
    public static string StatePath => Path.Combine(Root, "install-state.json");
    public static string LogPath => Path.Combine(Root, "launcher.log");
    public static string BackupRoot => Path.Combine(Root, "backups");

    public static T Load<T>(string path) where T : new()
    {
        try
        {
            return File.Exists(path)
                ? JsonSerializer.Deserialize<T>(File.ReadAllText(path), JsonOptions) ?? new T()
                : new T();
        }
        catch
        {
            return new T();
        }
    }

    public static void Save<T>(string path, T value)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        var temporary = path + ".tmp";
        File.WriteAllText(temporary, JsonSerializer.Serialize(value, JsonOptions));
        File.Move(temporary, path, true);
    }

    public static void Log(string message)
    {
        try
        {
            Directory.CreateDirectory(Root);
            File.AppendAllText(LogPath, $"{DateTimeOffset.Now:O} {message}{Environment.NewLine}");
        }
        catch
        {
            // Logging must never prevent installation or launch.
        }
    }
}
