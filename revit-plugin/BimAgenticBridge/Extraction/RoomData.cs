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

        [JsonProperty("sourceDocument")]
        public string SourceDocument { get; set; }
    }

    public sealed class LevelData
    {
        [JsonProperty("name")]
        public string Name { get; set; }

        [JsonProperty("elevation")]
        public double Elevation { get; set; }

        [JsonProperty("sourceDocument")]
        public string SourceDocument { get; set; }
    }

    public sealed class ModelSnapshot
    {
        public List<RoomData> Rooms { get; set; } = new List<RoomData>();
        public List<LevelData> Levels { get; set; } = new List<LevelData>();
        public List<string> SourceDocuments { get; set; } = new List<string>();
    }

    public sealed class RoomExportDocument
    {
        [JsonProperty("exportedAtUtc")]
        public DateTime ExportedAtUtc { get; set; }

        [JsonProperty("documentTitle")]
        public string DocumentTitle { get; set; }

        [JsonProperty("sourceDocuments")]
        public List<string> SourceDocuments { get; set; } = new List<string>();

        [JsonProperty("levels")]
        public List<LevelData> Levels { get; set; } = new List<LevelData>();

        [JsonProperty("roomCount")]
        public int RoomCount { get; set; }

        [JsonProperty("rooms")]
        public List<RoomData> Rooms { get; set; } = new List<RoomData>();

        [JsonProperty("notes")]
        public List<string> Notes { get; set; } = new List<string>();
    }
}
