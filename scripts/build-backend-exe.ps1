# Freeze the FastAPI backend with PyInstaller (one-folder, Windows x64).
# If Windows Defender quarantines the unsigned bootloader EXE, falls back to
# scripts/build-backend-portable.ps1 (embeddable CPython + .cmd launcher).
param(
    [string]$Python = "",
    [switch]$SkipInstall,
    [switch]$NoFallback
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $repoRoot "backend"
$spec = Join-Path $backend "packaging\bimagenticbridge-backend.spec"
$outDist = Join-Path $repoRoot "dist\payload"

if (-not $Python) {
    $venvPython = Join-Path $backend ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        $Python = $venvPython
    } else {
        $Python = "python"
    }
}

Write-Host "Using Python: $Python"
Write-Host "Backend root: $backend"

Push-Location $backend
try {
    if (-not $SkipInstall) {
        & $Python -m pip install -r requirements.txt pyinstaller certifi
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }

    $work = Join-Path $repoRoot "build\pyinstaller"
    New-Item -ItemType Directory -Force -Path $work | Out-Null
    New-Item -ItemType Directory -Force -Path $outDist | Out-Null

    & $Python -m PyInstaller `
        --noconfirm `
        --clean `
        --distpath $outDist `
        --workpath $work `
        $spec

    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    $exe = Join-Path $outDist "Backend\BimAgenticBridge.Backend.exe"
    Start-Sleep -Milliseconds 500
    if (Test-Path $exe) {
        # Stable launcher name for Inno Start Menu shortcuts / plugin Process.Start.
        $shim = "@echo off`r`n`"%~dp0BimAgenticBridge.Backend.exe`" %*`r`n"
        Set-Content -Path (Join-Path $outDist "Backend\BimAgenticBridge.Backend.cmd") -Value $shim -Encoding ASCII
        Write-Host ""
        Write-Host "Backend frozen at:" -ForegroundColor Green
        Write-Host "  $exe"
        exit 0
    }

    Write-Host ""
    Write-Host "PyInstaller finished but BimAgenticBridge.Backend.exe is missing." -ForegroundColor Yellow
    Write-Host "Unsigned PyInstaller bootloaders are often quarantined by Windows Defender." -ForegroundColor Yellow
    Write-Host "Fix: add Defender exclusions for dist\ and build\pyinstaller\, restore the file, re-run." -ForegroundColor Yellow

    if ($NoFallback) {
        Write-Error "Expected frozen exe not found: $exe"
    }

    Write-Host "Falling back to embeddable portable backend..." -ForegroundColor Cyan
}
finally {
    Pop-Location
}

& (Join-Path $PSScriptRoot "build-backend-portable.ps1") -Python $Python
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$cmd = Join-Path $outDist "Backend\BimAgenticBridge.Backend.cmd"
if (-not (Test-Path $cmd)) {
    Write-Error "Portable backend launcher missing: $cmd"
}
Write-Host "Portable launcher ready: $cmd" -ForegroundColor Green
