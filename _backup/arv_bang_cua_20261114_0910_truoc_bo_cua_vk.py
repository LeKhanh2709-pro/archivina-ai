# -*- coding: utf-8 -*-
# Bảng cửa của nút "Thống kê cửa" (người dùng yêu cầu 2026-11-04: "1 bảng hiện ra, có các cửa, tên hiện tại, tên đổi,
# chiều dài, chiều cao"): cửa đi + cửa sổ thấy trong mặt bằng đang mở, mỗi loại cửa (ElementType) 1 dòng – cửa trùng
# hiện 1 lần. Cột "Tên đổi" gõ được; bấm "Đổi tên" → core đổi Type Mark (tên cửa trên tag / bảng thống kê).
# Trả về {chỉ số IN: giá trị} cho ThongKeCua_TuDong.py (IN[7] = JSON {id type: tên mới}, IN[8] = tạo bảng thống kê
# Revit) hoặc None nếu Huỷ. Lựa chọn ô "bảng thống kê Revit" nhớ ở %APPDATA%\pyRevit\ARVTools\ThongKeCua.json.
# 2026-11-13 (người dùng yêu cầu + duyệt ảnh): hộp thoại có 2 cửa sổ (tab) – "Cửa đi, cửa sổ" như trên và "Vách kính":
# curtain wall thấy trong mặt bằng, tên = MARK của từng vách (IN[9] = JSON [{"ids": [...], "moi": ...}]), ô tag vách kính
# bằng Mark (IN[10]) + kiểu tag (IN[11]). Bấm nút ở cửa sổ nào thì làm việc của cửa sổ đó; tên gõ ở cửa sổ kia vẫn đặt.
# Thử tự động: ARV_HOI_ANH = đường dẫn PNG (vẽ bảng ra ảnh, không hiện cửa sổ, coi như bấm nút; thêm "<tên>_vk.png" cho
# cửa sổ Vách kính); ARV_HOI_TAB = 0 / 1; ARV_TK_THU = JSON {"<tên hiện tại>": "<tên đổi>"} điền sẵn cột Tên đổi;
# ARV_VK_THU = JSON {"<số thứ tự dòng>": "<tên>", "@trong": "<mẫu có %d cho dòng chưa có Mark>"}.
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
                                  DataGridViewColumnSortMode, TabControl, TabPage, Panel, DockStyle, ComboBox,
                                  ComboBoxStyle, Padding, TabSizeMode)
from System.Drawing import Size, Point, Font, Color, FontStyle

_LUU = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "pyRevit", "ARVTools", "ThongKeCua.json")
_HANG_MUC = ((DB.BuiltInCategory.OST_Doors, u"Cửa đi", DB.BuiltInParameter.DOOR_WIDTH, DB.BuiltInParameter.DOOR_HEIGHT),
             (DB.BuiltInCategory.OST_Windows, u"Cửa sổ", DB.BuiltInParameter.WINDOW_WIDTH,
              DB.BuiltInParameter.WINDOW_HEIGHT))
