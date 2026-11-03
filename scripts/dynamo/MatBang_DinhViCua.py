# ĐÃ GỘP vào TagCua_TuDong.py (IN[16] – IN[18], nút Tag cửa) theo yêu cầu người dùng 2026-11-03; file này giữ lại để
# chạy riêng bằng Dynamo, KHÔNG còn nút pyRevit và không cập nhật thêm (vd. chưa ẩn Mechanical Equipment).
# Tạo mặt bằng định vị cửa từ mặt bằng đang mở (người dùng yêu cầu 2026-11-02, mẫu theo ảnh mặt bằng chống cháy lan):
#   - Nhân bản view mặt bằng gốc (Duplicate, KHÔNG kèm chú thích / filled region), đặt tên theo mẫu IN[5]
#     (vd. "MẶT BẰNG ĐỊNH VỊ CỬA - Tầng 1"). View tên đó đã có thì không tạo thêm, chỉ mở view đó.
#   - Gán view template IN[1] ("MẶT BẰNG ĐỊNH VỊ CỬA"). Template đã có trong dự án thì dùng nguyên, KHÔNG sửa
#     (giữ phần người dùng đã chỉnh tay). Chưa có thì tạo: lấy template nền (mặc định template của view gốc, tức
#     đồ hoạ người dùng đang thấy; IN[2] có từ khoá thì lấy template mặt bằng có chữ đó, ưu tiên cùng tỉ lệ), rồi
#       + tường, sàn: Halftone (xám như ảnh mẫu); sàn: tắt mẫu tô bề mặt (nền trắng);
#       + cửa đi, cửa sổ: bỏ Halftone (nét đậm để định vị cửa, IN[8]);
#       + ẩn nội thất / thiết bị vệ sinh (IN[4]) để công cụ Tag cửa không phải tạo template "(ẩn nội thất)";
#       + bật hiện cửa đi, cửa sổ, tag cửa đi, tag cửa sổ.
#     API không nhân bản được view template → gán template nền cho view mới, Regenerate (template chỉ áp vào view khi
#     regenerate) rồi CreateViewTemplate. KHÔNG dùng ApplyViewTemplateParameters: thử trên G19 làm Revit 2027.3
#     lỗi nặng (generateViewSpecificGRep của tường) khi vẽ lại view.
#   - Không xoá, không sửa view gốc, không sửa template nền.
# INPUT
#   IN[0] (str)  Tên view mặt bằng gốc (để trống = view đang mở)
#   IN[1] (str)  Tên view template mặt bằng định vị cửa
#   IN[2] (str)  Từ khoá tìm template nền khi phải tạo template mới (trống = template của view gốc)
#   IN[3] (str)  Hạng mục để Halftone (tên BuiltInCategory), cách nhau bằng ;
#   IN[4] (str)  Hạng mục cần ẩn (tên BuiltInCategory), cách nhau bằng ;
#   IN[5] (str)  Mẫu tên view mới ({tang} = tên tầng, {view} = tên view gốc)
#   IN[6] (bool) Dry-run (True = chỉ báo cáo)
#   IN[7] (bool) Mở view mới sau khi tạo
#   IN[8] (str)  Hạng mục bỏ Halftone (tên BuiltInCategory), cách nhau bằng ;
# OUTPUT
#   OUT (list[str])  Báo cáo
import traceback
import unicodedata
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")
from Autodesk.Revit.DB import *
import Autodesk.Revit.DB as _RevitDB
# pythonnet 3.0: tên đã được import đích danh trước đó trong phiên bị loại khỏi "import *" → bổ sung đủ tên
globals().update({_n: getattr(_RevitDB, _n) for _n in dir(_RevitDB) if not _n.startswith("_") and _n not in globals()})
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

MAC_DINH = ["", u"MẶT BẰNG ĐỊNH VỊ CỬA", u"", "OST_Walls;OST_Floors",
            "OST_Furniture;OST_FurnitureSystems;OST_Casework;OST_SpecialityEquipment;OST_PlumbingFixtures",
            u"MẶT BẰNG ĐỊNH VỊ CỬA - {tang}", True, True, "OST_Doors;OST_Windows"]


def doc_in(i):
    try:
        v = IN[i]
    except Exception:
        v = None
    return MAC_DINH[i] if v is None or (isinstance(v, str) and v == "" and MAC_DINH[i] != "") else v


