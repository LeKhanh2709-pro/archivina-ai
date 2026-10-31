// BangVk.cs — hộp thoại WPF của lệnh VK (mẫu người dùng duyệt 2026-10-31). Không tham chiếu AutoCAD.
// Vk.Chia chép đúng vk:chia trong vk_nguon.lsp để xem trước tức thời; bấm Dựng vách thì LISP tính lại bằng chính
// vk:chia với vị trí cửa trả về, nên sửa quy tắc chia trong LISP thì phải sửa cả ở đây.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Shapes;

namespace KTool
{
    // o: (loại "K" / "S" / "D", rộng); tam: vị trí tâm đố; b: rộng ô kính; n: số ô kính
    class KetQuaChia
    {
        public List<(string Loai, double Rong)> O = new();
        public List<double> Tam = new();
        public double B;
        public int N;
    }

    static class Vk
    {
        const double DoRong = 65.0, ToiDa = 1200.0;

        // Như vk:chia: trả về kết quả, lỗi thì loi là thông báo
        internal static KetQuaChia Chia(double? L, int ns, double? ws, int nd, double? wd, List<int> vs, List<int> vd, out string loi)
        {
            loi = null;
            if (L == null || L <= DoRong) { loi = "Nhập chiều dài vách lớn hơn 65 mm"; return null; }
            if (ns < 0 || nd < 0) { loi = "Số lượng cửa không được âm"; return null; }
            if (ns > 0 && (ws == null || ws <= 0)) { loi = "Nhập bề rộng cửa sổ"; return null; }
            if (nd > 0 && (wd == null || wd <= 0)) { loi = "Nhập bề rộng cửa đi"; return null; }
            if (vs.Count > ns) { loi = $"Ô cửa sổ: ghi {vs.Count} ô nhưng chỉ có {ns} cửa sổ"; return null; }
            if (vd.Count > nd) { loi = $"Ô cửa đi: ghi {vd.Count} ô nhưng chỉ có {nd} cửa đi"; return null; }
            double S = L.Value - DoRong, R = S - ns * (ws ?? 0) - nd * (wd ?? 0);
            if (R < -1e-6) { loi = $"Vách quá ngắn: cửa chiếm {ChuDe.So(S - R)} > khoảng chia {ChuDe.So(S)}"; return null; }

            int n = R < 1e-6 ? 0 : 1 + (int)(R / ToiDa);
            int tong = n + ns + nd;
            double b = n > 0 ? R / n : 0.0;
            var coDinh = new Dictionary<int, string>();
            foreach (var (k, l) in vs.Select(k => (k, "S")).Concat(vd.Select(k => (k, "D"))))
            {
                if (k > tong) { loi = $"Ô đặt cửa phải từ 1 đến {tong}"; return null; }
                if (coDinh.ContainsKey(k)) { loi = "Hai cửa trùng một ô"; return null; }
                coDinh[k] = l;
            }
            // cửa không ghi ô: rải đều vào các ô còn trống (cửa đi trước, cửa sổ sau)
            var tuDo = Enumerable.Range(1, tong).Where(i => !coDinh.ContainsKey(i)).ToList();
            var tuDong = Enumerable.Repeat("D", nd - vd.Count).Concat(Enumerable.Repeat("S", ns - vs.Count)).ToList();
            for (int i = 0; i < tuDong.Count; i++)
                coDinh[tuDo[(int)((i + 0.5) * tuDo.Count / tuDong.Count)]] = tuDong[i];

            var kq = new KetQuaChia { B = b, N = n };
            double x = DoRong / 2.0;
            kq.Tam.Add(x);
            for (int i = 1; i <= tong; i++)
            {
                coDinh.TryGetValue(i, out string t);
                (string, double) o = t == "S" ? ("S", ws.Value) : t == "D" ? ("D", wd.Value) : ("K", b);
                kq.O.Add(o);
                x += o.Item2;
                kq.Tam.Add(x);
            }
            return kq;
        }

        internal static List<int> ViTri(KetQuaChia kq, string loai) =>
            kq.O.Select((x, i) => (x.Loai, i + 1)).Where(p => p.Loai == loai).Select(p => p.Item2).ToList();
    }

    class BangVk
    {
        readonly Window w;
        readonly TextBox txtDai, txtTen, txtNs, txtWs, txtNd, txtWd;
        readonly TextBlock lblDo, lblKinh, lblRong, lblTrangThai, lblTenTuDat;
        readonly Canvas cvPlan;
        readonly StackPanel spBang;
        readonly ToggleButton tgSo, tgDi;
        readonly CheckBox chkLat;
        readonly Func<string, bool> coBlock, tenHopLe;
        readonly double? diemDai;

