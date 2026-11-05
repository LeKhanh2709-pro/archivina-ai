# -*- coding: utf-8 -*-
# Hộp thoại hỏi trước khi chạy nút "Định vị + tag cửa" (người dùng yêu cầu 2026-11-03): có đặt mặt bằng lên bản vẽ không,
# giai đoạn nào, hạng mục nào (gõ tên mới = thêm hạng mục), khổ giấy A1 / A0 (khung tên theo khổ), số hiệu + tên bản vẽ.
# Trả về {chỉ số IN: giá trị} cho core.py (IN[21] – IN[27] của TagCua_TuDong.py) hoặc None nếu Huỷ.
# hoi_chi_tiet_cua: cùng bảng cho nút "Chi tiết cửa" (người dùng yêu cầu 2026-11-03 tối: chọn nhiều cửa rồi bấm → hỏi
# giai đoạn, hạng mục, khổ giấy, số hiệu, tên bản vẽ) → IN[1] / IN[2] / IN[3] / IN[16] / IN[17] của ChiTietCua_TuDong.py.
# hoi_chong_tham / hoi_ngan_chay: cùng bảng cho nút Chống thấm / Ngăn cháy lan (người dùng yêu cầu 2026-11-03 tối: tự
# trình bày vào bản vẽ) → IN[10] – IN[16] của ChongTham_VeVenChanTuong.py / NganChay_TrucHKT.py.
# hoi_tuong_xay: cùng bảng cho nút "Tường xây" (người dùng yêu cầu 2026-11-04: thay hộp thoại 17 ô) → IN[0] / IN[1] /
# IN[4] / IN[5] / IN[6] / IN[15] / IN[17] của ARV_MBTuongXayTang_v1.py; chỉ khổ A1 (bố cục lõi đo theo khung A1).
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

_THU_MUC_LUU = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "pyRevit", "ARVTools")
_LUU = os.path.join(_THU_MUC_LUU, "TagCua_sheet.json")


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


