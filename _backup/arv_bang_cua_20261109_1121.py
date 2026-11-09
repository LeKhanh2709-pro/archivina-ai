# -*- coding: utf-8 -*-
# Bảng cửa của nút "Thống kê cửa" (người dùng yêu cầu 2026-11-04: "1 bảng hiện ra, có các cửa, tên hiện tại, tên đổi,
# chiều dài, chiều cao"): cửa đi + cửa sổ thấy trong mặt bằng đang mở, mỗi loại cửa (ElementType) 1 dòng – cửa trùng
# hiện 1 lần. Cột "Tên đổi" gõ được; bấm "Đổi tên" → core đổi Type Mark (tên cửa trên tag / bảng thống kê).
# Trả về {chỉ số IN: giá trị} cho ThongKeCua_TuDong.py (IN[7] = JSON {id type: tên mới}, IN[8] = tạo bảng thống kê
# Revit) hoặc None nếu Huỷ. Lựa chọn ô "bảng thống kê Revit" nhớ ở %APPDATA%\pyRevit\ARVTools\ThongKeCua.json.
# Thử tự động: ARV_HOI_ANH = đường dẫn PNG (vẽ bảng ra ảnh, không hiện cửa sổ, coi như bấm Đổi tên);
# ARV_TK_THU = JSON {"<tên hiện tại>": "<tên đổi>"} điền sẵn cột Tên đổi.
import io
import os
import json
import unicodedata

import clr
clr.AddReference("RevitAPI")
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")
import Autodesk.Revit.DB as DB
from System.Windows.Forms import (Form, Label, CheckBox, Button, DialogResult, FormStartPosition, DataGridView,
                                  DataGridViewTextBoxColumn, DataGridViewAutoSizeColumnsMode, DataGridViewSelectionMode,
                                  AnchorStyles, MessageBox, MessageBoxButtons, MessageBoxIcon, DataGridViewEditMode,
                                  DataGridViewColumnSortMode)
from System.Drawing import Size, Point, Font, Color

_LUU = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "pyRevit", "ARVTools", "ThongKeCua.json")
_HANG_MUC = ((DB.BuiltInCategory.OST_Doors, u"Cửa đi", DB.BuiltInParameter.DOOR_WIDTH, DB.BuiltInParameter.DOOR_HEIGHT),
             (DB.BuiltInCategory.OST_Windows, u"Cửa sổ", DB.BuiltInParameter.WINDOW_WIDTH,
              DB.BuiltInParameter.WINDOW_HEIGHT))
_LOAI_TRU = (u"louver",)         # Type Comments CÓ CHỨA chữ này thì không đưa vào bảng (như IN[2] của core, 2026-11-09)
_COT = ((u"loai", u"Loại", 70), (u"cua", u"Cửa (Family : Type)", 260), (u"ten", u"Tên hiện tại", 120),
        (u"moi", u"Tên đổi", 120), (u"dai", u"Chiều dài", 80), (u"cao", u"Chiều cao", 80),
        (u"sl", u"SL mặt bằng", 80), (u"sl_da", u"SL cả dự án", 80))


def _ten(e):
    try:
        return DB.Element.Name.GetValue(e)
    except Exception:
        try:
            return e.Name
        except Exception:
            return u"?"


def _chuoi(t, bip):
    p = t.get_Parameter(bip) if t is not None else None
    return (p.AsString() or u"").strip() if p is not None else u""


def _khong_dau(s):
    s = unicodedata.normalize("NFD", u"%s" % (s or u"")).replace(u"đ", u"d").replace(u"Đ", u"D")
    return u"".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def _loai_tru(t):
    """Type Comments có chữ Louver (bất kỳ đâu, không phân biệt hoa thường / dấu) → không đưa vào bảng."""
    tc = _khong_dau(_chuoi(t, DB.BuiltInParameter.ALL_MODEL_TYPE_COMMENTS))
    return bool(tc) and any(k in tc for k in _LOAI_TRU)


def _kt(e, t, bips):
    for o in (e, t):
        if o is None:
            continue
        for b in bips:
            p = o.get_Parameter(b)
            if p is not None and p.HasValue and p.StorageType == DB.StorageType.Double:
                return int(round(DB.UnitUtils.ConvertFromInternalUnits(p.AsDouble(), DB.UnitTypeId.Millimeters)))
    return None


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
            f.write(u"%s" % json.dumps(d, ensure_ascii=False, indent=1))
    except Exception:
        pass


