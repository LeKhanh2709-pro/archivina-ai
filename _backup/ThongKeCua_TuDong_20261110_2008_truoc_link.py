# Bảng thống kê cửa của mặt bằng đang mở (người dùng yêu cầu 2026-11-04: "tạo 1 bảng thống kê các cửa có trong mặt bằng
# đó, những cửa trùng thì hiện 1 lần"):
#   - Mỗi hạng mục 1 bảng: "THỐNG KÊ CỬA ĐI - <tầng>", "THỐNG KÊ CỬA SỔ - <tầng>" (Revit không gộp được cửa đi + cửa sổ
#     vào 1 bảng: bảng nhiều hạng mục không có cột Rộng / Cao và bộ lọc không có "hoặc" – khảo sát Revit 2027.3).
#   - Cột: Ký hiệu (Type Mark) / Rộng / Cao / Số lượng; KHÔNG liệt kê từng cái (Itemize tắt), gộp theo Type Mark → cửa
#     trùng ký hiệu hiện 1 dòng kèm số lượng; dòng tổng cuối bảng.
#   - Lọc: Level = tầng của mặt bằng, bỏ cửa có Type Comments CHỨA chữ loại trừ (Louver, Lam thép, Lam nhôm; không phân biệt hoa
#     thường / dấu, vd. "Louver", "LOUVER nhôm", "CỬA LAM THÉP LOGIA CĂN HỘ" – người dùng yêu cầu 2026-11-09; bảng Revit
#     dùng bộ lọc "does not contain", thêm cả dạng HOA / thường vì bộ lọc này phân biệt). "Filter by sheet" TẮT mặc định (bật thì bảng đặt
#     trên sheet không có mặt bằng sẽ trống – thử 2026-11-04); mặt bằng crop 1 phần tầng thì bật IN[6] rồi đặt bảng lên
#     sheet của mặt bằng đó để bảng chỉ đếm cửa thấy trên sheet.
#   - Bảng cùng tên đã có (bấm lại) thì cập nhật lại cột / lọc / gộp, không tạo trùng, không xoá. Chưa có thì nhân bản
#     bảng cùng hạng mục có sẵn của dự án (giữ kiểu trình bày công ty), không có thì tạo mới.
#   - Đổi tên cửa (người dùng yêu cầu 2026-11-04 tối: "1 bảng hiện ra, có các cửa, tên hiện tại, tên đổi, chiều dài,
#     chiều cao"): nút bật bảng lib\arv_bang_cua.py (mỗi loại cửa thấy trong mặt bằng 1 dòng), người dùng gõ tên mới →
#     IN[7] = JSON {id type: tên mới} → đổi Type Mark của type đó (áp cho mọi cửa cùng type trong dự án). Làm TRƯỚC
#     bảng thống kê để bảng hiện tên mới. IN[8] = có tạo / cập nhật bảng thống kê Revit không.
#   - Báo CẦN XEM LẠI: cửa chưa có Type Mark, cùng Type Mark mà khác kích thước (Revit để trống ô), số cửa thấy trong
#     mặt bằng khác số cửa của tầng.
# Dry-run chỉ báo cáo, không sửa mô hình.
# INPUT
#   IN[0] (str)  Tên view mặt bằng (để trống = view đang mở)
#   IN[1] (str)  Hạng mục thống kê: Cửa đi;Cửa sổ (bỏ bớt nếu chỉ cần 1 bảng)
#   IN[2] (str)  Type Comments CÓ CHỨA chữ này thì KHÔNG thống kê (vd. Louver;Lam thép;Lam nhôm), cách nhau bằng ;
#   IN[3] (bool) Dry-run (True = chỉ báo cáo)
#   IN[4] (str)  Mẫu tên bảng ({loai} = CỬA ĐI / CỬA SỔ, {tang} = tên tầng, {view} = tên view)
#   IN[5] (bool) Mở bảng vừa tạo (bảng đầu tiên)
#   IN[6] (bool) Chỉ đếm cửa thấy trên sheet đặt bảng (Filter by sheet; dùng cho mặt bằng crop 1 phần tầng)
#   IN[7] (str)  Đổi tên cửa: JSON {"<id type>": "<Type Mark mới>"} (trống = không đổi; nút điền từ bảng cửa)
#   IN[8] (bool) Tạo / cập nhật bảng thống kê Revit (THỐNG KÊ CỬA ĐI / CỬA SỔ - <tầng>)
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

