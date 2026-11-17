; BIM Agentic Bridge — Inno Setup 6 script
; Build payload first via scripts/package-release.ps1
; Compile: ISCC.exe installer\BimAgenticBridge.iss

#include "version.iss"
#define MyAppName "BIM Agentic Bridge"
#define MyAppPublisher "Athis J"
#define MyAppURL "https://github.com/codewithathis/BimAgenticBridge"
; Prefer .cmd shim (works for both PyInstaller .exe and portable Python bundles).
#define MyAppExeName "BimAgenticBridge.Backend.cmd"
#define PayloadRoot "..\dist\payload"

[Setup]
AppId={{B7E3D2A1-4C5F-48A9-9E10-7D6C5B4A3210}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf64}\BimAgenticBridge
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=BIMAgenticBridge-Setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
; Prefer plugin DLL as icon source (backend may be a .cmd launcher).
UninstallDisplayIcon={app}\Plugin\BimAgenticBridge.dll
CloseApplications=yes
SetupLogging=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut for the backend"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "{#PayloadRoot}\Plugin\*"; DestDir: "{app}\Plugin"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#PayloadRoot}\Backend\*"; DestDir: "{app}\Backend"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "scripts\*"; DestDir: "{app}\InstallerScripts"; Flags: ignoreversion

[Icons]
Name: "{group}\Start Backend"; Filename: "{app}\Backend\{#MyAppExeName}"; Parameters: "serve"; WorkingDir: "{app}\Backend"
Name: "{group}\Stop Backend"; Filename: "{app}\Backend\{#MyAppExeName}"; Parameters: "--stop"; WorkingDir: "{app}\Backend"
Name: "{group}\Configure API Key"; Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\InstallerScripts\Prompt-ConfigureApiKey.ps1"" -BackendExe ""{app}\Backend\{#MyAppExeName}"""; WorkingDir: "{app}\Backend"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName} Backend"; Filename: "{app}\Backend\{#MyAppExeName}"; Parameters: "serve"; WorkingDir: "{app}\Backend"; Tasks: desktopicon

[Run]
Filename: "powershell.exe"; \
  Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\InstallerScripts\Initialize-UserConfig.ps1"" -InstallDir ""{app}"" -Version ""{#MyAppVersion}"""; \
  StatusMsg: "Writing user configuration…"; Flags: runhidden waituntilterminated
Filename: "powershell.exe"; \
  Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\InstallerScripts\Write-RevitAddin.ps1"" -PluginDllPath ""{app}\Plugin\BimAgenticBridge.dll"""; \
  StatusMsg: "Registering Revit 2027 add-in…"; Flags: runhidden waituntilterminated
Filename: "powershell.exe"; \
  Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\InstallerScripts\Save-ApiKey.ps1"" -BackendExe ""{app}\Backend\{#MyAppExeName}"" -Provider ""{code:GetProvider}"" -ApiKey ""{code:GetApiKey}"""; \
  StatusMsg: "Saving API credentials…"; Flags: runhidden waituntilterminated; Check: ShouldSaveApiKey
Filename: "{app}\Backend\{#MyAppExeName}"; Parameters: "serve"; WorkingDir: "{app}\Backend"; \
  Description: "Start local AI backend now"; Flags: nowait postinstall skipifsilent unchecked

[UninstallRun]
Filename: "{app}\Backend\{#MyAppExeName}"; Parameters: "--stop"; WorkingDir: "{app}\Backend"; RunOnceId: "StopBackend"; Flags: runhidden
Filename: "powershell.exe"; \
  Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\InstallerScripts\Remove-RevitAddin.ps1"""; \
  RunOnceId: "RemoveAddin"; Flags: runhidden waituntilterminated

[Code]
var
  ApiKeyPage: TInputQueryWizardPage;
  ProviderPage: TInputOptionWizardPage;
  RemoveUserData: Boolean;

function GetApiKey(Param: string): string;
begin
  Result := ApiKeyPage.Values[0];
end;

function GetProvider(Param: string): string;
begin
  if ProviderPage.SelectedValueIndex = 1 then
    Result := 'openai'
  else
    Result := 'gemini';
end;

function ShouldSaveApiKey: Boolean;
begin
  Result := Trim(ApiKeyPage.Values[0]) <> '';
end;

function RegFindRevit2027: Boolean;
var
  Names: TArrayOfString;
  I: Integer;
  DisplayName: string;
  UninstallKey: string;
begin
  Result := False;
  UninstallKey := 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall';
  if RegGetSubkeyNames(HKLM64, UninstallKey, Names) then
  begin
    for I := 0 to GetArrayLength(Names) - 1 do
    begin
      if RegQueryStringValue(HKLM64, UninstallKey + '\' + Names[I], 'DisplayName', DisplayName) then
      begin
        if Pos('Revit 2027', DisplayName) > 0 then
        begin
          Result := True;
          Exit;
        end;
      end;
    end;
  end;
  if RegKeyExists(HKLM64, 'SOFTWARE\Autodesk\Revit\2027') then
    Result := True;
end;

function FileFindRevit2027: Boolean;
begin
  Result := FileExists(ExpandConstant('{pf64}\Autodesk\Revit 2027\Revit.exe'))
    or FileExists(ExpandConstant('{pf}\Autodesk\Revit 2027\Revit.exe'));
end;

function InitializeSetup(): Boolean;
var
  SkipCheck: string;
begin
  Result := True;
  SkipCheck := ExpandConstant('{param:SkipRevitCheck}');
  if SkipCheck = '1' then
    Exit;

  if not RegFindRevit2027 and not FileFindRevit2027 then
  begin
    MsgBox(
      'Autodesk Revit 2027 was not detected on this computer.'#13#10#13#10 +
      'Install Revit 2027 first, then run this setup again.'#13#10 +
      '(Advanced: pass /SkipRevitCheck=1 to override.)',
      mbError,
      MB_OK);
    Result := False;
  end;
end;

procedure InitializeWizard;
begin
  ProviderPage := CreateInputOptionPage(
    wpSelectDir,
    'AI provider',
    'Choose which LLM provider to configure (optional)',
    'You can skip entering an API key and configure it later from the Start Menu.',
    True,
    False);
  ProviderPage.Add('Google Gemini');
  ProviderPage.Add('OpenAI');
  ProviderPage.SelectedValueIndex := 0;

  ApiKeyPage := CreateInputQueryPage(
    ProviderPage.ID,
    'API key (optional)',
    'Store your API key securely with Windows DPAPI',
    'Leave blank to configure later via Start Menu → BIM Agentic Bridge → Configure API Key.');
  ApiKeyPage.Add('API key:', False);
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  UserData: string;
  ResultCode: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if MsgBox(
      'Also delete user data (API credentials, config, logs, exported model JSON)?'#13#10 +
      'Choose No to keep settings for a future reinstall.',
      mbConfirmation,
      MB_YESNO) = IDYES then
    begin
      UserData := ExpandConstant('{localappdata}\BimAgenticBridge');
      Exec(
        'powershell.exe',
        '-NoProfile -ExecutionPolicy Bypass -Command "if (Test-Path ''' + UserData + ''') { Remove-Item -Recurse -Force ''' + UserData + ''' }"',
        '',
        SW_HIDE,
        ewWaitUntilTerminated,
        ResultCode);
    end;
  end;
end;
