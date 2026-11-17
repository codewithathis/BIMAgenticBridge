using System;
using System.IO;

namespace BimAgenticBridge.Services
{
    /// <summary>
    /// Shared paths used by the plugin and documented for the FastAPI backend.
    /// Default: %LOCALAPPDATA%\BimAgenticBridge\data.json
    /// </summary>
    public static class PathConfig
    {
        public const string AppFolderName = "BimAgenticBridge";
        public const string DataFileName = "data.json";
        /// <summary>
        /// Fallback when config.json is missing. Prefer RuntimeConfig.Load().ApiBaseUrl.
        /// </summary>
        public const string DefaultApiBaseUrl = "http://127.0.0.1:8000";

        public static string DataDirectory =>
            Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                AppFolderName);

        public static string DataJsonPath => Path.Combine(DataDirectory, DataFileName);

        public static void EnsureDataDirectory()
        {
            Directory.CreateDirectory(DataDirectory);
        }
    }
}
