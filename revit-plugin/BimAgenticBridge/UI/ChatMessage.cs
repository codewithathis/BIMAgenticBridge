namespace BimAgenticBridge.UI
{
    public sealed class ChatMessage
    {
        public ChatMessage(string role, string text)
        {
            Role = role;
            Text = text;
        }

        public string Role { get; }
        public string Text { get; }

        public string DisplayText => $"{Role}: {Text}";
    }
}
