#define MyAppName "Museum PDF Tool"
#define MyAppVersion "1.0"
#define MyAppPublisher "h2O"
#define MyAppExeName "MuseumPDFTool.exe" ; PyInstaller tarafından oluşturulan exe dosyası

[Setup]
AppId={{b0cc991c-2631-43a2-82ef-9ce21792c364}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=Output
OutputBaseFilename=Setup_{#MyAppName}
PrivilegesRequired=admin

[Files]
Source: "C:\Users\koris\Documents\MuseumProject\dist\MuseumPDFTool\MuseumPDFTool.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "static\*"; DestDir: "{app}\static"; Flags: ignoreversion recursesubdirs
Source: "templates\*"; DestDir: "{app}\templates"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}";

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent