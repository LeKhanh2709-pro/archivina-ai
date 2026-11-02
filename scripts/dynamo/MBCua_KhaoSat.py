# Khảo sát cho công cụ "Mặt bằng định vị cửa" (CHỈ ĐỌC, không sửa model): view template mặt bằng có sẵn,
# đồ hoạ tường / sàn / cửa / cột trong từng template (V/G, filter, detail level), vật liệu tường / sàn
# (cut / surface pattern), xuất ảnh các view mặt bằng tầng để so với ảnh mẫu.
# INPUT
#   IN[0] (str)  Thư mục ghi kết quả
# OUTPUT
#   OUT (list[str])
import os
import traceback
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")
from Autodesk.Revit.DB import *
from RevitServices.Persistence import DocumentManager
from System.Collections.Generic import List as NetList

_thu_muc = IN[0]
os.makedirs(_thu_muc, exist_ok=True)
OUT = None

HANG_MUC = [
    ("Tường", BuiltInCategory.OST_Walls),
    ("Sàn", BuiltInCategory.OST_Floors),
    ("Cửa đi", BuiltInCategory.OST_Doors),
    ("Cửa sổ", BuiltInCategory.OST_Windows),
    ("Cột KT", BuiltInCategory.OST_Columns),
    ("Cột KC", BuiltInCategory.OST_StructuralColumns),
    ("Khung KC", BuiltInCategory.OST_StructuralFraming),
    ("Shaft", BuiltInCategory.OST_ShaftOpening),
    ("Generic", BuiltInCategory.OST_GenericModel),
    ("Phòng", BuiltInCategory.OST_Rooms),
    ("Lan can", BuiltInCategory.OST_StairsRailing),
    ("Thang", BuiltInCategory.OST_Stairs),
    ("Thiết bị VS", BuiltInCategory.OST_PlumbingFixtures),
    ("Filled region", BuiltInCategory.OST_DetailComponents),
]


