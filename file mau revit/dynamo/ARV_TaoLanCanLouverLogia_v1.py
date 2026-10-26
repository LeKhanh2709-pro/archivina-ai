# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong ARV_TaoLanCanLouverLogia_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Tạo lan can + louver che cục nóng điều hòa cho logia, lấy thông tin từ mặt bằng DWG đã Link (KTS chốt 2026-10-21):
#   1. Logia = sàn (Floor) trên level IN[9] có tên type chứa IN[2] (VD "SHT-Gach Lat Logia-300x600"), lấy hộp bao.
#   2. Mặt ngoài logia = cặp nét song song cách nhau 150 mm (± 3) trên layer IN[1], nằm sát cạnh hộp bao logia
#      (≤ 300 mm) và phủ ≥ 50 % cạnh đó. Tuyến lan can = đường giữa cặp nét, dài từ tường đến tường (đầu nét CAD).
#      Nét dài hơn logia (chạy qua phòng bên cạnh) → cắt ở cạnh logia rồi bắt vào đầu tường Revit nằm trên tuyến
#      (≤ 400 mm); không có tường → giữ mép logia, báo "KIỂM TRA ĐẦU".
#   3. Cục nóng = cụm nét layer IN[6] nằm gọn trong khung IN[7] (dài x rộng, xoay 0/90°) có ≥ IN[8] nét.
#      - Logia không có cục nóng: lan can suốt chiều dài.
#      - Logia có cục nóng: louver (family IN[4], type IN[5], rộng = Width của type) đặt sát đầu tường GẦN cục nóng
#        hơn, lan can = tổng chiều dài − rộng louver (một đoạn).
#      - Lan can còn lại < IN[11] (1200) → bỏ lan can, louver kéo dài hết tuyến (KTS chốt 2026-10-21). Type louver
#        đúng bề rộng (Height như type IN[5]) có sẵn thì dùng, chưa có → nhân bản IN[5] thành "{rộng}X{cao}".
#   4. Lan can: Railing type IN[3], chân tại level, tuyến trên đường giữa cặp nét. Louver: family không host, điểm chèn
#      ở một đầu, phát triển theo +Hand, Facing quay ra ngoài nhà; đặt xong đo khối đặc theo phương vuông góc tuyến
#      rồi dời cho tâm bề dày lam nằm đúng giữa cặp nét 150 (AV-Lam Thép Logia2: khối 0…80 mm về phía Facing).
#      Chân lan can + louver (KTS chốt 2026-10-21): logia có gờ bê tông (tường Comments "ARV-GoLogia" của
#      ARV_TaoGoLogia_v1) trên cùng tuyến → đặt ở đỉnh gờ (VD +70 so với level); không có gờ → ở cao độ level (0).
#   5. Phần tử tạo ra có Comments "ARV-LanCanLogia". Chạy lại, trong phạm vi tuyến từng logia:
#      - Lan can / louver có Comments đó mà đúng kế hoạch (đầu tuyến ± 20 mm, louver đúng bề rộng) → giữ;
#        chỉ sai chân (lệch > 2 mm so với đỉnh gờ / level) → nâng / hạ chân tại chỗ (giữ Id, báo "nâng chân").
#      - Có Comments đó mà sai kế hoạch (VD lan can ngắn của lần chạy trước) → XOÁ rồi tạo lại (báo "thay").
#      - Không có Comments đó (dựng tay) → không đụng; phần tương ứng bỏ qua, báo "đã có (dựng tay)".
# INPUT
#   IN[0]  (str)   Một phần tên bản CAD (trống = bản CAD duy nhất có layer khớp IN[1])
#   IN[1]  (str)   Layer nét mặt ngoài logia, cách nhau ';' (khớp đúng tên) – VD "A-Line;A-line1;A-line2"
#   IN[2]  (str)   Chuỗi con tên floor type sàn logia – VD "Logia"
#   IN[3]  (str)   Railing type lan can – VD "Glass Panel - Bottom Fill" (sau thay "AV_Lan Can Kính Cường Lực")
#   IN[4]  (str)   Family louver – VD "AV-Lam Thép Logia2"
#   IN[5]  (str)   Type louver – VD "1000X2800"
#   IN[6]  (str)   Layer nét cục nóng – VD "0" (block cục nóng vẽ trên layer 0)
#   IN[7]  (str)   Khung cục nóng dài x rộng (mm) – VD "974x400"
#   IN[8]  (int)   Số nét tối thiểu trong khung để nhận là cục nóng – VD 150 (G19: 213 nét / cục)
#   IN[9]  (str)   Level – VD "Tầng 1"
#   IN[10] (bool)  Dry-run: True = chỉ báo cáo + xem trước, không ghi vào mô hình (mặc định True)
#   IN[11] (float) Lan can ngắn nhất (mm); ngắn hơn → louver kéo dài hết tuyến – VD 1200
# OUTPUT
#   OUT[0] (list[str])  Báo cáo: tóm tắt, đường dẫn log, rồi từng logia
#   OUT[1] (list[Line]) Xem trước: tuyến lan can, đoạn louver, vạch 600 mm chỉ ra ngoài (mm)

import os
import io
import csv
import math
import datetime
import unicodedata

DYNAMO = "IN" in globals()

