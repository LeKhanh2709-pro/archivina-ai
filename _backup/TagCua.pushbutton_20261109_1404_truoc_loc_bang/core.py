# Tự động tag cửa đi + cửa sổ trên mặt bằng đang mở của Revit (người dùng chốt 2026-11-02, sửa theo góp ý cùng ngày):
#   - Cửa đi: family tag "AV_Door Tag"; cửa sổ: "AV_Window Tag"; cửa sổ có tên family / type chứa từ khoá lam:
#     "AV_Louver Tag". Đối tượng có Type Comments "Louver" hoặc "Cửa nhôm" thì KHÔNG tag (người dùng chốt 2026-11-09).
#   - Tag hiện đúng Type Mark: nhãn family có tiền tố (vd. "S3.") thì thay bằng nhãn Type Mark trơn chép từ family tag
#     cùng hạng mục trong dự án (Revit 2027.3 không sửa được tiền tố nhãn qua API), rồi nạp lại family.
#   - Tag nằm ngang, ưu tiên NGAY GIỮA cửa (cửa đi phía không mở cánh, cửa sổ phía ngoài theo FacingOrientation);
#     KHÔNG đè cửa (kể cả cánh mở), cửa sổ, tường, cột, tag / chữ khác. Lưới vị trí quanh cửa xếp theo điểm = lùi xa
#     + 4 × dịch khỏi giữa cửa + phạt phía kia; không chỗ nào trống thì đặt chỗ ít đè nhất và liệt kê để xem lại.
#   - Leader: tag lệch khỏi giữa cửa (hoặc xa hơn 1 bề cao tag) thì bật leader gắn vào cửa.
#   - Nội thất không né mà ẩn: tạo view template riêng "<template gốc> (ẩn nội thất)" (tạo từ view vì API không nhân
#     bản được view template), ẩn các hạng mục nội thất, gán cho view. KHÔNG sửa template gốc.
#   - Cửa có EI (tham số chống cháy có giá trị) thì EI phải hiện trên tag: tag đã đặt mà chữ tag không chứa giá trị EI
#     → báo family tag chưa có nhãn EI.
#   - Cửa / cửa sổ đã có tag trong view thì bỏ qua: bấm lại không tạo trùng. Chỉ khi bật IN[14] mới dời tag đã có
#     (cùng family tag); chỉ khi bật IN[15] mới xoá tag đang gắn trên đối tượng Type Comments "Louver".
# Dry-run chỉ báo cáo (đặt thử trong SubTransaction rồi huỷ), không sửa mô hình.
#   - Mặt bằng định vị cửa (gộp từ nút "MB định vị cửa" theo yêu cầu người dùng 2026-11-03): view gốc đã là mặt bằng định
#     vị cửa (mang template IN[17] hoặc tên theo mẫu IN[18]) thì tag luôn; không thì nhân bản view gốc (Duplicate, không
#     kèm chú thích) thành "MẶT BẰNG ĐỊNH VỊ CỬA - <tầng>" (đã có thì dùng view đó), gán template IN[17] rồi tag trên đó.
#     Template chưa có thì tạo từ template của view gốc: tường + sàn Halftone, sàn tắt mẫu tô, cửa đi / cửa sổ bỏ Halftone,
#     ẩn các hạng mục IN[7], hiện tag cửa. Template đã có thì dùng nguyên. Không sửa view gốc / template gốc.
# INPUT
#   IN[0] (str)   Tên view mặt bằng (để trống = view đang mở)
#   IN[1] (str)   Family tag cửa đi
#   IN[2] (str)   Family tag cửa sổ
#   IN[3] (str)   Family tag lam / louver
#   IN[4] (str)   Từ khoá nhận lam / louver trong tên family / type cửa sổ, cách nhau bằng ;
#   IN[5] (bool)  Dry-run (True = chỉ báo cáo)
#   IN[6] (bool)  Tạo + gán view template ẩn nội thất
#   IN[7] (str)   Hạng mục nội thất cần ẩn (tên BuiltInCategory), cách nhau bằng ;
#   IN[8] (str)   Tên tham số chống cháy (EI) của cửa, cách nhau bằng ;
#   IN[9] (float) Khoảng hở giữa tag và vật cản (mm trên giấy in)
#   IN[10] (str)  Thư mục ghi log + ảnh (để trống = Documents\ARV_Logs\tag_cua)
#   IN[11] (str)  Type Comments của đối tượng KHÔNG tag (vd. Louver), cách nhau bằng ;
#   IN[12] (bool) Bỏ tiền tố nhãn Type Mark trong family tag (vd. "S3.") để tag hiện đúng Type Mark
#   IN[13] (bool) Luôn bật leader (False = chỉ bật khi tag không nằm ngay giữa cửa)
#   IN[14] (bool) Đặt lại vị trí các tag cửa / cửa sổ đã có (cùng family tag) theo quy tắc mới
#   IN[15] (bool) Xoá tag đang gắn trên đối tượng bị loại trừ theo Type Comments
#   IN[16] (bool) Tạo / mở mặt bằng định vị cửa rồi tag trên đó (False = tag ngay trên view IN[0])
#   IN[17] (str)  Tên view template mặt bằng định vị cửa
#   IN[18] (str)  Mẫu tên mặt bằng định vị cửa ({tang} = tên tầng, {view} = tên view gốc)
#   IN[19] (bool) Thêm ô dưới "rộngXcao" (mm) vào family tag cửa đi / cửa sổ, khung chữ nhật 2 ô (như mẫu CAD, người dùng
#                 duyệt 2026-11-03); nhãn Width / Height mm chép từ lib\tag_cua\ARV_TagNguon_Door / _Window.rfa
#   IN[20] (str)  Thư mục family .rfa nguồn nhãn Width / Height mm (trống = <extension>\lib\tag_cua khi chạy nút)
#   IN[21] (bool) Đặt mặt bằng lên sheet (người dùng yêu cầu 2026-11-03; nút pyRevit hỏi trong hộp thoại trước khi chạy)
#   IN[22] (str)  Giai đoạn (giá trị thư mục cấp 1 của Project Browser, vd. 03_TKBVTC)
#   IN[23] (str)  Hạng mục (thư mục cấp 2, vd. 01_MatBang; chưa có thì tạo mới bằng cách gán giá trị mới)
#   IN[24] (str)  Khổ giấy (A1 / A0) – tìm family khung tên có chữ đó, tự chọn tỉ lệ vừa khổ
#   IN[25] (str)  Khung tên "Family : Type" (trống = tự tìm theo khổ)
#   IN[26] (str)  Số hiệu sheet (trống = tiếp theo trong hạng mục)
#   IN[27] (str)  Tên sheet (trống = "MẶT BẰNG ĐỊNH VỊ CỬA <TẦNG>")
#   IN[28] (str)  View template gán cho mặt bằng định vị cửa (trống = template tên IN[17] nếu có, không thì giữ template
#                 view gốc; "<Không dùng view template>" = bỏ template). 2026-11-05: KHÔNG tạo / sửa view template nữa
#   IN[29] (float) Tỉ lệ mặt bằng, mẫu số (0 = tự chọn như cũ 1:100; template khoá tỉ lệ thì theo template)
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
# pythonnet 3.0: tên đã được import đích danh trước đó trong phiên bị loại khỏi "import *" → bổ sung đủ tên
globals().update({_n: getattr(_RevitDB, _n) for _n in dir(_RevitDB) if not _n.startswith("_") and _n not in globals()})
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

MAC_DINH = ["", "AV_Door Tag", "AV_Window Tag", "AV_Louver Tag", "Lam;Louver", True, True,
            "OST_Furniture;OST_FurnitureSystems;OST_Casework;OST_SpecialityEquipment;OST_PlumbingFixtures",
            "Fire Rating;EI;Giới hạn chịu lửa", 1.0, "", u"Louver;Cửa nhôm", True, False, False, False,
            True, u"MẶT BẰNG ĐỊNH VỊ CỬA", u"MẶT BẰNG ĐỊNH VỊ CỬA - {tang}", True, "",
            False, "", "", "A1", "", "", "", "", 0.0]
HAU_TO_TEMPLATE = u" (ẩn nội thất)"
MB_HALFTONE = ("OST_Floors",)                      # mặt bằng định vị cửa: sàn xám như ảnh mẫu người dùng
MB_DAM = ("OST_Doors", "OST_Windows")              # cửa nét đậm để định vị
MB_AN_THEM = ("OST_MechanicalEquipment", "OST_Elev", "OST_Sections")   # người dùng chốt 2026-11-03: ẩn cả thiết bị cơ
#                                                    điện, ký hiệu mặt đứng, mặt cắt
TEN_FILTER_TRUC_LINK = u"ARV_Ẩn trục file link"       # filter Grids: loại trục khác loại trục của file hiện tại → ẩn
# Tường / cột / vách như mẫu FPT (người dùng chốt 2026-11-03 tối): tường xây chỉ nét xám, không tô; cột + vách BTCT tô đặc
# xám đậm viền đen. Vách BTCT = tường có Structural Usage khác Non-bearing (link kết cấu) hoặc tên loại chứa một từ khoá
# dưới (lọc không phân biệt hoa thường; WS_ = tường kết cấu theo cách đặt tên của model G19).
TEN_FILTER_BTCT = u"ARV_Vách BTCT"
TEN_FILTER_XAY = u"ARV_Tường xây"
TEN_FILTER_COT = u"ARV_Cột BTCT"
TU_KHOA_BTCT = (u"BTCT", u"VBT", u"WS_", u"Concrete", u"Bê tông")
MAU_TO_BTCT = (100, 100, 100)
COT_BTCT = ("OST_StructuralColumns", "OST_Columns")
PHAT_PHIA_MM_GIAY = 8.0     # phạt khi đặt tag ở phía không ưu tiên (mm trên giấy, cộng vào khoảng cách)
HE_SO_LECH = 4.0            # mỗi mm dịch dọc tường khỏi giữa cửa tính bằng 4 mm lùi xa: ưu tiên tag ngay giữa cửa
TAM_XA_MM_GIAY = 8.0        # tag đặt xa nhất cách mép tường / cánh cửa (mm trên giấy) – gần cửa (người dùng 2026-11-03)


def doc_in(i):
    try:
        v = IN[i]
    except Exception:
        v = None
    return MAC_DINH[i] if v is None or (isinstance(v, str) and v == "" and MAC_DINH[i] != "") else v


def khong_dau(s):
    s = unicodedata.normalize("NFD", u"%s" % (s or u"")).replace(u"đ", u"d").replace(u"Đ", u"D")
    return u"".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def tach(s):
    return [x.strip() for x in (s or "").split(";") if x.strip()]


def ds_loai_tru(s):
    """Type Comments không tag = danh sách IN[11] + 2 loại luôn loại trừ (máy còn nhớ IN[11] cũ "Louver" vẫn bỏ cửa nhôm)."""
    ds = tach(s)
    co = [khong_dau(x) for x in ds]
    return ds + [x for x in (u"Louver", u"Cửa nhôm") if khong_dau(x) not in co]


def mm(v):
    return UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.Millimeters)


def ft(v):
    return UnitUtils.ConvertToInternalUnits(v, UnitTypeId.Millimeters)


def ten(e):
    try:
        return Element.Name.GetValue(e)
    except Exception:
        try:
            return e.Name
        except Exception:
            return "?"


# ---------------- Hình học 2D trong hệ toạ độ view (u = phải, v = lên) ----------------
def da_giac_giao(a, b):
    """Hai đa giác lồi (list (x, y)) có phần trong giao nhau không (định lý trục tách)."""
    for poly in (a, b):
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            nx, ny = y1 - y2, x2 - x1
            pa = [nx * x + ny * y for x, y in a]
            pb = [nx * x + ny * y for x, y in b]
            if max(pa) <= min(pb) + 1e-9 or max(pb) <= min(pa) + 1e-9:
                return False
    return True


def dien_tich_giao_hop(a, b):
    """Diện tích giao xấp xỉ theo khung bao (để chọn chỗ ít đè nhất)."""
    ax = [p[0] for p in a]
    ay = [p[1] for p in a]
    bx = [p[0] for p in b]
    by = [p[1] for p in b]
    w = min(max(ax), max(bx)) - max(min(ax), min(bx))
    h = min(max(ay), max(by)) - max(min(ay), min(by))
    return w * h if w > 0 and h > 0 else 0.0


