using System.Diagnostics;
using System.Drawing.Drawing2D;
using System.Reflection;
using System.Runtime.InteropServices;

namespace HoNRebornRu.Launcher;

internal sealed class MainForm : Form
{
    private const int WmNclButtonDown = 0xA1;
    private const int HtCaption = 0x2;

    private readonly InstallService _installer = new();
    private readonly GameLauncher _gameLauncher = new();
    private readonly UpdateClient _updateClient = new();
    private readonly LauncherSettings _settings;
    private readonly ToolTip _toolTip = new() { InitialDelay = 350, ReshowDelay = 100, AutoPopDelay = 8000 };

    private readonly Label _heroStatus = UiLabel("ПРОВЕРКА СОСТОЯНИЯ…", 11, LauncherTheme.Warning, FontStyle.Bold);
    private readonly Label _heroVersion = UiLabel("Версия —", 10, LauncherTheme.Muted);
    private readonly Label _installedValue = UiLabel("—", 22, LauncherTheme.Text, FontStyle.Bold);
    private readonly Label _availableValue = UiLabel("Последняя версия: —", 9, LauncherTheme.Muted);
    private readonly Label _lastChecked = UiLabel("Последняя проверка: ещё не выполнялась", 8.5f, LauncherTheme.Muted);
    private readonly Label _updateSummary = UiLabel("Проверяем установленный русификатор", 9.5f, LauncherTheme.Warning, FontStyle.Bold);
    private readonly Label _operationTitle = UiLabel("Подготовка", 9.5f, LauncherTheme.Text, FontStyle.Bold);
    private readonly Label _operationDetail = UiLabel("Проверяем локальную установку…", 8.5f, LauncherTheme.Muted);
    private readonly Label _progressPercent = UiLabel("0%", 8.5f, LauncherTheme.Muted, FontStyle.Bold);
    private readonly Label _gameCheck = UiLabel("• HoN: проверка", 9, LauncherTheme.Muted);
    private readonly Label _translationCheck = UiLabel("• Перевод: проверка", 9, LauncherTheme.Muted);
    private readonly Label _filesCheck = UiLabel("• Файлы: проверка", 9, LauncherTheme.Muted);
    private readonly Label _readinessHeadline = UiLabel("ПРОВЕРКА…", 11, LauncherTheme.Warning, FontStyle.Bold);
    private readonly Label _shortcutName = UiLabel("Автоматический поиск ярлыка", 8.8f, LauncherTheme.Muted);

    private readonly LauncherProgressBar _progress = new();
    private readonly LauncherButton _launchButton = UiButton("ИГРАТЬ", LauncherButtonKind.Primary);
    private readonly LauncherButton _checkButton = UiButton("ПРОВЕРИТЬ ОБНОВЛЕНИЯ", LauncherButtonKind.Secondary);
    private readonly LauncherButton _installButton = UiButton("УСТАНОВИТЬ / ОБНОВИТЬ", LauncherButtonKind.Primary);
    private readonly LauncherButton _restoreButton = UiButton("↺  ВОССТАНОВЛЕНИЕ", LauncherButtonKind.Ghost);
    private readonly LauncherButton _channelButton = UiButton("КАНАЛ: БЕТА", LauncherButtonKind.Ghost);
    private readonly LauncherButton _shortcutButton = UiButton("ВЫБРАТЬ ЯРЛЫК…", LauncherButtonKind.Secondary);
    private readonly LauncherRadioCard _officialMode = new()
    {
        Title = "ОФИЦИАЛЬНЫЙ ЯРЛЫК", Subtitle = "Ярлык игры с переводом"
    };
    private readonly LauncherRadioCard _directMode = new()
    {
        Title = "ПРЯМОЙ ЗАПУСК JUVIO", Subtitle = "Запуск напрямую с переводом"
    };

    private RemoteRelease? _remote;
    private CancellationTokenSource? _operation;
    private Image? _background;
    private bool _canLaunch;

