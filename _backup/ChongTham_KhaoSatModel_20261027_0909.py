# Khảo sát model Revit (CHỈ ĐỌC, không mở Transaction, không sửa gì) để viết công cụ chống thấm /
# ngăn cháy lan trục / lỗ mở MEP bản Revit.
# Chạy trên view mặt bằng của tầng cần làm (vd. tầng điển hình). Ghi:
#   <IN[0]>\khaosat.txt  : thống kê Room, sàn, cửa, thiết bị, trục / hộp kỹ thuật, link, kiểu hatch / nét / template
#   <IN[0]>\view.png     : ảnh view đang mở (để Claude xem)
# INPUT
#   IN[0] (str)  Thư mục ghi kết quả (tạo nếu chưa có)
# OUTPUT
#   OUT (list[str])  Tóm tắt + đường dẫn file
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Architecture import Room
from RevitServices.Persistence import DocumentManager
import os
from collections import Counter

doc = DocumentManager.Instance.CurrentDBDocument
view = doc.ActiveView
out_dir = IN[0] or os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs", "khaosat")
os.makedirs(out_dir, exist_ok=True)
lines = []


def mm(v):
    return round(UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.Millimeters), 1)


def m2(v):
    return round(UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.SquareMeters), 2)


def ten(e):
    try:
        return e.Name
    except Exception:
        return "?"


def fam_type(e):
    try:
        t = doc.GetElement(e.GetTypeId())
        f = t.FamilyName if hasattr(t, "FamilyName") else ""
        return "%s : %s" % (f, ten(t))
    except Exception:
        return "?"


def p(s=""):
    lines.append(str(s))


def bang(tieu_de, counter, n=60):
    p("== %s (%d loại, %d đối tượng)" % (tieu_de, len(counter), sum(counter.values())))
    for k, v in counter.most_common(n):
        p("   %5d  %s" % (v, k))


def comments(e):
    try:
        prm = e.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        return prm.AsString() or ""
    except Exception:
        return ""


p("FILE: %s | Revit %s | central: %s" % (doc.Title, doc.Application.VersionNumber,
                                         doc.IsWorkshared and "workshared" or "không"))
lv = view.GenLevel
p("VIEW: %s | loại %s | level %s | tỉ lệ 1/%s | template %s" % (
    view.Name, view.ViewType, lv.Name if lv else "-", view.Scale,
    ten(doc.GetElement(view.ViewTemplateId)) if view.ViewTemplateId != ElementId.InvalidElementId else "-"))
p("LEVELS: " + "; ".join("%s=%s" % (l.Name, mm(l.Elevation)) for l in
                         sorted(FilteredElementCollector(doc).OfClass(Level), key=lambda l: l.Elevation)))


def tren_level(cat):
    col = FilteredElementCollector(doc).OfCategory(cat).WhereElementIsNotElementType()
    out = []
    for e in col:
        try:
            if lv is None or e.LevelId == lv.Id:
                out.append(e)
        except Exception:
            pass
    return out


def tren_view(cat):
    return list(FilteredElementCollector(doc, view.Id).OfCategory(cat).WhereElementIsNotElementType())


# Room
rooms = [r for r in tren_level(BuiltInCategory.OST_Rooms) if r.Area > 0]
bang("ROOM trên level (tên)", Counter(r.get_Parameter(BuiltInParameter.ROOM_NAME).AsString() for r in rooms))
p("   mẫu: " + " | ".join("%s / %s / %s m2" % (r.Number, r.get_Parameter(BuiltInParameter.ROOM_NAME).AsString(),
                                               m2(r.Area)) for r in rooms[:15]))
try:
    p("   Room boundary location (option mặc định): Finish")
except Exception:
    pass
# Area (vùng diện tích) nếu có
areas = tren_level(BuiltInCategory.OST_Areas)
bang("AREA trên level", Counter(a.get_Parameter(BuiltInParameter.ROOM_NAME).AsString() for a in areas), 20)

# Sàn
floors = tren_level(BuiltInCategory.OST_Floors)
bang("SÀN trên level (type)", Counter(fam_type(f) for f in floors))
bang("SÀN Comments", Counter(comments(f)[:60] for f in floors), 40)
# Tường
walls = tren_level(BuiltInCategory.OST_Walls)
bang("TƯỜNG trên level (type)", Counter(fam_type(w) for w in walls))
# Cửa
doors = tren_level(BuiltInCategory.OST_Doors)
bang("CỬA ĐI (family : type)", Counter(fam_type(d) for d in doors))
mau = []
for d in doors[:12]:
    try:
        ph = doc.Phases[doc.Phases.Size - 1]
        fr, to = d.get_FromRoom(ph), d.get_ToRoom(ph)
        mau.append("%s: %s -> %s" % (d.Id.Value, fr and fr.get_Parameter(BuiltInParameter.ROOM_NAME).AsString(),
                                      to and to.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()))
    except Exception as ex:
        mau.append("%s: lỗi %s" % (d.Id.Value, ex))
