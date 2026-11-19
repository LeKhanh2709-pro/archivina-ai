# Tạo lỗ mở bằng MỘT Shaft Opening cho mọi trục / hộp kỹ thuật trên mặt bằng tầng đang mở của Revit (mỗi ô là một vòng
# biên trong sketch, như mẫu người dùng vẽ 2026-10-28: 1 lệnh shaft để dễ kiểm soát).
# Nhận trục / hộp đúng theo quy tắc của công cụ Ngăn cháy lan (dùng chung hàm tim_truc): tên room HKT → shaft opening
# → ống đứng → hình học (ô / khe kín giữa tường không cửa đi, cửa sổ, thiết bị, sàn hoàn thiện); loại thang máy / thang bộ.
#   - Biên lỗ mở = mép tường thô (dải lõi tường), không bo vào lớp trát / hoàn thiện (người dùng chốt 2026-10-28)
#   - Base Constraint = Top Constraint = level của mặt bằng đang mở; Base Offset -100 mm, Top Offset 1500 mm (mặc định,
#     người dùng chốt 2026-10-28)
#   - Tầng đã có shaft lỗ mở cục bộ (Base và Top cùng là level đó) thì thêm vòng vào shaft đó (shaft nhiều vòng nhất),
#     chưa có thì tạo 1 shaft mới. Ô đã có vòng lỗ mở thì bỏ qua: bấm lại không tạo trùng, không xoá.
#   - Dấu X nhận biết lỗ mở = 2 Symbolic Line mỗi vòng (người dùng chốt 2026-10-28). API không tạo được Symbolic Line
#     trong file dự án → chép 2 nét X của một shaft MẪU (nét sketch mang line style khác "<Sketch>", người dùng vẽ tay
#     một lần) rồi kéo về 2 đường chéo; vòng đã có trong shaft mà chưa có X cũng được bổ sung. Chưa có mẫu thì báo.
#   - Thêm vòng + dấu X nằm trong 1 lần sửa sketch (1 bước Undo); tạo shaft mới là 1 bước Undo riêng.
# Dry-run (mặc định) chỉ báo cáo, không sửa mô hình.
# INPUT
#   IN[0] (str)   Tên view mặt bằng (để trống = view đang mở, phải là mặt bằng tầng)
#   IN[1] (str)   Từ khoá tên room là trục / hộp kỹ thuật, cách nhau bằng ;  (không phân biệt dấu / hoa thường)
#   IN[2] (float) Diện tích lớn nhất của ô / khe kín nhận theo hình học (m2)
#   IN[3] (float) Bề rộng lòng nhỏ nhất của ô / khe (mm)
#   IN[4] (bool)  Dry-run (True = chỉ báo cáo)
#   IN[5] (str)   Thư mục ghi log + ảnh (để trống = Documents\ARV_Logs\lo_mo)
#   IN[6] (str)   Từ khoá loại trừ (thang máy, thang bộ) trong tên family / type / room, cách nhau bằng ;
#   IN[7] (float) Base Offset của lỗ mở (mm)
#   IN[8] (float) Top Offset của lỗ mở (mm)
#   IN[9] (bool)  Gắn dấu X (Symbolic Line chép từ shaft mẫu) cho mọi vòng lỗ mở chưa có X
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
# pythonnet 3.0: tên đã được import đích danh trước đó trong phiên (vd. ở script khác) bị loại khỏi "import *"
# → bổ sung đủ tên của namespace để không phụ thuộc thứ tự import
globals().update({_n: getattr(_RevitDB, _n) for _n in dir(_RevitDB) if not _n.startswith("_") and _n not in globals()})
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager
from System.Collections.Generic import List as NetList
# File gộp tự động bằng gop_lomo_shaft.py – KHÔNG sửa tay (sửa LoMo_ShaftOpening_nguon.py / NganChay_TrucHKT.py rồi gộp lại).


def ds_id(ids):
    """List[ElementId] tạo rỗng rồi Add (pythonnet của pyRevit không nhận List[T](list Python))"""
    kq = NetList[ElementId]()
    for i in ids:
        kq.Add(i)
    return kq


doc = DocumentManager.Instance.CurrentDBDocument


def gia_tri(i, mac_dinh):
    try:
        v = IN[i]
        return mac_dinh if v is None or (isinstance(v, str) and not v.strip()) else v
    except Exception:
        return mac_dinh


def tach(s):
    return [k.strip() for k in str(s).split(";") if k.strip()]


TEN_VIEW = gia_tri(0, "")
TU_KHOA_HKT = tach(gia_tri(1, "HKT;Hộp kỹ thuật;Trục kỹ thuật;Giếng kỹ thuật;Shaft"))
DT_MAX_M2 = float(gia_tri(2, 3.0))
RONG_MIN_MM = float(gia_tri(3, 80.0))
DRY_RUN = bool(gia_tri(4, True))
THU_MUC = str(gia_tri(5, os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs", "lo_mo")))
TU_KHOA_LOAI = tach(gia_tri(6, "Thang máy;Elevator;Lift;Thang bộ;Stair"))
BASE_OFFSET_MM = float(gia_tri(7, -100.0))
TOP_OFFSET_MM = float(gia_tri(8, 1500.0))
GAN_X = bool(gia_tri(9, True))
os.makedirs(THU_MUC, exist_ok=True)

# hằng số nhận trục (chép nguyên từ NganChay_TrucHKT.py khi gộp)
O_LON_MM = 1400.0         # ô lớn hơn 1400 x 1400 mm: vẫn hatch, liệt kê để xem lại
# Dải dài hẹp chỉ nhận theo hình học (không tên room, không ống / shaft / dấu X): khe giữa tường kiến trúc và vách lõi,
# không phải trục (HQV Site 2026-11-11: dải 595 × 4950 dọc lõi thang). Trục / hộp thật dài nhất đo được ~2,6 m.
KHE_DAI_MM = 3000.0
KHE_HEP_MM = 600.0
DT_NHO_NHAT_M2 = 0.01     # ô nhỏ hơn coi là khe giữa 2 lớp tường (0,03 làm sót hộp ống 150 x 150 lõi–lõi: G19_A_L3-32 2026-11-04)
O_LUOI_MM = 20.0          # cạnh ô lưới quét dấu chân tường
LOI_MONG_MM = 30.0        # tường có lõi mỏng hơn (gạch ốp, lớp gỗ…) là lớp hoàn thiện → không coi là vách
NOI_HO_MM = 400.0         # đầu tường hở cách tường khác tới mức này thì nối (như Revit khép room)
DT_CO_BANG_CHUNG_M2 = 30.0   # ô có ống đứng / shaft opening: nhận tới diện tích này
TU_LAYER_X = ("lo mo", "lomo", "material", "truc", "hkt", "shaft", "mep", "ky thuat")  # layer CAD có dấu X trục / lỗ mở
TU_LAYER_BO = ("hatch", "hidden", "khuat", "center", "thang", "elev", "lift", "interior", "noi that")
SO_X_CAD_TIN = 3          # CAD có từ chừng này dấu X trở lên: ô chỉ có hình học mà không có dấu X thì không vẽ, liệt kê
TU_SAN_KC = ("sbt", "ket cau", "btct", "structural")   # sàn kết cấu: không dùng để loại ô
bao_cao = []


# ==== PHẦN CHUNG: nhận trục / hộp kỹ thuật (dùng chung với LoMo_ShaftOpening.py – file gộp bằng gop_lomo_shaft.py) ====
def mm(v):
    return UnitUtils.ConvertToInternalUnits(v, UnitTypeId.Millimeters)


def ra_mm(v):
    return UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.Millimeters)


def ra_m2(v):
    return UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.SquareMeters)


def khong_dau(s):
    s = unicodedata.normalize("NFD", s or "").replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def co_tu(s, tu_khoa):
    s = khong_dau(s)
    return any(khong_dau(k) in s for k in tu_khoa)


def ten(e):
    try:
        return e.Name
    except Exception:
        return "?"


def ten_kieu(e):
    t = e.Document.GetElement(e.GetTypeId())
    return ten(t) if t is not None else ""


def ten_family(e):
    try:
        return e.Symbol.FamilyName
    except Exception:
        return ten_kieu(e)


def ten_tpl(v):
    return ten(doc.GetElement(v.ViewTemplateId)) if v.ViewTemplateId != ElementId.InvalidElementId else ""


# ---------- chọn view ----------
def chon_view():
    plans = [v for v in FilteredElementCollector(doc).OfClass(ViewPlan) if not v.IsTemplate]
    if TEN_VIEW:
        for v in plans:
            if v.Name == TEN_VIEW:
                return v
        raise Exception("Không tìm thấy view mặt bằng tên '%s'" % TEN_VIEW)
    la_cl = [v for v in plans if "chay lan" in khong_dau(ten_tpl(v)) or "chay lan" in khong_dau(v.Name)]
    av = doc.ActiveView
    for v in la_cl:
        if v.Id == av.Id:
            return v
    if not la_cl:
        raise Exception("Không có view mặt bằng nào có chữ 'cháy lan' trong tên view / template; nhập tên view vào IN[0]")
    return la_cl[0]


# ---------- hình học 2D ----------
def diem_loop(curves):
    pts = []
    for c in curves:
        for p in list(c.Tessellate())[:-1]:
            pts.append((p.X, p.Y))
    return pts


def trong_da_giac(x, y, pts):
    ben_trong = False
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            ben_trong = not ben_trong
    return ben_trong


