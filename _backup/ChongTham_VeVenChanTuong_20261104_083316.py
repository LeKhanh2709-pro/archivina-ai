# Vẽ nét vén chân tường chống thấm (Detail Line) trên view mặt bằng chống thấm của Revit.
# Hatch chống thấm = Filled Region 2D trong view (người dùng chốt 2026-10-27: không đụng hatch / filter của sàn gạch model).
#   - Nhận phòng ướt theo 2 nguồn:
#       a) sàn hoàn thiện ướt trên level (tên kiểu sàn chứa từ khoá, vd. "Gach Lat WC", "Gach Lat Logia")
#       b) bồn cầu / sen tắm / bồn tắm nằm ngoài mọi sàn ướt → WC chưa có sàn ướt (không dùng phễu thoát sàn)
#   - Biên phòng = mép tường thô / mặt lõi tường (room có sẵn tại điểm đó, hoặc room tạm trong SubTransaction rồi
#     rollback, không để lại gì trong model) → không bám theo khấc / lỗ của sàn. Room hở (không khép kín) hoặc tràn
#     sang phòng lớn thì quay về biên sàn. Không bao giờ bo vào lớp trát / hoàn thiện (người dùng chốt 2026-10-28).
#   - Mỗi vòng biên lùi vào trong phòng một khoảng (mặc định 50 mm) → nét vén, ngắt tại cửa đi
#   - Mọi phòng ướt được hatch bằng Filled Region theo biên mặt tường: kiểu "AV_Hatch Chống Thấm WC" / "... Logia"
#     (chưa có thì tạo, mẫu + màu lấy theo filter sàn SHT-WC / SHT-Logia của template), đưa xuống dưới nét vén
#   - View đã có nét vén: không vẽ lại vén (không xoá gì), chỉ bổ sung hatch cho phòng chưa có hatch
#   - Ẩn thiết bị vệ sinh trong view (Hide in View từng đối tượng, không sửa template), giữ phễu thoát sàn
#   - Detail Line kiểu nét "AV.Nét chống thấm" gom group "ARV_ChongTham_Ven"; Filled Region gom group "ARV_ChongTham_Hatch"
#   - Đặt lên bản vẽ (IN[10], không chạy khi Dry-run): sheet mới hoặc sheet trống có sẵn, mặt bằng giữa khổ giấy + chú thích
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
#   IN[10] (bool) Đặt mặt bằng lên bản vẽ (sheet) sau khi vẽ (người dùng yêu cầu 2026-11-03; nút pyRevit hỏi trong hộp thoại)
#   IN[11] (str)  Giai đoạn (giá trị thư mục cấp 1 của Project Browser, vd. TKBVTC)
#   IN[12] (str)  Hạng mục (thư mục cấp 2; chưa có thì tạo mới bằng cách gán giá trị mới)
#   IN[13] (str)  Khổ giấy (A1 / A0) – tìm family khung tên có chữ đó
#   IN[14] (str)  Khung tên "Family : Type" (trống = tự tìm theo khổ)
#   IN[15] (str)  Số hiệu sheet (trống = tiếp theo trong hạng mục; trùng sheet TRỐNG có sẵn = đặt vào sheet đó)
#   IN[16] (str)  Tên sheet (trống = "MẶT BẰNG CHỐNG THẤM <TẦNG>")
#   IN[17] (bool) Thêm chú thích (ô mẫu hatch WC / lô gia, nét vén + chữ) ở góc phải dưới bản vẽ
#   IN[18] (bool) Tầng của mặt bằng đang mở chưa có view chống thấm thì tạo view + template (người dùng yêu cầu 2026-11-04;
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
DAT_SHEET = bool(gia_tri(10, False))
SH_IN = [str(gia_tri(i, "")) for i in range(11, 17)]     # giai đoạn, hạng mục, khổ, khung tên, số hiệu, tên sheet
CHU_THICH = bool(gia_tri(17, True))
TAO_VIEW = bool(gia_tri(18, True))
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


