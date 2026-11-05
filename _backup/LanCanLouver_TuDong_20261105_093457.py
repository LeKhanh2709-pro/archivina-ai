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
#     IN[2] (Window Tags, G19 "TAG LOUVER MARK"), hạng mục khác → IN[3] (Multi-Category Tags). Dự án chưa có family đó thì
#     dùng / nạp bản đóng gói ARV_Tag Lan Can Mark / ARV_Tag Louver Mark / ARV_Tag Mark Da Hang Muc (thư mục IN[16],
#     mặc định <extension>\lib\tag_lan_can, chép từ 2 family mẫu của người dùng); không có file thì báo, bỏ hạng mục đó.
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
#   IN[3]  (str)   Family tag Mark đa hạng mục (Multi-Category Tags) cho hạng mục khác
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
MAC_DINH = ["", u"AV-Railing Tag- Mark-lan can", u"TAG LOUVER MARK", u"ARV_Tag Mark Da Hang Muc", u"LK;LC", True,
            u"LV", u"Louver;Lam", 1.0, "", False, False, True, TEN_MAU, u"OST_PlumbingFixtures", False, "",
            False, "", "", "A1", "", "", "", True]
# Family tag đóng gói (lib\tag_lan_can\<tên>.rfa): dùng khi dự án không có family IN[1] / IN[2] / IN[3]
DU_PHONG_LAN_CAN = u"ARV_Tag Lan Can Mark"
DU_PHONG_LOUVER = u"ARV_Tag Louver Mark"
DU_PHONG_DA = u"ARV_Tag Mark Da Hang Muc"
SO_MAC_DINH = u"A.DVLC.00"
PHAT_PHIA_MM_GIAY = 8.0     # phạt khi đặt tag ở phía trong nhà (mm giấy, cộng vào khoảng cách)
HE_SO_LECH = 4.0            # mỗi mm dịch khỏi giữa đối tượng tính bằng 4 mm lùi xa
TAM_XA_MM_GIAY = 8.0        # tag xa nhất cách mép đối tượng (mm giấy), như tag cửa
KHE_BANG_MM = 6.0           # khe giữa 2 bảng thống kê (mm giấy)
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
                                                                          DU_PHONG_DA) else u""
    if not duong or not os.path.isfile(duong):
        bao.append(u"CHƯA CÓ family tag '%s' (%s) trong dự án và không thấy file đóng gói '%s' → bỏ hạng mục này."
                   % (ten_fam, Category.GetCategory(doc, bic).Name, duong or u"-"))
        return None
    if dry:
        bao.append(u"Sẽ nạp family tag '%s' từ %s." % (ten_fam, duong))
        return None
    TransactionManager.Instance.EnsureInTransaction(doc)
    doc.LoadFamily(duong, tuy_chon_nap())
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
    hiện tag lan can / cửa sổ / đa hạng mục / Generic Model. Template người dùng tự làm thì không sửa. Gọi TRONG
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
    for bic in (BuiltInCategory.OST_StairsRailingTags, BuiltInCategory.OST_WindowTags, BuiltInCategory.OST_MultiCategoryTags,
                BuiltInCategory.OST_GenericModelTags, BuiltInCategory.OST_StairsRailing, BuiltInCategory.OST_Windows,
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
    # Hạng mục khác có Mark đúng tiền tố (vd. lan can kính dựng bằng tường / curtain wall)
    da_co = set(e.Id.Value for e, _, _, _ in ds)
    for bic in (BuiltInCategory.OST_Walls, BuiltInCategory.OST_SpecialityEquipment, BuiltInCategory.OST_Doors,
                BuiltInCategory.OST_StructuralFraming):
        for e in thay(bic):
            if e.Id.Value in da_co:
                continue
            mk = khong_dau(mark(e))
            if mk and any(mk.startswith(x) for x in tt_lc + tt_lv):
                ds.append((e, LOP_LAN_CAN if any(mk.startswith(x) for x in tt_lc) else LOP_LOUVER, bic, u"Mark"))
    chua_mark = [(e, lop) for e, lop, _, _ in ds if not mark(e)]
    if chua_mark:
        xem_lai.append(u"%d đối tượng CHƯA CÓ Mark (không tag, điền Mark rồi bấm lại): %s" % (
            len(chua_mark), u", ".join(u"%d (%s)" % (e.Id.Value, lop) for e, lop in chua_mark[:30])))

    # ---------- Kiểu tag (nạp family đóng gói nếu thiếu; ngoài transaction) ----------
    def dung_tien_to(e, lop):
        mk = khong_dau(mark(e))
        return bool(mk) and any(mk.startswith(x) for x in (tt_lc if lop == LOP_LAN_CAN else tt_lv))

    sai_tt = [(e, lop) for e, lop, _, _ in ds if mark(e) and not dung_tien_to(e, lop)]
    if sai_tt and doc_in(24):
        xem_lai.append(u"%d đối tượng có Mark KHÔNG theo tiền tố %s (không tag, đặt lại Mark rồi bấm lại): %s" % (
            len(sai_tt), u" / ".join(tach(doc_in(4)) + tach(doc_in(6))),
            u", ".join(u"%d (%s, Mark %s)" % (e.Id.Value, lop, mark(e)) for e, lop in sai_tt[:30])))

    def se_tag(e, lop):
        return bool(mark(e)) and (dung_tien_to(e, lop) or not doc_in(24))

    bic_tag = {BuiltInCategory.OST_StairsRailing: (doc_in(1), BuiltInCategory.OST_StairsRailingTags, DU_PHONG_LAN_CAN),
               BuiltInCategory.OST_Windows: (doc_in(2), BuiltInCategory.OST_WindowTags, DU_PHONG_LOUVER)}
    kieu = {}
    can = set(bic for e, lop, bic, _ in ds if se_tag(e, lop))
    for bic in can:
        ten_fam, cat_tag, du_phong = bic_tag.get(bic, (doc_in(3), BuiltInCategory.OST_MultiCategoryTags, DU_PHONG_DA))
        s = tim_kieu_tag(doc, ten_fam, cat_tag)
        if s is None and ten_fam != du_phong:
            bao_cao.append(u"Dự án chưa có family tag '%s' (%s) → dùng '%s'." % (
                ten_fam, Category.GetCategory(doc, cat_tag).Name, du_phong))
        if s is None:
            s = lay_kieu_tag(doc, du_phong, cat_tag, dry, bao_cao)
        if s is None and cat_tag != BuiltInCategory.OST_MultiCategoryTags:
            s = lay_kieu_tag(doc, DU_PHONG_DA, BuiltInCategory.OST_MultiCategoryTags, dry, bao_cao)
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
            xs_nha += [q[0] for q in poly]
            ys_nha += [q[1] for q in poly]
    tam_nha = ((min(xs_nha) + max(xs_nha)) / 2.0, (min(ys_nha) + max(ys_nha)) / 2.0) if xs_nha else None
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
    # Cửa đi / cửa sổ khác + lan can không nhận (cầu thang): vật cản theo khung bao trong view
    for bic in (BuiltInCategory.OST_Doors, BuiltInCategory.OST_Windows, BuiltInCategory.OST_StairsRailing,
                BuiltInCategory.OST_Stairs):
        for e in thay(bic):
            if e.Id.Value in dau_chan:
                continue
            k = khung_hop(e.get_BoundingBox(view))
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
            # Phía ưu tiên = phía NGOÀI nhà (xa tâm khung bao tường của view)
            uu_tien = 1
            if tam_nha is not None:
                du_, dv_ = gu0 - tam_nha[0], gv0 - tam_nha[1]
                uu_tien = 1 if du_ * f2[0] + dv_ * f2[1] >= 0 else -1
            mat = {1: max(f1, 0.0), -1: max(-f0, 0.0)}
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
            chi_tiet.append(u"%d Mark %s %s (%s): %s (%d ứng viên)%s" % (
                e.Id.Value, mk, lop, cach, nhan, len(ung_vien), u" – đặt lại tag cũ" if tg_cu is not None else u""))
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
                if any(s_.startswith(u"ĐÃ ĐẶT") for s_ in b_):
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
    if loai == LOP_LAN_CAN:
        f_2 = lay(BuiltInParameter.ELEM_TYPE_PARAM, BuiltInParameter.SYMBOL_NAME_PARAM)
        f_3 = lay(BuiltInParameter.CURVE_ELEM_LENGTH, BuiltInParameter.INSTANCE_LENGTH_PARAM)
        nhan = (u"Ký hiệu", u"Loại", u"Tổng chiều dài")
    else:
        f_2 = lay(BuiltInParameter.WINDOW_WIDTH, BuiltInParameter.GENERIC_WIDTH, BuiltInParameter.FAMILY_WIDTH_PARAM)
        f_3 = lay(BuiltInParameter.WINDOW_HEIGHT, BuiltInParameter.DOOR_HEIGHT, BuiltInParameter.GENERIC_HEIGHT,
                  BuiltInParameter.FAMILY_HEIGHT_PARAM)
        nhan = (u"Ký hiệu", u"Chiều rộng", u"Chiều cao")
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
    if loai == LOP_LAN_CAN and f_3 is not None:
        try:
            f_3.DisplayType = ScheduleFieldDisplayType.Totals
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
    try:
        d.ShowTitle = True
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
            si = ScheduleSheetInstance.Create(doc, sh.Id, vs.Id, XYZ(x0, y1, 0))
            bang.append((si, vs, cach))
            if len(dem) > 1:
                bao.append(u"Bảng %s chỉ thống kê hạng mục %s (còn %s)." % (nhan, Category.GetCategory(doc, bic).Name,
                           u", ".join(Category.GetCategory(doc, k).Name for k in dem if k != bic)))
        except Exception as ex:
            bao.append(u"Không tạo được bảng thống kê %s: %s" % (nhan, (u"%s" % ex).splitlines()[0][:150]))
    doc.Regenerate()
    y = y0
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


# ==== PHẦN CHUNG ĐẶT SHEET (chèn bằng gop_dat_sheet.py) ====
# ==== HẾT PHẦN CHUNG ĐẶT SHEET ====


try:
    OUT = _chinh()
except Exception:
    OUT = [u"LỖI:", traceback.format_exc()]
