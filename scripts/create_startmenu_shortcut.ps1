Param(
  [string]$ShortcutName = "IS-BACKOFFICE.lnk",
  [string]$TargetRelative = "scripts\open_is_backoffice.bat"
)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..")).Path
$target = Join-Path $repoRoot $TargetRelative
$startMenuPath = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\$ShortcutName"

$wsh = New-Object -ComObject WScript.Shell
$sc = $wsh.CreateShortcut($startMenuPath)
$sc.TargetPath = $target
$sc.WorkingDirectory = $repoRoot
$icon = Join-Path $repoRoot "assets\branding\is_backoffice_logo.png"
if (Test-Path $icon) { $sc.IconLocation = "$icon,0" } else { $sc.IconLocation = "$target,0" }
$sc.Description = "Launch IS-BACKOFFICE (Streamlit)"
$sc.Save()
Write-Output "Created Start Menu shortcut at $startMenuPath"
