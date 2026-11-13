# -*- coding: utf-8 -*-
# Nút "Hồ sơ đã duyệt" (người dùng yêu cầu 2026-11-13: "sinh ra 1 nút để lúc ấn có thể chuyển những gì đã trình bày –
# chống thấm, chống cháy lan, lan can louver, định vị cửa – vào file chính").
#
# Extension RIÊNG ARVHoSoDuyet.extension (người dùng 2026-11-13: "sinh nút mới ở trên thanh công cụ, đừng động gì đến
# archivina, để t có thể gỡ"): mọi thứ của nút nằm trong extension này; ARVTools.extension (tab Archivina) chỉ được ĐỌC
# và chạy, không sửa. Gỡ nút = bỏ thư mục extension này rồi Reload pyRevit.
#
# Cách làm: KHÔNG chép phần tử từ file duyệt sang (tag / dim bám đối tượng trong file link không chép được giữa 2 file).
# Nút chạy lại đúng các nút HS TKBVTC (Chống thấm, Ngăn cháy lan, Định vị lan can louver, Định vị + tag cửa) trên từng
# mặt bằng, trả lời sẵn hộp thoại "đặt lên bản vẽ" bằng PHƯƠNG ÁN ĐÃ DUYỆT (view template, tỉ lệ, giai đoạn, hạng mục, khổ,
# khung tên, số hiệu, tên bản vẽ) ghi trong lib\ho_so_duyet\<mã>.json. Kết quả = file người dùng đã duyệt.
#
#   - Tag cửa (người dùng 2026-11-13: "bản định vị cửa sắp xếp còn rối mắt"): bảng kiểm có ô chọn kiểu tag. "gon" / "2o"
#     = nút Định vị + tag cửa chạy bằng LÕI RIÊNG lib\loi_rieng\TagCua_xep_lai.py (xếp lại: trượt dọc tường, quay vuông
#     góc trước cửa, ít leader; "gon" = tag 1 ô chỉ mã) – thay lúc nạp qua arv_dynamo_host.load_core, không sửa file nào
#     của Archivina; "goc" = đúng lõi của Archivina.
#   - Cấu hình nhận theo tên file đang mở ("nhan_file"); không khớp thì hỏi lại trước khi chạy.
#   - Trước khi chạy: bảng kiểm từng mục (mặt bằng nguồn, view đích, bản vẽ, template, khung tên) → người dùng bấm Chạy.
#     Mục thiếu mặt bằng nguồn không chạy được; mục khác bỏ tích để không làm.
#   - Không xoá, không sửa view template. View đích đã nằm trên bản vẽ: giữ template / tỉ lệ đang có, lõi chỉ bổ sung
#     phần còn thiếu (các lõi "bấm lại không trùng").
#   - Kết quả nhận diện CAD của lần duyệt (lib\ho_so_duyet\<mã>\cad\) được chép vào thư mục đệm của lõi nếu ở đó chưa có
#     → không phải chạy lại AutoCAD; DWG / script nhận diện đã đổi thì khoá đệm khác, lõi tự nhận diện lại.
#   - Hoàn tác: cả lần bấm gom 1 TransactionGroup = 1 mục Undo (thử 2026-11-13: Revit 2027.3 cho đổi view khi group
#     đang mở; nếu không đổi được thì gom group, đổi view, mở group mới → mỗi tầng 1 mục Undo).
#   - Log đầy đủ: Documents\ARV_Logs\ho_so_duyet\ho_so_duyet_<giờ>.txt
# Biến môi trường chỉ dùng khi thử nền: ARV_HO_SO_DUYET_LOG (thư mục log gốc), ARV_HOI_ANH (vẽ bảng kiểm ra PNG, coi như
# bấm Chạy), ARV_HO_SO_DUYET_KHONG_NHOM=1 (không dùng TransactionGroup), ARV_HO_SO_DUYET_CHI = "<view>|<nút>;..." (chỉ
# chạy các mục đó), ARV_HO_SO_DUYET_TAG = gon / 2o / goc (kiểu tag thay lựa chọn trong bảng).
import io
import os
import sys
import json
import glob
import shutil
import datetime
import traceback
import unicodedata

import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
import Autodesk.Revit.DB as DB
import Autodesk.Revit.UI as UI

import arv_hoi_sheet

_HERE = os.path.dirname(os.path.abspath(__file__))
THU_MUC_CAU_HINH = os.path.join(_HERE, "ho_so_duyet")
TIEU_DE = u"Hồ sơ đã duyệt"

