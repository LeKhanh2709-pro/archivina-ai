# Tạo lỗ mở Shaft Opening cho mọi trục / hộp kỹ thuật trên mặt bằng tầng đang mở của Revit.
# Nhận trục / hộp đúng theo quy tắc của công cụ Ngăn cháy lan (dùng chung hàm tim_truc): tên room HKT → shaft opening
# → ống đứng → hình học (ô / khe kín giữa tường không cửa đi, cửa sổ, thiết bị, sàn hoàn thiện); loại thang máy / thang bộ.
#   - Biên lỗ mở = mép tường thô (dải lõi tường), không bo vào lớp trát / hoàn thiện (người dùng chốt 2026-10-28)
#   - Base Constraint = Top Constraint = level của mặt bằng đang mở; Base Offset -100 mm, Top Offset 1500 mm (mặc định,
#     người dùng chốt 2026-10-28)
#   - Comments của lỗ mở mới = "ARV_LoMo"; bấm lại: ô đã có shaft opening cắt qua tầng thì bỏ qua, không tạo trùng, không xoá
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
os.makedirs(THU_MUC, exist_ok=True)
GHI_CHU_LO_MO = "ARV_LoMo"

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


def chinh():
    view = chon_view()
    lv = view.GenLevel
    z = lv.Elevation
    bao_cao.append("View: %s (level %s) → lỗ mở Base / Top Constraint = %s, Base Offset %g mm, Top Offset %g mm" % (
        view.Name, lv.Name, lv.Name, BASE_OFFSET_MM, TOP_OFFSET_MM))
    zb, zt = z + mm(BASE_OFFSET_MM), z + mm(TOP_OFFSET_MM)
    shaft_co = []
    for e in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_ShaftOpening).WhereElementIsNotElementType():
        bb = e.get_BoundingBox(None)
        if bb is None or bb.Max.Z <= zb or bb.Min.Z >= zt:
            continue
        shaft_co.append(((bb.Min.X + bb.Max.X) / 2, (bb.Min.Y + bb.Max.Y) / 2))
    se_lam, da_co, bi_loai, xem_lai = tim_truc(
        view, lv, lambda v: any(trong_vung(p[0], p[1], v["pts"]) for p in shaft_co), "tạo lỗ mở",
        "shaft opening đã có cắt qua tầng: %d" % len(shaft_co))
    if DRY_RUN:
        TransactionManager.Instance.TransactionTaskDone()
        bao_cao.append("DRY-RUN: chưa tạo gì. Đặt IN[4] = False để tạo lỗ mở.")
        return view, []
    tren = sorted([l for l in FilteredElementCollector(doc).OfClass(Level) if l.Elevation > z + mm(1)],
                  key=lambda l: l.Elevation)
    moi = []
    for v in se_lam:
        ca = CurveArray()
        for l in v["loops"]:
            for c in l:
                ca.Append(c)
        try:
            try:
                op = doc.Create.NewOpening(lv, lv, ca)
            except Exception:
                if not tren:
                    raise
                op = doc.Create.NewOpening(lv, tren[0], ca)     # tạo tới tầng trên rồi đặt lại ràng buộc
            ok = (dat(op, BuiltInParameter.WALL_BASE_CONSTRAINT, "Base Constraint", lv.Id) and
                  dat(op, BuiltInParameter.WALL_BASE_OFFSET, "Base Offset", mm(BASE_OFFSET_MM)) and
                  dat(op, BuiltInParameter.WALL_HEIGHT_TYPE, "Top Constraint", lv.Id) and
                  dat(op, BuiltInParameter.WALL_TOP_OFFSET, "Top Offset", mm(TOP_OFFSET_MM)))
            dat(op, BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS, "Comments", GHI_CHU_LO_MO)
            if not ok:
                bao_cao.append("Lỗ mở %.2f m2 tại %s: không gán đủ ràng buộc (%s)" % (
                    v["m2"], toa_do(v["diem"]), doc_tham_so(op)))
            moi.append(op)
        except Exception as ex:
            bao_cao.append("Không tạo được lỗ mở %.2f m2 tại %s: %s" % (v["m2"], toa_do(v["diem"]), ex))
    doc.Regenerate()
    TransactionManager.Instance.TransactionTaskDone()
    bao_cao.append("ĐÃ TẠO %d lỗ mở Shaft Opening (Comments '%s')" % (len(moi), GHI_CHU_LO_MO))
    if moi:
        bao_cao.append("Kiểm tra lỗ mở đầu tiên: %s" % doc_tham_so(moi[0]))
    return view, [o.Id for o in moi]


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
