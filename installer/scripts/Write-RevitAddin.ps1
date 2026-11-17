# Registers BimAgenticBridge.addin for Revit 2027 after verifying Revit install.
param(
    [Parameter(Mandatory = $true)]
    [string]$PluginDllPath,
    [string]$RevitYear = "2027",
    [switch]$SkipRevitCheck
)

$ErrorActionPreference = "Stop"

function Find-Revit2027InstallPath {
    $uninstallRoots = @(
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )
    foreach ($root in $uninstallRoots) {
        $apps = Get-ItemProperty $root -ErrorAction SilentlyContinue |
            Where-Object { $_.DisplayName -and ($_.DisplayName -match "Revit\s*2027") }
        foreach ($app in $apps) {
            $loc = $app.InstallLocation
            if ($loc -and (Test-Path (Join-Path $loc "Revit.exe"))) {
                return (Resolve-Path $loc).Path
            }
        }
    }

    $candidateKeys = @(
        "HKLM:\SOFTWARE\Autodesk\Revit\2027",
        "HKLM:\SOFTWARE\WOW6432Node\Autodesk\Revit\2027"
    )
    foreach ($key in $candidateKeys) {
        if (Test-Path $key) {
            $props = Get-ItemProperty $key -ErrorAction SilentlyContinue
            foreach ($name in @("InstallPath", "InstallationLocation", "Path")) {
                $loc = $props.$name
                if ($loc -and (Test-Path (Join-Path $loc "Revit.exe"))) {
                    return (Resolve-Path $loc).Path
                }
            }
        }
    }

    $defaultPaths = @(
        "${env:ProgramFiles}\Autodesk\Revit 2027",
        "${env:ProgramFiles}\Autodesk\Revit 2027\Revit.exe"
    )
    foreach ($p in $defaultPaths) {
        if ($p.EndsWith("Revit.exe") -and (Test-Path $p)) {
            return (Split-Path $p -Parent)
        }
        if ((Test-Path $p) -and (Test-Path (Join-Path $p "Revit.exe"))) {
            return (Resolve-Path $p).Path
        }
    }
    return $null
}

if (-not (Test-Path $PluginDllPath)) {
    Write-Error "Plugin DLL not found: $PluginDllPath"
}

if (-not $SkipRevitCheck) {
    $revitPath = Find-Revit2027InstallPath
    if (-not $revitPath) {
        Write-Error "Autodesk Revit 2027 was not found. Install Revit 2027, then re-run setup."
    }
    Write-Host "Found Revit 2027 at: $revitPath"
}

$addinsDir = Join-Path $env:APPDATA "Autodesk\Revit\Addins\$RevitYear"
New-Item -ItemType Directory -Force -Path $addinsDir | Out-Null
$dllFull = (Resolve-Path $PluginDllPath).Path
$addinPath = Join-Path $addinsDir "BimAgenticBridge.addin"

$manifest = @"
<?xml version="1.0" encoding="utf-8"?>
<RevitAddIns>
  <AddIn Type="Application">
    <Name>BIM Agentic Bridge</Name>
    <Assembly>$dllFull</Assembly>
    <AddInId>B7E3D2A1-4C5F-48A9-9E10-7D6C5B4A3210</AddInId>
    <FullClassName>BimAgenticBridge.App</FullClassName>
    <VendorId>ATHISJ</VendorId>
    <VendorDescription>Athis J - AI-powered BIM room assessment for Autodesk Revit. https://github.com/codewithathis</VendorDescription>
  </AddIn>
</RevitAddIns>
"@

Set-Content -Path $addinPath -Value $manifest -Encoding UTF8
Write-Host "Wrote add-in: $addinPath"