if DYNAMO:
    import clr
    clr.AddReference("RevitAPI")
    from Autodesk.Revit.DB import (FilteredElementCollector, ImportInstance, Options, GeometryInstance, PolyLine,
                                   Line, Curve, XYZ, Transaction, UnitUtils, UnitTypeId, ModelPathUtils,
                                   BuiltInParameter, Level, Wall, Floor, LocationCurve, FamilySymbol, CurveLoop,
                                   ElementTransformUtils, FamilyInstance, ElementId, Solid, ViewDetailLevel)
    from Autodesk.Revit.DB.Architecture import Railing, RailingType
    from Autodesk.Revit.DB.Structure import StructuralType
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = u"ARV - Tạo lan can và louver logia từ CAD"
SCRIPT_TAG = u"ARV_TaoLanCanLouverLogia_v1"
COMMENT = u"ARV-LanCanLogia"
CURB_COMMENT = u"ARV-GoLogia"   # Gờ bê tông của ARV_TaoGoLogia_v1
PAIR_GAP_MM = 150.0       # Bề dày nét đôi mặt ngoài
PAIR_TOL_MM = 3.0
EDGE_MM = 300.0           # Cặp nét cách cạnh logia tối đa
COVER = 0.5               # Cặp nét phủ tối thiểu cạnh logia
SNAP_WALL_MM = 400.0      # Bắt đầu tường Revit khi nét dài hơn logia
ON_AXIS_MM = 50.0
EXIST_RAIL_MM = 50.0      # Lệch ngang tuyến để coi là cùng tuyến
SAME_END_MM = 20.0        # Đầu đoạn khớp kế hoạch
CENTRE_TOL_MM = 5.0       # Tâm bề dày louver lệch tim cặp nét tối đa
UNIT_TOL_MM = 3.0
SAME_Z_MM = 2.0           # Chân khớp kế hoạch


def norm(s):
    return unicodedata.normalize("NFC", (s or u"")).strip()


def fmt(p):
    return u"({:.0f}, {:.0f})".format(p[0], p[1])


# --- Hình học 2D thuần (mm) – chạy được ngoài Revit để thử --------------------------
class Facade(object):
    """Cặp nét đôi song song trục: axis 'H' (chạy theo X, line = y) hoặc 'V' (chạy theo Y, line = x)."""
    def __init__(self, axis, line, s, e, layer):
        self.axis, self.line, self.s, self.e, self.layer = axis, line, s, e, layer

    def point(self, t):
        return (t, self.line) if self.axis == 'H' else (self.line, t)


def axis_segments(segs):
    """segs [(a, b, layer)] → [(axis, line, s, e, layer)] chỉ đoạn song song trục X/Y (lệch ≤ 1 mm)."""
    out = []
    for a, b, layer in segs:
        if abs(a[1] - b[1]) <= 1.0 and abs(a[0] - b[0]) > 1.0:
            out.append(('H', (a[1] + b[1]) / 2.0, min(a[0], b[0]), max(a[0], b[0]), layer))
        elif abs(a[0] - b[0]) <= 1.0 and abs(a[1] - b[1]) > 1.0:
            out.append(('V', (a[0] + b[0]) / 2.0, min(a[1], b[1]), max(a[1], b[1]), layer))
    return out


def facade_pairs(segs):
    """Cặp nét cùng phương, cách nhau 150 ± 3, cùng hai đầu (± 3) → [Facade] trên đường giữa."""
    ax = axis_segments(segs)
    pairs, used = [], set()
    for i, p in enumerate(ax):
        if i in used:
            continue
        for j in range(i + 1, len(ax)):
            q = ax[j]
            if j in used or p[0] != q[0]:
                continue
            if (abs(abs(p[1] - q[1]) - PAIR_GAP_MM) <= PAIR_TOL_MM and abs(p[2] - q[2]) <= PAIR_TOL_MM
                    and abs(p[3] - q[3]) <= PAIR_TOL_MM):
                pairs.append(Facade(p[0], (p[1] + q[1]) / 2.0, (p[2] + q[2]) / 2.0, (p[3] + q[3]) / 2.0, p[4]))
                used.add(i)
                used.add(j)
                break
    return pairs


def match_facade(box, pairs):
    """Cặp nét mặt ngoài của logia (hộp bao x0, y0, x1, y1) → (Facade, lo, hi) hoặc None."""
    x0, y0, x1, y1 = box
    best = None
    for f in pairs:
        if f.axis == 'V':
            d, lo, hi = min(abs(f.line - x0), abs(f.line - x1)), y0, y1
        else:
            d, lo, hi = min(abs(f.line - y0), abs(f.line - y1)), x0, x1
        ov = min(f.e, hi) - max(f.s, lo)
        if d <= EDGE_MM and ov >= COVER * (hi - lo) and (best is None or d < best[0]):
            best = (d, f, lo, hi)
    return None if best is None else best[1:]


def outward(box, f):
    x0, y0, x1, y1 = box
    if f.axis == 'V':
        return (1.0 if f.line > (x0 + x1) / 2.0 else -1.0, 0.0)
    return (0.0, 1.0 if f.line > (y0 + y1) / 2.0 else -1.0)


