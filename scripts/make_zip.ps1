# make_zip.ps1  — run from the DocuSense directory
# Creates DocuSense_IBM_SkillsBuild_2026.zip in the parent folder
# Excludes: .venv/, data/raw/, data/processed/, *.db, *.joblib, *.log,
#           __pycache__/, .pytest_cache/, .idea/, .DS_Store

$REPO = Split-Path -Parent $PSScriptRoot
if (-not $REPO) { $REPO = Split-Path -Parent (Get-Location) }
# Support running from repo root
$HERE = $PSCommandPath | Split-Path -Parent
$REPO_ROOT = $HERE | Split-Path -Parent

$SRC  = $REPO_ROOT   # the DocuSense/ folder
$DEST = Join-Path (Split-Path -Parent $SRC) "DocuSense_IBM_SkillsBuild_2026.zip"

Write-Host "Packing: $SRC"
Write-Host "  -> $DEST"

# Exclusion patterns (relative paths under DocuSense/)
$EXCLUDES = @(
    ".venv",
    "venv",
    "data\raw",
    "data\processed",
    "playwright-browsers",
    ".pytest_cache",
    ".mypy_cache",
    "__pycache__",
    ".idea",
    ".vscode"
)

# Get all items recursively, excluding unwanted paths
$allFiles = Get-ChildItem -Path $SRC -Recurse -File | Where-Object {
    $rel = $_.FullName.Substring($SRC.Length + 1)
    $skip = $false
    foreach ($ex in $EXCLUDES) {
        if ($rel.StartsWith($ex + "\") -or $rel -eq $ex) { $skip = $true; break }
    }
    # Also skip *.db, *.joblib, *.log, *.zip
    if ($_.Extension -in @(".db", ".joblib", ".log", ".zip")) { $skip = $true }
    -not $skip
}

Write-Host "Files to include: $($allFiles.Count)"

if (Test-Path $DEST) { Remove-Item $DEST }

# Use Compress-Archive with -DestinationPath and pipe entries
$tempDir = Join-Path $env:TEMP "DocuSense_pack_$(Get-Random)"
New-Item -ItemType Directory -Path $tempDir | Out-Null

foreach ($f in $allFiles) {
    $rel  = $f.FullName.Substring($SRC.Length + 1)
    $dest = Join-Path $tempDir $rel
    $dir  = Split-Path -Parent $dest
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
    Copy-Item $f.FullName $dest
}

Compress-Archive -Path "$tempDir\*" -DestinationPath $DEST -CompressionLevel Optimal
Remove-Item -Recurse -Force $tempDir

$size = (Get-Item $DEST).Length / 1MB
Write-Host "Done!  $DEST  ($([math]::Round($size,1)) MB)"
