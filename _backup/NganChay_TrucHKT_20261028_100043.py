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
    bao_cao.append("Trục / hộp kỹ thuật sẽ %s: %d (%s); đã có %s: %d; loại vì thang: %d" % (
        viec, len(se_ve), ", ".join("%s %d" % kv for kv in sorted(dem_nguon.items())) or "-", viec, da_co, len(bi_loai)))
    for v in sorted(se_ve, key=lambda v: -v["m2"]):
        bao_cao.append("   %5.2f m2  %4d x %4d mm  %-14s tại %s" % (
            v["m2"], round(v["kt"][0]), round(v["kt"][1]), v["nguon"], toa_do(v["diem"])))
    if xem_lai:
        bao_cao.append("CẦN XEM LẠI (ô lớn hơn %d x %d mm, vẫn %s): %s" % (
            O_LON_MM, O_LON_MM, viec, "; ".join("%.2f m2 tại %s" % (v["m2"], toa_do(v["diem"])) for v in xem_lai)))
    for v, ly_do in bi_loai:
        bao_cao.append("Loại (%s): %.2f m2 tại %s" % (ly_do, v["m2"], toa_do(v["diem"])))

    return se_ve, da_co, bi_loai, xem_lai


# ==== HẾT PHẦN CHUNG ====


# ---------- chạy ----------
def chinh():
    view = chon_view()
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


try:
    v, moi = chinh()
    xuat_anh(v)
except Exception:
    bao_cao.append("LỖI: " + traceback.format_exc())

log = os.path.join(THU_MUC, "ngan_chay_%s.txt" % datetime.now().strftime("%Y%m%d_%H%M%S"))
with open(log, "w", encoding="utf-8") as f:
    f.write("\n".join(bao_cao))
bao_cao.append("Log: " + log)
OUT = bao_cao