def span_of(f, lo, hi, wall_ends):
    """Đoạn tuyến (s, e) + ghi chú. wall_ends: [(x, y)] đầu tường Revit."""
    notes = []
    s, e = f.s, f.e
    for side in (0, 1):
        val = s if side == 0 else e
        limit = lo - EDGE_MM if side == 0 else hi + EDGE_MM
        if (side == 0 and val >= limit) or (side == 1 and val <= limit):
            continue
        edge = lo if side == 0 else hi
        cand = []
        for p in wall_ends:
            off = p[1] - f.line if f.axis == 'H' else p[0] - f.line
            t = p[0] if f.axis == 'H' else p[1]
            if abs(off) <= ON_AXIS_MM and abs(t - edge) <= SNAP_WALL_MM:
                cand.append(t)
        if cand:
            val = min(cand, key=lambda t: abs(t - edge))
            notes.append(u"{} tuyến bắt đầu tường Revit".format(u"Đầu" if side == 0 else u"Cuối"))
        else:
            val = edge
            notes.append(u"KIỂM TRA ĐẦU – {} tuyến lấy mép logia (nét CAD dài hơn logia, không thấy tường)".format(
                u"đầu" if side == 0 else u"cuối"))
        if side == 0:
            s = val
        else:
            e = val
    return s, e, notes


def find_unit(boxes, size, min_count):
    """boxes [(x0, y0, x1, y1)] nét trong logia → khung cục nóng (x0, y0, x1, y1, số nét) hoặc None."""
    best = None
    for w, h in ((size[0], size[1]), (size[1], size[0])):
        xs = sorted(set(round(b[0]) for b in boxes))
        ys = sorted(set(round(b[1]) for b in boxes))
        for x in xs:
            col = [b for b in boxes if b[0] >= x - UNIT_TOL_MM and b[2] <= x + w + UNIT_TOL_MM]
            if len(col) < min_count:
                continue
            for y in ys:
                n = sum(1 for b in col if b[1] >= y - UNIT_TOL_MM and b[3] <= y + h + UNIT_TOL_MM)
                if n >= min_count and (best is None or n > best[4]):
                    best = (x, y, x + w, y + h, n)
    return best


class Plan(object):
    def __init__(self, fid, box):
        self.fid, self.box = fid, box
        self.facade = None
        self.s = self.e = None
        self.out = None
        self.unit = None
        self.louver = None      # (t0, t1)
        self.louver_type = None # FamilySymbol hoặc tên type sẽ nhân bản
        self.rail = None        # (t0, t1)
        self.base = 0.0         # chân lan can + louver so với level (mm): đỉnh gờ hoặc 0
        self.curb_id = u""      # gờ ARV-GoLogia trên tuyến
        self.lift_ids = []      # phần tử tool cũ đúng tuyến, sai chân → chỉnh chân
        self.notes = []
        self.status = u""
        self.rail_id = u""      # lan can giữ lại / đã tạo
        self.louver_id = u""
        self.need_rail = False  # phải tạo
        self.need_louver = False
        self.delete_ids = []    # phần tử tool cũ sai kế hoạch

    def pt(self, t):
        return self.facade.point(t)


def plan_logia(fid, box, pairs, wall_ends, unit_boxes, unit_size, unit_min, louver_w, min_rail):
    p = Plan(fid, box)
    m = match_facade(box, pairs)
    if m is None:
        p.status = u"Bỏ qua – không thấy cặp nét mặt ngoài dày 150"
        return p
    f, lo, hi = m
    p.facade = f
    p.out = outward(box, f)
    p.s, p.e, p.notes = span_of(f, lo, hi, wall_ends)
    if p.e - p.s <= 0:
        p.status = u"Bỏ qua – tuyến rỗng"
        return p
    p.unit = find_unit(unit_boxes, unit_size, unit_min)
    if p.unit is not None:
        if p.e - p.s < louver_w + 50.0:
            p.status = u"Bỏ qua – logia dài {:.0f} không đủ cho louver {:.0f}".format(p.e - p.s, louver_w)
            return p
        uc = (p.unit[1] + p.unit[3]) / 2.0 if f.axis == 'V' else (p.unit[0] + p.unit[2]) / 2.0
        if p.e - p.s - louver_w < min_rail:
            p.louver, p.rail = (p.s, p.e), None
            p.notes.append(u"lan can còn {:.0f} < {:.0f} → louver hết tuyến".format(p.e - p.s - louver_w, min_rail))
        elif abs(uc - p.s) <= abs(p.e - uc):
            p.louver, p.rail = (p.s, p.s + louver_w), (p.s + louver_w, p.e)
        else:
            p.louver, p.rail = (p.e - louver_w, p.e), (p.s, p.e - louver_w)
    else:
        p.rail = (p.s, p.e)
    p.status = u"OK"
    return p


def along(f, pt):
    """(toạ độ dọc tuyến, lệch ngang) của điểm so với tuyến f."""
    return (pt[0], pt[1] - f.line) if f.axis == 'H' else (pt[1], pt[0] - f.line)


def curb_base(p, curbs):
    """curbs [(a, b, Id, đỉnh)] gờ ARV-GoLogia (mm, so với level) → đặt p.base = đỉnh gờ trên cùng tuyến."""
    f = p.facade
    lo, hi = min(p.s, p.e), max(p.s, p.e)
    best = None
    for a, b, eid, top in curbs:
        ta, da = along(f, a)
        tb, db = along(f, b)
        if abs(da) > EXIST_RAIL_MM or abs(db) > EXIST_RAIL_MM:
            continue
        ov = min(max(ta, tb), hi) - max(min(ta, tb), lo)
        if ov > 0.5 * (hi - lo) and (best is None or ov > best[0]):
            best = (ov, eid, top)
    if best is not None:
        p.curb_id, p.base = best[1], best[2]
        p.notes.append(u"chân trên gờ Id {} ({:+.0f})".format(best[1], best[2]))


