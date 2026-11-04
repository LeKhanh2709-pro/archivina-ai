# Triển khai chi tiết cửa (người dùng yêu cầu 2026-11-03, mẫu bản vẽ "CHI TIẾT CỬA" A.CD.22.13): chọn 1 cửa đi / cửa sổ
# có sẵn family → tạo mặt bằng, mặt đứng, mặt cắt tỉ lệ 1/25 rồi đặt vào ô trống tiếp theo của sheet "CHI TIẾT CỬA"
# (khung A1 chia 6 ô: 2 hàng × 3 cột). Ký hiệu, vật liệu, phụ kiện người dùng tự điền vào phần trống của ô.
#   - Mặt bằng: callout từ mặt bằng tầng của cửa (ưu tiên view đang mở nếu đúng tầng), khung nhìn = cửa + lề IN[5],
#     XOAY theo mặt đứng (người dùng yêu cầu 2026-11-03): phía phải mặt bằng = phía phải mặt đứng, ngoài nhà ở dưới;
#     khung callout trên mặt bằng gốc ẩn bằng Hide in View (IN[13]).
#   - Mặt đứng CHỈ CÓ CỬA (tường, sàn, phần tử khác Hide in View); level ẩn trên mặt đứng + mặt cắt, thay bằng nét
#     đứt cốt sàn + chữ "CỐT SÀN HOÀN THIỆN <tên phòng>" có mũi tên trên mặt cắt (như mẫu người dùng gửi 2026-11-03).
#   - Mặt đứng: section đặt trước mặt tường, không cắt cửa, nhìn từ NGOÀI NHÀ. Phía ngoài nhà: một bên không có room
#     → bên đó; cả 2 bên có room thì bên có tên lô gia / ban công / sân; không rõ → phía KHÔNG mở cánh (theo cung mở
#     trên mặt bằng); cửa không có cung mở → mặt ngoài family (Facing). IN[11] ép phía nhìn.
#   - Mặt cắt: section vuông góc tường, cắt qua cánh cửa (cách tâm cửa 1/4 bề rộng), ngoài nhà nằm bên phải.
#     Ký hiệu section ẩn ở tỉ lệ thô hơn 1:<tỉ lệ> (mặt bằng 1/100 không thấy), mặt đứng / mặt cắt ẩn ký hiệu của nhau.
#   - View template: IN[6] – IN[8]; đã có thì dùng nguyên, KHÔNG sửa; chưa có thì tạo từ template nền (theo từ khoá
#     IN[9], không có thì template cùng tỉ lệ), tỉ lệ IN[4], Detail Level Fine, ẩn hạng mục IN[10], để view tự giữ
#     Far Clipping (template nền điều khiển Far Clipping thì mặt cắt thấy cả phòng phía sau).
#   - Kích thước tổng (IN[12]): mặt bằng = rộng; mặt đứng = rộng + cao (cửa sổ: cao độ bậu tính từ sàn + cao cửa);
#     mặt cắt = cao. Reference lấy từ family (Left / Right / Top / Bottom); family không có thì lấy mặt lỗ mở của tường
#     (mép, đỉnh, bậu); chân = nét cốt sàn.
#   - Sheet: tên IN[2]; chỉ dùng sheet do công cụ này tạo (có group lưới ô "ARV_ChiTietCua_Luoi ..."), KHÔNG đặt view
#     vào sheet người dùng tự làm dù trùng tên. Hết ô thì tạo sheet mới khung IN[1], số sheet = số lớn nhất của các
#     sheet tên IN[2] + 1 (chưa có sheet nào tên đó thì IN[3]). Lưới ô: Detail Line trên sheet (2 nét đứng, 1 nét ngang
#     chia vùng vẽ của khung tên + 1 nét ngăn dải thông tin dưới mỗi ô).
#   - Mỗi type cửa chỉ làm 1 lần: đã có view "CT CỬA <Type Mark> - MẶT ĐỨNG" thì báo và mở sheet chứa view đó.
#   - Không xoá, không sửa cửa / tường / view gốc / template đã có.
# Giới hạn: cửa trong file link không chọn được.
# INPUT
#   IN[0]  (str)   ID cửa (trống = cửa đang chọn; chưa chọn thì chọn trên màn hình)
#   IN[1]  (str)   Khung tên cho sheet mới (tên type title block)
#   IN[2]  (str)   Tên sheet chi tiết cửa
#   IN[3]  (str)   Số sheet đầu tiên (khi dự án chưa có sheet nào tên IN[2])
#   IN[4]  (float) Tỉ lệ (25 = 1/25)
#   IN[5]  (float) Lề khung nhìn quanh cửa (mm)
#   IN[6]  (str)   Tên view template mặt bằng
#   IN[7]  (str)   Tên view template mặt đứng
#   IN[8]  (str)   Tên view template mặt cắt
#   IN[9]  (str)   Từ khoá template nền khi phải tạo template: mặt bằng;mặt đứng;mặt cắt (không dấu)
#   IN[10] (str)   Hạng mục ẩn trong template mới (tên BuiltInCategory, cách nhau bằng ;)
#   IN[11] (str)   Phía nhìn mặt đứng: trống = tự động; facing = mặt ngoài family; nguoc = ngược Facing
#   IN[12] (bool)  Đặt kích thước tổng
#   IN[13] (bool)  Ẩn khung callout trên mặt bằng gốc
#   IN[14] (bool)  Dry-run (True = chỉ báo cáo)
#   IN[15] (bool)  Mở sheet sau khi tạo
# OUTPUT
#   OUT (list[str])  Báo cáo
import math
import re
import traceback
import unicodedata
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
clr.AddReference("RevitServices")
from Autodesk.Revit.DB import *
import Autodesk.Revit.DB as _RevitDB
# pythonnet 3.0: tên đã được import đích danh trước đó trong phiên bị loại khỏi "import *" → bổ sung đủ tên
globals().update({_n: getattr(_RevitDB, _n) for _n in dir(_RevitDB) if not _n.startswith("_") and _n not in globals()})
from Autodesk.Revit.UI.Selection import ObjectType
from System.Collections.Generic import List
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

TRANSACTION_NAME = u"ARV - Chi tiết cửa"
MAC_DINH = ["", u"AV-Khung A1(841x594)-Kien Truc", u"CHI TIẾT CỬA", u"A.CD.01", 25.0, 300.0,
            u"CHI TIẾT CỬA - MẶT BẰNG", u"CHI TIẾT CỬA - MẶT ĐỨNG", u"CHI TIẾT CỬA - MẶT CẮT",
            u"chi tiet mat bang;chi tiet mat dung;mat cat chi tiet",
            "OST_Furniture;OST_FurnitureSystems;OST_Casework;OST_SpecialityEquipment;OST_PlumbingFixtures;OST_Grids",
            u"", True, True, True, True]
NHOM_LUOI = u"ARV_ChiTietCua_Luoi"
TEN_NGOAI = (u"logia", u"lo gia", u"ban cong", u"balcony", u"san phoi", u"san thuong", u"terrace", u"ngoai nha")
SO_COT, SO_HANG = 3, 2
TI_LE_DAI_TT = 0.22          # dải thông tin dưới mỗi ô (tỉ lệ chiều cao ô)
UP = XYZ.BasisZ


def doc_in(i):
    try:
        v = IN[i]
    except Exception:
        v = None
    return MAC_DINH[i] if v is None or (isinstance(v, str) and v == "" and MAC_DINH[i] != "") else v


def ft(x_mm):
    return UnitUtils.ConvertToInternalUnits(float(x_mm), UnitTypeId.Millimeters)


def mm(x_ft):
    return UnitUtils.ConvertFromInternalUnits(x_ft, UnitTypeId.Millimeters)


def khong_dau(s):
    s = unicodedata.normalize("NFD", u"%s" % (s or u"")).replace(u"đ", u"d").replace(u"Đ", u"D")
    return u"".join(c for c in s if unicodedata.category(c) != "Mn").lower().strip()


def tach(s):
    return [x.strip() for x in (s or "").split(";") if x.strip()]


