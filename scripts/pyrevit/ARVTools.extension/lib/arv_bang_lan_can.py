# -*- coding: utf-8 -*-
# Bảng lan can, louver của nút "Thống kê lan can, louver" (người dùng yêu cầu 2026-11-05: "thống kê lan can louver như
# cửa"): cùng cột với bảng cửa (arv_bang_cua.py), nhưng tên là MARK của từng đối tượng, không phải Type Mark.
#   - Mỗi nhóm 1 dòng (đối tượng trùng hiện 1 lần): cùng lớp + cùng type + cùng kích thước + cùng Mark đúng tiền tố. Mark
#     trống / sai tiền tố (vd. số tự tăng 75, 76…) gộp chung để đặt tên 1 lần; Mark đúng tiền tố khác nhau giữ riêng dòng.
#   - Trả về {IN: giá trị} cho ThongKeLanCan_TuDong.py: IN[7] = JSON [{"ids": [...], "moi": "LK-01"}], IN[8] = tạo bảng
#     thống kê Revit; hoặc None nếu Huỷ.
# Thử tự động: ARV_HOI_ANH = đường dẫn PNG (vẽ bảng ra ảnh, không hiện cửa sổ, coi như bấm Đổi tên);
# ARV_TK_THU = JSON {"<số thứ tự dòng>": "<tên đổi>"} điền sẵn cột Tên đổi.
import io
import os
import json
import unicodedata

import clr
clr.AddReference("RevitAPI")
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")
import Autodesk.Revit.DB as DB
import arv_lk
from System.Windows.Forms import (Form, Label, CheckBox, Button, DialogResult, FormStartPosition, DataGridView,
                                  DataGridViewTextBoxColumn, DataGridViewAutoSizeColumnsMode, DataGridViewSelectionMode,
                                  AnchorStyles, MessageBox, MessageBoxButtons, MessageBoxIcon, DataGridViewEditMode,
                                  DataGridViewColumnSortMode)
from System.Drawing import Size, Point, Font, Color

_LUU = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "pyRevit", "ARVTools", "ThongKeLanCan.json")
LAN_CAN, LOUVER = u"Lan can", u"Louver"
_TIEN_TO = {LAN_CAN: (u"lk", u"lc"), LOUVER: (u"lv",)}       # như IN[1] / IN[2] của core
_TU_KHOA_LV = (u"louver", u"lam")                            # như IN[6] của core
_HANG_MUC = (DB.BuiltInCategory.OST_StairsRailing, DB.BuiltInCategory.OST_Windows, DB.BuiltInCategory.OST_GenericModel)
_COT = ((u"loai", u"Loại", 70), (u"cua", u"Lan can / louver (Family : Type)", 280), (u"ten", u"Tên hiện tại (Mark)", 140),
        (u"moi", u"Tên đổi", 110), (u"dai", u"Chiều dài", 80), (u"cao", u"Chiều cao", 80),
        (u"sl", u"SL mặt bằng", 80), (u"sl_da", u"SL cả dự án", 80))


def _kd(s):
    s = unicodedata.normalize("NFD", u"%s" % (s or u"")).replace(u"đ", u"d").replace(u"Đ", u"D")
    return u"".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def _ten(e):
    p = e.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM) if e is not None else None
    if p is not None and p.AsString():
        return p.AsString()
    try:
        return e.Name
    except Exception:
        return u"?"


def _mark(e):
    p = e.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK)
    return (p.AsString() or u"").strip() if p is not None else u""


def _dung_tien_to(mk, lop):
    k = _kd(mk)
    return bool(k) and any(k.startswith(x) for x in _TIEN_TO[lop])


