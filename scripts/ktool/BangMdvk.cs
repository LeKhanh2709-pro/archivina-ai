// BangMdvk.cs — hộp thoại WPF của lệnh MDVK (mẫu người dùng duyệt 2026-10-31). Không tham chiếu AutoCAD.
// Md.Tinh chép đúng vkmd:tinh trong vkmd_nguon.lsp để xem trước và chặn nhập sai; dựng hình vẫn do LISP.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Shapes;

namespace KTool
{
    // Một vách do LISP nhận được
    class VachMd
    {
        public string Loai;     // "D" / "S" / "K"
        public bool LaVk;       // block VK, không thì vách vẽ tay
        public double L;
        public List<(string Loai, double Rong)> O = new();
        public List<double> Tam = new();

        // "D|1|4210|K:826.67,D:1665,K:826.67|32.5,859.17,..."
        internal static VachMd Doc(string s)
        {
            string[] p = s.Split('|');
            var v = new VachMd { Loai = p[0], LaVk = p[1] == "1", L = So(p[2]) };
            foreach (string x in p[3].Split(',', StringSplitOptions.RemoveEmptyEntries))
            {
                string[] q = x.Split(':');
                v.O.Add((q[0], So(q[1])));
            }
            v.Tam = p[4].Split(',', StringSplitOptions.RemoveEmptyEntries).Select(So).ToList();
            return v;
        }

        static double So(string s) => double.Parse(s, CultureInfo.InvariantCulture);
    }

    // Kết quả vkmd:tinh: ngang (y1 y2) hoặc null; so (đáy đố dưới, đỉnh đố dưới, đỉnh cánh) hoặc null; hd cao cửa
    class KetQuaMd
    {
        public string Loai;
        public double[] Ngang, So;
        public double Hd;
        public bool BoNgang;    // cửa đi không đủ chỗ thanh ngang
    }

    static class Md
    {
        const double D = 65.0;

        internal static KetQuaMd Tinh(string loai, double? H, double? hd, double? hs, bool co, double? san, double? bau, out string loi)
        {
            loi = null;
            if (H == null || H <= 3 * D) { loi = "Nhập chiều cao vách"; return null; }
            if (loai == "D")
            {
                if (hd == null || hd <= 0) { loi = "Nhập chiều cao cửa đi"; return null; }
                if (hd > H + 1e-6) { loi = $"Cửa đi cao {ChuDe.So(hd.Value)} > vách {ChuDe.So(H.Value)}"; return null; }
                if (hd + D + D > H + 1e-6) return new KetQuaMd { Loai = loai, Hd = H.Value - D, BoNgang = true };
                return new KetQuaMd { Loai = loai, Ngang = new[] { hd.Value, hd.Value + D }, Hd = hd.Value };
            }
            if (co && (hs == null || hs <= 0)) { loi = "Nhập chiều cao cửa sổ"; return null; }
            if ((loai == "S" || co) && (san == null || san < 0)) { loi = "Nhập chiều dày sàn hoàn thiện (0 nếu không có)"; return null; }
            if ((loai == "S" || co) && (bau == null || bau <= 0)) { loi = "Nhập cao bậu cửa sổ"; return null; }

            double y1 = (loai == "S" || co) ? san.Value + bau.Value : 0, yt;
            double[] ngang = null, so = null;
            if (co) { yt = y1 + hs.Value; ngang = new[] { yt, yt + D }; }
            else yt = H.Value - D;
            if (loai == "S") so = new[] { y1 - D, y1, yt };
            if (ngang != null && ngang[1] > H - D - 1e-6)
            {
                loi = $"Thanh ngang chạm khung trên: sàn + bậu + cửa sổ + 65 = {ChuDe.So(ngang[1])} > {ChuDe.So(H.Value - D)} (bỏ thanh ngang hoặc giảm số đo)";
                return null;
            }
            if (so != null && yt - y1 <= 0) { loi = $"Vách thấp quá: sàn + bậu = {ChuDe.So(y1)} >= mép dưới khung trên {ChuDe.So(H.Value - D)}"; return null; }
            if (so != null && so[0] < D - 1e-6) { loi = $"Đố dưới cửa sổ chạm khung dưới: sàn + bậu phải >= {ChuDe.So(2 * D)}"; return null; }
            return new KetQuaMd { Loai = loai, Ngang = ngang, So = so };
        }
    }

