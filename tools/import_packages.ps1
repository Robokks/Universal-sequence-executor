# Imports approved local project archives into this repository, preserving existing docs.
# Run from PowerShell 7 or Windows PowerShell 5.1 with Git and downloaded ZIPs.
# Example:
# .\tools\import_packages.ps1 -PyCharmZip "D:\Downloads\PyCharm_LabVIEW_Batch_Builder_V0.6_Ready.zip"
# .\tools\import_packages.ps1 -PyCharmZip "...zip" -AixmlZip "...zip" -PythonZip "...zip" -CommitAndPush
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$PyCharmZip,
    [string]$AixmlZip,
    [string]$PythonZip,
    [switch]$CommitAndPush
)
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not (Test-Path (Join-Path $repo ".git"))) {
    throw "Run this script inside a clone of Robokks/Universal-sequence-executor"
}
function Import-Archive([string]$archive, [string]$target) {
    if (-not (Test-Path $archive -PathType Leaf)) { throw "Missing ZIP: $archive" }
    $temp = Join-Path ([IO.Path]::GetTempPath()) ("lv-executor-" + [Guid]::NewGuid().ToString("N"))
    try {
        New-Item -ItemType Directory -Path $temp -Force | Out-Null
        Expand-Archive -LiteralPath (Resolve-Path $archive).Path -DestinationPath $temp
        $children = @(Get-ChildItem -LiteralPath $temp -Force)
        if ($children.Count -eq 1 -and $children[0].PSIsContainer) {
            $source = $children[0].FullName
        } else { $source = $temp }
        New-Item -ItemType Directory -Path $target -Force | Out-Null
        Get-ChildItem -LiteralPath $source -Force | ForEach-Object {
            $to = Join-Path $target $_.Name
            if (Test-Path $to) {
                throw "Refusing to overwrite existing file or directory: $to. Review manually."
            }
            Copy-Item -LiteralPath $_.FullName -Destination $target -Recurse -Force
        }
    } finally {
        if (Test-Path $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
    }
}
Import-Archive $PyCharmZip (Join-Path $repo "tools\pycharm-batch-builder")
if ($AixmlZip) { Import-Archive $AixmlZip (Join-Path $repo "aixml-v0.4") }
if ($PythonZip) { Import-Archive $PythonZip (Join-Path $repo "simulator\python-v0.3") }
Push-Location $repo
try {
    & git status --short
    if ($LASTEXITCODE -ne 0) { throw "git status failed" }
    if ($CommitAndPush) {
        & git add tools/pycharm-batch-builder aixml-v0.4 simulator/python-v0.3
        if ($LASTEXITCODE -ne 0) { throw "git add failed" }
        & git diff --cached --stat
        Write-Host "Review the staged file list, confirm no proprietary data was included."
        & git commit -m "Import PyCharm batch builder, AIXML baseline and Python simulator"
        if ($LASTEXITCODE -ne 0) { throw "git commit failed" }
        & git push origin HEAD
        if ($LASTEXITCODE -ne 0) { throw "git push failed" }
    } else {
        Write-Host "Files staged on disk only. Review and commit/push when ready."
    }
} finally { Pop-Location }
