# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong ARV_MBTuongXayTang_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
# Revit 2027 / Dynamo 4.2 (PythonNet3).
#
# Trình bày MẶT BẰNG TƯỜNG XÂY (định vị tường) cả tầng theo mẫu FPT P5 A.CD.04.07 (KTS chốt 2026-11-03, G19):
#   1. View mặt bằng mới trên level IN[0] (tên IN[1]), chép thông số view template IN[2] vào view rồi BỎ gắn template
#      (template công ty để 1/150 – KHÔNG sửa template). Ẩn nội thất, thiết bị, Room, sàn. Tỷ lệ = số đầu tiên trong
#      IN[3] mà hình (kể cả dim, đầu trục) ước tính vừa vùng vẽ khung tên.
#   2. Trục của file: đầu trục 2D ở CẢ 2 ĐẦU, cách tường ngoài cùng GRID_END mm giấy. Dim trục 4 phía, mỗi phía
#      2 chuỗi: khoảng trục + kích thước tổng (dim type IN[8]).
#   3. Chuỗi định vị tường (dim type IN[9]): gom tường (lõi ≥ 80, thẳng, song song trục X / Y) thành TUYẾN thẳng hàng
#      (lệch tim ≤ 60, hở ≤ 2500, tổng dài ≥ 4000). Mỗi tuyến xét 2 phía (điểm mẫu cách mặt tường 400):
#        - một phía phần lớn KHÔNG có Room → mặt ngoài nhà: chuỗi đặt phía ngoài, cách mặt tường WALL_EXT mm giấy;
#        - không, mà một phía là Room công cộng IN[12] (hành lang, khu vực chung) → chuỗi phía đó, cách WALL_INT;
#        - cả 2 phía là phòng trong căn → không dim (chi tiết căn hộ đã dim).
#      Mốc: MẶT LÕI (gạch thô, bỏ trát) tường vuông góc chạm tuyến, mép cửa đi / cửa sổ trên tuyến (tham chiếu
#      Left / Right của family), đầu tường của tuyến, mặt cột / vách BTCT của file Revit link (kết cấu), trục.
#      Mốc cách nhau < DIM_MIN gộp; chữ số đoạn ngắn chồng nhau → kéo sang phía ngoài đường dim, lệch xen kẽ.
#   4. Legend IN[10] (nhân bản một legend có sẵn rồi vẽ): BẢNG KÝ HIỆU GHI CHÚ TƯỜNG – mỗi vật liệu lõi tường một
#      dòng (hatch theo IN[11], loại, các chiều dày lõi) + lưu ý chỉ ghi điều đúng với mô hình.
#   5. Sheet IN[4] / IN[5], khung tên IN[6], viewport type IN[7]: MB ở trên, giữa vùng vẽ; legend góc dưới trái.
#   6. Trục file link KC: tắt hiển thị view filter có sẵn IN[16] trong view (trục type không phải '…KT').
#   Không tạo / sửa type, style, view template, filter. Chưa làm: tag căn hộ, chi tiết điển hình cột vách giao tường
#   xây, dim trong lòng căn.
# INPUT
#   IN[0] (str)  Level (trống = level của view mặt bằng đang mở) – VD "TẦNG 3"; bản D:\AI để trống (nút pyRevit)
#   IN[1] (str)  Tên view – VD "MB TƯỜNG XÂY TẦNG ĐIỂN HÌNH"
#   IN[2] (str)  View template để chép thông số – VD "TC.04.MatBangTuongXay"
#   IN[3] (str)  Tỷ lệ thử lần lượt – VD "100;150"
#   IN[4] (str)  Số hiệu sheet – VD "A140"
#   IN[5] (str)  Tên sheet – VD "MẶT BẰNG TƯỜNG XÂY TẦNG ĐIỂN HÌNH"
#   IN[6] (str)  Khung tên (tên family hoặc type) – VD "AV-Khung A1(841x594)-Kien Truc"
#   IN[7] (str)  Viewport type – VD "AV-Title No Line"
#   IN[8] (str)  Dimension type dim trục – VD "AV_Dim 2.2mm_Cut dim 6mm"
#   IN[9] (str)  Dimension type định vị tường – VD "AV_Dim 2.2mm_Cut dim 4mm"
#   IN[10] (str) Tên legend ghi chú tường (trống = không làm) – VD "GHI CHÚ TƯỜNG XÂY TẦNG ĐIỂN HÌNH"
#   IN[11] (str) Vật liệu lõi → hatch | mô tả, cách nhau ';' – VD
#                "GachNung=AV_Hatch Gach Xay|Tường gạch đặc nung;BeTong=AV_Hatch BTCT|Cột, vách BTCT"
#                (vật liệu cột / vách link KC cũng thành một dòng, chiều dày "Theo hồ sơ KC")
#   IN[12] (str) Tên Room hành lang (cách ';') – VD "Hành lang". KTS 2026-11-03: KHÔNG dim trong lõi thang / phòng
#                kỹ thuật → bỏ "Khu vực chung" (G19 đặt tên đó cho sảnh thang, phòng kỹ thuật trong lõi)
#   IN[13] (bool) Dry-run: True = dựng thử rồi hoàn tác, chỉ báo cáo (mặc định True)
#   IN[14] (bool) Làm lại: đã có view / sheet / legend cùng tên → dựng lại (mặc định False = dừng). View cùng level
#                được DÙNG LẠI (xóa dim của view, giữ VG / ẩn hiện KTS đã chỉnh, không chép lại template); sheet xóa
#                rồi tạo mới; legend xóa nội dung, vẽ lại tại chỗ.
#   IN[15] (str) Tham số nhóm Project Browser của sheet "tên=giá trị;…" – VD
#                "01_GiaiDoan=03_TKBVTC;02_HangMuc=04_MatBangTuongXay" (G19: nhóm có sẵn, như sheet giữ chỗ A107)
#   IN[16] (str) View filter có sẵn để ẨN trục / level không phải kiến trúc (trục file link KC) – VD
#                "Trục + Level- Kiến Trúc-Not" (type trục không kết thúc 'KT'; trống = không đụng). Filter áp cả phần
#                tử link (ByHostView). Tool chỉ thêm filter vào view + tắt hiển thị, KHÔNG tạo / sửa filter.
#   IN[17] (bool) Đặt lên bản vẽ (mặc định True; D:\AI thêm 2026-11-04 cho nút một chạm). False = chỉ dựng view + legend,
#                không tạo / đụng sheet. Số hiệu IN[4] là sheet TRỐNG có sẵn (không view, không bảng thống kê) thì đặt
#                vào sheet đó, giữ tên / khung tên / tham số (như Chống thấm), không cần bật IN[14].
# OUTPUT
#   OUT[0] (list[str])  Báo cáo
#   OUT[1] (list)       Trống

import os
import io
import csv
import datetime
import unicodedata

DYNAMO = "IN" in globals()

if DYNAMO:
    import clr
    clr.AddReference("RevitAPI")
    from Autodesk.Revit.DB import (FilteredElementCollector, XYZ, Transaction, ModelPathUtils, BuiltInParameter,
                                   BuiltInCategory, Level, ViewType, ViewFamily, ViewFamilyType, ViewPlan, ViewSheet,
                                   Viewport, ElementId, Reference, FamilySymbol, FamilyInstance, ElementType, View,
                                   LocationPoint, LocationCurve, FailureProcessingResult, IFailuresPreprocessor,
                                   FailureSeverity, FilledRegion, FilledRegionType, CurveLoop, Line, TextNote,
                                   TextNoteOptions, TextNoteType, HorizontalTextAlignment, Category,
                                   ViewDuplicateOption, Wall, WallType, HostObjectUtils, ShellLayerType,
                                   ReferenceArray, Options, Solid, PlanarFace, DimensionType, Dimension,
                                   RevitLinkInstance, Grid, DatumEnds, DatumExtentType, GeometryInstance,
                                   FamilyInstanceReferenceType, ElementCategoryFilter, LogicalOrFilter,
                                   DocumentValidation, CurveElement, ParameterFilterElement, ScheduleSheetInstance)
    from System.Collections.Generic import List
    try:
        clr.AddReference("RevitServices")
        from RevitServices.Persistence import DocumentManager
        from RevitServices.Transactions import TransactionManager
        doc = DocumentManager.Instance.CurrentDBDocument
    except Exception:          # chạy thử ngoài Dynamo (pyRevit): doc do môi trường cấp
        TransactionManager = None

TRANSACTION_NAME = u"ARV - Mặt bằng tường xây tầng"
SCRIPT_TAG = u"ARV_MBTuongXayTang_v1"

# Khung A1 AV-Khung A1(841x594): vùng vẽ NHÌN THẤY (đo 2026-10-22, xem ARV_DanTrangCanHo_v2) – mm giấy
AREA_X0, AREA_X1, AREA_Y0, AREA_Y1 = 36.0, 733.0, 17.0, 576.0
SHEET_PAD = 4.0            # mm giấy: cách mép vùng vẽ
LABEL_GAP = 2.0            # mm giấy: tên hình cách đáy khung viewport (dưới đầu trục)
LEGEND_SCALE = 50
LEGEND_H_GUESS = 70.0      # mm giấy: cao legend dùng lại (không vẽ lại) – để chọn tỷ lệ

# Vị trí dim / trục – mm GIẤY (nhân tỷ lệ ra mm thật)
WALL_EXT = 7.0             # chuỗi định vị tường mặt ngoài nhà cách mặt tường
WALL_INT = 4.5             # chuỗi định vị tường phía hành lang cách mặt tường
GRID_CHAIN = 13.0          # chuỗi khoảng trục cách tường ngoài cùng
GRID_TOTAL = 19.0          # dim tổng
GRID_END = 22.0            # đầu đường trục
CROP_PAD = 31.0            # crop cách tường ngoài cùng (chứa đầu trục) – G19 1/100: khung viewport 694 mm ≤ 697
CORR_MERGE = 20.0          # 2 chuỗi hành lang đối diện, khoảng thông thủy < → gộp 1 chuỗi giữa (1/100: 2000 mm)
TEXT_DROP = 3.0            # chữ số bị chồng → dời sang phía đường dim, cách đường dim
TEXT_CHAR_W = 1.35         # bề rộng 1 chữ số dim (chữ 2,2 mm)