def ten(e):
    """Tên phần tử; PythonNet3 không đọc được Element.Name của ElementType → đọc qua tham số."""
    if e is None:
        return u"-"
    try:
        n = e.Name
        if n:
            return n
    except Exception:
        pass
    for bip in (BuiltInParameter.SYMBOL_NAME_PARAM, BuiltInParameter.ALL_MODEL_TYPE_NAME):
        try:
            p = e.get_Parameter(bip)
            if p is not None and p.AsString():
                return p.AsString()
        except Exception:
            pass
    return u"?"


def ten_view_hop_le(s):
    return re.sub(u"[\\\\:{}\\[\\]|;<>?`~]", u"", s).strip()


def ten_cat(doc, cid):
    try:
        return Category.GetCategory(doc, cid).Name
    except Exception:
        return str(cid.Value)


# ---------------------------------------------------------------- hình học cửa / tường
def diem_hinh(geo, ds):
    """Gom điểm (đỉnh cạnh solid, điểm curve 3D) của GeometryElement vào ds."""
    for g in geo:
        tn = g.GetType().Name
        if tn == "GeometryInstance":
            diem_hinh(g.GetInstanceGeometry(), ds)
        elif tn == "Solid":
            if g.Volume <= 0:
                continue
            for c in g.Edges:
                ds.extend(list(c.Tessellate()))
        elif tn in ("Line", "Arc", "NurbSpline", "HermiteSpline", "Ellipse"):
            ds.extend(list(g.Tessellate()))


def cung_mo(geo, ds):
    """Cung (Arc) trên hình mặt bằng của cửa = cung mở cánh."""
    for g in geo:
        tn = g.GetType().Name
        if tn == "GeometryInstance":
            cung_mo(g.GetInstanceGeometry(), ds)
        elif tn == "Arc":
            ds.append(g)


def mat_tuong(wall):
    """Các PlanarFace của tường (có reference để dim)."""
    opt = Options()
    opt.ComputeReferences = True
    opt.DetailLevel = ViewDetailLevel.Fine
    ds = []

    def duyet(geo):
        for g in geo:
            tn = g.GetType().Name
            if tn == "GeometryInstance":
                duyet(g.GetInstanceGeometry())
            elif tn == "Solid" and g.Volume > 0:
                for f in g.Faces:
                    if f.GetType().Name == "PlanarFace" and f.Reference is not None:
                        ds.append(f)
    try:
        duyet(wall.get_Geometry(opt))
    except Exception:
        pass
    return ds


def tam_mat(f):
    bb = f.GetBoundingBox()
    return f.Evaluate((bb.Min + bb.Max) * 0.5)


def ref_family(fi, loai):
    try:
        ds = list(fi.GetReferences(getattr(FamilyInstanceReferenceType, loai)))
        return ds[0] if ds else None
    except Exception:
        return None


# ---------------------------------------------------------------- sheet
NET_KHUNG = {}       # id family khung tên → danh sách nét (toạ độ family), đọc 1 lần mỗi lần chạy


def doc_net_khung(doc, tb_type, bao):
    """Nét thẳng trong family khung tên (Revit không trả hình học của khung tên trên sheet → mở family trong bộ nhớ,
    đọc, đóng không lưu). Phải gọi khi chưa mở transaction."""
    fam = tb_type.Family
    k = fam.Id.Value
    if k in NET_KHUNG:
        return NET_KHUNG[k]
    ds = []
    try:
        TransactionManager.Instance.ForceCloseTransaction()
        fdoc = doc.EditFamily(fam)
        try:
            for ce in FilteredElementCollector(fdoc).OfClass(CurveElement):
                c = ce.GeometryCurve
                if c is not None and c.GetType().Name == "Line":
                    ds.append((c.GetEndPoint(0), c.GetEndPoint(1)))
        finally:
            fdoc.Close(False)
    except Exception as ex:
        bao(u"   Không đọc được nét family khung tên (%s) → dùng lề mặc định." % ex)
    NET_KHUNG[k] = ds
    return ds


def vung_ve(doc, sheet, tb, bao):
    """Vùng vẽ của khung tên (feet, toạ độ sheet): (trái, dưới, phải, trên). Dò nét viền trong + mép trái dải khung tên."""
    bb = tb.get_BoundingBox(sheet)
    x0, y0, x1, y1 = bb.Min.X, bb.Min.Y, bb.Max.X, bb.Max.Y
    W, H = x1 - x0, y1 - y0
    tr = tb.GetTransform()
    doc_x, doc_y = {}, {}          # cộng dồn chiều dài nét đứng / ngang cùng toạ độ (nét viền có thể bị chia đoạn)
    for a, b in NET_KHUNG.get(doc.GetElement(tb.GetTypeId()).Family.Id.Value, []):
        a, b = tr.OfPoint(a), tr.OfPoint(b)
        if abs(a.X - b.X) < 1e-4:
            k = round(mm(a.X), 0)
            doc_x[k] = doc_x.get(k, 0) + abs(a.Y - b.Y)
        elif abs(a.Y - b.Y) < 1e-4:
            k = round(mm(a.Y), 0)
            doc_y[k] = doc_y.get(k, 0) + abs(a.X - b.X)
    xs = [ft(k) for k, d in doc_x.items() if d > 0.7 * H]
    ys = [ft(k) for k, d in doc_y.items() if d > 0.5 * W]
    # Mặc định theo khung AV-Khung A1 (viền trong cách mép ~35 / 16 mm, dải khung tên bên phải rộng ~110 mm)
    trai = max([x for x in xs if x0 - 1e-3 <= x <= x0 + 0.15 * W] or [x0 + ft(35)])
    # mép phải vùng vẽ = nét đứng dài trái nhất ở nửa phải (mép trái dải khung tên; không có dải thì là viền trong)
    phai = min([x for x in xs if x0 + 0.6 * W <= x <= x1 - ft(5)] or [x1 - ft(110)])
    duoi = max([y for y in ys if y0 - 1e-3 <= y <= y0 + 0.15 * H] or [y0 + ft(16)])
    tren = min([y for y in ys if y1 - 0.15 * H <= y <= y1 + 1e-3] or [y1 - ft(17)])
    return trai, duoi, phai, tren


def mat_san(doc, q, z_tren):
    """Reference mặt trên sàn cao nhất dưới điểm q (x, y) có cao độ ≤ z_tren. Trả về (reference, z) / (None, None)."""
    ol = Outline(XYZ(q.X - ft(10), q.Y - ft(10), z_tren - ft(1500)), XYZ(q.X + ft(10), q.Y + ft(10), z_tren + ft(10)))
    opt = Options()
    opt.ComputeReferences = True
    tot = (None, None)
    for fl in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Floors).WhereElementIsNotElementType() \
            .WherePasses(BoundingBoxIntersectsFilter(ol)):
        ds = []

        def duyet(geo):
            for g in geo:
                tn = g.GetType().Name
                if tn == "GeometryInstance":
                    duyet(g.GetInstanceGeometry())
                elif tn == "Solid" and g.Volume > 0:
                    for f in g.Faces:
                        if f.GetType().Name == "PlanarFace" and f.FaceNormal.Z > 0.99 and f.Reference is not None:
                            ds.append(f)
        try:
            duyet(fl.get_Geometry(opt))
        except Exception:
            continue
        for f in ds:
            z = f.Origin.Z
            if z > z_tren + ft(5) or (tot[1] is not None and z <= tot[1]):
                continue
            kq = f.Project(XYZ(q.X, q.Y, z))
            if kq is not None and kq.Distance < ft(1):
                tot = (f.Reference, z)
    return tot


def o_luoi(vung, k):
    trai, duoi, phai, tren = vung
    w, h = (phai - trai) / SO_COT, (tren - duoi) / SO_HANG
    hang, cot = k // SO_COT, k % SO_COT
    x0 = trai + cot * w
    y1 = tren - hang * h
    return x0, y1 - h, x0 + w, y1


