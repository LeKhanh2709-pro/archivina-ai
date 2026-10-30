// Biểu tượng nút K-TOOL: icon trắng nền trong suốt (người dùng chọn kiểu trắng đen 2026-10-30).
// Hình lấy từ bộ Material Design Icons (mdi, lưới 24 x 24, giấy phép Apache 2.0, nguồn api.iconify.design/mdi),
// nhúng dạng path trong code nên không cần file ảnh mang theo. Ký hiệu chưa có hình thì vẽ chữ.

using System.Collections.Generic;
using System.Globalization;
using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Imaging;

namespace KTool
{
    static class BieuTuong
    {
        // Ký hiệu nút -> path SVG (F1 = tô nonzero như SVG)
        static readonly Dictionary<string, string> Hinh = new Dictionary<string, string>
        {
            // VK: view-column-outline (vách chia đố)
            ["VK"] = "F1 M4 5v13h17V5zm10 2v9h-3V7zM6 7h3v9H6zm13 9h-3V7h3z",
            // MĐ: window-closed-variant (mặt đứng vách kính)
            ["MĐ"] = "F1 M21 20V2H3v18H1v3h22v-3M19 4v7h-6V4M5 4h6v7H5m0 9v-7h6v7m2 0v-7h6v7Z",
            // LM: close-box-outline (ô vuông có dấu X, người dùng chọn 2026-10-30)
            ["LM"] = "F1 M19 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2m0 16H5V5h14zM17 8.4L13.4 12l3.6 3.6l-1.4 1.4l-3.6-3.6L8.4 17L7 15.6l3.6-3.6L7 8.4L8.4 7l3.6 3.6L15.6 7z",
            // NC: wall-fire (tường ngăn lửa)
            ["NC"] = "F1 m22.14 15.34l-.02.01c.23.28.43.59.58.92l.09.19c.71 1.69.21 3.64-1.1 4.86c-1.19 1.09-2.85 1.38-4.39 1.18c-1.46-.18-2.8-1.1-3.57-2.37c-.23-.39-.43-.83-.53-1.28c-.13-.35-.17-.73-.2-1.1c-.09-1.6.55-3.3 1.76-4.3c-.55 1.21-.42 2.72.39 3.77l.11.13c.14.12.31.15.47.09c.15-.06.27-.21.27-.37l-.07-.24c-.88-2.33-.14-5.03 1.73-6.56c.51-.42 1.14-.8 1.8-.97c-.68 1.36-.46 3.14.63 4.2c.46.5 1.02.79 1.49 1.23zM19.86 20l-.01-.03c.45-.39.7-1.06.68-1.66L20.5 18c-.2-1-1.07-1.34-1.63-2.07l-.43-.78c-.22.5-.24.97-.15 1.51c.1.57.32 1.06.21 1.65c-.16.65-.67 1.3-1.56 1.51c.5.49 1.31.88 2.12.6c.26-.07.59-.26.8-.42M3 16h8.06L11 17c0 1.41.36 2.73 1 3.88V21H3zm-1-6h6v5H2zm7 0h6v.07A8.03 8.03 0 0 0 11.25 15H9zM3 4h8v5H3zm9 0h9v5h-9z",
            // CT: water-check (giọt nước đã chặn, chống thấm)
            ["CT"] = "F1 M21.75 16.25L17 21l-2.75-3l1.16-1.16L17 18.43l3.59-3.59zM17.62 12C16.31 8.1 12 3.25 12 3.25S6 10 6 14c0 3.31 2.69 6 6 6h.34c-.22-.64-.34-1.3-.34-2c0-3.18 2.5-5.78 5.62-6",
        };

        public static BitmapSource Ve(string ky, int px)
        {
            var dv = new DrawingVisual();
            using (DrawingContext dc = dv.RenderOpen())
            {
                if (Hinh.TryGetValue(ky, out string path))
                {
                    dc.PushTransform(new ScaleTransform(px / 24.0, px / 24.0));
                    dc.DrawGeometry(Brushes.White, null, Geometry.Parse(path));
                    dc.Pop();
                }
                else
                {
                    var ft = new FormattedText(ky, CultureInfo.InvariantCulture, FlowDirection.LeftToRight,
                        new Typeface(new FontFamily("Arial"), FontStyles.Normal, FontWeights.Bold, FontStretches.Normal),
                        px * (ky.Length > 2 ? 0.34 : 0.42), Brushes.White, 1.0);
                    dc.DrawText(ft, new Point((px - ft.Width) / 2, (px - ft.Height) / 2));
                }
            }
            var bmp = new RenderTargetBitmap(px, px, 96, 96, PixelFormats.Pbgra32);
            bmp.Render(dv);
            bmp.Freeze();
            return bmp;
        }
    }
}