def trong_vung(x, y, loops_pts):
    # điểm nằm trong số lẻ vòng biên = nằm trong vùng (vòng ngoài trừ lỗ)
    return sum(1 for pts in loops_pts if trong_da_giac(x, y, pts)) % 2 == 1


def bao_loi(pts):
    """Bao lồi (monotone chain)"""
    p = sorted(set(pts))
    if len(p) < 3:
        return p

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    duoi, tren = [], []
    for q in p:
        while len(duoi) >= 2 and cross(duoi[-2], duoi[-1], q) <= 0:
            duoi.pop()
        duoi.append(q)
    for q in reversed(p):
        while len(tren) >= 2 and cross(tren[-2], tren[-1], q) <= 0:
            tren.pop()
        tren.append(q)
    return duoi[:-1] + tren[:-1]


def kich_thuoc(pts):
    """(bề rộng nhỏ nhất, chiều dài theo phương đó) của bao lồi – đo đúng cả ô xoay xiên"""
    h = bao_loi(pts)
    if len(h) < 3:
        return 0.0, 0.0
    tot = None
    for i in range(len(h)):
        (x1, y1), (x2, y2) = h[i], h[(i + 1) % len(h)]
        L = math.hypot(x2 - x1, y2 - y1)
        if L < 1e-9:
            continue
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        rong = max(abs((x - x1) * uy - (y - y1) * ux) for x, y in h)
        dai = max((x - x1) * ux + (y - y1) * uy for x, y in h) - min((x - x1) * ux + (y - y1) * uy for x, y in h)
        if tot is None or rong < tot[0]:
            tot = (rong, dai)
    return tot


def phang(c, z):
    return c.CreateTransformed(Transform.CreateTranslation(XYZ(0, 0, z - c.GetEndPoint(0).Z)))


def diem_tam(e):
    """Điểm đặt trên mặt bằng của đối tượng: Location.Point, không có thì tâm khung bao"""
    try:
        p = e.Location.Point
        return (p.X, p.Y)
    except Exception:
        bb = e.get_BoundingBox(None)
        if bb is None:
            return None
        return ((bb.Min.X + bb.Max.X) / 2, (bb.Min.Y + bb.Max.Y) / 2)


def diem_hai_ben(d):
    """2 điểm dò hai bên cửa đi / cửa sổ (qua bề dày tường + 200 mm)"""
    try:
        p = d.Location.Point
        f = d.FacingOrientation
        k = (d.Host.Width if d.Host is not None else mm(200)) / 2 + mm(200)
        return [(p.X + f.X * k, p.Y + f.Y * k), (p.X - f.X * k, p.Y - f.Y * k)]
    except Exception:
        return []


VIEW_LINK = []       # view đang xét, để đọc đối tượng trong file link


def theo_level(cat, lv):
    kq = list(lk_tang(doc, VIEW_LINK[0], cat)) if VIEW_LINK else []
    for e in FilteredElementCollector(doc).OfCategory(cat).WhereElementIsNotElementType():
        lid = e.LevelId
        if lid == ElementId.InvalidElementId:
            try:
                lid = e.get_Parameter(BuiltInParameter.INSTANCE_SCHEDULE_ONLY_LEVEL_PARAM).AsElementId()
            except Exception:
                pass
        if lid == lv.Id:
            kq.append(e)
    return kq


def vong_san(f):
    """Các vòng biên của sàn (theo sketch), điểm 2D"""
    try:
        sk = f.Document.GetElement(f.SketchId)
        tf = f._tf if la_link(f) else Transform.Identity
        return [[(q.X, q.Y) for c in arr for q in (tf.OfPoint(p) for p in list(c.Tessellate())[:-1])] for arr in sk.Profile]
    except Exception:
        return []


def la_san_ket_cau(f):
    if co_tu(ten_kieu(f), TU_SAN_KC):
        return True
    try:
        return f.get_Parameter(BuiltInParameter.FLOOR_PARAMETER_IS_STRUCTURAL).AsInteger() == 1
    except Exception:
        return False


def ong_dung(lv):
    """Điểm 2D của ống / ống gió / ống luồn dây / máng cáp đi đứng qua cao độ level"""
    z = lv.Elevation
    kq = []
    for cat in (BuiltInCategory.OST_PipeCurves, BuiltInCategory.OST_DuctCurves, BuiltInCategory.OST_Conduit,
                BuiltInCategory.OST_CableTray):
        for e in FilteredElementCollector(doc).OfCategory(cat).WhereElementIsNotElementType():
            try:
                c = e.Location.Curve
                a, b = c.GetEndPoint(0), c.GetEndPoint(1)
            except Exception:
                continue
            dz = abs(b.Z - a.Z)
            if dz > 2 * math.hypot(b.X - a.X, b.Y - a.Y) and min(a.Z, b.Z) - mm(500) <= z + mm(1000) <= max(a.Z, b.Z) + mm(500):
                kq.append(((a.X + b.X) / 2, (a.Y + b.Y) / 2))
    for li, ld, tf in (lk_cac_link(doc, VIEW_LINK[0]) if VIEW_LINK else []):       # ống đứng trong file link (MEP link)
        for cat in (BuiltInCategory.OST_PipeCurves, BuiltInCategory.OST_DuctCurves, BuiltInCategory.OST_Conduit,
                    BuiltInCategory.OST_CableTray):
            for e in FilteredElementCollector(ld).OfCategory(cat).WhereElementIsNotElementType():
                try:
                    c = e.Location.Curve
                    a, b = tf.OfPoint(c.GetEndPoint(0)), tf.OfPoint(c.GetEndPoint(1))
                except Exception:
                    continue
                dz = abs(b.Z - a.Z)
                if dz > 2 * math.hypot(b.X - a.X, b.Y - a.Y) and min(a.Z, b.Z) - mm(500) <= z + mm(1000) <= max(a.Z, b.Z) + mm(500):
                    kq.append(((a.X + b.X) / 2, (a.Y + b.Y) / 2))
    return kq


# ---------- kiểu thể hiện ----------
def lay_line_style():
    cat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Lines)
    for sc in cat.SubCategories:
        if sc.Name == TEN_NET:
            return sc.GetGraphicsStyle(GraphicsStyleType.Projection), "dùng line style có sẵn '%s'" % TEN_NET
    if DRY_RUN:
        return None, "sẽ tạo line style '%s' (màu %d,%d,%d)" % ((TEN_NET,) + MAU_VIEN)
    sc = doc.Settings.Categories.NewSubcategory(cat, TEN_NET)
    sc.LineColor = Color(*MAU_VIEN)
    sc.SetLineWeight(1, GraphicsStyleType.Projection)
    return sc.GetGraphicsStyle(GraphicsStyleType.Projection), "đã tạo line style '%s' (màu %d,%d,%d)" % ((TEN_NET,) + MAU_VIEN)


def lay_mau_luoi():
    for p in FilteredElementCollector(doc).OfClass(FillPatternElement):
        if ten(p) == TEN_MAU_LUOI:
            return p.Id, "dùng mẫu có sẵn '%s'" % TEN_MAU_LUOI
    if DRY_RUN:
        return None, "sẽ tạo mẫu model '%s' (lưới %g mm, %g°)" % (TEN_MAU_LUOI, LUOI_MM, LUOI_GOC)
    fp = FillPattern(TEN_MAU_LUOI, FillPatternTarget.Model, FillPatternHostOrientation.ToView,
                     math.radians(LUOI_GOC), mm(LUOI_MM), mm(LUOI_MM))
    pe = FillPatternElement.Create(doc, fp)
    return pe.Id, "đã tạo mẫu model '%s' (lưới %g mm, %g°)" % (TEN_MAU_LUOI, LUOI_MM, LUOI_GOC)


def lay_kieu_hatch():
    for t in FilteredElementCollector(doc).OfClass(FilledRegionType):
        if ten(t) == TEN_HATCH:
            return t, "dùng kiểu có sẵn '%s'" % TEN_HATCH
    pid, ghi_chu = lay_mau_luoi()
    if DRY_RUN:
        return None, "sẽ tạo kiểu '%s' (màu %d,%d,%d); %s" % ((TEN_HATCH,) + MAU_HATCH + (ghi_chu,))
    goc = FilteredElementCollector(doc).OfClass(FilledRegionType).FirstElement()
    t = goc.Duplicate(TEN_HATCH)
    t.ForegroundPatternId = pid
    t.ForegroundPatternColor = Color(*MAU_HATCH)
    t.BackgroundPatternId = ElementId.InvalidElementId
    t.IsMasking = False
    return t, "đã tạo kiểu '%s' (màu %d,%d,%d); %s" % ((TEN_HATCH,) + MAU_HATCH + (ghi_chu,))


