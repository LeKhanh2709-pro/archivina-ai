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
#                 2026-11-05: KHÔNG tạo / sửa view template nữa, view mới gán template IN[19] (trống = template có chữ
#                 khoá nếu có, không thì giữ template của view gốc)
#   IN[19] (str)  View template gán cho view (trống = giữ; "<Không dùng view template>" = bỏ template; nút hỏi trong
#                 hộp thoại, người dùng yêu cầu 2026-11-05)
#   IN[20] (float) Tỉ lệ view, mẫu số (0 = giữ; template khoá tỉ lệ thì theo template)
#   IN[21] (bool) Không dùng CAD link (chỉ nhận trục theo Revit). Mặc định tắt = mặt bằng đang mở / view ngăn cháy
#                 lan có file CAD link thì nhận trục / hộp kỹ thuật theo CAD (người dùng yêu cầu 2026-11-11, model Site
#                 HQV: "áp dụng tương tự [chống thấm] với ngăn cháy lan"): bộ nhận diện của skill ngan-chay-truc-hkt
#                 (dwg_to_dxf.ps1 + tim_truc_ky_thuat.py: dấu X, ống đứng, khung lỗ mở MEP; loại cabin thang máy) →
#                 biên ô đổi toạ độ CAD → model; KHÔNG quét tường / room / ống Revit. Không có CAD link thì như cũ.
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


TPL_CHON = str(gia_tri(19, "")).strip()      # view template chọn trong hộp thoại (2026-11-05)
TI_LE = int(round(float(gia_tri(20, 0) or 0)))  # tỉ lệ chọn (0 = giữ)
VUA_TAO = set()                                # Id view vừa tạo (đã gán template / tỉ lệ trong sh_tao_view)
CROP_MO = set()                                # Id view có sẵn công cụ vừa bật crop (được nới crop theo phần đã vẽ)


def chon_hoac_tao_view():
    """IN[0] có tên → view đó. Không thì: view đang mở là view ngăn cháy lan → dùng; view đang mở là mặt bằng tầng → view
    ngăn cháy lan CÙNG TẦNG (tên view / template có chữ "ngăn cháy lan"), chưa có thì tạo (IN[18], sh_tao_view); còn lại như cũ."""
    v = chon_view_tang()
    if v is None or (v.Id.Value in VUA_TAO):
        return v
    # View có sẵn đang TẮT crop → bật crop = khung bao tường (như view công cụ tạo). Site HQV 2026-11-11: view
    # "MẶT BẰNG CHONG CHAY LAN" có sẵn thấy cả CAD hầm → khung mặt bằng 12409 x 4555 mm giấy, sheet trống. View đã
    # có crop (người dùng chỉnh) thì giữ nguyên.
    try:
        crop_tat = v.ViewType == ViewType.FloorPlan and not v.CropBoxActive
    except Exception:
        crop_tat = False
    if DRY_RUN:
        if TPL_CHON or TI_LE:
            bao_cao.append(u"Sẽ gán view template '%s', tỉ lệ %s cho '%s'." % (TPL_CHON or u"(giữ)",
                                                                           u"1:%d" % TI_LE if TI_LE else u"(giữ)", v.Name))
        if crop_tat:
            bao_cao.append(u"View '%s' đang tắt crop – sẽ bật crop theo khung tường." % v.Name)
        return v
    if not (TPL_CHON or TI_LE or crop_tat):
        return v
    TransactionManager.Instance.EnsureInTransaction(doc)
    if TPL_CHON or TI_LE:
        bao_cao.extend(sh_ap_tpl_tl(doc, v, TPL_CHON, TI_LE))
    if crop_tat:
        try:
            bao_cao.append(u"View có sẵn '%s' đang tắt crop → bật crop. %s" % (v.Name, sh_crop_theo_tuong(doc, v)))
            CROP_MO.add(v.Id.Value)
        except Exception as ex:
            bao_cao.append(u"View '%s' đang tắt crop, không bật được crop: %s" % (v.Name, (u"%s" % ex).splitlines()[0][:150]))
    TransactionManager.Instance.TransactionTaskDone()
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
    v, bao = sh_tao_view(doc, av, "chay lan", "MẶT BẰNG NGĂN CHÁY LAN", DRY_RUN, TPL_CHON, TI_LE)
    bao_cao.extend(bao)
    if not DRY_RUN:
        VUA_TAO.add(v.Id.Value)
    return v


# ---------- nguồn CAD link (người dùng yêu cầu 2026-11-11, như nút Chống thấm) ----------
# Mặt bằng có file CAD link (ImportInstance IsLinked) → nhận trục / hộp kỹ thuật bằng bộ nhận diện của skill CAD
# ngan-chay-truc-hkt (đã kiểm chứng HQV tháp B tầng 4: 116 ô): chay_cho_revit.ps1 chép bản sao DWG → DXF (Core Console)
# → tim_truc_ky_thuat.py → <tên>_vung.json (ô: dinh = 4+ đỉnh, toạ độ DWG mm; trang_thai se_hatch / loai / da_co).
# Chỉ vẽ ô "se_hatch"; ô "loai" (trùng cabin thang máy, lỗ mở không ống) chỉ báo. Kết quả lưu theo (đường dẫn, cỡ, giờ
# sửa) DWG ở <THU_MUC>\cad\ → bấm lại không chạy lại AutoCAD. Xref chưa bind trong DWG: DXFOUT không có nội dung xref
# (giới hạn của skill CAD) → trục trong xref không thấy.
CAD_NGUON = not bool(gia_tri(21, False))
CAD_CHO_TOI_DA_S = 2400


def cad_tim(views, lv=None):
    """[(view, ImportInstance, đường dẫn DWG)] của CAD link trong view đầu tiên có CAD link (CAD "Current view only" ưu
    tiên). Không view nào có: CAD đặt riêng cho mặt bằng khác CÙNG TẦNG lv; ≥ 2 file khác nhau thì dừng, báo."""
    def cua(ii):
        if not ii.IsLinked:
            return None
        try:
            t = doc.GetElement(ii.GetTypeId())
            p = ModelPathUtils.ConvertModelPathToUserVisiblePath(t.GetExternalFileReference().GetAbsolutePath())
        except Exception:
            return None
        return p if p and p.lower().endswith(".dwg") else None
    for v in views:
        if v is None:
            continue
        ds = [(v, ii, cua(ii)) for ii in FilteredElementCollector(doc, v.Id).OfClass(ImportInstance) if cua(ii)]
        rieng = [x for x in ds if x[1].ViewSpecific and x[1].OwnerViewId.Value == v.Id.Value]
        if rieng or ds:
            return rieng or ds
    if lv is not None:
        ds = []
        for ii in FilteredElementCollector(doc).OfClass(ImportInstance):
            if not ii.ViewSpecific or not cua(ii):
                continue
            ov = doc.GetElement(ii.OwnerViewId)
            if (ov is not None and getattr(ov, "GenLevel", None) is not None and not ov.IsTemplate
                    and ov.ViewType == ViewType.FloorPlan and ov.GenLevel.Id.Value == lv.Id.Value):
                if not any(x[2].lower() == cua(ii).lower() for x in ds):
                    ds.append((ov, ii, cua(ii)))
        if len(ds) > 1:
            raise Exception(u"Tầng %s có %d file CAD link đặt ở các mặt bằng khác nhau (%s) – không biết dựa theo bản nào. "
                            u"Mở mặt bằng có đúng file CAD cần dùng rồi bấm lại (hoặc bật IN[21] Không dùng CAD link)." % (
                                lv.Name, len(ds), u"; ".join(u"'%s' trong view '%s'" % (os.path.basename(x[2]), x[0].Name)
                                                            for x in ds)))
        return ds
    return []


