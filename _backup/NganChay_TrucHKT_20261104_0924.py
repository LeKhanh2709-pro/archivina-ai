# Hatch ngăn cháy lan trục / hộp kỹ thuật (Filled Region 2D) trên view mặt bằng chống cháy lan của Revit.
# Thể hiện theo skill CAD ngan-chay-truc-hkt: lưới NET 125 mm xoay 45° màu 220,30,30, viền tím (màu 6), chỉ hatch trong lòng ô.
#   - Vùng = khoảng trống khép kín giữa tường / cột trên level của view: quét lưới 20 mm theo DẢI LÕI của tường
#     (mép tường thô theo cấu tạo lớp của kiểu tường, bỏ lớp trát / hoàn thiện và tường ốp mỏng), lưới xoay theo
#     phương chính của tường → bắt được cả khe hộp gen hẹp ~120 mm mà room của Revit không bắt được.
#     Biên = mép tường thô trong lòng ô, sai số ≤ 1 ô lưới (người dùng chốt 2026-10-28: trong hộp kỹ thuật không có
#     lớp trát, không bao giờ bo vào mặt hoàn thiện). Tường cong / không có cấu tạo lớp: lấy mặt đáy khối. Chỉ đọc.
#   - Nhận trục / hộp kỹ thuật theo thứ tự bằng chứng:
#       a) tên room có từ khoá (HKT, hộp kỹ thuật, trục kỹ thuật, shaft…) hoặc chứa Shaft Opening
#       b) chứa ống / ống gió / ống luồn dây đi đứng, ô không có cửa đi và thiết bị vệ sinh
#       c) không có ống, dấu X trong model (như G19): ô / khe kín KHÔNG có cửa đi, cửa sổ, thiết bị vệ sinh, sàn hoàn
#          thiện, diện tích ≤ ngưỡng (mặc định 3 m2: ô 1770 x 2520 ở hành lang G19 không phải trục), bề rộng lòng ≥ ngưỡng
#   - Loại: ô chứa thang máy / thang bộ (tên family / type / room có từ khoá loại trừ)
#   - Ô lớn hơn 1400 x 1400 mm vẫn hatch nhưng liệt kê riêng để xem lại (như bản CAD)
#   - Kiểu Filled Region + mẫu lưới + line style viền chưa có thì tự tạo; Filled Region gom group "ARV_NganChay"
#   - Ẩn thiết bị vệ sinh / nội thất trong view (Hide in View từng đối tượng, không sửa template)
#   - Bấm lại: ô đã có hatch cùng kiểu thì bỏ qua, không vẽ trùng, không xoá gì
#   - Đặt lên bản vẽ (IN[10], không chạy khi Dry-run): sheet mới hoặc sheet trống có sẵn, mặt bằng giữa khổ giấy + chú thích
# Dry-run (mặc định) chỉ báo cáo, không sửa mô hình.
# INPUT
#   IN[0] (str)   Tên view (để trống = view đang mở nếu là view chống cháy lan, không thì view đầu tiên có chữ "cháy lan" trong tên view / template)
#   IN[1] (str)   Từ khoá tên room là trục / hộp kỹ thuật, cách nhau bằng ;  (không phân biệt dấu / hoa thường)
#   IN[2] (float) Diện tích lớn nhất của ô / khe kín nhận theo hình học (m2)
#   IN[3] (float) Bề rộng lòng nhỏ nhất của ô / khe (mm)
#   IN[4] (bool)  Dry-run (True = chỉ báo cáo)
#   IN[5] (str)   Thư mục ghi log + ảnh (để trống = Documents\ARV_Logs\ngan_chay)
#   IN[6] (str)   Từ khoá loại trừ (thang máy, thang bộ) trong tên family / type / room, cách nhau bằng ;
#   IN[7] (bool)  Ẩn thiết bị vệ sinh / nội thất trong view
#   IN[8] (str)   Tên kiểu Filled Region hatch ngăn cháy
#   IN[9] (str)   Tên line style viền hatch
#   IN[10] (bool) Đặt mặt bằng lên bản vẽ (sheet) sau khi vẽ (người dùng yêu cầu 2026-11-03; nút pyRevit hỏi trong hộp thoại)
#   IN[11] (str)  Giai đoạn (giá trị thư mục cấp 1 của Project Browser, vd. TKBVTC)
#   IN[12] (str)  Hạng mục (thư mục cấp 2; chưa có thì tạo mới bằng cách gán giá trị mới)
#   IN[13] (str)  Khổ giấy (A1 / A0) – tìm family khung tên có chữ đó
#   IN[14] (str)  Khung tên "Family : Type" (trống = tự tìm theo khổ)
#   IN[15] (str)  Số hiệu sheet (trống = tiếp theo trong hạng mục; trùng sheet TRỐNG có sẵn = đặt vào sheet đó)
#   IN[16] (str)  Tên sheet (trống = "MẶT BẰNG NGĂN CHÁY LAN <TẦNG>")
#   IN[17] (bool) Thêm chú thích (ô mẫu hatch ngăn cháy lan + chữ) ở góc phải dưới bản vẽ
#   IN[18] (bool) Tầng của mặt bằng đang mở chưa có view ngăn cháy lan thì tạo view + template (người dùng yêu cầu 2026-11-04;
#                 IN[0] trống và view đang mở là mặt bằng tầng)
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
THU_MUC = str(gia_tri(5, os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs", "ngan_chay")))
TU_KHOA_LOAI = tach(gia_tri(6, "Thang máy;Elevator;Lift;Thang bộ;Stair"))
AN_THIET_BI = bool(gia_tri(7, True))
TEN_HATCH = str(gia_tri(8, "AV_Hatch Ngăn Cháy Lan"))
TEN_NET = str(gia_tri(9, "AV.Nét ngăn cháy lan"))
DAT_SHEET = bool(gia_tri(10, False))
SH_IN = [str(gia_tri(i, "")) for i in range(11, 17)]     # giai đoạn, hạng mục, khổ, khung tên, số hiệu, tên sheet
CHU_THICH = bool(gia_tri(17, True))
TAO_VIEW = bool(gia_tri(18, True))
os.makedirs(THU_MUC, exist_ok=True)

# Thông số thể hiện lấy theo skill CAD ngan-chay-truc-hkt (NET 125 mm / 315°, RGB 220,30,30, viền màu 6)
LUOI_MM = 125.0
LUOI_GOC = 45.0
MAU_HATCH = (220, 30, 30)
MAU_VIEN = (255, 0, 255)
TEN_MAU_LUOI = "AV_Lưới NET 125 xoay 45"
O_LON_MM = 1400.0         # ô lớn hơn 1400 x 1400 mm: vẫn hatch, liệt kê để xem lại
DT_NHO_NHAT_M2 = 0.03     # ô nhỏ hơn coi là khe giữa 2 lớp tường
O_LUOI_MM = 20.0          # cạnh ô lưới quét dấu chân tường
LOI_MONG_MM = 30.0        # tường có lõi mỏng hơn (gạch ốp, lớp gỗ…) là lớp hoàn thiện → không coi là vách
NOI_HO_MM = 400.0         # đầu tường hở cách tường khác tới mức này thì nối (như Revit khép room)
DT_CO_BANG_CHUNG_M2 = 30.0   # ô có ống đứng / shaft opening: nhận tới diện tích này
TU_SAN_KC = ("sbt", "ket cau", "btct", "structural")   # sàn kết cấu: không dùng để loại ô
NHOM = "ARV_NganChay"
CAT_AN = (BuiltInCategory.OST_PlumbingFixtures, BuiltInCategory.OST_Furniture,
          BuiltInCategory.OST_FurnitureSystems, BuiltInCategory.OST_Casework)
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
    t = doc.GetElement(e.GetTypeId())
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


def theo_level(cat, lv):
    kq = []
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
        sk = doc.GetElement(f.SketchId)
        return [[(p.X, p.Y) for c in arr for p in list(c.Tessellate())[:-1]] for arr in sk.Profile]
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


def mat_day(e, opt):
    """Các mặt đáy (pháp tuyến hướng xuống) của khối đối tượng → list[list[vòng điểm 2D]]"""
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
        for e in FilteredElementCollector(doc, view.Id).OfCategory(cat).WhereElementIsNotElementType():
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
    for e in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_RoomSeparationLines) \
            .WhereElementIsNotElementType():
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


def tim_truc(view, lv, da_lam, viec, ghi_them):
    """Nhận trục / hộp kỹ thuật trên level của view → (se_lam, da_co, bi_loai, xem_lai).
    da_lam(v): ô đã làm rồi (đã hatch / đã có lỗ mở) → bỏ qua; viec: chữ trong báo cáo ("hatch", "tạo lỗ mở")"""
    z = lv.Elevation
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
    san = [s for s in san if s]
    ong = ong_dung(lv)
    shaft = [diem_tam(e) for e in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_ShaftOpening)
             .WhereElementIsNotElementType()]
    shaft = [p for p in shaft if p]
    loai = []
    for cat in (BuiltInCategory.OST_SpecialityEquipment, BuiltInCategory.OST_GenericModel,
                BuiltInCategory.OST_MechanicalEquipment, BuiltInCategory.OST_Stairs):
        for e in FilteredElementCollector(doc).OfCategory(cat).WhereElementIsNotElementType():
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
    for r in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType():
        if r.LevelId != lv.Id or r.Area <= 0 or r.Location is None:
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

    # ---- phân loại ----
    se_ve, da_co, bi_loai, xem_lai = [], 0, [], []
    for v in room_hkt + khe:
        pts = v["pts"]
        x, y = v["diem"]
        trong = lambda ds: [p for p in ds if trong_vung(p[0], p[1], pts)]
        if trong(loai) or any(r.IsPointInRoom(XYZ(x, y, z + mm(1000))) for r in room_loai):
            bi_loai.append((v, "thang máy / thang bộ"))
            continue
        if v["ten"]:
            nguon = "tên room '%s'" % v["ten"]
        elif any(trong_vung(x, y, r["pts"]) for r in room_hkt):
            continue          # đã nhận theo room đặt tên
        elif trong(cua) or trong(tb):
            continue
        elif trong(shaft):
            nguon = "shaft opening"
        elif trong(ong):
            nguon = "ống đứng"
        elif (not trong(cua_so) and not any(trong_vung(x, y, s_) for s_ in san)
              and v["m2"] <= DT_MAX_M2 and v["kt"][0] >= RONG_MIN_MM):
            nguon = "hình học"
        else:
            continue
        if da_lam(v):
            da_co += 1
            continue
        v["nguon"] = nguon
        se_ve.append(v)
        if v["kt"][0] > O_LON_MM:
            xem_lai.append(v)
    try:     # danh sách khoảng trống (mm) để vẽ ảnh đối chiếu khi cần
        import json
        with open(os.path.join(THU_MUC, "ngan_chay_vung.json"), "w", encoding="utf-8") as f:
            json.dump([{"m2": round(v["m2"], 3), "kt": [round(t) for t in v["kt"]], "nguon": v.get("nguon", ""),
                        "pts": [[(round(ra_mm(p[0])), round(ra_mm(p[1]))) for p in l] for l in v["pts"]]}
                       for v in room_hkt + khe], f, ensure_ascii=False)
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