p("   From/To room mẫu: " + " | ".join(mau))
bang("CỬA SỔ (family : type)", Counter(fam_type(d) for d in tren_level(BuiltInCategory.OST_Windows)))
# Thiết bị / nội thất (cả trong view: gồm link không tính)
bang("THIẾT BỊ VỆ SINH", Counter(fam_type(e) for e in tren_view(BuiltInCategory.OST_PlumbingFixtures)))
bang("NỘI THẤT", Counter(fam_type(e) for e in tren_view(BuiltInCategory.OST_Furniture)), 25)
bang("FURNITURE SYSTEMS / CASEWORK", Counter(fam_type(e) for e in tren_view(BuiltInCategory.OST_Casework)), 15)
bang("SPECIALTY EQUIPMENT", Counter(fam_type(e) for e in tren_view(BuiltInCategory.OST_SpecialityEquipment)), 25)
bang("MECHANICAL EQUIPMENT", Counter(fam_type(e) for e in tren_view(BuiltInCategory.OST_MechanicalEquipment)), 25)
bang("GENERIC MODEL", Counter(fam_type(e) for e in tren_view(BuiltInCategory.OST_GenericModel)), 40)
bang("CỘT (kiến trúc + kết cấu)", Counter(fam_type(e) for e in tren_view(BuiltInCategory.OST_Columns)) +
     Counter(fam_type(e) for e in tren_view(BuiltInCategory.OST_StructuralColumns)), 20)
# Trục / hộp kỹ thuật
shafts = list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_ShaftOpening).WhereElementIsNotElementType())
p("== SHAFT OPENING trong model: %d" % len(shafts))
pipes = tren_view(BuiltInCategory.OST_PipeCurves)
dung = 0
for pp in pipes:
    try:
        c = pp.Location.Curve
        d = c.GetEndPoint(1) - c.GetEndPoint(0)
        if abs(d.Normalize().Z) > 0.9:
            dung += 1
    except Exception:
        pass
p("== ỐNG trong view: %d (đứng: %d) | ống gió: %d" % (len(pipes), dung, len(tren_view(BuiltInCategory.OST_DuctCurves))))
bang("FLOOR OPENING / lỗ sàn", Counter(fam_type(e) for e in tren_view(BuiltInCategory.OST_FloorOpening)), 10)
# Detail / annotation có sẵn
bang("FILLED REGION trong view (type)", Counter(fam_type(e) for e in tren_view(BuiltInCategory.OST_DetailComponents)
                                                if isinstance(e, FilledRegion)), 20)
bang("DETAIL ITEM trong view", Counter(fam_type(e) for e in tren_view(BuiltInCategory.OST_DetailComponents)
                                       if not isinstance(e, FilledRegion)), 30)
p("== FILLED REGION TYPE: " + "; ".join(ten(t) for t in FilteredElementCollector(doc).OfClass(FilledRegionType)))
fp = list(FilteredElementCollector(doc).OfClass(FillPatternElement))
p("== FILL PATTERN (%d): " % len(fp) + "; ".join("%s[%s]" % (ten(f), f.GetFillPattern().Target) for f in fp[:80]))
lines_cat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Lines)
p("== LINE STYLE: " + "; ".join(sc.Name for sc in lines_cat.SubCategories))
tpl = [v for v in FilteredElementCollector(doc).OfClass(View) if v.IsTemplate]
p("== VIEW TEMPLATE (%d): " % len(tpl) + "; ".join(v.Name for v in tpl))
# Link
p("== LINK REVIT: " + "; ".join(ten(l) for l in FilteredElementCollector(doc).OfClass(RevitLinkInstance)))
p("== LINK / IMPORT CAD: " + "; ".join(ten(doc.GetElement(i.GetTypeId())) for i in
                                        FilteredElementCollector(doc).OfClass(ImportInstance)))
# Family detail item đã load (tìm khung lỗ mở / MEP)
fams = [f for f in FilteredElementCollector(doc).OfClass(Family)
        if f.FamilyCategory and f.FamilyCategory.Id.Value in (int(BuiltInCategory.OST_DetailComponents),
                                                               int(BuiltInCategory.OST_GenericAnnotation))]
p("== FAMILY DETAIL / ANNOTATION (%d): " % len(fams) + "; ".join(f.Name for f in fams[:120]))

# Ảnh view đang mở
anh = os.path.join(out_dir, "view")
try:
    opt = ImageExportOptions()
    opt.ExportRange = ExportRange.CurrentView
    opt.FilePath = anh
    opt.ZoomType = ZoomFitType.FitToPage
    opt.PixelSize = 2400
    opt.ImageResolution = ImageResolution.DPI_150
    opt.HLRandWFViewsFileType = ImageFileType.PNG
    opt.ShadowViewsFileType = ImageFileType.PNG
    doc.ExportImage(opt)
    p("ẢNH VIEW: " + anh + "*.png")
except Exception as ex:
    p("Không xuất được ảnh view: %s" % ex)

f_out = os.path.join(out_dir, "khaosat.txt")
with open(f_out, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
OUT = ["Đã ghi " + f_out] + lines[:40]
