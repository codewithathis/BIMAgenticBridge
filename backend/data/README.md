Revit export snapshot used when the API is hosted (Vercel).

On a Windows machine with the plugin, live data still comes from
`%LOCALAPPDATA%\BimAgenticBridge\data.json`. Redeploy after copying a newer export here:

```powershell
Copy-Item "$env:LOCALAPPDATA\BimAgenticBridge\data.json" .\backend\data\data.json
```