# mm thật
CORE_MIN = 80.0            # lõi tường ≥ → tường xây / BTCT cần định vị
ALIGN_TOL = 60.0           # lệch tim để cùng tuyến
ALIGN_GAP = 8000.0         # hở tối đa giữa 2 đoạn cùng tuyến (G19: tường bao trục X1 đứt 7700 ở logia / vách KC)
ALIGN_MIN = 4000.0         # tổng dài tối thiểu của tuyến
SIDE_PROBE = 400.0         # điểm mẫu phía tuyến cách mặt tường
SIDE_STEP = 600.0
EXT_MAX = 12000.0          # đầu chuỗi kéo tới tường / KC gặp đầu tiên trong khoảng này
CLIP_STEP = 100.0          # bước dò dọc đường dim tìm đoạn nằm trong căn hộ
CLIP_MIN = 1000.0          # đoạn chuỗi còn lại ngắn hơn → bỏ
EXT_MIN = 30.0            # gần hơn = đầu chuỗi đã chạm tường, không kéo
EXT_FACE_TOL = 150.0       # mốc cuối: mặt lệch biên gần của vật gặp ≤ (mặt lõi lùi trát 15; khuôn cửa sổ lùi
#                            so với hộp bao gồm bậu / nẹp)
BAND_PAD = 60.0            # dải tuyến nới thêm khi tìm tường vuông góc / kết cấu chạm tuyến
JAMB_GAP_MAX = 30.0        # má tường thô nằm NGOÀI mép family ≤ (cửa sổ G19: 5 mm chèn foam)
JAMB_IN_MAX = 60.0         # má tường thô lùi VÀO trong mép family ≤ (cửa đi G19: nẹp khuôn trùm 20 mm)
OPEN_SKIP = 120.0         # mặt đầu tường cách mép cửa < → là má cửa (đã có mốc cửa) → bỏ
DIM_MIN = 30.0             # mốc cách nhau < → gộp
CUT_Z = 1000.0             # cao độ mặt cắt so với level

HIDE_CATS = ("OST_Furniture", "OST_PlumbingFixtures", "OST_MechanicalEquipment", "OST_Rooms", "OST_RoomTags",
             "OST_Floors", "OST_Casework", "OST_SpecialityEquipment", "OST_FurnitureSystems")
TEXT_TITLE = u"AV_Text 3mm_Arial-Bold"
TEXT_BODY = u"AV_Arial_2 mm_Dot"
NOTE_COLS = (20.0, 96.0, 34.0)

PRI_GRID, PRI_CORE, PRI_STRUCT, PRI_OPEN, PRI_END = 0, 1, 2, 3, 4


class StopReport(Exception):
    def __init__(self, lines):
        Exception.__init__(self, lines[0] if lines else u"")
        self.lines = lines


def to_mm(feet):
    return feet * 304.8


def from_mm(mm):
    return mm / 304.8


def norm(s):
    return unicodedata.normalize("NFC", (s or u"")).strip()


def split_list(text):
    return [s.strip() for s in (text or u"").split(u";") if s.strip()]


def get_name(element):
    try:
        return element.Name
    except Exception:
        p = element.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
        return p.AsString() if p else u""


def id_value(eid):
    v = getattr(eid, "Value", None)
    return v if v is not None else eid.IntegerValue


def is_central_file(document):
    if not document.IsWorkshared:
        return False
    try:
        central = ModelPathUtils.ConvertModelPathToUserVisiblePath(document.GetWorksharingCentralModelPath())
    except Exception:
        return False
    return os.path.normcase(central or "") == os.path.normcase(document.PathName or "")


def delete_ids(elements):
    ids = List[ElementId]()
    for e in elements:
        ids.Add(e.Id)
    if ids.Count:
        doc.Delete(ids)


def by_name(cls, name):
    n = norm(name)
    return next((e for e in FilteredElementCollector(doc).OfClass(cls).ToElements() if norm(get_name(e)) == n), None)


def find_type(bic, name):
    n = norm(name)
    fam, sep, typ = n.partition(u" : ")          # "Family : Type" (hộp thoại nút pyRevit, D:\AI 2026-11-04)
    for e in FilteredElementCollector(doc).OfCategory(bic).WhereElementIsElementType().ToElements():
        if sep and norm(getattr(e, "FamilyName", u"")) == fam and norm(get_name(e)) == typ:
            return e
    for e in FilteredElementCollector(doc).OfCategory(bic).WhereElementIsElementType().ToElements():
        if norm(get_name(e)) == n or norm(getattr(e, "FamilyName", u"")) == n:
            return e
    return None


def find_vp_type(name):
    """Viewport type (ElementType family 'Viewport', không có category) theo tên."""
    n = norm(name)
    return next((e for e in FilteredElementCollector(doc).OfClass(ElementType).ToElements()
                 if norm(getattr(e, "FamilyName", u"")) == u"Viewport" and norm(get_name(e)) == n), None)


def parse_materials(text):
    """'GachNung=AV_Hatch Gach Xay|Tường gạch đặc nung;…' → [(từ khoá vật liệu, tên hatch, mô tả)]."""
    res = []
    for item in split_list(text):
        if u"=" not in item:
            continue
        key, rest = item.split(u"=", 1)
        hatch, _, desc = rest.partition(u"|")
        res.append((norm(key).lower(), norm(hatch), norm(desc)))
    return res


# --- Hình học tường -----------------------------------------------------------------
class WallInfo(object):
    """Tường thẳng song song trục: ax = True khi chạy dọc X. c = tọa độ tim theo phương vuông góc, hw = nửa dày,
    lo / hi = phạm vi dọc tuyến (hộp bao), cores = [(tọa độ mm, Reference mặt lõi)] theo phương vuông góc tuyến."""

    def __init__(self, w, ax, c, hw, lo, hi, cores, core_mm, mat):
        self.w, self.ax, self.c, self.hw, self.lo, self.hi = w, ax, c, hw, lo, hi
        self.cores, self.core_mm, self.mat = cores, core_mm, mat


def core_layers(wt):
    """(dày lõi mm, dày lớp ngoài lõi mm, dày lớp trong lõi mm, tên vật liệu lõi) – None nếu không có lõi."""
    cs = wt.GetCompoundStructure()
    if cs is None:
        return None
    i0, i1 = cs.GetFirstCoreLayerIndex(), cs.GetLastCoreLayerIndex()
    if i0 < 0 or i1 < 0:
        return None
    layers = list(cs.GetLayers())
    core = sum(to_mm(l.Width) for l in layers[i0:i1 + 1])
    t_ext = sum(to_mm(l.Width) for l in layers[:i0])
    t_int = sum(to_mm(l.Width) for l in layers[i1 + 1:])
    m = doc.GetElement(layers[i0].MaterialId)
    return core, t_ext, t_int, (get_name(m) if m is not None else u"")


def core_faces(w, t_ext, t_int):
    """Mặt LÕI tường (lớp gạch, bỏ trát): tham chiếu ẩn '<UniqueId>:-9999:2:SURFACE' (lõi phía ngoài) /
    ':-9999:3:SURFACE' (lõi phía trong) – như ARV_DanTrangCanHo_v2 (đo trên G19 2026-10-28). Không có lớp trát →
    mặt bên tường. Trả về [(tọa độ mm theo pháp tuyến, Reference)]."""
    res = []
    for shell, idx, t in ((ShellLayerType.Exterior, 2, t_ext), (ShellLayerType.Interior, 3, t_int)):
        side = HostObjectUtils.GetSideFaces(w, shell)
        if side is None or side.Count == 0:
            continue
        f = w.GetGeometryObjectFromReference(side[0])
        if not isinstance(f, PlanarFace):
            continue
        nv = f.FaceNormal
        if abs(nv.X) > 0.99:
            cd, sg = to_mm(f.Origin.X), (1.0 if nv.X > 0 else -1.0)
        else:
            cd, sg = to_mm(f.Origin.Y), (1.0 if nv.Y > 0 else -1.0)
        if t < 0.5:
            res.append((cd, side[0]))
        else:
            ref = Reference.ParseFromStableRepresentation(doc, u"{}:-9999:{}:SURFACE".format(w.UniqueId, idx))
            res.append((cd - sg * t, ref))
    return res


def collect_walls(level):
    z = level.Elevation + from_mm(CUT_Z)
    out = []
    for w in FilteredElementCollector(doc).OfClass(Wall).WhereElementIsNotElementType().ToElements():
        bb = w.get_BoundingBox(None)
        if bb is None or not (bb.Min.Z <= z <= bb.Max.Z):
            continue
        wt = doc.GetElement(w.GetTypeId())
        if not isinstance(wt, WallType):
            continue
        cl = core_layers(wt)
        if cl is None or cl[0] < CORE_MIN:
            continue
        lc = getattr(w.Location, "Curve", None)
        if not isinstance(lc, Line):
            continue
        d = lc.Direction
        if abs(d.X) > 0.999:
            ax = True
        elif abs(d.Y) > 0.999:
            ax = False
        else:
            continue
        c = to_mm(lc.Origin.Y if ax else lc.Origin.X)
        lo = to_mm(bb.Min.X if ax else bb.Min.Y)
        hi = to_mm(bb.Max.X if ax else bb.Max.Y)
        try:
            cores = core_faces(w, cl[1], cl[2])
        except Exception:
            cores = []
        out.append(WallInfo(w, ax, c, to_mm(w.Width) / 2.0, lo, hi, cores, cl[0], cl[3]))
    return out


def opening_faces(e, view, along_x):
    """2 mặt ngoài cùng (min / max) của khuôn cửa theo phương tường: ((tọa độ, Ref), (tọa độ, Ref)) – như
    opening_edges của ARV_DanTrangCanHo_v2 (hình học symbol + Transform). Không có → None."""
    opt = Options()
    opt.ComputeReferences = True
    opt.View = view
    fl = []
    for gi in (e.get_Geometry(opt) or []):
        if not isinstance(gi, GeometryInstance):
            continue
        T = gi.Transform
        for s in gi.GetSymbolGeometry():
            if not isinstance(s, Solid):
                continue
            for f in s.Faces:
                if not isinstance(f, PlanarFace) or f.Reference is None:
                    continue
                nv = T.OfVector(f.FaceNormal)
                if (abs(nv.X) if along_x else abs(nv.Y)) > 0.999:
                    p = T.OfPoint(f.Origin)
                    fl.append((to_mm(p.X if along_x else p.Y), f.Reference))
    if len(fl) < 2:
        return None
    return min(fl, key=lambda q: q[0]), max(fl, key=lambda q: q[0])


def collect_openings(level, view):
    """{id tường chủ: [(mép nhỏ (tọa độ, Ref), mép lớn (tọa độ, Ref))]} – cửa đi / cửa sổ trên tường thẳng.
    Mép = mặt hình học THẬT của khuôn (G19 2026-11-03: ước theo Width + hướng tay → vài cửa đảo Left / Right,
    đoạn dim chồng nhau '1610 / 2400'). Không lấy được hình học → Left / Right ước theo Width."""
    flt = LogicalOrFilter(ElementCategoryFilter(BuiltInCategory.OST_Doors),
                          ElementCategoryFilter(BuiltInCategory.OST_Windows))
    res, jamb_cache = {}, {}
    for e in FilteredElementCollector(doc).WherePasses(flt).WhereElementIsNotElementType().ToElements():
        if not isinstance(e, FamilyInstance) or e.Host is None or e.LevelId != level.Id:
            continue
        lp = e.Location
        hc = getattr(e.Host.Location, "Curve", None)
        if not isinstance(lp, LocationPoint) or not isinstance(hc, Line):
            continue
        along_x = abs(hc.Direction.X) > 0.999
        if not along_x and abs(hc.Direction.Y) <= 0.999:
            continue
        edge = opening_faces(e, view, along_x)
        if edge is None:
            wp = e.Symbol.LookupParameter("Width") or e.LookupParameter("Width")
            L = e.GetReferences(FamilyInstanceReferenceType.Left)
            R = e.GetReferences(FamilyInstanceReferenceType.Right)
            if wp is None or L.Count == 0 or R.Count == 0:
                continue
            cc, h = to_mm(lp.Point.X if along_x else lp.Point.Y), to_mm(wp.AsDouble()) / 2.0
            hand = e.HandOrientation.X if along_x else e.HandOrientation.Y
            a, b = (cc - h, L[0]), (cc + h, R[0])
            edge = (a, b) if hand >= 0 else ((cc - h, R[0]), (cc + h, L[0]))
        edge = rough_jambs(e.Host, along_x, edge, jamb_cache)
        res.setdefault(id_value(e.Host.Id), []).append(edge)
    return res