def _chinh():
    doc = DocumentManager.Instance.CurrentDBDocument
    bao_cao = []
    xem_lai = []
    chi_tiet = []

    def p(s):
        bao_cao.append(u"%s" % s)

    # ---------- View ----------
    ten_view = doc_in(0)
    view = None
    if ten_view:
        # Trùng tên (vd. "Tầng 1" có cả mặt bằng kiến trúc, trần, kết cấu) → ưu tiên Floor Plan
        ung = [v for v in FilteredElementCollector(doc).OfClass(ViewPlan) if not v.IsTemplate and v.Name == ten_view]
        ung.sort(key=lambda v: 0 if v.ViewType == ViewType.FloorPlan else 1)
        av = doc.ActiveView        # nút một chạm truyền tên view đang mở → lấy đúng view đó
        if av is not None and any(v.Id.Value == av.Id.Value for v in ung):
            ung = [av]
        view = ung[0] if ung else None
        if view is None:
            return [u"Không có view mặt bằng tên '%s'." % ten_view]
    else:
        view = doc.ActiveView
    if view is None or view.ViewType not in (ViewType.FloorPlan, ViewType.EngineeringPlan, ViewType.AreaPlan):
        return [u"View '%s' không phải mặt bằng. Mở mặt bằng cần tag rồi chạy lại." % (ten(view) if view else "-")]
    dry = bool(doc_in(5))
    if doc_in(16):
        view, mb_msg = mb_dinh_vi_cua(doc, view, dry, doc_in(17), doc_in(18), tach(doc_in(7)), doc_in(28),
                                      doc_in(29))
        for s_ in mb_msg:
            p(s_)
    # Đặt lên sheet: tạo sheet + bảng thống kê + chọn tỉ lệ TRƯỚC khi tag (cỡ tag theo tỉ lệ); viewport đặt sau khi tag
    sheet_ctx = None
    if doc_in(21):
        if dry:
            p(u"Sẽ đặt mặt bằng lên sheet khổ %s (giai đoạn '%s', hạng mục '%s')." % (doc_in(24), doc_in(22), doc_in(23)))
        else:
            try:
                sheet_ctx, sh_msg = chuan_bi_sheet(doc, view, doc_in(22), doc_in(23), doc_in(24), doc_in(25), doc_in(26),
                                                   doc_in(27), ds_loai_tru(doc_in(11)))
            except Exception as ex:
                TransactionManager.Instance.ForceCloseTransaction()
                sh_msg = [u"Không đặt được lên sheet: %s" % (u"%s" % ex).splitlines()[0][:200]]
            for s_ in sh_msg:
                p(s_)
    tl = float(view.Scale)
    U = view.RightDirection
    V = view.UpDirection
    khe = ft(float(doc_in(9)) * tl)

    def uv(pt):
        return (pt.X * U.X + pt.Y * U.Y + pt.Z * U.Z, pt.X * V.X + pt.Y * V.Y + pt.Z * V.Z)

    def xyz(a, b, z):
        return XYZ(a * U.X + b * V.X, a * U.Y + b * V.Y, z)

    def khung_hop(bb):
        """BoundingBoxXYZ → hình chữ nhật trong hệ uv (khung bao các góc)."""
        if bb is None:
            return None
        tf = bb.Transform
        pts = [uv(tf.OfPoint(XYZ(x, y, bb.Min.Z))) for x in (bb.Min.X, bb.Max.X) for y in (bb.Min.Y, bb.Max.Y)]
        xs = [q[0] for q in pts]
        ys = [q[1] for q in pts]
        return [(min(xs), min(ys)), (max(xs), min(ys)), (max(xs), max(ys)), (min(xs), max(ys))]

    def diem_hinh_hoc(e):
        """Các điểm hình học của đối tượng hiện trong view (gồm nét 2D của family: cánh mở, ký hiệu)."""
        opt = Options()
        opt.View = view
        opt.IncludeNonVisibleObjects = False
        pts = []

        def duyet(geo):
            for g in geo:
                tn = g.GetType().Name
                if tn == "GeometryInstance":
                    duyet(g.GetInstanceGeometry())
                elif tn == "Solid":
                    if g.Volume <= 0 and g.Edges.Size == 0:
                        continue
                    for ed in g.Edges:
                        pts.extend(ed.Tessellate())
                elif tn in ("Line", "Arc", "Ellipse", "NurbSpline", "HermiteSpline", "CylindricalHelix"):
                    pts.extend(g.Tessellate())
                elif tn == "PolyLine":
                    pts.extend(g.GetCoordinates())
        try:
            geo = e.get_Geometry(opt)
            if geo is not None:
                duyet(geo)
        except Exception:
            pass
        return pts

    def hcn_cuc_bo(pts, goc, h, f):
        """Hình chữ nhật bao các điểm theo hệ (h, f) đặt tại goc; trả về (đa giác uv, h0, h1, f0, f1)."""
        if not pts:
            return None
        hs = [(q.X - goc.X) * h.X + (q.Y - goc.Y) * h.Y for q in pts]
        fs = [(q.X - goc.X) * f.X + (q.Y - goc.Y) * f.Y for q in pts]
        h0, h1, f0, f1 = min(hs), max(hs), min(fs), max(fs)
        poly = [uv(goc + h * a + f * b) for a, b in ((h0, f0), (h1, f0), (h1, f1), (h0, f1))]
        return poly, h0, h1, f0, f1

    # ---------- Kiểu tag ----------
    def tim_kieu_tag(ten_fam, bic):
        for s in FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(bic):
            if s.FamilyName == ten_fam:
                return s
        return None

    def nap_tag_dong_goi(ten_fam, bic):
        """Dự án chưa có family tag (vd. model HQV tháp B, người dùng báo 2026-11-05) → nạp bản đóng gói
        <extension>\\lib\\tag_cua\\<tên>.rfa (chép từ G19). Ngoài transaction của phần ghi."""
        duong = os.path.join(thu_muc_nhan(), ten_fam + u".rfa") if ten_fam else u""
        if not duong or not os.path.isfile(duong):
            return None, u"không thấy file đóng gói '%s'" % (duong or u"-")
        if dry:
            return None, u"sẽ nạp từ %s" % duong
        TransactionManager.Instance.EnsureInTransaction(doc)
        try:
            doc.LoadFamily(duong, tuy_chon_nap())
        except Exception as ex:
            return None, u"không nạp được %s: %s" % (duong, (u"%s" % ex).splitlines()[0][:200])
        finally:
            TransactionManager.Instance.TransactionTaskDone()
        s = tim_kieu_tag(ten_fam, bic)
        return s, (u"đã nạp từ %s" % duong) if s is not None else u"nạp xong mà không thấy kiểu tag"

    kieu_cua = tim_kieu_tag(doc_in(1), BuiltInCategory.OST_DoorTags)
    kieu_cs = tim_kieu_tag(doc_in(2), BuiltInCategory.OST_WindowTags)
    for i_in, bic in ((1, BuiltInCategory.OST_DoorTags), (2, BuiltInCategory.OST_WindowTags)):
        if tim_kieu_tag(doc_in(i_in), bic) is None:
            s_, msg_ = nap_tag_dong_goi(doc_in(i_in), bic)
            p(u"Family tag '%s': %s." % (doc_in(i_in), msg_))
            if i_in == 1:
                kieu_cua = s_
            else:
                kieu_cs = s_
    kieu_lam = tim_kieu_tag(doc_in(3), BuiltInCategory.OST_WindowTags) or kieu_cs
    tk_lam = [khong_dau(x) for x in tach(doc_in(4))]
    for ten_fam, k in ((doc_in(1), kieu_cua), (doc_in(2), kieu_cs)):
        if k is None and not dry:
            p(u"CHƯA CÓ family tag '%s' trong dự án → bỏ qua hạng mục này (Load family rồi chạy lại)." % ten_fam)

    # ---------- Đối tượng cần tag ----------
    def thay(bic):
        return list(FilteredElementCollector(doc, view.Id).OfCategory(bic).WhereElementIsNotElementType())

    cuas = thay(BuiltInCategory.OST_Doors)
    css = thay(BuiltInCategory.OST_Windows)
    # Tag có sẵn trong view theo đối tượng được tag
    tag_co = {}           # id đối tượng → [tag]
    for tg in FilteredElementCollector(doc, view.Id).OfClass(IndependentTag):
        try:
            for i in tg.GetTaggedLocalElementIds():
                tag_co.setdefault(i.Value, []).append(tg)
        except Exception:
            pass
    ten_fam_tag = set(x for x in (doc_in(1), doc_in(2), doc_in(3)) if x)

    def fam_cua_tag(tg):
        try:
            return doc.GetElement(tg.GetTypeId()).FamilyName
        except Exception:
            return u""

    # Loại trừ theo Type Comments (vd. Louver): không tag; tag cửa / cửa sổ đang gắn trên đó thì liệt kê (xoá nếu IN[15])
    ten_loai = u";".join(ds_loai_tru(doc_in(11)))
    tk_loai = [khong_dau(x) for x in tach(ten_loai)]

    def bi_loai(e):
        t = doc.GetElement(e.GetTypeId())
        if t is None or not tk_loai:
            return False
        try:
            tc = khong_dau(t.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_COMMENTS).AsString() or u"")
        except Exception:
            tc = u""
        return any(k in tc for k in tk_loai)

    loai_tru = [e for e in cuas + css if bi_loai(e)]
    id_loai = set(e.Id.Value for e in loai_tru)
    tag_tren_loai = [tg for e in loai_tru for tg in tag_co.get(e.Id.Value, [])
                     if tg.Category is not None and tg.Category.Id.Value in (int(BuiltInCategory.OST_DoorTags),
                                                                              int(BuiltInCategory.OST_WindowTags))]
    vat_can = []          # (đa giác uv, mô tả)
    bo_vat_can = set()    # mô tả vật cản không còn tính (tag đã dời / đã xoá)
    for tg in tag_tren_loai:
        if doc_in(15) and not dry:
            bo_vat_can.add(u"chữ / tag %d" % tg.Id.Value)
    # Chữ / tag có sẵn trong view
    for cls in (IndependentTag, TextNote, SpatialElementTag):
        try:
            for e in FilteredElementCollector(doc, view.Id).OfClass(cls):
                k = khung_hop(e.get_BoundingBox(view))
                if k:
                    vat_can.append((k, u"chữ / tag %d" % e.Id.Value))
        except Exception:
            pass
    # Tường: hình chữ nhật dấu chân thật (theo hình học, đúng cả khi location line lệch tâm)
    so_tuong = 0
    diem_tuong = {}
    for w in FilteredElementCollector(doc, view.Id).OfClass(Wall):
        lc = w.Location
        cv = lc.Curve if lc is not None and hasattr(lc, "Curve") else None
        poly = None
        if cv is not None and cv.GetType().Name == "Line":
            d = cv.Direction
            h = XYZ(d.X, d.Y, 0).Normalize()
            f = XYZ(-h.Y, h.X, 0)
            pts_w = diem_hinh_hoc(w)
            diem_tuong[w.Id.Value] = pts_w
            r = hcn_cuc_bo(pts_w, cv.GetEndPoint(0), h, f)
            poly = r[0] if r else None
        if poly is None:
            poly = khung_hop(w.get_BoundingBox(view))
        if poly:
            vat_can.append((poly, u"tường %d" % w.Id.Value))
            so_tuong += 1
    for bic in (BuiltInCategory.OST_Columns, BuiltInCategory.OST_StructuralColumns):
        for e in thay(bic):
            k = khung_hop(e.get_BoundingBox(view))
            if k:
                vat_can.append((k, u"cột %d" % e.Id.Value))
    # Cửa đi / cửa sổ: dấu chân theo hệ của cửa (gồm cánh mở)
    dau_chan = {}
    for e in cuas + css:
        try:
            goc = e.Location.Point
            h = e.HandOrientation
            f = e.FacingOrientation
        except Exception:
            k = khung_hop(e.get_BoundingBox(view))
            if k:
                vat_can.append((k, u"cửa %d" % e.Id.Value))
            continue
        r = hcn_cuc_bo(diem_hinh_hoc(e), goc, h, f)
        if r is None:
            continue
        dau_chan[e.Id.Value] = (goc, h, f) + r
        vat_can.append((r[0], u"cửa %d" % e.Id.Value))

    _bb_cache = []

    def vat_can_bb():
        while len(_bb_cache) < len(vat_can):
            pl, mt = vat_can[len(_bb_cache)]
            xs = [q[0] for q in pl]
            ys = [q[1] for q in pl]
            _bb_cache.append((pl, mt, (min(xs), min(ys), max(xs), max(ys))))
        return _bb_cache

    # Vùng crop của view
    crop = None
    if view.CropBoxActive:
        crop = khung_hop(view.CropBox)

    # ---------- Bỏ tiền tố nhãn Type Mark trong family tag (sửa family, nạp lại; ngoài transaction) ----------
    tien_to_msg = u""
    if doc_in(12):
        fams = []
        for s in (kieu_cua, kieu_cs, kieu_lam):
            if s is not None and s.Family.Id.Value not in [f_.Id.Value for f_ in fams]:
                fams.append(s.Family)
        tien_to_msg = bo_tien_to(doc, fams, dry)
        # family vừa nạp lại → lấy lại kiểu tag
        kieu_cua = tim_kieu_tag(doc_in(1), BuiltInCategory.OST_DoorTags)
        kieu_cs = tim_kieu_tag(doc_in(2), BuiltInCategory.OST_WindowTags)
        kieu_lam = tim_kieu_tag(doc_in(3), BuiltInCategory.OST_WindowTags) or kieu_cs
    # ---------- Dòng 2 "rộng x cao" trong family tag cửa đi / cửa sổ (sửa family, nạp lại; ngoài transaction) ----------
    if doc_in(19):
        fams = [s.Family for s in (kieu_cua, kieu_cs) if s is not None]
        kt_msg = them_kich_thuoc(doc, fams, dry, thu_muc_nhan())
        if kt_msg:
            tien_to_msg = (tien_to_msg + u" | " if tien_to_msg else u"") + kt_msg
        kieu_cua = tim_kieu_tag(doc_in(1), BuiltInCategory.OST_DoorTags)
        kieu_cs = tim_kieu_tag(doc_in(2), BuiltInCategory.OST_WindowTags)
        kieu_lam = tim_kieu_tag(doc_in(3), BuiltInCategory.OST_WindowTags) or kieu_cs

    # ---------- Ghi ----------
    TransactionManager.Instance.EnsureInTransaction(doc)
    st = SubTransaction(doc)
    st.Start()
    tao = {"cua": 0, "cs": 0, "lam": 0}
    bo_qua = 0
    dat_lai = 0
    so_leader = 0
    tag_moi = []
    ei_thieu = []
    tpl_msg = u""
    xoa_msg = u""
    co_lap = []           # có phần tử = đang cô lập tạm do công cụ bật

    def bat_co_lap():
        """IndependentTag.Create xử lý lại mọi đối tượng đang hiện trong view, kể cả tag vừa tạo (đo 2026-11-09 trên HQV
        tháp B: để nguyên 1,2 s / tag, cô lập cửa + hạng mục tag 0,59 s, chỉ cô lập cửa đi + cửa sổ 0,017 s) → cô lập tạm
        trong lúc tạo tag, KHÔNG gồm hạng mục tag. Người dùng đang tự cô lập trong view thì không đụng."""
        if co_lap or view.IsInTemporaryViewMode(TemporaryViewMode.TemporaryHideIsolate):
            return
        from System.Collections.Generic import List
        ids = List[ElementId]()
        for bic in (BuiltInCategory.OST_Doors, BuiltInCategory.OST_Windows):
            ids.Add(ElementId(bic))
        view.IsolateCategoriesTemporary(ids)
        co_lap.append(True)

    def tat_co_lap():
        if co_lap:
            del co_lap[:]
            view.DisableTemporaryViewMode(TemporaryViewMode.TemporaryHideIsolate)

    try:
        # --- View template ẩn nội thất ---
        if doc_in(6):
            tpl_msg = gan_template(doc, view, [x for x in tach(doc_in(7))])
        for s in (kieu_cua, kieu_cs, kieu_lam):
            if s is not None and not s.IsActive:
                s.Activate()
        # --- Tag trên đối tượng bị loại trừ (Type Comments) ---
        if tag_tren_loai:
            ds_ten = u", ".join(u"%d" % tg.Id.Value for tg in tag_tren_loai[:40])
            if doc_in(15):
                from System.Collections.Generic import List
                ids = List[ElementId]()
                for tg in tag_tren_loai:
                    ids.Add(tg.Id)
                doc.Delete(ids)
                xoa_msg = u"Đã xoá %d tag trên đối tượng có Type Comments '%s': %s" % (len(tag_tren_loai), ten_loai, ds_ten)
            else:
                xoa_msg = (u"Có %d tag đang gắn trên đối tượng có Type Comments '%s' (chưa xoá; Shift+bấm, tích ô Xoá "
                           u"để xoá): %s" % (len(tag_tren_loai), ten_loai, ds_ten))

        # Tăng tốc (người dùng báo nút chậm 2026-11-09; HQV tháp B 195 tag mất 475 s ở bước tạo tag + Regenerate): tạo / đưa
        # hết tag về điểm đặt cửa trước, Regenerate MỘT lần, đo khung từng tag rồi mới tìm chỗ. Khung tag tại điểm đặt
        # không phụ thuộc tag khác nên chỗ đặt như cũ.
        viec = []
        ds = [(e, "cua") for e in cuas] + [(e, "cs") for e in css]
        for e, loai in ds:
            if e.Id.Value in id_loai:
                continue
            tg_cu = None
            co = tag_co.get(e.Id.Value, [])
            if co:
                cung_fam = [x for x in co if fam_cua_tag(x) in ten_fam_tag]
                if doc_in(14) and cung_fam:
                    tg_cu = cung_fam[0]          # đặt lại tag đã có (không xoá, không tạo mới)
                else:
                    bo_qua += 1
                    continue
            kieu = kieu_cua
            if loai == "cs":
                t = doc.GetElement(e.GetTypeId())
                ten_ft = khong_dau((t.FamilyName if t else "") + " " + ten(t))
                if any(k in ten_ft for k in tk_lam):
                    loai, kieu = "lam", kieu_lam
                else:
                    kieu = kieu_cs
            if kieu is None:
                continue
            dc = dau_chan.get(e.Id.Value)
            if dc is None:
                xem_lai.append(u"%d (Mark %s): không đọc được hình học / vị trí → chưa tag" % (e.Id.Value, mark(e)))
                continue
            goc, h, f, poly_e, h0, h1, f0, f1 = dc
            # Tag xoay theo phương tường như mẫu người dùng (2026-11-03): tường dọc trên view → tag đứng
            hu_, hv_ = uv(h)
            huong = TagOrientation.Vertical if abs(hv_) > abs(hu_) else TagOrientation.Horizontal
            if tg_cu is None:
                bat_co_lap()
                tg = IndependentTag.Create(doc, kieu.Id, view.Id, Reference(e), False, huong, goc)
            else:
                tg = tg_cu
                tg.HasLeader = False
                tg.TagOrientation = huong
                tg.TagHeadPosition = goc
            viec.append((e, loai, tg, tg_cu, dc))
        tat_co_lap()
        if viec:
            doc.Regenerate()
        viec = [x + (khung_hop(x[2].get_BoundingBox(view)),) for x in viec]    # đo hết TRƯỚC khi dời tag nào
        for e, loai, tg, tg_cu, dc, k in viec:
            goc, h, f, poly_e, h0, h1, f0, f1 = dc
            if tg_cu is None:
                nhan_cu = None
            else:
                nhan_cu = u"chữ / tag %d" % tg.Id.Value
                bo_vat_can.add(nhan_cu)       # tag cũ thôi là vật cản khi tới lượt nó
            hu, hv = uv(goc)
            cu = (k[0][0] + k[2][0]) / 2.0 - hu       # lệch tâm khung so với đầu tag
            cv_ = (k[0][1] + k[2][1]) / 2.0 - hv
            a = (k[2][0] - k[0][0]) / 2.0              # nửa rộng, nửa cao khung tag (hệ uv)
            b = (k[2][1] - k[0][1]) / 2.0
            h2 = uv(h)
            f2 = uv(f)
            e_f = a * abs(f2[0]) + b * abs(f2[1])      # nửa bề dày tag chiếu lên phương vuông tường
            e_h = a * abs(h2[0]) + b * abs(h2[1])      # nửa bề dài tag chiếu lên phương dọc tường
            # Mặt tường host hai phía, đo theo hình học thật (điểm đặt cửa có thể không nằm giữa tường)
            mat_tuong = {1: 0.0, -1: 0.0}
            try:
                pts_w = diem_tuong.get(e.Host.Id.Value)
                if pts_w:
                    fs = [(q.X - goc.X) * f.X + (q.Y - goc.Y) * f.Y for q in pts_w]
                    mat_tuong = {1: max(max(fs), 0.0), -1: max(-min(fs), 0.0)}
                else:
                    mat_tuong = {1: e.Host.Width / 2.0, -1: e.Host.Width / 2.0}
            except Exception:
                pass
            # Phía ưu tiên: cửa đi = phía không mở cánh (phía dấu chân ngắn hơn); cửa sổ = phía ngoài (+Facing).
            # Ứng viên = lưới vị trí quanh cửa ở cả hai phía. Điểm = lùi xa khỏi tường + HE_SO_LECH × dịch khỏi giữa cửa
            # + phạt phía không ưu tiên → ưu tiên tag nằm ngay giữa cửa (người dùng chốt 2026-11-02). Thử lần lượt, lấy
            # chỗ trống đầu tiên. Vùng cánh mở bị loại vì dấu chân cửa là vật cản.
            if loai == "cua":
                uu_tien = -1 if f1 >= -f0 else 1
            else:
                uu_tien = 1
            phat = ft(PHAT_PHIA_MM_GIAY * tl)
            buoc_h = max(e_h * 0.5, ft(50))
            buoc_f = max(e_f * 0.5, ft(50))
            tam_h = (h0 + h1) / 2.0
            gioi_han_h = (h1 - h0) / 2.0 + e_h * 2.0
            # Gần cửa, KHÔNG đè hình (người dùng 2026-11-03 tối: "để gần cửa tránh vào hình"; bỏ cách đặt tag trên ô cửa):
            # (1) sát mặt tường phía ưu tiên, ngay giữa cửa; (2) sát mặt tường phía kia; rồi lưới gần (dịch dọc tường ≤ 2
            # bề dài tag, lùi ≤ TAM_XA_MM_GIAY) xếp theo độ gần. Hết chỗ trống thì lấy chỗ đè ít nhất NGAY GẦN cửa.
            dau_tien = []
            for s_ in (uu_tien, -uu_tien):
                dau_tien.append((0.0, goc + h * tam_h + f * (s_ * (mat_tuong[s_] + khe + e_f)),
                                 u"sát tường phía %s" % (u"ưu tiên" if s_ == uu_tien else u"kia"), True, False))
            ung_vien = []
            for s_ in (1, -1):
                d0 = mat_tuong[s_] + khe + e_f
                d_max = max(f1 if s_ > 0 else -f0, mat_tuong[s_]) + khe + e_f + ft(TAM_XA_MM_GIAY * tl)
                i = 0
                while d0 + i * buoc_f <= d_max:
                    d = d0 + i * buoc_f
                    j = -int(gioi_han_h / buoc_h)
                    while j * buoc_h <= gioi_han_h:
                        dh = j * buoc_h
                        diem = (d - d0) + abs(dh) * HE_SO_LECH + (0.0 if s_ == uu_tien else phat)
                        # còn kề cửa (trong bề rộng cửa, cách mặt tường ≤ 1 bề cao tag) → không cần leader
                        sat_giua = (abs(dh) <= (h1 - h0) / 2.0 + 1e-9 and d - d0 <= 2 * e_f + 1e-9)
                        ung_vien.append((diem, goc + h * (tam_h + dh) + f * (s_ * d),
                                         u"phía %s cách tường %d dịch %d" % (u"ưu tiên" if s_ == uu_tien else u"kia",
                                                                            round(mm(d - d0)), round(mm(dh))),
                                         sat_giua, False))
                        j += 1
                    i += 1
            ung_vien.sort(key=lambda x: x[0])
            ung_vien = dau_tien + ung_vien
            # Vật cản ở gần (lọc trước theo khung bao cho nhanh)
            r_gan = gioi_han_h + ft(TAM_XA_MM_GIAY * tl) + max(f1, -f0) + 2 * (e_f + e_h)
            gu, gv = uv(goc)
            gan = [(pl, mt, bb) for pl, mt, bb in vat_can_bb()
                   if mt not in bo_vat_can and mt != nhan_cu
                   and bb[0] <= gu + r_gan and bb[2] >= gu - r_gan and bb[1] <= gv + r_gan and bb[3] >= gv - r_gan]
            tot = None
            loai_bo = []          # lý do bỏ các ứng viên trước chỗ được chọn (ghi log để soát)
            for _, c, nhan, sat_giua, chi_tag in ung_vien:
                cu0, cv0 = uv(c)
                hop = [(cu0 - a - khe, cv0 - b - khe), (cu0 + a + khe, cv0 - b - khe),
                       (cu0 + a + khe, cv0 + b + khe), (cu0 - a - khe, cv0 + b + khe)]
                if crop and not (hop[0][0] >= crop[0][0] and hop[0][1] >= crop[0][1] and
                                 hop[2][0] <= crop[2][0] and hop[2][1] <= crop[2][1]):
                    loai_bo.append(u"%s: ngoài crop" % nhan)
                    continue
                de = [(pl, mt) for pl, mt, bb in gan
                      if (not chi_tag or mt.startswith(u"chữ / tag") or mt.startswith(u"tag mới"))
                      and bb[0] < hop[2][0] and bb[2] > hop[0][0] and bb[1] < hop[2][1] and bb[3] > hop[0][1]
                      and da_giac_giao(hop, pl)]
                if de:
                    loai_bo.append(u"%s: đè %s" % (nhan, ", ".join(sorted(set(m for _, m in de))[:3])))
                dt = sum(dien_tich_giao_hop(hop, pl) for pl, mt in de)
                if tot is None or dt < tot[1] - 1e-9:
                    tot = (c, dt, hop, de, nhan, sat_giua)
                if not de:
                    break
            if tot is None:
                c, de, hop, nhan, sat_giua = goc, [("", u"ngoài vùng crop")], None, u"-", False
            else:
                c, _, hop, de, nhan, sat_giua = tot
            chi_tiet.append(u"%d Mark %s %s: %s (%d ứng viên)%s" % (e.Id.Value, mark(e), loai, nhan, len(ung_vien),
                                                                   u" – đặt lại tag cũ" if tg_cu is not None else u""))
            chi_tiet.extend(u"      bỏ " + x for x in [x for x in loai_bo if not x.endswith(u"ngoài crop")][:12])
            cu0, cv0 = uv(c)
            dau = xyz(cu0 - cu, cv0 - cv_, goc.Z)
            tg.TagHeadPosition = dau
            # Leader: tag không nằm ngay giữa cửa (hoặc IN[13] luôn bật) → leader gắn vào cửa
            if doc_in(13) or not sat_giua:
                tg.HasLeader = True
                try:
                    tg.LeaderEndCondition = LeaderEndCondition.Attached
                except Exception:
                    pass
                tg.TagHeadPosition = dau
                so_leader += 1
            if hop:
                vat_can.append(([(hop[0][0] + khe, hop[0][1] + khe), (hop[1][0] - khe, hop[1][1] + khe),
                                 (hop[2][0] - khe, hop[2][1] - khe), (hop[3][0] + khe, hop[3][1] - khe)],
                                u"tag mới %d" % e.Id.Value))
            if tg_cu is None:
                tao[loai] += 1
            else:
                dat_lai += 1
            tag_moi.append(tg)
            if de:
                xem_lai.append(u"%d (Mark %s, %s): tag còn đè %s" % (e.Id.Value, mark(e), loai,
                                                                     ", ".join(sorted(set(m for _, m in de))[:4])))
            # EI
            if loai == "cua":
                ei = gia_tri_ei(doc, e, tach(doc_in(8)))
                if ei:
                    txt = u""         # chữ tag đã có sau lần Regenerate chung (dời tag / leader không đổi chữ)
                    try:
                        txt = tg.TagText or u""
                    except Exception:
                        pass
                    if khong_dau(ei).replace(" ", "") not in khong_dau(txt).replace(" ", ""):
                        ei_thieu.append(u"%d (Mark %s, %s): chữ tag '%s'" % (e.Id.Value, mark(e), ei, txt.strip()))
        if dry:
            st.RollBack()
        else:
            st.Commit()
    except Exception:
        try:
            tat_co_lap()
        except Exception:
            pass
        if st.HasStarted() and not st.HasEnded():
            st.RollBack()
        raise
    finally:
        TransactionManager.Instance.TransactionTaskDone()
    if sheet_ctx is not None:
        try:
            for s_ in dat_viewport(doc, sheet_ctx, view):
                p(s_)
        except Exception as ex:
            TransactionManager.Instance.ForceCloseTransaction()
            p(u"Không đặt được viewport lên sheet: %s" % (u"%s" % ex).splitlines()[0][:200])

    p(u"View: %s (1:%d)%s" % (view.Name, view.Scale, u" – DRY-RUN, chưa ghi gì" if dry else u""))
    p(u"Đã tag: %d cửa đi, %d cửa sổ, %d lam / louver; đặt lại %d tag cũ; %d tag có leader; bỏ qua %d đối tượng "
      u"đã có tag; không tag %d đối tượng có Type Comments '%s'" %
      (tao["cua"], tao["cs"], tao["lam"], dat_lai, so_leader, bo_qua, len(loai_tru), ten_loai))
    if tien_to_msg:
        p(tien_to_msg)
    if xoa_msg:
        p(xoa_msg)
    p(u"Vật cản đã xét: %d (tường %d)" % (len(vat_can), so_tuong))
    if tpl_msg:
        p(tpl_msg)
    if xem_lai:
        p(u"CẦN XEM LẠI (%d):" % len(xem_lai))
        for s in xem_lai:
            p(u"   " + s)
    else:
        p(u"Không tag nào đè lên cửa / tường / chữ.")
    if ei_thieu:
        p(u"CỬA CÓ EI NHƯNG TAG KHÔNG HIỆN EI (%d) – family tag cửa chưa có nhãn tham số chống cháy:" % len(ei_thieu))
        for s in ei_thieu:
            p(u"   " + s)
    if dry:
        p(u"DRY-RUN: chưa tạo gì. Đặt IN[5] = False để tag.")

    # Log + ảnh
    thu_muc = doc_in(10) or os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs", "tag_cua")
    try:
        os.makedirs(thu_muc, exist_ok=True)
        f_log = os.path.join(thu_muc, "tag_cua_%s_%d.txt" % (datetime.now().strftime("%Y%m%d_%H%M%S_%f"), view.Id.Value))
        with open(f_log, "w", encoding="utf-8") as fh:
            fh.write("\n".join(bao_cao + [u"", u"CHI TIẾT VỊ TRÍ:"] + chi_tiet))
        p(u"Log: " + f_log)
    except Exception as ex:
        p(u"Không ghi được log: %s" % ex)
    return bao_cao


