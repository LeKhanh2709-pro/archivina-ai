# Mặt bằng định vị lan can, louver (người dùng yêu cầu 2026-11-05: "giống nút Định vị + tag cửa", lan can / louver nhận
# diện và hiện tên theo MARK):
#   - Bấm trên mặt bằng tầng: tạo / mở "MẶT BẰNG ĐỊNH VỊ LAN CAN, LOUVER - <tầng>" (nhân bản view đang mở, không kèm chú
#     thích; template "MẶT BẰNG ĐỊNH VỊ LAN CAN, LOUVER": sàn Halftone, tường xây Halftone, vách / cột BTCT tô đặc, ẩn nội
#     thất / thiết bị vệ sinh / thiết bị cơ điện / ký hiệu mặt đứng, mặt cắt, ẩn trục file link; crop sát nhà) rồi tag.
#     View đang mở đã là mặt bằng định vị lan can thì tag luôn. Tạo view / template / đặt sheet dùng khối chung
#     DatSheet_chung.py (như Chống thấm, Ngăn cháy lan).
#   - Nhận diện theo Mark (instance): Mark bắt đầu bằng tiền tố lan can (IN[4], G19 "LK-01") = lan can, tiền tố louver
#     (IN[6], G19 "LV-01") = louver, ở mọi hạng mục. Mark khác tiền tố: Railings = lan can; Windows / Generic Models có
#     Type Comments hoặc tên family / type chứa từ khoá louver (IN[7]) = louver. Chưa có Mark thì KHÔNG tag, liệt kê để
#     điền Mark (tag hiện Mark nên không có Mark thì tag trống).
#   - Chỉ tag đối tượng có Mark đúng tiền tố (IN[24]); lan can / louver mang Mark khác (vd. số tự tăng 55, 56…) thì liệt
#     kê để đặt lại Mark.
#   - Tag hiện Mark: Railings → family IN[1] (Railing Tags, G19 "AV-Railing Tag- Mark-lan can" người dùng dựng), Windows →
#     IN[2] (Window Tags, G19 "TAG LOUVER MARK"), Generic Models → IN[3] (Generic Model Tags). Dự án chưa có family đó
#     thì dùng / nạp bản đóng gói ARV_Tag Lan Can Mark / ARV_Tag Louver Mark / ARV_Tag Louver Mark GM (thư mục IN[16],
#     mặc định <extension>\lib\tag_lan_can, chép từ 2 family mẫu của người dùng); không có file thì báo, bỏ hạng mục đó.
#     Hạng mục khác (tường, curtain wall…) mang Mark LK / LV chỉ liệt kê: API không đổi được family tag sang
#     Multi-Category (thử 2026-11-05: "The input category id cannot be assigned").
#   - Vị trí tag như Tag cửa: ưu tiên NGAY GIỮA đối tượng, phía NGOÀI nhà (xa tâm nhà), không đè tường / cột / cửa /
#     cửa sổ / lan can / louver / chữ / tag; lưới gần (dịch dọc ≤ ½ đối tượng + 2 bề dài tag, lùi ≤ TAM_XA_MM_GIAY);
#     lệch khỏi giữa thì leader gắn vào đối tượng; hết chỗ trống thì chỗ ít đè nhất + liệt kê "CẦN XEM LẠI". Tag nằm
#     ngang như 2 tag mẫu người dùng đặt ở G19 Tầng 1 (IN[11] = xoay theo phương đối tượng như tag cửa).
#   - Bấm lại không trùng: đối tượng đã có tag (bất kỳ) trong view thì bỏ qua; IN[10] = dời lại tag đã có cùng family.
#   - Đặt lên bản vẽ (IN[17] – IN[23]): khung tên theo khổ, giữa vùng vẽ, giữ tỉ lệ view; sheet trống có sẵn mang số hiệu
#     đó thì đặt vào; 2 bảng thống kê "BẢNG THỐNG KÊ LAN CAN / LOUVER <TẦNG>" (Mark, chiều dài / rộng × cao, số lượng,
#     gộp theo Mark, lọc theo tầng) góc phải dưới.
# Dry-run: đặt thử tag trong SubTransaction rồi huỷ, không tạo view / sheet / nạp family.
# INPUT
#   IN[0]  (str)   Tên view mặt bằng (trống = view đang mở)
#   IN[1]  (str)   Family tag lan can (Railing Tags)
#   IN[2]  (str)   Family tag louver hạng mục Windows (Window Tags)
#   IN[3]  (str)   Family tag louver hạng mục Generic Models (Generic Model Tags)
#   IN[4]  (str)   Tiền tố Mark lan can, cách nhau bằng ;
#   IN[5]  (bool)  Dry-run (True = chỉ báo cáo)
#   IN[6]  (str)   Tiền tố Mark louver, cách nhau bằng ;
#   IN[7]  (str)   Từ khoá louver trong Type Comments / tên family / type, cách nhau bằng ;
#   IN[8]  (float) Khoảng hở tag - vật cản (mm giấy)
#   IN[9]  (str)   Thư mục log (trống = Documents\ARV_Logs\lan_can_louver)
#   IN[10] (bool)  Đặt lại vị trí tag đã có (cùng family tag)
#   IN[11] (bool)  Tag xoay theo phương lan can / louver (False = luôn nằm ngang)
#   IN[12] (bool)  Tạo / mở mặt bằng định vị lan can, louver rồi tag trên đó (False = tag ngay trên view IN[0])
#   IN[13] (str)   Tên view template / tiền tố tên view
#   IN[14] (str)   Hạng mục ẩn thêm trong template công cụ tạo (BuiltInCategory, ;)
#   IN[15] (bool)  Luôn bật leader
#   IN[16] (str)   Thư mục family tag .rfa đóng gói (trống = <extension>\lib\tag_lan_can khi chạy nút)
#   IN[17] (bool)  Đặt mặt bằng lên bản vẽ
#   IN[18] (str)   Giai đoạn
#   IN[19] (str)   Hạng mục
#   IN[20] (str)   Khổ giấy (A1 / A0)
#   IN[21] (str)   Khung tên "Family : Type" (trống = tự tìm theo khổ)
#   IN[22] (str)   Số hiệu sheet (trống = tiếp theo trong hạng mục)
#   IN[23] (str)   Tên sheet (trống = "MẶT BẰNG ĐỊNH VỊ LAN CAN, LOUVER <TẦNG>")
#   IN[24] (bool)  Chỉ tag đối tượng có Mark đúng tiền tố IN[4] / IN[6] (False = tag mọi lan can / louver có Mark)
# OUTPUT
#   OUT (list[str])  Báo cáo
import math
import os
import traceback
import unicodedata
from datetime import datetime
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")
from Autodesk.Revit.DB import *
import Autodesk.Revit.DB as _RevitDB
# pythonnet 3.0: tên đã được import đích danh trước đó trong phiên bị loại khỏi "import *" → bổ sung đủ tên
globals().update({_n: getattr(_RevitDB, _n) for _n in dir(_RevitDB) if not _n.startswith("_") and _n not in globals()})
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager
from System.Collections.Generic import List as NetList

TEN_MAU = u"MẶT BẰNG ĐỊNH VỊ LAN CAN, LOUVER"
TU_KHOA_VIEW = u"dinh vi lan can"          # chữ khoá (không dấu) nhận view / template / sheet trống của công cụ
MAC_DINH = ["", u"AV-Railing Tag- Mark-lan can", u"TAG LOUVER MARK", u"ARV_Tag Louver Mark GM", u"LK;LC", True,
            u"LV", u"Louver;Lam", 1.0, "", False, False, True, TEN_MAU, u"OST_PlumbingFixtures", False, "",
            False, "", "", "A1", "", "", "", True]
# Family tag đóng gói (lib\tag_lan_can\<tên>.rfa): dùng khi dự án không có family IN[1] / IN[2] / IN[3]
# Cùng tên 2 family mẫu của người dùng trong G19 (người dùng yêu cầu 2026-11-05: model khác nạp đúng family đó)
DU_PHONG_LAN_CAN = u"AV-Railing Tag- Mark-lan can"
DU_PHONG_LOUVER = u"TAG LOUVER MARK"
DU_PHONG_GM = u"ARV_Tag Louver Mark GM"       # Generic Model Tags (louver dựng bằng Generic Model)
SO_MAC_DINH = u"A.DVLC.00"
PHAT_PHIA_MM_GIAY = 8.0     # phạt khi đặt tag ở phía trong nhà (mm giấy, cộng vào khoảng cách)
HE_SO_LECH = 4.0            # mỗi mm dịch khỏi giữa đối tượng tính bằng 4 mm lùi xa
TAM_XA_MM_GIAY = 8.0        # tag xa nhất cách mép đối tượng (mm giấy), như tag cửa
KHE_BANG_MM = 6.0           # khe giữa 2 bảng thống kê (mm giấy)
TIA_MM = 8000.0             # dò phía ngoài nhà: tia dài tối đa (mm thật)
LOP_LAN_CAN, LOP_LOUVER = u"lan can", u"louver"


def doc_in(i):
    try:
        v = IN[i]
    except Exception:
        v = None
    return MAC_DINH[i] if v is None or (isinstance(v, str) and v == "" and MAC_DINH[i] != "") else v


def khong_dau(s):
    s = unicodedata.normalize("NFD", u"%s" % (s or u"")).replace(u"đ", u"d").replace(u"Đ", u"D")
    return u"".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def tach(s):
    return [x.strip() for x in (s or "").split(";") if x.strip()]


def mm(v):
    return UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.Millimeters)


def ft(v):
    return UnitUtils.ConvertToInternalUnits(v, UnitTypeId.Millimeters)


def ten(e):
    try:
        return Element.Name.GetValue(e)
    except Exception:
        try:
            return e.Name
        except Exception:
            return "?"


def mark(e):
    try:
        return (e.get_Parameter(BuiltInParameter.ALL_MODEL_MARK).AsString() or u"").strip()
    except Exception:
        return u""


def da_giac_giao(a, b):
    """Hai đa giác lồi (list (x, y)) có phần trong giao nhau không (định lý trục tách)."""
    for poly in (a, b):
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            nx, ny = y1 - y2, x2 - x1
            pa = [nx * x + ny * y for x, y in a]
            pb = [nx * x + ny * y for x, y in b]
            if max(pa) <= min(pb) + 1e-9 or max(pb) <= min(pa) + 1e-9:
                return False
    return True


def dien_tich_giao_hop(a, b):
    ax = [p[0] for p in a]
    ay = [p[1] for p in a]
    bx = [p[0] for p in b]
    by = [p[1] for p in b]
    w = min(max(ax), max(bx)) - max(min(ax), min(bx))
    h = min(max(ay), max(by)) - max(min(ay), min(by))
    return w * h if w > 0 and h > 0 else 0.0


def tuy_chon_nap():
    """IFamilyLoadOptions: family đã có thì giữ nguyên giá trị tham số trong dự án. Tên lớp .NET riêng mỗi lần gọi."""
    import uuid
    ns = "ARV.LanCan.N" + uuid.uuid4().hex

    class _Nap(_RevitDB.IFamilyLoadOptions):
        __namespace__ = ns

        def OnFamilyFound(self, familyInUse, overwriteParameterValues):
            return (True, False)

        def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
            return (True, _RevitDB.FamilySource.Family, False)

    return _Nap()


def thu_muc_tag():
    """Thư mục family tag đóng gói (IN[16]); trống = <extension>\\lib\\tag_lan_can khi chạy từ nút (__file__ = core.py)."""
    d = (doc_in(16) or u"").strip()
    if d:
        return d
    try:
        f = globals().get("__file__")
        if f:
            return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(f)), u"..", u"..", u"..", u"lib",
                                                 u"tag_lan_can"))
    except Exception:
        pass
    return u""


def tim_kieu_tag(doc, ten_fam, bic):
    for s in FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(bic):
        if s.FamilyName == ten_fam:
            return s
    return None


def lay_kieu_tag(doc, ten_fam, bic, dry, bao):
    """Kiểu tag theo tên family; chưa có thì nạp file đóng gói (ngoài transaction của dự án). Trả về FamilySymbol | None."""
    s = tim_kieu_tag(doc, ten_fam, bic)
    if s is not None:
        return s
    duong = os.path.join(thu_muc_tag(), ten_fam + u".rfa") if ten_fam in (DU_PHONG_LAN_CAN, DU_PHONG_LOUVER,
                                                                          DU_PHONG_GM) else u""
    if not duong or not os.path.isfile(duong):
        bao.append(u"CHƯA CÓ family tag '%s' (%s) trong dự án và không thấy file đóng gói '%s' → bỏ hạng mục này."
                   % (ten_fam, Category.GetCategory(doc, bic).Name, duong or u"-"))
        return None
    if dry:
        bao.append(u"Sẽ nạp family tag '%s' từ %s." % (ten_fam, duong))
        return None
    TransactionManager.Instance.EnsureInTransaction(doc)
    try:
        doc.LoadFamily(duong, tuy_chon_nap())
    except Exception as ex:
        bao.append(u"KHÔNG nạp được family tag '%s' từ %s: %s" % (ten_fam, duong, (u"%s" % ex).splitlines()[0][:200]))
        return None
    finally:
        TransactionManager.Instance.TransactionTaskDone()
    ten_nap = os.path.splitext(os.path.basename(duong))[0]
    s = tim_kieu_tag(doc, ten_fam, bic) or tim_kieu_tag(doc, ten_nap, bic)
    bao.append(u"Nạp family tag '%s' từ %s%s." % (ten_nap, duong, u"" if s is not None else u" – KHÔNG thấy kiểu tag sau khi nạp"))
    return s