def rough_jambs(wall, along_x, edge, cache):
    """KTS 2026-11-03: cửa sổ VÀ cửa đi dim vào MÁ TƯỜNG THÔ. Mốc = mặt má lỗ trên tường host gần mép ngoài cùng của
    family nhất: nằm ngoài mép ≤ JAMB_GAP_MAX (cửa sổ cách tường 5 mm chèn foam – W2_2200X2350: khuôn 2200, lỗ 2210)
    hoặc lùi vào trong ≤ JAMB_IN_MAX (cửa đi có nẹp khuôn trùm ra ngoài lỗ – DW01_800X2200: nẹp ±420, lỗ ±400).
    Không có → giữ mặt ngoài cùng của family."""
    key = id_value(wall.Id)
    if key not in cache:
        opt = Options()
        opt.ComputeReferences = True
        faces = []
        for s in (wall.get_Geometry(opt) or []):
            if not isinstance(s, Solid):
                continue
            for f in s.Faces:
                if isinstance(f, PlanarFace) and f.Reference is not None:
                    nv = f.FaceNormal
                    if abs(nv.X) > 0.999:
                        faces.append((True, to_mm(f.Origin.X), f.Reference))
                    elif abs(nv.Y) > 0.999:
                        faces.append((False, to_mm(f.Origin.Y), f.Reference))
        cache[key] = faces
    fs = [(cd, r) for ax_, cd, r in cache[key] if ax_ == along_x]
    (ca, ra), (cb, rb) = edge
    lo = [q for q in fs if -JAMB_IN_MAX <= ca - q[0] <= JAMB_GAP_MAX]
    hi = [q for q in fs if -JAMB_IN_MAX <= q[0] - cb <= JAMB_GAP_MAX]
    a = min(lo, key=lambda q: abs(ca - q[0])) if lo else (ca, ra)
    b = min(hi, key=lambda q: abs(q[0] - cb)) if hi else (cb, rb)
    return a, b


def link_material(ld, e):
    """Tên vật liệu kết cấu của cột (Structural Material, instance rồi type) / vách (lớp lõi) trong file link."""
    try:
        if isinstance(e, Wall):
            cs = ld.GetElement(e.GetTypeId()).GetCompoundStructure()
            i0 = cs.GetFirstCoreLayerIndex() if cs is not None else -1
            m = ld.GetElement(list(cs.GetLayers())[i0].MaterialId) if i0 >= 0 else None
        else:
            p = e.get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM)
            m = ld.GetElement(p.AsElementId()) if p is not None else None
            if m is None:
                tp = ld.GetElement(e.GetTypeId()).get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM)
                m = ld.GetElement(tp.AsElementId()) if tp is not None else None
        return get_name(m) if m is not None else u""
    except Exception:
        return u""


def collect_structure(level, warns, struct_mats):
    """Cột / vách của file Revit link cắt qua mặt cắt: [(x0, y0, x1, y1, [(trục X?, tọa độ mm, Reference link)])].
    struct_mats (set) nhận tên vật liệu kết cấu – cho dòng BTCT của bảng ký hiệu tường (G19: AV_BeTongCotThep)."""
    flt = LogicalOrFilter(ElementCategoryFilter(BuiltInCategory.OST_StructuralColumns),
                          ElementCategoryFilter(BuiltInCategory.OST_Walls))
    opt = Options()
    opt.ComputeReferences = True
    z = level.Elevation + from_mm(CUT_Z)
    res = []
    for lk in FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements():
        ld = lk.GetLinkDocument()
        if ld is None:
            continue
        T = lk.GetTotalTransform()
        n0 = len(res)
        for e in FilteredElementCollector(ld).WherePasses(flt).WhereElementIsNotElementType().ToElements():
            bb = e.get_BoundingBox(None)
            if bb is None:
                continue
            mn, mx = T.OfPoint(bb.Min), T.OfPoint(bb.Max)
            if not (min(mn.Z, mx.Z) <= z <= max(mn.Z, mx.Z)):
                continue
            if isinstance(e, Wall):       # vách kết cấu: chỉ lấy loại có lõi BTCT (bỏ lớp hoàn thiện mỏng)
                if to_mm(e.Width) < CORE_MIN:
                    continue
            geo = e.get_Geometry(opt)
            if geo is None:
                continue
            solids = []
            for g in geo:
                if isinstance(g, Solid) and g.Volume > 0:
                    solids.append(g)
                elif isinstance(g, GeometryInstance):
                    for g2 in g.GetInstanceGeometry():
                        if isinstance(g2, Solid) and g2.Volume > 0:
                            solids.append(g2)
            faces = []
            for s in solids:
                for f in s.Faces:
                    if not isinstance(f, PlanarFace) or f.Reference is None:
                        continue
                    nv, p = T.OfVector(f.FaceNormal), T.OfPoint(f.Origin)
                    try:
                        if abs(nv.X) > 0.999:
                            faces.append((True, to_mm(p.X), f.Reference.CreateLinkReference(lk)))
                        elif abs(nv.Y) > 0.999:
                            faces.append((False, to_mm(p.Y), f.Reference.CreateLinkReference(lk)))
                    except Exception:
                        pass
            if faces:
                mat = norm(link_material(ld, e))
                if mat:
                    struct_mats.add(mat)
                res.append((to_mm(min(mn.X, mx.X)), to_mm(min(mn.Y, mx.Y)), to_mm(max(mn.X, mx.X)),
                            to_mm(max(mn.Y, mx.Y)), faces))
        if len(res) > n0:
            warns.append(u"Mốc kết cấu từ link '{}': {} cột / vách.".format(get_name(lk), len(res) - n0))
    return res


# --- View, trục ---------------------------------------------------------------------
def walls_box(walls):
    xs, ys = [], []
    for wi in walls:
        bb = wi.w.get_BoundingBox(None)
        xs += [to_mm(bb.Min.X), to_mm(bb.Max.X)]
        ys += [to_mm(bb.Min.Y), to_mm(bb.Max.Y)]
    return min(xs), min(ys), max(xs), max(ys)


def pick_scale(scales, box, legend_h):
    """Tỷ lệ đầu tiên mà MB (tường + dim + đầu trục, ước theo CROP_PAD) và legend phía dưới vừa vùng vẽ."""
    aw = AREA_X1 - AREA_X0 - 2 * SHEET_PAD
    ah = AREA_Y1 - AREA_Y0 - 2 * SHEET_PAD
    for s in scales:
        w = (box[2] - box[0]) / s + 2 * CROP_PAD
        h = (box[3] - box[1]) / s + 2 * CROP_PAD
        if w <= aw and h + legend_h + 12.0 <= ah:
            return s
    return scales[-1]


def make_view(level, name, template, scale, box, old=None):
    """old: view cùng tên đã có (Làm lại) → dùng lại, xóa dim của view, KHÔNG chép lại template – giữ VG KTS đã
    chỉnh (G19 2026-11-03: tắt Grids link KC bị mất khi tool xóa view tạo mới)."""
    if old is not None:
        v = old
        delete_ids([d for d in FilteredElementCollector(doc, v.Id).OfClass(Dimension).ToElements()
                    if d.OwnerViewId == v.Id])
    else:
        vft = next((t for t in FilteredElementCollector(doc).OfClass(ViewFamilyType).ToElements()
                    if t.ViewFamily == ViewFamily.FloorPlan), None)
        if vft is None:
            raise StopReport([u"DỪNG: file không có View Family Type mặt bằng."])
        v = ViewPlan.Create(doc, vft.Id, level.Id)
        v.ViewTemplateId = ElementId.InvalidElementId
        v.Name = name
        if template is not None:
            v.ApplyViewTemplateParameters(template)
            v.ViewTemplateId = ElementId.InvalidElementId
    v.Scale = scale
    for name_ in HIDE_CATS:
        try:
            c = Category.GetCategory(doc, getattr(BuiltInCategory, name_))
            if c is not None and v.CanCategoryBeHidden(c.Id):
                v.SetCategoryHidden(c.Id, True)
        except Exception:
            pass
    pad = CROP_PAD * scale
    v.CropBoxActive = True
    cb = v.CropBox
    cb.Min = XYZ(from_mm(box[0] - pad), from_mm(box[1] - pad), cb.Min.Z)
    cb.Max = XYZ(from_mm(box[2] + pad), from_mm(box[3] + pad), cb.Max.Z)
    v.CropBox = cb
    v.CropBoxVisible = False
    doc.Regenerate()
    return v


def hide_by_filter(view, name, warns):
    """Tắt hiển thị view filter có sẵn tên `name` trong view (thêm vào view nếu chưa có). G19 2026-11-03: filter
    'Trục + Level- Kiến Trúc-Not' ẩn trục 'AV_Truc Dinh Vi-KC' của link KC – khung viewport 766 → 695 mm."""
    if not name.strip():
        return False
    f = by_name(ParameterFilterElement, name)
    if f is None:
        warns.append(u"Không có view filter '{}' → trục file link KC vẫn hiện (tắt tay trong VG).".format(name))
        return False
    try:
        if id_value(f.Id) not in [id_value(i) for i in view.GetFilters()]:
            view.AddFilter(f.Id)
        view.SetFilterVisibility(f.Id, False)
        return True
    except Exception as ex:
        warns.append(u"Không tắt được filter '{}' ({}) – tắt tay trong VG.".format(name, ex))
        return False


