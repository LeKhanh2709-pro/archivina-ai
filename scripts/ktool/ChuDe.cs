// ChuDe.cs — phần dùng chung của hộp thoại WPF VK / MDVK: màu sáng / tối, nạp XAML nhúng, đọc / viết số,
// các phần chung của cửa sổ (kéo, đóng, công tắc chế độ). File này không tham chiếu AutoCAD (thử được ngoài AutoCAD).

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Markup;
using System.Windows.Media;
using System.Windows.Shapes;

namespace KTool
{
    static class ChuDe
    {
        // Khoá màu dùng trong XAML: Nen, Pan, Pan2, Ln, Chu, Chu2, Chu3, Tieude, Chan, Fld, Rl, Ck, So, Di, Ok, Ac
        // + các màu chỉ dùng trong code: Kinh (ô kính), Do_ (đố), nhãn loại ô.
        static readonly Dictionary<string, string> Toi = new()
        {
            ["Nen"] = "#23272E", ["Pan"] = "#2C313A", ["Pan2"] = "#353B46", ["Ln"] = "#444C5A", ["Chu"] = "#ECEFF4",
            ["Chu2"] = "#A7AFBD", ["Chu3"] = "#6F7888", ["Tieude"] = "#1B1F25", ["Chan"] = "#1F2329", ["Fld"] = "#1B1F25",
            ["Rl"] = "#3A414D", ["Ck"] = "#6B7485", ["So"] = "#4B9BFF", ["Di"] = "#F0564F", ["Ok"] = "#4FC38A",
            ["Ac"] = "#3B82F6", ["Kinh"] = "#8FB8D8", ["Do_"] = "#ECEFF4",
            ["NhanS"] = "#1F3A5F", ["ChuS"] = "#9CC7FF", ["NhanD"] = "#5A2523", ["ChuD"] = "#FFB3AF",
            ["NhanK"] = "#3A414D", ["ChuK"] = "#C5CCD8",
        };

        static readonly Dictionary<string, string> Sang = new()
        {
            ["Nen"] = "#F5F6F8", ["Pan"] = "#FFFFFF", ["Pan2"] = "#EEF1F5", ["Ln"] = "#D3D8E0", ["Chu"] = "#1C2128",
            ["Chu2"] = "#5B6573", ["Chu3"] = "#8A93A1", ["Tieude"] = "#E9ECF1", ["Chan"] = "#EEF0F4", ["Fld"] = "#FFFFFF",
            ["Rl"] = "#E4E7EC", ["Ck"] = "#9AA3B0", ["So"] = "#1F6FE0", ["Di"] = "#D8342C", ["Ok"] = "#1D8A5A",
            ["Ac"] = "#3B82F6", ["Kinh"] = "#5B93B8", ["Do_"] = "#2B3138",
            ["NhanS"] = "#DCEBFF", ["ChuS"] = "#12509F", ["NhanD"] = "#FDE3E1", ["ChuD"] = "#A3221C",
            ["NhanK"] = "#E9ECF1", ["ChuK"] = "#4A5360",
        };

        internal static SolidColorBrush Co(string hex)
        {
            var b = new SolidColorBrush((Color)ColorConverter.ConvertFromString(hex));
            b.Freeze();
            return b;
        }

        // Đặt màu của chế độ vào Resources của cửa sổ: DynamicResource trong XAML đổi theo ngay
        internal static void Dat(Window w, bool toi)
        {
            foreach (var kv in toi ? Toi : Sang) w.Resources[kv.Key] = Co(kv.Value);
        }

        internal static Brush Mau(Window w, string khoa) => (Brush)w.Resources[khoa];

        // XAML nhúng trong DLL (KTool.csproj: LogicalName = tên file)
        static object NapXaml(string ten)
        {
            using Stream s = Assembly.GetExecutingAssembly().GetManifestResourceStream(ten)
                             ?? throw new FileNotFoundException("DLL không có XAML nhúng: " + ten);
            return XamlReader.Load(s);
        }

        // Tạo cửa sổ từ XAML, nối kiểu dùng chung và các nút chung (đóng, sáng / tối). Chế độ đổi thì gọi veLai().
        internal static Window TaoCuaSo(string ten, bool toi, Action<bool> doiCheDo)
        {
            var w = (Window)NapXaml(ten);
            w.Resources.MergedDictionaries.Add((ResourceDictionary)NapXaml("ChuDe.xaml"));
            Dat(w, toi);
            if (SystemParameters.WorkArea.Height < w.Height) w.Height = SystemParameters.WorkArea.Height;

            var sang = (ToggleButton)w.FindName("tgSang");
            var dem = (ToggleButton)w.FindName("tgToi");
            var icSang = (System.Windows.Shapes.Path)w.FindName("icSang");
            var icToi = (System.Windows.Shapes.Path)w.FindName("icToi");
            bool hienTai = toi;
            void Chon(bool laToi)
            {
                hienTai = laToi;
                sang.IsChecked = !laToi;
                dem.IsChecked = laToi;
                // biểu tượng nút đang chọn luôn trắng trên nền xanh
                icSang.Stroke = laToi ? Mau(w, "Chu2") : Brushes.White;
                icToi.Stroke = laToi ? Brushes.White : Mau(w, "Chu2");
            }
            Chon(toi);
            sang.Click += (s, e) => { Dat(w, false); Chon(false); doiCheDo(false); };
            dem.Click += (s, e) => { Dat(w, true); Chon(true); doiCheDo(true); };
            w.Loaded += (s, e) => Chon(hienTai);
            return w;
        }

        // Số -> chuỗi gọn, dấu phẩy thập phân, tối đa 2 chữ số lẻ (như vk:so trong LISP)
        internal static string So(double x) =>
            Math.Round(x, 2, MidpointRounding.AwayFromZero).ToString("0.##", CultureInfo.InvariantCulture).Replace('.', ',');

        // Chuỗi -> số (nhận cả dấu phẩy); rỗng / sai -> null (như vk:doc-so)
        internal static double? DocSo(string s)
        {
            if (string.IsNullOrWhiteSpace(s)) return null;
            s = s.Trim();
            int i = s.IndexOf(',');
            if (i >= 0) s = s.Remove(i, 1).Insert(i, ".");
            return double.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out double v) ? v : null;
        }

        // Thêm vào Canvas
        internal static void Them(Canvas c, UIElement e, double x, double y)
        {
            Canvas.SetLeft(e, x);
            Canvas.SetTop(e, y);
            c.Children.Add(e);
        }

        internal static TextBlock Chu(string s, Brush mau, double co = 11) =>
            new TextBlock { Text = s, Foreground = mau, FontSize = co, IsHitTestVisible = false };

        // Viết chữ căn giữa tại (x, y)
        internal static void ChuGiua(Canvas c, TextBlock t, double x, double y, double goc = 0)
        {
            t.Measure(new Size(double.PositiveInfinity, double.PositiveInfinity));
            Size z = t.DesiredSize;
            if (goc != 0)
            {
                t.RenderTransformOrigin = new Point(0.5, 0.5);
                t.RenderTransform = new RotateTransform(goc);
            }
            Them(c, t, x - z.Width / 2, y - z.Height / 2);
        }
    }
}