# Nút HS TKBVTC chạy được trong hồ sơ đã duyệt. ham: hàm hỏi trong arv_hoi_sheet (bị thay bằng câu trả lời đã duyệt);
# dich / in_tpl / in_tl: chỉ số IN như arv_hoi_sheet._doi_in; in_log + log: ô thư mục log của lõi + tên thư mục mặc định
NUT = {
    "ChongTham": {"nhan": u"Chống thấm", "tu_khoa": u"chong tham", "ten_goc": u"MẶT BẰNG CHỐNG THẤM",
                  "ham": "hoi_chong_tham", "dich": 0, "in_tpl": 19, "in_tl": 20, "in_log": 6, "log": "chong_tham",
                  "hoi_chon": True},
    "NganChay": {"nhan": u"Ngăn cháy lan", "tu_khoa": u"chay lan", "ten_goc": u"MẶT BẰNG NGĂN CHÁY LAN",
                 "ham": "hoi_ngan_chay", "dich": 0, "in_tpl": 19, "in_tl": 20, "in_log": 5, "log": "ngan_chay",
                 "hoi_chon": True},
    "LanCanLouver": {"nhan": u"Định vị lan can, louver", "tu_khoa": u"dinh vi lan can",
                     "ten_goc": u"MẶT BẰNG ĐỊNH VỊ LAN CAN, LOUVER", "ham": "hoi_lan_can_louver", "dich": 7,
                     "in_tpl": 25, "in_tl": 26, "in_log": 9, "log": "lan_can_louver"},
    "TagCua": {"nhan": u"Định vị + tag cửa", "tu_khoa": u"dinh vi cua", "ten_goc": u"MẶT BẰNG ĐỊNH VỊ CỬA",
               "ham": "hoi", "in_tpl": 28, "in_tl": 29, "in_log": 10, "log": "tag_cua"},
}
THU_TU = ("ChongTham", "NganChay", "LanCanLouver", "TagCua")
# Dòng báo cáo của lõi đưa vào bảng tóm tắt (đủ ở file log)
DONG_CHINH = (u"ĐÃ VẼ", u"ĐÃ ĐẶT", u"Đã đặt mặt bằng", u"Đã tag", u"Dùng sheet trống", u"Số hiệu '", u"CẦN XEM LẠI",
              u"LỖI", u"Traceback", u"Phòng ướt theo CAD", u"Trục / hộp kỹ thuật cần hatch", u"Không có ", u"Chưa có ",
              u"Bản xếp lại")
_DANG = {}          # mục đang chạy (hàm trả lời hộp thoại đọc ở đây)
# Kiểu tag cửa: (mã, chữ hiện trong bảng kiểm). "gon" / "2o" chạy lõi riêng xếp lại; "goc" = lõi của Archivina
KIEU_TAG = (("chu", u"Chỉ chữ mã, không khung – gọn nhất, tag nằm sát cửa (kích thước xem bảng thống kê)"),
            ("gon", u"Khung 1 ô 10 × 3,5 mm, chỉ mã – xếp lại"),
            ("2o", u"Khung 2 ô mã / rộngXcao – xếp lại"),
            ("goc", u"Như nút Định vị + tag cửa của Archivina (2 ô, cách xếp cũ)"))
ENV_TAG = {"chu": "2", "gon": "1"}      # giá trị ARV_TAG_GON cho lõi riêng
LOI_TAG_RIENG = os.path.join(_HERE, "loi_rieng", "TagCua_xep_lai.py")


def kd(s):
    s = unicodedata.normalize("NFD", u"{}".format(s or u"")).replace(u"đ", u"d").replace(u"Đ", u"D")
    return u"".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def _ten(e):
    return arv_hoi_sheet._ten(e)


def thu_muc_log():
    return os.environ.get("ARV_HO_SO_DUYET_LOG") or os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")


# ---------------------------------------------------------------- cấu hình

def doc_cau_hinh():
    """[(đường dẫn, dict)] mọi cấu hình hợp lệ trong lib\\ho_so_duyet\\*.json."""
    ds = []
    for p in sorted(glob.glob(os.path.join(THU_MUC_CAU_HINH, "*.json"))):
        try:
            with io.open(p, "r", encoding="utf-8-sig") as f:
                d = json.load(f)
            if d.get("mat_bang"):
                d["_ma"] = os.path.splitext(os.path.basename(p))[0]
                ds.append((p, d))
        except Exception:
            pass
    return ds


def ten_file(doc):
    try:
        if doc.PathName:
            return os.path.basename(doc.PathName)
    except Exception:
        pass
    return u"%s" % doc.Title


def khop(doc, ch):
    t = kd(ten_file(doc))
    return any(kd(k) in t for k in ch.get("nhan_file", []) if k)