def fit_grids(view, box, scale, warns):
    """Trục của file (song song X / Y): 2D trong view, dài tới GRID_END mm giấy ngoài tường, đầu trục 2 đầu.
    Trả về (trục dọc [(x mm, Reference)], trục ngang [(y mm, Reference)])."""
    ext = GRID_END * scale
    gx, gy = [], []
    for gr in FilteredElementCollector(doc).OfClass(Grid).ToElements():
        c = gr.Curve
        if not isinstance(c, Line):
            continue
        vert = abs(c.Direction.Y) > 0.99
        if not vert and abs(c.Direction.X) <= 0.99:
            continue
        p0 = c.GetEndPoint(0)
        if vert and not box[0] - 1.0 <= to_mm(p0.X) <= box[2] + 1.0:
            continue
        if not vert and not box[1] - 1.0 <= to_mm(p0.Y) <= box[3] + 1.0:
            continue
        try:
            for e in (DatumEnds.End0, DatumEnds.End1):
                gr.SetDatumExtentType(e, view, DatumExtentType.ViewSpecific)
            cv = list(gr.GetCurvesInView(DatumExtentType.ViewSpecific, view))[0]
            q0, q1 = cv.GetEndPoint(0), cv.GetEndPoint(1)
            if vert:
                a, b = XYZ(q0.X, from_mm(box[1] - ext), q0.Z), XYZ(q0.X, from_mm(box[3] + ext), q0.Z)
            else:
                a, b = XYZ(from_mm(box[0] - ext), q0.Y, q0.Z), XYZ(from_mm(box[2] + ext), q0.Y, q0.Z)
            if (q1 - q0).DotProduct(b - a) < 0:
                a, b = b, a
            gr.SetCurveInView(DatumExtentType.ViewSpecific, view, Line.CreateBound(a, b))
            gr.ShowBubbleInView(DatumEnds.End0, view)
            gr.ShowBubbleInView(DatumEnds.End1, view)
        except Exception as ex:
            warns.append(u"Trục {}: không chỉnh được đầu trục ({}).".format(get_name(gr), ex))
        if vert:
            gx.append((to_mm(p0.X), Reference(gr)))
        else:
            gy.append((to_mm(p0.Y), Reference(gr)))
    return gx, gy


# --- Dim ----------------------------------------------------------------------------
def dedupe(refs):
    """refs: [(tọa độ mm, Reference, ưu tiên)] → [(tọa độ, Reference)] tăng dần; cụm mốc cách nhau < DIM_MIN
    giữ mốc ưu tiên cao nhất (trục > lõi tường > kết cấu > cửa > đầu tường)."""
    out = []
    for c, r, p in sorted(refs, key=lambda q: q[0]):
        if out and c - out[-1][0] < DIM_MIN:
            if p < out[-1][2]:
                out[-1] = (c, r, p)
            continue
        out.append((c, r, p))
    return [(c, r) for c, r, _p in out]


def new_dim(view, along_x, pos, lo, hi, refs, dtype, z):
    ra = ReferenceArray()
    for _c, r in refs:
        ra.Append(r)
    if ra.Size < 2:
        return None
    if along_x:
        ln = Line.CreateBound(XYZ(from_mm(lo), from_mm(pos), z), XYZ(from_mm(hi), from_mm(pos), z))
    else:
        ln = Line.CreateBound(XYZ(from_mm(pos), from_mm(lo), z), XYZ(from_mm(pos), from_mm(hi), z))
    try:
        return doc.Create.NewDimension(view, ln, ra, dtype)
    except Exception:
        return None


def dim_no_tiny(view, along_x, pos, lo, hi, chain, refs, dtype, z, rounds=4):
    """Tọa độ mép cửa chỉ ước theo Width (G19 thử 2026-11-03: khuôn lệch mặt lõi 5 mm → đoạn dim '5'). Tạo dim
    rồi đọc giá trị thật: đoạn < DIM_MIN → bỏ mốc ưu tiên thấp hơn trong 2 mốc của đoạn, dựng lại."""
    pri = {}
    for _c, r, p in refs:
        try:
            pri[r.ConvertToStableRepresentation(doc)] = p
        except Exception:
            pass
    d = new_dim(view, along_x, pos, lo, hi, chain, dtype, z)
    for _i in range(rounds):
        if d is None or d.NumberOfSegments < 2:
            return d
        doc.Regenerate()
        rs = [r for r in d.References]
        vals = [to_mm(s.Value) for s in d.Segments]
        bad = [i for i, v in enumerate(vals) if v < DIM_MIN]
        if not bad or len(rs) != len(vals) + 1:
            return d
        drop = set()
        for i in bad:
            a, b = rs[i], rs[i + 1]
            pa = pri.get(a.ConvertToStableRepresentation(doc), PRI_END)
            pb = pri.get(b.ConvertToStableRepresentation(doc), PRI_END)
            drop.add(i + 1 if pb >= pa else i)
        keep = [(0.0, r) for i, r in enumerate(rs) if i not in drop]
        doc.Delete(d.Id)
        d = new_dim(view, along_x, pos, lo, hi, keep, dtype, z)
    return d


TEXT_H = 2.2               # mm giấy: cao chữ dim (AV_Dim 2.2mm, đo G19: chữ cách đường dim 0,3 / 1 mm)
TEXT_PAD = 0.6             # mm giấy: 2 chữ dim cách nhau ít hơn → coi như chồng (KTS: "30|60" dính nhau)
TEXT_STEPS = (0.0, -2.5, 2.5, -5.0, 5.0, -7.5, 7.5, -10.0, 10.0, -12.5, 12.5, -15.0, 15.0)   # mm giấy: lùi
#                            dọc đường dim khi tìm chỗ trống (±10 còn kẹt 2 chữ ở cụm cửa mặt ngoài G19 trục X10)


def text_box(along_x, t, value_mm, scale):
    """Hộp chữ số dim (mm thật) quanh TextPosition t – đo trên ảnh G19 1/100: chữ ngang nằm trên điểm đặt, chữ dọc
    nằm bên trái điểm đặt; rộng TEXT_CHAR_W mm giấy / chữ số."""
    w = len(u"{}".format(int(round(value_mm)))) * TEXT_CHAR_W * scale
    h = TEXT_H * scale
    x, y = to_mm(t.X), to_mm(t.Y)
    return (x - w / 2.0, y, x + w / 2.0, y + h) if along_x else (x - h, y - w / 2.0, x, y + w / 2.0)


def box_hit(b, occ, own=None, pad=0.0):
    """Hộp b chạm (hoặc cách < pad, mm thật) hộp nào trong occ – bỏ qua đường dim của chính dim own."""
    for o, tag in occ:
        if tag is not None and tag == own:
            continue
        if min(b[2], o[2]) - max(b[0], o[0]) > -pad and min(b[3], o[3]) - max(b[1], o[1]) > -pad:
            return True
    return False


def place_texts(dim, along_x, pos, lo, hi, sides, scale, occ):
    """KTS 2026-11-03 (G19 hành lang X2–X3): chữ dim KHÔNG được chồng nhau. Chữ số nào chồng chữ / đường dim đã
    đặt (ghi trong occ, gồm cả dim trục) → thử lần lượt: hai phía đường dim (sides: phía ưu tiên trước, cách
    TEXT_DROP mm giấy), lùi dọc đường TEXT_STEPS; chỗ đầu tiên còn trống thì đặt (Revit tự vẽ gạch dẫn).
    Trả về (số chữ đã dời, số chữ không tìm được chỗ)."""
    tag = id_value(dim.Id)
    t = 0.3 * scale
    occ.append(((lo, pos - t, hi, pos + t) if along_x else (pos - t, lo, pos + t, hi), tag))
    if dim.NumberOfSegments < 2:
        register_dim_text(dim, along_x, scale, occ)
        return 0, 0
    doc.Regenerate()
    moved, stuck = 0, 0
    drop, hgt, pad = TEXT_DROP * scale, TEXT_H * scale, TEXT_PAD * scale
    for s in dim.Segments:
        t0 = s.TextPosition
        if t0 is None:
            continue
        val = to_mm(s.Value)
        b = text_box(along_x, t0, val, scale)
        if not box_hit(b, occ, tag, pad):
            occ.append((b, None))
            continue
        placed = None
        for side in sides:
            # điểm đặt theo phía: chữ ngang nằm TRÊN điểm đặt, chữ dọc nằm TRÁI điểm đặt
            p = pos + drop if side > 0 else pos - drop - hgt
            if not along_x:
                p = pos + drop + hgt if side > 0 else pos - drop
            for st in TEXT_STEPS:
                d = from_mm(st * scale)
                cand = XYZ(t0.X + d, from_mm(p), t0.Z) if along_x else XYZ(from_mm(p), t0.Y + d, t0.Z)
                cb = text_box(along_x, cand, val, scale)
                if not box_hit(cb, occ, tag, pad):
                    placed = (cand, cb)
                    break
            if placed:
                break
        if placed is None:
            stuck += 1
            occ.append((b, None))
            continue
        s.TextPosition = placed[0]
        occ.append((placed[1], None))
        moved += 1
    return moved, stuck


def register_dim_text(dim, along_x, scale, occ):
    segs = [s for s in dim.Segments] if dim.NumberOfSegments > 1 else [dim]
    for s in segs:
        if s.TextPosition is not None and s.Value is not None:
            occ.append((text_box(along_x, s.TextPosition, to_mm(s.Value), scale), None))


def grid_dims(view, box, gx, gy, scale, dtype, z, occ):
    """Dim trục 4 phía × 2 hàng; chữ + đường dim ghi vào occ để chữ dim tường tránh."""
    n = 0
    for refs, along_x, lo_side, hi_side, lo, hi in ((gx, True, box[1], box[3], box[0], box[2]),
                                                   (gy, False, box[0], box[2], box[1], box[3])):
        if len(refs) < 2:
            continue
        srt = sorted(refs, key=lambda q: q[0])
        for sign, base in ((-1.0, lo_side), (1.0, hi_side)):
            for pos, rr in ((base + sign * GRID_CHAIN * scale, srt), (base + sign * GRID_TOTAL * scale,
                                                                         [srt[0], srt[-1]])):
                d = new_dim(view, along_x, pos, lo, hi, rr, dtype, z)
                if d is not None:
                    n += 1
                    doc.Regenerate()
                    place_texts(d, along_x, pos, lo, hi, (), scale, occ)
    return n


def room_kind(x, y, z, public):
    r = doc.GetRoomAtPoint(XYZ(from_mm(x), from_mm(y), z))
    if r is None:
        return 0
    p = r.get_Parameter(BuiltInParameter.ROOM_NAME)
    return 1 if norm(p.AsString() if p else u"") in public else 2


def side_kind(x, y, z, public, solids):
    """Loại phía tuyến tại điểm mẫu (x, y): 1 hành lang (Room IN[12]), 2 phòng / trong nhà, 0 NGOÀI NHÀ – không Room
    VÀ ít nhất một trong 4 tia ±X / ±Y từ điểm không chạm tường / cột / vách nào (thoát ra ngoài nhà). KTS
    2026-11-03 (G19 lõi thang): hộp kỹ thuật, khoảng trống trong lõi không có Room (lõi phải ~3,5 m) bị coi là mặt
    ngoài → dim trong lõi; khe thông tầng X4–X5, đầu hành lang hở vẫn có tia thoát → mặt ngoài."""
    kd = room_kind(x, y, z, public)
    if kd != 0:
        return kd
    if any(b[0] <= x <= b[2] and b[1] <= y <= b[3] for b in solids):
        return 2
    rays = [True, True, True, True]                      # +X, −X, +Y, −Y chưa bị chặn
    for b in solids:
        if b[1] <= y <= b[3]:
            if b[0] >= x:
                rays[0] = False
            if b[2] <= x:
                rays[1] = False
        if b[0] <= x <= b[2]:
            if b[1] >= y:
                rays[2] = False
            if b[3] <= y:
                rays[3] = False
        if not any(rays):
            return 2
    return 0


