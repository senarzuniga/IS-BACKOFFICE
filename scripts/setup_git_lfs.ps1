<#
  setup_git_lfs.ps1
  Helper script to enable Git LFS and track common media types on Windows PowerShell.

  Usage:
    .\scripts\setup_git_lfs.ps1    # will run install and track defaults
    .\scripts\setup_git_lfs.ps1 -Push  # also pushes the .gitattributes commit
#>
param(
    [switch]$Push
)

function _err_exit($msg) {
    Write-Error $msg
    exit 1
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    _err_exit "git not found in PATH. Install Git for Windows and re-run this script."
}

Write-Host "Initializing Git LFS (git lfs install) and tracking common media types..."
git lfs install

$patterns = @('*.mp4','*.mov','*.mkv','*.avi','*.zip','*.tar.gz','*.pdf','*.docx','*.pptx')
foreach ($p in $patterns) {
    git lfs track $p
}

git add .gitattributes || Write-Warning "Could not stage .gitattributes (git add failed)."
try {
    git commit -m "chore(git-lfs): track media files with Git LFS"
} catch {
    Write-Warning "Commit may have failed (nothing to commit or error)."
}

if ($Push) {
    Write-Host "Pushing to origin main..."
    git push origin main
}

Write-Host "Done. If git commands failed, run the script locally after installing Git/Git LFS."