def _chinh():
    global OUT
    doc = DocumentManager.Instance.CurrentDBDocument
    lines = []

    def p(s=""):
        lines.append(str(s))

    def ghi():
        with open(os.path.join(_thu_muc, "khaosat_mbcua.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def ten(e):
        try:
            return Element.Name.GetValue(e)
        except Exception:
            try:
                return e.Name
            except Exception:
                return "?"

    def mau(c):
        try:
            if c is None or not c.IsValid:
                return "-"
            return "%d,%d,%d" % (c.Red, c.Green, c.Blue)
        except Exception:
            return "-"

    def mau_nen(pid):
        try:
            if pid is None or pid == ElementId.InvalidElementId:
                return "-"
            e = doc.GetElement(pid)
            return ten(e) if e is not None else str(pid.Value)
        except Exception:
            return "?"

    def ogs_txt(o):
        if o is None:
            return "-"
        parts = []
        try:
            if o.Halftone:
                parts.append("HALFTONE")
        except Exception:
            pass
        for nhan, fn in [
            ("projLine", lambda: mau(o.ProjectionLineColor) + "/w" + str(o.ProjectionLineWeight) + "/pat" + mau_nen(o.ProjectionLinePatternId)),
            ("cutLine", lambda: mau(o.CutLineColor) + "/w" + str(o.CutLineWeight) + "/pat" + mau_nen(o.CutLinePatternId)),
            ("surfFg", lambda: ("vis" if o.IsSurfaceForegroundPatternVisible else "AN") + ":" + mau_nen(o.SurfaceForegroundPatternId) + ":" + mau(o.SurfaceForegroundPatternColor)),
            ("surfBg", lambda: ("vis" if o.IsSurfaceBackgroundPatternVisible else "AN") + ":" + mau_nen(o.SurfaceBackgroundPatternId) + ":" + mau(o.SurfaceBackgroundPatternColor)),
            ("cutFg", lambda: ("vis" if o.IsCutForegroundPatternVisible else "AN") + ":" + mau_nen(o.CutForegroundPatternId) + ":" + mau(o.CutForegroundPatternColor)),
            ("cutBg", lambda: ("vis" if o.IsCutBackgroundPatternVisible else "AN") + ":" + mau_nen(o.CutBackgroundPatternId) + ":" + mau(o.CutBackgroundPatternColor)),
            ("transp", lambda: str(o.Transparency)),
            ("detail", lambda: str(o.DetailLevel)),
        ]:
            try:
                parts.append("%s=%s" % (nhan, fn()))
            except Exception as ex:
                parts.append("%s=?(%s)" % (nhan, ex))
        return " | ".join(parts)

    p("== A. VIEW TEMPLATE MẶT BẰNG")
    views = list(FilteredElementCollector(doc).OfClass(View))
    tpl = [v for v in views if v.IsTemplate and v.ViewType in (ViewType.FloorPlan, ViewType.AreaPlan)]
    tpl_all = [v for v in views if v.IsTemplate]
    p("Tất cả template: %s" % "; ".join(sorted("%s [%s]" % (ten(v), v.ViewType) for v in tpl_all)))
    for t in sorted(tpl, key=ten):
        p("")
        p("-- TEMPLATE '%s' id=%d | scale 1:%s | detail %s | display %s" % (ten(t), t.Id.Value, t.Scale, t.DetailLevel, t.DisplayStyle))
        try:
            ctl = [doc.GetElement(i) for i in []]
            ks = t.GetTemplateParameterIds()
            khong = t.GetNonControlledTemplateParameterIds()
            p("   số tham số template: %d, không điều khiển: %d" % (ks.Count, khong.Count))
        except Exception as ex:
            p("   tham số template: ? %s" % ex)
        for nhan, bic in HANG_MUC:
            cid = ElementId(bic)
            try:
                an = t.GetCategoryHidden(cid)
            except Exception:
                an = "?"
            try:
                o = t.GetCategoryOverrides(cid)
            except Exception:
                o = None
            p("   %s: ẩn=%s | %s" % (nhan, an, ogs_txt(o)))
        try:
            for fid in t.GetFilters():
                f = doc.GetElement(fid)
                p("   FILTER '%s' vis=%s | %s" % (ten(f), t.GetFilterVisibility(fid), ogs_txt(t.GetFilterOverrides(fid))))
        except Exception as ex:
            p("   filter: ? %s" % ex)
        try:
            dung = [ten(v) for v in views if not v.IsTemplate and v.ViewTemplateId == t.Id]
            p("   view dùng: %s" % "; ".join(dung))
        except Exception:
            pass

    p("")
    p("== B. LOẠI TƯỜNG / SÀN (coarse pattern + vật liệu lớp)")
    for cls, nhan in ((WallType, "Tường"), (FloorType, "Sàn")):
        dem = 0
        for wt in FilteredElementCollector(doc).OfClass(cls):
            if dem > 40:
                break
            dem += 1
            try:
                cs = wt.GetCompoundStructure()
                lop = []
                if cs is not None:
                    for ly in cs.GetLayers():
                        m = doc.GetElement(ly.MaterialId)
                        if m is None:
                            lop.append("%s:-" % ly.Function)
                            continue
                        lop.append("%s:%s(cutFg %s %s, surfFg %s %s)" % (
                            ly.Function, ten(m), mau_nen(m.CutForegroundPatternId), mau(m.CutForegroundPatternColor),
                            mau_nen(m.SurfaceForegroundPatternId), mau(m.SurfaceForegroundPatternColor)))
                p("   %s '%s' coarse=%s %s | %s" % (nhan, ten(wt), mau_nen(wt.CoarseScaleFillPatternId), mau(wt.CoarseScaleFillPatternColor), " ; ".join(lop)))
            except Exception as ex:
                p("   %s '%s' ? %s" % (nhan, ten(wt), ex))

    p("")
    p("== C. VIEW MẶT BẰNG TẦNG")
    xuat = []
    for v in views:
        if v.IsTemplate or v.ViewType != ViewType.FloorPlan:
            continue
        t = doc.GetElement(v.ViewTemplateId) if v.ViewTemplateId != ElementId.InvalidElementId else None
        p("   %s | id %d | 1:%s | detail %s | template %s" % (ten(v), v.Id.Value, v.Scale, v.DetailLevel, ten(t) if t else "-"))
        if t is not None and (u"Định Vị Cửa" in ten(t) or u"1.1" in ten(t) or u"Cháy Lan" in ten(t)):
            xuat.append(v)
        elif ten(v) == u"Tầng 1":
            xuat.append(v)
    try:
        ds = NetList[ElementId]()
        for v in xuat[:6]:
            ds.Add(v.Id)
        opt = ImageExportOptions()
        opt.ExportRange = ExportRange.SetOfViews
        opt.SetViewsAndSheets(ds)
        opt.FilePath = os.path.join(_thu_muc, "view")
        opt.ZoomType = ZoomFitType.FitToPage
        opt.PixelSize = 4700
        opt.ImageResolution = ImageResolution.DPI_300
        opt.HLRandWFViewsFileType = ImageFileType.PNG
        opt.ShadowViewsFileType = ImageFileType.PNG
        doc.ExportImage(opt)
        p("ẢNH: %s (%s)" % (_thu_muc, ", ".join("%s [%d]" % (ten(v), v.Id.Value) for v in xuat[:6])))
    except Exception as ex:
        p("Không xuất được ảnh: %s" % ex)
    ghi()
    with open(os.path.join(_thu_muc, "da_chay.txt"), "w", encoding="utf-8") as f:
        f.write("ok")
    OUT = lines[:80]


try:
    _chinh()
except Exception:
    with open(os.path.join(_thu_muc, "loi.txt"), "w", encoding="utf-8") as _f:
        _f.write(traceback.format_exc())
    with open(os.path.join(_thu_muc, "da_chay.txt"), "w", encoding="utf-8") as _f:
        _f.write("loi")
