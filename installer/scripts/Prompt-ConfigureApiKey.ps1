param(
    [Parameter(Mandatory = $true)]
    [string]$BackendExe
)

$ErrorActionPreference = "Stop"
Write-Host "BIM Agentic Bridge — Configure API Key"
Write-Host ""
$provider = Read-Host "Provider [gemini/openai] (default gemini)"
if ([string]::IsNullOrWhiteSpace($provider)) { $provider = "gemini" }
$provider = $provider.Trim().ToLowerInvariant()
if ($provider -ne "gemini" -and $provider -ne "openai") {
    Write-Error "Provider must be gemini or openai."
}
$key = Read-Host "Paste API key"
if ([string]::IsNullOrWhiteSpace($key)) {
    Write-Host "Cancelled — no key saved."
    exit 0
}

& $PSScriptRoot\Save-ApiKey.ps1 -BackendExe $BackendExe -Provider $provider -ApiKey $key
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Done. Restart the backend if it is already running."
}
exit $LASTEXITCODE
