#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Bảng thống kê cửa của mặt bằng đang mở (người dùng yêu cầu 2026-11-04: "tạo 1 bảng thống kê các cửa có trong mặt bằng đó, những cửa trùng thì hiện 1 lần"): - Mỗi hạng mục 1 bảng: "THỐNG KÊ CỬA ĐI - <tầng>", "THỐNG KÊ CỬA SỔ - <tầng>" (Revit không gộp được cửa đi + cửa sổ vào 1 bảng: bảng nhiều hạng mục không có cột Rộng / Cao và bộ lọc không có "hoặc" – khảo sát Revit 2027.3). - Cột: Ký hiệu (Type Mark) / Rộng / Cao / Số lượng; KHÔNG liệt kê từng cái (Itemize tắt), gộp theo Type Mark → cửa trùng ký hiệu hiện 1 dòng kèm số lượng; dòng tổng cuối bảng. - Lọc: Level = tầng của mặt bằng, bỏ cửa có Type Comments CHỨA chữ loại trừ (Louver, Lam thép, Lam nhôm; không phân biệt hoa thường / dấu, vd. "Louver", "LOUVER nhôm", "CỬA LAM THÉP LOGIA CĂN HỘ" – người dùng yêu cầu 2026-11-09; bảng Revit dùng bộ lọc "does not contain", thêm cả dạng HOA / thường vì bộ lọc này phân biệt). "Filter by sheet" TẮT mặc định (bật thì bảng đặt trên sheet không có mặt bằng sẽ trống – thử 2026-11-04); mặt bằng crop 1 phần tầng thì bật IN[6] rồi đặt bảng lên sheet của mặt bằng đó để bảng chỉ đếm cửa thấy trên sheet. - Bảng cùng tên đã có (bấm lại) thì cập nhật lại cột / lọc / gộp, không tạo trùng, không xoá. Chưa có thì nhân bản bảng cùng hạng mục có sẵn của dự án (giữ kiểu trình bày công ty), không có thì tạo mới. - Đổi tên cửa (người dùng yêu cầu 2026-11-04 tối: "1 bảng hiện ra, có các cửa, tên hiện tại, tên đổi, chiều dài, chiều cao"): nút bật bảng lib/arv_bang_cua.py (mỗi loại cửa thấy trong mặt bằng 1 dòng), người dùng gõ tên mới → IN[7] = JSON {id type: tên mới} → đổi Type Mark của type đó (áp cho mọi cửa cùng type trong dự án). Làm TRƯỚC bảng thống kê để bảng hiện tên mới. IN[8] = có tạo / cập nhật bảng thống kê Revit không. - Báo CẦN XEM LẠI: cửa chưa có Type Mark, cùng Type Mark mà khác kích thước (Revit để trống ô), số cửa thấy trong mặt bằng khác số cửa của tầng. - Vách kính (người dùng yêu cầu + duyệt 2026-11-13: "1 cửa sổ đặt tên cửa đi cửa sổ, 1 cửa sổ tag vách kính bằng mark"): bảng lib/arv_bang_cua.py có thêm cửa sổ "Vách kính" (curtain wall thấy trong mặt bằng, tên = MARK của từng vách) → IN[9] = JSON đặt Mark, IN[10] = tag mỗi vách 1 tag tường hiện Mark (family ARV_Tag Vach Kinh Mark, chưa có thì nạp bản đóng gói lib/tag_vach_kinh); xem khối VÁCH KÍNH bên dưới. - Cửa nằm trong vách kính (người dùng chốt 2026-11-14: "không tag các cửa và thống kê các cửa (cửa đi, cửa sổ) khi nằm trong vách kính"): cửa đi / cửa sổ có host là curtain wall (kể cả tấm vách kính là family cửa) KHÔNG vào bảng đổi tên, KHÔNG vào bảng thống kê – vách kính có tên riêng (Mark). Tầng có cửa như vậy thì bảng thống kê là bảng vẽ (drafting view) như trường hợp file link, vì bảng thống kê Revit không lọc được theo vách chủ. IN[13] bật = đếm như cũ. Dry-run chỉ báo cáo, không sửa mô hình."""
__title__ = "Thống kê\ncửa"
# Bấm: ghi luôn vào mô hình (không hộp thoại, không Dry-run) trên view mặt bằng tầng – Ctrl+Z một lần là hoàn tác.
#   View đang mở là view mặt bằng tầng (tên view / view template có chữ "mặt bằng tầng") thì vẽ vào đó;
#   không thì: có đúng 1 view như vậy → vẽ vào view đó; nhiều view → hỏi chọn; không có → báo, không làm gì.
# Shift+bấm (config.py): hộp thoại đầy đủ như các nút khác, mặc định Dry-run.
import os
import sys
import unicodedata
import traceback

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
# Không dùng "from Autodesk.Revit.DB import <tên>": pythonnet 3.0 loại tên import đích danh đầu tiên khỏi "import *" của core.py
import Autodesk.Revit.DB as DB
import Autodesk.Revit.UI as UI

