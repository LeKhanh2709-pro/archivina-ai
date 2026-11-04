# -*- coding: utf-8 -*-
# Hộp thoại hỏi trước khi chạy nút "Định vị + tag cửa" (người dùng yêu cầu 2026-11-03): có đặt mặt bằng lên bản vẽ không,
# giai đoạn nào, hạng mục nào (gõ tên mới = thêm hạng mục), khổ giấy A1 / A0 (khung tên theo khổ), số hiệu + tên bản vẽ.
# Trả về {chỉ số IN: giá trị} cho core.py (IN[21] – IN[27] của TagCua_TuDong.py) hoặc None nếu Huỷ.
# Cấp nhóm sheet đọc từ Project Browser của dự án đang mở (giống cap_thu_muc_sheet / ts_giai_doan trong core.py: sửa
# quy tắc ở đây thì sửa cả core.py). Lựa chọn lần trước nhớ ở %APPDATA%\pyRevit\ARVTools\TagCua_sheet.json.
import io
import os
import re
import json
import unicodedata

import clr
clr.AddReference("RevitAPI")
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")
import Autodesk.Revit.DB as DB
from System.Windows.Forms import (Form, Label, ComboBox, ComboBoxStyle, TextBox, CheckBox, Button, DialogResult,
                                  FormStartPosition, FormBorderStyle)
from System.Drawing import Size, Point, Font

_LUU = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "pyRevit", "ARVTools", "TagCua_sheet.json")


def _khong_dau(s):
    s = unicodedata.normalize("NFD", u"{}".format(s or u"")).replace(u"đ", u"d").replace(u"Đ", u"D")
    return u"".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def _ten(e):
    try:
        return DB.Element.Name.GetValue(e)
    except Exception:
        pass
    try:
        p_ = e.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM) or e.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME)
        if p_ is not None and p_.AsString():
            return p_.AsString()
    except Exception:
        pass
    try:
        return e.Name
    except Exception:
        return u"?"


def _ts(e, pid):
    for prm in e.Parameters:
        if prm.Id.Value == pid.Value:
            return prm
    return None


def _gt(prm):
    try:
        return (prm.AsString() or u"") if prm.StorageType == DB.StorageType.String else (prm.AsValueString() or u"")
    except Exception:
        return u""


def _cap(doc):
    try:
        bo = DB.BrowserOrganization.GetCurrentBrowserOrganizationForSheets(doc)
    except Exception:
        return []
    for s in DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet):
        try:
            items = list(bo.GetFolderItems(s.Id))
        except Exception:
            continue
        if items:
            return [it.ElementId for it in items]
    return []


def _gd_hm(doc):
    cap = _cap(doc)
    if len(cap) >= 2:
        return cap[0], cap[1]
    hm = cap[0] if cap else None
    dem = {}            # tham số sheet có chữ "giai đoạn" → số sheet có giá trị (chọn tham số đang dùng nhiều nhất)
    for s in DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet):
        for prm in s.Parameters:
            if prm.Definition is not None and prm.StorageType == DB.StorageType.String and \
                    u"giai doan" in _khong_dau(prm.Definition.Name) and (hm is None or prm.Id.Value != hm.Value):
                k = prm.Id.Value
                dem.setdefault(k, [prm.Id, 0])
                if prm.AsString():
                    dem[k][1] += 1
    gd = max(dem.values(), key=lambda x: x[1])[0] if dem else None
    return gd, hm


def _so_tiep(sheets, pid_gd, gd, pid_hm, hm):
    dung = set(s.SheetNumber for s in sheets)
    cung = []
    for s in sheets:
        if pid_hm is None or not hm:
            continue
        p_ = _ts(s, pid_hm)
        if p_ is None or _gt(p_) != hm:
            continue
        if pid_gd is not None and gd:
            q_ = _ts(s, pid_gd)
            if q_ is not None and _gt(q_) and _gt(q_) != gd:
                continue
        cung.append(s.SheetNumber)
    goc = None
    for so in sorted(cung):
        if re.search(r"\d+$", so):
            goc = so
    if goc is None:
        return u""
    m = re.search(r"(\d+)$", goc)
    dau, n, w = goc[:m.start()], int(m.group(1)), len(m.group(1))
    while True:
        n += 1
        ung = u"%s%0*d" % (dau, w, n)
        if ung not in dung:
            return ung


