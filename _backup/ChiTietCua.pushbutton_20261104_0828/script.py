#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Triển khai chi tiết cửa (người dùng yêu cầu 2026-11-03, mẫu bản vẽ "CHI TIẾT CỬA" A.CD.22.13): chọn 1 cửa đi / cửa sổ có sẵn family → tạo mặt bằng, mặt đứng, mặt cắt tỉ lệ 1/25 rồi đặt vào ô trống tiếp theo của sheet "CHI TIẾT CỬA" (khung A1 chia 6 ô: 2 hàng × 3 cột). Ký hiệu, vật liệu, phụ kiện người dùng tự điền vào phần trống của ô. - Mặt bằng: callout từ mặt bằng tầng của cửa (ưu tiên view đang mở nếu đúng tầng), khung nhìn = cửa + lề IN[5], XOAY theo mặt đứng (người dùng yêu cầu 2026-11-03): phía phải mặt bằng = phía phải mặt đứng, ngoài nhà ở dưới; khung callout trên mặt bằng gốc ẩn bằng Hide in View (IN[13]). - Mặt đứng CHỈ CÓ CỬA (tường, sàn, phần tử khác Hide in View); level ẩn trên mặt đứng + mặt cắt, thay bằng nét đứt cốt sàn + chữ "CỐT SÀN HOÀN THIỆN" có mũi tên trên mặt cắt (như mẫu người dùng gửi 2026-11-03). - Mặt bằng chỉ hiện cửa + tường (sàn, cửa khác, đồ đạc Hide in View), khung nhìn trùm hết cung mở cánh. - Kiểu view riêng: Floor Plan "CT CỬA", Section "MẶT CẮT CỬA" (mặt đứng + mặt cắt); viewport "AV-Title No Line". - Mặt đứng: section đặt trước mặt tường, không cắt cửa, nhìn từ NGOÀI NHÀ. Phía ngoài nhà: một bên không có room → bên đó; cả 2 bên có room thì bên có tên lô gia / ban công / sân; không rõ → phía KHÔNG mở cánh (theo cung mở trên mặt bằng); cửa không có cung mở → mặt ngoài family (Facing). IN[11] ép phía nhìn. - Mặt cắt: section vuông góc tường, cắt qua cánh cửa (cách tâm cửa 1/4 bề rộng), ngoài nhà nằm bên phải. Ký hiệu section ẩn ở tỉ lệ thô hơn 1:<tỉ lệ> (mặt bằng 1/100 không thấy), mặt đứng / mặt cắt ẩn ký hiệu của nhau. - View template: IN[6] – IN[8]; đã có thì dùng nguyên, KHÔNG sửa; chưa có thì tạo từ template nền (theo từ khoá IN[9], không có thì template cùng tỉ lệ), tỉ lệ IN[4], Detail Level Fine, ẩn hạng mục IN[10], để view tự giữ Far Clipping (template nền điều khiển Far Clipping thì mặt cắt thấy cả phòng phía sau). - Kích thước tổng (IN[12]): mặt bằng = rộng; mặt đứng = rộng + cao (cửa sổ: cao độ bậu tính từ sàn + cao cửa); mặt cắt = cao. Reference lấy từ family (Left / Right / Top / Bottom); family không có thì lấy mặt lỗ mở của tường (mép, đỉnh, bậu); chân = nét cốt sàn. - Sheet: tên IN[2]; chỉ dùng sheet do công cụ này tạo (có group lưới ô "ARV_ChiTietCua_Luoi ..."), KHÔNG đặt view vào sheet người dùng tự làm dù trùng tên. Hết ô thì tạo sheet mới khung IN[1], số sheet = số lớn nhất của các sheet tên IN[2] + 1 (chưa có sheet nào tên đó thì IN[3]). Lưới ô: Detail Line trên sheet (2 nét đứng, 1 nét ngang chia vùng vẽ của khung tên + 1 nét ngăn dải thông tin dưới mỗi ô). - Mỗi type cửa chỉ làm 1 lần: đã có view "CT CỬA <Type Mark> - MẶT ĐỨNG" thì báo và mở sheet chứa view đó. - Nhiều cửa (người dùng yêu cầu 2026-11-03): chọn nhiều cửa rồi bấm → làm lần lượt, xếp tiếp các ô; nút pyRevit hỏi giai đoạn / hạng mục / khổ giấy (khung tên) / số hiệu / tên bản vẽ trước khi chạy (librv_hoi_sheet.py). - Không xoá, không sửa cửa / tường / view gốc / template đã có. Giới hạn: cửa trong file link không chọn được."""
__title__ = "Chi tiết\ncửa"
# Bấm: ghi luôn vào mô hình (không hộp thoại, không Dry-run) trên view bất kỳ – Ctrl+Z một lần là hoàn tác.
#   View đang mở là view bất kỳ (tên view / view template có chữ "bất kỳ") thì vẽ vào đó;
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
TIEU_DE = u"Chi tiết cửa"
KHONG_VIEW = True
HOI = u"arv_hoi_sheet.hoi_chi_tiet_cua"           # "<module trong lib>.<hàm>(doc, view)": hộp thoại hỏi thêm trước khi chạy, trả về {IN: giá trị} / None


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
    lab.Text = u"View đang mở không phải view bất kỳ. Chọn view để vẽ:"
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
    if KHONG_VIEW:             # lõi tự lấy đối tượng (vd. Chi tiết cửa: cửa đang chọn / chọn trên màn hình)
        ov = {14: False}
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
    view = None
    for v in ds:
        if av is not None and v.Id.Value == av.Id.Value:
            view = v
    if view is None:
        if not ds:
            UI.TaskDialog.Show(TIEU_DE, u"Chưa có view mặt bằng bất kỳ (tên view hoặc view template có chữ "
                                     u"'bất kỳ'). Tạo view, gán view template rồi bấm lại.")
            return
        if len(ds) == 1:
            view = ds[0]
        else:
            ten_chon = hoi_chon_view([v.Name for v in ds])
            if ten_chon is None:
                return
            view = [v for v in ds if v.Name == ten_chon][0]
    ov = {14: False}
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