def make_alignments(walls):
    """Tuyến: các tường cùng phương, lệch tim ≤ ALIGN_TOL, hở ≤ ALIGN_GAP (gộp bắc cầu)."""
    out = []
    for ax in (True, False):
        ws = sorted([w for w in walls if w.ax == ax], key=lambda q: q.c)
        groups = []
        for q in ws:
            hit = [g for g in groups if abs(g[0].c - q.c) <= ALIGN_TOL and
                   any(q.lo <= o.hi + ALIGN_GAP and q.hi >= o.lo - ALIGN_GAP for o in g)]
            if not hit:
                groups.append([q])
                continue
            hit[0].append(q)
            for g in hit[1:]:
                hit[0].extend(g)
                groups.remove(g)
        for g in groups:
            if sum(o.hi - o.lo for o in g) >= ALIGN_MIN:
                out.append((ax, g))
    return out


class Chain(object):
    """Một chuỗi định vị tường: phương, phạm vi lo–hi, vị trí đường dim, phía đặt chuỗi (0 = giữa hành lang),
    các mốc [(tọa độ, Reference, ưu tiên)], nhãn log."""

    def __init__(self, ax, c, lo, hi, pos, sgn, kind, refs, face, band=None):
        self.ax, self.c, self.lo, self.hi, self.pos, self.sgn = ax, c, lo, hi, pos, sgn
        self.kind, self.refs, self.face = kind, refs, face
        self.band = band            # (blo, bhi) mm theo phương vuông góc: tường vuông góc chạm dải → mốc


def clip_apartments(chains, z, public):
    """KTS 2026-11-03 (G19 khối cánh phải, Y3–Y4): KHÔNG dim vào căn hộ. Dò dọc đường dim mỗi CLIP_STEP: điểm nằm
    trong Room không phải hành lang (phòng căn hộ, lõi) → cắt. Chuỗi tách thành các đoạn liền ở ngoài nhà / hành lang /
    trong tường; đoạn < CLIP_MIN bỏ; mốc ngoài đoạn bỏ. Trả về (chuỗi mới, số chuỗi bị cắt)."""
    out, n_cut = [], 0
    for ch in chains:
        ok = []
        s = ch.lo
        while s <= ch.hi + 0.1:
            x, y = (s, ch.pos) if ch.ax else (ch.pos, s)
            ok.append((s, room_kind(x, y, z, public) != 2))
            s += CLIP_STEP
        runs, start = [], None
        for s, good in ok:
            if good and start is None:
                start = s
            elif not good and start is not None:
                runs.append((start, s - CLIP_STEP))
                start = None
        if start is not None:
            runs.append((start, ch.hi))
        if len(runs) == 1 and runs[0][0] <= ch.lo + 1.0 and runs[0][1] >= ch.hi - CLIP_STEP:
            out.append(ch)
            continue
        n_cut += 1
        for a, b in runs:
            # mút đoạn: mốc gần nhất ngoài vùng bị cắt (mặt tường căn hộ) – nới nửa bước dò
            a2, b2 = (a - CLIP_STEP if a > ch.lo + 1.0 else a), (b + CLIP_STEP if b < ch.hi - 1.0 else b)
            refs = [r for r in ch.refs if a2 - 1.0 <= r[0] <= b2 + 1.0]
            if b2 - a2 < CLIP_MIN or len(refs) < 2:
                continue
            lo, hi = min(r[0] for r in refs), max(r[0] for r in refs)
            out.append(Chain(ch.ax, ch.c, lo, hi, ch.pos, ch.sgn, ch.kind + u" (cắt căn hộ)", refs, ch.face, ch.band))
    return out, n_cut


def opening_stoppers(level, view):
    """Cửa đi / cửa sổ KHÔNG gắn tường trên level: [(hộp bao mm, [(trục X?, tọa độ, Ref)])] – chặn tia kéo dài chuỗi
    (G19: mặt khối cánh X4 đoạn y 21850–24482 chỉ là cửa sổ 2400×3150 không host → tia xuyên vào tường ngăn trong
    căn). Cửa có host bỏ qua: tường host đã chặn, còn hộp bao gồm cung cánh mở chồng ra hành lang (thử: dừng ở
    x 13300 giữa hành lang)."""
    flt = LogicalOrFilter(ElementCategoryFilter(BuiltInCategory.OST_Doors),
                          ElementCategoryFilter(BuiltInCategory.OST_Windows))
    opt = Options()
    opt.ComputeReferences = True
    opt.View = view
    res = []
    for e in FilteredElementCollector(doc).WherePasses(flt).WhereElementIsNotElementType().ToElements():
        if not isinstance(e, FamilyInstance) or e.LevelId != level.Id or e.Host is not None:
            continue
        bb = e.get_BoundingBox(None)
        if bb is None:
            continue
        faces = []
        for gi in (e.get_Geometry(opt) or []):
            if not isinstance(gi, GeometryInstance):
                continue
            T = gi.Transform
            for s in gi.GetSymbolGeometry():
                if not isinstance(s, Solid):
                    continue
                for f in s.Faces:
                    if not isinstance(f, PlanarFace) or f.Reference is None:
                        continue
                    nv, p = T.OfVector(f.FaceNormal), T.OfPoint(f.Origin)
                    if abs(nv.X) > 0.999:
                        faces.append((True, to_mm(p.X), f.Reference))
                    elif abs(nv.Y) > 0.999:
                        faces.append((False, to_mm(p.Y), f.Reference))
        if faces:
            res.append(((to_mm(bb.Min.X), to_mm(bb.Min.Y), to_mm(bb.Max.X), to_mm(bb.Max.Y)), faces))
    return res


def extend_chains(chains, walls, struct, gx, gy, stoppers=()):
    """KTS 2026-11-03 (G19, ảnh khoanh đỏ): đầu chuỗi dừng giữa khoảng trống (hành lang ngang Y3–Y4 dừng ở x 18550,
    mặt trên khối giữa dừng trước khe X4–X5, mặt khối cánh nhìn ra khe dừng ở y 24300) → kéo tiếp theo đường dim
    tới tường / cột / vách ĐẦU TIÊN gặp (≤ EXT_MAX): mốc cuối = mặt lõi (KC: mặt) phía gần của nó; trên đoạn kéo
    thêm lấy mặt lõi các tường vuông góc chạm dải tuyến và trục đi qua."""
    solids = []                      # (hộp bao mm, [(trục X?, tọa độ, Ref)])
    for q in walls:
        bb = q.w.get_BoundingBox(None)
        faces = [(not q.ax, cd, r) for cd, r in q.cores]     # mặt lõi tường dọc Y có pháp tuyến X
        solids.append(((to_mm(bb.Min.X), to_mm(bb.Min.Y), to_mm(bb.Max.X), to_mm(bb.Max.Y)), faces))
    for x0, y0, x1, y1, faces in struct:
        solids.append(((x0, y0, x1, y1), faces))
    solids += list(stoppers)
    n = 0
    for ch in chains:
        ax, p = ch.ax, ch.pos
        for end in (-1, 1):
            tip = ch.lo if end < 0 else ch.hi
            best = None
            for b, faces in solids:
                plo, phi = (b[1], b[3]) if ax else (b[0], b[2])      # phạm vi vuông góc đường dim
                alo, ahi = (b[0], b[2]) if ax else (b[1], b[3])      # phạm vi dọc đường dim
                if not plo <= p <= phi:
                    continue
                if end < 0 and ahi <= tip + 1.0:
                    d = tip - ahi
                elif end > 0 and alo >= tip - 1.0:
                    d = alo - tip
                else:
                    continue
                if d > EXT_MAX or (best is not None and d >= best[0]):
                    continue
                # mốc = mặt ĐÚNG ở biên gần của vật gặp (G19 thử: vách KC lấy nhầm mặt khuất trong lõi → kéo lố 2000)
                near = ahi if end < 0 else alo
                fs = [(cd, r) for fx, cd, r in faces if fx == ax and abs(cd - near) <= EXT_FACE_TOL]
                if fs:
                    best = (d, min(fs, key=lambda q: abs(q[0] - near)))
            if best is None or best[0] < EXT_MIN:
                continue
            cd, r = best[1]
            new_lo, new_hi = (cd, ch.lo) if end < 0 else (ch.hi, cd)
            ch.refs.append((cd, r, PRI_CORE))
            if ch.band is not None:
                for q in walls:
                    if q.ax == ax or q.hi < ch.band[0] or q.lo > ch.band[1] or not new_lo - 1.0 <= q.c <= new_hi + 1.0:
                        continue
                    ch.refs += [(c_, r_, PRI_CORE) for c_, r_ in q.cores]
                for x0, y0, x1, y1, faces in struct:     # cột / vách KC chạm dải trên đoạn kéo thêm (vách lõi)
                    slo, shi = (y0, y1) if ax else (x0, x1)
                    alo, ahi = (x0, x1) if ax else (y0, y1)
                    if shi < ch.band[0] or slo > ch.band[1] or ahi < new_lo - 1.0 or alo > new_hi + 1.0:
                        continue
                    ch.refs += [(c_, r_, PRI_STRUCT) for fx, c_, r_ in faces if fx == ax and new_lo - 1.0 <= c_ <= new_hi + 1.0]
            ch.refs += [(c_, r_, PRI_GRID) for c_, r_ in (gx if ax else gy) if new_lo < c_ < new_hi]
            if end < 0:
                ch.lo = min(ch.lo, cd)
            else:
                ch.hi = max(ch.hi, cd)
            n += 1
    return n


def merge_corridors(chains, scale):
    """KTS 2026-11-03 (G19 hành lang X2–X3 rộng 1600): 2 chuỗi hành lang đối diện nhau, khoảng thông thủy giữa 2
    mặt tường < CORR_MERGE mm giấy → chữ 2 chuỗi đè nhau. Gộp thành MỘT chuỗi ở giữa hành lang, mốc của cả hai
    bên, chữ đoạn ngắn kéo xen kẽ hai phía. Gộp theo CỤM (một bên tường bị tách nhiều tuyến – G19 X3: ghép từng
    cặp còn sót 1 chuỗi cách tường 450 đè chữ chuỗi giữa). Xét cả chuỗi 'mặt ngoài': đầu hành lang hở không có
    Room (G19 X3 y 3000–5615) làm tuyến bị xếp mặt ngoài nhưng vẫn đối diện chuỗi hành lang bên kia."""
    corr = list(chains)
    parent = dict((id(ch), id(ch)) for ch in corr)

    def root(k):
        while parent[k] != k:
            k = parent[k]
        return k
    for a in corr:
        for b in corr:
            if a is b or a.ax != b.ax or a.sgn <= 0 or b.sgn >= 0:
                continue                    # a: chuỗi phía +, b: chuỗi phía −, b nằm phía + của a
            gap = b.face - a.face
            if 0 < gap < CORR_MERGE * scale and min(a.hi, b.hi) - max(a.lo, b.lo) > 0:
                parent[root(id(a))] = root(id(b))
    groups = {}
    for ch in corr:
        groups.setdefault(root(id(ch)), []).append(ch)
    used, out = set(), []
    for grp in groups.values():
        ups = [ch for ch in grp if ch.sgn > 0]
        downs = [ch for ch in grp if ch.sgn < 0]
        if not ups or not downs:
            continue
        used.update(id(ch) for ch in grp)
        refs = []
        for ch in grp:
            refs += ch.refs
        face_a, face_b = max(ch.face for ch in ups), min(ch.face for ch in downs)
        bands = [ch.band for ch in grp if ch.band is not None]
        band = (min(b[0] for b in bands), max(b[1] for b in bands)) if bands else None
        out.append(Chain(grp[0].ax, (face_a + face_b) / 2.0, min(ch.lo for ch in grp), max(ch.hi for ch in grp),
                         (face_a + face_b) / 2.0, 0.0, u"hành lang (gộp {} tuyến)".format(len(grp)), refs, None,
                         band))
    return [ch for ch in chains if id(ch) not in used] + out


