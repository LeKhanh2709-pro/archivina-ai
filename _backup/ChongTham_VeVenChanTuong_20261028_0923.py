# Vẽ nét vén chân tường chống thấm (Detail Line) trên view mặt bằng chống thấm của Revit.
# Hatch chống thấm = Filled Region 2D trong view (người dùng chốt 2026-10-27: không đụng hatch / filter của sàn gạch model).
#   - Nhận phòng ướt theo 2 nguồn:
#       a) sàn hoàn thiện ướt trên level (tên kiểu sàn chứa từ khoá, vd. "Gach Lat WC", "Gach Lat Logia")
#       b) bồn cầu / sen tắm / bồn tắm nằm ngoài mọi sàn ướt → WC chưa có sàn ướt (không dùng phễu thoát sàn)
#   - Biên phòng = mặt hoàn thiện tường (room có sẵn tại điểm đó, hoặc room tạm trong SubTransaction rồi rollback,
#     không để lại gì trong model) → không bám theo khấc / lỗ của sàn. Room hở (không khép kín) hoặc tràn sang
#     phòng lớn thì quay về biên sàn.
#   - Mỗi vòng biên lùi vào trong phòng một khoảng (mặc định 50 mm) → nét vén, ngắt tại cửa đi
#   - Mọi phòng ướt được hatch bằng Filled Region theo biên mặt tường: kiểu "AV_Hatch Chống Thấm WC" / "... Logia"
#     (chưa có thì tạo, mẫu + màu lấy theo filter sàn SHT-WC / SHT-Logia của template), đưa xuống dưới nét vén
#   - View đã có nét vén: không vẽ lại vén (không xoá gì), chỉ bổ sung hatch cho phòng chưa có hatch
#   - Ẩn thiết bị vệ sinh trong view (Hide in View từng đối tượng, không sửa template), giữ phễu thoát sàn
#   - Detail Line kiểu nét "AV.Nét chống thấm" gom group "ARV_ChongTham_Ven"; Filled Region gom group "ARV_ChongTham_Hatch"
# Dry-run (mặc định) chỉ báo cáo, không sửa mô hình. Không xoá gì: view đã có nét vén cùng kiểu thì dừng và báo.
# INPUT
#   IN[0] (str)   Tên view (để trống = view đang mở nếu template có "chống thấm", không thì view đầu tiên có template đó)
#   IN[1] (str)   Từ khoá tên kiểu sàn ướt, cách nhau bằng ;  (không phân biệt dấu / hoa thường)
#   IN[2] (float) Khoảng lùi nét vén vào trong phòng (mm)
#   IN[3] (str)   Tên line style nét vén
#   IN[4] (bool)  Dry-run (True = chỉ báo cáo)
#   IN[5] (bool)  Vẽ cả khi view đã có nét vén cùng kiểu
#   IN[6] (str)   Thư mục ghi log + ảnh (để trống = Documents\ARV_Logs\chong_tham)
#   IN[7] (str)   Từ khoá tên family thiết bị nhận ra WC, cách nhau bằng ; (không dùng phễu thoát sàn: có cả ở hành lang, lô gia)
#   IN[8] (bool)  Ẩn thiết bị vệ sinh trong view
#   IN[9] (bool)  Hatch chống thấm bằng Filled Region cho mọi phòng ướt
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


