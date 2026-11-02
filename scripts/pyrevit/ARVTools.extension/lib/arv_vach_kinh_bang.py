# -*- coding: utf-8 -*-
"""Bảng nhập Vách kính (WPF) cho nút ARV Tools > Vách kính. Bố cục theo bảng VK người dùng duyệt 2026-10-31
(BangVk.cs / BangVk.xaml của K-TOOL): sơ đồ mặt bằng trên cùng, nhập liệu trái, bảng các ô phải (bấm ô = tích /
bỏ tích cửa), thêm xem trước mặt đứng như MDVK. Phần tính lấy từ arv_vach_kinh (chia, tinh_cao) nên xem trước
khớp đúng với vách dựng ra.

Chạy được IronPython 2.7 (pyRevit) và CPython 3 (pythonnet) – chỉ dùng WPF thuần, không dùng pyrevit.forms.
"""
from __future__ import division, unicode_literals

import io
import os

import clr
clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")
clr.AddReference("WindowsBase")
clr.AddReference("System.Xaml")
from System.Windows import (Thickness, CornerRadius, GridLength, HorizontalAlignment, VerticalAlignment,
                            Visibility, Point, Size, SystemParameters)
from System.Windows.Controls import Canvas, Grid, ColumnDefinition, Border, TextBlock
from System.Windows.Markup import XamlReader
from System.Windows.Media import (SolidColorBrush, ColorConverter, Brushes, Geometry, RotateTransform, PenLineCap,
                                  Stretch)
from System.Windows.Shapes import Line, Rectangle, Path
from System.Windows.Input import Cursors
from System.Windows.Automation import AutomationProperties
from System.Windows.Interop import WindowInteropHelper

import arv_vach_kinh as vk

THU_MUC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vach_kinh")

TOI = {"Nen": "#23272E", "Pan": "#2C313A", "Pan2": "#353B46", "Ln": "#444C5A", "Chu": "#ECEFF4", "Chu2": "#A7AFBD",
       "Chu3": "#6F7888", "Tieude": "#1B1F25", "Chan": "#1F2329", "Fld": "#1B1F25", "Rl": "#3A414D", "Ck": "#6B7485",
       "So": "#4B9BFF", "Di": "#F0564F", "Ok": "#4FC38A", "Ac": "#3B82F6", "Kinh": "#8FB8D8", "Do_": "#ECEFF4",
       "NhanS": "#1F3A5F", "ChuS": "#9CC7FF", "NhanD": "#5A2523", "ChuD": "#FFB3AF", "NhanK": "#3A414D",
       "ChuK": "#C5CCD8"}
SANG = {"Nen": "#F5F6F8", "Pan": "#FFFFFF", "Pan2": "#EEF1F5", "Ln": "#D3D8E0", "Chu": "#1C2128", "Chu2": "#5B6573",
        "Chu3": "#8A93A1", "Tieude": "#E9ECF1", "Chan": "#EEF0F4", "Fld": "#FFFFFF", "Rl": "#E4E7EC", "Ck": "#9AA3B0",
        "So": "#1F6FE0", "Di": "#D8342C", "Ok": "#1D8A5A", "Ac": "#3B82F6", "Kinh": "#5B93B8", "Do_": "#2B3138",
        "NhanS": "#DCEBFF", "ChuS": "#12509F", "NhanD": "#FDE3E1", "ChuD": "#A3221C", "NhanK": "#E9ECF1",
        "ChuK": "#4A5360"}

MAC_DINH = {"goc": False, "cao": "", "ws": "1000", "hs": "1400", "co_ngang": True, "san": "50", "bau": "1400",
            "wd": "1665", "hd": "2700", "lat": False, "but": "S", "theme": "",
            "canh": [{"ten": "", "dai": "", "ns": "0", "nd": "0", "vs": [], "vd": []},
                     {"ten": "", "dai": "", "ns": "0", "nd": "0", "vs": [], "vd": []}]}


def co(hex_):
    b = SolidColorBrush(ColorConverter.ConvertFromString(hex_))
    b.Freeze()
    return b


def doc_xaml(ten):
    with io.open(os.path.join(THU_MUC, ten), encoding="utf-8") as f:
        return XamlReader.Parse(f.read())