def wall_chains(view, walls, align, opens, struct, gx, gy, scale, dtype, z, public, log, occ):
    chains = plan_chains(walls, align, opens, struct, gx, gy, scale, z, public)
    chains = merge_corridors(chains, scale)
    n_ext = extend_chains(chains, walls, struct, gx, gy, opening_stoppers(view.GenLevel, view))
    if n_ext:
        log.append([u"", u"", u"", u"kéo dài đầu chuỗi tới tường gặp đầu tiên", n_ext, u""])
    chains, n_cut = clip_apartments(chains, z, public)
    if n_cut:
        log.append([u"", u"", u"", u"cắt đoạn chuỗi đi qua căn hộ / lõi", n_cut, u""])
    n_dim, n_moved, n_stuck = 0, 0, 0
    for ch in chains:
        chain = dedupe(ch.refs)
        d = dim_no_tiny(view, ch.ax, ch.pos, ch.lo, ch.hi, chain, ch.refs, dtype, z)
        row = [u"X" if ch.ax else u"Y", u"{:.0f}".format(ch.c), u"{:.0f}–{:.0f}".format(ch.lo, ch.hi), ch.kind,
               len(chain)]
        if d is None:
            log.append(row + [u"LỖI tạo dim"])
            continue
        n_dim += 1
        # Phía thử trước: chuỗi mặt ngoài → phía tường (phía ngoài là chuỗi trục); chuỗi hành lang một bên → lòng
        # hành lang; chuỗi gộp giữa hành lang (sgn = 0) → cả hai phía
        if ch.sgn == 0:
            sides = (1.0, -1.0)
        elif ch.kind == u"mặt ngoài":
            sides = (-ch.sgn, ch.sgn)
        else:
            sides = (ch.sgn, -ch.sgn)
        mv, st = place_texts(d, ch.ax, ch.pos, ch.lo, ch.hi, sides, scale, occ)
        n_moved += mv
        n_stuck += st
        log.append(row + [u"{} đoạn{}".format(max(d.NumberOfSegments, 1),
                                              u", {} chữ còn chồng".format(st) if st else u"")])
    return n_dim, n_moved, n_stuck


def plan_chains(walls, align, opens, struct, gx, gy, scale, z, public):
    opt = Options()
    opt.ComputeReferences = True
    chains = []
    solids = []                                          # hộp bao tường (mm) + cột / vách KC – dò "ngoài nhà"
    for q in walls:
        bb = q.w.get_BoundingBox(None)
        solids.append((to_mm(bb.Min.X), to_mm(bb.Min.Y), to_mm(bb.Max.X), to_mm(bb.Max.Y)))
    solids += [(x0, y0, x1, y1) for x0, y0, x1, y1, _f in struct]
    for ax, g in align:
        lo, hi = min(o.lo for o in g), max(o.hi for o in g)
        c = sum(o.c for o in g) / float(len(g))
        hw = max(o.hw for o in g)
        k = [[0, 0, 0], [0, 0, 0]]
        s = lo + SIDE_PROBE
        while s < hi - SIDE_PROBE:
            for si in (0, 1):
                off = (-1.0 if si == 0 else 1.0) * (hw + SIDE_PROBE)
                kd = side_kind(s, c + off, z, public, solids) if ax else side_kind(c + off, s, z, public, solids)
                k[si][kd] += 1
            s += SIDE_STEP
        pick, gap, kind = None, 0.0, u""
        for si in (0, 1):
            if k[si][0] > k[si][1] + k[si][2]:
                pick, gap, kind = si, WALL_EXT * scale, u"mặt ngoài"
        if pick is None:
            for si in (0, 1):
                if k[si][1] > k[si][2]:
                    pick, gap, kind = si, WALL_INT * scale, u"hành lang"
        if pick is None:
            continue
        sgn = -1.0 if pick == 0 else 1.0
        pos = c + sgn * (hw + gap)
        blo, bhi = c - hw - BAND_PAD, c + hw + BAND_PAD
        refs = []
        for q in walls:                                  # tường vuông góc chạm tuyến → mặt lõi
            if q.ax == ax or q.hi < blo or q.lo > bhi or not lo - 150.0 <= q.c <= hi + 150.0:
                continue
            refs += [(cd, r, PRI_CORE) for cd, r in q.cores]
        edges = []
        ids = set(id_value(o.w.Id) for o in g)
        for wid in ids:                                  # cửa trên tuyến → 2 mép khuôn
            for (ca, ra), (cb, rb) in opens.get(wid, []):
                refs += [(ca, ra, PRI_OPEN), (cb, rb, PRI_OPEN)]
                edges += [ca, cb]
        for o in g:                                      # đầu tường của tuyến (bỏ má cửa)
            geo = o.w.get_Geometry(opt)
            for gob in (geo or []):
                if not isinstance(gob, Solid):
                    continue
                for f in gob.Faces:
                    if not isinstance(f, PlanarFace) or f.Reference is None:
                        continue
                    nv = f.FaceNormal
                    if (abs(nv.X) if ax else abs(nv.Y)) < 0.999:
                        continue
                    cd = to_mm(f.Origin.X if ax else f.Origin.Y)
                    if any(abs(e - cd) < OPEN_SKIP for e in edges):
                        continue
                    ub = f.GetBoundingBox()
                    pm = f.Evaluate((ub.Min + ub.Max) / 2.0)
                    if abs(to_mm(pm.Y if ax else pm.X) - c) > hw + 5.0:
                        continue
                    refs.append((cd, f.Reference, PRI_END))
        for x0, y0, x1, y1, faces in struct:             # cột / vách kết cấu chạm tuyến
            slo, shi = (y0, y1) if ax else (x0, x1)
            alo, ahi = (x0, x1) if ax else (y0, y1)
            if shi < blo or slo > bhi or ahi < lo - 150.0 or alo > hi + 150.0:
                continue
            refs += [(cd, r, PRI_STRUCT) for fx, cd, r in faces if fx == ax]
        refs += [(cd, r, PRI_GRID) for cd, r in (gx if ax else gy) if lo - 1.0 < cd < hi + 1.0]
        chains.append(Chain(ax, c, lo, hi, pos, sgn, kind, refs, c + sgn * hw, (blo, bhi)))
    return chains


# --- Legend ghi chú tường ---------------------------------------------------------------
class NoteDraw(object):
    """Vẽ trong legend theo mm giấy (gốc 0,0 = góc trên trái)."""

    def __init__(self, view, t_title, t_body):
        self.view, self.s = view, view.Scale
        self.t_title, self.t_body = t_title, t_body

    def Q(self, x, y):
        return XYZ(from_mm(x * self.s), from_mm(y * self.s), 0)

    def line(self, a, b):
        doc.Create.NewDetailCurve(self.view, Line.CreateBound(self.Q(a[0], a[1]), self.Q(b[0], b[1])))

    def text(self, x, y, width, value, tt=None, center=False):
        opts = TextNoteOptions((tt or self.t_body).Id)
        if center:
            opts.HorizontalAlignment = HorizontalTextAlignment.Center
        tn = TextNote.Create(doc, self.view.Id, self.Q(x, y), from_mm(width), value, opts)
        doc.Regenerate()
        bb = tn.get_BoundingBox(self.view)
        return tn, (to_mm(bb.Max.Y - bb.Min.Y) / self.s if bb is not None else 3.0)

    def swatch(self, x0, x1, cy, frt):
        loop = CurveLoop()
        pts = [self.Q(x0 + 2.0, cy + 2.2), self.Q(x1 - 2.0, cy + 2.2), self.Q(x1 - 2.0, cy - 2.2),
               self.Q(x0 + 2.0, cy - 2.2)]
        for i in range(4):
            loop.Append(Line.CreateBound(pts[i], pts[(i + 1) % 4]))
        loops = List[CurveLoop]()
        loops.Add(loop)
        FilledRegion.Create(doc, frt.Id, self.view.Id, loops)


def note_rows(walls, struct_mats, mats, warns):
    """Mỗi vật liệu lõi một dòng: (FilledRegionType | None, mô tả, 'dày lõi …'). Vật liệu chỉ có ở cột / vách
    link KC (G19: tường VBT-150 của file là gờ logia, thấp hơn mặt cắt) → chiều dày ghi 'Theo hồ sơ KC'."""
    groups = {}
    for wi in walls:
        groups.setdefault(norm(wi.mat), set()).add(int(round(wi.core_mm)))
    for m in struct_mats:
        groups.setdefault(m, set())
    rows = []
    for mat, cores in sorted(groups.items()):
        hit = next((m for m in mats if m[0] and m[0] in mat.lower()), None)
        frt, desc = None, mat or u"(chưa gán vật liệu)"
        if hit is not None:
            desc = hit[2] or desc
            frt = by_name(FilledRegionType, hit[1]) if hit[1] else None
            if hit[1] and frt is None:
                warns.append(u"Không có filled region type '{}' → ô ký hiệu '{}' để trống.".format(hit[1], desc))
        else:
            warns.append(u"Vật liệu lõi '{}' chưa có trong IN[11] → ghi tên vật liệu, không hatch.".format(mat))
        val = u", ".join(u"{}".format(c) for c in sorted(cores)) + u" mm" if cores else u"Theo hồ sơ KC"
        rows.append((frt, desc, val))
    return rows


def finish_note(walls):
    """Lưu ý trát: chỉ ghi khi mọi tường có trát dùng cùng một chiều dày lớp ngoài lõi."""
    ts = set()
    for wi in walls:
        cl = core_layers(doc.GetElement(wi.w.GetTypeId()))
        for t in (cl[1], cl[2]):
            if t > 0.5:
                ts.add(int(round(t)))
    if len(ts) == 1:
        return u"- Tường xây trát vữa dày {} mm mỗi mặt (theo cấu tạo type tường).".format(ts.pop())
    return None


