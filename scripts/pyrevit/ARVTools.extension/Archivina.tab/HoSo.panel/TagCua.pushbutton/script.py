#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Tự động tag cửa đi + cửa sổ trên mặt bằng đang mở của Revit (người dùng chốt 2026-11-02, sửa theo góp ý cùng ngày): - Cửa đi: family tag "AV_Door Tag"; cửa sổ: "AV_Window Tag"; cửa sổ có tên family / type chứa từ khoá lam: "AV_Louver Tag". Đối tượng có Type Comments "Louver" thì KHÔNG tag. - Tag hiện đúng Type Mark: nhãn family có tiền tố (vd. "S3.") thì thay bằng nhãn Type Mark trơn chép từ family tag cùng hạng mục trong dự án (Revit 2027.3 không sửa được tiền tố nhãn qua API), rồi nạp lại family. - Tag nằm ngang, ưu tiên NGAY GIỮA cửa (cửa đi phía không mở cánh, cửa sổ phía ngoài theo FacingOrientation); KHÔNG đè cửa (kể cả cánh mở), cửa sổ, tường, cột, tag / chữ khác. Lưới vị trí quanh cửa xếp theo điểm = lùi xa + 4 × dịch khỏi giữa cửa + phạt phía kia; không chỗ nào trống thì đặt chỗ ít đè nhất và liệt kê để xem lại. - Leader: tag lệch khỏi giữa cửa (hoặc xa hơn 1 bề cao tag) thì bật leader gắn vào cửa. - Nội thất không né mà ẩn: tạo view template riêng "<template gốc> (ẩn nội thất)" (tạo từ view vì API không nhân bản được view template), ẩn các hạng mục nội thất, gán cho view. KHÔNG sửa template gốc. - Cửa có EI (tham số chống cháy có giá trị) thì EI phải hiện trên tag: tag đã đặt mà chữ tag không chứa giá trị EI → báo family tag chưa có nhãn EI. - Cửa / cửa sổ đã có tag trong view thì bỏ qua: bấm lại không tạo trùng. Chỉ khi bật IN[14] mới dời tag đã có (cùng family tag); chỉ khi bật IN[15] mới xoá tag đang gắn trên đối tượng Type Comments "Louver". Dry-run chỉ báo cáo (đặt thử trong SubTransaction rồi huỷ), không sửa mô hình. - Mặt bằng định vị cửa (gộp từ nút "MB định vị cửa" theo yêu cầu người dùng 2026-11-03): view gốc đã là mặt bằng định vị cửa (mang template IN[17] hoặc tên theo mẫu IN[18]) thì tag luôn; không thì nhân bản view gốc (Duplicate, không kèm chú thích) thành "MẶT BẰNG ĐỊNH VỊ CỬA - <tầng>" (đã có thì dùng view đó), gán template IN[17] rồi tag trên đó. Template chưa có thì tạo từ template của view gốc: tường + sàn Halftone, sàn tắt mẫu tô, cửa đi / cửa sổ bỏ Halftone, ẩn các hạng mục IN[7], hiện tag cửa. Template đã có thì dùng nguyên. Không sửa view gốc / template gốc."""
__title__ = "Định vị\n+ tag cửa"
# Bấm: ghi luôn vào mô hình (không hộp thoại, không Dry-run) trên view mặt bằng – Ctrl+Z một lần là hoàn tác.
#   View đang mở là view mặt bằng (tên view / view template có chữ "mặt bằng") thì vẽ vào đó;
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
TIEU_DE = u"Định vị + tag cửa"
KHONG_VIEW = False
TAO_IN = None          # chỉ số IN[] "tạo view khi tầng chưa có" (None = không tạo, báo như cũ)
HOI = u"arv_hoi_sheet.hoi"           # "<module trong lib>.<hàm>(doc, view)": hộp thoại hỏi thêm trước khi chạy, trả về {IN: giá trị} / None


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
    lab.Text = u"View đang mở không phải view mặt bằng. Chọn view để vẽ:"
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
    """Tầng của view đang mở chưa có view mặt bằng: lõi nhân bản view đang mở + gán template rồi vẽ (IN[TAO_IN])."""
    truoc = set(v.Id.Value for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan))
    ov = {5: False, TAO_IN: True}
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
        ov = {5: False}
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
            UI.TaskDialog.Show(TIEU_DE, u"Chưa có view mặt bằng mặt bằng (tên view hoặc view template có chữ "
                                     u"'mặt bằng'). Tạo view, gán view template rồi bấm lại.")
            return
        if len(ds) == 1:
            view = ds[0]
        else:
            ten_chon = hoi_chon_view([v.Name for v in ds])
            if ten_chon is None:
                return
            view = [v for v in ds if v.Name == ten_chon][0]
    ov = {5: False}
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
