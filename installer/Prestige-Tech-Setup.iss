#define MyAppName "Prestige Tech Dashboard"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Prestige Tech"
#define MyAppExeName "Prestige-Tech-Dashboard.exe"

[Setup]
AppId={{FBAFA82B-BB63-5986-AAF5-6AA73F07DA6C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Prestige Tech Dashboard Installer
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoVersion=1.0.0.0
DefaultDirName={autopf}\Prestige Tech\Dashboard
DefaultGroupName=Prestige Tech
DisableProgramGroupPage=yes
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist-installer
OutputBaseFilename=Prestige-Tech-Setup
SetupIconFile=prestige_tech_app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
SetupLogging=yes
UsePreviousAppDir=yes
UsePreviousGroup=yes
AllowNoIcons=yes
MinVersion=10.0
AppMutex=PrestigeTech.Dashboard.1.0

[Tasks]
Name: "desktopicon"; Description: "Utwórz skrót na pulpicie"; GroupDescription: "Dodatkowe skróty:"; Flags: unchecked

[Files]
Source: "payload\Prestige-Tech-Dashboard.exe"; DestDir: "{app}"; DestName: "{#MyAppExeName}"; Flags: ignoreversion

[Icons]
Name: "{group}\Prestige Tech Dashboard"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\Prestige Tech Dashboard"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Uruchom Prestige Tech Dashboard"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{cmd}"; Parameters: "/C taskkill /F /IM Prestige-Tech-Dashboard.exe >nul 2>&1"; Flags: runhidden; RunOnceId: "StopPrestigeTechDashboard"