def _doc_luu(duong=_LUU):
    try:
        with io.open(duong, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _ghi_luu(d, duong=_LUU):
    try:
        if not os.path.isdir(os.path.dirname(duong)):
            os.makedirs(os.path.dirname(duong))
        with io.open(duong, "w", encoding="utf-8") as f:
            f.write(json.dumps(d, ensure_ascii=False))
    except Exception:
        pass




def _bang(doc, tieu_de, co_dat, nhan_dat, ten_mac_dinh, duong_luu, dong_dau=u"", goi_y_rieng=None,
          ds_kho=(u"A1", u"A0")):
    """Dựng + hiện hộp thoại. Trả về dict {dat, gd, hm, kho, kt, so, ten} hoặc None nếu Huỷ.
    goi_y_rieng(gd, hm, ten) → số hiệu gợi ý riêng (None = theo số tiếp theo trong hạng mục)."""
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
    luu = _doc_luu(duong_luu)

    f = Form()
    f.Text = tieu_de
    f.StartPosition = FormStartPosition.CenterScreen
    f.FormBorderStyle = FormBorderStyle.FixedDialog
    f.MaximizeBox = False
    f.MinimizeBox = False
    f.Font = Font("Segoe UI", 9.0)
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

    if dong_dau:
        lb0 = Label()
        lb0.Text = dong_dau
        lb0.Location = Point(14, y[0] + 3)
        lb0.Size = Size(580, 22)
        f.Controls.Add(lb0)
        y[0] += 34
    chk = CheckBox()
    if co_dat:
        chk.Text = nhan_dat
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
    for k in ds_kho:
        cb_kho.Items.Add(k)
    dong(u"Khổ giấy:", cb_kho)
    cb_kt = ComboBox()
    cb_kt.DropDownStyle = ComboBoxStyle.DropDownList
    dong(u"Khung tên:", cb_kt)
    tb_so = TextBox()
    dong(u"Số hiệu bản vẽ:", tb_so)
    tb_ten = TextBox()
    tb_ten.Text = ten_mac_dinh
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
        if so_tay[0]:
            return
        g, h = u"%s" % (cb_gd.Text or u""), u"%s" % (cb_hm.Text or u"")
        so = goi_y_rieng(g, h, u"%s" % (tb_ten.Text or u"")) if goi_y_rieng is not None else None
        tb_so.Text = so if so is not None else _so_tiep(sheets, pid_gd, g, pid_hm, h)

    def nap_khung(*a):
        k = _khong_dau(u"%s" % cb_kho.SelectedItem)
        cb_kt.Items.Clear()
        hop = [t for t in ten_khung if k in _khong_dau(t).replace(u" ", u"") and u"bia" not in _khong_dau(t)]
        # Khung tên công ty (tên có chữ "khung") lên đầu, khung mặc định của Revit ("... metric") xuống cuối (người dùng
        # gặp 2026-11-04: sheet ngăn cháy lan nhận nhầm "A1 metric")
        hop.sort(key=lambda t: (0 if u"khung" in _khong_dau(t) else 1, 1 if u"metric" in _khong_dau(t) else 0, t))
        for t in (hop or ten_khung):
            cb_kt.Items.Add(t)
        if cb_kt.Items.Count:
            cb_kt.SelectedIndex = 0
            luu_kt = luu.get("khung_" + k)
            co_cty = u"khung" in _khong_dau(u"%s" % cb_kt.Items[0])
            for i in range(cb_kt.Items.Count):
                # lựa chọn nhớ từ lần trước là khung mặc định "metric" trong khi có khung công ty → bỏ qua
                if u"%s" % cb_kt.Items[i] == luu_kt and not (co_cty and u"metric" in _khong_dau(luu_kt)):
                    cb_kt.SelectedIndex = i

    def so_sua(*a):
        so_tay[0] = tb_so.Focused

    cb_gd.TextChanged += lambda s, e: (nap_hm(), goi_y_so())
    cb_hm.TextChanged += lambda s, e: goi_y_so()
    tb_ten.TextChanged += lambda s, e: goi_y_so()
    cb_kho.SelectedIndexChanged += nap_khung
    tb_so.TextChanged += so_sua
    cb_gd.Text = luu.get("gd", ds_gd[-1] if ds_gd else u"")
    nap_hm()
    cb_hm.Text = luu.get("hm", u"")
    cb_kho.SelectedIndex = list(ds_kho).index(luu.get("kho")) if luu.get("kho") in ds_kho else 0
    nap_khung()
    goi_y_so()

    f.ClientSize = Size(610, y[0] + 56)
    ok = Button()
    ok.Text = u"Chạy"
    ok.Size = Size(100, 30)
    ok.Location = Point(380, y[0] + 12)
    ok.DialogResult = DialogResult.OK
    huy = Button()
    huy.Text = u"Huỷ"
    huy.Size = Size(100, 30)
    huy.Location = Point(490, y[0] + 12)
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
    kq = {"dat": bool(chk.Checked) if co_dat else True, "gd": u"%s" % (cb_gd.Text or u""),
          "hm": u"%s" % (cb_hm.Text or u""), "kho": u"%s" % cb_kho.SelectedItem,
          "kt": u"%s" % (cb_kt.SelectedItem or u""), "so": u"%s" % (tb_so.Text or u""), "ten": u"%s" % (tb_ten.Text or u"")}
    luu.update({"gd": kq["gd"], "hm": kq["hm"], "kho": kq["kho"]})
    if co_dat:
        luu["dat"] = kq["dat"]
    luu["khung_" + _khong_dau(kq["kho"])] = kq["kt"]
    _ghi_luu(luu, duong_luu)
    return kq


def hoi(doc, view):
    tang = view.GenLevel.Name if view.GenLevel is not None else view.Name
    kq = _bang(doc, u"Định vị + tag cửa – đặt lên bản vẽ", True,
               u"Đặt mặt bằng định vị cửa lên bản vẽ (kèm bảng thống kê cửa đi / cửa sổ)",
               u"MẶT BẰNG ĐỊNH VỊ CỬA %s" % tang.upper(), _LUU)
    if kq is None:
        return None
    return {21: kq["dat"], 22: kq["gd"], 23: kq["hm"], 24: kq["kho"], 25: kq["kt"], 26: kq["so"], 27: kq["ten"]}


def _o_da_dung(doc, s):
    """Số ô đã có chi tiết trên sheet chi tiết cửa (mỗi ô 3 viewport)."""
    n = sum(1 for _ in DB.FilteredElementCollector(doc, s.Id).OfClass(DB.Viewport))
    return (n + 2) // 3


def _khoa_so(s):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


def hoi_chi_tiet_cua(doc, view, uidoc=None):
    """Bảng hỏi cho nút Chi tiết cửa. Số hiệu gợi ý: sheet chi tiết cửa của công cụ (có group lưới
    ARV_ChiTietCua_Luoi) số lớn nhất cùng tên + giai đoạn + hạng mục còn ô trống; không có thì số tiếp theo trong hạng
    mục (trống = công cụ tự đánh số)."""
    # Đếm như lõi ChiTietCua_TuDong.py (lay_cua): vách kính = tường có lưới curtain; tấm / đố / cửa làm tấm của vách
    # kính tính vào vách chứa nó
    n_cua, n_khac, vach = 0, 0, set()
    loai_cua = (int(DB.BuiltInCategory.OST_Doors), int(DB.BuiltInCategory.OST_Windows))
    loai_tam = loai_cua + (int(DB.BuiltInCategory.OST_CurtainWallPanels), int(DB.BuiltInCategory.OST_CurtainWallMullions))

    def la_vach(w):
        try:
            return w is not None and w.GetType().Name == "Wall" and w.CurtainGrid is not None
        except Exception:
            return False
    if uidoc is not None:
        for i in uidoc.Selection.GetElementIds():
            e = doc.GetElement(i)
            if la_vach(e):
                vach.add(e.Id.Value)
                continue
            c = e.Category.Id.Value if e is not None and e.Category is not None else None
            chu = None
            if c in loai_tam:
                try:
                    chu = e.Host
                except Exception:
                    chu = None
            if la_vach(chu):
                vach.add(chu.Id.Value)
            elif c in loai_cua:
                n_cua += 1
            else:
                n_khac += 1
    if n_cua or vach:
        ds = ([u"%d cửa đi / cửa sổ" % n_cua] if n_cua else []) + ([u"%d vách kính" % len(vach)] if vach else [])
        dong_dau = u"Đã chọn %s%s. Mỗi type / vách làm 1 lần, 6 chi tiết / bản vẽ." % (
            u" + ".join(ds), u" (bỏ qua %d đối tượng khác)" % n_khac if n_khac else u"")
    else:
        dong_dau = u"Chưa chọn cửa / vách kính: bấm Chạy rồi chọn trên màn hình, bấm Finish để xong."
    pid_gd, pid_hm = _gd_hm(doc)
    cua_cong_cu = []
    for s in DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet):
        for g in DB.FilteredElementCollector(doc, s.Id).OfClass(DB.Group):
            if _ten(g.GroupType).startswith(u"ARV_ChiTietCua_Luoi"):
                cua_cong_cu.append(s)
                break

    def goi_y(gd, hm, ten_bv):
        ung = []
        for s in cua_cong_cu:
            if s.Name != ten_bv.strip().upper():
                continue
            if pid_gd is not None and gd and _ts(s, pid_gd) is not None and _gt(_ts(s, pid_gd)) != gd:
                continue
            if pid_hm is not None and hm and _ts(s, pid_hm) is not None and _gt(_ts(s, pid_hm)) != hm:
                continue
            ung.append(s)
        ung.sort(key=lambda s: _khoa_so(s.SheetNumber))
        if ung and _o_da_dung(doc, ung[-1]) < 6:
            return ung[-1].SheetNumber
        return None

    kq = _bang(doc, u"Chi tiết cửa – đặt lên bản vẽ", False, u"", u"CHI TIẾT CỬA",
               os.path.join(_THU_MUC_LUU, "ChiTietCua_sheet.json"), dong_dau, goi_y)
    if kq is None:
        return None
    return {1: kq["kt"], 2: kq["ten"].strip().upper() or u"CHI TIẾT CỬA", 3: kq["so"].strip(), 16: kq["gd"], 17: kq["hm"]}