def tang_so(s):
    m = re.search(u"(\\d+)(\\D*)$", s)
    if not m:
        return s + u"-1"
    n = m.group(1)
    return s[:m.start(1)] + str(int(n) + 1).zfill(len(n)) + m.group(2)


def khoa_so(s):
    return [int(t) if t.isdigit() else t for t in re.split(u"(\\d+)", s)]


# ---------------------------------------------------------------- template
def lay_template(doc, view, ten_tpl, tu_khoa, ti_le, an_cat, p, ghi):
    """Template tên ten_tpl (đã có thì dùng nguyên). Chưa có: tạo từ template nền rồi chỉnh. Trả về template / None."""
    tpls = [v for v in FilteredElementCollector(doc).OfClass(View) if v.IsTemplate]
    for t in tpls:
        if t.Name == ten_tpl:
            if view is not None and not view.IsValidViewTemplate(t.Id):
                p(u"   Template '%s' đã có nhưng không dùng được cho view này → bỏ qua." % ten_tpl)
                return None
            return t
    ung = [t for t in tpls if view is None or view.IsValidViewTemplate(t.Id)]
    tk = khong_dau(tu_khoa)

    def hang(t):
        n = khong_dau(t.Name)
        return (0 if tk and tk in n else 1, 0 if t.Scale == ti_le else 1, 0 if u"chi tiet" in n else 1, len(n))
    ung.sort(key=hang)
    nen = ung[0] if ung and (ung[0].Scale == ti_le or (tk and tk in khong_dau(ung[0].Name))) else None
    if not ghi:
        p(u"   Sẽ tạo template '%s' từ template nền '%s'." % (ten_tpl, nen.Name if nen is not None else u"(không có, theo view)"))
        return None
    view.ViewTemplateId = nen.Id if nen is not None else ElementId.InvalidElementId
    doc.Regenerate()            # template chỉ áp vào view khi regenerate
    tpl = view.CreateViewTemplate()
    tpl.Name = ten_tpl
    # Template phải điều khiển V/G model để ẩn được hạng mục; Far Clipping / Crop để view tự giữ
    try:
        bo = set([ElementId(BuiltInParameter.VIEWER_BOUND_FAR_CLIPPING).Value,
                  ElementId(BuiltInParameter.VIEWER_BOUND_OFFSET_FAR).Value,
                  ElementId(BuiltInParameter.VIEWER_CROP_REGION).Value,
                  ElementId(BuiltInParameter.VIEWER_CROP_REGION_VISIBLE).Value])
        vg = ElementId(BuiltInParameter.VIS_GRAPHICS_MODEL).Value
        ds = List[ElementId]()
        for i in tpl.GetNonControlledTemplateParameterIds():
            if i.Value != vg:
                ds.Add(i)
        co = set(i.Value for i in ds)
        for i in tpl.GetTemplateParameterIds():
            if i.Value in bo and i.Value not in co:
                ds.Add(i)
        tpl.SetNonControlledTemplateParameterIds(ds)
    except Exception as ex:
        p(u"   Không chỉnh được tham số điều khiển của template: %s" % ex)
    try:
        tpl.Scale = ti_le
    except Exception:
        pass
    try:
        tpl.DetailLevel = ViewDetailLevel.Fine
    except Exception:
        pass
    an = []
    for n in an_cat:
        try:
            c = ElementId(getattr(BuiltInCategory, n))
            if tpl.CanCategoryBeHidden(c):
                if not tpl.GetCategoryHidden(c):
                    tpl.SetCategoryHidden(c, True)
                an.append(ten_cat(doc, c))
        except Exception:
            pass
    for bic in (BuiltInCategory.OST_Doors, BuiltInCategory.OST_Windows, BuiltInCategory.OST_Walls):
        try:
            if tpl.GetCategoryHidden(ElementId(bic)):
                tpl.SetCategoryHidden(ElementId(bic), False)
        except Exception:
            pass
    p(u"   Tạo template '%s' từ '%s' (1:%d, Fine, ẩn: %s)." % (ten_tpl, nen.Name if nen is not None else u"view",
                                                             ti_le, u", ".join(an) or u"-"))
    return tpl


def an_ky_hieu(doc, view, ten_views):
    """Hide in View các ký hiệu view (section / callout) có tên trong ten_views. Trả về số đã ẩn."""
    ds = List[ElementId]()
    for e in FilteredElementCollector(doc, view.Id).OfCategory(BuiltInCategory.OST_Viewers).WhereElementIsNotElementType():
        n = ten(e)
        try:
            pn = e.get_Parameter(BuiltInParameter.VIEW_NAME)
            if pn is not None and pn.AsString():
                n = pn.AsString()
        except Exception:
            pass
        if n in ten_views and e.CanBeHidden(view):
            ds.Add(e.Id)
    if ds.Count:
        view.HideElements(ds)
    return ds.Count


def phan_tu_crop(doc, view):
    """Phần tử khung crop của view (để xoay mặt bằng): phần tử có ID_PARAM = id view (ngoài chính view đó). Revit
    2027.3: callout mặt bằng có crop id = id view - 1, hạng mục "Views" (KHÔNG phải OST_CropBoundary).
    Dự phòng: id view - 1 thuộc OST_CropBoundary, rồi tìm theo tên view."""
    cb = int(BuiltInCategory.OST_CropBoundary)
    try:
        luat = ParameterFilterRuleFactory.CreateEqualsRule(ElementId(BuiltInParameter.ID_PARAM), view.Id)
        for e in FilteredElementCollector(doc).WherePasses(ElementParameterFilter(luat)):
            if e.Id.Value != view.Id.Value and not e.GetType().Name.startswith(u"View"):
                return e
    except Exception:
        pass
    try:
        e = doc.GetElement(ElementId(view.Id.Value - 1))
        if e is not None and e.Category is not None and e.Category.Id.Value == cb:
            return e
    except Exception:
        pass
    for e in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CropBoundary).WhereElementIsNotElementType():
        try:
            pn = e.get_Parameter(BuiltInParameter.VIEW_NAME)
            if pn is not None and pn.AsString() == view.Name:
                return e
        except Exception:
            pass
    return None


def kieu_net_dut(doc):
    """Line style nét đứt cho nét cốt sàn: ưu tiên tên có 'khuất' / 'đứt', rồi '<Hidden>' / 'hidden' / 'dash'."""
    cat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Lines)
    tot = None
    for sc in cat.SubCategories:
        n = khong_dau(sc.Name)
        hang = 0 if (u"khuat" in n or u"net dut" in n) else 1 if n == u"<hidden>" else 2 if (u"hidden" in n or u"dash" in n) else 9
        if hang < 9 and (tot is None or hang < tot[0]):
            gs = sc.GetGraphicsStyle(GraphicsStyleType.Projection)
            if gs is not None:
                tot = (hang, gs)
    return tot[1] if tot else None


def chieu_cao_chu(doc, loai):
    """Chiều cao chữ (feet giấy) của TextNoteType."""
    try:
        return loai.get_Parameter(BuiltInParameter.TEXT_SIZE).AsDouble()
    except Exception:
        return ft(2.5)


def mat_hinh_cua(doc, fi):
    """Mặt phẳng trong hình family của cửa: [(pháp tuyến, tâm mặt, reference)] theo toạ độ dự án. Reference của hình
    symbol đổi sang reference của instance qua chuỗi ổn định '<UniqueId>:0:INSTANCE:<ref symbol>' để dim trên view
    (mặt đứng ẩn tường nên không dim vào mặt lỗ tường được)."""
    opt = Options()
    opt.ComputeReferences = True
    opt.DetailLevel = ViewDetailLevel.Fine
    ds = []

    def them(solid, tr, doi):
        if solid.GetType().Name != "Solid" or solid.Volume <= 0:
            return
        for f in solid.Faces:
            if f.GetType().Name != "PlanarFace" or f.Reference is None:
                continue
            r = f.Reference
            if doi:
                try:
                    r = Reference.ParseFromStableRepresentation(
                        doc, u"%s:0:INSTANCE:%s" % (fi.UniqueId, f.Reference.ConvertToStableRepresentation(doc)))
                except Exception:
                    continue
            ds.append((tr.OfVector(f.FaceNormal), tr.OfPoint(tam_mat(f)), r))
    try:
        for g in fi.get_Geometry(opt):
            if g.GetType().Name == "GeometryInstance":
                for s in g.GetSymbolGeometry():
                    them(s, g.Transform, True)
            else:
                them(g, Transform.Identity, False)
    except Exception:
        pass
    return ds


