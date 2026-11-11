#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Trình bày MẶT BẰNG TƯỜNG XÂY (định vị tường) cả tầng theo mẫu FPT P5 A.CD.04.07 (KTS chốt 2026-11-03, G19): 1. View mặt bằng mới trên level IN[0] (tên IN[1]), chép thông số view template IN[2] vào view rồi BỎ gắn template (template công ty để 1/150 – KHÔNG sửa template). Ẩn nội thất, thiết bị, Room, sàn. Tỷ lệ = số đầu tiên trong IN[3] mà hình (kể cả dim, đầu trục) ước tính vừa vùng vẽ khung tên. 2. Trục của file: đầu trục 2D ở CẢ 2 ĐẦU, cách tường ngoài cùng GRID_END mm giấy. Dim trục 4 phía, mỗi phía 2 chuỗi: khoảng trục + kích thước tổng (dim type IN[8]). 3. Chuỗi định vị tường (dim type IN[9]): gom tường (lõi ≥ 80, thẳng, song song trục X / Y) thành TUYẾN thẳng hàng (lệch tim ≤ 60, hở ≤ 2500, tổng dài ≥ 4000). Mỗi tuyến xét 2 phía (điểm mẫu cách mặt tường 400): - một phía phần lớn KHÔNG có Room → mặt ngoài nhà: chuỗi đặt phía ngoài, cách mặt tường WALL_EXT mm giấy; - không, mà một phía là Room công cộng IN[12] (hành lang, khu vực chung) → chuỗi phía đó, cách WALL_INT; - cả 2 phía là phòng trong căn → không dim (chi tiết căn hộ đã dim). Mốc: MẶT LÕI (gạch thô, bỏ trát) tường vuông góc chạm tuyến, mép cửa đi / cửa sổ trên tuyến (tham chiếu Left / Right của family), đầu tường của tuyến, mặt cột / vách BTCT của file Revit link (kết cấu), trục. Mốc cách nhau < DIM_MIN gộp; chữ số đoạn ngắn chồng nhau → kéo sang phía ngoài đường dim, lệch xen kẽ. 4. Legend IN[10] (nhân bản một legend có sẵn rồi vẽ): BẢNG KÝ HIỆU GHI CHÚ TƯỜNG – mỗi vật liệu lõi tường một dòng (hatch theo IN[11], loại, các chiều dày lõi) + lưu ý chỉ ghi điều đúng với mô hình. 5. Sheet IN[4] / IN[5], khung tên IN[6], viewport type IN[7]: MB ở trên, giữa vùng vẽ; legend góc dưới trái. 6. Trục file link KC: tắt hiển thị view filter có sẵn IN[16] trong view (trục type không phải '…KT'). Không tạo / sửa type, style, view template, filter. Chưa làm: tag căn hộ, chi tiết điển hình cột vách giao tường xây, dim trong lòng căn."""
__title__ = "Tường\nxây"
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

VIEW_IN = None
TU_KHOA = u""
TIEU_DE = u"Tường xây"
KHONG_VIEW = False
TAO_IN = None          # chỉ số IN[] "tạo view khi tầng chưa có" (None = không tạo, báo như cũ)
HOI = u"arv_hoi_sheet.hoi_tuong_xay"           # "<module trong lib>.<hàm>(doc, view)": hộp thoại hỏi thêm trước khi chạy, trả về {IN: giá trị} / None


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
    ov = {13: False, TAO_IN: True}
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
        ov = {13: False}
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
    ov = {13: False}
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
