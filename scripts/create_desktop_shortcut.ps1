$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$target = Join-Path $repoRoot 'IS-BACKOFFICE_Menu_General.cmd'
$desktop = [Environment]::GetFolderPath('Desktop')
$linkPath = Join-Path $desktop 'IS-BACKOFFICE Menu General.lnk'

if (-not (Test-Path $target)) {
    throw "No se encontró el lanzador principal: $target"
}

$ws = New-Object -ComObject WScript.Shell
$shortcut = $ws.CreateShortcut($linkPath)
$shortcut.TargetPath = $target
$shortcut.WorkingDirectory = $repoRoot
$shortcut.WindowStyle = 7
$shortcut.IconLocation = "C:\Windows\System32\SHELL32.dll, 70"
$shortcut.Description = 'Abre el menú general de IS-BACKOFFICE'
$shortcut.Save()

Write-Host "Acceso directo creado en: $linkPath"