    public MainForm()
    {
        _settings = AppStorage.Load<LauncherSettings>(AppStorage.SettingsPath);
        AutoScaleMode = AutoScaleMode.Dpi;
        AutoScaleDimensions = new SizeF(96, 96);
        Text = "HoN Reborn RU Launcher";
        ClientSize = new Size(1100, 700);
        MinimumSize = new Size(1100, 700);
        MaximumSize = new Size(1100, 700);
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.None;
        BackColor = LauncherTheme.Background;
        DoubleBuffered = true;
        LoadBackground();

        BuildTitleBar();
        BuildHero();
        BuildLaunchCard();
        BuildUpdateCard();
        BuildFooter();
        SelectLaunchMode(_settings.LaunchMode);
        UpdateChannelButton();

        Shown += async (_, _) =>
        {
            await RefreshLocalStateAsync();
            if (_settings.CheckUpdatesAtStartup) await RunGuardedAsync(CheckUpdatesAsync);
        };
        FormClosed += (_, _) =>
        {
            _operation?.Cancel();
            _updateClient.Dispose();
            _toolTip.Dispose();
            _background?.Dispose();
        };
    }

    private void BuildTitleBar()
    {
        var titleBar = new Panel
        {
            Dock = DockStyle.Top, Height = 48,
            BackColor = Color.FromArgb(245, 7, 10, 13)
        };
        var mark = UiLabel("◆", 11, LauncherTheme.Red, FontStyle.Bold);
        mark.Location = new Point(18, 14); mark.AutoSize = true;
        var title = UiLabel("HoN REBORN RU", 9.5f, LauncherTheme.Text, FontStyle.Bold);
        title.Location = new Point(42, 14); title.AutoSize = true;
        var version = UiLabel($"Launcher {Program.LauncherVersion}", 8.3f, LauncherTheme.Muted);
        version.Location = new Point(185, 15); version.AutoSize = true;

        var minimize = TitleButton("—");
        minimize.Location = new Point(1008, 0);
        minimize.Click += (_, _) => WindowState = FormWindowState.Minimized;
        var close = TitleButton("×", true);
        close.Location = new Point(1054, 0);
        close.Click += (_, _) => Close();

        titleBar.Controls.AddRange([mark, title, version, minimize, close]);
        titleBar.MouseDown += DragWindow;
        mark.MouseDown += DragWindow;
        title.MouseDown += DragWindow;
        version.MouseDown += DragWindow;
        Controls.Add(titleBar);
    }

    private void BuildHero()
    {
        var eyebrow = UiLabel("HEROES OF NEWERTH", 24, LauncherTheme.Text, FontStyle.Bold, "Georgia");
        eyebrow.Location = new Point(42, 72); eyebrow.AutoSize = true;
        var subtitle = UiLabel("РУССКАЯ ЛОКАЛИЗАЦИЯ", 14, LauncherTheme.Gold, FontStyle.Bold);
        subtitle.Location = new Point(45, 113); subtitle.AutoSize = true;
        _heroStatus.Location = new Point(46, 160); _heroStatus.AutoSize = true;
        _heroVersion.Location = new Point(46, 188); _heroVersion.AutoSize = true;

        _launchButton.Location = new Point(650, 105);
        _launchButton.Size = new Size(398, 68);
        _launchButton.Font = new Font("Segoe UI Semibold", 18, FontStyle.Bold);
        _launchButton.CornerRadius = 9;
        _launchButton.Click += (_, _) => LaunchSelected();
        var playHint = UiLabel("Запуск с русским переводом", 8.8f, LauncherTheme.Muted);
        playHint.Location = new Point(650, 181); playHint.Size = new Size(398, 24);
        playHint.TextAlign = ContentAlignment.MiddleCenter;

        Controls.AddRange([eyebrow, subtitle, _heroStatus, _heroVersion, _launchButton, playHint]);
    }

