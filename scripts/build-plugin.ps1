# Build the Revit plugin and refresh the .addin install.
# Revit must be closed first - it locks bin\Debug\BimAgenticBridge.dll.

param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Debug",
    [string]$RevitInstallPath = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$dotnet = "C:\Program Files\dotnet\dotnet.exe"
if (-not (Test-Path $dotnet)) {
    $dotnet = "dotnet"
}

$revit = Get-Process -Name "Revit" -ErrorAction SilentlyContinue
if ($revit) {
    $pids = ($revit | ForEach-Object { $_.Id }) -join ", "
    Write-Host ""
    Write-Host "Cannot build: Autodesk Revit is running (PID $pids)." -ForegroundColor Red
    Write-Host "It locks: revit-plugin\BimAgenticBridge\bin\$Configuration\BimAgenticBridge.dll" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Fix:"
    Write-Host "  1. Close all Revit windows"
    Write-Host "  2. Re-run: powershell -ExecutionPolicy Bypass -File .\scripts\build-plugin.ps1"
    Write-Host ""
    exit 1
}

$sln = Join-Path $repoRoot "revit-plugin\BimAgenticBridge.sln"
$args = @("build", $sln, "-c", $Configuration)
if ($RevitInstallPath) {
    $args += "-p:RevitInstallPath=$RevitInstallPath"
}

Write-Host "Building plugin ($Configuration)..."
& $dotnet @args
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Installing add-in..."
& (Join-Path $PSScriptRoot "install-addin.ps1") -Configuration $Configuration
Write-Host ""
Write-Host "Done. Start Revit 2027 to load the updated plugin." -ForegroundColor Green
