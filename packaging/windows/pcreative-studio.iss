; Pcreative Studio — instalador profesional para Windows (Inno Setup 6).
;
; Genera un único Setup .exe que instala Pcreative Studio "como cualquier app
; de Windows": carpeta en Program Files, entrada en Agregar/quitar
; programas (con icono, editor y URLs), accesos directos en el menú
; Inicio (+ escritorio opcional), registro App Paths (para lanzarla desde
; Win+R / cmd como `pcreative-studio`), y desinstalador limpio.
;
; Por defecto instala per-machine (Program Files, pide UAC) como las apps
; normales; el usuario puede cambiar a per-user en el diálogo si no tiene
; admin (PrivilegesRequiredOverridesAllowed=dialog).
;
; La versión se inyecta desde GitHub Actions con /DAppVersion=X.Y.Z.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

#define MyAppName      "Pcreative Studio"
#define MyAppPublisher "pcreativedev"
#define MyAppURL       "https://github.com/pcreativedev/pcreative-studio"
#define MyAppExeName   "PcreativeStudio.exe"

[Setup]
; AppId único e inmutable — identifica la app para upgrades/uninstall.
AppId={{A8F2E0D4-7C5B-4E1F-9B3A-2D6F0E8C5A91}
AppName={#MyAppName}
AppVersion={#AppVersion}
AppVerName={#MyAppName} {#AppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
AppCopyright=© {#MyAppPublisher}

; ── Ubicación e privilegios ──────────────────────────────────────────
; {autopf} = "Program Files" si se instala con admin (per-machine), o
; "%LOCALAPPDATA%\Programs" si el usuario elige per-user en el diálogo.
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; admin por defecto (Program Files, como las apps normales) pero el
; usuario puede cambiar a per-user si no tiene privilegios.
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; ── Salida del instalador ────────────────────────────────────────────
OutputDir=..\..\dist\installer
OutputBaseFilename=PcreativeStudio-Setup-{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; ── Requisitos / arquitectura ────────────────────────────────────────
; Qt6 necesita Windows 10 1809+ (build 17763) y x64.
MinVersion=10.0.17763
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; ── Identidad visual + Agregar/quitar programas ──────────────────────
SetupIconFile=..\..\assets\pcreative-studio.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} {#AppVersion}
LicenseFile=..\..\LICENSE
; Metadata del propio Setup.exe (Detalles → propiedades del archivo).
VersionInfoVersion={#AppVersion}.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
VersionInfoProductName={#MyAppName}

; ── Cerrar la app si está corriendo (para actualizar limpio) ─────────
CloseApplications=yes
RestartApplications=no

; NOTA: el instalador NO está firmado todavía → UAC mostrará "Editor
; desconocido" y SmartScreen avisará en la primera ejecución. Documentado
; en README. Firma futura: Azure Trusted Signing / DigiCert (ver ROADMAP).

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Bundle del output PyInstaller --onedir (incluye Qt, vendor/node+git,
; terminal/, assets). Inno recurre subdirs y crea los vacíos.
Source: "..\..\dist\PcreativeStudio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Menú Inicio
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "Crea plantillas web con agentes de IA"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; Escritorio (opcional)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; App Paths → permite lanzar "pcreative-studio" desde Win+R, cmd y el buscador.
; HKA = HKLM si per-machine, HKCU si per-user (según privilegios).
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\{#MyAppExeName}"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\{#MyAppExeName}"; ValueType: string; ValueName: "Path"; ValueData: "{app}"

[Run]
; Ofrecer lanzar la app al terminar (desmarcable).
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Limpiar artefactos generados (cache de PyInstaller). El config del
; usuario (%APPDATA%\pcreative-studio) se conserva — son sus ajustes/keys.
Type: filesandordirs; Name: "{app}\__pycache__"
