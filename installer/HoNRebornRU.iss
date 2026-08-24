#ifndef MyAppVersion
  #define MyAppVersion "0.1.0-beta.1"
#endif
#ifndef BuildRoot
  #define BuildRoot "..\dist\launcher"
#endif
#ifndef OutputRoot
  #define OutputRoot "..\dist\release"
#endif

[Setup]
AppId={{A966B0F4-D8A2-4C8A-991E-9E8428CD385B}
AppName=HoN Reborn RU
AppVersion={#MyAppVersion}
AppPublisher=HoN Reborn RU Community
AppPublisherURL=https://github.com/jlambo12/HoN-Reborn-Ru
AppSupportURL=https://github.com/jlambo12/HoN-Reborn-Ru/issues
AppUpdatesURL=https://github.com/jlambo12/HoN-Reborn-Ru/releases
DefaultDirName={autopf}\HoN Reborn RU
DefaultGroupName=HoN Reborn RU
DisableProgramGroupPage=yes
OutputDir={#OutputRoot}
OutputBaseFilename=HoNRebornRU-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
UninstallDisplayName=HoN Reborn RU
CloseApplications=yes
RestartApplications=no
SetupLogging=yes
VersionInfoVersion=1.0.0.0
VersionInfoProductName=HoN Reborn RU
VersionInfoDescription=Автономный установщик русской локализации HoN Reborn
VersionInfoCompany=HoN Reborn RU Community
VersionInfoCopyright=HoN Reborn RU Community

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Files]
Source: "{#BuildRoot}\HoNRebornRU.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#BuildRoot}\HoNRebornRU.Updater.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\HoN Reborn RU"; Filename: "{app}\HoNRebornRU.exe"
Name: "{autodesktop}\HoN Reborn RU"; Filename: "{app}\HoNRebornRU.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные ярлыки:"; Flags: checkedonce

[Run]
Filename: "{app}\HoNRebornRU.exe"; Description: "Запустить HoN Reborn RU"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{app}\HoNRebornRU.exe"; Parameters: "--uninstall-silent"; Flags: runhidden waituntilterminated; RunOnceId: "RestoreHoNTranslation"