def so_luong(s):
    v = vk.doc_so(s)
    return max(0, int(v)) if v is not None else 0


def ten_loai(l):
    return "Cửa sổ mở" if l == "S" else ("Cửa đi" if l == "D" else "Kính")


class BangVachKinh(object):
    """nho: bộ nhớ bảng (dict như MAC_DINH); dang_dung: tập tên vách (Mark) đã có; tien_to: "T1-" theo tầng;
    diem_dai: chiều dài các cánh đo từ điểm đã pick (None nếu chưa pick)."""

    def __init__(self, nho, dang_dung, tien_to, diem_dai=None, owner=None, toi=False):
        self.nho = dict(MAC_DINH)
        self.nho.update(nho or {})
        cu = list((nho or {}).get("canh") or [])
        self.nho["canh"] = []
        for i in range(2):
            c = dict(MAC_DINH["canh"][i])
            if i < len(cu):
                c.update(cu[i])
            self.nho["canh"].append(c)
        self.dang_dung = set(dang_dung or [])
        self.tien_to = tien_to or ""
        self.diem_dai = diem_dai
        self.ma = "huy"
        self.toi = toi if not self.nho.get("theme") else self.nho["theme"] == "dark"
        self.dang_dat = False
        self.canh_hien = 0
        self.kq = None
        self.loi_chia = None
        self.cao = None
        self.loi_cao = None

        w = doc_xaml("BangVachKinh.xaml")
        self.w = w
        w.Resources.MergedDictionaries.Add(doc_xaml("ChuDe.xaml"))
        self.dat_mau(self.toi)
        if SystemParameters.WorkArea.Height < w.Height:
            w.Height = SystemParameters.WorkArea.Height
        if owner:
            WindowInteropHelper(w).Owner = owner
        f = w.FindName
        for t in ("txtTen", "txtDai", "txtCao", "txtNs", "txtWs", "txtHs", "txtSan", "txtBau", "txtNd", "txtWd",
                  "txtHd", "chkGoc", "chkNgang", "chkLat", "tgCanh1", "tgCanh2", "bdCanh", "tgSo", "tgDi", "lblDo",
                  "lblKinh", "lblRong", "lblTrangThai", "lblTenTuDat", "lblDai", "lblPick", "lblCao", "lblSoDo",
                  "cvPlan", "cvMd", "spBang", "tgSang", "tgToi", "icSang", "icToi"):
            setattr(self, t, f(t))

        n = self.nho
        self.dang_dat = True
        self.txtCao.Text = n["cao"]
        self.txtWs.Text, self.txtHs.Text, self.txtWd.Text, self.txtHd.Text = n["ws"], n["hs"], n["wd"], n["hd"]
        self.txtSan.Text, self.txtBau.Text = n["san"], n["bau"]
        self.chkNgang.IsChecked = bool(n["co_ngang"])
        self.chkLat.IsChecked = bool(n["lat"])
        self.chkGoc.IsChecked = bool(n["goc"])
        self.nap_canh(0)
        self.dang_dat = False
        self.but = n.get("but") or "S"

        for t in (self.txtDai, self.txtCao, self.txtWs, self.txtHs, self.txtSan, self.txtBau, self.txtWd, self.txtHd,
                  self.txtTen):
            t.TextChanged += self.doi_chu
            t.GotKeyboardFocus += self.chon_het
        for t in (self.txtNs, self.txtNd):
            t.LostKeyboardFocus += lambda s, e: self.kiem_so_luong()
            t.GotKeyboardFocus += self.chon_het
        for c in (self.chkNgang, self.chkLat):
            c.Click += lambda s, e: self.cap_nhat()
        self.chkGoc.Click += lambda s, e: self.doi_goc()
        self.tgCanh1.Click += lambda s, e: self.doi_canh(0)
        self.tgCanh2.Click += lambda s, e: self.doi_canh(1)
        self.tgSo.Click += lambda s, e: (self.kiem_so_luong(), self.dat_but("S"))
        self.tgDi.Click += lambda s, e: (self.kiem_so_luong(), self.dat_but("D"))
        self.tgSang.Click += lambda s, e: self.doi_che_do(False)
        self.tgToi.Click += lambda s, e: self.doi_che_do(True)
        self.cvPlan.SizeChanged += lambda s, e: self.ve_so_do()
        self.cvMd.SizeChanged += lambda s, e: self.ve_mat_dung()
        f("btnPick").Click += lambda s, e: self.dong("pick")
        f("btnOk").Click += lambda s, e: self.bam_ok()
        f("btnHuy").Click += lambda s, e: self.dong("huy")
        f("btnDong").Click += lambda s, e: self.dong("huy")
        w.Loaded += lambda s, e: (self.chon_che_do(self.toi), self.txtDai.Focus(), self.txtDai.SelectAll())
        self.cap_nhat()

    # ------------------------------------------------------------ màu
    def dat_mau(self, toi):
        for k, v in (TOI if toi else SANG).items():
            self.w.Resources[k] = co(v)

    def mau(self, k):
        return self.w.Resources[k]

    def chon_che_do(self, toi):
        self.toi = toi
        self.tgSang.IsChecked = not toi
        self.tgToi.IsChecked = toi
        self.icSang.Stroke = self.mau("Chu2") if toi else Brushes.White
        self.icToi.Stroke = Brushes.White if toi else self.mau("Chu2")

    def doi_che_do(self, toi):
        self.dat_mau(toi)
        self.chon_che_do(toi)
        self.cap_nhat()

    # ------------------------------------------------------------ cánh
    def chon_het(self, s, e):
        s.SelectAll()

    def luu_canh(self):
        c = self.nho["canh"][self.canh_hien]
        c["ten"], c["dai"], c["ns"], c["nd"] = self.txtTen.Text, self.txtDai.Text, self.txtNs.Text, self.txtNd.Text

    def nap_canh(self, i):
        self.canh_hien = i
        c = self.nho["canh"][i]
        dd = self.dang_dat
        self.dang_dat = True
        self.txtTen.Text, self.txtDai.Text, self.txtNs.Text, self.txtNd.Text = c["ten"], c["dai"], c["ns"], c["nd"]
        self.dang_dat = dd
        self.da_ns, self.da_nd = self.txtNs.Text, self.txtNd.Text

    def doi_canh(self, i):
        self.kiem_so_luong()
        self.luu_canh()
        self.nap_canh(i)
        self.cap_nhat()

    def doi_goc(self):
        self.kiem_so_luong()
        self.luu_canh()
        if not self.chkGoc.IsChecked:
            self.nap_canh(0)
        self.cap_nhat()

    @property
    def goc(self):
        return bool(self.chkGoc.IsChecked)

    def dau(self):
        return vk.NUA_GOC if self.goc else vk.NUA

    # ------------------------------------------------------------ tích ô (như BangVk.cs)
    def dat_but(self, b):
        self.but = b
        self.tgSo.IsChecked = b == "S"
        self.tgDi.IsChecked = b == "D"

    def canh(self):
        return self.nho["canh"][self.canh_hien]

    def dat_so_luong(self):
        c = self.canh()
        self.dang_dat = True
        self.txtNs.Text = self.da_ns = c["ns"] = "%d" % len(c["vs"])
        self.txtNd.Text = self.da_nd = c["nd"] = "%d" % len(c["vd"])
        self.dang_dat = False

    def kiem_so_luong(self):
        loai = "S" if self.txtNs.Text != self.da_ns else ("D" if self.txtNd.Text != self.da_nd else None)
        if loai is None:
            return
        self.da_ns, self.da_nd = self.txtNs.Text, self.txtNd.Text
        self.dat_but(loai)
        c = self.canh()
        ns, nd = so_luong(self.txtNs.Text), so_luong(self.txtNd.Text)
        if self.kq is not None:
            c["vs"] = vk.vi_tri(self.kq, "S")[:ns]
            c["vd"] = vk.vi_tri(self.kq, "D")[:nd]
        else:
            c["vs"], c["vd"] = c["vs"][:ns], c["vd"][:nd]
        self.luu_canh()
        self.cap_nhat()

    def tich(self, loai, i, bat):
        if not bat:
            self.dat_but(loai)
        if self.kq is not None:
            s, d = vk.vi_tri(self.kq, "S"), vk.vi_tri(self.kq, "D")
            if bat:
                if loai == "S":
                    s = sorted(set(s) | {i})
                    d = [x for x in d if x != i]
                else:
                    d = sorted(set(d) | {i})
                    s = [x for x in s if x != i]
            elif loai == "S":
                s = [x for x in s if x != i]
            else:
                d = [x for x in d if x != i]
            c = self.canh()
            c["vs"], c["vd"] = s, d
            self.dat_so_luong()
        self.cap_nhat()

    def bam_o(self, i):
        self.kiem_so_luong()
        if self.kq is None or i < 1 or i > len(self.kq["o"]):
            return
        l = self.kq["o"][i - 1][0]
        if l in ("S", "D"):
            self.tich(l, i, False)
        else:
            self.tich(self.but, i, True)

    # ------------------------------------------------------------ tính
    def doi_chu(self, s, e):
        if not self.dang_dat:
            self.luu_canh()
            self.cap_nhat()

    def chia_canh(self, i):
        """Chia 1 cánh theo dữ liệu đã lưu; vị trí tích không còn hợp thì đặt lại tự động. Trả (kq, lỗi, đặt lại)."""
        c = self.nho["canh"][i]
        L, ws, wd = vk.doc_so(c["dai"]), vk.doc_so(self.txtWs.Text), vk.doc_so(self.txtWd.Text)
        ns, nd = so_luong(c["ns"]), so_luong(c["nd"])
        kq, loi = vk.chia(L, ns, ws, nd, wd, c["vs"], c["vd"], self.dau())
        dat_lai = False
        if kq is None and (c["vs"] or c["vd"]):
            kq2, _ = vk.chia(L, ns, ws, nd, wd, [], [], self.dau())
            if kq2 is not None:
                kq, loi, dat_lai = kq2, None, True
                c["vs"], c["vd"] = [], []
        if kq is not None and self.goc and i == 1 and kq["o"][0][0] != "K":
            loi = "Cánh 2: ô 1 sát góc là kính góc, không đặt cửa vào ô này"
        return kq, loi, dat_lai

    def ds_canh(self):
        return [0, 1] if self.goc else [0]

    def tinh_cao(self):
        co_di = any(so_luong(self.nho["canh"][i]["nd"]) > 0 for i in self.ds_canh())
        co_so = any(so_luong(self.nho["canh"][i]["ns"]) > 0 for i in self.ds_canh())
        return vk.tinh_cao(vk.doc_so(self.txtCao.Text), co_di, vk.doc_so(self.txtHd.Text), co_so,
                           vk.doc_so(self.txtHs.Text), bool(self.chkNgang.IsChecked), vk.doc_so(self.txtSan.Text),
                           vk.doc_so(self.txtBau.Text))

    def ten_tu_dat(self):
        """Tên tự đặt cho các cánh để trống (theo thứ tự cánh)."""
        trong = [i for i in self.ds_canh() if not self.nho["canh"][i]["ten"].strip()]
        return dict(zip(trong, vk.ten_tu_dat(self.dang_dung, self.tien_to, len(trong))))

    def cap_nhat(self):
        self.dat_but(self.but)
        goc = self.goc
        self.bdCanh.Visibility = Visibility.Visible if goc else Visibility.Collapsed
        self.tgCanh1.IsChecked = self.canh_hien == 0
        self.tgCanh2.IsChecked = self.canh_hien == 1
        self.lblPick.Text = "Pick 3 điểm" if goc else "Pick 2 điểm"
        self.lblDai.Text = ("Chiều dài cánh %d (mm, góc ngoài - mép ngoài đầu cánh)" % (self.canh_hien + 1)
                            if goc else "Chiều dài vách (mm, mép ngoài - mép ngoài)")
        self.lblSoDo.Text = ("Cánh %d, từ góc ra đầu cánh. Bấm vào ô để tích / bỏ tích cửa" % (self.canh_hien + 1)
                             if goc else "Mặt bằng vách, trái sang phải. Bấm vào ô để tích / bỏ tích cửa")
        self.kq, self.loi_chia, dat_lai = self.chia_canh(self.canh_hien)
        self.cao, self.loi_cao = self.tinh_cao()
        tu = self.ten_tu_dat()
        c = self.canh()
        self.lblTenTuDat.Text = (tu.get(self.canh_hien, "") + "  (tự đặt)") if not c["ten"].strip() else ""
        kq = self.kq
        self.lblDo.Text = "%d" % len(kq["tam"]) if kq else "-"
        self.lblKinh.Text = "%d" % kq["n"] if kq else "-"
        self.lblRong.Text = vk.so(kq["b"]) if kq and kq["n"] > 0 else "-"
        if self.cao:
            ds = ["đố ngang %s" % vk.so(z - vk.NUA) for z, _ in self.cao["ngang"]]
            if self.cao["so"]:
                ds.append("cửa sổ %s - %s" % (vk.so(self.cao["so"][0]), vk.so(self.cao["so"][1])))
            if self.cao["di_tren"] is not None:
                ds.append("cửa đi cao %s" % vk.so(self.cao["di_tren"]))
            self.lblCao.Text = ("Cao độ (mặt dưới, từ sàn): " + "; ".join(ds)) if ds else ""
        else:
            self.lblCao.Text = ""
        self.ve_so_do()
        self.ve_bang()
        self.ve_mat_dung()
        self.trang_thai(dat_lai)

    def loi_tong(self):
        """Lỗi chặn nút Dựng vách (mọi cánh)."""
        for i in self.ds_canh():
            kq, loi, _ = self.chia_canh(i)
            if loi:
                return ("Cánh %d: " % (i + 1) if self.goc else "") + loi
        _, loi = self.tinh_cao()
        return loi

    def trang_thai(self, dat_lai):
        loi = self.loi_chia or self.loi_cao
        if loi is None and self.goc:
            khac = 1 - self.canh_hien
            _, l2, _ = self.chia_canh(khac)
            if l2:
                loi = "Cánh %d: %s" % (khac + 1, l2)
        if loi:
            s = loi
        else:
            s = "Mỗi ô dưới 1200, đố 65."
            if dat_lai:
                s = "Vị trí cửa đã tích không còn hợp với số ô mới, đã đặt lại tự động."
            t = self.canh()["ten"].strip()
            if t and t in self.dang_dung:
                s += " Tên đã có: sẽ đặt \"%s\"." % vk.ten_khong_trung(t, self.dang_dung)
            if self.cao and self.cao["ghi_chu"]:
                s += " " + "; ".join(self.cao["ghi_chu"]).capitalize() + "."
            if self.diem_dai is None:
                s += " Chưa pick thì bấm Dựng vách sẽ hỏi điểm đặt."
            elif self.khop_diem():
                s += " Dựng đúng các điểm đã pick."
            else:
                s += " Chiều dài đã sửa tay: sẽ hỏi lại điểm đặt."
        self.lblTrangThai.Text = s
        self.lblTrangThai.Foreground = self.mau("Di" if loi else "Chu2")

    def khop_diem(self):
        if not self.diem_dai or len(self.diem_dai) != len(self.ds_canh()):
            return False
        for i, d in zip(self.ds_canh(), self.diem_dai):
            L = vk.doc_so(self.nho["canh"][i]["dai"])
            if L is None or abs(L - d) > 0.006:
                return False
        return True

    # ------------------------------------------------------------ vẽ
    def _them(self, cv, e, x, y):
        Canvas.SetLeft(e, x)
        Canvas.SetTop(e, y)
        cv.Children.Add(e)

    def _chu(self, s, mau, co_chu=11):
        t = TextBlock()
        t.Text, t.Foreground, t.FontSize, t.IsHitTestVisible = s, mau, co_chu, False
        return t

    def _chu_giua(self, cv, t, x, y, goc=0):
        t.Measure(Size(1e6, 1e6))
        z = t.DesiredSize
        if goc:
            t.RenderTransformOrigin = Point(0.5, 0.5)
            t.RenderTransform = RotateTransform(goc)
        self._them(cv, t, x - z.Width / 2, y - z.Height / 2)

    def _line(self, cv, x1, y1, x2, y2, mau, day=1.0):
        l = Line()
        l.X1, l.Y1, l.X2, l.Y2, l.Stroke, l.StrokeThickness, l.IsHitTestVisible = x1, y1, x2, y2, mau, day, False
        cv.Children.Add(l)

    def _hcn(self, cv, x, y, w, h, nen, vien=None, bam=None):
        r = Rectangle()
        r.Width, r.Height, r.Fill = max(w, 1), max(h, 1), nen
        if vien is not None:
            r.Stroke, r.StrokeThickness = vien, 1
        r.IsHitTestVisible = bam is not None
        self._them(cv, r, x, y)
        return r

    def ve_so_do(self):
        cv = self.cvPlan
        cv.Children.Clear()
        W, H = cv.ActualWidth, cv.ActualHeight
        kq = self.kq
        if kq is None or W <= 0 or H <= 0:
            return
        L = kq["tam"][-1] + vk.NUA
        le = 4.0
        s = (W - 2 * le) / L
        y = round(H * 0.46)
        chu2, chu3 = self.mau("Chu2"), self.mau("Chu3")
        for i, (loai, rong) in enumerate(kq["o"]):
            xa, xb = le + kq["tam"][i] * s, le + kq["tam"][i + 1] * s
            cx, r = (xa + xb) / 2, xb - xa
            if loai == "K":
                self._line(cv, xa, y, xb, y, self.mau("Kinh"), 2)
            else:
                m = self.mau("So" if loai == "S" else "Di")
                self._hcn(cv, xa, y - 5, r, 10, m)
                if loai == "D":
                    dinh = max(2, y - 42)
                    self._line(cv, xa, y - 5, cx, dinh, m, 1.5)
                    self._line(cv, cx, dinh, xb, y - 5, m, 1.5)
            if r >= 42:
                self._chu_giua(cv, self._chu(vk.so(rong), chu2), cx, y + 22)
                self._chu_giua(cv, self._chu("%d" % (i + 1), chu3), cx, y + 37)
            elif r >= 13:
                self._chu_giua(cv, self._chu(vk.so(rong), chu2, 10), cx, y + 30, -90)
        do = self.mau("Do_")
        for j, c in enumerate(kq["tam"]):
            if j == 0 and self.goc:
                if self.canh_hien == 0:      # đố góc 150
                    self._hcn(cv, le, y - 10, vk.GOC * s, 20, do)
                else:                        # kính góc: đố góc thuộc cánh 1
                    self._hcn(cv, le, y - 10, vk.GOC * s, 20, Brushes.Transparent, do)
                continue
            self._hcn(cv, le + c * s - 1.5, y - 10, 3, 20, do)
        for i in range(len(kq["o"])):
            o = i + 1
            r = self._hcn(cv, le + kq["tam"][i] * s, 0, (kq["tam"][i + 1] - kq["tam"][i]) * s, H, Brushes.Transparent,
                          bam=True)
            r.Cursor = Cursors.Hand
            r.ToolTip = "Ô %d: %s %s" % (o, ten_loai(kq["o"][i][0]), vk.so(kq["o"][i][1]))
            r.MouseLeftButtonUp += (lambda oo: (lambda a, e: self.bam_o(oo)))(o)

    def ve_bang(self):
        sp = self.spBang
        sp.Children.Clear()
        kq = self.kq
        if kq is None:
            return
        vien = self.mau("Rl")
        for i, (loai, rong) in enumerate(kq["o"]):
            o = i + 1
            cua = loai != "K"
            g = Grid()
            for wdt in (36, None, 86, 40):
                cd = ColumnDefinition()
                if wdt:
                    cd.Width = GridLength(wdt)
                g.ColumnDefinitions.Add(cd)
            t = self._chu("%d" % o, self.mau("Chu"), 12)
            t.VerticalAlignment = VerticalAlignment.Center
            g.Children.Add(t)
            nhan = Border()
            nhan.Background, nhan.CornerRadius, nhan.Padding = self.mau("Nhan" + loai), CornerRadius(3), Thickness(7, 1, 7, 1)
            nhan.HorizontalAlignment, nhan.VerticalAlignment = HorizontalAlignment.Left, VerticalAlignment.Center
            ten = ten_loai(loai)
            if loai == "K" and self.goc and self.canh_hien == 1 and i == 0:
                ten = "Kính góc"
            nhan.Child = self._chu(ten, self.mau("Chu" + loai))
            Grid.SetColumn(nhan, 1)
            g.Children.Add(nhan)
            rg = self._chu(vk.so(rong), self.mau("Chu"), 12)
            rg.HorizontalAlignment, rg.VerticalAlignment = HorizontalAlignment.Right, VerticalAlignment.Center
            Grid.SetColumn(rg, 2)
            g.Children.Add(rg)
            hop = Border()
            hop.Width = hop.Height = 15
            hop.CornerRadius, hop.BorderThickness = CornerRadius(3), Thickness(1)
            hop.BorderBrush = self.mau("Ac") if cua else self.mau("Ck")
            hop.Background = self.mau("Ac") if cua else Brushes.Transparent
            hop.HorizontalAlignment, hop.VerticalAlignment = HorizontalAlignment.Right, VerticalAlignment.Center
            if cua:
                pth = Path()
                pth.Data = Geometry.Parse("M5 12.5l4.5 4.5L19 7.5")
                pth.Stroke, pth.StrokeThickness, pth.Width, pth.Height = Brushes.White, 2.2, 11, 11
                pth.Stretch = Stretch.Uniform
                pth.StrokeStartLineCap = pth.StrokeEndLineCap = PenLineCap.Round
                hop.Child = pth
            Grid.SetColumn(hop, 3)
            g.Children.Add(hop)
            dong = Border()
            dong.Child, dong.Padding = g, Thickness(10, 4, 10, 4)
            dong.BorderBrush, dong.BorderThickness = vien, Thickness(0, 0, 0, 1)
            dong.Background, dong.Cursor, dong.MinHeight = Brushes.Transparent, Cursors.Hand, 27
            nen_o = self.mau("Pan2")
            dong.MouseEnter += (lambda d: (lambda a, e: setattr(d, "Background", nen_o)))(dong)
            dong.MouseLeave += (lambda d: (lambda a, e: setattr(d, "Background", Brushes.Transparent)))(dong)
            dong.MouseLeftButtonUp += (lambda oo: (lambda a, e: self.bam_o(oo)))(o)
            AutomationProperties.SetName(dong, "Ô %d" % o)
            sp.Children.Add(dong)

    def ve_mat_dung(self):
        """Mặt đứng cánh đang xem: đố, khung, đố ngang (bỏ đoạn qua cửa), cửa đi (hình thoi), cửa sổ hất (chữ V)."""
        cv = self.cvMd
        cv.Children.Clear()
        W, Hc = cv.ActualWidth, cv.ActualHeight
        kq, cao = self.kq, self.cao
        H = vk.doc_so(self.txtCao.Text)
        if kq is None or cao is None or not H or W <= 0 or Hc <= 0:
            return
        L = kq["tam"][-1] + vk.NUA
        s = min((W - 8) / L, (Hc - 8) / H)
        x0 = (W - L * s) / 2
        y0 = Hc - (Hc - H * s) / 2

        def X(x):
            return x0 + x * s

        def Y(z):
            return y0 - z * s
        do, kinh = self.mau("Do_"), self.mau("Kinh")
        mS, mD = self.mau("So"), self.mau("Di")
        tam, o, d = kq["tam"], kq["o"], vk.DO
        for i, (loai, r) in enumerate(o):
            # mép trong 2 đố của ô; ô 1 vách góc: sau đố góc 150 (cánh 1) / sát góc (cánh 2, kính góc)
            if i > 0:
                xa = tam[i] + vk.NUA
            elif self.goc:
                xa = vk.GOC if self.canh_hien == 0 else 0.0
            else:
                xa = d
            xb = tam[i + 1] - vk.NUA
            # thanh ngang trong ô: khung trên, khung dưới (trừ cửa đi), đố ngang suốt (trừ đoạn qua cửa), đố dưới cửa sổ
            bars = [(H - d, H)]
            if loai != "D":
                bars.append((0, d))
            for zc, nguon in cao["ngang"]:
                if loai == "D" and cao["di_tren"] is not None and zc - vk.NUA < cao["di_tren"] - 1e-6:
                    continue
                if loai == "S" and cao["so"] and cao["so"][0] - 1e-6 < zc < cao["so"][1] + d - 1e-6 and nguon != "S":
                    continue
                bars.append((zc - vk.NUA, zc + vk.NUA))
            if loai == "S" and cao["so"]:
                bars.append((cao["duoi"] - vk.NUA, cao["duoi"] + vk.NUA))
            bars.sort()
            for z1, z2 in bars:
                self._hcn(cv, X(xa), Y(z2), (xb - xa) * s, (z2 - z1) * s, do)
            # ô kính giữa 2 thanh liên tiếp
            for k in range(len(bars) - 1):
                z1, z2 = bars[k][1], bars[k + 1][0]
                if z2 - z1 > 1:
                    self._hcn(cv, X(xa), Y(z2), (xb - xa) * s, (z2 - z1) * s, Brushes.Transparent, kinh)
            if loai == "D" and cao["di_tren"] is not None:
                zt = cao["di_tren"]
                cx = (xa + xb) / 2
                self._hcn(cv, X(xa), Y(zt), (xb - xa) * s, zt * s, Brushes.Transparent, mD)
                self._line(cv, X(cx), Y(zt), X(cx), Y(0), mD, 1)
                for xx in (xa, xb):           # 2 cánh mở: hình thoi
                    self._line(cv, X(xx), Y(zt / 2), X(cx), Y(zt), mD, 1)
                    self._line(cv, X(xx), Y(zt / 2), X(cx), Y(0), mD, 1)
            if loai == "S" and cao["so"]:
                z1, z2 = cao["so"]
                self._hcn(cv, X(xa), Y(z2), (xb - xa) * s, (z2 - z1) * s, Brushes.Transparent, mS)
                cx = (xa + xb) / 2
                self._line(cv, X(xa), Y(z1), X(cx), Y(z2), mS, 1)
                self._line(cv, X(xb), Y(z1), X(cx), Y(z2), mS, 1)
        # đố đứng chạy suốt
        for j, c in enumerate(tam):
            if j == 0 and self.goc:
                if self.canh_hien == 0:
                    self._hcn(cv, X(0), Y(H), vk.GOC * s, H * s, do)
                continue
            self._hcn(cv, X(c - vk.NUA), Y(H), d * s, H * s, do)

    # ------------------------------------------------------------ kết thúc
    def bam_ok(self):
        self.kiem_so_luong()
        self.luu_canh()
        self.cap_nhat()
        loi = self.loi_tong()
        if loi:
            self.lblTrangThai.Text = loi
            self.lblTrangThai.Foreground = self.mau("Di")
            return
        self.dong("ok")

    def dong(self, ma):
        self.kiem_so_luong()
        self.luu_canh()
        self.ma = ma
        self.w.Close()

    def hien(self):
        self.w.ShowDialog()
        return self.ket_qua()

    def ket_qua(self):
        n = self.nho
        n.update({"goc": self.goc, "cao": self.txtCao.Text, "ws": self.txtWs.Text, "hs": self.txtHs.Text,
                  "co_ngang": bool(self.chkNgang.IsChecked), "san": self.txtSan.Text, "bau": self.txtBau.Text,
                  "wd": self.txtWd.Text, "hd": self.txtHd.Text, "lat": bool(self.chkLat.IsChecked), "but": self.but,
                  "theme": "dark" if self.toi else "light"})
        cfg = None
        if self.ma == "ok":
            tu = self.ten_tu_dat()
            canh = []
            for i in self.ds_canh():
                c = n["canh"][i]
                kq, _, _ = self.chia_canh(i)
                canh.append({"ten": c["ten"].strip() or tu.get(i, ""), "L": vk.doc_so(c["dai"]),
                             "ns": so_luong(c["ns"]), "nd": so_luong(c["nd"]),
                             "vs": vk.vi_tri(kq, "S"), "vd": vk.vi_tri(kq, "D")})
            cfg = {"goc": self.goc, "H": vk.doc_so(self.txtCao.Text), "ws": vk.doc_so(self.txtWs.Text),
                   "wd": vk.doc_so(self.txtWd.Text), "hd": vk.doc_so(self.txtHd.Text),
                   "hs": vk.doc_so(self.txtHs.Text), "co_ngang": bool(self.chkNgang.IsChecked),
                   "san": vk.doc_so(self.txtSan.Text), "bau": vk.doc_so(self.txtBau.Text),
                   "lat": bool(self.chkLat.IsChecked), "canh": canh}
        return {"ma": self.ma, "nho": n, "cfg": cfg}