def gom_nhom(ids, ten_goc):
    """Gom phần tử vào Detail Group, đặt tên kiểu group (trùng thì thêm _2, _3…)"""
    g = doc.Create.NewGroup(ds_id(ids))
    ten_nhom = ten_goc
    da_dung = set(ten(t) for t in FilteredElementCollector(doc).OfClass(GroupType))
    i = 1
    while ten_nhom in da_dung:
        i += 1
        ten_nhom = "%s_%d" % (ten_goc, i)
    doc.GetElement(g.GetTypeId()).Name = ten_nhom
    return ten_nhom


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
    """Room trong link tại điểm p (toạ độ model chính), CHỈ room thuộc tầng của view → LkPT hoặc None. (Link đặt chồng nhiều
    bản lệch cao độ: bản khác tầng cũng trả room tại điểm đó → biên phòng sai, đo trên HQV Site 2026-11-11: 3 phòng xiên.)"""
    lv = view.GenLevel
    for li, ld, tf in lk_cac_link(doc, view):
        ids = lk_level_khop(ld, tf, lv) if lv is not None else None
        if ids is not None and not ids:
            continue
        try:
            r = ld.GetRoomAtPoint(tf.Inverse.OfPoint(p))
        except Exception:
            r = None
        if r is not None and (ids is None or r.LevelId.Value in ids):
            return LkPT(r, li, tf)
    return None


def lk_room_moi_link(doc, p, lv=None):
    """Room trong bất kỳ link đã nạp tại điểm p (toạ độ model chính) → LkPT hoặc None (không cần view); có lv thì chỉ room
    thuộc tầng lv (link đặt chồng nhiều bản lệch cao độ)."""
    for li in FilteredElementCollector(doc).OfClass(RevitLinkInstance):
        try:
            ld = li.GetLinkDocument()
            if ld is None:
                continue
            tf = li.GetTotalTransform()
            ids = lk_level_khop(ld, tf, lv) if lv is not None else None
            if ids is not None and not ids:
                continue
            r = ld.GetRoomAtPoint(tf.Inverse.OfPoint(p))
            if r is not None and ids is not None and r.LevelId.Value not in ids:
                r = None
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


def lk_an_bang_filter(doc, view, ten_f, bics, giu_tu=()):
    """Ẩn đối tượng trong link theo hạng mục bằng view filter (Revit không Hide in View từng phần tử link): filter tên ten_f,
    hạng mục bics, giữ lại đối tượng có Family Name chứa một chữ trong giu_tu. Filter cũng áp cho đối tượng model chính.
    View có template điều khiển filter thì KHÔNG sửa template, chỉ báo. Gọi TRONG transaction. Trả về câu báo cáo."""
    from System.Collections.Generic import List as _List
    f = None
    for x in FilteredElementCollector(doc).OfClass(ParameterFilterElement):
        if x.Name == ten_f:
            f = x
            break
    if f is None:
        cats = _List[ElementId]()
        for b in bics:
            cats.Add(ElementId(b))
        pid = ElementId(BuiltInParameter.ALL_MODEL_FAMILY_NAME)
        loc_duoc = any(i.Value == pid.Value for i in ParameterFilterUtilities.GetFilterableParametersInCommon(doc, cats))
        luat = _List[FilterRule]()
        if loc_duoc:
            for k in giu_tu:
                luat.Add(ParameterFilterRuleFactory.CreateNotContainsRule(pid, k))
        if luat.Count:
            f = ParameterFilterElement.Create(doc, ten_f, cats, ElementParameterFilter(luat))
        else:
            f = ParameterFilterElement.Create(doc, ten_f, cats)
    tpl = doc.GetElement(view.ViewTemplateId) if view.ViewTemplateId != ElementId.InvalidElementId else None
    if tpl is not None:
        vg = BuiltInParameter.VIS_GRAPHICS_FILTERS
        if not any(i.Value == int(vg) for i in tpl.GetNonControlledTemplateParameterIds()):
            return (u"CẦN XEM LẠI: đối tượng trong link chưa ẩn – template '%s' điều khiển filter (công cụ không sửa template): "
                    u"thêm filter '%s' vào template và tắt hiển thị." % (tpl.Name, ten_f))
    try:
        if not view.IsFilterApplied(f.Id):
            view.AddFilter(f.Id)
        view.SetFilterVisibility(f.Id, False)
        return u"Ẩn đối tượng trong link bằng filter '%s' trong view." % ten_f
    except Exception as ex:
        return u"CẦN XEM LẠI: không gắn được filter '%s' vào view (%s)." % (ten_f, (u"%s" % ex).splitlines()[0][:120])


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


# ---------- quét lưới dấu chân tường ----------
def goc_chinh(tuong):
    """Phương chính của tường (độ, 0–90) theo tổng chiều dài"""
    dem = {}
    for w in tuong:
        try:
            c = w.Location.Curve
            a, b = c.GetEndPoint(0), c.GetEndPoint(1)
        except Exception:
            continue
        L = math.hypot(b.X - a.X, b.Y - a.Y)
        if L > 1e-6:
            g = round(math.degrees(math.atan2(b.Y - a.Y, b.X - a.X)) % 90.0)
            dem[g % 90] = dem.get(g % 90, 0.0) + L
    return max(dem.items(), key=lambda kv: kv[1])[0] if dem else 0.0


def mat_day(e, opt, tf=None):
    """Các mặt đáy (pháp tuyến hướng xuống) của khối đối tượng → list[list[vòng điểm 2D]];
    tf: Transform của file link (toạ độ đưa về model chính)"""
    if tf is not None:
        return [[[(q.X, q.Y) for q in (tf.OfPoint(XYZ(x, y, 0)) for x, y in v)] for v in f] for f in mat_day(e, opt)]
    kq = []
    ds = list(e.get_Geometry(opt) or [])
    while ds:
        g = ds.pop()
        ten_lop = g.GetType().Name
        if ten_lop == "GeometryInstance":
            ds.extend(list(g.GetInstanceGeometry()))
            continue
        if ten_lop != "Solid" or g.Volume <= 0:
            continue
        for f in g.Faces:
            if f.GetType().Name == "PlanarFace" and f.FaceNormal.Z < -0.99:
                vong = [diem_loop(list(cl)) for cl in f.GetEdgesAsCurveLoops()]
                vong = [v for v in vong if len(v) >= 3]
                if vong:
                    kq.append(vong)
    return kq


def loi_tuong(w):
    """Đường tim DẢI LÕI của tường thẳng: (A, B, bề dày lõi, bề dày tường); None nếu tường cong / không có cấu tạo lớp"""
    cv = w.Location.Curve
    if cv.GetType().Name != "Line":
        return None
    cau_tao = w.WallType.GetCompoundStructure()
    if cau_tao is None:
        return None
    lop = list(cau_tao.GetLayers())
    i0, i1 = cau_tao.GetFirstCoreLayerIndex(), cau_tao.GetLastCoreLayerIndex()
    if not lop or i0 < 0 or i1 < i0:
        return None
    W = w.Width
    ngoai = sum(l.Width for l in lop[:i0])                  # lớp phía ngoài lõi (theo Orientation)
    cw = sum(l.Width for l in lop[i0:i1 + 1])
    tam_loi = W / 2 - ngoai - cw / 2                        # tim lõi lệch khỏi tim tường về phía Orientation
    k = w.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).AsInteger()
    dinh_vi = {0: 0.0, 1: tam_loi, 2: W / 2, 3: -W / 2, 4: W / 2 - ngoai, 5: W / 2 - ngoai - cw}.get(k, 0.0)
    o = w.Orientation
    d = tam_loi - dinh_vi
    A, B = cv.GetEndPoint(0), cv.GetEndPoint(1)
    return ((A.X + o.X * d, A.Y + o.Y * d), (B.X + o.X * d, B.Y + o.Y * d), cw, W)


def keo_noi(w, dau_i):
    """Nửa bề dày lớn nhất của tường nối ở đầu dau_i (0 / 1) → kéo dải lõi cho kín góc nối"""
    kq = 0.0
    try:
        for e in w.Location.get_ElementsAtJoin(dau_i):
            if e.Id.Value != w.Id.Value:
                try:
                    kq = max(kq, e.Width / 2)
                except Exception:
                    pass
    except Exception:
        pass
    return kq


