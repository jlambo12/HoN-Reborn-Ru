using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;

namespace HoNRebornRu.Launcher;

internal sealed partial class InstallService
{
    public string JuvioRoot { get; } = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Juvio");
    public string BaseArchive => Path.Combine(JuvioRoot, "heroes of newerth", "resources0.jz");
    public string ExtensionDirectory => Path.Combine(JuvioRoot, "extensions");
    public string InstalledArchive => Path.Combine(ExtensionDirectory, "resources0.jz");

    public InstallationState? ReadState()
    {
        if (!File.Exists(AppStorage.StatePath)) return null;
        var state = AppStorage.Load<InstallationState>(AppStorage.StatePath);
        return state.SchemaVersion == 1 && state.Product == "HoN-Reborn-RU" ? state : null;
    }

    public async Task<string?> GetInstalledVersionAsync(CancellationToken cancellationToken = default)
    {
        var state = ReadState();
        if (state is null || !File.Exists(InstalledArchive)) return null;
        var currentHash = await Sha256Async(InstalledArchive, cancellationToken);
        return currentHash.Equals(state.InstalledSha256, StringComparison.OrdinalIgnoreCase) ? state.Version : null;
    }

    public async Task InstallAsync(string downloadedArchive, UpdateManifest manifest, CancellationToken cancellationToken)
    {
        if (!File.Exists(BaseArchive)) throw new FileNotFoundException("HoN Reborn / Juvio не найден.", BaseArchive);
        var baseHash = await Sha256Async(BaseArchive, cancellationToken);
        if (manifest.CompatibleGameHashes.Count == 0 || !manifest.CompatibleGameHashes.Contains(baseHash, StringComparer.OrdinalIgnoreCase))
            throw new InvalidOperationException($"Версия игры несовместима с переводом. SHA-256 игры: {baseHash}");

        var info = new FileInfo(downloadedArchive);
        if (info.Length != manifest.Translation.SizeBytes) throw new InvalidDataException("Размер скачанного архива не совпадает с манифестом.");
        var downloadedHash = await Sha256Async(downloadedArchive, cancellationToken);
        if (!downloadedHash.Equals(manifest.Translation.Sha256, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Контрольная сумма скачанного перевода не совпадает.");

        Directory.CreateDirectory(ExtensionDirectory);
        Directory.CreateDirectory(AppStorage.BackupRoot);
        var oldState = ReadState();
        string? previousBackup = null;
        string? previousHash = null;
        Dictionary<string, LocaleState> previousLocales;
        if (oldState is not null)
        {
            if (!File.Exists(InstalledArchive)) throw new InvalidOperationException("Установленный перевод был удалён вне лаунчера. Сначала выполните восстановление вручную.");
            var currentHash = await Sha256Async(InstalledArchive, cancellationToken);
            if (!currentHash.Equals(oldState.InstalledSha256, StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException("Файл extensions\\resources0.jz изменён после установки. Лаунчер не будет его перезаписывать.");
            previousBackup = oldState.PreviousExtensionBackup;
            previousHash = oldState.PreviousExtensionSha256;
            previousLocales = oldState.PreviousLocales;
        }
        else
        {
            previousLocales = CaptureLocales();
            if (File.Exists(InstalledArchive))
            {
                previousHash = await Sha256Async(InstalledArchive, cancellationToken);
                previousBackup = Path.Combine(AppStorage.BackupRoot, $"resources0-before-{DateTime.Now:yyyyMMdd-HHmmss}.jz");
                File.Copy(InstalledArchive, previousBackup, false);
                var backupHash = await Sha256Async(previousBackup, cancellationToken);
                if (!backupHash.Equals(previousHash, StringComparison.OrdinalIgnoreCase))
                    throw new IOException("Не удалось проверить резервную копию существующего расширения.");
            }
        }

        SetRussianLocale();
        var temporary = Path.Combine(ExtensionDirectory, $".resources0-{Guid.NewGuid():N}.tmp");
        try
        {
            File.Copy(downloadedArchive, temporary, true);
            var temporaryHash = await Sha256Async(temporary, cancellationToken);
            if (!temporaryHash.Equals(downloadedHash, StringComparison.OrdinalIgnoreCase))
                throw new IOException("Ошибка проверки временной копии перевода.");
            File.Move(temporary, InstalledArchive, true);
        }
        finally
        {
            if (File.Exists(temporary)) File.Delete(temporary);
        }
        var installedHash = await Sha256Async(InstalledArchive, cancellationToken);
        if (!installedHash.Equals(downloadedHash, StringComparison.OrdinalIgnoreCase))
            throw new IOException("Ошибка проверки установленного перевода.");

        AppStorage.Save(AppStorage.StatePath, new InstallationState
        {
            Version = manifest.Version,
            InstalledAt = DateTimeOffset.UtcNow,
            InstalledSha256 = installedHash,
            PreviousExtensionBackup = previousBackup,
            PreviousExtensionSha256 = previousHash,
            BaseGameSha256 = baseHash,
            PreviousLocales = previousLocales
        });
        AppStorage.Log($"Installed translation {manifest.Version} ({installedHash}).");
    }

    public async Task RestoreAsync(CancellationToken cancellationToken)
    {
        var state = ReadState() ?? throw new InvalidOperationException("Состояние установки не найдено.");
        if (!File.Exists(InstalledArchive)) throw new FileNotFoundException("Установленный перевод не найден.", InstalledArchive);
        var currentHash = await Sha256Async(InstalledArchive, cancellationToken);
        if (!currentHash.Equals(state.InstalledSha256, StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("Перевод был изменён после установки. Восстановление остановлено во избежание потери данных.");

        if (!string.IsNullOrWhiteSpace(state.PreviousExtensionBackup))
        {
            var backup = Path.GetFullPath(state.PreviousExtensionBackup);
            var allowed = Path.GetFullPath(AppStorage.BackupRoot).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
            if (!backup.StartsWith(allowed, StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("В состоянии установки указан небезопасный путь резервной копии.");
            if (!File.Exists(backup)) throw new FileNotFoundException("Резервная копия не найдена.", backup);
            var backupHash = await Sha256Async(backup, cancellationToken);
            if (!backupHash.Equals(state.PreviousExtensionSha256, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Контрольная сумма резервной копии не совпадает.");
            var temporary = Path.Combine(ExtensionDirectory, $".resources0-restore-{Guid.NewGuid():N}.tmp");
            File.Copy(backup, temporary, true);
            File.Move(temporary, InstalledArchive, true);
        }
        else
        {
            File.Delete(InstalledArchive);
        }
        RestoreLocales(state.PreviousLocales);
        File.Delete(AppStorage.StatePath);
        AppStorage.Log("Restored previous extension and locale settings.");
    }

    private Dictionary<string, LocaleState> CaptureLocales()
    {
        var result = new Dictionary<string, LocaleState>(StringComparer.OrdinalIgnoreCase);
        foreach (var path in LocalePaths())
        {
            var existed = File.Exists(path);
            var text = existed ? File.ReadAllText(path) : "";
            var match = HostLocaleRegex().Match(text);
            result[path] = new LocaleState { FileExisted = existed, PreviousValue = match.Success ? match.Groups[1].Value : null };
        }
        return result;
    }

    private void SetRussianLocale()
    {
        foreach (var path in LocalePaths()) SetLocale(path, "ru", removeWhenNull: false);
    }

    private static void RestoreLocales(Dictionary<string, LocaleState> locales)
    {
        foreach (var pair in locales) SetLocale(pair.Key, pair.Value.PreviousValue, removeWhenNull: true);
    }

    private static void SetLocale(string path, string? locale, bool removeWhenNull)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        var text = File.Exists(path) ? File.ReadAllText(path) : "";
        var regex = HostLocaleLineRegex();
        if (locale is not null)
        {
            var replacement = $"SetSave \"host_locale\" \"{locale}\"";
            text = regex.IsMatch(text) ? regex.Replace(text, replacement, 1) : text.TrimEnd('\r', '\n') + Environment.NewLine + replacement + Environment.NewLine;
        }
        else if (removeWhenNull)
        {
            text = regex.Replace(text, "", 1);
        }
        var temporary = path + ".honru.tmp";
        File.WriteAllText(temporary, text, new UTF8Encoding(false));
        File.Move(temporary, path, true);
    }

    private static IEnumerable<string> LocalePaths()
    {
        var documents = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
        yield return Path.Combine(documents, "Juvio", "Heroes of Newerth", "startup.cfg");
        yield return Path.Combine(documents, "Juvio", "extensions", "startup.cfg");
    }

    public static async Task<string> Sha256Async(string path, CancellationToken cancellationToken = default)
    {
        await using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read, 1024 * 1024, true);
        var hash = await SHA256.HashDataAsync(stream, cancellationToken);
        return Convert.ToHexString(hash).ToLowerInvariant();
    }

    [GeneratedRegex("(?m)^SetSave\\s+\"host_locale\"\\s+\"([^\"]*)\".*$")]
    private static partial Regex HostLocaleRegex();

    [GeneratedRegex("(?m)^SetSave\\s+\"host_locale\"\\s+\"[^\"]*\"[^\\r\\n]*")]
    private static partial Regex HostLocaleLineRegex();
}
