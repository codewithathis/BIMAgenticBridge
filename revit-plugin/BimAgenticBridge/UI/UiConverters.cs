using System;
using System.Globalization;
using System.Windows;
using System.Windows.Data;

namespace BimAgenticBridge.UI
{
    public sealed class InverseBooleanConverter : IValueConverter
    {
        public static readonly InverseBooleanConverter Instance = new InverseBooleanConverter();

        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            return value is bool flag && !flag;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            return value is bool flag && !flag;
        }
    }

    public sealed class BooleanToVisibilityConverter : IValueConverter
    {
        public static readonly BooleanToVisibilityConverter Instance = new BooleanToVisibilityConverter();
        public static readonly BooleanToVisibilityConverter InverseInstance = new BooleanToVisibilityConverter
        {
            Invert = true
        };

        public bool Invert { get; set; }

        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            bool visible = value is bool flag && flag;
            if (Invert)
            {
                visible = !visible;
            }

            return visible ? Visibility.Visible : Visibility.Collapsed;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotSupportedException();
        }
    }

    public sealed class NullOrEmptyToVisibilityConverter : IValueConverter
    {
        public static readonly NullOrEmptyToVisibilityConverter Instance = new NullOrEmptyToVisibilityConverter();

        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            bool hasText = value is string text && !string.IsNullOrWhiteSpace(text);
            return hasText ? Visibility.Collapsed : Visibility.Visible;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotSupportedException();
        }
    }
}