def mark(e):
    try:
        return e.get_Parameter(BuiltInParameter.ALL_MODEL_MARK).AsString() or "-"
    except Exception:
        return "-"


def gia_tri_ei(doc, e, ten_ts):
    """Giá trị chống cháy của cửa (instance trước, rồi type); rỗng nếu không có."""
    t = doc.GetElement(e.GetTypeId())
    for el in (e, t):
        if el is None:
            continue
        for n in ten_ts:
            try:
                pr = el.LookupParameter(n)
                if pr is None:
                    continue
                v = pr.AsString() if pr.StorageType == StorageType.String else pr.AsValueString()
                if v and v.strip() and v.strip() not in ("0", "-"):
                    return v.strip()
            except Exception:
                pass
    return u""


def bo_tien_to(doc, fams, dry):
    """Cho tag hiện đúng Type Mark, bỏ tiền tố (vd. "S3.") trong nhãn các family tag (người dùng chốt 2026-11-02).
    Revit 2027.3 đọc được định dạng nhãn (AnnotationLabel.GetParameterFormatting) nhưng KHÔNG sửa được: Prefix gán vào
    không ăn, SetParameterFormatting / AnnotationLabel.Create chưa công khai. Nên thay nhãn: chép một nhãn "Type Mark
    trơn" (1 tham số Type Mark, không tiền tố / hậu tố) từ family tag khác đang có trong dự án (vd. AV-Tag-DOOR,
    AV_Door Tag_Full) vào family cần sửa, đặt đúng vị trí / bề rộng / căn lề / kiểu chữ của nhãn cũ, xoá nhãn cũ, nạp
    lại family. Không có nhãn nguồn thì báo sửa tay. Gọi NGOÀI transaction của dự án."""
    lop_nhan = getattr(_RevitDB, "AnnotationLabel", None)
    if lop_nhan is None:
        return u"Revit bản này chưa có API đọc nhãn: mở family tag, Edit Label, xoá tiền tố của Type Mark rồi nạp lại."

    def la_type_mark(fm, fd):
        try:
            dn = fm.GetParameterDefinition(fd)
            return dn is not None and int(dn.BuiltInParameter) == int(BuiltInParameter.ALL_MODEL_TYPE_MARK)
        except Exception:
            return False

    def nhan_tien_to(fd):
        """[(nhãn, tiền tố)] các nhãn có Type Mark kèm tiền tố"""
        kq = []
        for lb in FilteredElementCollector(fd).OfClass(lop_nhan):
            tt = [fm.Prefix for fm in lb.GetParameterFormatting() if la_type_mark(fm, fd) and fm.Prefix]
            if tt:
                kq.append((lb, tt[0]))
        return kq

    def nhan_tron(fd):
        for lb in FilteredElementCollector(fd).OfClass(lop_nhan):
            fmts = list(lb.GetParameterFormatting())
            if len(fmts) == 1 and la_type_mark(fmts[0], fd) and not fmts[0].Prefix and not fmts[0].Suffix:
                return lb
        return None

    ket_qua = []
    nguon = {}            # id hạng mục → (family doc nguồn, nhãn nguồn, tên family): chép nhãn trong cùng hạng mục
    da_mo = []
    ten_bo = set(f_.Name for f_ in fams)
    id_da = int(BuiltInCategory.OST_MultiCategoryTags)

    def tim_nguon(cat_id):
        if cat_id in nguon:
            return nguon[cat_id]
        nguon[cat_id] = None
        for f2 in FilteredElementCollector(doc).OfClass(Family):
            if f2.Name in ten_bo or f2.FamilyCategory is None or f2.FamilyCategory.Id.Value != cat_id                     or not f2.IsEditable:
                continue
            fd2 = doc.EditFamily(f2)
            da_mo.append(fd2)
            lb2 = nhan_tron(fd2)
            if lb2 is not None:
                nguon[cat_id] = (fd2, lb2, f2.Name)
                break
        return nguon[cat_id]

    TransactionManager.Instance.ForceCloseTransaction()
    try:
        for fam in fams:
            ten_f = fam.Name
            cat_id = fam.FamilyCategory.Id.Value if fam.FamilyCategory is not None else None
            try:
                if not fam.IsEditable:
                    ket_qua.append(u"'%s' không sửa được" % ten_f)
                    continue
                fd = doc.EditFamily(fam)
                da_mo.append(fd)
                can_sua = nhan_tien_to(fd)
                if not can_sua:
                    continue
                ds_tt = u", ".join(sorted(set(tt for _, tt in can_sua)))
                ng = tim_nguon(cat_id)
                if ng is None:
                    ng = tim_nguon(id_da)
                if ng is None:
                    ket_qua.append(u"'%s': còn tiền tố '%s' – không có family tag cùng hạng mục nào trong dự án có nhãn "
                                   u"Type Mark trơn để chép; sửa tay: Edit Family → chọn nhãn → Edit Label → xoá Prefix "
                                   u"→ Load" % (ten_f, ds_tt))
                    continue
                if dry:
                    ket_qua.append(u"'%s': sẽ bỏ tiền tố '%s' (thay nhãn chép từ '%s')" % (ten_f, ds_tt, ng[2]))
                    continue
                from System.Collections.Generic import List
                t = Transaction(fd, u"Bỏ tiền tố Type Mark")
                t.Start()
                try:
                    for lb, tt in can_sua:
                        ids = List[ElementId]()
                        ids.Add(ng[1].Id)
                        # nhãn là đối tượng theo view → chép view sang view (view nhãn nguồn → view nhãn cũ)
                        moi = list(ElementTransformUtils.CopyElements(ng[0].GetElement(ng[1].OwnerViewId), ids,
                                                                      fd.GetElement(lb.OwnerViewId), Transform.Identity,
                                                                      tuy_chon_dan()))
                        nm = [x for x in FilteredElementCollector(fd).OfClass(lop_nhan)
                              if any(x.Id.Value == i.Value for i in moi)][0]
                        nm.ChangeTypeId(lb.GetTypeId())
                        nm.HorizontalAlignment = lb.HorizontalAlignment
                        nm.VerticalAlignment = lb.VerticalAlignment
                        nm.Width = lb.Width
                        nm.Coord = lb.Coord
                        fd.Delete(lb.Id)
                    t.Commit()
                except Exception:
                    if t.HasStarted() and not t.HasEnded():
                        t.RollBack()
                    raise
                if nhan_tien_to(fd):
                    ket_qua.append(u"'%s': thay nhãn xong mà vẫn còn tiền tố – không nạp lại" % ten_f)
                    continue
                fd.LoadFamily(doc, tuy_chon_nap())
                ket_qua.append(u"'%s': đã bỏ tiền tố '%s' (thay nhãn chép từ '%s')" % (ten_f, ds_tt, ng[2]))
            except Exception as ex:
                ket_qua.append(u"'%s': không bỏ được tiền tố (%s) – sửa tay: Edit Family → Edit Label → xoá Prefix"
                               % (ten_f, (u"%s" % ex).splitlines()[0][:150] if u"%s" % ex else u"?"))
    finally:
        for fd in da_mo:
            try:
                fd.Close(False)
            except Exception:
                pass
    if not ket_qua:
        return u""
    return u"Nhãn Type Mark của family tag: " + u"; ".join(ket_qua)


