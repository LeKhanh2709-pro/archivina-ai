# Thống kê lan can, louver của mặt bằng đang mở (người dùng yêu cầu 2026-11-05: "tạo thống kê lan can louver như cửa"):
#   - Tên = MARK của từng đối tượng (không phải Type Mark như cửa). Nút bật bảng lib\arv_bang_lan_can.py, người dùng gõ tên
#     mới → IN[7] = JSON [{"ids": [...], "moi": "LK-01", "cu": ..., "nhan": ...}] → đặt Mark cho các đối tượng đó.
#   - Mỗi lớp 1 bảng: "BẢNG THỐNG KÊ LAN CAN <TẦNG>" (Railings), "BẢNG THỐNG KÊ LOUVER <TẦNG>" (hạng mục có nhiều louver
#     nhất trong view: Windows / Generic Models). Cùng tên với bảng của nút Định vị lan can, louver nên bảng đã đặt trên
#     sheet được cập nhật theo, không tạo trùng, không xoá.
#   - Cột như bảng cửa: Tên / Chiều dài (lan can: Tổng chiều dài) / Chiều cao / Số lượng; KHÔNG liệt kê từng cái, gộp theo
#     Mark → trùng tên hiện 1 dòng; dòng TỔNG cuối bảng.
#   - Lọc: Level = tầng của mặt bằng + Mark bắt đầu bằng tiền tố đang dùng (bộ lọc Revit không có "hoặc": dùng cả LK và LC
#     thì lọc "Mark có giá trị"). Chưa có Mark đúng tiền tố thì không vào bảng, báo CẦN XEM LẠI.
#   - Chưa có bảng cùng tên thì nhân bản bảng cùng hạng mục có sẵn (ưu tiên tên có "thống kê", giữ kiểu trình bày công ty),
#     không có thì tạo mới. Bảng cùng tên khác hạng mục thì báo, không đụng.
# Dry-run chỉ báo cáo, không sửa mô hình.
# INPUT
#   IN[0] (str)  Tên view mặt bằng (để trống = view đang mở)
#   IN[1] (str)  Tiền tố Mark lan can, cách nhau bằng ;
#   IN[2] (str)  Tiền tố Mark louver, cách nhau bằng ;
#   IN[3] (bool) Dry-run (True = chỉ báo cáo)
#   IN[4] (str)  Mẫu tên bảng ({loai} = LAN CAN / LOUVER, {tang} = tên tầng, {view} = tên view)
#   IN[5] (bool) Mở bảng vừa tạo (bảng đầu tiên)
#   IN[6] (str)  Từ khoá louver trong Type Comments / tên family / type, cách nhau bằng ;
#   IN[7] (str)  Đổi tên: JSON [{"ids": [id...], "moi": "<Mark mới>"}] (trống = không đổi; nút điền từ bảng)
#   IN[8] (bool) Tạo / cập nhật bảng thống kê Revit
# OUTPUT
#   OUT (list[str])  Báo cáo
import json
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
from System.Collections.Generic import List as NetList

TRANSACTION_NAME = u"ARV - Thống kê lan can, louver"
MAC_DINH = ["", u"LK;LC", u"LV", True, u"BẢNG THỐNG KÊ {loai} {tang}", True, u"Louver;Lam", "", True]
LAN_CAN, LOUVER = u"LAN CAN", u"LOUVER"
HANG_MUC = (BuiltInCategory.OST_StairsRailing, BuiltInCategory.OST_Windows, BuiltInCategory.OST_GenericModel)


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


def ten(e):
    p = e.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM) if e is not None else None
    if p is not None and p.AsString():
        return p.AsString()
    try:
        return e.Name
    except Exception:
        return u"?"


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


def mark(e):
    p = e.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
    return (p.AsString() or u"").strip() if p is not None else u""


def phan_loai(doc, e, bic, tt_lc, tt_lv, tk_lv):
    """LAN_CAN / LOUVER / None – cùng quy tắc với LanCanLouver_TuDong.py."""
    k = khong_dau(mark(e))
    if k and any(k.startswith(x) for x in tt_lc):
        return LAN_CAN
    if k and any(k.startswith(x) for x in tt_lv):
        return LOUVER
    if bic == BuiltInCategory.OST_StairsRailing:
        return LAN_CAN
    t = doc.GetElement(e.GetTypeId())
    if t is None:
        return None
    p = t.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_COMMENTS)
    tc = khong_dau(p.AsString() if p is not None else u"")
    tn = u" %s " % khong_dau(u"%s %s" % (getattr(t, "FamilyName", u""), ten(t))).replace(u"-", u" ").replace(u"_", u" ")
    for x in tk_lv:
        if x in tc or (u" %s " % x) in tn or (len(x) > 3 and x in tn):
            return LOUVER
    return None


