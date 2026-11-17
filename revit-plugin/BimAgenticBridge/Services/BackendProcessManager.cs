using System;
using System.Diagnostics;
using System.IO;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Newtonsoft.Json.Linq;

namespace BimAgenticBridge.Services
{
    /// <summary>
    /// Ensures the local FastAPI backend is reachable without blocking Revit startup.
    /// v1 policy: never stop the backend when Revit closes (multi-session safe).
    /// </summary>
    public sealed class BackendProcessManager
    {
        public static readonly BackendProcessManager Instance = new BackendProcessManager();

        public static readonly TimeSpan DefaultReadyTimeout = TimeSpan.FromSeconds(45);

        private readonly object _gate = new object();
        private Task<BackendEnsureResult> _ensureTask;
        private int _startedPid;

        private BackendProcessManager()
        {
        }

        public Task<BackendEnsureResult> EnsureStartedAsync(CancellationToken cancellationToken = default)
        {
            lock (_gate)
            {
                if (_ensureTask == null || _ensureTask.IsFaulted || _ensureTask.IsCanceled)
                {
                    _ensureTask = EnsureCoreAsync(cancellationToken);
                }

                return _ensureTask;
            }
        }

        /// <summary>
        /// Kick off ensure without awaiting (safe for OnStartup).
        /// </summary>
        public void BeginEnsure()
        {
            _ = EnsureStartedAsync();
        }

        private async Task<BackendEnsureResult> EnsureCoreAsync(CancellationToken cancellationToken)
        {
            RuntimeConfigData config = RuntimeConfig.Load();
            string baseUrl = (config.ApiBaseUrl ?? PathConfig.DefaultApiBaseUrl).TrimEnd('/');

            BackendHealth health = await ProbeHealthAsync(baseUrl, cancellationToken).ConfigureAwait(false);
            if (health.State == BackendHealthState.Ours)
            {
                return BackendEnsureResult.Ok("Local AI backend is ready.");
            }

            if (health.State == BackendHealthState.Foreign)
            {
                return BackendEnsureResult.Fail(
                    "Port " + config.ApiPort + " is in use by another application. "
                    + "Stop that process or change api_port in %LOCALAPPDATA%\\BimAgenticBridge\\config.json.");
            }

            string exe = RuntimeConfig.ResolveBackendExePath(config);
            if (string.IsNullOrEmpty(exe))
            {
                // Dev mode: expect user to run uvicorn manually.
                health = await WaitForOursAsync(baseUrl, TimeSpan.FromSeconds(3), cancellationToken).ConfigureAwait(false);
                if (health.State == BackendHealthState.Ours)
                {
                    return BackendEnsureResult.Ok("Local AI backend is ready.");
                }

                return BackendEnsureResult.Fail(
                    "Local AI backend is not running and no installed Backend.exe was found. "
                    + "Start the backend (Start Menu or uvicorn), or install BIM Agentic Bridge.");
            }

            try
            {
                ClearStalePid();
                ProcessStartInfo startInfo = CreateBackendStartInfo(exe);

                Process process = Process.Start(startInfo);
                if (process == null)
                {
                    return BackendEnsureResult.Fail("Failed to start BimAgenticBridge.Backend.exe.");
                }

                _startedPid = process.Id;
                WritePid(process.Id);
            }
            catch (Exception ex)
            {
                return BackendEnsureResult.Fail("Could not start local AI backend: " + ex.Message);
            }

            health = await WaitForOursAsync(baseUrl, DefaultReadyTimeout, cancellationToken).ConfigureAwait(false);
            if (health.State == BackendHealthState.Ours)
            {
                return BackendEnsureResult.Ok("Local AI backend started.");
            }

            if (health.State == BackendHealthState.Foreign)
            {
                return BackendEnsureResult.Fail(
                    "Started backend but port is serving a different application. Check config.json port settings.");
            }

            return BackendEnsureResult.Fail(
                "Timed out waiting for the local AI backend. See %LOCALAPPDATA%\\BimAgenticBridge\\logs\\backend.log.");
        }

