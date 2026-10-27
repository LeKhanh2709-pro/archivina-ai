# Vẽ nét vén chân tường chống thấm (Detail Line) trên view mặt bằng chống thấm của Revit.
# Hatch chống thấm giữ nguyên cách đang dùng (filter sàn SHT-WC / SHT-Logia trong view template) → công cụ CHỈ vẽ nét vén.
#   - Lấy các sàn hoàn thiện ướt trên level của view (tên kiểu sàn chứa từ khoá, vd. "Gach Lat WC", "Gach Lat Logia")
#   - Mỗi đường biên sàn (cả lỗ trong) lùi vào trong sàn một khoảng (mặc định 50 mm) → nét vén
#   - Bỏ nét vén ở cạnh giáp một sàn ướt khác (sàn WC chia nhiều tấm)
#   - Ngắt nét vén tại cửa đi (cạnh song song với tường chứa cửa, trong bề rộng cửa)
#   - Vẽ Detail Line kiểu nét "AV.Nét chống thấm", gom vào 1 Detail Group "ARV_ChongTham_Ven"
# Dry-run (mặc định) chỉ báo cáo, không sửa mô hình. Không xoá gì: view đã có nét vén cùng kiểu thì dừng và báo.
# INPUT
#   IN[0] (str)   Tên view (để trống = view đang mở nếu template có "chống thấm", không thì view đầu tiên có template đó)
#   IN[1] (str)   Từ khoá tên kiểu sàn ướt, cách nhau bằng ;  (không phân biệt dấu / hoa thường)
#   IN[2] (float) Khoảng lùi nét vén vào trong sàn (mm)
#   IN[3] (str)   Tên line style nét vén
#   IN[4] (bool)  Dry-run (True = chỉ báo cáo)
#   IN[5] (bool)  Vẽ cả khi view đã có nét vén cùng kiểu
#   IN[6] (str)   Thư mục ghi log + ảnh (để trống = Documents\ARV_Logs\chong_tham)
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
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager
from System.Collections.Generic import List as NetList

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
os.makedirs(THU_MUC, exist_ok=True)

GOC_SONG_SONG = 20.0      # độ: cạnh vén lệch tường chứa cửa dưới góc này mới bị cắt
VUOT_CUA_MM = 150.0       # dải cắt vươn ra ngoài mặt tường mỗi bên (ngoài khoảng lùi)
NGAN_NHAT_MM = 5.0        # đoạn vén ngắn hơn thì bỏ
bao_cao = []


def mm(v):
    return UnitUtils.ConvertToInternalUnits(v, UnitTypeId.Millimeters)


def ra_mm(v):
    return UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.Millimeters)


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
    # điểm nằm trong số lẻ vòng biên = nằm trong sàn (vòng ngoài trừ lỗ)
    return sum(1 for pts in loops_pts if trong_da_giac(x, y, pts)) % 2 == 1


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