    private void BuildLaunchCard()
    {
        var card = new LauncherCard { Location = new Point(32, 230), Size = new Size(510, 350) };
        var title = SectionTitle("ЗАПУСК ИГРЫ", 22, 18);
        var description = UiLabel("Выберите проверенный способ запуска", 8.8f, LauncherTheme.Muted);
        description.Location = new Point(22, 45); description.AutoSize = true;

        _officialMode.Location = new Point(22, 76); _officialMode.Size = new Size(226, 68);
        _officialMode.Click += (_, _) => SelectLaunchMode(GameLaunchMode.OfficialShortcut);
        _directMode.Location = new Point(260, 76); _directMode.Size = new Size(226, 68);
        _directMode.Click += (_, _) => SelectLaunchMode(GameLaunchMode.Direct);

        var shortcutLabel = UiLabel("ЯРЛЫК ИГРЫ", 8, LauncherTheme.Muted, FontStyle.Bold);
        shortcutLabel.Location = new Point(22, 160); shortcutLabel.AutoSize = true;
        _shortcutName.Location = new Point(22, 181); _shortcutName.Size = new Size(274, 28);
        _shortcutName.TextAlign = ContentAlignment.MiddleLeft;
        _shortcutButton.Location = new Point(307, 174); _shortcutButton.Size = new Size(179, 38);
        _shortcutButton.Click += (_, _) => SelectShortcut();

        var gearUp = new LauncherCard
        {
            Location = new Point(22, 230), Size = new Size(464, 91), CornerRadius = 8,
            FillColor = Color.FromArgb(238, 31, 27, 20), BorderColor = Color.FromArgb(92, 74, 42)
        };
        var gearTitle = UiLabel("GEARUP", 9, LauncherTheme.Warning, FontStyle.Bold);
        gearTitle.Location = new Point(16, 12); gearTitle.AutoSize = true;
        var gearText = UiLabel("Сначала нажмите «Бустить» в GearUP, затем запускайте игру здесь.\nКнопку запуска внутри GearUP использовать не нужно.", 8.5f, Color.FromArgb(201, 187, 151));
        gearText.Location = new Point(16, 35); gearText.Size = new Size(430, 46);
        gearUp.Controls.AddRange([gearTitle, gearText]);

        card.Controls.AddRange([title, description, _officialMode, _directMode, shortcutLabel,
            _shortcutName, _shortcutButton, gearUp]);
        Controls.Add(card);
    }

    private void BuildUpdateCard()
    {
        var card = new LauncherCard { Location = new Point(558, 230), Size = new Size(510, 350) };
        var title = SectionTitle("РУСИФИКАТОР", 22, 18);
        _installedValue.Location = new Point(22, 52); _installedValue.AutoSize = true;
        _updateSummary.Location = new Point(22, 88); _updateSummary.Size = new Size(258, 24);
        _availableValue.Location = new Point(22, 116); _availableValue.Size = new Size(258, 22);
        _lastChecked.Location = new Point(22, 139); _lastChecked.Size = new Size(270, 22);

        var statusTitle = UiLabel("СОСТОЯНИЕ", 8, LauncherTheme.Muted, FontStyle.Bold);
        statusTitle.Location = new Point(306, 22); statusTitle.AutoSize = true;
        _readinessHeadline.Location = new Point(306, 47); _readinessHeadline.Size = new Size(180, 25);
        _gameCheck.Location = new Point(306, 82); _gameCheck.Size = new Size(180, 22);
        _translationCheck.Location = new Point(306, 106); _translationCheck.Size = new Size(180, 22);
        _filesCheck.Location = new Point(306, 130); _filesCheck.Size = new Size(180, 22);

        _checkButton.Location = new Point(22, 174); _checkButton.Size = new Size(202, 40);
        _checkButton.Click += async (_, _) => await RunGuardedAsync(CheckUpdatesAsync);
        _installButton.Location = new Point(234, 174); _installButton.Size = new Size(252, 40);
        _installButton.Click += async (_, _) => await RunGuardedAsync(InstallOrUpdateAsync);

        _progress.Location = new Point(22, 232); _progress.Size = new Size(410, 14);
        _progressPercent.Location = new Point(438, 226); _progressPercent.Size = new Size(48, 24);
        _progressPercent.TextAlign = ContentAlignment.MiddleRight;
        _operationTitle.Location = new Point(22, 258); _operationTitle.Size = new Size(464, 22);
        _operationDetail.Location = new Point(22, 281); _operationDetail.Size = new Size(464, 38);

        card.Controls.AddRange([title, _installedValue, _updateSummary, _availableValue, _lastChecked,
            statusTitle, _readinessHeadline, _gameCheck, _translationCheck, _filesCheck,
            _checkButton, _installButton, _progress, _progressPercent, _operationTitle, _operationDetail]);
        Controls.Add(card);
    }