def la_view_dich(doc, v):
    tpl = doc.GetElement(v.ViewTemplateId) if v.ViewTemplateId != ElementId.InvalidElementId else None
    return TU_KHOA_VIEW in khong_dau(v.Name) or (tpl is not None and TU_KHOA_VIEW in khong_dau(tpl.Name))


def bo_sung_template(doc, view, ten_mau, ten_bic_an):
    """Template công cụ tạo (tên = ten_mau): ẩn thêm hạng mục ten_bic_an (thiết bị vệ sinh: mặt bằng định vị không cần),
    hiện tag lan can / cửa sổ / Generic Model. Template người dùng tự làm thì không sửa. Gọi TRONG
    transaction."""
    tpl = doc.GetElement(view.ViewTemplateId) if view.ViewTemplateId != ElementId.InvalidElementId else None
    if tpl is None or tpl.Name != ten_mau:
        return u""
    an = []
    for n in ten_bic_an:
        try:
            c = ElementId(getattr(BuiltInCategory, n))
            if tpl.CanCategoryBeHidden(c) and not tpl.GetCategoryHidden(c):
                tpl.SetCategoryHidden(c, True)
                an.append(Category.GetCategory(doc, c).Name)
        except Exception:
            pass
    for bic in (BuiltInCategory.OST_StairsRailingTags, BuiltInCategory.OST_WindowTags, BuiltInCategory.OST_GenericModelTags, BuiltInCategory.OST_StairsRailing, BuiltInCategory.OST_Windows,
                BuiltInCategory.OST_GenericModel):
        try:
            if tpl.GetCategoryHidden(ElementId(bic)):
                tpl.SetCategoryHidden(ElementId(bic), False)
        except Exception:
            pass
    return (u"Template '%s': ẩn thêm %s." % (ten_mau, u", ".join(an))) if an else u""


def mb_dinh_vi(doc, goc, dry, ten_mau, ten_bic_an):
    """View để tag: view đang mở đã là mặt bằng định vị lan can (tên / template có chữ khoá) thì dùng luôn; tầng đã có
    view đó thì mở; chưa có thì tạo bằng sh_tao_view (khối chung). Trả về (view, [báo cáo])."""
    bao = []
    if la_view_dich(doc, goc):
        bao.append(u"View đang mở '%s' là mặt bằng định vị lan can, louver – tag luôn." % goc.Name)
        moi = goc
    elif goc.ViewType != ViewType.FloorPlan or goc.GenLevel is None:
        bao.append(u"View '%s' không phải mặt bằng tầng → tag ngay trên view này." % goc.Name)
        return goc, bao
    else:
        cung = sorted([v for v in FilteredElementCollector(doc).OfClass(ViewPlan)
                       if not v.IsTemplate and v.ViewType == ViewType.FloorPlan and v.GenLevel is not None
                       and v.GenLevel.Id.Value == goc.GenLevel.Id.Value and la_view_dich(doc, v)], key=lambda v: v.Name)
        if cung:
            moi = cung[0]
            bao.append(u"Tầng %s đã có '%s' – tag trên view đó." % (goc.GenLevel.Name, moi.Name))
        else:
            moi, b_ = sh_tao_view(doc, goc, TU_KHOA_VIEW, ten_mau, dry)
            bao.extend(b_)
            if dry:
                return moi, bao
    if not dry:
        TransactionManager.Instance.EnsureInTransaction(doc)
        try:
            if moi.Id.Value != goc.Id.Value:
                bao.extend(sh_chuan_template_nhe(doc, moi, ten_mau))
            s_ = bo_sung_template(doc, moi, ten_mau, ten_bic_an)
            if s_:
                bao.append(s_)
            doc.Regenerate()
        finally:
            TransactionManager.Instance.TransactionTaskDone()
        if moi.Id.Value != goc.Id.Value:
            try:
                DocumentManager.Instance.CurrentUIDocument.RequestViewChange(moi)
            except Exception:
                pass
    return moi, bao


def sh_chuan_template_nhe(doc, view, ten_mau):
    """Như sh_chuan_template của khối chung nhưng gọi trong transaction đang mở."""
    tpl = doc.GetElement(view.ViewTemplateId) if view.ViewTemplateId != ElementId.InvalidElementId else None
    if tpl is None or tpl.Name != ten_mau:
        return []
    return sh_trinh_bay_template(doc, tpl)


