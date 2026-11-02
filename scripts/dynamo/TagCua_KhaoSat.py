# Khảo sát tag cửa trong model Revit (CHỈ ĐỌC: không mở Transaction, không sửa gì) để viết công cụ tự động tag cửa.
# Ghi:
#   <IN[0]>\khaosat_tagcua.txt : family tag cửa (kiểu, nhãn trong family), cửa (family / type / Mark / kích thước),
#                                tag đang có (view, kiểu tag, leader, hướng, vị trí so với cửa), view mặt bằng
#   <IN[0]>\view*.png          : ảnh các view mặt bằng có tag cửa (để Claude xem cách đặt)
# INPUT
#   IN[0] (str)  Thư mục ghi kết quả (tạo nếu chưa có)
# OUTPUT
#   OUT (list[str])  Tóm tắt + đường dẫn file
import os
import traceback
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")
from Autodesk.Revit.DB import *
from RevitServices.Persistence import DocumentManager
from collections import Counter, defaultdict

_thu_muc = (IN[0] if len(IN) and IN[0] else os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs", "tagcua"))
os.makedirs(_thu_muc, exist_ok=True)
with open(os.path.join(_thu_muc, "da_chay.txt"), "w", encoding="utf-8") as _f:
    _f.write("Python node đã chạy")
OUT = None


def _chinh():
    global OUT
    doc = DocumentManager.Instance.CurrentDBDocument
    lines = []

    def p(s=""):
        lines.append(str(s))

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

    def ts(e, bip):
        try:
            pr = e.get_Parameter(bip)
            if pr is None:
                return ""
            return pr.AsString() or pr.AsValueString() or ""
        except Exception:
            return ""

    def ghi():
        with open(os.path.join(_thu_muc, "khaosat_tagcua.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    p("FILE: " + doc.PathName)
    p("VIEW ĐANG MỞ: %s (%s)" % (ten(doc.ActiveView), doc.ActiveView.ViewType))

    # ---------- 1. Family tag cửa / tag đa hạng mục ----------
    id_door_tag = int(BuiltInCategory.OST_DoorTags)
    id_multi = int(BuiltInCategory.OST_MultiCategoryTags)
    fams = [f for f in FilteredElementCollector(doc).OfClass(Family)
            if f.FamilyCategory and f.FamilyCategory.Id.Value in (id_door_tag, id_multi)]
    p("")
    p("== 1. FAMILY TAG CỬA / ĐA HẠNG MỤC (%d)" % len(fams))
    for f in fams:
        p("-- %s  [%s]" % (f.Name, f.FamilyCategory.Name))
        for tid in f.GetFamilySymbolIds():
            t = doc.GetElement(tid)
            ps = []
            for pr in t.Parameters:
                try:
                    v = pr.AsValueString() if pr.StorageType != StorageType.String else pr.AsString()
                    if v:
                        ps.append("%s=%s" % (pr.Definition.Name, v))
                except Exception:
                    pass
            p("     kiểu: %s | %s" % (ten(t), "; ".join(ps[:25])))
        # Đọc nhãn / chữ trong family (mở bản family trong bộ nhớ, đóng không lưu)
        try:
            fd = doc.EditFamily(f)
            try:
                for e in FilteredElementCollector(fd).WhereElementIsNotElementType():
                    cn = e.GetType().Name
                    if cn in ("TextElement", "TextNote", "Label") or "Text" in cn or "Label" in cn:
                        txt = ""
                        try:
                            txt = e.Text
                        except Exception:
                            pass
                        kieu = ""
                        try:
                            kieu = ten(fd.GetElement(e.GetTypeId()))
                        except Exception:
                            pass
                        p("     [%s] kiểu chữ '%s' : %r" % (cn, kieu, txt))
                pars = []
                for fp in fd.FamilyManager.Parameters:
                    pars.append(fp.Definition.Name)
                p("     tham số family: " + ", ".join(pars))
                # Nét / vùng trong family tag (để biết hình dạng ký hiệu)
                cnt = Counter(e.GetType().Name for e in FilteredElementCollector(fd).WhereElementIsNotElementType()
                              if e.Category is not None)
                p("     đối tượng: " + ", ".join("%s×%d" % kv for kv in cnt.most_common(15)))
            finally:
                fd.Close(False)
        except Exception as ex:
            p("     (không mở được family: %s)" % ex)
    ghi()

    # Kiểu tag mặc định cho cửa
    try:
        did = doc.GetDefaultFamilyTypeId(ElementId(BuiltInCategory.OST_DoorTags))
        p("KIỂU TAG CỬA MẶC ĐỊNH: " + (ten_kieu(doc.GetElement(did)) if did != ElementId.InvalidElementId else "(chưa đặt)"))
    except Exception as ex:
        p("Kiểu tag mặc định: lỗi %s" % ex)

    # ---------- 2. Cửa ----------
    doors = list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType())
    p("")
    p("== 2. CỬA (%d)" % len(doors))
    theo_kieu = Counter()
    theo_lv = Counter()
    mark_rong = 0
    marks = Counter()
    type_marks = defaultdict(set)
    host_cw = 0
    for d in doors:
        k = ten_kieu(d)
        theo_kieu[k] += 1
        lv = doc.GetElement(d.LevelId)
        theo_lv[ten(lv) if lv else "?"] += 1
        m = ts(d, BuiltInParameter.ALL_MODEL_MARK)
        if not m:
            mark_rong += 1
        marks[m] += 1
        t = doc.GetElement(d.GetTypeId())
        type_marks[k].add(ts(t, BuiltInParameter.ALL_MODEL_TYPE_MARK) if t else "")
        try:
            h = d.Host
            if h is not None and h.GetType().Name != "Wall":
                host_cw += 1
            elif h is not None and getattr(h, "CurtainGrid", None) is not None:
                host_cw += 1
        except Exception:
            pass
    p("Theo tầng: " + ", ".join("%s=%d" % kv for kv in theo_lv.most_common()))
    p("Mark trống: %d / %d ; Mark trùng: %d giá trị" % (mark_rong, len(doors), sum(1 for k, v in marks.items() if k and v > 1)))
    p("Cửa trên vách kính / host không phải tường thường: %d" % host_cw)
    p("Ví dụ Mark: " + ", ".join(sorted([k for k in marks if k])[:40]))
    for k, v in theo_kieu.most_common():
        t = None
        for d in doors:
            if ten_kieu(d) == k:
                t = doc.GetElement(d.GetTypeId())
                break
        rong = ts(t, BuiltInParameter.DOOR_WIDTH) or ts(t, BuiltInParameter.FAMILY_WIDTH_PARAM) if t else ""
        cao = ts(t, BuiltInParameter.DOOR_HEIGHT) or ts(t, BuiltInParameter.FAMILY_HEIGHT_PARAM) if t else ""
        p("   %4d  %s | Type Mark=%s | rộng %s cao %s" % (v, k, "/".join(sorted(type_marks[k])) or "-", rong, cao))
    # Tham số kiểu của một cửa mẫu mỗi family (để biết family có tham số mã cửa riêng không)
    da = set()
    for d in doors:
        t = doc.GetElement(d.GetTypeId())
        if t is None or t.FamilyName in da:
            continue
        da.add(t.FamilyName)
        ps_i = sorted(set(pr.Definition.Name for pr in d.Parameters))
        ps_t = sorted(set(pr.Definition.Name for pr in t.Parameters))
        p("   [tham số] %s\n      instance: %s\n      type: %s" % (t.FamilyName, ", ".join(ps_i), ", ".join(ps_t)))
    ghi()

    # ---------- 3. Tag đang có ----------
    tags = list(FilteredElementCollector(doc).OfClass(IndependentTag))
    p("")
    p("== 3. TAG ĐANG CÓ (%d tất cả hạng mục)" % len(tags))
    theo_cat = Counter()
    tag_cua = []
    for tg in tags:
        try:
            ids = list(tg.GetTaggedLocalElementIds())
        except Exception:
            ids = []
        cat = "?"
        if ids:
            e = doc.GetElement(ids[0])
            if e is not None and e.Category is not None:
                cat = e.Category.Name
                if e.Category.Id.Value == int(BuiltInCategory.OST_Doors):
                    tag_cua.append((tg, e))
        theo_cat["%s | %s" % (cat, ten_kieu(tg))] += 1
    for k, v in theo_cat.most_common(40):
        p("   %4d  %s" % (v, k))
    p("Tag cửa: %d" % len(tag_cua))
    theo_view = Counter()
    for tg, d in tag_cua:
        theo_view[ten(doc.GetElement(tg.OwnerViewId))] += 1
    p("Tag cửa theo view: " + ", ".join("%s=%d" % kv for kv in theo_view.most_common()))
    # Chi tiết vị trí: toạ độ đầu tag trong hệ của cửa (dọc tường = HandOrientation, vuông góc = FacingOrientation)
    p("Chi tiết (view | kiểu tag | Mark | leader | hướng tag | dx dọc tường, dy theo mặt cửa (mm) | rộng cửa | text):")
    for tg, d in tag_cua[:200]:
        try:
            v = doc.GetElement(tg.OwnerViewId)
            lc = d.Location.Point
            hd = tg.TagHeadPosition
            hv = d.HandOrientation
            fv = d.FacingOrientation
            dv = hd - lc
            dx = mm(dv.X * hv.X + dv.Y * hv.Y)
            dy = mm(dv.X * fv.X + dv.Y * fv.Y)
            t = doc.GetElement(d.GetTypeId())
            rong = ts(t, BuiltInParameter.DOOR_WIDTH) or ts(t, BuiltInParameter.FAMILY_WIDTH_PARAM)
            goc = round(__import__("math").degrees(__import__("math").atan2(hv.Y, hv.X)), 1)
            txt = ""
            try:
                txt = tg.TagText
            except Exception:
                pass
            p("   %s | %s | %s | leader=%s | %s | tường %s° | dx=%s dy=%s | %s | %r | cửa %s"
              % (ten(v), ten_kieu(tg), ts(d, BuiltInParameter.ALL_MODEL_MARK), tg.HasLeader, tg.TagOrientation,
                 goc, dx, dy, rong, txt, d.Id.Value))
        except Exception as ex:
            p("   lỗi %s" % ex)
    ghi()

    # ---------- 4. View mặt bằng ----------
    p("")
    p("== 4. VIEW MẶT BẰNG")
    views = [v for v in FilteredElementCollector(doc).OfClass(ViewPlan) if not v.IsTemplate]
    for v in views:
        tpl = doc.GetElement(v.ViewTemplateId) if v.ViewTemplateId != ElementId.InvalidElementId else None
        lv = v.GenLevel
        p("   %s | %s | 1:%d | tầng %s | template %s | trên sheet: %s"
          % (ten(v), v.ViewType, v.Scale, ten(lv) if lv else "-", ten(tpl) if tpl else "-",
             ts(v, BuiltInParameter.VIEWPORT_SHEET_NUMBER) or "-"))
    sheets = list(FilteredElementCollector(doc).OfClass(ViewSheet))
    p("Sheet (%d): %s" % (len(sheets), "; ".join("%s %s" % (s.SheetNumber, s.Name) for s in sheets[:40])))
    ghi()

    # ---------- 5. Ảnh ----------
    xuat = [doc.GetElement(i) for i in set(tg.OwnerViewId for tg, d in tag_cua)]
    if doc.ActiveView.Id not in [v.Id for v in xuat]:
        xuat.append(doc.ActiveView)
    try:
        from System.Collections.Generic import List as NetList
        ds = NetList[ElementId]()
        for v in xuat[:6]:
            ds.Add(v.Id)
        opt = ImageExportOptions()
        opt.ExportRange = ExportRange.SetOfViews
        opt.SetViewsAndSheets(ds)
        opt.FilePath = os.path.join(_thu_muc, "view")
        opt.ZoomType = ZoomFitType.FitToPage
        opt.PixelSize = 6000
        opt.ImageResolution = ImageResolution.DPI_300
        opt.HLRandWFViewsFileType = ImageFileType.PNG
        opt.ShadowViewsFileType = ImageFileType.PNG
        doc.ExportImage(opt)
        p("ẢNH: %s\\view*.png (%s)" % (_thu_muc, ", ".join(ten(v) for v in xuat[:6])))
    except Exception as ex:
        p("Không xuất được ảnh: %s" % ex)
    ghi()
    OUT = lines[:60]


try:
    _chinh()
except Exception:
    with open(os.path.join(_thu_muc, "loi.txt"), "w", encoding="utf-8") as _f:
        _f.write(traceback.format_exc())