    private void BuildFooter()
    {
        var footer = new Panel
        {
            Location = new Point(0, 614), Size = new Size(1100, 86),
            BackColor = Color.FromArgb(247, 8, 11, 14)
        };
        _restoreButton.Location = new Point(32, 20); _restoreButton.Size = new Size(212, 40);
        _restoreButton.Click += async (_, _) => await RestoreAsync();
        var logButton = UiButton("▣  ЖУРНАЛ", LauncherButtonKind.Ghost);
        logButton.Location = new Point(256, 20); logButton.Size = new Size(156, 40);
        logButton.Click += (_, _) => OpenLog();
        var releasesButton = UiButton("↗  РЕЛИЗЫ", LauncherButtonKind.Ghost);
        releasesButton.Location = new Point(424, 20); releasesButton.Size = new Size(156, 40);
        releasesButton.Click += (_, _) => GameLauncher.ShellOpen(
            _remote?.Release.HtmlUrl ?? "https://github.com/jlambo12/HoN-Reborn-Ru/releases");
        _channelButton.Location = new Point(592, 20); _channelButton.Size = new Size(150, 40);
        _channelButton.Font = new Font("Segoe UI Semibold", 8, FontStyle.Bold);
        _channelButton.Click += (_, _) => ToggleChannel();
        var safety = UiLabel("Автономно • SHA-256 • безопасный rollback", 8.5f, LauncherTheme.Muted);
        safety.Location = new Point(750, 23); safety.Size = new Size(180, 36);
        safety.TextAlign = ContentAlignment.MiddleRight;
        var version = UiLabel($"v{Program.LauncherVersion}", 9, LauncherTheme.Gold, FontStyle.Bold);
        version.Location = new Point(950, 30); version.Size = new Size(118, 24);
        version.TextAlign = ContentAlignment.MiddleRight;
        footer.Controls.AddRange([_restoreButton, logButton, releasesButton, _channelButton, safety, version]);
        Controls.Add(footer);
        footer.BringToFront();
    }

    private async Task CheckUpdatesAsync(CancellationToken cancellationToken)
    {
        SetOperation("Проверка версии", "Связываюсь с GitHub Releases…", 10, LauncherTheme.Warning);
        _remote = await _updateClient.FindReleaseAsync(CurrentChannel(), cancellationToken);
        _availableValue.Text = $"Последняя версия: {_remote.Manifest.Version}";
        _lastChecked.Text = $"Последняя проверка: {DateTime.Now:HH:mm}";
        var installed = await _installer.GetInstalledVersionAsync(cancellationToken);
        var needsTranslation = installed is null || IsNewer(_remote.Manifest.Version, installed);
        _updateSummary.Text = needsTranslation ? "ДОСТУПНО ОБНОВЛЕНИЕ" : "✓ Установлена последняя версия";
        _updateSummary.ForeColor = needsTranslation ? LauncherTheme.Warning : LauncherTheme.Success;
        _installButton.Text = needsTranslation ? "УСТАНОВИТЬ ОБНОВЛЕНИЕ" : "ПЕРЕУСТАНОВИТЬ";
        SetOperation("Проверка завершена", needsTranslation
            ? $"Доступна версия {_remote.Manifest.Version}."
            : "Русификатор и Launcher актуальны.", 100,
            needsTranslation ? LauncherTheme.Warning : LauncherTheme.Success);
        await OfferLauncherUpdateAsync(_remote, cancellationToken);
    }