def quet_khe(view, lv):
    """Khoảng trống khép kín giữa tường / cột: list[{pts, loops(curve), m2, diem, kt}]"""
    zc = lv.Elevation + mm(1000)
    opt = Options()
    opt.DetailLevel = ViewDetailLevel.Fine
    tuong, chi_tuong = [], []
    for cat in (BuiltInCategory.OST_Walls, BuiltInCategory.OST_Columns, BuiltInCategory.OST_StructuralColumns):
        for e in list(FilteredElementCollector(doc, view.Id).OfCategory(cat).WhereElementIsNotElementType()) + \
                lk_thay(doc, view, cat, False):      # kể cả tường / cột / vách của file link đang thấy (kiến trúc + kết cấu)
            bb = e.get_BoundingBox(None)
            if bb is not None and bb.Min.Z - mm(10) <= zc <= bb.Max.Z + mm(10):
                tuong.append(e)
                if cat == BuiltInCategory.OST_Walls:
                    chi_tuong.append(e)
    th = math.radians(goc_chinh(chi_tuong))
    cs, sn = math.cos(th), math.sin(th)
    xoay = lambda p: (p[0] * cs + p[1] * sn, -p[0] * sn + p[1] * cs)
    mat, loi, bo_mong = [], {}, 0
    id_tuong = set(w.Id.Value for w in chi_tuong)
    for e in tuong:
        try:
            tt = loi_tuong(e) if e.Id.Value in id_tuong else None
        except Exception:
            tt = None
        if tt is not None:
            (ax, ay), (bx, by), cw, W = tt
            if cw < mm(LOI_MONG_MM):
                bo_mong += 1           # tường ốp / lớp hoàn thiện riêng: không phải vách
                continue
            L = math.hypot(bx - ax, by - ay)
            if L < 1e-6:
                continue
            ux, uy = (bx - ax) / L, (by - ay) / L
            loi[e.Id.Value] = (ax, ay, bx, by, cw)
            ka, kb = keo_noi(e, 0), keo_noi(e, 1)
            pa, pb = (ax - ux * ka, ay - uy * ka), (bx + ux * kb, by + uy * kb)
            nx_, ny_ = -uy * cw / 2, ux * cw / 2
            mat.append([[xoay(p) for p in ((pa[0] + nx_, pa[1] + ny_), (pb[0] + nx_, pb[1] + ny_),
                                           (pb[0] - nx_, pb[1] - ny_), (pa[0] - nx_, pa[1] - ny_))]])
            continue
        try:
            for vong in mat_day(e, opt):
                mat.append([[xoay(p) for p in v] for v in vong])
        except Exception:
            pass
    bao_cao.append("Quét theo dải lõi %d tường (bỏ %d tường ốp / hoàn thiện mỏng)" % (len(loi), bo_mong))
    c = mm(O_LUOI_MM)
    # đường phân chia phòng (Room Separation) trên level: coi như vách mỏng 1,5 ô lưới (G19: khép 2 ô ở hành lang)
    for e in list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_RoomSeparationLines)
                  .WhereElementIsNotElementType()) + lk_tang(doc, view, BuiltInCategory.OST_RoomSeparationLines):
        try:
            cv = e.GeometryCurve
            if abs(cv.GetEndPoint(0).Z - lv.Elevation) > mm(500) and e.LevelId != lv.Id:
                continue
            ds = [cv.GetEndPoint(0), cv.GetEndPoint(1)] if cv.GetType().Name == "Line" else list(cv.Tessellate())
        except Exception:
            continue
        for a, b in zip(ds, ds[1:]):
            L = math.hypot(b.X - a.X, b.Y - a.Y)
            if L < 1e-6:
                continue
            nx_, ny_ = -(b.Y - a.Y) / L * 0.75 * c, (b.X - a.X) / L * 0.75 * c
            mat.append([[xoay(p) for p in ((a.X + nx_, a.Y + ny_), (b.X + nx_, b.Y + ny_),
                                           (b.X - nx_, b.Y - ny_), (a.X - nx_, a.Y - ny_))]])
    if not mat:
        return [], 0
    xs = [p[0] for f in mat for v in f for p in v]
    ys = [p[1] for f in mat for v in f for p in v]
    x0, y0 = min(xs) - 3 * c, min(ys) - 3 * c
    nx, ny = int((max(xs) - x0) / c) + 4, int((max(ys) - y0) / c) + 4
    luoi = [bytearray(nx) for _ in range(ny)]
    mep_doc, mep_ngang = [], []   # mép vách song song trục lưới: (x, y_min, y_max) / (y, x_min, x_max)

    def to(f):                 # tô 1 mặt (các vòng điểm đã xoay) theo quy tắc chẵn lẻ
        canh = [(v[i], v[(i + 1) % len(v)]) for v in f for i in range(len(v))]
        for a, b in canh:
            if abs(a[0] - b[0]) < 1e-6:
                mep_doc.append((a[0], min(a[1], b[1]), max(a[1], b[1])))
            elif abs(a[1] - b[1]) < 1e-6:
                mep_ngang.append((a[1], min(a[0], b[0]), max(a[0], b[0])))
        fy = [p[1] for v in f for p in v]
        for j in range(max(0, int((min(fy) - y0) / c) - 1), min(ny, int((max(fy) - y0) / c) + 2)):
            yc = y0 + (j + 0.5) * c
            cat_x = sorted(a[0] + (yc - a[1]) * (b[0] - a[0]) / (b[1] - a[1]) for a, b in canh if (a[1] > yc) != (b[1] > yc))
            for k in range(0, len(cat_x) - 1, 2):
                i0 = max(0, int(math.ceil((cat_x[k] - x0) / c - 0.5)))
                i1 = min(nx - 1, int(math.floor((cat_x[k + 1] - x0) / c - 0.5)))
                if i1 >= i0:
                    luoi[j][i0:i1 + 1] = b"\x01" * (i1 - i0 + 1)

    def dac(p):
        i, j = int((p[0] - x0) / c), int((p[1] - y0) / c)
        return 0 <= i < nx and 0 <= j < ny and luoi[j][i] == 1

    def bat_mep(v):
        """Đỉnh vùng (toạ độ ô lưới) → toạ độ đã xoay; mỗi cạnh bắt vào mép vách gần nhất trong 1 ô lưới
        (biên sát đúng mép tường thô, không lệch theo lưới)"""
        P = [(x0 + q[0] * c, y0 + q[1] * c) for q in v]
        n = len(P)
        canh = []
        for k in range(n):
            a, b = P[k], P[(k + 1) % n]
            if abs(a[0] - b[0]) < 1e-9:
                lo, hi = min(a[1], b[1]), max(a[1], b[1])
                ds = [m[0] for m in mep_doc if abs(m[0] - a[0]) <= c * 1.01 and min(hi, m[2]) - max(lo, m[1]) > c / 2]
                canh.append(("d", min(ds, key=lambda t: abs(t - a[0])) if ds else a[0]))
            else:
                lo, hi = min(a[0], b[0]), max(a[0], b[0])
                ds = [m[0] for m in mep_ngang if abs(m[0] - a[1]) <= c * 1.01 and min(hi, m[2]) - max(lo, m[1]) > c / 2]
                canh.append(("n", min(ds, key=lambda t: abs(t - a[1])) if ds else a[1]))
        kq_ = []
        for k in range(n):
            e1, e2 = canh[k - 1], canh[k]
            if e1[0] == e2[0]:
                continue
            q = (e1[1], e2[1]) if e1[0] == "d" else (e2[1], e1[1])
            if not kq_ or abs(q[0] - kq_[-1][0]) + abs(q[1] - kq_[-1][1]) > mm(1):
                kq_.append(q)
        while len(kq_) > 1 and abs(kq_[0][0] - kq_[-1][0]) + abs(kq_[0][1] - kq_[-1][1]) <= mm(1):
            kq_.pop()
        # bỏ đỉnh thẳng hàng (bậc lưới bị bắt về cùng một mép)
        doi = True
        while doi and len(kq_) >= 4:
            doi = False
            for k in range(len(kq_)):
                a, b, d_ = kq_[k - 1], kq_[k], kq_[(k + 1) % len(kq_)]
                if abs((b[0] - a[0]) * (d_[1] - b[1]) - (b[1] - a[1]) * (d_[0] - b[0])) < 1e-9:
                    del kq_[k]
                    doi = True
                    break
        return kq_

    for f in mat:
        to(f)
    # nối đầu tường hở: đầu tường cách tường khác ≤ NOI_HO_MM theo phương tường thì kéo dài cho chạm
    # (Revit vẫn khép room qua khe này; G19: 2 ô hành lang hở 185 / 285 mm)
    so_noi = 0
    dau = []                   # (tâm đầu tường x, y, hướng ra ux, uy, bề dày, id tường)
    for wid, (ax, ay, bx, by, ww) in loi.items():       # theo tim dải lõi, bề dày lõi
        for (px, py), (qx, qy) in (((ax, ay), (bx, by)), ((bx, by), (ax, ay))):
            L = math.hypot(px - qx, py - qy)
            if L < 1e-6:
                continue
            ux, uy = (px - qx) / L, (py - qy) / L
            cx, cy = px, py
            dau.append((cx, cy, ux, uy, ww, wid))
            t, buoc, gap_trong, cham = 0.0, c / 2, False, None
            while t <= mm(NOI_HO_MM):
                d = dac(xoay((cx + ux * t, cy + uy * t)))
                if not d:
                    gap_trong = True
                elif gap_trong:
                    cham = t
                    break
                t += buoc
            if cham is None or not gap_trong:
                continue
            nx_, ny_ = -uy * ww / 2, ux * ww / 2
            ex, ey = cx + ux * (cham + c), cy + uy * (cham + c)
            to([[xoay(v) for v in ((cx + nx_, cy + ny_), (ex + nx_, ey + ny_), (ex - nx_, ey - ny_), (cx - nx_, cy - ny_))]])
            so_noi += 1
    # nối góc: 2 đầu tường không song song, giao điểm tim cách cả 2 đầu ≤ NOI_HO_MM → kéo dài cả 2 tới giao điểm
    G = mm(NOI_HO_MM)
    for m in range(len(dau)):
        x1, y1, u1, v1, w1, id1 = dau[m]
        for n in range(m + 1, len(dau)):
            x2, y2, u2, v2, w2, id2 = dau[n]
            if id1 == id2 or abs(x1 - x2) > 2 * G or abs(y1 - y2) > 2 * G:
                continue
            det = u1 * (-v2) - v1 * (-u2)
            if abs(det) < 0.2:          # gần song song
                # hốc chữ U: 2 đầu tường song song cùng hướng, thẳng hàng, miệng ≤ NOI_HO_MM → đóng miệng hốc
                # (G19: hốc 470 x 120 sau tường lô gia, người dùng chỉ là trục 2026-10-28)
                lech_truc = (x2 - x1) * u1 + (y2 - y1) * v1
                mieng = abs(-(x2 - x1) * v1 + (y2 - y1) * u1)
                if u1 * u2 + v1 * v2 > 0.98 and abs(lech_truc) <= max(w1, w2) / 2 + c and \
                        (w1 + w2) / 2 < mieng <= G + (w1 + w2) / 2:
                    k_ = 1.5 * c
                    to([[xoay(p) for p in ((x1, y1), (x2, y2), (x2 - u2 * k_, y2 - v2 * k_), (x1 - u1 * k_, y1 - v1 * k_))]])
                    so_noi += 1
                continue
            t1 = ((x2 - x1) * (-v2) - (y2 - y1) * (-u2)) / det
            t2 = (u1 * (y2 - y1) - v1 * (x2 - x1)) / det
            if not (-w2 / 2 <= t1 <= G and -w1 / 2 <= t2 <= G) or (t1 <= c and t2 <= c):
                continue
            for x, y, u, v, ww, t, wk in ((x1, y1, u1, v1, w1, t1, w2), (x2, y2, u2, v2, w2, t2, w1)):
                if t <= 0:
                    continue
                e_ = t + wk / 2
                nx_, ny_ = -v * ww / 2, u * ww / 2
                ex, ey = x + u * e_, y + v * e_
                to([[xoay(p) for p in ((x + nx_, y + ny_), (ex + nx_, ey + ny_), (ex - nx_, ey - ny_), (x - nx_, y - ny_))]])
            so_noi += 1
    # dải ô trống theo hàng + hợp nhất (4 hướng)
    chay, cha = [], []

    def goc(a):
        while cha[a] != a:
            cha[a] = cha[cha[a]]
            a = cha[a]
        return a
    truoc = []
    for j in range(ny):
        hang, i, nay = luoi[j], 0, []
        while True:
            a = hang.find(0, i)
            if a < 0:
                break
            b = hang.find(1, a)
            b = nx if b < 0 else b
            k = len(chay)
            chay.append((j, a, b - 1))
            cha.append(k)
            nay.append(k)
            i = b
        p = 0
        for k in nay:
            _, a, b = chay[k]
            while p < len(truoc) and chay[truoc[p]][2] < a:
                p += 1
            q = p
            while q < len(truoc) and chay[truoc[q]][1] <= b:
                ra, rb = goc(k), goc(truoc[q])
                if ra != rb:
                    cha[ra] = rb
                q += 1
        truoc = nay
    nhom = {}
    for k, (j, a, b) in enumerate(chay):
        nhom.setdefault(goc(k), []).append(k)
    c2 = ra_m2(c * c)
    kq = []
    for ks in nhom.values():
        o = sum(chay[k][2] - chay[k][1] + 1 for k in ks)
        if not (DT_NHO_NHAT_M2 <= o * c2 <= DT_CO_BANG_CHUNG_M2):
            continue
        if any(chay[k][0] in (0, ny - 1) or chay[k][1] == 0 or chay[k][2] == nx - 1 for k in ks):
            continue
        S = set((i, chay[k][0]) for k in ks for i in range(chay[k][1], chay[k][2] + 1))
        # biên: cạnh ô giáp ngoài, hướng ngược chiều kim đồng hồ quanh vùng
        di = {}
        for (i, j) in S:
            if (i, j - 1) not in S:
                di.setdefault((i, j), []).append((i + 1, j))
            if (i + 1, j) not in S:
                di.setdefault((i + 1, j), []).append((i + 1, j + 1))
            if (i, j + 1) not in S:
                di.setdefault((i + 1, j + 1), []).append((i, j + 1))
            if (i - 1, j) not in S:
                di.setdefault((i, j + 1), []).append((i, j))
        vong = []
        while di:
            dau = next(iter(di))
            v, p = [dau], dau
            while True:
                ds = di.get(p)
                if not ds:
                    break
                n = ds.pop()
                if not ds:
                    del di[p]
                if n == dau:
                    break
                v.append(n)
                p = n
            gon = [v[t] for t in range(len(v)) if not (
                (v[t - 1][0] == v[t][0] == v[(t + 1) % len(v)][0]) or (v[t - 1][1] == v[t][1] == v[(t + 1) % len(v)][1]))]
            if len(gon) >= 4:
                vong.append(gon)
        if not vong:
            continue
        ve_the_gioi = lambda q: ((x0 + q[0] * c) * cs - (y0 + q[1] * c) * sn, (x0 + q[0] * c) * sn + (y0 + q[1] * c) * cs)
        sat = [v for v in (bat_mep(v) for v in vong) if len(v) >= 4]
        if not sat:
            continue
        pts = [[(p[0] * cs - p[1] * sn, p[0] * sn + p[1] * cs) for p in v] for v in sat]
        z = lv.Elevation
        loops = [[Line.CreateBound(XYZ(a[0], a[1], z), XYZ(b[0], b[1], z)) for a, b in zip(v, v[1:] + v[:1])] for v in pts]
        gi = sum(i for i, j in S) / float(len(S))
        gj = sum(j for i, j in S) / float(len(S))
        ti, tj = min(S, key=lambda q: (q[0] - gi) ** 2 + (q[1] - gj) ** 2)
        diem = ve_the_gioi((ti + 0.5, tj + 0.5))
        dt = sorted((abs(sum(v[t][0] * v[(t + 1) % len(v)][1] - v[(t + 1) % len(v)][0] * v[t][1]
                             for t in range(len(v)))) / 2 for v in sat), reverse=True)
        rong, dai = kich_thuoc(max(sat, key=len))
        kq.append({"pts": pts, "loops": loops, "m2": ra_m2(dt[0] - sum(dt[1:])), "diem": diem,
                   "kt": (ra_mm(rong), ra_mm(dai)), "ten": ""})
    bao_cao.append("Nối %d đầu tường hở ≤ %g mm khi quét" % (so_noi, NOI_HO_MM))
    return kq, len(mat)


