using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;

namespace HoNRebornRu.Launcher;

internal static class ShortcutService
{
    private const string PlayShortcutName = "HoN Reborn RU — Играть.lnk";

    public static void EnsurePlayShortcutForInstalledBuild()
    {
        var executable = Environment.ProcessPath;
        if (string.IsNullOrWhiteSpace(executable) || !IsUnderProgramFiles(executable)) return;

        CreateUserPlayShortcut(executable);
    }

    public static string CreateUserPlayShortcut(string executable)
    {
        executable = Path.GetFullPath(executable);

        var commonShortcut = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.CommonDesktopDirectory), PlayShortcutName);
        if (File.Exists(commonShortcut)) return commonShortcut;

        var userShortcut = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), PlayShortcutName);
        CreateShortcut(userShortcut, executable, "--launch-game", "Запустить HoN Reborn с русским переводом");
        AppStorage.Log($"Created localized game shortcut: {userShortcut}");
        return userShortcut;
    }

    public static void RemoveUserPlayShortcut()
    {
        var path = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), PlayShortcutName);
        if (File.Exists(path)) File.Delete(path);
    }

    private static bool IsUnderProgramFiles(string path)
    {
        var fullPath = Path.GetFullPath(path);
        return IsUnder(fullPath, Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles)) ||
               IsUnder(fullPath, Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86));
    }

    private static bool IsUnder(string path, string root)
    {
        if (string.IsNullOrWhiteSpace(root)) return false;
        var prefix = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        return path.StartsWith(prefix, StringComparison.OrdinalIgnoreCase);
    }

    private static void CreateShortcut(string shortcutPath, string targetPath, string arguments, string description)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(shortcutPath)!);
        var link = (IShellLinkW)new ShellLink();
        try
        {
            link.SetPath(targetPath);
            link.SetArguments(arguments);
            link.SetWorkingDirectory(Path.GetDirectoryName(targetPath)!);
            link.SetDescription(description);
            link.SetIconLocation(targetPath, 0);
            ((IPersistFile)link).Save(shortcutPath, true);
        }
        finally
        {
            Marshal.FinalReleaseComObject(link);
        }
    }

    [ComImport]
    [Guid("00021401-0000-0000-C000-000000000046")]
    private class ShellLink;

    [ComImport]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    [Guid("000214F9-0000-0000-C000-000000000046")]
    private interface IShellLinkW
    {
        void GetPath([Out, MarshalAs(UnmanagedType.LPWStr)] System.Text.StringBuilder file, int maximumPath,
            IntPtr findData, uint flags);
        void GetIDList(out IntPtr itemIdList);
        void SetIDList(IntPtr itemIdList);
        void GetDescription([Out, MarshalAs(UnmanagedType.LPWStr)] System.Text.StringBuilder name, int maximumName);
        void SetDescription([MarshalAs(UnmanagedType.LPWStr)] string name);
        void GetWorkingDirectory([Out, MarshalAs(UnmanagedType.LPWStr)] System.Text.StringBuilder directory, int maximumPath);
        void SetWorkingDirectory([MarshalAs(UnmanagedType.LPWStr)] string directory);
        void GetArguments([Out, MarshalAs(UnmanagedType.LPWStr)] System.Text.StringBuilder arguments, int maximumPath);
        void SetArguments([MarshalAs(UnmanagedType.LPWStr)] string arguments);
        void GetHotkey(out short hotkey);
        void SetHotkey(short hotkey);
        void GetShowCmd(out int showCommand);
        void SetShowCmd(int showCommand);
        void GetIconLocation([Out, MarshalAs(UnmanagedType.LPWStr)] System.Text.StringBuilder iconPath,
            int maximumPath, out int iconIndex);
        void SetIconLocation([MarshalAs(UnmanagedType.LPWStr)] string iconPath, int iconIndex);
        void SetRelativePath([MarshalAs(UnmanagedType.LPWStr)] string path, uint reserved);
        void Resolve(IntPtr window, uint flags);
        void SetPath([MarshalAs(UnmanagedType.LPWStr)] string path);
    }
}
