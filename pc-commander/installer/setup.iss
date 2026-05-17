#define MyAppName      "NexAgent"
#define MyAppVersion   "1.2.1"
#define MyAppPublisher "NexAgent Project"
#define MyAppExeName   "NexAgent.exe"
#define MyAppURL       "https://github.com/nexagent"

[Setup]
AppId={{B9C3D7E1-F2A4-4810-BCDE-129034567891}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\LICENSE.txt
OutputDir=..\dist\installer
OutputBaseFilename=NexAgent_Setup_v{#MyAppVersion}
SetupIconFile=..\assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=120
DisableProgramGroupPage=yes
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=NexAgent - Remote PC Control via Telegram + SSH
ShowLanguageDialog=no
LanguageDetectionMethod=locale

[Languages]
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";  Description: "إنشاء اختصار على سطح المكتب"; GroupDescription: "اختصارات:"; Languages: arabic
Name: "desktopicon";  Description: "Create a &desktop icon";         GroupDescription: "Shortcuts:";   Languages: english
Name: "startupicon";  Description: "التشغيل التلقائي مع ويندوز";     GroupDescription: "الإعدادات:";  Languages: arabic
Name: "startupicon";  Description: "Start automatically with Windows"; GroupDescription: "Settings:";  Languages: english
Name: "installlayer2"; Description: "تثبيت طبقة SSH (SshRemote V2) — مطلوب صلاحيات المدير"; GroupDescription: "الطبقة الثانية:"; Languages: arabic
Name: "installlayer2"; Description: "Install SSH layer (SshRemote V2) — requires Admin rights";  GroupDescription: "Layer 2:";       Languages: english

[Files]
; Layer 1 — NexAgent Bot executable
Source: "..\dist\NexAgent\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\NexAgent\*";               DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Layer 2 — SshRemote V2 core files
Source: "..\core\sshremote_tunnel_v2.ps1"; DestDir: "{app}\core"; Flags: ignoreversion; Tasks: installlayer2
Source: "..\core\setup_v2.bat";            DestDir: "{app}\core"; Flags: ignoreversion; Tasks: installlayer2
Source: "..\core\start_tunnel_v2.bat";     DestDir: "{app}\core"; Flags: ignoreversion; Tasks: installlayer2
Source: "..\core\stop_tunnel_v2.bat";      DestDir: "{app}\core"; Flags: ignoreversion; Tasks: installlayer2
Source: "..\core\show_port_v2.bat";        DestDir: "{app}\core"; Flags: ignoreversion; Tasks: installlayer2
Source: "..\core\uninstall_v2.bat";        DestDir: "{app}\core"; Flags: ignoreversion; Tasks: installlayer2
Source: "..\core\sshremote_key.pub";       DestDir: "{app}\core"; Flags: ignoreversion; Tasks: installlayer2
Source: "..\core\sshremote_config.ini";    DestDir: "{app}\core"; Flags: ignoreversion onlyifdoesntexist; Tasks: installlayer2
Source: "..\core\README_AR.txt";           DestDir: "{app}\core"; Flags: ignoreversion; Tasks: installlayer2
Source: "..\core\README_EN.txt";           DestDir: "{app}\core"; Flags: ignoreversion; Tasks: installlayer2

; Unified config template (not overwritten if already exists)
Source: "..\nexagent_config.ini"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist

; Docs
Source: "..\DOCS.md";       DestDir: "{app}"; Flags: ignoreversion
Source: "..\INSTALL_AR.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\INSTALL_EN.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}";            Filename: "{app}\{#MyAppExeName}"
Name: "{group}\إلغاء التثبيت";           Filename: "{uninstallexe}"; Languages: arabic
Name: "{group}\Uninstall {#MyAppName}";  Filename: "{uninstallexe}"; Languages: english
Name: "{commondesktop}\{#MyAppName}";    Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{group}\SSH Setup (Layer 2)";     Filename: "{app}\core\setup_v2.bat"; Tasks: installlayer2

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "NexAgent"; ValueData: """{app}\{#MyAppExeName}"" --startup"; Flags: uninsdeletevalue; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "تشغيل {#MyAppName} الآن"; Flags: nowait postinstall skipifsilent; Languages: arabic
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName} now";  Flags: nowait postinstall skipifsilent; Languages: english

[UninstallRun]
Filename: "{app}\core\uninstall_v2.bat"; Flags: runhidden; Tasks: installlayer2

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
procedure InitializeWizard;
begin
  WizardForm.WelcomeLabel2.Caption :=
    'سيقوم هذا المعالج بتثبيت ' + ExpandConstant('{#MyAppName}') + ' ' +
    ExpandConstant('{#MyAppVersion}') + ' على جهازك.' + #13#10 + #13#10 +
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' + #13#10 +
    '🖥️  الطبقة الأولى  — بوت تيليغرام للتحكم بالحاسب' + #13#10 +
    '🔐  الطبقة الثانية — نفق SSH آمن (SshRemote V2)' + #13#10 +
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' + #13#10 + #13#10 +
    'يُنصح بإغلاق جميع البرامج قبل المتابعة.';
end;