def _sheet_trong(doc, tu_khoa):
    """Sheet TRỐNG có sẵn (không view, không bảng thống kê) có chữ tu_khoa (không dấu) trong tên, số hiệu nhỏ nhất."""
    ds = []
    for s in DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet):
        if s.IsPlaceholder or tu_khoa not in _khong_dau(s.Name) or s.GetAllPlacedViews().Count:
            continue
        if any(not x.IsTitleblockRevisionSchedule for x in
               DB.FilteredElementCollector(doc, s.Id).OfClass(DB.ScheduleSheetInstance)):
            continue
        ds.append(s)
    ds.sort(key=lambda s: _khoa_so(s.SheetNumber))
    return ds[0] if ds else None


def _hoi_mat_bang(doc, view, tieu_de, ten_goc, tu_khoa, ten_luu):
    """Bảng hỏi đặt view vừa vẽ lên bản vẽ (Chống thấm / Ngăn cháy lan) → IN[10] – IN[16]. View đã nằm trên sheet thì
    không hỏi (lõi báo 'đã nằm trên sheet'). Có sheet trống sẵn mang tên đúng loại (vd. G19 A.4-201 MẶT BẰNG CHỐNG
    THẤM) thì gợi ý số hiệu đó = đặt vào sheet đó; xoá / đổi số hiệu để tạo sheet mới."""
    tpl = doc.GetElement(view.ViewTemplateId) if view.ViewTemplateId != DB.ElementId.InvalidElementId else None
    la_dich = tu_khoa in _khong_dau(view.Name) or (tpl is not None and tu_khoa in _khong_dau(_ten(tpl)))
    try:        # view truyền vào không phải view đích = lõi sẽ tạo view mới từ view này → luôn hỏi
        dang = view.get_Parameter(DB.BuiltInParameter.VIEWER_SHEET_NUMBER)
        if la_dich and dang is not None and dang.AsString() and dang.AsString() not in (u"---", u"-"):
            return {10: True}
    except Exception:
        pass
    tang = view.GenLevel.Name if view.GenLevel is not None else view.Name
    trong = _sheet_trong(doc, tu_khoa)
    dong_dau = u""
    if trong is not None:
        dong_dau = u"Có bản vẽ trống %s – %s: giữ số hiệu này = đặt vào bản vẽ đó." % (trong.SheetNumber, trong.Name)

    def goi_y(gd, hm, ten_bv):
        return trong.SheetNumber if trong is not None else None

    kq = _bang(doc, tieu_de, True, u"Đặt mặt bằng lên bản vẽ (kèm chú thích)", u"%s %s" % (ten_goc, tang.upper()),
               os.path.join(_THU_MUC_LUU, ten_luu), dong_dau, goi_y)
    if kq is None:
        return None
    return {10: kq["dat"], 11: kq["gd"], 12: kq["hm"], 13: kq["kho"], 14: kq["kt"], 15: kq["so"].strip(),
            16: kq["ten"].strip().upper()}


