using System;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace BimAgenticBridge.Commands
{
    [Transaction(TransactionMode.Manual)]
    public sealed class ShowChatCommand : IExternalCommand
    {
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            try
            {
                var paneId = new DockablePaneId(App.DockablePaneGuid);
                DockablePane pane = commandData.Application.GetDockablePane(paneId);
                if (pane == null)
                {
                    message = "BimAgenticBridge chat pane is not registered.";
                    return Result.Failed;
                }

                if (pane.IsShown())
                {
                    pane.Hide();
                }
                else
                {
                    pane.Show();
                }

                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                message = ex.Message;
                return Result.Failed;
            }
        }
    }
}