def phan_loai(doc, e, bic):
    """Lan can / Louver / None. Mark có tiền tố → theo Mark; không thì theo hạng mục / Type Comments / tên (như core)."""
    k = _kd(_mark(e))
    if k and any(k.startswith(x) for x in _TIEN_TO[LAN_CAN]):
        return LAN_CAN
    if k and any(k.startswith(x) for x in _TIEN_TO[LOUVER]):
        return LOUVER
    if bic == DB.BuiltInCategory.OST_StairsRailing:
        return LAN_CAN
    t = e.Document.GetElement(e.GetTypeId())
    if t is None:
        return None
    p = t.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_COMMENTS)
    tc = _kd(p.AsString() if p is not None else u"")
    ten = u" %s " % _kd(u"%s %s" % (getattr(t, "FamilyName", u""), _ten(t))).replace(u"-", u" ").replace(u"_", u" ")
    for x in _TU_KHOA_LV:
        if x in tc or (u" %s " % x) in ten or (len(x) > 3 and x in ten):
            return LOUVER
    return None


def _mm(v):
    return DB.UnitUtils.ConvertFromInternalUnits(v, DB.UnitTypeId.Millimeters)


def _kt(o, bips):
    for b in bips:
        p = o.get_Parameter(b) if o is not None else None
        if p is not None and p.HasValue and p.StorageType == DB.StorageType.Double:
            return int(round(_mm(p.AsDouble())))
    return None


def _kich_thuoc(doc, e, t, lop):
    """(chiều dài, chiều cao) mm. Lan can: dài theo đường dẫn (làm tròn 10 mm để gộp), cao theo type Railing Height."""
    if lop == LAN_CAN and e.Category is not None and e.Category.Id.Value == int(DB.BuiltInCategory.OST_StairsRailing):
        dai = _kt(e, (DB.BuiltInParameter.CURVE_ELEM_LENGTH, DB.BuiltInParameter.INSTANCE_LENGTH_PARAM))
        if dai is None:
            try:
                dai = int(round(_mm(sum(c.Length for c in e.GetPath()))))
            except Exception:
                dai = None
        cao = None
        p = t.LookupParameter("Railing Height") if t is not None else None
        if p is not None and p.HasValue:
            cao = int(round(_mm(p.AsDouble())))
        return (int(round(dai / 10.0)) * 10 if dai is not None else None), cao
    b_rong = (DB.BuiltInParameter.WINDOW_WIDTH, DB.BuiltInParameter.GENERIC_WIDTH, DB.BuiltInParameter.FAMILY_WIDTH_PARAM)
    b_cao = (DB.BuiltInParameter.WINDOW_HEIGHT, DB.BuiltInParameter.GENERIC_HEIGHT, DB.BuiltInParameter.FAMILY_HEIGHT_PARAM)
    return (_kt(e, b_rong) if _kt(e, b_rong) is not None else _kt(t, b_rong),
            _kt(e, b_cao) if _kt(e, b_cao) is not None else _kt(t, b_cao))


def _nhom_mot(doc, e, bic):
    """(khoá nhóm, lớp, type, dài, cao, Mark) hoặc None nếu không phải lan can / louver."""
    lop = phan_loai(doc, e, bic)
    if lop is None:
        return None
    t = e.Document.GetElement(e.GetTypeId())
    dai, cao = _kich_thuoc(doc, e, t, lop)
    mk = _mark(e)
    tid = (t.Id.Value if not e.Document.IsLinked else (e.Document.Title, t.Id.Value)) if t is not None else -1
    return (lop, tid, dai, cao, mk if _dung_tien_to(mk, lop) else u""), lop, t, dai, cao, mk


def _tom_tat_mark(marks):
    """Tên hiện tại của dòng: 1 Mark, hoặc vài Mark sai tiền tố (số tự tăng) đang bị gộp."""
    ds = sorted(set(m for m in marks if m), key=lambda m: (len(m), m))
    if len(ds) <= 4:
        return u", ".join(ds)
    return u"%s … (%d Mark)" % (u", ".join(ds[:3]), len(ds))