    class BangMdvk
    {
        readonly Window w;
        readonly TextBox txtCao, txtHd, txtHs, txtSan, txtBau;
        readonly CheckBox chkCo;
        readonly TextBlock lblTrangThai;
        readonly Canvas cvMd;
        readonly StackPanel spVach;
        readonly FrameworkElement khungDi, khungSo;
        readonly List<VachMd> ds;
        readonly bool coDi, coSo;

        int chon;
        KetQuaMd kqXem;
        string loiChung;
        bool toi;

        internal string Ma = "huy";
        internal Window CuaSo => w;
        internal bool CheDoToi => toi;

        internal BangMdvk(Dictionary<string, string> vao, List<VachMd> ds, bool cheDoToi)
        {
            this.ds = ds;
            toi = cheDoToi;
            w = ChuDe.TaoCuaSo("BangMdvk.xaml", toi, t => { toi = t; VeDanhSach(); CapNhat(); });
            txtCao = (TextBox)w.FindName("txtCao"); txtHd = (TextBox)w.FindName("txtHd"); txtHs = (TextBox)w.FindName("txtHs");
            txtSan = (TextBox)w.FindName("txtSan"); txtBau = (TextBox)w.FindName("txtBau");
            chkCo = (CheckBox)w.FindName("chkCo");
            lblTrangThai = (TextBlock)w.FindName("lblTrangThai");
            cvMd = (Canvas)w.FindName("cvMd");
            spVach = (StackPanel)w.FindName("spVach");
            khungDi = (FrameworkElement)w.FindName("khungDi");
            khungSo = (FrameworkElement)w.FindName("khungSo");

            string Lay(string k, string md) => vao.TryGetValue(k, out string v) ? v : md;
            txtCao.Text = Lay("cao", ""); txtHd.Text = Lay("hd", "2700"); txtHs.Text = Lay("hs", "1400");
            txtSan.Text = Lay("san", "50"); txtBau.Text = Lay("bau", "1400");
            chkCo.IsChecked = Lay("co", "1") == "1";

            int nDi = ds.Count(v => v.Loai == "D"), nSo = ds.Count(v => v.Loai == "S"), nKinh = ds.Count(v => v.Loai == "K");
            coDi = nDi > 0;
            coSo = ds.Count > nDi;
            var moTa = new List<string>();
            if (nDi > 0) moTa.Add($"{nDi} cửa đi");
            if (nSo > 0) moTa.Add($"{nSo} cửa sổ");
            if (nKinh > 0) moTa.Add($"{nKinh} kính");
            ((TextBlock)w.FindName("lblSoVach")).Text = $"Tìm thấy {ds.Count} vách: {string.Join(", ", moTa)}";
            ((TextBlock)w.FindName("lblOk")).Text = $"Dựng {ds.Count} mặt đứng";

            foreach (TextBox t in new[] { txtCao, txtHd, txtHs, txtSan, txtBau })
            {
                t.TextChanged += (s, e) => CapNhat();
                t.GotKeyboardFocus += (s, e) => t.SelectAll();
            }
            chkCo.Click += (s, e) => CapNhat();
            cvMd.SizeChanged += (s, e) => VeMatDung();
            ((Button)w.FindName("btnOk")).Click += (s, e) => { CapNhat(); if (loiChung == null) { Ma = "ok"; w.Close(); } };
            ((Button)w.FindName("btnHuy")).Click += (s, e) => w.Close();
            ((Button)w.FindName("btnDong")).Click += (s, e) => w.Close();
            w.Loaded += (s, e) => { txtCao.Focus(); txtCao.SelectAll(); };
            VeDanhSach();
            CapNhat();
        }

        static string TenLoai(string l) => l == "D" ? "Cửa đi" : l == "S" ? "Cửa sổ" : "Kính không cửa";