BIP_RONG = ("GENERIC_WIDTH", "FAMILY_WIDTH_PARAM", "DOOR_WIDTH", "WINDOW_WIDTH", "FAMILY_ROUGH_WIDTH_PARAM")
BIP_CAO = ("DOOR_HEIGHT", "WINDOW_HEIGHT", "GENERIC_HEIGHT", "FAMILY_HEIGHT_PARAM", "FAMILY_ROUGH_HEIGHT_PARAM")
KHUNG_RONG_MM = 14.0        # khung tag 2 ô (mm giấy) – gọn như tag mẫu FPT (người dùng 2026-11-03), vừa "2160X2400"
KHUNG_O_MM = 3.5            # cao mỗi ô (mm giấy)
CO_CHU_MM = 2.0             # cỡ chữ nhãn tag (mm giấy)
KHE_X_MM = 0.8              # nửa bề rộng chữ "X" giữa Width và Height (mm giấy)


def dat_co_chu(fd, mk):
    """Cỡ chữ nhãn tag + chữ "X" = CO_CHU_MM (kiểu nhãn của nhãn Type Mark, kiểu chữ 'ARV_Tag X'); nền chữ Opaque để
    che nét tường khi tag nằm trên ô cửa (như mẫu FPT)."""
    for el in [fd.GetElement(mk.GetTypeId())] + [t_ for t_ in FilteredElementCollector(fd).OfClass(TextNoteType)
                                                if ten(t_) == u"ARV_Tag X"]:
        try:
            p_ = el.get_Parameter(BuiltInParameter.TEXT_SIZE)
            if p_ is not None and not p_.IsReadOnly and abs(p_.AsDouble() - ft(CO_CHU_MM)) > 1e-9:
                p_.Set(ft(CO_CHU_MM))
        except Exception:
            pass
        try:
            p_ = el.get_Parameter(BuiltInParameter.TEXT_BACKGROUND)
            if p_ is not None and not p_.IsReadOnly and p_.AsInteger() != 0:
                p_.Set(0)             # 0 = Opaque
        except Exception:
            pass


def nen_chu_dung(fd, mk):
    try:
        p_ = fd.GetElement(mk.GetTypeId()).get_Parameter(BuiltInParameter.TEXT_BACKGROUND)
        return p_ is None or p_.AsInteger() == 0
    except Exception:
        return True


def khung_cua_tool(fd):
    """Nét khung 2 ô do công cụ vẽ: detail line KHÔNG gắn tham số hiện / ẩn (khung bo góc gốc của family có gắn)."""
    fm_ = fd.FamilyManager
    kq = []
    for c in FilteredElementCollector(fd).OfClass(CurveElement):
        try:
            if str(c.CurveElementType) != "DetailCurve" or not c.GeometryCurve.IsBound:
                continue
            if fm_.GetAssociatedFamilyParameter(c.get_Parameter(BuiltInParameter.IS_VISIBLE_PARAM)) is None:
                kq.append(c)
        except Exception:
            pass
    return kq


def ve_khung_2_o(fd, view, mk, cx, cy):
    """Khung tag như mẫu CAD người dùng (2026-11-03): chữ nhật góc vuông chia 2 ô bằng 1 nét ngang, ô trên mã, ô dưới
    kích thước. Tắt khung bo góc cũ (tham số hiện khung của family = 0), vẽ 5 detail line mới cùng kiểu nét khung cũ."""
    cu = [c for c in FilteredElementCollector(fd).OfClass(CurveElement)
          if str(c.CurveElementType) == "DetailCurve" and c.GeometryCurve.IsBound]
    kieu_net = cu[0].LineStyle if cu else None
    fm_ = fd.FamilyManager
    for c in cu:
        try:
            pv = fm_.GetAssociatedFamilyParameter(c.get_Parameter(BuiltInParameter.IS_VISIBLE_PARAM))
            if pv is not None:
                fm_.Set(pv, 0)
        except Exception:
            pass
    w, h = ft(KHUNG_RONG_MM) / 2.0, ft(KHUNG_O_MM)
    z = mk.Coord.Z
    goc = [XYZ(cx - w, cy - h, z), XYZ(cx + w, cy - h, z), XYZ(cx + w, cy + h, z), XYZ(cx - w, cy + h, z)]
    doan = [(goc[i], goc[(i + 1) % 4]) for i in range(4)] + [(XYZ(cx - w, cy, z), XYZ(cx + w, cy, z))]
    for a, b in doan:
        dc = fd.FamilyCreate.NewDetailCurve(view, Line.CreateBound(a, b))
        if kieu_net is not None:
            try:
                dc.LineStyle = kieu_net
            except Exception:
                pass


THANG_TL = (100,)   # tỉ lệ mặt bằng định vị cửa LUÔN 1:100 (người dùng chốt 2026-11-03 tối); không vừa khổ thì chỉ báo
BIEN_MM = 8.0           # lề trong vùng vẽ của khung tên (mm giấy)
TIEU_DE_MM = 15.0       # chỗ tên view dưới viewport
KHE_BANG_MM = 6.0       # khe giữa 2 bảng thống kê / giữa bảng và mặt bằng
DU_TAG_MM = 12.0        # chừa mỗi bên khung viewport cho tag đặt ngoài nhà (tỉ lệ chọn trước khi tag)


def cap_thu_muc_sheet(doc):
    """Các cấp nhóm sheet trong Project Browser của dự án đang mở: [(id tham số, tên)] theo thứ tự cấp (vd. giai đoạn
    → hạng mục). Đọc từ sheet đầu tiên có thư mục."""
    try:
        bo = BrowserOrganization.GetCurrentBrowserOrganizationForSheets(doc)
    except Exception:
        return []
    for s in FilteredElementCollector(doc).OfClass(ViewSheet):
        try:
            items = list(bo.GetFolderItems(s.Id))
        except Exception:
            continue
        if not items:
            continue
        kq = []
        for it in items:
            pid = it.ElementId
            ten_ts = u"%s" % pid.Value
            for prm in s.Parameters:
                if prm.Id.Value == pid.Value and prm.Definition is not None:
                    ten_ts = prm.Definition.Name
            kq.append((pid, ten_ts))
        return kq
    return []


def ts_theo_id(e, pid):
    for prm in e.Parameters:
        if prm.Id.Value == pid.Value:
            return prm
    return None


def ts_giai_doan(doc, cap):
    """(id tham số giai đoạn, id tham số hạng mục). Browser 2 cấp: cấp 1 = giai đoạn, cấp 2 = hạng mục. 1 cấp: cấp đó là
    hạng mục, giai đoạn = tham số sheet có chữ "giai đoạn" (vd. G19 'Lọc Giai Đoạn Hồ Sơ')."""
    if len(cap) >= 2:
        return cap[0][0], cap[1][0]
    hm = cap[0][0] if cap else None
    dem = {}            # tham số sheet có chữ "giai đoạn" → số sheet có giá trị (chọn tham số đang dùng nhiều nhất)
    for s in FilteredElementCollector(doc).OfClass(ViewSheet):
        for prm in s.Parameters:
            if prm.Definition is not None and prm.StorageType == StorageType.String and \
                    u"giai doan" in khong_dau(prm.Definition.Name) and (hm is None or prm.Id.Value != hm.Value):
                k = prm.Id.Value
                dem.setdefault(k, [prm.Id, 0])
                if prm.AsString():
                    dem[k][1] += 1
    gd = max(dem.values(), key=lambda x: x[1])[0] if dem else None
    return gd, hm


def gia_tri_chuoi(prm):
    try:
        return (prm.AsString() or u"") if prm.StorageType == StorageType.String else (prm.AsValueString() or u"")
    except Exception:
        return u""


def so_hieu_tiep(doc, pid_gd, gd, pid_hm, hm):
    """Số hiệu sheet tiếp theo trong cùng hạng mục (tăng phần số cuối, giữ số chữ số); chưa có thì "A.DVC.01"."""
    import re
    dung = set(s.SheetNumber for s in FilteredElementCollector(doc).OfClass(ViewSheet))
    cung = []
    for s in FilteredElementCollector(doc).OfClass(ViewSheet):
        if pid_hm is not None and hm:
            p_ = ts_theo_id(s, pid_hm)
            if p_ is None or gia_tri_chuoi(p_) != hm:
                continue
            if pid_gd is not None and gd:
                q_ = ts_theo_id(s, pid_gd)
                if q_ is not None and gia_tri_chuoi(q_) and gia_tri_chuoi(q_) != gd:
                    continue
            cung.append(s.SheetNumber)
    goc = None
    for so in sorted(cung):
        if re.search(r"\d+$", so):
            goc = so
    if goc is None:
        goc = u"A.DVC.00"
    m = re.search(r"(\d+)$", goc)
    dau, n, w = goc[:m.start()], int(m.group(1)), len(m.group(1))
    while True:
        n += 1
        ung = u"%s%0*d" % (dau, w, n)
        if ung not in dung:
            return ung


def tim_khung_ten(doc, kho, khung):
    ds = list(FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_TitleBlocks))
    if khung:
        for s in ds:
            if khung in (u"%s : %s" % (s.FamilyName, ten(s)), ten(s), s.FamilyName):
                return s
    k = khong_dau(kho or u"A1").replace(u" ", u"")
    ung = [s for s in ds if k in khong_dau(s.FamilyName + u" " + ten(s)).replace(u" ", u"")
           and u"bia" not in khong_dau(s.FamilyName + u" " + ten(s))]
    ung.sort(key=lambda s: (0 if u"khung" in khong_dau(s.FamilyName) else 1, s.FamilyName))
    return ung[0] if ung else None


def net_khung_ten(doc, tb_sym):
    """Nét đứng [(x, dài)] / nét ngang [(y, dài)] của family khung tên, toạ độ family. Đọc trong file family (EditFamily,
    đóng không lưu) vì hình học khung tên trên sheet trả về rỗng (thử G19). Gọi NGOÀI transaction."""
    dung, ngang = [], []
    fd = None
    try:
        TransactionManager.Instance.ForceCloseTransaction()
        fd = doc.EditFamily(tb_sym.Family)
        for c in FilteredElementCollector(fd).OfClass(CurveElement):
            try:
                g = c.GeometryCurve
                if g is None or not g.IsBound or g.GetType().Name != "Line":
                    continue
                a, b_ = g.GetEndPoint(0), g.GetEndPoint(1)
                if abs(a.X - b_.X) < 1e-6:
                    dung.append((a.X, abs(a.Y - b_.Y)))
                elif abs(a.Y - b_.Y) < 1e-6:
                    ngang.append((a.Y, abs(a.X - b_.X)))
            except Exception:
                pass
    except Exception:
        pass
    finally:
        if fd is not None:
            try:
                fd.Close(False)
            except Exception:
                pass
    return dung, ngang


def vung_ve(doc, sheet, tb_inst, net):
    """Vùng vẽ (x0, y0, x1, y1) theo toạ độ sheet: trong khung trong, bên trái dải khung tên phải. Đo từ nét đứng / nét
    ngang dài của family khung tên (net_khung_ten, đổi sang toạ độ sheet theo vị trí khung tên); không đo được thì lấy
    khung bao trừ lề 25 / 15 mm và 1/6 bên phải."""
    tf = tb_inst.GetTotalTransform()
    dung = [(tf.OfPoint(XYZ(x, 0, 0)).X, l) for x, l in net[0]]
    ngang = [(tf.OfPoint(XYZ(0, y, 0)).Y, l) for y, l in net[1]]
    bb = tb_inst.get_BoundingBox(sheet)
    X0, Y0, X1, Y1 = bb.Min.X, bb.Min.Y, bb.Max.X, bb.Max.Y
    W, H = X1 - X0, Y1 - Y0
    d40 = ft(40.0)
    dai_d = [x for x, l in dung if l > 0.6 * H]
    dai_n = [y for y, l in ngang if l > 0.6 * W]
    x0 = max([x for x in dai_d if x < X0 + d40] or [X0 + ft(25.0)])
    x1 = max([x for x in dai_d if X0 + d40 < x < X1 - d40] or [X1 - W / 6.0])
    y0 = max([y for y in dai_n if y < Y0 + d40] or [Y0 + ft(15.0)])
    y1 = min([y for y in dai_n if y > Y1 - d40] or [Y1 - ft(15.0)])
    return x0, y0, x1, y1