def _doc_luu():
    try:
        with io.open(_LUU, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _ghi_luu(d):
    try:
        if not os.path.isdir(os.path.dirname(_LUU)):
            os.makedirs(os.path.dirname(_LUU))
        with io.open(_LUU, "w", encoding="utf-8") as f:
            f.write(json.dumps(d, ensure_ascii=False))
    except Exception:
        pass


def hoi(doc, view):
    sheets = list(DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet))
    pid_gd, pid_hm = _gd_hm(doc)
    cap_hm = {}                     # giai đoạn → [hạng mục]
    for s in sheets:
        g = _gt(_ts(s, pid_gd)) if pid_gd is not None and _ts(s, pid_gd) is not None else u""
        h = _gt(_ts(s, pid_hm)) if pid_hm is not None and _ts(s, pid_hm) is not None else u""
        if h:
            cap_hm.setdefault(g, set()).add(h)
            cap_hm.setdefault(u"*", set()).add(h)
    ds_gd = sorted(k for k in cap_hm if k not in (u"*", u""))
    khung = list(DB.FilteredElementCollector(doc).OfClass(DB.FamilySymbol).OfCategory(DB.BuiltInCategory.OST_TitleBlocks))
    ten_khung = [u"%s : %s" % (s.FamilyName, _ten(s)) for s in khung]
    tang = view.GenLevel.Name if view.GenLevel is not None else view.Name
    luu = _doc_luu()

    f = Form()
    f.Text = u"Định vị + tag cửa – đặt lên bản vẽ"
    f.StartPosition = FormStartPosition.CenterScreen
    f.FormBorderStyle = FormBorderStyle.FixedDialog
    f.MaximizeBox = False
    f.MinimizeBox = False
    f.Font = Font("Segoe UI", 9.0)
    f.ClientSize = Size(610, 330)
    y = [14]

    def dong(nhan, ctl):
        lb = Label()
        lb.Text = nhan
        lb.Location = Point(14, y[0] + 3)
        lb.Size = Size(200, 22)
        ctl.Location = Point(220, y[0])
        ctl.Size = Size(370, 24)
        f.Controls.Add(lb)
        f.Controls.Add(ctl)
        y[0] += 34

    chk = CheckBox()
    chk.Text = u"Đặt mặt bằng định vị cửa lên bản vẽ (kèm bảng thống kê cửa đi / cửa sổ)"
    chk.Location = Point(14, y[0])
    chk.Size = Size(530, 24)
    chk.Checked = bool(luu.get("dat", True))
    f.Controls.Add(chk)
    y[0] += 34
    cb_gd = ComboBox()
    cb_gd.DropDownStyle = ComboBoxStyle.DropDown
    for g in ds_gd:
        cb_gd.Items.Add(g)
    dong(u"Giai đoạn:" if pid_gd is not None else u"Giai đoạn (không có):", cb_gd)
    cb_gd.Enabled = pid_gd is not None
    cb_hm = ComboBox()
    cb_hm.DropDownStyle = ComboBoxStyle.DropDown
    dong(u"Hạng mục (gõ tên mới = thêm):", cb_hm)
    cb_kho = ComboBox()
    cb_kho.DropDownStyle = ComboBoxStyle.DropDownList
    for k in (u"A1", u"A0"):
        cb_kho.Items.Add(k)
    dong(u"Khổ giấy:", cb_kho)
    cb_kt = ComboBox()
    cb_kt.DropDownStyle = ComboBoxStyle.DropDownList
    dong(u"Khung tên:", cb_kt)
    tb_so = TextBox()
    dong(u"Số hiệu bản vẽ:", tb_so)
    tb_ten = TextBox()
    tb_ten.Text = u"MẶT BẰNG ĐỊNH VỊ CỬA %s" % tang.upper()
    dong(u"Tên bản vẽ:", tb_ten)
    so_tay = [False]

    def nap_hm(*a):
        g = u"%s" % (cb_gd.Text or u"")
        cu = u"%s" % (cb_hm.Text or u"")
        cb_hm.Items.Clear()
        for h in sorted(cap_hm.get(g, cap_hm.get(u"*", set())) if g else cap_hm.get(u"*", set())):
            cb_hm.Items.Add(h)
        cb_hm.Text = cu

    def goi_y_so(*a):
        if not so_tay[0]:
            tb_so.Text = _so_tiep(sheets, pid_gd, u"%s" % (cb_gd.Text or u""), pid_hm, u"%s" % (cb_hm.Text or u""))

    def nap_khung(*a):
        k = _khong_dau(u"%s" % cb_kho.SelectedItem)
        cb_kt.Items.Clear()
        hop = [t for t in ten_khung if k in _khong_dau(t).replace(u" ", u"") and u"bia" not in _khong_dau(t)]
        for t in (hop or ten_khung):
            cb_kt.Items.Add(t)
        if cb_kt.Items.Count:
            cb_kt.SelectedIndex = 0
            luu_kt = luu.get("khung_" + k)
            for i in range(cb_kt.Items.Count):
                if u"%s" % cb_kt.Items[i] == luu_kt:
                    cb_kt.SelectedIndex = i

    def so_sua(*a):
        so_tay[0] = tb_so.Focused

    cb_gd.TextChanged += lambda s, e: (nap_hm(), goi_y_so())
    cb_hm.TextChanged += lambda s, e: goi_y_so()
    cb_kho.SelectedIndexChanged += nap_khung
    tb_so.TextChanged += so_sua
    cb_gd.Text = luu.get("gd", ds_gd[-1] if ds_gd else u"")
    nap_hm()
    cb_hm.Text = luu.get("hm", u"")
    cb_kho.SelectedIndex = 1 if luu.get("kho") == u"A0" else 0
    nap_khung()
    goi_y_so()

    ok = Button()
    ok.Text = u"Chạy"
    ok.Size = Size(100, 30)
    ok.Location = Point(380, 286)
    ok.DialogResult = DialogResult.OK
    huy = Button()
    huy.Text = u"Huỷ"
    huy.Size = Size(100, 30)
    huy.Location = Point(490, 286)
    huy.DialogResult = DialogResult.Cancel
    f.Controls.Add(ok)
    f.Controls.Add(huy)
    f.AcceptButton = ok
    f.CancelButton = huy
    anh_thu = os.environ.get("ARV_HOI_ANH")         # chỉ khi thử: vẽ hộp thoại ra PNG, không hiện cửa sổ, coi như bấm Chạy
    if anh_thu:
        from System.Drawing import Bitmap, Rectangle
        from System.Windows.Forms import Application
        f.StartPosition = FormStartPosition.Manual
        f.Location = Point(-5000, -5000)
        f.ShowInTaskbar = False
        f.Opacity = 0.0
        f.Show()
        Application.DoEvents()
        bm = Bitmap(f.Width, f.Height)
        f.DrawToBitmap(bm, Rectangle(0, 0, f.Width, f.Height))
        bm.Save(anh_thu)
        f.Hide()
    elif f.ShowDialog() != DialogResult.OK:
        return None
    kq = {21: bool(chk.Checked), 22: u"%s" % (cb_gd.Text or u""), 23: u"%s" % (cb_hm.Text or u""),
          24: u"%s" % cb_kho.SelectedItem, 25: u"%s" % (cb_kt.SelectedItem or u""), 26: u"%s" % (tb_so.Text or u""),
          27: u"%s" % (tb_ten.Text or u"")}
    luu.update({"dat": kq[21], "gd": kq[22], "hm": kq[23], "kho": kq[24]})
    luu["khung_" + _khong_dau(kq[24])] = kq[25]
    _ghi_luu(luu)
    return kq
