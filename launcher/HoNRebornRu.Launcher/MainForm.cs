using System.Diagnostics;
using System.Reflection;

namespace HoNRebornRu.Launcher;

internal sealed class MainForm : Form
{
    private readonly InstallService _installer = new();
    private readonly GameLauncher _gameLauncher = new();
    private readonly UpdateClient _updateClient = new();
    private readonly LauncherSettings _settings;
    private readonly Label _installedValue = ValueLabel();
    private readonly Label _availableValue = ValueLabel();
    private readonly Label _status = new() { AutoSize = false, ForeColor = Color.FromArgb(225, 216, 190), Font = new Font("Segoe UI", 10), TextAlign = ContentAlignment.MiddleLeft };
    private readonly ProgressBar _progress = new() { Style = ProgressBarStyle.Continuous, Minimum = 0, Maximum = 100 };
    private readonly ComboBox _channel = new() { DropDownStyle = ComboBoxStyle.DropDownList };
    private readonly ComboBox _launchMode = new() { DropDownStyle = ComboBoxStyle.DropDownList };
    private readonly Button _installButton;
    private readonly Button _checkButton;
    private readonly Button _launchButton;
    private readonly Button _restoreButton;
    private RemoteRelease? _remote;
    private CancellationTokenSource? _operation;

