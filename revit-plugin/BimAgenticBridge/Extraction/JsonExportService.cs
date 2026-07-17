using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using Autodesk.Revit.DB;
using BimAgenticBridge.Services;
using Newtonsoft.Json;

namespace BimAgenticBridge.Extraction
{
    /// <summary>
    /// Serializes extracted room data to data.json using an atomic write.
    /// </summary>
    public sealed class JsonExportService
    {
        private static readonly JsonSerializerSettings SerializerSettings = new JsonSerializerSettings
        {
            Formatting = Formatting.Indented,
            NullValueHandling = NullValueHandling.Ignore
        };

        public string Export(Document doc, IList<RoomData> rooms, string outputPath = null)
        {
            if (doc == null)
            {
                throw new ArgumentNullException(nameof(doc));
            }

            if (rooms == null)
            {
                throw new ArgumentNullException(nameof(rooms));
            }

            string path = string.IsNullOrWhiteSpace(outputPath)
                ? PathConfig.DataJsonPath
                : outputPath;

            PathConfig.EnsureDataDirectory();

            var payload = new RoomExportDocument
            {
                ExportedAtUtc = DateTime.UtcNow,
                DocumentTitle = string.IsNullOrWhiteSpace(doc.Title) ? "Untitled" : doc.Title,
                Rooms = new List<RoomData>(rooms)
            };

            string json = JsonConvert.SerializeObject(payload, SerializerSettings);
            string directory = Path.GetDirectoryName(path);
            if (!string.IsNullOrEmpty(directory))
            {
                Directory.CreateDirectory(directory);
            }

            string tempPath = path + ".tmp";
            File.WriteAllText(tempPath, json, Encoding.UTF8);

            if (File.Exists(path))
            {
                File.Delete(path);
            }

            File.Move(tempPath, path);
            return path;
        }
    }
}