TRANSACTION_NAME = u"ARV - Thống kê cửa"
MAC_DINH = ["", u"Cửa đi;Cửa sổ", u"Louver;Lam thép;Lam nhôm", True, u"THỐNG KÊ {loai} - {tang}", True, False, "", True]
# (từ khoá không dấu nhận trong IN[1], hạng mục, nhãn, tham số rộng, tham số cao)
HANG_MUC = [(u"cua di", BuiltInCategory.OST_Doors, u"CỬA ĐI", BuiltInParameter.DOOR_WIDTH, BuiltInParameter.DOOR_HEIGHT),
            (u"cua so", BuiltInCategory.OST_Windows, u"CỬA SỔ", BuiltInParameter.WINDOW_WIDTH,
             BuiltInParameter.WINDOW_HEIGHT)]
COT = [u"Tên", u"Chiều dài", u"Chiều cao", u"Số lượng"]


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


def mm(v):
    return UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.Millimeters)


def ten(e):
    try:
        return Element.Name.GetValue(e)
    except Exception:
        try:
            return e.Name
        except Exception:
            return "?"


def gia_tri_kt(e, t, bips):
    """Kích thước (mm) lấy ở instance trước, không có thì ở type."""
    for o in (e, t):
        if o is None:
            continue
        for b in bips:
            p = o.get_Parameter(b)
            if p is not None and p.HasValue and p.StorageType == StorageType.Double:
                return int(round(mm(p.AsDouble())))
    return None


def chuoi_type(t, bip):
    p = t.get_Parameter(bip) if t is not None else None
    return (p.AsString() or u"").strip() if p is not None else u""


def co_chu(s, ds):
    """s CÓ CHỨA một chữ trong ds (ds đã khong_dau) – không phân biệt hoa thường / dấu."""
    ks = khong_dau(s)
    return bool(ks) and any(k in ks for k in ds)


# ==== PHẦN CHUNG FILE LINK (nguồn: Link_chung.py, chép vào công cụ bằng gop_link.py – không sửa tay trong công cụ) ====
# Model chỉ chứa link (vd. HQV Site: tường / cửa / WC đều nằm trong các file link): công cụ đọc đối tượng link qua LkPT, là
# lớp bọc trả toạ độ đã đổi về model chính và chuyển mọi thuộc tính khác cho phần tử gốc. Phần tử trong link chỉ ĐỌC được.
LK_HE_SO_ID = 10000000000      # id giả = id link instance × hệ số + id phần tử, không trùng giữa các link


def _lk_mm(v):
    return UnitUtils.ConvertToInternalUnits(v, UnitTypeId.Millimeters)


class LkId(object):
    """Id giả của phần tử link: có .Value như ElementId, dùng làm khoá và để in."""
    def __init__(self, v):
        self.Value = v

    def __eq__(self, o):
        return getattr(o, "Value", None) == self.Value

    def __ne__(self, o):
        return not self.__eq__(o)

    def __hash__(self):
        return hash(self.Value)

    def __str__(self):
        return "%d" % self.Value


class _LkViTri(object):
    """Location của phần tử link, đã đổi về toạ độ model chính."""
    def __init__(self, pt):
        self._pt = pt
        self._loc = pt._e.Location

    @property
    def Point(self):
        return self._pt._tf.OfPoint(self._loc.Point)

    @property
    def Curve(self):
        return self._loc.Curve.CreateTransformed(self._pt._tf)

    @property
    def Rotation(self):
        return self._loc.Rotation

    def get_ElementsAtJoin(self, i):
        return [LkPT(x, self._pt._li, self._pt._tf) for x in self._loc.get_ElementsAtJoin(i)]


class _LkDoanBien(object):
    """BoundarySegment của room link: GetCurve đã đổi toạ độ."""
    def __init__(self, sg, tf):
        self._sg, self._tf = sg, tf

    def GetCurve(self):
        return self._sg.GetCurve().CreateTransformed(self._tf)


