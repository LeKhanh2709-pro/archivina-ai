# Triển khai chi tiết cửa (người dùng yêu cầu 2026-11-03, mẫu bản vẽ "CHI TIẾT CỬA" A.CD.22.13): chọn 1 cửa đi / cửa sổ
# có sẵn family → tạo mặt bằng, mặt đứng, mặt cắt tỉ lệ 1/25 rồi đặt vào ô trống tiếp theo của sheet "CHI TIẾT CỬA"
# (khung A1 chia 6 ô: 2 hàng × 3 cột). Ký hiệu, vật liệu, phụ kiện người dùng tự điền vào phần trống của ô.
#   - Mặt bằng: callout từ mặt bằng tầng của cửa (ưu tiên view đang mở nếu đúng tầng), khung nhìn = cửa + lề IN[5],
#     XOAY theo mặt đứng (người dùng yêu cầu 2026-11-03): phía phải mặt bằng = phía phải mặt đứng, ngoài nhà ở dưới;
#     khung callout trên mặt bằng gốc ẩn bằng Hide in View (IN[13]).
#   - Mặt đứng CHỈ CÓ CỬA (tường, sàn, phần tử khác Hide in View); level ẩn trên mặt đứng + mặt cắt, thay bằng nét
#     đứt cốt sàn + chữ "CỐT SÀN HOÀN THIỆN" có mũi tên trên mặt cắt (như mẫu người dùng gửi 2026-11-03).
#   - Mặt bằng chỉ hiện cửa + tường (sàn, cửa khác, đồ đạc Hide in View), khung nhìn trùm hết cung mở cánh.
#   - Kiểu view riêng: Floor Plan "CT CỬA", Section "MẶT CẮT CỬA" (mặt đứng + mặt cắt); viewport "AV-Title No Line".
#   - Mặt đứng: section đặt trước mặt tường, không cắt cửa, nhìn từ NGOÀI NHÀ. Phía ngoài nhà: một bên không có room
#     → bên đó; cả 2 bên có room thì bên có tên lô gia / ban công / sân; không rõ → phía KHÔNG mở cánh (theo cung mở
#     trên mặt bằng); cửa không có cung mở → mặt ngoài family (Facing). IN[11] ép phía nhìn.
#   - Mặt cắt: section vuông góc tường, cắt qua cánh cửa (cách tâm cửa 1/4 bề rộng), ngoài nhà nằm bên phải.
#     Ký hiệu section ẩn ở tỉ lệ thô hơn 1:<tỉ lệ> (mặt bằng 1/100 không thấy), mặt đứng / mặt cắt ẩn ký hiệu của nhau.
#   - View template: IN[6] – IN[8]; đã có thì dùng nguyên, KHÔNG sửa; chưa có thì tạo từ template nền (theo từ khoá
#     IN[9], không có thì template cùng tỉ lệ), tỉ lệ IN[4], Detail Level Fine, ẩn hạng mục IN[10], để view tự giữ
#     Far Clipping (template nền điều khiển Far Clipping thì mặt cắt thấy cả phòng phía sau).
#   - Kích thước tổng (IN[12]): mặt bằng = rộng; mặt đứng = rộng + cao (cửa sổ: cao độ bậu tính từ sàn + cao cửa);
#     mặt cắt = cao. Reference lấy từ family (Left / Right / Top / Bottom); family không có thì lấy mặt lỗ mở của tường
#     (mép, đỉnh, bậu); chân = nét cốt sàn.
#   - Sheet: tên IN[2]; chỉ dùng sheet do công cụ này tạo (có group lưới ô "ARV_ChiTietCua_Luoi ..."), KHÔNG đặt view
#     vào sheet người dùng tự làm dù trùng tên. Hết ô thì tạo sheet mới khung IN[1], số sheet = số lớn nhất của các
#     sheet tên IN[2] + 1 (chưa có sheet nào tên đó thì IN[3]). Lưới ô: Detail Line trên sheet (2 nét đứng, 1 nét ngang
#     chia vùng vẽ của khung tên + 1 nét ngăn dải thông tin dưới mỗi ô).
#   - Mỗi type cửa chỉ làm 1 lần: đã có view "CT CỬA <Type Mark> - MẶT ĐỨNG" thì báo và mở sheet chứa view đó.
#   - Nhiều cửa (người dùng yêu cầu 2026-11-03): chọn nhiều cửa rồi bấm → làm lần lượt, xếp tiếp các ô; nút pyRevit hỏi
#     giai đoạn / hạng mục / khổ giấy (khung tên) / số hiệu / tên bản vẽ trước khi chạy (lib\arv_hoi_sheet.py).
#   - Vách kính (curtain wall, người dùng yêu cầu 2026-11-03): chọn vách (hoặc tấm kính / đố / cửa của vách) → cùng 3
#     view, tên "CT VÁCH KÍNH <Mark> - ...", mỗi Mark 1 lần (không có Mark thì "VK <dài>x<cao>"). Mặt đứng giữ vách +
#     tấm + đố; dim chuỗi theo lưới đố + tổng (ngang, đứng); mặt cắt qua giữa ô cửa sổ (không có thì ô cửa đi, ô kính
#     gần giữa). Giữ tỉ lệ 1:IN[4] (người dùng chốt 2026-11-04); không lọt 1 ô thì chiếm khối 2 / 3 / 4 / 6 ô liền nhau
#     trên sheet mới, lưới bỏ nét chia trong khối, 1 dải thông tin dưới khối; ô còn lại của sheet dùng tiếp.
#   - Không xoá, không sửa cửa / tường / view gốc / template đã có.
# Giới hạn: cửa trong file link không chọn được; vách kính cong chưa làm.
# INPUT
#   IN[0]  (str)   ID cửa, nhiều id cách nhau bằng ; (trống = các cửa đang chọn; chưa chọn thì chọn trên màn hình)
#   IN[1]  (str)   Khung tên cho sheet mới (tên type title block)
#   IN[2]  (str)   Tên bản vẽ (tên sheet) chi tiết cửa
#   IN[3]  (str)   Số hiệu sheet: có thì xếp vào sheet đó (của công cụ, còn ô) rồi các sheet số lớn hơn, hết thì tạo
#                  sheet số đó / số tiếp theo; trống = số lớn nhất của các sheet tên IN[2] + 1 (chưa có thì A.CD.01)
#   IN[4]  (float) Tỉ lệ (25 = 1/25)
#   IN[5]  (float) Lề khung nhìn quanh cửa (mm)
#   IN[6]  (str)   Tên view template mặt bằng
#   IN[7]  (str)   Tên view template mặt đứng
#   IN[8]  (str)   Tên view template mặt cắt
#   IN[9]  (str)   Từ khoá template nền khi phải tạo template: mặt bằng;mặt đứng;mặt cắt (không dấu)
#   IN[10] (str)   Hạng mục ẩn trong template mới (tên BuiltInCategory, cách nhau bằng ;)
#   IN[11] (str)   Phía nhìn mặt đứng: trống = tự động; facing = mặt ngoài family; nguoc = ngược Facing
#   IN[12] (bool)  Đặt kích thước tổng
#   IN[13] (bool)  Ẩn khung callout trên mặt bằng gốc
#   IN[14] (bool)  Dry-run (True = chỉ báo cáo)
#   IN[15] (bool)  Mở sheet sau khi tạo
#   IN[16] (str)   Giai đoạn (thư mục cấp 1 của Project Browser) gán cho sheet mới; chỉ dùng sheet cùng giai đoạn
#   IN[17] (str)   Hạng mục (thư mục cấp 2) gán cho sheet mới; chỉ dùng sheet cùng hạng mục
# OUTPUT
#   OUT (list[str])  Báo cáo
import math
import re
import traceback
import unicodedata
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
clr.AddReference("RevitServices")
from Autodesk.Revit.DB import *
import Autodesk.Revit.DB as _RevitDB
# pythonnet 3.0: tên đã được import đích danh trước đó trong phiên bị loại khỏi "import *" → bổ sung đủ tên
globals().update({_n: getattr(_RevitDB, _n) for _n in dir(_RevitDB) if not _n.startswith("_") and _n not in globals()})
from Autodesk.Revit.UI.Selection import ObjectType
from System.Collections.Generic import List
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

TRANSACTION_NAME = u"ARV - Chi tiết cửa"
MAC_DINH = ["", u"AV-Khung A1(841x594)-Kien Truc", u"CHI TIẾT CỬA", u"A.CD.01", 25.0, 300.0,
            u"CHI TIẾT CỬA - MẶT BẰNG", u"CHI TIẾT CỬA - MẶT ĐỨNG", u"CHI TIẾT CỬA - MẶT CẮT",
            u"chi tiet mat bang;chi tiet mat dung;mat cat chi tiet",
            "OST_Furniture;OST_FurnitureSystems;OST_Casework;OST_SpecialityEquipment;OST_PlumbingFixtures;OST_Grids",
            u"", True, True, True, True, u"", u""]
NHOM_LUOI = u"ARV_ChiTietCua_Luoi"
# Cửa trong file link: không Hide in View từng phần tử link được → template riêng (tên + HAU_TO_LINK) ẩn cả hạng mục
HAU_TO_LINK = u" (LINK)"
AN_LINK_MD = ("OST_Walls", "OST_Floors", "OST_Ceilings", "OST_Roofs", "OST_Columns", "OST_StructuralColumns",
              "OST_StructuralFraming", "OST_StructuralFoundation", "OST_Stairs", "OST_StairsRailing", "OST_GenericModel",
              "OST_Furniture", "OST_Casework", "OST_PlumbingFixtures", "OST_SpecialityEquipment", "OST_MechanicalEquipment",
              "OST_Topography", "OST_Planting", "OST_Entourage", "OST_Site", "OST_Parking", "OST_Rooms")
AN_LINK_MB = ("OST_Floors", "OST_Ceilings", "OST_Roofs", "OST_StructuralFraming", "OST_Stairs", "OST_StairsRailing",
              "OST_GenericModel", "OST_Furniture", "OST_Casework", "OST_PlumbingFixtures", "OST_SpecialityEquipment",
              "OST_MechanicalEquipment", "OST_Rooms")
KIEU_VIEWPORT = u"AV-Title No Line"           # kiểu viewport đặt lên sheet (người dùng chốt 2026-11-03)
KIEU_MB = u"CT CỬA"                           # kiểu view riêng: Floor Plan (CT CỬA), Section (MẶT CẮT CỬA)
KIEU_MC = u"MẶT CẮT CỬA"
TIEN_TO = (u"CT CỬA", u"CT VÁCH KÍNH")       # tiền tố tên view chi tiết cửa / vách kính
KHOI_VK = ((1, 1), (2, 1), (3, 1), (2, 2), (3, 2))   # khối ô (cột × hàng) cho vách kính, ít ô trước
TEN_NGOAI = (u"logia", u"lo gia", u"ban cong", u"balcony", u"san phoi", u"san thuong", u"terrace", u"ngoai nha")
SO_COT, SO_HANG = 3, 2
TI_LE_DAI_TT = 0.22          # dải thông tin dưới mỗi ô (tỉ lệ chiều cao ô)
UP = XYZ.BasisZ


def doc_in(i):
    try:
        v = IN[i]
    except Exception:
        v = None
    return MAC_DINH[i] if v is None or (isinstance(v, str) and v == "" and MAC_DINH[i] != "") else v


def ft(x_mm):
    return UnitUtils.ConvertToInternalUnits(float(x_mm), UnitTypeId.Millimeters)


def mm(x_ft):
    return UnitUtils.ConvertFromInternalUnits(x_ft, UnitTypeId.Millimeters)


def khong_dau(s):
    s = unicodedata.normalize("NFD", u"%s" % (s or u"")).replace(u"đ", u"d").replace(u"Đ", u"D")
    return u"".join(c for c in s if unicodedata.category(c) != "Mn").lower().strip()


def tach(s):
    return [x.strip() for x in (s or "").split(";") if x.strip()]


def ten(e):
    """Tên phần tử; PythonNet3 không đọc được Element.Name của ElementType → đọc qua tham số."""
    if e is None:
        return u"-"
    try:
        n = e.Name
        if n:
            return n
    except Exception:
        pass
    for bip in (BuiltInParameter.SYMBOL_NAME_PARAM, BuiltInParameter.ALL_MODEL_TYPE_NAME):
        try:
            p = e.get_Parameter(bip)
            if p is not None and p.AsString():
                return p.AsString()
        except Exception:
            pass
    return u"?"


def ten_view_hop_le(s):
    return re.sub(u"[\\\\:{}\\[\\]|;<>?`~]", u"", s).strip()


def ten_cat(doc, cid):
    try:
        return Category.GetCategory(doc, cid).Name
    except Exception:
        return str(cid.Value)


# ---------------------------------------------------------------- hình học cửa / tường
def diem_hinh(geo, ds):
    """Gom điểm (đỉnh cạnh solid, điểm curve 3D) của GeometryElement vào ds."""
    for g in geo:
        tn = g.GetType().Name
        if tn == "GeometryInstance":
            diem_hinh(g.GetInstanceGeometry(), ds)
        elif tn == "Solid":
            if g.Volume <= 0:
                continue
            for c in g.Edges:
                ds.extend(list(c.Tessellate()))
        elif tn in ("Line", "Arc", "NurbSpline", "HermiteSpline", "Ellipse"):
            ds.extend(list(g.Tessellate()))


def cung_mo(geo, ds):
    """Cung (Arc) trên hình mặt bằng của cửa = cung mở cánh."""
    for g in geo:
        tn = g.GetType().Name
        if tn == "GeometryInstance":
            cung_mo(g.GetInstanceGeometry(), ds)
        elif tn == "Arc":
            ds.append(g)


# ==== PHẦN CHUNG FILE LINK (nguồn: Link_chung.py, chép vào công cụ bằng gop_link.py – không sửa tay trong công cụ) ====
# Model chỉ chứa link (vd. HQV Site: tường / cửa / WC đều nằm trong các file link): công cụ đọc đối tượng link qua LkPT, là
# lớp bọc trả toạ độ đã đổi về model chính và chuyển mọi thuộc tính khác cho phần tử gốc. Phần tử trong link chỉ ĐỌC được.
LK_HE_SO_ID = 10000000000      # id giả = id link instance × hệ số + id phần tử, không trùng giữa các link


def _lk_mm(v):
    return UnitUtils.ConvertToInternalUnits(v, UnitTypeId.Millimeters)


class LkId(object):
    """Id giả của phần tử link: có .Value như ElementId, dùng làm khoá và để in."""
    def __init__(self, v):
        self.Value = v

    def __eq__(self, o):
        return getattr(o, "Value", None) == self.Value

    def __ne__(self, o):
        return not self.__eq__(o)

    def __hash__(self):
        return hash(self.Value)

    def __str__(self):
        return "%d" % self.Value


class _LkViTri(object):
    """Location của phần tử link, đã đổi về toạ độ model chính."""
    def __init__(self, pt):
        self._pt = pt
        self._loc = pt._e.Location

    @property
    def Point(self):
        return self._pt._tf.OfPoint(self._loc.Point)

    @property
    def Curve(self):
        return self._loc.Curve.CreateTransformed(self._pt._tf)

    @property
    def Rotation(self):
        return self._loc.Rotation

    def get_ElementsAtJoin(self, i):
        return [LkPT(x, self._pt._li, self._pt._tf) for x in self._loc.get_ElementsAtJoin(i)]


class _LkDoanBien(object):
    """BoundarySegment của room link: GetCurve đã đổi toạ độ."""
    def __init__(self, sg, tf):
        self._sg, self._tf = sg, tf

    def GetCurve(self):
        return self._sg.GetCurve().CreateTransformed(self._tf)


class LkPT(object):
    """Phần tử trong file link nhìn như phần tử model chính (chỉ đọc). Thuộc tính không khai báo ở đây lấy từ phần tử gốc."""
    def __init__(self, e, li, tf=None):
        self._e = e
        self._li = li
        self._tf = tf if tf is not None else li.GetTotalTransform()

    def __getattr__(self, ten_tt):
        return getattr(self._e, ten_tt)

    @property
    def Id(self):
        return LkId(self._li.Id.Value * LK_HE_SO_ID + self._e.Id.Value)

    @property
    def Location(self):
        return _LkViTri(self) if self._e.Location is not None else None

    @property
    def HandOrientation(self):
        return self._tf.OfVector(self._e.HandOrientation)

    @property
    def FacingOrientation(self):
        return self._tf.OfVector(self._e.FacingOrientation)

    @property
    def Orientation(self):
        return self._tf.OfVector(self._e.Orientation)

    @property
    def Host(self):
        h = self._e.Host
        return LkPT(h, self._li, self._tf) if h is not None else None

    def GetPath(self):
        return [c.CreateTransformed(self._tf) for c in self._e.GetPath()]

    def get_BoundingBox(self, view=None):
        bb = self._e.get_BoundingBox(None)
        if bb is None:
            return None
        ds = [self._tf.OfPoint(XYZ(x, y, z)) for x in (bb.Min.X, bb.Max.X) for y in (bb.Min.Y, bb.Max.Y)
              for z in (bb.Min.Z, bb.Max.Z)]
        kq = BoundingBoxXYZ()
        kq.Min = XYZ(min(p.X for p in ds), min(p.Y for p in ds), min(p.Z for p in ds))
        kq.Max = XYZ(max(p.X for p in ds), max(p.Y for p in ds), max(p.Z for p in ds))
        return kq

    def get_Geometry(self, opt):
        """Hình học đã đổi toạ độ. Có view thì lấy theo mặt bằng cùng tầng trong file link (để có nét 2D: cánh mở, ký hiệu)."""
        o = Options()
        try:
            o.IncludeNonVisibleObjects = opt.IncludeNonVisibleObjects
            o.ComputeReferences = opt.ComputeReferences
        except Exception:
            pass
        vm = lk_view_tang(self._e, self._tf) if getattr(opt, "View", None) is not None else None
        if vm is not None:
            o.View = vm
        else:
            try:
                o.DetailLevel = opt.DetailLevel if getattr(opt, "View", None) is None else ViewDetailLevel.Fine
            except Exception:
                o.DetailLevel = ViewDetailLevel.Fine
        g = self._e.get_Geometry(o)
        if vm is not None and (g is None or not any(True for _ in g)):       # view trong link ẩn đối tượng → lấy hình 3D
            o2 = Options()
            o2.DetailLevel = ViewDetailLevel.Fine
            o2.ComputeReferences = o.ComputeReferences
            g = self._e.get_Geometry(o2)
        return g.GetTransformed(self._tf) if g is not None else None

    def GetBoundarySegments(self, opt):
        kq = self._e.GetBoundarySegments(opt)
        return [[_LkDoanBien(s, self._tf) for s in vong] for vong in kq] if kq is not None else None

    @property
    def GeometryCurve(self):
        return self._e.GeometryCurve.CreateTransformed(self._tf)

    def IsPointInRoom(self, p):
        return self._e.IsPointInRoom(self._tf.Inverse.OfPoint(p))

    def IsHidden(self, view):
        return False

    def CanBeHidden(self, view):
        return False