# ---------- chạy ----------
def chinh():
    view = chon_view()
    lv = view.GenLevel
    bao_cao.append("View: %s (template %s, level %s)" % (view.Name, ten_tpl(view) or "-", lv.Name if lv else "-"))
    if lv is None:
        raise Exception("View không gắn level")

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
    bao_cao.append("Sàn ướt trên level: %d (%s)" % (len(sans), "; ".join(
        "%s=%d" % (t, n) for t, n in sorted(dict((ten_kieu(f), sum(1 for g in sans if ten_kieu(g) == ten_kieu(f)))
                                                 for f in sans).items()))))

    # cửa đi trên level
    cua = [d for d in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType()
           if d.LevelId == lv.Id]
    vung_cuas, cua_loi = [], []
    for d in cua:
        try:
            vg = vung_cua(d)
        except Exception:
            vg = None
        if vg is None:
            cua_loi.append(str(d.Id.Value))
        else:
            vung_cuas.append(vg)
    bao_cao.append("Cửa đi trên level: %d (không đọc được bề rộng: %s)" % (len(cua), ", ".join(cua_loi) or "0"))

    d = mm(LUI_MM)
    z = lv.Elevation
    bien = {}
    for f in sans:
        try:
            loops = [[c for c in ca] for ca in doc.GetElement(f.SketchId).Profile]
            bien[f.Id.Value] = (loops, [diem_loop(l) for l in loops])
        except Exception:
            pass

    def giap_san_khac(ln, id_san):
        """Cạnh vén nằm sát một sàn ướt khác (phía ngoài sàn đang xét) → không vẽ"""
        a, b = ln.GetEndPoint(0), ln.GetEndPoint(1)
        m = (a + b) * 0.5
        n = XYZ(-(b - a).Y, (b - a).X, 0).Normalize() * (d + mm(60))
        for q in (m + n, m - n):
            if trong_san(q.X, q.Y, bien[id_san][1]):
                continue
            for k, (_, pts) in bien.items():
                if k != id_san and trong_san(q.X, q.Y, pts):
                    return True
        return False

    net_ve, san_loi, tong_cat, bo_giap = [], [], 0, 0
    for f in sans:
        try:
            if f.Id.Value not in bien:
                raise Exception("không đọc được sketch")
            loops, loops_pts = bien[f.Id.Value]
            for l in loops:
                lui = loop_lui_vao(l, loops_pts, d)
                if lui is None:
                    san_loi.append("%s (lùi vòng biên lỗi)" % f.Id.Value)
                    continue
                for c in lui:
                    if isinstance(c, Line) or c.GetType().Name == "Line":
                        a, b = c.GetEndPoint(0), c.GetEndPoint(1)
                        ln = Line.CreateBound(XYZ(a.X, a.Y, z), XYZ(b.X, b.Y, z))
                        if giap_san_khac(ln, f.Id.Value):
                            bo_giap += 1
                            continue
                        con, nc = ngat_tai_cua(ln, vung_cuas)
                        tong_cat += nc
                        net_ve += con
                    else:
                        net_ve.append(c.CreateTransformed(Transform.CreateTranslation(XYZ(0, 0, z - c.GetEndPoint(0).Z))))
        except Exception as ex:
            san_loi.append("%s (%s)" % (f.Id.Value, ex))
    bao_cao.append("Nét vén sẽ vẽ: %d đoạn, tổng %.1f m; số lần cắt tại cửa: %d; cạnh giáp sàn ướt khác bỏ: %d" % (
        len(net_ve), sum(ra_mm(c.Length) for c in net_ve) / 1000.0, tong_cat, bo_giap))
    if san_loi:
        bao_cao.append("Sàn lỗi (bỏ qua, cần xem lại): " + "; ".join(san_loi))

    if DRY_RUN:
        bao_cao.append("DRY-RUN: chưa vẽ gì. Đặt IN[4] = False để vẽ.")
        return view, []
    if da_co and not VE_CA_KHI_CO:
        bao_cao.append("DỪNG: view đã có %d nét '%s' (không tự xoá). Xoá tay hoặc đặt IN[5] = True để vẽ thêm."
                       % (len(da_co), TEN_NET))
        return view, []

    TransactionManager.Instance.EnsureInTransaction(doc)
    moi = []
    for c in net_ve:
        try:
            dc = doc.Create.NewDetailCurve(view, c)
            dc.LineStyle = gs
            moi.append(dc.Id)
        except Exception as ex:
            bao_cao.append("Không vẽ được 1 đoạn: %s" % ex)
    nhom = None
    if moi:
        try:
            g = doc.Create.NewGroup(NetList[ElementId](moi))
            ten_nhom = "ARV_ChongTham_Ven"
            da_dung = set(ten(t) for t in FilteredElementCollector(doc).OfClass(GroupType))
            i = 1
            while ten_nhom in da_dung:
                i += 1
                ten_nhom = "ARV_ChongTham_Ven_%d" % i
            doc.GetElement(g.GetTypeId()).Name = ten_nhom
            nhom = ten_nhom
        except Exception as ex:
            bao_cao.append("Không gom group được: %s" % ex)
    TransactionManager.Instance.TransactionTaskDone()
    bao_cao.append("ĐÃ VẼ %d nét vén%s" % (len(moi), (", group '%s'" % nhom) if nhom else ""))
    return view, moi


def xuat_anh(view):
    try:
        TransactionManager.Instance.ForceCloseTransaction()
        opt = ImageExportOptions()
        opt.ExportRange = ExportRange.SetOfViews
        opt.SetViewsAndSheets(NetList[ElementId]([view.Id]))
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
