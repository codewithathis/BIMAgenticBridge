using System;

namespace BimAgenticBridge.UI
{
    public enum ChatRole
    {
        User,
        Assistant,
        System,
        Error
    }

    public sealed class ChatMessage
    {
        public ChatMessage(ChatRole role, string text)
        {
            Role = role;
            Text = text ?? string.Empty;
            Timestamp = DateTime.Now;
        }

        public ChatRole Role { get; }
        public string Text { get; }
        public DateTime Timestamp { get; }

        public string RoleLabel =>
            Role switch
            {
                ChatRole.User => "You",
                ChatRole.Assistant => "Assistant",
                ChatRole.System => "System",
                ChatRole.Error => "Error",
                _ => "Message"
            };

        public string TimeLabel => Timestamp.ToString("HH:mm");

        public bool IsUser => Role == ChatRole.User;
        public bool IsAssistant => Role == ChatRole.Assistant;
        public bool IsSystem => Role == ChatRole.System || Role == ChatRole.Error;
    }
}