def kich_thuoc_view(doc, view):
    """(rộng, cao) theo model của phần view sẽ in: vùng crop nếu bật crop, không thì khung bao tường trong view."""
    if view.CropBoxActive:
        cb = view.CropBox
        return cb.Max.X - cb.Min.X, cb.Max.Y - cb.Min.Y
    U, V = view.RightDirection, view.UpDirection
    us, vs = [], []
    for w in FilteredElementCollector(doc, view.Id).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType():
        bb = w.get_BoundingBox(view)
        if bb is None:
            continue
        for q in (bb.Min, bb.Max):
            us.append(q.X * U.X + q.Y * U.Y)
            vs.append(q.X * V.X + q.Y * V.Y)
    if not us:
        return ft(30000.0), ft(20000.0)
    return (max(us) - min(us)) * 1.1, (max(vs) - min(vs)) * 1.1


def tao_bang(doc, bic, ten_bang, level, loai_tru_tc):
    """Bảng thống kê cửa của 1 tầng: Tên (Type Mark) / Chiều rộng / Chiều cao / Số lượng/Tầng, gộp theo Type Mark, lọc
    Level = tầng của mặt bằng, bỏ Type Comments loại trừ (Louver). Đã có bảng cùng tên thì dùng lại. Nhân bản bảng thống
    kê cùng hạng mục có sẵn (giữ kiểu trình bày công ty), không có thì tạo mới."""
    for vs in FilteredElementCollector(doc).OfClass(ViewSchedule):
        if not vs.IsTemplate and vs.Name == ten_bang:
            return vs, u"dùng lại bảng '%s'" % ten_bang
    nguon = [vs for vs in FilteredElementCollector(doc).OfClass(ViewSchedule)
             if not vs.IsTemplate and not vs.IsTitleblockRevisionSchedule and vs.Definition.CategoryId.Value == int(bic)]
    nguon.sort(key=lambda vs: (0 if u"thong ke" in khong_dau(vs.Name) else 1, vs.Name))
    if nguon:
        vs = doc.GetElement(nguon[0].Duplicate(ViewDuplicateOption.Duplicate))
        cach = u"nhân bản '%s'" % nguon[0].Name
    else:
        vs = ViewSchedule.CreateSchedule(doc, ElementId(bic))
        cach = u"tạo mới"
    vs.Name = ten_bang
    d = vs.Definition
    can = [("mark", BuiltInParameter.ALL_MODEL_TYPE_MARK, u"Tên"), ("rong", BuiltInParameter.GENERIC_WIDTH, u"Chiều rộng"),
           ("cao", BuiltInParameter.GENERIC_HEIGHT, u"Chiều cao")]
    co = {}
    for i in range(d.GetFieldCount()):
        f = d.GetField(i)
        try:
            pid = f.ParameterId.Value
        except Exception:
            pid = None
        co.setdefault(("pid", pid), f)
        if str(f.FieldType) == "Count":
            co[("count", None)] = f

    def lay(pid_bip, ten_rieng=None):
        k = ("pid", int(pid_bip))
        if k in co:
            return co[k]
        for sf in d.GetSchedulableFields():
            try:
                if sf.ParameterId.Value == int(pid_bip):
                    co[k] = d.AddField(sf)
                    return co[k]
            except Exception:
                pass
        return None

    f_mark = lay(BuiltInParameter.ALL_MODEL_TYPE_MARK)
    f_rong = lay(BuiltInParameter.DOOR_WIDTH if int(bic) == int(BuiltInCategory.OST_Doors) else BuiltInParameter.WINDOW_WIDTH) \
        or lay(BuiltInParameter.GENERIC_WIDTH) or lay(BuiltInParameter.FAMILY_WIDTH_PARAM)
    f_cao = lay(BuiltInParameter.DOOR_HEIGHT if int(bic) == int(BuiltInCategory.OST_Doors) else BuiltInParameter.WINDOW_HEIGHT) \
        or lay(BuiltInParameter.GENERIC_HEIGHT) or lay(BuiltInParameter.FAMILY_HEIGHT_PARAM)
    f_dem = co.get(("count", None))
    if f_dem is None:
        for sf in d.GetSchedulableFields():
            if str(sf.FieldType) == "Count":
                f_dem = d.AddField(sf)
                break
    f_tang = lay(BuiltInParameter.FAMILY_LEVEL_PARAM) or lay(BuiltInParameter.SCHEDULE_LEVEL_PARAM)
    f_tc = lay(BuiltInParameter.ALL_MODEL_TYPE_COMMENTS)
    hien = [(f_mark, u"Tên"), (f_rong, u"Chiều rộng"), (f_cao, u"Chiều cao"), (f_dem, u"Số lượng/Tầng")]
    for i in range(d.GetFieldCount()):
        f = d.GetField(i)
        f.IsHidden = not any(f.FieldId == g.FieldId for g, _ in hien if g is not None)
    for f, nhan in hien:
        if f is not None:
            f.ColumnHeading = nhan
    try:
        from System.Collections.Generic import List
        thu_tu = List[ScheduleFieldId]()
        for f, _ in hien:
            if f is not None:
                thu_tu.Add(f.FieldId)
        for i in range(d.GetFieldCount()):
            f = d.GetField(i)
            if not any(f.FieldId == g.FieldId for g, _ in hien if g is not None):
                thu_tu.Add(f.FieldId)
        d.SetFieldOrder(thu_tu)
    except Exception:
        pass
    d.ClearFilters()
    if f_tang is not None and level is not None:
        d.AddFilter(ScheduleFilter(f_tang.FieldId, ScheduleFilterType.Equal, level.Id))
    if f_tc is not None:
        for tc in loai_tru_tc:
            d.AddFilter(ScheduleFilter(f_tc.FieldId, ScheduleFilterType.NotContains, tc))
    d.ClearSortGroupFields()
    if f_mark is not None:
        d.AddSortGroupField(ScheduleSortGroupField(f_mark.FieldId))
    d.IsItemized = False
    try:
        d.ShowTitle = True
    except Exception:
        pass
    return vs, cach


def chuan_bi_sheet(doc, view, gd, hm, kho, khung, so_hieu, ten_sheet, loai_tru_tc):
    """Tạo sheet (khung tên theo khổ), gán giai đoạn / hạng mục theo cách nhóm sheet của dự án, đặt 2 bảng thống kê cửa
    ở góc phải dưới vùng vẽ, chọn tỉ lệ lớn nhất mà mặt bằng vừa phần còn lại và đặt tỉ lệ cho view (TRƯỚC khi tag vì cỡ
    tag theo tỉ lệ). Trả về (ngữ cảnh để đặt viewport sau khi tag | None, [báo cáo])."""
    bao = []
    try:
        dang = view.get_Parameter(BuiltInParameter.VIEWER_SHEET_NUMBER)
        if dang is not None and dang.AsString() and dang.AsString() not in (u"---", u"-"):
            return None, [u"View '%s' đã nằm trên sheet %s – không đặt thêm." % (view.Name, dang.AsString())]
    except Exception:
        pass
    tb = tim_khung_ten(doc, kho, khung)
    if tb is None:
        return None, [u"Không có family khung tên khổ %s trong dự án (tên family / type có chữ '%s') – chưa đặt lên "
                      u"sheet. Load khung tên rồi bấm lại." % (kho, kho)]
    cap = cap_thu_muc_sheet(doc)
    pid_gd, pid_hm = ts_giai_doan(doc, cap)
    tang = view.GenLevel.Name if view.GenLevel is not None else view.Name
    ten_sheet = (ten_sheet or u"MẶT BẰNG ĐỊNH VỊ CỬA %s" % tang).strip().upper()
    so = (so_hieu or u"").strip() or so_hieu_tiep(doc, pid_gd, gd, pid_hm, hm)
    dung = set(s.SheetNumber for s in FilteredElementCollector(doc).OfClass(ViewSheet))
    if so in dung:
        import re
        cu = so
        m = re.search(r"(\d+)$", so)
        dau, n, w = (so[:m.start()], int(m.group(1)), len(m.group(1))) if m else (so + u"-", 0, 1)
        while so in dung:
            n += 1
            so = u"%s%0*d" % (dau, w, n)
        bao.append(u"Số hiệu '%s' đã có – dùng '%s'." % (cu, so))
    net = net_khung_ten(doc, tb)         # mở family khung tên: phải trước khi mở transaction
    TransactionManager.Instance.EnsureInTransaction(doc)
    sh = ViewSheet.Create(doc, tb.Id)
    sh.SheetNumber = so
    sh.Name = ten_sheet
    for pid, gt_, nhan in ((pid_gd, gd, u"giai đoạn"), (pid_hm, hm, u"hạng mục")):
        if pid is None or not gt_:
            continue
        prm = ts_theo_id(sh, pid)
        if prm is not None and not prm.IsReadOnly:
            prm.Set(gt_)
        else:
            bao.append(u"Không gán được %s '%s' (tham số không ghi được)." % (nhan, gt_))
    doc.Regenerate()
    tb_inst = [t for t in FilteredElementCollector(doc, sh.Id).OfCategory(BuiltInCategory.OST_TitleBlocks)
               .WhereElementIsNotElementType()][0]
    x0, y0, x1, y1 = vung_ve(doc, sh, tb_inst, net)
    bao.append(u"Vùng vẽ trên sheet: x %d–%d, y %d–%d mm." % (mm(x0), mm(x1), mm(y0), mm(y1)))
    b, khe = ft(BIEN_MM), ft(KHE_BANG_MM)
    # Bảng thống kê: cửa đi trên, cửa sổ dưới, sát góc phải dưới vùng vẽ
    bang = []
    for bic, loai in ((BuiltInCategory.OST_Doors, u"CỬA ĐI"), (BuiltInCategory.OST_Windows, u"CỬA SỔ")):
        try:
            vs, cach = tao_bang(doc, bic, u"BẢNG THỐNG KÊ %s %s" % (loai, tang.upper()), view.GenLevel, loai_tru_tc)
            si = ScheduleSheetInstance.Create(doc, sh.Id, vs.Id, XYZ(x0, y1, 0))
            bang.append((si, vs, cach))
        except Exception as ex:
            bao.append(u"Không tạo được bảng thống kê %s: %s" % (loai, (u"%s" % ex).splitlines()[0][:120]))
    doc.Regenerate()
    def co_bang(si, vs):
        """(rộng, cao) bảng trên giấy theo khung bao. Khung bao của ScheduleSheetInstance đúng kích thước nhưng lệch vị
        trí (thử G19: thấp hơn bảng thật ~12 mm) → chỉ lấy kích thước, đặt bảng theo Point (góc trên trái)."""
        bb_ = si.get_BoundingBox(sh)
        return bb_.Max.X - bb_.Min.X, bb_.Max.Y - bb_.Min.Y

    # Bảng sát GÓC khung bản vẽ như mẫu FPT (người dùng 2026-11-03 chiều): đáy bảng cửa sổ trên nét khung dưới, mép phải
    # trên nét dải khung tên; bảng cửa đi ngay trên
    rong_bang = cao_bang = 0.0
    y = y0
    for si, vs, cach in reversed(bang):
        w, h = co_bang(si, vs)
        rong_bang = max(rong_bang, w)
        si.Point = XYZ(x1 - w, y + h, 0)           # Point = góc trên trái của bảng
        y += h + khe
        cao_bang = y - y0
    doc.Regenerate()
    for si, vs, cach in bang:
        bao.append(u"Bảng '%s' (%s)." % (vs.Name, cach))
    # Bố cục (người dùng chốt 2026-11-03): mặt bằng NGAY GIỮA vùng vẽ của khổ giấy, bảng ở góc phải dưới, không đè nhau
    tieu_de = ft(TIEU_DE_MM)
    vung = (x0 + b, y0 + b + tieu_de, x1 - b, y1 - b)
    o_bang = (x1 - rong_bang - khe, y0, x1, y0 + cao_bang + khe) if bang else None
    tpl = doc.GetElement(view.ViewTemplateId) if view.ViewTemplateId != ElementId.InvalidElementId else None
    # Tỉ lệ chọn trong hộp thoại (IN[29], 2026-11-05) hoặc template khoá tỉ lệ → dùng đúng tỉ lệ đó, KHÔNG sửa template
    # (trước đây bỏ quyền điều khiển tỉ lệ của template)
    try:
        tl_chon = int(round(float(doc_in(29) or 0)))
    except Exception:
        tl_chon = 0
    thang_tl = THANG_TL
    if tpl is not None and tpl_khoa_tl(tpl):
        thang_tl = (tpl.Scale,)
    elif tl_chon > 0:
        thang_tl = (tl_chon,)
    if tpl is not None and thang_tl is THANG_TL:
        try:
            ids_tl = [int(BuiltInParameter.VIEW_SCALE_PULLDOWN_METRIC), int(BuiltInParameter.VIEW_SCALE),
                      int(BuiltInParameter.VIEW_SCALE_PULLDOWN_IMPERIAL)]
            nc = list(tpl.GetNonControlledTemplateParameterIds())
            them = [ElementId(i) for i in ids_tl if not any(x.Value == i for x in nc)]
            if them:
                from System.Collections.Generic import List
                ds = List[ElementId]()
                for x in nc + them:
                    ds.Add(x)
                tpl.SetNonControlledTemplateParameterIds(ds)
        except Exception as ex:
            bao.append(u"Không bỏ điều khiển tỉ lệ của template '%s': %s" % (tpl.Name, ex))
    # Tỉ lệ: ưu tiên 1:100; khung viewport THẬT (gồm trục, bóng trục, chú thích) + chỗ tag quanh nhà, đặt giữa vùng vẽ,
    # phải vừa vùng và không đè ô bảng. Đo bằng viewport đặt thử trong SubTransaction rồi huỷ.
    du = 2.0 * ft(DU_TAG_MM)
    cx_, cy_ = (vung[0] + vung[2]) / 2.0, (vung[1] + vung[3]) / 2.0

    def do_khung(n):
        st = SubTransaction(doc)
        st.Start()
        try:
            if view.Scale != n:
                view.Scale = n
            vp_ = Viewport.Create(doc, sh.Id, view.Id, XYZ(0, 0, 0))
            doc.Regenerate()
            o_ = vp_.GetBoxOutline()
            return o_.MaximumPoint.X - o_.MinimumPoint.X + du, o_.MaximumPoint.Y - o_.MinimumPoint.Y + du
        except Exception:
            wm_, hm2 = kich_thuoc_view(doc, view)
            return wm_ / n + du, hm2 / n + du
        finally:
            st.RollBack()

    # Tỉ lệ ưu tiên 1:100 (người dùng chốt): lấy tỉ lệ đầu tiên vừa vùng vẽ; chạm ô bảng thì chỉ báo, không lùi tỉ lệ
    tl = None
    for n in thang_tl:
        w_, h_ = do_khung(n)
        if w_ > vung[2] - vung[0] or h_ > vung[3] - vung[1]:
            continue
        tl = n
        if o_bang is not None and (cx_ - w_ / 2.0 < o_bang[2] and cx_ + w_ / 2.0 > o_bang[0] and
                                   cy_ - h_ / 2.0 < o_bang[3] and cy_ + h_ / 2.0 > o_bang[1]):
            bao.append(u"CẦN XEM LẠI: khung mặt bằng 1:%d (kể cả trục, chừa chỗ tag) có thể chạm bảng thống kê góc phải "
                       u"dưới – xem lại, dời bảng tay nếu cần." % n)
        break
    if tl is None:
        tl = thang_tl[-1]
        bao.append(u"CẦN XEM LẠI: mặt bằng 1:%d (kể cả trục, chừa chỗ tag) lớn hơn vùng vẽ khổ %s – chọn khổ lớn hơn hoặc "
                   u"thu crop view." % (tl, kho))
    if view.Scale != tl:
        view.Scale = tl
    doc.Regenerate()
    TransactionManager.Instance.TransactionTaskDone()
    bao.append(u"Sheet %s – %s (khung %s : %s, khổ %s); tỉ lệ mặt bằng 1:%d, đặt giữa khổ giấy." % (
        so, ten_sheet, tb.FamilyName, ten(tb), kho, tl))
    if not cap:
        bao.append(u"Project Browser không nhóm sheet theo tham số – không gán giai đoạn / hạng mục.")
    return {"sheet": sh, "vung": vung, "ten_view": ten_sheet}, bao


