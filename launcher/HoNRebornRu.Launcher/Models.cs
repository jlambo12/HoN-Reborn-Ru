using System.Text.Json.Serialization;

namespace HoNRebornRu.Launcher;

internal sealed class UpdateManifest
{
    [JsonPropertyName("schema_version")]
    public int SchemaVersion { get; set; }

    [JsonPropertyName("version")]
    public string Version { get; set; } = "";

    [JsonPropertyName("channel")]
    public string Channel { get; set; } = "beta";

    [JsonPropertyName("translation")]
    public ReleaseAsset Translation { get; set; } = new();

    [JsonPropertyName("launcher")]
    public ReleaseAsset Launcher { get; set; } = new();

    [JsonPropertyName("updater")]
    public ReleaseAsset Updater { get; set; } = new();

    [JsonPropertyName("compatible_game_hashes")]
    public List<string> CompatibleGameHashes { get; set; } = [];

    [JsonPropertyName("release_notes_url")]
    public string ReleaseNotesUrl { get; set; } = "";
}

internal sealed class ReleaseAsset
{
    [JsonPropertyName("version")]
    public string Version { get; set; } = "";

    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("sha256")]
    public string Sha256 { get; set; } = "";

    [JsonPropertyName("size_bytes")]
    public long SizeBytes { get; set; }
}

internal sealed class GitHubRelease
{
    [JsonPropertyName("tag_name")]
    public string TagName { get; set; } = "";

    [JsonPropertyName("html_url")]
    public string HtmlUrl { get; set; } = "";

    [JsonPropertyName("draft")]
    public bool Draft { get; set; }

    [JsonPropertyName("prerelease")]
    public bool Prerelease { get; set; }

    [JsonPropertyName("assets")]
    public List<GitHubAsset> Assets { get; set; } = [];
}

internal sealed class GitHubAsset
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("browser_download_url")]
    public string BrowserDownloadUrl { get; set; } = "";
}

internal sealed class RemoteRelease
{
    public required GitHubRelease Release { get; init; }
    public required UpdateManifest Manifest { get; init; }
    public required IReadOnlyDictionary<string, string> AssetUrls { get; init; }
}

internal enum ReleaseChannel
{
    Stable,
    Beta
}

internal enum GameLaunchMode
{
    OfficialShortcut,
    Direct
}

internal sealed class LauncherSettings
{
    public ReleaseChannel Channel { get; set; } = ReleaseChannel.Beta;
    public GameLaunchMode LaunchMode { get; set; } = GameLaunchMode.OfficialShortcut;
    public string? OfficialShortcutPath { get; set; }
    public bool CheckUpdatesAtStartup { get; set; } = true;
}

internal sealed class LocaleState
{
    public bool FileExisted { get; set; }
    public string? PreviousValue { get; set; }
}

internal sealed class InstallationState
{
    public int SchemaVersion { get; set; } = 3;
    public string Product { get; set; } = "HoN-Reborn-RU";
    public string Version { get; set; } = "";
    public DateTimeOffset InstalledAt { get; set; }
    public string InstalledSha256 { get; set; } = "";
    public string? PreviousExtensionBackup { get; set; }
    public string? PreviousExtensionSha256 { get; set; }
    public string? PreviousBaseOverlayBackup { get; set; }
    public string? PreviousBaseOverlaySha256 { get; set; }
    public string? MigratedBaseOverlaySha256 { get; set; }
    public string BaseGameSha256 { get; set; } = "";
    public Dictionary<string, LocaleState> PreviousLocales { get; set; } = new(StringComparer.OrdinalIgnoreCase);
    public bool? LocaleSettingsModified { get; set; }
}