    public MainForm()
    {
        _settings = AppStorage.Load<LauncherSettings>(AppStorage.SettingsPath);
        Text = "HoN Reborn RU Launcher";
        ClientSize = new Size(900, 600);
        MinimumSize = new Size(900, 600);
        MaximumSize = new Size(900, 600);
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.FixedSingle;
        MaximizeBox = false;
        BackColor = Color.FromArgb(8, 12, 16);
        LoadBackground();

        var header = new Panel { Dock = DockStyle.Top, Height = 112, BackColor = Color.FromArgb(225, 8, 12, 16) };
        Controls.Add(header);
        header.Controls.Add(new Label
        {
            Text = "HEROES OF NEWERTH  •  РУССКАЯ ЛОКАЛИЗАЦИЯ",
            ForeColor = Color.FromArgb(218, 178, 96), Font = new Font("Georgia", 18, FontStyle.Bold),
            AutoSize = true, Location = new Point(28, 24)
        });
        header.Controls.Add(new Label
        {
            Text = "Автономный лаунчер  •  безопасные обновления через GitHub Releases",
            ForeColor = Color.FromArgb(174, 190, 192), Font = new Font("Segoe UI", 10),
            AutoSize = true, Location = new Point(31, 65)
        });

        var body = new Panel { Location = new Point(28, 136), Size = new Size(844, 430), BackColor = Color.FromArgb(232, 12, 18, 23) };
        Controls.Add(body);

        body.Controls.Add(Caption("УСТАНОВКА И ОБНОВЛЕНИЯ", 24, 20));
        body.Controls.Add(SmallLabel("Установленная версия", 26, 62));
        _installedValue.Location = new Point(210, 58); body.Controls.Add(_installedValue);
        body.Controls.Add(SmallLabel("Доступная версия", 26, 94));
        _availableValue.Location = new Point(210, 90); body.Controls.Add(_availableValue);
        body.Controls.Add(SmallLabel("Канал обновлений", 26, 132));
        _channel.Items.AddRange(["Стабильный", "Бета"]);
        _channel.SelectedIndex = _settings.Channel == ReleaseChannel.Stable ? 0 : 1;
        _channel.Location = new Point(210, 129); _channel.Size = new Size(180, 28);
        _channel.SelectedIndexChanged += (_, _) => SaveUiSettings();
        body.Controls.Add(_channel);

        _checkButton = ThemeButton("ПРОВЕРИТЬ", 26, 174, 174, Color.FromArgb(45, 91, 111));
        _checkButton.Click += async (_, _) => await RunGuardedAsync(CheckUpdatesAsync);
        body.Controls.Add(_checkButton);
        _installButton = ThemeButton("УСТАНОВИТЬ / ОБНОВИТЬ", 212, 174, 246, Color.FromArgb(126, 49, 38));
        _installButton.Click += async (_, _) => await RunGuardedAsync(InstallOrUpdateAsync);
        body.Controls.Add(_installButton);

        body.Controls.Add(Caption("ЗАПУСК ИГРЫ", 480, 20));
        body.Controls.Add(SmallLabel("Способ запуска", 482, 62));
        _launchMode.Items.AddRange(["Официальный ярлык", "GearUP", "Прямой запуск Juvio"]);
        _launchMode.SelectedIndex = (int)_settings.LaunchMode;
        _launchMode.Location = new Point(482, 88); _launchMode.Size = new Size(322, 28);
        _launchMode.SelectedIndexChanged += (_, _) => SaveUiSettings();
        body.Controls.Add(_launchMode);
        _launchButton = ThemeButton("ЗАПУСТИТЬ ИГРУ", 482, 132, 322, Color.FromArgb(111, 75, 32));
        _launchButton.Click += (_, _) => LaunchSelected();
        body.Controls.Add(_launchButton);
        var shortcutButton = ThemeButton("ВЫБРАТЬ ЯРЛЫК…", 482, 184, 156, Color.FromArgb(50, 61, 66));
        shortcutButton.Click += (_, _) => SelectShortcut();
        body.Controls.Add(shortcutButton);
        var releasesButton = ThemeButton("СТРАНИЦА РЕЛИЗОВ", 648, 184, 156, Color.FromArgb(50, 61, 66));
        releasesButton.Click += (_, _) => GameLauncher.ShellOpen(_remote?.Release.HtmlUrl ?? "https://github.com/jlambo12/HoN-Reborn-Ru/releases");
        body.Controls.Add(releasesButton);

        var separator = new Panel { Location = new Point(24, 248), Size = new Size(796, 1), BackColor = Color.FromArgb(76, 89, 91) };
        body.Controls.Add(separator);
        _status.Location = new Point(26, 262); _status.Size = new Size(778, 48); _status.Text = "Подготовка…";
        body.Controls.Add(_status);
        _progress.Location = new Point(26, 319); _progress.Size = new Size(778, 18); body.Controls.Add(_progress);
        _restoreButton = ThemeButton("ВОССТАНОВИТЬ ПРЕДЫДУЩУЮ ВЕРСИЮ", 26, 356, 322, Color.FromArgb(63, 55, 51));
        _restoreButton.Click += async (_, _) => await RestoreAsync();
        body.Controls.Add(_restoreButton);
        var logButton = ThemeButton("ОТКРЫТЬ ЖУРНАЛ", 638, 356, 166, Color.FromArgb(50, 61, 66));
        logButton.Click += (_, _) => OpenLog();
        body.Controls.Add(logButton);

        Shown += async (_, _) =>
        {
            await RefreshLocalStateAsync();
            if (_settings.CheckUpdatesAtStartup) await RunGuardedAsync(CheckUpdatesAsync);
        };
        FormClosed += (_, _) => { _operation?.Cancel(); _updateClient.Dispose(); };
    }

    private async Task CheckUpdatesAsync(CancellationToken cancellationToken)
    {
        SetStatus("Проверяю GitHub Releases…", 10);
        _remote = await _updateClient.FindReleaseAsync(CurrentChannel(), cancellationToken);
        _availableValue.Text = _remote.Manifest.Version;
        var installed = await _installer.GetInstalledVersionAsync(cancellationToken);
        var needsTranslation = installed is null || IsNewer(_remote.Manifest.Version, installed);
        SetStatus(needsTranslation ? $"Доступен перевод {_remote.Manifest.Version}." : "Установлена актуальная версия перевода.", 100);
        await OfferLauncherUpdateAsync(_remote, cancellationToken);
    }