def la_link(e):
    return isinstance(e, LkPT)


def lk_tham_chieu(e):
    """Reference để tag / dim: phần tử link thì là link reference."""
    return Reference(e._e).CreateLinkReference(e._li) if la_link(e) else Reference(e)


def lk_cac_link(doc, view):
    """Các link đã nạp và đang thấy trong view: [(instance, document, transform)]."""
    kq = []
    for li in FilteredElementCollector(doc, view.Id).OfClass(RevitLinkInstance):
        try:
            ld = li.GetLinkDocument()
            if ld is not None:
                kq.append((li, ld, li.GetTotalTransform()))
        except Exception:
            pass
    return kq


def lk_level_khop(ld, tf, lv):
    """Id level của file link trùng cao độ với level lv của model chính (đã tính link đặt lệch cao độ, vd. tầng điển hình)."""
    return set(l.Id.Value for l in FilteredElementCollector(ld).OfClass(Level)
               if abs(l.Elevation + tf.Origin.Z - lv.Elevation) < _lk_mm(5))


_LK_VIEW = {}


def lk_view_tang(e, tf):
    """Mặt bằng trong file link cùng level của e (để đọc nét 2D của family); không có thì None."""
    ld = e.Document
    k = (ld.PathName or ld.Title, e.LevelId.Value)
    if k not in _LK_VIEW:
        ds = [v for v in FilteredElementCollector(ld).OfClass(ViewPlan)
              if not v.IsTemplate and v.ViewType == ViewType.FloorPlan and v.GenLevel is not None
              and v.GenLevel.Id == e.LevelId]
        ds.sort(key=lambda v: v.Id.Value)
        _LK_VIEW[k] = ds[0] if ds else None
    return _LK_VIEW[k]


def lk_tren_level(e, ids, tf=None, lv=None):
    """Phần tử e (trong link) thuộc các level ids? LevelId rỗng thì xét tham số level, host, cuối cùng theo cao độ."""
    if e.LevelId.Value in ids:
        return True
    if e.LevelId != ElementId.InvalidElementId:
        return False
    for bip in (BuiltInParameter.INSTANCE_SCHEDULE_ONLY_LEVEL_PARAM, BuiltInParameter.FAMILY_LEVEL_PARAM,
                BuiltInParameter.STAIRS_RAILING_BASE_LEVEL_PARAM):
        try:
            p = e.get_Parameter(bip)
            if p is not None and p.HasValue:
                return p.AsElementId().Value in ids
        except Exception:
            pass
    try:
        if e.Host is not None and e.Host.LevelId.Value in ids:
            return True
    except Exception:
        pass
    if tf is not None and lv is not None:
        bb = e.get_BoundingBox(None)
        if bb is not None:
            z = bb.Min.Z + tf.Origin.Z
            return lv.Elevation - _lk_mm(300) <= z <= lv.Elevation + _lk_mm(2000)
    return False


def lk_thay(doc, view, bic, theo_level=True):
    """Đối tượng hạng mục bic trong các link đang thấy trong view (đúng tầng của view khi theo_level) → list[LkPT]."""
    kq = []
    lv = view.GenLevel
    for li, ld, tf in lk_cac_link(doc, view):
        ids = lk_level_khop(ld, tf, lv) if theo_level and lv is not None else None
        if theo_level and not ids:
            continue
        for e in FilteredElementCollector(doc, view.Id, li.Id).OfCategory(bic).WhereElementIsNotElementType():
            if ids is None or lk_tren_level(e, ids, tf, lv):
                kq.append(LkPT(e, li, tf))
    return kq


def lk_tang(doc, view, bic):
    """Như lk_thay nhưng không lọc theo view (kể cả đối tượng view không vẽ, vd. room) – chỉ trong link đang thấy, đúng tầng."""
    kq = []
    lv = view.GenLevel
    for li, ld, tf in lk_cac_link(doc, view):
        ids = lk_level_khop(ld, tf, lv)
        if not ids:
            continue
        for e in FilteredElementCollector(ld).OfCategory(bic).WhereElementIsNotElementType():
            if lk_tren_level(e, ids, tf, lv):
                kq.append(LkPT(e, li, tf))
    return kq


def lk_room_tai_diem(doc, view, p):
    """Room trong link tại điểm p (toạ độ model chính) → LkPT hoặc None."""
    for li, ld, tf in lk_cac_link(doc, view):
        try:
            r = ld.GetRoomAtPoint(tf.Inverse.OfPoint(p))
        except Exception:
            r = None
        if r is not None:
            return LkPT(r, li, tf)
    return None


def lk_room_moi_link(doc, p):
    """Room trong bất kỳ link đã nạp tại điểm p (toạ độ model chính) → LkPT hoặc None (không cần view)."""
    for li in FilteredElementCollector(doc).OfClass(RevitLinkInstance):
        try:
            ld = li.GetLinkDocument()
            if ld is None:
                continue
            tf = li.GetTotalTransform()
            r = ld.GetRoomAtPoint(tf.Inverse.OfPoint(p))
        except Exception:
            r = None
        if r is not None:
            return LkPT(r, li, tf)
    return None


def lk_level_host(doc, e):
    """Level của model chính cùng cao độ với level của phần tử link e (đã tính Z của instance); không có thì None."""
    try:
        z = e.Document.GetElement(e.LevelId).Elevation + e._tf.Origin.Z
    except Exception:
        return None
    ds = [l for l in FilteredElementCollector(doc).OfClass(Level) if abs(l.Elevation - z) < _lk_mm(5)]
    return ds[0] if ds else None


def lk_tu_id(doc, v):
    """Id giả (id link instance × hệ số + id phần tử) → LkPT; id thường → phần tử model chính."""
    v = int(v)
    if v < LK_HE_SO_ID:
        return doc.GetElement(ElementId(v))
    li = doc.GetElement(ElementId(v // LK_HE_SO_ID))
    ld = li.GetLinkDocument() if li is not None else None
    e = ld.GetElement(ElementId(v % LK_HE_SO_ID)) if ld is not None else None
    return LkPT(e, li) if e is not None else None


class LkMat(object):
    """PlanarFace của phần tử link: pháp tuyến / điểm đã đổi toạ độ, Reference là link reference (dùng để dim)."""
    def __init__(self, f, tf, li, ref=None):
        self._f, self._tf = f, tf
        self.Reference = ref if ref is not None else f.Reference.CreateLinkReference(li)
        self.FaceNormal = tf.OfVector(f.FaceNormal)
        self.Origin = tf.OfPoint(f.Origin)

    def GetBoundingBox(self):
        return self._f.GetBoundingBox()

    def Evaluate(self, uv):
        return self._tf.OfPoint(self._f.Evaluate(uv))

    def Project(self, p):
        return self._f.Project(self._tf.Inverse.OfPoint(p))

    def GetType(self):
        return self._f.GetType()


def lk_mat_phang(e, opt):
    """Các PlanarFace (có reference) của phần tử link e dạng LkMat; hình học lấy trong file link rồi đổi toạ độ."""
    kq = []

    def duyet(geo, tf):
        for g in geo:
            tn = g.GetType().Name
            if tn == "GeometryInstance":
                duyet(g.GetInstanceGeometry(), tf)
            elif tn == "Solid" and g.Volume > 0:
                for f in g.Faces:
                    if f.GetType().Name == "PlanarFace" and f.Reference is not None:
                        try:
                            kq.append(LkMat(f, tf, e._li))
                        except Exception:
                            pass
    geo = e._e.get_Geometry(opt)
    if geo is not None:
        duyet(geo, e._tf)
    return kq


def lk_khoa_tag(tg):
    """Khoá các đối tượng mà tag đang gắn (phần tử model chính: id; phần tử link: id giả như LkPT.Id)."""
    kq = []
    for x in tg.GetTaggedElementIds():
        if x.LinkInstanceId != ElementId.InvalidElementId:
            kq.append(x.LinkInstanceId.Value * LK_HE_SO_ID + x.LinkedElementId.Value)
        else:
            kq.append(x.HostElementId.Value)
    return kq


def lk_ghi_chu(doc, view):
    """Một dòng báo cáo: các link đang thấy trong view + số link khớp tầng."""
    ds = lk_cac_link(doc, view)
    lv = view.GenLevel
    khop = [li.Name.split(" : ")[0] for li, ld, tf in ds if lv is not None and lk_level_khop(ld, tf, lv)]
    return "File link thấy trong view: %d, khớp tầng: %s" % (len(ds), ", ".join(sorted(set(khop))) or "(không)")
def lk_bang_ve(doc, ten_view, tieu_de, cot, rong_cot, dong):
    """Bảng vẽ trên drafting view tỉ lệ 1:1: Revit không lọc được bảng thống kê theo tầng khi lấy cả file link (Level của
    link không dùng được làm bộ lọc; thêm link thì đếm mọi tầng của mọi bản link). cot: tên cột; rong_cot: mm giấy; dong:
    list[list[chuỗi]]. Đã có view tên đó thì chỉ sửa chữ khi đúng số dòng, không xoá gì. Gọi TRONG transaction.
    Trả về (view, cách làm)."""
    cao_dong, cao_dau = _lk_mm(8), _lk_mm(10)
    so_cot = len(cot)
    ds = [v for v in FilteredElementCollector(doc).OfClass(ViewDrafting) if not v.IsTemplate and v.Name == ten_view]
    if ds:
        v = ds[0]
        notes = sorted(FilteredElementCollector(doc, v.Id).OfClass(TextNote), key=lambda n: (-round(n.Coord.Y, 2), n.Coord.X))
        cu = [n for n in notes if round(n.Coord.Y, 2) < 0]             # ô dữ liệu nằm dưới tiêu đề + đầu cột
        ky_vong = sum(1 for d in dong for x in d if x != u"")
        if len(cu) != ky_vong:
            return v, u"bảng '%s' đã có nhưng khác số ô (%d, cần %d) – CHƯA cập nhật, xoá view đó rồi bấm lại" % (ten_view, len(cu), ky_vong)
        phang = [x for d in dong for x in d if x != u""]
        for n, x in zip(cu, phang):
            if n.Text != x:
                n.Text = x
        return v, u"cập nhật chữ bảng đã có"
    vft = [t for t in FilteredElementCollector(doc).OfClass(ViewFamilyType) if t.ViewFamily == ViewFamily.Drafting][0]
    v = ViewDrafting.Create(doc, vft.Id)
    v.Name = ten_view
    v.Scale = 1
    kieu = sorted(FilteredElementCollector(doc).OfClass(TextNoteType), key=lambda t: t.Id.Value)
    def diem_kieu(t):
        ten_k = (t.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() or u"").lower()
        co = t.get_Parameter(BuiltInParameter.TEXT_SIZE).AsDouble()
        return (0 if u"arial" in ten_k else 1, abs(co - _lk_mm(2.5)))
    kt = min(kieu, key=diem_kieu)
    tong = sum(_lk_mm(x) for x in rong_cot)
    tao_chu = lambda x_, y_, s_: TextNote.Create(doc, v.Id, XYZ(x_, y_, 0), s_, kt.Id)
    tao_net = lambda a_, b_: doc.Create.NewDetailCurve(v, Line.CreateBound(a_, b_))
    tao_chu(_lk_mm(2), cao_dau * 1.5, tieu_de)
    xs = [0.0]
    for r_ in rong_cot:
        xs.append(xs[-1] + _lk_mm(r_))
    y_tren = cao_dau
    y_day = -cao_dong * len(dong)
    for i_ in range(len(dong) + 2):
        y_ = cao_dau if i_ == 0 else -cao_dong * (i_ - 1)
        tao_net(XYZ(0, y_, 0), XYZ(tong, y_, 0))
    for x_ in xs:
        tao_net(XYZ(x_, y_tren, 0), XYZ(x_, y_day, 0))
    for c_ in range(so_cot):
        tao_chu(xs[c_] + _lk_mm(2), cao_dau - _lk_mm(3), cot[c_])
    for r_i, d in enumerate(dong):
        for c_ in range(so_cot):
            if d[c_] != u"":
                tao_chu(xs[c_] + _lk_mm(2), -cao_dong * r_i - _lk_mm(2), d[c_])
    return v, u"bảng vẽ mới (drafting view)"


class LkBangTrenSheet(object):
    """Viewport của bảng vẽ, dùng được như ScheduleSheetInstance khi xếp bảng lên sheet (Point = góc trên trái)."""
    def __init__(self, vp):
        self._vp = vp

    def get_BoundingBox(self, v=None):
        o = self._vp.GetBoxOutline()
        bb = BoundingBoxXYZ()
        bb.Min, bb.Max = o.MinimumPoint, o.MaximumPoint
        return bb

    @property
    def Point(self):
        o = self._vp.GetBoxOutline()
        return XYZ(o.MinimumPoint.X, o.MaximumPoint.Y, 0)

    @Point.setter
    def Point(self, p):
        o = self._vp.GetBoxOutline()
        w, h = o.MaximumPoint.X - o.MinimumPoint.X, o.MaximumPoint.Y - o.MinimumPoint.Y
        self._vp.SetBoxCenter(XYZ(p.X + w / 2.0, p.Y - h / 2.0, 0))


def lk_kich_thuoc(e):
    """(chiều dài / rộng, chiều cao) mm dạng chuỗi của cửa, lan can, louver (model chính hoặc link), dùng cho bảng vẽ."""
    def mm_(p):
        return u"%d" % round(UnitUtils.ConvertFromInternalUnits(p.AsDouble(), UnitTypeId.Millimeters))

    def tim(bips, nguon):
        for b in bips:
            for o in nguon:
                p = o.get_Parameter(b) if o is not None else None
                if p is not None and p.HasValue and p.StorageType == StorageType.Double and p.AsDouble() > 0:
                    return mm_(p)
        return u""
    t = e.Document.GetElement(e.GetTypeId())
    dai = tim((BuiltInParameter.CURVE_ELEM_LENGTH, BuiltInParameter.INSTANCE_LENGTH_PARAM, BuiltInParameter.DOOR_WIDTH,
               BuiltInParameter.WINDOW_WIDTH, BuiltInParameter.GENERIC_WIDTH, BuiltInParameter.FAMILY_WIDTH_PARAM), (e, t))
    cao = tim((BuiltInParameter.DOOR_HEIGHT, BuiltInParameter.WINDOW_HEIGHT, BuiltInParameter.GENERIC_HEIGHT,
               BuiltInParameter.FAMILY_HEIGHT_PARAM), (e, t))
    if not cao and t is not None:
        p = t.LookupParameter("Railing Height")
        if p is not None and p.HasValue:
            cao = mm_(p)
    return dai, cao


def lk_dat_bang_len_sheet(doc, sh, vs, x0, y1):
    """Đặt drafting view bảng lên sheet (view đã nằm trên sheet khác thì nêu lỗi). Trả về LkBangTrenSheet."""
    if not Viewport.CanAddViewToSheet(doc, sh.Id, vs.Id):
        raise Exception(u"bảng '%s' đã nằm trên sheet khác" % vs.Name)
    vp = Viewport.Create(doc, sh.Id, vs.Id, XYZ(x0, y1, 0))
    for t in FilteredElementCollector(doc).OfClass(ElementType):
        if t.GetType().Name == "ElementType" and t.Category is None and (t.FamilyName or u"") == u"Viewport" and u"No Line" in (t.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() or u""):
            vp.ChangeTypeId(t.Id)
            break
    return LkBangTrenSheet(vp)
# ==== HẾT PHẦN CHUNG FILE LINK ====


def mat_tuong(wall):
    """Các PlanarFace của tường (có reference để dim)."""
    opt = Options()
    opt.ComputeReferences = True
    opt.DetailLevel = ViewDetailLevel.Fine
    ds = []
    if la_link(wall):
        try:
            return lk_mat_phang(wall, opt)
        except Exception:
            return []

    def duyet(geo):
        for g in geo:
            tn = g.GetType().Name
            if tn == "GeometryInstance":
                duyet(g.GetInstanceGeometry())
            elif tn == "Solid" and g.Volume > 0:
                for f in g.Faces:
                    if f.GetType().Name == "PlanarFace" and f.Reference is not None:
                        ds.append(f)
    try:
        duyet(wall.get_Geometry(opt))
    except Exception:
        pass
    return ds


def tam_mat(f):
    bb = f.GetBoundingBox()
    return f.Evaluate((bb.Min + bb.Max) * 0.5)


def ref_family(fi, loai):
    try:
        ds = list(fi.GetReferences(getattr(FamilyInstanceReferenceType, loai)))
        if ds and la_link(fi):
            return ds[0].CreateLinkReference(fi._li)
        return ds[0] if ds else None
    except Exception:
        return None


# ---------------------------------------------------------------- sheet
NET_KHUNG = {}       # id family khung tên → danh sách nét (toạ độ family), đọc 1 lần mỗi lần chạy


def doc_net_khung(doc, tb_type, bao):
    """Nét thẳng trong family khung tên (Revit không trả hình học của khung tên trên sheet → mở family trong bộ nhớ,
    đọc, đóng không lưu). Phải gọi khi chưa mở transaction."""
    fam = tb_type.Family
    k = fam.Id.Value
    if k in NET_KHUNG:
        return NET_KHUNG[k]
    ds = []
    try:
        TransactionManager.Instance.ForceCloseTransaction()
        fdoc = doc.EditFamily(fam)
        try:
            for ce in FilteredElementCollector(fdoc).OfClass(CurveElement):
                c = ce.GeometryCurve
                if c is not None and c.GetType().Name == "Line":
                    ds.append((c.GetEndPoint(0), c.GetEndPoint(1)))
        finally:
            fdoc.Close(False)
    except Exception as ex:
        bao(u"   Không đọc được nét family khung tên (%s) → dùng lề mặc định." % ex)
    NET_KHUNG[k] = ds
    return ds


def vung_ve(doc, sheet, tb, bao):
    """Vùng vẽ của khung tên (feet, toạ độ sheet): (trái, dưới, phải, trên). Dò nét viền trong + mép trái dải khung tên."""
    bb = tb.get_BoundingBox(sheet)
    x0, y0, x1, y1 = bb.Min.X, bb.Min.Y, bb.Max.X, bb.Max.Y
    W, H = x1 - x0, y1 - y0
    tr = tb.GetTransform()
    doc_x, doc_y = {}, {}          # cộng dồn chiều dài nét đứng / ngang cùng toạ độ (nét viền có thể bị chia đoạn)
    for a, b in NET_KHUNG.get(doc.GetElement(tb.GetTypeId()).Family.Id.Value, []):
        a, b = tr.OfPoint(a), tr.OfPoint(b)
        if abs(a.X - b.X) < 1e-4:
            k = round(mm(a.X), 0)
            doc_x[k] = doc_x.get(k, 0) + abs(a.Y - b.Y)
        elif abs(a.Y - b.Y) < 1e-4:
            k = round(mm(a.Y), 0)
            doc_y[k] = doc_y.get(k, 0) + abs(a.X - b.X)
    xs = [ft(k) for k, d in doc_x.items() if d > 0.7 * H]
    ys = [ft(k) for k, d in doc_y.items() if d > 0.5 * W]
    # Mặc định theo khung AV-Khung A1 (viền trong cách mép ~35 / 16 mm, dải khung tên bên phải rộng ~110 mm)
    trai = max([x for x in xs if x0 - 1e-3 <= x <= x0 + 0.15 * W] or [x0 + ft(35)])
    # mép phải vùng vẽ = nét đứng dài trái nhất ở nửa phải (mép trái dải khung tên; không có dải thì là viền trong)
    phai = min([x for x in xs if x0 + 0.6 * W <= x <= x1 - ft(5)] or [x1 - ft(110)])
    duoi = max([y for y in ys if y0 - 1e-3 <= y <= y0 + 0.15 * H] or [y0 + ft(16)])
    tren = min([y for y in ys if y1 - 0.15 * H <= y <= y1 + 1e-3] or [y1 - ft(17)])
    return trai, duoi, phai, tren


def mat_san(doc, q, z_tren):
    """Reference mặt trên sàn cao nhất dưới điểm q (x, y) có cao độ ≤ z_tren. Trả về (reference, z) / (None, None)."""
    ol = Outline(XYZ(q.X - ft(10), q.Y - ft(10), z_tren - ft(1500)), XYZ(q.X + ft(10), q.Y + ft(10), z_tren + ft(10)))
    opt = Options()
    opt.ComputeReferences = True
    tot = (None, None)
    for fl in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Floors).WhereElementIsNotElementType() \
            .WherePasses(BoundingBoxIntersectsFilter(ol)):
        ds = []

        def duyet(geo):
            for g in geo:
                tn = g.GetType().Name
                if tn == "GeometryInstance":
                    duyet(g.GetInstanceGeometry())
                elif tn == "Solid" and g.Volume > 0:
                    for f in g.Faces:
                        if f.GetType().Name == "PlanarFace" and f.FaceNormal.Z > 0.99 and f.Reference is not None:
                            ds.append(f)
        try:
            duyet(fl.get_Geometry(opt))
        except Exception:
            continue
        for f in ds:
            z = f.Origin.Z
            if z > z_tren + ft(5) or (tot[1] is not None and z <= tot[1]):
                continue
            kq = f.Project(XYZ(q.X, q.Y, z))
            if kq is not None and kq.Distance < ft(1):
                tot = (f.Reference, z)
    # sàn trong file link (model chỉ chứa link): chỉ cần cao độ mặt sàn
    for li in FilteredElementCollector(doc).OfClass(RevitLinkInstance):
        ld = li.GetLinkDocument()
        if ld is None:
            continue
        tf = li.GetTotalTransform()
        a, b = tf.Inverse.OfPoint(ol.MinimumPoint), tf.Inverse.OfPoint(ol.MaximumPoint)
        ol_l = Outline(XYZ(min(a.X, b.X), min(a.Y, b.Y), min(a.Z, b.Z)), XYZ(max(a.X, b.X), max(a.Y, b.Y), max(a.Z, b.Z)))
        for fl in FilteredElementCollector(ld).OfCategory(BuiltInCategory.OST_Floors).WhereElementIsNotElementType() \
                .WherePasses(BoundingBoxIntersectsFilter(ol_l)):
            try:
                mats = lk_mat_phang(LkPT(fl, li, tf), opt)
            except Exception:
                continue
            for f in mats:
                if f.FaceNormal.Z < 0.99:
                    continue
                z = f.Origin.Z
                if z > z_tren + ft(5) or (tot[1] is not None and z <= tot[1]):
                    continue
                kq = f.Project(XYZ(q.X, q.Y, z))
                if kq is not None and kq.Distance < ft(1):
                    tot = (f.Reference, z)
    return tot


def o_luoi(vung, k):
    trai, duoi, phai, tren = vung
    w, h = (phai - trai) / SO_COT, (tren - duoi) / SO_HANG
    hang, cot = k // SO_COT, k % SO_COT
    x0 = trai + cot * w
    y1 = tren - hang * h
    return x0, y1 - h, x0 + w, y1


def o_trong(doc, sheet, vung, vps):
    """Các ô còn trống của sheet công cụ (thứ tự ô): ô có nét dải thông tin RIÊNG trong group lưới (ô thuộc khối ghép
    của vách kính không có) và không viewport nào lấn vào ô quá 10 mm (hộp viewport mặt đứng tính cả hộp bao ký hiệu
    mặt cắt, vượt phần thấy ~8 mm)."""
    nets = []
    for g in FilteredElementCollector(doc, sheet.Id).OfClass(Group):
        if not ten(g.GroupType).startswith(NHOM_LUOI):
            continue
        for i in g.GetMemberIds():
            try:
                c = doc.GetElement(i).GeometryCurve
            except Exception:
                c = None
            if c is not None and c.GetType().Name == "Line":
                nets.append((c.GetEndPoint(0), c.GetEndPoint(1)))
    hops = [vp.GetBoxOutline() for vp in vps]
    tl = ft(1)
    kq = []
    for k in range(SO_COT * SO_HANG):
        x0, y0, x1, y1 = o_luoi(vung, k)
        y = y0 + (y1 - y0) * TI_LE_DAI_TT
        if not any(abs(a.Y - y) < tl and abs(b.Y - y) < tl and abs(min(a.X, b.X) - x0) < tl
                   and abs(max(a.X, b.X) - x1) < tl for a, b in nets):
            continue
        if any(min(o.MaximumPoint.X, x1) - max(o.MinimumPoint.X, x0) > ft(10)
               and min(o.MaximumPoint.Y, y1) - max(o.MinimumPoint.Y, y0) > ft(10) for o in hops):
            continue
        kq.append(k)
    return kq


def tang_so(s):
    m = re.search(u"(\\d+)(\\D*)$", s)
    if not m:
        return s + u"-1"
    n = m.group(1)
    return s[:m.start(1)] + str(int(n) + 1).zfill(len(n)) + m.group(2)


def khoa_so(s):
    return [int(t) if t.isdigit() else t for t in re.split(u"(\\d+)", s)]


def tach_so(s):
    """(phần chữ đầu, số cuối) của số hiệu sheet; không có số cuối thì (s, None)."""
    m = re.search(u"(\\d+)(\\D*)$", s or u"")
    return (s[:m.start(1)], int(m.group(1))) if m else (s, None)


def doc_tho(i):
    """Đầu vào dạng chuỗi, trống thì trả chuỗi trống (không thay bằng mặc định)."""
    try:
        v = IN[i]
    except Exception:
        v = None
    return (u"%s" % v).strip() if v is not None else u""


def tim_khung(doc, tb_ten):
    """Type khung tên theo tên "Family : Type" / tên type / tên family; không có thì khung có chữ A1."""
    tbs = list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsElementType())
    for t in tbs:
        if tb_ten and tb_ten in (ten(t), u"%s : %s" % (t.FamilyName, ten(t)), t.FamilyName):
            return t, True
    a1 = [t for t in tbs if u"a1" in khong_dau(t.FamilyName + ten(t))]
    return ((a1 or tbs)[0] if tbs else None), False


