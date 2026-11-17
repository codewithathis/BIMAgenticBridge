param(
    [string]$RevitYear = "2027",
    [switch]$RemoveUserData
)

$ErrorActionPreference = "Stop"
$addinPath = Join-Path $env:APPDATA "Autodesk\Revit\Addins\$RevitYear\BimAgenticBridge.addin"
if (Test-Path $addinPath) {
    Remove-Item -Force $addinPath
    Write-Host "Removed $addinPath"
}

if ($RemoveUserData) {
    $root = Join-Path $env:LOCALAPPDATA "BimAgenticBridge"
    if (Test-Path $root) {
        Remove-Item -Recurse -Force $root
        Write-Host "Removed user data: $root"
    }
}
