using System;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace BimAgenticBridge.Extraction
{
    public sealed class RoomData
    {
        [JsonProperty("name")]
        public string Name { get; set; }

        [JsonProperty("number")]
        public string Number { get; set; }

        [JsonProperty("level")]
        public string Level { get; set; }

        [JsonProperty("area")]
        public double Area { get; set; }

        [JsonProperty("doorCount")]
        public int DoorCount { get; set; }

        [JsonProperty("windowCount")]
        public int WindowCount { get; set; }
    }

    public sealed class RoomExportDocument
    {
        [JsonProperty("exportedAtUtc")]
        public DateTime ExportedAtUtc { get; set; }

        [JsonProperty("documentTitle")]
        public string DocumentTitle { get; set; }

        [JsonProperty("rooms")]
        public List<RoomData> Rooms { get; set; } = new List<RoomData>();
    }
}