def lay_dong(doc, view):
    """Mỗi loại cửa (type) thấy trong mặt bằng 1 dòng: dict loai / cua / ten / dai / cao / sl / sl_da / id / cat."""
    dong = []
    for bic, loai, b_rong, b_cao in _HANG_MUC:
        nhom = {}
        for e in DB.FilteredElementCollector(doc, view.Id).OfCategory(bic).WhereElementIsNotElementType():
            t = doc.GetElement(e.GetTypeId())
            if t is None or _loai_tru(t):
                continue
            g = nhom.setdefault(t.Id.Value, {"t": t, "sl": 0, "dai": set(), "cao": set()})
            g["sl"] += 1
            g["dai"].add(_kt(e, t, (b_rong, DB.BuiltInParameter.FAMILY_WIDTH_PARAM)))
            g["cao"].add(_kt(e, t, (b_cao, DB.BuiltInParameter.FAMILY_HEIGHT_PARAM)))
        if not nhom:
            continue
        sl_da = {}
        for e in DB.FilteredElementCollector(doc).OfCategory(bic).WhereElementIsNotElementType():
            k = e.GetTypeId().Value
            if k in nhom:
                sl_da[k] = sl_da.get(k, 0) + 1
        for k, g in nhom.items():
            t = g["t"]
            dong.append({"id": k, "cat": int(bic), "loai": loai, "cua": u"%s : %s" % (t.FamilyName, _ten(t)),
                         "ten": _chuoi(t, DB.BuiltInParameter.ALL_MODEL_TYPE_MARK),
                         "dai": u" / ".join(str(x) for x in sorted(x for x in g["dai"] if x is not None)) or u"?",
                         "cao": u" / ".join(str(x) for x in sorted(x for x in g["cao"] if x is not None)) or u"?",
                         "sl": g["sl"], "sl_da": sl_da.get(k, g["sl"])})
    dong.sort(key=lambda d: (d["cat"] != int(DB.BuiltInCategory.OST_Doors), d["ten"] == u"", d["ten"], d["cua"]))
    return dong


def _ten_cua_loai_khac(doc, bic, bo_id):
    """{Type Mark: [tên type]} của các type CÙNG hạng mục trong cả dự án (trừ các type đang đổi) để báo trùng."""
    d = {}
    for t in DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory(bic)).WhereElementIsElementType():
        if t.Id.Value in bo_id:
            continue
        mk = _chuoi(t, DB.BuiltInParameter.ALL_MODEL_TYPE_MARK)
        if mk:
            d.setdefault(mk, []).append(u"%s : %s" % (getattr(t, "FamilyName", u""), _ten(t)))
    return d