def _chinh():
    doc = DocumentManager.Instance.CurrentDBDocument
    bao_cao = []
    xem_lai = []
    chi_tiet = []

    def p(s):
        bao_cao.append(u"%s" % s)

    # ---------- View ----------
    ten_view = doc_in(0)
    if ten_view:
        ung = [v for v in FilteredElementCollector(doc).OfClass(ViewPlan) if not v.IsTemplate and v.Name == ten_view]
        ung.sort(key=lambda v: 0 if v.ViewType == ViewType.FloorPlan else 1)
        av = doc.ActiveView
        if av is not None and any(v.Id.Value == av.Id.Value for v in ung):
            ung = [av]
        view = ung[0] if ung else None
        if view is None:
            return [u"Không có view mặt bằng tên '%s'." % ten_view]
    else:
        view = doc.ActiveView
    if view is None or view.ViewType not in (ViewType.FloorPlan, ViewType.EngineeringPlan, ViewType.AreaPlan):
        return [u"View '%s' không phải mặt bằng. Mở mặt bằng tầng rồi chạy lại." % (ten(view) if view else "-")]
    dry = bool(doc_in(5))
    ten_mau = (doc_in(13) or TEN_MAU).strip()
    if doc_in(12):
        view, b_ = mb_dinh_vi(doc, view, dry, ten_mau, tach(doc_in(14)))
        for s_ in b_:
            p(s_)

    tl = float(view.Scale)
    U = view.RightDirection
    V = view.UpDirection
    khe = ft(float(doc_in(8)) * tl)

    def uv(pt):
        return (pt.X * U.X + pt.Y * U.Y + pt.Z * U.Z, pt.X * V.X + pt.Y * V.Y + pt.Z * V.Z)

    def xyz(a, b, z):
        return XYZ(a * U.X + b * V.X, a * U.Y + b * V.Y, z)

    def khung_hop(bb):
        if bb is None:
            return None
        tf = bb.Transform
        pts = [uv(tf.OfPoint(XYZ(x, y, bb.Min.Z))) for x in (bb.Min.X, bb.Max.X) for y in (bb.Min.Y, bb.Max.Y)]
        xs = [q[0] for q in pts]
        ys = [q[1] for q in pts]
        return [(min(xs), min(ys)), (max(xs), min(ys)), (max(xs), max(ys)), (min(xs), max(ys))]

    def diem_hinh_hoc(e):
        """Các điểm hình học của đối tượng hiện trong view (gồm nét 2D của family)."""
        opt = Options()
        opt.View = view
        opt.IncludeNonVisibleObjects = False
        pts = []

        def duyet(geo):
            for g in geo:
                tn = g.GetType().Name
                if tn == "GeometryInstance":
                    duyet(g.GetInstanceGeometry())
                elif tn == "Solid":
                    if g.Volume <= 0 and g.Edges.Size == 0:
                        continue
                    for ed in g.Edges:
                        pts.extend(ed.Tessellate())
                elif tn in ("Line", "Arc", "Ellipse", "NurbSpline", "HermiteSpline", "CylindricalHelix"):
                    pts.extend(g.Tessellate())
                elif tn == "PolyLine":
                    pts.extend(g.GetCoordinates())
        try:
            geo = e.get_Geometry(opt)
            if geo is not None:
                duyet(geo)
        except Exception:
            pass
        return pts

    def hcn_cuc_bo(pts, goc, h, f):
        """Hình chữ nhật bao các điểm theo hệ (h, f) đặt tại goc; trả về (đa giác uv, h0, h1, f0, f1)."""
        if not pts:
            return None
        hs = [(q.X - goc.X) * h.X + (q.Y - goc.Y) * h.Y for q in pts]
        fs = [(q.X - goc.X) * f.X + (q.Y - goc.Y) * f.Y for q in pts]
        h0, h1, f0, f1 = min(hs), max(hs), min(fs), max(fs)
        poly = [uv(goc + h * a + f * b) for a, b in ((h0, f0), (h1, f0), (h1, f1), (h0, f1))]
        return poly, h0, h1, f0, f1

    def thay(bic):
        return list(FilteredElementCollector(doc, view.Id).OfCategory(bic).WhereElementIsNotElementType())

    # ---------- Đối tượng: lan can / louver theo Mark ----------
    tt_lc = [khong_dau(x) for x in tach(doc_in(4))]
    tt_lv = [khong_dau(x) for x in tach(doc_in(6))]
    tk_lv = [khong_dau(x) for x in tach(doc_in(7))]

    def loai_doi_tuong(e, bic):
        """(lớp lan can / louver | None, cách nhận). Mark có tiền tố → theo Mark; không thì theo hạng mục / tên."""
        mk = khong_dau(mark(e))
        if mk and any(mk.startswith(x) for x in tt_lc):
            return LOP_LAN_CAN, u"Mark"
        if mk and any(mk.startswith(x) for x in tt_lv):
            return LOP_LOUVER, u"Mark"
        if bic == BuiltInCategory.OST_StairsRailing:
            return LOP_LAN_CAN, u"hạng mục Railings"
        t = doc.GetElement(e.GetTypeId())
        if t is None:
            return None, u""
        try:
            tc = khong_dau(t.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_COMMENTS).AsString() or u"")
        except Exception:
            tc = u""
        ten_ft = khong_dau(u"%s %s" % (getattr(t, "FamilyName", u""), ten(t)))
        for k in tk_lv:
            if k in tc:
                return LOP_LOUVER, u"Type Comments"
            # "lam" chỉ khớp nguyên chữ trong tên family / type (tránh "lamp", "lamination")
            if (u" %s " % k) in (u" %s " % ten_ft.replace(u"-", u" ").replace(u"_", u" ")) or \
                    (len(k) > 3 and k in ten_ft):
                return LOP_LOUVER, u"tên family / type"
        return None, u""

    ds = []              # (đối tượng, lớp, hạng mục, cách nhận)
    for bic in (BuiltInCategory.OST_StairsRailing, BuiltInCategory.OST_Windows, BuiltInCategory.OST_GenericModel):
        for e in thay(bic):
            lop, cach = loai_doi_tuong(e, bic)
            if lop is not None:
                ds.append((e, lop, bic, cach))
    # Hạng mục khác (tường, curtain wall…) mang Mark đúng tiền tố: chưa hỗ trợ tag (Revit 2027.3 không đổi được family tag
    # sang Multi-Category qua API) → chỉ liệt kê
    da_co = set(e.Id.Value for e, _, _, _ in ds)
    khac = []
    for bic in (BuiltInCategory.OST_Walls, BuiltInCategory.OST_SpecialityEquipment, BuiltInCategory.OST_Doors,
                BuiltInCategory.OST_StructuralFraming, BuiltInCategory.OST_CurtainWallPanels):
        for e in thay(bic):
            mk = khong_dau(mark(e))
            if e.Id.Value not in da_co and mk and any(mk.startswith(x) for x in tt_lc + tt_lv):
                khac.append(u"%d (%s, Mark %s)" % (e.Id.Value, e.Category.Name if e.Category else u"?", mark(e)))
    if khac:
        xem_lai.append(u"%d đối tượng hạng mục khác Railings / Windows / Generic Models mang Mark lan can / louver – "
                       u"chưa tag (tag tay bằng Multi-Category Tag): %s" % (len(khac), u", ".join(khac[:20])))
    chua_mark = [(e, lop) for e, lop, _, _ in ds if not mark(e)]
    if chua_mark:
        xem_lai.append(u"%d đối tượng CHƯA CÓ Mark (không tag; đặt tên bằng nút Thống kê lan can, louver rồi bấm lại): %s" % (
            len(chua_mark), u", ".join(u"%d (%s)" % (e.Id.Value, lop) for e, lop in chua_mark[:30])))

    # ---------- Kiểu tag (nạp family đóng gói nếu thiếu; ngoài transaction) ----------
    def dung_tien_to(e, lop):
        mk = khong_dau(mark(e))
        return bool(mk) and any(mk.startswith(x) for x in (tt_lc if lop == LOP_LAN_CAN else tt_lv))

    sai_tt = [(e, lop) for e, lop, _, _ in ds if mark(e) and not dung_tien_to(e, lop)]
    if sai_tt and doc_in(24):
        xem_lai.append(u"%d đối tượng có Mark KHÔNG theo tiền tố %s (không tag; đặt tên bằng nút Thống kê lan can, louver rồi bấm lại): %s" % (
            len(sai_tt), u" / ".join(tach(doc_in(4)) + tach(doc_in(6))),
            u", ".join(u"%d (%s, Mark %s)" % (e.Id.Value, lop, mark(e)) for e, lop in sai_tt[:30])))

    def se_tag(e, lop):
        return bool(mark(e)) and (dung_tien_to(e, lop) or not doc_in(24))

    bic_tag = {BuiltInCategory.OST_StairsRailing: (doc_in(1), BuiltInCategory.OST_StairsRailingTags, DU_PHONG_LAN_CAN),
               BuiltInCategory.OST_Windows: (doc_in(2), BuiltInCategory.OST_WindowTags, DU_PHONG_LOUVER),
               BuiltInCategory.OST_GenericModel: (doc_in(3), BuiltInCategory.OST_GenericModelTags, DU_PHONG_GM)}
    kieu = {}
    # Luôn nạp family tag lan can + louver (Windows), và Generic Models nếu view có louver loại đó, kể cả khi chưa có đối
    # tượng nào đủ Mark để tag: người dùng cần family trong dự án (2026-11-05: model chưa có Mark thì trước đây không nạp)
    can = set(bic for _, _, bic, _ in ds) | set((BuiltInCategory.OST_StairsRailing, BuiltInCategory.OST_Windows))
    for bic in can:
        ten_fam, cat_tag, du_phong = bic_tag[bic]
        s = tim_kieu_tag(doc, ten_fam, cat_tag)
        if s is None and ten_fam != du_phong:
            bao_cao.append(u"Dự án chưa có family tag '%s' (%s) → dùng '%s'." % (
                ten_fam, Category.GetCategory(doc, cat_tag).Name, du_phong))
        if s is None:
            s = lay_kieu_tag(doc, du_phong, cat_tag, dry, bao_cao)
        kieu[bic] = s
    ten_fam_tag = set(s.FamilyName for s in kieu.values() if s is not None)

    # ---------- Tag có sẵn + vật cản ----------
    tag_co = {}
    for tg in FilteredElementCollector(doc, view.Id).OfClass(IndependentTag):
        try:
            for i in tg.GetTaggedLocalElementIds():
                tag_co.setdefault(i.Value, []).append(tg)
        except Exception:
            pass

    def fam_cua_tag(tg):
        try:
            return doc.GetElement(tg.GetTypeId()).FamilyName
        except Exception:
            return u""

    vat_can = []
    bo_vat_can = set()
    for cls in (IndependentTag, TextNote, SpatialElementTag):
        try:
            for e in FilteredElementCollector(doc, view.Id).OfClass(cls):
                k = khung_hop(e.get_BoundingBox(view))
                if k:
                    vat_can.append((k, u"chữ / tag %d" % e.Id.Value))
        except Exception:
            pass
    xs_nha, ys_nha = [], []
    tuong_poly = []          # (đa giác uv, khung bao) – dò phía ngoài nhà
    for w in FilteredElementCollector(doc, view.Id).OfClass(Wall):
        lc = w.Location
        cv = lc.Curve if lc is not None and hasattr(lc, "Curve") else None
        poly = None
        if cv is not None and cv.GetType().Name == "Line":
            d = cv.Direction
            h = XYZ(d.X, d.Y, 0).Normalize()
            f = XYZ(-h.Y, h.X, 0)
            r = hcn_cuc_bo(diem_hinh_hoc(w), cv.GetEndPoint(0), h, f)
            poly = r[0] if r else None
        if poly is None:
            poly = khung_hop(w.get_BoundingBox(view))
        if poly:
            vat_can.append((poly, u"tường %d" % w.Id.Value))
            xs_ = [q[0] for q in poly]
            ys_ = [q[1] for q in poly]
            tuong_poly.append((poly, (min(xs_), min(ys_), max(xs_), max(ys_))))
            xs_nha += [q[0] for q in poly]
            ys_nha += [q[1] for q in poly]
    tam_nha = ((min(xs_nha) + max(xs_nha)) / 2.0, (min(ys_nha) + max(ys_nha)) / 2.0) if xs_nha else None

    def trong_da_giac(x, y, poly):
        """Điểm trong đa giác lồi (cùng phía mọi cạnh)."""
        dau = 0
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            c = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
            if abs(c) < 1e-12:
                continue
            s = 1 if c > 0 else -1
            if dau == 0:
                dau = s
            elif s != dau:
                return False
        return True

    def khoang_trong(x0, y0, du, dv, bat_dau):
        """Khoảng (feet) từ điểm (x0, y0) theo hướng (du, dv) tới tường đầu tiên, tối đa TIA_MM. Phía ngoài nhà = phía
        trống xa hơn (nhà chữ U: logia nhìn ra sân trong vẫn đúng, tâm nhà thì sai – thử G19 2026-11-05)."""
        toi_da = ft(TIA_MM)
        x1, y1 = x0 + du * toi_da, y0 + dv * toi_da
        gan = [pl for pl, bb in tuong_poly if bb[0] <= max(x0, x1) and bb[2] >= min(x0, x1)
               and bb[1] <= max(y0, y1) and bb[3] >= min(y0, y1)]
        gan = [pl for pl in gan if not trong_da_giac(x0, y0, pl)]     # bỏ gờ / tường đỡ ngay dưới lan can
        # Giao tia – cạnh đa giác chính xác (bước dò cố định nhảy qua tường mỏng – thử G19 2026-11-05)
        tot = toi_da
        for pl in gan:
            n = len(pl)
            for i in range(n):
                ax, ay = pl[i]
                bx, by = pl[(i + 1) % n]
                ex, ey = bx - ax, by - ay
                mau = du * ey - dv * ex
                if abs(mau) < 1e-12:
                    continue
                t = ((ax - x0) * ey - (ay - y0) * ex) / mau        # khoảng trên tia
                s = ((ax - x0) * dv - (ay - y0) * du) / mau        # vị trí trên cạnh [0, 1]
                if -1e-9 <= s <= 1 + 1e-9 and bat_dau <= t < tot:
                    tot = t
        return tot
    for bic in (BuiltInCategory.OST_Columns, BuiltInCategory.OST_StructuralColumns):
        for e in thay(bic):
            k = khung_hop(e.get_BoundingBox(view))
            if k:
                vat_can.append((k, u"cột %d" % e.Id.Value))

    def khung_doi_tuong(e):
        """(goc, h, f, đa giác uv, h0, h1, f0, f1): hệ cục bộ theo phương đối tượng. Lan can: đoạn đường dẫn dài nhất;
        family: Hand / Facing; còn lại: khung bao trong view."""
        pts = diem_hinh_hoc(e)
        goc = h = None
        try:
            if isinstance(e.Location, LocationPoint):
                goc = e.Location.Point
                h = e.HandOrientation
        except Exception:
            goc = h = None
        if h is None:
            cvs = []
            try:
                cvs = list(e.GetPath())                    # Railing
            except Exception:
                try:
                    cvs = [e.Location.Curve]               # tường / dầm
                except Exception:
                    cvs = []
            cvs = [c for c in cvs if c is not None and c.IsBound]
            if cvs:
                c = max(cvs, key=lambda c: c.Length)
                a, b = c.GetEndPoint(0), c.GetEndPoint(1)
                d = XYZ(b.X - a.X, b.Y - a.Y, 0)
                if d.GetLength() > 1e-6:
                    h = d.Normalize()
                    goc = XYZ((a.X + b.X) / 2.0, (a.Y + b.Y) / 2.0, a.Z)
        if h is None or abs(h.Z) > 0.9:
            k = khung_hop(e.get_BoundingBox(view))
            if not k:
                return None
            h = XYZ(U.X, U.Y, 0).Normalize()
            cu_, cv2 = (k[0][0] + k[2][0]) / 2.0, (k[0][1] + k[2][1]) / 2.0
            goc = xyz(cu_, cv2, 0)
            if not pts:
                pts = [xyz(x, y, 0) for x, y in k]
        h = XYZ(h.X, h.Y, 0).Normalize()
        f = XYZ(-h.Y, h.X, 0)
        r = hcn_cuc_bo(pts, goc, h, f)
        if r is None:
            return None
        return (goc, h, f) + r

    dau_chan = {}
    for e, lop, bic, cach in ds:
        dc = khung_doi_tuong(e)
        if dc is not None:
            dau_chan[e.Id.Value] = dc
            vat_can.append((dc[3], u"%s %d" % (lop, e.Id.Value)))
    # Cửa đi / cửa sổ khác: dấu chân theo hình học trong view theo hệ (Hand, Facing) như Tag cửa (khung bao family cửa
    # sổ lớn hơn hình thật, chặn oan chỗ đặt tag – thử G19 2026-11-05); lan can không nhận (cầu thang), cầu thang: khung bao
    for bic in (BuiltInCategory.OST_Doors, BuiltInCategory.OST_Windows, BuiltInCategory.OST_StairsRailing,
                BuiltInCategory.OST_Stairs):
        for e in thay(bic):
            if e.Id.Value in dau_chan:
                continue
            k = None
            try:
                if bic in (BuiltInCategory.OST_Doors, BuiltInCategory.OST_Windows):
                    r_ = hcn_cuc_bo(diem_hinh_hoc(e), e.Location.Point, e.HandOrientation, e.FacingOrientation)
                    k = r_[0] if r_ else None
            except Exception:
                k = None
            k = k or khung_hop(e.get_BoundingBox(view))
            if k:
                vat_can.append((k, u"cửa / lan can %d" % e.Id.Value))

    _bb_cache = []

    def vat_can_bb():
        while len(_bb_cache) < len(vat_can):
            pl, mt = vat_can[len(_bb_cache)]
            xs = [q[0] for q in pl]
            ys = [q[1] for q in pl]
            _bb_cache.append((pl, mt, (min(xs), min(ys), max(xs), max(ys))))
        return _bb_cache

    crop = khung_hop(view.CropBox) if view.CropBoxActive else None

    # ---------- Ghi ----------
    tao = {LOP_LAN_CAN: 0, LOP_LOUVER: 0}
    bo_qua = 0
    dat_lai = 0
    so_leader = 0
    khong_kieu = []
    TransactionManager.Instance.EnsureInTransaction(doc)
    st = SubTransaction(doc)
    st.Start()
    try:
        for s in kieu.values():
            if s is not None and not s.IsActive:
                s.Activate()
        for e, lop, bic, cach in ds:
            mk = mark(e)
            if not se_tag(e, lop):
                continue
            kt = kieu.get(bic)
            if kt is None:
                khong_kieu.append(u"%d (%s, Mark %s)" % (e.Id.Value, lop, mk))
                continue
            tg_cu = None
            co = tag_co.get(e.Id.Value, [])
            if co:
                cung_fam = [x for x in co if fam_cua_tag(x) in ten_fam_tag]
                if doc_in(10) and cung_fam:
                    tg_cu = cung_fam[0]
                else:
                    bo_qua += 1
                    continue
            dc = dau_chan.get(e.Id.Value)
            if dc is None:
                xem_lai.append(u"%d (Mark %s): không đọc được hình học trong view → chưa tag" % (e.Id.Value, mk))
                continue
            goc, h, f, poly_e, h0, h1, f0, f1 = dc
            hu_, hv_ = uv(h)
            huong = TagOrientation.Vertical if (doc_in(11) and abs(hv_) > abs(hu_)) else TagOrientation.Horizontal
            # điểm giữa đối tượng (theo dấu chân) – đặt tag tạm tại đây
            giua = goc + h * ((h0 + h1) / 2.0) + f * ((f0 + f1) / 2.0)
            if tg_cu is None:
                ref = Reference(e)
                tg = IndependentTag.Create(doc, kt.Id, view.Id, ref, False, huong, giua)
                nhan_cu = None
            else:
                tg = tg_cu
                nhan_cu = u"chữ / tag %d" % tg.Id.Value
                bo_vat_can.add(nhan_cu)
                tg.HasLeader = False
                tg.TagOrientation = huong
                tg.TagHeadPosition = giua
            doc.Regenerate()
            k = khung_hop(tg.get_BoundingBox(view))
            gu0, gv0 = uv(giua)
            cu = (k[0][0] + k[2][0]) / 2.0 - gu0
            cv_ = (k[0][1] + k[2][1]) / 2.0 - gv0
            a = (k[2][0] - k[0][0]) / 2.0
            b = (k[2][1] - k[0][1]) / 2.0
            h2 = uv(h)
            f2 = uv(f)
            e_f = a * abs(f2[0]) + b * abs(f2[1])
            e_h = a * abs(h2[0]) + b * abs(h2[1])
            mat = {1: max(f1, 0.0), -1: max(-f0, 0.0)}
            # Phía ưu tiên = phía NGOÀI nhà: dò tia từ giữa đối tượng ra 2 phía, phía gặp tường xa hơn; bằng nhau (cả 2
            # trống / cùng kẹt) thì phía xa tâm khung bao tường
            gc = goc + h * ((h0 + h1) / 2.0)
            gcu, gcv = uv(gc)
            kt_ = {s_: khoang_trong(gcu, gcv, s_ * f2[0], s_ * f2[1], mat[s_] + ft(50.0)) for s_ in (1, -1)}
            if abs(kt_[1] - kt_[-1]) > ft(150.0):
                uu_tien = 1 if kt_[1] > kt_[-1] else -1
            elif tam_nha is not None:
                du_, dv_ = gu0 - tam_nha[0], gv0 - tam_nha[1]
                uu_tien = 1 if du_ * f2[0] + dv_ * f2[1] >= 0 else -1
            else:
                uu_tien = 1
            phat = ft(PHAT_PHIA_MM_GIAY * tl)
            buoc_h = max(e_h * 0.5, ft(50))
            buoc_f = max(e_f * 0.5, ft(50))
            tam_h = (h0 + h1) / 2.0
            gioi_han_h = (h1 - h0) / 2.0 + e_h * 2.0
            dau_tien = []
            for s_ in (uu_tien, -uu_tien):
                dau_tien.append((0.0, goc + h * tam_h + f * (s_ * (mat[s_] + khe + e_f)),
                                 u"sát phía %s" % (u"ngoài" if s_ == uu_tien else u"trong"), True))
            ung_vien = []
            for s_ in (1, -1):
                d0 = mat[s_] + khe + e_f
                d_max = d0 + ft(TAM_XA_MM_GIAY * tl)
                i = 0
                while d0 + i * buoc_f <= d_max:
                    d = d0 + i * buoc_f
                    j = -int(gioi_han_h / buoc_h)
                    while j * buoc_h <= gioi_han_h:
                        dh = j * buoc_h
                        diem = (d - d0) + abs(dh) * HE_SO_LECH + (0.0 if s_ == uu_tien else phat)
                        sat_giua = (abs(dh) <= (h1 - h0) / 2.0 + 1e-9 and d - d0 <= 2 * e_f + 1e-9)
                        ung_vien.append((diem, goc + h * (tam_h + dh) + f * (s_ * d),
                                         u"phía %s cách %d dịch %d" % (u"ngoài" if s_ == uu_tien else u"trong",
                                                                       round(mm(d - d0)), round(mm(dh))), sat_giua))
                        j += 1
                    i += 1
            ung_vien.sort(key=lambda x: x[0])
            ung_vien = dau_tien + ung_vien
            r_gan = gioi_han_h + ft(TAM_XA_MM_GIAY * tl) + max(f1, -f0) + 2 * (e_f + e_h)
            gu, gv = uv(goc)
            gan = [(pl, mt, bb) for pl, mt, bb in vat_can_bb()
                   if mt not in bo_vat_can and mt != nhan_cu
                   and bb[0] <= gu + r_gan and bb[2] >= gu - r_gan and bb[1] <= gv + r_gan and bb[3] >= gv - r_gan]
            tot = None
            loai_bo = []
            for _, c, nhan, sat_giua in ung_vien:
                cu0, cv0 = uv(c)
                hop = [(cu0 - a - khe, cv0 - b - khe), (cu0 + a + khe, cv0 - b - khe),
                       (cu0 + a + khe, cv0 + b + khe), (cu0 - a - khe, cv0 + b + khe)]
                if crop and not (hop[0][0] >= crop[0][0] and hop[0][1] >= crop[0][1] and
                                 hop[2][0] <= crop[2][0] and hop[2][1] <= crop[2][1]):
                    loai_bo.append(u"%s: ngoài crop" % nhan)
                    continue
                de = [(pl, mt) for pl, mt, bb in gan
                      if bb[0] < hop[2][0] and bb[2] > hop[0][0] and bb[1] < hop[2][1] and bb[3] > hop[0][1]
                      and da_giac_giao(hop, pl)]
                if de:
                    loai_bo.append(u"%s: đè %s" % (nhan, ", ".join(sorted(set(m for _, m in de))[:3])))
                dt = sum(dien_tich_giao_hop(hop, pl) for pl, mt in de)
                if tot is None or dt < tot[1] - 1e-9:
                    tot = (c, dt, hop, de, nhan, sat_giua)
                if not de:
                    break
            if tot is None:
                c, de, hop, nhan, sat_giua = giua, [("", u"ngoài vùng crop")], None, u"-", False
            else:
                c, _, hop, de, nhan, sat_giua = tot
            chi_tiet.append(u"%d Mark %s %s (%s): %s (%d ứng viên; trống phía +f %d / -f %d mm)%s" % (
                e.Id.Value, mk, lop, cach, nhan, len(ung_vien), mm(kt_[1]), mm(kt_[-1]),
                u" – đặt lại tag cũ" if tg_cu is not None else u""))
            chi_tiet.extend(u"      bỏ " + x for x in [x for x in loai_bo if not x.endswith(u"ngoài crop")][:12])
            cu0, cv0 = uv(c)
            dau = xyz(cu0 - cu, cv0 - cv_, giua.Z)
            tg.TagHeadPosition = dau
            if doc_in(15) or not sat_giua:
                tg.HasLeader = True
                try:
                    tg.LeaderEndCondition = LeaderEndCondition.Attached
                except Exception:
                    pass
                tg.TagHeadPosition = dau
                so_leader += 1
            if hop:
                vat_can.append(([(hop[0][0] + khe, hop[0][1] + khe), (hop[1][0] - khe, hop[1][1] + khe),
                                 (hop[2][0] - khe, hop[2][1] - khe), (hop[3][0] + khe, hop[3][1] - khe)],
                                u"tag mới %d" % e.Id.Value))
            if tg_cu is None:
                tao[lop] += 1
            else:
                dat_lai += 1
            if de:
                xem_lai.append(u"%d (Mark %s, %s): tag còn đè %s" % (e.Id.Value, mk, lop,
                                                                     ", ".join(sorted(set(m for _, m in de))[:4])))
            try:
                doc.Regenerate()
                txt = (tg.TagText or u"").strip()
                if khong_dau(txt).replace(u" ", u"") != khong_dau(mk).replace(u" ", u""):
                    xem_lai.append(u"%d: chữ tag '%s' khác Mark '%s' – family tag '%s' chưa hiện đúng Mark" % (
                        e.Id.Value, txt, mk, kt.FamilyName))
            except Exception:
                pass
        if dry:
            st.RollBack()
        else:
            st.Commit()
    except Exception:
        if st.HasStarted() and not st.HasEnded():
            st.RollBack()
        raise
    finally:
        TransactionManager.Instance.TransactionTaskDone()

    # ---------- Đặt lên bản vẽ + bảng thống kê ----------
    if doc_in(17):
        tang = view.GenLevel.Name if view.GenLevel is not None else view.Name
        ten_sheet = ((doc_in(23) or u"").strip() or u"%s %s" % (ten_mau, tang)).upper()
        if dry:
            p(u"Sẽ đặt mặt bằng lên bản vẽ '%s' khổ %s (giai đoạn '%s', hạng mục '%s') + bảng thống kê lan can / "
              u"louver." % (ten_sheet, doc_in(20), doc_in(18), doc_in(19)))
        else:
            try:
                b_ = dat_mat_bang_len_sheet(doc, view, doc_in(18), doc_in(19), doc_in(20), doc_in(21), doc_in(22),
                                            ten_sheet, SO_MAC_DINH, None)
                for s_ in b_:
                    p(s_)
                # View đã nằm trên sheet từ lần bấm trước (lúc đó chưa có Mark nên chưa có bảng): vẫn bổ sung bảng còn thiếu
                if any(s_.startswith(u"ĐÃ ĐẶT") or u"đã nằm trên sheet" in s_ for s_ in b_):
                    for s_ in dat_bang_thong_ke(doc, view, [x for x in ds if se_tag(x[0], x[1])], tang):
                        p(s_)
            except Exception as ex:
                TransactionManager.Instance.ForceCloseTransaction()
                p(u"Không đặt được lên bản vẽ: %s" % (u"%s" % ex).splitlines()[0][:200])

    p(u"View: %s (1:%d)%s" % (view.Name, view.Scale, u" – DRY-RUN, chưa ghi gì" if dry else u""))
    so_lc = sum(1 for _, l, _, _ in ds if l == LOP_LAN_CAN)
    p(u"Nhận %d lan can, %d louver trong view (theo Mark tiền tố %s / %s; Railings; louver theo %s)." % (
        so_lc, len(ds) - so_lc, doc_in(4), doc_in(6), doc_in(7)))
    p(u"Đã tag: %d lan can, %d louver; đặt lại %d tag cũ; %d tag có leader; bỏ qua %d đối tượng đã có tag." % (
        tao[LOP_LAN_CAN], tao[LOP_LOUVER], dat_lai, so_leader, bo_qua))
    for bic, s in kieu.items():
        p(u"   %s → tag '%s'" % (Category.GetCategory(doc, bic).Name, s.FamilyName if s is not None else u"(thiếu)"))
    if khong_kieu:
        xem_lai.append(u"%d đối tượng chưa tag vì thiếu family tag: %s" % (len(khong_kieu), u", ".join(khong_kieu[:20])))
    p(u"Vật cản đã xét: %d" % len(vat_can))
    if xem_lai:
        p(u"CẦN XEM LẠI (%d):" % len(xem_lai))
        for s in xem_lai:
            p(u"   " + s)
    else:
        p(u"Không tag nào đè lên tường / cửa / lan can / chữ.")
    if dry:
        p(u"DRY-RUN: chưa tạo gì. Đặt IN[5] = False để tag.")
    thu_muc = doc_in(9) or os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs", "lan_can_louver")
    try:
        os.makedirs(thu_muc, exist_ok=True)
        f_log = os.path.join(thu_muc, "lan_can_louver_%s_%d.txt" % (datetime.now().strftime("%Y%m%d_%H%M%S_%f"),
                                                                   view.Id.Value))
        with open(f_log, "w", encoding="utf-8") as fh:
            fh.write("\n".join(bao_cao + [u"", u"CHI TIẾT VỊ TRÍ:"] + chi_tiet))
        p(u"Log: " + f_log)
    except Exception as ex:
        p(u"Không ghi được log: %s" % ex)
    return bao_cao