def cac_muc(ch):
    """Danh sách mục theo thứ tự chạy: mỗi mặt bằng lần lượt các nút THU_TU. Giá trị = chung < nut < mục."""
    ra = []
    chung = ch.get("chung", {})
    for mb in ch.get("mat_bang", []):
        for nut in THU_TU:
            rieng = (mb.get("viec") or {}).get(nut)
            if rieng is None or nut not in NUT:
                continue
            d = {}
            d.update(chung)
            d.update((ch.get("nut") or {}).get(nut, {}))
            d.update(rieng)
            ra.append({"view": mb["view"], "nut": nut, "so": (d.get("so") or u"").strip(),
                       "ten": (d.get("ten") or u"").strip(), "tpl": (d.get("template") or u"").strip(),
                       "tl": int(d.get("ti_le") or 0), "gd": d.get("giai_doan") or u"", "hm": d.get("hang_muc") or u"",
                       "kho": d.get("kho") or u"A1", "kt": d.get("khung_ten") or u""})
    return ra


# ---------------------------------------------------------------- đọc mô hình

def mat_bang_nguon(doc, ten):
    ung = [v for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan)
           if not v.IsTemplate and v.Name == ten and v.GenLevel is not None]
    ung.sort(key=lambda v: 0 if v.ViewType == DB.ViewType.FloorPlan else 1)
    return ung[0] if ung else None


def _tpl_cua(doc, v):
    return doc.GetElement(v.ViewTemplateId) if v.ViewTemplateId != DB.ElementId.InvalidElementId else None


def view_dich(doc, mb, nut):
    """View đích của nút trên tầng của mặt bằng mb, tìm như lõi: Định vị + tag cửa = mặt bằng tên 'MẶT BẰNG ĐỊNH VỊ CỬA -
    <tầng>'; nút khác = mặt bằng cùng tầng có chữ khoá trong tên view / tên view template (xếp theo tên)."""
    lv = mb.GenLevel.Id.Value
    ds = []
    for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan):
        if v.IsTemplate or v.ViewType != DB.ViewType.FloorPlan or v.GenLevel is None or v.GenLevel.Id.Value != lv:
            continue
        if nut == "TagCua":
            if v.Name == u"%s - %s" % (NUT[nut]["ten_goc"], mb.GenLevel.Name):
                ds.append(v)
        else:
            t = _tpl_cua(doc, v)
            if NUT[nut]["tu_khoa"] in kd(v.Name) or (t is not None and NUT[nut]["tu_khoa"] in kd(_ten(t))):
                ds.append(v)
    ds.sort(key=lambda v: v.Name)
    return ds


def so_sheet_cua(view):
    try:
        p = view.get_Parameter(DB.BuiltInParameter.VIEWER_SHEET_NUMBER)
        s = p.AsString() if p is not None else None
        return s if s and s not in (u"---", u"-") else None
    except Exception:
        return None


def _sheet_trong(doc, s):
    if s.IsPlaceholder or s.GetAllPlacedViews().Count:
        return False
    return not any(not x.IsTitleblockRevisionSchedule
                   for x in DB.FilteredElementCollector(doc, s.Id).OfClass(DB.ScheduleSheetInstance))


def kiem_tra(doc, muc_ds):
    """Điền cho từng mục: duoc (chạy được), tinh_trang (chữ hiện trong bảng), canh_bao (bool)."""
    sheets = dict((s.SheetNumber, s) for s in DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet))
    tpl_co = set(_ten(t) for t in arv_hoi_sheet._templates(doc))
    khung = set(u"%s : %s" % (s.FamilyName, _ten(s)) for s in DB.FilteredElementCollector(doc)
                .OfClass(DB.FamilySymbol).OfCategory(DB.BuiltInCategory.OST_TitleBlocks))
    for m in muc_ds:
        m["duoc"], m["canh_bao"] = True, False
        mb = mat_bang_nguon(doc, m["view"])
        if mb is None:
            m["duoc"], m["canh_bao"] = False, True
            m["tinh_trang"] = u"KHÔNG CHẠY: file không có mặt bằng tầng tên '%s'" % m["view"]
            continue
        y = []
        dich = view_dich(doc, mb, m["nut"])
        dang = so_sheet_cua(dich[0]) if dich else None
        if dang:
            y.append(u"đã nằm trên bản vẽ %s%s, chỉ bổ sung phần thiếu (view '%s')" % (
                dang, u"" if dang == m["so"] else u" (khác số duyệt %s)" % m["so"], dich[0].Name))
        else:
            y.append(u"dùng view có sẵn '%s'" % dich[0].Name if dich else u"tạo view mới")
            sh = sheets.get(m["so"])
            if sh is None:
                y.append(u"tạo bản vẽ mới %s" % m["so"])
            elif _sheet_trong(doc, sh):
                y.append(u"đặt vào bản vẽ trống có sẵn %s – %s" % (m["so"], sh.Name))
            else:
                m["canh_bao"] = True
                y.append(u"LƯU Ý: số %s đã có nội dung khác → lõi dùng số kế tiếp" % m["so"])
        if NUT[m["nut"]].get("hoi_chon") and len(dich) > 1:
            m["canh_bao"] = True
            y.append(u"LƯU Ý: tầng có %d view cùng loại → nút hỏi chọn view" % len(dich))
        if m["tpl"] and m["tpl"] not in tpl_co:
            m["canh_bao"] = True
            y.append(u"LƯU Ý: thiếu view template '%s' (giữ template đang có)" % m["tpl"])
        if m["kt"] and m["kt"] not in khung and not dang:
            m["canh_bao"] = True
            y.append(u"LƯU Ý: thiếu khung tên '%s'" % m["kt"])
        m["tinh_trang"] = u"; ".join(y)
    return muc_ds