def cad_script():
    """chay_cho_revit.ps1 của skill ngan-chay-truc-hkt (không gắn cứng ổ / thư mục)."""
    goc = []
    if os.environ.get("ARCHIVINA_AI"):
        goc.append(os.environ["ARCHIVINA_AI"])
    goc.append(os.path.expanduser("~"))
    for o in "CDEFGHIJKLMNOPQRSTUVWXYZ":
        if os.path.isdir(o + ":\\AI"):
            goc.append(o + ":\\AI")
    for g in goc:
        p = os.path.join(g, ".claude", "skills", "ngan-chay-truc-hkt", "scripts", "chay_cho_revit.ps1")
        if os.path.isfile(p):
            return p
    return None


def io_doc(p):
    import io
    with io.open(p, encoding="utf-8", errors="replace") as f_:
        return f_.read()


def cad_nhan_dien(duong):
    """Chạy (hoặc lấy kết quả đã có) bộ nhận diện cho 1 DWG → (dict json, thư mục, đã có sẵn?)."""
    import glob
    import hashlib
    import json
    import subprocess
    st = os.stat(duong)
    # Khoá đệm gồm cả nội dung script nhận diện (*.py, *.ps1 cạnh ps1): sửa bộ nhận diện thì lần bấm sau tự chạy lại, không
    # dùng kết quả cũ (2026-11-12, sửa nhận diện theo góp ý người dùng trên Site HQV).
    ban = hashlib.md5()
    ps1_ = cad_script()
    if ps1_:
        for f_ in sorted(glob.glob(os.path.join(os.path.dirname(ps1_), "*.py")) + glob.glob(os.path.join(os.path.dirname(ps1_), "*.ps1"))):
            with open(f_, "rb") as h_:
                ban.update(h_.read())
    khoa = hashlib.md5((u"%s|%d|%d|%s" % (duong.lower(), st.st_size, int(st.st_mtime), ban.hexdigest())).encode("utf-8")).hexdigest()[:10]
    ten_f = "".join(c if (c.isalnum() and ord(c) < 128) or c in "-_" else "_" for c in os.path.splitext(os.path.basename(duong))[0])
    od = os.path.join(THU_MUC, "cad", "%s_%s" % (ten_f[:40], khoa))
    xong = os.path.join(od, "xong.txt")
    js = glob.glob(os.path.join(od, "*_vung.json"))
    if js and os.path.isfile(xong) and io_doc(xong).strip().startswith("OK"):
        return json.loads(io_doc(js[0])), od, True
    ps1 = cad_script()
    if ps1 is None:
        raise Exception(u"Không tìm thấy bộ nhận diện ngăn cháy CAD (chay_cho_revit.ps1 của skill ngan-chay-truc-hkt trong "
                        u"<ổ>:\\AI\\.claude\\skills). Chép thư mục skill của máy chính sang, hoặc bật IN[21] Không dùng CAD link.")
    os.makedirs(od, exist_ok=True)
    if os.path.isfile(xong):
        os.rename(xong, xong + ".%s" % datetime.now().strftime("%H%M%S"))     # lần trước lỗi: giữ lại, không xoá
    cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1, "-Dwg", duong, "-OutDir", od]
    try:
        subprocess.run(cmd, timeout=CAD_CHO_TOI_DA_S, creationflags=0x08000000,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        raise Exception(u"Nhận diện CAD quá %d phút: %s (nhật ký %s)" % (CAD_CHO_TOI_DA_S // 60, duong, os.path.join(od, "nhat_ky.txt")))
    kq = io_doc(xong).strip() if os.path.isfile(xong) else u"không có xong.txt"
    js = glob.glob(os.path.join(od, "*_vung.json"))
    if not kq.startswith("OK") or not js:
        raise Exception(u"Nhận diện CAD lỗi (%s) – xem %s" % (kq[:200], os.path.join(od, "nhat_ky.txt")))
    return json.loads(io_doc(js[0])), od, False


def cad_truc(view, lv, da_lam):
    """Trục / hộp kỹ thuật theo CAD link → (se_ve, da_co, bi_loai, xem_lai) như tim_truc; None = không có CAD link."""
    ds = cad_tim([doc.ActiveView, view], lv)
    if not ds:
        return None
    z = lv.Elevation
    del VIEW_LINK[:]
    VIEW_LINK.append(view)
    se_ve, da_co, bi_loai, xem_lai = [], 0, [], []

    def diem(tf, q):
        p = tf.OfPoint(XYZ(mm(q[0]), mm(q[1]), 0))
        return XYZ(p.X, p.Y, z)
    for v_, ii, duong in ds:
        bao_cao.append(u"NGUỒN CAD: '%s' (view '%s') – nhận trục / hộp theo CAD, không quét tường / room / ống Revit." % (
            duong, v_.Name))
        if not os.path.isfile(duong):
            raise Exception(u"Không thấy file CAD link: %s (Reload CAD trong Manage Links, hoặc bật IN[21] Không dùng CAD link)" % duong)
        js, od, san = cad_nhan_dien(duong)
        bao_cao.append(u"   Kết quả nhận diện %s: %s" % (u"đã có (DWG không đổi)" if san else u"mới chạy", od))
        tf = ii.GetTotalTransform()
        dem = {}
        for o in js.get("vung", []):
            tt = o.get("trang_thai")
            ps = [diem(tf, q) for q in o.get("dinh", [])]
            if len(ps) > 2 and ps[0].DistanceTo(ps[-1]) < mm(1):
                ps = ps[:-1]
            if len(ps) < 3:
                continue
            pts = [(p.X, p.Y) for p in ps]
            cx, cy = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
            v = {"pts": [pts], "m2": float(o.get("dien_tich_m2") or 0), "diem": (cx, cy), "ten": "",
                 "kt": tuple(sorted((float(o.get("rong") or 0), float(o.get("dai") or 0)))),
                 "nguon": u"CAD: %s" % (o.get("kieu") or u"")}
            if tt == "loai":
                bi_loai.append((v, u"CAD: %s" % (o.get("ghi_chu") or o.get("kieu") or u"loại")))
                continue
            if tt == "da_co":
                da_co += 1
                continue
            if tt != "se_hatch":
                continue
            try:
                v["loops"] = [[Line.CreateBound(ps[k], ps[(k + 1) % len(ps)]) for k in range(len(ps))
                               if ps[k].DistanceTo(ps[(k + 1) % len(ps)]) >= mm(1)]]
            except Exception as ex:
                bao_cao.append(u"   Ô CAD %s: không dựng được biên (%s)" % (o.get("id"), ex))
                continue
            if da_lam(v):
                da_co += 1
                continue
            se_ve.append(v)
            dem[o.get("kieu") or u"?"] = dem.get(o.get("kieu") or u"?", 0) + 1
            if v["kt"][0] > O_LON_MM:
                xem_lai.append(v)
        bao_cao.append(u"   Ô sẽ hatch: %d (%s)" % (sum(dem.values()), u"; ".join(u"%s %d" % kv for kv in sorted(dem.items())) or u"-"))
        if js.get("ong_chua_bo"):
            bao_cao.append(u"   CẦN XEM LẠI: %d ống đứng trong CAD chưa có khung / dấu X (không vẽ)" % len(js["ong_chua_bo"]))
    bao_cao.append(u"Trục / hộp kỹ thuật cần hatch (theo CAD): %d; đã có hatch: %d; loại: %d" % (len(se_ve), da_co, len(bi_loai)))
    for v in sorted(se_ve, key=lambda v: -v["m2"]):
        bao_cao.append(u"   %5.2f m2  %4d x %4d mm  %-30s tại %s" % (v["m2"], round(v["kt"][0]), round(v["kt"][1]), v["nguon"],
                                                                   toa_do(v["diem"])))
    if xem_lai:
        bao_cao.append(u"CẦN XEM LẠI (ô lớn hơn %d x %d mm, vẫn nhận): %s" % (
            O_LON_MM, O_LON_MM, u"; ".join(u"%.2f m2 tại %s" % (v["m2"], toa_do(v["diem"])) for v in xem_lai)))
    dem_l = {}
    for _, ly in bi_loai:
        dem_l[ly] = dem_l.get(ly, 0) + 1
    if dem_l:
        bao_cao.append(u"Loại: %s" % u"; ".join(u"%s %d" % kv for kv in sorted(dem_l.items())))
    TransactionManager.Instance.EnsureInTransaction(doc)     # như tim_truc: transaction mở tới cuối chinh()
    return se_ve, da_co, bi_loai, xem_lai


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
    da_lam = lambda v: any(trong_vung(v["diem"][0], v["diem"][1], h) for h in da_hatch)
    cad = cad_truc(view, lv, da_lam) if CAD_NGUON else None
    if cad is not None:
        se_ve, da_co, bi_loai, xem_lai = cad
        bao_cao.append("hatch ngăn cháy đã có trong view: %d" % len(da_hatch))
    else:
        se_ve, da_co, bi_loai, xem_lai = tim_truc(
            view, lv, da_lam, "hatch", "hatch ngăn cháy đã có trong view: %d" % len(da_hatch))
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

    # Hatch 1 đối tượng (người dùng yêu cầu 2026-11-12): mọi ô vào MỘT Filled Region; vùng cũ tách rời trong view thì
    # hỏi gộp (sh_ve_hatch_gop, khối PHẦN CHUNG ĐẶT SHEET)
    if kieu is None:
        kieu = next((t for t in FilteredElementCollector(doc).OfClass(FilledRegionType) if ten(t) == TEN_HATCH), None)
    if DRY_RUN:
        if kieu is not None:
            sh_ve_hatch_gop(doc, view, kieu.Id, [v["loops"] for v in se_ve], NHOM, bao_cao, dry=True)
        TransactionManager.Instance.TransactionTaskDone()
        bao_cao.append("DRY-RUN: chưa vẽ gì. Đặt IN[4] = False để vẽ.")
        return view, []

    moi = []
    if kieu is not None:
        try:
            moi = sh_ve_hatch_gop(doc, view, kieu.Id, [v["loops"] for v in se_ve], NHOM, bao_cao,
                                  gs_id=gs.Id if gs is not None else None)
        except Exception as ex:
            bao_cao.append("Không hatch được: %s" % str(ex).splitlines()[0])
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
    if AN_THIET_BI and any(lk_thay(doc, view, c_, True) for c_ in CAT_AN):
        try:
            bao_cao.append(lk_an_bang_filter(doc, view, u"ARV_Ẩn thiết bị vệ sinh, nội thất (link)", list(CAT_AN)))
        except Exception as ex:
            bao_cao.append("Không ẩn được thiết bị trong link: %s" % ex)
    TransactionManager.Instance.TransactionTaskDone()
    bao_cao.append("ĐÃ VẼ %d Filled Region ngăn cháy lan (%d ô)%s" % (
        len(moi), len(se_ve), (" – group '%s'" % nhom) if nhom else ""))
    return view, moi


# ==== PHẦN CHUNG ĐẶT SHEET (nguồn: DatSheet_chung.py, chép vào file công cụ bằng gop_dat_sheet.py – sửa ở nguồn) ====
# Đặt mặt bằng vừa vẽ lên bản vẽ (người dùng yêu cầu 2026-11-03 cho Chống thấm + Ngăn cháy lan, cùng cách nút Tag cửa):
#   - Tạo sheet: khung tên theo khổ (A1 / A0), số hiệu (trống = tiếp theo trong hạng mục), tên, gán giai đoạn / hạng mục
#     theo cách nhóm sheet trong Project Browser của dự án (giống cap_thu_muc_sheet / ts_giai_doan của TagCua_TuDong.py).
#   - Mặt bằng đặt GIỮA vùng vẽ, giữ nguyên tỉ lệ của view (không sửa view template), "Title on Sheet" = tên sheet nếu
#     đang trống. View đã nằm trên sheet thì không đặt thêm.
#   - Thu trục của file hiện tại trong view về sát quanh nhà (đầu trục ViewSpecific, cách mép tường SH_TRUC_DU_MM giấy)
#     để khung viewport không bị trục dài đẩy lệch / tràn khổ (thử G19: trục A, X1 làm khung rộng 720 > 681 mm).
#   - Bảng ghi chú (Diện tích | Ký hiệu | Tên vị trí) vẽ trong drafting view "BẢNG GHI CHÚ - <tên sheet>" cùng tỉ lệ mặt bằng (mẫu
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
#   ĐỔI 2026-11-05 (người dùng yêu cầu): KHÔNG tạo / sửa view template nữa (bỏ phần tạo template ở trên). Hộp thoại nút
#   hỏi View template + Tỉ lệ → sh_ap_tpl_tl gán đúng template đã chọn (hoặc bỏ template) + tỉ lệ cho view (mới hoặc đã
#   có); template khoá tỉ lệ thì giữ tỉ lệ template, chỉ báo. sh_chuan_template không còn làm gì.
# Hàm, hằng ở khối này có tiền tố sh_ / SH_ để không trùng tên với file công cụ.
SH_BIEN_MM = 8.0             # lề trong vùng vẽ của khung tên (mm giấy)
SH_TIEU_DE_MM = 15.0         # chỗ tên view dưới viewport
SH_O_MAU_MM = (16.0, 7.0)    # ô mẫu chú thích (rộng, cao) mm giấy
SH_DONG_MM = 11.0            # khoảng cách dòng chú thích
SH_KHE_CHU_MM = 4.0          # khe giữa ô mẫu và chữ
SH_BANG_COT_MM = (24.0, 22.0, 78.0)   # Bảng ghi chú: rộng cột Diện tích / Ký hiệu / Tên vị trí, mm giấy
SH_BANG_TIEU_DE_MM = 9.0     # cao dòng tên bảng, dòng tiêu đề cột
SH_BANG_HANG_MM = 12.0       # cao mỗi hàng
SH_BANG_LE_MM = 2.0          # lề chữ cột Tên vị trí
SH_TEN_BANG = u"BẢNG GHI CHÚ"
SH_TEN_CHU_THICH_CU = u"CHÚ THÍCH"   # view chú thích bản trước 2026-11-09 (không có diện tích)
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
    for w in list(FilteredElementCollector(doc, view.Id).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()) + lk_thay(doc, view, BuiltInCategory.OST_Walls, True):
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


def sh_dien_tich(doc, view, id_kieu):
    """Tổng diện tích (m2) các Filled Region kiểu id_kieu trong view. Có vùng không đọc được thì None (ghi [Chờ bổ sung])."""
    tong = 0.0
    for r in FilteredElementCollector(doc, view.Id).OfClass(FilledRegion):
        if r.GetTypeId().Value != id_kieu.Value:
            continue
        p = r.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
        if p is None or not p.HasValue:
            return None
        tong += UnitUtils.ConvertFromInternalUnits(p.AsDouble(), UnitTypeId.SquareMeters)
    return tong


def sh_chu_dt(m2):
    return u"%.1f m²" % m2 if m2 is not None else u"[Chờ bổ sung]"


# ---- Hatch 1 đối tượng cho cả view (người dùng yêu cầu 2026-11-12: "các đường bo chỉ trong 1 lệnh để kiểm soát được
#   diện tích, không tách mỗi trục / mỗi WC thành 1 hatch"): mọi vòng biên chống thấm / ngăn cháy lan của view nằm trong
#   MỘT Filled Region. Thử trên bản sao Site: API KHÔNG sửa được sketch Filled Region (SketchEditScope.Start báo "Sketch
#   does not support editing") → bấm lại có vùng mới, hoặc view còn nhiều vùng cũ tách rời, thì tạo 1 vùng chứa đủ biên
#   cũ + mới rồi XOÁ vùng cũ, CHỈ khi người dùng đồng ý trong hộp thoại (liệt kê id). Vòng chồng / chạm nhau (Site
#   Tầng 1, 5BA: FilledRegion.Create báo "curve loops intersect") được hợp bằng khối đùn mỏng + BooleanOperationsUtils,
#   chỗ chồng chỉ tính 1 lần. Vùng cũ nằm trong group không phải của công cụ thì giữ nguyên, không gộp.
SH_DAY_KHOI = 1.0            # bề dày khối đùn tạm để hợp vòng (feet, không tạo phần tử)
SH_NAN_MM = 1.0              # nắn đỉnh lệch < 1 mm trước khi hợp (sh_nan)


def sh_cl(loops):
    """[[Curve]] → list CurveLoop"""
    kq = []
    for l in loops:
        cl = CurveLoop()
        for c in l:
            cl.Append(c)
        kq.append(cl)
    return kq


def sh_ds_cl(cls):
    ds = NetList[CurveLoop]()
    for cl in cls:
        ds.Add(cl)
    return ds


def sh_doi_goc(muc):
    """Phép dời điểm đầu của các mục về gốc toạ độ: Boolean của Revit mất chính xác khi hình cách gốc xa (thử Site HQV
    ~2,4 km: hợp 1 ô hộp kỹ thuật 500 x 1600 báo lỗi, dời về gần gốc thì được)"""
    for m in muc:
        for l in m:
            for c in l:
                return Transform.CreateTranslation(c.GetEndPoint(0).Negate())
    return Transform.Identity


def sh_nan(muc, tol_mm=SH_NAN_MM):
    """Nắn toạ độ X / Y các đỉnh lệch nhau < tol_mm về cùng 1 giá trị (vòng toàn đoạn thẳng; vòng có cung giữ nguyên).
    Lý do (thử Site HQV Tầng 1): ô CAD cạnh 500 mm lệch 0,5 mm chạm đỉnh ô bên cạnh → mảnh chồng siêu mỏng, Boolean
    Revit báo lỗi, ô không hợp được. Hình dời tối đa tol_mm."""
    tol = sh_ft(tol_mm)

    def bang(vals):
        m, nhom = {}, None
        for v in sorted(set(vals)):
            if nhom is None or v - nhom > tol:
                nhom = v
            m[v] = nhom
        return m
    xs, ys = [], []
    for m in muc:
        for l in m:
            for c in l:
                p = c.GetEndPoint(0)
                xs.append(p.X)
                ys.append(p.Y)
    bx, by = bang(xs), bang(ys)
    kq = []
    for m in muc:
        moi = []
        for l in m:
            try:
                if any(c.GetType().Name != "Line" for c in l):
                    raise Exception("có cung")
                pts = []
                for c in l:
                    p = c.GetEndPoint(0)
                    q = XYZ(bx[p.X], by[p.Y], p.Z)
                    if not pts or q.DistanceTo(pts[-1]) > tol * 0.01:
                        pts.append(q)
                if len(pts) > 1 and pts[0].DistanceTo(pts[-1]) <= tol * 0.01:
                    pts.pop()
                if len(pts) < 3:
                    raise Exception("suy biến")
                moi.append([Line.CreateBound(pts[k], pts[(k + 1) % len(pts)]) for k in range(len(pts))])
            except Exception:
                moi.append(list(l))
        kq.append(moi)
    return kq


def sh_khoi(m, T):
    """Mục [[Curve]] → khối đùn mỏng đã dời bằng T (chỉ để tính hình học, không tạo phần tử)"""
    ds = NetList[CurveLoop]()
    for cl in sh_cl(m):
        ds.Add(CurveLoop.CreateViaTransform(cl, T))
    return GeometryCreationUtilities.CreateExtrusionGeometry(ds, XYZ.BasisZ, SH_DAY_KHOI)


def sh_hop_khoi(muc, T):
    """Hợp khối các mục (đã dời bằng T) → (khối hợp | None, list chỉ số mục không dựng / hợp được)"""
    khoi, loi = None, []
    for i, m in enumerate(muc):
        try:
            s = sh_khoi(m, T)
            khoi = s if khoi is None else BooleanOperationsUtils.ExecuteBooleanOperation(
                khoi, s, BooleanOperationsType.Union)
        except Exception:
            loi.append(i)
    return khoi, loi


def sh_mat_day(khoi, T):
    """Vòng biên mặt đáy (= mặt phẳng hatch) của khối hợp, dời ngược T về chỗ cũ"""
    vong = []
    if khoi is not None:
        for fc in khoi.Faces:
            try:
                bb = fc.GetBoundingBox()
                if fc.ComputeNormal((bb.Min + bb.Max) / 2.0).Z < -0.99:
                    vong.extend(CurveLoop.CreateViaTransform(cl, T.Inverse) for cl in fc.GetEdgesAsCurveLoops())
            except Exception:
                pass
    return vong


def sh_vi_tri(m):
    """Chữ vị trí + diện tích gần đúng của 1 mục để báo cáo"""
    try:
        p = m[0][0].GetEndPoint(0)
        return u"(%.0f, %.0f)" % (sh_mm(p.X), sh_mm(p.Y))
    except Exception:
        return u"?"


def sh_tao_vung(doc, kieu_id, view, muc, bao, giu=0):
    """Tạo MỘT Filled Region chứa mọi mục: thử nguyên vòng; lỗi (vòng chồng / chạm) thì hợp khối; mục không hợp được thì
    thử thêm nguyên vòng của nó vào vùng gộp, vẫn lỗi thì để riêng: mục cũ (chỉ số < giu) giữ nguyên vùng cũ, mục mới vẽ
    riêng. Trả về (list id đã tạo, list chỉ số mục không vào vùng gộp, có vùng gộp hay không)."""
    if not muc:
        return [], [], False
    tat_ca = [cl for m in muc for cl in sh_cl(m)]
    try:
        fr = FilledRegion.Create(doc, kieu_id, view.Id, sh_ds_cl(tat_ca))
        bao.append(u"Gộp 1 Filled Region: %d vùng / %d vòng." % (len(muc), len(tat_ca)))
        return [fr.Id], [], True
    except Exception:
        pass
    muc = sh_nan(muc)            # nắn đỉnh lệch < 1 mm rồi hợp (vùng đã vẽ có thể dời tối đa 1 mm)
    T = sh_doi_goc(muc)
    khoi, loi = sh_hop_khoi(muc, T)
    vong = sh_mat_day(khoi, T)
    ids, co_gop = [], False
    if loi:                      # thử thêm nguyên vòng mục lỗi (không chồng lên phần đã hợp thì vẫn tạo được)
        try:
            ids.append(FilledRegion.Create(doc, kieu_id, view.Id, sh_ds_cl(
                vong + [cl for i in loi for cl in sh_cl(muc[i])])).Id)
            bao.append(u"Gộp 1 Filled Region: %d vùng, có vòng chồng / chạm nhau → hợp lại (chỗ chồng tính 1 lần); "
                       u"%d vùng không hợp được, thêm nguyên vòng." % (len(muc), len(loi)))
            return ids, [], True
        except Exception:
            pass
    try:
        if not vong:
            raise Exception(u"không có vòng sau khi hợp")
        ids.append(FilledRegion.Create(doc, kieu_id, view.Id, sh_ds_cl(vong)).Id)
        co_gop = True
        bao.append(u"Gộp 1 Filled Region: %d vùng, có vòng chồng / chạm nhau → hợp lại còn %d vòng (chỗ chồng tính 1 lần)."
                   % (len(muc) - len(loi), len(vong)))
    except Exception as ex:
        bao.append(u"KHÔNG GỘP ĐƯỢC thành 1 Filled Region (%s) → vẽ riêng từng vùng." % str(ex).splitlines()[0])
        loi = list(range(len(muc)))
    for i in loi:
        if i < giu:
            continue
        try:
            ids.append(FilledRegion.Create(doc, kieu_id, view.Id, sh_ds_cl(sh_cl(muc[i]))).Id)
        except Exception as ex:
            bao.append(u"Không hatch được 1 vùng tại %s: %s" % (sh_vi_tri(muc[i]), str(ex).splitlines()[0]))
    if loi and co_gop:
        bao.append(u"CẦN XEM LẠI: %d vùng không hợp được vào vùng gộp, để riêng (%s)." % (
            len(loi), u"; ".join((u"cũ " if i < giu else u"mới ") + sh_vi_tri(muc[i]) for i in loi)))
    return ids, loi, co_gop


def sh_hoi_gop(view, ten_kieu, cu, n_moi, m2_cu):
    """Hỏi có thay các Filled Region cũ bằng 1 vùng gộp không. Biến môi trường ARV_GOP_HATCH = 1 / 0 trả lời sẵn (chạy
    thử nền, không hiện hộp thoại)."""
    tl = os.environ.get("ARV_GOP_HATCH", "")
    if tl in ("1", "0"):
        return tl == "1"
    clr.AddReference("RevitAPIUI")
    from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons, TaskDialogResult
    td = TaskDialog(u"Gộp hatch thành 1 đối tượng")
    td.MainInstruction = u"View '%s' đang có %d Filled Region '%s' (tổng %s)." % (
        view.Name, len(cu), ten_kieu, sh_chu_dt(m2_cu))
    td.MainContent = (u"Gộp %s thành 1 Filled Region để kiểm soát diện tích?\n\n"
                      u"Yes: %d Filled Region cũ bị XOÁ, thay bằng 1 vùng có đúng các biên đó (chỗ chồng nhau chỉ tính "
                      u"1 lần). Ctrl+Z để hoàn tác.\nNo: giữ nguyên vùng cũ%s." % (
                          (u"chúng cùng %d vùng mới" % n_moi) if n_moi else u"chúng", len(cu),
                          (u", %d vùng mới vẽ thành 1 Filled Region riêng" % n_moi) if n_moi else u""))
    td.ExpandedContent = u"Id các Filled Region cũ: " + u", ".join(str(r.Id.Value) for r in cu)
    td.CommonButtons = TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No
    td.DefaultButton = TaskDialogResult.Yes
    return td.Show() == TaskDialogResult.Yes


def sh_ve_hatch_gop(doc, view, kieu_id, muc_moi, tien_to_nhom, bao, gs_id=None, dry=False):
    """Vẽ hatch kiểu kieu_id của view thành 1 Filled Region. muc_moi: list mục mới ([[Curve]] mỗi mục).
    Vùng cũ cùng kiểu (ngoài group hoặc trong group tên bắt đầu bằng tien_to_nhom): mục mới đã nằm trọn trong vùng cũ thì
    bỏ (so khối, tránh bấm lại lần nào cũng thấy "ô mới"); ≥ 2 vùng cũ, hoặc có vùng cũ + có mục mới → hỏi gộp
    (sh_hoi_gop); đồng ý thì 1 vùng chứa biên cũ + mới, xong mới xoá các vùng cũ đã vào vùng gộp. Gọi TRONG transaction.
    Trả về list id Filled Region mới tạo."""
    cu, ngoai = [], 0
    for r in FilteredElementCollector(doc, view.Id).OfClass(FilledRegion):
        if r.GetTypeId().Value != kieu_id.Value:
            continue
        if r.GroupId.Value != -1 and not sh_ten(doc.GetElement(doc.GetElement(r.GroupId).GetTypeId())).startswith(
                tien_to_nhom):
            ngoai += 1
            continue
        cu.append(r)
    ten_kieu = sh_ten(doc.GetElement(kieu_id))
    if ngoai:
        bao.append(u"%d Filled Region '%s' nằm trong group khác (không phải của công cụ) → giữ nguyên, không gộp." % (
            ngoai, ten_kieu))
    muc_cu = [[list(cl) for cl in r.GetBoundaries()] for r in cu]
    muc_moi = list(muc_moi)
    if cu and muc_moi:
        nan = sh_nan(muc_cu + muc_moi)
        T = sh_doi_goc(muc_cu)
        khoi_cu, _ = sh_hop_khoi(nan[:len(muc_cu)], T)
        if khoi_cu is not None:
            con, bo = [], 0
            for m, mn in zip(muc_moi, nan[len(muc_cu):]):
                try:
                    s = sh_khoi(mn, T)
                    du = BooleanOperationsUtils.ExecuteBooleanOperation(s, khoi_cu, BooleanOperationsType.Difference)
                    if du.Volume < 0.01 * s.Volume:
                        bo += 1
                        continue
                except Exception:
                    pass
                con.append(m)
            if bo:
                bao.append(u"%d vùng mới đã nằm trọn trong hatch cũ → không vẽ thêm." % bo)
            muc_moi = con
    can_hoi = len(cu) >= 2 or (cu and muc_moi)
    if dry:
        bao.append(u"Sẽ vẽ %d vùng mới vào 1 Filled Region '%s'%s." % (
            len(muc_moi), ten_kieu, (u"; view có %d vùng cũ → sẽ hỏi gộp thành 1" % len(cu)) if can_hoi else u""))
        return []
    gop = False
    if can_hoi:
        m2 = 0.0
        for r in cu:
            p = r.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
            m2 = None if (m2 is None or p is None or not p.HasValue) else (
                m2 + UnitUtils.ConvertFromInternalUnits(p.AsDouble(), UnitTypeId.SquareMeters))
        gop = sh_hoi_gop(view, ten_kieu, cu, len(muc_moi), m2)
        bao.append(u"View có %d Filled Region '%s' cũ → người dùng chọn %s." % (
            len(cu), ten_kieu, u"GỘP thành 1" if gop else u"giữ nguyên"))
    muc = (muc_cu if gop else []) + muc_moi
    if not muc:
        return []
    # gs_id None (chống thấm): giữ viền mặc định của kiểu (API không có hàm đọc line style viền của Filled Region)
    st = SubTransaction(doc)
    st.Start()
    ids, loi, co_gop = sh_tao_vung(doc, kieu_id, view, muc, bao, giu=len(muc_cu) if gop else 0)
    if gop and not co_gop:             # không tạo được vùng gộp → bỏ lần thử, giữ vùng cũ, chỉ vẽ mục mới
        st.RollBack()
        bao.append(u"Không gộp được vùng cũ + mới → giữ nguyên %d Filled Region cũ (không xoá)." % len(cu))
        gop = False
        st = SubTransaction(doc)
        st.Start()
        ids, loi, co_gop = sh_tao_vung(doc, kieu_id, view, muc_moi, bao)
    st.Commit()
    for i in ids:
        if gs_id is not None:
            try:
                doc.GetElement(i).SetLineStyleId(gs_id)
            except Exception:
                pass
    if gop:                            # vùng gộp tạo xong mới xoá các vùng cũ đã vào vùng gộp
        xoa = [r for k, r in enumerate(cu) if k not in loi]
        nhom = {}
        for r in xoa:
            if r.GroupId.Value != -1:
                nhom[r.GroupId.Value] = doc.GetElement(r.GroupId)
        for g in nhom.values():
            g.UngroupMembers()
        ds = NetList[ElementId]()
        for r in xoa:
            ds.Add(r.Id)
        if xoa:
            doc.Delete(ds)
        bao.append(u"ĐÃ XOÁ %d Filled Region cũ (%d group cũ đã rã), thay bằng 1 vùng gộp %d%s." % (
            len(xoa), len(nhom), ids[0].Value,
            (u"; giữ %d vùng cũ không hợp được" % (len(cu) - len(xoa))) if len(xoa) < len(cu) else u""))
    return ids


def sh_cap_nhat_bang(doc, v, muc):
    """Bảng ghi chú đã có: chỉ sửa chữ ô diện tích theo số mới (ghép ô với tên vị trí cùng hàng), không xoá gì.
    Gọi TRONG transaction. Trả về chuỗi báo cáo."""
    notes = list(FilteredElementCollector(doc, v.Id).OfClass(TextNote))
    doi, thieu = [], []
    for m in muc:
        if "m2" not in m:
            continue
        nhan = [t for t in notes if t.Text.strip() == m["chu"]]
        o = [t for t in notes if nhan and t.Id.Value != nhan[0].Id.Value and t.Coord.X < nhan[0].Coord.X
             and abs(t.Coord.Y - nhan[0].Coord.Y) < sh_ft(0.5 * v.Scale)]
        if not o:
            thieu.append(m["chu"])
            continue
        moi = sh_chu_dt(m["m2"])
        if o[0].Text.strip() != moi:
            doi.append(u"%s: %s → %s" % (m["chu"], o[0].Text.strip(), moi))
            o[0].Text = moi
    kq = u"đã cập nhật diện tích (%s)" % u"; ".join(doi) if doi else u"diện tích không đổi"
    if thieu:
        kq += u"; CẦN XEM LẠI: bảng không có hàng %s" % u", ".join(thieu)
    return kq


def sh_chu_thich(doc, ten_view, ti_le, muc):
    """Bảng ghi chú (drafting view) theo mẫu người dùng 2026-11-09: Diện tích | Ký hiệu | Tên vị trí.
    muc: [{"vung": id kiểu Filled Region, "vien": id line style | None, "chu": u"...", "m2": số, "cot": u"tên cột 3"} |
    {"net": GraphicsStyle, "chu": u"..."}] (hàng không có "m2" để trống ô diện tích). Trả về (view, báo cáo).
    Gọi TRONG transaction."""
    for v in FilteredElementCollector(doc).OfClass(ViewDrafting):
        if not v.IsTemplate and v.Name == ten_view:
            sh_ = v.get_Parameter(BuiltInParameter.VIEWER_SHEET_NUMBER)
            if sh_ is not None and sh_.AsString() and sh_.AsString() not in (u"---", u"-"):
                return None, u"Bảng '%s' đã nằm trên sheet %s – không đặt thêm." % (ten_view, sh_.AsString())
            return v, u"dùng lại bảng '%s', %s" % (ten_view, sh_cap_nhat_bang(doc, v, muc))
    vft = [t for t in FilteredElementCollector(doc).OfClass(ViewFamilyType) if t.ViewFamily == ViewFamily.Drafting]
    if not vft:
        return None, u"Dự án không có kiểu Drafting View – không vẽ bảng ghi chú."
    v = ViewDrafting.Create(doc, vft[0].Id)
    v.Name = ten_view
    v.Scale = ti_le

    def g(mm):      # mm giấy → feet trong view
        return sh_ft(mm * float(ti_le))

    w, h = g(SH_O_MAU_MM[0]), g(SH_O_MAU_MM[1])
    c1, c2, c3 = [g(x) for x in SH_BANG_COT_MM]
    rong = c1 + c2 + c3
    td, hang = g(SH_BANG_TIEU_DE_MM), g(SH_BANG_HANG_MM)
    day = -2 * td - hang * len(muc)
    gs = None
    for sc in doc.Settings.Categories.get_Item(BuiltInCategory.OST_Lines).SubCategories:
        if sc.Name == u"Thin Lines":
            gs = sc.GetGraphicsStyle(GraphicsStyleType.Projection)

    def ke(x0, y0, x1, y1):
        dc = doc.Create.NewDetailCurve(v, Line.CreateBound(XYZ(x0, y0, 0), XYZ(x1, y1, 0)))
        if gs is not None:
            dc.LineStyle = gs

    for i in range(len(muc) + 3):
        y = -td * min(i, 2) - hang * max(i - 2, 0)
        ke(0, y, rong, y)
    ke(0, 0, 0, day)
    ke(rong, 0, rong, day)
    ke(c1, -td, c1, day)
    ke(c1 + c2, -td, c1 + c2, day)
    kc = sh_kieu_chu(doc)
    giua, trai = TextNoteOptions(kc), TextNoteOptions(kc)
    giua.HorizontalAlignment = HorizontalTextAlignment.Center
    giua.VerticalAlignment = VerticalTextAlignment.Middle
    trai.HorizontalAlignment = HorizontalTextAlignment.Left
    trai.VerticalAlignment = VerticalTextAlignment.Middle
    cot3 = muc[0].get("cot", u"TÊN VỊ TRÍ")
    TextNote.Create(doc, v.Id, XYZ(rong / 2.0, -td / 2.0, 0), SH_TEN_BANG, giua)
    y = -1.5 * td
    TextNote.Create(doc, v.Id, XYZ(c1 / 2.0, y, 0), u"DIỆN TÍCH", giua)
    TextNote.Create(doc, v.Id, XYZ(c1 + c2 / 2.0, y, 0), u"KÝ HIỆU", giua)
    TextNote.Create(doc, v.Id, XYZ(c1 + c2 + c3 / 2.0, y, 0), cot3, giua)
    xm = c1 + c2 / 2.0
    for i, m in enumerate(muc):
        yc = -2 * td - hang * (i + 0.5)
        if "vung" in m:
            cl = CurveLoop()
            p = [XYZ(xm - w / 2, yc - h / 2, 0), XYZ(xm + w / 2, yc - h / 2, 0), XYZ(xm + w / 2, yc + h / 2, 0),
                 XYZ(xm - w / 2, yc + h / 2, 0)]
            for k in range(4):
                cl.Append(Line.CreateBound(p[k], p[(k + 1) % 4]))
            ds = NetList[CurveLoop]()
            ds.Add(cl)
            fr = FilledRegion.Create(doc, m["vung"], v.Id, ds)
            if m.get("vien") is not None:
                fr.SetLineStyleId(m["vien"])
        else:
            dc = doc.Create.NewDetailCurve(v, Line.CreateBound(XYZ(xm - w / 2, yc, 0), XYZ(xm + w / 2, yc, 0)))
            dc.LineStyle = m["net"]
        if "m2" in m:
            TextNote.Create(doc, v.Id, XYZ(c1 / 2.0, yc, 0), sh_chu_dt(m["m2"]), giua)
        TextNote.Create(doc, v.Id, XYZ(c1 + c2 + g(SH_BANG_LE_MM), yc, 0), m["chu"], trai)
    return v, u"tạo bảng '%s' (%d hàng)" % (ten_view, len(muc))


def sh_dat_bang(doc, view, sh, vung, muc, ten_sheet, bao):
    """Vẽ + đặt Bảng ghi chú sát góc phải dưới vùng vẽ. Gọi TRONG transaction. Trả về khung (x0, y0, x1, y1) hoặc None."""
    x0, y0, x1, y1 = vung
    b = sh_ft(SH_BIEN_MM)
    try:
        vct, msg = sh_chu_thich(doc, u"%s - %s" % (SH_TEN_BANG, ten_sheet), view.Scale, muc)
        bao.append(u"Bảng ghi chú: %s." % msg)
        for m in muc:
            if "m2" in m:
                bao.append(u"Diện tích %s: %s (tổng Filled Region trong view)." % (m["chu"], sh_chu_dt(m["m2"])))
        if vct is None:
            return None
        doc.Regenerate()
        vp_ct = Viewport.Create(doc, sh.Id, vct.Id, XYZ(x1, y0, 0))
        k_ = sh_kieu_viewport(doc, False)
        if k_ is not None:
            vp_ct.ChangeTypeId(k_.Id)
        doc.Regenerate()
        o_ = vp_ct.GetBoxOutline()
        wc, hc = o_.MaximumPoint.X - o_.MinimumPoint.X, o_.MaximumPoint.Y - o_.MinimumPoint.Y
        vp_ct.SetBoxCenter(XYZ(x1 - b - wc / 2.0, y0 + b + hc / 2.0, 0))
        return (x1 - b - wc, y0 + b, x1 - b, y0 + b + hc)
    except Exception as ex:
        bao.append(u"Không vẽ được bảng ghi chú: %s" % (u"%s" % ex).splitlines()[0][:150])
        return None


def sh_bang_khi_da_dat(doc, view, so_sheet, muc, ten_sheet):
    """View đã nằm trên sheet (bấm lại): cập nhật diện tích của Bảng ghi chú; chưa có bảng thì đặt mới; còn chú thích bản
    cũ thì chỉ báo (công cụ không tự xoá). Gọi NGOÀI transaction. Trả về [báo cáo]."""
    if not muc:
        return []
    sheets = [s for s in FilteredElementCollector(doc).OfClass(ViewSheet) if s.SheetNumber == so_sheet]
    if not sheets:
        return []
    sh = sheets[0]
    dat = [doc.GetElement(i) for i in sh.GetAllPlacedViews()]
    bang = [v for v in dat if v.ViewType == ViewType.DraftingView and v.Name.startswith(SH_TEN_BANG + u" - ")]
    if bang:
        TransactionManager.Instance.EnsureInTransaction(doc)
        msg = sh_cap_nhat_bang(doc, bang[0], muc)
        TransactionManager.Instance.TransactionTaskDone()
        return [u"Bảng ghi chú trên sheet %s: %s." % (so_sheet, msg)]
    cu = [v for v in dat if v.ViewType == ViewType.DraftingView and v.Name.startswith(SH_TEN_CHU_THICH_CU + u" - ")]
    if cu:
        return [u"CẦN XEM LẠI: sheet %s còn chú thích bản cũ '%s' (chưa có diện tích). Xoá viewport đó trên sheet rồi bấm "
                u"lại nút để đặt Bảng ghi chú mới (công cụ không tự xoá)." % (so_sheet, cu[0].Name)]
    tbs = [t for t in FilteredElementCollector(doc, sh.Id).OfClass(FamilyInstance)
           .OfCategory(BuiltInCategory.OST_TitleBlocks)]
    if not tbs:
        return [u"Sheet %s không có khung tên – chưa đặt Bảng ghi chú." % so_sheet]
    net = sh_net_khung(doc, doc.GetElement(tbs[0].GetTypeId()))     # mở family khung tên: phải ngoài transaction
    bao = []
    TransactionManager.Instance.EnsureInTransaction(doc)
    sh_dat_bang(doc, view, sh, sh_vung_ve(sh, tbs[0], net), muc, ten_sheet, bao)
    TransactionManager.Instance.TransactionTaskDone()
    return bao


SH_KHONG_TPL = u"<Không dùng view template>"    # giá trị ô View template của hộp thoại = bỏ template


def sh_tim_tpl(doc, ten_tpl):
    """View template mặt bằng theo tên (đúng tên, không thì không phân biệt hoa thường / dấu)."""
    ds = [v for v in FilteredElementCollector(doc).OfClass(ViewPlan) if v.IsTemplate]
    for v in ds:
        if v.Name == ten_tpl:
            return v
    for v in ds:
        if sh_kd(v.Name).strip() == sh_kd(ten_tpl).strip():
            return v
    return None


def sh_tpl_khoa_tl(tpl):
    """Template điều khiển tỉ lệ (View Scale có trong template và đang được điều khiển)."""
    try:
        co = set(i.Value for i in tpl.GetTemplateParameterIds())
        nc = set(i.Value for i in tpl.GetNonControlledTemplateParameterIds())
    except Exception:
        return False
    for b in (BuiltInParameter.VIEW_SCALE_PULLDOWN_METRIC, BuiltInParameter.VIEW_SCALE):
        v = ElementId(b).Value
        if v in co and v not in nc:
            return True
    return False


def sh_ap_tpl_tl(doc, view, ten_tpl, ti_le):
    """Gán view template + tỉ lệ đã chọn trong hộp thoại (người dùng yêu cầu 2026-11-05). Gọi TRONG transaction.
    ten_tpl: trống = giữ template đang có; SH_KHONG_TPL = bỏ template; tên = gán template đó (không tạo, không sửa
    template). ti_le: mẫu số (0 = giữ); template khoá tỉ lệ thì tỉ lệ theo template, chỉ báo."""
    bao = []
    ten_tpl = (ten_tpl or u"").strip()
    if ten_tpl == SH_KHONG_TPL:
        if view.ViewTemplateId != ElementId.InvalidElementId:
            view.ViewTemplateId = ElementId.InvalidElementId
            bao.append(u"Bỏ view template của '%s'." % view.Name)
    elif ten_tpl:
        tpl = sh_tim_tpl(doc, ten_tpl)
        if tpl is None:
            bao.append(u"CẦN XEM LẠI: không có view template '%s' – giữ template đang có của '%s'." % (ten_tpl, view.Name))
        elif view.ViewTemplateId.Value != tpl.Id.Value:
            view.ViewTemplateId = tpl.Id
            bao.append(u"Gán view template '%s' cho '%s'." % (tpl.Name, view.Name))
        else:
            bao.append(u"View '%s' đã dùng template '%s'." % (view.Name, tpl.Name))
    try:
        ti_le = int(round(float(ti_le or 0)))
    except Exception:
        ti_le = 0
    if ti_le > 0:
        tpl = doc.GetElement(view.ViewTemplateId) if view.ViewTemplateId != ElementId.InvalidElementId else None
        if tpl is not None and sh_tpl_khoa_tl(tpl):
            if tpl.Scale != ti_le:
                bao.append(u"Template '%s' khoá tỉ lệ 1:%d → giữ 1:%d (không sửa template), không dùng 1:%d." % (
                    tpl.Name, tpl.Scale, tpl.Scale, ti_le))
        elif view.Scale != ti_le:
            view.Scale = ti_le
            bao.append(u"Tỉ lệ '%s': 1:%d." % (view.Name, ti_le))
    doc.Regenerate()
    return bao


def sh_tao_view(doc, goc, tu_khoa, ten_mau, dry, ten_tpl=u"", ti_le=0):
    """View mặt bằng mới cho tầng của view goc (xem chú thích đầu khối). tu_khoa: chữ khoá không dấu (vd. "chong tham")
    để nhận template có sẵn khi không chọn template; ten_mau: tên in hoa (vd. "MẶT BẰNG CHỐNG THẤM") = tên loại view và
    tiền tố tên view. ten_tpl / ti_le: template + tỉ lệ chọn trong hộp thoại (sh_ap_tpl_tl). KHÔNG tạo / sửa view template
    (người dùng chốt 2026-11-05): không chọn template thì dùng template có chữ khoá nếu có, không thì giữ template của
    view gốc. Trả về (view, [báo cáo]); dry: chỉ báo, trả về goc."""
    bao = []
    tang = goc.GenLevel.Name
    ten_moi = u"%s - %s" % (ten_mau, tang)
    ten_tpl = (ten_tpl or u"").strip()
    if not ten_tpl:
        for v in FilteredElementCollector(doc).OfClass(View):
            if v.IsTemplate and v.ViewType == ViewType.FloorPlan and tu_khoa in sh_kd(v.Name):
                if not ten_tpl or v.Name == ten_mau:
                    ten_tpl = v.Name
    if dry:
        bao.append(u"Sẽ tạo view '%s' (nhân bản '%s'), view template '%s'%s – Dry-run tính trên view gốc." % (
            ten_moi, goc.Name, ten_tpl or u"của view gốc",
            u", tỉ lệ 1:%d" % int(float(ti_le)) if ti_le else u""))
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
    bao.extend(sh_ap_tpl_tl(doc, moi, ten_tpl, ti_le))
    try:
        bao.append(sh_crop_theo_tuong(doc, moi))
    except Exception as ex:
        bao.append(u"Không đặt được crop: %s" % (u"%s" % ex).splitlines()[0][:150])
    TransactionManager.Instance.TransactionTaskDone()
    return moi, bao


def sh_chuan_template(doc, view, ten_mau):
    """Trước 2026-11-05: bổ sung template công cụ tạo. Nay các nút không sửa view template nữa → không làm gì."""
    return []


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
    for w in list(FilteredElementCollector(doc, view.Id).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()) + lk_thay(doc, view, BuiltInCategory.OST_Walls, True):
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
    so_dang = None
    try:
        dang = view.get_Parameter(BuiltInParameter.VIEWER_SHEET_NUMBER)
        if dang is not None and dang.AsString() and dang.AsString() not in (u"---", u"-"):
            so_dang = dang.AsString()
    except Exception:
        pass
    if so_dang:
        return ([u"View '%s' đã nằm trên sheet %s – không đặt thêm." % (view.Name, so_dang)]
                + sh_bang_khi_da_dat(doc, view, so_dang, muc_chu_thich, ten_sheet))
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
    o_ct = sh_dat_bang(doc, view, sh, (x0, y0, x1, y1), muc_chu_thich, ten_sheet, bao) if muc_chu_thich else None
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
                muc.append({"vung": t.Id, "vien": vien, "chu": "NGĂN CHÁY LAN TRỤC / HỘP KỸ THUẬT",
                            "m2": sh_dien_tich(doc, view, t.Id), "cot": "TÊN VỊ TRÍ NGĂN CHÁY LAN"})
                break
    tang = view.GenLevel.Name if view.GenLevel is not None else view.Name
    gd, hm, kho, khung, so, ten_sh = SH_IN
    ten_sh = (ten_sh or "MẶT BẰNG NGĂN CHÁY LAN %s" % tang).strip().upper()
    # Crop view công cụ tạo / vừa bật crop lấy theo tường Revit; phần vẽ theo CAD link có thể nằm ngoài → nới crop
    # cho đủ phần đã vẽ trước khi đặt sheet (Site HQV 2026-11-12: link L5-L15 không nạp, Tầng 3BA hatch bị cắt mép dưới).
    if view.Id.Value in VUA_TAO or view.Id.Value in CROP_MO:
        TransactionManager.Instance.EnsureInTransaction(doc)
        try:
            s_ = sh_mo_crop_theo_ve(doc, view)
            if s_:
                bao_cao.append(s_)
        except Exception as ex:
            bao_cao.append(u"Không nới được crop theo phần đã vẽ: %s" % (u"%s" % ex).splitlines()[0][:150])
        TransactionManager.Instance.TransactionTaskDone()
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