def lay_dong(doc, view):
    """Mỗi nhóm thấy trong mặt bằng 1 dòng: dict khoa / lop / loai / cua / ten / dai / cao / sl / sl_da / ids / ids_da /
    can_dat. Trả về (dòng, {Mark: [khoá nhóm]} cả dự án để báo trùng tên)."""
    trong_view = {}
    for bic in _HANG_MUC:
        for e in list(DB.FilteredElementCollector(doc, view.Id).OfCategory(bic).WhereElementIsNotElementType()) + \
                arv_lk.doi_tuong_link(doc, view, bic):
            r = _nhom_mot(doc, e, bic)
            if r is None:
                continue
            khoa, lop, t, dai, cao, mk = r
            g = trong_view.setdefault(khoa, {"khoa": khoa, "lop": lop, "t": t, "dai": dai, "cao": cao, "ids": [],
                                             "marks": []})
            g["ids"].append(e.Id.Value)
            g["marks"].append(mk)
    ca_du_an = {}
    ten_du_an = {}
    for bic in _HANG_MUC:
        for e in DB.FilteredElementCollector(doc).OfCategory(bic).WhereElementIsNotElementType():
            r = _nhom_mot(doc, e, bic)
            if r is None:
                continue
            ca_du_an.setdefault(r[0], []).append(e.Id.Value)
            if r[0][4]:
                ten_du_an.setdefault(r[0][4], set()).add(r[0])
    dong = []
    for khoa, g in trong_view.items():
        t = g["t"]
        dong.append({"khoa": khoa, "lop": g["lop"], "loai": g["lop"],
                     "cua": u"%s : %s" % (getattr(t, "FamilyName", u"?"), _ten(t)) if t is not None else u"?",
                     "ten": _tom_tat_mark(g["marks"]), "dung": bool(khoa[4]),
                     "dai": u"%s" % g["dai"] if g["dai"] is not None else u"?",
                     "cao": u"%s" % g["cao"] if g["cao"] is not None else u"?",
                     "sl": len(g["ids"]), "sl_da": len(ca_du_an.get(khoa, g["ids"])),
                     "ids": g["ids"], "ids_da": ca_du_an.get(khoa, g["ids"]), "link": t is not None and t.Document.IsLinked})
    dong.sort(key=lambda d: (d["lop"] != LAN_CAN, not d["dung"], d["ten"], d["cua"], -(int(d["dai"]) if d["dai"] != u"?" else 0)))
    return dong, ten_du_an


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