        List<int> vs, vd;           // vị trí cửa đang tích
        string but;                 // "S" / "D": ô tích sẽ là
        KetQuaChia kq;
        string loiChia, daNs, daNd;
        bool tenLoi, toi, dangDat;

        internal string Ma = "huy";
        internal Window CuaSo => w;

        // vao: dai ns ws nd wd lat ten loaitich vs vd (bộ nhớ của LISP) + diemdai: chiều dài 2 điểm đã pick
        internal BangVk(Dictionary<string, string> vao, bool cheDoToi, Func<string, bool> coBlock, Func<string, bool> tenHopLe)
        {
            this.coBlock = coBlock;
            this.tenHopLe = tenHopLe;
            toi = cheDoToi;
            w = ChuDe.TaoCuaSo("BangVk.xaml", toi, t => { toi = t; CapNhat(); });
            T<TextBox>("txtDai", out txtDai); T<TextBox>("txtTen", out txtTen); T<TextBox>("txtNs", out txtNs);
            T<TextBox>("txtWs", out txtWs); T<TextBox>("txtNd", out txtNd); T<TextBox>("txtWd", out txtWd);
            T<TextBlock>("lblDo", out lblDo); T<TextBlock>("lblKinh", out lblKinh); T<TextBlock>("lblRong", out lblRong);
            T<TextBlock>("lblTrangThai", out lblTrangThai); T<TextBlock>("lblTenTuDat", out lblTenTuDat);
            T<Canvas>("cvPlan", out cvPlan); T<StackPanel>("spBang", out spBang);
            T<ToggleButton>("tgSo", out tgSo); T<ToggleButton>("tgDi", out tgDi); T<CheckBox>("chkLat", out chkLat);

            string Lay(string k, string md = "") => vao.TryGetValue(k, out string v) ? v : md;
            dangDat = true;
            txtDai.Text = Lay("dai"); txtTen.Text = Lay("ten");
            txtNs.Text = Lay("ns", "0"); txtWs.Text = Lay("ws", "1000");
            txtNd.Text = Lay("nd", "0"); txtWd.Text = Lay("wd", "1665");
            chkLat.IsChecked = Lay("lat", "0") == "1";
            dangDat = false;
            daNs = txtNs.Text; daNd = txtNd.Text;
            vs = DocViTri(Lay("vs")); vd = DocViTri(Lay("vd"));
            diemDai = ChuDe.DocSo(Lay("diemdai"));
            string lt = Lay("loaitich");
            but = lt == "rd" ? "D" : lt == "rs" ? "S"
                : (ChuDe.DocSo(txtNd.Text) ?? 0) > 0 && (ChuDe.DocSo(txtNs.Text) ?? 0) <= 0 ? "D" : "S";

            foreach (TextBox t in new[] { txtDai, txtWs, txtWd, txtTen })
                t.TextChanged += (s, e) => { if (!dangDat) CapNhat(); };
            // số lượng: chốt khi rời ô (gõ dở "1" của "12" không được làm mất vị trí cửa đã tích)
            foreach (TextBox t in new[] { txtNs, txtNd })
            {
                t.LostKeyboardFocus += (s, e) => KiemSoLuong();
                t.GotKeyboardFocus += (s, e) => t.SelectAll();
            }
            foreach (TextBox t in new[] { txtDai, txtWs, txtWd })
                t.GotKeyboardFocus += (s, e) => t.SelectAll();
            tgSo.Click += (s, e) => { KiemSoLuong(); DatBut("S"); };
            tgDi.Click += (s, e) => { KiemSoLuong(); DatBut("D"); };
            cvPlan.SizeChanged += (s, e) => VeSoDo();
            ((Button)w.FindName("btnPick")).Click += (s, e) => { KiemSoLuong(); Ma = "pick"; w.Close(); };
            ((Button)w.FindName("btnOk")).Click += (s, e) => BamOk();
            ((Button)w.FindName("btnHuy")).Click += (s, e) => { KiemSoLuong(); w.Close(); };
            ((Button)w.FindName("btnDong")).Click += (s, e) => { KiemSoLuong(); w.Close(); };
            w.Loaded += (s, e) => { txtDai.Focus(); txtDai.SelectAll(); };
            CapNhat();
        }

        void T<K>(string ten, out K o) where K : class => o = (K)w.FindName(ten);

        static List<int> DocViTri(string s) =>
            (s ?? "").Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries)
                .Select(x => int.TryParse(x, out int i) ? i : 0).Where(i => i > 0).ToList();