class LkPT(object):
    """Phần tử trong file link nhìn như phần tử model chính (chỉ đọc). Thuộc tính không khai báo ở đây lấy từ phần tử gốc."""
    def __init__(self, e, li, tf=None):
        self._e = e
        self._li = li
        self._tf = tf if tf is not None else li.GetTotalTransform()

    def __getattr__(self, ten_tt):
        return getattr(self._e, ten_tt)

    @property
    def Id(self):
        return LkId(self._li.Id.Value * LK_HE_SO_ID + self._e.Id.Value)

    @property
    def Location(self):
        return _LkViTri(self) if self._e.Location is not None else None

    @property
    def HandOrientation(self):
        return self._tf.OfVector(self._e.HandOrientation)

    @property
    def FacingOrientation(self):
        return self._tf.OfVector(self._e.FacingOrientation)

    @property
    def Orientation(self):
        return self._tf.OfVector(self._e.Orientation)

    @property
    def Host(self):
        h = self._e.Host
        return LkPT(h, self._li, self._tf) if h is not None else None

    def GetPath(self):
        return [c.CreateTransformed(self._tf) for c in self._e.GetPath()]

    def get_BoundingBox(self, view=None):
        bb = self._e.get_BoundingBox(None)
        if bb is None:
            return None
        ds = [self._tf.OfPoint(XYZ(x, y, z)) for x in (bb.Min.X, bb.Max.X) for y in (bb.Min.Y, bb.Max.Y)
              for z in (bb.Min.Z, bb.Max.Z)]
        kq = BoundingBoxXYZ()
        kq.Min = XYZ(min(p.X for p in ds), min(p.Y for p in ds), min(p.Z for p in ds))
        kq.Max = XYZ(max(p.X for p in ds), max(p.Y for p in ds), max(p.Z for p in ds))
        return kq

    def get_Geometry(self, opt):
        """Hình học đã đổi toạ độ. Có view thì lấy theo mặt bằng cùng tầng trong file link (để có nét 2D: cánh mở, ký hiệu)."""
        o = Options()
        try:
            o.IncludeNonVisibleObjects = opt.IncludeNonVisibleObjects
            o.ComputeReferences = opt.ComputeReferences
        except Exception:
            pass
        vm = lk_view_tang(self._e, self._tf) if getattr(opt, "View", None) is not None else None
        if vm is not None:
            o.View = vm
        else:
            try:
                o.DetailLevel = opt.DetailLevel if getattr(opt, "View", None) is None else ViewDetailLevel.Fine
            except Exception:
                o.DetailLevel = ViewDetailLevel.Fine
        g = self._e.get_Geometry(o)
        return g.GetTransformed(self._tf) if g is not None else None

    def GetBoundarySegments(self, opt):
        kq = self._e.GetBoundarySegments(opt)
        return [[_LkDoanBien(s, self._tf) for s in vong] for vong in kq] if kq is not None else None

    @property
    def GeometryCurve(self):
        return self._e.GeometryCurve.CreateTransformed(self._tf)

    def IsPointInRoom(self, p):
        return self._e.IsPointInRoom(self._tf.Inverse.OfPoint(p))

    def IsHidden(self, view):
        return False

    def CanBeHidden(self, view):
        return False


def la_link(e):
    return isinstance(e, LkPT)


def lk_tham_chieu(e):
    """Reference để tag / dim: phần tử link thì là link reference."""
    return Reference(e._e).CreateLinkReference(e._li) if la_link(e) else Reference(e)


def lk_cac_link(doc, view):
    """Các link đã nạp và đang thấy trong view: [(instance, document, transform)]."""
    kq = []
    for li in FilteredElementCollector(doc, view.Id).OfClass(RevitLinkInstance):
        try:
            ld = li.GetLinkDocument()
            if ld is not None:
                kq.append((li, ld, li.GetTotalTransform()))
        except Exception:
            pass
    return kq


def lk_level_khop(ld, tf, lv):
    """Id level của file link trùng cao độ với level lv của model chính (đã tính link đặt lệch cao độ, vd. tầng điển hình)."""
    return set(l.Id.Value for l in FilteredElementCollector(ld).OfClass(Level)
               if abs(l.Elevation + tf.Origin.Z - lv.Elevation) < _lk_mm(5))


_LK_VIEW = {}


def lk_view_tang(e, tf):
    """Mặt bằng trong file link cùng level của e (để đọc nét 2D của family); không có thì None."""
    ld = e.Document
    k = (ld.PathName or ld.Title, e.LevelId.Value)
    if k not in _LK_VIEW:
        ds = [v for v in FilteredElementCollector(ld).OfClass(ViewPlan)
              if not v.IsTemplate and v.ViewType == ViewType.FloorPlan and v.GenLevel is not None
              and v.GenLevel.Id == e.LevelId]
        ds.sort(key=lambda v: v.Id.Value)
        _LK_VIEW[k] = ds[0] if ds else None
    return _LK_VIEW[k]