def chon_hoac_tao_view():
    """IN[0] có tên → view đó. Không thì: view đang mở là view ngăn cháy lan → dùng; view đang mở là mặt bằng tầng → view
    ngăn cháy lan CÙNG TẦNG (tên view / template có chữ "ngăn cháy lan"), chưa có thì tạo (IN[18], sh_tao_view); còn lại như cũ."""
    v = chon_view_tang()
    if not DRY_RUN and v is not None:
        bao_cao.extend(sh_chuan_template(doc, v, "MẶT BẰNG NGĂN CHÁY LAN"))
    return v


def chon_view_tang():
    av = doc.ActiveView
    if TEN_VIEW or not TAO_VIEW or av is None or av.ViewType != ViewType.FloorPlan or av.GenLevel is None:
        return chon_view()
    la = lambda v: "chay lan" in khong_dau(ten_tpl(v)) or "chay lan" in khong_dau(v.Name)
    if la(av):
        return av
    cung = sorted([v for v in FilteredElementCollector(doc).OfClass(ViewPlan) if not v.IsTemplate and la(v)
                   and v.GenLevel is not None and v.GenLevel.Id.Value == av.GenLevel.Id.Value], key=lambda v: v.Name)
    if cung:
        return cung[0]
    v, bao = sh_tao_view(doc, av, "chay lan", "MẶT BẰNG NGĂN CHÁY LAN", DRY_RUN)
    bao_cao.extend(bao)
    return v