VIEW_IN = 0
TU_KHOA = u""
TIEU_DE = u"Thống kê cửa"
KHONG_VIEW = False
TAO_IN = None          # chỉ số IN[] "tạo view khi tầng chưa có" (None = không tạo, báo như cũ)
HOI = u"arv_bang_cua.hoi_thong_ke_cua"           # "<module trong lib>.<hàm>(doc, view)": hộp thoại hỏi thêm trước khi chạy, trả về {IN: giá trị} / None


def khong_dau(s):
    s = unicodedata.normalize("NFD", u"{}".format(s or u"")).replace(u"đ", u"d").replace(u"Đ", u"D")
    return u"".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def la_view_dich(doc, v):
    tpl = doc.GetElement(v.ViewTemplateId) if v.ViewTemplateId != DB.ElementId.InvalidElementId else None
    return TU_KHOA in khong_dau(v.Name) or (tpl is not None and TU_KHOA in khong_dau(tpl.Name))


def hoi_chon_view(ten_views):
    """Danh sách view để chọn (bấm đúp hoặc nút Vẽ). Trả về tên view hoặc None nếu Huỷ."""
    clr.AddReference("System.Windows.Forms")
    clr.AddReference("System.Drawing")
    from System.Windows.Forms import (Form, ListBox, Button, Label, DialogResult, DockStyle, FormStartPosition,
                                      FlowLayoutPanel, FlowDirection, Padding)
    from System.Drawing import Size, Font
    f = Form()
    f.Text = TIEU_DE
    f.StartPosition = FormStartPosition.CenterScreen
    f.Size = Size(520, 460)
    f.Font = Font("Segoe UI", 9.0)
    lab = Label()
    lab.Text = u"View đang mở không phải view mặt bằng tầng. Chọn view để vẽ:"
    lab.Dock = DockStyle.Top
    lab.Height = 36
    lab.Padding = Padding(8, 10, 8, 0)
    lb = ListBox()
    lb.Dock = DockStyle.Fill
    lb.IntegralHeight = False
    for t in ten_views:
        lb.Items.Add(t)
    lb.SelectedIndex = 0
    bottom = FlowLayoutPanel()
    bottom.Dock = DockStyle.Bottom
    bottom.Height = 48
    bottom.FlowDirection = FlowDirection.RightToLeft
    bottom.Padding = Padding(8)
    ok = Button()
    ok.Text = u"Vẽ"
    ok.Size = Size(100, 30)
    ok.DialogResult = DialogResult.OK
    huy = Button()
    huy.Text = u"Huỷ"
    huy.Size = Size(100, 30)
    huy.DialogResult = DialogResult.Cancel
    bottom.Controls.Add(huy)
    bottom.Controls.Add(ok)
    f.AcceptButton = ok
    f.CancelButton = huy

    def bam_dup(sender, e):
        f.DialogResult = DialogResult.OK
        f.Close()

    lb.DoubleClick += bam_dup
    f.Controls.Add(lb)
    f.Controls.Add(lab)
    f.Controls.Add(bottom)
    if f.ShowDialog() == DialogResult.OK and lb.SelectedItem is not None:
        return u"{}".format(lb.SelectedItem)
    return None


def chay_tao_view(uiapp, uidoc, doc, av):
    """Tầng của view đang mở chưa có view mặt bằng tầng: lõi nhân bản view đang mở + gán template rồi vẽ (IN[TAO_IN])."""
    truoc = set(v.Id.Value for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan))
    ov = {3: False, TAO_IN: True}
    if VIEW_IN is not None:
        ov[VIEW_IN] = u""
    if HOI:
        m_, f_ = HOI.rsplit(".", 1)
        them = getattr(__import__(m_), f_)(doc, av)
        if them is None:
            return
        ov.update(them)
    lines = arv_dynamo_host.run_button(_here, uiapp, ask=False, overrides=ov)
    moi = [v for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan)
           if not v.IsTemplate and v.Id.Value not in truoc and la_view_dich(doc, v)]
    try:
        from pyrevit import script
        out = script.get_output()
        out.set_title(TIEU_DE)
        out.print_md(u"## {} – tạo view: {}".format(TIEU_DE, moi[0].Name if moi else u"-"))
    except Exception:
        pass
    for ln in lines or []:
        print(ln)
    if moi:
        try:
            uidoc.RequestViewChange(moi[0])
        except Exception:
            pass