        static int SoLuong(string s)
        {
            double? v = ChuDe.DocSo(s);
            return v == null ? 0 : Math.Max(0, (int)v.Value);
        }

        void DatBut(string b)
        {
            but = b;
            tgSo.IsChecked = b == "S";
            tgDi.IsChecked = b == "D";
        }

        void DatSoLuong()
        {
            dangDat = true;
            txtNs.Text = daNs = vs.Count.ToString();
            txtNd.Text = daNd = vd.Count.ToString();
            dangDat = false;
        }

        // Ô Số lượng vừa sửa: giữ các cửa đang có (bớt thì bỏ từ cuối), cửa thêm thì tự đặt (như vk:sua-sl)
        void KiemSoLuong()
        {
            string loai = txtNs.Text != daNs ? "S" : txtNd.Text != daNd ? "D" : null;
            if (loai == null) return;
            daNs = txtNs.Text; daNd = txtNd.Text;
            DatBut(loai);
            int ns = SoLuong(txtNs.Text), nd = SoLuong(txtNd.Text);
            if (kq != null)
            {
                vs = Vk.ViTri(kq, "S").Take(ns).ToList();
                vd = Vk.ViTri(kq, "D").Take(nd).ToList();
            }
            else { vs = vs.Take(ns).ToList(); vd = vd.Take(nd).ToList(); }
            CapNhat();
        }

        // Như vk:tich: vị trí cửa = các ô đang là cửa + / - ô i; bỏ tích thì "Ô tích sẽ là" chuyển theo loại cửa vừa bỏ
        void Tich(string loai, int i, bool bat)
        {
            if (!bat) DatBut(loai);
            if (kq != null)
            {
                List<int> so = Vk.ViTri(kq, "S"), di = Vk.ViTri(kq, "D");
                if (bat)
                {
                    if (loai == "S") { so.Remove(i); so.Add(i); so.Sort(); di.Remove(i); }
                    else { di.Remove(i); di.Add(i); di.Sort(); so.Remove(i); }
                }
                else if (loai == "S") so.Remove(i);
                else di.Remove(i);
                vs = so; vd = di;
                DatSoLuong();
            }
            CapNhat();
        }

        internal void BamO(int i)
        {
            KiemSoLuong();
            if (kq == null || i < 1 || i > kq.O.Count) return;
            string l = kq.O[i - 1].Loai;
            if (l == "S" || l == "D") Tich(l, i, false);
            else Tich(but, i, true);
        }

        internal string TenTuDat(double L) => TenBlock("VACH KINH " + ChuDe.So(L).Replace(",", "_"));

        // Trùng tên thì thêm " (2)"... (như vk:ten-block)
        string TenBlock(string goc)
        {
            string ten = goc;
            for (int i = 2; coBlock(ten); i++) ten = $"{goc} ({i})";
            return ten;
        }

        void CapNhat()
        {
            DatBut(but);
            double? L = ChuDe.DocSo(txtDai.Text), ws = ChuDe.DocSo(txtWs.Text), wd = ChuDe.DocSo(txtWd.Text);
            int ns = SoLuong(txtNs.Text), nd = SoLuong(txtNd.Text);
            bool datLai = false;
            kq = Vk.Chia(L, ns, ws, nd, wd, vs, vd, out loiChia);
            // vị trí đã tích không còn hợp (vd. vách ngắn đi, ít ô hơn) -> đặt lại tự động
            if (kq == null && (vs.Count > 0 || vd.Count > 0))
            {
                var kq2 = Vk.Chia(L, ns, ws, nd, wd, new List<int>(), new List<int>(), out _);
                if (kq2 != null) { kq = kq2; loiChia = null; vs = new List<int>(); vd = new List<int>(); datLai = true; }
            }

            string tn = (txtTen.Text ?? "").Trim();
            tenLoi = tn != "" && !tenHopLe(tn);
            lblTenTuDat.Text = tn == "" ? (L != null ? TenTuDat(L.Value) : "Để trống: tự đặt VACH KINH <dài>") : "";

            lblDo.Text = kq != null ? kq.Tam.Count.ToString() : "-";
            lblKinh.Text = kq != null ? kq.N.ToString() : "-";
            lblRong.Text = kq != null && kq.N > 0 ? ChuDe.So(kq.B) : "-";

            VeSoDo();
            VeBang();
            TrangThai(L, tn, datLai);
        }