# ---------- chạy ----------
def chinh():
    view = chon_hoac_tao_view()
    lv = view.GenLevel
    if lv is None:
        raise Exception("View '%s' không gắn level" % view.Name)
    z = lv.Elevation
    bao_cao.append("View: %s (template %s, level %s)" % (view.Name, ten_tpl(view) or "-", lv.Name))

    da_hatch = []
    for r in FilteredElementCollector(doc, view.Id).OfClass(FilledRegion):
        if ten(doc.GetElement(r.GetTypeId())) == TEN_HATCH:
            try:
                da_hatch.append([diem_loop(list(cl)) for cl in r.GetBoundaries()])
            except Exception:
                pass
    se_ve, da_co, bi_loai, xem_lai = tim_truc(
        view, lv, lambda v: any(trong_vung(v["diem"][0], v["diem"][1], h) for h in da_hatch), "hatch",
        "hatch ngăn cháy đã có trong view: %d" % len(da_hatch))
    an = []
    if AN_THIET_BI:
        for cat in CAT_AN:
            for e in FilteredElementCollector(doc, view.Id).OfCategory(cat).WhereElementIsNotElementType():
                try:
                    if e.CanBeHidden(view) and not e.IsHidden(view):
                        an.append(e)
                except Exception:
                    pass
        bao_cao.append("Thiết bị vệ sinh / nội thất sẽ ẩn trong view: %d" % len(an))

    kieu, ghi_chu = lay_kieu_hatch() if se_ve else (None, "")
    gs, ghi_chu_net = lay_line_style() if se_ve else (None, "")
    if se_ve:
        bao_cao.append("Hatch: %s" % ghi_chu)
        bao_cao.append("Viền: %s" % ghi_chu_net)

    if DRY_RUN:
        TransactionManager.Instance.TransactionTaskDone()
        bao_cao.append("DRY-RUN: chưa vẽ gì. Đặt IN[4] = False để vẽ.")
        return view, []

    moi = []
    for v in se_ve:
        try:
            cls = NetList[CurveLoop]()
            for l in v["loops"]:
                cl = CurveLoop()
                for c in l:
                    cl.Append(c)
                cls.Add(cl)
            fr = FilledRegion.Create(doc, kieu.Id, view.Id, cls)
            if gs is not None:
                fr.SetLineStyleId(gs.Id)
            moi.append(fr.Id)
        except Exception as ex:
            bao_cao.append("Không hatch được ô %.2f m2 tại %s: %s" % (v["m2"], toa_do(v["diem"]), ex))
    nhom = None
    if moi:
        try:
            nhom = gom_nhom(moi, NHOM)
        except Exception as ex:
            bao_cao.append("Không gom group được: %s" % ex)
    if an:
        try:
            view.HideElements(ds_id([e.Id for e in an]))
            bao_cao.append("ĐÃ ẨN %d thiết bị vệ sinh / nội thất trong view" % len(an))
        except Exception as ex:
            bao_cao.append("Không ẩn được thiết bị: %s" % ex)
    TransactionManager.Instance.TransactionTaskDone()
    bao_cao.append("ĐÃ VẼ %d hatch ngăn cháy lan (Filled Region)%s" % (
        len(moi), (" – group '%s'" % nhom) if nhom else ""))
    return view, moi


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