def chon_hoac_tao_view():
    """IN[0] có tên → view đó. Không thì: view đang mở là view chống thấm → dùng; view đang mở là mặt bằng tầng → view
    chống thấm CÙNG TẦNG (tên view / template có chữ "chống thấm"), chưa có thì tạo (IN[18], sh_tao_view); còn lại như cũ."""
    av = doc.ActiveView
    if TEN_VIEW or not TAO_VIEW or av is None or av.ViewType != ViewType.FloorPlan or av.GenLevel is None:
        return chon_view()
    la = lambda v: "chong tham" in khong_dau(ten_tpl(v)) or "chong tham" in khong_dau(v.Name)
    if la(av):
        return av
    cung = sorted([v for v in FilteredElementCollector(doc).OfClass(ViewPlan) if not v.IsTemplate and la(v)
                   and v.GenLevel is not None and v.GenLevel.Id.Value == av.GenLevel.Id.Value], key=lambda v: v.Name)
    if cung:
        return cung[0]
    v, bao = sh_tao_view(doc, av, "chong tham", "MẶT BẰNG CHỐNG THẤM", DRY_RUN)
    bao_cao.extend(bao)
    return v


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
    """Các vòng biên mặt lõi tường (mép tường thô) của room, đã đưa về cao độ z; None nếu room hở"""
    opt = SpatialElementBoundaryOptions()
    opt.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.CoreBoundary
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
    view = chon_hoac_tao_view()
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
    co = set(e.Id.Value for e in tb_all)
    # thiết bị đã bị ẩn trong view (lần chạy trước ẩn đi) vẫn phải dùng để nhận WC (G19 2026-10-28: sót 1 WC không sàn)
    tb_all += [e for e in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures)
               .WhereElementIsNotElementType() if e.Id.Value not in co and e.IsHidden(view)]
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
#   template mới từ template của view gốc: tường + sàn Halftone, sàn tắt mẫu tô, ẩn nội thất / thiết bị cơ điện /
#   ký hiệu mặt đứng, mặt cắt. KHÔNG ẩn hạng mục thiết bị vệ sinh (công cụ ẩn từng cái, giữ phễu thoát sàn).
#   Template đã có thì dùng nguyên, không sửa. Không sửa view gốc / template gốc.
# Hàm, hằng ở khối này có tiền tố sh_ / SH_ để không trùng tên với file công cụ.
SH_BIEN_MM = 8.0             # lề trong vùng vẽ của khung tên (mm giấy)
SH_TIEU_DE_MM = 15.0         # chỗ tên view dưới viewport
SH_O_MAU_MM = (16.0, 7.0)    # ô mẫu chú thích (rộng, cao) mm giấy
SH_DONG_MM = 11.0            # khoảng cách dòng chú thích
SH_KHE_CHU_MM = 4.0          # khe giữa ô mẫu và chữ
SH_AN_VIEW_MOI = ("OST_Furniture", "OST_FurnitureSystems", "OST_Casework", "OST_SpecialityEquipment",
                  "OST_MechanicalEquipment", "OST_Elev", "OST_Sections")   # hạng mục ẩn trong template mới
SH_HALFTONE_VIEW_MOI = ("OST_Walls", "OST_Floors")
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
                tpl.SetCategoryOverrides(c, o)
            except Exception:
                pass
        an = []
        for n in SH_AN_VIEW_MOI:
            try:
                c = ElementId(getattr(BuiltInCategory, n))
                if tpl.CanCategoryBeHidden(c) and not tpl.GetCategoryHidden(c):
                    tpl.SetCategoryHidden(c, True)
                an.append(Category.GetCategory(doc, c).Name)
            except Exception:
                pass
        bao.append(u"Tạo view template '%s' từ '%s': tường + sàn Halftone, sàn tắt mẫu tô, ẩn: %s." % (
            ten_mau, tpl_goc.Name if tpl_goc is not None else u"view gốc", u", ".join(an)))
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
    TransactionManager.Instance.TransactionTaskDone()
    return moi, bao


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


def len_ban_ve(view):
    """Đặt view chống thấm lên sheet, chú thích theo hatch / nét đang có trong view."""
    muc = []
    if CHU_THICH:
        dung = set(r.GetTypeId().Value for r in FilteredElementCollector(doc, view.Id).OfClass(FilledRegion))
        for loai, nhan in (("wc", "CHỐNG THẤM SÀN WC"), ("logia", "CHỐNG THẤM SÀN LÔ GIA")):
            for t in FilteredElementCollector(doc).OfClass(FilledRegionType):
                if ten(t) == TEN_HATCH[loai] and t.Id.Value in dung:
                    muc.append({"vung": t.Id, "chu": nhan})
        for sc in doc.Settings.Categories.get_Item(BuiltInCategory.OST_Lines).SubCategories:
            if sc.Name == TEN_NET:
                gs = sc.GetGraphicsStyle(GraphicsStyleType.Projection)
                if any(c.LineStyle.Id == gs.Id for c in FilteredElementCollector(doc, view.Id).OfClass(CurveElement)
                       if c.CurveElementType == CurveElementType.DetailCurve):
                    muc.append({"net": gs, "chu": "VÉN CHỐNG THẤM CHÂN TƯỜNG"})
    tang = view.GenLevel.Name if view.GenLevel is not None else view.Name
    gd, hm, kho, khung, so, ten_sh = SH_IN
    ten_sh = (ten_sh or "MẶT BẰNG CHỐNG THẤM %s" % tang).strip().upper()
    bao_cao.extend(dat_mat_bang_len_sheet(doc, view, gd, hm, kho or "A1", khung, so, ten_sh, "A.CT.00", muc))


try:
    v, moi = chinh()
    xuat_anh(v)
    if DAT_SHEET and not DRY_RUN:
        len_ban_ve(v)
except Exception:
    bao_cao.append("LỖI: " + traceback.format_exc())

log = os.path.join(THU_MUC, "chong_tham_%s.txt" % datetime.now().strftime("%Y%m%d_%H%M%S"))
with open(log, "w", encoding="utf-8") as f:
    f.write("\n".join(bao_cao))
bao_cao.append("Log: " + log)
OUT = bao_cao