def hoi_thong_ke_cua(doc, view):
    tang = view.GenLevel.Name if view.GenLevel is not None else view.Name
    dong = lay_dong(doc, view)
    if not dong:
        MessageBox.Show(u"Mặt bằng '%s' không có cửa đi / cửa sổ nào." % view.Name, u"Thống kê cửa")
        return None
    luu = _doc_luu()
    thu = {}
    try:
        thu = json.loads(os.environ.get("ARV_TK_THU") or u"{}")
    except Exception:
        thu = {}

    f = Form()
    f.Text = u"Thống kê cửa – %s (%s)" % (view.Name, tang)
    f.StartPosition = FormStartPosition.CenterScreen
    f.Font = Font("Segoe UI", 9.0)
    f.MinimizeBox = False
    rong = sum(w for _, _, w in _COT) + 60
    f.ClientSize = Size(rong, min(720, 150 + 24 * len(dong)))
    f.MinimumSize = Size(700, 300)

    lb = Label()
    lb.Text = (u"Mỗi loại cửa thấy trong mặt bằng 1 dòng (cửa trùng hiện 1 lần). Gõ tên mới vào cột 'Tên đổi' (để trống = "
               u"giữ nguyên). Đổi tên = đổi Type Mark của loại cửa: áp cho MỌI cửa cùng loại trong dự án (cột 'SL cả dự "
               u"án'); tag cửa tự hiện tên mới. Dòng vàng: cùng tên với loại cửa khác.")
    lb.Location = Point(12, 8)
    lb.Size = Size(rong - 24, 40)
    lb.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
    f.Controls.Add(lb)

    g = DataGridView()
    g.Location = Point(12, 52)
    g.Size = Size(rong - 24, f.ClientSize.Height - 52 - 50)
    g.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right
    g.AllowUserToAddRows = False
    g.AllowUserToDeleteRows = False
    g.RowHeadersVisible = False
    g.SelectionMode = DataGridViewSelectionMode.CellSelect
    g.EditMode = DataGridViewEditMode.EditOnEnter
    g.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill
    g.BackgroundColor = Color.White
    for k, nhan, w in _COT:
        c = DataGridViewTextBoxColumn()
        c.Name = k
        c.HeaderText = nhan
        c.FillWeight = float(w)
        c.ReadOnly = k != u"moi"
        c.SortMode = DataGridViewColumnSortMode.NotSortable
        g.Columns.Add(c)
    g.Columns[u"moi"].DefaultCellStyle.BackColor = Color.FromArgb(232, 244, 255)
    dem_ten = {}
    for d in dong:
        if d["ten"]:
            dem_ten[(d["cat"], d["ten"])] = dem_ten.get((d["cat"], d["ten"]), 0) + 1
    for d in dong:
        i = g.Rows.Add()
        r = g.Rows[i]
        for k, _, _ in _COT:
            r.Cells[k].Value = u"%s" % (thu.get(d["ten"], u"") if k == u"moi" else d[k])
        if not d["ten"] or dem_ten.get((d["cat"], d["ten"]), 0) > 1:
            for k, _, _ in _COT:
                if k != u"moi":
                    r.Cells[k].Style.BackColor = Color.FromArgb(255, 245, 200)
    f.Controls.Add(g)

    chk = CheckBox()
    chk.Text = u"Tạo / cập nhật bảng thống kê Revit (THỐNG KÊ CỬA ĐI / CỬA SỔ - %s)" % tang.upper()
    chk.Location = Point(12, f.ClientSize.Height - 40)
    chk.Size = Size(rong - 260, 24)
    chk.Anchor = AnchorStyles.Bottom | AnchorStyles.Left
    chk.Checked = bool(luu.get("bang_revit", False))
    f.Controls.Add(chk)
    ok = Button()
    ok.Text = u"Đổi tên"
    ok.Size = Size(100, 30)
    ok.Location = Point(rong - 224, f.ClientSize.Height - 42)
    ok.Anchor = AnchorStyles.Bottom | AnchorStyles.Right
    huy = Button()
    huy.Text = u"Huỷ"
    huy.Size = Size(100, 30)
    huy.Location = Point(rong - 112, f.ClientSize.Height - 42)
    huy.Anchor = AnchorStyles.Bottom | AnchorStyles.Right
    huy.DialogResult = DialogResult.Cancel
    f.Controls.Add(ok)
    f.Controls.Add(huy)
    f.CancelButton = huy

    def ket_qua():
        g.EndEdit()
        doi = {}
        for i, d in enumerate(dong):
            v = g.Rows[i].Cells[u"moi"].Value
            v = (u"%s" % v).strip() if v is not None else u""
            if v and v != d["ten"]:
                doi[d["id"]] = (v, d)
        return doi

    def kiem_tra():
        """Cảnh báo tên mới trùng tên loại cửa khác (cùng hạng mục) → hỏi có đổi tiếp không."""
        doi = ket_qua()
        bao = []
        for cat in set(d["cat"] for _, d in doi.values()):
            ids = set(k for k, (_, d) in doi.items() if d["cat"] == cat)
            khac = _ten_cua_loai_khac(doc, cat, ids)
            moi = {}
            for k, (v, d) in doi.items():
                if d["cat"] != cat:
                    continue
                if v in khac:
                    bao.append(u"'%s' (%s) trùng tên loại cửa khác: %s" % (v, d["cua"], u"; ".join(khac[v][:3])))
                moi.setdefault(v, []).append(d["cua"])
            # tên giữ nguyên của các dòng không đổi cũng tính
            for d in dong:
                if d["cat"] == cat and d["id"] not in doi and d["ten"] in moi:
                    moi[d["ten"]].append(d["cua"])
            for v, ds in moi.items():
                if len(ds) > 1:
                    bao.append(u"'%s' đặt cho %d loại cửa: %s" % (v, len(ds), u"; ".join(ds[:4])))
        return doi, sorted(set(bao))

    def bam_ok(s, e):
        doi, bao = kiem_tra()
        if bao and MessageBox.Show(u"Tên mới bị trùng:\n\n- " + u"\n- ".join(bao[:12]) +
                                   u"\n\nCác loại cửa cùng tên sẽ gộp chung 1 dòng trong bảng thống kê. Vẫn đổi?",
                                   u"Thống kê cửa", MessageBoxButtons.YesNo, MessageBoxIcon.Warning) != DialogResult.Yes:
            return
        f.DialogResult = DialogResult.OK
        f.Close()

    ok.Click += bam_ok
    anh_thu = os.environ.get("ARV_HOI_ANH")
    if anh_thu:
        from System.Drawing import Bitmap, Rectangle
        from System.Windows.Forms import Application
        f.StartPosition = FormStartPosition.Manual
        f.Location = Point(-5000, -5000)
        f.ShowInTaskbar = False
        f.Opacity = 0.0
        f.Show()
        Application.DoEvents()
        g.ClearSelection()
        Application.DoEvents()
        bm = Bitmap(f.Width, f.Height)
        f.DrawToBitmap(bm, Rectangle(0, 0, f.Width, f.Height))
        bm.Save(anh_thu)
        f.Hide()
    elif f.ShowDialog() != DialogResult.OK:
        return None
    doi = ket_qua()
    luu["bang_revit"] = bool(chk.Checked)
    _ghi_luu(luu)
    return {7: json.dumps({str(k): v for k, (v, _) in doi.items()}, ensure_ascii=False), 8: bool(chk.Checked)}
