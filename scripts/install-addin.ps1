# Installs BIM Agentic Bridge into the current user's Revit 2027 Addins folder.
# Run from repo root after a successful Debug (or Release) build.

param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Debug",
    [string]$RevitYear = "2027"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$dllPath = Join-Path $repoRoot "revit-plugin\BimAgenticBridge\bin\$Configuration\BimAgenticBridge.dll"

if (-not (Test-Path $dllPath)) {
    Write-Error "Built DLL not found: $dllPath`nBuild the plugin first, then re-run this script."
}

$addinsDir = Join-Path $env:APPDATA "Autodesk\Revit\Addins\$RevitYear"
New-Item -ItemType Directory -Force -Path $addinsDir | Out-Null

$addinPath = Join-Path $addinsDir "BimAgenticBridge.addin"
$dllFull = (Resolve-Path $dllPath).Path

@"
<?xml version="1.0" encoding="utf-8"?>
<RevitAddIns>
  <AddIn Type="Application">
    <Name>BIM Agentic Bridge</Name>
    <Assembly>$dllFull</Assembly>
    <AddInId>B7E3D2A1-4C5F-48A9-9E10-7D6C5B4A3210</AddInId>
    <FullClassName>BimAgenticBridge.App</FullClassName>
    <VendorId>ATHISJ</VendorId>
    <VendorDescription>Athis J — AI-powered BIM room assessment for Autodesk Revit. https://github.com/codewithathis</VendorDescription>
  </AddIn>
</RevitAddIns>
"@ | Set-Content -Path $addinPath -Encoding UTF8

Write-Host "Installed add-in manifest:"
Write-Host "  $addinPath"
Write-Host "Assembly:"
Write-Host "  $dllFull"
Write-Host ""
Write-Host "Restart Revit $RevitYear, then open ribbon tab 'BIM Agentic' → 'AI Chat'."
Write-Host "Author: Athis J — https://github.com/codewithathis"