def reconcile(p, rails, louvers):
    """rails [(a, b, Id, của tool, chân)], louvers [(đầu, cuối, Id, của tool, tâm khối, chân)] (mm, điểm 2D) →
    đặt p.rail_id / louver_id (giữ), need_*, delete_ids, lift_ids, ghi chú."""
    f = p.facade
    lo, hi = min(p.s, p.e), max(p.s, p.e)

    def seg_on(a, b):
        ta, da = along(f, a)
        tb, db = along(f, b)
        if abs(da) > EXIST_RAIL_MM or abs(db) > EXIST_RAIL_MM:
            return None
        s, e = min(ta, tb), max(ta, tb)
        return (s, e) if min(e, hi) - max(s, lo) > 50.0 else None

    def louver_on(a, b):
        ta, da = along(f, a)
        tb, db = along(f, b)
        if abs(da) > 300.0 or abs(db) > 300.0:
            return None
        s, e = min(ta, tb), max(ta, tb)
        return (s, e) if min(e, hi) - max(s, lo) > 50.0 else None

    def same(x, want):
        return want is not None and abs(x[0] - want[0]) <= SAME_END_MM and abs(x[1] - want[1]) <= SAME_END_MM

    for items, want, kind in ((rails, p.rail, u"lan can"), (louvers, p.louver, u"louver")):
        keep = None
        for it in items:
            a, b, eid, mine = it[:4]
            x = seg_on(a, b) if kind == u"lan can" else louver_on(a, b)
            if x is None:
                continue
            centred = kind == u"lan can" or (it[4] is not None and abs(along(f, it[4])[1]) <= CENTRE_TOL_MM)
            z = it[-1]
            if not mine:
                keep = keep or eid
                p.notes.append(u"đã có {} dựng tay Id {}".format(kind, eid))
            elif same(x, want) and centred and keep is None:
                keep = eid
                if abs(z - p.base) > SAME_Z_MM:
                    p.lift_ids.append(eid)
                    p.notes.append(u"{} chân {} Id {} ({:+.0f} → {:+.0f})".format(
                        kind, u"nâng" if p.base > z else u"hạ", eid, z, p.base))
            else:
                p.delete_ids.append(eid)
                p.notes.append(u"thay {} cũ Id {} ({:.0f}{})".format(
                    kind, eid, x[1] - x[0], u"" if centred else u", lệch tim"))
        if kind == u"lan can":
            p.rail_id = keep or u""
            p.need_rail = p.rail is not None and keep is None
        else:
            p.louver_id = keep or u""
            p.need_louver = p.louver is not None and keep is None


# --- Revit ---------------------------------------------------------------------------
def to_mm(feet):
    return UnitUtils.ConvertFromInternalUnits(feet, UnitTypeId.Millimeters)


def from_mm(mm):
    return UnitUtils.ConvertToInternalUnits(mm, UnitTypeId.Millimeters)


def xy(p):
    return (to_mm(p.X), to_mm(p.Y))


def get_name(element):
    try:
        return element.Name
    except Exception:
        p = element.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
        return p.AsString() if p else u""


def is_central_file(document):
    if not document.IsWorkshared:
        return False
    try:
        central = ModelPathUtils.ConvertModelPathToUserVisiblePath(document.GetWorksharingCentralModelPath())
    except Exception:
        return False
    return os.path.normcase(central or "") == os.path.normcase(document.PathName or "")


class StopReport(Exception):
    def __init__(self, lines):
        Exception.__init__(self, lines[0])
        self.lines = lines


def layer_of(geo_obj):
    style = doc.GetElement(geo_obj.GraphicsStyleId)
    if style is not None and style.GraphicsStyleCategory is not None:
        return norm(style.GraphicsStyleCategory.Name)
    return None


def cad_objects(cad):
    opt = Options()
    if cad.ViewSpecific:
        opt.View = doc.GetElement(cad.OwnerViewId)
    result = []

    def walk(geo):
        for obj in geo:
            if isinstance(obj, GeometryInstance):
                walk(obj.GetInstanceGeometry())
            else:
                result.append(obj)

    geo = cad.get_Geometry(opt)
    if geo is not None:
        walk(geo)
    return result


def pick_cad(cad_filter, layers):
    found = []
    for inst in FilteredElementCollector(doc).OfClass(ImportInstance).ToElements():
        name = get_name(doc.GetElement(inst.GetTypeId()))
        if cad_filter and cad_filter.lower() not in name.lower():
            continue
        objects = cad_objects(inst)
        all_layers = set(l for l in (layer_of(o) for o in objects) if l)
        found.append((inst, name, objects, all_layers))
    hits = [f for f in found if f[3] & layers]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise StopReport([u"DỪNG: không có bản CAD{} nào có layer '{}'.".format(
            u" khớp '{}'".format(cad_filter) if cad_filter else u"", u"; ".join(sorted(layers)))])
    raise StopReport([u"DỪNG: {} bản CAD có layer khớp – nhập tên bản CAD vào ô IN[0]: {}".format(
        len(hits), u", ".join(h[1] for h in hits))])


def find_level(name):
    levels = list(FilteredElementCollector(doc).OfClass(Level).ToElements())
    for l in levels:
        if norm(l.Name) == norm(name):
            return l
    raise StopReport([u"DỪNG: không có level '{}'. Các level: {}".format(
        name, u", ".join(l.Name for l in sorted(levels, key=lambda x: x.Elevation)))])


def find_railing_type(name):
    types = list(FilteredElementCollector(doc).OfClass(RailingType).ToElements())
    for t in types:
        if norm(get_name(t)) == norm(name):
            return t
    raise StopReport([u"DỪNG: không có Railing type '{}' (IN[3]). Các type: {}".format(
        name, u", ".join(sorted(get_name(t) for t in types)))])