        void VeDanhSach()
        {
            spVach.Children.Clear();
            for (int i = 0; i < ds.Count; i++)
            {
                int so = i;
                VachMd v = ds[i];
                var sp = new StackPanel { Orientation = Orientation.Horizontal };
                sp.Children.Add(new Rectangle
                {
                    Width = 9, Height = 9, RadiusX = 2, RadiusY = 2, Margin = new Thickness(0, 0, 8, 0),
                    VerticalAlignment = VerticalAlignment.Center,
                    Fill = ChuDe.Mau(w, v.Loai == "D" ? "Di" : v.Loai == "S" ? "So" : "Kinh"),
                });
                var chu = new StackPanel();
                chu.Children.Add(ChuDe.Chu($"{i + 1}. {TenLoai(v.Loai)}", ChuDe.Mau(w, "Chu"), 12));
                chu.Children.Add(ChuDe.Chu($"Dài {ChuDe.So(v.L)}{(v.LaVk ? " (VK)" : " (vẽ tay)")}", ChuDe.Mau(w, "Chu2")));
                sp.Children.Add(chu);
                bool dang = i == chon;
                var dong = new Border
                {
                    Child = sp, Padding = new Thickness(8, 4, 8, 4), CornerRadius = new CornerRadius(4), Cursor = Cursors.Hand,
                    Background = dang ? ChuDe.Mau(w, "Pan2") : Brushes.Transparent,
                    BorderBrush = dang ? ChuDe.Mau(w, "Ln") : Brushes.Transparent, BorderThickness = new Thickness(1),
                };
                dong.MouseLeftButtonUp += (a, e) => { chon = so; VeDanhSach(); CapNhat(); };
                System.Windows.Automation.AutomationProperties.SetName(dong, $"Vách {i + 1}");
                spVach.Children.Add(dong);
            }
        }

        void CapNhat()
        {
            VachMd v = ds[chon];
            bool co = chkCo.IsChecked == true;
            double? H = ChuDe.DocSo(txtCao.Text), hd = ChuDe.DocSo(txtHd.Text), hs = ChuDe.DocSo(txtHs.Text),
                    san = ChuDe.DocSo(txtSan.Text), bau = ChuDe.DocSo(txtBau.Text);

            // bật ô của loại vách có trong danh sách; khung không thuộc vách đang xem thì mờ đi
            khungDi.IsEnabled = coDi;
            khungSo.IsEnabled = coSo;
            khungDi.Opacity = v.Loai == "D" ? 1 : 0.5;
            khungSo.Opacity = v.Loai != "D" ? 1 : 0.5;
            txtHs.IsEnabled = co;
            bool canSan = co || ds.Any(x => x.Loai == "S");
            txtSan.IsEnabled = canSan;
            txtBau.IsEnabled = canSan;

            kqXem = Md.Tinh(v.Loai, H, hd, hs, co, san, bau, out string loiXem);
            // lỗi của vách bất kỳ chặn nút Dựng; thông số bảng áp cho mọi vách
            loiChung = loiXem;
            if (loiChung == null)
                foreach (VachMd x in ds)
                {
                    Md.Tinh(x.Loai, H, hd, hs, co, san, bau, out string l);
                    if (l != null) { loiChung = $"Vách {ChuDe.So(x.L)} mm ({TenLoai(x.Loai).ToLower()}): {l}"; break; }
                }

            lblTrangThai.Foreground = ChuDe.Mau(w, loiChung != null ? "Di" : "Chu2");
            lblTrangThai.Text = loiChung ?? MoTa(kqXem);
            VeMatDung();
        }

        static string MoTa(KetQuaMd k)
        {
            var p = new List<string>();
            if (k.Loai == "D")
            {
                if (k.BoNgang) return $"Không đủ chỗ thanh ngang: bỏ thanh ngang, cửa cao {ChuDe.So(k.Hd)} sát dưới khung trên";
                p.Add($"Đỉnh cửa +{ChuDe.So(k.Hd)}");
            }
            if (k.So != null) p.Add($"Mép dưới cánh +{ChuDe.So(k.So[1])}, cao cửa sổ {ChuDe.So(k.So[2] - k.So[1])}");
            if (k.Ngang != null) p.Add($"tâm thanh ngang +{ChuDe.So(k.Ngang[0] + 32.5)}");
            return p.Count > 0 ? string.Join(", ", p) : "Vách kính không có thanh ngang";
        }

