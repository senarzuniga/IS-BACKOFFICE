# Create a Desktop shortcut to launch IS-BACKOFFICE via scripts\open_is_backoffice.bat
Param(
  [string]$ShortcutName = "IS-BACKOFFICE.lnk",
  [string]$TargetRelative = "scripts\open_is_backoffice.bat"
)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..")).Path
$target = Join-Path $repoRoot $TargetRelative
$shortcutPath = Join-Path $env:USERPROFILE "Desktop\$ShortcutName"

$wsh = New-Object -ComObject WScript.Shell
$sc = $wsh.CreateShortcut($shortcutPath)
$sc.TargetPath = $target
$sc.WorkingDirectory = $repoRoot
$sc.Arguments = ""
$icon = Join-Path $repoRoot "assets\branding\icon.ico"
if (Test-Path $icon) { $sc.IconLocation = "$icon,0" } else { $sc.IconLocation = "$target,0" }
$sc.Description = "Launch IS-BACKOFFICE (Streamlit) from repository"
$sc.Save()
Write-Output "Created shortcut at $shortcutPath pointing to $target"
