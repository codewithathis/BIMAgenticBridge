using System;
using System.IO;
using Newtonsoft.Json;

namespace BimAgenticBridge.Services
{
    /// <summary>
    /// Reads %LOCALAPPDATA%\BimAgenticBridge\config.json written by the installer / backend.
    /// </summary>
    public sealed class RuntimeConfigData
    {
        [JsonProperty("install_dir")]
        public string InstallDir { get; set; }

        [JsonProperty("api_base_url")]
        public string ApiBaseUrl { get; set; }

        [JsonProperty("api_host")]
        public string ApiHost { get; set; }

        [JsonProperty("api_port")]
        public int ApiPort { get; set; }

        [JsonProperty("auth_token")]
        public string AuthToken { get; set; }

        [JsonProperty("version")]
        public string Version { get; set; }

        [JsonProperty("backend_exe_path")]
        public string BackendExePath { get; set; }

        [JsonProperty("require_auth")]
        public bool RequireAuth { get; set; }
    }

    public static class RuntimeConfig
    {
        public static string ConfigJsonPath =>
            Path.Combine(PathConfig.DataDirectory, "config.json");

        public static RuntimeConfigData Load()
        {
            try
            {
                if (!File.Exists(ConfigJsonPath))
                {
                    return CreateDefaults();
                }

                string json = File.ReadAllText(ConfigJsonPath);
                var data = JsonConvert.DeserializeObject<RuntimeConfigData>(json);
                if (data == null)
                {
                    return CreateDefaults();
                }

                if (string.IsNullOrWhiteSpace(data.ApiBaseUrl))
                {
                    int port = data.ApiPort > 0 ? data.ApiPort : 8000;
                    string host = string.IsNullOrWhiteSpace(data.ApiHost) ? "127.0.0.1" : data.ApiHost.Trim();
                    data.ApiBaseUrl = "http://" + host + ":" + port;
                }

                if (data.ApiPort <= 0)
                {
                    data.ApiPort = 8000;
                }

                return data;
            }
            catch
            {
                return CreateDefaults();
            }
        }

        public static string ResolveBackendExePath(RuntimeConfigData config)
        {
            if (config == null)
            {
                config = Load();
            }

            if (!string.IsNullOrWhiteSpace(config.BackendExePath) && File.Exists(config.BackendExePath))
            {
                return config.BackendExePath;
            }

            if (!string.IsNullOrWhiteSpace(config.InstallDir))
            {
                string backendDir = Path.Combine(config.InstallDir, "Backend");
                foreach (string name in new[]
                {
                    "BimAgenticBridge.Backend.exe",
                    "BimAgenticBridge.Backend.cmd"
                })
                {
                    string candidate = Path.Combine(backendDir, name);
                    if (File.Exists(candidate))
                    {
                        return candidate;
                    }
                }
            }

            return null;
        }

        private static RuntimeConfigData CreateDefaults()
        {
            return new RuntimeConfigData
            {
                ApiBaseUrl = PathConfig.DefaultApiBaseUrl,
                ApiHost = "127.0.0.1",
                ApiPort = 8000,
                AuthToken = string.Empty,
                RequireAuth = false,
                Version = "1.0.0"
            };
        }
    }
}
