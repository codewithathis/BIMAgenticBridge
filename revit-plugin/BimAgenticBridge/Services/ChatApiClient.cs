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
        private readonly HttpClient _httpClient;
        private readonly bool _ownsClient;

        public ChatApiClient(string baseUrl = null, HttpClient httpClient = null)
        {
            if (httpClient != null)
            {
                _httpClient = httpClient;
                _ownsClient = false;
            }
            else
            {
                _httpClient = new HttpClient
                {
                    BaseAddress = new Uri((baseUrl ?? PathConfig.DefaultApiBaseUrl).TrimEnd('/') + "/"),
                    Timeout = TimeSpan.FromMinutes(2)
                };
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
                    throw new HttpRequestException(
                        $"Chat API returned {(int)response.StatusCode}: {body}");
                }

                var result = JsonConvert.DeserializeObject<ChatResponse>(body);
                if (result == null)
                {
                    throw new InvalidOperationException("Chat API returned an empty response.");
                }

                return result;
            }
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