def mat_gan(mats, truc, muc, sai):
    """Reference mặt có pháp tuyến song song truc, vị trí (tâm · truc) gần muc nhất trong khoảng sai."""
    ung = [(abs(q.DotProduct(truc) - muc), r) for n, q, r in mats if abs(n.DotProduct(truc)) > 0.99
           and abs(q.DotProduct(truc) - muc) <= sai]
    return min(ung, key=lambda m: m[0])[1] if ung else None


def tao_dim(doc, view, p0, p1, refs):
    ra = ReferenceArray()
    for r in refs:
        ra.Append(r)
    return doc.Create.NewDimension(view, Line.CreateBound(p0, p1), ra)


# ---------------------------------------------------------------- chính
def _chinh():
    doc = DocumentManager.Instance.CurrentDBDocument
    uidoc = DocumentManager.Instance.CurrentUIDocument
    bao_cao = []

    def p(s):
        bao_cao.append(u"%s" % s)

    dry = bool(doc_in(14))
    ti_le = int(round(float(doc_in(4) or 25)))
    le = ft(float(doc_in(5) or 300))

    # ---------- Cửa ----------
    fi = None
    sid = (u"%s" % (doc_in(0) or u"")).strip()
    if sid:
        try:
            fi = doc.GetElement(ElementId(int(float(sid))))
        except Exception:
            return [u"ID cửa '%s' không hợp lệ." % sid]
    else:
        sel = list(uidoc.Selection.GetElementIds()) if uidoc is not None else []
        if sel:
            fi = doc.GetElement(sel[0])
        elif uidoc is not None:
            try:
                r = uidoc.Selection.PickObject(ObjectType.Element, u"Chọn cửa đi / cửa sổ cần triển khai chi tiết")
                fi = doc.GetElement(r.ElementId)
            except Exception:
                return [u"Đã huỷ chọn cửa."]
    if fi is None or fi.Category is None or fi.Category.Id.Value not in (int(BuiltInCategory.OST_Doors),
                                                                         int(BuiltInCategory.OST_Windows)):
        return [u"Đối tượng đã chọn không phải cửa đi / cửa sổ. Chọn 1 cửa rồi bấm lại."]
    sym = doc.GetElement(fi.GetTypeId())
    mk = u""
    for bip in (BuiltInParameter.WINDOW_TYPE_ID, BuiltInParameter.ALL_MODEL_TYPE_MARK):
        try:
            pm = sym.get_Parameter(bip)
            if pm is not None and pm.AsString():
                mk = pm.AsString().strip()
                break
        except Exception:
            pass
    ky_hieu = ten_view_hop_le(mk or ten(sym))
    la_cua_so = fi.Category.Id.Value == int(BuiltInCategory.OST_Windows)
    ten_v = {k: ten_view_hop_le(u"CT CỬA %s - %s" % (ky_hieu, t)) for k, t in
             (("mb", u"MẶT BẰNG"), ("md", u"MẶT ĐỨNG"), ("mc", u"MẶT CẮT"))}
    p(u"Cửa: id %d | %s : %s | Type Mark '%s'%s" % (fi.Id.Value, sym.FamilyName, ten(sym), mk or u"(trống → dùng tên type)",
                                                   u" – DRY-RUN, không sửa mô hình" if dry else u""))

    views = [v for v in FilteredElementCollector(doc).OfClass(View) if not v.IsTemplate]
    trung = [v for v in views if v.Name in ten_v.values()]
    if trung:
        p(u"Type này đã có chi tiết (view: %s) → không tạo thêm." % u", ".join(v.Name for v in trung))
        for vp in FilteredElementCollector(doc).OfClass(Viewport):
            if any(vp.ViewId.Value == v.Id.Value for v in trung):
                sh = doc.GetElement(vp.SheetId)
                p(u"Nằm trên sheet %s - %s." % (sh.SheetNumber, sh.Name))
                if bool(doc_in(15)) and not dry:
                    try:
                        uidoc.RequestViewChange(sh)
                    except Exception:
                        pass
                break
        return bao_cao

    # ---------- Khung toạ độ cửa ----------
    lv = doc.GetElement(fi.LevelId)
    if lv is None:
        return [u"Cửa không có level → không làm được."]
    P = fi.Location.Point
    H = XYZ(fi.HandOrientation.X, fi.HandOrientation.Y, 0).Normalize()
    N = UP.CrossProduct(H).Normalize()          # pháp tuyến tường (một trong hai phía)
    pts = []
    opt = Options()
    opt.DetailLevel = ViewDetailLevel.Fine
    diem_hinh(fi.get_Geometry(opt), pts)
    if not pts:
        bb = fi.get_BoundingBox(None)
        pts = [bb.Min, bb.Max, XYZ(bb.Min.X, bb.Max.Y, bb.Min.Z), XYZ(bb.Max.X, bb.Min.Y, bb.Max.Z)]
    hs = [(q - P).DotProduct(H) for q in pts]
    ss = [(q - P).DotProduct(N) for q in pts]
    zs = [q.Z for q in pts]
    hmin, hmax, zmin, zmax = min(hs), max(hs), min(zs), max(zs)
    rong = hmax - hmin
    hc = (hmin + hmax) / 2.0
    wall = fi.Host
    mats = []
    if wall is not None and wall.Category is not None and wall.Category.Id.Value == int(BuiltInCategory.OST_Walls):
        mats = mat_tuong(wall)
        sw = [(tam_mat(f) - P).DotProduct(N) for f in mats if abs(f.FaceNormal.DotProduct(N)) > 0.99]
        # 2 mặt tường gần tâm cửa nhất mỗi phía
        am = [s for s in sw if s <= 0]
        du = [s for s in sw if s >= 0]
        if am and du:
            ss += [max(am), min(du)]
    smin, smax = min(ss), max(ss)
    z_lv = lv.Elevation
    goc_mb = None
    av = doc.ActiveView
    if av is not None and av.ViewType == ViewType.FloorPlan and not av.IsTemplate and av.GenLevel is not None \
            and av.GenLevel.Id.Value == lv.Id.Value:
        goc_mb = av
    else:
        ung = [v for v in views if v.ViewType == ViewType.FloorPlan and v.GenLevel is not None
               and v.GenLevel.Id.Value == lv.Id.Value and not v.Name.startswith(u"CT CỬA")
               and v.GetPrimaryViewId().Value < 0]
        ung.sort(key=lambda v: (0 if v.Name == lv.Name else 1, 0 if v.Scale == 100 else 1,
                                0 if v.ViewTemplateId.Value > 0 else 1, v.Name))
        goc_mb = ung[0] if ung else None
    if goc_mb is None:
        return bao_cao + [u"Không có mặt bằng tầng '%s' để tạo callout." % lv.Name]
    p(u"   Kích thước theo hình family: rộng %.0f, cao %.0f (z %.0f → %.0f so với level %s), dày %.0f"
      % (mm(rong), mm(zmax - zmin), mm(zmin - z_lv), mm(zmax - z_lv), lv.Name, mm(smax - smin)))

    # ---------- Phía nhìn mặt đứng (ngoài nhà) ----------
    ep = u"%s" % (doc_in(11) or u"")
    ep = khong_dau(ep)
    F = XYZ(fi.FacingOrientation.X, fi.FacingOrientation.Y, 0).Normalize()
    S, ly_do = None, u""
    if ep == u"facing":
        S, ly_do = F, u"ép theo mặt ngoài family (Facing)"
    elif ep == u"nguoc":
        S, ly_do = F.Negate(), u"ép ngược Facing"
    else:
        z_do = zmin + ft(1000) if not la_cua_so else z_lv + ft(1000)
        rooms = []
        for dau in (1, -1):
            q = P + N * (dau * ((smax if dau > 0 else -smin) + ft(400)))
            try:
                rooms.append(doc.GetRoomAtPoint(XYZ(q.X, q.Y, z_do)))
            except Exception:
                rooms.append(None)
        ra, rb = rooms
        if (ra is None) != (rb is None):
            S = N if ra is None else N.Negate()
            ly_do = u"ngoài nhà = phía không có room (phía kia: %s)" % ten(rb if ra is None else ra)
        elif ra is not None and rb is not None:
            na = any(t in khong_dau(ten(ra)) for t in TEN_NGOAI)
            nb = any(t in khong_dau(ten(rb)) for t in TEN_NGOAI)
            if na != nb:
                S = N if na else N.Negate()
                ly_do = u"ngoài nhà = phía room '%s'" % ten(ra if na else rb)
        if S is None:
            arcs = []
            try:
                o2 = Options()
                o2.View = goc_mb
                cung_mo(fi.get_Geometry(o2), arcs)
            except Exception:
                arcs = []
            if arcs:
                tong = sum((a.Evaluate(0.5, True) - P).DotProduct(N) for a in arcs)
                if abs(tong) > ft(10):
                    S = N.Negate() if tong > 0 else N
                    ly_do = u"cửa trong nhà: nhìn từ phía không mở cánh"
        if S is None:
            S, ly_do = F, u"không xác định được ngoài nhà (room 2 phía: %s / %s) và không có cung mở → theo mặt ngoài " \
                          u"family (Facing)" % (ten(ra) if ra is not None else u"không có",
                                                ten(rb) if rb is not None else u"không có")
    if S.DotProduct(N) < 0:
        N = N.Negate()
        ss = [-s for s in ss]
        smin, smax = min(ss), max(ss)
    # từ đây N = S (phía người nhìn mặt đứng), smax = mép phía ngoài
    p(u"   Mặt đứng: %s." % ly_do)

    # ---------- Kế hoạch view ----------
    z_lo = min(zmin, z_lv) - le
    z_hi = zmax + le
    X_d = UP.CrossProduct(N)                     # phía phải của người đứng ngoài nhìn vào (= phía phải mặt bằng)
    goc_xoay = math.atan2(X_d.Y, X_d.X)          # xoay mặt bằng để phía phải trùng mặt đứng, ngoài nhà ở dưới
    p(u"   Mặt bằng: callout trên '%s', xoay %.1f° cho trùng chiều mặt đứng (ngoài nhà ở dưới)."
      % (goc_mb.Name, math.degrees(goc_xoay)))
    for k in ("mb", "md", "mc"):
        p(u"   %s '%s' tỉ lệ 1:%d" % (u"Sẽ tạo" if dry else u"Tạo", ten_v[k], ti_le))

    # ---------- Sheet ----------
    ten_sh = (doc_in(2) or MAC_DINH[2]).strip()
    sheets = [s for s in FilteredElementCollector(doc).OfClass(ViewSheet) if not s.IsPlaceholder and s.Name == ten_sh]
    cua_minh = []
    for s in sheets:
        for g in FilteredElementCollector(doc, s.Id).OfClass(Group):
            if ten(g.GroupType).startswith(NHOM_LUOI):
                cua_minh.append(s)
                break
    cua_minh.sort(key=lambda s: khoa_so(s.SheetNumber))
    tb_ten = (doc_in(1) or u"").strip()
    tbs = list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsElementType())
    tb_type = None
    for t in tbs:
        if ten(t) == tb_ten or (u"%s : %s" % (t.FamilyName, ten(t))) == tb_ten or t.FamilyName == tb_ten:
            tb_type = t
            break
    if tb_type is None and tbs:
        a1 = [t for t in tbs if u"a1" in khong_dau(t.FamilyName + ten(t))]
        tb_type = (a1 or tbs)[0]
        p(u"   Không có khung tên '%s' → dùng '%s'." % (tb_ten, tb_type.FamilyName))
    vp_all = list(FilteredElementCollector(doc).OfClass(Viewport))
    chon_sh, chon_o, vung = None, None, None
    for s in cua_minh:
        tb = list(FilteredElementCollector(doc, s.Id).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsNotElementType())
        if not tb:
            continue
        doc_net_khung(doc, doc.GetElement(tb[0].GetTypeId()), p)
        vg = vung_ve(doc, s, tb[0], p)
        tams = [vp.GetBoxCenter() for vp in vp_all if vp.SheetId.Value == s.Id.Value]
        for k in range(SO_COT * SO_HANG):
            x0, y0, x1, y1 = o_luoi(vg, k)
            if not any(x0 <= c.X <= x1 and y0 <= c.Y <= y1 for c in tams):
                chon_sh, chon_o, vung = s, k, vg
                break
        if chon_sh is not None:
            break
    so_moi = None
    if chon_sh is None:
        so = sorted([s.SheetNumber for s in sheets], key=khoa_so)
        so_moi = tang_so(so[-1]) if so else (doc_in(3) or MAC_DINH[3]).strip()
        co_so = set(s.SheetNumber for s in FilteredElementCollector(doc).OfClass(ViewSheet))
        while so_moi in co_so:
            so_moi = tang_so(so_moi)
        p(u"   %s sheet mới %s - %s (khung '%s'), ô 1/6." % (u"Sẽ tạo" if dry else u"Tạo", so_moi, ten_sh,
                                                         tb_type.FamilyName if tb_type is not None else u"không có"))
    else:
        p(u"   Đặt vào sheet %s - %s, ô %d/6." % (chon_sh.SheetNumber, chon_sh.Name, chon_o + 1))

    tk = tach(doc_in(9))
    tk += [u""] * (3 - len(tk))
    an_cat = tach(doc_in(10))
    if dry:
        co_tpl = set(t.Name for t in FilteredElementCollector(doc).OfClass(View) if t.IsTemplate)
        for j, i in enumerate((6, 7, 8)):
            ten_tpl = (doc_in(i) or u"").strip()
            if ten_tpl in co_tpl:
                p(u"   Template '%s' đã có → dùng nguyên." % ten_tpl)
            else:
                lay_template(doc, None, ten_tpl, tk[j], ti_le, an_cat, p, False)
        return bao_cao

    # ================================================================ GHI
    if chon_sh is None and tb_type is not None:
        doc_net_khung(doc, tb_type, p)
    TransactionManager.Instance.EnsureInTransaction(doc)
    ten_sec = None
    for t in FilteredElementCollector(doc).OfClass(ViewFamilyType):
        if t.ViewFamily == ViewFamily.Section:
            if ten_sec is None or (t.DefaultTemplateId.Value < 0 and ten_sec.DefaultTemplateId.Value >= 0):
                ten_sec = t
    tam = P + H * hc

    def hop(O, nhin, R, xlo, xhi, ylo, yhi, sau):
        """Hộp cho ViewSection.CreateSection. Thử trên Revit 2027.3: view nhìn theo +BasisZ (ViewDirection = -BasisZ),
        mặt cắt ở Min.Z, cắt xa ở Max.Z, RightDirection = -BasisX. nhin = hướng nhìn, R = phía phải trên view,
        [xlo, xhi] đo theo R, sau = chiều sâu nhìn tính từ mặt cắt (qua O)."""
        tr = Transform.Identity
        tr.Origin = O
        tr.BasisX = R.Negate()
        tr.BasisY = UP
        tr.BasisZ = nhin
        b = BoundingBoxXYZ()
        b.Transform = tr
        b.Min = XYZ(-xhi, ylo, 0)
        b.Max = XYZ(-xlo, yhi, sau)
        return b

    def khung(O, X):
        xs = [(q - O).DotProduct(X) for q in pts]
        return min(xs), max(xs)

    # Cốt sàn hoàn thiện (thay level, level ẩn trên mặt đứng / mặt cắt): mặt trên sàn trong nhà, không có thì ngoài nhà
    z_do_san = zmin + ft(5) if not la_cua_so else z_lv + ft(300)
    phia_san = -1
    z_s = mat_san(doc, P - N * (-smin + ft(150)), z_do_san)[1]
    if z_s is None:
        phia_san = 1
        z_s = mat_san(doc, P + N * (smax + ft(150)), z_do_san)[1]
    z_cot = z_s if z_s is not None else z_lv
    room_san = None
    try:
        q = P + N * (phia_san * ((smax if phia_san > 0 else -smin) + ft(400)))
        room_san = doc.GetRoomAtPoint(XYZ(q.X, q.Y, z_lv + ft(1000)))
    except Exception:
        pass
    chu_cot = u"CỐT SÀN HOÀN THIỆN" + (u" " + ten(room_san).upper() if room_san is not None else u"")
    loai_chu = doc.GetElement(doc.GetDefaultElementTypeId(ElementTypeGroup.TextNoteType))
    h_chu = chieu_cao_chu(doc, loai_chu) * ti_le                 # chiều cao chữ theo toạ độ model
    dai_chu = len(chu_cot) * h_chu * 0.75                         # ước lượng chiều dài chữ (Arial chữ hoa)

    # Mặt đứng: mặt cắt đặt trước mặt ngoài tường (không cắt cửa), nhìn vào tường từ phía ngoài nhà (N)
    O_d = XYZ(tam.X, tam.Y, zmin) + N * (smax + ft(200))
    a, b = khung(O_d, X_d)
    v_md = ViewSection.CreateSection(doc, ten_sec.Id,
                                     hop(O_d, N.Negate(), X_d, a - le, b + le, z_lo - zmin, z_hi - zmin,
                                         smax - smin + ft(400)))
    # Mặt cắt: cắt qua cánh, cách tâm 1/4 bề rộng về phía người nhìn; ngoài nhà (N) nằm bên phải
    X_c = N
    V_c = N.CrossProduct(UP)                     # phía người nhìn (UP × V_c = N)
    O_c = XYZ(tam.X, tam.Y, zmin) + V_c * (rong / 4.0)
    a2, b2 = khung(O_c, X_c)
    a2 = min(a2, smin)
    b2 = max(b2, smax)
    # chữ cốt sàn bên trái (trong nhà) như mẫu, nằm NGOÀI khung cắt (vùng annotation crop nới rộng) để không đè
    # tường / sàn phía trong: mũi tên chỉ xuống nét sàn, chữ bên phải mũi tên
    trai_mc = a2 - le
    x_mui = trai_mc - dai_chu - 2.5 * h_chu
    v_mc = ViewSection.CreateSection(doc, ten_sec.Id,
                                     hop(O_c, V_c.Negate(), X_c, trai_mc, b2 + le, z_lo - zmin, z_hi - zmin,
                                         rong * 0.75 + ft(50)))
    for nhan, v, vd, r in ((u"mặt đứng", v_md, N, X_d), (u"mặt cắt", v_mc, V_c, X_c)):
        if v.ViewDirection.DotProduct(vd) < 0.99 or v.RightDirection.DotProduct(r) < 0.99:
            p(u"   CẢNH BÁO: hướng %s khác dự kiến (ViewDirection %s, Right %s) – Revit đổi quy ước CreateSection?"
              % (nhan, v.ViewDirection, v.RightDirection))
    # Mặt bằng: callout chữ nhật rộng theo X, sâu theo Y quanh tâm cửa, rồi xoay khung crop để phía phải = X_d
    # (cùng chiều mặt đứng), phía ngoài nhà ở dưới
    C = P + H * hc + N * ((smin + smax) / 2.0)
    nw, nd = rong / 2.0 + le, (smax - smin) / 2.0 + le
    v_mb = ViewSection.CreateCallout(doc, goc_mb.Id, goc_mb.GetTypeId(),
                                     XYZ(C.X - nw, C.Y - nd, z_lv), XYZ(C.X + nw, C.Y + nd, z_lv))
    v_mb = doc.GetElement(v_mb.Id)
    if abs(goc_xoay) > 1e-4:
        crop = phan_tu_crop(doc, v_mb)
        try:
            if crop is None:
                raise Exception(u"không tìm thấy phần tử crop")
            ElementTransformUtils.RotateElement(doc, crop.Id, Line.CreateBound(XYZ(C.X, C.Y, z_lv), XYZ(C.X, C.Y, z_lv + 1)),
                                                goc_xoay)
            doc.Regenerate()
        except Exception as ex:
            p(u"   CẢNH BÁO: không xoay được mặt bằng (%s) → mặt bằng theo trục dự án." % ex)
    if v_mb.RightDirection.DotProduct(X_d) < 0.99:
        p(u"   CẢNH BÁO: mặt bằng chưa cùng chiều mặt đứng (Right %s, cần %s)." % (v_mb.RightDirection, X_d))
    tieu_de = {"mb": u"MẶT BẰNG", "md": u"MẶT ĐỨNG", "mc": u"MẶT CẮT"}
    vs = {"mb": v_mb, "md": v_md, "mc": v_mc}
    for k, v in vs.items():
        v.Name = ten_v[k]
        try:
            v.Scale = ti_le
        except Exception:
            pass
        try:
            v.get_Parameter(BuiltInParameter.VIEW_DESCRIPTION).Set(tieu_de[k])
        except Exception:
            pass
    for k, i in (("mb", 6), ("md", 7), ("mc", 8)):
        tpl = lay_template(doc, vs[k], (doc_in(i) or u"").strip(), tk[["mb", "md", "mc"].index(k)], ti_le, an_cat, p, True)
        if tpl is not None and vs[k].ViewTemplateId.Value != tpl.Id.Value:
            vs[k].ViewTemplateId = tpl.Id
    for k, v in vs.items():
        try:
            v.Scale = ti_le
        except Exception:
            pass
        try:
            v.CropBoxActive = True
            v.CropBoxVisible = False
        except Exception:
            pass
        try:            # cắt chú thích sát khung nhìn: đầu level / ký hiệu ngoài khung không làm to viewport
            v.get_Parameter(BuiltInParameter.VIEWER_ANNOTATION_CROP_ACTIVE).Set(1)
            sm = v.GetCropRegionShapeManager()
            for thuoc_tinh in ("LeftAnnotationCropOffset", "RightAnnotationCropOffset",
                               "TopAnnotationCropOffset", "BottomAnnotationCropOffset"):
                setattr(sm, thuoc_tinh, ft(3))
        except Exception:
            pass
    try:            # annotation crop trái của mặt cắt chứa chữ cốt sàn (offset đo trên giấy)
        v_mc.GetCropRegionShapeManager().LeftAnnotationCropOffset = (trai_mc - x_mui) / ti_le + ft(4)
    except Exception as ex:
        p(u"   Không nới được vùng chú thích trái của mặt cắt (%s) – chữ cốt sàn có thể bị cắt." % ex)
    for v in (v_md, v_mc):
        try:
            v.get_Parameter(BuiltInParameter.VIEWER_BOUND_FAR_CLIPPING).Set(2)     # cắt xa, không vẽ nét
        except Exception:
            pass
        try:
            v.get_Parameter(BuiltInParameter.SECTION_COARSER_SCALE_PULLDOWN_METRIC).Set(ti_le)
        except Exception:
            pass
    doc.Regenerate()
    so_an = an_ky_hieu(doc, v_md, [v_mc.Name, v_mb.Name]) + an_ky_hieu(doc, v_mc, [v_md.Name, v_mb.Name]) \
        + an_ky_hieu(doc, v_mb, [v_md.Name, v_mc.Name])
    if bool(doc_in(13)):
        so_an += an_ky_hieu(doc, goc_mb, [v_mb.Name])
    p(u"   Đã tạo 3 view (id %d, %d, %d); ẩn %d ký hiệu view không cần thấy." % (v_mb.Id.Value, v_md.Id.Value,
                                                                          v_mc.Id.Value, so_an))

    # ---------- Cốt sàn: nét đứt trên mặt đứng + mặt cắt, chữ "CỐT SÀN HOÀN THIỆN ..." có mũi tên trên mặt cắt ----------
    gs_dut = kieu_net_dut(doc)
    net_san = {}
    for k, v, O, X, x_a, x_b in (("md", v_md, O_d, X_d, a - le, b + le), ("mc", v_mc, O_c, X_c, x_mui - h_chu, b2 + le)):
        g0 = XYZ(O.X, O.Y, z_cot)
        net_san[k] = doc.Create.NewDetailCurve(v, Line.CreateBound(g0 + X * x_a, g0 + X * x_b))
        if gs_dut is not None:
            try:
                net_san[k].LineStyle = gs_dut
            except Exception:
                pass
    g0 = XYZ(O_c.X, O_c.Y, z_cot)
    tn = TextNote.Create(doc, v_mc.Id, g0 + X_c * (x_mui + h_chu) + UP * (2.2 * h_chu), chu_cot, loai_chu.Id)
    try:
        ld = tn.AddLeader(TextNoteLeaderTypes.TNLT_STRAIGHT_L)
        ld.End = g0 + X_c * x_mui
        ld.Elbow = g0 + X_c * x_mui + UP * (1.7 * h_chu)
    except Exception as ex:
        p(u"   Không thêm được mũi tên cho chữ cốt sàn (%s)." % ex)
    p(u"   Cốt sàn: %s %+.0f so với level, nét '%s', chữ '%s' (kiểu chữ '%s')." % (
        u"mặt sàn trong nhà" if z_s is not None and phia_san < 0 else u"mặt sàn ngoài nhà" if z_s is not None else u"level",
        mm(z_cot - z_lv), ten(gs_dut) if gs_dut is not None else u"mặc định", chu_cot, ten(loai_chu)))

    # ---------- Kích thước tổng ----------
    if bool(doc_in(12)):
        dim_kq = []
        r_trai, r_phai = ref_family(fi, "Left"), ref_family(fi, "Right")
        r_tren, r_duoi = ref_family(fi, "Top"), ref_family(fi, "Bottom")
        nguon_w = u"family"
        h_tr, h_ph = hmin, hmax
        if r_trai is None or r_phai is None:     # mép lỗ mở của tường
            nguon_w = u"mép lỗ tường"
            mep = [(abs((tam_mat(f) - P).DotProduct(H) - hmin), (tam_mat(f) - P).DotProduct(H), f) for f in mats
                   if abs(f.FaceNormal.DotProduct(H)) > 0.99 and smin - ft(5) <= (tam_mat(f) - P).DotProduct(N) <= smax + ft(5)]
            tr = [m for m in mep if abs(m[1] - hmin) < ft(150)]
            ph = [(abs(m[1] - hmax), m[1], m[2]) for m in mep if abs(m[1] - hmax) < ft(150)]
            r_trai = min(tr, key=lambda m: m[0])[2].Reference if tr else None
            r_phai = min(ph, key=lambda m: m[0])[2].Reference if ph else None
            h_tr = min(tr, key=lambda m: m[0])[1] if tr else hmin
            h_ph = min(ph, key=lambda m: m[0])[1] if ph else hmax
        nguon_h = u"family"
        z_dinh, z_bau = zmax, zmin
        if r_tren is None:
            dinh = [(abs(tam_mat(f).Z - zmax), f) for f in mats if f.FaceNormal.Z < -0.99
                    and abs(tam_mat(f).Z - zmax) < ft(150) and abs((tam_mat(f) - P).DotProduct(H) - hc) < rong]
            r_tren = min(dinh, key=lambda m: m[0])[1].Reference if dinh else None
            z_dinh = tam_mat(min(dinh, key=lambda m: m[0])[1]).Z if dinh else zmax
            nguon_h = u"đỉnh lỗ tường"
        if la_cua_so and r_duoi is None:
            bau = [(abs(tam_mat(f).Z - zmin), f) for f in mats if f.FaceNormal.Z > 0.99
                   and abs(tam_mat(f).Z - zmin) < ft(150) and abs((tam_mat(f) - P).DotProduct(H) - hc) < rong]
            r_duoi = min(bau, key=lambda m: m[0])[1].Reference if bau else None
            z_bau = tam_mat(min(bau, key=lambda m: m[0])[1]).Z if bau else zmin
        # mặt đứng ẩn tường → mép / đỉnh / bậu lấy trên hình cửa: mặt gần mép lỗ tường nhất (không có thì mép hình cửa)
        r_md = {"trai": r_trai, "phai": r_phai, "tren": r_tren, "duoi": r_duoi}
        if nguon_w != u"family" or nguon_h != u"family" or (la_cua_so and ref_family(fi, "Bottom") is None):
            mh = mat_hinh_cua(doc, fi)
            p0h = P.DotProduct(H)
            if nguon_w != u"family":
                r_md["trai"] = mat_gan(mh, H, p0h + h_tr, ft(60))
                r_md["phai"] = mat_gan(mh, H, p0h + h_ph, ft(60))
            if nguon_h != u"family":
                r_md["tren"] = mat_gan(mh, UP, z_dinh, ft(60))
            if la_cua_so and ref_family(fi, "Bottom") is None:
                r_md["duoi"] = mat_gan(mh, UP, z_bau, ft(60))
        # chân: nét cốt sàn của từng view (level ẩn, sàn ẩn trên mặt đứng)
        nguon_h += u", chân = nét cốt sàn"

        def chuoi_h(k):
            d, t = (r_md["duoi"], r_md["tren"]) if k == "md" else (r_duoi, r_tren)
            ds = [net_san[k].GeometryCurve.Reference, d, t] if la_cua_so else [net_san[k].GeometryCurve.Reference, t]
            return [r for r in ds if r is not None]

        def thu(nhan, view, p0, p1, refs):
            if len(refs) < 2:
                dim_kq.append(u"%s: thiếu reference" % nhan)
                return
            try:
                tao_dim(doc, view, p0, p1, refs)
                dim_kq.append(u"%s: OK" % nhan)
            except Exception as ex:
                dim_kq.append(u"%s: lỗi (%s)" % (nhan, u"%s" % ex))
        wr = [r for r in (r_trai, r_phai) if r is not None]
        # mặt bằng: dim rộng phía ngoài nhà
        q = P + N * (smax + le * 0.5)
        thu(u"MB rộng (%s)" % nguon_w, v_mb, XYZ(q.X, q.Y, z_lv) + H * (hmin - le), XYZ(q.X, q.Y, z_lv) + H * (hmax + le), wr)
        # mặt đứng: rộng phía trên cửa, cao bên phải
        q = O_d + UP * (zmax - zmin + le * 0.5)
        thu(u"MĐ rộng", v_md, q - X_d * (rong + le), q + X_d * (rong + le),
            [r for r in (r_md["trai"], r_md["phai"]) if r is not None])
        x_ph = max(a, b) + le * 0.5
        q = O_d + X_d * x_ph
        thu(u"MĐ cao (%s)" % nguon_h, v_md, XYZ(q.X, q.Y, z_lo), XYZ(q.X, q.Y, z_hi), chuoi_h("md"))
        q = O_c + X_c * (b2 + le * 0.5)
        thu(u"MC cao", v_mc, XYZ(q.X, q.Y, z_lo), XYZ(q.X, q.Y, z_hi), chuoi_h("mc"))
        p(u"   Kích thước: %s." % u"; ".join(dim_kq))

    # ---------- Ẩn level (mặt đứng, mặt cắt); mặt đứng chỉ còn cửa: Hide in View mọi phần tử model khác ----------
    giu = set([fi.Id.Value])
    try:
        giu.update(i.Value for i in fi.GetSubComponentIds())
    except Exception:
        pass
    try:
        if fi.SuperComponent is not None:
            giu.add(fi.SuperComponent.Id.Value)
    except Exception:
        pass
    lv_cat = int(BuiltInCategory.OST_Levels)
    # mốc khác (mặt phẳng tham chiếu, scope box, lưới trục) ẩn ở cả 3 view: chúng kéo viewport to ra, vượt ô
    moc = set(int(b) for b in (BuiltInCategory.OST_CLines, BuiltInCategory.OST_VolumeOfInterest, BuiltInCategory.OST_Grids))
    for v in (v_mb, v_md, v_mc):
        ds = List[ElementId]()
        for e in FilteredElementCollector(doc, v.Id).WhereElementIsNotElementType():
            try:
                if e.Category is not None and e.Category.Id.Value in moc and e.CanBeHidden(v):
                    ds.Add(e.Id)
            except Exception:
                pass
        if ds.Count:
            v.HideElements(ds)
            p(u"   %s: ẩn %d mặt phẳng tham chiếu / scope box / lưới trục." % (v.Name, ds.Count))
    for v, chi_cua in ((v_md, True), (v_mc, False)):
        ds = List[ElementId]()
        so_lv = 0
        for e in FilteredElementCollector(doc, v.Id).WhereElementIsNotElementType():
            c = e.Category
            if c is None or e.Id.Value in giu or e.ViewSpecific:      # nét cốt sàn, dim, chữ của view: giữ
                continue
            la_lv = c.Id.Value == lv_cat
            if not la_lv and not (chi_cua and c.CategoryType == CategoryType.Model):
                continue
            try:
                if e.CanBeHidden(v):
                    ds.Add(e.Id)
                    so_lv += 1 if la_lv else 0
            except Exception:
                pass
        if ds.Count:
            v.HideElements(ds)
        p(u"   %s: ẩn %d level%s." % (u"Mặt đứng" if chi_cua else u"Mặt cắt", so_lv,
                                    u" + %d phần tử khác (chỉ giữ cửa)" % (ds.Count - so_lv) if chi_cua else u""))
    doc.Regenerate()
    so_dim = {v.Name: sum(1 for _ in FilteredElementCollector(doc, v.Id).OfClass(Dimension)) for v in (v_mb, v_md, v_mc)}
    p(u"   Kích thước còn trong view sau khi ẩn: %s." % u", ".join(u"%s %d" % (k, n) for k, n in so_dim.items()))

    # ---------- Sheet + đặt view ----------
    if chon_sh is None:
        if tb_type is None:
            TransactionManager.Instance.TransactionTaskDone()
            return bao_cao + [u"Dự án không có khung tên nào → đã tạo view, chưa đặt lên sheet."]
        if not tb_type.IsActive:
            tb_type.Activate()
        chon_sh = ViewSheet.Create(doc, tb_type.Id)
        chon_sh.SheetNumber = so_moi
        chon_sh.Name = ten_sh
        doc.Regenerate()
        tb = list(FilteredElementCollector(doc, chon_sh.Id).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsNotElementType())[0]
        vung = vung_ve(doc, chon_sh, tb, p)
        chon_o = 0
        trai, duoi, phai, tren = vung
        nets = []
        for c in range(1, SO_COT):
            x = trai + (phai - trai) * c / SO_COT
            nets.append((XYZ(x, duoi, 0), XYZ(x, tren, 0)))
        for r in range(1, SO_HANG):
            y = duoi + (tren - duoi) * r / SO_HANG
            nets.append((XYZ(trai, y, 0), XYZ(phai, y, 0)))
        for k in range(SO_COT * SO_HANG):
            x0, y0, x1, y1 = o_luoi(vung, k)
            y = y0 + (y1 - y0) * TI_LE_DAI_TT
            nets.append((XYZ(x0, y, 0), XYZ(x1, y, 0)))
        ids = List[ElementId]()
        for a0, a1 in nets:
            ids.Add(doc.Create.NewDetailCurve(chon_sh, Line.CreateBound(a0, a1)).Id)
        g = doc.Create.NewGroup(ids)
        try:
            g.GroupType.Name = u"%s %s" % (NHOM_LUOI, so_moi)
        except Exception:
            pass
        p(u"   Sheet %s: vùng vẽ %.0f × %.0f mm, lưới 6 ô (group '%s %s')." % (
            so_moi, mm(phai - trai), mm(tren - duoi), NHOM_LUOI, so_moi))
    x0, y0, x1, y1 = o_luoi(vung, chon_o)
    y0v = y0 + (y1 - y0) * TI_LE_DAI_TT          # vùng đặt view (trên dải thông tin)
    cx, cy = (x0 + x1) / 2.0, (y0v + y1) / 2.0
    vps = {}
    for k in ("md", "mc", "mb"):
        if not Viewport.CanAddViewToSheet(doc, chon_sh.Id, vs[k].Id):
            p(u"   Không đặt được view '%s' lên sheet." % vs[k].Name)
            continue
        vps[k] = Viewport.Create(doc, chon_sh.Id, vs[k].Id, XYZ(cx, cy, 0))
    doc.Regenerate()

    def kt(vp):
        o = vp.GetBoxOutline()
        return o.MaximumPoint.X - o.MinimumPoint.X, o.MaximumPoint.Y - o.MinimumPoint.Y

    if len(vps) == 3:
        gap, gap_td = ft(12), ft(16)            # khoảng hở giữa view / chỗ tên view dưới mỗi view
        (wd, hd), (wc, hc2), (wb, hb) = kt(vps["md"]), kt(vps["mc"]), kt(vps["mb"])
        cot_a = max(wd, wb)
        tong_w = cot_a + gap + wc
        tong_h = hd + gap_td + hb + gap_td
        xl = x0 + max((x1 - x0 - tong_w) / 2.0, ft(5))
        yt = y1 - max((y1 - y0v - tong_h) / 2.0, ft(5))
        vps["md"].SetBoxCenter(XYZ(xl + cot_a / 2.0, yt - hd / 2.0, 0))
        vps["mc"].SetBoxCenter(XYZ(xl + cot_a + gap + wc / 2.0, yt - hc2 / 2.0, 0))
        vps["mb"].SetBoxCenter(XYZ(xl + cot_a / 2.0, yt - hd - gap_td - hb / 2.0, 0))
        doc.Regenerate()
        # Gióng: sàn mặt cắt ngang sàn mặt đứng; tâm cửa mặt bằng thẳng tâm cửa mặt đứng
        try:
            def len_sheet(vp, view, q):
                tr = list(view.GetModelToProjectionTransforms())[0].GetModelToProjectionTransform()
                return vp.GetProjectionToSheetTransform().OfPoint(tr.OfPoint(q))
            yd = len_sheet(vps["md"], v_md, XYZ(tam.X, tam.Y, z_lv)).Y
            yc = len_sheet(vps["mc"], v_mc, XYZ(tam.X, tam.Y, z_lv)).Y
            vps["mc"].SetBoxCenter(vps["mc"].GetBoxCenter() + XYZ(0, yd - yc, 0))
            if abs(X_d.DotProduct(v_mb.RightDirection)) > 0.99:
                xd = len_sheet(vps["md"], v_md, tam).X
                xb = len_sheet(vps["mb"], v_mb, tam).X
                vps["mb"].SetBoxCenter(vps["mb"].GetBoxCenter() + XYZ(xd - xb, 0, 0))
        except Exception as ex:
            p(u"   Không gióng được view theo sàn / tâm cửa (%s)." % ex)
        doc.Regenerate()
        vuot = tong_w > x1 - x0 or tong_h > y1 - y0v
        p(u"   Đặt 3 view vào ô %d: cụm %.0f × %.0f mm, vùng đặt view %.0f × %.0f mm%s." % (
            chon_o + 1, mm(tong_w), mm(tong_h), mm(x1 - x0), mm(y1 - y0v), u" – VƯỢT Ô, cần xếp lại tay" if vuot else u""))
    TransactionManager.Instance.TransactionTaskDone()
    p(u"Xong: sheet %s - %s, ô %d. Phần trống dưới ô để điền ký hiệu, kích thước, vật liệu, phụ kiện." % (
        chon_sh.SheetNumber, chon_sh.Name, chon_o + 1))
    if bool(doc_in(15)):
        try:
            uidoc.RequestViewChange(chon_sh)
        except Exception:
            pass
    return bao_cao


try:
    OUT = _chinh()
except Exception:
    OUT = [u"LỖI:", traceback.format_exc()]