    private async Task InstallOrUpdateAsync(CancellationToken cancellationToken)
    {
        if (_remote is null) await CheckUpdatesAsync(cancellationToken);
        var remote = _remote ?? throw new InvalidOperationException("Релиз не найден.");
        if (!remote.AssetUrls.TryGetValue(remote.Manifest.Translation.Name, out var url))
            throw new InvalidDataException("В релизе отсутствует архив перевода.");
        var temporary = Path.Combine(Path.GetTempPath(), $"HoN-Reborn-RU-{Guid.NewGuid():N}.jz");
        try
        {
            SetOperation("Скачивание", "Загружаю файлы русификатора…", 0, LauncherTheme.Warning);
            await _updateClient.DownloadAsync(url, temporary, new Progress<int>(value =>
            {
                _progress.Value = value;
                _progressPercent.Text = $"{value}%";
                _operationDetail.Text = $"Скачивание файлов… {value}%";
            }), cancellationToken);
            SetOperation("Проверка файлов", "Проверяю SHA-256 и подготавливаю установку…", 92, LauncherTheme.Warning);
            await _installer.InstallAsync(temporary, remote.Manifest, cancellationToken);
            SetOperation("Завершено", $"Русификатор {remote.Manifest.Version} установлен.", 100, LauncherTheme.Success);
            await RefreshLocalStateAsync();
        }
        finally
        {
            if (File.Exists(temporary)) File.Delete(temporary);
        }
    }

    private async Task OfferLauncherUpdateAsync(RemoteRelease remote, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(remote.Manifest.Launcher.Version) ||
            !IsNewer(remote.Manifest.Launcher.Version, Program.LauncherVersion)) return;
        if (!LauncherDialog.Confirm(this, "Обновление Launcher",
                $"Доступна новая версия Launcher {remote.Manifest.Launcher.Version}. Обновить сейчас?",
                "ОБНОВИТЬ")) return;
        if (!remote.AssetUrls.TryGetValue(remote.Manifest.Launcher.Name, out var launcherUrl) ||
            !remote.AssetUrls.TryGetValue(remote.Manifest.Updater.Name, out var updaterUrl))
            throw new InvalidDataException("В GitHub Release отсутствуют файлы обновления лаунчера.");