def hoi_thong_ke_lan_can(doc, view):
    tang = view.GenLevel.Name if view.GenLevel is not None else view.Name
    dong, ten_du_an = lay_dong(doc, view)
    if not dong:
        MessageBox.Show(u"Mặt bằng '%s' không có lan can / louver nào." % view.Name, u"Thống kê lan can, louver")
        return None
    luu = _doc_luu()
    try:
        thu = json.loads(os.environ.get("ARV_TK_THU") or u"{}")
    except Exception:
        thu = {}

    f = Form()
    f.Text = u"Thống kê lan can, louver – %s (%s)" % (view.Name, tang)
    f.StartPosition = FormStartPosition.CenterScreen
    f.Font = Font("Segoe UI", 9.0)
    f.MinimizeBox = False
    rong = sum(w for _, _, w in _COT) + 60
    f.ClientSize = Size(rong, min(720, 180 + 24 * len(dong)))
    f.MinimumSize = Size(700, 320)

    lb = Label()
    lb.Text = (u"Cùng loại + cùng kích thước hiện 1 dòng. Gõ tên vào cột 'Tên đổi' (để trống = giữ nguyên): lan can LK-…, "
               u"louver LV-…. Đổi tên = đặt Mark cho tất cả đối tượng của dòng; tag tự hiện tên mới. "
               u"Dòng vàng: chưa có Mark đúng tiền tố (nút Định vị lan can, louver chưa tag) hoặc trùng tên dòng khác.")
    lb.Location = Point(12, 8)
    lb.Size = Size(rong - 24, 40)
    lb.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
    f.Controls.Add(lb)

    g = DataGridView()
    g.Location = Point(12, 52)
    g.Size = Size(rong - 24, f.ClientSize.Height - 52 - 78)
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
    for i_d, d in enumerate(dong):
        i = g.Rows.Add()
        r = g.Rows[i]
        for k, _, _ in _COT:
            r.Cells[k].Value = u"%s" % (thu.get(u"%d" % i_d, u"") if k == u"moi" else d[k])
        if d.get("link"):           # đối tượng trong file link: chỉ đọc (đặt Mark phải mở file link)
            r.Cells[u"moi"].ReadOnly = True
            r.Cells[u"moi"].Style.BackColor = Color.FromArgb(235, 235, 235)
        if not d["dung"] or len(ten_du_an.get(d["khoa"][4], ())) > 1:
            for k, _, _ in _COT:
                if k != u"moi":
                    r.Cells[k].Style.BackColor = Color.FromArgb(255, 245, 200)
    f.Controls.Add(g)

    chk_da = CheckBox()
    chk_da.Text = u"Đặt tên cho cả đối tượng cùng nhóm ở các tầng khác (cột 'SL cả dự án'); bỏ tích = chỉ mặt bằng này"
    chk_da.Location = Point(12, f.ClientSize.Height - 68)
    chk_da.Size = Size(rong - 24, 24)
    chk_da.Anchor = AnchorStyles.Bottom | AnchorStyles.Left
    chk_da.Checked = bool(luu.get("ca_du_an", True))
    f.Controls.Add(chk_da)
    chk = CheckBox()
    chk.Text = u"Tạo / cập nhật bảng thống kê Revit (BẢNG THỐNG KÊ LAN CAN / LOUVER %s)" % tang.upper()
    chk.Location = Point(12, f.ClientSize.Height - 40)
    chk.Size = Size(rong - 260, 24)
    chk.Anchor = AnchorStyles.Bottom | AnchorStyles.Left
    chk.Checked = bool(luu.get("bang_revit", True))
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
        doi = []
        for i, d in enumerate(dong):
            v = g.Rows[i].Cells[u"moi"].Value
            v = (u"%s" % v).strip() if v is not None else u""
            if v and v != d["ten"]:
                doi.append((v, d))
        return doi

    def kiem_tra():
        """Cảnh báo: tên mới sai tiền tố (nút Định vị sẽ không tag), hoặc trùng tên nhóm khác (bảng để trống kích thước)."""
        doi = ket_qua()
        khoa_doi = set(d["khoa"] for _, d in doi)
        bao = []
        moi = {}
        for v, d in doi:
            if not _dung_tien_to(v, d["lop"]):
                bao.append(u"'%s' (%s) không theo tiền tố %s – nút Định vị lan can, louver sẽ không tag." % (
                    v, d["cua"], u" / ".join(x.upper() for x in _TIEN_TO[d["lop"]])))
            moi.setdefault(v, []).append(d)
            khac = [k for k in ten_du_an.get(v, ()) if k not in khoa_doi]
            if khac:
                bao.append(u"'%s' đã có ở nhóm khác trong dự án – bảng thống kê gộp chung, ô kích thước có thể trống." % v)
        for v, ds in moi.items():
            if len(ds) > 1:
                bao.append(u"'%s' đặt cho %d dòng khác loại / kích thước – bảng thống kê gộp chung, ô kích thước có thể "
                           u"trống." % (v, len(ds)))
        return sorted(set(bao))

    def bam_ok(s, e):
        bao = kiem_tra()
        if bao and MessageBox.Show(u"Cần xem lại:\n\n- " + u"\n- ".join(bao[:12]) + u"\n\nVẫn đổi?",
                                   u"Thống kê lan can, louver", MessageBoxButtons.YesNo,
                                   MessageBoxIcon.Warning) != DialogResult.Yes:
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
    luu["ca_du_an"] = bool(chk_da.Checked)
    _ghi_luu(luu)
    return {7: json.dumps([{"ids": (d["ids_da"] if chk_da.Checked else d["ids"]), "moi": v, "cu": d["ten"], "nhan": d["cua"]}
                           for v, d in doi], ensure_ascii=False),
            8: bool(chk.Checked)}
