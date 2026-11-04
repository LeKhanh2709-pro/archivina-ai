// Xem trước icon tab Archivina: ribbon giả lập sáng / tối + bảng icon phóng to; xuất icon PNG 96 px (đen / trắng).
// Chạy: dotnet run -- <thư mục làm việc>   (đọc bang_icon.json + mdi.json, ghi out\*.png, xem_ribbon.png, bang_icon.png)
using System; using System.Collections.Generic; using System.Globalization; using System.IO; using System.Linq;
using System.Text.Json; using System.Text.RegularExpressions;
using System.Windows; using System.Windows.Media; using System.Windows.Media.Imaging;

class Nut { public string Ten, Nhan, Icon; }
class Panel { public string Ten, TieuDe; public List<List<Nut>> Chong = new(); public List<Nut> Lon = new(); }

static class P {
  static Dictionary<string, Geometry> Hinh = new();
  static Typeface Chu = new Typeface("Segoe UI");

  static Geometry Doc(string body) {
    var g = new GeometryGroup { FillRule = FillRule.Nonzero };
    foreach (Match m in Regex.Matches(body, "d=\"([^\"]+)\"")) g.Children.Add(Geometry.Parse(m.Groups[1].Value));
    g.Freeze(); return g;
  }

  static void VeIcon(DrawingContext dc, string ten, Rect r, Brush b) {
    var g = Hinh[ten].Clone();
    g.Transform = new MatrixTransform(r.Width / 24, 0, 0, r.Height / 24, r.X, r.Y);
    dc.DrawGeometry(b, null, g);
  }

  static FormattedText Text(string s, double size, Brush b, bool dam = false) =>
    new FormattedText(s, CultureInfo.GetCultureInfo("vi-VN"), FlowDirection.LeftToRight,
      dam ? new Typeface(new FontFamily("Segoe UI"), FontStyles.Normal, FontWeights.SemiBold, FontStretches.Normal) : Chu,
      size, b, 1.0);

  static void Luu(Visual v, int w, int h, double tl, string file) {
    var bmp = new RenderTargetBitmap((int)(w * tl), (int)(h * tl), 96 * tl, 96 * tl, PixelFormats.Pbgra32); bmp.Render(v);
    var enc = new PngBitmapEncoder(); enc.Frames.Add(BitmapFrame.Create(bmp));
    using var fs = File.Create(file); enc.Save(fs);
  }

  // Vẽ 1 dải ribbon (danh sách panel) tại (x0, y0); trả về chiều rộng
  static double VeRibbon(DrawingContext dc, List<Panel> ds, double x0, double y0, bool toi) {
    Brush nen = new SolidColorBrush(toi ? Color.FromRgb(0x3B, 0x44, 0x53) : Color.FromRgb(0xF5, 0xF6, 0xF7));
    Brush vien = new SolidColorBrush(toi ? Color.FromRgb(0x55, 0x60, 0x70) : Color.FromRgb(0xD5, 0xD8, 0xDC));
    Brush chu = toi ? Brushes.White : new SolidColorBrush(Color.FromRgb(0x20, 0x20, 0x20));
    Brush thanh = new SolidColorBrush(toi ? Color.FromRgb(0x2E, 0x35, 0x41) : Color.FromRgb(0xE4, 0xE7, 0xEA));
    Brush mau = toi ? Brushes.White : new SolidColorBrush(Color.FromRgb(0x20, 0x20, 0x20));
    double H = 96, x = x0;
    foreach (var p in ds) {
      double w = 8, xi = x + 6;
      // Vẽ nội dung vào nhóm riêng, đặt lên trên nền panel sau khi biết chiều rộng
      var nhom = new DrawingGroup(); var dcNen = dc; var dcp = nhom.Open();
      dc = dcp;
      foreach (var n in p.Lon) {
        var dong = n.Nhan.Split('\n');
        double bw = Math.Max(44, dong.Max(d => Text(d, 11, chu).Width) + 10);
        double bx = xi;
        VeIcon(dc, n.Icon, new Rect(bx + (bw - 32) / 2, y0 + 6, 32, 32), mau);
        for (int i = 0; i < dong.Length; i++) {
          var t = Text(dong[i], 11, chu); dc.DrawText(t, new Point(bx + (bw - t.Width) / 2, y0 + 41 + i * 14));
        }
        xi += bw + 2;
      }
      foreach (var c in p.Chong) {
        double cw = c.Max(n => Text(n.Nhan, 11, chu).Width) + 26, cy = y0 + 6;
        double dy = c.Count == 3 ? 24 : 32, oy = c.Count == 3 ? 0 : 4;
        foreach (var n in c) {
          VeIcon(dc, n.Icon, new Rect(xi + 2, cy + oy + 2, 16, 16), mau);
          dc.DrawText(Text(n.Nhan, 11, chu), new Point(xi + 22, cy + oy + 2));
          cy += dy;
        }
        xi += cw + 6;
      }
      dcp.Close(); dc = dcNen;
      w = xi - x + 4;
      var td = Text(p.TieuDe, 11, chu);
      w = Math.Max(w, td.Width + 16);
      dc.DrawRectangle(nen, null, new Rect(x, y0, w, H));
      dc.DrawRectangle(thanh, null, new Rect(x, y0 + H - 18, w, 18));
      dc.DrawRectangle(vien, null, new Rect(x + w - 1, y0, 1, H));
      dc.DrawDrawing(nhom);
      dc.DrawText(td, new Point(x + (w - td.Width) / 2, y0 + H - 17));
      x += w;
    }
    return x - x0;
  }

