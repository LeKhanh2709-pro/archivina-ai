#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Vẽ nét vén chân tường chống thấm (Detail Line) trên view mặt bằng chống thấm của Revit. Hatch chống thấm = Filled Region 2D trong view (người dùng chốt 2026-10-27: không đụng hatch / filter của sàn gạch model). - Nhận phòng ướt theo 2 nguồn: a) sàn hoàn thiện ướt trên level (tên kiểu sàn chứa từ khoá, vd. "Gach Lat WC", "Gach Lat Logia") b) bồn cầu / sen tắm / bồn tắm nằm ngoài mọi sàn ướt → WC chưa có sàn ướt (không dùng phễu thoát sàn) - Biên phòng = mép tường thô / mặt lõi tường (room có sẵn tại điểm đó, hoặc room tạm trong SubTransaction rồi rollback, không để lại gì trong model) → không bám theo khấc / lỗ của sàn. Room hở (không khép kín) hoặc tràn sang phòng lớn thì quay về biên sàn. Không bao giờ bo vào lớp trát / hoàn thiện (người dùng chốt 2026-10-28). - Mỗi vòng biên lùi vào trong phòng một khoảng (mặc định 50 mm) → nét vén, ngắt tại cửa đi - Mọi phòng ướt được hatch bằng Filled Region theo biên mặt tường: kiểu "AV_Hatch Chống Thấm WC" / "... Logia" (chưa có thì tạo, mẫu + màu lấy theo filter sàn SHT-WC / SHT-Logia của template), đưa xuống dưới nét vén - View đã có nét vén: không vẽ lại vén (không xoá gì), chỉ bổ sung hatch cho phòng chưa có hatch - Ẩn thiết bị vệ sinh trong view (Hide in View từng đối tượng, không sửa template), giữ phễu thoát sàn - Detail Line kiểu nét "AV.Nét chống thấm" gom group "ARV_ChongTham_Ven"; Filled Region gom group "ARV_ChongTham_Hatch" Dry-run (mặc định) chỉ báo cáo, không sửa mô hình. Không xoá gì: view đã có nét vén cùng kiểu thì dừng và báo."""
__title__ = "Chống\nthấm"
# Bấm: ghi luôn vào mô hình (không hộp thoại, không Dry-run) trên view chống thấm – Ctrl+Z một lần là hoàn tác.
#   View đang mở là view chống thấm (tên view / view template có chữ "chống thấm") thì vẽ vào đó;
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
TU_KHOA = u"chong tham"
TIEU_DE = u"Chống thấm"


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
    lab.Text = u"View đang mở không phải view chống thấm. Chọn view để vẽ:"
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
    if not TU_KHOA:            # làm trên mặt bằng tầng đang mở (vd. Lỗ mở shaft)
        if av is None or av.ViewType not in (DB.ViewType.FloorPlan, DB.ViewType.EngineeringPlan) or av.GenLevel is None:
            UI.TaskDialog.Show(TIEU_DE, u"Hãy mở mặt bằng tầng cần làm rồi bấm lại.")
            return
        ds = [av]
    else:
        ds = sorted([v for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan)
                     if not v.IsTemplate and la_view_dich(doc, v)], key=lambda v: v.Name)
    view = None
    for v in ds:
        if av is not None and v.Id.Value == av.Id.Value:
            view = v
    if view is None:
        if not ds:
            UI.TaskDialog.Show(TIEU_DE, u"Chưa có view mặt bằng chống thấm (tên view hoặc view template có chữ "
                                     u"'chống thấm'). Tạo view, gán view template rồi bấm lại.")
            return
        if len(ds) == 1:
            view = ds[0]
        else:
            ten_chon = hoi_chon_view([v.Name for v in ds])
            if ten_chon is None:
                return
            view = [v for v in ds if v.Name == ten_chon][0]
    ov = {4: False}
    if VIEW_IN is not None:
        ov[VIEW_IN] = view.Name
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
