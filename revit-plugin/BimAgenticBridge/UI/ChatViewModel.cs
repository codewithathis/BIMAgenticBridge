using System;
using System.Collections.ObjectModel;
using System.Collections.Specialized;
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
        /// <summary>
        /// Max wait for Revit to schedule/run the ExternalEvent export.
        /// </summary>
        public static readonly TimeSpan ExportTimeout = TimeSpan.FromSeconds(45);

        private readonly ChatApiClient _apiClient;
        private readonly ExportRequestHandler _exportHandler;
        private readonly ExternalEvent _exportEvent;
        private readonly object _exportLock = new object();

        private string _inputText = string.Empty;
        private bool _isBusy;
        private string _statusText = string.Empty;
        private TaskCompletionSource<bool> _exportTcs;

        public ChatViewModel(ChatApiClient apiClient, ExportRequestHandler exportHandler, ExternalEvent exportEvent)
        {
            _apiClient = apiClient ?? throw new ArgumentNullException(nameof(apiClient));
            _exportHandler = exportHandler ?? throw new ArgumentNullException(nameof(exportHandler));
            _exportEvent = exportEvent ?? throw new ArgumentNullException(nameof(exportEvent));

            Messages = new ObservableCollection<ChatMessage>();
            Messages.CollectionChanged += OnMessagesChanged;
            SendCommand = new RelayCommand(() => _ = SendAsync(), () => !IsBusy && !string.IsNullOrWhiteSpace(InputText));

            Messages.Add(new ChatMessage(
                ChatRole.Assistant,
                "Hi — I can answer questions about rooms, levels, doors, and windows in the active Revit model. Try: “How many rooms are on Level 1?”"));
        }

        public event PropertyChangedEventHandler PropertyChanged;
        public event Action MessagesChanged;

        public ObservableCollection<ChatMessage> Messages { get; }

        public string ProductName => AppInfo.PanelHeader;
        public string Subtitle => AppInfo.PanelSubtitle;
        public string Credit => AppInfo.PanelCredit;
        public string AuthorGitHubUrl => AppInfo.AuthorGitHubUrl;

        public string InputText
        {
            get => _inputText;
            set
            {
                if (_inputText == value)
                {
                    return;
                }

                _inputText = value ?? string.Empty;
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
                OnPropertyChanged(nameof(ShowEmptyState));
                ((RelayCommand)SendCommand).RaiseCanExecuteChanged();
            }
        }

        public string StatusText
        {
            get => _statusText;
            private set
            {
                if (_statusText == value)
                {
                    return;
                }

                _statusText = value ?? string.Empty;
                OnPropertyChanged();
                OnPropertyChanged(nameof(HasStatus));
            }
        }

        public bool HasStatus => !string.IsNullOrWhiteSpace(StatusText);

        public bool ShowEmptyState => Messages.Count == 0 && !IsBusy;

        public ICommand SendCommand { get; }

        public async Task SendAsync()
        {
            string message = (InputText ?? string.Empty).Trim();
            if (string.IsNullOrEmpty(message) || IsBusy)
            {
                return;
            }

            IsBusy = true;
            StatusText = "Sending…";
            InputText = string.Empty;
            Messages.Add(new ChatMessage(ChatRole.User, message));

            try
            {
                StatusText = "Starting local AI backend…";
                BackendEnsureResult ensure = await BackendProcessManager.Instance
                    .EnsureStartedAsync()
                    .ConfigureAwait(true);
                if (!ensure.Succeeded)
                {
                    Messages.Add(new ChatMessage(ChatRole.Error, ensure.Message));
                    return;
                }

                StatusText = "Waiting for AI agent…";
                ChatResponse response = await _apiClient.PostChatAsync(message).ConfigureAwait(true);

                if (string.Equals(response.Status, "extraction_required", StringComparison.OrdinalIgnoreCase))
                {
                    Messages.Add(new ChatMessage(ChatRole.System, "Refreshing room data from Revit…"));
                    StatusText = "Extracting rooms from Revit…";

                    ExportWaitResult exportResult = await RequestExportAsync(ExportTimeout).ConfigureAwait(true);
                    if (exportResult == ExportWaitResult.TimedOut)
                    {
                        Messages.Add(new ChatMessage(
                            ChatRole.Error,
                            $"Extraction timed out after {(int)ExportTimeout.TotalSeconds}s. "
                            + "Return to Revit (close dialogs) and try again."));
                        return;
                    }

                    if (exportResult == ExportWaitResult.Failed)
                    {
                        Messages.Add(new ChatMessage(
                            ChatRole.Error,
                            _exportHandler.LastError ?? "Extraction failed."));
                        return;
                    }

                    Messages.Add(new ChatMessage(
                        ChatRole.System,
                        "Model data updated."));

                    StatusText = "Analyzing exported data…";
                    response = await _apiClient.PostChatAsync(message, dataReady: true).ConfigureAwait(true);
                }

                if (string.Equals(response.Status, "ok", StringComparison.OrdinalIgnoreCase))
                {
                    Messages.Add(new ChatMessage(ChatRole.Assistant, response.Reply ?? "(empty reply)"));
                }
                else if (string.Equals(response.Status, "extraction_required", StringComparison.OrdinalIgnoreCase))
                {
                    Messages.Add(new ChatMessage(
                        ChatRole.Error,
                        response.Reason ?? "Backend still requires extraction. Check the data path and try again."));
                }
                else if (string.Equals(response.Status, "error", StringComparison.OrdinalIgnoreCase))
                {
                    Messages.Add(new ChatMessage(
                        ChatRole.Error,
                        response.Reason ?? response.Reply ?? "The chat service returned an error."));
                }
                else
                {
                    Messages.Add(new ChatMessage(
                        ChatRole.Error,
                        response.Reply ?? response.Reason ?? "Unexpected response."));
                }
            }
            catch (Exception ex)
            {
                Messages.Add(new ChatMessage(ChatRole.Error, ex.Message));
            }
            finally
            {
                StatusText = string.Empty;
                IsBusy = false;
            }
        }

        private void OnMessagesChanged(object sender, NotifyCollectionChangedEventArgs e)
        {
            OnPropertyChanged(nameof(ShowEmptyState));
            MessagesChanged?.Invoke();
        }

        private async Task<ExportWaitResult> RequestExportAsync(TimeSpan timeout)
        {
            TaskCompletionSource<bool> tcs;
            lock (_exportLock)
            {
                _exportTcs = new TaskCompletionSource<bool>();
                tcs = _exportTcs;
                _exportHandler.OnCompleted = () =>
                {
                    lock (_exportLock)
                    {
                        _exportTcs?.TrySetResult(_exportHandler.LastSucceeded);
                    }
                };
            }

            _exportEvent.Raise();

            Task completed = await Task.WhenAny(tcs.Task, Task.Delay(timeout)).ConfigureAwait(true);
            if (completed != tcs.Task)
            {
                lock (_exportLock)
                {
                    if (ReferenceEquals(_exportTcs, tcs))
                    {
                        _exportHandler.OnCompleted = null;
                        _exportTcs = null;
                    }
                }

                // Abandon waiting; late completion is ignored.
                tcs.TrySetCanceled();
                return ExportWaitResult.TimedOut;
            }

            bool succeeded = await tcs.Task.ConfigureAwait(true);
            return succeeded ? ExportWaitResult.Succeeded : ExportWaitResult.Failed;
        }

        private void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }

        private enum ExportWaitResult
        {
            Succeeded,
            Failed,
            TimedOut
        }
    }
}
