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
# @@GHI_CHU_GOP@@


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
# @@HANG_SO_CHUNG@@
bao_cao = []


# @@PHAN_CHUNG@@


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