        void VeMatDung()
        {
            cvMd.Children.Clear();
            double W = cvMd.ActualWidth, Hc = cvMd.ActualHeight;
            double? hh = ChuDe.DocSo(txtCao.Text);
            VachMd v = ds[chon];
            if (W <= 0 || Hc <= 0 || kqXem == null || hh == null) return;
            double H = hh.Value, L = v.L, d = 65, nua = 32.5;
            const double leT = 30, leD = 28, le = 6;
            double sc = Math.Min((W - leT - le) / L, (Hc - leD - le) / H);
            double x0 = leT + ((W - leT - le) - L * sc) / 2, yb = Hc - leD - ((Hc - leD - le) - H * sc) / 2;
            double Px(double x) => x0 + x * sc;
            double Py(double y) => yb - y * sc;
            Brush doM = ChuDe.Mau(w, "Do_"), soM = ChuDe.Mau(w, "So"), diM = ChuDe.Mau(w, "Di"), kinh = ChuDe.Mau(w, "Kinh"), chu2 = ChuDe.Mau(w, "Chu2");

            void Thanh(double xa, double xb, double y1, double y2, Brush m) =>
                ChuDe.Them(cvMd, new Rectangle { Width = Math.Max((xb - xa) * sc, 1), Height = Math.Max((y2 - y1) * sc, 1), Fill = m }, Px(xa), Py(y2));
            void Net(double ax, double ay, double bx, double by, Brush m, double t) =>
                cvMd.Children.Add(new Line { X1 = ax, Y1 = ay, X2 = bx, Y2 = by, Stroke = m, StrokeThickness = t });

            for (int i = 0; i < v.O.Count; i++)
            {
                string loai = v.O[i].Loai;
                double xa = v.Tam[i] + nua, xb = v.Tam[i + 1] - nua, cx = (xa + xb) / 2;
                // như vkmd:ve-xem: khung trên, khung dưới trừ ô cửa đi, thanh ngang, đố dưới cửa sổ
                Thanh(xa, xb, H - d, H, doM);
                if (loai != "D") Thanh(xa, xb, 0, d, doM);
                if (kqXem.Ngang != null) Thanh(xa, xb, kqXem.Ngang[0], kqXem.Ngang[1], doM);
                if (loai == "S")
                {
                    double[] so = kqXem.So;
                    Thanh(xa, xb, so[1], so[2], soM);
                    Thanh(xa, xb, so[0], so[1], doM);
                }
                else if (loai == "D")
                {
                    double hd = kqXem.Hd;
                    ChuDe.Them(cvMd, new Rectangle { Width = (xb - xa) * sc, Height = hd * sc, Stroke = diM, StrokeThickness = 1.5 }, Px(xa), Py(hd));
                    Net(Px(cx), Py(hd), Px(xa), Py(hd / 2), diM, 1);
                    Net(Px(xa), Py(hd / 2), Px(cx), Py(0), diM, 1);
                    Net(Px(cx), Py(0), Px(xb), Py(hd / 2), diM, 1);
                    Net(Px(xb), Py(hd / 2), Px(cx), Py(hd), diM, 1);
                }
                else
                {
                    // ký hiệu kính "///"
                    double cy = H * 0.55;
                    for (int q = -1; q < 2; q++)
                        Net(Px(cx) + q * 7 - 6, Py(cy) + 6, Px(cx) + q * 7 + 6, Py(cy) - 6, kinh, 0.8);
                }
            }
            foreach (double c in v.Tam) Thanh(c - nua, c + nua, 0, H, doM);

            double yDim = Py(0) + 10, xDim = Px(0) - 10;
            Net(Px(0), yDim, Px(L), yDim, chu2, 0.7);
            ChuDe.ChuGiua(cvMd, ChuDe.Chu(ChuDe.So(L), chu2, 12), Px(L / 2), yDim + 10);
            Net(xDim, Py(H), xDim, Py(0), chu2, 0.7);
            ChuDe.ChuGiua(cvMd, ChuDe.Chu(ChuDe.So(H), chu2, 12), xDim - 10, Py(H / 2), -90);
        }

        internal Dictionary<string, string> KetQua() => new()
        {
            ["ma"] = Ma, ["cao"] = txtCao.Text ?? "", ["hd"] = txtHd.Text ?? "", ["hs"] = txtHs.Text ?? "",
            ["co"] = chkCo.IsChecked == true ? "1" : "0", ["san"] = txtSan.Text ?? "", ["bau"] = txtBau.Text ?? "",
            ["theme"] = toi ? "dark" : "light",
        };
    }
}