# ---------------- Bảng thống kê ----------------
def tao_bang_tk(doc, bic, ten_bang, level, loai, ds_mark):
    """Bảng thống kê 1 hạng mục của 1 tầng, gộp theo Mark. loai = lan can: Ký hiệu / Loại / Tổng chiều dài / Số lượng;
    louver: Ký hiệu / Chiều rộng / Chiều cao / Số lượng. Lọc tầng + Mark (BeginsWith tiền tố chung của các Mark đã nhận
    trong tầng, không có tiền tố chung thì chỉ lọc Mark có giá trị). Đã có bảng cùng tên thì dùng lại, không sửa."""
    for vs in FilteredElementCollector(doc).OfClass(ViewSchedule):
        if not vs.IsTemplate and vs.Name == ten_bang:
            return vs, u"dùng lại bảng '%s'" % ten_bang
    vs = ViewSchedule.CreateSchedule(doc, ElementId(bic))
    vs.Name = ten_bang
    d = vs.Definition
    co = {}

    def lay(*bips):
        for bip in bips:
            k = int(bip)
            if k in co:
                return co[k]
            for sf in d.GetSchedulableFields():
                try:
                    if sf.ParameterId.Value == k:
                        co[k] = d.AddField(sf)
                        return co[k]
                except Exception:
                    pass
        return None

    f_mark = lay(BuiltInParameter.ALL_MODEL_MARK)
    # Cột như bảng cửa + ThongKeLanCan_TuDong.py (người dùng yêu cầu 2026-11-05 "như cửa"): Tên / Chiều dài / Chiều cao / SL
    if loai == LOP_LAN_CAN:
        f_2 = lay(BuiltInParameter.CURVE_ELEM_LENGTH, BuiltInParameter.INSTANCE_LENGTH_PARAM)
        f_3 = None
        for sf in d.GetSchedulableFields():
            try:
                if sf.GetName(doc) == u"Railing Height":
                    f_3 = d.AddField(sf)
                    break
            except Exception:
                pass
        nhan = (u"Tên", u"Tổng chiều dài", u"Chiều cao")
    else:
        f_2 = lay(BuiltInParameter.WINDOW_WIDTH, BuiltInParameter.GENERIC_WIDTH, BuiltInParameter.FAMILY_WIDTH_PARAM)
        f_3 = lay(BuiltInParameter.WINDOW_HEIGHT, BuiltInParameter.DOOR_HEIGHT, BuiltInParameter.GENERIC_HEIGHT,
                  BuiltInParameter.FAMILY_HEIGHT_PARAM)
        nhan = (u"Tên", u"Chiều dài", u"Chiều cao")
    f_dem = None
    for sf in d.GetSchedulableFields():
        if str(sf.FieldType) == "Count":
            f_dem = d.AddField(sf)
            break
    f_tang = lay(BuiltInParameter.STAIRS_RAILING_BASE_LEVEL_PARAM, BuiltInParameter.FAMILY_LEVEL_PARAM,
                 BuiltInParameter.SCHEDULE_LEVEL_PARAM, BuiltInParameter.INSTANCE_REFERENCE_LEVEL_PARAM)
    hien = [(f_mark, nhan[0]), (f_2, nhan[1]), (f_3, nhan[2]), (f_dem, u"Số lượng")]
    for i in range(d.GetFieldCount()):
        f = d.GetField(i)
        f.IsHidden = not any(f.FieldId == g.FieldId for g, _ in hien if g is not None)
    for f, nh in hien:
        if f is not None:
            f.ColumnHeading = nh
    for f in (f_dem, f_2 if loai == LOP_LAN_CAN else None):
        try:
            if f is not None:
                f.DisplayType = ScheduleFieldDisplayType.Totals
        except Exception:
            pass
    try:
        thu_tu = NetList[ScheduleFieldId]()
        for f, _ in hien:
            if f is not None:
                thu_tu.Add(f.FieldId)
        for i in range(d.GetFieldCount()):
            f = d.GetField(i)
            if not any(f.FieldId == g.FieldId for g, _ in hien if g is not None):
                thu_tu.Add(f.FieldId)
        d.SetFieldOrder(thu_tu)
    except Exception:
        pass
    d.ClearFilters()
    if f_tang is not None and level is not None:
        d.AddFilter(ScheduleFilter(f_tang.FieldId, ScheduleFilterType.Equal, level.Id))
    if f_mark is not None:
        tt = os.path.commonprefix([m_.upper() for m_ in ds_mark]) if ds_mark else u""
        tt = tt.rstrip(u"0123456789")
        if tt:
            d.AddFilter(ScheduleFilter(f_mark.FieldId, ScheduleFilterType.BeginsWith, tt))
        else:
            d.AddFilter(ScheduleFilter(f_mark.FieldId, ScheduleFilterType.HasValue))
        d.ClearSortGroupFields()
        d.AddSortGroupField(ScheduleSortGroupField(f_mark.FieldId))
    d.IsItemized = False
    for ten_tt, gt in (("ShowTitle", True), ("ShowHeaders", True), ("ShowGrandTotal", True),
                       ("ShowGrandTotalTitle", True), ("ShowGrandTotalCount", False), ("GrandTotalTitle", u"TỔNG")):
        try:
            setattr(d, ten_tt, gt)
        except Exception:
            pass
    return vs, u"tạo mới"


def dat_bang_thong_ke(doc, view, ds, tang):
    """2 bảng (lan can, louver) xếp sát góc phải dưới vùng vẽ của sheet chứa view, bảng louver dưới. Mỗi bảng theo hạng
    mục có nhiều đối tượng nhất của lớp đó."""
    bao = []
    so = view.get_Parameter(BuiltInParameter.VIEWER_SHEET_NUMBER).AsString()
    sh = [s for s in FilteredElementCollector(doc).OfClass(ViewSheet) if s.SheetNumber == so]
    if not sh:
        return [u"Không thấy sheet chứa view – không đặt bảng thống kê."]
    sh = sh[0]
    tbs = [t for t in FilteredElementCollector(doc, sh.Id).OfCategory(BuiltInCategory.OST_TitleBlocks)
           .WhereElementIsNotElementType()]
    if not tbs:
        return [u"Sheet không có khung tên – không đặt bảng thống kê."]
    net = sh_net_khung(doc, doc.GetElement(tbs[0].GetTypeId()))
    TransactionManager.Instance.EnsureInTransaction(doc)
    x0, y0, x1, y1 = sh_vung_ve(sh, tbs[0], net)
    lv = view.GenLevel
    bang = []
    co_san = dict((si.ScheduleId.Value, si) for si in FilteredElementCollector(doc, sh.Id).OfClass(ScheduleSheetInstance)
                  if not si.IsTitleblockRevisionSchedule)
    y_dau = y0          # bảng đã đặt trên sheet thì giữ nguyên chỗ, bảng mới xếp lên trên
    for lop, nhan in ((LOP_LAN_CAN, u"LAN CAN"), (LOP_LOUVER, u"LOUVER")):
        dem = {}
        for e, l, bic, _ in ds:
            if l == lop and mark(e):
                dem.setdefault(bic, []).append(mark(e))
        if not dem:
            continue
        bic = max(dem.keys(), key=lambda k: len(dem[k]))
        try:
            vs, cach = tao_bang_tk(doc, bic, u"BẢNG THỐNG KÊ %s %s" % (nhan, tang.upper()), lv, lop, dem[bic])
            doc.Regenerate()
            if vs.Id.Value in co_san:
                y_dau = max(y_dau, co_san[vs.Id.Value].get_BoundingBox(sh).Max.Y + ft(KHE_BANG_MM))
                continue
            si = ScheduleSheetInstance.Create(doc, sh.Id, vs.Id, XYZ(x0, y1, 0))
            bang.append((si, vs, cach))
            if len(dem) > 1:
                bao.append(u"Bảng %s chỉ thống kê hạng mục %s (còn %s)." % (nhan, Category.GetCategory(doc, bic).Name,
                           u", ".join(Category.GetCategory(doc, k).Name for k in dem if k != bic)))
        except Exception as ex:
            bao.append(u"Không tạo được bảng thống kê %s: %s" % (nhan, (u"%s" % ex).splitlines()[0][:150]))
    doc.Regenerate()
    y = y_dau
    khe = ft(KHE_BANG_MM)
    for si, vs, cach in reversed(bang):
        bb_ = si.get_BoundingBox(sh)
        w, h = bb_.Max.X - bb_.Min.X, bb_.Max.Y - bb_.Min.Y
        si.Point = XYZ(x1 - w, y + h, 0)           # Point = góc trên trái của bảng
        y += h + khe
        bao.append(u"Bảng '%s' (%s)." % (vs.Name, cach))
    doc.Regenerate()
    # Mặt bằng có chạm vùng bảng không
    try:
        vp = [v for v in FilteredElementCollector(doc, sh.Id).OfClass(Viewport) if v.ViewId.Value == view.Id.Value][0]
        o = vp.GetBoxOutline()
        rong = max([si.get_BoundingBox(sh).Max.X - si.get_BoundingBox(sh).Min.X for si, _, _ in bang] or [0.0])
        if bang and o.MaximumPoint.X > x1 - rong - khe and o.MinimumPoint.Y < y:
            bao.append(u"CẦN XEM LẠI: khung mặt bằng có thể chạm bảng thống kê góc phải dưới – dời tay nếu cần.")
    except Exception:
        pass
    TransactionManager.Instance.TransactionTaskDone()
    return bao


# ==== PHẦN CHUNG ĐẶT SHEET (nguồn: DatSheet_chung.py, chép vào file công cụ bằng gop_dat_sheet.py – sửa ở nguồn) ====
# Đặt mặt bằng vừa vẽ lên bản vẽ (người dùng yêu cầu 2026-11-03 cho Chống thấm + Ngăn cháy lan, cùng cách nút Tag cửa):
#   - Tạo sheet: khung tên theo khổ (A1 / A0), số hiệu (trống = tiếp theo trong hạng mục), tên, gán giai đoạn / hạng mục
#     theo cách nhóm sheet trong Project Browser của dự án (giống cap_thu_muc_sheet / ts_giai_doan của TagCua_TuDong.py).
#   - Mặt bằng đặt GIỮA vùng vẽ, giữ nguyên tỉ lệ của view (không sửa view template), "Title on Sheet" = tên sheet nếu
#     đang trống. View đã nằm trên sheet thì không đặt thêm.
#   - Thu trục của file hiện tại trong view về sát quanh nhà (đầu trục ViewSpecific, cách mép tường SH_TRUC_DU_MM giấy)
#     để khung viewport không bị trục dài đẩy lệch / tràn khổ (thử G19: trục A, X1 làm khung rộng 720 > 681 mm).
#   - Chú thích (ô mẫu hatch / nét + chữ) vẽ trong drafting view "CHÚ THÍCH - <tên sheet>" cùng tỉ lệ mặt bằng (mẫu
#     hatch theo model co giãn đúng như trên mặt bằng), đặt sát góc phải dưới vùng vẽ. Chữ chỉ là tên vùng, không ghi
#     vật liệu / chiều cao vén (chưa có số liệu).
# Tạo view khi tầng chưa có (người dùng yêu cầu 2026-11-04, "tạo view, đặt template như MB định vị cửa"): sh_tao_view
#   nhân bản mặt bằng tầng đang mở (không kèm chú thích) thành "<MẪU> - <tầng>", loại view riêng (mục riêng trong
#   Project Browser), gán view template có chữ khoá trong tên (vd. G19 "1.7 Mặt Bằng Chống thấm"); chưa có thì tạo
#   template mới từ template của view gốc: sàn Halftone + tắt mẫu tô, ẩn nội thất / thiết bị cơ điện / ký hiệu mặt
#   đứng, mặt cắt; tường / cột / vách + ẩn trục link như MB định vị cửa (sh_trinh_bay_template, cũng bổ sung cho
#   template công cụ đã tạo trước). KHÔNG ẩn hạng mục thiết bị vệ sinh (công cụ ẩn từng cái, giữ phễu thoát sàn).
#   Template mới: kiểu hiển thị Hidden Line, TẮT các filter chép theo view gốc (thử G19: filter vật liệu sàn tô đặc cả mặt bằng), không xoá filter.
#   View mới: crop = khung bao tường + SH_CROP_DU_MM giấy (view gốc G19 crop rất lớn → mặt bằng trôi ra ngoài khổ).
#   Template đã có thì dùng nguyên, không sửa. Không sửa view gốc / template gốc.
# Hàm, hằng ở khối này có tiền tố sh_ / SH_ để không trùng tên với file công cụ.
SH_BIEN_MM = 8.0             # lề trong vùng vẽ của khung tên (mm giấy)
SH_TIEU_DE_MM = 15.0         # chỗ tên view dưới viewport
SH_O_MAU_MM = (16.0, 7.0)    # ô mẫu chú thích (rộng, cao) mm giấy
SH_DONG_MM = 11.0            # khoảng cách dòng chú thích
SH_KHE_CHU_MM = 4.0          # khe giữa ô mẫu và chữ
SH_AN_VIEW_MOI = ("OST_Furniture", "OST_FurnitureSystems", "OST_Casework", "OST_SpecialityEquipment",
                  "OST_MechanicalEquipment", "OST_Elev", "OST_Sections")   # hạng mục ẩn trong template mới
SH_HALFTONE_VIEW_MOI = ("OST_Floors",)          # tường: theo filter tường xây / vách BTCT như MB định vị cửa
# Tường / cột / vách + ẩn trục link như template MB định vị cửa (người dùng yêu cầu 2026-11-04; chép từ
# TagCua_TuDong.py, cùng tên filter nên các công cụ dùng chung filter)
SH_FILTER_TRUC_LINK = u"ARV_Ẩn trục file link"
SH_FILTER_BTCT = u"ARV_Vách BTCT"
SH_FILTER_XAY = u"ARV_Tường xây"
SH_FILTER_COT = u"ARV_Cột BTCT"
SH_TU_KHOA_BTCT = (u"BTCT", u"VBT", u"WS_", u"Concrete", u"Bê tông")
SH_MAU_TO_BTCT = (100, 100, 100)
SH_COT_BTCT = ("OST_StructuralColumns", "OST_Columns")
SH_CROP_DU_MM = 35.0         # view mới: crop = khung bao tường + lề này (mm giấy), đủ chỗ bóng trục đã thu (20 mm)
SH_TRUC_DU_MM = 20.0         # đầu trục cách mép nhà (mm giấy) khi thu trục (như nút Tag cửa, người dùng duyệt 2026-11-03)


def sh_ft(v):
    return UnitUtils.ConvertToInternalUnits(v, UnitTypeId.Millimeters)


def sh_mm(v):
    return UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.Millimeters)


def sh_kd(s):
    s = unicodedata.normalize("NFD", u"%s" % (s or u"")).replace(u"đ", u"d").replace(u"Đ", u"D")
    return u"".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def sh_ten(e):
    try:
        return Element.Name.GetValue(e)
    except Exception:
        pass
    try:
        return e.Name
    except Exception:
        return u"?"


def sh_ts(e, pid):
    for prm in e.Parameters:
        if prm.Id.Value == pid.Value:
            return prm
    return None


def sh_gt(prm):
    try:
        return (prm.AsString() or u"") if prm.StorageType == StorageType.String else (prm.AsValueString() or u"")
    except Exception:
        return u""


def sh_cap_thu_muc(doc):
    """Id tham số các cấp nhóm sheet trong Project Browser (vd. giai đoạn → hạng mục), đọc từ sheet đầu tiên có thư mục."""
    try:
        bo = BrowserOrganization.GetCurrentBrowserOrganizationForSheets(doc)
    except Exception:
        return []
    for s in FilteredElementCollector(doc).OfClass(ViewSheet):
        try:
            items = list(bo.GetFolderItems(s.Id))
        except Exception:
            continue
        if items:
            return [it.ElementId for it in items]
    return []


def sh_gd_hm(doc, cap):
    """(id tham số giai đoạn, id tham số hạng mục). Browser 2 cấp: cấp 1 = giai đoạn, cấp 2 = hạng mục. 1 cấp: cấp đó là
    hạng mục, giai đoạn = tham số sheet có chữ "giai đoạn" dùng nhiều nhất."""
    if len(cap) >= 2:
        return cap[0], cap[1]
    hm = cap[0] if cap else None
    dem = {}
    for s in FilteredElementCollector(doc).OfClass(ViewSheet):
        for prm in s.Parameters:
            if prm.Definition is not None and prm.StorageType == StorageType.String and \
                    u"giai doan" in sh_kd(prm.Definition.Name) and (hm is None or prm.Id.Value != hm.Value):
                k = prm.Id.Value
                dem.setdefault(k, [prm.Id, 0])
                if prm.AsString():
                    dem[k][1] += 1
    gd = max(dem.values(), key=lambda x: x[1])[0] if dem else None
    return gd, hm


def sh_so_tiep(doc, pid_gd, gd, pid_hm, hm, mac_dinh):
    """Số hiệu tiếp theo trong cùng hạng mục (tăng phần số cuối, giữ số chữ số); hạng mục chưa có sheet thì mac_dinh."""
    import re
    dung = set(s.SheetNumber for s in FilteredElementCollector(doc).OfClass(ViewSheet))
    cung = []
    for s in FilteredElementCollector(doc).OfClass(ViewSheet):
        if pid_hm is not None and hm:
            p_ = sh_ts(s, pid_hm)
            if p_ is None or sh_gt(p_) != hm:
                continue
            if pid_gd is not None and gd:
                q_ = sh_ts(s, pid_gd)
                if q_ is not None and sh_gt(q_) and sh_gt(q_) != gd:
                    continue
            cung.append(s.SheetNumber)
    goc = None
    for so in sorted(cung):
        if re.search(r"\d+$", so):
            goc = so
    if goc is None:
        goc = mac_dinh
    m = re.search(r"(\d+)$", goc)
    dau, n, w = (goc[:m.start()], int(m.group(1)), len(m.group(1))) if m else (goc + u".", 0, 2)
    while True:
        n += 1
        ung = u"%s%0*d" % (dau, w, n)
        if ung not in dung:
            return ung


def sh_khung_ten(doc, kho, khung):
    ds = list(FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_TitleBlocks))
    if khung:
        for s in ds:
            if khung in (u"%s : %s" % (s.FamilyName, sh_ten(s)), sh_ten(s), s.FamilyName):
                return s
    k = sh_kd(kho or u"A1").replace(u" ", u"")
    ung = [s for s in ds if k in sh_kd(s.FamilyName + u" " + sh_ten(s)).replace(u" ", u"")
           and u"bia" not in sh_kd(s.FamilyName + u" " + sh_ten(s))]
    ung.sort(key=lambda s: (0 if u"khung" in sh_kd(s.FamilyName) else 1, s.FamilyName))
    return ung[0] if ung else None


def sh_net_khung(doc, tb_sym):
    """Nét đứng [(x, dài)] / ngang [(y, dài)] của family khung tên (toạ độ family), đọc trong file family (đóng không lưu)
    vì hình học khung tên trên sheet trả về rỗng. Gọi NGOÀI transaction."""
    dung, ngang = [], []
    fd = None
    try:
        TransactionManager.Instance.ForceCloseTransaction()
        fd = doc.EditFamily(tb_sym.Family)
        for c in FilteredElementCollector(fd).OfClass(CurveElement):
            try:
                g = c.GeometryCurve
                if g is None or not g.IsBound or g.GetType().Name != "Line":
                    continue
                a, b_ = g.GetEndPoint(0), g.GetEndPoint(1)
                if abs(a.X - b_.X) < 1e-6:
                    dung.append((a.X, abs(a.Y - b_.Y)))
                elif abs(a.Y - b_.Y) < 1e-6:
                    ngang.append((a.Y, abs(a.X - b_.X)))
            except Exception:
                pass
    except Exception:
        pass
    finally:
        if fd is not None:
            try:
                fd.Close(False)
            except Exception:
                pass
    return dung, ngang


def sh_vung_ve(sheet, tb_inst, net):
    """Vùng vẽ (x0, y0, x1, y1) trên sheet: trong khung trong, bên trái dải khung tên phải (đo từ nét dài của family
    khung tên; không đo được thì khung bao trừ lề 25 / 15 mm và 1/6 bên phải)."""
    tf = tb_inst.GetTotalTransform()
    dung = [(tf.OfPoint(XYZ(x, 0, 0)).X, l) for x, l in net[0]]
    ngang = [(tf.OfPoint(XYZ(0, y, 0)).Y, l) for y, l in net[1]]
    bb = tb_inst.get_BoundingBox(sheet)
    X0, Y0, X1, Y1 = bb.Min.X, bb.Min.Y, bb.Max.X, bb.Max.Y
    W, H = X1 - X0, Y1 - Y0
    d40 = sh_ft(40.0)
    dai_d = [x for x, l in dung if l > 0.6 * H]
    dai_n = [y for y, l in ngang if l > 0.6 * W]
    x0 = max([x for x in dai_d if x < X0 + d40] or [X0 + sh_ft(25.0)])
    x1 = max([x for x in dai_d if X0 + d40 < x < X1 - d40] or [X1 - W / 6.0])
    y0 = max([y for y in dai_n if y < Y0 + d40] or [Y0 + sh_ft(15.0)])
    y1 = min([y for y in dai_n if y > Y1 - d40] or [Y1 - sh_ft(15.0)])
    return x0, y0, x1, y1


def sh_kieu_viewport(doc, co_tieu_de):
    """Kiểu viewport: co_tieu_de = có nhãn tên view (ưu tiên kiểu không phải 'no scale' / 'detail'); không thì kiểu tắt
    tên (Show Title = No). Không có kiểu phù hợp → None (giữ mặc định)."""
    kieu = []
    for et in FilteredElementCollector(doc).OfClass(ElementType):
        try:
            if et.FamilyName != "Viewport":
                continue
            hien = et.get_Parameter(BuiltInParameter.VIEWPORT_ATTR_SHOW_LABEL)
            nhan = et.get_Parameter(BuiltInParameter.VIEWPORT_ATTR_LABEL_TAG)
            n = sh_kd(sh_ten(et))
            if co_tieu_de:
                if nhan is None or nhan.AsElementId() == ElementId.InvalidElementId or (hien is not None and hien.AsInteger() == 0):
                    continue
                kieu.append((0 if u"no scale" not in n and u"detail" not in n else 1, sh_ten(et), et))
            elif hien is not None and hien.AsInteger() == 0:
                kieu.append((0 if u"no title" in n else 1, sh_ten(et), et))
        except Exception:
            pass
    kieu.sort(key=lambda k: (k[0], k[1]))
    return kieu[0][2] if kieu else None


def sh_kieu_chu(doc):
    """Kiểu chữ chú thích: Arial cao 2–3 mm (gần 2.5 nhất), không có thì kiểu mặc định của dự án."""
    ung = []
    for t in FilteredElementCollector(doc).OfClass(TextNoteType):
        try:
            cao = sh_mm(t.get_Parameter(BuiltInParameter.TEXT_SIZE).AsDouble())
            font = sh_kd(t.get_Parameter(BuiltInParameter.TEXT_FONT).AsString())
            if u"arial" in font and 1.9 <= cao <= 3.1:
                ung.append((abs(cao - 2.5), -cao, sh_ten(t), t.Id))
        except Exception:
            pass
    ung.sort(key=lambda k: (k[0], k[1], k[2]))
    return ung[0][3] if ung else doc.GetDefaultElementTypeId(ElementTypeGroup.TextNoteType)


def sh_thu_truc(doc, view):
    """Đầu trục của file hiện tại trong view → ViewSpecific, cắt theo khung bao tường + SH_TRUC_DU_MM × tỉ lệ. Chỉ đổi
    hiển thị trục trong view này (không đổi trục 3D / view khác); trục của link không sửa. Gọi TRONG transaction."""
    xs, ys = [], []
    for w in FilteredElementCollector(doc, view.Id).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType():
        bb = w.get_BoundingBox(view)
        if bb is not None:
            xs += [bb.Min.X, bb.Max.X]
            ys += [bb.Min.Y, bb.Max.Y]
    if not xs:
        return u"Không có tường trong view – không thu trục."
    goc_bb = [XYZ(x, y, 0) for x in (min(xs), max(xs)) for y in (min(ys), max(ys))]
    du = sh_ft(SH_TRUC_DU_MM * view.Scale)
    n = 0
    for g in FilteredElementCollector(doc, view.Id).OfClass(Grid):
        try:
            if g.IsCurved:
                continue
            ds = g.GetCurvesInView(DatumExtentType.ViewSpecific, view)
            if ds is None or ds.Count != 1:
                continue
            cv = ds[0]
            p0, p1 = cv.GetEndPoint(0), cv.GetEndPoint(1)
            d = (p1 - p0).Normalize()
            ts = [(q.X - p0.X) * d.X + (q.Y - p0.Y) * d.Y for q in goc_bb]
            a, b = p0 + d * (min(ts) - du), p0 + d * (max(ts) + du)
            a, b = XYZ(a.X, a.Y, p0.Z), XYZ(b.X, b.Y, p1.Z)
            for dau in (DatumEnds.End0, DatumEnds.End1):
                if g.GetDatumExtentTypeInView(dau, view) != DatumExtentType.ViewSpecific:
                    g.SetDatumExtentType(dau, view, DatumExtentType.ViewSpecific)
            g.SetCurveInView(DatumExtentType.ViewSpecific, view, Line.CreateBound(a, b))
            n += 1
        except Exception:
            pass
    return u"Thu trục: %d trục cắt sát nhà (cách mép tường %g mm giấy)." % (n, SH_TRUC_DU_MM)


def sh_chu_thich(doc, ten_view, ti_le, muc):
    """Drafting view chú thích. muc: [{"vung": id kiểu Filled Region, "vien": id line style | None, "chu": u"..."} |
    {"net": GraphicsStyle, "chu": u"..."}]. Trả về (view, báo cáo). Gọi TRONG transaction."""
    for v in FilteredElementCollector(doc).OfClass(ViewDrafting):
        if not v.IsTemplate and v.Name == ten_view:
            sh_ = v.get_Parameter(BuiltInParameter.VIEWER_SHEET_NUMBER)
            if sh_ is not None and sh_.AsString() and sh_.AsString() not in (u"---", u"-"):
                return None, u"Chú thích '%s' đã nằm trên sheet %s – không đặt thêm." % (ten_view, sh_.AsString())
            return v, u"dùng lại view chú thích '%s'" % ten_view
    vft = [t for t in FilteredElementCollector(doc).OfClass(ViewFamilyType) if t.ViewFamily == ViewFamily.Drafting]
    if not vft:
        return None, u"Dự án không có kiểu Drafting View – không vẽ chú thích."
    v = ViewDrafting.Create(doc, vft[0].Id)
    v.Name = ten_view
    v.Scale = ti_le
    s = float(ti_le)
    w, h = sh_ft(SH_O_MAU_MM[0] * s), sh_ft(SH_O_MAU_MM[1] * s)
    dong, khe = sh_ft(SH_DONG_MM * s), sh_ft(SH_KHE_CHU_MM * s)
    kc = sh_kieu_chu(doc)
    opt = TextNoteOptions(kc)
    opt.HorizontalAlignment = HorizontalTextAlignment.Left
    opt.VerticalAlignment = VerticalTextAlignment.Middle
    TextNote.Create(doc, v.Id, XYZ(0, 0, 0), u"CHÚ THÍCH:", opt)
    y = -dong
    for m in muc:
        yc = y
        if "vung" in m:
            cl = CurveLoop()
            p = [XYZ(0, yc - h / 2, 0), XYZ(w, yc - h / 2, 0), XYZ(w, yc + h / 2, 0), XYZ(0, yc + h / 2, 0)]
            for i in range(4):
                cl.Append(Line.CreateBound(p[i], p[(i + 1) % 4]))
            ds = NetList[CurveLoop]()
            ds.Add(cl)
            fr = FilledRegion.Create(doc, m["vung"], v.Id, ds)
            if m.get("vien") is not None:
                fr.SetLineStyleId(m["vien"])
        else:
            dc = doc.Create.NewDetailCurve(v, Line.CreateBound(XYZ(0, yc, 0), XYZ(w, yc, 0)))
            dc.LineStyle = m["net"]
        TextNote.Create(doc, v.Id, XYZ(w + khe, yc, 0), m["chu"], opt)
        y -= dong
    return v, u"tạo view chú thích '%s' (%d mục)" % (ten_view, len(muc))