def xuat_anh(view):
    try:
        TransactionManager.Instance.ForceCloseTransaction()
        opt = ImageExportOptions()
        opt.ExportRange = ExportRange.SetOfViews
        opt.SetViewsAndSheets(ds_id([view.Id]))
        opt.FilePath = os.path.join(THU_MUC, "ngan_chay")
        opt.ZoomType = ZoomFitType.FitToPage
        opt.PixelSize = 6000
        opt.ImageResolution = ImageResolution.DPI_300
        opt.HLRandWFViewsFileType = ImageFileType.PNG
        opt.ShadowViewsFileType = ImageFileType.PNG
        doc.ExportImage(opt)
        bao_cao.append("Ảnh: %s*.png" % opt.FilePath)
    except Exception as ex:
        bao_cao.append("Không xuất được ảnh: %s" % ex)


def len_ban_ve(view):
    """Đặt view ngăn cháy lan lên sheet, chú thích = kiểu hatch ngăn cháy (kèm viền) nếu có trong view."""
    muc = []
    if CHU_THICH:
        for r in FilteredElementCollector(doc, view.Id).OfClass(FilledRegion):
            t = doc.GetElement(r.GetTypeId())
            if ten(t) == TEN_HATCH:
                vien = None
                for sc in doc.Settings.Categories.get_Item(BuiltInCategory.OST_Lines).SubCategories:
                    if sc.Name == TEN_NET:
                        vien = sc.GetGraphicsStyle(GraphicsStyleType.Projection).Id
                muc.append({"vung": t.Id, "vien": vien, "chu": "NGĂN CHÁY LAN TRỤC / HỘP KỸ THUẬT"})
                break
    tang = view.GenLevel.Name if view.GenLevel is not None else view.Name
    gd, hm, kho, khung, so, ten_sh = SH_IN
    ten_sh = (ten_sh or "MẶT BẰNG NGĂN CHÁY LAN %s" % tang).strip().upper()
    bao_cao.extend(dat_mat_bang_len_sheet(doc, view, gd, hm, kho or "A1", khung, so, ten_sh, "A.NCL.00", muc))


try:
    v, moi = chinh()
    xuat_anh(v)
    if DAT_SHEET and not DRY_RUN:
        len_ban_ve(v)
except Exception:
    bao_cao.append("LỖI: " + traceback.format_exc())

log = os.path.join(THU_MUC, "ngan_chay_%s.txt" % datetime.now().strftime("%Y%m%d_%H%M%S"))
with open(log, "w", encoding="utf-8") as f:
    f.write("\n".join(bao_cao))
bao_cao.append("Log: " + log)
OUT = bao_cao