def find_symbol(family_name, type_name):
    syms = [s for s in FilteredElementCollector(doc).OfClass(FamilySymbol).ToElements()
            if norm(s.FamilyName) == norm(family_name)]
    if not syms:
        raise StopReport([u"DỪNG: không có family louver '{}' (IN[4]) – load family vào mô hình.".format(family_name)])
    for s in syms:
        if norm(get_name(s)) == norm(type_name):
            return s
    raise StopReport([u"DỪNG: family '{}' không có type '{}' (IN[5]). Các type: {}".format(
        family_name, type_name, u", ".join(sorted(get_name(s) for s in syms)))])


def symbol_width(s):
    p = s.get_Parameter(BuiltInParameter.FAMILY_WIDTH_PARAM) or s.LookupParameter("Width")
    if p is None:
        raise StopReport([u"DỪNG: type louver '{}' không có tham số Width.".format(get_name(s))])
    return to_mm(p.AsDouble())


def read_cad(objects, facade_layers, unit_layer):
    """→ (segs [(a, b, layer)] nét mặt ngoài, boxes [(x0, y0, x1, y1)] nét layer cục nóng)."""
    segs, boxes = [], []
    for obj in objects:
        l = layer_of(obj)
        if l in facade_layers:
            if isinstance(obj, Line):
                segs.append((xy(obj.GetEndPoint(0)), xy(obj.GetEndPoint(1)), l))
            elif isinstance(obj, PolyLine):
                pts = [xy(p) for p in obj.GetCoordinates()]
                segs.extend((a, b, l) for a, b in zip(pts[:-1], pts[1:]))
        if l == unit_layer:
            if isinstance(obj, Curve):
                pts = [xy(p) for p in obj.Tessellate()]
            elif isinstance(obj, PolyLine):
                pts = [xy(p) for p in obj.GetCoordinates()]
            else:
                continue
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            boxes.append((min(xs), min(ys), max(xs), max(ys)))
    return segs, boxes


def logia_floors(level, type_part):
    result = []
    for fl in FilteredElementCollector(doc).OfClass(Floor).ToElements():
        if fl.LevelId != level.Id:
            continue
        if norm(type_part).lower() not in norm(get_name(doc.GetElement(fl.GetTypeId()))).lower():
            continue
        bb = fl.get_BoundingBox(None)
        if bb is None:
            continue
        result.append((fl.Id.Value, (to_mm(bb.Min.X), to_mm(bb.Min.Y), to_mm(bb.Max.X), to_mm(bb.Max.Y))))
    return result


def wall_end_points(level):
    pts = []
    for wl in FilteredElementCollector(doc).OfClass(Wall).ToElements():
        loc = wl.Location
        prm = wl.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        if prm is not None and norm(prm.AsString()) == CURB_COMMENT:
            continue   # gờ nằm trên tuyến – không dùng làm đầu tường
        if wl.LevelId == level.Id and isinstance(loc, LocationCurve):
            pts.append(xy(loc.Curve.GetEndPoint(0)))
            pts.append(xy(loc.Curve.GetEndPoint(1)))
    return pts


def is_mine(el):
    prm = el.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    return prm is not None and norm(prm.AsString()) == COMMENT


def existing_curbs(level):
    """[(đầu, cuối, Id, đỉnh)] gờ ARV-GoLogia trên level (đỉnh so với level, mm)."""
    out = []
    for wl in FilteredElementCollector(doc).OfClass(Wall).ToElements():
        loc = wl.Location
        prm = wl.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        if (wl.LevelId != level.Id or not isinstance(loc, LocationCurve) or prm is None
                or norm(prm.AsString()) != CURB_COMMENT):
            continue
        top = to_mm(wl.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET).AsDouble()
                    + wl.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM).AsDouble())
        out.append((xy(loc.Curve.GetEndPoint(0)), xy(loc.Curve.GetEndPoint(1)), wl.Id.Value, top))
    return out


def rail_base_param(r):
    return r.get_Parameter(BuiltInParameter.STAIRS_RAILING_HEIGHT_OFFSET)


def louver_base_param(fi):
    return fi.get_Parameter(BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM)


def existing_rails(level):
    """[(a, b, Id, của tool, chân)] mỗi lan can trên level: đoạn từ đầu đến cuối đường dẫn."""
    out = []
    for r in FilteredElementCollector(doc).OfClass(Railing).ToElements():
        if r.LevelId != level.Id:
            continue
        path = list(r.GetPath())
        if path:
            out.append((xy(path[0].GetEndPoint(0)), xy(path[-1].GetEndPoint(1)), r.Id.Value, is_mine(r),
                        to_mm(rail_base_param(r).AsDouble())))
    return out


def existing_louvers(symbol):
    """[(đầu, cuối, Id, của tool, tâm khối đặc, chân)]: đầu = điểm chèn, cuối = điểm chèn + Hand × Width."""
    out = []
    for fi in FilteredElementCollector(doc).OfClass(FamilyInstance).ToElements():
        if fi.Symbol.Family.Id != symbol.Family.Id or not hasattr(fi.Location, "Point"):
            continue
        o = xy(fi.Location.Point)
        h = fi.HandOrientation
        w = symbol_width(fi.Symbol)
        ex, ey = solid_extent(fi, (1.0, 0.0)), solid_extent(fi, (0.0, 1.0))
        c = ((ex[0] + ex[1]) / 2.0, (ey[0] + ey[1]) / 2.0) if ex and ey else None
        bp = louver_base_param(fi)
        out.append((o, (o[0] + h.X * w, o[1] + h.Y * w), fi.Id.Value, is_mine(fi), c,
                    to_mm(bp.AsDouble()) if bp is not None else 0.0))
    return out