def sh_tao_view(doc, goc, tu_khoa, ten_mau, dry):
    """View mặt bằng mới cho tầng của view goc (xem chú thích đầu khối). tu_khoa: chữ khoá không dấu (vd. "chong tham")
    để nhận template có sẵn; ten_mau: tên in hoa (vd. "MẶT BẰNG CHỐNG THẤM") = tên template mới, tên loại view và tiền
    tố tên view. Trả về (view, [báo cáo]); dry: chỉ báo, trả về goc."""
    bao = []
    tang = goc.GenLevel.Name
    ten_moi = u"%s - %s" % (ten_mau, tang)
    tpl_goc = doc.GetElement(goc.ViewTemplateId) if goc.ViewTemplateId != ElementId.InvalidElementId else None
    tpl = None
    for v in FilteredElementCollector(doc).OfClass(View):
        if v.IsTemplate and v.ViewType == ViewType.FloorPlan and tu_khoa in sh_kd(v.Name):
            if tpl is None or v.Name == ten_mau:
                tpl = v
    if dry:
        bao.append(u"Sẽ tạo view '%s' (nhân bản '%s'), template '%s' – Dry-run tính trên view gốc." % (
            ten_moi, goc.Name, tpl.Name if tpl is not None else u"%s (tạo mới)" % ten_mau))
        return goc, bao
    TransactionManager.Instance.EnsureInTransaction(doc)
    moi = doc.GetElement(goc.Duplicate(ViewDuplicateOption.Duplicate))
    ten_dat, k = ten_moi, 1
    dung = set(v.Name for v in FilteredElementCollector(doc).OfClass(View) if not v.IsTemplate)
    while ten_dat in dung:
        k += 1
        ten_dat = u"%s (%d)" % (ten_moi, k)
    moi.Name = ten_dat
    bao.append(u"Tạo view '%s' (nhân bản '%s', không kèm chú thích)." % (ten_dat, goc.Name))
    if tpl is None:
        # Template không nhân bản được qua API → gán template nền, Regenerate rồi CreateViewTemplate (như Tag cửa).
        # KHÔNG dùng ApplyViewTemplateParameters: Revit 2027.3 lỗi nặng.
        if tpl_goc is not None:
            moi.ViewTemplateId = tpl_goc.Id
        doc.Regenerate()
        tpl = moi.CreateViewTemplate()
        tpl.Name = ten_mau
        try:
            pid = ElementId(BuiltInParameter.VIS_GRAPHICS_MODEL)
            nc = list(tpl.GetNonControlledTemplateParameterIds())
            if any(i.Value == pid.Value for i in nc):
                ds = NetList[ElementId]()
                for i in nc:
                    if i.Value != pid.Value:
                        ds.Add(i)
                tpl.SetNonControlledTemplateParameterIds(ds)
        except Exception:
            pass
        for n in SH_HALFTONE_VIEW_MOI:
            try:
                c = ElementId(getattr(BuiltInCategory, n))
                o = tpl.GetCategoryOverrides(c)
                o.SetHalftone(True)
                if n == "OST_Floors":
                    o.SetSurfaceForegroundPatternVisible(False)
                    o.SetSurfaceBackgroundPatternVisible(False)
                    o.SetCutForegroundPatternVisible(False)
                    o.SetCutBackgroundPatternVisible(False)
                tpl.SetCategoryOverrides(c, o)
            except Exception:
                pass
        try:     # template gốc có thể là Shaded / Consistent Colors (thử G19: sàn, tường tô màu vật liệu) → Hidden Line
            if tpl.DisplayStyle != DisplayStyle.HLR:
                cu_ = tpl.DisplayStyle
                tpl.DisplayStyle = DisplayStyle.HLR
                bao.append(u"Template mới: kiểu hiển thị %s → Hidden Line." % cu_)
        except Exception as ex:
            bao.append(u"Không đặt được Hidden Line cho template: %s" % (u"%s" % ex).splitlines()[0][:120])
        tat = 0
        for fid in list(tpl.GetFilters()):
            try:
                if sh_ten(doc.GetElement(fid)).startswith(u"ARV_"):
                    continue
                if tpl.GetIsFilterEnabled(fid):
                    tpl.SetIsFilterEnabled(fid, False)
                    tat += 1
            except Exception:
                pass
        if tat:
            bao.append(u"Template mới: tắt %d filter chép theo view gốc (không xoá filter)." % tat)
        an = []
        for n in SH_AN_VIEW_MOI:
            try:
                c = ElementId(getattr(BuiltInCategory, n))
                if tpl.CanCategoryBeHidden(c) and not tpl.GetCategoryHidden(c):
                    tpl.SetCategoryHidden(c, True)
                an.append(Category.GetCategory(doc, c).Name)
            except Exception:
                pass
        bao.append(u"Tạo view template '%s' từ '%s': sàn Halftone, tắt mẫu tô, ẩn: %s." % (
            ten_mau, tpl_goc.Name if tpl_goc is not None else u"view gốc", u", ".join(an)))
        bao.extend(sh_trinh_bay_template(doc, tpl))
    elif tpl.Name == ten_mau:
        bao.append(u"Dùng view template '%s' (công cụ tạo trước đó)." % tpl.Name)
        bao.extend(sh_trinh_bay_template(doc, tpl))
    else:
        bao.append(u"Dùng view template có sẵn '%s' (không sửa)." % tpl.Name)
    try:          # loại view riêng → mục "Floor Plans (<MẪU>)" trong Project Browser, như Tag cửa
        vft = None
        for t_ in FilteredElementCollector(doc).OfClass(ViewFamilyType):
            if t_.ViewFamily == ViewFamily.FloorPlan and sh_ten(t_) == ten_mau:
                vft = t_
        if vft is None:
            vft = doc.GetElement(moi.GetTypeId()).Duplicate(ten_mau)
            bao.append(u"Tạo loại view '%s' (mục riêng trong Project Browser)." % ten_mau)
        if moi.GetTypeId().Value != vft.Id.Value:
            moi.ChangeTypeId(vft.Id)
    except Exception as ex:
        bao.append(u"Không gán được loại view '%s': %s" % (ten_mau, (u"%s" % ex).splitlines()[0][:150]))
    if moi.ViewTemplateId.Value != tpl.Id.Value:
        moi.ViewTemplateId = tpl.Id
    doc.Regenerate()
    try:
        bao.append(sh_crop_theo_tuong(doc, moi))
    except Exception as ex:
        bao.append(u"Không đặt được crop: %s" % (u"%s" % ex).splitlines()[0][:150])
    TransactionManager.Instance.TransactionTaskDone()
    return moi, bao


def sh_chuan_template(doc, view, ten_mau):
    """View đã có: template là template công cụ tạo (tên = ten_mau) thì bổ sung tường / cột / vách + ẩn trục link (bản
    tạo trước 2026-11-04 chưa có). Template người dùng tự làm (vd. G19 "1.7 Mặt Bằng Chống thấm") không sửa."""
    tpl = doc.GetElement(view.ViewTemplateId) if view.ViewTemplateId != ElementId.InvalidElementId else None
    if tpl is None or tpl.Name != ten_mau:
        return []
    TransactionManager.Instance.EnsureInTransaction(doc)
    bao = sh_trinh_bay_template(doc, tpl)
    doc.Regenerate()
    TransactionManager.Instance.TransactionTaskDone()
    return bao


def sh_trinh_bay_template(doc, tpl):
    """Template công cụ tạo: ẩn trục link + tường / cột / vách như MB định vị cửa; bật lại các filter ARV_. Gọi TRONG
    transaction."""
    bao = []
    for ham, nhan in ((sh_an_truc_link, u"ẩn trục file link"), (sh_trinh_bay_btct, u"tường / cột / vách")):
        try:
            bao.append(ham(doc, tpl))
        except Exception as ex:
            bao.append(u"Không chỉnh được %s: %s" % (nhan, (u"%s" % ex).splitlines()[0][:150]))
    for fid in list(tpl.GetFilters()):
        try:
            if sh_ten(doc.GetElement(fid)).startswith(u"ARV_") and not tpl.GetIsFilterEnabled(fid):
                tpl.SetIsFilterEnabled(fid, True)
        except Exception:
            pass
    return bao


def sh_bo_dieu_khien(tpl, bip):
    """Bỏ tham số bip khỏi danh sách KHÔNG điều khiển của template (để template điều khiển nó)."""
    try:
        pid = ElementId(bip)
        nc = list(tpl.GetNonControlledTemplateParameterIds())
        if any(i.Value == pid.Value for i in nc):
            ds = NetList[ElementId]()
            for i in nc:
                if i.Value != pid.Value:
                    ds.Add(i)
            tpl.SetNonControlledTemplateParameterIds(ds)
    except Exception:
        pass


def sh_an_truc_link(doc, tpl):
    """Ẩn trục của file link, giữ trục file hiện tại: filter Grids "Type Name khác mọi loại trục của file hiện tại", ẩn
    trong template (API 2027.3 không tắt riêng Grids của link theo view). Như an_truc_link của TagCua_TuDong.py."""
    loai_truc = sorted(set(sh_ten(doc.GetElement(g.GetTypeId())) for g in FilteredElementCollector(doc).OfClass(Grid)))
    if not loai_truc:
        return u"File không có trục riêng – không tạo filter ẩn trục link."
    cats = NetList[ElementId]()
    cats.Add(ElementId(BuiltInCategory.OST_Grids))
    loc_duoc = [p_.Value for p_ in ParameterFilterUtilities.GetFilterableParametersInCommon(doc, cats)]
    pid = None
    for b_ in (BuiltInParameter.ALL_MODEL_TYPE_NAME, BuiltInParameter.SYMBOL_NAME_PARAM):
        if int(b_) in loc_duoc:
            pid = ElementId(b_)
            break
    if pid is None:
        return u"Không có tham số tên loại lọc được cho Grids – chưa ẩn trục link (ẩn tay: V/G → Revit Links)."
    f_ = None
    for x in FilteredElementCollector(doc).OfClass(ParameterFilterElement):
        if x.Name == SH_FILTER_TRUC_LINK:
            f_ = x
    loc = [ElementParameterFilter(ParameterFilterRuleFactory.CreateNotEqualsRule(pid, t_)) for t_ in loai_truc]
    loc_net = NetList[ElementFilter]()
    for x in loc:
        loc_net.Add(x)
    bo = loc[0] if len(loc) == 1 else LogicalAndFilter(loc_net)
    if f_ is None:
        f_ = ParameterFilterElement.Create(doc, SH_FILTER_TRUC_LINK, cats, bo)
    else:
        f_.SetElementFilter(bo)
    sh_bo_dieu_khien(tpl, BuiltInParameter.VIS_GRAPHICS_FILTERS)
    if not any(i.Value == f_.Id.Value for i in tpl.GetFilters()):
        tpl.AddFilter(f_.Id)
    tpl.SetFilterVisibility(f_.Id, False)
    return u"Ẩn trục file link: filter '%s' (Grids, loại trục khác %s)." % (SH_FILTER_TRUC_LINK, u", ".join(loai_truc))


def sh_ghi_de_btct(dac):
    o = OverrideGraphicSettings()
    o.SetCutLineColor(Color(0, 0, 0))
    o.SetProjectionLineColor(Color(0, 0, 0))
    if dac is not None:
        o.SetCutForegroundPatternId(dac)
        o.SetCutForegroundPatternColor(Color(*SH_MAU_TO_BTCT))
        o.SetCutForegroundPatternVisible(True)
    return o