def toa_do(p):
    return "(%d, %d)" % (round(ra_mm(p[0])), round(ra_mm(p[1])))


def dau_x_cad(view, lv):
    """Dấu X (2 đường chéo của khung trục / lỗ mở) trong file CAD import / link của mặt bằng tầng, trên layer có từ khoá
    TU_LAYER_X (lỗ mở, A-Material, trục, HKT…), bỏ layer TU_LAYER_BO (hatch, nét khuất thang máy…)
    → list[{c, pts (4 góc), m2, layer}] (HQV tháp B 2026-11-05: 85 ô A-Lo mo + 31 ô A-Material = 116 trục)"""
    z = lv.Elevation
    nhom = {}
    for ii in FilteredElementCollector(doc).OfClass(ImportInstance):
        opt = Options()
        try:
            if ii.ViewSpecific:
                ov = doc.GetElement(ii.OwnerViewId)
                gl = getattr(ov, "GenLevel", None)      # PythonNet3: không dùng isinstance với lớp Revit
                if gl is None or gl.Id != lv.Id:
                    continue
                opt.View = ov
            else:
                bb = ii.get_BoundingBox(None)
                if bb is None or not (bb.Min.Z - mm(1500) <= z <= bb.Max.Z + mm(1500)):
                    continue
            ds = list(ii.get_Geometry(opt) or [])
        except Exception:
            continue
        while ds:
            g = ds.pop()
            tn = g.GetType().Name
            if tn == "GeometryInstance":
                ds.extend(list(g.GetInstanceGeometry()))
                continue
            if tn not in ("Line", "PolyLine"):
                continue
            try:
                st = doc.GetElement(g.GraphicsStyleId)
                lop = st.GraphicsStyleCategory.Name if st is not None else ""
            except Exception:
                lop = ""
            k = khong_dau(lop.split("$0$")[-1])
            if not any(t in k for t in TU_LAYER_X) or any(t in k for t in TU_LAYER_BO):
                continue
            pts = [g.GetEndPoint(0), g.GetEndPoint(1)] if tn == "Line" else list(g.GetCoordinates())
            for a, b in zip(pts, pts[1:]):
                L = math.hypot(b.X - a.X, b.Y - a.Y)
                if L < mm(150):
                    continue
                key = (round((a.X + b.X) / 2 / mm(30)), round((a.Y + b.Y) / 2 / mm(30)), lop)
                nhom.setdefault(key, []).append(((a.X, a.Y), (b.X, b.Y), L))
    kq, da = [], set()
    for (_, _, lop), ds in nhom.items():
        for i in range(len(ds)):
            for j in range(i + 1, len(ds)):
                (a1, b1, L1), (a2, b2, L2) = ds[i], ds[j]
                if abs(L1 - L2) > mm(20):
                    continue
                if abs(((b1[0] - a1[0]) * (b2[0] - a2[0]) + (b1[1] - a1[1]) * (b2[1] - a2[1])) / (L1 * L2)) > 0.995:
                    continue
                cx, cy = (a1[0] + b1[0] + a2[0] + b2[0]) / 4, (a1[1] + b1[1] + a2[1] + b2[1]) / 4
                khoa = (round(cx / mm(50)), round(cy / mm(50)))
                if khoa in da:
                    continue
                goc4 = sorted([a1, b1, a2, b2], key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
                rong, dai = kich_thuoc(goc4)
                dt = abs(sum(goc4[t][0] * goc4[(t + 1) % 4][1] - goc4[(t + 1) % 4][0] * goc4[t][1] for t in range(4))) / 2
                if rong < mm(100) or ra_m2(dt) > DT_CO_BANG_CHUNG_M2:
                    continue
                da.add(khoa)
                kq.append({"c": (cx, cy), "pts": goc4, "m2": ra_m2(dt), "layer": lop.split("$0$")[-1]})
    return kq


def tim_truc(view, lv, da_lam, viec, ghi_them):
    """Nhận trục / hộp kỹ thuật trên level của view → (se_lam, da_co, bi_loai, xem_lai).
    da_lam(v): ô đã làm rồi (đã hatch / đã có lỗ mở) → bỏ qua; viec: chữ trong báo cáo ("hatch", "tạo lỗ mở")"""
    z = lv.Elevation
    del VIEW_LINK[:]
    VIEW_LINK.append(view)
    bao_cao.append(lk_ghi_chu(doc, view))
    # ---- dữ liệu trên level ----
    cua = [p for d in theo_level(BuiltInCategory.OST_Doors, lv) for p in diem_hai_ben(d)]
    cua_so = [p for d in theo_level(BuiltInCategory.OST_Windows, lv) for p in diem_hai_ben(d)]
    tb = []
    da_xet = set()
    for e in list(theo_level(BuiltInCategory.OST_PlumbingFixtures, lv)) + list(
            FilteredElementCollector(doc, view.Id).OfCategory(BuiltInCategory.OST_PlumbingFixtures)
            .WhereElementIsNotElementType()):
        if e.Id.Value in da_xet:
            continue
        da_xet.add(e.Id.Value)
        p = diem_tam(e)
        if p is None:
            continue
        try:     # bồn cầu host trên sàn: điểm đặt sát tường → dò thêm 200 mm theo hướng mặt
            f = e.FacingOrientation
            p = (p[0] + f.X * mm(200), p[1] + f.Y * mm(200))
        except Exception:
            pass
        tb.append(p)
    san = [vong_san(f) for f in FilteredElementCollector(doc).OfClass(Floor)
           if f.LevelId == lv.Id and not la_san_ket_cau(f)]
    # sàn hoàn thiện trong link: chỉ link kiến trúc (link có cửa ở tầng này); sàn của link kết cấu không phải sàn hoàn thiện
    li_kt = set(d._li.Id.Value for d in lk_tang(doc, view, BuiltInCategory.OST_Doors))
    san += [vong_san(f) for f in lk_tang(doc, view, BuiltInCategory.OST_Floors)
            if f._li.Id.Value in li_kt and not la_san_ket_cau(f)]
    san = [s for s in san if s]
    ong = ong_dung(lv)
    shaft = [diem_tam(e) for e in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_ShaftOpening)
             .WhereElementIsNotElementType()]
    shaft += [diem_tam(e) for e in lk_tang(doc, view, BuiltInCategory.OST_ShaftOpening)]
    shaft = [p for p in shaft if p]
    loai = []
    for cat in (BuiltInCategory.OST_SpecialityEquipment, BuiltInCategory.OST_GenericModel,
                BuiltInCategory.OST_MechanicalEquipment, BuiltInCategory.OST_Stairs):
        for e in list(FilteredElementCollector(doc).OfCategory(cat).WhereElementIsNotElementType()) + \
                lk_thay(doc, view, cat, False):
            if cat == BuiltInCategory.OST_Stairs or co_tu(ten_family(e) + " " + ten_kieu(e), TU_KHOA_LOAI):
                p = diem_tam(e)
                bb = e.get_BoundingBox(None)
                if p and bb and bb.Min.Z - mm(500) <= z + mm(1000) <= bb.Max.Z + mm(500):
                    loai.append(p)
    bao_cao.append("Trên level: cửa đi %d, cửa sổ %d, thiết bị vệ sinh %d, sàn hoàn thiện %d, ống đứng %d, "
                   "shaft opening %d, thang máy / thang bộ %d; %s" % (
                       len(cua) // 2, len(cua_so) // 2, len(tb), len(san), len(ong), len(shaft), len(loai),
                       ghi_them))
    if not ong and not shaft:
        bao_cao.append("Model không có ống đứng / shaft opening → trục, hộp nhận theo tên room hoặc hình học "
                       "(ô kín không cửa, cửa sổ, thiết bị, sàn) – xem ảnh để duyệt (Cần xác nhận lại).")

    # ---- room đã đặt tên trục / hộp kỹ thuật hoặc thang (chỉ đọc) ----
    opt = SpatialElementBoundaryOptions()
    opt.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.CoreBoundary
    room_hkt, room_loai = [], []
    for r in [x for x in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()
              if x.LevelId == lv.Id] + lk_tang(doc, view, BuiltInCategory.OST_Rooms):
        if r.Area <= 0 or r.Location is None:
            continue
        ten_r = r.get_Parameter(BuiltInParameter.ROOM_NAME).AsString() or ""
        if co_tu(ten_r, TU_KHOA_LOAI):
            room_loai.append(r)
        elif co_tu(ten_r, TU_KHOA_HKT):
            loops = [[phang(sg.GetCurve(), z) for sg in segs] for segs in (r.GetBoundarySegments(opt) or [])]
            loops = [l for l in loops if len(l) >= 2]
            if loops:
                p0 = r.Location.Point
                room_hkt.append({"loops": loops, "pts": [diem_loop(l) for l in loops], "m2": ra_m2(r.Area),
                                 "ten": ten_r, "diem": (p0.X, p0.Y)})
    for v in room_hkt:
        v["kt"] = tuple(ra_mm(t) for t in kich_thuoc(max(v["pts"], key=len)))

    # ---- khoảng trống kín giữa tường (quét lưới) ----
    TransactionManager.Instance.EnsureInTransaction(doc)
    khe, so_mat = quet_khe(view, lv)
    bao_cao.append("Quét dấu chân %d mặt đáy tường / cột: %d khoảng trống kín ≤ %g m2" % (
        so_mat, len(khe), DT_CO_BANG_CHUNG_M2))

    # ---- dấu X trục / lỗ mở trong CAD import của tầng ----
    xcad = dau_x_cad(view, lv)
    co_cad = len(xcad) >= SO_X_CAD_TIN
    if xcad:
        dem_l = {}
        for d in xcad:
            dem_l[d["layer"]] = dem_l.get(d["layer"], 0) + 1
        bao_cao.append("CAD của tầng: %d dấu X trục / lỗ mở (%s)%s" % (
            len(xcad), ", ".join("%s %d" % kv for kv in sorted(dem_l.items())),
            " → ô chỉ có hình học mà không có dấu X thì không vẽ" if co_cad else ""))
    x_dung = set()            # chỉ số dấu X đã nằm trong ô được nhận

    # ---- phân loại ----
    se_ve, da_co, bi_loai, xem_lai, khong_x, khe_dai = [], 0, [], [], [], []
    for v in room_hkt + khe:
        pts = v["pts"]
        x, y = v["diem"]
        trong = lambda ds: [p for p in ds if trong_vung(p[0], p[1], pts)]
        if trong(loai) or any(r.IsPointInRoom(XYZ(x, y, z + mm(1000))) for r in room_loai):
            bi_loai.append((v, "thang máy / thang bộ"))
            continue
        ix = [i for i, d in enumerate(xcad) if trong_vung(d["c"][0], d["c"][1], pts)]
        tong_x = sum(xcad[i]["m2"] for i in ix)
        if v["ten"]:
            nguon = "tên room '%s'" % v["ten"]
        elif any(trong_vung(x, y, r["pts"]) for r in room_hkt):
            continue          # đã nhận theo room đặt tên
        elif ix:
            # ô kín chứa dấu X CAD: ô không lớn hơn nhiều so với khung X thì bo theo mép tường thô của ô;
            # ô rộng hơn hẳn (tường hộp chưa dựng trong model) thì để bo theo khung X ở dưới
            # ô chứa từ 2 dấu X trở lên (vách ngăn giữa các hộp chưa dựng) hoặc không trùm khung X (điểm 30 % từ góc
            # vào tâm nằm ngoài ô) cũng bo theo khung X
            if v["m2"] > max(2.0 * tong_x, tong_x + 0.5) or len(ix) > 1 or not all(
                    trong_vung(q[0] + 0.3 * (xcad[ix[0]]["c"][0] - q[0]), q[1] + 0.3 * (xcad[ix[0]]["c"][1] - q[1]), pts)
                    for q in xcad[ix[0]]["pts"]):
                continue
            nguon = "dấu X CAD"
        elif trong(cua) or trong(tb):
            continue
        elif trong(shaft):
            nguon = "shaft opening"
        elif trong(ong):
            nguon = "ống đứng"
        elif (not trong(cua_so) and not any(trong_vung(x, y, s_) for s_ in san)
              and v["m2"] <= DT_MAX_M2 and v["kt"][0] >= RONG_MIN_MM):
            if v["kt"][1] >= KHE_DAI_MM and v["kt"][0] <= KHE_HEP_MM:
                khe_dai.append(v)       # dải dài hẹp (khe giữa tường kiến trúc và vách / lõi) – không phải trục, liệt kê
                continue
            if co_cad:
                khong_x.append(v)       # CAD đã đánh dấu đủ trục mà ô này không có dấu X → không vẽ, liệt kê
                continue
            nguon = "hình học"
        else:
            continue
        x_dung.update(ix)
        if da_lam(v):
            da_co += 1
            continue
        v["nguon"] = nguon
        se_ve.append(v)
        if v["kt"][0] > O_LON_MM:
            xem_lai.append(v)
    # dấu X CAD không nằm trong ô kín nào được nhận (tường hộp chưa dựng / ô hở): bo theo khung dấu X
    for i, d in enumerate(xcad):
        if i in x_dung:
            continue
        cx, cy = d["c"]
        if any(trong_vung(p[0], p[1], [d["pts"]]) for p in loai) or any(
                r.IsPointInRoom(XYZ(cx, cy, z + mm(1000))) for r in room_loai):
            continue
        if any(trong_vung(cx, cy, v["pts"]) for v in se_ve):
            continue
        g4 = d["pts"]
        v = {"pts": [g4], "loops": [[Line.CreateBound(XYZ(a[0], a[1], z), XYZ(b[0], b[1], z))
                                     for a, b in zip(g4, g4[1:] + g4[:1])]],
             "m2": d["m2"], "diem": (cx, cy), "kt": tuple(ra_mm(t) for t in kich_thuoc(g4)), "ten": ""}
        if da_lam(v):
            da_co += 1
            continue
        v["nguon"] = "khung X CAD"
        se_ve.append(v)
        if v["kt"][0] > O_LON_MM:
            xem_lai.append(v)
    if khe_dai:
        bao_cao.append("KHÔNG VẼ %d dải dài hẹp (dài ≥ %d, rộng ≤ %d mm: khe giữa tường và vách / lõi, Cần xác nhận lại): %s" % (
            len(khe_dai), KHE_DAI_MM, KHE_HEP_MM, "; ".join("%.2f m2 %dx%d tại %s" % (
                v["m2"], round(v["kt"][0]), round(v["kt"][1]), toa_do(v["diem"])) for v in khe_dai)))
    if khong_x:
        bao_cao.append("KHÔNG VẼ %d ô kín nhỏ không có dấu X trong CAD (khe tường, hốc – Cần xác nhận lại): %s" % (
            len(khong_x), "; ".join("%.2f m2 %dx%d tại %s" % (v["m2"], round(v["kt"][0]), round(v["kt"][1]),
                                                              toa_do(v["diem"])) for v in khong_x)))
    try:     # danh sách khoảng trống (mm) để vẽ ảnh đối chiếu khi cần
        import json
        with open(os.path.join(THU_MUC, "ngan_chay_vung.json"), "w", encoding="utf-8") as f:
            json.dump([{"m2": round(v["m2"], 3), "kt": [round(t) for t in v["kt"]], "nguon": v.get("nguon", ""),
                        "pts": [[(round(ra_mm(p[0])), round(ra_mm(p[1]))) for p in l] for l in v["pts"]]}
                       for v in room_hkt + khe + [v for v in se_ve if v["nguon"] == "khung X CAD"]],
                      f, ensure_ascii=False)
    except Exception:
        pass
    dem_nguon = {}
    for v in se_ve:
        dem_nguon[v["nguon"].split(" '")[0]] = dem_nguon.get(v["nguon"].split(" '")[0], 0) + 1
    bao_cao.append("Trục / hộp kỹ thuật cần %s: %d (%s); đã có %s: %d; loại vì thang: %d" % (
        viec, len(se_ve), ", ".join("%s %d" % kv for kv in sorted(dem_nguon.items())) or "-", viec, da_co, len(bi_loai)))
    for v in sorted(se_ve, key=lambda v: -v["m2"]):
        bao_cao.append("   %5.2f m2  %4d x %4d mm  %-14s tại %s" % (
            v["m2"], round(v["kt"][0]), round(v["kt"][1]), v["nguon"], toa_do(v["diem"])))
    if xem_lai:
        bao_cao.append("CẦN XEM LẠI (ô lớn hơn %d x %d mm, vẫn nhận): %s" % (
            O_LON_MM, O_LON_MM, "; ".join("%.2f m2 tại %s" % (v["m2"], toa_do(v["diem"])) for v in xem_lai)))
    for v, ly_do in bi_loai:
        bao_cao.append("Loại (%s): %.2f m2 tại %s" % (ly_do, v["m2"], toa_do(v["diem"])))

    return se_ve, da_co, bi_loai, xem_lai


