# Hatch ngăn cháy lan trục / hộp kỹ thuật (Filled Region 2D) trên view mặt bằng chống cháy lan của Revit.
# Thể hiện theo skill CAD ngan-chay-truc-hkt: lưới NET 125 mm xoay 45° màu 220,30,30, viền tím (màu 6), chỉ hatch trong lòng ô.
#   - Vùng = ô khép kín bởi tường trên level của view (room có sẵn + room tạm NewRooms2 trong SubTransaction rồi rollback,
#     không để lại gì trong model); biên = mặt hoàn thiện trong lòng ô.
#   - Nhận trục / hộp kỹ thuật theo thứ tự bằng chứng:
#       a) tên room có từ khoá (HKT, hộp kỹ thuật, trục kỹ thuật, shaft…) hoặc chứa Shaft Opening
#       b) chứa ống / ống gió / ống luồn dây đi đứng, ô không có cửa đi và thiết bị vệ sinh
#       c) không có ống, dấu X trong model (như G19): ô kín KHÔNG có cửa đi, cửa sổ, thiết bị vệ sinh, sàn hoàn thiện,
#          diện tích ≤ ngưỡng, bề rộng lòng ≥ ngưỡng (suy luận hình học, người dùng xem ảnh duyệt)
#   - Loại: ô chứa thang máy / thang bộ (tên family / type / room có từ khoá loại trừ)
#   - Ô lớn hơn 1400 x 1400 mm vẫn hatch nhưng liệt kê riêng để xem lại (như bản CAD)
#   - Kiểu Filled Region + mẫu lưới + line style viền chưa có thì tự tạo; Filled Region gom group "ARV_NganChay"
#   - Ẩn thiết bị vệ sinh / nội thất trong view (Hide in View từng đối tượng, không sửa template)
#   - Bấm lại: ô đã có hatch cùng kiểu thì bỏ qua, không vẽ trùng, không xoá gì
# Dry-run (mặc định) chỉ báo cáo, không sửa mô hình.
# INPUT
#   IN[0] (str)   Tên view (để trống = view đang mở nếu là view chống cháy lan, không thì view đầu tiên có chữ "cháy lan" trong tên view / template)
#   IN[1] (str)   Từ khoá tên room là trục / hộp kỹ thuật, cách nhau bằng ;  (không phân biệt dấu / hoa thường)
#   IN[2] (float) Diện tích lớn nhất của ô kín nhận theo hình học (m2)
#   IN[3] (float) Bề rộng lòng nhỏ nhất của ô (mm)
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
DT_MAX_M2 = float(gia_tri(2, 6.0))
RONG_MIN_MM = float(gia_tri(3, 200.0))
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
DT_NHO_NHAT_M2 = 0.05     # ô nhỏ hơn coi là khe tường
NHOM = "ARV_NganChay"
CAT_AN = (BuiltInCategory.OST_PlumbingFixtures, BuiltInCategory.OST_Furniture,
          BuiltInCategory.OST_FurnitureSystems, BuiltInCategory.OST_Casework)
bao_cao = []


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


def toa_do(p):
    return "(%d, %d)" % (round(ra_mm(p[0])), round(ra_mm(p[1])))


