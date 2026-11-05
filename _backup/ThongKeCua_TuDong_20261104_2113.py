# Bảng thống kê cửa của mặt bằng đang mở (người dùng yêu cầu 2026-11-04: "tạo 1 bảng thống kê các cửa có trong mặt bằng
# đó, những cửa trùng thì hiện 1 lần"):
#   - Mỗi hạng mục 1 bảng: "THỐNG KÊ CỬA ĐI - <tầng>", "THỐNG KÊ CỬA SỔ - <tầng>" (Revit không gộp được cửa đi + cửa sổ
#     vào 1 bảng: bảng nhiều hạng mục không có cột Rộng / Cao và bộ lọc không có "hoặc" – khảo sát Revit 2027.3).
#   - Cột: Ký hiệu (Type Mark) / Rộng / Cao / Số lượng; KHÔNG liệt kê từng cái (Itemize tắt), gộp theo Type Mark → cửa
#     trùng ký hiệu hiện 1 dòng kèm số lượng; dòng tổng cuối bảng.
#   - Lọc: Level = tầng của mặt bằng, bỏ Type Comments loại trừ (Louver). "Filter by sheet" TẮT mặc định (bật thì bảng đặt
#     trên sheet không có mặt bằng sẽ trống – thử 2026-11-04); mặt bằng crop 1 phần tầng thì bật IN[6] rồi đặt bảng lên
#     sheet của mặt bằng đó để bảng chỉ đếm cửa thấy trên sheet.
#   - Bảng cùng tên đã có (bấm lại) thì cập nhật lại cột / lọc / gộp, không tạo trùng, không xoá. Chưa có thì nhân bản
#     bảng cùng hạng mục có sẵn của dự án (giữ kiểu trình bày công ty), không có thì tạo mới.
#   - Báo CẦN XEM LẠI: cửa chưa có Type Mark, cùng Type Mark mà khác kích thước (Revit để trống ô), số cửa thấy trong
#     mặt bằng khác số cửa của tầng.
# Dry-run chỉ báo cáo, không sửa mô hình.
# INPUT
#   IN[0] (str)  Tên view mặt bằng (để trống = view đang mở)
#   IN[1] (str)  Hạng mục thống kê: Cửa đi;Cửa sổ (bỏ bớt nếu chỉ cần 1 bảng)
#   IN[2] (str)  Type Comments của đối tượng KHÔNG thống kê (vd. Louver), cách nhau bằng ;
#   IN[3] (bool) Dry-run (True = chỉ báo cáo)
#   IN[4] (str)  Mẫu tên bảng ({loai} = CỬA ĐI / CỬA SỔ, {tang} = tên tầng, {view} = tên view)
#   IN[5] (bool) Mở bảng vừa tạo (bảng đầu tiên)
#   IN[6] (bool) Chỉ đếm cửa thấy trên sheet đặt bảng (Filter by sheet; dùng cho mặt bằng crop 1 phần tầng)
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
MAC_DINH = ["", u"Cửa đi;Cửa sổ", "Louver", True, u"THỐNG KÊ {loai} - {tang}", True, False]
# (từ khoá không dấu nhận trong IN[1], hạng mục, nhãn, tham số rộng, tham số cao)
HANG_MUC = [(u"cua di", BuiltInCategory.OST_Doors, u"CỬA ĐI", BuiltInParameter.DOOR_WIDTH, BuiltInParameter.DOOR_HEIGHT),
            (u"cua so", BuiltInCategory.OST_Windows, u"CỬA SỔ", BuiltInParameter.WINDOW_WIDTH,
             BuiltInParameter.WINDOW_HEIGHT)]
COT = [u"Ký hiệu", u"Rộng", u"Cao", u"Số lượng"]


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


def dem_trong_view(doc, view, bic, rong_bip, cao_bip, loai_tru):
    """Cửa thấy trong mặt bằng: {Type Mark: {"so": n, "kt": set((rộng, cao)), "type": set(tên)}}, số bị loại, số khác
    tầng (thấy trong view nhưng Level khác tầng → bảng không đếm)."""
    lv = view.GenLevel
    nhom, bo, khac_tang = {}, 0, []
    for e in FilteredElementCollector(doc, view.Id).OfCategory(bic).WhereElementIsNotElementType():
        t = doc.GetElement(e.GetTypeId())
        if chuoi_type(t, BuiltInParameter.ALL_MODEL_TYPE_COMMENTS).lower() in loai_tru:
            bo += 1
            continue
        if lv is not None and e.LevelId != lv.Id:
            khac_tang.append(e)
            continue
        mk = chuoi_type(t, BuiltInParameter.ALL_MODEL_TYPE_MARK)
        g = nhom.setdefault(mk, {"so": 0, "kt": set(), "type": set()})
        g["so"] += 1
        g["kt"].add((gia_tri_kt(e, t, (rong_bip, BuiltInParameter.FAMILY_WIDTH_PARAM)),
                     gia_tri_kt(e, t, (cao_bip, BuiltInParameter.FAMILY_HEIGHT_PARAM))))
        g["type"].add(u"%s : %s" % (t.FamilyName if t is not None else u"?", ten(t)))
    return nhom, bo, khac_tang


def dem_theo_tang(doc, lv, bic, loai_tru):
    n = 0
    for e in FilteredElementCollector(doc).OfCategory(bic).WhereElementIsNotElementType():
        if e.LevelId != lv.Id:
            continue
        t = doc.GetElement(e.GetTypeId())
        if chuoi_type(t, BuiltInParameter.ALL_MODEL_TYPE_COMMENTS).lower() in loai_tru:
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
        for tc in loai_tru_tc:
            d.AddFilter(ScheduleFilter(f_tc.FieldId, ScheduleFilterType.NotEqual, tc))
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
    loai_tru_thuong = set(x.lower() for x in loai_tru)
    chon = [khong_dau(x) for x in tach(doc_in(1))]
    hang_muc = [h for h in HANG_MUC if any(h[0] in c for c in chon)]
    if not hang_muc:
        return [u"IN[1] không có hạng mục nào nhận được (Cửa đi / Cửa sổ)."]
    bao.append(u"Mặt bằng: %s – tầng %s%s" % (view.Name, lv.Name, u" (DRY-RUN: chỉ báo cáo)" if dry else u""))
    mau = doc_in(4) or MAC_DINH[4]
    xem_lai = []
    bang_tao = []
    for _, bic, nhan, rong_bip, cao_bip in hang_muc:
        nhom, bo, khac_tang = dem_trong_view(doc, view, bic, rong_bip, cao_bip, loai_tru_thuong)
        tong = sum(g["so"] for g in nhom.values())
        theo_tang = dem_theo_tang(doc, lv, bic, loai_tru_thuong)
        ten_bang = mau.replace(u"{loai}", nhan).replace(u"{tang}", lv.Name.upper()).replace(u"{view}", view.Name)
        bao.append(u"")
        bao.append(u"== %s: %d cái thấy trong mặt bằng, %d ký hiệu (mỗi ký hiệu 1 dòng)%s" % (
            nhan, tong, len(nhom), (u", bỏ %d cái Type Comments %s" % (bo, u" / ".join(loai_tru))) if bo else u""))
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
            vs, cach = lap_bang(doc, bic, ten_bang, lv, loai_tru, rong_bip, cao_bip, bool(doc_in(6)))
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
