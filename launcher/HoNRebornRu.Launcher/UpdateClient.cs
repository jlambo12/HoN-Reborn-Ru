using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;

namespace HoNRebornRu.Launcher;

internal sealed class UpdateClient : IDisposable
{
    private const string ReleasesApi = "https://api.github.com/repos/jlambo12/HoN-Reborn-Ru/releases?per_page=20";
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromMinutes(10) };

    public UpdateClient()
    {
        _http.DefaultRequestHeaders.UserAgent.Add(new ProductInfoHeaderValue("HoN-Reborn-RU-Launcher", Program.LauncherVersion));
        _http.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/vnd.github+json"));
        _http.DefaultRequestHeaders.Add("X-GitHub-Api-Version", "2022-11-28");
    }

    public async Task<RemoteRelease> FindReleaseAsync(ReleaseChannel channel, CancellationToken cancellationToken)
    {
        using var response = await _http.GetAsync(ReleasesApi, cancellationToken);
        response.EnsureSuccessStatusCode();
        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var releases = await JsonSerializer.DeserializeAsync<List<GitHubRelease>>(stream, AppStorage.JsonOptions, cancellationToken) ?? [];
        var candidates = new List<(GitHubRelease Release, SemVersion Version)>();
        foreach (var release in releases.Where(release => !release.Draft && (channel == ReleaseChannel.Beta || !release.Prerelease)))
        {
            if (SemVersion.TryParse(release.TagName, out var version) && version is not null)
                candidates.Add((release, version));
        }

        // GitHub does not guarantee semantic-version ordering here. In particular,
        // beta.9 may be returned before beta.10, so always inspect newest first.
        foreach (var candidate in candidates.OrderByDescending(candidate => candidate.Version))
        {
            var release = candidate.Release;
            var manifestAsset = release.Assets.FirstOrDefault(asset => asset.Name.Equals("update-manifest.json", StringComparison.OrdinalIgnoreCase));
            if (manifestAsset is null) continue;
            try
            {
                var manifest = await _http.GetFromJsonAsync<UpdateManifest>(manifestAsset.BrowserDownloadUrl, AppStorage.JsonOptions, cancellationToken);
                if (manifest is null || manifest.SchemaVersion != 1 || !manifest.Version.Equals(release.TagName.TrimStart('v', 'V'), StringComparison.OrdinalIgnoreCase)) continue;
                if (channel == ReleaseChannel.Stable && !manifest.Channel.Equals("stable", StringComparison.OrdinalIgnoreCase)) continue;
                return new RemoteRelease
                {
                    Release = release,
                    Manifest = manifest,
                    AssetUrls = release.Assets.ToDictionary(asset => asset.Name, asset => asset.BrowserDownloadUrl, StringComparer.OrdinalIgnoreCase)
                };
            }
            catch (HttpRequestException)
            {
                // Skip malformed historical releases and continue with the next candidate.
            }
        }
        throw new InvalidOperationException(channel == ReleaseChannel.Beta
            ? "В GitHub Releases не найден совместимый релиз."
            : "Стабильный релиз пока не опубликован. Выберите канал «Бета»."
        );
    }

    public async Task DownloadAsync(string url, string destination, IProgress<int>? progress, CancellationToken cancellationToken)
    {
        using var response = await _http.GetAsync(url, HttpCompletionOption.ResponseHeadersRead, cancellationToken);
        response.EnsureSuccessStatusCode();
        var length = response.Content.Headers.ContentLength;
        await using var input = await response.Content.ReadAsStreamAsync(cancellationToken);
        await using var output = new FileStream(destination, FileMode.Create, FileAccess.Write, FileShare.None, 128 * 1024, true);
        var buffer = new byte[128 * 1024];
        long total = 0;
        while (true)
        {
            var read = await input.ReadAsync(buffer, cancellationToken);
            if (read == 0) break;
            await output.WriteAsync(buffer.AsMemory(0, read), cancellationToken);
            total += read;
            if (length is > 0) progress?.Report((int)Math.Min(100, total * 100 / length.Value));
        }
        await output.FlushAsync(cancellationToken);
    }

    public void Dispose() => _http.Dispose();
}
