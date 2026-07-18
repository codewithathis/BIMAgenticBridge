using System.Windows.Controls;
using System.Windows.Input;
using Autodesk.Revit.UI;
using BimAgenticBridge.Extraction;
using BimAgenticBridge.Services;

namespace BimAgenticBridge.UI
{
    public partial class ChatPanel : Page, IDockablePaneProvider
    {
        private ChatViewModel _viewModel;

        public ChatPanel()
        {
            InitializeComponent();
        }

        public void Initialize(ChatApiClient apiClient, ExportRequestHandler exportHandler, ExternalEvent exportEvent)
        {
            if (_viewModel != null)
            {
                _viewModel.MessagesChanged -= OnMessagesChanged;
            }

            _viewModel = new ChatViewModel(apiClient, exportHandler, exportEvent);
            _viewModel.MessagesChanged += OnMessagesChanged;
            DataContext = _viewModel;
            ScrollToEnd();
        }

        public void SetupDockablePane(DockablePaneProviderData data)
        {
            data.FrameworkElement = this;
            data.InitialState = new DockablePaneState
            {
                DockPosition = DockPosition.Right
            };
        }

        private void InputBox_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Enter && _viewModel != null && _viewModel.SendCommand.CanExecute(null))
            {
                _viewModel.SendCommand.Execute(null);
                e.Handled = true;
            }
        }

        private void OnMessagesChanged()
        {
            Dispatcher.InvokeAsync(ScrollToEnd);
        }

        private void ScrollToEnd()
        {
            if (MessageScroller == null)
            {
                return;
            }

            MessageScroller.UpdateLayout();
            MessageScroller.ScrollToEnd();
        }
    }
}