# ---------- chạy ----------
def chinh():
    view = chon_view()
    lv = view.GenLevel
    if lv is None:
        raise Exception("View '%s' không gắn level" % view.Name)
    z = lv.Elevation
    bao_cao.append("View: %s (template %s, level %s)" % (view.Name, ten_tpl(view) or "-", lv.Name))

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
    da_hatch = []
    for r in FilteredElementCollector(doc, view.Id).OfClass(FilledRegion):
        if ten(doc.GetElement(r.GetTypeId())) == TEN_HATCH:
            try:
                da_hatch.append([diem_loop(list(cl)) for cl in r.GetBoundaries()])
            except Exception:
                pass
    bao_cao.append("Trên level: cửa đi %d, cửa sổ %d, thiết bị vệ sinh %d, sàn hoàn thiện %d, ống đứng %d, "
                   "shaft opening %d, thang máy / thang bộ %d; hatch ngăn cháy đã có trong view: %d" % (
                       len(cua) // 2, len(cua_so) // 2, len(tb), len(san), len(ong), len(shaft), len(loai),
                       len(da_hatch)))
    if not ong and not shaft:
        bao_cao.append("Model không có ống đứng / shaft opening → trục, hộp nhận theo tên room hoặc hình học "
                       "(ô kín không cửa, cửa sổ, thiết bị, sàn) – xem ảnh để duyệt (Cần xác nhận lại).")

    # ---- các ô khép kín: room có sẵn + room tạm (rollback) ----
    TransactionManager.Instance.EnsureInTransaction(doc)
    vung = []
    st = SubTransaction(doc)
    st.Start()
    try:
        co_san = set(r.Id.Value for r in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms)
                     .WhereElementIsNotElementType() if r.LevelId == lv.Id)
        try:
            doc.Create.NewRooms2(lv)
        except Exception as ex:
            bao_cao.append("Không tạo được room tạm: %s" % ex)
        doc.Regenerate()
        opt = SpatialElementBoundaryOptions()
        opt.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.Finish
        for r in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType():
            if r.LevelId != lv.Id or r.Area <= 0 or r.Location is None:
                continue
            loops = []
            for segs in r.GetBoundarySegments(opt) or []:
                l = [phang(s.GetCurve(), z) for s in segs]
                if len(l) >= 2:
                    loops.append(l)
            if not loops:
                continue
            ten_r = r.get_Parameter(BuiltInParameter.ROOM_NAME).AsString() if r.Id.Value in co_san else ""
            p0 = r.Location.Point
            vung.append({"loops": loops, "pts": [diem_loop(l) for l in loops], "m2": ra_m2(r.Area),
                         "ten": ten_r or "", "diem": (p0.X, p0.Y)})
    finally:
        st.RollBack()
    bao_cao.append("Ô khép kín trên level: %d" % len(vung))

    # ---- phân loại ----
    se_ve, da_co, bi_loai, xem_lai = [], 0, [], []
    for v in vung:
        pts = v["pts"]
        x, y = v["diem"]
        trong = lambda ds: [p for p in ds if trong_vung(p[0], p[1], pts)]
        rong, dai = kich_thuoc(max(pts, key=len))
        v["kt"] = (ra_mm(rong), ra_mm(dai))
        if v["ten"] and co_tu(v["ten"], TU_KHOA_LOAI) or trong(loai):
            if v["m2"] < 30:
                bi_loai.append((v, "thang máy / thang bộ"))
            continue
        if v["ten"] and co_tu(v["ten"], TU_KHOA_HKT):
            nguon = "tên room '%s'" % v["ten"]
        elif trong(shaft):
            nguon = "shaft opening"
        elif trong(ong) and not trong(cua) and not trong(tb):
            nguon = "ống đứng"
        elif v["ten"] and khong_dau(v["ten"]) not in ("room", "phong"):
            continue          # room đã đặt tên chức năng khác (phòng ngủ, WC…)
        elif (not trong(cua) and not trong(cua_so) and not trong(tb)
              and not any(trong_vung(x, y, s) for s in san)
              and DT_NHO_NHAT_M2 <= v["m2"] <= DT_MAX_M2 and v["kt"][0] >= RONG_MIN_MM):
            nguon = "hình học"
        else:
            continue
        if any(trong_vung(x, y, h) for h in da_hatch):
            da_co += 1
            continue
        v["nguon"] = nguon
        se_ve.append(v)
        if v["kt"][0] > O_LON_MM:
            xem_lai.append(v)
    dem_nguon = {}
    for v in se_ve:
        dem_nguon[v["nguon"].split(" '")[0]] = dem_nguon.get(v["nguon"].split(" '")[0], 0) + 1
    bao_cao.append("Trục / hộp kỹ thuật sẽ hatch: %d (%s); đã có hatch: %d; loại vì thang: %d" % (
        len(se_ve), ", ".join("%s %d" % kv for kv in sorted(dem_nguon.items())) or "-", da_co, len(bi_loai)))
    for v in sorted(se_ve, key=lambda v: -v["m2"]):
        bao_cao.append("   %5.2f m2  %4d x %4d mm  %-14s tại %s" % (
            v["m2"], round(v["kt"][0]), round(v["kt"][1]), v["nguon"], toa_do(v["diem"])))
    if xem_lai:
        bao_cao.append("CẦN XEM LẠI (ô lớn hơn %d x %d mm, vẫn hatch): %s" % (
            O_LON_MM, O_LON_MM, "; ".join("%.2f m2 tại %s" % (v["m2"], toa_do(v["diem"])) for v in xem_lai)))
    for v, ly_do in bi_loai:
        bao_cao.append("Loại (%s): %.2f m2 tại %s" % (ly_do, v["m2"], toa_do(v["diem"])))

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
