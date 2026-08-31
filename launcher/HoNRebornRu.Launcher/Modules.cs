namespace HoNRebornRu.Launcher;

internal enum HonPlusModuleState
{
    NotInstalled,
    Installed,
    NeedsAttention
}

internal sealed record HonPlusModuleDescriptor(
    string Id,
    string DisplayName,
    string Description);

internal sealed record HonPlusModuleSnapshot(
    HonPlusModuleState State,
    string? Version,
    bool GameFound,
    bool FilesFound,
    bool CanRemove);

internal interface IHonPlusModule
{
    HonPlusModuleDescriptor Descriptor { get; }

    Task<HonPlusModuleSnapshot> InspectAsync(CancellationToken cancellationToken = default);

    Task InstallAsync(
        string packagePath,
        UpdateManifest manifest,
        CancellationToken cancellationToken = default);

    Task RemoveAsync(CancellationToken cancellationToken = default);
}

internal sealed class LocalizationModule : IHonPlusModule
{
    public const string ModuleId = "ru-localization";

    private readonly InstallService _installer;

    public LocalizationModule(InstallService? installer = null)
    {
        _installer = installer ?? new InstallService();
    }

    public HonPlusModuleDescriptor Descriptor { get; } = new(
        ModuleId,
        "Русская локализация",
        "Русский интерфейс, сообщения и описания игрового контента.");

    public async Task<HonPlusModuleSnapshot> InspectAsync(CancellationToken cancellationToken = default)
    {
        var state = _installer.ReadState();
        var version = await _installer.GetInstalledVersionAsync(cancellationToken);
        var archive = state?.SchemaVersion == 2
            ? _installer.BaseOverlayArchive
            : _installer.InstalledArchive;
        var filesFound = File.Exists(archive);
        var gameFound = File.Exists(Path.Combine(_installer.JuvioRoot, "bin", "juvio.exe"));
        var installed = version is not null && state is not null && filesFound;
        var moduleState = installed
            ? HonPlusModuleState.Installed
            : state is not null || filesFound
                ? HonPlusModuleState.NeedsAttention
                : HonPlusModuleState.NotInstalled;

        return new HonPlusModuleSnapshot(moduleState, version, gameFound, filesFound, state is not null);
    }

    public Task InstallAsync(
        string packagePath,
        UpdateManifest manifest,
        CancellationToken cancellationToken = default) =>
        _installer.InstallAsync(packagePath, manifest, cancellationToken);

    public Task RemoveAsync(CancellationToken cancellationToken = default) =>
        _installer.RestoreAsync(cancellationToken);
}

internal static class ModuleCatalog
{
    public static IReadOnlyList<IHonPlusModule> CreateDefault() =>
        [new LocalizationModule()];

    public static IHonPlusModule Require(IReadOnlyList<IHonPlusModule> modules, string id) =>
        modules.Single(module => module.Descriptor.Id.Equals(id, StringComparison.OrdinalIgnoreCase));

    internal static bool HasUniqueIds(IReadOnlyList<IHonPlusModule> modules) =>
        modules.Select(module => module.Descriptor.Id).Distinct(StringComparer.OrdinalIgnoreCase).Count() == modules.Count;
}