# ---------------------------------------------------------------- bảng kiểm trước khi chạy

def hoi_ke_hoach(ch, ten_f, muc_ds, khop_ten, ghi_chu_tag=u""):
    """Bảng kiểm. Trả về (danh sách mục được tích, kiểu tag cửa "gon" / "2o" / "goc"); (None, None) = Huỷ."""
    clr.AddReference("System.Windows.Forms")
    clr.AddReference("System.Drawing")
    from System.Windows.Forms import (Form, Label, ListView, ListViewItem, ColumnHeaderStyle, Button, DialogResult,
                                      FormStartPosition, FormBorderStyle, CheckState)
    from System.Windows.Forms import View as KieuXem
    from System.Drawing import Size, Point, Font, FontStyle, Color
    f = Form()
    f.Text = TIEU_DE
    f.StartPosition = FormStartPosition.CenterScreen
    f.FormBorderStyle = FormBorderStyle.FixedDialog
    f.MaximizeBox = False
    f.MinimizeBox = False
    f.Font = Font("Segoe UI", 9.0)
    rong = 1040
    y = 12
    lb = Label()
    lb.Text = ch.get("ten", ch["_ma"])
    lb.Font = Font(f.Font, FontStyle.Bold)
    lb.Location = Point(14, y)
    lb.Size = Size(rong - 28, 20)
    f.Controls.Add(lb)
    y += 22
    lb2 = Label()
    lb2.Text = u"File đang mở: %s%s" % (ten_f, u"" if khop_ten else u"   –   TÊN FILE KHÔNG KHỚP hồ sơ đã duyệt (%s)" % (
        u", ".join(ch.get("nhan_file", []))))
    if not khop_ten:
        lb2.ForeColor = Color.FromArgb(170, 60, 0)
    lb2.Location = Point(14, y)
    lb2.Size = Size(rong - 28, 20)
    f.Controls.Add(lb2)
    y += 26
    lv = ListView()
    lv.View = KieuXem.Details
    lv.CheckBoxes = True
    lv.FullRowSelect = True
    lv.GridLines = True
    lv.HeaderStyle = ColumnHeaderStyle.Nonclickable
    lv.Location = Point(14, y)
    cao = min(max(len(muc_ds), 6), 22) * 20 + 36
    lv.Size = Size(rong - 28, cao)
    for nhan, w in ((u"Mặt bằng", 104), (u"Việc", 150), (u"Bản vẽ duyệt", 92), (u"Tỉ lệ", 50), (u"Tình trạng trong file đang mở", rong - 28 - 104 - 150 - 92 - 50 - 6)):
        lv.Columns.Add(nhan, w)
    for m in muc_ds:
        it = ListViewItem(m["view"])
        it.SubItems.Add(NUT[m["nut"]]["nhan"])
        it.SubItems.Add(m["so"])
        it.SubItems.Add(u"1:%d" % m["tl"] if m["tl"] else u"")
        it.SubItems.Add(m["tinh_trang"])
        it.Checked = bool(m["duoc"])
        if not m["duoc"]:
            it.ForeColor = Color.Gray
        elif m["canh_bao"]:
            it.ForeColor = Color.FromArgb(170, 60, 0)
        lv.Items.Add(it)

    def chan(sender, e):                 # mục không chạy được thì không tích được
        if not muc_ds[e.Index]["duoc"]:
            e.NewValue = CheckState.Unchecked

    lv.ItemCheck += chan
    f.Controls.Add(lv)
    y += cao + 8
    n_duoc = sum(1 for m in muc_ds if m["duoc"])
    lb3 = Label()
    lb3.Text = (u"Bấm Chạy: lần lượt chạy các mục đang tích bằng đúng các nút HS TKBVTC, trả lời sẵn theo phương án đã duyệt "
                u"(không hỏi lại từng nút). Không xoá gì, không sửa view template; mục đã làm rồi thì không vẽ trùng.\n"
                u"Revit sẽ bận vài phút. Hoàn tác: Ctrl+Z 1 lần cho cả lần bấm (báo cáo cuối ghi rõ). Nên Synchronize / lưu "
                u"file trước khi chạy.")
    lb3.Location = Point(14, y)
    lb3.Size = Size(rong - 28, 52)
    f.Controls.Add(lb3)
    y += 56
    # Kiểu tag cửa (chỉ khi có mục Định vị + tag cửa)
    from System.Windows.Forms import ComboBox, ComboBoxStyle
    cb_tag = ComboBox()
    co_tag = any(m["nut"] == "TagCua" for m in muc_ds)
    if co_tag:
        lb4 = Label()
        lb4.Text = u"Tag cửa:"
        lb4.Location = Point(14, y + 7)
        lb4.Size = Size(56, 20)
        f.Controls.Add(lb4)
        cb_tag.DropDownStyle = ComboBoxStyle.DropDownList
        for _, chu in KIEU_TAG:
            cb_tag.Items.Add(chu)
        ma_ds = [k for k, _ in KIEU_TAG]
        mac_dinh = ch.get("tag_cua") if ch.get("tag_cua") in ma_ds else "chu"
        if not os.path.isfile(LOI_TAG_RIENG):
            mac_dinh = "goc"
        cb_tag.SelectedIndex = ma_ds.index(mac_dinh)
        cb_tag.Location = Point(72, y + 3)
        cb_tag.Size = Size(520, 24)
        f.Controls.Add(cb_tag)
        if ghi_chu_tag:
            lb5 = Label()
            lb5.Text = ghi_chu_tag
            lb5.ForeColor = Color.FromArgb(170, 60, 0)
            lb5.Location = Point(14, y + 32)
            lb5.Size = Size(rong - 260, 20)
            f.Controls.Add(lb5)
    ok = Button()
    ok.Text = u"Chạy"
    ok.Size = Size(100, 30)
    ok.Location = Point(rong - 228, y)
    ok.DialogResult = DialogResult.OK
    ok.Enabled = n_duoc > 0
    huy = Button()
    huy.Text = u"Huỷ"
    huy.Size = Size(100, 30)
    huy.Location = Point(rong - 118, y)
    huy.DialogResult = DialogResult.Cancel
    f.Controls.Add(ok)
    f.Controls.Add(huy)
    f.AcceptButton = ok
    f.CancelButton = huy
    f.ClientSize = Size(rong, y + 44)
    anh_thu = os.environ.get("ARV_HOI_ANH")          # chỉ khi thử: vẽ bảng ra PNG, không hiện cửa sổ, coi như bấm Chạy
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
        return None, None
    kieu = KIEU_TAG[cb_tag.SelectedIndex][0] if co_tag and cb_tag.SelectedIndex >= 0 else "goc"
    return [m for i, m in enumerate(muc_ds) if m["duoc"] and lv.Items[i].Checked], kieu