def lk_tren_level(e, ids, tf=None, lv=None):
    """Phần tử e (trong link) thuộc các level ids? LevelId rỗng thì xét tham số level, host, cuối cùng theo cao độ."""
    if e.LevelId.Value in ids:
        return True
    if e.LevelId != ElementId.InvalidElementId:
        return False
    for bip in (BuiltInParameter.INSTANCE_SCHEDULE_ONLY_LEVEL_PARAM, BuiltInParameter.FAMILY_LEVEL_PARAM,
                BuiltInParameter.STAIRS_RAILING_BASE_LEVEL_PARAM):
        try:
            p = e.get_Parameter(bip)
            if p is not None and p.HasValue:
                return p.AsElementId().Value in ids
        except Exception:
            pass
    try:
        if e.Host is not None and e.Host.LevelId.Value in ids:
            return True
    except Exception:
        pass
    if tf is not None and lv is not None:
        bb = e.get_BoundingBox(None)
        if bb is not None:
            z = bb.Min.Z + tf.Origin.Z
            return lv.Elevation - _lk_mm(300) <= z <= lv.Elevation + _lk_mm(2000)
    return False


def lk_thay(doc, view, bic, theo_level=True):
    """Đối tượng hạng mục bic trong các link đang thấy trong view (đúng tầng của view khi theo_level) → list[LkPT]."""
    kq = []
    lv = view.GenLevel
    for li, ld, tf in lk_cac_link(doc, view):
        ids = lk_level_khop(ld, tf, lv) if theo_level and lv is not None else None
        if theo_level and not ids:
            continue
        for e in FilteredElementCollector(doc, view.Id, li.Id).OfCategory(bic).WhereElementIsNotElementType():
            if ids is None or lk_tren_level(e, ids, tf, lv):
                kq.append(LkPT(e, li, tf))
    return kq


def lk_tang(doc, view, bic):
    """Như lk_thay nhưng không lọc theo view (kể cả đối tượng view không vẽ, vd. room) – chỉ trong link đang thấy, đúng tầng."""
    kq = []
    lv = view.GenLevel
    for li, ld, tf in lk_cac_link(doc, view):
        ids = lk_level_khop(ld, tf, lv)
        if not ids:
            continue
        for e in FilteredElementCollector(ld).OfCategory(bic).WhereElementIsNotElementType():
            if lk_tren_level(e, ids, tf, lv):
                kq.append(LkPT(e, li, tf))
    return kq


def lk_room_tai_diem(doc, view, p):
    """Room trong link tại điểm p (toạ độ model chính) → LkPT hoặc None."""
    for li, ld, tf in lk_cac_link(doc, view):
        try:
            r = ld.GetRoomAtPoint(tf.Inverse.OfPoint(p))
        except Exception:
            r = None
        if r is not None:
            return LkPT(r, li, tf)
    return None


def lk_khoa_tag(tg):
    """Khoá các đối tượng mà tag đang gắn (phần tử model chính: id; phần tử link: id giả như LkPT.Id)."""
    kq = []
    for x in tg.GetTaggedElementIds():
        if x.LinkInstanceId != ElementId.InvalidElementId:
            kq.append(x.LinkInstanceId.Value * LK_HE_SO_ID + x.LinkedElementId.Value)
        else:
            kq.append(x.HostElementId.Value)
    return kq


def lk_ghi_chu(doc, view):
    """Một dòng báo cáo: các link đang thấy trong view + số link khớp tầng."""
    ds = lk_cac_link(doc, view)
    lv = view.GenLevel
    khop = [li.Name.split(" : ")[0] for li, ld, tf in ds if lv is not None and lk_level_khop(ld, tf, lv)]
    return "File link thấy trong view: %d, khớp tầng: %s" % (len(ds), ", ".join(sorted(set(khop))) or "(không)")
# ==== HẾT PHẦN CHUNG FILE LINK ====


def dem_trong_view(doc, view, bic, rong_bip, cao_bip, loai_tru):
    """Cửa thấy trong mặt bằng: {Type Mark: {"so": n, "kt": set((rộng, cao)), "type": set(tên)}}, số bị loại, các Type
    Comments bị loại, số khác tầng (thấy trong view nhưng Level khác tầng → bảng không đếm)."""
    lv = view.GenLevel
    nhom, bo, bo_tc, khac_tang = {}, 0, set(), []
    for e in list(FilteredElementCollector(doc, view.Id).OfCategory(bic).WhereElementIsNotElementType()) + lk_thay(doc, view, bic, True):
        t = e.Document.GetElement(e.GetTypeId())
        tc = chuoi_type(t, BuiltInParameter.ALL_MODEL_TYPE_COMMENTS)
        if co_chu(tc, loai_tru):
            bo += 1
            bo_tc.add(tc)
            continue
        if lv is not None and not la_link(e) and e.LevelId != lv.Id:
            khac_tang.append(e)
            continue
        mk = chuoi_type(t, BuiltInParameter.ALL_MODEL_TYPE_MARK)
        g = nhom.setdefault(mk, {"so": 0, "kt": set(), "type": set()})
        g["so"] += 1
        g["kt"].add((gia_tri_kt(e, t, (rong_bip, BuiltInParameter.FAMILY_WIDTH_PARAM)),
                     gia_tri_kt(e, t, (cao_bip, BuiltInParameter.FAMILY_HEIGHT_PARAM))))
        g["type"].add(u"%s : %s" % (t.FamilyName if t is not None else u"?", ten(t)))
    return nhom, bo, bo_tc, khac_tang