def sh_trinh_bay_btct(doc, tpl):
    """Tường xây Halftone không tô, cột + vách BTCT tô đặc xám đậm viền đen bằng 3 filter (như trinh_bay_btct của
    TagCua_TuDong.py: màu nét ghi đè theo hạng mục Walls không ăn trong Revit 2027.3). Template đã có filter vách BTCT
    thì giữ nguyên (người dùng có thể đã chỉnh tay)."""
    fs = {}
    for x in FilteredElementCollector(doc).OfClass(ParameterFilterElement):
        if x.Name in (SH_FILTER_BTCT, SH_FILTER_XAY, SH_FILTER_COT):
            fs[x.Name] = x
    f_ = fs.get(SH_FILTER_BTCT)
    if f_ is not None and any(i.Value == f_.Id.Value for i in tpl.GetFilters()):
        return u"Tường / cột / vách: template đã có filter '%s', giữ nguyên." % SH_FILTER_BTCT
    dac = None
    for fp in FilteredElementCollector(doc).OfClass(FillPatternElement):
        try:
            p_ = fp.GetFillPattern()
            if p_.IsSolidFill and p_.Target == FillPatternTarget.Drafting:
                dac = fp.Id
                break
        except Exception:
            pass
    sh_bo_dieu_khien(tpl, BuiltInParameter.VIS_GRAPHICS_FILTERS)
    o = OverrideGraphicSettings()          # thay cả ghi đè cũ của hạng mục Walls (bản trước để Halftone cả hạng mục)
    o.SetCutForegroundPatternVisible(False)
    o.SetCutBackgroundPatternVisible(False)
    tpl.SetCategoryOverrides(ElementId(BuiltInCategory.OST_Walls), o)
    cats = NetList[ElementId]()
    cats.Add(ElementId(BuiltInCategory.OST_Walls))
    loc_duoc = [p_.Value for p_ in ParameterFilterUtilities.GetFilterableParametersInCommon(doc, cats)]
    co, khong = [], []
    b_kc = BuiltInParameter.WALL_STRUCTURAL_USAGE_PARAM
    if int(b_kc) in loc_duoc:
        co.append(ElementParameterFilter(ParameterFilterRuleFactory.CreateNotEqualsRule(ElementId(b_kc), 0)))
        khong.append(ElementParameterFilter(ParameterFilterRuleFactory.CreateNotEqualsRule(ElementId(b_kc), 0), True))
    b_ten = None
    for b_ in (BuiltInParameter.ALL_MODEL_TYPE_NAME, BuiltInParameter.SYMBOL_NAME_PARAM):
        if int(b_) in loc_duoc:
            b_ten = b_
            break
    for k in (SH_TU_KHOA_BTCT if b_ten is not None else ()):
        r_ = ParameterFilterRuleFactory.CreateContainsRule(ElementId(b_ten), k)
        co.append(ElementParameterFilter(r_))
        khong.append(ElementParameterFilter(r_, True))
    if not co:
        return u"Không có tham số lọc được để nhận vách BTCT – chỉnh tay trong V/G."

    def gop(ds_, lop):
        if len(ds_) == 1:
            return ds_[0]
        net = NetList[ElementFilter]()
        for x in ds_:
            net.Add(x)
        return lop(net)

    def dat(ten_f, cats_, bo, ghi_de):
        f = fs.get(ten_f)
        if f is None:
            f = (ParameterFilterElement.Create(doc, ten_f, cats_, bo) if bo is not None
                 else ParameterFilterElement.Create(doc, ten_f, cats_))
        elif bo is not None:
            f.SetElementFilter(bo)
        if not any(i.Value == f.Id.Value for i in tpl.GetFilters()):
            tpl.AddFilter(f.Id)
        tpl.SetFilterOverrides(f.Id, ghi_de)

    dat(SH_FILTER_BTCT, cats, gop(co, LogicalOrFilter), sh_ghi_de_btct(dac))
    o = OverrideGraphicSettings()
    o.SetHalftone(True)
    dat(SH_FILTER_XAY, cats, gop(khong, LogicalAndFilter), o)
    cats_cot = NetList[ElementId]()
    for n in SH_COT_BTCT:
        cats_cot.Add(ElementId(getattr(BuiltInCategory, n)))
    dat(SH_FILTER_COT, cats_cot, None, sh_ghi_de_btct(dac))
    return (u"Tường xây Halftone, không tô (filter '%s'); vách BTCT (filter '%s') + cột (filter '%s') tô đặc xám %s viền "
            u"đen, như MB định vị cửa." % (SH_FILTER_XAY, SH_FILTER_BTCT, SH_FILTER_COT, SH_MAU_TO_BTCT))


def sh_crop_theo_tuong(doc, view):
    """Crop view = khung bao tường trong view + SH_CROP_DU_MM × tỉ lệ (toạ độ theo hệ của CropBox), khung crop ẩn."""
    cb = view.CropBox
    tf = cb.Transform
    inv = tf.Inverse
    xs, ys = [], []
    for w in FilteredElementCollector(doc, view.Id).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType():
        bb = w.get_BoundingBox(None)
        if bb is None:
            continue
        for x in (bb.Min.X, bb.Max.X):
            for y in (bb.Min.Y, bb.Max.Y):
                q = inv.OfPoint(XYZ(x, y, 0))
                xs.append(q.X)
                ys.append(q.Y)
    if not xs:
        return u"Không có tường trong view – giữ crop của view gốc."
    du = sh_ft(SH_CROP_DU_MM * view.Scale)
    moi = BoundingBoxXYZ()
    moi.Transform = tf
    moi.Min = XYZ(min(xs) - du, min(ys) - du, cb.Min.Z)
    moi.Max = XYZ(max(xs) + du, max(ys) + du, cb.Max.Z)
    view.CropBox = moi
    view.CropBoxActive = True
    view.CropBoxVisible = False
    return u"Crop view mới = khung bao tường + %g mm giấy (%d x %d mm giấy)." % (
        SH_CROP_DU_MM, sh_mm(moi.Max.X - moi.Min.X) / view.Scale, sh_mm(moi.Max.Y - moi.Min.Y) / view.Scale)


def dat_mat_bang_len_sheet(doc, view, gd, hm, kho, khung, so_hieu, ten_sheet, so_mac_dinh, muc_chu_thich):
    """Tạo sheet + đặt mặt bằng giữa vùng vẽ + chú thích góc phải dưới. Trả về [báo cáo]."""
    bao = []
    try:
        dang = view.get_Parameter(BuiltInParameter.VIEWER_SHEET_NUMBER)
        if dang is not None and dang.AsString() and dang.AsString() not in (u"---", u"-"):
            return [u"View '%s' đã nằm trên sheet %s – không đặt thêm." % (view.Name, dang.AsString())]
    except Exception:
        pass
    cap = sh_cap_thu_muc(doc)
    pid_gd, pid_hm = sh_gd_hm(doc, cap)
    so = (so_hieu or u"").strip() or sh_so_tiep(doc, pid_gd, gd, pid_hm, hm, so_mac_dinh)
    # Số hiệu trùng sheet TRỐNG có sẵn (vd. G19 dựng sẵn A.4-201 MẶT BẰNG CHỐNG THẤM) → đặt vào sheet đó, giữ nguyên
    # tên / khung tên / tham số người dùng đã đặt
    trong = [s for s in FilteredElementCollector(doc).OfClass(ViewSheet)
             if s.SheetNumber == so and not s.IsPlaceholder and s.GetAllPlacedViews().Count == 0
             and not any(True for _ in FilteredElementCollector(doc, s.Id).OfClass(ScheduleSheetInstance)
                         if not _.IsTitleblockRevisionSchedule)]
    if trong:
        tbs = [t for t in FilteredElementCollector(doc, trong[0].Id).OfCategory(BuiltInCategory.OST_TitleBlocks)
               .WhereElementIsNotElementType()]
        if tbs:
            return sh_dat_vao(doc, view, trong[0], tbs[0], doc.GetElement(tbs[0].GetTypeId()), muc_chu_thich,
                              [u"Dùng sheet trống có sẵn %s – %s (giữ tên, khung tên, tham số)." % (
                                  so, trong[0].Name)], ten_sheet, cap, None)
    tb = sh_khung_ten(doc, kho, khung)
    if tb is None:
        return [u"Không có family khung tên khổ %s trong dự án (tên family / type có chữ '%s') – chưa đặt lên sheet. "
                u"Load khung tên rồi bấm lại." % (kho, kho)]
    dung = set(s.SheetNumber for s in FilteredElementCollector(doc).OfClass(ViewSheet))
    if so in dung:
        import re
        cu = so
        m = re.search(r"(\d+)$", so)
        dau, n, w = (so[:m.start()], int(m.group(1)), len(m.group(1))) if m else (so + u"-", 0, 1)
        while so in dung:
            n += 1
            so = u"%s%0*d" % (dau, w, n)
        bao.append(u"Số hiệu '%s' đã có – dùng '%s'." % (cu, so))
    TransactionManager.Instance.EnsureInTransaction(doc)
    sh = ViewSheet.Create(doc, tb.Id)
    sh.SheetNumber = so
    sh.Name = ten_sheet
    for pid, gt_, nhan in ((pid_gd, gd, u"giai đoạn"), (pid_hm, hm, u"hạng mục")):
        if pid is None or not gt_:
            continue
        prm = sh_ts(sh, pid)
        if prm is not None and not prm.IsReadOnly:
            prm.Set(gt_)
        else:
            bao.append(u"Không gán được %s '%s' (tham số không ghi được)." % (nhan, gt_))
    doc.Regenerate()
    tb_inst = [t for t in FilteredElementCollector(doc, sh.Id).OfCategory(BuiltInCategory.OST_TitleBlocks)
               .WhereElementIsNotElementType()][0]
    TransactionManager.Instance.TransactionTaskDone()
    return sh_dat_vao(doc, view, sh, tb_inst, tb, muc_chu_thich, bao, ten_sheet, cap, kho)


def sh_dat_vao(doc, view, sh, tb_inst, tb, muc_chu_thich, bao, ten_sheet, cap, kho):
    """Đặt chú thích (góc phải dưới vùng vẽ) + mặt bằng (giữa vùng vẽ, giữ tỉ lệ view) lên sheet sh. Trả về [báo cáo]."""
    net = sh_net_khung(doc, tb)          # mở family khung tên: phải ngoài transaction
    TransactionManager.Instance.EnsureInTransaction(doc)
    x0, y0, x1, y1 = sh_vung_ve(sh, tb_inst, net)
    b = sh_ft(SH_BIEN_MM)
    o_ct = None
    if muc_chu_thich:
        try:
            vct, msg = sh_chu_thich(doc, u"CHÚ THÍCH - %s" % ten_sheet, view.Scale, muc_chu_thich)
            bao.append(u"Chú thích: %s." % msg)
            if vct is not None:
                doc.Regenerate()
                vp_ct = Viewport.Create(doc, sh.Id, vct.Id, XYZ(x1, y0, 0))
                k_ = sh_kieu_viewport(doc, False)
                if k_ is not None:
                    vp_ct.ChangeTypeId(k_.Id)
                doc.Regenerate()
                o_ = vp_ct.GetBoxOutline()
                wc, hc = o_.MaximumPoint.X - o_.MinimumPoint.X, o_.MaximumPoint.Y - o_.MinimumPoint.Y
                vp_ct.SetBoxCenter(XYZ(x1 - b - wc / 2.0, y0 + b + hc / 2.0, 0))
                o_ct = (x1 - b - wc, y0 + b, x1 - b, y0 + b + hc)
        except Exception as ex:
            bao.append(u"Không vẽ được chú thích: %s" % (u"%s" % ex).splitlines()[0][:150])
    try:
        prm = view.get_Parameter(BuiltInParameter.VIEW_DESCRIPTION)
        if prm is not None and not prm.IsReadOnly and not (prm.AsString() or u"").strip():
            prm.Set(ten_sheet)
    except Exception:
        pass
    vx0, vy0, vx1, vy1 = x0 + b, y0 + b + sh_ft(SH_TIEU_DE_MM), x1 - b, y1 - b
    bao.append(sh_thu_truc(doc, view))
    doc.Regenerate()
    vp = Viewport.Create(doc, sh.Id, view.Id, XYZ((vx0 + vx1) / 2.0, (vy0 + vy1) / 2.0, 0))
    k_ = sh_kieu_viewport(doc, True)
    if k_ is not None:
        vp.ChangeTypeId(k_.Id)
    doc.Regenerate()
    o = vp.GetBoxOutline()
    w, h = o.MaximumPoint.X - o.MinimumPoint.X, o.MaximumPoint.Y - o.MinimumPoint.Y
    cx = (vx0 + vx1) / 2.0 if w <= vx1 - vx0 else vx0 + w / 2.0
    cy = (vy0 + vy1) / 2.0 if h <= vy1 - vy0 else vy1 - h / 2.0
    vp.SetBoxCenter(XYZ(cx, cy, 0))
    TransactionManager.Instance.TransactionTaskDone()
    if w > vx1 - vx0 + 1e-6 or h > vy1 - vy0 + 1e-6:
        bao.append(u"CẦN XEM LẠI: mặt bằng 1:%d (kể cả trục, chú thích) %d x %d mm lớn hơn vùng vẽ %d x %d mm – chọn khổ "
                   u"lớn hơn hoặc thu crop view." % (view.Scale, sh_mm(w), sh_mm(h), sh_mm(vx1 - vx0), sh_mm(vy1 - vy0)))
    elif o_ct is not None and cx + w / 2.0 > o_ct[0] and cy - h / 2.0 < o_ct[3]:
        bao.append(u"CẦN XEM LẠI: khung mặt bằng có thể chạm chú thích góc phải dưới – dời tay nếu cần.")
    bao.append(u"ĐÃ ĐẶT lên sheet %s – %s (khung %s : %s%s), mặt bằng 1:%d giữa vùng vẽ, kiểu viewport '%s'." % (
        sh.SheetNumber, sh.Name, tb.FamilyName, sh_ten(tb), u", khổ %s" % kho if kho else u"", view.Scale,
        sh_ten(k_) if k_ is not None else u"mặc định"))
    if not cap:
        bao.append(u"Project Browser không nhóm sheet theo tham số – không gán giai đoạn / hạng mục.")
    return bao
# ==== HẾT PHẦN CHUNG ĐẶT SHEET ====


try:
    OUT = _chinh()
except Exception:
    OUT = [u"LỖI:", traceback.format_exc()]