# ---------------------------------------------------------------- trả lời sẵn hộp thoại của từng nút

def _tpl_tl(doc, view, nut, m):
    """(tên template, tỉ lệ) truyền cho lõi: phương án đã duyệt; riêng view đích đã nằm trên bản vẽ thì giữ template /
    tỉ lệ đang có (không đổi cách trình bày người dùng đã đặt lên bản vẽ)."""
    mb = mat_bang_nguon(doc, m["view"]) or view
    dich = view_dich(doc, mb, nut)
    if dich and so_sheet_cua(dich[0]):
        t = _tpl_cua(doc, dich[0])
        tl = t.Scale if t is not None and arv_hoi_sheet._tpl_khoa_tl(t) else dich[0].Scale
        return (_ten(t) if t is not None else arv_hoi_sheet.KHONG_TPL), tl
    return (m["tpl"] or u""), (m["tl"] or view.Scale)


def _tra_loi(nut):
    """Hàm thay arv_hoi_sheet.<ham>: cùng dạng kết quả {IN: giá trị} nhưng không hiện hộp thoại."""
    tt = NUT[nut]

    def ham(doc, view, *a):
        m = _DANG.get("muc")
        if m is None or m["nut"] != nut:
            return None
        tang = view.GenLevel.Name if view.GenLevel is not None else view.Name
        ten_bv = m["ten"] or u"%s %s" % (tt["ten_goc"], tang.upper())
        tpl, tl = _tpl_tl(doc, view, nut, m)
        if nut == "TagCua":             # như arv_hoi_sheet.hoi
            ra = {6: False, 21: True, 22: m["gd"], 23: m["hm"], 24: m["kho"], 25: m["kt"], 26: m["so"], 27: ten_bv}
        else:                           # như arv_hoi_sheet._hoi_mat_bang + _doi_in
            t = _tpl_cua(doc, view)
            la_dich = tt["tu_khoa"] in kd(view.Name) or (t is not None and tt["tu_khoa"] in kd(_ten(t)))
            if la_dich and so_sheet_cua(view):
                kq = {10: True}
            else:
                kq = {10: True, 11: m["gd"], 12: m["hm"], 13: m["kho"], 14: m["kt"], 15: m["so"], 16: ten_bv.upper()}
            ra = dict((k + tt["dich"], v) for k, v in kq.items())
        ra[tt["in_tpl"]] = tpl
        ra[tt["in_tl"]] = float(tl)
        ra[tt["in_log"]] = os.path.join(thu_muc_log(), tt["log"])
        _DANG["tra_loi"] = ra
        return ra
    return ham