# ==== HẾT PHẦN CHUNG ====


# ---------- riêng công cụ lỗ mở ----------
def chon_view():
    """Mặt bằng tầng: theo tên (IN[0]) hoặc view đang mở"""
    loai_mb = (ViewType.FloorPlan, ViewType.EngineeringPlan)
    if TEN_VIEW:
        ds = [v for v in FilteredElementCollector(doc).OfClass(ViewPlan)
              if not v.IsTemplate and v.Name == TEN_VIEW and v.ViewType in loai_mb]
        if not ds:
            raise Exception("Không tìm thấy mặt bằng tầng tên '%s'" % TEN_VIEW)
        return ds[0]
    av = doc.ActiveView
    if av is None or av.ViewType not in loai_mb or av.GenLevel is None:
        raise Exception("View đang mở không phải mặt bằng tầng – mở mặt bằng tầng cần tạo lỗ mở rồi chạy lại")
    return av


def dat(e, bip, ten_ui, gt):
    """Gán tham số theo BuiltInParameter, không được thì theo tên trên giao diện; trả về True nếu gán được"""
    p = e.get_Parameter(bip)
    if p is None or p.IsReadOnly:
        p = e.LookupParameter(ten_ui)
    if p is None or p.IsReadOnly:
        return False
    return bool(p.Set(gt))


