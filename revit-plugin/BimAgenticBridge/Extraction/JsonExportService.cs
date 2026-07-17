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
    /// Serializes extracted model data to data.json using an atomic write.
    /// </summary>
    public sealed class JsonExportService
    {
        private static readonly JsonSerializerSettings SerializerSettings = new JsonSerializerSettings
        {
            Formatting = Formatting.Indented,
            NullValueHandling = NullValueHandling.Ignore
        };

        // Encoding.UTF8 writes a BOM by default; Python json rejects that unless utf-8-sig is used.
        private static readonly Encoding Utf8NoBom = new UTF8Encoding(encoderShouldEmitUTF8Identifier: false);

        public string Export(Document doc, ModelSnapshot snapshot, string outputPath = null)
        {
            if (doc == null)
            {
                throw new ArgumentNullException(nameof(doc));
            }

            if (snapshot == null)
            {
                throw new ArgumentNullException(nameof(snapshot));
            }

            string path = string.IsNullOrWhiteSpace(outputPath)
                ? PathConfig.DataJsonPath
                : outputPath;

            PathConfig.EnsureDataDirectory();

            var notes = new List<string>();
            if (snapshot.Rooms.Count == 0)
            {
                notes.Add(
                    "No rooms were found in the host model or loaded links. " +
                    "Rooms are usually in an Architectural model — open or link " +
                    "'Snowdon Towers Sample Architectural.rvt' and extract again.");
            }

            var payload = new RoomExportDocument
            {
                ExportedAtUtc = DateTime.UtcNow,
                DocumentTitle = string.IsNullOrWhiteSpace(doc.Title) ? "Untitled" : doc.Title,
                SourceDocuments = new List<string>(snapshot.SourceDocuments),
                Levels = new List<LevelData>(snapshot.Levels),
                RoomCount = snapshot.Rooms.Count,
                Rooms = new List<RoomData>(snapshot.Rooms),
                Notes = notes
            };

            string json = JsonConvert.SerializeObject(payload, SerializerSettings);
            string directory = Path.GetDirectoryName(path);
            if (!string.IsNullOrEmpty(directory))
            {
                Directory.CreateDirectory(directory);
            }

            string tempPath = path + ".tmp";
            File.WriteAllText(tempPath, json, Utf8NoBom);

            if (File.Exists(path))
            {
                File.Delete(path);
            }

            File.Move(tempPath, path);
            return path;
        }
    }
}