# ---------------------------------------------------------------- kết quả nhận diện CAD của lần duyệt

def chep_dem_cad(ch, ghi):
    """Chép lib\\ho_so_duyet\\<mã>\\cad\\<log nút>\\<thư mục khoá> → <log>\\<log nút>\\cad\\ nếu chưa có (không ghi đè)."""
    goc = os.path.join(THU_MUC_CAU_HINH, ch["_ma"], "cad")
    n = 0
    if not os.path.isdir(goc):
        return 0
    for ten_nut in os.listdir(goc):
        for td in glob.glob(os.path.join(goc, ten_nut, "*")):
            if not os.path.isdir(td):
                continue
            dich = os.path.join(thu_muc_log(), ten_nut, "cad", os.path.basename(td))
            if os.path.isdir(dich):
                continue
            try:
                shutil.copytree(td, dich)
                n += 1
            except Exception as ex:
                ghi(u"Không chép được kết quả nhận diện CAD %s: %s" % (os.path.basename(td), ex))
    return n


# ---------------------------------------------------------------- chạy

class _Bat(object):
    """Hứng chữ các nút in ra (để gom báo cáo)."""

    def __init__(self, ghi):
        self._ghi = ghi
        self.dong = []

    def write(self, s):
        for ln in u"{}".format(s or u"").splitlines():
            if ln.strip():
                self.dong.append(ln.rstrip())
                self._ghi(u"   | " + ln.rstrip())

    def flush(self):
        pass


class _UiDocGia(object):
    """Bỏ RequestViewChange cuối mỗi nút (yêu cầu đổi view còn treo làm nút sau chạy nhầm view)."""

    def __init__(self, u):
        self._u = u

    def __getattr__(self, n):
        return getattr(self._u, n)

    def RequestViewChange(self, v):
        pass


class _UiAppGia(object):
    def __init__(self, a):
        self._a = a

    def __getattr__(self, n):
        return getattr(self._a, n)

    @property
    def ActiveUIDocument(self):
        return _UiDocGia(self._a.ActiveUIDocument)


class _Nhom(object):
    """TransactionGroup bọc các lần chạy → gom mục Undo."""

    def __init__(self, doc, ghi):
        self._doc, self._ghi, self._tg, self.so_nhom = doc, ghi, None, 0
        self.tat = bool(os.environ.get("ARV_HO_SO_DUYET_KHONG_NHOM"))

    def mo(self, ten):
        if self.tat or self._tg is not None:
            return
        try:
            self._tg = DB.TransactionGroup(self._doc, ten)
            self._tg.Start()
            self.so_nhom += 1
        except Exception as ex:
            self._tg = None
            self.tat = True
            self._ghi(u"Không mở được TransactionGroup (%s) – chạy không gom Undo." % ex)

    def dong(self):
        if self._tg is None:
            return
        try:
            self._tg.Assimilate()
        except Exception as ex:
            self._ghi(u"Không gom được Undo: %s" % ex)
        self._tg = None


def _doi_view(uidoc, doc, v, nhom, ten_nhom):
    """Mở mặt bằng v. Đang trong TransactionGroup mà Revit không cho đổi view thì gom group, đổi view, mở group mới."""
    if doc.ActiveView is not None and doc.ActiveView.Id.Value == v.Id.Value:
        return
    try:
        uidoc.ActiveView = v
    except Exception:
        pass
    if doc.ActiveView is None or doc.ActiveView.Id.Value != v.Id.Value:
        nhom.dong()
        uidoc.ActiveView = v
        nhom.mo(ten_nhom)
    if doc.ActiveView is None or doc.ActiveView.Id.Value != v.Id.Value:
        raise Exception(u"Không mở được mặt bằng '%s' – mục này không chạy." % v.Name)


def _chay_nut(uiapp, panel_dir, nut, ghi):
    sp = os.path.join(panel_dir, nut + ".pushbutton", "script.py")
    bat = _Bat(ghi)
    if not os.path.isfile(sp):
        bat.write(u"LỖI: không thấy nút %s (%s)" % (nut, sp))
        return bat.dong
    cu = sys.stdout
    sys.stdout = bat
    try:
        with io.open(sp, encoding="utf-8") as f_:
            ma = f_.read()
        exec(compile(ma, sp, "exec"), {"__revit__": _UiAppGia(uiapp), "__file__": sp, "__name__": "__main__"})
    except BaseException:
        bat.write(u"LỖI: " + traceback.format_exc())
    finally:
        sys.stdout = cu
    return bat.dong