_LOAI_TRU = (u"louver", u"lam thep", u"lam nhom")    # Type Comments CÓ CHỨA chữ này (viết không dấu) thì không đưa vào bảng (như IN[2] của core, 2026-11-09)
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
    """Type Comments có chữ Louver / Lam thép / Lam nhôm (bất kỳ đâu, không phân biệt hoa thường / dấu) → không đưa vào bảng."""
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
        for e in list(DB.FilteredElementCollector(doc, view.Id).OfCategory(bic).WhereElementIsNotElementType()) + \
                arv_lk.doi_tuong_link(doc, view, bic):
            t = e.Document.GetElement(e.GetTypeId())
            if t is None or _loai_tru(t):
                continue
            k_nhom = t.Id.Value if not e.Document.IsLinked else (e.Document.Title, t.Id.Value)
            g = nhom.setdefault(k_nhom, {"t": t, "sl": 0, "dai": set(), "cao": set(), "link": e.Document.IsLinked})
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
            dong.append({"id": k, "link": g["link"], "cat": int(bic), "loai": loai + (u" (link)" if g["link"] else u""),
                         "cua": u"%s : %s" % (t.FamilyName, _ten(t)),
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


# ---- Cửa sổ "Vách kính" (người dùng yêu cầu 2026-11-13: "1 cửa sổ đặt tên cửa đi cửa sổ, 1 cửa sổ tag vách kính bằng mark") ----
_VK_TAG = u"ARV_Tag Vach Kinh Mark"            # family tag tường hiện Mark đóng gói (lib\tag_vach_kinh), như VK_TAG của core
_COT_VK = ((u"loai", u"Loại", 70), (u"cua", u"Vách kính (kiểu tường)", 230), (u"ten", u"Tên hiện tại (Mark)", 130),
           (u"moi", u"Tên đổi", 130), (u"dai", u"Chiều dài", 80), (u"cao", u"Chiều cao", 80),
           (u"sl", u"SL mặt bằng", 80), (u"tag", u"Đã tag", 70))


def _la_vach(e):
    try:
        return e.WallType.Kind == DB.WallKind.Curtain
    except Exception:
        return False


def _ten_kieu(t):
    p = t.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM) if t is not None else None
    return p.AsString() if p is not None and p.AsString() else _ten(t)


def _khoa_tn(s):
    """Sắp tên kiểu T1-VK.2 trước T1-VK.10."""
    import re
    return [int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", s or u"")]


def lay_dong_vk(doc, view):
    """Vách kính (curtain wall) thấy trong mặt bằng; cùng kiểu + cùng dài + cùng cao + cùng Mark 1 dòng:
    dict loai / cua / ten / dai / cao / sl / tag / ids / link."""
    da_tag = set()
    for tg in DB.FilteredElementCollector(doc, view.Id).OfClass(DB.IndependentTag):
        if tg.Category is not None and tg.Category.Id.Value == int(DB.BuiltInCategory.OST_WallTags):
            for x in tg.GetTaggedElementIds():
                da_tag.add((x.LinkInstanceId.Value, x.LinkedElementId.Value) if x.LinkInstanceId != DB.ElementId.InvalidElementId
                           else (-1, x.HostElementId.Value))
    ds = [(e, -1) for e in DB.FilteredElementCollector(doc, view.Id).OfClass(DB.Wall) if _la_vach(e)]
    lv = view.GenLevel
    for li in DB.FilteredElementCollector(doc, view.Id).OfClass(DB.RevitLinkInstance):
        try:
            ld = li.GetLinkDocument()
        except Exception:
            ld = None
        if ld is None or lv is None:
            continue
        tf = li.GetTotalTransform()
        ids = set(l.Id.Value for l in DB.FilteredElementCollector(ld).OfClass(DB.Level)
                  if abs(l.Elevation + tf.Origin.Z - lv.Elevation) < arv_lk._mm(5))
        for e in DB.FilteredElementCollector(doc, view.Id, li.Id).OfClass(DB.Wall):
            if _la_vach(e) and e.LevelId.Value in ids:
                ds.append((e, li.Id.Value))
    nhom = {}
    for e, li_id in ds:
        t = e.WallType
        try:
            dai = int(round(DB.UnitUtils.ConvertFromInternalUnits(e.Location.Curve.Length, DB.UnitTypeId.Millimeters)))
        except Exception:
            dai = None
        cao = _kt(e, None, (DB.BuiltInParameter.WALL_USER_HEIGHT_PARAM,))
        mk = _chuoi(e, DB.BuiltInParameter.ALL_MODEL_MARK)
        k = (li_id, t.Id.Value, dai, cao, mk)
        g = nhom.setdefault(k, {"t": t, "ids": [], "tag": 0})
        g["ids"].append(e.Id.Value)
        if (li_id, e.Id.Value) in da_tag:
            g["tag"] += 1
    dong = []
    for (li_id, _, dai, cao, mk), g in nhom.items():
        t = g["t"]
        dong.append({"link": li_id != -1, "loai": u"Vách kính" + (u" (link)" if li_id != -1 else u""),
                     "cua": u"%s : %s" % (t.FamilyName, _ten_kieu(t)), "ten": mk,
                     "dai": u"%s" % dai if dai is not None else u"?", "cao": u"%s" % cao if cao is not None else u"?",
                     "sl": len(g["ids"]), "tag": u"%d / %d" % (g["tag"], len(g["ids"])), "ids": sorted(g["ids"])})
    dong.sort(key=lambda d: (d["ten"] == u"", _khoa_tn(d["ten"]), d["cua"], d["dai"]))
    return dong


def _kieu_tag_tuong(doc):
    return sorted(u"%s : %s" % (s.FamilyName, _ten_kieu(s))
                  for s in DB.FilteredElementCollector(doc).OfClass(DB.FamilySymbol).OfCategory(DB.BuiltInCategory.OST_WallTags))


def _luoi(cot):
    g = DataGridView()
    g.Dock = DockStyle.Fill
    g.AllowUserToAddRows = False
    g.AllowUserToDeleteRows = False
    g.RowHeadersVisible = False
    g.SelectionMode = DataGridViewSelectionMode.CellSelect
    g.EditMode = DataGridViewEditMode.EditOnEnter
    g.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill
    g.BackgroundColor = Color.White
    for k, nhan, w in cot:
        c = DataGridViewTextBoxColumn()
        c.Name = k
        c.HeaderText = nhan
        c.FillWeight = float(w)
        c.ReadOnly = k != u"moi"
        c.SortMode = DataGridViewColumnSortMode.NotSortable
        g.Columns.Add(c)
    g.Columns[u"moi"].DefaultCellStyle.BackColor = Color.FromArgb(232, 244, 255)
    return g


def _to_vang(r, cot):
    for k, _, _ in cot:
        if k != u"moi":
            r.Cells[k].Style.BackColor = Color.FromArgb(255, 245, 200)


def _khoa_o(r):
    r.Cells[u"moi"].ReadOnly = True
    r.Cells[u"moi"].Style.BackColor = Color.FromArgb(235, 235, 235)


def hoi_thong_ke_cua(doc, view):
    """Hộp thoại 2 cửa sổ: "Cửa đi, cửa sổ" (đổi Type Mark + bảng thống kê Revit) và "Vách kính" (đặt Mark + tag bằng Mark).
    Bấm nút ở cửa sổ nào thì làm việc của cửa sổ đó; tên đã gõ ở cửa sổ kia vẫn được đặt.
    Trả về {7: JSON đổi tên cửa, 8: bảng Revit, 9: JSON đặt Mark vách, 10: tag vách, 11: kiểu tag} hoặc None nếu Huỷ.
    Thử tự động: ARV_HOI_ANH = PNG cửa sổ cửa (+ "<tên>_vk.png" cửa sổ vách kính), ARV_HOI_TAB = 0 / 1 (cửa sổ coi như đang
    bấm), ARV_TK_THU = {"<tên hiện tại>": "<tên đổi>"}, ARV_VK_THU = {"<số thứ tự dòng>": "<tên>", "@trong": "T1-VK.9%d"}."""
    tang = view.GenLevel.Name if view.GenLevel is not None else view.Name
    dong = lay_dong(doc, view)
    dong_vk = lay_dong_vk(doc, view)
    if not dong and not dong_vk:
        MessageBox.Show(u"Mặt bằng '%s' không có cửa đi / cửa sổ / vách kính nào." % view.Name, u"Thống kê cửa")
        return None
    luu = _doc_luu()
    thu, thu_vk = {}, {}
    try:
        thu = json.loads(os.environ.get("ARV_TK_THU") or u"{}")
        thu_vk = json.loads(os.environ.get("ARV_VK_THU") or u"{}")
    except Exception:
        pass

    f = Form()
    f.Text = u"Thống kê cửa – %s (%s)" % (view.Name, tang)
    f.StartPosition = FormStartPosition.CenterScreen
    f.Font = Font("Segoe UI", 9.0)
    f.MinimizeBox = False
    rong = sum(w for _, _, w in _COT) + 90
    f.ClientSize = Size(rong, min(760, 250 + 24 * max(len(dong), len(dong_vk))))
    f.MinimumSize = Size(760, 360)
    f.Padding = Padding(8)

    tc = TabControl()
    tc.Dock = DockStyle.Fill
    tc.Font = Font("Segoe UI", 10.0, FontStyle.Bold)
    tc.ItemSize = Size(150, 28)                 # (TabControl.Padding kiểu Point không đặt được từ pythonnet)
    tc.SizeMode = TabSizeMode.Fixed
    fn = Font("Segoe UI", 9.0)

    # ---- cửa sổ 1: cửa đi, cửa sổ
    p1 = TabPage()
    p1.Text = u"Cửa đi, cửa sổ"
    p1.Font = fn
    p1.Padding = Padding(6)
    p1.UseVisualStyleBackColor = True
    g = _luoi(_COT)
    dem_ten = {}
    for d in dong:
        if d["ten"]:
            dem_ten[(d["cat"], d["ten"])] = dem_ten.get((d["cat"], d["ten"]), 0) + 1
    for d in dong:
        r = g.Rows[g.Rows.Add()]
        for k, _, _ in _COT:
            r.Cells[k].Value = u"%s" % (thu.get(d["ten"], u"") if k == u"moi" else d[k])
        if d.get("link"):           # cửa trong file link: chỉ đọc (đổi tên phải mở file link)
            _khoa_o(r)
        if not d["ten"] or dem_ten.get((d["cat"], d["ten"]), 0) > 1:
            _to_vang(r, _COT)
    lb = Label()
    lb.Text = (u"Mỗi loại cửa thấy trong mặt bằng 1 dòng (cửa trùng hiện 1 lần). Gõ tên mới vào cột 'Tên đổi' (để trống = "
               u"giữ nguyên). Đổi tên = đổi Type Mark của loại cửa: áp cho MỌI cửa cùng loại trong dự án (cột 'SL cả dự "
               u"án'); tag cửa tự hiện tên mới. Dòng vàng: chưa có tên hoặc cùng tên với loại cửa khác.")
    lb.Dock = DockStyle.Top
    lb.Height = 42
    d1 = Panel()
    d1.Dock = DockStyle.Bottom
    d1.Height = 32
    chk = CheckBox()
    chk.Text = u"Tạo / cập nhật bảng thống kê Revit (THỐNG KÊ CỬA ĐI / CỬA SỔ - %s)" % tang.upper()
    chk.Location = Point(2, 6)
    chk.Size = Size(rong - 80, 24)
    chk.Checked = bool(luu.get("bang_revit", False))
    d1.Controls.Add(chk)
    p1.Controls.Add(g)
    p1.Controls.Add(lb)
    p1.Controls.Add(d1)

    # ---- cửa sổ 2: vách kính
    p2 = TabPage()
    p2.Text = u"Vách kính"
    p2.Font = fn
    p2.Padding = Padding(6)
    p2.UseVisualStyleBackColor = True
    g2 = _luoi(_COT_VK)
    dem_vk = {}
    for d in dong_vk:
        if d["ten"]:
            dem_vk[d["ten"]] = dem_vk.get(d["ten"], 0) + 1
    so_trong = 0
    for i_d, d in enumerate(dong_vk):
        r = g2.Rows[g2.Rows.Add()]
        dien = thu_vk.get(u"%d" % i_d, u"")
        if not d["ten"] and not d["link"] and thu_vk.get(u"@trong"):
            so_trong += 1
            dien = thu_vk[u"@trong"] % so_trong
        for k, _, _ in _COT_VK:
            r.Cells[k].Value = u"%s" % (dien if k == u"moi" else d[k])
        if d["link"]:               # vách trong file link: chỉ đọc (đặt Mark phải mở file link), vẫn tag được
            _khoa_o(r)
        if not d["ten"] or dem_vk.get(d["ten"], 0) > 1:
            _to_vang(r, _COT_VK)
    lb2 = Label()
    lb2.Text = (u"Vách kính (curtain wall) thấy trong mặt bằng; vách cùng kiểu + cùng dài + cùng cao + cùng tên hiện 1 dòng. "
                u"Tên vách = MARK của từng vách: gõ vào cột 'Tên đổi' (để trống = giữ nguyên) → đặt Mark cho các vách của "
                u"dòng. Dòng vàng: chưa có Mark (không tag) hoặc trùng Mark với dòng khác. Tag: mỗi vách 1 tag hiện Mark, "
                u"giữa vách, phía ngoài nhà; vách đã có tag (cột 'Đã tag') thì không tag thêm.")
    lb2.Dock = DockStyle.Top
    lb2.Height = 58
    d2 = Panel()
    d2.Size = Size(rong - 16 - 24, 32)
    d2.Dock = DockStyle.Bottom
    chk_tag = CheckBox()
    chk_tag.Text = u"Tag vách kính bằng Mark trên mặt bằng này"
    chk_tag.Location = Point(2, 6)
    chk_tag.Size = Size(290, 24)
    chk_tag.Checked = bool(luu.get("tag_vk", True))
    lt = Label()
    lt.Text = u"Family tag:"
    lt.Location = Point(300, 9)
    lt.Size = Size(72, 22)
    cb = ComboBox()
    cb.DropDownStyle = ComboBoxStyle.DropDownList
    cb.Location = Point(374, 5)
    cb.Size = Size(d2.Width - 374 - 4, 24)
    cb.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
    kieu = _kieu_tag_tuong(doc)
    nap = u"%s (nạp vào dự án)" % _VK_TAG
    co_san = [k for k in kieu if k.startswith(_VK_TAG + u" : ")]
    if not co_san:
        cb.Items.Add(nap)
    for k in co_san + [k for k in kieu if k not in co_san]:
        cb.Items.Add(k)
    cb.SelectedIndex = 0
    d2.Controls.Add(chk_tag)
    d2.Controls.Add(lt)
    d2.Controls.Add(cb)
    p2.Controls.Add(g2)
    p2.Controls.Add(lb2)
    p2.Controls.Add(d2)

    tc.TabPages.Add(p1)
    tc.TabPages.Add(p2)

    day = Panel()
    day.Size = Size(rong - 16, 44)
    day.Dock = DockStyle.Bottom
    ok = Button()
    ok.Size = Size(130, 30)
    ok.Location = Point(day.Width - 100 - 12 - 130, 10)
    ok.Anchor = AnchorStyles.Bottom | AnchorStyles.Right
    huy = Button()
    huy.Text = u"Huỷ"
    huy.Size = Size(100, 30)
    huy.Location = Point(day.Width - 100, 10)
    huy.Anchor = AnchorStyles.Bottom | AnchorStyles.Right
    huy.DialogResult = DialogResult.Cancel
    day.Controls.Add(ok)
    day.Controls.Add(huy)
    f.Controls.Add(tc)
    f.Controls.Add(day)
    f.CancelButton = huy

    def dat_nut(s=None, e=None):
        ok.Text = u"Đổi tên" if tc.SelectedIndex == 0 else u"Đặt tên + tag"

    tc.SelectedIndexChanged += dat_nut
    if not dong or (dong_vk and luu.get("tab") == 1):
        tc.SelectedIndex = 1
    dat_nut()

    def ket_qua():
        g.EndEdit()
        doi = {}
        for i, d in enumerate(dong):
            v = g.Rows[i].Cells[u"moi"].Value
            v = (u"%s" % v).strip() if v is not None else u""
            if v and v != d["ten"] and not d.get("link"):
                doi[d["id"]] = (v, d)
        return doi

    def ket_qua_vk():
        g2.EndEdit()
        doi = []
        for i, d in enumerate(dong_vk):
            v = g2.Rows[i].Cells[u"moi"].Value
            v = (u"%s" % v).strip() if v is not None else u""
            if v and v != d["ten"] and not d["link"]:
                doi.append((v, d))
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
        return sorted(set(bao))

    def kiem_tra_vk():
        """Cảnh báo Mark mới trùng Mark vách kính khác (trong mặt bằng hoặc cả dự án)."""
        doi = ket_qua_vk()
        if not doi:
            return []
        dang_doi = set(i for _, d in doi for i in d["ids"])
        khac = {}
        for e in DB.FilteredElementCollector(doc).OfClass(DB.Wall):
            if _la_vach(e) and e.Id.Value not in dang_doi:
                mk = _chuoi(e, DB.BuiltInParameter.ALL_MODEL_MARK)
                if mk:
                    khac[mk] = khac.get(mk, 0) + 1
        bao, moi = [], {}
        for v, d in doi:
            if v in khac:
                bao.append(u"'%s' đã là Mark của %d vách kính khác trong dự án" % (v, khac[v]))
            moi.setdefault(v, []).append(u"%s x %s" % (d["dai"], d["cao"]))
        for v, ds in moi.items():
            if len(ds) > 1:
                bao.append(u"'%s' đặt cho %d dòng khác kích thước: %s" % (v, len(ds), u"; ".join(ds[:4])))
        return sorted(set(bao))

    def bam_ok(s, e):
        bao = kiem_tra() + kiem_tra_vk()
        if bao and MessageBox.Show(u"Tên mới bị trùng:\n\n- " + u"\n- ".join(bao[:12]) + u"\n\nVẫn đặt tên?",
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
        for i_tab, duong in ((0, anh_thu), (1, os.path.splitext(anh_thu)[0] + u"_vk.png")):
            tc.SelectedIndex = i_tab
            Application.DoEvents()
            g.ClearSelection()
            g2.ClearSelection()
            Application.DoEvents()
            bm = Bitmap(f.Width, f.Height)
            f.DrawToBitmap(bm, Rectangle(0, 0, f.Width, f.Height))
            bm.Save(duong)
        tc.SelectedIndex = int(os.environ.get("ARV_HOI_TAB") or 0)
        f.Hide()
    elif f.ShowDialog() != DialogResult.OK:
        return None
    doi = ket_qua()
    doi_vk = ket_qua_vk()
    tab = tc.SelectedIndex
    if tab == 0:
        luu["bang_revit"] = bool(chk.Checked)
    else:
        luu["tag_vk"] = bool(chk_tag.Checked)
    luu["tab"] = tab
    _ghi_luu(luu)
    kieu_chon = u"%s" % cb.SelectedItem if cb.SelectedItem is not None else u""
    return {7: json.dumps({str(k): v for k, (v, _) in doi.items()}, ensure_ascii=False),
            8: bool(chk.Checked) and tab == 0,
            9: json.dumps([{"ids": d["ids"], "moi": v, "cu": d["ten"]} for v, d in doi_vk], ensure_ascii=False),
            10: bool(chk_tag.Checked) and tab == 1,
            11: u"" if kieu_chon == nap else kieu_chon}