def louver_symbol(template, width, planned):
    """Type cùng family, Width = width, Height = Height của type mẫu → FamilySymbol, hoặc tên type sẽ nhân bản."""
    key = int(round(width))
    if key in planned:
        return planned[key]
    th = template.get_Parameter(BuiltInParameter.FAMILY_HEIGHT_PARAM) or template.LookupParameter("Height")
    height = to_mm(th.AsDouble()) if th else 0.0
    for s in FilteredElementCollector(doc).OfClass(FamilySymbol).ToElements():
        if s.Family.Id != template.Family.Id:
            continue
        sh = s.get_Parameter(BuiltInParameter.FAMILY_HEIGHT_PARAM) or s.LookupParameter("Height")
        if abs(symbol_width(s) - width) <= 1.0 and sh is not None and abs(to_mm(sh.AsDouble()) - height) <= 1.0:
            planned[key] = s
            return s
    planned[key] = u"{}X{:.0f}".format(key, height)
    return planned[key]


def type_label(t):
    return get_name(t) if not isinstance(t, (str, type(u""))) else t + u" (mới)"


def set_comment(el):
    prm = el.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    if prm is not None and not prm.IsReadOnly:
        prm.Set(COMMENT)


def create_railing(p, rtype, level):
    a, b = p.pt(p.rail[0]), p.pt(p.rail[1])
    loop = CurveLoop()
    loop.Append(Line.CreateBound(XYZ(from_mm(a[0]), from_mm(a[1]), 0.0), XYZ(from_mm(b[0]), from_mm(b[1]), 0.0)))
    r = Railing.Create(doc, loop, rtype.Id, level.Id)
    rail_base_param(r).Set(from_mm(p.base))
    set_comment(r)
    return r


def set_base(el, base_mm):
    """Chỉnh chân lan can / louver đã có (so với level, mm)."""
    prm = rail_base_param(el) if isinstance(el, Railing) else louver_base_param(el)
    prm.Set(from_mm(base_mm))


def create_louver(p, symbol, level):
    """Điểm chèn ở một đầu, Hand dọc tuyến, Facing = Z × Hand → chọn chiều Hand sao cho Facing ra ngoài."""
    d = (p.out[1], -p.out[0])
    a, b = p.pt(p.louver[0]), p.pt(p.louver[1])
    start = a if (b[0] - a[0]) * d[0] + (b[1] - a[1]) * d[1] > 0 else b
    o = XYZ(from_mm(start[0]), from_mm(start[1]), 0.0)
    fi = doc.Create.NewFamilyInstance(o, symbol, level, StructuralType.NonStructural)
    ang = math.atan2(d[1], d[0])
    if abs(ang) > 1e-9:
        ElementTransformUtils.RotateElement(doc, fi.Id, Line.CreateBound(o, o.Add(XYZ.BasisZ)), ang)
    doc.Regenerate()
    ext = solid_extent(fi, p.out)
    if ext is not None:
        off = (ext[0] + ext[1]) / 2.0 - p.facade.line * (p.out[0] + p.out[1])
        if abs(off) > 0.5:
            ElementTransformUtils.MoveElement(doc, fi.Id, XYZ(from_mm(-p.out[0] * off), from_mm(-p.out[1] * off), 0.0))
    louver_base_param(fi).Set(from_mm(p.base))
    set_comment(fi)
    return fi


def solid_extent(fi, u):
    """(min, max) toạ độ tuyệt đối (mm) của khối đặc theo phương trục u = (±1, 0) / (0, ±1), nhân dấu theo u."""
    opt = Options()
    opt.DetailLevel = ViewDetailLevel.Fine
    vals = []

    def walk(geo):
        for obj in geo:
            if isinstance(obj, GeometryInstance):
                walk(obj.GetInstanceGeometry())
            elif isinstance(obj, Solid) and obj.Volume > 0:
                for e in obj.Edges:
                    for q in e.Tessellate():
                        vals.append(to_mm(q.X * u[0] + q.Y * u[1]))

    geo = fi.get_Geometry(opt)
    if geo is not None:
        walk(geo)
    return (min(vals), max(vals)) if vals else None


def preview_lines(plans, z0_mm):
    try:
        clr.AddReference("ProtoGeometry")
        from Autodesk.DesignScript.Geometry import Point as DSPoint, Line as DSLine
        out = []
        for p in plans:
            z_mm = z0_mm + p.base
            segs = [(p.pt(p.rail[0]), p.pt(p.rail[1]))] if p.rail else []
            if p.louver:
                a, b = p.pt(p.louver[0]), p.pt(p.louver[1])
                segs.append((a, b))
                m = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
                segs.append((m, (m[0] + p.out[0] * 600.0, m[1] + p.out[1] * 600.0)))
            for a, b in segs:
                out.append(DSLine.ByStartPointEndPoint(DSPoint.ByCoordinates(a[0], a[1], z_mm),
                                                       DSPoint.ByCoordinates(b[0], b[1], z_mm)))
        return out
    except Exception:
        return []


