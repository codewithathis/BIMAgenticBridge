# Saves DPAPI-protected credentials by invoking the frozen backend configure command.
param(
    [Parameter(Mandatory = $true)]
    [string]$BackendExe,
    [Parameter(Mandatory = $true)]
    [string]$ApiKey,
    [ValidateSet("gemini", "openai")]
    [string]$Provider = "gemini"
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path $BackendExe)) {
    Write-Error "Backend exe not found: $BackendExe"
}
if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    Write-Host "No API key provided; skipping credential save."
    exit 0
}

$ext = [System.IO.Path]::GetExtension($BackendExe)
if ($ext -match '\.cmd|\.bat') {
    & cmd.exe /c "`"$BackendExe`" configure --provider $Provider --key $ApiKey"
} else {
    & $BackendExe configure --provider $Provider --key $ApiKey
}
exit $LASTEXITCODE