def _thay_loi_tag(kieu_tag, ghi):
    """Kiểu tag "gon" / "2o": nút Định vị + tag cửa của Archivina nạp lõi riêng LOI_TAG_RIENG thay core.py của nó (thay
    lúc nạp, không sửa file của Archivina; __file__ của lõi vẫn là core.py gốc nên family đóng gói lib\\tag_cua vẫn tìm
    đúng). Trả về hàm trả lại như cũ."""
    import arv_dynamo_host
    goc = arv_dynamo_host.load_core
    cu_gon = os.environ.get("ARV_TAG_GON")
    if kieu_tag in ("chu", "gon", "2o") and os.path.isfile(LOI_TAG_RIENG):
        def nap(core_path):
            if os.path.basename(os.path.dirname(core_path)) == "TagCua.pushbutton":
                return goc(LOI_TAG_RIENG)
            return goc(core_path)
        arv_dynamo_host.load_core = nap
        if kieu_tag in ENV_TAG:
            os.environ["ARV_TAG_GON"] = ENV_TAG[kieu_tag]
        else:
            os.environ.pop("ARV_TAG_GON", None)
        ghi(u"Tag cửa: kiểu '%s' – lõi riêng %s" % (kieu_tag, LOI_TAG_RIENG))
    else:
        ghi(u"Tag cửa: lõi của Archivina (không xếp lại)")

    def tra_lai():
        arv_dynamo_host.load_core = goc
        if cu_gon is None:
            os.environ.pop("ARV_TAG_GON", None)
        else:
            os.environ["ARV_TAG_GON"] = cu_gon
    return tra_lai


