using System;
using System.Reflection;
using Autodesk.Revit.UI;
using BimAgenticBridge.Extraction;
using BimAgenticBridge.Services;
using BimAgenticBridge.UI;

namespace BimAgenticBridge
{
    public sealed class App : IExternalApplication
    {
        public static readonly Guid DockablePaneGuid = new Guid("6F2C1A90-8B4E-4D3A-9C71-2E5F8A1B0D44");

        private ChatPanel _chatPanel;
        private ChatApiClient _apiClient;
        private ExportRequestHandler _exportHandler;
        private ExternalEvent _exportEvent;

        public Result OnStartup(UIControlledApplication application)
        {
            try
            {
                _apiClient = new ChatApiClient();
                _exportHandler = new ExportRequestHandler();
                _exportEvent = ExternalEvent.Create(_exportHandler);

                _chatPanel = new ChatPanel();
                _chatPanel.Initialize(_apiClient, _exportHandler, _exportEvent);

                application.RegisterDockablePane(
                    new DockablePaneId(DockablePaneGuid),
                    AppInfo.DockablePaneTitle,
                    _chatPanel);

                CreateRibbon(application);
                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                TaskDialog.Show(AppInfo.ProductName, "Startup failed: " + ex.Message);
                return Result.Failed;
            }
        }

        public Result OnShutdown(UIControlledApplication application)
        {
            _apiClient?.Dispose();
            return Result.Succeeded;
        }

        private static void CreateRibbon(UIControlledApplication application)
        {
            try
            {
                application.CreateRibbonTab(AppInfo.RibbonTabName);
            }
            catch (Autodesk.Revit.Exceptions.ArgumentException)
            {
                // Tab already exists.
            }

            RibbonPanel panel = application.CreateRibbonPanel(AppInfo.RibbonTabName, AppInfo.RibbonPanelName);
            string assemblyPath = Assembly.GetExecutingAssembly().Location;

            var buttonData = new PushButtonData(
                "ShowBimAgenticChat",
                AppInfo.RibbonButtonName,
                assemblyPath,
                "BimAgenticBridge.Commands.ShowChatCommand");

            PushButton button = panel.AddItem(buttonData) as PushButton;
            if (button != null)
            {
                button.ToolTip = AppInfo.RibbonButtonTooltip;
                button.LongDescription = AppInfo.RibbonButtonDescription;
            }
        }
    }
}