        var currentExecutable = Environment.ProcessPath ?? throw new InvalidOperationException("Не удалось определить путь лаунчера.");
        var installDirectory = Path.GetDirectoryName(currentExecutable)!;
        var installedUpdater = Path.Combine(installDirectory, "HoNRebornRU.Updater.exe");
        var launcherDownload = Path.Combine(Path.GetTempPath(), $"HoNRebornRU-{Guid.NewGuid():N}.exe");
        var updaterDownload = Path.Combine(Path.GetTempPath(), $"HoNRebornRU-Updater-{Guid.NewGuid():N}.exe");
        SetOperation("Обновление Launcher", "Скачиваю автономные компоненты…", 0, LauncherTheme.Warning);
        await _updateClient.DownloadAsync(launcherUrl, launcherDownload,
            new Progress<int>(value => SetProgress(value / 2, "Скачивание Launcher…")), cancellationToken);
        await VerifyAssetAsync(launcherDownload, remote.Manifest.Launcher, cancellationToken);
        await _updateClient.DownloadAsync(updaterUrl, updaterDownload,
            new Progress<int>(value => SetProgress(50 + value / 2, "Скачивание Updater…")), cancellationToken);
        await VerifyAssetAsync(updaterDownload, remote.Manifest.Updater, cancellationToken);
        Process.Start(new ProcessStartInfo
        {
            FileName = updaterDownload,
            UseShellExecute = true,
            Verb = "runas",
            ArgumentList =
            {
                "--replace", currentExecutable, launcherDownload, remote.Manifest.Launcher.Sha256,
                installedUpdater, remote.Manifest.Updater.Sha256, Environment.ProcessId.ToString()
            }
        });
        Close();
    }

    private static async Task VerifyAssetAsync(string path, ReleaseAsset asset, CancellationToken cancellationToken)
    {
        if (new FileInfo(path).Length != asset.SizeBytes)
            throw new InvalidDataException($"Размер {asset.Name} не совпадает с манифестом.");
        var hash = await InstallService.Sha256Async(path, cancellationToken);
        if (!hash.Equals(asset.Sha256, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException($"SHA-256 {asset.Name} не совпадает.");
    }

    private async Task RestoreAsync()
    {
        if (!LauncherDialog.Confirm(this, "Восстановление",
                "Восстановить расширение, которое использовалось до установки русификатора?",
                "ВОССТАНОВИТЬ")) return;
        await RunGuardedAsync(async token =>
        {
            SetOperation("Восстановление", "Проверяю резервную копию…", 30, LauncherTheme.Warning);
            await _installer.RestoreAsync(token);
            await RefreshLocalStateAsync();
            SetOperation("Восстановлено", "Предыдущая версия расширения возвращена.", 100, LauncherTheme.Success);
        });
    }

    private void LaunchSelected()
    {
        _launchButton.Text = "ЗАПУСК…";
        _launchButton.Enabled = false;
        Refresh();
        try
        {
            SaveUiSettings();
            var status = _gameLauncher.Launch(_settings.LaunchMode, _settings);
            SetOperation("Игра запущена", status, 100, LauncherTheme.Success);
            WindowState = FormWindowState.Minimized;
        }
        catch (Exception exception)
        {
            ShowError(exception);
        }
        finally
        {
            _launchButton.Text = "ИГРАТЬ";
            _launchButton.Enabled = _canLaunch && _operation is null;
        }
    }

    private void SelectShortcut()
    {
        using var dialog = new OpenFileDialog
        {
            Filter = "Ярлыки Windows (*.lnk)|*.lnk|Программы (*.exe)|*.exe",
            CheckFileExists = true,
            Title = "Выберите ярлык Heroes of Newerth Reborn"
        };
        if (dialog.ShowDialog(this) != DialogResult.OK) return;
        _settings.OfficialShortcutPath = dialog.FileName;
        AppStorage.Save(AppStorage.SettingsPath, _settings);
        RefreshShortcutState();
        SetOperation("Ярлык выбран", "Путь запуска сохранён.", 100, LauncherTheme.Success);
    }

    private async Task RefreshLocalStateAsync()
    {
        var version = await _installer.GetInstalledVersionAsync();
        var state = _installer.ReadState();
        var juvioRoot = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Juvio");
        var gameFound = File.Exists(Path.Combine(juvioRoot, "bin", "juvio.exe"));
        var stateArchive = state?.SchemaVersion == 1 ? _installer.LegacyInstalledArchive : _installer.InstalledArchive;
        var translationFound = File.Exists(stateArchive);
        var installed = version is not null && state is not null && translationFound;

        _installedValue.Text = version ?? "Не установлен";
        _heroStatus.Text = installed ? "✓ РУСИФИКАТОР УСТАНОВЛЕН" : "РУСИФИКАТОР НЕ УСТАНОВЛЕН";
        _heroStatus.ForeColor = installed ? LauncherTheme.Success : LauncherTheme.Warning;
        _heroVersion.Text = installed ? $"Версия {version}" : "Установите перевод, чтобы начать играть";
        _updateSummary.Text = installed ? "✓ Русификатор установлен" : "ТРЕБУЕТСЯ УСТАНОВКА";
        _updateSummary.ForeColor = installed ? LauncherTheme.Success : LauncherTheme.Warning;

        SetCheck(_gameCheck, gameFound, "HoN найден", "HoN не найден");
        SetCheck(_translationCheck, installed, "Перевод установлен", "Перевод не установлен");
        SetCheck(_filesCheck, translationFound, "Файлы готовы", "Файлы не готовы");
        var ready = gameFound && installed && translationFound;
        _readinessHeadline.Text = ready ? "● ВСЁ ГОТОВО" : "● НУЖНО ВНИМАНИЕ";
        _readinessHeadline.ForeColor = ready ? LauncherTheme.Success : LauncherTheme.Warning;
        _canLaunch = ready;
        _launchButton.Enabled = ready && _operation is null;
        _restoreButton.Enabled = state is not null && _operation is null;
        RefreshShortcutState();
    }

    private void RefreshShortcutState()
    {
        var configured = _settings.OfficialShortcutPath;
        var path = !string.IsNullOrWhiteSpace(configured) && File.Exists(configured)
            ? configured
            : _gameLauncher.FindOfficialShortcut();
        _shortcutName.Text = path is null ? "Ярлык не найден — выберите вручную" : Path.GetFileName(path);
        _shortcutName.ForeColor = path is null ? LauncherTheme.Warning : LauncherTheme.Text;
        _toolTip.SetToolTip(_shortcutName, path ?? "Официальный ярлык не найден");
        _shortcutButton.Text = path is null ? "ВЫБРАТЬ ЯРЛЫК…" : "ИЗМЕНИТЬ ЯРЛЫК…";
    }

    private async Task RunGuardedAsync(Func<CancellationToken, Task> action)
    {
        ToggleBusy(true);
        _operation = new CancellationTokenSource();
        try { await action(_operation.Token); }
        catch (OperationCanceledException)
        {
            SetOperation("Операция отменена", "Изменения не применялись.", 0, LauncherTheme.Warning);
        }
        catch (Exception exception) { ShowError(exception); }
        finally
        {
            _operation.Dispose();
            _operation = null;
            ToggleBusy(false);
            await RefreshLocalStateAsync();
        }
    }

    private void ShowError(Exception exception)
    {
        AppStorage.Log("ERROR " + exception);
        var (title, detail) = FriendlyError(exception);
        SetOperation(title, detail, 0, LauncherTheme.Error);
    }

    private static (string Title, string Detail) FriendlyError(Exception exception)
    {
        if (exception is HttpRequestException or TaskCanceledException)
            return ("Не удалось проверить обновления", "Проверьте подключение к интернету и повторите попытку.");
        if (exception.Message.Contains("Закройте Heroes", StringComparison.OrdinalIgnoreCase))
            return ("Игра сейчас запущена", "Закройте Heroes of Newerth Reborn и повторите операцию.");
        if (exception.Message.Contains("не установлен", StringComparison.OrdinalIgnoreCase))
            return ("Русификатор не установлен", "Сначала установите перевод в блоке обновлений.");
        if (exception.Message.Contains("ярлык", StringComparison.OrdinalIgnoreCase))
            return ("Ярлык игры не найден", "Нажмите «Выбрать ярлык» и укажите официальный ярлык HoN Reborn.");
        if (exception.Message.Contains("Стабильный релиз", StringComparison.OrdinalIgnoreCase))
            return ("Стабильный релиз пока недоступен", "Переключите канал обновлений на «Бета».");
        if (exception is UnauthorizedAccessException)
            return ("Недостаточно прав", "Перезапустите Launcher от имени администратора и повторите попытку.");
        if (exception is IOException or InvalidDataException)
            return ("Не удалось проверить файлы", "Файлы не изменены. Подробности записаны в журнал.");
        return ("Операция не выполнена", "Подробности записаны в журнал. Повторите попытку или откройте журнал.");
    }

    private void ToggleBusy(bool busy)
    {
        _checkButton.Enabled = !busy;
        _installButton.Enabled = !busy;
        _shortcutButton.Enabled = !busy;
        _channelButton.Enabled = !busy;
        _officialMode.Enabled = !busy;
        _directMode.Enabled = !busy;
        _restoreButton.Enabled = !busy && _installer.ReadState() is not null;
        _launchButton.Enabled = !busy && _canLaunch;
    }

    private void SetOperation(string title, string detail, int progress, Color color)
    {
        _operationTitle.Text = title;
        _operationTitle.ForeColor = color;
        _operationDetail.Text = detail;
        SetProgress(progress, detail);
    }

    private void SetProgress(int value, string detail)
    {
        _progress.Value = value;
        _progressPercent.Text = $"{Math.Clamp(value, 0, 100)}%";
        _operationDetail.Text = detail;
    }

    private void SelectLaunchMode(GameLaunchMode mode)
    {
        _settings.LaunchMode = mode == GameLaunchMode.Direct ? GameLaunchMode.Direct : GameLaunchMode.OfficialShortcut;
        _officialMode.Selected = _settings.LaunchMode == GameLaunchMode.OfficialShortcut;
        _directMode.Selected = _settings.LaunchMode == GameLaunchMode.Direct;
        SaveUiSettings();
    }

    private void ToggleChannel()
    {
        _settings.Channel = _settings.Channel == ReleaseChannel.Beta ? ReleaseChannel.Stable : ReleaseChannel.Beta;
        _remote = null;
        UpdateChannelButton();
        SaveUiSettings();
        _availableValue.Text = "Последняя версия: нажмите «Проверить»";
        SetOperation("Канал изменён", $"Выбран канал «{(_settings.Channel == ReleaseChannel.Beta ? "Бета" : "Стабильный")}».", 0, LauncherTheme.Warning);
    }

    private void UpdateChannelButton() => _channelButton.Text =
        _settings.Channel == ReleaseChannel.Beta ? "КАНАЛ: БЕТА" : "КАНАЛ: СТАБИЛЬНЫЙ";

    private ReleaseChannel CurrentChannel() => _settings.Channel;

    private void SaveUiSettings() => AppStorage.Save(AppStorage.SettingsPath, _settings);

    private static bool IsNewer(string candidate, string current) =>
        SemVersion.TryParse(candidate, out var left) && SemVersion.TryParse(current, out var right) &&
        left!.CompareTo(right) > 0;

    private void OpenLog()
    {
        Directory.CreateDirectory(AppStorage.Root);
        if (!File.Exists(AppStorage.LogPath)) File.WriteAllText(AppStorage.LogPath, "Журнал пока пуст.");
        GameLauncher.ShellOpen(AppStorage.LogPath);
    }

    private void LoadBackground()
    {
        using var stream = Assembly.GetExecutingAssembly()
            .GetManifestResourceStream("HoNRebornRu.Launcher.Assets.launcher-background.png");
        if (stream is null) return;
        using var image = Image.FromStream(stream);
        _background = new Bitmap(image);
    }

    protected override void OnPaintBackground(PaintEventArgs e)
    {
        e.Graphics.Clear(LauncherTheme.Background);
        if (_background is not null)
        {
            var scale = Math.Max(ClientSize.Width / (float)_background.Width, ClientSize.Height / (float)_background.Height);
            var width = (int)(_background.Width * scale);
            var height = (int)(_background.Height * scale);
            var destination = new Rectangle((ClientSize.Width - width) / 2, (ClientSize.Height - height) / 2, width, height);
            e.Graphics.DrawImage(_background, destination);
        }
        using var shade = new LinearGradientBrush(ClientRectangle,
            Color.FromArgb(126, 3, 6, 9), Color.FromArgb(218, 5, 8, 11), LinearGradientMode.Vertical);
        e.Graphics.FillRectangle(shade, ClientRectangle);
        using var sideShade = new LinearGradientBrush(ClientRectangle,
            Color.FromArgb(105, 4, 8, 11), Color.FromArgb(105, 16, 4, 5), LinearGradientMode.Horizontal);
        e.Graphics.FillRectangle(sideShade, ClientRectangle);
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        using var border = new Pen(Color.FromArgb(65, 73, 80));
        e.Graphics.DrawRectangle(border, 0, 0, Width - 1, Height - 1);
    }

    private void DragWindow(object? sender, MouseEventArgs e)
    {
        if (e.Button != MouseButtons.Left) return;
        ReleaseCapture();
        SendMessage(Handle, WmNclButtonDown, HtCaption, 0);
    }

    private static void SetCheck(Label label, bool ok, string success, string failure)
    {
        label.Text = ok ? $"✓ {success}" : $"• {failure}";
        label.ForeColor = ok ? LauncherTheme.Success : LauncherTheme.Warning;
    }

    private static Label SectionTitle(string text, int x, int y)
    {
        var label = UiLabel(text, 10, LauncherTheme.Gold, FontStyle.Bold);
        label.Location = new Point(x, y); label.AutoSize = true;
        return label;
    }

    private static Label UiLabel(string text, float size, Color color, FontStyle style = FontStyle.Regular,
        string family = "Segoe UI") => new()
    {
        Text = text,
        BackColor = Color.Transparent,
        ForeColor = color,
        Font = new Font(family, size, style),
        AutoEllipsis = true
    };

    private static LauncherButton UiButton(string text, LauncherButtonKind kind) => new()
    {
        Text = text, Kind = kind, ForeColor = LauncherTheme.Text
    };

    private static LauncherButton TitleButton(string text, bool close = false) => new()
    {
        Text = text,
        Kind = close ? LauncherButtonKind.Danger : LauncherButtonKind.Ghost,
        CornerRadius = 0,
        Size = new Size(46, 48),
        Font = new Font("Segoe UI", close ? 16 : 12, FontStyle.Regular),
        TabStop = false
    };

    [DllImport("user32.dll")]
    private static extern bool ReleaseCapture();

    [DllImport("user32.dll")]
    private static extern IntPtr SendMessage(IntPtr window, int message, int wParam, int lParam);
}
