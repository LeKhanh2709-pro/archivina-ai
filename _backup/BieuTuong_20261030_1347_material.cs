// Biểu tượng nút K-TOOL: icon trắng nền trong suốt (người dùng chọn kiểu trắng đen 2026-10-30).
// Hình lấy từ bộ Google Material Icons (bản baseline, lưới 24 x 24, giấy phép Apache 2.0, nguồn api.iconify.design/ic),
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
            // VK: view_week (vách chia đố)
            ["VK"] = "F1 M5.33 20H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2h1.33c1.1 0 2 .9 2 2v12a2 2 0 0 1-2 2M22 18V6c0-1.1-.9-2-2-2h-1.33c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2H20a2 2 0 0 0 2-2m-7.33 0V6c0-1.1-.9-2-2-2h-1.33c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h1.33c1.1 0 2-.9 2-2",
            // MĐ: window (mặt đứng vách kính)
            ["MĐ"] = "F1 M11 11V3H5c-1.1 0-2 .9-2 2v6zm2 0h8V5c0-1.1-.9-2-2-2h-6zm-2 2H3v6c0 1.1.9 2 2 2h6zm2 0v8h6c1.1 0 2-.9 2-2v-6z",
            // LM: disabled_by_default (ô có dấu X như block A-MEP)
            ["LM"] = "F1 M3 3v18h18V3zm14 12.59L15.59 17L12 13.41L8.41 17L7 15.59L10.59 12L7 8.41L8.41 7L12 10.59L15.59 7L17 8.41L13.41 12z",
            // NC: local_fire_department (ngăn cháy lan)
            ["NC"] = "F1 m12 12.9l-2.13 2.09c-.56.56-.87 1.29-.87 2.07C9 18.68 10.35 20 12 20s3-1.32 3-2.94c0-.78-.31-1.52-.87-2.07z" +
                     "M16 6l-.44.55C14.38 8.02 12 7.19 12 5.3V2S4 6 4 13c0 2.92 1.56 5.47 3.89 6.86c-.56-.79-.89-1.76-.89-2.8c0-1.32 .52-2.56 1.47-3.5L12 10.1l3.53 3.47c.95.93 1.47 2.17 1.47 3.5c0 1.02-.31 1.96-.85 2.75c1.89-1.15 3.29-3.06 3.71-5.3c.66-3.55-1.07-6.9-3.86-8.52",
            // CT: water_damage (chống thấm)
            ["CT"] = "F1 M12 3L2 12h3v8h14v-8h3zm0 13c-1.1 0-2-.9-2-2s2-4 2-4s2 2.9 2 4s-.9 2-2 2",
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
