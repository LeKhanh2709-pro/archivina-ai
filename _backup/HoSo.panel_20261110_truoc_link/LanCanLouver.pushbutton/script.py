#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Mặt bằng định vị lan can, louver (người dùng yêu cầu 2026-11-05: "giống nút Định vị + tag cửa", lan can / louver nhận diện và hiện tên theo MARK): - Bấm trên mặt bằng tầng: tạo / mở "MẶT BẰNG ĐỊNH VỊ LAN CAN, LOUVER - <tầng>" (nhân bản view đang mở, không kèm chú thích; template "MẶT BẰNG ĐỊNH VỊ LAN CAN, LOUVER": sàn Halftone, tường xây Halftone, vách / cột BTCT tô đặc, ẩn nội thất / thiết bị vệ sinh / thiết bị cơ điện / ký hiệu mặt đứng, mặt cắt, ẩn trục file link; crop sát nhà) rồi tag. View đang mở đã là mặt bằng định vị lan can thì tag luôn. Tạo view / template / đặt sheet dùng khối chung DatSheet_chung.py (như Chống thấm, Ngăn cháy lan). - Nhận diện theo Mark (instance): Mark bắt đầu bằng tiền tố lan can (IN[4], G19 "LK-01") = lan can, tiền tố louver (IN[6], G19 "LV-01") = louver, ở mọi hạng mục. Mark khác tiền tố: Railings = lan can; Windows / Generic Models có Type Comments hoặc tên family / type chứa từ khoá louver (IN[7]) = louver. Chưa có Mark thì KHÔNG tag, liệt kê để điền Mark (tag hiện Mark nên không có Mark thì tag trống). - Chỉ tag đối tượng có Mark đúng tiền tố (IN[24]); lan can / louver mang Mark khác (vd. số tự tăng 55, 56…) thì liệt kê để đặt lại Mark. - Tag hiện Mark: Railings → family IN[1] (Railing Tags, G19 "AV-Railing Tag- Mark-lan can" người dùng dựng), Windows → IN[2] (Window Tags, G19 "TAG LOUVER MARK"), Generic Models → IN[3] (Generic Model Tags). Dự án chưa có family đó thì dùng / nạp bản đóng gói ARV_Tag Lan Can Mark / ARV_Tag Louver Mark / ARV_Tag Louver Mark GM (thư mục IN[16], mặc định <extension>/lib/tag_lan_can, chép từ 2 family mẫu của người dùng); không có file thì báo, bỏ hạng mục đó. Hạng mục khác (tường, curtain wall…) mang Mark LK / LV chỉ liệt kê: API không đổi được family tag sang Multi-Category (thử 2026-11-05: "The input category id cannot be assigned"). - Vị trí tag như Tag cửa: ưu tiên NGAY GIỮA đối tượng, phía NGOÀI nhà (xa tâm nhà), không đè tường / cột / cửa / cửa sổ / lan can / louver / chữ / tag; lưới gần (dịch dọc ≤ ½ đối tượng + 2 bề dài tag, lùi ≤ TAM_XA_MM_GIAY); lệch khỏi giữa thì leader gắn vào đối tượng; hết chỗ trống thì chỗ ít đè nhất + liệt kê "CẦN XEM LẠI". Tag nằm ngang như 2 tag mẫu người dùng đặt ở G19 Tầng 1 (IN[11] = xoay theo phương đối tượng như tag cửa). - Bấm lại không trùng: đối tượng đã có tag (bất kỳ) trong view thì bỏ qua; IN[10] = dời lại tag đã có cùng family. - Đặt lên bản vẽ (IN[17] – IN[23]): khung tên theo khổ, giữa vùng vẽ, giữ tỉ lệ view; sheet trống có sẵn mang số hiệu đó thì đặt vào; 2 bảng thống kê "BẢNG THỐNG KÊ LAN CAN / LOUVER <TẦNG>" (Mark, chiều dài / rộng × cao, số lượng, gộp theo Mark, lọc theo tầng) góc phải dưới. Dry-run: đặt thử tag trong SubTransaction rồi huỷ, không tạo view / sheet / nạp family."""
__title__ = "Định vị\nlan can, louver"
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
TIEU_DE = u"Định vị lan can, louver"
KHONG_VIEW = False
TAO_IN = None          # chỉ số IN[] "tạo view khi tầng chưa có" (None = không tạo, báo như cũ)
HOI = u"arv_hoi_sheet.hoi_lan_can_louver"           # "<module trong lib>.<hàm>(doc, view)": hộp thoại hỏi thêm trước khi chạy, trả về {IN: giá trị} / None


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
