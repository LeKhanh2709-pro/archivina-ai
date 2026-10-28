#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Hatch ngăn cháy lan trục / hộp kỹ thuật (Filled Region 2D) trên view mặt bằng chống cháy lan của Revit. Thể hiện theo skill CAD ngan-chay-truc-hkt: lưới NET 125 mm xoay 45° màu 220,30,30, viền tím (màu 6), chỉ hatch trong lòng ô. - Vùng = khoảng trống khép kín giữa tường / cột trên level của view: quét lưới 20 mm theo dấu chân thật của tường (mặt đáy khối tường, đã trừ lỗ cửa), lưới xoay theo phương chính của tường → bắt được cả khe hộp gen hẹp ~120 mm mà room của Revit không bắt được; biên = mặt tường trong lòng ô (sai số ≤ 1 ô lưới). Chỉ đọc, không tạo room. - Nhận trục / hộp kỹ thuật theo thứ tự bằng chứng: a) tên room có từ khoá (HKT, hộp kỹ thuật, trục kỹ thuật, shaft…) hoặc chứa Shaft Opening b) chứa ống / ống gió / ống luồn dây đi đứng, ô không có cửa đi và thiết bị vệ sinh c) không có ống, dấu X trong model (như G19): ô / khe kín KHÔNG có cửa đi, cửa sổ, thiết bị vệ sinh, sàn hoàn thiện, diện tích ≤ ngưỡng (mặc định 3 m2: ô 1770 x 2520 ở hành lang G19 không phải trục), bề rộng lòng ≥ ngưỡng - Loại: ô chứa thang máy / thang bộ (tên family / type / room có từ khoá loại trừ) - Ô lớn hơn 1400 x 1400 mm vẫn hatch nhưng liệt kê riêng để xem lại (như bản CAD) - Kiểu Filled Region + mẫu lưới + line style viền chưa có thì tự tạo; Filled Region gom group "ARV_NganChay" - Ẩn thiết bị vệ sinh / nội thất trong view (Hide in View từng đối tượng, không sửa template) - Bấm lại: ô đã có hatch cùng kiểu thì bỏ qua, không vẽ trùng, không xoá gì Dry-run (mặc định) chỉ báo cáo, không sửa mô hình."""
__title__ = "Ngăn\ncháy lan"
# Bấm: ghi luôn vào mô hình (không hộp thoại, không Dry-run) trên view chống cháy lan – Ctrl+Z một lần là hoàn tác.
#   View đang mở là view chống cháy lan (tên view / view template có chữ "chống cháy lan") thì vẽ vào đó;
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
TU_KHOA = u"chay lan"
TIEU_DE = u"Ngăn cháy lan"


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
    lab.Text = u"View đang mở không phải view chống cháy lan. Chọn view để vẽ:"
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


def chay():
    uiapp = __revit__
    uidoc = uiapp.ActiveUIDocument
    if uidoc is None:
        UI.TaskDialog.Show(TIEU_DE, u"Chưa mở dự án nào.")
        return
    doc = uidoc.Document
    av = doc.ActiveView
    ds = sorted([v for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan) if not v.IsTemplate and la_view_dich(doc, v)],
                key=lambda v: v.Name)
    view = None
    for v in ds:
        if av is not None and v.Id.Value == av.Id.Value:
            view = v
    if view is None:
        if not ds:
            UI.TaskDialog.Show(TIEU_DE, u"Chưa có view mặt bằng chống cháy lan (tên view hoặc view template có chữ "
                                     u"'chống cháy lan'). Tạo view, gán view template rồi bấm lại.")
            return
        if len(ds) == 1:
            view = ds[0]
        else:
            ten_chon = hoi_chon_view([v.Name for v in ds])
            if ten_chon is None:
                return
            view = [v for v in ds if v.Name == ten_chon][0]
    lines = arv_dynamo_host.run_button(_here, uiapp, ask=False, overrides={VIEW_IN: view.Name, 4: False})
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