# Nhóm sheet theo Project Browser: chép từ TagCua_TuDong.py (cap_thu_muc_sheet / ts_giai_doan) và
# lib\arv_hoi_sheet.py – sửa quy tắc ở một chỗ thì sửa cả các chỗ kia.
def cap_thu_muc_sheet(doc):
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


def ts_theo_id(e, pid):
    for prm in e.Parameters:
        if prm.Id.Value == pid.Value:
            return prm
    return None


def gia_tri_chuoi(prm):
    try:
        return (prm.AsString() or u"") if prm.StorageType == StorageType.String else (prm.AsValueString() or u"")
    except Exception:
        return u""


def ts_giai_doan(doc):
    """(id tham số giai đoạn, id tham số hạng mục). Browser 2 cấp: cấp 1 = giai đoạn, cấp 2 = hạng mục. 1 cấp: cấp đó là
    hạng mục, giai đoạn = tham số sheet có chữ "giai đoạn" dùng nhiều nhất."""
    cap = cap_thu_muc_sheet(doc)
    if len(cap) >= 2:
        return cap[0], cap[1]
    hm = cap[0] if cap else None
    dem = {}
    for s in FilteredElementCollector(doc).OfClass(ViewSheet):
        for prm in s.Parameters:
            if prm.Definition is not None and prm.StorageType == StorageType.String and \
                    u"giai doan" in khong_dau(prm.Definition.Name) and (hm is None or prm.Id.Value != hm.Value):
                k = prm.Id.Value
                dem.setdefault(k, [prm.Id, 0])
                if prm.AsString():
                    dem[k][1] += 1
    gd = max(dem.values(), key=lambda x: x[1])[0] if dem else None
    return gd, hm


# ---------------------------------------------------------------- template
def lay_template(doc, view, ten_tpl, tu_khoa, ti_le, an_cat, p, ghi, an_ep=()):
    """Template tên ten_tpl (đã có thì dùng nguyên). Chưa có: tạo từ template nền rồi chỉnh. Trả về template / None."""
    tpls = [v for v in FilteredElementCollector(doc).OfClass(View) if v.IsTemplate]
    for t in tpls:
        if t.Name == ten_tpl:
            if view is not None and not view.IsValidViewTemplate(t.Id):
                p(u"   Template '%s' đã có nhưng không dùng được cho view này → bỏ qua." % ten_tpl)
                return None
            return t
    ung = [t for t in tpls if (view is None or view.IsValidViewTemplate(t.Id))
           and (ten_tpl.endswith(HAU_TO_LINK) or not t.Name.endswith(HAU_TO_LINK))]
    tk = khong_dau(tu_khoa)

    def hang(t):
        n = khong_dau(t.Name)
        return (0 if tk and tk in n else 1, 0 if t.Scale == ti_le else 1, 0 if u"chi tiet" in n else 1, len(n))
    ung.sort(key=hang)
    nen = ung[0] if ung and (ung[0].Scale == ti_le or (tk and tk in khong_dau(ung[0].Name))) else None
    if not ghi:
        p(u"   Sẽ tạo template '%s' từ template nền '%s'." % (ten_tpl, nen.Name if nen is not None else u"(không có, theo view)"))
        return None
    view.ViewTemplateId = nen.Id if nen is not None else ElementId.InvalidElementId
    doc.Regenerate()            # template chỉ áp vào view khi regenerate
    tpl = view.CreateViewTemplate()
    tpl.Name = ten_tpl
    # Template phải điều khiển V/G model để ẩn được hạng mục; Far Clipping / Crop để view tự giữ
    try:
        bo = set([ElementId(BuiltInParameter.VIEWER_BOUND_FAR_CLIPPING).Value,
                  ElementId(BuiltInParameter.VIEWER_BOUND_OFFSET_FAR).Value,
                  ElementId(BuiltInParameter.VIEWER_CROP_REGION).Value,
                  ElementId(BuiltInParameter.VIEWER_CROP_REGION_VISIBLE).Value])
        vg = ElementId(BuiltInParameter.VIS_GRAPHICS_MODEL).Value
        ds = List[ElementId]()
        for i in tpl.GetNonControlledTemplateParameterIds():
            if i.Value != vg:
                ds.Add(i)
        co = set(i.Value for i in ds)
        for i in tpl.GetTemplateParameterIds():
            if i.Value in bo and i.Value not in co:
                ds.Add(i)
        tpl.SetNonControlledTemplateParameterIds(ds)
    except Exception as ex:
        p(u"   Không chỉnh được tham số điều khiển của template: %s" % ex)
    try:
        tpl.Scale = ti_le
    except Exception:
        pass
    try:
        tpl.DetailLevel = ViewDetailLevel.Fine
    except Exception:
        pass
    an = []
    for n in an_cat:
        try:
            c = ElementId(getattr(BuiltInCategory, n))
            if tpl.CanCategoryBeHidden(c):
                if not tpl.GetCategoryHidden(c):
                    tpl.SetCategoryHidden(c, True)
                an.append(ten_cat(doc, c))
        except Exception:
            pass
    for bic in (BuiltInCategory.OST_Doors, BuiltInCategory.OST_Windows, BuiltInCategory.OST_Walls,
                BuiltInCategory.OST_CurtainWallPanels, BuiltInCategory.OST_CurtainWallMullions):
        try:
            if ("%s" % bic) in an_ep:
                continue
            if tpl.GetCategoryHidden(ElementId(bic)):
                tpl.SetCategoryHidden(ElementId(bic), False)
        except Exception:
            pass
    for n in an_ep:           # template cho cửa trong link: ẩn cả hạng mục (kể cả tường ở mặt đứng)
        try:
            c = ElementId(getattr(BuiltInCategory, n))
            if tpl.CanCategoryBeHidden(c) and not tpl.GetCategoryHidden(c):
                tpl.SetCategoryHidden(c, True)
                an.append(ten_cat(doc, c))
        except Exception:
            pass
    p(u"   Tạo template '%s' từ '%s' (1:%d, Fine, ẩn: %s)." % (ten_tpl, nen.Name if nen is not None else u"view",
                                                             ti_le, u", ".join(an) or u"-"))
    return tpl


def an_ky_hieu(doc, view, ten_views, crop_ids=()):
    """Hide in View các ký hiệu view (section / callout) có tên trong ten_views và khung callout (phần tử crop hạng mục
    "Views") có id trong crop_ids. Trả về số đã ẩn."""
    ds = List[ElementId]()
    for e in FilteredElementCollector(doc, view.Id).WhereElementIsNotElementType():
        if e.Id.Value in crop_ids:
            try:
                if e.CanBeHidden(view):
                    ds.Add(e.Id)
            except Exception:
                pass
            continue
        if e.Category is None or e.Category.Id.Value != int(BuiltInCategory.OST_Viewers):
            continue
        n = ten(e)
        try:
            pn = e.get_Parameter(BuiltInParameter.VIEW_NAME)
            if pn is not None and pn.AsString():
                n = pn.AsString()
        except Exception:
            pass
        if n in ten_views and e.CanBeHidden(view):
            ds.Add(e.Id)
    if ds.Count:
        view.HideElements(ds)
    return ds.Count