TEN_VIEW = gia_tri(0, "")
TU_KHOA_SAN = [k for k in str(gia_tri(1, "Gach Lat WC;Gach Lat Logia")).split(";") if k.strip()]
LUI_MM = float(gia_tri(2, 50))
TEN_NET = str(gia_tri(3, "AV.Nét chống thấm"))
DRY_RUN = bool(gia_tri(4, True))
VE_CA_KHI_CO = bool(gia_tri(5, False))
THU_MUC = str(gia_tri(6, os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs", "chong_tham")))
TU_KHOA_TB = [k for k in str(gia_tri(7, "Toilet;Bồn cầu;Tiểu nam;Sen tắm;Bồn tắm;Shower")).split(";")
              if k.strip()]
AN_THIET_BI = bool(gia_tri(8, True))
VE_HATCH = bool(gia_tri(9, True))
os.makedirs(THU_MUC, exist_ok=True)

GOC_SONG_SONG = 20.0      # độ: cạnh vén lệch tường chứa cửa dưới góc này mới bị cắt
VUOT_CUA_MM = 150.0       # dải cắt vươn ra ngoài mặt tường mỗi bên (ngoài khoảng lùi)
NGAN_NHAT_MM = 5.0        # đoạn vén ngắn hơn thì bỏ
DT_WC_TOI_DA_M2 = 15.0    # phòng nhận theo thiết bị lớn hơn thì không vẽ, báo xem lại (vd. lavabo / phễu ở sảnh)
CO_MIN_MM, CO_MAX_MM = 500.0, 2500.0   # bề rộng lỗ mở không cửa (cổ) dùng để tách room tràn
TRAN_SAN = 1.5            # room lớn hơn tổng sàn ướt bên trong quá 1.5 lần (+1 m2) = room tràn → dùng biên sàn
GIU_HIEN = ("pheu thoat", "thoat san", "floor drain")   # thiết bị không ẩn
TEN_HATCH = {"wc": "AV_Hatch Chống Thấm WC", "logia": "AV_Hatch Chống Thấm Logia"}
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


def ten(e):
    try:
        return e.Name
    except Exception:
        return "?"


def ten_kieu(e):
    return ten(doc.GetElement(e.GetTypeId()))


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
    la_ct = [v for v in plans if "chong tham" in khong_dau(ten_tpl(v)) or "chong tham" in khong_dau(v.Name)]
    av = doc.ActiveView
    for v in la_ct:
        if v.Id == av.Id:
            return v
    if not la_ct:
        raise Exception("Không có view mặt bằng nào dùng template chống thấm; nhập tên view vào IN[0]")
    return la_ct[0]


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


def trong_san(x, y, loops_pts):
    # điểm nằm trong số lẻ vòng biên = nằm trong vùng (vòng ngoài trừ lỗ)
    return sum(1 for pts in loops_pts if trong_da_giac(x, y, pts)) % 2 == 1


def diem_trong(loops_pts):
    """Một điểm nằm trong vùng: thử lưới 9x9 trên khung bao, lấy điểm xa biên nhất (theo khung)"""
    xs = [p[0] for pts in loops_pts for p in pts]
    ys = [p[1] for pts in loops_pts for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    tot, kc_tot = None, -1.0
    for i in range(1, 10):
        for j in range(1, 10):
            x, y = x0 + (x1 - x0) * i / 10.0, y0 + (y1 - y0) * j / 10.0
            if trong_san(x, y, loops_pts):
                kc = min(min(abs(x - px) + abs(y - py) for px, py in pts) for pts in loops_pts)
                if kc > kc_tot:
                    tot, kc_tot = (x, y), kc
    return tot


def phang(c, z):
    return c.CreateTransformed(Transform.CreateTranslation(XYZ(0, 0, z - c.GetEndPoint(0).Z)))


def loop_lui_vao(curves, loops_pts, d):
    cl = CurveLoop()
    for c in curves:
        cl.Append(c)
    for dau in (1, -1):
        try:
            kq = CurveLoop.CreateViaOffset(cl, dau * d, XYZ.BasisZ)
        except Exception:
            continue
        ok = True
        for c in kq:
            m = c.Evaluate(0.5, True)
            if not trong_san(m.X, m.Y, loops_pts):
                ok = False
                break
        if ok:
            return list(kq)
    return None


# ---------- cửa ----------
def be_rong_cua(d):
    for nguon in (d, doc.GetElement(d.GetTypeId())):
        for bip in (BuiltInParameter.DOOR_WIDTH, BuiltInParameter.FAMILY_WIDTH_PARAM,
                    BuiltInParameter.FAMILY_ROUGH_WIDTH_PARAM):
            try:
                prm = nguon.get_Parameter(bip)
                if prm and prm.HasValue and prm.AsDouble() > 0:
                    return prm.AsDouble()
            except Exception:
                pass
    return None


def vung_cua(d):
    """(gốc, hướng dọc tường u, hướng vuông góc v, nửa rộng, nửa dày dải cắt) theo đơn vị feet"""
    p = d.Location.Point
    u = XYZ(d.HandOrientation.X, d.HandOrientation.Y, 0).Normalize()
    v = XYZ(-u.Y, u.X, 0)
    w = be_rong_cua(d)
    if w is None:
        return None
    try:
        day = d.Host.Width
    except Exception:
        day = mm(250)
    return (XYZ(p.X, p.Y, 0), u, v, w / 2.0, day / 2.0 + mm(LUI_MM) + mm(VUOT_CUA_MM))


def cat_doan(a, b, vung):
    """Phần [t0, t1] của đoạn a→b nằm trong dải cắt (Liang–Barsky), None nếu không giao"""
    g, u, v, nr, nd = vung
    pa, pb = a - g, b - g
    ua, ub = pa.DotProduct(u), pb.DotProduct(u)
    va, vb = pa.DotProduct(v), pb.DotProduct(v)
    t0, t1 = 0.0, 1.0
    for p0, dp, lim in ((ua, ub - ua, nr), (va, vb - va, nd)):
        for q, r in ((-dp, p0 + lim), (dp, lim - p0)):
            if abs(q) < 1e-12:
                if r < 0:
                    return None
            else:
                t = r / q
                if q < 0:
                    t0 = max(t0, t)
                else:
                    t1 = min(t1, t)
    return (t0, t1) if t1 - t0 > 1e-9 else None


def ngat_tai_cua(line, cac_vung):
    """Trả về danh sách Line còn lại sau khi cắt tại các cửa"""
    doan = [(line.GetEndPoint(0), line.GetEndPoint(1))]
    so_cat = 0
    for vung in cac_vung:
        u = vung[1]
        moi = []
        for a, b in doan:
            dirv = (b - a)
            if dirv.GetLength() < 1e-9:
                continue
            cos = abs(dirv.Normalize().DotProduct(u))
            k = cat_doan(a, b, vung)
            if k is None:
                moi.append((a, b))
                continue
            t0, t1 = k
            if cos >= math.cos(math.radians(GOC_SONG_SONG)):
                so_cat += 1
                if t0 > 0:
                    moi.append((a, a + (b - a) * t0))
                if t1 < 1:
                    moi.append((a + (b - a) * t1, b))
            elif t0 <= 1e-6 and t1 >= 1 - 1e-6:
                so_cat += 1          # đoạn ngắn vuông góc nằm gọn trong ô cửa (má cửa) → bỏ
            else:
                moi.append((a, b))
        doan = moi
    kq = [Line.CreateBound(a, b) for a, b in doan if (b - a).GetLength() >= mm(NGAN_NHAT_MM)]
    return kq, so_cat


# ---------- phòng (room) ----------
def bien_room(r, z):
    """Các vòng biên mặt hoàn thiện của room, đã đưa về cao độ z; None nếu room hở"""
    opt = SpatialElementBoundaryOptions()
    opt.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.Finish
    loops = []
    for segs in r.GetBoundarySegments(opt) or []:
        l = [phang(s.GetCurve(), z) for s in segs]
        if len(l) >= 2:
            loops.append(l)
    if not loops or r.Area <= 0:
        return None
    return loops


def dien_tich(loops_pts):
    """Diện tích (feet2) vùng theo quy tắc chẵn lẻ: vòng lớn nhất trừ các vòng còn lại"""
    def s(pts):
        return abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                       for i in range(len(pts)))) / 2.0
    a = sorted((s(p) for p in loops_pts), reverse=True)
    return a[0] - sum(a[1:]) if a else 0.0


def tim_phong(diem, lv, z, phong):
    """Phòng chứa điểm (x, y): phòng đã tìm / room có sẵn / room tạm. Trả về (chỉ số trong phong, mới?)"""
    x, y = diem
    for i, p in enumerate(phong):
        if p["room"] and trong_san(x, y, p["pts"]):
            return i, False
    r = doc.GetRoomAtPoint(XYZ(x, y, lv.Elevation + mm(1000)))
    nguon = "room có sẵn"
    if r is None:
        r = doc.Create.NewRoom(lv, UV(x, y))
        doc.Regenerate()
        nguon = "room tạm"
    loops = bien_room(r, z)
    if loops is None:
        return None, False
    pts = [diem_loop(l) for l in loops]
    phong.append({"loops": loops, "pts": pts, "room": True, "nguon": nguon, "san": [], "tb": [],
                  "dt": dien_tich(pts), "hat": diem})
    return len(phong) - 1, True


def tach_co(loops_pts, hat, dt_max, dt_dich=None):
    """Room tràn qua lỗ mở không cửa: tách vùng bằng dây cung nối 2 đỉnh lõm (đầu tường), dài CO_MIN..CO_MAX,
    nằm trong vùng, không cắt cạnh nào. Lấy phần chứa điểm hạt, rộng 1 m2..dt_max; có dt_dich thì lấy phần
    có diện tích gần dt_dich nhất, không thì phần nhỏ nhất. Trả về (điểm phần tách, (a, b) dây cung) hoặc None"""
    v = max(loops_pts, key=lambda q: dien_tich([q]))
    n = len(v)
    if n < 4:
        return None
    sa = sum(v[i][0] * v[(i + 1) % n][1] - v[(i + 1) % n][0] * v[i][1] for i in range(n))

    def cheo(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def cat_nhau(p1, p2, p3, p4):
        d1, d2 = cheo(p3, p4, p1), cheo(p3, p4, p2)
        d3, d4 = cheo(p1, p2, p3), cheo(p1, p2, p4)
        return ((d1 > 1e-9 and d2 < -1e-9) or (d1 < -1e-9 and d2 > 1e-9)) and                ((d3 > 1e-9 and d4 < -1e-9) or (d3 < -1e-9 and d4 > 1e-9))

    lom = [i for i in range(n) if cheo(v[i - 1], v[i], v[(i + 1) % n]) * sa < -1e-9]
    m2 = mm(1000) * mm(1000)
    tot, diem_tot = None, None
    for ii in range(len(lom)):
        for jj in range(ii + 1, len(lom)):
            i, j = lom[ii], lom[jj]
            if j - i < 2 or (i == 0 and j == n - 1):
                continue
            a, b = v[i], v[j]
            dai = math.hypot(b[0] - a[0], b[1] - a[1])
            if dai < mm(CO_MIN_MM) or dai > mm(CO_MAX_MM):
                continue
            if not trong_da_giac((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0, v):
                continue
            if any(cat_nhau(a, b, v[k], v[(k + 1) % n]) for k in range(n)
                   if k not in (i, j) and (k + 1) % n not in (i, j)):
                continue
            for phan in (v[i:j + 1], v[j:] + v[:i + 1]):
                if not trong_da_giac(hat[0], hat[1], phan):
                    continue
                dt = dien_tich([phan])
                if dt < m2 or dt > dt_max:
                    continue
                diem_so = abs(dt - dt_dich) if dt_dich else dt
                if diem_tot is None or diem_so < diem_tot:
                    tot, diem_tot = (phan, (a, b)), diem_so
    return tot


def ap_tach(p, kq, z, vung_cuas):
    """Thay biên phòng bằng phần tách; thêm dải cắt tại dây cung để nét vén không chạy qua lỗ mở"""
    phan, (a, b) = kq
    l = []
    for k in range(len(phan)):
        p1, p2 = phan[k], phan[(k + 1) % len(phan)]
        if math.hypot(p2[0] - p1[0], p2[1] - p1[1]) > mm(1):
            l.append(Line.CreateBound(XYZ(p1[0], p1[1], z), XYZ(p2[0], p2[1], z)))
    p["loops"], p["pts"], p["dt"] = [l], [phan], dien_tich([phan])
    p["nguon"] = "room tách tại lỗ mở"
    u = XYZ(b[0] - a[0], b[1] - a[1], 0)
    dai = u.GetLength()
    u = u.Normalize()
    vung_cuas.append((XYZ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0, 0), u, XYZ(-u.Y, u.X, 0), dai / 2.0,
                      mm(LUI_MM) + mm(VUOT_CUA_MM)))


# ---------- hatch cho WC không có sàn ướt ----------
def kieu_hatch(view, loai):
    """FilledRegionType "AV_Hatch Chống Thấm WC / Logia": có sẵn thì dùng; chưa có thì tạo, mẫu + màu hatch bề mặt
    lấy theo filter sàn tương ứng (tên filter có chữ WC / Logia) của template — chỉ đọc filter, không sửa"""
    ten_t = TEN_HATCH[loai]
    for t in FilteredElementCollector(doc).OfClass(FilledRegionType):
        if ten(t) == ten_t:
            return t, "dùng kiểu có sẵn '%s'" % ten_t
    nguon = doc.GetElement(view.ViewTemplateId) if view.ViewTemplateId != ElementId.InvalidElementId else view
    pid, mau, ten_f = None, None, None
    for fid in nguon.GetFilters():
        f = doc.GetElement(fid)
        if loai in khong_dau(ten(f)).replace("-", " ").split():
            o = nguon.GetFilterOverrides(fid)
            if o.SurfaceForegroundPatternId != ElementId.InvalidElementId:
                pid, mau, ten_f = o.SurfaceForegroundPatternId, o.SurfaceForegroundPatternColor, ten(f)
                break
    if pid is None:
        return None, "không có kiểu '%s' và không thấy filter sàn %s có hatch bề mặt trong template" % (ten_t, loai)
    ten_mau = ten(doc.GetElement(pid))
    if DRY_RUN:
        return None, "sẽ tạo kiểu mới '%s' (mẫu %s theo filter %s)" % (ten_t, ten_mau, ten_f)
    goc = FilteredElementCollector(doc).OfClass(FilledRegionType).FirstElement()
    t = goc.Duplicate(ten_t)
    t.ForegroundPatternId = pid
    if mau.IsValid:
        t.ForegroundPatternColor = mau
    t.BackgroundPatternId = ElementId.InvalidElementId
    t.IsMasking = False
    return t, "đã tạo kiểu mới '%s' (mẫu %s theo filter %s)" % (ten_t, ten_mau, ten_f)


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


# ---------- chạy ----------
def chinh():
    view = chon_view()
    lv = view.GenLevel
    bao_cao.append("View: %s (template %s, level %s)" % (view.Name, ten_tpl(view) or "-", lv.Name if lv else "-"))
    if lv is None:
        raise Exception("View không gắn level")
    z = lv.Elevation
    d = mm(LUI_MM)

    # line style
    gs = None
    for sc in doc.Settings.Categories.get_Item(BuiltInCategory.OST_Lines).SubCategories:
        if sc.Name == TEN_NET:
            gs = sc.GetGraphicsStyle(GraphicsStyleType.Projection)
    if gs is None:
        raise Exception("Không có line style '%s' trong model" % TEN_NET)

    # nét vén đã có?
    da_co = [c for c in FilteredElementCollector(doc, view.Id).OfClass(CurveElement)
             if c.CurveElementType == CurveElementType.DetailCurve and c.LineStyle.Id == gs.Id]
    bao_cao.append("Nét '%s' đã có trong view: %d" % (TEN_NET, len(da_co)))

    # sàn ướt
    kh = [khong_dau(k.strip()) for k in TU_KHOA_SAN]
    sans = [f for f in FilteredElementCollector(doc).OfClass(Floor)
            if f.LevelId == lv.Id and any(k in khong_dau(ten_kieu(f)) for k in kh)]
    dem = {}
    for f in sans:
        dem[ten_kieu(f)] = dem.get(ten_kieu(f), 0) + 1
    bao_cao.append("Sàn ướt trên level: %d (%s)" % (len(sans), "; ".join("%s=%d" % kv for kv in sorted(dem.items()))))
    bien_san = {}
    for f in sans:
        try:
            loops = [[phang(c, z) for c in ca] for ca in doc.GetElement(f.SketchId).Profile]
            bien_san[f.Id.Value] = (loops, [diem_loop(l) for l in loops])
        except Exception:
            bao_cao.append("Sàn %s: không đọc được sketch" % f.Id.Value)

    # thiết bị vệ sinh trên level, kể cả đã ẩn trong view (thiết bị đặt trên sàn: LevelId rỗng → xét Schedule Level / host)
    def tren_level(e):
        if e.LevelId == lv.Id:
            return True
        prm = e.get_Parameter(BuiltInParameter.INSTANCE_SCHEDULE_ONLY_LEVEL_PARAM)
        if prm and prm.AsElementId() == lv.Id:
            return True
        try:
            return e.Host is not None and e.Host.LevelId == lv.Id
        except Exception:
            return False
    tb_all = [e for e in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures)
              .WhereElementIsNotElementType() if tren_level(e)]
    co = set(e.Id.Value for e in tb_all)
    tb_all += [e for e in FilteredElementCollector(doc, view.Id).OfCategory(BuiltInCategory.OST_PlumbingFixtures)
               .WhereElementIsNotElementType() if e.Id.Value not in co]     # thiết bị không host / không level
    khtb = [khong_dau(k.strip()) for k in TU_KHOA_TB]
    tb_wc = [e for e in tb_all if any(k in khong_dau(ten_family(e)) for k in khtb)]
    bao_cao.append("Thiết bị vệ sinh trên level: %d; dùng để nhận WC: %d (%s)" % (
        len(tb_all), len(tb_wc), "; ".join(sorted(set(ten_family(e) for e in tb_wc)))))

    # cửa đi trên level
    cua = [e for e in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType()
           if e.LevelId == lv.Id]
    vung_cuas, cua_loi = [], []
    for e in cua:
        try:
            vg = vung_cua(e)
        except Exception:
            vg = None
        if vg is None:
            cua_loi.append(str(e.Id.Value))
        else:
            vung_cuas.append(vg)
    bao_cao.append("Cửa đi trên level: %d (không đọc được bề rộng: %s)" % (len(cua), ", ".join(cua_loi) or "0"))

    # ---- tìm phòng ướt: room tạm trong SubTransaction, rollback sau khi lấy biên ----
    TransactionManager.Instance.EnsureInTransaction(doc)
    phong, can_xem = [], []
    st = SubTransaction(doc)
    st.Start()
    try:
        for f in sans:
            if f.Id.Value not in bien_san:
                continue
            loops, pts = bien_san[f.Id.Value]
            p = diem_trong(pts)
            i = None
            if p:
                try:
                    i, _ = tim_phong(p, lv, z, phong)
                except Exception as ex:
                    can_xem.append("sàn %s: lỗi tìm phòng (%s)" % (f.Id.Value, ex))
            if i is not None and "hat" not in phong[i]:
                phong[i]["hat"] = p
            if i is None:      # room hở → dùng biên sàn
                phong.append({"loops": loops, "pts": pts, "room": False, "nguon": "biên sàn (room hở)",
                              "san": [f], "tb": [], "dt": dien_tich(pts)})
            else:
                phong[i]["san"].append(f)
        id_san = set(bien_san.keys())
        for e in tb_wc:
            try:
                if e.Host is not None and e.Host.Id.Value in id_san:
                    continue       # thiết bị đặt trên sàn ướt → đã có
            except Exception:
                pass
            # điểm dò: vị trí thiết bị lệch 200 mm theo hướng mặt (khung bao family kéo dài ra sau tường, không dùng)
            try:
                q = e.Location.Point + XYZ(e.FacingOrientation.X, e.FacingOrientation.Y, 0) * mm(200)
            except Exception:
                continue
            x, y = q.X, q.Y
            if any(trong_san(x, y, b[1]) for b in bien_san.values()):
                continue           # thiết bị nằm trên sàn ướt → đã có
            try:
                i, moi = tim_phong((x, y), lv, z, phong)
            except Exception as ex:
                can_xem.append("thiết bị %s: lỗi tìm phòng (%s)" % (e.Id.Value, ex))
                continue
            if i is None:
                can_xem.append("thiết bị %s (%s) tại (%.0f, %.0f): phòng hở, không vẽ" % (
                    e.Id.Value, ten_family(e), ra_mm(x), ra_mm(y)))
                continue
            phong[i]["tb"].append(e)
    finally:
        st.RollBack()

    # room tràn sang phòng lớn → dùng biên từng sàn
    ds = []
    for p in phong:
        if p["room"] and p["san"]:
            dt_san = sum(dien_tich(bien_san[f.Id.Value][1]) for f in p["san"])
            if p["dt"] > TRAN_SAN * dt_san + mm(1000) * mm(1000):
                kq = tach_co(p["pts"], p["hat"], TRAN_SAN * dt_san + mm(1000) * mm(1000), dt_san)
                if kq:
                    dt_cu = p["dt"]
                    ap_tach(p, kq, z, vung_cuas)
                    can_xem.append("room %.1f m2 tràn qua lỗ mở (sàn %s) → tách còn %.1f m2" % (
                        ra_m2(dt_cu), ", ".join(str(f.Id.Value) for f in p["san"]), ra_m2(p["dt"])))
                    ds.append(p)
                    continue
                can_xem.append("room %.1f m2 lớn hơn sàn ướt %.1f m2 (sàn %s) → dùng biên sàn" % (
                    ra_m2(p["dt"]), ra_m2(dt_san), ", ".join(str(f.Id.Value) for f in p["san"])))
                for f in p["san"]:
                    loops, pts = bien_san[f.Id.Value]
                    ds.append({"loops": loops, "pts": pts, "room": False, "nguon": "biên sàn (room tràn)",
                               "san": [f], "tb": [], "dt": dien_tich(pts)})
                continue
        if not p["san"] and p["dt"] > mm(1000) * mm(1000) * DT_WC_TOI_DA_M2:
            kq = tach_co(p["pts"], p["hat"], mm(1000) * mm(1000) * DT_WC_TOI_DA_M2)
            if kq:
                dt_cu = p["dt"]
                ap_tach(p, kq, z, vung_cuas)
                can_xem.append("phòng nhận theo thiết bị %s: room %.1f m2 tràn qua lỗ mở → tách còn %.1f m2" % (
                    ", ".join("%s %s" % (ten_family(e), e.Id.Value) for e in p["tb"]), ra_m2(dt_cu), ra_m2(p["dt"])))
                ds.append(p)
                continue
            can_xem.append("phòng nhận theo thiết bị %s rộng %.1f m2 > %.0f m2 → không vẽ" % (
                ", ".join("%s %s" % (ten_family(e), e.Id.Value) for e in p["tb"]), ra_m2(p["dt"]), DT_WC_TOI_DA_M2))
            continue
        ds.append(p)
    phong = ds
    them = [p for p in phong if not p["san"]]
    bao_cao.append("Phòng ướt: %d (theo sàn: %d, chỉ theo thiết bị — WC chưa có sàn ướt: %d)" % (
        len(phong), len(phong) - len(them), len(them)))
    for p in them:
        x, y = diem_trong(p["pts"]) or (0, 0)
        bao_cao.append("   WC không có sàn ướt: %.1f m2 tại (%.0f, %.0f) — %s" % (
            ra_m2(p["dt"]), ra_mm(x), ra_mm(y), ", ".join("%s %s" % (ten_family(e), e.Id.Value) for e in p["tb"])))
    nguon_dem = {}
    for p in phong:
        nguon_dem[p["nguon"]] = nguon_dem.get(p["nguon"], 0) + 1
    bao_cao.append("Nguồn biên: %s" % "; ".join("%s=%d" % kv for kv in sorted(nguon_dem.items())))

    # ---- nét vén ----
    net_ve, loi, tong_cat = [], [], 0
    for p in phong:
        for l in p["loops"]:
            lui = loop_lui_vao(l, p["pts"], d)
            if lui is None:
                loi.append("vòng biên tại (%.0f, %.0f)" % (ra_mm(l[0].GetEndPoint(0).X), ra_mm(l[0].GetEndPoint(0).Y)))
                continue
            for c in lui:
                if c.GetType().Name == "Line":
                    con, nc = ngat_tai_cua(c, vung_cuas)
                    tong_cat += nc
                    net_ve += con
                else:
                    net_ve.append(c)
    bao_cao.append("Nét vén sẽ vẽ: %d đoạn, tổng %.1f m; số lần cắt tại cửa: %d" % (
        len(net_ve), sum(ra_mm(c.Length) for c in net_ve) / 1000.0, tong_cat))
    if loi:
        bao_cao.append("Lùi vòng biên lỗi (bỏ qua, cần xem lại): " + "; ".join(loi))
    if can_xem:
        bao_cao.append("CẦN XEM LẠI:\n   " + "\n   ".join(can_xem))

    # ---- thiết bị cần ẩn ----
    an = [e for e in FilteredElementCollector(doc, view.Id).OfCategory(BuiltInCategory.OST_PlumbingFixtures)
          .WhereElementIsNotElementType()
          if not any(k in khong_dau(ten_family(e)) for k in GIU_HIEN) and e.CanBeHidden(view)]
    bao_cao.append("Thiết bị vệ sinh sẽ ẩn trong view: %d (giữ hiện: phễu thoát sàn)" % len(an) if AN_THIET_BI
                   else "Không ẩn thiết bị (IN[8] = False)")

    # ---- hatch Filled Region: phòng chưa có hatch chống thấm trong view ----
    da_hatch = []
    for r in FilteredElementCollector(doc, view.Id).OfClass(FilledRegion):
        if ten(doc.GetElement(r.GetTypeId())) in TEN_HATCH.values():
            try:
                da_hatch.append([diem_loop(list(cl)) for cl in r.GetBoundaries()])
            except Exception:
                pass
    can_hatch = []
    if VE_HATCH:
        for p in phong:
            q = diem_trong(p["pts"])
            if q and any(trong_san(q[0], q[1], h) for h in da_hatch):
                continue
            loai = "logia" if any("logia" in khong_dau(ten_kieu(f)) for f in p["san"]) else "wc"
            can_hatch.append((p, loai))
    kieu = {}
    for loai in sorted(set(l for _, l in can_hatch)):
        kieu[loai] = kieu_hatch(view, loai)
        bao_cao.append("Hatch %s: %s" % (loai.upper(), kieu[loai][1]))
    bao_cao.append("Hatch Filled Region sẽ vẽ: %d phòng (WC %d, lô gia %d); phòng đã có hatch: %d" % (
        len(can_hatch), sum(1 for _, l in can_hatch if l == "wc"), sum(1 for _, l in can_hatch if l == "logia"),
        len(phong) - len(can_hatch) if VE_HATCH else 0))

    if DRY_RUN:
        TransactionManager.Instance.TransactionTaskDone()
        bao_cao.append("DRY-RUN: chưa vẽ gì. Đặt IN[4] = False để vẽ.")
        return view, []
    ve_net = not (da_co and not VE_CA_KHI_CO)
    if not ve_net:
        bao_cao.append("View đã có %d nét '%s' → không vẽ lại vén (không xoá), chỉ bổ sung hatch." % (len(da_co), TEN_NET))

    # hatch trước, nét vén sau (nét vén nằm trên hatch)
    id_hatch = []
    for p, loai in can_hatch:
        tk = kieu[loai][0]
        if tk is None:
            continue
        try:
            cls = NetList[CurveLoop]()
            for l in p["loops"]:
                cl = CurveLoop()
                for c in l:
                    cl.Append(c)
                cls.Add(cl)
            id_hatch.append(FilledRegion.Create(doc, tk.Id, view.Id, cls).Id)
        except Exception as ex:
            bao_cao.append("Không hatch được 1 phòng (%s): %s" % (loai, ex))
    if id_hatch:
        try:     # hatch xuống dưới cùng để không đè nét vén (làm trước khi gom group)
            doc.Regenerate()
            DetailElementOrderUtils.SendToBack(doc, view, ds_id(id_hatch))
        except Exception as ex:
            bao_cao.append("Không đưa hatch xuống dưới được: %s" % str(ex).splitlines()[0])
    moi = []
    if ve_net:
        for c in net_ve:
            try:
                dc = doc.Create.NewDetailCurve(view, c)
                dc.LineStyle = gs
                moi.append(dc.Id)
            except Exception as ex:
                bao_cao.append("Không vẽ được 1 đoạn: %s" % ex)
    nhom_v = nhom_h = None
    try:
        if moi:
            nhom_v = gom_nhom(moi, "ARV_ChongTham_Ven")
        if id_hatch:
            nhom_h = gom_nhom(id_hatch, "ARV_ChongTham_Hatch")
    except Exception as ex:
        bao_cao.append("Không gom group được: %s" % ex)
    if AN_THIET_BI and an:
        try:
            view.HideElements(ds_id([e.Id for e in an]))
            bao_cao.append("ĐÃ ẨN %d thiết bị vệ sinh trong view" % len(an))
        except Exception as ex:
            bao_cao.append("Không ẩn được thiết bị: %s" % ex)
    TransactionManager.Instance.TransactionTaskDone()
    bao_cao.append("ĐÃ VẼ %d nét vén%s + %d hatch Filled Region%s" % (
        len(moi), (" (group '%s')" % nhom_v) if nhom_v else "", len(id_hatch),
        (" (group '%s')" % nhom_h) if nhom_h else ""))
    return view, moi + id_hatch


def xuat_anh(view):
    try:
        TransactionManager.Instance.ForceCloseTransaction()
        opt = ImageExportOptions()
        opt.ExportRange = ExportRange.SetOfViews
        opt.SetViewsAndSheets(ds_id([view.Id]))
        opt.FilePath = os.path.join(THU_MUC, "chong_tham")
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

log = os.path.join(THU_MUC, "chong_tham_%s.txt" % datetime.now().strftime("%Y%m%d_%H%M%S"))
with open(log, "w", encoding="utf-8") as f:
    f.write("\n".join(bao_cao))
bao_cao.append("Log: " + log)
OUT = bao_cao