    private async Task InstallOrUpdateAsync(CancellationToken cancellationToken)
    {
        if (_remote is null) await CheckUpdatesAsync(cancellationToken);
        var remote = _remote ?? throw new InvalidOperationException("Релиз не найден.");
        if (!remote.AssetUrls.TryGetValue(remote.Manifest.Translation.Name, out var url)) throw new InvalidDataException("В релизе отсутствует архив перевода.");
        var temporary = Path.Combine(Path.GetTempPath(), $"HoN-Reborn-RU-{Guid.NewGuid():N}.jz");
        try
        {
            SetStatus("Скачиваю перевод…", 0);
            await _updateClient.DownloadAsync(url, temporary, new Progress<int>(value => _progress.Value = value), cancellationToken);
            SetStatus("Проверяю и устанавливаю перевод…", 100);
            await _installer.InstallAsync(temporary, remote.Manifest, cancellationToken);
            await RefreshLocalStateAsync();
            SetStatus($"Перевод {remote.Manifest.Version} установлен. Можно запускать игру.", 100);
        }
        finally
        {
            if (File.Exists(temporary)) File.Delete(temporary);
        }
    }

    private async Task OfferLauncherUpdateAsync(RemoteRelease remote, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(remote.Manifest.Launcher.Version) || !IsNewer(remote.Manifest.Launcher.Version, Program.LauncherVersion)) return;
        if (MessageBox.Show($"Доступна новая версия лаунчера {remote.Manifest.Launcher.Version}. Обновить сейчас?", "HoN Reborn RU", MessageBoxButtons.YesNo, MessageBoxIcon.Information) != DialogResult.Yes) return;
        if (!remote.AssetUrls.TryGetValue(remote.Manifest.Launcher.Name, out var launcherUrl) ||
            !remote.AssetUrls.TryGetValue(remote.Manifest.Updater.Name, out var updaterUrl))
            throw new InvalidDataException("В GitHub Release отсутствуют файлы обновления лаунчера.");