def make_legend(name, walls, struct_mats, mats, rebuild, warns):
    """Legend bảng ký hiệu tường + lưu ý. Trả về (legend | None, cao mm giấy)."""
    t_title, t_body = by_name(TextNoteType, TEXT_TITLE), by_name(TextNoteType, TEXT_BODY)
    if t_title is None or t_body is None:
        warns.append(u"Thiếu text type '{}' / '{}' → không vẽ legend ghi chú.".format(TEXT_TITLE, TEXT_BODY))
        return None, 0.0
    legends = [v for v in FilteredElementCollector(doc).OfClass(View).ToElements()
               if v.ViewType == ViewType.Legend and not v.IsTemplate]
    old = next((v for v in legends if norm(get_name(v)) == norm(name)), None)
    if old is not None and not rebuild:
        warns.append(u"Dùng lại legend có sẵn '{}' (không vẽ lại – bật Làm lại để vẽ lại).".format(name))
        return old, LEGEND_H_GUESS
    if old is not None:
        delete_ids([e for e in FilteredElementCollector(doc, old.Id).WhereElementIsNotElementType().ToElements()
                    if e.OwnerViewId == old.Id and isinstance(e, (TextNote, CurveElement, FilledRegion))])
        view = old
    else:
        src = next((v for v in legends if v.CanViewBeDuplicated(ViewDuplicateOption.Duplicate)), None)
        if src is None:
            warns.append(u"File chưa có legend nào để nhân bản → bỏ qua bảng ghi chú (tạo 1 legend trống rồi chạy lại).")
            return None, 0.0
        view = doc.GetElement(src.Duplicate(ViewDuplicateOption.Duplicate))
        view.Name = name
    try:
        view.Scale = LEGEND_SCALE
    except Exception:
        pass
    nd = NoteDraw(view, t_title, t_body)
    xs = [0.0]
    for w in NOTE_COLS:
        xs.append(xs[-1] + w)
    W = xs[-1]
    nd.line((0.0, 0.0), (W, 0.0))
    nd.text(W / 2.0, -2.0, W, u"BẢNG KÝ HIỆU GHI CHÚ TƯỜNG", t_title, True)
    y = -7.5
    nd.line((0.0, y), (W, y))
    y_cols = y
    for i, hd in enumerate((u"Kí hiệu", u"Loại", u"Chiều dày lõi")):
        nd.text((xs[i] + xs[i + 1]) / 2.0, y - 1.6, NOTE_COLS[i] - 2.0, hd, center=True)
    y -= 6.0
    nd.line((0.0, y), (W, y))
    for frt, desc, val in note_rows(walls, struct_mats, mats, warns):
        tn, h = nd.text(xs[1] + 1.5, y - 1.5, NOTE_COLS[1] - 3.0, desc)
        rh = max(7.0, h + 3.0)
        cy = y - rh / 2.0
        tn.Coord = nd.Q(xs[1] + 1.5, cy + h / 2.0)
        if frt is not None:
            nd.swatch(xs[0], xs[1], cy, frt)
        nd.text((xs[2] + xs[3]) / 2.0, cy + 1.3, NOTE_COLS[2] - 2.0, val, center=True)
        y -= rh
        nd.line((0.0, y), (W, y))
    for x in xs[1:-1]:
        nd.line((x, y_cols), (x, y))
    notes = [u"Lưu ý:",
             u"- Kích thước định vị ghi đến mặt tường xây thô (chưa trát), má lỗ cửa đi / cửa sổ trên tường thô "
             u"và mặt cột, vách BTCT."]
    fn = finish_note(walls)
    if fn:
        notes.append(fn)
    notes += [u"- Cột, vách BTCT xem hồ sơ kết cấu.",
              u"- Chi tiết tường căn hộ, vệ sinh, logia xem bản vẽ chi tiết căn hộ tương ứng."]
    y -= 1.2
    for note in notes:
        _tn, h = nd.text(1.5, y, W - 3.0, note)
        y -= h + 0.6
    y -= 1.0
    nd.line((0.0, y), (W, y))
    nd.line((0.0, 0.0), (0.0, y))
    nd.line((W, 0.0), (W, y))
    return view, -y


# --- Sheet --------------------------------------------------------------------------------
def outline_mm(vp):
    o = vp.GetBoxOutline()
    return (to_mm(o.MinimumPoint.X), to_mm(o.MinimumPoint.Y), to_mm(o.MaximumPoint.X), to_mm(o.MaximumPoint.Y))


def move_vp(vp, dx_mm, dy_mm):
    c = vp.GetBoxCenter()
    vp.SetBoxCenter(XYZ(c.X + from_mm(dx_mm), c.Y + from_mm(dy_mm), c.Z))


def place_label(vp, o, warns):
    """Tên hình ngay dưới đầu trục, mép trái thẳng tường ngoài cùng, gạch chân dài bằng mặt bằng. LabelOffset tính
    từ góc dưới trái khung viewport (đo G19 2026-11-03) → đặt lúc link đang tạm ẩn, khung như sau khi KTS tắt
    Grids của link. Mặc định Revit để tên lệch trái ra ngoài khung tên (G19 lần chạy đầu)."""
    try:
        vp.LabelOffset = XYZ(0, 0, 0)
        doc.Regenerate()
        lo = vp.GetLabelOutline()
        top = to_mm(lo.MaximumPoint.Y) - o[1]
        left = to_mm(lo.MinimumPoint.X) - o[0]
        vp.LabelOffset = XYZ(from_mm(CROP_PAD - left), from_mm(-LABEL_GAP - top), 0)
        vp.LabelLineLength = from_mm(max(50.0, o[2] - o[0] - 2 * CROP_PAD))
    except Exception as ex:
        warns.append(u"Không đặt được vị trí tên hình ({}) – kéo tay.".format(ex))


def set_sheet_group(sh, text, warns):
    """Ghi tham số nhóm Project Browser (VD 01_GiaiDoan, 02_HangMuc) – thiếu tham số / chỉ đọc → cảnh báo."""
    done = []
    for item in split_list(text):
        name, sep, value = item.partition(u"=")
        name, value = norm(name), norm(value)
        if not sep or not name:
            continue
        p = sh.LookupParameter(name)
        if p is None or p.IsReadOnly:
            warns.append(u"Sheet không có tham số '{}' (hoặc chỉ đọc) → không xếp nhóm theo tham số này.".format(name))
            continue
        p.Set(value)
        done.append(u"{} = {}".format(name, value))
    return done


def empty_sheet(sh):
    """Sheet trống: không view / legend đặt lên, không bảng thống kê (trừ bảng revision của khung tên)."""
    if sh.IsPlaceholder or sh.GetAllPlacedViews().Count:
        return False
    return not any(not x.IsTitleblockRevisionSchedule
                   for x in FilteredElementCollector(doc, sh.Id).OfClass(ScheduleSheetInstance))


def make_sheet(number, name, tb, vp_type, plan, legend, warns, sh=None):
    """sh: sheet trống có sẵn (D:\\AI 2026-11-04) → đặt vào đó, giữ số hiệu / tên / khung tên."""
    if sh is None:
        sh = ViewSheet.Create(doc, tb.Id)
        sh.SheetNumber = number
        sh.Name = name
    vp = Viewport.Create(doc, sh.Id, plan.Id, XYZ(from_mm((AREA_X0 + AREA_X1) / 2.0), from_mm(400.0), 0))
    if vp_type is not None:
        vp.ChangeTypeId(vp_type.Id)
    # Trục của file link (ByHostView) không bị crop cắt → khung viewport phình (G19: 766 thay vì 698 mm). Đo và
    # căn vị trí khi TẠM ẩn link, rồi hiện lại – phòng khi không có filter IN[16] (khung đúng sau khi KTS tắt tay).
    links = List[ElementId]()
    for e in FilteredElementCollector(doc, plan.Id).OfClass(RevitLinkInstance).ToElements():
        if e.CanBeHidden(plan):
            links.Add(e.Id)
    if links.Count:
        plan.HideElements(links)
    doc.Regenerate()
    o = outline_mm(vp)
    move_vp(vp, (AREA_X0 + AREA_X1) / 2.0 - (o[0] + o[2]) / 2.0, AREA_Y1 - SHEET_PAD - o[3])
    doc.Regenerate()
    o = outline_mm(vp)
    place_label(vp, o, warns)
    if links.Count:
        plan.UnhideElements(links)
        doc.Regenerate()
    if o[0] < AREA_X0 - 0.5 or o[2] > AREA_X1 + 0.5:
        warns.append(u"MB rộng {:.0f} mm giấy, vượt vùng vẽ {:.0f} mm → thêm tỷ lệ nhỏ hơn vào IN[3].".format(
            o[2] - o[0], AREA_X1 - AREA_X0))
    lvp = None
    if legend is not None:
        lvp = Viewport.Create(doc, sh.Id, legend.Id, XYZ(from_mm(150.0), from_mm(80.0), 0))
        nt = find_vp_type(u"No Title")
        if nt is not None:
            lvp.ChangeTypeId(nt.Id)
        doc.Regenerate()
        lo = outline_mm(lvp)
        move_vp(lvp, AREA_X0 + SHEET_PAD - lo[0], AREA_Y0 + SHEET_PAD - lo[1])
        doc.Regenerate()
        lo = outline_mm(lvp)
        if lo[3] > o[1] - 2.0:
            warns.append(u"Legend chồng lên MB trên sheet – kéo lại tay hoặc dùng tỷ lệ nhỏ hơn.")
    return sh, vp, lvp


# --- Chính --------------------------------------------------------------------------------
def make_warning_swallower(failed):
    """Nuốt cảnh báo; lỗi chỉ dính dim tự động → xóa dim đó thay vì hủy cả lượt (như ARV_DanTrangCanHo_v2).
    Khai báo lớp trong hàm, namespace riêng mỗi lần chạy (pythonnet không cho khai báo lại cùng tên)."""
    ns = "ARV.MBTuongXayTang.R" + datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    try:
        class SwallowWarnings(IFailuresPreprocessor):
            __namespace__ = ns

            def PreprocessFailures(self, fa):
                fixed = False
                for m in list(fa.GetFailureMessages()):
                    sev = m.GetSeverity()
                    if sev == FailureSeverity.Warning:
                        fa.DeleteWarning(m)
                    elif sev == FailureSeverity.Error:
                        d = fa.GetDocument()
                        ids = list(m.GetFailingElementIds())
                        els = [d.GetElement(i) for i in ids]
                        if els and all(e is not None and e.Category is not None and
                                       e.Category.BuiltInCategory == BuiltInCategory.OST_Dimensions for e in els):
                            lst = List[ElementId]()
                            for i in ids:
                                lst.Add(i)
                            fa.DeleteElements(lst)
                            failed.append(u"{} ({})".format(m.GetDescriptionText(), len(ids)))
                            fixed = True
                return FailureProcessingResult.ProceedWithCommit if fixed else FailureProcessingResult.Continue
        return SwallowWarnings()
    except Exception:
        return None


def log_folder():
    import tempfile
    for base in (os.path.join(os.path.expanduser("~"), "Documents"), tempfile.gettempdir()):
        folder = os.path.join(base, "ARV_Logs")
        try:
            if not os.path.isdir(folder):
                os.makedirs(folder)
            return folder
        except Exception:
            continue
    raise IOError(u"Không tạo được thư mục log")


LOG_HEADER = [u"Phương", u"Tim tuyến (mm)", u"Phạm vi (mm)", u"Phía đặt", u"Số mốc", u"Kết quả"]


