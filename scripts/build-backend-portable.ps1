# Fallback backend bundle when PyInstaller EXEs are quarantined by Windows Defender.
# Ships an embeddable CPython runtime + the FastAPI app (no system Python required).
param(
    [string]$PythonVersion = "3.12.10",
    [string]$Python = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$backendSrc = Join-Path $repoRoot "backend"
$outDir = Join-Path $repoRoot "dist\payload\Backend"
$work = Join-Path $repoRoot "build\portable-python"
$embedZip = Join-Path $work "python-embed.zip"
$embedUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"

if (-not $Python) {
    $venvPython = Join-Path $backendSrc ".venv\Scripts\python.exe"
    $Python = if (Test-Path $venvPython) { $venvPython } else { "python" }
}

New-Item -ItemType Directory -Force -Path $work | Out-Null
if (Test-Path $outDir) {
    Remove-Item -Recurse -Force $outDir
}
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

Write-Host "Downloading embeddable Python $PythonVersion..."
Invoke-WebRequest -Uri $embedUrl -OutFile $embedZip
Expand-Archive -Path $embedZip -DestinationPath (Join-Path $outDir "python") -Force

$pth = Get-ChildItem (Join-Path $outDir "python") -Filter "python*._pth" | Select-Object -First 1
if ($pth) {
    $content = Get-Content $pth.FullName
    $content = $content | ForEach-Object {
        if ($_ -match '^#\s*import site') { 'import site' } else { $_ }
    }
    if ($content -notcontains 'import site') {
        $content += 'import site'
    }
    $content += '..'
    $content += '../app'
    Set-Content -Path $pth.FullName -Value $content -Encoding ASCII
}

Write-Host "Bootstrapping pip into embeddable runtime..."
$getPip = Join-Path $work "get-pip.py"
Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPip
$embedPy = Join-Path $outDir "python\python.exe"
& $embedPy $getPip --no-warn-script-location
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Install runtime deps only (no pytest) into the embeddable environment.
$req = Join-Path $work "requirements-runtime.txt"
Get-Content (Join-Path $backendSrc "requirements.txt") |
    Where-Object { $_ -and ($_ -notmatch '^\s*#') -and ($_ -notmatch 'pytest') } |
    Set-Content $req
& $embedPy -m pip install -r $req --no-warn-script-location
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Copy application sources next to the launcher.
Copy-Item -Recurse (Join-Path $backendSrc "app") (Join-Path $outDir "app")
Copy-Item (Join-Path $backendSrc "run_server.py") $outDir
if (Test-Path (Join-Path $backendSrc "data")) {
    Copy-Item -Recurse (Join-Path $backendSrc "data") (Join-Path $outDir "data")
}

$launcher = @'
@echo off
setlocal
cd /d "%~dp0"
"%~dp0python\python.exe" "%~dp0run_server.py" %*
'@
Set-Content -Path (Join-Path $outDir "BimAgenticBridge.Backend.cmd") -Value $launcher -Encoding ASCII

# Also provide a .exe-named shim via PowerShell wrapper for Start Menu / plugin Process.Start.
$shimPs1 = @'
param([Parameter(ValueFromRemainingArguments = $true)]$Args)
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $root "python\python.exe") (Join-Path $root "run_server.py") @Args
exit $LASTEXITCODE
'@
Set-Content -Path (Join-Path $outDir "BimAgenticBridge.Backend.ps1") -Value $shimPs1 -Encoding UTF8

Write-Host ""
Write-Host "Portable backend staged at: $outDir" -ForegroundColor Green
Write-Host "Launcher: BimAgenticBridge.Backend.cmd"
