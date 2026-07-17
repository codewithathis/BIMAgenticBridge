# Revit Plugin (BimAgenticBridge)

.NET 10 WPF dockable chat add-in for **Revit 2027**.

## Prerequisites

- Visual Studio 2022 (17.14+) or `dotnet` SDK 10
- Autodesk Revit 2027
- Default API path: `D:\Development\Autodesk\Revit 2027`

If Revit is installed elsewhere, build with:

```powershell
dotnet build -p:RevitInstallPath="C:\Path\To\Revit 2027"
```

## Build

```powershell
cd revit-plugin
& "C:\Program Files\dotnet\dotnet.exe" build BimAgenticBridge.sln -c Debug
```

Or open `BimAgenticBridge.sln` in Visual Studio and build.

## Install the add-in

1. Copy `BimAgenticBridge.addin` to `%AppData%\Autodesk\Revit\Addins\2027\`
2. Edit the `<Assembly>` path so it points at your built `BimAgenticBridge.dll`  
   (default Debug output: `revit-plugin\BimAgenticBridge\bin\Debug\BimAgenticBridge.dll`)
3. Ensure `Newtonsoft.Json.dll` is next to the plugin DLL (copied on build)
4. Restart Revit 2027

## Runtime data path

Room export writes to:

`%LOCALAPPDATA%\BimAgenticBridge\data.json`
