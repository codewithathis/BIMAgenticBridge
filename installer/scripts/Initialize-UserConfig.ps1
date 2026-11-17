# Creates %LOCALAPPDATA%\BimAgenticBridge\config.json if missing (preserves existing).
param(
    [Parameter(Mandatory = $true)]
    [string]$InstallDir,
    [string]$Version = "1.0.0",
    [int]$ApiPort = 8000
)

$ErrorActionPreference = "Stop"
$root = Join-Path $env:LOCALAPPDATA "BimAgenticBridge"
New-Item -ItemType Directory -Force -Path $root | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $root "logs") | Out-Null

$configPath = Join-Path $root "config.json"
$backendExe = Join-Path $InstallDir "Backend\BimAgenticBridge.Backend.exe"
if (-not (Test-Path $backendExe)) {
    $backendExe = Join-Path $InstallDir "Backend\BimAgenticBridge.Backend.cmd"
}

if (Test-Path $configPath) {
    try {
        $existing = Get-Content -Raw -Path $configPath | ConvertFrom-Json
        # Refresh install paths / version but preserve auth_token and require_auth.
        $existing.install_dir = $InstallDir
        $existing.backend_exe_path = $backendExe
        $existing.version = $Version
        if (-not $existing.api_host) { $existing | Add-Member -NotePropertyName api_host -NotePropertyValue "127.0.0.1" -Force }
        if (-not $existing.api_port) { $existing | Add-Member -NotePropertyName api_port -NotePropertyValue $ApiPort -Force }
        if (-not $existing.api_base_url) {
            $existing | Add-Member -NotePropertyName api_base_url -NotePropertyValue ("http://127.0.0.1:{0}" -f $ApiPort) -Force
        }
        ($existing | ConvertTo-Json -Depth 5) + "`n" | Set-Content -Path $configPath -Encoding UTF8
        Write-Host "Updated existing config: $configPath"
        exit 0
    } catch {
        Write-Warning "Could not update existing config; leaving file as-is. $_"
        exit 0
    }
}

$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$token = [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+','-').Replace('/','_')

$config = [ordered]@{
    install_dir       = $InstallDir
    backend_exe_path  = $backendExe
    api_host          = "127.0.0.1"
    api_port          = $ApiPort
    api_base_url      = "http://127.0.0.1:$ApiPort"
    auth_token        = $token
    require_auth      = $true
    version           = $Version
}

($config | ConvertTo-Json -Depth 5) + "`n" | Set-Content -Path $configPath -Encoding UTF8
Write-Host "Created config: $configPath"
