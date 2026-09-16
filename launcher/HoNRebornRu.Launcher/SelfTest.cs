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
            if (release.Manifest.Version != "0.1.0-beta.20") failures.Add("direct fallback release version");
        }
        catch (Exception exception)
        {
            failures.Add("direct fallback after proxy failure: " + exception.GetType().Name);
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
        const string manifestUrl = "https://downloads.example/update-manifest.json";
        var json = request.RequestUri?.AbsoluteUri == manifestUrl
            ? """{"schema_version":1,"version":"0.1.0-beta.20","channel":"beta"}"""
            : $$"""[{"tag_name":"v0.1.0-beta.20","html_url":"https://example.invalid/release","draft":false,"prerelease":true,"assets":[{"name":"update-manifest.json","browser_download_url":"{{manifestUrl}}"}]}]""";
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
}