def dat_viewport(doc, ctx, view):
    """Đặt mặt bằng vào giữa vùng còn lại của sheet, kiểu viewport có tên view (title), "Title on Sheet" = tên sheet."""
    bao = []
    sh = ctx["sheet"]
    vx0, vy0, vx1, vy1 = ctx["vung"]
    TransactionManager.Instance.EnsureInTransaction(doc)
    try:
        prm = view.get_Parameter(BuiltInParameter.VIEW_DESCRIPTION)
        if prm is not None and not prm.IsReadOnly:
            prm.Set(ctx["ten_view"])
    except Exception:
        pass
    vp = Viewport.Create(doc, sh.Id, view.Id, XYZ((vx0 + vx1) / 2.0, (vy0 + vy1) / 2.0, 0))
    kieu = []
    for et in FilteredElementCollector(doc).OfClass(ElementType):
        try:
            if et.FamilyName != "Viewport":
                continue
            nhan = et.get_Parameter(BuiltInParameter.VIEWPORT_ATTR_LABEL_TAG)
            if nhan is None or nhan.AsElementId() == ElementId.InvalidElementId:
                continue
            n = khong_dau(ten(et))
            kieu.append((0 if u"no scale" not in n and u"detail" not in n else 1, ten(et), et))
        except Exception:
            pass
    if kieu:
        kieu.sort(key=lambda k: (k[0], k[1]))
        vp.ChangeTypeId(kieu[0][2].Id)
    doc.Regenerate()
    o = vp.GetBoxOutline()
    w, h = o.MaximumPoint.X - o.MinimumPoint.X, o.MaximumPoint.Y - o.MinimumPoint.Y
    c = vp.GetBoxCenter()
    # khung viewport (gồm chú thích) đặt giữa vùng; lớn hơn vùng thì canh trái trên
    cx = (vx0 + vx1) / 2.0 if w <= vx1 - vx0 else vx0 + w / 2.0
    cy = (vy0 + vy1) / 2.0 if h <= vy1 - vy0 else vy1 - h / 2.0
    vp.SetBoxCenter(XYZ(cx, cy, 0))
    TransactionManager.Instance.TransactionTaskDone()
    if w > vx1 - vx0 + 1e-6 or h > vy1 - vy0 + 1e-6:
        bao.append(u"CẦN XEM LẠI: khung mặt bằng (kể cả chú thích, trục) %d x %d mm lớn hơn vùng trống %d x %d mm trên sheet."
                   % (mm(w), mm(h), mm(vx1 - vx0), mm(vy1 - vy0)))
    bao.append(u"Đã đặt mặt bằng lên sheet %s (kiểu viewport '%s')." % (sh.SheetNumber, kieu[0][1] if kieu else u"mặc định"))
    return bao


def thu_muc_nhan():
    """Thư mục family .rfa nguồn nhãn (IN[20]); trống = <extension>\\lib\\tag_cua khi chạy từ nút pyRevit (__file__ =
    core.py trong thư mục nút)."""
    d = (doc_in(20) or u"").strip()
    if d:
        return d
    try:
        f = globals().get("__file__")
        if f:
            return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(f)), u"..", u"..", u"..", u"lib",
                                                 u"tag_cua"))
    except Exception:
        pass
    return u""


def them_kich_thuoc(doc, fams, dry, thu_muc_nguon=u""):
    """Ô dưới của tag = Width "X" Height theo mm, như mẫu CAD người dùng "1400X2195" (2026-11-03). API 2027.3 không tạo
    được nhãn mới, nên chép nhãn có sẵn rồi ghép:
      1. family tag cùng hạng mục có 1 nhãn chứa cả Width + Height (vd. người dùng tự sửa) → chép nhãn đó;
      2. không thì nhãn Width (không tiền tố, căn phải) + chữ "X" (TextNote) + nhãn Height KHÔNG tiền tố (căn trái).
         Width lấy từ family tag cùng hạng mục trong dự án (AV_Door Tag_Full / AV_Window Tag_Full); Height không tiền tố
         lấy trong dự án hoặc family .rfa trong thu_muc_nguon (AV-Tag-DOOR-Lomo / AV-Tag-Window-Lomo, mở riêng để chép,
         không nạp vào dự án);
      3. không có Height không tiền tố thì dùng nhãn "x Height" (tiền tố "x ") của AV_*_Full.
    Nhãn "theo đơn vị dự án" trong family tag hiển thị theo đơn vị CỦA FILE FAMILY (G19: mét → "0.900") → đặt đơn vị
    Length của family tag = mm, 0 số lẻ, không nhóm số. Nhãn Type Mark ở ô trên, khung chữ nhật 2 ô (ve_khung_2_o), nạp
    lại. Family đã có nhãn bề rộng thì bỏ qua (bấm lại không thêm). Gọi NGOÀI transaction của dự án."""
    lop_nhan = getattr(_RevitDB, "AnnotationLabel", None)
    if lop_nhan is None:
        return u""

    def fmts(lb, fd):
        """[(tên BuiltInParameter, tiền tố)]"""
        kq = []
        for fm in lb.GetParameterFormatting():
            try:
                kq.append((str(fm.GetParameterDefinition(fd).BuiltInParameter), fm.Prefix or u""))
            except Exception:
                pass
        return kq

    def gop_dung(lb, fd):
        """Nhãn gộp đúng mẫu "830X2200": Width trước, Height sau, giữa có chữ X (tiền tố Height / hậu tố Width).
        Model G19_A_L3-32 có family AV-Tag-Window-Lomo (hạng mục Door Tags) nhãn gộp "Height Width" → hiện "2200 830",
        SAI (người dùng báo 2026-11-04) → không dùng làm nguồn."""
        f = []
        for fm in lb.GetParameterFormatting():
            try:
                f.append((str(fm.GetParameterDefinition(fd).BuiltInParameter), fm.Prefix or u"", fm.Suffix or u""))
            except Exception:
                pass
        if len(f) != 2 or f[0][0] not in BIP_RONG or f[1][0] not in BIP_CAO:
            return False
        return u"X" in (f[0][2] + f[1][1]).upper()

    def nhan_theo(fd, ds):
        for lb in FilteredElementCollector(fd).OfClass(lop_nhan):
            if any(b in ds for b, _ in fmts(lb, fd)):
                return lb
        return None

    def tam_y(lb):
        h = lb.Height if hasattr(lb, "Height") else 0.0
        va = str(lb.VerticalAlignment)
        return lb.Coord.Y - h / 2.0 if va == "Top" else (lb.Coord.Y + h / 2.0 if va == "Bottom" else lb.Coord.Y)

    def loai(lb, fd):
        """'gop' (rộng + cao), 'rong' (chỉ rộng, không tiền tố), 'cao' (chỉ cao, không tiền tố), 'cao_x' (cao có tiền tố)"""
        f = fmts(lb, fd)
        r = [t_ for b, t_ in f if b in BIP_RONG]
        c = [t_ for b, t_ in f if b in BIP_CAO]
        if r and c:
            return "gop" if gop_dung(lb, fd) else None
        if r and len(f) == 1 and not r[0]:
            return "rong"
        if c and len(f) == 1:
            return "cao" if not c[0] else "cao_x"
        return None

    ket_qua = []
    da_mo = []
    kho = {}            # id hạng mục → {loại: (family doc, nhãn, tên family)}
    ten_bo = set(f_.Name for f_ in fams)

    def ghi_kho(cat_id, fd2, ten2):
        for lb in FilteredElementCollector(fd2).OfClass(lop_nhan):
            k = loai(lb, fd2)
            if k and k not in kho[cat_id]:
                kho[cat_id][k] = (fd2, lb, ten2)

    def tim_nguon(cat_id):
        """Thứ tự: nhãn gộp trong dự án (người dùng tự sửa) → family nguồn đóng gói (Width / Height theo mm) → family
        tag trong dự án (AV_*_Full: Width theo mét, Height có tiền tố "x ")."""
        if cat_id in kho:
            return kho[cat_id]
        kho[cat_id] = {}
        du_an = {}
        kho[cat_id], tam = du_an, kho[cat_id]
        for f2 in FilteredElementCollector(doc).OfClass(Family):
            if f2.Name in ten_bo or f2.FamilyCategory is None or f2.FamilyCategory.Id.Value != cat_id or not f2.IsEditable:
                continue
            fd2 = doc.EditFamily(f2)
            da_mo.append(fd2)
            ghi_kho(cat_id, fd2, f2.Name)
        kho[cat_id] = tam
        if "gop" in du_an:
            kho[cat_id]["gop"] = du_an["gop"]
        if thu_muc_nguon and os.path.isdir(thu_muc_nguon):
            for fn in sorted(os.listdir(thu_muc_nguon)):
                if not fn.lower().endswith(".rfa"):
                    continue
                try:
                    fd2 = doc.Application.OpenDocumentFile(os.path.join(thu_muc_nguon, fn))
                except Exception:
                    continue
                da_mo.append(fd2)
                # Chép nhãn khác hạng mục bị Revit từ chối → đổi tạm hạng mục family nguồn (chỉ trong bộ nhớ, không lưu)
                if fd2.OwnerFamily.FamilyCategory is not None and fd2.OwnerFamily.FamilyCategory.Id.Value != cat_id:
                    try:
                        t2 = Transaction(fd2, u"Đổi hạng mục tạm")
                        t2.Start()
                        fd2.OwnerFamily.FamilyCategory = Category.GetCategory(fd2, ElementId(cat_id))
                        t2.Commit()
                    except Exception:
                        continue
                if fd2.OwnerFamily.FamilyCategory is not None and fd2.OwnerFamily.FamilyCategory.Id.Value == cat_id:
                    ghi_kho(cat_id, fd2, fn)
        for k, v in du_an.items():
            kho[cat_id].setdefault(k, v)
        return kho[cat_id]

    def kieu_chu_x(fd, lb_mau):
        """TextNoteType cho chữ "X": cùng cỡ chữ / font / tỉ lệ rộng với nhãn mẫu."""
        ds = list(FilteredElementCollector(fd).OfClass(TextNoteType))
        for t_ in ds:
            if ten(t_) == u"ARV_Tag X":
                return t_
        if not ds:
            return None
        kx = ds[0].Duplicate(u"ARV_Tag X")
        lt = fd.GetElement(lb_mau.GetTypeId())
        for b in (BuiltInParameter.TEXT_SIZE, BuiltInParameter.TEXT_FONT, BuiltInParameter.TEXT_WIDTH_SCALE,
                  BuiltInParameter.LINE_COLOR, BuiltInParameter.TEXT_BACKGROUND):
            try:
                a, d = lt.get_Parameter(b), kx.get_Parameter(b)
                if a is None or d is None or d.IsReadOnly:
                    continue
                if a.StorageType == StorageType.Double:
                    d.Set(a.AsDouble())
                elif a.StorageType == StorageType.Integer:
                    d.Set(a.AsInteger())
                elif a.StorageType == StorageType.String:
                    d.Set(a.AsString())
            except Exception:
                pass
        return kx

    def chep(nguon_, view_dich):
        from System.Collections.Generic import List
        ids = List[ElementId]()
        ids.Add(nguon_[1].Id)
        ids_moi = list(ElementTransformUtils.CopyElements(nguon_[0].GetElement(nguon_[1].OwnerViewId), ids, view_dich,
                                                          Transform.Identity, tuy_chon_dan()))
        return [e_ for e_ in [view_dich.Document.GetElement(i) for i in ids_moi] if e_ is not None][0]

    TransactionManager.Instance.ForceCloseTransaction()
    try:
        for fam in fams:
            ten_f = fam.Name
            cat_id = fam.FamilyCategory.Id.Value if fam.FamilyCategory is not None else None
            try:
                if not fam.IsEditable:
                    continue
                fd = doc.EditFamily(fam)
                da_mo.append(fd)
                sai = [lb for lb in FilteredElementCollector(fd).OfClass(lop_nhan)
                       if any(b in BIP_RONG for b, _ in fmts(lb, fd)) and any(b in BIP_CAO for b, _ in fmts(lb, fd))
                       and not gop_dung(lb, fd)]
                net = khung_cua_tool(fd)
                mk = nhan_theo(fd, ("ALL_MODEL_TYPE_MARK",))
                if sai and len(net) >= 5 and mk is not None:
                    # Ô kích thước do công cụ chép SAI thứ tự ("2200 830") → bỏ nhãn đó + khung 2 ô của công cụ, đưa nhãn
                    # mã về giữa khung rồi thêm lại theo cách Width "X" Height bên dưới
                    if dry:
                        ket_qua.append(u"'%s': sẽ sửa ô kích thước sai thứ tự (cao rộng) thành rộng X cao" % ten_f)
                        continue
                    t = Transaction(fd, u"Bỏ ô kích thước sai thứ tự")
                    t.Start()
                    try:
                        from System.Collections.Generic import List
                        ys_ = []
                        for c in net:
                            ys_ += [c.GeometryCurve.GetEndPoint(0).Y, c.GeometryCurve.GetEndPoint(1).Y]
                        ids = List[ElementId]()
                        for e_ in list(net) + sai:
                            ids.Add(e_.Id)
                        fd.Delete(ids)
                        mk.VerticalAlignment = getattr(type(mk.VerticalAlignment), "Middle")
                        mk.Coord = XYZ(mk.Coord.X, (max(ys_) + min(ys_)) / 2.0, mk.Coord.Z)
                        t.Commit()
                    except Exception:
                        if t.HasStarted() and not t.HasEnded():
                            t.RollBack()
                        raise
                    ket_qua.append(u"'%s': bỏ ô kích thước sai thứ tự (cao rộng)" % ten_f)
                if nhan_theo(fd, BIP_RONG) is not None:
                    # Đã thêm ô kích thước trước đó → chỉ chỉnh lại cỡ khung / chữ theo hằng số hiện hành (vd. bản 17 × 8 mm
                    # chạy trên model người dùng 2026-11-03 → bản gọn 14 × 7 mm, chữ 2 mm)
                    mk = nhan_theo(fd, ("ALL_MODEL_TYPE_MARK",))
                    net = khung_cua_tool(fd)
                    if mk is None or len(net) < 5:
                        continue
                    pts = []
                    for c in net:
                        pts += [c.GeometryCurve.GetEndPoint(0), c.GeometryCurve.GetEndPoint(1)]
                    xs_, ys_ = [q.X for q in pts], [q.Y for q in pts]
                    lt = fd.GetElement(mk.GetTypeId())
                    co_cu = lt.get_Parameter(BuiltInParameter.TEXT_SIZE).AsDouble() if lt is not None and \
                        lt.get_Parameter(BuiltInParameter.TEXT_SIZE) is not None else 0.0
                    if abs((max(xs_) - min(xs_)) - ft(KHUNG_RONG_MM)) < ft(0.05) and \
                            abs((max(ys_) - min(ys_)) - 2 * ft(KHUNG_O_MM)) < ft(0.05) and abs(co_cu - ft(CO_CHU_MM)) < ft(0.01) \
                            and nen_chu_dung(fd, mk):
                        continue
                    if dry:
                        ket_qua.append(u"'%s': sẽ chỉnh khung tag về %g × %g mm, chữ %g mm" % (
                            ten_f, KHUNG_RONG_MM, 2 * KHUNG_O_MM, CO_CHU_MM))
                        continue
                    t = Transaction(fd, u"Chỉnh cỡ khung tag")
                    t.Start()
                    try:
                        from System.Collections.Generic import List
                        cx, cy = (max(xs_) + min(xs_)) / 2.0, (max(ys_) + min(ys_)) / 2.0
                        view_mk = fd.GetElement(mk.OwnerViewId)
                        ids = List[ElementId]()
                        for c in net:
                            ids.Add(c.Id)
                        fd.Delete(ids)
                        o = ft(KHUNG_O_MM)
                        y2 = cy - o / 2.0
                        mk.VerticalAlignment = getattr(type(mk.VerticalAlignment), "Middle")
                        mk.Coord = XYZ(mk.Coord.X, cy + o / 2.0, mk.Coord.Z)
                        for lb in FilteredElementCollector(fd).OfClass(lop_nhan):
                            bs = [b_ for b_, _ in fmts(lb, fd)]
                            if lb.Id.Value == mk.Id.Value or not any(b_ in BIP_RONG + BIP_CAO for b_ in bs):
                                continue
                            lb.VerticalAlignment = getattr(type(lb.VerticalAlignment), "Middle")
                            if any(b_ in BIP_RONG for b_ in bs) and any(b_ in BIP_CAO for b_ in bs):
                                x_ = cx
                            elif any(b_ in BIP_RONG for b_ in bs):
                                x_ = cx - ft(KHE_X_MM)
                            else:
                                x_ = cx + ft(KHE_X_MM)
                            lb.Coord = XYZ(x_, y2, lb.Coord.Z)
                        for tn in FilteredElementCollector(fd).OfClass(TextNote):
                            if (tn.Text or u"").strip() == u"X":
                                tn.Coord = XYZ(cx, y2, tn.Coord.Z)
                        dat_co_chu(fd, mk)
                        ve_khung_2_o(fd, view_mk, mk, cx, cy)
                        t.Commit()
                    except Exception:
                        if t.HasStarted() and not t.HasEnded():
                            t.RollBack()
                        raise
                    fd.LoadFamily(doc, tuy_chon_nap(True))
                    ket_qua.append(u"'%s': chỉnh khung tag về %g × %g mm, chữ %g mm" % (
                        ten_f, KHUNG_RONG_MM, 2 * KHUNG_O_MM, CO_CHU_MM))
                    continue
                mk = nhan_theo(fd, ("ALL_MODEL_TYPE_MARK",))
                ng = tim_nguon(cat_id)
                cach, ten_ng = None, u""
                if "gop" in ng:
                    cach, ten_ng = "gop", ng["gop"][2]
                elif "rong" in ng and "cao" in ng:
                    cach, ten_ng = "ghep", u"%s + %s" % (ng["rong"][2], ng["cao"][2])
                elif "rong" in ng and "cao_x" in ng:
                    cach, ten_ng = "x", ng["rong"][2]
                if mk is None or cach is None:
                    ket_qua.append(u"'%s': không có %s để thêm ô rộng x cao – sửa tay: Edit Label thêm Width, "
                                   u"Height" % (ten_f, u"nhãn Type Mark" if mk is None else
                                               u"family tag cùng hạng mục có nhãn Width / Height"))
                    continue
                if dry:
                    ket_qua.append(u"'%s': sẽ thêm ô rộng x cao (nhãn từ '%s')" % (ten_f, ten_ng))
                    continue
                t = Transaction(fd, u"Thêm ô rộng x cao")
                t.Start()
                try:
                    # Nhãn "theo đơn vị dự án" trong family hiển thị theo đơn vị của chính file family → mm
                    u_ = fd.GetUnits()
                    fo = FormatOptions(UnitTypeId.Millimeters)
                    fo.Accuracy = 1.0
                    fo.UseDigitGrouping = False
                    u_.SetFormatOptions(SpecTypeId.Length, fo)
                    fd.SetUnits(u_)
                    view_mk = fd.GetElement(mk.OwnerViewId)
                    cx, cy = mk.Coord.X, tam_y(mk)
                    o = ft(KHUNG_O_MM)
                    y2 = cy - o / 2.0           # tâm ô dưới
                    khe = ft(KHE_X_MM)          # nửa bề rộng chữ "X" (mm giấy)

                    def dat(lb, x, canh):
                        lb.ChangeTypeId(mk.GetTypeId())
                        # kiểu enum căn lề của nhãn lấy theo giá trị đang có (tên lớp enum khác nhau giữa các bản API)
                        lb.HorizontalAlignment = getattr(type(lb.HorizontalAlignment), canh)
                        lb.VerticalAlignment = getattr(type(lb.VerticalAlignment), "Middle")
                        lb.Coord = XYZ(x, y2, lb.Coord.Z)

                    if cach == "gop":
                        dat(chep(ng["gop"], view_mk), cx, "Center")
                    else:
                        r_ = chep(ng["rong"], view_mk)
                        c_ = chep(ng["cao" if cach == "ghep" else "cao_x"], view_mk)
                        if cach == "ghep":
                            dat(r_, cx - khe, "Right")
                            dat(c_, cx + khe, "Left")
                            kx = kieu_chu_x(fd, mk)
                            if kx is not None:
                                op = TextNoteOptions(kx.Id)
                                op.HorizontalAlignment = HorizontalTextAlignment.Center
                                op.VerticalAlignment = VerticalTextAlignment.Middle
                                TextNote.Create(fd, view_mk.Id, XYZ(cx, y2, mk.Coord.Z), u"X", op)
                        else:
                            dat(r_, cx - ft(0.35), "Right")
                            dat(c_, cx + ft(0.35), "Left")
                    mk.VerticalAlignment = getattr(type(mk.VerticalAlignment), "Middle")
                    mk.Coord = XYZ(mk.Coord.X, cy + o / 2.0, mk.Coord.Z)
                    dat_co_chu(fd, mk)
                    ve_khung_2_o(fd, view_mk, mk, cx, cy)
                    t.Commit()
                except Exception:
                    if t.HasStarted() and not t.HasEnded():
                        t.RollBack()
                    raise
                fd.LoadFamily(doc, tuy_chon_nap(True))     # lấy tham số hiện khung mới của family
                ket_qua.append(u"'%s': đã thêm ô rộng X cao (mm), khung 2 ô (nhãn từ '%s')" % (ten_f, ten_ng))
            except Exception as ex:
                ket_qua.append(u"'%s': không thêm được ô rộng x cao (%s)"
                               % (ten_f, (u"%s" % ex).splitlines()[0][:150] if u"%s" % ex else u"?"))
    finally:
        for fd in da_mo:
            try:
                fd.Close(False)
            except Exception:
                pass
    if not ket_qua:
        return u""
    return u"Kích thước trên tag: " + u"; ".join(ket_qua)


