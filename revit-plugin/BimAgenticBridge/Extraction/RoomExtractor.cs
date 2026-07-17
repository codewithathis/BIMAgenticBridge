using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;

namespace BimAgenticBridge.Extraction
{
    /// <summary>
    /// Extracts rooms, levels, and door/window counts from the host document and loaded links.
    /// </summary>
    public sealed class RoomExtractor
    {
        public ModelSnapshot Extract(Document doc)
        {
            if (doc == null)
            {
                throw new ArgumentNullException(nameof(doc));
            }

            var snapshot = new ModelSnapshot();
            string hostTitle = string.IsNullOrWhiteSpace(doc.Title) ? "Host" : doc.Title;
            snapshot.SourceDocuments.Add(hostTitle);

            CollectLevels(doc, hostTitle, snapshot.Levels);
            CollectRooms(doc, hostTitle, snapshot.Rooms);

            var links = new FilteredElementCollector(doc)
                .OfClass(typeof(RevitLinkInstance))
                .Cast<RevitLinkInstance>()
                .ToList();

            foreach (RevitLinkInstance linkInstance in links)
            {
                Document linkDoc = linkInstance.GetLinkDocument();
                if (linkDoc == null)
                {
                    continue;
                }

                string linkTitle = string.IsNullOrWhiteSpace(linkDoc.Title)
                    ? linkInstance.Name
                    : linkDoc.Title;

                if (!snapshot.SourceDocuments.Contains(linkTitle))
                {
                    snapshot.SourceDocuments.Add(linkTitle);
                }

                CollectLevels(linkDoc, linkTitle, snapshot.Levels);
                CollectRooms(linkDoc, linkTitle, snapshot.Rooms);
            }

            return snapshot;
        }

        private static void CollectLevels(Document doc, string sourceDocument, ICollection<LevelData> levels)
        {
            foreach (Level level in new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>())
            {
                levels.Add(new LevelData
                {
                    Name = level.Name ?? string.Empty,
                    Elevation = UnitUtils.ConvertFromInternalUnits(level.Elevation, UnitTypeId.Meters),
                    SourceDocument = sourceDocument
                });
            }
        }

        private static void CollectRooms(Document doc, string sourceDocument, ICollection<RoomData> rooms)
        {
            var roomsById = new Dictionary<ElementId, RoomData>();
            var roomElements = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Rooms)
                .WhereElementIsNotElementType()
                .ToElements();

            foreach (Element element in roomElements)
            {
                var room = element as Room;
                if (room == null || room.Area <= 0)
                {
                    continue;
                }

                string levelName = room.Level != null ? room.Level.Name : string.Empty;

                roomsById[room.Id] = new RoomData
                {
                    Name = room.get_Parameter(BuiltInParameter.ROOM_NAME)?.AsString() ?? room.Name ?? string.Empty,
                    Number = room.Number ?? string.Empty,
                    Level = levelName,
                    Area = Math.Round(UnitUtils.ConvertFromInternalUnits(room.Area, UnitTypeId.SquareMeters), 2),
                    DoorCount = 0,
                    WindowCount = 0,
                    SourceDocument = sourceDocument
                };
            }

            Phase phase = ResolvePhase(doc);
            CountHostedOpenings(doc, BuiltInCategory.OST_Doors, roomsById, phase, isDoor: true);
            CountHostedOpenings(doc, BuiltInCategory.OST_Windows, roomsById, phase, isDoor: false);

            foreach (RoomData room in roomsById.Values)
            {
                rooms.Add(room);
            }
        }

        private static Phase ResolvePhase(Document doc)
        {
            View activeView = doc.ActiveView;
            Parameter viewPhaseParam = activeView?.get_Parameter(BuiltInParameter.VIEW_PHASE);
            ElementId phaseId = viewPhaseParam?.AsElementId() ?? ElementId.InvalidElementId;
            if (phaseId != ElementId.InvalidElementId)
            {
                return doc.GetElement(phaseId) as Phase;
            }

            return new FilteredElementCollector(doc)
                .OfClass(typeof(Phase))
                .Cast<Phase>()
                .LastOrDefault();
        }

        private static void CountHostedOpenings(
            Document doc,
            BuiltInCategory category,
            IDictionary<ElementId, RoomData> roomsById,
            Phase phase,
            bool isDoor)
        {
            var openings = new FilteredElementCollector(doc)
                .OfCategory(category)
                .WhereElementIsNotElementType()
                .ToElements();

            foreach (Element element in openings)
            {
                var familyInstance = element as FamilyInstance;
                if (familyInstance == null)
                {
                    continue;
                }

                var countedRooms = new HashSet<ElementId>();
                Room fromRoom = phase != null ? familyInstance.get_FromRoom(phase) : familyInstance.FromRoom;
                Room toRoom = phase != null ? familyInstance.get_ToRoom(phase) : familyInstance.ToRoom;

                TryCountRoom(fromRoom, roomsById, countedRooms, isDoor);
                TryCountRoom(toRoom, roomsById, countedRooms, isDoor);
            }
        }

        private static void TryCountRoom(
            Room room,
            IDictionary<ElementId, RoomData> roomsById,
            ISet<ElementId> countedRooms,
            bool isDoor)
        {
            if (room == null || !roomsById.ContainsKey(room.Id) || !countedRooms.Add(room.Id))
            {
                return;
            }

            if (isDoor)
            {
                roomsById[room.Id].DoorCount++;
            }
            else
            {
                roomsById[room.Id].WindowCount++;
            }
        }
    }
}