LOG_HEADER = [u"STT", u"Sàn logia Id", u"Layer mặt ngoài", u"Tuyến từ", u"Tuyến đến", u"Dài (mm)", u"Cục nóng",
              u"Louver từ", u"Louver đến", u"Type louver", u"Lan can (mm)", u"Chân (mm)", u"Gờ Id", u"Ghi chú",
              u"Kết quả", u"Lan can Id", u"Louver Id"]


def write_log(rows, source, dry_run):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoLanCanLouverLogia_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(u"# Dự án: {}\n".format(doc.Title))
        f.write(u"# File nguồn: {}\n".format(source))
        f.write(u"# Ngày xuất: {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write(u"# Chế độ: {}\n".format(u"Chạy thử (dry-run)" if dry_run else u"Thực hiện"))
        f.write(u"# Đơn vị: mm\n")
        w = csv.writer(f)
        w.writerow(LOG_HEADER)
        w.writerows(rows)
    return path


def split_layers(text):
    return set(norm(s) for s in (text or u"").split(u";") if norm(s))


def parse_size(text):
    t = norm(text).lower().replace(u"×", u"x")
    a, b = t.split(u"x")
    return (float(a), float(b))


DONE_STATUS = (u"Sẽ tạo", u"Đã tạo", u"Sẽ thay", u"Đã thay", u"Sẽ chỉnh chân", u"Đã chỉnh chân")


def action(p, dry_run):
    if p.delete_ids:
        word = u"thay"
    elif p.need_rail or p.need_louver:
        word = u"tạo"
    else:
        word = u"chỉnh chân"
    return (u"Sẽ " if dry_run else u"Đã ") + word


def main(cad_filter, facade_layers, floor_part, rail_type_name, louver_family, louver_type, unit_layer,
         unit_size, unit_min, level_name, dry_run, min_rail):
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."], []
    cad, cad_name, objects, all_layers = pick_cad(cad_filter, facade_layers)
    missing = sorted((facade_layers | {unit_layer}) - all_layers)
    level = find_level(level_name)
    rtype = find_railing_type(rail_type_name)
    symbol = find_symbol(louver_family, louver_type)
    louver_w = symbol_width(symbol)
    floors = logia_floors(level, floor_part)
    if not floors:
        raise StopReport([u"DỪNG: level '{}' không có sàn nào có type chứa '{}' (IN[2]).".format(level_name, floor_part)])

    segs, unit_boxes = read_cad(objects, facade_layers, unit_layer)
    pairs = facade_pairs(segs)
    wall_ends = wall_end_points(level)
    rails = existing_rails(level)
    louvers = existing_louvers(symbol)
    curbs = existing_curbs(level)

    planned = {}   # rộng louver → FamilySymbol có sẵn hoặc tên type sẽ nhân bản
    plans = []
    for fid, box in floors:
        x0, y0, x1, y1 = box
        inside = [b for b in unit_boxes if b[0] >= x0 - 5 and b[2] <= x1 + 5 and b[1] >= y0 - 5 and b[3] <= y1 + 5]
        p = plan_logia(fid, box, pairs, wall_ends, inside, unit_size, unit_min, louver_w, min_rail)
        if p.status == u"OK":
            if p.louver:
                p.louver_type = louver_symbol(symbol, p.louver[1] - p.louver[0], planned)
            curb_base(p, curbs)
            reconcile(p, rails, louvers)
            if not (p.need_rail or p.need_louver or p.delete_ids or p.lift_ids):
                p.status = u"Bỏ qua – đã đúng"
        plans.append(p)
    plans.sort(key=lambda q: (-round((q.box[1] + q.box[3]) / 2.0), round((q.box[0] + q.box[2]) / 2.0)))
    jobs = [p for p in plans if p.status == u"OK"]

    if not dry_run and jobs:
        TransactionManager.Instance.ForceCloseTransaction()
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        try:
            for key in sorted(planned):
                t = planned[key]
                if isinstance(t, (str, type(u""))):
                    new_type = symbol.Duplicate(t)
                    (new_type.get_Parameter(BuiltInParameter.FAMILY_WIDTH_PARAM)
                     or new_type.LookupParameter("Width")).Set(from_mm(key))
                    planned[key] = new_type
            for p in jobs:
                for eid in p.delete_ids:
                    doc.Delete(ElementId(eid))
            for p in jobs:
                for eid in p.lift_ids:
                    set_base(doc.GetElement(ElementId(eid)), p.base)
                if p.need_rail:
                    p.rail_id = create_railing(p, rtype, level).Id.Value
                if p.need_louver:
                    sym = planned[int(round(p.louver[1] - p.louver[0]))]
                    if not sym.IsActive:
                        sym.Activate()
                        doc.Regenerate()
                    p.louver_id = create_louver(p, sym, level).Id.Value
                p.status = action(p, False)
            tx.Commit()
        except Exception as ex:
            tx.RollBack()
            return [u"LỖI khi tạo, mọi thay đổi đã được hoàn tác: {}".format(ex)], []
    elif dry_run:
        for p in jobs:
            p.status = action(p, True)

    rows = []
    for i, p in enumerate(plans, 1):
        f = p.facade
        rows.append([i, p.fid, f.layer if f else u"—",
                     fmt(p.pt(p.s)) if f and p.s is not None else u"—",
                     fmt(p.pt(p.e)) if f and p.e is not None else u"—",
                     u"{:.0f}".format(p.e - p.s) if f and p.s is not None else u"—",
                     fmt(((p.unit[0] + p.unit[2]) / 2.0, (p.unit[1] + p.unit[3]) / 2.0)) if p.unit else u"không",
                     fmt(p.pt(p.louver[0])) if p.louver else u"—", fmt(p.pt(p.louver[1])) if p.louver else u"—",
                     type_label(p.louver_type) if p.louver_type is not None else u"—",
                     u"{:.0f}".format(p.rail[1] - p.rail[0]) if p.rail else u"—",
                     u"{:+.0f}".format(p.base), p.curb_id,
                     u"; ".join(p.notes), p.status, p.rail_id, p.louver_id])

    done = [p for p in plans if p.status in DONE_STATUS]
    ok = [p for p in plans if p.rail or p.louver]
    report = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN")]
    report.append(u"CAD: {} – level: {} – lan can '{}' – louver '{} : {}' rộng {:.0f} – lan can ngắn nhất {:.0f}".format(
        cad_name, level.Name, get_name(rtype), louver_family, louver_type, louver_w, min_rail))
    if missing:
        report.append(u"LƯU Ý: bản CAD không có layer: {}".format(u"; ".join(missing)))
    report.append(u"Logia: {} – lan can + louver: {}, chỉ louver (hết tuyến): {}, chỉ lan can: {}".format(
        len(plans), len([p for p in ok if p.rail and p.louver]), len([p for p in ok if p.louver and not p.rail]),
        len([p for p in ok if p.rail and not p.louver])))
    report.append(u"{}: {} logia (thay {}, chỉnh chân {}), đã đúng: {}".format(
        u"Sẽ làm" if dry_run else u"Đã làm", len(done), len([p for p in done if p.delete_ids]),
        len([p for p in done if p.lift_ids]), len([p for p in plans if p.status == u"Bỏ qua – đã đúng"])))
    report.append(u"Chân trên gờ {}: {} logia, ở cao độ level: {}".format(
        CURB_COMMENT, len([p for p in ok if p.curb_id]), len([p for p in ok if not p.curb_id])))
    new_types = sorted(set(type_label(p.louver_type) for p in done if p.louver_type is not None and p.need_louver))
    if new_types:
        report.append(u"Type louver dùng: {}".format(u", ".join(new_types)))
    skipped = [p for p in plans if p not in done and p.status != u"Bỏ qua – đã đúng"]
    for p in skipped:
        report.append(u"  Sàn {}: {}".format(p.fid, p.status))
    checks = [p for p in plans if any(n.startswith(u"KIỂM TRA") for n in p.notes)]
    if checks:
        report.append(u"KIỂM TRA ĐẦU tuyến {} logia: {}".format(len(checks), u", ".join(str(p.fid) for p in checks)))
    try:
        report.append(u"Log: " + write_log(rows, cad_name, dry_run))
    except Exception as ex:
        report.append(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        report.append(u"Xem trước: tuyến lan can, đoạn louver + vạch 600 mm chỉ ra ngoài. Đúng thì đổi Dry-run = False "
                      u"và Run lại. Undo bằng mục \"{}\".".format(TRANSACTION_NAME))
    report.append(u" | ".join(LOG_HEADER))
    report += [u" | ".join(u"{}".format(v) for v in r) for r in rows]
    return report, preview_lines(done, to_mm(level.Elevation))


def force_rerun_next_time():
    """Đánh dấu node 'đã sửa' để lần Run sau luôn chạy lại (chỉ ở chế độ Manual)."""
    try:
        clr.AddReference("DynamoRevitDS")
        from Dynamo.Applications import DynamoRevit
        ws = DynamoRevit.RevitDynamoModel.CurrentWorkspace
        rt = ws.RunSettings.RunType
        try:
            clr.AddReference("DynamoCore")
            from Dynamo.Models import RunType
            manual = rt == RunType.Manual
        except Exception:
            manual = False
        if not (manual or str(rt) in ("0", "Manual", "RunType.Manual")):
            return u"Chế độ chạy không phải Manual – lần sau phải đổi một ô đầu vào thì node mới chạy lại."
        for n in ws.Nodes:
            if SCRIPT_TAG in (getattr(n, "Script", None) or u""):
                n.MarkNodeAsModified(True)
                return None
        return u"Không tìm thấy node để đánh dấu chạy lại."
    except Exception as ex:
        return u"Không đánh dấu được node chạy lại ({}) – lần sau đổi một ô đầu vào rồi Run.".format(ex)


if DYNAMO:
    import traceback

    def _s(i, default):
        v = IN[i] if len(IN) > i else None
        return (v if v is not None and u"{}".format(v).strip() else default)

    try:
        OUT = list(main(
            u"{}".format(_s(0, u"")).strip(),
            split_layers(_s(1, u"A-Line;A-line1;A-line2")),
            norm(_s(2, u"Logia")),
            norm(_s(3, u"Glass Panel - Bottom Fill")),
            norm(_s(4, u"AV-Lam Thép Logia2")),
            norm(_s(5, u"1000X2800")),
            norm(u"{}".format(_s(6, u"0"))),
            parse_size(_s(7, u"974x400")),
            int(float(_s(8, 150))),
            norm(_s(9, u"Tầng 1")),
            True if (len(IN) <= 10 or IN[10] is None) else bool(IN[10]),
            float(_s(11, 1200.0)),
        ))
    except StopReport as ex:
        OUT = [ex.lines, []]
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], []]
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with io.open(os.path.join(folder, "TaoLanCanLouverLogia_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))), "w", encoding="utf-8-sig") as f:
                f.write(u"\n".join(OUT[0]))
        except Exception:
            pass
    note = force_rerun_next_time()
    if note:
        OUT[0].append(u"LƯU Ý: " + note)