def dem_theo_tang(doc, lv, bic, loai_tru, view=None):
    n = 0
    for e in (lk_tang(doc, view, bic) if view is not None else []):
        if not co_chu(chuoi_type(e.Document.GetElement(e.GetTypeId()), BuiltInParameter.ALL_MODEL_TYPE_COMMENTS), loai_tru):
            n += 1
    for e in FilteredElementCollector(doc).OfCategory(bic).WhereElementIsNotElementType():
        if e.LevelId != lv.Id:
            continue
        t = doc.GetElement(e.GetTypeId())
        if co_chu(chuoi_type(t, BuiltInParameter.ALL_MODEL_TYPE_COMMENTS), loai_tru):
            continue
        n += 1
    return n


def lap_bang(doc, bic, ten_bang, level, loai_tru_tc, rong_bip, cao_bip, theo_sheet=False):
    """Tạo / cập nhật bảng thống kê 1 hạng mục: cột Ký hiệu / Rộng / Cao / Số lượng, gộp theo Type Mark, lọc Level +
    Type Comments. Trả về (bảng, cách làm)."""
    vs = None
    for x in FilteredElementCollector(doc).OfClass(ViewSchedule):
        if not x.IsTemplate and x.Name == ten_bang:
            vs = x
            break
    if vs is not None:
        if vs.Definition.CategoryId.Value != int(bic):
            raise Exception(u"đã có bảng tên '%s' nhưng khác hạng mục – đổi tên bảng đó hoặc đổi mẫu tên" % ten_bang)
        cach = u"cập nhật bảng đã có"
    else:
        nguon = [x for x in FilteredElementCollector(doc).OfClass(ViewSchedule)
                 if not x.IsTemplate and not x.IsTitleblockRevisionSchedule and not x.IsInternalKeynoteSchedule
                 and x.Definition.CategoryId.Value == int(bic)]
        nguon.sort(key=lambda x: (0 if u"thong ke" in khong_dau(x.Name) else 1, x.Name))
        vs = None
        if nguon:
            try:
                vs = doc.GetElement(nguon[0].Duplicate(ViewDuplicateOption.Duplicate))
                cach = u"nhân bản kiểu trình bày của '%s'" % nguon[0].Name
            except Exception:
                vs = None
        if vs is None:
            vs = ViewSchedule.CreateSchedule(doc, ElementId(bic))
            cach = u"tạo mới"
        vs.Name = ten_bang
    d = vs.Definition
    co = {}
    for i in range(d.GetFieldCount()):
        f = d.GetField(i)
        if str(f.FieldType) == "Count":
            co.setdefault(("count", None), f)
            continue
        try:
            co.setdefault(("pid", f.ParameterId.Value), f)
        except Exception:
            pass

    def lay(bip):
        k = ("pid", int(bip))
        if k in co:
            return co[k]
        for sf in d.GetSchedulableFields():
            try:
                if str(sf.FieldType) != "Count" and sf.ParameterId.Value == int(bip):
                    co[k] = d.AddField(sf)
                    return co[k]
            except Exception:
                pass
        return None

    f_mark = lay(BuiltInParameter.ALL_MODEL_TYPE_MARK)
    f_rong = lay(rong_bip) or lay(BuiltInParameter.FAMILY_WIDTH_PARAM)
    f_cao = lay(cao_bip) or lay(BuiltInParameter.FAMILY_HEIGHT_PARAM)
    f_dem = co.get(("count", None))
    if f_dem is None:
        for sf in d.GetSchedulableFields():
            if str(sf.FieldType) == "Count":
                f_dem = d.AddField(sf)
                break
    f_tang = lay(BuiltInParameter.FAMILY_LEVEL_PARAM) or lay(BuiltInParameter.SCHEDULE_LEVEL_PARAM)
    f_tc = lay(BuiltInParameter.ALL_MODEL_TYPE_COMMENTS)
    if f_mark is None or f_dem is None:
        raise Exception(u"không thêm được cột Type Mark / Count vào bảng")
    hien = [(f_mark, COT[0]), (f_rong, COT[1]), (f_cao, COT[2]), (f_dem, COT[3])]
    ids_hien = [g.FieldId for g, _ in hien if g is not None]
    for i in range(d.GetFieldCount()):
        f = d.GetField(i)
        f.IsHidden = not any(f.FieldId == x for x in ids_hien)
    for f, nhan in hien:
        if f is not None:
            f.ColumnHeading = nhan
    try:
        f_dem.DisplayType = ScheduleFieldDisplayType.Totals
    except Exception:
        pass
    try:
        from System.Collections.Generic import List
        thu_tu = List[ScheduleFieldId]()
        for x in ids_hien:
            thu_tu.Add(x)
        for i in range(d.GetFieldCount()):
            f = d.GetField(i)
            if not any(f.FieldId == x for x in ids_hien):
                thu_tu.Add(f.FieldId)
        d.SetFieldOrder(thu_tu)
    except Exception:
        pass
    d.ClearFilters()
    if f_tang is not None and level is not None:
        d.AddFilter(ScheduleFilter(f_tang.FieldId, ScheduleFilterType.Equal, level.Id))
    if f_tc is not None:
        # Bộ lọc bảng Revit phân biệt HOA / thường và mỗi bảng tối đa 8 bộ lọc (thử 2026-11-09) → bỏ chữ cái đầu của từ khoá
        # (khỏi lo "Lam" / "lam"), còn 2 dạng thường + HOA: 3 từ khoá = 6 bộ lọc, cộng 1 lọc tầng
        chu_loc = []
        for tc in loai_tru_tc:
            goc = tc[1:] if len(tc) > 3 else tc
            for x in (goc, goc.lower(), goc.upper()):
                if x not in chu_loc:
                    chu_loc.append(x)
        con_cho = 8 - d.GetFilterCount()
        for x in chu_loc[:con_cho]:     # "does not contain": Type Comments có chữ này ở bất kỳ đâu đều bị bỏ
            d.AddFilter(ScheduleFilter(f_tc.FieldId, ScheduleFilterType.NotContains, x))
        if len(chu_loc) > con_cho:
            cach += u"; CẦN XEM LẠI: quá 8 bộ lọc của bảng Revit, chưa lọc được: " + u", ".join(chu_loc[con_cho:])
    d.ClearSortGroupFields()
    d.AddSortGroupField(ScheduleSortGroupField(f_mark.FieldId))
    d.IsItemized = False                # gộp: cửa trùng Type Mark → 1 dòng
    for ten_tt, gt in (("ShowTitle", True), ("ShowHeaders", True), ("ShowGrandTotal", True),
                       ("ShowGrandTotalTitle", True), ("ShowGrandTotalCount", False), ("GrandTotalTitle", u"TỔNG")):
        try:
            setattr(d, ten_tt, gt)
        except Exception:
            pass
    try:
        if d.IsValidCategoryForFilterBySheet() and d.IsFilteredBySheet != bool(theo_sheet):
            d.IsFilteredBySheet = bool(theo_sheet)
    except Exception:
        pass
    return vs, cach


