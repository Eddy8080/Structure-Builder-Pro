; Script do Inno Setup para Structure Builder Pro
; Desenvolvido para instalação profissional no Windows

[Setup]
AppId=Anagma.StructureBuilderPro.v5
AppName=Structure Builder Pro
AppVersion=5.6.2
AppPublisher=Edilson Monteiro
AppMutex=Anagma.StructureBuilderPro.v5
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
DefaultDirName={autopf}\StructureBuilderPro
DefaultGroupName=Structure Builder Pro
AllowNoIcons=yes
WizardSmallImageFile=logo_pequena.png
WizardImageFile=banner_lateral.png
; Fecha a aplicação automaticamente se estiver aberta
CloseApplications=yes
; Tenta reiniciar a aplicação se necessário
RestartApplications=yes
; Ícone do instalador e do desinstalador
SetupIconFile=logo.ico
UninstallDisplayIcon={app}\StructureBuilderPro.exe
Compression=lzma
SolidCompression=yes
WizardStyle=modern
OutputDir=output_installer
OutputBaseFilename=StructureBuilderPro_Setup_v5.6.2

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; O executável principal gerado pelo PyInstaller
Source: "dist\StructureBuilderPro.exe"; DestDir: "{app}"; Flags: ignoreversion
; Arquivo de manual
Source: "manual.html"; DestDir: "{app}"; Flags: ignoreversion
; Ícone para referência
Source: "logo.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Structure Builder Pro"; Filename: "{app}\StructureBuilderPro.exe"; IconFilename: "{app}\logo.ico"; AppUserModelID: "Anagma.StructureBuilderPro.v5"
Name: "{group}\Manual de Uso"; Filename: "{app}\manual.html"
Name: "{group}\{cm:UninstallProgram,Structure Builder Pro}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Structure Builder Pro"; Filename: "{app}\StructureBuilderPro.exe"; Tasks: desktopicon; IconFilename: "{app}\logo.ico"; AppUserModelID: "Anagma.StructureBuilderPro.v5"

[Registry]
; Engenharia Sênior: Registro Nativo no Shell do Windows para Soberania de Ícone
Root: HKCR; Subkey: "Applications\StructureBuilderPro.exe"; ValueType: string; ValueName: "FriendlyAppName"; ValueData: "Structure Builder Pro"; Flags: uninsdeletekey
Root: HKCR; Subkey: "Applications\StructureBuilderPro.exe"; ValueType: string; ValueName: "AppUserModelID"; ValueData: "Anagma.StructureBuilderPro.v5"; Flags: uninsdeletekey
Root: HKCR; Subkey: "Applications\StructureBuilderPro.exe\DefaultIcon"; ValueType: string; ValueData: "{app}\logo.ico,0"; Flags: uninsdeletekey
Root: HKCR; Subkey: "Applications\StructureBuilderPro.exe\shell\open\command"; ValueType: string; ValueData: """{app}\StructureBuilderPro.exe"""; Flags: uninsdeletekey

; Vincula o AppUserModelID globalmente para evitar que o Chrome/Edge sequestre a identidade
Root: HKCU; Subkey: "Software\Classes\AppUserModelId\Anagma.StructureBuilderPro.v5"; ValueType: string; ValueName: "DisplayName"; ValueData: "Structure Builder Pro"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\AppUserModelId\Anagma.StructureBuilderPro.v5"; ValueType: string; ValueName: "IconUri"; ValueData: "{app}\logo.ico"; Flags: uninsdeletekey

[Run]
Filename: "{app}\StructureBuilderPro.exe"; Description: "{cm:LaunchProgram,Structure Builder Pro}"; Flags: nowait postinstall skipifsilent
