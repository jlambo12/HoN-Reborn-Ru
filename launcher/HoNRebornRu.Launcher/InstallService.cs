using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Diagnostics;

namespace HoNRebornRu.Launcher;

internal sealed partial class InstallService
{
    public string JuvioRoot { get; } = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Juvio");
    public string BaseArchive => Path.Combine(JuvioRoot, "heroes of newerth", "resources0.jz");
    public string BaseDirectory => Path.GetDirectoryName(BaseArchive)!;
    public string ExtensionDirectory => Path.Combine(JuvioRoot, "extensions");
    public string LegacyInstalledArchive => Path.Combine(ExtensionDirectory, "resources0.jz");
    public string BaseOverlayArchive => Path.Combine(BaseDirectory, "resources_ru0.jz");
    public string InstalledArchive => LegacyInstalledArchive;

    public InstallationState? ReadState()
    {
        if (!File.Exists(AppStorage.StatePath)) return null;
        var state = AppStorage.Load<InstallationState>(AppStorage.StatePath);
        return state.SchemaVersion is 1 or 2 or 3 && state.Product == "HoN-Reborn-RU" ? state : null;
    }

    public async Task<string?> GetInstalledVersionAsync(CancellationToken cancellationToken = default)
    {
        var state = ReadState();
        if (state is null) return null;
        var archive = ArchiveForState(state);
        if (!File.Exists(archive)) return null;
        var currentHash = await Sha256Async(archive, cancellationToken);
        return currentHash.Equals(state.InstalledSha256, StringComparison.OrdinalIgnoreCase) ? state.Version : null;
    }

    public async Task InstallAsync(string downloadedArchive, UpdateManifest manifest, CancellationToken cancellationToken)
    {
        EnsureGameStopped();
        if (!File.Exists(BaseArchive)) throw new FileNotFoundException("HoN Reborn / Juvio не найден.", BaseArchive);
        var baseHash = await Sha256Async(BaseArchive, cancellationToken);
        if (manifest.CompatibleGameHashes.Count == 0 || !manifest.CompatibleGameHashes.Contains(baseHash, StringComparer.OrdinalIgnoreCase))
            throw new InvalidOperationException($"Версия игры несовместима с переводом. SHA-256 игры: {baseHash}");

        var info = new FileInfo(downloadedArchive);
        if (info.Length != manifest.Translation.SizeBytes) throw new InvalidDataException("Размер скачанного архива не совпадает с манифестом.");
        var downloadedHash = await Sha256Async(downloadedArchive, cancellationToken);
        if (!downloadedHash.Equals(manifest.Translation.Sha256, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Контрольная сумма скачанного перевода не совпадает.");

        Directory.CreateDirectory(BaseDirectory);
        Directory.CreateDirectory(AppStorage.BackupRoot);
        var oldState = ReadState();
        if (oldState?.SchemaVersion is 1 or 3)
            await ValidateInstalledExtensionAsync(oldState, cancellationToken);
        else if (oldState?.SchemaVersion == 2)
            await ValidateBaseOverlayAsync(oldState, cancellationToken);
        string? previousBackup = null;
        string? previousHash = null;
        string? previousBaseBackup = null;
        string? previousBaseHash = null;
        string? migratedBaseHash = null;
        var previousLocales = oldState?.PreviousLocales ?? new Dictionary<string, LocaleState>(StringComparer.OrdinalIgnoreCase);
        bool? localeSettingsModified = false;
        if (oldState?.SchemaVersion is 1 or 3)
        {
            if (!File.Exists(InstalledArchive)) throw new InvalidOperationException("Установленный перевод был удалён вне лаунчера. Сначала выполните восстановление вручную.");
            var currentHash = await Sha256Async(InstalledArchive, cancellationToken);
            if (!currentHash.Equals(oldState.InstalledSha256, StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException("Файл extensions\\resources0.jz изменён после установки. Лаунчер не будет его перезаписывать.");
            previousBackup = oldState.PreviousExtensionBackup;
            previousHash = oldState.PreviousExtensionSha256;
            previousBaseBackup = oldState.PreviousBaseOverlayBackup;
            previousBaseHash = oldState.PreviousBaseOverlaySha256;
            migratedBaseHash = oldState.MigratedBaseOverlaySha256;
            localeSettingsModified = oldState.LocaleSettingsModified;
        }
        else if (oldState?.SchemaVersion == 2)
        {
            (previousBackup, previousHash) = await BackupCurrentExtensionAsync(cancellationToken);
            migratedBaseHash = oldState.InstalledSha256;
            if (!string.IsNullOrWhiteSpace(oldState.PreviousExtensionBackup) &&
                Path.GetFileName(oldState.PreviousExtensionBackup).StartsWith("resources_ru0-before-", StringComparison.OrdinalIgnoreCase))
            {
                previousBaseBackup = oldState.PreviousExtensionBackup;
                previousBaseHash = oldState.PreviousExtensionSha256;
            }
            localeSettingsModified = oldState.LocaleSettingsModified;
        }
        else
        {
            (previousBackup, previousHash) = await BackupCurrentExtensionAsync(cancellationToken);
        }

        Directory.CreateDirectory(ExtensionDirectory);
        var temporary = Path.Combine(ExtensionDirectory, $".resources0-{Guid.NewGuid():N}.tmp");
        var rollback = Path.Combine(ExtensionDirectory, $".resources0-rollback-{Guid.NewGuid():N}.tmp");
        var hadInstalledArchive = File.Exists(InstalledArchive);
        if (hadInstalledArchive) File.Copy(InstalledArchive, rollback, false);
        var stateSaved = false;
        try
        {
            File.Copy(downloadedArchive, temporary, true);
            var temporaryHash = await Sha256Async(temporary, cancellationToken);
            if (!temporaryHash.Equals(downloadedHash, StringComparison.OrdinalIgnoreCase))
                throw new IOException("Ошибка проверки временной копии перевода.");
            File.Move(temporary, InstalledArchive, true);
            var installedHash = await Sha256Async(InstalledArchive, cancellationToken);
            if (!installedHash.Equals(downloadedHash, StringComparison.OrdinalIgnoreCase))
                throw new IOException("Ошибка проверки установленного перевода.");

            AppStorage.Save(AppStorage.StatePath, new InstallationState
            {
                SchemaVersion = 3,
                Version = manifest.Version,
                InstalledAt = DateTimeOffset.UtcNow,
                InstalledSha256 = installedHash,
                PreviousExtensionBackup = previousBackup,
                PreviousExtensionSha256 = previousHash,
                PreviousBaseOverlayBackup = previousBaseBackup,
                PreviousBaseOverlaySha256 = previousBaseHash,
                MigratedBaseOverlaySha256 = migratedBaseHash,
                BaseGameSha256 = baseHash,
                PreviousLocales = previousLocales,
                LocaleSettingsModified = localeSettingsModified
            });
            stateSaved = true;
            AppStorage.Log($"Installed translation {manifest.Version} ({installedHash}).");
        }
        catch
        {
            if (!stateSaved)
            {
                if (hadInstalledArchive)
                    File.Move(rollback, InstalledArchive, true);
                else
                    File.Delete(InstalledArchive);
            }
            throw;
        }
        finally
        {
            if (File.Exists(temporary)) File.Delete(temporary);
            if (File.Exists(rollback)) File.Delete(rollback);
        }
        if (!string.IsNullOrWhiteSpace(migratedBaseHash))
        {
            try { await DeleteOwnedBaseOverlayAsync(migratedBaseHash, cancellationToken); }
            catch (Exception exception) { AppStorage.Log("Obsolete base overlay cleanup failed: " + exception); }
        }
    }

    public async Task RestoreAsync(CancellationToken cancellationToken)
    {
        EnsureGameStopped();
        var state = ReadState() ?? throw new InvalidOperationException("Состояние установки не найдено.");
        var archive = ArchiveForState(state);
        if (!File.Exists(archive)) throw new FileNotFoundException("Установленный перевод не найден.", archive);
        var currentHash = await Sha256Async(archive, cancellationToken);
        if (!currentHash.Equals(state.InstalledSha256, StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("Перевод был изменён после установки. Восстановление остановлено во избежание потери данных.");

        if (state.SchemaVersion == 3)
        {
            await RestoreArchiveAsync(InstalledArchive, state.PreviousExtensionBackup, state.PreviousExtensionSha256, cancellationToken);
            if (!string.IsNullOrWhiteSpace(state.MigratedBaseOverlaySha256))
                await DeleteOwnedBaseOverlayAsync(state.MigratedBaseOverlaySha256, cancellationToken);
            if (!string.IsNullOrWhiteSpace(state.PreviousBaseOverlayBackup))
                await RestoreArchiveAsync(BaseOverlayArchive, state.PreviousBaseOverlayBackup, state.PreviousBaseOverlaySha256, cancellationToken);
        }
        else
        {
            await RestoreArchiveAsync(archive, state.PreviousExtensionBackup, state.PreviousExtensionSha256, cancellationToken);
        }
        // Releases before beta.5 changed host_locale in startup.cfg. Restore that
        // legacy change on uninstall, but never touch configs for new installs.
        if (state.LocaleSettingsModified is not false) RestoreLocales(state.PreviousLocales);
        File.Delete(AppStorage.StatePath);
        AppStorage.Log("Restored previous extension and locale settings.");
    }

    private async Task ValidateInstalledExtensionAsync(InstallationState state, CancellationToken cancellationToken)
    {
        if (!File.Exists(InstalledArchive))
            throw new FileNotFoundException("Перевод предыдущей версии не найден.", InstalledArchive);
        var currentHash = await Sha256Async(InstalledArchive, cancellationToken);
        if (!currentHash.Equals(state.InstalledSha256, StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("Файл extensions\\resources0.jz изменён после установки. Миграция остановлена без удаления файла.");
    }

    private async Task ValidateBaseOverlayAsync(InstallationState state, CancellationToken cancellationToken)
    {
        if (!File.Exists(BaseOverlayArchive))
            throw new FileNotFoundException("Перевод предыдущей версии не найден.", BaseOverlayArchive);
        var currentHash = await Sha256Async(BaseOverlayArchive, cancellationToken);
        if (!currentHash.Equals(state.InstalledSha256, StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("Файл resources_ru0.jz изменён после установки. Миграция остановлена без удаления файла.");
    }

    private async Task<(string? Backup, string? Hash)> BackupCurrentExtensionAsync(CancellationToken cancellationToken)
    {
        if (!File.Exists(InstalledArchive)) return (null, null);
        var hash = await Sha256Async(InstalledArchive, cancellationToken);
        var backup = Path.Combine(AppStorage.BackupRoot, $"resources0-before-{DateTime.Now:yyyyMMdd-HHmmss}-{Guid.NewGuid():N}.jz");
        File.Copy(InstalledArchive, backup, false);
        if (!hash.Equals(await Sha256Async(backup, cancellationToken), StringComparison.OrdinalIgnoreCase))
            throw new IOException("Не удалось проверить резервную копию существующего расширения.");
        return (backup, hash);
    }

    private string ArchiveForState(InstallationState state) => state.SchemaVersion == 2
        ? BaseOverlayArchive
        : InstalledArchive;

    private static async Task RestoreArchiveAsync(string target, string? backupPath, string? expectedHash, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(backupPath))
        {
            File.Delete(target);
            return;
        }
        var backup = ValidateBackupPath(backupPath);
        if (!File.Exists(backup)) throw new FileNotFoundException("Резервная копия не найдена.", backup);
        var backupHash = await Sha256Async(backup, cancellationToken);
        if (!backupHash.Equals(expectedHash, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Контрольная сумма резервной копии не совпадает.");
        Directory.CreateDirectory(Path.GetDirectoryName(target)!);
        var temporary = Path.Combine(Path.GetDirectoryName(target)!, $".resources-restore-{Guid.NewGuid():N}.tmp");
        File.Copy(backup, temporary, true);
        File.Move(temporary, target, true);
    }

    private async Task DeleteOwnedBaseOverlayAsync(string expectedHash, CancellationToken cancellationToken)
    {
        if (!File.Exists(BaseOverlayArchive)) return;
        var currentHash = await Sha256Async(BaseOverlayArchive, cancellationToken);
        if (!currentHash.Equals(expectedHash, StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("Файл resources_ru0.jz изменён после установки. Лаунчер не будет его удалять.");
        File.Delete(BaseOverlayArchive);
    }

    private static string ValidateBackupPath(string path)
    {
        var backup = Path.GetFullPath(path);
        var allowed = Path.GetFullPath(AppStorage.BackupRoot).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        if (!backup.StartsWith(allowed, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("В состоянии установки указан небезопасный путь резервной копии.");
        return backup;
    }

    private Dictionary<string, LocaleState> CaptureLocales()
    {
        var result = new Dictionary<string, LocaleState>(StringComparer.OrdinalIgnoreCase);
        foreach (var path in LocalePaths())
        {
            var existed = File.Exists(path);
            var (text, _) = ReadTextPreservingEncoding(path);
            var match = HostLocaleRegex().Match(text);
            result[path] = new LocaleState { FileExisted = existed, PreviousValue = match.Success ? match.Groups[1].Value : null };
        }
        return result;
    }

    private static void RestoreLocales(Dictionary<string, LocaleState> locales)
    {
        foreach (var pair in locales) SetLocale(pair.Key, pair.Value.PreviousValue, removeWhenNull: true);
    }

    private static void SetLocale(string path, string? locale, bool removeWhenNull)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        var (text, encoding) = ReadTextPreservingEncoding(path);
        // Older launcher builds could join the locale command to the next SetSave
        // command. Repair that form before replacing the locale line.
        text = ConcatenatedLocaleCommandRegex().Replace(text, "$1" + Environment.NewLine);
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
        File.WriteAllText(temporary, text, encoding);
        File.Move(temporary, path, true);
    }

    private static (string Text, Encoding Encoding) ReadTextPreservingEncoding(string path)
    {
        if (!File.Exists(path)) return ("", new UTF8Encoding(false));

        using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite);
        Span<byte> prefix = stackalloc byte[3];
        var count = stream.Read(prefix);
        Encoding encoding = count >= 2 && prefix[0] == 0xFF && prefix[1] == 0xFE
            ? Encoding.Unicode
            : count >= 2 && prefix[0] == 0xFE && prefix[1] == 0xFF
                ? Encoding.BigEndianUnicode
                : count >= 3 && prefix[0] == 0xEF && prefix[1] == 0xBB && prefix[2] == 0xBF
                    ? new UTF8Encoding(true)
                    : new UTF8Encoding(false);
        stream.Position = 0;
        using var reader = new StreamReader(stream, encoding, detectEncodingFromByteOrderMarks: true);
        return (reader.ReadToEnd(), encoding);
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

    private static void EnsureGameStopped()
    {
        var processes = Process.GetProcessesByName("juvio");
        try
        {
            if (processes.Length > 0)
                throw new InvalidOperationException("Закройте Heroes of Newerth Reborn перед установкой или восстановлением перевода.");
        }
        finally
        {
            foreach (var process in processes) process.Dispose();
        }
    }

    [GeneratedRegex("(?m)^SetSave\\s+\"host_locale\"\\s+\"([^\"]*)\".*$")]
    private static partial Regex HostLocaleRegex();

    [GeneratedRegex("(?m)^SetSave\\s+\"host_locale\"\\s+\"[^\"]*\"[^\\r\\n]*")]
    private static partial Regex HostLocaleLineRegex();

    [GeneratedRegex("(?m)^(SetSave\\s+\"host_locale\"\\s+\"[^\"\\r\\n]*\")(?=SetSave\\s+)")]
    private static partial Regex ConcatenatedLocaleCommandRegex();
}