def tuy_chon_dan():
    """CopyPasteOptions: trùng tên kiểu thì dùng kiểu của tài liệu đích, không hiện hộp thoại Duplicate Types."""
    import uuid
    ns = "ARV.TagCua.D" + uuid.uuid4().hex

    class _Trung(_RevitDB.IDuplicateTypeNamesHandler):
        __namespace__ = ns

        def OnDuplicateTypeNamesFound(self, args):
            return _RevitDB.DuplicateTypeAction.UseDestinationTypes

    op = CopyPasteOptions()
    op.SetDuplicateTypeNamesHandler(_Trung())
    return op


def tuy_chon_nap(ghi_de_tham_so=False):
    """IFamilyLoadOptions: ghi đè family đã có trong dự án; mặc định giữ giá trị tham số trong dự án (ghi_de_tham_so=True
    thì lấy giá trị tham số của family, vd. kích thước khung tag vừa đổi). Tên lớp .NET đặt riêng mỗi lần gọi vì
    pythonnet không cho định nghĩa lại cùng tên trong một phiên Revit."""
    import uuid
    ns = "ARV.TagCua.N" + uuid.uuid4().hex

    class _Nap(_RevitDB.IFamilyLoadOptions):
        __namespace__ = ns

        def OnFamilyFound(self, familyInUse, overwriteParameterValues):
            return (True, ghi_de_tham_so)

        def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
            return (True, _RevitDB.FamilySource.Family, ghi_de_tham_so)

    return _Nap()


TRUC_DU_MM_GIAY = 20.0      # đầu trục cách mép nhà (mm giấy) khi thu trục


def thu_truc(doc, view):
    """Thu trục về sát quanh nhà như mẫu người dùng (2026-11-03): đầu trục của file hiện tại trong view chuyển sang
    ViewSpecific và cắt theo khung bao tường của nhà + TRUC_DU_MM_GIAY × tỉ lệ. Không đổi trục 3D / view khác. Trục
    của link không sửa được (đã ẩn bằng filter)."""
    xs, ys = [], []
    for w in FilteredElementCollector(doc, view.Id).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType():
        bb = w.get_BoundingBox(view)
        if bb is not None:
            xs += [bb.Min.X, bb.Max.X]
            ys += [bb.Min.Y, bb.Max.Y]
    if not xs:
        return u"Không có tường trong view – không thu trục."
    goc_bb = [XYZ(x, y, 0) for x in (min(xs), max(xs)) for y in (min(ys), max(ys))]
    du = ft(TRUC_DU_MM_GIAY * view.Scale)
    n = 0
    for g in FilteredElementCollector(doc, view.Id).OfClass(Grid):
        try:
            if g.IsCurved:
                continue
            ds = g.GetCurvesInView(DatumExtentType.ViewSpecific, view)
            if ds is None or ds.Count != 1:
                continue
            cv = ds[0]
            p0, p1 = cv.GetEndPoint(0), cv.GetEndPoint(1)
            d = (p1 - p0).Normalize()
            ts = [(q.X - p0.X) * d.X + (q.Y - p0.Y) * d.Y for q in goc_bb]
            a, b = p0 + d * (min(ts) - du), p0 + d * (max(ts) + du)
            a, b = XYZ(a.X, a.Y, p0.Z), XYZ(b.X, b.Y, p1.Z)
            for dau in (DatumEnds.End0, DatumEnds.End1):
                if g.GetDatumExtentTypeInView(dau, view) != DatumExtentType.ViewSpecific:
                    g.SetDatumExtentType(dau, view, DatumExtentType.ViewSpecific)
            g.SetCurveInView(DatumExtentType.ViewSpecific, view, Line.CreateBound(a, b))
            n += 1
        except Exception:
            pass
    return u"Thu trục: %d trục cắt sát nhà (cách mép tường %g mm giấy)." % (n, TRUC_DU_MM_GIAY)


def an_truc_link(doc, tpl):
    """Ẩn trục của file link, giữ trục file hiện tại (người dùng yêu cầu 2026-11-03). API 2027.3 không tắt riêng hạng mục
    Grids của link theo view (RevitLinkGraphicsSettings không có chỉnh theo hạng mục) → filter Grids "Type Name khác mọi
    loại trục của file hiện tại", đặt ẩn trong template. Filter của view tác dụng lên phần tử link khi link hiển thị
    By Host View (mặc định). Link dùng cùng tên loại trục với file hiện tại thì không ẩn được."""
    from System.Collections.Generic import List
    loai_truc = sorted(set(ten(doc.GetElement(g.GetTypeId())) for g in FilteredElementCollector(doc).OfClass(Grid)))
    if not loai_truc:
        return u"File không có trục riêng – không tạo filter ẩn trục link."
    cats = List[ElementId]()
    cats.Add(ElementId(BuiltInCategory.OST_Grids))
    loc_duoc = [p_.Value for p_ in ParameterFilterUtilities.GetFilterableParametersInCommon(doc, cats)]
    pid = None
    for b_ in (BuiltInParameter.ALL_MODEL_TYPE_NAME, BuiltInParameter.SYMBOL_NAME_PARAM):
        if int(b_) in loc_duoc:
            pid = ElementId(b_)
            break
    if pid is None:
        return u"Không có tham số tên loại lọc được cho Grids – chưa ẩn trục link (ẩn tay: V/G → Revit Links → Custom)."
    f_ = None
    for x in FilteredElementCollector(doc).OfClass(ParameterFilterElement):
        if x.Name == TEN_FILTER_TRUC_LINK:
            f_ = x
    loc = [ElementParameterFilter(ParameterFilterRuleFactory.CreateNotEqualsRule(pid, t_)) for t_ in loai_truc]
    loc_net = List[ElementFilter]()
    for x in loc:
        loc_net.Add(x)
    bo = loc[0] if len(loc) == 1 else LogicalAndFilter(loc_net)
    if f_ is None:
        f_ = ParameterFilterElement.Create(doc, TEN_FILTER_TRUC_LINK, cats, bo)
    else:
        f_.SetElementFilter(bo)
    try:
        pf = ElementId(BuiltInParameter.VIS_GRAPHICS_FILTERS)
        nc = list(tpl.GetNonControlledTemplateParameterIds())
        if any(i.Value == pf.Value for i in nc):
            ds = List[ElementId]()
            for i in nc:
                if i.Value != pf.Value:
                    ds.Add(i)
            tpl.SetNonControlledTemplateParameterIds(ds)
    except Exception:
        pass
    if not any(i.Value == f_.Id.Value for i in tpl.GetFilters()):
        tpl.AddFilter(f_.Id)
    tpl.SetFilterVisibility(f_.Id, False)
    return u"Ẩn trục file link: filter '%s' (Grids, loại trục khác %s)." % (TEN_FILTER_TRUC_LINK, u", ".join(loai_truc))


def to_dac_id(doc):
    for fp in FilteredElementCollector(doc).OfClass(FillPatternElement):
        try:
            p_ = fp.GetFillPattern()
            if p_.IsSolidFill and p_.Target == FillPatternTarget.Drafting:
                return fp.Id
        except Exception:
            pass
    return None


def ghi_de_btct(dac):
    o = OverrideGraphicSettings()
    o.SetCutLineColor(Color(0, 0, 0))
    o.SetProjectionLineColor(Color(0, 0, 0))
    if dac is not None:
        o.SetCutForegroundPatternId(dac)
        o.SetCutForegroundPatternColor(Color(*MAU_TO_BTCT))
        o.SetCutForegroundPatternVisible(True)
    return o


