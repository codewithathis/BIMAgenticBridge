# Revit Plugin (BimAgenticBridge)

.NET Framework 4.8 WPF dockable chat add-in for Revit 2024.

## Prerequisites

- Visual Studio 2022 with .NET desktop development
- Autodesk Revit 2024 (for `RevitAPI.dll` / `RevitAPIUI.dll`)
- Newtonsoft.Json 13.0.3 NuGet package

## Restore Newtonsoft.Json

From the repo root (PowerShell):

```powershell
$pkgDir = "revit-plugin\BimAgenticBridge\packages\Newtonsoft.Json.13.0.3"
$zip = "$env:TEMP\newtonsoft.json.13.0.3.zip"
Invoke-WebRequest -Uri "https://www.nuget.org/api/v2/package/Newtonsoft.Json/13.0.3" -OutFile $zip
Expand-Archive -Path $zip -DestinationPath $pkgDir -Force
```

Or open the solution in Visual Studio and restore NuGet packages.

## Build

1. Open `BimAgenticBridge.sln` in Visual Studio
2. Confirm Revit 2024 reference paths in `BimAgenticBridge.csproj` match your install
3. Build **Debug** or **Release**

## Install the add-in

1. Copy `BimAgenticBridge.addin` to `%AppData%\Autodesk\Revit\Addins\2024\`
2. Edit the `<Assembly>` path in that file so it points at your built `BimAgenticBridge.dll`
3. Ensure `Newtonsoft.Json.dll` is next to the plugin DLL (Copy Local is enabled)
4. Restart Revit 2024

## Runtime data path

Room export writes to:

`%LOCALAPPDATA%\BimAgenticBridge\data.json`
