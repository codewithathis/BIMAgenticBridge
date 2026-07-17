using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;

namespace BimAgenticBridge.Extraction
{
    /// <summary>
    /// Extracts room Name, Number, Level, Area and door/window counts via FilteredElementCollector.
    /// </summary>
    public sealed class RoomExtractor
    {
        public List<RoomData> Extract(Document doc)
        {
            if (doc == null)
            {
                throw new ArgumentNullException(nameof(doc));
            }

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

                string levelName = string.Empty;
                if (room.Level != null)
                {
                    levelName = room.Level.Name;
                }

                roomsById[room.Id] = new RoomData
                {
                    Name = room.get_Parameter(BuiltInParameter.ROOM_NAME)?.AsString() ?? room.Name ?? string.Empty,
                    Number = room.Number ?? string.Empty,
                    Level = levelName,
                    Area = UnitUtils.ConvertFromInternalUnits(room.Area, UnitTypeId.SquareMeters),
                    DoorCount = 0,
                    WindowCount = 0
                };
            }

            Phase phase = ResolvePhase(doc);
            CountHostedOpenings(doc, BuiltInCategory.OST_Doors, roomsById, phase, isDoor: true);
            CountHostedOpenings(doc, BuiltInCategory.OST_Windows, roomsById, phase, isDoor: false);

            return new List<RoomData>(roomsById.Values);
        }

        private static Phase ResolvePhase(Document doc)
        {
            View activeView = doc.ActiveView;
            Parameter viewPhaseParam = activeView?.get_Parameter(BuiltInParameter.VIEW_PHASE);
            ElementId phaseId = viewPhaseParam?.AsElementId();
            if (phaseId != null && phaseId != ElementId.InvalidElementId)
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