def trinh_bay_btct(doc, tpl):
    """Tường xây chỉ nét xám không tô, cột + vách BTCT tô đặc xám đậm viền đen (như mẫu FPT, người dùng chốt 2026-11-03).
    Revit 2027.3 BỎ QUA màu nét ghi đè theo hạng mục Walls (đã thử: chỉ ăn ghi đè từng phần tử hoặc filter) → dùng 2 filter:
    TEN_FILTER_BTCT (Structural Usage khác Non-bearing hoặc tên loại chứa TU_KHOA_BTCT) và TEN_FILTER_XAY (phần còn lại,
    Halftone). Hạng mục Walls chỉ tắt mẫu tô mặt cắt. "Structural" (Yes / No) của tường không lọc được bằng filter.
    Chỉ làm một lần cho mỗi template: template đã có filter TEN_FILTER_BTCT thì giữ nguyên (người dùng có thể đã chỉnh tay).
    Filter của view tác dụng cả lên phần tử link kết cấu khi link hiển thị By Host View."""
    from System.Collections.Generic import List
    fs = {}
    for x in FilteredElementCollector(doc).OfClass(ParameterFilterElement):
        if x.Name in (TEN_FILTER_BTCT, TEN_FILTER_XAY, TEN_FILTER_COT):
            fs[x.Name] = x
    f_ = fs.get(TEN_FILTER_BTCT)
    if f_ is not None and any(i.Value == f_.Id.Value for i in tpl.GetFilters()):
        return u"Tường / cột / vách: template đã có filter '%s', giữ nguyên." % TEN_FILTER_BTCT
    dac = to_dac_id(doc)
    o = OverrideGraphicSettings()
    o.SetCutForegroundPatternVisible(False)
    o.SetCutBackgroundPatternVisible(False)
    tpl.SetCategoryOverrides(ElementId(BuiltInCategory.OST_Walls), o)
    cats = List[ElementId]()
    cats.Add(ElementId(BuiltInCategory.OST_Walls))
    loc_duoc = [p_.Value for p_ in ParameterFilterUtilities.GetFilterableParametersInCommon(doc, cats)]
    co, khong = [], []      # luật nhận BTCT / luật phủ định (tường xây = không khớp luật nào)
    b_kc = BuiltInParameter.WALL_STRUCTURAL_USAGE_PARAM
    if int(b_kc) in loc_duoc:
        co.append(ElementParameterFilter(ParameterFilterRuleFactory.CreateNotEqualsRule(ElementId(b_kc), 0)))
        khong.append(ElementParameterFilter(ParameterFilterRuleFactory.CreateNotEqualsRule(ElementId(b_kc), 0), True))
    b_ten = None
    for b_ in (BuiltInParameter.ALL_MODEL_TYPE_NAME, BuiltInParameter.SYMBOL_NAME_PARAM):
        if int(b_) in loc_duoc:
            b_ten = b_
            break
    for k in (TU_KHOA_BTCT if b_ten is not None else ()):
        r_ = ParameterFilterRuleFactory.CreateContainsRule(ElementId(b_ten), k)
        co.append(ElementParameterFilter(r_))
        khong.append(ElementParameterFilter(r_, True))
    if not co:
        return u"Không có tham số lọc được để nhận vách BTCT – chỉnh tay trong V/G."

    def gop(ds_, lop):
        if len(ds_) == 1:
            return ds_[0]
        net = List[ElementFilter]()
        for x in ds_:
            net.Add(x)
        return lop(net)

    def dat(ten_f, cats_, bo, ghi_de):
        f = fs.get(ten_f)
        if f is None:
            f = (ParameterFilterElement.Create(doc, ten_f, cats_, bo) if bo is not None
                 else ParameterFilterElement.Create(doc, ten_f, cats_))
        elif bo is not None:
            f.SetElementFilter(bo)
        if not any(i.Value == f.Id.Value for i in tpl.GetFilters()):
            tpl.AddFilter(f.Id)
        tpl.SetFilterOverrides(f.Id, ghi_de)

    dat(TEN_FILTER_BTCT, cats, gop(co, LogicalOrFilter), ghi_de_btct(dac))
    o = OverrideGraphicSettings()
    o.SetHalftone(True)
    dat(TEN_FILTER_XAY, cats, gop(khong, LogicalAndFilter), o)
    cats_cot = List[ElementId]()
    for n in COT_BTCT:
        cats_cot.Add(ElementId(getattr(BuiltInCategory, n)))
    dat(TEN_FILTER_COT, cats_cot, None, ghi_de_btct(dac))
    return (u"Tường xây Halftone, không tô (filter '%s'); vách BTCT (filter '%s': Structural Usage khác Non-bearing hoặc "
            u"tên loại chứa %s) + cột (filter '%s') tô đặc xám %s viền đen."
            % (TEN_FILTER_XAY, TEN_FILTER_BTCT, u" / ".join(TU_KHOA_BTCT), TEN_FILTER_COT, MAU_TO_BTCT))


KHONG_TPL = u"<Không dùng view template>"     # ô View template của hộp thoại = bỏ template


def tpl_khoa_tl(tpl):
    """Template điều khiển tỉ lệ (View Scale có trong template và đang được điều khiển)."""
    try:
        co = set(i.Value for i in tpl.GetTemplateParameterIds())
        nc = set(i.Value for i in tpl.GetNonControlledTemplateParameterIds())
    except Exception:
        return False
    for b in (BuiltInParameter.VIEW_SCALE_PULLDOWN_METRIC, BuiltInParameter.VIEW_SCALE):
        v = ElementId(b).Value
        if v in co and v not in nc:
            return True
    return False


def ap_tpl_tl(doc, view, ten_tpl, ti_le):
    """Gán view template + tỉ lệ chọn trong hộp thoại (2026-11-05), như sh_ap_tpl_tl của DatSheet_chung.py. Gọi TRONG
    transaction. Không tạo / sửa template."""
    bao = []
    ten_tpl = (ten_tpl or u"").strip()
    if ten_tpl == KHONG_TPL:
        if view.ViewTemplateId != ElementId.InvalidElementId:
            view.ViewTemplateId = ElementId.InvalidElementId
            bao.append(u"Bỏ view template của '%s'." % view.Name)
    elif ten_tpl:
        ds = [v for v in FilteredElementCollector(doc).OfClass(ViewPlan) if v.IsTemplate]
        tpl = ([v for v in ds if v.Name == ten_tpl] or [v for v in ds if khong_dau(v.Name) == khong_dau(ten_tpl)] or
               [None])[0]
        if tpl is None:
            bao.append(u"CẦN XEM LẠI: không có view template '%s' – giữ template đang có của '%s'." % (ten_tpl, view.Name))
        elif view.ViewTemplateId.Value != tpl.Id.Value:
            view.ViewTemplateId = tpl.Id
            bao.append(u"Gán view template '%s' cho '%s'." % (tpl.Name, view.Name))
    try:
        ti_le = int(round(float(ti_le or 0)))
    except Exception:
        ti_le = 0
    if ti_le > 0:
        tpl = doc.GetElement(view.ViewTemplateId) if view.ViewTemplateId != ElementId.InvalidElementId else None
        if tpl is not None and tpl_khoa_tl(tpl):
            if tpl.Scale != ti_le:
                bao.append(u"Template '%s' khoá tỉ lệ 1:%d → giữ 1:%d (không sửa template), không dùng 1:%d." % (
                    tpl.Name, tpl.Scale, tpl.Scale, ti_le))
        elif view.Scale != ti_le:
            view.Scale = ti_le
            bao.append(u"Tỉ lệ '%s': 1:%d." % (view.Name, ti_le))
    doc.Regenerate()
    return bao


def mb_dinh_vi_cua(doc, goc, dry, ten_tpl, mau_ten, ten_bic_an, tpl_chon=u"", ti_le=0):
    """Trả về (view để tag, [dòng báo cáo]). Xem khối chú thích đầu file (IN[16] – IN[18], IN[28] – IN[29]).
    2026-11-05 (người dùng yêu cầu): KHÔNG tạo / sửa view template (bỏ tạo template 'MẶT BẰNG ĐỊNH VỊ CỬA', ẩn hạng mục,
    filter trục link / tường / vách trong template). View gán template tpl_chon (chọn trong hộp thoại); trống thì view
    mới dùng template tên ten_tpl nếu có, không thì giữ template của view gốc."""
    bao = []
    ten_tpl = (ten_tpl or MAC_DINH[17]).strip()
    mau_ten = (mau_ten or MAC_DINH[18]).strip()
    tpl_chon = (tpl_chon or u"").strip()
    tpl_goc = doc.GetElement(goc.ViewTemplateId) if goc.ViewTemplateId != ElementId.InvalidElementId else None
    tien_to = mau_ten.split(u"{")[0].strip(u" -")
    if (tpl_goc is not None and tpl_goc.Name == ten_tpl) or (tien_to and goc.Name.startswith(tien_to)):
        moi = goc
    else:
        moi = None
    if goc.GenLevel is None or goc.ViewType != ViewType.FloorPlan:
        bao.append(u"View '%s' không phải mặt bằng tầng → tag ngay trên view này, không tạo mặt bằng định vị cửa." % goc.Name)
        return goc, bao
    ten_moi = mau_ten.replace(u"{tang}", goc.GenLevel.Name).replace(u"{view}", goc.Name).strip()
    co_ten_tpl = False
    for v in FilteredElementCollector(doc).OfClass(View):
        if v.IsTemplate and v.Name == ten_tpl:
            co_ten_tpl = True
        elif moi is None and not v.IsTemplate and v.ViewType == ViewType.FloorPlan and v.Name == ten_moi:
            moi = v
    if not tpl_chon and moi is None and co_ten_tpl:
        tpl_chon = ten_tpl
    if dry:
        if moi is None:
            bao.append(u"Sẽ tạo mặt bằng định vị cửa '%s' (nhân bản '%s') rồi tag trên đó – Dry-run thử tag trên "
                       u"view gốc." % (ten_moi, goc.Name))
        else:
            bao.append(u"Mặt bằng định vị cửa: '%s'." % moi.Name)
        bao.append(u"View template: %s, tỉ lệ: %s (không tạo / sửa template)." % (
            tpl_chon or u"giữ như hiện có", u"1:%d" % int(float(ti_le)) if ti_le else u"giữ"))
        return (moi or goc), bao
    TransactionManager.Instance.EnsureInTransaction(doc)
    if moi is None:
        moi = doc.GetElement(goc.Duplicate(ViewDuplicateOption.Duplicate))
        moi.Name = ten_moi
        bao.append(u"Tạo mặt bằng định vị cửa '%s' (nhân bản '%s', không kèm chú thích)." % (ten_moi, goc.Name))
        # Loại view riêng → Project Browser có mục "Floor Plans (MẶT BẰNG ĐỊNH VỊ CỬA)" (người dùng yêu cầu 2026-11-03)
        try:
            vft = None
            for t_ in FilteredElementCollector(doc).OfClass(ViewFamilyType):
                if t_.ViewFamily == ViewFamily.FloorPlan and ten(t_) == ten_tpl:
                    vft = t_
            if vft is None:
                vft = doc.GetElement(moi.GetTypeId()).Duplicate(ten_tpl)
                bao.append(u"Tạo loại view '%s' (mục riêng trong Project Browser)." % ten_tpl)
            if moi.GetTypeId().Value != vft.Id.Value:
                moi.ChangeTypeId(vft.Id)
        except Exception as ex:
            bao.append(u"Không gán được loại view '%s': %s" % (ten_tpl, (u"%s" % ex).splitlines()[0][:150]))
    else:
        bao.append(u"Mặt bằng định vị cửa: '%s'." % moi.Name)
    bao.extend(ap_tpl_tl(doc, moi, tpl_chon, ti_le))
    tpl = doc.GetElement(moi.ViewTemplateId) if moi.ViewTemplateId != ElementId.InvalidElementId else None
    for bic in (BuiltInCategory.OST_DoorTags, BuiltInCategory.OST_WindowTags):
        try:
            c = ElementId(bic)
            if (tpl if tpl is not None else moi).GetCategoryHidden(c):
                bao.append(u"CẦN XEM LẠI: %s đang ẩn %s – tag sẽ không hiện (công cụ không sửa template)." % (
                    u"template '%s'" % tpl.Name if tpl is not None else u"view", Category.GetCategory(doc, c).Name))
        except Exception:
            pass
    try:
        bao.append(thu_truc(doc, moi))
    except Exception as ex:
        bao.append(u"Không thu được trục: %s" % (u"%s" % ex).splitlines()[0][:150])
    TransactionManager.Instance.TransactionTaskDone()
    bao.append(u"View '%s': template %s, tỉ lệ 1:%d." % (moi.Name, u"'%s'" % tpl.Name if tpl is not None else u"(không)",
                                                         moi.Scale))
    if moi.Id.Value != goc.Id.Value:
        try:
            DocumentManager.Instance.CurrentUIDocument.RequestViewChange(moi)
        except Exception:
            pass
    return moi, bao


def gan_template(doc, view, ten_bic):
    """Gán view template '<gốc> (ẩn nội thất)' cho view: nhân bản template đang gán (không sửa bản gốc) hoặc tạo từ
    view nếu chưa có; ẩn các hạng mục nội thất. Template đã có thì dùng lại."""
    cats = []
    for n in ten_bic:
        try:
            cats.append(ElementId(getattr(BuiltInCategory, n)))
        except Exception:
            pass
    tpl_id = view.ViewTemplateId
    goc = doc.GetElement(tpl_id) if tpl_id != ElementId.InvalidElementId else None

    def da_an_du(t):
        """Template đã ẩn đủ các hạng mục nội thất (vd. 'MẶT BẰNG ĐỊNH VỊ CỬA') thì dùng luôn, không tạo bản mới."""
        try:
            pid = ElementId(BuiltInParameter.VIS_GRAPHICS_MODEL).Value
            if any(i.Value == pid for i in t.GetNonControlledTemplateParameterIds()):
                return False
            return all(t.GetCategoryHidden(c) or not t.CanCategoryBeHidden(c) for c in cats)
        except Exception:
            return False

    if goc is not None and (goc.Name.endswith(HAU_TO_TEMPLATE) or da_an_du(goc)):
        moi = goc
        thong_bao = u"View template '%s' đã gán sẵn" % goc.Name
    else:
        ten_moi = (goc.Name if goc is not None else view.Name) + HAU_TO_TEMPLATE
        moi = None
        for v in FilteredElementCollector(doc).OfClass(View):
            if v.IsTemplate and v.Name == ten_moi:
                moi = v
        if moi is not None:
            thong_bao = u"Gán view template có sẵn '%s'" % ten_moi
        else:
            # View template không Duplicate được qua API → tạo từ view (view đang hiển thị đúng theo template gốc)
            moi = view.CreateViewTemplate()
            moi.Name = ten_moi
            thong_bao = u"Tạo view template '%s' (từ %s)" % (ten_moi, u"template '%s'" % goc.Name if goc else u"view")
    # Template phải điều khiển V/G hạng mục model thì việc ẩn mới có tác dụng
    try:
        pid = ElementId(BuiltInParameter.VIS_GRAPHICS_MODEL)
        nc = list(moi.GetNonControlledTemplateParameterIds())
        if any(i.Value == pid.Value for i in nc):
            from System.Collections.Generic import List
            ds = List[ElementId]()
            for i in nc:
                if i.Value != pid.Value:
                    ds.Add(i)
            moi.SetNonControlledTemplateParameterIds(ds)
    except Exception:
        pass
    an = []
    for c in cats:
        try:
            if moi.CanCategoryBeHidden(c) and not moi.GetCategoryHidden(c):
                moi.SetCategoryHidden(c, True)
            an.append(Category.GetCategory(doc, c).Name)
        except Exception:
            pass
    for bic in (BuiltInCategory.OST_DoorTags, BuiltInCategory.OST_WindowTags):
        try:
            if moi.GetCategoryHidden(ElementId(bic)):
                moi.SetCategoryHidden(ElementId(bic), False)
        except Exception:
            pass
    if view.ViewTemplateId.Value != moi.Id.Value:
        view.ViewTemplateId = moi.Id
    return thong_bao + u", ẩn: " + u", ".join(an)


try:
    OUT = _chinh()
except Exception:
    OUT = [u"LỖI:", traceback.format_exc()]