def lap_bang(doc, bic, ten_bang, level, lop, tien_to_dung):
    """Tạo / cập nhật bảng thống kê 1 lớp: Tên / Chiều dài / Chiều cao / Số lượng, gộp theo Mark, lọc Level + Mark.
    tien_to_dung: các tiền tố gốc (chữ hoa) đang dùng trong tầng. Trả về (bảng, cách làm)."""
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
            co.setdefault("count", f)
            continue
        try:
            co.setdefault(f.ParameterId.Value, f)
        except Exception:
            pass

    def lay_id(k):
        if k in co:
            return co[k]
        for sf in d.GetSchedulableFields():
            try:
                if str(sf.FieldType) != "Count" and sf.ParameterId.Value == k:
                    co[k] = d.AddField(sf)
                    return co[k]
            except Exception:
                pass
        return None

    def lay(*bips):
        for b in bips:
            f = lay_id(int(b))
            if f is not None:
                return f
        return None

    def lay_ten(*tens):
        """Cột theo tên hiển thị (tham số type của Railing không có BuiltInParameter dùng được)."""
        for sf in d.GetSchedulableFields():
            try:
                if sf.GetName(doc) in tens:
                    return lay_id(sf.ParameterId.Value)
            except Exception:
                pass
        return None

    f_mark = lay(BuiltInParameter.ALL_MODEL_MARK)
    if lop == LAN_CAN:
        f_dai = lay(BuiltInParameter.CURVE_ELEM_LENGTH, BuiltInParameter.INSTANCE_LENGTH_PARAM)
        f_cao = lay_ten(u"Railing Height")
        nhan_dai = u"Tổng chiều dài"
    else:
        f_dai = lay(BuiltInParameter.WINDOW_WIDTH, BuiltInParameter.GENERIC_WIDTH, BuiltInParameter.FAMILY_WIDTH_PARAM)
        f_cao = lay(BuiltInParameter.WINDOW_HEIGHT, BuiltInParameter.GENERIC_HEIGHT, BuiltInParameter.FAMILY_HEIGHT_PARAM)
        nhan_dai = u"Chiều dài"
    f_dem = co.get("count")
    if f_dem is None:
        for sf in d.GetSchedulableFields():
            if str(sf.FieldType) == "Count":
                f_dem = d.AddField(sf)
                break
    f_tang = lay(BuiltInParameter.STAIRS_RAILING_BASE_LEVEL_PARAM, BuiltInParameter.FAMILY_LEVEL_PARAM,
                 BuiltInParameter.SCHEDULE_LEVEL_PARAM, BuiltInParameter.INSTANCE_REFERENCE_LEVEL_PARAM)
    if f_mark is None or f_dem is None:
        raise Exception(u"không thêm được cột Mark / Count vào bảng")
    hien = [(f_mark, u"Tên"), (f_dai, nhan_dai), (f_cao, u"Chiều cao"), (f_dem, u"Số lượng")]
    ids_hien = [g.FieldId for g, _ in hien if g is not None]
    for i in range(d.GetFieldCount()):
        f = d.GetField(i)
        f.IsHidden = not any(f.FieldId == x for x in ids_hien)
    for f, nhan in hien:
        if f is not None:
            f.ColumnHeading = nhan
    for f in (f_dem, f_dai if lop == LAN_CAN else None):
        try:
            if f is not None:
                f.DisplayType = ScheduleFieldDisplayType.Totals
        except Exception:
            pass
    try:
        thu_tu = NetList[ScheduleFieldId]()
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
    if len(tien_to_dung) == 1:
        d.AddFilter(ScheduleFilter(f_mark.FieldId, ScheduleFilterType.BeginsWith, tien_to_dung[0]))
    else:
        d.AddFilter(ScheduleFilter(f_mark.FieldId, ScheduleFilterType.HasValue))
    d.ClearSortGroupFields()
    d.AddSortGroupField(ScheduleSortGroupField(f_mark.FieldId))
    d.IsItemized = False                # gộp: trùng Mark → 1 dòng
    for ten_tt, gt in (("ShowTitle", True), ("ShowHeaders", True), ("ShowGrandTotal", True),
                       ("ShowGrandTotalTitle", True), ("ShowGrandTotalCount", False), ("GrandTotalTitle", u"TỔNG")):
        try:
            setattr(d, ten_tt, gt)
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
    """Đặt Mark theo JSON. Mark chỉ đọc / đối tượng trong group không đặt được thì báo, không dừng."""
    if not json_doi:
        return
    try:
        doi = json.loads(json_doi)
    except Exception as ex:
        bao.append(u"IN[7] không phải JSON hợp lệ: %s" % ex)
        return
    if not doi:
        bao.append(u"Không có tên nào cần đổi.")
        return
    bao.append(u"")
    bao.append(u"== ĐẶT MARK – %d nhóm%s" % (len(doi), u" (DRY-RUN)" if dry else u""))
    if not dry:
        TransactionManager.Instance.EnsureInTransaction(doc)
    for it in doi:
        moi = (u"%s" % it.get("moi", u"")).strip()
        if not moi:
            continue
        ok, loi = 0, []
        for i in it.get("ids", []):
            e = doc.GetElement(ElementId(int(i)))
            p = e.get_Parameter(BuiltInParameter.ALL_MODEL_MARK) if e is not None else None
            if p is None or p.IsReadOnly:
                loi.append(u"%s" % i)
                continue
            if dry:
                ok += 1
                continue
            try:
                p.Set(moi)
                ok += 1
            except Exception:
                loi.append(u"%s" % i)
        bao.append(u"   %s → %s  (%s, %d cái)" % (it.get("cu") or u"(trống)", moi, it.get("nhan", u""), ok))
        if loi:
            xem_lai.append(u"Không đặt được Mark '%s' cho %d đối tượng (chỉ đọc / trong group): %s" % (
                moi, len(loi), u", ".join(loi[:20])))
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
    goc_lc, goc_lv = tach(doc_in(1)), tach(doc_in(2))
    tt_lc, tt_lv = [khong_dau(x) for x in goc_lc], [khong_dau(x) for x in goc_lv]
    tk_lv = [khong_dau(x) for x in tach(doc_in(6))]
    bao.append(u"Mặt bằng: %s – tầng %s%s" % (view.Name, lv.Name, u" (DRY-RUN: chỉ báo cáo)" if dry else u""))
    xem_lai = []
    bang_tao = []
    doi_ten(doc, doc_in(7), dry, bao, xem_lai)
    lam_bang = bool(doc_in(8))
    if not lam_bang:
        bao.append(u"Không tạo bảng thống kê Revit (IN[8] tắt).")
    # Đọc lại sau khi đặt Mark: {lớp: {hạng mục: [đối tượng]}}
    theo_lop = {LAN_CAN: {}, LOUVER: {}}
    for bic in HANG_MUC:
        for e in FilteredElementCollector(doc, view.Id).OfCategory(bic).WhereElementIsNotElementType():
            lop = phan_loai(doc, e, bic, tt_lc, tt_lv, tk_lv)
            if lop is not None:
                theo_lop[lop].setdefault(bic, []).append(e)
    mau = doc_in(4) or MAC_DINH[4]
    for lop, goc_tt, tt in ((LAN_CAN, goc_lc, tt_lc), (LOUVER, goc_lv, tt_lv)):
        nhom = theo_lop[lop]
        tat_ca = [e for ds in nhom.values() for e in ds]
        dung = [e for e in tat_ca if any(khong_dau(mark(e)).startswith(x) for x in tt)]
        bao.append(u"")
        bao.append(u"== %s: %d cái thấy trong mặt bằng, %d có Mark đúng tiền tố %s" % (
            lop, len(tat_ca), len(dung), u" / ".join(goc_tt)))
        dem = {}
        for e in dung:
            dem[mark(e)] = dem.get(mark(e), 0) + 1
        for mk in sorted(dem):
            bao.append(u"   %-14s x%d" % (mk, dem[mk]))
        sai = [e for e in tat_ca if e not in dung]
        if sai:
            xem_lai.append(u"%s: %d cái chưa có Mark đúng tiền tố %s – không vào bảng, nút Định vị không tag (vd. id %s)." % (
                lop, len(sai), u" / ".join(goc_tt), u", ".join(str(e.Id.Value) for e in sai[:5])))
        if not lam_bang or not tat_ca:
            continue
        # Hạng mục có nhiều đối tượng nhất của lớp (ưu tiên có Mark đúng); bộ lọc bảng không gộp được 2 hạng mục
        bic = max(nhom.keys(), key=lambda k: (sum(1 for e in nhom[k] if e in dung), len(nhom[k])))
        if len(nhom) > 1:
            xem_lai.append(u"Bảng %s chỉ thống kê hạng mục %s; còn %s." % (lop, Category.GetCategory(doc, bic).Name,
                           u", ".join(Category.GetCategory(doc, k).Name for k in nhom if k != bic)))
        dang_dung = [g for g, x in zip(goc_tt, tt) if any(khong_dau(mark(e)).startswith(x) for e in dung)]
        tien_to = dang_dung or goc_tt[:1]
        ten_bang = mau.replace(u"{loai}", lop).replace(u"{tang}", lv.Name.upper()).replace(u"{view}", view.Name)
        if dry:
            bao.append(u"   Sẽ tạo / cập nhật bảng '%s'." % ten_bang)
            continue
        TransactionManager.Instance.EnsureInTransaction(doc)
        st = SubTransaction(doc)            # bảng lỗi giữa chừng thì huỷ riêng bảng đó
        st.Start()
        try:
            vs, cach = lap_bang(doc, bic, ten_bang, lv, lop, tien_to)
            doc.Regenerate()
            st.Commit()
            bang_tao.append(vs)
            bao.append(u"   Bảng '%s' (%s):" % (ten_bang, cach))
            for d_ in doc_bang(vs):
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
