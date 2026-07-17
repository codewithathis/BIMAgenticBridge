# Revit Plugin (BimAgenticBridge)

.NET 10 WPF dockable chat add-in for **Revit 2027**.

## Prerequisites

- Visual Studio 2022 (17.14+) **or** .NET SDK 10 (x64)
- Autodesk Revit 2027
- Default API path: `D:\Development\Autodesk\Revit 2027`

### If Visual Studio says `Microsoft.NET.Sdk` could not be found

Windows is resolving the **x86** `dotnet` host (`C:\Program Files (x86)\dotnet`), which has no SDKs. Use the **x64** host:

1. Close Visual Studio
2. Confirm: `"C:\Program Files\dotnet\dotnet.exe" --list-sdks` shows `10.0.x`
3. Set user env vars (then reopen VS / a new terminal):
   - `DOTNET_ROOT` = `C:\Program Files\dotnet`
   - `DOTNET_HOST_PATH` = `C:\Program Files\dotnet\dotnet.exe`
4. Ensure `C:\Program Files\dotnet` appears **before** `C:\Program Files (x86)\dotnet` in PATH

If Revit is installed elsewhere, build with:

```powershell
dotnet build -p:RevitInstallPath="C:\Path\To\Revit 2027"
```

## Build

```powershell
cd revit-plugin
& "C:\Program Files\dotnet\dotnet.exe" build BimAgenticBridge.sln -c Debug
```

Or open `BimAgenticBridge.sln` in Visual Studio and build (after the PATH/`DOTNET_ROOT` fix above).

## Install the add-in

1. Copy `BimAgenticBridge.addin` to `%AppData%\Autodesk\Revit\Addins\2027\`
2. Edit the `<Assembly>` path so it points at your built `BimAgenticBridge.dll`  
   (default Debug output: `revit-plugin\BimAgenticBridge\bin\Debug\BimAgenticBridge.dll`)
3. Ensure `Newtonsoft.Json.dll` is next to the plugin DLL (copied on build)
4. Restart Revit 2027

## Runtime data path

Room export writes to:

`%LOCALAPPDATA%\BimAgenticBridge\data.json`