  [STAThread] static void Main(string[] a) {
    string d = a.Length > 0 ? a[0] : ".";
    using (var js = JsonDocument.Parse(File.ReadAllText(Path.Combine(d, "mdi.json"))))
      foreach (var ic in js.RootElement.GetProperty("icons").EnumerateObject())
        Hinh[ic.Name] = Doc(ic.Value.GetProperty("body").GetString());
    var ds = new List<Panel>();
    using (var js = JsonDocument.Parse(File.ReadAllText(Path.Combine(d, "bang_icon.json"))))
      foreach (var pp in js.RootElement.EnumerateObject()) {
        var p = new Panel { Ten = pp.Name, TieuDe = pp.Value.GetProperty("title").GetString() };
        Nut N(JsonElement e) => new Nut { Ten = e[0].GetString(), Nhan = e[1].GetString(), Icon = e[2].GetString() };
        if (pp.Value.TryGetProperty("stacks", out var st)) foreach (var c in st.EnumerateArray()) p.Chong.Add(c.EnumerateArray().Select(N).ToList());
        if (pp.Value.TryGetProperty("large", out var lg)) p.Lon = lg.EnumerateArray().Select(N).ToList();
        ds.Add(p);
      }
    // Dải 1: Kết cấu → Hoàn thiện; dải 2: phần còn lại (ribbon thật là 1 dải liền, chia 2 cho vừa ảnh)
    var d1 = ds.Take(4).ToList(); var d2 = ds.Skip(4).ToList();
    int W = 1400, H = 2 * (2 * 96 + 30) + 70;
    var v = new DrawingVisual();
    using (var dc = v.RenderOpen()) {
      dc.DrawRectangle(Brushes.White, null, new Rect(0, 0, W, H));
      double y = 8;
      foreach (bool toi in new[] { false, true }) {
        dc.DrawText(Text(toi ? "Giao diện TỐI (icon.dark.png – nét trắng)" : "Giao diện SÁNG (icon.png – nét đen)", 13, Brushes.Black, true), new Point(8, y));
        y += 22;
        VeRibbon(dc, d1, 8, y, toi); y += 100;
        VeRibbon(dc, d2, 8, y, toi); y += 114;
      }
    }
    Luu(v, W, H, 1.5, Path.Combine(d, "xem_ribbon.png"));

    // Bảng icon phóng to 48 px kèm tên nút
    var tat = ds.SelectMany(p => p.Lon.Concat(p.Chong.SelectMany(c => c)).Select(n => (p.TieuDe, n))).ToList();
    int cot = 6, o = 220, h = 92, hang = (tat.Count + cot - 1) / cot;
    var v2 = new DrawingVisual();
    using (var dc = v2.RenderOpen()) {
      dc.DrawRectangle(Brushes.White, null, new Rect(0, 0, cot * o, hang * h));
      for (int i = 0; i < tat.Count; i++) {
        var (pt, n) = tat[i]; double x = (i % cot) * o, y = (i / cot) * h;
        VeIcon(dc, n.Icon, new Rect(x + 10, y + 12, 48, 48), new SolidColorBrush(Color.FromRgb(0x20, 0x20, 0x20)));
        dc.DrawText(Text($"{i + 1}. {n.Nhan.Replace('\n', ' ')}", 12, Brushes.Black, true), new Point(x + 66, y + 14));
        dc.DrawText(Text(pt, 11, Brushes.Gray), new Point(x + 66, y + 32));
        dc.DrawText(Text(n.Icon, 10, Brushes.SteelBlue), new Point(x + 66, y + 48));
      }
    }
    Luu(v2, cot * o, hang * h, 1, Path.Combine(d, "bang_icon.png"));

    // Icon thật cho pyRevit: 96 px (pyRevit tự thu nhỏ 32 / 16), nền trong suốt
    var od = Directory.CreateDirectory(Path.Combine(d, "out")).FullName;
    foreach (var (_, n) in tat)
      foreach (bool toi in new[] { false, true }) {
        var vi = new DrawingVisual();
        using (var dc = vi.RenderOpen())
          VeIcon(dc, n.Icon, new Rect(4, 4, 88, 88), toi ? Brushes.White : new SolidColorBrush(Color.FromRgb(0x20, 0x20, 0x20)));
        Luu(vi, 96, 96, 1, Path.Combine(od, n.Ten + (toi ? ".dark.png" : ".png")));
      }
    Console.WriteLine($"{tat.Count} nút");
  }
}
