#define MyAppName "PC Commander"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "PC Commander"
#define MyAppExeName "PCCommander.exe"
#define MyAppURL "https://github.com/pccommander"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
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
OutputBaseFilename=PCCommander_Setup_v{#MyAppVersion}
SetupIconFile=..\assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=120
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} - Control your PC via Telegram
ShowLanguageDialog=no
LanguageDetectionMethod=locale

[Languages]
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "إنشاء اختصار على سطح المكتب"; GroupDescription: "اختصارات إضافية:"; Languages: arabic
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Languages: english
Name: "startupicon"; Description: "التشغيل التلقائي مع ويندوز"; GroupDescription: "الإعدادات:"; Languages: arabic
Name: "startupicon"; Description: "Start automatically with Windows"; GroupDescription: "Settings:"; Languages: english

[Files]
Source: "..\dist\PCCommander\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\PCCommander\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\إلغاء التثبيت"; Filename: "{uninstallexe}"; Languages: arabic
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"; Languages: english
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "PCCommander"; ValueData: """{app}\{#MyAppExeName}"" --startup"; Flags: uninsdeletevalue; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "تشغيل {#MyAppName} الآن"; Flags: nowait postinstall skipifsilent; Languages: arabic
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName} now"; Flags: nowait postinstall skipifsilent; Languages: english

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
procedure InitializeWizard;
begin
  WizardForm.WelcomeLabel2.Caption := 
    'سيقوم هذا المعالج بتثبيت ' + ExpandConstant('{#MyAppName}') + ' ' + 
    ExpandConstant('{#MyAppVersion}') + ' على جهازك.' + #13#10 + #13#10 +
    'يتيح لك هذا البرنامج التحكم الكامل بحاسبك عن بُعد عبر تيليغرام.' + #13#10 +
    'يُنصح بإغلاق جميع البرامج قبل المتابعة.';
end;
