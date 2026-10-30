// Biểu tượng nút K-TOOL vẽ bằng code (hình vector, không cần file ảnh mang theo).
// Vẽ trên lưới 32 x 32 rồi co theo cỡ nút (32 px nút lớn, 16 px nút nhỏ): ô vuông bo góc màu + hình trắng.
// Ký hiệu chưa có hình riêng thì vẽ chữ như bản cũ.

using System.Globalization;
using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Imaging;

namespace KTool
{
    static class BieuTuong
    {
        public static BitmapSource Ve(string ky, Color mau, int px)
        {
            var dv = new DrawingVisual();
            using (DrawingContext dc = dv.RenderOpen())
            {
                dc.DrawRoundedRectangle(new SolidColorBrush(mau), null, new Rect(0, 0, px, px), px * 0.18, px * 0.18);
                dc.PushTransform(new ScaleTransform(px / 32.0, px / 32.0));
                bool coHinh = true;
                switch (ky)
                {
                    case "VK": VachKinhMatBang(dc); break;
                    case "MĐ": VachKinhMatDung(dc); break;
                    case "LM": LoMo(dc); break;
                    case "NC": NganChay(dc, mau); break;
                    case "CT": ChongTham(dc); break;
                    default: coHinh = false; break;
                }
                dc.Pop();
                if (!coHinh) Chu(dc, ky, px);
            }
            var bmp = new RenderTargetBitmap(px, px, 96, 96, PixelFormats.Pbgra32);
            bmp.Render(dv);
            bmp.Freeze();
            return bmp;
        }

        static readonly Brush Trang = Brushes.White;

        static Pen But(double day)
        {
            var p = new Pen(Trang, day) { StartLineCap = PenLineCap.Round, EndLineCap = PenLineCap.Round, LineJoin = PenLineJoin.Round };
            p.Freeze();
            return p;
        }

        // Mặt bằng vách kính: 2 nét kính + 4 đố đứng + cung mở cửa
        static void VachKinhMatBang(DrawingContext dc)
        {
            Pen kinh = But(1.4);
            dc.DrawLine(kinh, new Point(4, 22), new Point(28, 22));
            dc.DrawLine(kinh, new Point(4, 25), new Point(28, 25));
            foreach (double x in new[] { 3.0, 13.5, 26.0 })
                dc.DrawRectangle(Trang, null, new Rect(x, 20, 3, 7));
            // Cánh cửa mở 90° ở ô bên phải
            dc.DrawLine(But(2.2), new Point(17.5, 21), new Point(17.5, 11));
            var cung = Geometry.Parse("M 17.5,11 A 10,10 0 0 1 27.5,21");
            dc.DrawGeometry(null, But(1.2), cung);
        }

        // Mặt đứng vách kính: khung + đố đứng + đố ngang + ký hiệu kính ///
        static void VachKinhMatDung(DrawingContext dc)
        {
            Pen khung = But(2.2);
            dc.DrawRectangle(null, khung, new Rect(5, 5, 22, 22));
            dc.DrawLine(khung, new Point(12.3, 5), new Point(12.3, 27));
            dc.DrawLine(khung, new Point(19.7, 5), new Point(19.7, 27));
            dc.DrawLine(khung, new Point(5, 12), new Point(27, 12));
            Pen kinh = But(1.1);
            foreach (double x0 in new[] { 5.0, 12.3, 19.7 })
            {
                dc.DrawLine(kinh, new Point(x0 + 2.0, 20.5), new Point(x0 + 4.5, 16.5));
                dc.DrawLine(kinh, new Point(x0 + 2.5, 23.5), new Point(x0 + 5.5, 18.5));
            }
        }

        // Lỗ mở MEP: khung + dấu X như block A-MEP
        static void LoMo(DrawingContext dc)
        {
            Pen p = But(2.2);
            dc.DrawRectangle(null, p, new Rect(6, 6, 20, 20));
            dc.DrawLine(p, new Point(6, 6), new Point(26, 26));
            dc.DrawLine(p, new Point(26, 6), new Point(6, 26));
        }

        // Ngăn cháy lan: ngọn lửa (lõi lửa khoét theo màu nền)
        static void NganChay(DrawingContext dc, Color nen)
        {
            var lua = Geometry.Parse("M 16,3 C 18,9 25,12 25,20 C 25,25.5 21,29 16,29 C 11,29 7,25.5 7,20 C 7,15 10,13 11,9 C 13,12 13,14 14,15 C 15,11 16,7 16,3 Z");
            dc.DrawGeometry(Trang, null, lua);
            var loi = Geometry.Parse("M 16,16.5 C 17.2,19.5 20.2,21 20.2,24 C 20.2,26.4 18.3,27.6 16,27.6 C 13.7,27.6 11.8,26.4 11.8,24 C 11.8,21.3 14.8,19.8 16,16.5 Z");
            dc.DrawGeometry(new SolidColorBrush(nen), null, loi);
        }

        // Chống thấm: giọt nước trên sàn gạch chéo
        static void ChongTham(DrawingContext dc)
        {
            var giot = Geometry.Parse("M 16,2.5 C 16,2.5 9,11.5 9,16.5 C 9,20.4 12.1,23.3 16,23.3 C 19.9,23.3 23,20.4 23,16.5 C 23,11.5 16,2.5 16,2.5 Z");
            dc.DrawGeometry(Trang, null, giot);
            dc.DrawLine(But(2.0), new Point(4, 26), new Point(28, 26));
            Pen gach = But(1.3);
            for (double x = 6; x <= 27; x += 4.2)
                dc.DrawLine(gach, new Point(x, 26), new Point(x - 2.6, 29.5));
        }

        static void Chu(DrawingContext dc, string ky, int px)
        {
            var ft = new FormattedText(ky, CultureInfo.InvariantCulture, FlowDirection.LeftToRight,
                new Typeface(new FontFamily("Arial"), FontStyles.Normal, FontWeights.Bold, FontStretches.Normal),
                px * (ky.Length > 2 ? 0.34 : 0.42), Trang, 1.0);
            dc.DrawText(ft, new Point((px - ft.Width) / 2, (px - ft.Height) / 2));
        }
    }
}