        void TrangThai(double? L, string tn, bool datLai)
        {
            string s;
            bool loi = true;
            if (loiChia != null) s = loiChia;
            else if (tenLoi) s = "Tên có ký tự không dùng được trong tên block (< > / \\ \" : ; ? * | , = `)";
            else
            {
                loi = false;
                s = "Mỗi ô dưới 1200, đố 65.";
                if (datLai) s = "Vị trí cửa đã tích không còn hợp với số ô mới, đã đặt lại tự động.";
                else if (tn != "" && coBlock(tn)) s = $"Tên đã có trong bản vẽ, block sẽ đặt \"{TenBlock(tn)}\".";
                if (diemDai == null) s += " Chưa pick thì bấm Dựng vách sẽ hỏi điểm đặt.";
                else if (L != null && Math.Abs(L.Value - diemDai.Value) < 0.006) s += " Dựng đúng 2 điểm đã pick.";
                else s += " Chiều dài đã sửa tay: sẽ hỏi lại điểm đặt.";
            }
            lblTrangThai.Text = s;
            lblTrangThai.Foreground = ChuDe.Mau(w, loi ? "Di" : "Chu2");
        }

        void VeSoDo()
        {
            cvPlan.Children.Clear();
            double W = cvPlan.ActualWidth, H = cvPlan.ActualHeight;
            if (kq == null || W <= 0 || H <= 0) return;
            double L = kq.Tam[^1] + 32.5, le = 4, s = (W - 2 * le) / L, y = Math.Round(H * 0.46);
            Brush chu2 = ChuDe.Mau(w, "Chu2"), chu3 = ChuDe.Mau(w, "Chu3");
            for (int i = 0; i < kq.O.Count; i++)
            {
                var (loai, rong) = kq.O[i];
                double xa = le + kq.Tam[i] * s, xb = le + kq.Tam[i + 1] * s, cx = (xa + xb) / 2, r = xb - xa;
                if (loai == "K")
                    cvPlan.Children.Add(new Line { X1 = xa, X2 = xb, Y1 = y, Y2 = y, Stroke = ChuDe.Mau(w, "Kinh"), StrokeThickness = 2 });
                else
                {
                    Brush m = ChuDe.Mau(w, loai == "S" ? "So" : "Di");
                    ChuDe.Them(cvPlan, new Rectangle { Width = Math.Max(r, 1), Height = 10, Fill = m }, xa, y - 5);
                    if (loai == "D")
                    {
                        double dinh = Math.Max(2, y - 42);
                        cvPlan.Children.Add(new Line { X1 = xa, X2 = cx, Y1 = y - 5, Y2 = dinh, Stroke = m, StrokeThickness = 1.5 });
                        cvPlan.Children.Add(new Line { X1 = cx, X2 = xb, Y1 = dinh, Y2 = y - 5, Stroke = m, StrokeThickness = 1.5 });
                    }
                }
                if (r >= 42)
                {
                    ChuDe.ChuGiua(cvPlan, ChuDe.Chu(ChuDe.So(rong), chu2), cx, y + 22);
                    ChuDe.ChuGiua(cvPlan, ChuDe.Chu((i + 1).ToString(), chu3), cx, y + 37);
                }
                else if (r >= 13)
                {
                    // ô hẹp: số đo quay dọc, số ô bỏ qua cho khỏi chồng chữ
                    ChuDe.ChuGiua(cvPlan, ChuDe.Chu(ChuDe.So(rong), chu2, 10), cx, y + 30, -90);
                }
            }
            foreach (double c in kq.Tam)
                ChuDe.Them(cvPlan, new Rectangle { Width = 3, Height = 20, Fill = ChuDe.Mau(w, "Do_"), IsHitTestVisible = false },
                           le + c * s - 1.5, y - 10);
            // vùng bấm từng ô
            for (int i = 0; i < kq.O.Count; i++)
            {
                int o = i + 1;
                var r = new Rectangle
                {
                    Width = Math.Max((kq.Tam[i + 1] - kq.Tam[i]) * s, 1), Height = H, Fill = Brushes.Transparent, Cursor = Cursors.Hand,
                    ToolTip = $"Ô {o}: {TenLoai(kq.O[i].Loai)} {ChuDe.So(kq.O[i].Rong)}",
                };
                r.MouseLeftButtonUp += (a, e) => BamO(o);
                ChuDe.Them(cvPlan, r, le + kq.Tam[i] * s, 0);
            }
        }

        static string TenLoai(string l) => l == "S" ? "Cửa sổ mở" : l == "D" ? "Cửa đi" : "Kính";

