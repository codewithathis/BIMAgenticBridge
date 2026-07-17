using System;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace BimAgenticBridge.Extraction
{
    /// <summary>
    /// Runs room extraction on the Revit API thread via ExternalEvent.
    /// </summary>
    public sealed class ExportRequestHandler : IExternalEventHandler
    {
        private readonly RoomExtractor _extractor = new RoomExtractor();
        private readonly JsonExportService _jsonExport = new JsonExportService();

        public string LastExportPath { get; private set; }
        public string LastError { get; private set; }
        public bool LastSucceeded { get; private set; }
        public Action OnCompleted { get; set; }

        public void Execute(UIApplication app)
        {
            LastSucceeded = false;
            LastError = null;
            LastExportPath = null;

            try
            {
                UIDocument uiDoc = app?.ActiveUIDocument;
                Document doc = uiDoc?.Document;
                if (doc == null)
                {
                    LastError = "No active Revit document.";
                    return;
                }

                var rooms = _extractor.Extract(doc);
                LastExportPath = _jsonExport.Export(doc, rooms);
                LastSucceeded = true;
            }
            catch (Exception ex)
            {
                LastError = ex.Message;
            }
            finally
            {
                OnCompleted?.Invoke();
            }
        }

        public string GetName()
        {
            return "BimAgenticBridge.ExportRequestHandler";
        }
    }
}