def phan_tu_crop(doc, view):
    """Phần tử khung crop của view (để xoay mặt bằng): phần tử có ID_PARAM = id view (ngoài chính view đó). Revit
    2027.3: callout mặt bằng có crop id = id view - 1, hạng mục "Views" (KHÔNG phải OST_CropBoundary).
    Dự phòng: id view - 1 thuộc OST_CropBoundary, rồi tìm theo tên view."""
    cb = int(BuiltInCategory.OST_CropBoundary)
    try:
        luat = ParameterFilterRuleFactory.CreateEqualsRule(ElementId(BuiltInParameter.ID_PARAM), view.Id)
        for e in FilteredElementCollector(doc).WherePasses(ElementParameterFilter(luat)):
            if e.Id.Value != view.Id.Value and not e.GetType().Name.startswith(u"View"):
                return e
    except Exception:
        pass
    try:
        e = doc.GetElement(ElementId(view.Id.Value - 1))
        if e is not None and e.Category is not None and e.Category.Id.Value == cb:
            return e
    except Exception:
        pass
    for e in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CropBoundary).WhereElementIsNotElementType():
        try:
            pn = e.get_Parameter(BuiltInParameter.VIEW_NAME)
            if pn is not None and pn.AsString() == view.Name:
                return e
        except Exception:
            pass
    return None


def kieu_net_dut(doc):
    """Line style nét đứt cho nét cốt sàn: ưu tiên tên có 'khuất' / 'đứt', rồi '<Hidden>' / 'hidden' / 'dash'."""
    cat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Lines)
    tot = None
    for sc in cat.SubCategories:
        n = khong_dau(sc.Name)
        hang = 0 if (u"khuat" in n or u"net dut" in n) else 1 if n == u"<hidden>" else 2 if (u"hidden" in n or u"dash" in n) else 9
        if hang < 9 and (tot is None or hang < tot[0]):
            gs = sc.GetGraphicsStyle(GraphicsStyleType.Projection)
            if gs is not None:
                tot = (hang, gs)
    return tot[1] if tot else None


def chieu_cao_chu(doc, loai):
    """Chiều cao chữ (feet giấy) của TextNoteType."""
    try:
        return loai.get_Parameter(BuiltInParameter.TEXT_SIZE).AsDouble()
    except Exception:
        return ft(2.5)


def mat_hinh_cua(doc, fi, view=None):
    """Mặt phẳng trong hình family của cửa: [(pháp tuyến, tâm mặt, reference)] theo toạ độ dự án. Reference của hình
    symbol đổi sang reference của instance qua chuỗi ổn định '<UniqueId>:0:INSTANCE:<ref symbol>' để dim trên view
    (mặt đứng ẩn tường nên không dim vào mặt lỗ tường được). view: lấy hình theo view (view cắt qua phần tử: reference
    hình 3D không dùng được, Revit xoá dim)."""
    opt = Options()
    opt.ComputeReferences = True
    if view is not None:
        opt.View = view
    else:
        opt.DetailLevel = ViewDetailLevel.Fine
    ds = []
    lk = la_link(fi)                 # cửa trong file link: hình 3D trong file link, reference đổi sang link reference
    d_ref = fi.Document if lk else doc
    goc_fi = fi._e if lk else fi
    tf_lk = fi._tf if lk else Transform.Identity
    if lk:
        opt = Options()
        opt.ComputeReferences = True
        opt.DetailLevel = ViewDetailLevel.Fine

    def them(solid, tr, doi):
        if solid.GetType().Name != "Solid" or solid.Volume <= 0:
            return
        tr = tf_lk.Multiply(tr)
        for f in solid.Faces:
            if f.GetType().Name != "PlanarFace" or f.Reference is None:
                continue
            r = f.Reference
            if doi:
                try:
                    r = Reference.ParseFromStableRepresentation(
                        d_ref, u"%s:0:INSTANCE:%s" % (goc_fi.UniqueId, f.Reference.ConvertToStableRepresentation(d_ref)))
                except Exception:
                    continue
            if lk:
                try:
                    r = r.CreateLinkReference(fi._li)
                except Exception:
                    continue
            ds.append((tr.OfVector(f.FaceNormal), tr.OfPoint(tam_mat(f)), r))
    try:
        for g in goc_fi.get_Geometry(opt):
            if g.GetType().Name == "GeometryInstance":
                for s in g.GetSymbolGeometry():
                    them(s, g.Transform, True)
            else:
                them(g, Transform.Identity, False)
    except Exception:
        pass
    return ds


def mat_gan(mats, truc, muc, sai):
    """Reference mặt có pháp tuyến song song truc, vị trí (tâm · truc) gần muc nhất trong khoảng sai."""
    ung = [(abs(q.DotProduct(truc) - muc), r) for n, q, r in mats if abs(n.DotProduct(truc)) > 0.99
           and abs(q.DotProduct(truc) - muc) <= sai]
    return min(ung, key=lambda m: m[0])[1] if ung else None


def tao_dim(doc, view, p0, p1, refs):
    ra = ReferenceArray()
    for r in refs:
        ra.Append(r)
    return doc.Create.NewDimension(view, Line.CreateBound(p0, p1), ra)


# ---------------------------------------------------------------- chính
LOAI_CUA = (int(BuiltInCategory.OST_Doors), int(BuiltInCategory.OST_Windows))
SHEET_CUOI = [None]          # sheet chứa chi tiết vừa làm / đã có (để mở sau khi chạy hết các cửa)


LOAI_TAM = LOAI_CUA + (int(BuiltInCategory.OST_CurtainWallPanels), int(BuiltInCategory.OST_CurtainWallMullions),
                       int(BuiltInCategory.OST_Walls))


def la_cua(e):
    return e is not None and e.Category is not None and e.Category.Id.Value in LOAI_CUA


def la_vach(e):
    """Vách kính = tường có lưới curtain (curtain wall)."""
    try:
        return e is not None and e.GetType().Name == "Wall" and e.CurtainGrid is not None
    except Exception:
        return False


def phan_vach(doc, w):
    """Tấm (kính, cửa đi / cửa sổ làm tấm, tấm tường) + đố của vách kính (vách trong link: phần tử link)."""
    cg = w.CurtainGrid
    ds = []
    for i in list(cg.GetPanelIds()) + list(cg.GetMullionIds()):
        e = w.Document.GetElement(i)
        if e is not None:
            ds.append(LkPT(e, w._li, w._tf) if la_link(w) else e)
    return ds


def vach_chua(doc, e, bang):
    """Vách kính chứa e (tấm / đố / cửa làm tấm curtain); không thuộc vách nào thì None. bang dựng 1 lần mỗi lượt."""
    if not bang:
        bang[-1] = None
        for w in FilteredElementCollector(doc).OfClass(Wall):
            if la_vach(w):
                cg = w.CurtainGrid
                for i in list(cg.GetPanelIds()) + list(cg.GetMullionIds()):
                    bang[i.Value] = w
    return bang.get(e.Id.Value)


def lay_cua(doc, uidoc):
    """Danh sách cửa / vách kính cần làm: IN[0] (nhiều id cách nhau bằng ; hoặc ,) → các đối tượng đang chọn → chọn
    trên màn hình (chọn được nhiều, Finish để xong). Tấm kính / đố / cửa làm tấm của vách kính → lấy vách kính chứa nó.
    Trả về (danh sách, [báo cáo])."""
    sid = (u"%s" % (doc_in(0) or u"")).strip()
    bang = {}
    bc = []

    def chuan(e):
        if e is None or la_vach(e):
            return e
        if la_link(e):        # phần tử link: tấm / cửa của vách kính → vách chứa nó
            try:
                h_ = e.Host
                if la_vach(h_):
                    return h_
            except Exception:
                pass
            return e if la_cua(e) else None
        if e.Category is not None and e.Category.Id.Value in LOAI_TAM:
            w = vach_chua(doc, e, bang)
            if w is not None:
                return w
        return e if la_cua(e) else None

    def gom(els):
        ds, da = [], set()
        for e in els:
            c = chuan(e)
            if c is not None and c.Id.Value not in da:
                da.add(c.Id.Value)
                ds.append(c)
        return ds

    if sid:
        els = []
        for t in re.split(u"[;,\\s]+", sid):
            if not t:
                continue
            try:
                e = lk_tu_id(doc, int(float(t)))
            except Exception:
                e = None
            if chuan(e) is None:
                bc.append(u"ID '%s' không phải cửa đi / cửa sổ / vách kính → bỏ qua." % t)
            else:
                els.append(e)
        return gom(els), bc
    sel = [doc.GetElement(i) for i in uidoc.Selection.GetElementIds()] if uidoc is not None else []
    try:            # đối tượng trong file link đang chọn (Tab chọn trong link)
        for r in (uidoc.Selection.GetReferences() if uidoc is not None else []):
            if r.LinkedElementId != ElementId.InvalidElementId:
                li = doc.GetElement(r.ElementId)
                e_ = li.GetLinkDocument().GetElement(r.LinkedElementId) if li is not None else None
                if e_ is not None:
                    sel.append(LkPT(e_, li))
    except Exception:
        pass
    if sel:
        bo = sum(1 for e in sel if chuan(e) is None)
        if bo:
            bc.append(u"Bỏ qua %d đối tượng đang chọn không phải cửa đi / cửa sổ / vách kính." % bo)
        return gom(sel), bc
    ds = []
    if uidoc is not None:
        try:
            av = uidoc.ActiveView
            chi_link = av is not None and getattr(av, "GenLevel", None) is not None and not any(
                True for _ in FilteredElementCollector(doc, av.Id).OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsNotElementType()) and bool(lk_thay(doc, av, BuiltInCategory.OST_Doors, True))
            if chi_link:          # mặt bằng chỉ có cửa trong link → chọn trong link
                refs = uidoc.Selection.PickObjects(ObjectType.LinkedElement, u"Chọn các cửa đi / cửa sổ / vách kính "
                                                   u"(trong file link) cần triển khai chi tiết rồi bấm Finish")
                ds = gom(LkPT(doc.GetElement(r.ElementId).GetLinkDocument().GetElement(r.LinkedElementId),
                              doc.GetElement(r.ElementId)) for r in refs)
            else:
                refs = uidoc.Selection.PickObjects(ObjectType.Element, u"Chọn các cửa đi / cửa sổ / vách kính cần triển "
                                                                       u"khai chi tiết rồi bấm Finish")
                ds = gom(doc.GetElement(r.ElementId) for r in refs)
        except Exception:
            bc.append(u"Đã huỷ chọn cửa.")
    return ds, bc