def chay():
    uiapp = __revit__
    uidoc = uiapp.ActiveUIDocument
    if uidoc is None:
        UI.TaskDialog.Show(TIEU_DE, u"Chưa mở dự án nào.")
        return
    doc = uidoc.Document
    av = doc.ActiveView
    if KHONG_VIEW:             # lõi tự lấy đối tượng (vd. Chi tiết cửa: cửa đang chọn / chọn trên màn hình)
        ov = {3: False}
        if HOI:                # hộp thoại hỏi thêm: (doc, view đang mở, uidoc) → {IN: giá trị} / None = Huỷ
            m_, f_ = HOI.rsplit(".", 1)
            them = getattr(__import__(m_), f_)(doc, av, uidoc)
            if them is None:
                return
            ov.update(them)
        lines = arv_dynamo_host.run_button(_here, uiapp, ask=False, overrides=ov)
        try:
            from pyrevit import script
            out = script.get_output()
            out.set_title(TIEU_DE)
            out.print_md(u"## {}".format(TIEU_DE))
        except Exception:
            pass
        for ln in lines or []:
            print(ln)
        return
    if not TU_KHOA:            # làm trên mặt bằng tầng đang mở (vd. Lỗ mở shaft)
        if av is None or av.ViewType not in (DB.ViewType.FloorPlan, DB.ViewType.EngineeringPlan) or av.GenLevel is None:
            UI.TaskDialog.Show(TIEU_DE, u"Hãy mở mặt bằng tầng cần làm rồi bấm lại.")
            return
        ds = [av]
    else:
        ds = sorted([v for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan)
                     if not v.IsTemplate and la_view_dich(doc, v)], key=lambda v: v.Name)
        # Mặt bằng tầng đang mở (không phải view đích): chỉ xét view đích CÙNG TẦNG; chưa có thì lõi tạo view + template
        # từ view đang mở (người dùng yêu cầu 2026-11-04, như mặt bằng định vị cửa)
        if TAO_IN is not None and av is not None and av.ViewType == DB.ViewType.FloorPlan and av.GenLevel is not None                 and not la_view_dich(doc, av):
            ds = [v for v in ds if v.GenLevel is not None and v.GenLevel.Id.Value == av.GenLevel.Id.Value]
            if not ds:
                return chay_tao_view(uiapp, uidoc, doc, av)
    view = None
    for v in ds:
        if av is not None and v.Id.Value == av.Id.Value:
            view = v
    if view is None:
        if not ds:
            UI.TaskDialog.Show(TIEU_DE, u"Chưa có view mặt bằng mặt bằng tầng (tên view hoặc view template có chữ "
                                     u"'mặt bằng tầng'). Tạo view, gán view template rồi bấm lại.")
            return
        if len(ds) == 1:
            view = ds[0]
        else:
            ten_chon = hoi_chon_view([v.Name for v in ds])
            if ten_chon is None:
                return
            view = [v for v in ds if v.Name == ten_chon][0]
    ov = {3: False}
    if VIEW_IN is not None:
        ov[VIEW_IN] = view.Name
    if HOI:
        m_, f_ = HOI.rsplit(".", 1)
        them = getattr(__import__(m_), f_)(doc, view)
        if them is None:
            return
        ov.update(them)
    lines = arv_dynamo_host.run_button(_here, uiapp, ask=False, overrides=ov)
    try:
        from pyrevit import script
        out = script.get_output()
        out.set_title(TIEU_DE)
        out.print_md(u"## {} – view: {}".format(TIEU_DE, view.Name))
    except Exception:
        pass
    for ln in lines or []:
        print(ln)
    if av is None or view.Id.Value != av.Id.Value:
        try:
            uidoc.RequestViewChange(view)
        except Exception:
            pass


if os.environ.get("ARV_TOOLS_AUTO_REPORT"):
    arv_dynamo_host.run_button(_here, __revit__)     # chạy thử tự động: giữ dry-run như mọi nút
else:
    try:
        chay()
    except Exception:
        print(traceback.format_exc())