def write_log(rows, level_name, dry_run):
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(log_folder(), "MBTuongXayTang_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(u"# Dự án: {}\n# Level: {}\n# Ngày: {}\n# Chế độ: {}\n".format(
            doc.Title, level_name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            u"Chạy thử (dry-run)" if dry_run else u"Thực hiện"))
        w = csv.writer(f)
        w.writerow(LOG_HEADER)
        w.writerows(rows)
    return path


def main(level_name, view_name, tmpl_name, scale_text, number, sheet_name, tb_name, vp_name, dim_grid_name,
         dim_wall_name, legend_name, mat_text, public_text, dry_run, rebuild, group_text=u"", grid_filter=u"",
         place=True):
    if is_central_file(doc):
        raise StopReport([u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."])
    if level_name.strip():
        level = by_name(Level, level_name)
        if level is None:
            raise StopReport([u"DỪNG: không có level '{}'.".format(level_name)])
    else:
        av = doc.ActiveView
        level = av.GenLevel if av.ViewType == ViewType.FloorPlan else None
        if level is None:
            raise StopReport([u"DỪNG: IN[0] trống và view đang mở không phải mặt bằng."])
    try:
        scales = [int(float(s)) for s in split_list(scale_text)]
    except ValueError:
        raise StopReport([u"DỪNG: IN[3] tỷ lệ '{}' không hợp lệ.".format(scale_text)])
    if not scales or not view_name.strip() or (place and not number.strip()):
        raise StopReport([u"DỪNG: thiếu tỷ lệ (IN[3]), tên view (IN[1]) hoặc số sheet (IN[4])."])
    template = None
    if tmpl_name.strip():
        template = next((v for v in FilteredElementCollector(doc).OfClass(View).ToElements()
                         if v.IsTemplate and norm(get_name(v)) == norm(tmpl_name)), None)
        if template is None:
            raise StopReport([u"DỪNG: không có view template '{}'.".format(tmpl_name)])
    # Sheet (D:\AI 2026-11-04): IN[17] False → không đụng sheet; số hiệu là sheet trống có sẵn → đặt vào đó
    old_sheets = [s for s in FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()
                  if place and norm(s.SheetNumber) == norm(number)]
    target = next((s for s in old_sheets if empty_sheet(s)), None)
    if target is not None:
        old_sheets = [s for s in old_sheets if s.Id != target.Id]
    tb = find_type(BuiltInCategory.OST_TitleBlocks, tb_name) if place and target is None else None
    vp_type = find_vp_type(vp_name) if vp_name.strip() else None
    dt_grid, dt_wall = by_name(DimensionType, dim_grid_name), by_name(DimensionType, dim_wall_name)
    lack = [n for n, e in ((u"khung tên '{}'".format(tb_name), tb if place and target is None else True),
                           (u"dim type '{}'".format(dim_grid_name), dt_grid),
                           (u"dim type '{}'".format(dim_wall_name), dt_wall)) if e is None]
    if vp_name.strip() and vp_type is None:
        lack.append(u"viewport type '{}'".format(vp_name))
    if lack:
        raise StopReport([u"DỪNG: file không có " + u", ".join(lack) + u" (tool không tự tạo type)."])
    public = set(norm(s) for s in split_list(public_text))

    old_views = [v for v in FilteredElementCollector(doc).OfClass(ViewPlan).ToElements()
                 if not v.IsTemplate and norm(get_name(v)) == norm(view_name)]
    if (old_views or old_sheets) and not rebuild:
        raise StopReport([u"DỪNG: đã có view '{}' ({}) / sheet '{}' ({}) – bật IN[14] Làm lại để dựng lại, "
                          u"hoặc đổi tên / số sheet.".format(view_name, len(old_views), number, len(old_sheets))])
    foreign = [s for s in old_sheets if norm(s.Name) != norm(sheet_name)]
    if foreign:
        raise StopReport([u"DỪNG: số sheet {} đang dùng cho '{}' – đổi IN[4].".format(number, foreign[0].Name)])
    reuse = [v for v in old_views if v.GenLevel is not None and v.GenLevel.Id == level.Id][:1]   # giữ, không xóa
    locked = [get_name(e) for e in old_views + old_sheets
              if e not in reuse and not DocumentValidation.CanDeleteElement(doc, e.Id)]
    if locked:
        raise StopReport([u"DỪNG: không xóa được {} (đang mở trong Revit?) – đóng tab rồi chạy lại.".format(
            u", ".join(locked))])

    warns, failed, log = [], [], []
    z = level.Elevation + from_mm(CUT_Z)
    if TransactionManager is not None:
        TransactionManager.Instance.ForceCloseTransaction()
    tx = Transaction(doc, TRANSACTION_NAME)
    sw = make_warning_swallower(failed)
    if sw is not None:
        fo = tx.GetFailureHandlingOptions()
        fo.SetFailuresPreprocessor(sw)
        tx.SetFailureHandlingOptions(fo)
    tx.Start()
    try:
        keep = next((v for v in old_views if v.GenLevel is not None and v.GenLevel.Id == level.Id), None)
        drop = [v for v in old_views if keep is None or v.Id != keep.Id]
        if old_views or old_sheets:
            warns.append(u"Làm lại – {}xóa {} view, {} sheet cũ.".format(
                u"dùng lại view '{}' (giữ VG, dựng lại dim), ".format(get_name(keep)) if keep is not None else u"",
                len(drop), len(old_sheets)))
            delete_ids(drop + old_sheets)
        walls = collect_walls(level)
        if not walls:
            raise StopReport([u"DỪNG: level {} không có tường lõi ≥ {:.0f} mm.".format(level.Name, CORE_MIN)])
        box = walls_box(walls)
        struct_mats = set()
        struct = collect_structure(level, warns, struct_mats)
        legend, legend_h = (make_legend(legend_name.strip(), walls, struct_mats, parse_materials(mat_text), rebuild,
                                        warns) if legend_name.strip() else (None, 0.0))
        scale = pick_scale(scales, box, legend_h)
        view = make_view(level, view_name.strip(), template, scale, box, keep)
        if hide_by_filter(view, grid_filter, warns):
            warns.append(u"Đã ẩn trục không phải kiến trúc (link KC) bằng filter '{}'.".format(grid_filter.strip()))
        gx, gy = fit_grids(view, box, scale, warns)
        occ = []                                         # ô chữ / đường dim đã đặt – chữ dim không chồng nhau
        n_grid = grid_dims(view, box, gx, gy, scale, dt_grid, z, occ)
        opens = collect_openings(level, view)
        align = make_alignments(walls)
        n_wall, n_moved, n_stuck = wall_chains(view, walls, align, opens, struct, gx, gy, scale, dt_wall, z, public,
                                               log, occ)
        if n_stuck:
            warns.append(u"Còn {} chữ dim không tìm được chỗ trống (xem cột Kết quả) – KTS kéo tay.".format(n_stuck))
        sheet, group = None, []
        if place:
            sheet, vp, lvp = make_sheet(number.strip(), sheet_name.strip(), tb, vp_type, view, legend, warns, target)
            if target is None:
                group = set_sheet_group(sheet, group_text, warns)
            else:
                warns.append(u"Đặt vào sheet trống có sẵn {} '{}' (giữ tên, khung tên, tham số).".format(
                    sheet.SheetNumber, sheet.Name))
            p = view.get_Parameter(BuiltInParameter.VIEW_DESCRIPTION)
            if p is not None and not p.IsReadOnly:
                p.Set(sheet.Name)
        summary = [u"Level {} – view '{}' 1/{} – {}".format(level.Name, get_name(view), scale,
                                                            u"sheet {} '{}'".format(sheet.SheetNumber, sheet.Name)
                                                            if sheet is not None else u"không đặt lên sheet (IN[17])"),
                   u"Tường lõi ≥ {:.0f}: {} đoạn, {} tuyến; trục {} dọc / {} ngang".format(
                       CORE_MIN, len(walls), len(align), len(gx), len(gy)),
                   u"Dim trục: {} – chuỗi định vị tường: {} (dời {} chữ dim tránh chồng, còn chồng {})".format(
                       n_grid, n_wall, n_moved, n_stuck),
                   u"Legend: {}".format(get_name(legend) if legend is not None else u"(không)"),
                   u"Nhóm sheet: {}".format(u"; ".join(group) or u"(không)")]
        if dry_run:
            tx.RollBack()
        else:
            tx.Commit()
    except Exception:
        if tx.HasStarted() and not tx.HasEnded():
            tx.RollBack()
        raise

    report = [u"{} – {} – Làm lại: {}".format(TRANSACTION_NAME, u"CHẠY THỬ (đã dựng rồi hoàn tác)" if dry_run
                                              else u"ĐÃ THỰC HIỆN", u"CÓ" if rebuild else u"KHÔNG")]
    report += summary
    if failed:
        warns.append(u"Revit báo lỗi dim tự động → đã xóa dim đó: " + u"; ".join(failed))
    report += [u"CẢNH BÁO: " + w for w in warns]
    report.append(u"CHƯA LÀM: tag căn hộ, chi tiết điển hình cột vách giao tường xây, dim trong lòng căn. "
                  u"Dim tự động là bản nháp – KTS soát.")
    try:
        report.append(u"Log: " + write_log(log, level.Name, dry_run))
    except Exception as ex:
        report.append(u"Không ghi được log: {}".format(ex))
    if dry_run:
        report.append(u"Đúng thì đổi Dry-run = False và Run lại. Undo bằng mục \"{}\".".format(TRANSACTION_NAME))
    report.append(u" | ".join(LOG_HEADER))
    report += [u" | ".join(u"{}".format(v) for v in r) for r in log]
    return report, []


if DYNAMO:
    import traceback

    def _in(i, default):
        v = IN[i] if len(IN) > i else None
        return default if v is None else v

    try:
        OUT = list(main(
            _in(0, u""),
            _in(1, u"MB TƯỜNG XÂY TẦNG ĐIỂN HÌNH"),
            _in(2, u"TC.04.MatBangTuongXay"),
            u"{}".format(_in(3, u"100;150")),
            u"{}".format(_in(4, u"A140")),
            _in(5, u"MẶT BẰNG TƯỜNG XÂY TẦNG ĐIỂN HÌNH"),
            _in(6, u"AV-Khung A1(841x594)-Kien Truc"),
            _in(7, u"AV-Title No Line"),
            _in(8, u"AV_Dim 2.2mm_Cut dim 6mm"),
            _in(9, u"AV_Dim 2.2mm_Cut dim 4mm"),
            _in(10, u"GHI CHÚ TƯỜNG XÂY TẦNG ĐIỂN HÌNH"),
            _in(11, u"GachNung=AV_Hatch Gach Xay|Tường gạch đặc nung;BeTong=AV_Hatch BTCT|Cột, vách BTCT"),
            _in(12, u"Hành lang"),
            bool(_in(13, True)),
            bool(_in(14, False)),
            _in(15, u"01_GiaiDoan=03_TKBVTC;02_HangMuc=04_MatBangTuongXay"),
            _in(16, u"Trục + Level- Kiến Trúc-Not"),
            bool(_in(17, True)),
        ))
    except StopReport as ex:
        OUT = [ex.lines, []]
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], []]
