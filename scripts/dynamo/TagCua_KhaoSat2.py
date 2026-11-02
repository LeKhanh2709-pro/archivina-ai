# Khảo sát bổ sung cho công cụ tag cửa (CHỈ ĐỌC, không sửa model): cửa sổ + tag cửa sổ, cửa chống cháy (EI),
# nội bộ family tag (nhãn, hiển thị theo tham số, kích thước), kích thước tag trong view, phía cánh mở của cửa,
# view template + hiển thị nội thất của view đang mở.
# INPUT
#   IN[0] (str)  Thư mục ghi kết quả
# OUTPUT
#   OUT (list[str])
import os
import math
import traceback
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")
from Autodesk.Revit.DB import *
from RevitServices.Persistence import DocumentManager
from collections import Counter, defaultdict
from System.Collections.Generic import List as NetList

_thu_muc = IN[0]
os.makedirs(_thu_muc, exist_ok=True)
OUT = None


def _chinh():
    global OUT
    doc = DocumentManager.Instance.CurrentDBDocument
    lines = []

    def p(s=""):
        lines.append(str(s))

    def ghi():
        with open(os.path.join(_thu_muc, "khaosat2.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

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

    def ten_kieu(e):
        try:
            t = doc.GetElement(e.GetTypeId())
            return "%s : %s" % (t.FamilyName, ten(t))
        except Exception:
            return "?"

    def gt(e, ten_ts):
        try:
            pr = e.LookupParameter(ten_ts)
            if pr is None:
                return None
            return pr.AsString() if pr.StorageType == StorageType.String else pr.AsValueString()
        except Exception:
            return None

    def cuc_bo(e, pt):
        """toạ độ (dọc tường, theo mặt) của điểm pt so với e"""
        lc = e.Location.Point
        hv, fv = e.HandOrientation, e.FacingOrientation
        d = pt - lc
        return mm(d.X * hv.X + d.Y * hv.Y), mm(d.X * fv.X + d.Y * fv.Y)

    def bb_cuc_bo(e, v):
        bb = e.get_BoundingBox(v)
        if bb is None:
            return "-"
        xs, ys = [], []
        for x in (bb.Min.X, bb.Max.X):
            for y in (bb.Min.Y, bb.Max.Y):
                a, b = cuc_bo(e, XYZ(x, y, bb.Min.Z))
                xs.append(a)
                ys.append(b)
        return "dọc %s..%s, mặt %s..%s" % (min(xs), max(xs), min(ys), max(ys))

    # ---------- A. Cửa sổ ----------
    wins = list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsNotElementType())
    p("== A. CỬA SỔ (%d)" % len(wins))
    ck = Counter()
    tm = defaultdict(set)
    host = Counter()
    for w in wins:
        k = ten_kieu(w)
        ck[k] += 1
        t = doc.GetElement(w.GetTypeId())
        tm[k].add(gt(t, "Type Mark") or "")
        try:
            h = w.Host
            host[(h.GetType().Name + " " + ten(doc.GetElement(h.GetTypeId()))) if h is not None else "không host"] += 1
        except Exception:
            host["?"] += 1
    for k, v in ck.most_common():
        p("   %4d  %s | Type Mark=%s" % (v, k, "/".join(sorted(tm[k]))))
    p("Host: " + "; ".join("%s=%d" % kv for kv in host.most_common(10)))
    p("Mark ví dụ: " + ", ".join(sorted(set(gt(w, "Mark") or "" for w in wins))[:30]))
    ghi()

    # ---------- B. EI / chống cháy ----------
    p("")
    p("== B. CHỐNG CHÁY / EI TRÊN CỬA")
    doors = list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType())
    fr = Counter()
    ei_ts = Counter()
    for d in doors:
        t = doc.GetElement(d.GetTypeId())
        fr["%s | Fire Rating='%s'" % (ten_kieu(d), gt(t, "Fire Rating") or "")] += 1
        for e, loai in ((d, "inst"), (t, "type")):
            for pr in e.Parameters:
                n = pr.Definition.Name
                try:
                    v = pr.AsString() if pr.StorageType == StorageType.String else pr.AsValueString()
                except Exception:
                    v = None
                if "EI" in n.upper() or "CHAY" in n.upper() or "CHÁY" in n.upper() or (v and "EI" in v.upper()):
                    ei_ts["%s %s='%s'" % (loai, n, v)] += 1
    for k, v in fr.most_common():
        p("   %4d  %s" % (v, k))
    p("Tham số có EI / cháy: " + ("; ".join("%s ×%d" % kv for kv in ei_ts.most_common(30)) or "không có"))
    ghi()

    # ---------- C. Tag có sẵn: kích thước + vị trí ----------
    p("")
    p("== C. TAG CỬA / CỬA SỔ CÓ SẴN")
    for tg in FilteredElementCollector(doc).OfClass(IndependentTag):
        ids = list(tg.GetTaggedLocalElementIds())
        if not ids:
            continue
        e = doc.GetElement(ids[0])
        if e is None or e.Category is None or e.Category.Id.Value not in (int(BuiltInCategory.OST_Doors),
                                                                          int(BuiltInCategory.OST_Windows)):
            continue
        v = doc.GetElement(tg.OwnerViewId)
        bb = tg.get_BoundingBox(v)
        kt = "-"
        if bb is not None:
            kt = "%s x %s mm (giấy %.1f x %.1f)" % (mm(bb.Max.X - bb.Min.X), mm(bb.Max.Y - bb.Min.Y),
                                                     mm(bb.Max.X - bb.Min.X) / v.Scale, mm(bb.Max.Y - bb.Min.Y) / v.Scale)
            tam = (bb.Min + bb.Max) * 0.5
            tam_cb = cuc_bo(e, tam)
        else:
            tam_cb = "-"
        dau = cuc_bo(e, tg.TagHeadPosition)
        try:
            wt = mm(e.Host.Width)
        except Exception:
            wt = "?"
        p("   %s | %s | %s | 1:%d | %s | %r | đầu tag %s | tâm khung %s | khung %s | cửa: %s | tường dày %s | flipH %s flipF %s"
          % (e.Category.Name, ten(v), ten_kieu(tg), v.Scale, ten_kieu(e), tg.TagText, dau, tam_cb, kt,
             bb_cuc_bo(e, v), wt, e.HandFlipped, e.FacingFlipped))
    ghi()

    # ---------- D. Family tag: nội bộ ----------
    p("")
    p("== D. NỘI BỘ FAMILY TAG")
    cats = (int(BuiltInCategory.OST_DoorTags), int(BuiltInCategory.OST_WindowTags), int(BuiltInCategory.OST_MultiCategoryTags))
    fams = [f for f in FilteredElementCollector(doc).OfClass(Family)
            if f.FamilyCategory and f.FamilyCategory.Id.Value in cats]
    stt = 0
    for f in fams:
        p("-- %s [%s] kiểu: %s" % (f.Name, f.FamilyCategory.Name,
                                   ", ".join(ten(doc.GetElement(i)) for i in f.GetFamilySymbolIds())))
        try:
            fd = doc.EditFamily(f)
        except Exception as ex:
            p("   không mở được: %s" % ex)
            continue
        try:
            fm = fd.FamilyManager
            for fp in fm.Parameters:
                vals = []
                for ft in fm.Types:
                    try:
                        if fp.StorageType == StorageType.Integer:
                            vals.append("%s=%s" % (ft.Name, ft.AsInteger(fp)))
                        elif fp.StorageType == StorageType.Double:
                            vals.append("%s=%s" % (ft.Name, mm(ft.AsDouble(fp))))
                        else:
                            vals.append("%s=%s" % (ft.Name, ft.AsString(fp)))
                    except Exception:
                        pass
                p("   tham số: %s (%s, %s) %s" % (fp.Definition.Name, "inst" if fp.IsInstance else "type",
                                                 fp.StorageType, "; ".join(vals)))
            for e in FilteredElementCollector(fd).WhereElementIsNotElementType():
                cn = e.GetType().Name
                if e.Category is None and cn not in ("AnnotationLabel",):
                    continue
                if cn in ("Material", "ViewSheet", "PropertySetElement", "SunAndShadowSettings", "LoadCase"):
                    continue
                vis = ""
                try:
                    vp = e.get_Parameter(BuiltInParameter.IS_VISIBLE_PARAM)
                    if vp is not None:
                        a = fm.GetAssociatedFamilyParameter(vp)
                        vis = " | hiện theo '%s'" % a.Definition.Name if a else ""
                except Exception:
                    pass
                bb = None
                try:
                    vw = [x for x in FilteredElementCollector(fd).OfClass(View) if not x.IsTemplate]
                    bb = e.get_BoundingBox(vw[0] if vw else None)
                except Exception:
                    pass
                kt = ("[%s,%s]-[%s,%s]" % (mm(bb.Min.X), mm(bb.Min.Y), mm(bb.Max.X), mm(bb.Max.Y))) if bb else ""
                txt = ""
                if cn == "AnnotationLabel":
                    try:
                        txt = repr(e.Text)
                    except Exception:
                        pass
                    mem = [m for m in dir(e) if not m.startswith("_")]
                    p("   AnnotationLabel thành viên: " + ", ".join(mem))
                    for m in mem:
                        if m.startswith("Get") or m in ("Coord", "Position", "Width", "HorizontalAlignment"):
                            try:
                                at = getattr(e, m)
                                val = at() if callable(at) and m.startswith("Get") else at
                                p("      %s = %s" % (m, val))
                            except Exception as ex:
                                p("      %s: %s" % (m, ex))
                p("   %s %s %s%s %s" % (cn, e.Category.Name if e.Category else "", kt, vis, txt))
            # Ảnh view của family
            try:
                vw = [x for x in FilteredElementCollector(fd).OfClass(View) if not x.IsTemplate and x.CanBePrinted]
                if vw:
                    stt += 1
                    ds = NetList[ElementId]()
                    ds.Add(vw[0].Id)
                    opt = ImageExportOptions()
                    opt.ExportRange = ExportRange.SetOfViews
                    opt.SetViewsAndSheets(ds)
                    opt.FilePath = os.path.join(_thu_muc, "fam_%02d" % stt)
                    opt.ZoomType = ZoomFitType.FitToPage
                    opt.PixelSize = 1600
                    opt.HLRandWFViewsFileType = ImageFileType.PNG
                    fd.ExportImage(opt)
                    p("   ảnh: fam_%02d*.png" % stt)
            except Exception as ex:
                p("   ảnh lỗi: %s" % ex)
        finally:
            fd.Close(False)
        ghi()

    # ---------- E. View đang mở + template ----------
    p("")
    v = doc.ActiveView
    tpl = doc.GetElement(v.ViewTemplateId) if v.ViewTemplateId != ElementId.InvalidElementId else None
    p("== E. VIEW ĐANG MỞ: %s | 1:%d | template %s" % (ten(v), v.Scale, ten(tpl) if tpl else "-"))
    cat_kt = [BuiltInCategory.OST_Furniture, BuiltInCategory.OST_FurnitureSystems, BuiltInCategory.OST_Casework,
              BuiltInCategory.OST_SpecialityEquipment, BuiltInCategory.OST_PlumbingFixtures,
              BuiltInCategory.OST_GenericModel, BuiltInCategory.OST_ElectricalEquipment,
              BuiltInCategory.OST_LightingFixtures, BuiltInCategory.OST_DoorTags, BuiltInCategory.OST_WindowTags]
    for bic in cat_kt:
        cid = ElementId(bic)
        try:
            n = FilteredElementCollector(doc, v.Id).OfCategory(bic).WhereElementIsNotElementType().GetElementCount()
            p("   %s: ẩn trong view=%s, ẩn trong template=%s, số đối tượng thấy=%d"
              % (bic, v.GetCategoryHidden(cid), tpl.GetCategoryHidden(cid) if tpl else "-", n))
        except Exception as ex:
            p("   %s: %s" % (bic, ex))
    if tpl:
        try:
            p("   template điều khiển: " + ", ".join(str(i.Value) for i in tpl.GetTemplateParameterIds())[:300])
        except Exception:
            pass
    p("View template có trong dự án: " + "; ".join(sorted(ten(x) for x in FilteredElementCollector(doc).OfClass(View)
                                                          if x.IsTemplate)))
    # Đồ trong view theo hạng mục (để biết "nội thất" gồm gì)
    c = Counter()
    for e in FilteredElementCollector(doc, v.Id).WhereElementIsNotElementType():
        if e.Category is not None and e.Category.CategoryType == CategoryType.Model:
            c[e.Category.Name] += 1
    p("Hạng mục model thấy trong view: " + ", ".join("%s=%d" % kv for kv in c.most_common(30)))
    ghi()
    OUT = lines[:80]


try:
    _chinh()
except Exception:
    with open(os.path.join(_thu_muc, "loi2.txt"), "w", encoding="utf-8") as _f:
        _f.write(traceback.format_exc())