def hoi_chong_tham(doc, view):
    return _hoi_mat_bang(doc, view, u"Chống thấm – đặt lên bản vẽ", u"MẶT BẰNG CHỐNG THẤM", u"chong tham",
                         "ChongTham_sheet.json")


def hoi_ngan_chay(doc, view):
    return _hoi_mat_bang(doc, view, u"Ngăn cháy lan – đặt lên bản vẽ", u"MẶT BẰNG NGĂN CHÁY LAN", u"chay lan",
                         "NganChay_sheet.json")


def _ten_ts(doc, pid):
    """Tên tham số sheet theo Id (để lõi ghi bằng LookupParameter)."""
    if pid is None:
        return u""
    for s in DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet):
        prm = _ts(s, pid)
        if prm is not None and prm.Definition is not None:
            return prm.Definition.Name
    return u""


def _bao(tieu_de, noi_dung):
    from System.Windows.Forms import MessageBox
    if not os.environ.get("ARV_HOI_ANH"):
        MessageBox.Show(noi_dung, tieu_de)


def hoi_tuong_xay(doc, view):
    """Bảng hỏi cho nút Tường xây (thay hộp thoại 17 ô): view 'MẶT BẰNG TƯỜNG XÂY - <tầng>' của tầng đang mở, đặt lên
    bản vẽ (sheet trống có sẵn tên có chữ 'tường xây' thì gợi ý số hiệu đó = đặt vào sheet đó)."""
    tieu_de = u"Tường xây – đặt lên bản vẽ"
    tang = view.GenLevel.Name if view.GenLevel is not None else view.Name
    ten_view = u"MẶT BẰNG TƯỜNG XÂY - %s" % tang
    if any(not v.IsTemplate and v.Name == ten_view for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan)):
        _bao(tieu_de, u"Tầng %s đã có view '%s'.\n\nMuốn dựng lại: Shift+bấm nút, bật ô Làm lại." % (tang, ten_view))
        return None
    trong = _sheet_trong(doc, u"tuong xay")
    dong_dau = u""
    if trong is not None:
        dong_dau = u"Có bản vẽ trống %s – %s: giữ số hiệu này = đặt vào bản vẽ đó." % (trong.SheetNumber, trong.Name)

    def goi_y(gd, hm, ten_bv):
        return trong.SheetNumber if trong is not None else None

    kq = _bang(doc, tieu_de, True, u"Đặt mặt bằng lên bản vẽ (kèm bảng ký hiệu tường)",
               u"MẶT BẰNG TƯỜNG XÂY %s" % tang.upper(), os.path.join(_THU_MUC_LUU, "TuongXay_sheet.json"), dong_dau,
               goi_y, ds_kho=(u"A1",))
    if kq is None:
        return None
    so = kq["so"].strip()
    if kq["dat"] and not so:
        _bao(tieu_de, u"Chưa có số hiệu bản vẽ: bấm lại và nhập số hiệu (hoặc bỏ tích đặt lên bản vẽ).")
        return None
    pid_gd, pid_hm = _gd_hm(doc)
    nhom = u";".join(u"%s=%s" % (_ten_ts(doc, pid), gt) for pid, gt in ((pid_gd, kq["gd"]), (pid_hm, kq["hm"]))
                     if pid is not None and gt.strip() and _ten_ts(doc, pid))
    return {0: tang, 1: ten_view, 4: so, 5: kq["ten"].strip().upper() or u"MẶT BẰNG TƯỜNG XÂY", 6: kq["kt"],
            15: nhom, 17: kq["dat"]}
