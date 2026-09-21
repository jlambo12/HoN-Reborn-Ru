using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;

namespace HoNRebornRu.Launcher;

internal sealed class UpdateClient : IDisposable
{
    private const string ReleasesApi = "https://api.github.com/repos/jlambo12/HoN-Reborn-Ru/releases?per_page=100";
    private readonly HttpClient _configuredHttp;
    private readonly HttpClient _directHttp;
    private readonly Action<string> _log;
    private readonly TimeSpan _configuredAttemptTimeout;
    private readonly TimeSpan _overallDiscoveryTimeout;
    private HttpClient _releaseHttp;

    public UpdateClient()
        : this(CreateHandler(useProxy: true), CreateHandler(useProxy: false), AppStorage.Log)
    {
    }

    internal UpdateClient(
        HttpMessageHandler configuredHandler, HttpMessageHandler directHandler, Action<string>? log = null,
        TimeSpan? configuredAttemptTimeout = null, TimeSpan? overallDiscoveryTimeout = null)
    {
        _configuredHttp = CreateClient(configuredHandler);
        _directHttp = CreateClient(directHandler);
        _log = log ?? (_ => { });
        _configuredAttemptTimeout = configuredAttemptTimeout ?? TimeSpan.FromSeconds(5);
        _overallDiscoveryTimeout = overallDiscoveryTimeout ?? TimeSpan.FromSeconds(30);
        _releaseHttp = _configuredHttp;
    }

    public async Task<RemoteRelease> FindReleaseAsync(ReleaseChannel channel, CancellationToken cancellationToken)
    {
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        deadline.CancelAfter(_overallDiscoveryTimeout);
        var requestToken = deadline.Token;
        try
        {
            using var configuredAttempt = CancellationTokenSource.CreateLinkedTokenSource(requestToken);
            configuredAttempt.CancelAfter(_configuredAttemptTimeout);
            try
            {
                var release = await FindReleaseWithClientAsync(_configuredHttp, channel, configuredAttempt.Token);
                _releaseHttp = _configuredHttp;
                return release;
            }
            catch (HttpRequestException exception)
            {
                _log($"GitHub request through the configured proxy failed; retrying directly: {exception.Message}");
            }
            catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested && !requestToken.IsCancellationRequested)
            {
                _log($"GitHub request through the configured proxy exceeded {_configuredAttemptTimeout.TotalSeconds:0.#} seconds; retrying directly.");
            }

            var directRelease = await FindReleaseWithClientAsync(_directHttp, channel, requestToken);
            _releaseHttp = _directHttp;
            return directRelease;
        }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
        {
            throw new TimeoutException($"GitHub Releases не ответил за {_overallDiscoveryTimeout.TotalSeconds:0.#} секунд.");
        }
    }

    public async Task DownloadAsync(string url, string destination, IProgress<int>? progress, CancellationToken cancellationToken)
    {
        try
        {
            await DownloadWithClientAsync(_releaseHttp, url, destination, progress, cancellationToken);
        }
        catch (HttpRequestException exception) when (!ReferenceEquals(_releaseHttp, _directHttp))
        {
            _log($"Release download through the configured proxy failed; retrying directly: {exception.Message}");
            await DownloadWithClientAsync(_directHttp, url, destination, progress, cancellationToken);
            _releaseHttp = _directHttp;
        }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested && !ReferenceEquals(_releaseHttp, _directHttp))
        {
            _log("Release download through the configured proxy timed out; retrying directly.");
            await DownloadWithClientAsync(_directHttp, url, destination, progress, cancellationToken);
            _releaseHttp = _directHttp;
        }
    }

    private static SocketsHttpHandler CreateHandler(bool useProxy) => new()
    {
        UseProxy = useProxy,
        ConnectTimeout = useProxy ? TimeSpan.FromSeconds(5) : TimeSpan.FromSeconds(25),
        AutomaticDecompression = System.Net.DecompressionMethods.All
    };

    private static HttpClient CreateClient(HttpMessageHandler handler)
    {
        var client = new HttpClient(handler)
        {
            // A failed GitHub connection must return control to the user quickly;
            // the old ten-minute timeout looked like a frozen launcher.
            Timeout = TimeSpan.FromSeconds(30)
        };
        client.DefaultRequestHeaders.UserAgent.Add(new ProductInfoHeaderValue("HoN-Reborn-RU-Launcher", Program.LauncherVersion));
        client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/vnd.github+json"));
        client.DefaultRequestHeaders.Add("X-GitHub-Api-Version", "2022-11-28");
        return client;
    }

    private static async Task<RemoteRelease> FindReleaseWithClientAsync(
        HttpClient client, ReleaseChannel channel, CancellationToken cancellationToken)
    {
        using var response = await client.GetAsync(ReleasesApi, cancellationToken);
        response.EnsureSuccessStatusCode();
        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var releases = await JsonSerializer.DeserializeAsync<List<GitHubRelease>>(stream, AppStorage.JsonOptions, cancellationToken) ?? [];
        var candidates = new List<(GitHubRelease Release, SemVersion Version, GitHubAsset ManifestAsset)>();
        foreach (var listedRelease in releases.Where(release => !release.Draft && (channel == ReleaseChannel.Beta || !release.Prerelease)))
        {
            var manifestAsset = listedRelease.Assets.FirstOrDefault(asset =>
                asset.Name.Equals("update-manifest.json", StringComparison.OrdinalIgnoreCase));
            if (manifestAsset is not null && SemVersion.TryParse(listedRelease.TagName, out var version) && version is not null)
                candidates.Add((listedRelease, version, manifestAsset));
        }

        // Select exactly one target: the highest semantic version that exposes an
        // update manifest. Never fall back to an older manifest after selecting
        // the target, otherwise one broken request can turn a direct .15 -> .19
        // update into a chain of intermediate installations.
        var candidate = candidates.OrderByDescending(item => item.Version).FirstOrDefault();
        if (candidate.Release is null)
            throw new InvalidOperationException(channel == ReleaseChannel.Beta
                ? "В GitHub Releases не найден совместимый релиз."
                : "Стабильный релиз пока не опубликован. Выберите канал «Бета»."
            );

        var release = candidate.Release;
        var manifest = await client.GetFromJsonAsync<UpdateManifest>(
            candidate.ManifestAsset.BrowserDownloadUrl, AppStorage.JsonOptions, cancellationToken);
        if (manifest is null || manifest.SchemaVersion != 1 ||
            !manifest.Version.Equals(release.TagName.TrimStart('v', 'V'), StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Манифест последнего релиза повреждён или не соответствует его версии.");
        if (channel == ReleaseChannel.Stable && !manifest.Channel.Equals("stable", StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Последний стабильный релиз содержит манифест другого канала.");
        return new RemoteRelease
        {
            Release = release,
            Manifest = manifest,
            AssetUrls = release.Assets.ToDictionary(asset => asset.Name, asset => asset.BrowserDownloadUrl, StringComparer.OrdinalIgnoreCase)
        };
    }

    private static async Task DownloadWithClientAsync(
        HttpClient client, string url, string destination, IProgress<int>? progress, CancellationToken cancellationToken)
    {
        using var response = await client.GetAsync(url, HttpCompletionOption.ResponseHeadersRead, cancellationToken);
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

    public void Dispose()
    {
        _configuredHttp.Dispose();
        _directHttp.Dispose();
    }
}