        void VeBang()
        {
            spBang.Children.Clear();
            if (kq == null) return;
            Brush vien = ChuDe.Mau(w, "Rl");
            for (int i = 0; i < kq.O.Count; i++)
            {
                int o = i + 1;
                var (loai, rong) = kq.O[i];
                bool cua = loai != "K";
                var g = new Grid();
                g.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(36) });
                g.ColumnDefinitions.Add(new ColumnDefinition());
                g.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(86) });
                g.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(40) });

                var so = ChuDe.Chu(o.ToString(), ChuDe.Mau(w, "Chu"), 12);
                so.VerticalAlignment = VerticalAlignment.Center;
                g.Children.Add(so);

                var nhan = new Border
                {
                    Background = ChuDe.Mau(w, "Nhan" + loai), CornerRadius = new CornerRadius(3), Padding = new Thickness(7, 1, 7, 1),
                    HorizontalAlignment = HorizontalAlignment.Left, VerticalAlignment = VerticalAlignment.Center,
                    Child = ChuDe.Chu(TenLoai(loai), ChuDe.Mau(w, "Chu" + loai)),
                };
                Grid.SetColumn(nhan, 1);
                g.Children.Add(nhan);

                var rg = ChuDe.Chu(ChuDe.So(rong), ChuDe.Mau(w, "Chu"), 12);
                rg.HorizontalAlignment = HorizontalAlignment.Right;
                rg.VerticalAlignment = VerticalAlignment.Center;
                Grid.SetColumn(rg, 2);
                g.Children.Add(rg);

                var hop = new Border
                {
                    Width = 15, Height = 15, CornerRadius = new CornerRadius(3), BorderThickness = new Thickness(1),
                    BorderBrush = cua ? ChuDe.Mau(w, "Ac") : ChuDe.Mau(w, "Ck"),
                    Background = cua ? ChuDe.Mau(w, "Ac") : Brushes.Transparent,
                    HorizontalAlignment = HorizontalAlignment.Right, VerticalAlignment = VerticalAlignment.Center,
                };
                if (cua)
                    hop.Child = new Path
                    {
                        Data = Geometry.Parse("M5 12.5l4.5 4.5L19 7.5"), Stroke = Brushes.White, StrokeThickness = 2.2,
                        Width = 11, Height = 11, Stretch = Stretch.Uniform,
                        StrokeStartLineCap = PenLineCap.Round, StrokeEndLineCap = PenLineCap.Round,
                    };
                Grid.SetColumn(hop, 3);
                g.Children.Add(hop);

                var dong = new Border
                {
                    Child = g, Padding = new Thickness(10, 4, 10, 4), BorderBrush = vien, BorderThickness = new Thickness(0, 0, 0, 1),
                    Background = Brushes.Transparent, Cursor = Cursors.Hand, MinHeight = 27,
                };
                Brush nenO = ChuDe.Mau(w, "Pan2");
                dong.MouseEnter += (a, e) => dong.Background = nenO;
                dong.MouseLeave += (a, e) => dong.Background = Brushes.Transparent;
                dong.MouseLeftButtonUp += (a, e) => BamO(o);
                System.Windows.Automation.AutomationProperties.SetName(dong, $"Ô {o}");
                spBang.Children.Add(dong);
            }
        }

        void BamOk()
        {
            KiemSoLuong();
            CapNhat();
            if (kq != null && !tenLoi) { Ma = "ok"; w.Close(); }
        }

        internal bool CheDoToi => toi;

        // Trả về LISP: bộ nhớ bảng + kqs / kqd = vị trí cửa thật (kể cả cửa tự đặt) để LISP tính đúng như xem trước
        internal Dictionary<string, string> KetQua()
        {
            var r = new Dictionary<string, string>
            {
                ["ma"] = Ma, ["dai"] = txtDai.Text ?? "", ["ns"] = txtNs.Text ?? "0", ["ws"] = txtWs.Text ?? "",
                ["nd"] = txtNd.Text ?? "0", ["wd"] = txtWd.Text ?? "", ["lat"] = chkLat.IsChecked == true ? "1" : "0",
                ["ten"] = (txtTen.Text ?? "").Trim(), ["loaitich"] = but == "D" ? "rd" : "rs",
                ["vs"] = string.Join(",", vs), ["vd"] = string.Join(",", vd),
                ["theme"] = toi ? "dark" : "light",
            };
            if (kq != null)
            {
                r["kqs"] = string.Join(",", Vk.ViTri(kq, "S"));
                r["kqd"] = string.Join(",", Vk.ViTri(kq, "D"));
            }
            return r;
        }
    }
}