        private static async Task<BackendHealth> WaitForOursAsync(
            string baseUrl,
            TimeSpan timeout,
            CancellationToken cancellationToken)
        {
            var sw = Stopwatch.StartNew();
            BackendHealth last = new BackendHealth { State = BackendHealthState.Down };
            while (sw.Elapsed < timeout)
            {
                cancellationToken.ThrowIfCancellationRequested();
                last = await ProbeHealthAsync(baseUrl, cancellationToken).ConfigureAwait(false);
                if (last.State == BackendHealthState.Ours || last.State == BackendHealthState.Foreign)
                {
                    return last;
                }

                await Task.Delay(500, cancellationToken).ConfigureAwait(false);
            }

            return last;
        }

        private static async Task<BackendHealth> ProbeHealthAsync(string baseUrl, CancellationToken cancellationToken)
        {
            try
            {
                using (var client = new HttpClient { Timeout = TimeSpan.FromSeconds(2) })
                {
                    HttpResponseMessage response = await client
                        .GetAsync(baseUrl.TrimEnd('/') + "/health", cancellationToken)
                        .ConfigureAwait(false);
                    string body = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
                    if (!response.IsSuccessStatusCode)
                    {
                        return new BackendHealth { State = BackendHealthState.Foreign };
                    }

                    try
                    {
                        JObject json = JObject.Parse(body);
                        string product = (string)json["product"];
                        if (string.Equals(product, "BIM Agentic Bridge", StringComparison.OrdinalIgnoreCase)
                            || string.Equals((string)json["product_slug"], "bim-agentic-bridge", StringComparison.OrdinalIgnoreCase))
                        {
                            return new BackendHealth { State = BackendHealthState.Ours, Version = (string)json["version"] };
                        }
                    }
                    catch
                    {
                        // Non-JSON or unexpected payload on the port.
                    }

                    return new BackendHealth { State = BackendHealthState.Foreign };
                }
            }
            catch
            {
                return new BackendHealth { State = BackendHealthState.Down };
            }
        }

        private static ProcessStartInfo CreateBackendStartInfo(string launcherPath)
        {
            string workDir = Path.GetDirectoryName(launcherPath) ?? string.Empty;
            string ext = Path.GetExtension(launcherPath) ?? string.Empty;
            if (ext.Equals(".cmd", StringComparison.OrdinalIgnoreCase)
                || ext.Equals(".bat", StringComparison.OrdinalIgnoreCase))
            {
                return new ProcessStartInfo
                {
                    FileName = "cmd.exe",
                    Arguments = "/c \"" + launcherPath + "\" serve",
                    WorkingDirectory = workDir,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    WindowStyle = ProcessWindowStyle.Hidden
                };
            }

            return new ProcessStartInfo
            {
                FileName = launcherPath,
                Arguments = "serve",
                WorkingDirectory = workDir,
                UseShellExecute = false,
                CreateNoWindow = true,
                WindowStyle = ProcessWindowStyle.Hidden
            };
        }

        private static void WritePid(int pid)
        {
            try
            {
                PathConfig.EnsureDataDirectory();
                string path = Path.Combine(PathConfig.DataDirectory, "backend.pid");
                File.WriteAllText(path, "{\"pid\":" + pid + ",\"started_at\":" + DateTimeOffset.UtcNow.ToUnixTimeSeconds() + "}\n");
            }
            catch
            {
                // Non-fatal.
            }
        }

        private static void ClearStalePid()
        {
            try
            {
                string path = Path.Combine(PathConfig.DataDirectory, "backend.pid");
                if (!File.Exists(path))
                {
                    return;
                }

                string json = File.ReadAllText(path);
                JObject obj = JObject.Parse(json);
                int pid = (int)obj["pid"];
                try
                {
                    Process.GetProcessById(pid);
                    // Still running — leave it; Ensure will reuse via health check.
                }
                catch (ArgumentException)
                {
                    File.Delete(path);
                }
            }
            catch
            {
                // Ignore.
            }
        }
    }

    public enum BackendHealthState
    {
        Down,
        Ours,
        Foreign
    }

    public sealed class BackendHealth
    {
        public BackendHealthState State { get; set; }
        public string Version { get; set; }
    }

    public sealed class BackendEnsureResult
    {
        public bool Succeeded { get; private set; }
        public string Message { get; private set; }

        public static BackendEnsureResult Ok(string message)
        {
            return new BackendEnsureResult { Succeeded = true, Message = message };
        }

        public static BackendEnsureResult Fail(string message)
        {
            return new BackendEnsureResult { Succeeded = false, Message = message };
        }
    }
}
