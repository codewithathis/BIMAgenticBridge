using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using System.Windows.Input;
using Autodesk.Revit.UI;
using BimAgenticBridge.Extraction;
using BimAgenticBridge.Services;

namespace BimAgenticBridge.UI
{
    public sealed class RelayCommand : ICommand
    {
        private readonly Action _execute;
        private readonly Func<bool> _canExecute;

        public RelayCommand(Action execute, Func<bool> canExecute = null)
        {
            _execute = execute ?? throw new ArgumentNullException(nameof(execute));
            _canExecute = canExecute;
        }

        public event EventHandler CanExecuteChanged;

        public bool CanExecute(object parameter)
        {
            return _canExecute == null || _canExecute();
        }

        public void Execute(object parameter)
        {
            _execute();
        }

        public void RaiseCanExecuteChanged()
        {
            CanExecuteChanged?.Invoke(this, EventArgs.Empty);
        }
    }

    public sealed class ChatViewModel : INotifyPropertyChanged
    {
        private readonly ChatApiClient _apiClient;
        private readonly ExportRequestHandler _exportHandler;
        private readonly ExternalEvent _exportEvent;
        private readonly object _exportLock = new object();

        private string _inputText;
        private bool _isBusy;
        private TaskCompletionSource<bool> _exportTcs;

        public ChatViewModel(ChatApiClient apiClient, ExportRequestHandler exportHandler, ExternalEvent exportEvent)
        {
            _apiClient = apiClient ?? throw new ArgumentNullException(nameof(apiClient));
            _exportHandler = exportHandler ?? throw new ArgumentNullException(nameof(exportHandler));
            _exportEvent = exportEvent ?? throw new ArgumentNullException(nameof(exportEvent));

            Messages = new ObservableCollection<ChatMessage>();
            SendCommand = new RelayCommand(() => _ = SendAsync(), () => !IsBusy && !string.IsNullOrWhiteSpace(InputText));
        }

        public event PropertyChangedEventHandler PropertyChanged;

        public ObservableCollection<ChatMessage> Messages { get; }

        public string InputText
        {
            get => _inputText;
            set
            {
                if (_inputText == value)
                {
                    return;
                }

                _inputText = value;
                OnPropertyChanged();
                ((RelayCommand)SendCommand).RaiseCanExecuteChanged();
            }
        }

        public bool IsBusy
        {
            get => _isBusy;
            private set
            {
                if (_isBusy == value)
                {
                    return;
                }

                _isBusy = value;
                OnPropertyChanged();
                ((RelayCommand)SendCommand).RaiseCanExecuteChanged();
            }
        }

        public ICommand SendCommand { get; }

        public async Task SendAsync()
        {
            string message = (InputText ?? string.Empty).Trim();
            if (string.IsNullOrEmpty(message) || IsBusy)
            {
                return;
            }

            IsBusy = true;
            InputText = string.Empty;
            Messages.Add(new ChatMessage("You", message));

            try
            {
                ChatResponse response = await _apiClient.PostChatAsync(message).ConfigureAwait(true);

                if (string.Equals(response.Status, "extraction_required", StringComparison.OrdinalIgnoreCase))
                {
                    Messages.Add(new ChatMessage("System", "Refreshing room data from Revit..."));
                    bool exported = await RequestExportAsync().ConfigureAwait(true);
                    if (!exported)
                    {
                        Messages.Add(new ChatMessage("System", _exportHandler.LastError ?? "Extraction failed."));
                        return;
                    }

                    Messages.Add(new ChatMessage(
                        "System",
                        "Exported to " + (_exportHandler.LastExportPath ?? PathConfig.DataJsonPath)));

                    response = await _apiClient.PostChatAsync(message, dataReady: true).ConfigureAwait(true);
                }

                if (string.Equals(response.Status, "ok", StringComparison.OrdinalIgnoreCase))
                {
                    Messages.Add(new ChatMessage("Assistant", response.Reply ?? "(empty reply)"));
                }
                else if (string.Equals(response.Status, "extraction_required", StringComparison.OrdinalIgnoreCase))
                {
                    Messages.Add(new ChatMessage(
                        "System",
                        response.Reason ?? "Backend still requires extraction. Check the data path and try again."));
                }
                else
                {
                    Messages.Add(new ChatMessage("System", response.Reply ?? response.Reason ?? "Unexpected response."));
                }
            }
            catch (Exception ex)
            {
                Messages.Add(new ChatMessage("System", $"Error: {ex.Message}"));
            }
            finally
            {
                IsBusy = false;
            }
        }

        private Task<bool> RequestExportAsync()
        {
            lock (_exportLock)
            {
                _exportTcs = new TaskCompletionSource<bool>();
                _exportHandler.OnCompleted = () =>
                {
                    lock (_exportLock)
                    {
                        _exportTcs?.TrySetResult(_exportHandler.LastSucceeded);
                    }
                };
            }

            _exportEvent.Raise();
            return _exportTcs.Task;
        }

        private void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
}
