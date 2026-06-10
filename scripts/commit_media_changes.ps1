<#
  commit_media_changes.ps1
  Stages the media panel changes and commits them locally. Optionally pushes.

  Usage:
    .\scripts\commit_media_changes.ps1           # commit locally
    .\scripts\commit_media_changes.ps1 -Push    # commit and push to origin/main
#>
param(
    [switch]$Push,
    [string]$Branch = "main"
)

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "git not found in PATH. Install Git and run this script locally."
    exit 1
}

$files = @("backoffice/ui/media_upload_panel.py", "streamlit_app.py", ".gitattributes")
Write-Host "Staging: $files"
git add -- $files

try {
    git commit -m "feat(media): add media upload panel and menu entry"
} catch {
    Write-Warning "Commit may have failed (nothing to commit or error)."
}

if ($Push) {
    git push origin $Branch
}

Write-Host "Done. Verify with 'git status' and 'git log -n 5'."
