using System.Net;
using System.Text;

namespace HoNRebornRu.Launcher;

internal static class SelfTest
{
    public static int Run()
    {
        var failures = new List<string>();
        if (!SemVersion.TryParse("0.1.0-beta.2", out var beta2)) failures.Add("parse beta2");
        if (!SemVersion.TryParse("0.1.0-beta.10", out var beta10)) failures.Add("parse beta10");
        if (!SemVersion.TryParse("0.1.0", out var stable)) failures.Add("parse stable");
        if (beta2 is null || beta10 is null || beta2.CompareTo(beta10) >= 0) failures.Add("beta numeric ordering");
        if (beta10 is null || stable is null || beta10.CompareTo(stable) >= 0) failures.Add("stable ordering");
        if (!InstallService.CanReconcileInstalledArchive("target", "old", "target")) failures.Add("adopt exact official archive");
        if (!InstallService.CanReconcileInstalledArchive("managed", "managed", "target")) failures.Add("accept managed archive");
        if (InstallService.CanReconcileInstalledArchive("unknown", "managed", "target")) failures.Add("reject unknown archive");
        var savedState = new InstallationState { Version = "0.1.0-beta.20" };
        if (!InstallService.ShouldStartFreshInstallation(savedState, managedArchiveExists: false)) failures.Add("repair missing managed archive");
        if (InstallService.ShouldStartFreshInstallation(savedState, managedArchiveExists: true)) failures.Add("preserve valid managed archive");
        if (InstallService.ShouldStartFreshInstallation(null, managedArchiveExists: false)) failures.Add("ignore missing archive without state");
        var modules = ModuleCatalog.CreateDefault();
        if (!ModuleCatalog.HasUniqueIds(modules)) failures.Add("unique module ids");
        if (modules.Count != 1 || modules[0].Descriptor.Id != LocalizationModule.ModuleId)
            failures.Add("built-in localization module");
        try
        {
            using var client = new UpdateClient(
                new StubHttpHandler(_ => throw new HttpRequestException("configured proxy unavailable")),
                new StubHttpHandler(DirectReleaseResponse));
            var release = client.FindReleaseAsync(ReleaseChannel.Beta, CancellationToken.None).GetAwaiter().GetResult();
            if (release.Manifest.Version != "0.1.0-beta.20") failures.Add("direct jump to latest release");
        }
        catch (Exception exception)
        {
            failures.Add("direct fallback after proxy failure: " + exception.GetType().Name);
        }
        try
        {
            using var client = new UpdateClient(
                new BlockingHttpHandler(),
                new StubHttpHandler(DirectReleaseResponse),
                configuredAttemptTimeout: TimeSpan.FromMilliseconds(25),
                overallDiscoveryTimeout: TimeSpan.FromSeconds(2));
            var release = client.FindReleaseAsync(ReleaseChannel.Beta, CancellationToken.None).GetAwaiter().GetResult();
            if (release.Manifest.Version != "0.1.0-beta.20") failures.Add("direct fallback after proxy timeout");
        }
        catch (Exception exception)
        {
            failures.Add("bounded proxy timeout fallback: " + exception.GetType().Name);
        }
        if (failures.Count == 0)
        {
            Console.WriteLine("PASS: launcher self-test");
            return 0;
        }
        Console.Error.WriteLine("FAIL: " + string.Join(", ", failures));
        return 1;
    }

    private static HttpResponseMessage DirectReleaseResponse(HttpRequestMessage request)
    {
        const string manifest16 = "https://downloads.example/beta16/update-manifest.json";
        const string manifest19 = "https://downloads.example/beta19/update-manifest.json";
        const string manifest20 = "https://downloads.example/beta20/update-manifest.json";
        var url = request.RequestUri?.AbsoluteUri;
        var json = url switch
        {
            manifest16 => """{"schema_version":1,"version":"0.1.0-beta.16","channel":"beta"}""",
            manifest19 => """{"schema_version":1,"version":"0.1.0-beta.19","channel":"beta"}""",
            manifest20 => """{"schema_version":1,"version":"0.1.0-beta.20","channel":"beta"}""",
            _ => $$"""
                [
                {"tag_name":"v0.1.0-beta.19","html_url":"https://example.invalid/19","draft":false,"prerelease":true,"assets":[{"name":"update-manifest.json","browser_download_url":"{{manifest19}}"}]},
                {"tag_name":"v0.1.0-beta.16","html_url":"https://example.invalid/16","draft":false,"prerelease":true,"assets":[{"name":"update-manifest.json","browser_download_url":"{{manifest16}}"}]},
                {"tag_name":"v0.1.0-beta.20","html_url":"https://example.invalid/20","draft":false,"prerelease":true,"assets":[{"name":"update-manifest.json","browser_download_url":"{{manifest20}}"}]}
                ]
                """
        };
        return new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(json, Encoding.UTF8, "application/json")
        };
    }

    private sealed class StubHttpHandler(Func<HttpRequestMessage, HttpResponseMessage> responseFactory) : HttpMessageHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken) =>
            Task.FromResult(responseFactory(request));
    }

    private sealed class BlockingHttpHandler : HttpMessageHandler
    {
        protected override async Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request, CancellationToken cancellationToken)
        {
            await Task.Delay(Timeout.InfiniteTimeSpan, cancellationToken);
            throw new InvalidOperationException("unreachable");
        }
    }
}
