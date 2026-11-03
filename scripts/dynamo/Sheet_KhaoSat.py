# CHỈ ĐỌC: khảo sát để đặt view lên sheet tự động – cách nhóm sheet trong Project Browser (giai đoạn / hạng mục),
# tham số sheet, khung tên (family, khổ, kích thước), sheet có sẵn (số hiệu, tên, view trên đó, vị trí viewport),
# kiểu viewport, bảng thống kê cửa có sẵn; xuất ảnh vài sheet để xem bố cục.
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


def _chinh():
    global OUT
    doc = DocumentManager.Instance.CurrentDBDocument
    L = []

    def p(s=""):
        L.append(u"%s" % s)

    def mm(v):
        return round(UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.Millimeters), 1)

    def ten(e):
        try:
            return Element.Name.GetValue(e)
        except Exception:
            try:
                return e.Name
            except Exception:
                return "?"

    def gt(pr):
        if pr is None:
            return None
        try:
            if pr.StorageType == StorageType.String:
                return pr.AsString()
            if pr.StorageType == StorageType.ElementId:
                e = doc.GetElement(pr.AsElementId())
                return ten(e) if e is not None else pr.AsValueString()
            return pr.AsValueString()
        except Exception:
            return "?"

    p("== A. CÁCH NHÓM SHEET TRONG PROJECT BROWSER")
    try:
        bo = BrowserOrganization.GetCurrentBrowserOrganizationForSheets(doc)
        p("Browser organization sheet: '%s' id %d" % (ten(bo), bo.Id.Value))
        for prm in bo.Parameters:
            if prm.HasValue:
                p("   tham số tổ chức: %s = %s" % (prm.Definition.Name, gt(prm)))
        try:
            p("   sắp xếp theo: %s" % bo.SortingParameterId.Value)
        except Exception:
            pass
        for nm in dir(bo):
            if "Folder" in nm or "Sort" in nm:
                p("   member: " + nm)
    except Exception as ex:
        p("Không đọc được browser organization: %s" % ex)
    for e in FilteredElementCollector(doc).OfClass(BrowserOrganization):
        p("   có tổ chức: '%s' id %d" % (ten(e), e.Id.Value))

    p("")
    p("== B. SHEET CÓ SẴN")
    sheets = sorted(FilteredElementCollector(doc).OfClass(ViewSheet), key=lambda s: s.SheetNumber)
    bo = None
    try:
        bo = BrowserOrganization.GetCurrentBrowserOrganizationForSheets(doc)
    except Exception:
        pass
    for s in sheets:
        thu_muc = ""
        if bo is not None:
            try:
                thu_muc = " / ".join("%s" % fi.Name for fi in bo.GetFolderItems(s.Id))
            except Exception as ex:
                thu_muc = "?%s" % ex
        tb = list(FilteredElementCollector(doc, s.Id).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsNotElementType())
        tbs = ", ".join("%s : %s" % (doc.GetElement(t.GetTypeId()).FamilyName, ten(doc.GetElement(t.GetTypeId()))) for t in tb)
        p("-- %s | %s | thư mục: %s | khung: %s | placeholder=%s" % (s.SheetNumber, s.Name, thu_muc, tbs, s.IsPlaceholder))
        for prm in s.Parameters:
            try:
                if prm.Definition is not None and not prm.IsReadOnly and prm.HasValue and prm.StorageType == StorageType.String:
                    v = prm.AsString()
                    if v:
                        p("     %s = %s" % (prm.Definition.Name, v))
            except Exception:
                pass
        for vid in s.GetAllPlacedViews():
            v = doc.GetElement(vid)
            p("     view: %s [%s] 1:%s" % (ten(v), v.ViewType, getattr(v, "Scale", "-")))
        for vp in FilteredElementCollector(doc, s.Id).OfClass(Viewport):
            c = vp.GetBoxCenter()
            o = vp.GetBoxOutline()
            p("     viewport %s kiểu '%s' tâm (%s,%s) khung %s x %s" % (ten(doc.GetElement(vp.ViewId)), ten(doc.GetElement(vp.GetTypeId())),
                                                                    mm(c.X), mm(c.Y), mm(o.MaximumPoint.X - o.MinimumPoint.X), mm(o.MaximumPoint.Y - o.MinimumPoint.Y)))
        for si in FilteredElementCollector(doc, s.Id).OfClass(ScheduleSheetInstance):
            if si.IsTitleblockRevisionSchedule:
                continue
            bb = si.get_BoundingBox(s)
            p("     bảng: %s tại (%s,%s)" % (ten(doc.GetElement(si.ScheduleId)), mm(si.Point.X), mm(si.Point.Y)))
        for t in tb:
            bb = t.get_BoundingBox(s)
            if bb is not None:
                p("     khung tên bbox (%s,%s)-(%s,%s)" % (mm(bb.Min.X), mm(bb.Min.Y), mm(bb.Max.X), mm(bb.Max.Y)))

    p("")
    p("== C. FAMILY KHUNG TÊN")
    for s in FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_TitleBlocks):
        w = s.get_Parameter(BuiltInParameter.SHEET_WIDTH)
        h = s.get_Parameter(BuiltInParameter.SHEET_HEIGHT)
        p("   %s : %s | %s x %s" % (s.FamilyName, ten(s), mm(w.AsDouble()) if w else "-", mm(h.AsDouble()) if h else "-"))
        for prm in s.Parameters:
            try:
                if prm.Definition is not None and prm.StorageType == StorageType.Double and "width" not in prm.Definition.Name.lower():
                    pass
            except Exception:
                pass

    p("")
    p("== D. KIỂU VIEWPORT")
    for vt in FilteredElementCollector(doc).OfClass(ElementType):
        try:
            if vt.FamilyName == "Viewport":
                tt = vt.get_Parameter(BuiltInParameter.VIEWPORT_ATTR_LABEL_TAG)
                p("   '%s' title family: %s" % (ten(vt), gt(tt)))
        except Exception:
            pass

    p("")
    p("== E. BẢNG THỐNG KÊ")
    for vs in FilteredElementCollector(doc).OfClass(ViewSchedule):
        if vs.IsTemplate or vs.IsTitleblockRevisionSchedule:
            continue
        try:
            d = vs.Definition
            cat = Category.GetCategory(doc, d.CategoryId)
            cot = []
            for i in range(d.GetFieldCount()):
                f = d.GetField(i)
                cot.append("%s%s" % (f.GetName(), "(ẩn)" if f.IsHidden else ""))
            loc = []
            for i in range(d.GetFilterCount()):
                fl = d.GetFilter(i)
                loc.append("%s %s %s" % (d.GetField(fl.FieldId).GetName(), fl.FilterType, fl.GetStringValue() if fl.IsStringValue else (fl.GetElementIdValue().Value if fl.IsElementIdValue else "")))
            p("   '%s' [%s] cột: %s | lọc: %s | itemized=%s | tpl=%s" % (ten(vs), cat.Name if cat else "-", ", ".join(cot), "; ".join(loc), d.IsItemized,
                                                                     ten(doc.GetElement(vs.ViewTemplateId)) if vs.ViewTemplateId != ElementId.InvalidElementId else "-"))
        except Exception as ex:
            p("   '%s' ? %s" % (ten(vs), ex))

    p("")
    p("== F. THAM SỐ DỰ ÁN (Project Information)")
    pi = doc.ProjectInformation
    for prm in pi.Parameters:
        try:
            if prm.HasValue and prm.StorageType == StorageType.String and prm.AsString():
                p("   %s = %s" % (prm.Definition.Name, prm.AsString()))
        except Exception:
            pass

    # Ảnh các sheet có view (tối đa 4)
    try:
        ds = NetList[ElementId]()
        n = 0
        for s in sheets:
            if s.GetAllPlacedViews().Count and n < 4:
                ds.Add(s.Id)
                n += 1
        if n:
            opt = ImageExportOptions()
            opt.ExportRange = ExportRange.SetOfViews
            opt.SetViewsAndSheets(ds)
            opt.FilePath = os.path.join(_thu_muc, "sheet")
            opt.ZoomType = ZoomFitType.FitToPage
            opt.PixelSize = 3000
            opt.ImageResolution = ImageResolution.DPI_150
            opt.HLRandWFViewsFileType = ImageFileType.PNG
            opt.ShadowViewsFileType = ImageFileType.PNG
            doc.ExportImage(opt)
            p("ẢNH: %d sheet" % n)
    except Exception as ex:
        p("Không xuất ảnh: %s" % ex)
    with open(os.path.join(_thu_muc, "khaosat_sheet.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    with open(os.path.join(_thu_muc, "da_chay.txt"), "w", encoding="utf-8") as f:
        f.write("ok")
    OUT = L[:60]


try:
    _chinh()
except Exception:
    with open(os.path.join(_thu_muc, "loi.txt"), "w", encoding="utf-8") as _f:
        _f.write(traceback.format_exc())
    with open(os.path.join(_thu_muc, "da_chay.txt"), "w", encoding="utf-8") as _f:
        _f.write("loi")