def doc_bang(vs):
    """Nội dung bảng như hiển thị (đọc lại sau khi tạo)."""
    dong = []
    try:
        sec = vs.GetTableData().GetSectionData(SectionType.Body)
        for r in range(sec.NumberOfRows):
            o = [vs.GetCellText(SectionType.Body, r, c) for c in range(sec.NumberOfColumns)]
            if any(x.strip() for x in o):
                dong.append(u" | ".join(o))
    except Exception as ex:
        dong.append(u"(không đọc được nội dung bảng: %s)" % ex)
    return dong


def doi_ten(doc, json_doi, dry, bao, xem_lai):
    """Đổi Type Mark theo JSON {id type: tên mới}. Báo từng dòng; tên mới trùng Type Mark của type khác cùng hạng mục thì
    vẫn đổi (người dùng đã xác nhận trong bảng) nhưng ghi CẦN XEM LẠI."""
    import json
    if not json_doi:
        return
    try:
        doi = json.loads(json_doi)
    except Exception as ex:
        bao.append(u"IN[7] không phải JSON hợp lệ: %s" % ex)
        return
    if not doi:
        bao.append(u"Không có tên cửa nào cần đổi.")
        return
    bao.append(u"")
    bao.append(u"== ĐỔI TÊN CỬA (Type Mark) – %d loại%s" % (len(doi), u" (DRY-RUN)" if dry else u""))
    if not dry:
        TransactionManager.Instance.EnsureInTransaction(doc)
    for k, moi in doi.items():
        moi = (u"%s" % moi).strip()
        try:
            t = doc.GetElement(ElementId(int(k)))
        except Exception:
            t = None
        if t is None or not moi:
            bao.append(u"   bỏ qua id %s: không có loại cửa này / tên trống" % k)
            continue
        p = t.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)
        cu = (p.AsString() or u"") if p is not None else u""
        so = sum(1 for e in FilteredElementCollector(doc).OfCategoryId(t.Category.Id).WhereElementIsNotElementType()
                 if e.GetTypeId().Value == t.Id.Value)
        nhan = u"%s : %s" % (getattr(t, "FamilyName", u""), ten(t))
        if p is None or p.IsReadOnly:
            bao.append(u"   KHÔNG đổi được '%s' (%s): Type Mark chỉ đọc" % (cu, nhan))
            continue
        trung = [u"%s : %s" % (getattr(x, "FamilyName", u""), ten(x))
                 for x in FilteredElementCollector(doc).OfCategoryId(t.Category.Id).WhereElementIsElementType()
                 if x.Id.Value != t.Id.Value and chuoi_type(x, BuiltInParameter.ALL_MODEL_TYPE_MARK) == moi
                 and (u"%s" % x.Id.Value) not in doi]
        if trung:
            xem_lai.append(u"Tên mới '%s' của %s trùng loại cửa khác: %s – bảng thống kê gộp chung 1 dòng." % (
                moi, nhan, u"; ".join(trung[:3])))
        if not dry:
            p.Set(moi)
        bao.append(u"   %s → %s  (%s, %d cửa trong dự án)" % (cu or u"(trống)", moi, nhan, so))
    if not dry:
        doc.Regenerate()