def _chinh(fi):
    """Làm chi tiết cho 1 cửa. Trả về báo cáo."""
    doc = DocumentManager.Instance.CurrentDBDocument
    bao_cao = []

    def p(s):
        bao_cao.append(u"%s" % s)

    dry = bool(doc_in(14))
    ti_le = int(round(float(doc_in(4) or 25)))
    le = ft(float(doc_in(5) or 300))
    sym = fi.Document.GetElement(fi.GetTypeId())
    vk = la_vach(fi)
    lk = la_link(fi)          # cửa / vách nằm trong file link: dim vào link reference, ẩn đối tượng khác bằng hạng mục
    mk = u""
    if vk:      # vách kính: mỗi vách một kích thước → nhận theo Mark của vách (type dùng chung nhiều vách)
        cv = fi.Location.Curve
        if cv.GetType().Name != "Line":
            return [u"Vách kính id %d là vách cong → chưa làm được chi tiết." % fi.Id.Value]
        try:
            mk = (fi.get_Parameter(BuiltInParameter.ALL_MODEL_MARK).AsString() or u"").strip()
        except Exception:
            mk = u""
        bbw = fi.get_BoundingBox(None)
        ky_hieu = ten_view_hop_le(mk or u"VK %.0fx%.0f" % (mm(cv.Length), mm(bbw.Max.Z - bbw.Min.Z)))
    else:
        for bip in (BuiltInParameter.WINDOW_TYPE_ID, BuiltInParameter.ALL_MODEL_TYPE_MARK):
            try:
                pm = sym.get_Parameter(bip)
                if pm is not None and pm.AsString():
                    mk = pm.AsString().strip()
                    break
            except Exception:
                pass
        ky_hieu = ten_view_hop_le(mk or ten(sym))
    la_cua_so = fi.Category.Id.Value == int(BuiltInCategory.OST_Windows)
    ten_v = {k: ten_view_hop_le(u"%s %s - %s" % (TIEN_TO[1] if vk else TIEN_TO[0], ky_hieu, t)) for k, t in
             (("mb", u"MẶT BẰNG"), ("md", u"MẶT ĐỨNG"), ("mc", u"MẶT CẮT"))}
    if vk:
        p(u"Vách kính: id %d | %s | Mark '%s'%s" % (fi.Id.Value, ten(sym), mk or u"(trống → %s)" % ky_hieu,
                                                   u" – DRY-RUN, không sửa mô hình" if dry else u""))
    else:
        p(u"Cửa: id %d | %s : %s | Type Mark '%s'%s" % (fi.Id.Value, sym.FamilyName, ten(sym), mk or u"(trống → dùng tên type)",
                                                       u" – DRY-RUN, không sửa mô hình" if dry else u""))

    views = [v for v in FilteredElementCollector(doc).OfClass(View) if not v.IsTemplate]
    trung = [v for v in views if v.Name in ten_v.values()]
    if trung:
        p(u"Type này đã có chi tiết (view: %s) → không tạo thêm." % u", ".join(v.Name for v in trung))
        for vp in FilteredElementCollector(doc).OfClass(Viewport):
            if any(vp.ViewId.Value == v.Id.Value for v in trung):
                sh = doc.GetElement(vp.SheetId)
                p(u"Nằm trên sheet %s - %s." % (sh.SheetNumber, sh.Name))
                SHEET_CUOI[0] = sh
                break
        return bao_cao

    # ---------- Khung toạ độ cửa ----------
    lv = lk_level_host(doc, fi) if lk else doc.GetElement(fi.LevelId)
    if lv is None:
        return [u"Cửa không có level%s → không làm được." % (
            u" (model chính không có level cùng cao độ với level của cửa trong link)" if lk else u"")]
    if lk:
        p(u"   Cửa trong file link '%s' (id trong link %d), level model chính '%s'." % (
            fi._li.Name.split(u" : ")[0], fi._e.Id.Value, lv.Name))
    if vk:
        P0, P1 = cv.GetEndPoint(0), cv.GetEndPoint(1)
        P = (P0 + P1) * 0.5
        H = XYZ(P1.X - P0.X, P1.Y - P0.Y, 0).Normalize()
        parts = phan_vach(doc, fi)
    else:
        P = fi.Location.Point
        H = XYZ(fi.HandOrientation.X, fi.HandOrientation.Y, 0).Normalize()
        parts = []
    nguon = [fi] + parts                         # các phần tử tạo nên hình cửa / vách kính
    N = UP.CrossProduct(H).Normalize()          # pháp tuyến tường (một trong hai phía)
    pts = []
    opt = Options()
    opt.DetailLevel = ViewDetailLevel.Fine
    for e in nguon:
        try:
            diem_hinh(e.get_Geometry(opt), pts)
        except Exception:
            pass
    if not pts:
        bb = fi.get_BoundingBox(None)
        pts = [bb.Min, bb.Max, XYZ(bb.Min.X, bb.Max.Y, bb.Min.Z), XYZ(bb.Max.X, bb.Min.Y, bb.Max.Z)]
    hs = [(q - P).DotProduct(H) for q in pts]
    ss = [(q - P).DotProduct(N) for q in pts]
    zs = [q.Z for q in pts]
    hmin, hmax, zmin, zmax = min(hs), max(hs), min(zs), max(zs)
    rong = hmax - hmin
    hc = (hmin + hmax) / 2.0
    wall = None if vk else fi.Host
    mats = []
    if wall is not None and wall.Category is not None and wall.Category.Id.Value == int(BuiltInCategory.OST_Walls):
        mats = mat_tuong(wall)
        sw = [(tam_mat(f) - P).DotProduct(N) for f in mats if abs(f.FaceNormal.DotProduct(N)) > 0.99]
        # 2 mặt tường gần tâm cửa nhất mỗi phía
        am = [s for s in sw if s <= 0]
        du = [s for s in sw if s >= 0]
        if am and du:
            ss += [max(am), min(du)]
    smin, smax = min(ss), max(ss)
    z_lv = lv.Elevation
    goc_mb = None
    av = doc.ActiveView
    if av is not None and av.ViewType == ViewType.FloorPlan and not av.IsTemplate and av.GenLevel is not None \
            and av.GenLevel.Id.Value == lv.Id.Value:
        goc_mb = av
    else:
        ung = [v for v in views if v.ViewType == ViewType.FloorPlan and v.GenLevel is not None
               and v.GenLevel.Id.Value == lv.Id.Value and not v.Name.startswith(TIEN_TO)
               and v.GetPrimaryViewId().Value < 0]
        ung.sort(key=lambda v: (0 if v.Name == lv.Name else 1, 0 if v.Scale == 100 else 1,
                                0 if v.ViewTemplateId.Value > 0 else 1, v.Name))
        goc_mb = ung[0] if ung else None
    if goc_mb is None:
        return bao_cao + [u"Không có mặt bằng tầng '%s' để tạo callout." % lv.Name]
    p(u"   Kích thước theo hình %s: rộng %.0f, cao %.0f (z %.0f → %.0f so với level %s), dày %.0f"
      % (u"vách (%d tấm + đố)" % len(parts) if vk else u"family", mm(rong), mm(zmax - zmin), mm(zmin - z_lv),
         mm(zmax - z_lv), lv.Name, mm(smax - smin)))

    # ---------- Phía nhìn mặt đứng (ngoài nhà) ----------
    ep = u"%s" % (doc_in(11) or u"")
    ep = khong_dau(ep)
    F = fi.Orientation if vk else fi.FacingOrientation        # vách: Orientation = mặt ngoài tường
    F = XYZ(F.X, F.Y, 0).Normalize()
    S, ly_do = None, u""
    if ep == u"facing":
        S, ly_do = F, u"ép theo mặt ngoài family (Facing)"
    elif ep == u"nguoc":
        S, ly_do = F.Negate(), u"ép ngược Facing"
    else:
        z_do = zmin + ft(1000) if not la_cua_so else z_lv + ft(1000)
        rooms = []
        for dau in (1, -1):
            q = P + N * (dau * ((smax if dau > 0 else -smin) + ft(400)))
            try:
                r_ = doc.GetRoomAtPoint(XYZ(q.X, q.Y, z_do))
                if r_ is None:
                    r_ = lk_room_moi_link(doc, XYZ(q.X, q.Y, z_do))
                rooms.append(r_)
            except Exception:
                rooms.append(None)
        ra, rb = rooms
        if (ra is None) != (rb is None):
            S = N if ra is None else N.Negate()
            ly_do = u"ngoài nhà = phía không có room (phía kia: %s)" % ten(rb if ra is None else ra)
        elif ra is not None and rb is not None:
            na = any(t in khong_dau(ten(ra)) for t in TEN_NGOAI)
            nb = any(t in khong_dau(ten(rb)) for t in TEN_NGOAI)
            if na != nb:
                S = N if na else N.Negate()
                ly_do = u"ngoài nhà = phía room '%s'" % ten(ra if na else rb)
        if S is None:
            arcs = []
            try:
                o2 = Options()
                o2.View = goc_mb
                for e in nguon:
                    cung_mo(e.get_Geometry(o2), arcs)
            except Exception:
                arcs = []
            if arcs:
                tong = sum((a.Evaluate(0.5, True) - P).DotProduct(N) for a in arcs)
                if abs(tong) > ft(10):
                    S = N.Negate() if tong > 0 else N
                    ly_do = u"cửa trong nhà: nhìn từ phía không mở cánh"
        if S is None:
            S, ly_do = F, u"không xác định được ngoài nhà (room 2 phía: %s / %s) và không có cung mở → theo mặt ngoài " \
                          u"family (Facing)" % (ten(ra) if ra is not None else u"không có",
                                                ten(rb) if rb is not None else u"không có")
    if S.DotProduct(N) < 0:
        N = N.Negate()
        ss = [-s for s in ss]
        smin, smax = min(ss), max(ss)
    # từ đây N = S (phía người nhìn mặt đứng), smax = mép phía ngoài
    p(u"   Mặt đứng: %s." % ly_do)
    # khung nhìn mặt bằng trùm hết hình mặt bằng của cửa (kể cả cung mở cánh – nét 2D chỉ có trong hình theo view)
    pts_mb = []
    o3 = Options()
    o3.View = goc_mb
    for e in nguon:
        try:
            diem_hinh(e.get_Geometry(o3), pts_mb)
        except Exception:
            pass
    hs_mb = [hmin, hmax] + [(q - P).DotProduct(H) for q in pts_mb]
    ss_mb = [smin, smax] + [(q - P).DotProduct(N) for q in pts_mb]
    hmin_mb, hmax_mb, smin_mb, smax_mb = min(hs_mb), max(hs_mb), min(ss_mb), max(ss_mb)

    # ---------- Kế hoạch view ----------
    z_lo = min(zmin, z_lv) - le
    X_d = UP.CrossProduct(N)                     # phía phải của người đứng ngoài nhìn vào (= phía phải mặt bằng)
    goc_xoay = math.atan2(X_d.Y, X_d.X)          # xoay mặt bằng để phía phải trùng mặt đứng, ngoài nhà ở dưới
    p(u"   Mặt bằng: callout trên '%s', xoay %.1f° cho trùng chiều mặt đứng (ngoài nhà ở dưới)."
      % (goc_mb.Name, math.degrees(goc_xoay)))

    # ---------- Sheet ----------
    ten_sh = (doc_in(2) or MAC_DINH[2]).strip()
    so_dau = doc_tho(3)
    gd, hm = doc_tho(16), doc_tho(17)
    pid_gd, pid_hm = ts_giai_doan(doc) if (gd or hm) else (None, None)

    def dung_nhom(s):
        """Sheet cùng giai đoạn / hạng mục đã chọn (tham số không có thì coi như cùng)."""
        for pid, gt_ in ((pid_gd, gd), (pid_hm, hm)):
            if pid is not None and gt_:
                prm = ts_theo_id(s, pid)
                if prm is not None and gia_tri_chuoi(prm) != gt_:
                    return False
        return True
    sheets = [s for s in FilteredElementCollector(doc).OfClass(ViewSheet)
              if not s.IsPlaceholder and s.Name == ten_sh and dung_nhom(s)]
    cua_minh = []
    for s in sheets:
        for g in FilteredElementCollector(doc, s.Id).OfClass(Group):
            if ten(g.GroupType).startswith(NHOM_LUOI):
                cua_minh.append(s)
                break
    cua_minh.sort(key=lambda s: khoa_so(s.SheetNumber))
    if so_dau:          # số hiệu chọn trong bảng hỏi: chỉ xếp vào sheet đó và các sheet số lớn hơn cùng tiền tố
        dau, n_dau = tach_so(so_dau)
        cua_minh = [s for s in cua_minh if s.SheetNumber == so_dau or (
            n_dau is not None and tach_so(s.SheetNumber)[0] == dau and (tach_so(s.SheetNumber)[1] or -1) >= n_dau)]
    tb_ten = (doc_in(1) or u"").strip()
    tb_type, dung_ten = tim_khung(doc, tb_ten)
    if tb_type is not None and not dung_ten:
        p(u"   Không có khung tên '%s' → dùng '%s'." % (tb_ten, tb_type.FamilyName))
    vp_all = list(FilteredElementCollector(doc).OfClass(Viewport))
    vung_sh = {}
    for s in cua_minh:
        tb = list(FilteredElementCollector(doc, s.Id).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsNotElementType())
        if tb:
            doc_net_khung(doc, doc.GetElement(tb[0].GetTypeId()), p)
            vung_sh[s.Id.Value] = vung_ve(doc, s, tb[0], p)
    vung_mau = vung_sh[cua_minh[0].Id.Value] if cua_minh and cua_minh[0].Id.Value in vung_sh else None

    # ---------- Khối ô: cửa 1 ô; vách kính GIỮ tỉ lệ 1:IN[4] (người dùng chốt 2026-11-04), không lọt 1 ô thì chiếm khối
    # 2 / 3 / 4 / 6 ô liền nhau trên sheet mới (lưới bỏ nét chia trong khối, 1 dải thông tin dưới khối) ----------
    loai_chu = doc.GetElement(doc.GetDefaultElementTypeId(ElementTypeGroup.TextNoteType))
    # lề phải mặt đứng (dim đứng): vách kính dim chuỗi + tổng
    le_d = max(le, ft(20) * ti_le) if vk else le
    le_c = max(le, ft(13) * ti_le) if vk else le     # lề phải mặt cắt (vách kính: 1 dim chuỗi)
    z_hi = zmax + le_d
    khoi = (1, 1)
    if vk:
        if vung_mau is not None:
            o_w, o_h = (vung_mau[2] - vung_mau[0]) / SO_COT, (vung_mau[3] - vung_mau[1]) / SO_HANG
        else:
            o_w, o_h = ft(232.7), ft(280)        # ô của khung A1 mặc định (vùng vẽ 698 × 560)
        t_chu = chieu_cao_chu(doc, loai_chu)
        s_ = ti_le
        wd = (hmax - hmin + le + le_d) / s_ + ft(6)
        # khung mặt đứng chỉnh theo ký hiệu mặt cắt: trên ~14 mm (3 + đầu ký hiệu ~10 + 1), dưới ~28 mm (3 + đầu ký
        # hiệu + 2 dim ngang + 1,5), cộng lề chú thích 6 mm
        hd = (zmax - min(zmin, z_lv)) / s_ + ft(48)
        wc = (smax - smin + le + le_c) / s_ + t_chu * (len(u"CỐT SÀN HOÀN THIỆN") * 0.75 + 2.5) + ft(6)
        wb = (hmax_mb - hmin_mb + le) / s_ + ft(6)
        hb = (smax_mb - smin_mb + le * 0.5 + max(le * 0.5, ft(15) * s_)) / s_ + ft(6)
        cw, ch = max(wd, wb) + ft(12) + wc + ft(2), hd + ft(14) + hb + ft(14) + ft(2)   # khớp cụm thật ± 1 %
        vuot_kh = True
        for w_, h_ in KHOI_VK:
            if cw <= w_ * o_w and ch <= h_ * o_h - o_h * TI_LE_DAI_TT:
                khoi, vuot_kh = (w_, h_), False
                break
        if vuot_kh:
            khoi = KHOI_VK[-1]
        p(u"   Vách kính 1:%d: cụm ước lượng %.0f × %.0f mm → khối %d × %d ô%s." % (
            ti_le, mm(cw), mm(ch), khoi[0], khoi[1],
            u" – VẪN VƯỢT KHỔ (vách quá dài cho 1 tờ ở 1:%d), cần chia đoạn / xếp tay" % ti_le if vuot_kh else u""))
    chon_sh, chon_o, vung = None, None, None
    if khoi == (1, 1):
        for s in cua_minh:
            vg = vung_sh.get(s.Id.Value)
            if vg is None:
                continue
            trong = o_trong(doc, s, vg, [vp for vp in vp_all if vp.SheetId.Value == s.Id.Value])
            if trong:
                chon_sh, chon_o, vung = s, trong[0], vg
                break
    o_khoi = [(chon_o or 0) + r * SO_COT + c for r in range(khoi[1]) for c in range(khoi[0])]
    ten_o = u"ô %d" % (o_khoi[0] + 1) if len(o_khoi) == 1 else u"ô %s (khối %d × %d)" % (
        u", ".join(str(k + 1) for k in o_khoi), khoi[0], khoi[1])
    so_moi = None
    if chon_sh is None:
        so = sorted([s.SheetNumber for s in sheets], key=khoa_so)
        so_moi = so_dau or (tang_so(so[-1]) if so else MAC_DINH[3])
        co_so = set(s.SheetNumber for s in FilteredElementCollector(doc).OfClass(ViewSheet))
        while so_moi in co_so:
            so_moi = tang_so(so_moi)
        p(u"   %s sheet mới %s - %s (khung '%s'), %s." % (u"Sẽ tạo" if dry else u"Tạo", so_moi, ten_sh,
                                                     tb_type.FamilyName if tb_type is not None else u"không có", ten_o))
    else:
        p(u"   Đặt vào sheet %s - %s, %s/6." % (chon_sh.SheetNumber, chon_sh.Name, ten_o))
    for k in ("mb", "md", "mc"):
        p(u"   %s '%s' tỉ lệ 1:%d" % (u"Sẽ tạo" if dry else u"Tạo", ten_v[k], ti_le))

    def ten_tpl_i(i):
        return (doc_in(i) or u"").strip()

    tk = tach(doc_in(9))
    tk += [u""] * (3 - len(tk))
    an_cat = tach(doc_in(10))
    if dry:
        co_tpl = set(t.Name for t in FilteredElementCollector(doc).OfClass(View) if t.IsTemplate)
        for j, i in enumerate((6, 7, 8)):
            ten_tpl = ten_tpl_i(i)
            if ten_tpl in co_tpl:
                p(u"   Template '%s' đã có → dùng nguyên." % ten_tpl)
            else:
                lay_template(doc, None, ten_tpl, tk[j], ti_le, an_cat, p, False)
        return bao_cao

    # ================================================================ GHI
    if chon_sh is None and tb_type is not None:
        doc_net_khung(doc, tb_type, p)
    TransactionManager.Instance.EnsureInTransaction(doc)
    ten_sec = None
    for t in FilteredElementCollector(doc).OfClass(ViewFamilyType):
        if t.ViewFamily == ViewFamily.Section:
            if ten_sec is None or (t.DefaultTemplateId.Value < 0 and ten_sec.DefaultTemplateId.Value >= 0):
                ten_sec = t

    def kieu_rieng(goc_t, ten_moi, ho):
        """Kiểu view riêng cho chi tiết cửa (Project Browser gom thành mục riêng); chưa có thì chép từ goc_t."""
        for t in FilteredElementCollector(doc).OfClass(ViewFamilyType):
            if t.ViewFamily == ho and ten(t) == ten_moi:
                return t
        t = goc_t.Duplicate(ten_moi)
        p(u"   Tạo kiểu view '%s' (chép từ '%s')." % (ten_moi, ten(goc_t)))
        return t
    kieu_mc = kieu_rieng(ten_sec, KIEU_MC, ViewFamily.Section)
    # Ký hiệu mặt cắt trên mặt đứng là vết cắt → kiểu MẶT CẮT CỬA (kiểu riêng của công cụ) phải dùng section tag có đầu
    # (G19: "Wall Section" dùng tag Head / Tail = none → chỉ có đường, không có đầu). Ưu tiên tag của kiểu mặt cắt "chi
    # tiết" (G19: AV_Section Detail), rồi tag bất kỳ có đầu.
    try:
        def co_dau(tag_id):
            t = doc.GetElement(tag_id)
            if t is None:
                return False
            for prm in t.Parameters:
                if prm.StorageType == StorageType.ElementId and khong_dau(prm.Definition.Name) in (u"section head",):
                    return prm.AsElementId().Value > 0
            return False
        p_tag = kieu_mc.get_Parameter(BuiltInParameter.SECTION_TAG)
        if p_tag is not None and not co_dau(p_tag.AsElementId()):
            ung_tag = []
            for t in FilteredElementCollector(doc).OfClass(ViewFamilyType):
                if t.ViewFamily != ViewFamily.Section or t.Id.Value == kieu_mc.Id.Value:
                    continue
                pt = t.get_Parameter(BuiltInParameter.SECTION_TAG)
                if pt is not None and co_dau(pt.AsElementId()):
                    ung_tag.append((0 if u"chi tiet" in khong_dau(ten(t)) else 1, pt.AsElementId()))
            if ung_tag:
                ung_tag.sort(key=lambda u_: u_[0])
                p_tag.Set(ung_tag[0][1])
                p(u"   Kiểu '%s': đổi section tag sang '%s' (tag cũ không có đầu ký hiệu)." % (
                    KIEU_MC, ten(doc.GetElement(ung_tag[0][1]))))
            else:
                p(u"   CẢNH BÁO: dự án không có section tag nào có đầu ký hiệu → vết cắt chỉ có đường.")
    except Exception as ex:
        p(u"   Không kiểm được section tag của kiểu '%s' (%s)." % (KIEU_MC, ex))
    kieu_mb = kieu_rieng(doc.GetElement(goc_mb.GetTypeId()), KIEU_MB, ViewFamily.FloorPlan)
    tam = P + H * hc

    def hop(O, nhin, R, xlo, xhi, ylo, yhi, sau):
        """Hộp cho ViewSection.CreateSection. Thử trên Revit 2027.3: view nhìn theo +BasisZ (ViewDirection = -BasisZ),
        mặt cắt ở Min.Z, cắt xa ở Max.Z, RightDirection = -BasisX. nhin = hướng nhìn, R = phía phải trên view,
        [xlo, xhi] đo theo R, sau = chiều sâu nhìn tính từ mặt cắt (qua O)."""
        tr = Transform.Identity
        tr.Origin = O
        tr.BasisX = R.Negate()
        tr.BasisY = UP
        tr.BasisZ = nhin
        b = BoundingBoxXYZ()
        b.Transform = tr
        b.Min = XYZ(-xhi, ylo, 0)
        b.Max = XYZ(-xlo, yhi, sau)
        return b

    def khung(O, X):
        xs = [(q - O).DotProduct(X) for q in pts]
        return min(xs), max(xs)

    # Cốt sàn hoàn thiện (thay level, level ẩn trên mặt đứng / mặt cắt): mặt trên sàn trong nhà, không có thì ngoài nhà
    z_do_san = zmin + ft(5) if not (la_cua_so or vk) else max(zmin, z_lv) + ft(300)
    phia_san = -1
    z_s = mat_san(doc, P - N * (-smin + ft(150)), z_do_san)[1]
    if z_s is None:
        phia_san = 1
        z_s = mat_san(doc, P + N * (smax + ft(150)), z_do_san)[1]
    z_cot = z_s if z_s is not None else z_lv
    chu_cot = u"CỐT SÀN HOÀN THIỆN"
    h_chu =chieu_cao_chu(doc, loai_chu) * ti_le                 # chiều cao chữ theo toạ độ model
    dai_chu = len(chu_cot) * h_chu * 0.75                         # ước lượng chiều dài chữ (Arial chữ hoa)

    # Mặt đứng: mặt cắt đặt trước mặt ngoài tường (không cắt cửa), nhìn vào tường từ phía ngoài nhà (N)
    O_d = XYZ(tam.X, tam.Y, zmin) + N * (smax + ft(200))
    a, b = khung(O_d, X_d)
    v_md = ViewSection.CreateSection(doc, kieu_mc.Id,
                                     hop(O_d, N.Negate(), X_d, a - le, b + le_d, z_lo - zmin, z_hi - zmin,
                                         smax - smin + ft(400)))
    # Mặt cắt: cắt qua cánh, cách tâm 1/4 bề rộng về phía người nhìn; ngoài nhà (N) nằm bên phải
    X_c = N
    V_c = N.CrossProduct(UP)                     # phía người nhìn (UP × V_c = N)
    O_c = XYZ(tam.X, tam.Y, zmin) + V_c * (rong / 4.0)
    sau_mc = rong * 0.75 + ft(50)
    if vk:
        # vách kính: cắt qua giữa ô cửa sổ, không có thì ô cửa đi (lệch 1/4 như cửa), rồi ô kính gần giữa vách; nhìn
        # sâu tới đố cạnh ô (không thấy cả dãy đố phía sau)
        hang_tam = {int(BuiltInCategory.OST_Windows): 0, int(BuiltInCategory.OST_Doors): 1,
                    int(BuiltInCategory.OST_CurtainWallPanels): 2}
        ung = []
        for e in parts:
            c = e.Category
            if c is None or c.Id.Value not in hang_tam:
                continue
            bb = e.get_BoundingBox(None)
            if bb is None:
                continue
            hx = [(XYZ(x, y, 0) - XYZ(P.X, P.Y, 0)).DotProduct(V_c) for x in (bb.Min.X, bb.Max.X) for y in (bb.Min.Y, bb.Max.Y)]
            w_t = max(hx) - min(hx)
            if w_t < ft(100):
                continue
            hang = hang_tam[c.Id.Value] + (1 if khong_dau(ten(e)) in (u"empty", u"wall") else 0)
            x_t = (max(hx) + min(hx)) / 2.0 + (w_t / 4.0 if hang == 1 else 0)
            ung.append((hang, abs(x_t - (hc if V_c.DotProduct(H) > 0 else -hc)), x_t, w_t, ten(e)))
        if ung:
            ung.sort(key=lambda u_: (u_[0], u_[1]))
            _, _, x_t, w_t, ten_t = ung[0]
            O_c = XYZ(P.X, P.Y, zmin) + V_c * x_t
            sau_mc = w_t / 2.0 + ft(150)
            p(u"   Mặt cắt vách kính qua ô '%s' (rộng %.0f)." % (ten_t, mm(w_t)))
    a2, b2 = khung(O_c, X_c)
    a2 = min(a2, smin)
    b2 = max(b2, smax)
    # chữ cốt sàn bên trái (trong nhà) như mẫu, nằm NGOÀI khung cắt (vùng annotation crop nới rộng) để không đè
    # tường / sàn phía trong: mũi tên chỉ xuống nét sàn, chữ bên phải mũi tên
    trai_mc = a2 - le
    x_mui = trai_mc - dai_chu - 2.5 * h_chu
    # khung mặt cắt sát chiều cao (cốt sàn / chân cửa → đỉnh cửa ± 3 mm giấy): ký hiệu section của nó hiện trên mặt đứng
    # làm vết cắt, đường cắt dài đúng bằng khung này, 2 đầu ký hiệu nằm ngay ngoài (người dùng yêu cầu 2026-11-04)
    z_lo_c = min(zmin, z_cot) - ft(3) * ti_le
    z_hi_c = zmax + ft(3) * ti_le
    v_mc = ViewSection.CreateSection(doc, kieu_mc.Id,
                                     hop(O_c, V_c.Negate(), X_c, trai_mc, b2 + le_c, z_lo_c - zmin, z_hi_c - zmin,
                                         sau_mc))
    for nhan, v, vd, r in ((u"mặt đứng", v_md, N, X_d), (u"mặt cắt", v_mc, V_c, X_c)):
        if v.ViewDirection.DotProduct(vd) < 0.99 or v.RightDirection.DotProduct(r) < 0.99:
            p(u"   CẢNH BÁO: hướng %s khác dự kiến (ViewDirection %s, Right %s) – Revit đổi quy ước CreateSection?"
              % (nhan, v.ViewDirection, v.RightDirection))
    # Mặt bằng: callout chữ nhật rộng theo X, sâu theo Y quanh tâm cửa, rồi xoay khung crop để phía phải = X_d
    # (cùng chiều mặt đứng), phía ngoài nhà ở dưới; khung trùm hết hình mặt bằng (pts_mb)
    # lề nửa: cung mở đã to; vách kính: phía ngoài nhà chừa chỗ dim rộng (9 mm giấy, ở 1/100 lề 150 mm không đủ)
    le_mb = max(le * 0.5, ft(15) * ti_le) if vk else le * 0.5
    C = P + H * ((hmin_mb + hmax_mb) / 2.0) + N * ((smin_mb - le * 0.5 + smax_mb + le_mb) / 2.0)
    nw, nd = (hmax_mb - hmin_mb) / 2.0 + le * 0.5, (smax_mb + le_mb - smin_mb + le * 0.5) / 2.0
    v_mb = ViewSection.CreateCallout(doc, goc_mb.Id, kieu_mb.Id,
                                     XYZ(C.X - nw, C.Y - nd, z_lv), XYZ(C.X + nw, C.Y + nd, z_lv))
    v_mb = doc.GetElement(v_mb.Id)
    if abs(goc_xoay) > 1e-4:
        crop = phan_tu_crop(doc, v_mb)
        try:
            if crop is None:
                raise Exception(u"không tìm thấy phần tử crop")
            ElementTransformUtils.RotateElement(doc, crop.Id, Line.CreateBound(XYZ(C.X, C.Y, z_lv), XYZ(C.X, C.Y, z_lv + 1)),
                                                goc_xoay)
            doc.Regenerate()
        except Exception as ex:
            p(u"   CẢNH BÁO: không xoay được mặt bằng (%s) → mặt bằng theo trục dự án." % ex)
    if v_mb.RightDirection.DotProduct(X_d) < 0.99:
        p(u"   CẢNH BÁO: mặt bằng chưa cùng chiều mặt đứng (Right %s, cần %s)." % (v_mb.RightDirection, X_d))
    tieu_de = {"mb": u"MẶT BẰNG", "md": u"MẶT ĐỨNG", "mc": u"MẶT CẮT"}     # mặt cắt: thêm "n-n" khi đặt lên sheet
    vs = {"mb": v_mb, "md": v_md, "mc": v_mc}
    for k, v in vs.items():
        v.Name = ten_v[k]
        try:
            v.Scale = ti_le
        except Exception:
            pass
        try:
            v.get_Parameter(BuiltInParameter.VIEW_DESCRIPTION).Set(tieu_de[k])
        except Exception:
            pass
    for k, i in (("mb", 6), ("md", 7), ("mc", 8)):
        an_lk = []
        if lk and k == "md":      # mặt đứng chỉ có cửa: ẩn hạng mục (Revit không ẩn từng phần tử trong link)
            an_lk = list(AN_LINK_MD)
        elif lk and k == "mb":    # mặt bằng: cửa + tường
            an_lk = list(AN_LINK_MB)
        tpl = lay_template(doc, vs[k], ten_tpl_i(i) + (HAU_TO_LINK if (lk and an_lk) else u""), tk[["mb", "md", "mc"].index(k)],
                           ti_le, an_cat + ([] if k == "mb" else ["OST_Levels"]), p, True, an_lk)
        if tpl is not None and vs[k].ViewTemplateId.Value != tpl.Id.Value:
            vs[k].ViewTemplateId = tpl.Id
    for k, v in vs.items():
        try:
            v.Scale = ti_le
        except Exception:
            pass
        try:
            v.CropBoxActive = True
            v.CropBoxVisible = False
        except Exception:
            pass
        try:            # cắt chú thích sát khung nhìn: đầu level / ký hiệu ngoài khung không làm to viewport
            v.get_Parameter(BuiltInParameter.VIEWER_ANNOTATION_CROP_ACTIVE).Set(1)
            sm = v.GetCropRegionShapeManager()
            for thuoc_tinh in ("LeftAnnotationCropOffset", "RightAnnotationCropOffset",
                               "TopAnnotationCropOffset", "BottomAnnotationCropOffset"):
                setattr(sm, thuoc_tinh, ft(3))
        except Exception:
            pass
    try:            # annotation crop trái của mặt cắt chứa chữ cốt sàn (offset đo trên giấy)
        v_mc.GetCropRegionShapeManager().LeftAnnotationCropOffset = (trai_mc - x_mui) / ti_le + ft(4)
    except Exception as ex:
        p(u"   Không nới được vùng chú thích trái của mặt cắt (%s) – chữ cốt sàn có thể bị cắt." % ex)
    for v in (v_md, v_mc):
        try:
            v.get_Parameter(BuiltInParameter.VIEWER_BOUND_FAR_CLIPPING).Set(2)     # cắt xa, không vẽ nét
        except Exception:
            pass
        try:
            v.get_Parameter(BuiltInParameter.SECTION_COARSER_SCALE_PULLDOWN_METRIC).Set(ti_le)
        except Exception:
            pass
    doc.Regenerate()
    # Ký hiệu / khung callout của MỌI view chi tiết cửa ẩn trong nhau (cửa gần nhau: khung callout cửa làm sau hiện
    # trên mặt bằng chi tiết cửa làm trước) – cả view đã có từ lần bấm trước
    ct = [v for v in FilteredElementCollector(doc).OfClass(View) if not v.IsTemplate and v.Name.startswith(TIEN_TO)]
    ten_ct = set(v.Name for v in ct)
    crop_ct = {}
    for v in ct:
        if v.ViewType == ViewType.FloorPlan:
            c = phan_tu_crop(doc, v)
            if c is not None:
                crop_ct[v.Id.Value] = c.Id.Value
    so_an = 0
    for v in ct:
        moi = v.Id.Value in (v_mb.Id.Value, v_md.Id.Value, v_mc.Id.Value)
        ten_an = (ten_ct - set([v.Name])) if moi else set([v_mb.Name, v_md.Name, v_mc.Name])
        if v.Id.Value == v_md.Id.Value:
            ten_an.discard(v_mc.Name)            # ký hiệu mặt cắt giữ trên mặt đứng = vết cắt
        crop_an = set(i for k, i in crop_ct.items() if k != v.Id.Value and (moi or k == v_mb.Id.Value))
        so_an += an_ky_hieu(doc, v, ten_an, crop_an)
    if bool(doc_in(13)):
        so_an += an_ky_hieu(doc, goc_mb, [v_mb.Name])
    p(u"   Đã tạo 3 view (id %d, %d, %d); ẩn %d ký hiệu view không cần thấy." % (v_mb.Id.Value, v_md.Id.Value,
                                                                          v_mc.Id.Value, so_an))

    # ---------- Cốt sàn: nét đứt trên mặt đứng + mặt cắt, chữ "CỐT SÀN HOÀN THIỆN ..." có mũi tên trên mặt cắt ----------
    gs_dut = kieu_net_dut(doc)
    gs_an = None
    try:
        gs_an = Category.GetCategory(doc, BuiltInCategory.OST_InvisibleLines).GetGraphicsStyle(GraphicsStyleType.Projection)
    except Exception:
        pass
    net_san = {}
    for k, v, O, X, x_a, x_b in (("md", v_md, O_d, X_d, a - le, b + le), ("mc", v_mc, O_c, X_c, x_mui - h_chu, b2 + le)):
        g0 = XYZ(O.X, O.Y, z_cot)
        net_san[k] = doc.Create.NewDetailCurve(v, Line.CreateBound(g0 + X * x_a, g0 + X * x_b))
        gs = gs_an if gs_an is not None else gs_dut      # nét hiện là nét suốt ô trên sheet; nét này để dim bám
        if gs is not None:
            try:
                net_san[k].LineStyle = gs
            except Exception:
                pass
    g0 = XYZ(O_c.X, O_c.Y, z_cot)
    tn = TextNote.Create(doc, v_mc.Id, g0 + X_c * (x_mui + h_chu) + UP * (2.2 * h_chu), chu_cot, loai_chu.Id)
    try:
        ld = tn.AddLeader(TextNoteLeaderTypes.TNLT_STRAIGHT_L)
        ld.End = g0 + X_c * x_mui
        ld.Elbow = g0 + X_c * x_mui + UP * (1.7 * h_chu)
    except Exception as ex:
        p(u"   Không thêm được mũi tên cho chữ cốt sàn (%s)." % ex)
    p(u"   Cốt sàn: %s %+.0f so với level, nét '%s', chữ '%s' (kiểu chữ '%s')." % (
        u"mặt sàn trong nhà" if z_s is not None and phia_san < 0 else u"mặt sàn ngoài nhà" if z_s is not None else u"level",
        mm(z_cot - z_lv), ten(gs_dut) if gs_dut is not None else u"mặc định", chu_cot, ten(loai_chu)))

    # ---------- Vết cắt = ký hiệu section của mặt cắt trên mặt đứng (người dùng yêu cầu 2026-11-04 "vết cắt thể hiện bằng
    # section"; thay vạch + mũi tên vẽ tay). Khung mặt đứng: trên = đầu ký hiệu, dưới = đầu ký hiệu + dim ngang (dim ngang
    # xuống CHÂN mặt đứng, người dùng yêu cầu 2026-11-04) ----------
    try:
        if v_md.GetCategoryHidden(ElementId(BuiltInCategory.OST_Sections)):
            v_md.SetCategoryHidden(ElementId(BuiltInCategory.OST_Sections), False)
    except Exception:
        pass
    doc.Regenerate()
    ky_mc = None
    for e in FilteredElementCollector(doc, v_md.Id).OfCategory(BuiltInCategory.OST_Viewers).WhereElementIsNotElementType():
        try:
            pn = e.get_Parameter(BuiltInParameter.VIEW_NAME)
            if pn is not None and pn.AsString() == v_mc.Name:
                ky_mc = e
                break
        except Exception:
            pass
    bb_k = ky_mc.get_BoundingBox(v_md) if ky_mc is not None else None
    # hộp bao ký hiệu rộng hơn ký hiệu thật (G19: ±24 mm giấy) → trên (đầu ký hiệu tròn + mũi tên) chừa 12 mm giấy, dưới
    # (đuôi) chừa theo tham số Height của family đuôi + 1 mm
    duoi_k = ft(12)
    try:
        tag_k = doc.GetElement(kieu_mc.get_Parameter(BuiltInParameter.SECTION_TAG).AsElementId())
        for prm in tag_k.Parameters:
            if prm.StorageType == StorageType.ElementId and khong_dau(prm.Definition.Name) == u"section tail":
                sym_d = doc.GetElement(prm.AsElementId())
                duoi_k = ft(1)
                if sym_d is not None:
                    for q_ in sym_d.Parameters:
                        if khong_dau(q_.Definition.Name) == u"height" and q_.StorageType == StorageType.Double:
                            duoi_k = q_.AsDouble() + ft(1)
    except Exception:
        pass
    if bb_k is not None:
        z_ky_lo = max(min(bb_k.Min.Z, z_lo_c), z_lo_c - duoi_k * ti_le)
        z_ky_hi = min(max(bb_k.Max.Z, z_hi_c), z_hi_c + ft(12) * ti_le)
    else:
        z_ky_lo, z_ky_hi = z_lo_c - ft(10) * ti_le, z_hi_c + ft(10) * ti_le
        p(u"   CẢNH BÁO: ký hiệu mặt cắt không hiện trên mặt đứng (template ẩn Sections?) → vết cắt thiếu.")
    # dim ngang dưới chân: chuỗi cách đuôi ký hiệu 5 mm giấy, tổng 12 mm (chữ dim nằm phía trên đường dim)
    z_dim1, z_dim2 = z_ky_lo - ft(5) * ti_le, z_ky_lo - ft(12) * ti_le
    z_day_md = (z_dim2 if vk else z_dim1) - ft(1) * ti_le
    try:
        cb = v_md.CropBox
        tr_inv = cb.Transform.Inverse
        y_lo = tr_inv.OfPoint(XYZ(O_d.X, O_d.Y, z_day_md)).Y
        y_hi = tr_inv.OfPoint(XYZ(O_d.X, O_d.Y, z_ky_hi + ft(1) * ti_le)).Y
        cb.Min = XYZ(cb.Min.X, y_lo, cb.Min.Z)
        cb.Max = XYZ(cb.Max.X, y_hi, cb.Max.Z)
        v_md.CropBox = cb
    except Exception as ex:
        p(u"   Không chỉnh được khung mặt đứng theo ký hiệu mặt cắt (%s)." % ex)
    p(u"   Vết cắt: ký hiệu section của mặt cắt (chừa %+.0f / %+.0f mm so với cốt sàn / đỉnh; hộp bao %s)." % (
        mm(z_ky_lo - z_cot), mm(z_ky_hi - zmax),
        u"%+.0f / %+.0f" % (mm(bb_k.Min.Z - z_cot), mm(bb_k.Max.Z - zmax)) if bb_k is not None else u"-"))

    # ---------- Kích thước vách kính: mép = mặt ngoài đố biên (không có đố thì mặt tấm); chuỗi theo lưới đố + tổng ----------
    luoi_ids = []
    dim_vk = []          # dim vách kính đã tạo: kiểm lại sau khi ẩn phần tử (mất thì dựng lại vào nét ẩn)
    if vk and not lk:     # vách trong link: lưới không lấy được trên view model chính → dim theo mép đố
        try:
            luoi_ids = list(fi.CurtainGrid.GetUGridLineIds()) + list(fi.CurtainGrid.GetVGridLineIds())
        except Exception:
            luoi_ids = []
    if bool(doc_in(12)) and vk:
        dim_kq = []
        m_cat = int(BuiltInCategory.OST_CurtainWallMullions)
        p0h = P.DotProduct(H)
        dos = [e for e in parts if e.Category is not None and e.Category.Id.Value == m_cat]
        nguon_m = u"đố" if dos else u"tấm"
        if not dos:
            dos = [e for e in parts if e.GetType().Name != "Wall"]

        def mep(view, loc=None):
            """(trái, phải, (z chân, ref chân), ref đỉnh) theo mặt đố biên (không có đố thì mặt tấm) trên view."""
            mh = []
            for e in dos:
                if loc is None or loc(e):
                    mh += mat_hinh_cua(doc, e, view)
            mh_h = [(q.DotProduct(H) - p0h, r) for n, q, r in mh if abs(n.DotProduct(H)) > 0.99]
            mh_z = [(q.Z, r) for n, q, r in mh if abs(n.Z) > 0.99]
            return (min(mh_h, key=lambda m: m[0]) if mh_h else None, max(mh_h, key=lambda m: m[0]) if mh_h else None,
                    min(mh_z, key=lambda m: m[0]) if mh_z else None, max(mh_z, key=lambda m: m[0]) if mh_z else None)
        m_tr, m_ph, z_bot, m_tren = mep(None)
        r_trai, r_phai = (m_tr[1] if m_tr else None), (m_ph[1] if m_ph else None)
        r_tren = m_tren[1] if m_tren else None
        chan_cao = z_bot is not None and z_bot[0] - z_cot > ft(5)       # chân vách cao hơn cốt sàn
        r_duoi = z_bot[1] if chan_cao else None
        h_trai = m_tr[0] if m_tr else hmin
        h_phai = m_ph[0] if m_ph else hmax
        z_day = z_bot[0] if z_bot else zmin
        z_dinh = m_tren[0] if m_tren else zmax
        # mặt cắt cắt qua đố: reference lấy theo hình của chính view đó
        x_cat_c = O_c.DotProduct(V_c)

        def qua_cat(e):
            bb = e.get_BoundingBox(None)
            if bb is None:
                return False
            xs = [XYZ(x, y, 0).DotProduct(V_c) for x in (bb.Min.X, bb.Max.X) for y in (bb.Min.Y, bb.Max.Y)]
            return min(xs) - ft(1) <= x_cat_c <= max(xs) + ft(1)
        _, _, mc_bot, mc_tren = mep(v_mc, qua_cat)
        gs_an_d = None
        try:
            gs_an_d = Category.GetCategory(doc, BuiltInCategory.OST_InvisibleLines).GetGraphicsStyle(GraphicsStyleType.Projection)
        except Exception:
            pass

        def net_an(view, q0, q1):
            """Nét ẩn trên view làm chỗ bám dim (khi Revit xoá dim vào mặt đố)."""
            c = doc.Create.NewDetailCurve(view, Line.CreateBound(q0, q1))
            if gs_an_d is not None:
                c.LineStyle = gs_an_d
            return c.GeometryCurve.Reference

        def ref_luoi(gl, view):
            """Reference đường lưới curtain (trục đố) trên view."""
            o = Options()
            o.ComputeReferences = True
            o.IncludeNonVisibleObjects = True
            o.View = view
            try:
                for g in gl.get_Geometry(o):
                    if g.GetType().Name == "Line" and g.Reference is not None:
                        return g.Reference
            except Exception:
                pass
            try:
                return Reference(gl)
            except Exception:
                return None
        luoi_dung, luoi_ngang = [], []           # (vị trí theo H / cao độ, đường lưới)
        for i in luoi_ids:
            gl = doc.GetElement(i)
            try:
                c = gl.FullCurve
                d = (c.GetEndPoint(1) - c.GetEndPoint(0)).Normalize()
                q = c.Evaluate(0.5, True)
            except Exception:
                continue
            if abs(d.Z) > 0.99:
                luoi_dung.append((q.DotProduct(H) - p0h, gl))
            elif abs(d.Z) < 0.01:
                luoi_ngang.append((q.Z, gl))
        luoi_dung.sort(key=lambda m: m[0])
        luoi_ngang.sort(key=lambda m: m[0])

        def thu(nhan, view, p0, p1, refs, du_phong=None):
            """Tạo dim; Revit xoá dim (reference không dùng được trên view) thì dựng lại bằng refs du_phong() (nét ẩn)."""
            refs = [r for r in refs if r is not None]
            loi = u"thiếu reference"
            if len(refs) >= 2:
                try:
                    d = tao_dim(doc, view, p0, p1, refs)
                    doc.Regenerate()
                    if d.IsValidObject:
                        dim_kq.append(u"%s: OK (%d đoạn)" % (nhan, len(refs) - 1))
                        dim_vk.append((d, nhan, view, p0, p1, du_phong))
                        return True
                    loi = u"Revit xoá dim"
                except Exception as ex:
                    loi = u"lỗi (%s)" % ex
            if du_phong is not None:
                try:
                    tao_dim(doc, view, p0, p1, du_phong())
                    dim_kq.append(u"%s: OK theo nét ẩn (%s)" % (nhan, loi))
                    return True
                except Exception as ex:
                    loi += u"; nét ẩn lỗi (%s)" % ex
            dim_kq.append(u"%s: %s" % (nhan, loi))
            return False
        d1, d2 = ft(9) * ti_le, ft(16) * ti_le      # chuỗi / tổng cách mép vách (đo trên giấy 9 / 16 mm)
        # mặt bằng phía ngoài nhà: chuỗi khoảng cách đố (người dùng yêu cầu 2026-11-04; trục đố = lưới đứng, trên mặt bằng
        # lưới chỉ là điểm nên bám nét ẩn tại trục) cách mép 6 mm giấy, tổng 13 mm
        g_mb = XYZ(P.X, P.Y, z_lv)

        def ne_mb(hs):
            return [net_an(v_mb, g_mb + H * h + N * smin, g_mb + H * h + N * smax) for h in hs]
        for nhan, dn, chuoi in ((u"MB chuỗi đố", ft(6) * ti_le, True), (u"MB rộng", ft(13) * ti_le, False)):
            if chuoi and not luoi_dung:
                continue
            q = P + N * (smax_mb + dn)
            giua = [h for h, _ in luoi_dung] if chuoi else []
            # bám nét ẩn tại mép + trục đố (reference mặt đố biên theo view mặt bằng không ổn định: VK.11 mất đoạn cuối)
            thu(nhan, v_mb, XYZ(q.X, q.Y, z_lv) + H * (hmin - le), XYZ(q.X, q.Y, z_lv) + H * (hmax + le),
                ne_mb([h_trai] + giua + [h_phai]))
        # mặt đứng: chuỗi đố + tổng dưới CHÂN (dưới đầu ký hiệu mặt cắt), chuỗi đứng + tổng bên phải
        for nhan, z_d, chuoi in ((u"MĐ ngang chuỗi", z_dim1, True), (u"MĐ ngang tổng", z_dim2, False)):
            if chuoi and not luoi_dung:
                continue
            q = XYZ(O_d.X, O_d.Y, z_d)
            refs = [r_trai] + ([ref_luoi(gl, v_md) for _, gl in luoi_dung] if chuoi else []) + [r_phai]
            thu(nhan, v_md, q + X_d * (a - le), q + X_d * (b + le), refs)
        r_san_md = net_san["md"].GeometryCurve.Reference
        for nhan, dx, chuoi in ((u"MĐ đứng chuỗi", d1, True), (u"MĐ đứng tổng", d2, False)):
            if chuoi and not (luoi_ngang or r_duoi is not None):
                continue
            q = O_d + X_d * (b + dx)
            refs = [r_san_md, r_duoi] + ([ref_luoi(gl, v_md) for _, gl in luoi_ngang] if chuoi else []) + [r_tren]
            thu(nhan, v_md, XYZ(q.X, q.Y, z_lo), XYZ(q.X, q.Y, z_hi), refs)
        q = O_c + X_c * (b2 + d1)
        r_san_mc = net_san["mc"].GeometryCurve.Reference
        g_mc = XYZ(O_c.X, O_c.Y, 0)
        thu(u"MC cao", v_mc, XYZ(q.X, q.Y, z_lo), XYZ(q.X, q.Y, z_hi),
            [r_san_mc, mc_bot[1] if (chan_cao and mc_bot) else None, mc_tren[1] if mc_tren else None],
            lambda: [r_san_mc] + [net_an(v_mc, g_mc + X_c * smin + UP * z, g_mc + X_c * smax + UP * z)
                                  for z in ([z_day] if chan_cao else []) + [z_dinh]])
        p(u"   Kích thước (mép theo %s, %d lưới đứng / %d lưới ngang): %s." % (
            nguon_m, len(luoi_dung), len(luoi_ngang), u"; ".join(dim_kq)))

    # ---------- Kích thước tổng ----------
    if bool(doc_in(12)) and not vk:
        dim_kq = []
        r_trai, r_phai = ref_family(fi, "Left"), ref_family(fi, "Right")
        r_tren, r_duoi = ref_family(fi, "Top"), ref_family(fi, "Bottom")
        nguon_w = u"family"
        h_tr, h_ph = hmin, hmax
        if r_trai is None or r_phai is None:     # mép lỗ mở của tường
            nguon_w = u"mép lỗ tường"
            mep = [(abs((tam_mat(f) - P).DotProduct(H) - hmin), (tam_mat(f) - P).DotProduct(H), f) for f in mats
                   if abs(f.FaceNormal.DotProduct(H)) > 0.99 and smin - ft(5) <= (tam_mat(f) - P).DotProduct(N) <= smax + ft(5)]
            tr = [m for m in mep if abs(m[1] - hmin) < ft(150)]
            ph = [(abs(m[1] - hmax), m[1], m[2]) for m in mep if abs(m[1] - hmax) < ft(150)]
            r_trai = min(tr, key=lambda m: m[0])[2].Reference if tr else None
            r_phai = min(ph, key=lambda m: m[0])[2].Reference if ph else None
            h_tr = min(tr, key=lambda m: m[0])[1] if tr else hmin
            h_ph = min(ph, key=lambda m: m[0])[1] if ph else hmax
        nguon_h = u"family"
        z_dinh, z_bau = zmax, zmin
        if r_tren is None:
            dinh = [(abs(tam_mat(f).Z - zmax), f) for f in mats if f.FaceNormal.Z < -0.99
                    and abs(tam_mat(f).Z - zmax) < ft(150) and abs((tam_mat(f) - P).DotProduct(H) - hc) < rong]
            r_tren = min(dinh, key=lambda m: m[0])[1].Reference if dinh else None
            z_dinh = tam_mat(min(dinh, key=lambda m: m[0])[1]).Z if dinh else zmax
            nguon_h = u"đỉnh lỗ tường"
        if la_cua_so and r_duoi is None:
            bau = [(abs(tam_mat(f).Z - zmin), f) for f in mats if f.FaceNormal.Z > 0.99
                   and abs(tam_mat(f).Z - zmin) < ft(150) and abs((tam_mat(f) - P).DotProduct(H) - hc) < rong]
            r_duoi = min(bau, key=lambda m: m[0])[1].Reference if bau else None
            z_bau = tam_mat(min(bau, key=lambda m: m[0])[1]).Z if bau else zmin
        # mặt đứng ẩn tường → mép / đỉnh / bậu lấy trên hình cửa: mặt gần mép lỗ tường nhất (không có thì mép hình cửa)
        r_md = {"trai": r_trai, "phai": r_phai, "tren": r_tren, "duoi": r_duoi}
        if nguon_w != u"family" or nguon_h != u"family" or (la_cua_so and ref_family(fi, "Bottom") is None):
            mh = mat_hinh_cua(doc, fi)
            p0h = P.DotProduct(H)
            if nguon_w != u"family":
                r_md["trai"] = mat_gan(mh, H, p0h + h_tr, ft(60))
                r_md["phai"] = mat_gan(mh, H, p0h + h_ph, ft(60))
            if nguon_h != u"family":
                r_md["tren"] = mat_gan(mh, UP, z_dinh, ft(60))
            if la_cua_so and ref_family(fi, "Bottom") is None:
                r_md["duoi"] = mat_gan(mh, UP, z_bau, ft(60))
        # chân: nét cốt sàn của từng view (level ẩn, sàn ẩn trên mặt đứng)
        nguon_h += u", chân = nét cốt sàn"

        def chuoi_h(k):
            d, t = (r_md["duoi"], r_md["tren"]) if k == "md" else (r_duoi, r_tren)
            ds = [net_san[k].GeometryCurve.Reference, d, t] if la_cua_so else [net_san[k].GeometryCurve.Reference, t]
            return [r for r in ds if r is not None]

        def thu(nhan, view, p0, p1, refs):
            if len(refs) < 2:
                dim_kq.append(u"%s: thiếu reference" % nhan)
                return
            try:
                tao_dim(doc, view, p0, p1, refs)
                dim_kq.append(u"%s: OK" % nhan)
            except Exception as ex:
                dim_kq.append(u"%s: lỗi (%s)" % (nhan, u"%s" % ex))
        if lk:
            # Cửa trong file link: dim vào reference của link bị Revit bỏ khi regenerate (thử Site HQV 2026-11-11: tạo
            # được rồi mất hết) → bám nét ẩn (Invisible lines) đặt đúng mép / đỉnh / bậu cửa, số đo giữ nguyên
            gs_vo = None
            try:
                gs_vo = Category.GetCategory(doc, BuiltInCategory.OST_InvisibleLines).GetGraphicsStyle(GraphicsStyleType.Projection)
            except Exception:
                pass

            def na(view, q0, q1):
                c_ = doc.Create.NewDetailCurve(view, Line.CreateBound(q0, q1))
                if gs_vo is not None:
                    c_.LineStyle = gs_vo
                return c_.GeometryCurve.Reference
            g_mb = XYZ(P.X, P.Y, z_lv)
            r_trai = na(v_mb, g_mb + H * h_tr + N * smin, g_mb + H * h_tr + N * smax)
            r_phai = na(v_mb, g_mb + H * h_ph + N * smin, g_mb + H * h_ph + N * smax)
            x_tr, x_ph = sorted([(P + H * h_tr - O_d).DotProduct(X_d), (P + H * h_ph - O_d).DotProduct(X_d)])
            dz = lambda z_: UP * (z_ - O_d.Z)
            r_md = {"trai": na(v_md, O_d + X_d * x_tr + dz(zmin), O_d + X_d * x_tr + dz(zmax)),
                    "phai": na(v_md, O_d + X_d * x_ph + dz(zmin), O_d + X_d * x_ph + dz(zmax)),
                    "tren": na(v_md, O_d + X_d * x_tr + dz(z_dinh), O_d + X_d * x_ph + dz(z_dinh)),
                    "duoi": na(v_md, O_d + X_d * x_tr + dz(z_bau), O_d + X_d * x_ph + dz(z_bau)) if la_cua_so else None}
            dzc = lambda z_: UP * (z_ - O_c.Z)
            r_tren = na(v_mc, O_c + X_c * smin + dzc(z_dinh), O_c + X_c * smax + dzc(z_dinh))
            r_duoi = na(v_mc, O_c + X_c * smin + dzc(z_bau), O_c + X_c * smax + dzc(z_bau)) if la_cua_so else None
            nguon_w += u" – nét ẩn đặt tại mép cửa trong link"
        wr = [r for r in (r_trai, r_phai) if r is not None]
        # mặt bằng: dim rộng phía ngoài nhà
        q = P + N * (smax_mb + le * 0.25)
        thu(u"MB rộng (%s)" % nguon_w, v_mb, XYZ(q.X, q.Y, z_lv) + H * (hmin - le), XYZ(q.X, q.Y, z_lv) + H * (hmax + le), wr)
        # mặt đứng: rộng dưới CHÂN (dưới đầu ký hiệu mặt cắt), cao bên phải
        q = XYZ(O_d.X, O_d.Y, z_dim1)
        thu(u"MĐ rộng", v_md, q - X_d * (rong + le), q + X_d * (rong + le),
            [r for r in (r_md["trai"], r_md["phai"]) if r is not None])
        x_ph = max(a, b) + le * 0.5
        q = O_d + X_d * x_ph
        thu(u"MĐ cao (%s)" % nguon_h, v_md, XYZ(q.X, q.Y, z_lo), XYZ(q.X, q.Y, z_hi), chuoi_h("md"))
        q = O_c + X_c * (b2 + le * 0.5)
        thu(u"MC cao", v_mc, XYZ(q.X, q.Y, z_lo), XYZ(q.X, q.Y, z_hi), chuoi_h("mc"))
        p(u"   Kích thước: %s." % u"; ".join(dim_kq))

    # ---------- Ẩn level (mặt đứng, mặt cắt); mặt đứng chỉ còn cửa: Hide in View mọi phần tử model khác ----------
    giu = set([fi.Id.Value] + [e.Id.Value for e in parts] + [i.Value for i in luoi_ids])   # vách kính: tấm, đố, lưới
    for e in nguon:
        try:
            giu.update(i.Value for i in e.GetSubComponentIds())
        except Exception:
            pass
    try:
        if fi.SuperComponent is not None:
            giu.add(fi.SuperComponent.Id.Value)
    except Exception:
        pass
    lv_cat = int(BuiltInCategory.OST_Levels)
    vw_cat = int(BuiltInCategory.OST_Viewers)          # ký hiệu mặt cắt (vết cắt) trên mặt đứng: giữ
    # mốc khác (mặt phẳng tham chiếu, scope box, lưới trục) ẩn ở cả 3 view: chúng kéo viewport to ra, vượt ô
    moc = set(int(b) for b in (BuiltInCategory.OST_CLines, BuiltInCategory.OST_VolumeOfInterest, BuiltInCategory.OST_Grids))
    for v in (v_mb, v_md, v_mc):
        ds = List[ElementId]()
        for e in FilteredElementCollector(doc, v.Id).WhereElementIsNotElementType():
            try:
                if e.Category is not None and e.Category.Id.Value in moc and e.CanBeHidden(v):
                    ds.Add(e.Id)
            except Exception:
                pass
        if ds.Count:
            v.HideElements(ds)
            p(u"   %s: ẩn %d mặt phẳng tham chiếu / scope box / lưới trục." % (v.Name, ds.Count))
    # level: lấy từ toàn dự án (collector theo view không trả level) → ẩn trên mặt đứng + mặt cắt
    levels = list(FilteredElementCollector(doc).OfClass(Level))
    tuong = int(BuiltInCategory.OST_Walls)
    # mặt đứng: chỉ giữ cửa; mặt bằng: giữ cửa + tường (ẩn sàn, cửa khác, đồ đạc...); mặt cắt: chỉ ẩn level
    for v, nhan, giu_cat in ((v_md, u"Mặt đứng", ()), (v_mb, u"Mặt bằng", (tuong,)), (v_mc, u"Mặt cắt", None)):
        ds = List[ElementId]()
        so_lv = 0
        if v is not v_mb:
            try:        # tắt cả hạng mục Levels của view (bắt cả level của file link); template điều khiển thì bỏ qua
                if not v.GetCategoryHidden(ElementId(BuiltInCategory.OST_Levels)):
                    v.SetCategoryHidden(ElementId(BuiltInCategory.OST_Levels), True)
            except Exception:
                pass
            for l in levels:
                try:
                    if l.CanBeHidden(v) and not l.IsHidden(v):
                        ds.Add(l.Id)
                        so_lv += 1
                except Exception:
                    pass
        if giu_cat is not None:
            for e in FilteredElementCollector(doc, v.Id).WhereElementIsNotElementType():
                c = e.Category
                if c is None or e.Id.Value in giu or e.ViewSpecific:      # nét cốt sàn, dim, chữ của view: giữ
                    continue
                if c.CategoryType != CategoryType.Model or c.Id.Value in giu_cat or c.Id.Value in (lv_cat, vw_cat):
                    continue
                try:
                    if e.CanBeHidden(v):
                        ds.Add(e.Id)
                except Exception:
                    pass
        if ds.Count:
            v.HideElements(ds)
        p(u"   %s: ẩn %d level%s." % (nhan, so_lv, u" + %d phần tử khác (giữ cửa%s)" % (
            ds.Count - so_lv, u" + tường" if giu_cat else u"") if giu_cat is not None else u""))
    doc.Regenerate()
    dung_lai = []
    for d, nhan, view, p0, p1, du_phong in dim_vk:
        if du_phong is None:
            continue
        # dim bám phần tử vừa Hide in View: Revit ẩn theo (vẫn IsValidObject) hoặc xoá → kiểm bằng collector của view
        if d.IsValidObject and any(x.Id.Value == d.Id.Value for x in
                                   FilteredElementCollector(doc, view.Id).OfClass(Dimension)):
            continue
        try:
            if d.IsValidObject:
                doc.Delete(d.Id)            # dim công cụ vừa tạo trong lượt này, đã không hiện → thay bằng dim nét ẩn
            tao_dim(doc, view, p0, p1, du_phong())
            dung_lai.append(nhan)
        except Exception as ex:
            p(u"   %s: mất sau khi ẩn phần tử, dựng lại theo nét ẩn lỗi (%s)." % (nhan, ex))
    if dung_lai:
        p(u"   Dim mất sau khi ẩn phần tử → dựng lại theo nét ẩn: %s." % u", ".join(dung_lai))
        doc.Regenerate()
    so_dim = {v.Name: sum(1 for _ in FilteredElementCollector(doc, v.Id).OfClass(Dimension)) for v in (v_mb, v_md, v_mc)}
    p(u"   Kích thước còn trong view sau khi ẩn: %s." % u", ".join(u"%s %d" % (k, n) for k, n in so_dim.items()))

    # ---------- Sheet + đặt view ----------
    if chon_sh is None:
        if tb_type is None:
            TransactionManager.Instance.TransactionTaskDone()
            return bao_cao + [u"Dự án không có khung tên nào → đã tạo view, chưa đặt lên sheet."]
        if not tb_type.IsActive:
            tb_type.Activate()
        chon_sh = ViewSheet.Create(doc, tb_type.Id)
        chon_sh.SheetNumber = so_moi
        chon_sh.Name = ten_sh
        for pid, gt_, nhan in ((pid_gd, gd, u"giai đoạn"), (pid_hm, hm, u"hạng mục")):
            if pid is None or not gt_:
                continue
            prm = ts_theo_id(chon_sh, pid)
            if prm is not None and not prm.IsReadOnly:
                prm.Set(gt_)
            else:
                p(u"   Không gán được %s '%s' cho sheet (tham số không ghi được)." % (nhan, gt_))
        doc.Regenerate()
        tb = list(FilteredElementCollector(doc, chon_sh.Id).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsNotElementType())[0]
        vung = vung_ve(doc, chon_sh, tb, p)
        chon_o = 0
        trai, duoi, phai, tren = vung
        trong_khoi = set(o_khoi)                 # khối ghép của vách kính: không vẽ nét chia bên trong
        nets = []
        for c in range(1, SO_COT):               # nét đứng chia cột, từng hàng
            for r in range(SO_HANG):
                if r * SO_COT + c - 1 in trong_khoi and r * SO_COT + c in trong_khoi:
                    continue
                _, y0, x0, y1 = o_luoi(vung, r * SO_COT + c - 1)
                nets.append((XYZ(x0, y0, 0), XYZ(x0, y1, 0)))
        for r in range(1, SO_HANG):              # nét ngang chia hàng, từng cột
            for c in range(SO_COT):
                if (r - 1) * SO_COT + c in trong_khoi and r * SO_COT + c in trong_khoi:
                    continue
                x0, y0, x1, _ = o_luoi(vung, r * SO_COT + c - SO_COT)
                nets.append((XYZ(x0, y0, 0), XYZ(x1, y0, 0)))
        for k in range(SO_COT * SO_HANG):        # dải thông tin: mỗi ô 1 nét; khối ghép 1 nét dưới hàng cuối khối
            if k in trong_khoi and len(o_khoi) > 1:
                continue
            x0, y0, x1, y1 = o_luoi(vung, k)
            y = y0 + (y1 - y0) * TI_LE_DAI_TT
            nets.append((XYZ(x0, y, 0), XYZ(x1, y, 0)))
        if len(o_khoi) > 1:
            x0, y0, _, y1 = o_luoi(vung, o_khoi[-1] - (khoi[0] - 1))
            x1 = o_luoi(vung, o_khoi[-1])[2]
            y = y0 + (y1 - y0) * TI_LE_DAI_TT
            nets.append((XYZ(x0, y, 0), XYZ(x1, y, 0)))
        ids = List[ElementId]()
        for a0, a1 in nets:
            ids.Add(doc.Create.NewDetailCurve(chon_sh, Line.CreateBound(a0, a1)).Id)
        g = doc.Create.NewGroup(ids)
        try:
            g.GroupType.Name = u"%s %s" % (NHOM_LUOI, so_moi)
        except Exception:
            pass
        p(u"   Sheet %s: vùng vẽ %.0f × %.0f mm, lưới 6 ô (group '%s %s')." % (
            so_moi, mm(phai - trai), mm(tren - duoi), NHOM_LUOI, so_moi))
    x0, _, _, y1 = o_luoi(vung, chon_o)          # khối ô: góc trên trái = ô đầu, góc dưới phải = ô cuối
    _, y0, x1, y1d = o_luoi(vung, chon_o + (khoi[1] - 1) * SO_COT + khoi[0] - 1)
    y0v = y0 + (y1d - y0) * TI_LE_DAI_TT         # vùng đặt view (trên dải thông tin của hàng cuối khối)
    cx, cy = (x0 + x1) / 2.0, (y0v + y1) / 2.0
    vps = {}
    for k in ("md", "mc", "mb"):
        if not Viewport.CanAddViewToSheet(doc, chon_sh.Id, vs[k].Id):
            p(u"   Không đặt được view '%s' lên sheet." % vs[k].Name)
            continue
        vps[k] = Viewport.Create(doc, chon_sh.Id, vs[k].Id, XYZ(cx, cy, 0))
    kieu_vp = None
    for vp in vps.values():
        kieu_vp = next((t for t in vp.GetValidTypes() if ten(doc.GetElement(t)) == KIEU_VIEWPORT), None)
        break
    if kieu_vp is not None:
        for vp in vps.values():
            if vp.GetTypeId().Value != kieu_vp.Value:
                vp.ChangeTypeId(kieu_vp)
    elif vps:
        p(u"   Không có kiểu viewport '%s' → giữ kiểu mặc định." % KIEU_VIEWPORT)
    if "mc" in vps:     # đầu ký hiệu section trên mặt đứng hiện số chi tiết của mặt cắt → tên "MẶT CẮT n-n" cho khớp
        try:
            dn = vps["mc"].get_Parameter(BuiltInParameter.VIEWPORT_DETAIL_NUMBER).AsString()
            if dn:
                v_mc.get_Parameter(BuiltInParameter.VIEW_DESCRIPTION).Set(u"MẶT CẮT %s-%s" % (dn, dn))
        except Exception as ex:
            p(u"   Không đặt được tên mặt cắt theo số chi tiết (%s)." % ex)
    doc.Regenerate()

    def len_sheet(vp, view, q):
        tr = list(view.GetModelToProjectionTransforms())[0].GetModelToProjectionTransform()
        return vp.GetProjectionToSheetTransform().OfPoint(tr.OfPoint(q))

    def hop_ht(k):
        """(x0, y0, x1, y1) phần THẤY ĐƯỢC của viewport trên sheet. Mặt đứng: khung crop + 3 mm chú thích – hộp viewport
        Revit tính cả hộp bao ký hiệu mặt cắt (vết cắt), vượt khung ~8 mm giấy mỗi đầu mà không in ra (thử 2026-11-04)."""
        o = vps[k].GetBoxOutline()
        hop_vp = (o.MinimumPoint.X, o.MinimumPoint.Y, o.MaximumPoint.X, o.MaximumPoint.Y)
        if k != "md":
            return hop_vp
        try:
            cb = v_md.CropBox
            g_ = [len_sheet(vps[k], v_md, cb.Transform.OfPoint(XYZ(xx, yy, cb.Min.Z)))
                  for xx in (cb.Min.X, cb.Max.X) for yy in (cb.Min.Y, cb.Max.Y)]
            return (max(min(q.X for q in g_) - ft(3), hop_vp[0]), max(min(q.Y for q in g_) - ft(3), hop_vp[1]),
                    min(max(q.X for q in g_) + ft(3), hop_vp[2]), min(max(q.Y for q in g_) + ft(3), hop_vp[3]))
        except Exception:
            return hop_vp

    def dat_tam(k, cx_, cy_):
        """Đặt viewport sao cho TÂM phần thấy được nằm ở (cx_, cy_)."""
        h_ = hop_ht(k)
        vps[k].SetBoxCenter(vps[k].GetBoxCenter() + XYZ(cx_ - (h_[0] + h_[2]) / 2.0, cy_ - (h_[1] + h_[3]) / 2.0, 0))

    def kt(k):
        h_ = hop_ht(k)
        return h_[2] - h_[0], h_[3] - h_[1]

    if len(vps) == 3:
        gap, gap_td = ft(12), ft(14)            # khoảng hở giữa view / chỗ tên view dưới mỗi view
        (wd, hd), (wc, hc2), (wb, hb) = kt("md"), kt("mc"), kt("mb")
        cot_a = max(wd, wb)
        tong_w = cot_a + gap + wc
        tong_h = hd + gap_td + hb + gap_td
        xl = x0 + max((x1 - x0 - tong_w) / 2.0, ft(5))
        yt = y1 - max((y1 - y0v - tong_h) / 2.0, ft(5))
        dat_tam("md", xl + cot_a / 2.0, yt - hd / 2.0)
        dat_tam("mc", xl + cot_a + gap + wc / 2.0, yt - hc2 / 2.0)
        dat_tam("mb", xl + cot_a / 2.0, yt - hd - gap_td - hb / 2.0)
        doc.Regenerate()
        # Gióng: sàn mặt cắt ngang sàn mặt đứng; tâm cửa mặt bằng thẳng tâm cửa mặt đứng
        try:
            yd = len_sheet(vps["md"], v_md, XYZ(tam.X, tam.Y, z_lv)).Y
            yc = len_sheet(vps["mc"], v_mc, XYZ(tam.X, tam.Y, z_lv)).Y
            vps["mc"].SetBoxCenter(vps["mc"].GetBoxCenter() + XYZ(0, yd - yc, 0))
            if abs(X_d.DotProduct(v_mb.RightDirection)) > 0.99:
                xd = len_sheet(vps["md"], v_md, tam).X
                xb = len_sheet(vps["mb"], v_mb, tam).X
                vps["mb"].SetBoxCenter(vps["mb"].GetBoxCenter() + XYZ(xd - xb, 0, 0))
        except Exception as ex:
            p(u"   Không gióng được view theo sàn / tâm cửa (%s)." % ex)
        doc.Regenerate()
        # tên view đặt theo đáy hộp viewport → mặt đứng (hộp to hơn phần thấy) dời tên lên sát phần thấy
        for k in vps:
            try:
                h_ = hop_ht(k)
                o = vps[k].GetBoxOutline()
                dx_, dy_ = h_[0] - o.MinimumPoint.X, h_[1] - o.MinimumPoint.Y
                if dx_ > ft(0.5) or dy_ > ft(0.5):
                    vps[k].LabelOffset = vps[k].LabelOffset + XYZ(dx_, dy_, 0)
            except Exception as ex:
                p(u"   Không dời được tên view %s (%s)." % (vs[k].Name, ex))
        doc.Regenerate()
        # Nét đứt cốt sàn hoàn thiện chạy suốt bề rộng ô (như mẫu), vẽ trên sheet tại cao độ sàn của mặt đứng
        # (mặt cắt đã gióng cùng cao độ); nét sàn trong từng view chỉ để dim bám vào (nét ẩn)
        try:
            tr_d = list(v_md.GetModelToProjectionTransforms())[0].GetModelToProjectionTransform()
            y_san = vps["md"].GetProjectionToSheetTransform().OfPoint(tr_d.OfPoint(XYZ(tam.X, tam.Y, z_cot))).Y
            net = doc.Create.NewDetailCurve(chon_sh, Line.CreateBound(XYZ(x0, y_san, 0), XYZ(x1, y_san, 0)))
            if gs_dut is not None:
                net.LineStyle = gs_dut
        except Exception as ex:
            p(u"   Không vẽ được nét cốt sàn trên sheet (%s)." % ex)
        vuot =tong_w > x1 - x0 or tong_h > y1 - y0v
        p(u"   Đặt 3 view vào %s: cụm %.0f × %.0f mm, vùng đặt view %.0f × %.0f mm%s." % (
            ten_o, mm(tong_w), mm(tong_h), mm(x1 - x0), mm(y1 - y0v), u" – VƯỢT Ô, cần xếp lại tay" if vuot else u""))
    TransactionManager.Instance.TransactionTaskDone()
    p(u"Xong: sheet %s - %s, %s. Phần trống dưới ô để điền ký hiệu, kích thước, vật liệu, phụ kiện." % (
        chon_sh.SheetNumber, chon_sh.Name, ten_o))
    SHEET_CUOI[0] = chon_sh
    return bao_cao


