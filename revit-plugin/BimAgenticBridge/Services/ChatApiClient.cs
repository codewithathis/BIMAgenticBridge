using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;

namespace BimAgenticBridge.Services
{
    public sealed class ChatRequest
    {
        [JsonProperty("message")]
        public string Message { get; set; }

        [JsonProperty("force_extract")]
        public bool ForceExtract { get; set; }

        [JsonProperty("data_ready")]
        public bool DataReady { get; set; }
    }

    public sealed class ChatResponse
    {
        [JsonProperty("status")]
        public string Status { get; set; }

        [JsonProperty("reply")]
        public string Reply { get; set; }

        [JsonProperty("reason")]
        public string Reason { get; set; }
    }

    public sealed class ChatApiClient : IDisposable
    {
        public const string AuthHeaderName = "X-BimAgentic-Token";

        private readonly HttpClient _httpClient;
        private readonly bool _ownsClient;

        public ChatApiClient(string baseUrl = null, string authToken = null, HttpClient httpClient = null)
        {
            if (httpClient != null)
            {
                _httpClient = httpClient;
                _ownsClient = false;
            }
            else
            {
                RuntimeConfigData config = RuntimeConfig.Load();
                string resolvedBase = baseUrl
                    ?? (string.IsNullOrWhiteSpace(config.ApiBaseUrl) ? PathConfig.DefaultApiBaseUrl : config.ApiBaseUrl);
                string token = authToken ?? config.AuthToken ?? string.Empty;

                _httpClient = new HttpClient
                {
                    BaseAddress = new Uri(resolvedBase.TrimEnd('/') + "/"),
                    Timeout = TimeSpan.FromMinutes(2)
                };
                if (!string.IsNullOrWhiteSpace(token))
                {
                    _httpClient.DefaultRequestHeaders.TryAddWithoutValidation(AuthHeaderName, token);
                }

                _ownsClient = true;
            }
        }

        public async Task<ChatResponse> PostChatAsync(string message, bool dataReady = false, bool forceExtract = false)
        {
            var payload = new ChatRequest
            {
                Message = message,
                DataReady = dataReady,
                ForceExtract = forceExtract
            };

            string json = JsonConvert.SerializeObject(payload);
            using (var content = new StringContent(json, Encoding.UTF8, "application/json"))
            using (HttpResponseMessage response = await _httpClient.PostAsync("chat", content).ConfigureAwait(false))
            {
                string body = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
                if (!response.IsSuccessStatusCode)
                {
                    if ((int)response.StatusCode == 401)
                    {
                        throw new HttpRequestException(
                            "Local backend rejected the auth token. Reinstall or repair config.json auth_token.");
                    }

                    if ((int)response.StatusCode == 503)
                    {
                        throw new HttpRequestException(
                            "AI backend is not configured or the API key was rejected. "
                            + "Use Start Menu → BIM Agentic Bridge → Configure API Key. Details: " + TrimBody(body));
                    }

                    throw new HttpRequestException(
                        $"Chat API returned {(int)response.StatusCode}: {TrimBody(body)}");
                }

                var result = JsonConvert.DeserializeObject<ChatResponse>(body);
                if (result == null)
                {
                    throw new InvalidOperationException("Chat API returned an empty response.");
                }

                return result;
            }
        }

        private static string TrimBody(string body)
        {
            if (string.IsNullOrWhiteSpace(body))
            {
                return string.Empty;
            }

            body = body.Trim();
            return body.Length <= 300 ? body : body.Substring(0, 300) + "…";
        }

        public void Dispose()
        {
            if (_ownsClient)
            {
                _httpClient.Dispose();
            }
        }
    }
}