def chay(uiapp, panel_dir):
    """panel_dir: thư mục HoSo.panel của ARVTools.extension (chứa các nút <Tên>.pushbutton được chạy)."""
    uidoc = uiapp.ActiveUIDocument
    if uidoc is None:
        UI.TaskDialog.Show(TIEU_DE, u"Chưa mở dự án nào.")
        return
    doc = uidoc.Document
    if doc.IsFamilyDocument:
        UI.TaskDialog.Show(TIEU_DE, u"Đang mở family. Mở file dự án rồi bấm lại.")
        return
    ds = doc_cau_hinh()
    if not ds:
        UI.TaskDialog.Show(TIEU_DE, u"Chưa có hồ sơ đã duyệt nào (thư mục %s trống)." % THU_MUC_CAU_HINH)
        return
    ung = [d for _, d in ds if khop(doc, d)]
    khop_ten = bool(ung)
    if not ung:
        if len(ds) > 1:
            UI.TaskDialog.Show(TIEU_DE, u"File đang mở '%s' không khớp hồ sơ đã duyệt nào:\n\n%s" % (
                ten_file(doc), u"\n".join(u"- %s (file tên có: %s)" % (d.get("ten", d["_ma"]), u", ".join(
                    d.get("nhan_file", []))) for _, d in ds)))
            return
        ung = [ds[0][1]]            # chỉ có 1 hồ sơ: vẫn hiện bảng kiểm, ghi rõ tên file không khớp
    ch = ung[0]
    muc_ds = kiem_tra(doc, cac_muc(ch))
    ghi_chu_tag = u""
    try:
        if any(s.FamilyName in (u"AV_Door Tag", u"AV_Window Tag") for s in DB.FilteredElementCollector(doc).OfClass(DB.FamilySymbol)
               if s.Category is not None and s.Category.Id.Value in (int(DB.BuiltInCategory.OST_DoorTags),
                                                                    int(DB.BuiltInCategory.OST_WindowTags))):
            ghi_chu_tag = u"File đã có family tag AV_Door / AV_Window Tag: khung tag giữ kiểu đang có."
    except Exception:
        pass
    chon, kieu_tag = hoi_ke_hoach(ch, ten_file(doc), muc_ds, khop_ten, ghi_chu_tag)
    if os.environ.get("ARV_HOI_ANH"):          # chỉ khi thử nền
        if os.environ.get("ARV_HO_SO_DUYET_TAG"):
            kieu_tag = os.environ["ARV_HO_SO_DUYET_TAG"]
        if os.environ.get("ARV_HO_SO_DUYET_CHI") and chon:
            chi = set(os.environ["ARV_HO_SO_DUYET_CHI"].split(";"))
            chon = [m for m in chon if u"%s|%s" % (m["view"], m["nut"]) in chi]
    if not chon:
        return

    t0 = datetime.datetime.now()
    td_log = os.path.join(thu_muc_log(), "ho_so_duyet")
    if not os.path.isdir(td_log):
        os.makedirs(td_log)
    duong_log = os.path.join(td_log, "ho_so_duyet_%s.txt" % t0.strftime("%Y%m%d_%H%M%S"))
    flog = io.open(duong_log, "w", encoding="utf-8")

    def ghi(s):
        flog.write(u"{}\n".format(s))
        flog.flush()

    ghi(u"%s – %s" % (TIEU_DE, ch.get("ten", ch["_ma"])))
    ghi(u"File: %s | bắt đầu %s | %d mục" % (doc.PathName or doc.Title, t0.strftime("%Y-%m-%d %H:%M:%S"), len(chon)))
    n_dem = chep_dem_cad(ch, ghi)
    if n_dem:
        ghi(u"Chép %d kết quả nhận diện CAD của lần duyệt vào thư mục đệm (DWG / script đã đổi thì lõi tự nhận diện lại)." % n_dem)
    tra_loi_tag = _thay_loi_tag(kieu_tag, ghi)
    av_goc = doc.ActiveView
    goc = dict((NUT[n]["ham"], getattr(arv_hoi_sheet, NUT[n]["ham"])) for n in NUT)
    for n in NUT:
        setattr(arv_hoi_sheet, NUT[n]["ham"], _tra_loi(n))
    nhom = _Nhom(doc, ghi)
    ket_qua = []
    try:
        nhom.mo(TIEU_DE)
        for m in chon:
            kq = {"muc": m, "dong": [], "sheet": None, "loi": False}
            ket_qua.append(kq)
            ghi(u"=== %s – %s (%s) %s" % (m["view"], NUT[m["nut"]]["nhan"], m["so"],
                                         datetime.datetime.now().strftime("%H:%M:%S")))
            try:
                mb = mat_bang_nguon(doc, m["view"])
                _doi_view(uidoc, doc, mb, nhom, TIEU_DE)
                _DANG.clear()
                _DANG["muc"] = m
                kq["dong"] = _chay_nut(uiapp, panel_dir, m["nut"], ghi)
                if _DANG.get("tra_loi") is not None:
                    ghi(u"   trả lời hộp thoại: %s" % _DANG["tra_loi"])
                dich = view_dich(doc, mb, m["nut"])
                kq["sheet"] = so_sheet_cua(dich[0]) if dich else None
                kq["view"] = dich[0].Name if dich else None
            except BaseException:
                kq["dong"].append(u"LỖI: " + traceback.format_exc())
                ghi(u"   LỖI: " + traceback.format_exc())
            kq["loi"] = any(ln.strip().startswith((u"LỖI", u"Traceback")) for ln in kq["dong"])
    finally:
        _DANG.clear()
        for k, v in goc.items():
            setattr(arv_hoi_sheet, k, v)
        tra_loi_tag()
        nhom.dong()
    try:
        if av_goc is not None and doc.ActiveView.Id.Value != av_goc.Id.Value:
            uidoc.ActiveView = av_goc
    except Exception:
        pass

    # ---- báo cáo
    giay = (datetime.datetime.now() - t0).total_seconds()
    n_loi = sum(1 for k in ket_qua if k["loi"])
    n_sheet = sum(1 for k in ket_qua if k["sheet"])
    dong = [u"%s – %s" % (TIEU_DE, ch.get("ten", ch["_ma"])),
            u"File: %s" % (doc.PathName or doc.Title),
            u"Xong %d mục trong %d phút %02d giây: %d mục đã nằm trên bản vẽ, %d mục có LỖI." % (
                len(ket_qua), int(giay) // 60, int(giay) % 60, n_sheet, n_loi),
            u"Hoàn tác: Ctrl+Z %s. Chưa lưu file – xem xong rồi tự lưu / Synchronize." % (
                u"%d lần (mỗi lần 1 nhóm '%s')" % (nhom.so_nhom, TIEU_DE) if nhom.so_nhom else u"từng bước của từng nút"),
            u"Log đầy đủ: %s" % duong_log, u"-" * 100]
    for k in ket_qua:
        m = k["muc"]
        dong.append(u"%-12s | %-24s | %s%s" % (m["view"], NUT[m["nut"]]["nhan"],
                                              u"bản vẽ %s" % k["sheet"] if k["sheet"] else u"CHƯA nằm trên bản vẽ",
                                              u"  (view '%s')" % k["view"] if k.get("view") else u""))
        for ln in k["dong"]:
            s = ln.strip()
            if s.startswith(DONG_CHINH):
                dong.append(u"      " + s[:400])
    for ln in dong:
        ghi(ln)
    flog.close()
    try:
        from pyrevit import script
        out = script.get_output()
        out.set_title(TIEU_DE)
    except Exception:
        pass
    for ln in dong:
        print(ln)
    return ket_qua