def doc_tham_so(e):
    def lay(bip, ten_ui):
        p = e.get_Parameter(bip) or e.LookupParameter(ten_ui)
        if p is None:
            return "?"
        if p.StorageType == StorageType.ElementId:
            return ten(doc.GetElement(p.AsElementId()))
        if p.StorageType == StorageType.Double:
            return "%g mm" % round(ra_mm(p.AsDouble()), 1)
        return p.AsValueString() or ""
    return "Base %s / %s, Top %s / %s" % (
        lay(BuiltInParameter.WALL_BASE_CONSTRAINT, "Base Constraint"), lay(BuiltInParameter.WALL_BASE_OFFSET, "Base Offset"),
        lay(BuiltInParameter.WALL_HEIGHT_TYPE, "Top Constraint"), lay(BuiltInParameter.WALL_TOP_OFFSET, "Top Offset"))


# ---------- 1 shaft opening cho cả tầng + dấu X (Symbolic Line chép từ shaft mẫu) ----------
import time


class _BoQuaCanhBao(IFailuresPreprocessor):
    """Bỏ cảnh báo khi kết thúc sửa sketch (lỗi thật vẫn để Revit báo)"""
    __namespace__ = "ARV.LoMo.X%d" % int(time.time() * 1000)   # tên kiểu .NET mới mỗi lần nạp (chạy lại trong cùng phiên)

    def PreprocessFailures(self, fa):
        for m in fa.GetFailureMessages():
            if m.GetSeverity() == FailureSeverity.Warning:
                fa.DeleteWarning(m)
        return FailureProcessingResult.Continue


def tach_sketch(op):
    """Sketch của shaft → (nét biên, nét symbolic): nét symbolic = ModelLine mang line style khác "<Sketch>" """
    sk = doc.GetElement(op.SketchId)
    bien, ky = [], []
    for i in sk.GetAllElements():
        e = doc.GetElement(i)
        if e.GetType().Name == "ModelLine":
            (bien if e.LineStyle is None or e.LineStyle.Name == "<Sketch>" else ky).append(e)
    return bien, ky


def vong_shaft(op):
    """Các vòng biên trong sketch của shaft → list[list[(x, y)]]"""
    sk = doc.GetElement(op.SketchId)
    return [[(p.X, p.Y) for c in arr for p in list(c.Tessellate())[:-1]] for arr in sk.Profile]


def la_shaft_tang(op, lv):
    """Shaft lỗ mở cục bộ của tầng: Base Constraint và Top Constraint đều là level này"""
    b = op.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)
    t = op.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)
    return b is not None and t is not None and b.AsElementId() == lv.Id and t.AsElementId() == lv.Id


def tim_mau_x():
    """2 nét symbolic của một shaft mẫu có dấu X vẽ tay → (id 2 nét, mô tả); không có thì (None, "")"""
    for o in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_ShaftOpening).WhereElementIsNotElementType():
        try:
            ky = tach_sketch(o)[1]
        except Exception:
            continue
        if len(ky) >= 2:
            return [e.Id for e in ky[:2]], "shaft %d (nét %s)" % (o.Id.Value, ky[0].LineStyle.Name)
    return None, ""


def duong_cheo(curves, z):
    """2 đường chéo của hình chữ nhật bao 1 vòng biên, theo phương cạnh dài nhất (đúng cả lỗ xoay xiên)"""
    dai = max(curves, key=lambda c: c.Length)
    a, b = dai.GetEndPoint(0), dai.GetEndPoint(1)
    L = math.hypot(b.X - a.X, b.Y - a.Y)
    ux, uy = (b.X - a.X) / L, (b.Y - a.Y) / L
    pts = [p for c in curves for p in (c.GetEndPoint(0), c.GetEndPoint(1))]
    su = [p.X * ux + p.Y * uy for p in pts]
    sv = [-p.X * uy + p.Y * ux for p in pts]
    diem = lambda s, t: XYZ(s * ux - t * uy, s * uy + t * ux, z)
    u0, u1, v0, v1 = min(su), max(su), min(sv), max(sv)
    return [Line.CreateBound(diem(u0, v0), diem(u1, v1)), Line.CreateBound(diem(u0, v1), diem(u1, v0))]