def khong_dau(s):
    s = unicodedata.normalize("NFD", u"%s" % (s or u"")).replace(u"đ", u"d").replace(u"Đ", u"D")
    return u"".join(c for c in s if unicodedata.category(c) != "Mn").lower().strip()


def tach(s):
    return [x.strip() for x in (s or "").split(";") if x.strip()]


def ten(e):
    try:
        return Element.Name.GetValue(e)
    except Exception:
        try:
            return e.Name
        except Exception:
            return "?"


def cat_ids(doc, ten_bic, bao):
    ds = []
    for n in ten_bic:
        try:
            ds.append(ElementId(getattr(BuiltInCategory, n)))
        except Exception:
            bao(u"Không có hạng mục '%s' → bỏ qua." % n)
    return ds


def ten_cat(doc, cid):
    try:
        return Category.GetCategory(doc, cid).Name
    except Exception:
        return str(cid.Value)


def _chinh():
    doc = DocumentManager.Instance.CurrentDBDocument
    bao_cao = []

    def p(s):
        bao_cao.append(u"%s" % s)

    # ---------- View gốc ----------
    ten_view = doc_in(0)
    av = doc.ActiveView
    if ten_view:
        ung = [v for v in FilteredElementCollector(doc).OfClass(ViewPlan)
               if not v.IsTemplate and v.ViewType == ViewType.FloorPlan and v.Name == ten_view]
        if av is not None and any(v.Id.Value == av.Id.Value for v in ung):
            ung = [av]
        goc = ung[0] if ung else None
        if goc is None:
            return [u"Không có mặt bằng (Floor Plan) tên '%s'." % ten_view]
    else:
        goc = av
    if goc is None or goc.IsTemplate or goc.ViewType != ViewType.FloorPlan or goc.GenLevel is None:
        return [u"View '%s' không phải mặt bằng tầng. Mở mặt bằng cần làm rồi chạy lại." % (ten(goc) if goc else "-")]
    dry = bool(doc_in(6))
    ten_tpl = (doc_in(1) or u"").strip()
    tang = goc.GenLevel.Name
    ten_moi = (doc_in(5) or MAC_DINH[5]).replace(u"{tang}", tang).replace(u"{view}", goc.Name).strip()
    p(u"View gốc: '%s' (tầng %s, 1:%s)%s" % (goc.Name, tang, goc.Scale, u" – DRY-RUN, không sửa mô hình" if dry else u""))

    views = list(FilteredElementCollector(doc).OfClass(View))
    da_co = [v for v in views if not v.IsTemplate and v.ViewType == ViewType.FloorPlan and v.Name == ten_moi]
    tpl = None
    for v in views:
        if v.IsTemplate and v.Name == ten_tpl:
            tpl = v

    # ---------- Template nền (chỉ dùng khi phải tạo template mới) ----------
    nen = None
    if tpl is None:
        tk = khong_dau(doc_in(2))
        if tk:
            ung = [v for v in views if v.IsTemplate and v.ViewType == ViewType.FloorPlan and tk in khong_dau(v.Name)
                   and khong_dau(v.Name) != khong_dau(ten_tpl) and not v.Name.endswith(u"(ẩn nội thất)")]
            ung.sort(key=lambda v: (0 if v.Scale == goc.Scale else 1, len(v.Name), v.Name))
            nen = ung[0] if ung else None
        if nen is None and goc.ViewTemplateId != ElementId.InvalidElementId:
            nen = doc.GetElement(goc.ViewTemplateId)

    # ---------- Dry-run: chỉ báo ----------
    if da_co:
        p(u"Đã có mặt bằng '%s' (id %d) → không tạo thêm, mở view đó." % (ten_moi, da_co[0].Id.Value))
    else:
        p(u"%s mặt bằng mới '%s' (nhân bản '%s', không kèm chú thích)." % (u"Sẽ tạo" if dry else u"Tạo", ten_moi, goc.Name))
    if tpl is not None:
        p(u"View template '%s' đã có trong dự án → dùng nguyên, không sửa." % ten_tpl)
    else:
        p(u"%s view template '%s' từ template nền '%s'." % (u"Sẽ tạo" if dry else u"Tạo", ten_tpl,
                                                             nen.Name if nen is not None else u"(không có, theo view)"))
    if dry:
        return bao_cao

    # ---------- Ghi ----------
    TransactionManager.Instance.EnsureInTransaction(doc)
    if da_co:
        moi = da_co[0]
    else:
        moi = doc.GetElement(goc.Duplicate(ViewDuplicateOption.Duplicate))
        moi.Name = ten_moi
    if tpl is None:
        nen_id = nen.Id if nen is not None else ElementId.InvalidElementId
        if moi.ViewTemplateId.Value != nen_id.Value:
            moi.ViewTemplateId = nen_id
        doc.Regenerate()        # template chỉ áp vào view khi regenerate
        tpl = moi.CreateViewTemplate()
        tpl.Name = ten_tpl
        # Template phải điều khiển V/G hạng mục model thì Halftone / ẩn mới có tác dụng
        try:
            pid = ElementId(BuiltInParameter.VIS_GRAPHICS_MODEL)
            nc = list(tpl.GetNonControlledTemplateParameterIds())
            if any(i.Value == pid.Value for i in nc):
                from System.Collections.Generic import List
                ds = List[ElementId]()
                for i in nc:
                    if i.Value != pid.Value:
                        ds.Add(i)
                tpl.SetNonControlledTemplateParameterIds(ds)
        except Exception as ex:
            p(u"Không bật được điều khiển V/G model của template: %s" % ex)
        xam = []
        for c in cat_ids(doc, tach(doc_in(3)), p):
            try:
                o = tpl.GetCategoryOverrides(c)
                o.SetHalftone(True)
                if c.Value == int(BuiltInCategory.OST_Floors):
                    o.SetSurfaceForegroundPatternVisible(False)
                    o.SetSurfaceBackgroundPatternVisible(False)
                tpl.SetCategoryOverrides(c, o)
                if tpl.GetCategoryHidden(c):
                    tpl.SetCategoryHidden(c, False)
                xam.append(ten_cat(doc, c))
            except Exception as ex:
                p(u"Không đặt được Halftone cho %s: %s" % (ten_cat(doc, c), ex))
        dam = []
        for c in cat_ids(doc, tach(doc_in(8)), p):
            try:
                o = tpl.GetCategoryOverrides(c)
                if o.Halftone:
                    o.SetHalftone(False)
                    tpl.SetCategoryOverrides(c, o)
                dam.append(ten_cat(doc, c))
            except Exception as ex:
                p(u"Không bỏ được Halftone cho %s: %s" % (ten_cat(doc, c), ex))
        an = []
        for c in cat_ids(doc, tach(doc_in(4)), p):
            try:
                if tpl.CanCategoryBeHidden(c):
                    if not tpl.GetCategoryHidden(c):
                        tpl.SetCategoryHidden(c, True)
                    an.append(ten_cat(doc, c))
            except Exception:
                pass
        for bic in (BuiltInCategory.OST_Doors, BuiltInCategory.OST_Windows,
                    BuiltInCategory.OST_DoorTags, BuiltInCategory.OST_WindowTags):
            try:
                if tpl.GetCategoryHidden(ElementId(bic)):
                    tpl.SetCategoryHidden(ElementId(bic), False)
            except Exception:
                pass
        p(u"   Halftone: %s; tắt mẫu tô bề mặt sàn; nét đậm (bỏ Halftone): %s; ẩn: %s"
          % (u", ".join(xam) or u"-", u", ".join(dam) or u"-", u", ".join(an) or u"-"))
    if moi.ViewTemplateId.Value != tpl.Id.Value:
        moi.ViewTemplateId = tpl.Id
    TransactionManager.Instance.TransactionTaskDone()
    p(u"Xong: mặt bằng '%s' (id %d) mang view template '%s'." % (moi.Name, moi.Id.Value, tpl.Name))
    if bool(doc_in(7)):
        try:
            DocumentManager.Instance.CurrentUIDocument.RequestViewChange(moi)
            p(u"Đã mở view '%s'. Tiếp theo có thể bấm nút Tag cửa trên view này." % moi.Name)
        except Exception as ex:
            p(u"Không mở được view mới (%s) – mở tay trong Project Browser." % ex)
    return bao_cao


try:
    OUT = _chinh()
except Exception:
    OUT = [u"LỖI:", traceback.format_exc()]