def _chinh():
    doc = DocumentManager.Instance.CurrentDBDocument
    bao = []
    ten_view = doc_in(0)
    if ten_view:
        ung = [v for v in FilteredElementCollector(doc).OfClass(ViewPlan) if not v.IsTemplate and v.Name == ten_view]
        ung.sort(key=lambda v: 0 if v.ViewType == ViewType.FloorPlan else 1)
        av = doc.ActiveView
        if av is not None and any(v.Id.Value == av.Id.Value for v in ung):
            ung = [av]
        view = ung[0] if ung else None
        if view is None:
            return [u"Không có view mặt bằng tên '%s'." % ten_view]
    else:
        view = doc.ActiveView
    if view is None or view.ViewType not in (ViewType.FloorPlan, ViewType.EngineeringPlan, ViewType.AreaPlan) \
            or view.GenLevel is None:
        return [u"View '%s' không phải mặt bằng tầng. Mở mặt bằng cần thống kê rồi chạy lại." % (ten(view) if view else "-")]
    lv = view.GenLevel
    dry = bool(doc_in(3))
    loai_tru = tach(doc_in(2))
    loai_tru_thuong = [khong_dau(x) for x in loai_tru]
    chon = [khong_dau(x) for x in tach(doc_in(1))]
    hang_muc = [h for h in HANG_MUC if any(h[0] in c for c in chon)]
    if not hang_muc:
        return [u"IN[1] không có hạng mục nào nhận được (Cửa đi / Cửa sổ)."]
    bao.append(u"Mặt bằng: %s – tầng %s%s" % (view.Name, lv.Name, u" (DRY-RUN: chỉ báo cáo)" if dry else u""))
    mau = doc_in(4) or MAC_DINH[4]
    xem_lai = []
    bang_tao = []
    doi_ten(doc, doc_in(7), dry, bao, xem_lai)
    lam_bang = bool(doc_in(8))
    if not lam_bang:
        hang_muc = []
        bao.append(u"Không tạo bảng thống kê Revit (IN[8] tắt).")
    for _, bic, nhan, rong_bip, cao_bip in hang_muc:
        nhom, bo, bo_tc, khac_tang = dem_trong_view(doc, view, bic, rong_bip, cao_bip, loai_tru_thuong)
        tong = sum(g["so"] for g in nhom.values())
        theo_tang = dem_theo_tang(doc, lv, bic, loai_tru_thuong, view)
        co_link = bool(lk_thay(doc, view, bic, True))
        ten_bang = mau.replace(u"{loai}", nhan).replace(u"{tang}", lv.Name.upper()).replace(u"{view}", view.Name)
        bao.append(u"")
        bao.append(u"== %s: %d cái thấy trong mặt bằng, %d ký hiệu (mỗi ký hiệu 1 dòng)%s" % (
            nhan, tong, len(nhom), (u", bỏ %d cái Type Comments có chữ %s (%s)" % (
                bo, u" / ".join(loai_tru), u"; ".join(sorted(bo_tc))[:200])) if bo else u""))
        for mk in sorted(nhom, key=lambda k: (k == u"", k)):
            g = nhom[mk]
            kt = sorted(g["kt"], key=lambda x: (x[0] or 0, x[1] or 0))
            bao.append(u"   %-14s %s  x%d" % (mk or u"(trống)", u", ".join(u"%sx%s" % (a or u"?", b or u"?") for a, b in kt),
                                            g["so"]))
            if not mk:
                xem_lai.append(u"%s chưa có Type Mark (%d cái, gộp chung 1 dòng trống): %s" % (
                    nhan, g["so"], u"; ".join(sorted(g["type"]))[:300]))
            elif len(kt) > 1:
                xem_lai.append(u"%s '%s' cùng ký hiệu nhưng khác kích thước %s – ô Rộng / Cao để trống: %s" % (
                    nhan, mk, u", ".join(u"%sx%s" % k for k in kt), u"; ".join(sorted(g["type"]))[:300]))
        if khac_tang:
            xem_lai.append(u"%d %s thấy trong mặt bằng nhưng Level khác tầng %s – bảng KHÔNG đếm (vd. id %s)." % (
                len(khac_tang), nhan.lower(), lv.Name, u", ".join(str(e.Id.Value) for e in khac_tang[:5])))
        if theo_tang != tong and not doc_in(6):
            xem_lai.append(u"%s: tầng %s có %d cái, mặt bằng chỉ thấy %d (crop / ẩn) – bảng lọc theo tầng nên đếm %d; đặt "
                           u"bảng lên sheet của mặt bằng này và bật IN[6] (Shift+bấm) thì bảng chỉ đếm cửa thấy trên sheet."
                           % (nhan, lv.Name, theo_tang, tong, theo_tang))
        if dry:
            bao.append(u"   Sẽ tạo / cập nhật bảng '%s'." % ten_bang)
            continue
        TransactionManager.Instance.EnsureInTransaction(doc)
        st = SubTransaction(doc)            # bảng lỗi giữa chừng thì huỷ riêng bảng đó
        st.Start()
        try:
            if co_link:
                dong_bang = []
                for mk in sorted(nhom, key=lambda k: (k == u"", k)):
                    g = nhom[mk]
                    kt = sorted(g["kt"], key=lambda x: (x[0] or 0, x[1] or 0))
                    r_, c_ = (kt[0] if len(kt) == 1 else (None, None))
                    dong_bang.append([mk or u"(trống)", u"%s" % r_ if r_ else u"", u"%s" % c_ if c_ else u"", u"%d" % g["so"]])
                dong_bang.append([u"TỔNG", u"", u"", u"%d" % tong])
                vs, cach = lk_bang_ve(doc, ten_bang, ten_bang, COT, [34, 22, 22, 20], dong_bang)
                bao.append(u"   Bảng lấy từ file link: Revit không lọc được bảng thống kê theo tầng cho đối tượng trong link nên vẽ "
                           u"thành bảng rời; đổi cửa thì bấm lại nút để cập nhật.")
            else:
                vs, cach = lap_bang(doc, bic, ten_bang, lv, loai_tru, rong_bip, cao_bip, bool(doc_in(6)))
            doc.Regenerate()
            st.Commit()
            bang_tao.append(vs)
            bao.append(u"   Bảng '%s' (%s):" % (ten_bang, cach))
            for d_ in ([] if co_link else doc_bang(vs)):
                bao.append(u"      " + d_)
        except Exception as ex:
            if st.HasStarted() and not st.HasEnded():
                st.RollBack()
            bao.append(u"   KHÔNG tạo được bảng '%s': %s" % (ten_bang, (u"%s" % ex).splitlines()[0][:200]))
    TransactionManager.Instance.TransactionTaskDone()
    if xem_lai:
        bao.append(u"")
        bao.append(u"CẦN XEM LẠI:")
        bao.extend(u" - " + s for s in xem_lai)
    if bang_tao and doc_in(5):
        try:
            DocumentManager.Instance.CurrentUIDocument.RequestViewChange(bang_tao[0])
        except Exception:
            pass
    return bao


try:
    OUT = _chinh()
except Exception:
    try:
        TransactionManager.Instance.ForceCloseTransaction()
    except Exception:
        pass
    OUT = [u"LỖI:", traceback.format_exc()]