        var currentExecutable = Environment.ProcessPath ?? throw new InvalidOperationException("Не удалось определить путь лаунчера.");
        var installDirectory = Path.GetDirectoryName(currentExecutable)!;
        var installedUpdater = Path.Combine(installDirectory, "HoNRebornRU.Updater.exe");
        var launcherDownload = Path.Combine(Path.GetTempPath(), $"HoNRebornRU-{Guid.NewGuid():N}.exe");
        var updaterDownload = Path.Combine(Path.GetTempPath(), $"HoNRebornRU-Updater-{Guid.NewGuid():N}.exe");
        SetStatus("Скачиваю обновление лаунчера…", 0);
        await _updateClient.DownloadAsync(launcherUrl, launcherDownload, new Progress<int>(value => _progress.Value = value / 2), cancellationToken);
        await VerifyAssetAsync(launcherDownload, remote.Manifest.Launcher, cancellationToken);
        await _updateClient.DownloadAsync(updaterUrl, updaterDownload, new Progress<int>(value => _progress.Value = 50 + value / 2), cancellationToken);
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
        if (new FileInfo(path).Length != asset.SizeBytes) throw new InvalidDataException($"Размер {asset.Name} не совпадает с манифестом.");
        var hash = await InstallService.Sha256Async(path, cancellationToken);
        if (!hash.Equals(asset.Sha256, StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException($"SHA-256 {asset.Name} не совпадает.");
    }

    private async Task RestoreAsync()
    {
        if (MessageBox.Show("Восстановить расширение и язык, которые использовались до установки русификатора?", "HoN Reborn RU", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
        await RunGuardedAsync(async token =>
        {
            SetStatus("Восстанавливаю предыдущую версию…", 30);
            await _installer.RestoreAsync(token);
            await RefreshLocalStateAsync();
            SetStatus("Предыдущая версия восстановлена.", 100);
        });
    }

    private void LaunchSelected()
    {
        try
        {
            SaveUiSettings();
            _gameLauncher.Launch(_settings.LaunchMode, _settings);
            SetStatus(_settings.LaunchMode == GameLaunchMode.GearUp
                ? "GearUP открыт. Запустите HoN Reborn внутри GearUP."
                : "Игра запущена.", 100);
        }
        catch (Exception exception) { ShowError(exception); }
    }

    private void SelectShortcut()
    {
        using var dialog = new OpenFileDialog { Filter = "Ярлыки Windows (*.lnk)|*.lnk|Программы (*.exe)|*.exe", CheckFileExists = true };
        if (dialog.ShowDialog(this) != DialogResult.OK) return;
        if (_settings.LaunchMode == GameLaunchMode.GearUp) _settings.GearUpShortcutPath = dialog.FileName;
        else _settings.OfficialShortcutPath = dialog.FileName;
        AppStorage.Save(AppStorage.SettingsPath, _settings);
        SetStatus("Путь запуска сохранён.", 100);
    }

    private async Task RefreshLocalStateAsync()
    {
        var version = await _installer.GetInstalledVersionAsync();
        _installedValue.Text = version ?? "не установлен";
        _restoreButton.Enabled = _installer.ReadState() is not null;
    }

    private async Task RunGuardedAsync(Func<CancellationToken, Task> action)
    {
        ToggleBusy(true);
        _operation = new CancellationTokenSource();
        try { await action(_operation.Token); }
        catch (OperationCanceledException) { SetStatus("Операция отменена.", 0); }
        catch (Exception exception) { ShowError(exception); }
        finally { _operation.Dispose(); _operation = null; ToggleBusy(false); }
    }

    private void ShowError(Exception exception)
    {
        AppStorage.Log("ERROR " + exception);
        SetStatus("Ошибка: " + exception.Message, 0);
        MessageBox.Show(exception.Message, "HoN Reborn RU", MessageBoxButtons.OK, MessageBoxIcon.Error);
    }

    private void ToggleBusy(bool busy)
    {
        _checkButton.Enabled = !busy; _installButton.Enabled = !busy; _restoreButton.Enabled = !busy && _installer.ReadState() is not null;
    }

    private void SetStatus(string text, int progress)
    {
        _status.Text = text; _progress.Value = Math.Clamp(progress, 0, 100);
    }

    private ReleaseChannel CurrentChannel() => _channel.SelectedIndex == 0 ? ReleaseChannel.Stable : ReleaseChannel.Beta;
    private void SaveUiSettings()
    {
        _settings.Channel = CurrentChannel();
        _settings.LaunchMode = (GameLaunchMode)Math.Max(0, _launchMode.SelectedIndex);
        AppStorage.Save(AppStorage.SettingsPath, _settings);
    }

    private static bool IsNewer(string candidate, string current) =>
        SemVersion.TryParse(candidate, out var left) && SemVersion.TryParse(current, out var right) && left!.CompareTo(right) > 0;

    private void OpenLog()
    {
        Directory.CreateDirectory(AppStorage.Root);
        if (!File.Exists(AppStorage.LogPath)) File.WriteAllText(AppStorage.LogPath, "Журнал пока пуст.");
        GameLauncher.ShellOpen(AppStorage.LogPath);
    }

    private void LoadBackground()
    {
        using var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream("HoNRebornRu.Launcher.Assets.launcher-background.png");
        if (stream is null) return;
        using var image = Image.FromStream(stream);
        BackgroundImage = new Bitmap(image);
        BackgroundImageLayout = ImageLayout.Stretch;
    }

    private static Label Caption(string text, int x, int y) => new()
    {
        Text = text, Location = new Point(x, y), AutoSize = true,
        ForeColor = Color.FromArgb(207, 170, 91), Font = new Font("Segoe UI Semibold", 11, FontStyle.Bold)
    };

    private static Label SmallLabel(string text, int x, int y) => new()
    {
        Text = text, Location = new Point(x, y), AutoSize = true,
        ForeColor = Color.FromArgb(173, 184, 184), Font = new Font("Segoe UI", 9)
    };

    private static Label ValueLabel() => new()
    {
        AutoSize = true, ForeColor = Color.White, Font = new Font("Segoe UI Semibold", 10, FontStyle.Bold), Text = "—"
    };

    private static Button ThemeButton(string text, int x, int y, int width, Color color)
    {
        var button = new Button
        {
            Text = text, Location = new Point(x, y), Size = new Size(width, 40), BackColor = color,
            ForeColor = Color.White, FlatStyle = FlatStyle.Flat, Font = new Font("Segoe UI Semibold", 9, FontStyle.Bold), Cursor = Cursors.Hand
        };
        button.FlatAppearance.BorderColor = Color.FromArgb(179, 143, 72);
        button.FlatAppearance.BorderSize = 1;
        return button;
    }
}