def _chay():
    """Làm lần lượt mọi cửa đã chọn (người dùng yêu cầu 2026-11-03: chọn nhiều cửa trước rồi bấm nút). Ở nút pyRevit cả
    lượt gom trong 1 TransactionGroup → Ctrl+Z một lần là hoàn tác hết."""
    doc = DocumentManager.Instance.CurrentDBDocument
    uidoc = DocumentManager.Instance.CurrentUIDocument
    ds, kq = lay_cua(doc, uidoc)
    if not ds:
        return kq + [u"Chưa chọn cửa đi / cửa sổ / vách kính nào. Chọn các đối tượng cần làm chi tiết rồi bấm lại."]
    # Đọc sẵn nét khung tên (mở family) trước khi có transaction / transaction group
    tb_type, _ = tim_khung(doc, (doc_in(1) or u"").strip())
    if tb_type is not None:
        doc_net_khung(doc, tb_type, kq.append)
    for s in FilteredElementCollector(doc).OfClass(ViewSheet):
        if any(ten(g.GroupType).startswith(NHOM_LUOI) for g in FilteredElementCollector(doc, s.Id).OfClass(Group)):
            for tb in FilteredElementCollector(doc, s.Id).OfCategory(BuiltInCategory.OST_TitleBlocks) \
                    .WhereElementIsNotElementType():
                doc_net_khung(doc, doc.GetElement(tb.GetTypeId()), kq.append)
    kq.append(u"Số cửa / vách kính đã chọn: %d." % len(ds))
    nhom = None
    if not bool(doc_in(14)) and hasattr(TransactionManager.Instance, "rollback_open"):     # chạy trong nút pyRevit
        nhom = TransactionGroup(doc, TRANSACTION_NAME)
        nhom.Start()
    try:
        for i, fi in enumerate(ds, 1):
            kq.append(u"===== %d/%d" % (i, len(ds)))
            kq.extend(_chinh(fi))
            TransactionManager.Instance.ForceCloseTransaction()
    except Exception:
        if nhom is not None:
            try:
                TransactionManager.Instance.rollback_open()
            except Exception:
                pass
            nhom.RollBack()
            nhom = None
            kq.append(u"Có lỗi → đã hoàn tác toàn bộ lượt này.")
        raise
    finally:
        if nhom is not None and nhom.GetStatus() == TransactionStatus.Started:
            nhom.Assimilate()
    if bool(doc_in(15)) and not bool(doc_in(14)) and SHEET_CUOI[0] is not None and uidoc is not None:
        try:
            uidoc.RequestViewChange(SHEET_CUOI[0])
        except Exception:
            pass
    return kq


try:
    OUT = _chay()
except Exception:
    OUT = [u"LỖI:", traceback.format_exc()]