def dat_rang_buoc(op, lv):
    ok = (dat(op, BuiltInParameter.WALL_BASE_CONSTRAINT, "Base Constraint", lv.Id) and
          dat(op, BuiltInParameter.WALL_BASE_OFFSET, "Base Offset", mm(BASE_OFFSET_MM)) and
          dat(op, BuiltInParameter.WALL_HEIGHT_TYPE, "Top Constraint", lv.Id) and
          dat(op, BuiltInParameter.WALL_TOP_OFFSET, "Top Offset", mm(TOP_OFFSET_MM)))
    if not ok:
        bao_cao.append("Shaft %d: không gán đủ ràng buộc (%s)" % (op.Id.Value, doc_tham_so(op)))


def tao_shaft(lv, vung):
    """Tạo 1 shaft opening với vòng biên của 1 ô (transaction riêng) → Opening"""
    ca = CurveArray()
    for l in vung["loops"]:
        for c in l:
            ca.Append(c)
    tren = sorted([l for l in FilteredElementCollector(doc).OfClass(Level) if l.Elevation > lv.Elevation + mm(1)],
                  key=lambda l: l.Elevation)
    t = Transaction(doc, "ARV - Lỗ mở shaft")
    t.Start()
    try:
        try:
            op = doc.Create.NewOpening(lv, lv, ca)
        except Exception:
            if not tren:
                raise
            op = doc.Create.NewOpening(lv, tren[0], ca)     # tạo tới tầng trên rồi đặt lại ràng buộc
        dat_rang_buoc(op, lv)
        t.Commit()
        return op
    except Exception:
        if t.HasStarted() and not t.HasEnded():
            t.RollBack()
        raise


def vong_chua_x(op):
    """Các vòng biên đã có trong sketch nhưng chưa có dấu X (ít hơn 2 nét symbolic có trung điểm trong vòng)"""
    sk = doc.GetElement(op.SketchId)
    _, ky = tach_sketch(op)
    giua_ky = []
    for e in ky:
        c = e.GeometryCurve
        a, b = c.GetEndPoint(0), c.GetEndPoint(1)
        giua_ky.append(((a.X + b.X) / 2, (a.Y + b.Y) / 2))
    can_x = []
    for arr in sk.Profile:
        cs = [c for c in arr]
        pts = [(c.GetEndPoint(0).X, c.GetEndPoint(0).Y) for c in cs]
        if sum(1 for q in giua_ky if trong_da_giac(q[0], q[1], pts)) < 2:
            can_x.append(cs)
    return can_x


def them_vong_va_x(op, vung_moi, mau_x):
    """Trong 1 lần sửa sketch của shaft: thêm vòng biên các ô mới + dấu X cho mọi vòng chưa có X → (số vòng thêm, số X)"""
    sk = doc.GetElement(op.SketchId)
    zs = sk.SketchPlane.GetPlane().Origin.Z
    can_x = vong_chua_x(op) if mau_x is not None else []
    ses = SketchEditScope(doc, "ARV - Lỗ mở shaft")
    t = Transaction(doc, "ARV - Lỗ mở shaft")
    so_vong = 0
    try:
        ses.Start(op.SketchId)     # chỉ mở được khi không còn transaction nào đang mở
        t.Start()
        for v in vung_moi:
            cs = []
            for l in v["loops"]:
                for c in l:
                    cs.append(doc.Create.NewModelCurve(phang(c, zs), sk.SketchPlane).GeometryCurve)
            can_x.append(cs)
            so_vong += 1
        so_x = 0
        if mau_x is not None:
            for cs in can_x:
                moi = list(ElementTransformUtils.CopyElements(doc, ds_id(mau_x), XYZ(0, 0, 0)))
                for i, l in zip(moi, duong_cheo(cs, zs)):
                    doc.GetElement(i).SetGeometryCurve(l, True)
                so_x += 1
        t.Commit()
        ses.Commit(_BoQuaCanhBao())
        return so_vong, so_x
    except Exception:
        try:
            if t.HasStarted() and not t.HasEnded():
                t.RollBack()
            if ses.IsActive:
                ses.Cancel()
        except Exception:
            pass
        raise


def chinh():
    view = chon_view()
    lv = view.GenLevel
    z = lv.Elevation
    bao_cao.append("View: %s (level %s) → 1 shaft opening cho cả tầng, Base / Top Constraint = %s, Base Offset %g mm, "
                   "Top Offset %g mm" % (view.Name, lv.Name, lv.Name, BASE_OFFSET_MM, TOP_OFFSET_MM))
    zb, zt = z + mm(BASE_OFFSET_MM), z + mm(TOP_OFFSET_MM)
    tam_vong, cua_tang = [], []      # tâm từng vòng của mọi shaft cắt qua tầng; shaft lỗ mở cục bộ của tầng
    for e in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_ShaftOpening).WhereElementIsNotElementType():
        bb = e.get_BoundingBox(None)
        if bb is None or bb.Max.Z <= zb or bb.Min.Z >= zt:
            continue
        try:
            vs = vong_shaft(e)
        except Exception:
            vs = []
        for p in vs:
            tam_vong.append((sum(q[0] for q in p) / len(p), sum(q[1] for q in p) / len(p)))
        if la_shaft_tang(e, lv):
            cua_tang.append((len(vs), e))
    se_lam, da_co, bi_loai, xem_lai = tim_truc(
        view, lv, lambda v: any(trong_vung(p[0], p[1], v["pts"]) for p in tam_vong), "lỗ mở",
        "vòng lỗ mở đã có cắt qua tầng: %d" % len(tam_vong))
    dich = max(cua_tang, key=lambda t: t[0])[1] if cua_tang else None
    mau_x, ghi_mau = tim_mau_x() if GAN_X else (None, "")
    if dich is not None:
        bao_cao.append("Thêm vào shaft có sẵn của tầng: %d (%d vòng)" % (dich.Id.Value, max(cua_tang, key=lambda t: t[0])[0]))
    elif se_lam:
        bao_cao.append("Tầng chưa có shaft lỗ mở → tạo 1 shaft mới chứa cả %d vòng" % len(se_lam))
    if GAN_X:
        if mau_x is None:
            bao_cao.append("CHƯA GẮN DẤU X: model chưa có shaft mẫu có dấu X. Vẽ tay 1 lần: chọn shaft → Edit Sketch → "
                           "Symbolic Line vẽ 2 đường chéo của 1 ô → Finish, rồi bấm lại (bấm lại sẽ bổ sung X cho các vòng).")
        else:
            bao_cao.append("Dấu X chép từ %s" % ghi_mau)
    if DRY_RUN:
        TransactionManager.Instance.TransactionTaskDone()
        bao_cao.append("DRY-RUN: chưa tạo gì. Đặt IN[4] = False để tạo lỗ mở.")
        return view, []
    TransactionManager.Instance.TransactionTaskDone()
    TransactionManager.Instance.ForceCloseTransaction()     # Dynamo giữ transaction tới cuối lượt chạy → đóng hẳn
    con = list(se_lam)
    if dich is None and con:
        try:
            dich = tao_shaft(lv, con[0])
            con = con[1:]
            bao_cao.append("ĐÃ TẠO shaft opening %d" % dich.Id.Value)
        except Exception as ex:
            bao_cao.append("Không tạo được shaft opening: %s" % str(ex).splitlines()[0])
            return view, []
    if dich is None:
        bao_cao.append("Không có ô trục nào cần lỗ mở.")
        return view, []
    try:
        so_vong, so_x = them_vong_va_x(dich, con, mau_x if GAN_X else None)
        bao_cao.append("ĐÃ THÊM %d vòng lỗ mở + %d dấu X vào shaft %d" % (so_vong, so_x, dich.Id.Value))
    except Exception as ex:
        bao_cao.append("LỖI khi sửa sketch shaft %d: %s – không thêm vòng / dấu X nào" % (dich.Id.Value, str(ex).splitlines()[0]))
    dich = doc.GetElement(dich.Id)
    bao_cao.append("Shaft %d sau cùng: %d vòng, %d nét dấu X; %s" % (
        dich.Id.Value, doc.GetElement(dich.SketchId).Profile.Size, len(tach_sketch(dich)[1]), doc_tham_so(dich)))
    return view, [dich.Id]


def xuat_anh(view):
    try:
        TransactionManager.Instance.ForceCloseTransaction()
        opt = ImageExportOptions()
        opt.ExportRange = ExportRange.SetOfViews
        opt.SetViewsAndSheets(ds_id([view.Id]))
        opt.FilePath = os.path.join(THU_MUC, "lo_mo")
        opt.ZoomType = ZoomFitType.FitToPage
        opt.PixelSize = 6000
        opt.ImageResolution = ImageResolution.DPI_300
        opt.HLRandWFViewsFileType = ImageFileType.PNG
        opt.ShadowViewsFileType = ImageFileType.PNG
        doc.ExportImage(opt)
        bao_cao.append("Ảnh: %s*.png" % opt.FilePath)
    except Exception as ex:
        bao_cao.append("Không xuất được ảnh: %s" % ex)


try:
    v, moi = chinh()
    xuat_anh(v)
except Exception:
    bao_cao.append("LỖI: " + traceback.format_exc())

log = os.path.join(THU_MUC, "lo_mo_%s.txt" % datetime.now().strftime("%Y%m%d_%H%M%S"))
with open(log, "w", encoding="utf-8") as f:
    f.write("\n".join(bao_cao))
bao_cao.append("Log: " + log)
OUT = bao_cao
