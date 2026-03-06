; Script do Inno Setup para Structure Builder Pro
; Desenvolvido para instalação profissional no Windows

[Setup]
AppId={{google.structure.builder.pro.2.0}}
AppName=Structure Builder Pro
AppVersion=2.0
AppPublisher=Edilson Monteiro
DefaultDirName={autopf}\StructureBuilderPro
DefaultGroupName=Structure Builder Pro
AllowNoIcons=yes
; Ícone do instalador e do desinstalador
SetupIconFile=logo.ico
UninstallDisplayIcon={app}\StructureBuilderPro.exe
Compression=lzma
SolidCompression=yes
WizardStyle=modern
OutputDir=output_installer

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
Name: "{group}\Structure Builder Pro"; Filename: "{app}\StructureBuilderPro.exe"; IconFilename: "{app}\logo.ico"
Name: "{group}\Manual de Uso"; Filename: "{app}\manual.html"
Name: "{group}\{cm:UninstallProgram,Structure Builder Pro}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Structure Builder Pro"; Filename: "{app}\StructureBuilderPro.exe"; Tasks: desktopicon; IconFilename: "{app}\logo.ico"

[Run]
Filename: "{app}\StructureBuilderPro.exe"; Description: "{cm:LaunchProgram,Structure Builder Pro}"; Flags: nowait postinstall skipifsilent
