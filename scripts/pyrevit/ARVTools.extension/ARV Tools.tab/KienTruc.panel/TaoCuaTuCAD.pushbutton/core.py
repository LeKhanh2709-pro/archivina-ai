# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong ARV_TaoCuaTuCAD_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Tạo cửa đi gắn vào tường Revit có sẵn từ mặt bằng DWG đã Link (cửa trong CAD là nét rời / block ẩn danh,
# nên nhận cửa theo CUNG MỞ CÁNH trên layer cửa):
#   1. Đọc cung tròn trên layer cửa (IN[1]): bán kính 300–1500 mm, góc quét 30°–100° (cửa vẽ mở 90° hoặc 45°).
#      Tâm cung = bản lề, bán kính = bề rộng cánh. Cung trùng nhau (cùng tâm, cùng bán kính) tính một lần.
#   2. Tường chủ: tường Revit trên level IN[4] có tim đi qua bản lề (lệch ≤ nửa bề dày tường + 60 mm) và một đầu
#      cung nằm dọc theo tim tường (cánh ở vị trí đóng). Không có → báo cáo, không tạo.
#   3. Cửa 2 cánh: hai cung trên cùng tường, bản lề hai đầu, cánh đóng gặp nhau giữa ô → chỉ báo cáo (chưa có
#      family 2 cánh).
#   4. Bề rộng = PHỦ BÌ KHUÔN CỬA CAD (= Width của family; khuôn cách mặt tường ~10 mm nên khe tường lớn hơn 20 mm):
#      khe lỗ tường = đầu mút nét layer IN[2] trong dải bề dày tường gần nhất phía bản lề / phía đối diện; khuôn = nét
#      layer cửa IN[1] trong dải đó, nằm trong khe – từ bản lề lùi về sau và từ đầu cánh tiến ra, lấy mép xa nhất.
#      Làm tròn IN[6] mm. Thiếu đầu tường hoặc khuôn ở một bên → báo cáo, không tạo.
#   5. Type: type có sẵn của family IN[3] có Width khớp (±IN[6]/2 mm) và Height = IN[7] → dùng; chưa có → nhân bản
#      type mẫu IN[5] thành "DW01_{rộng}X{cao}", đặt Width / Height.
#   6. Đặt cửa giữa ô (trên tim tường chủ), Sill = 0, lật hướng mở (Facing) và bản lề (Hand) theo cung CAD.
#      Bỏ qua ô đã có cửa (cửa cùng tường, tâm cách ≤ 100 mm); cửa cũ khác bề rộng → báo "SAI RỘNG" kèm Id để xoá.
# INPUT
#   IN[0] (str)   Một phần tên bản CAD (để trống = bản CAD duy nhất có layer khớp IN[1])
#   IN[1] (str)   Chuỗi lọc layer cửa đi, nhiều chuỗi cách nhau bằng ';' (VD "A-Door"; khớp chuỗi con)
#   IN[2] (str)   Chuỗi lọc layer tường CAD để đo khe lỗ cửa (VD "A-Wall")
#   IN[3] (str)   Tên family cửa 1 cánh (VD "D1_WO_OP1")
#   IN[4] (str)   Tên level của tường chủ (VD "TẦNG 2")
#   IN[5] (str)   Type mẫu để nhân bản khi chưa có type đúng bề rộng (VD "DW01_900X2200 2")
#   IN[6] (float) Làm tròn bề rộng (mm), VD 5
#   IN[7] (float) Chiều cao cửa (mm), VD 2200
#   IN[8] (bool)  Dry-run: True = chỉ báo cáo + xem trước, không ghi vào mô hình (mặc định True)
# OUTPUT
#   OUT[0] (list[str])  Báo cáo: tóm tắt, đường dẫn log, rồi từng cửa
#   OUT[1] (list[Line]) Xem trước: đoạn ô cửa trên tim tường (mm)

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
                                   Line, Arc, XYZ, Transaction, UnitUtils, UnitTypeId, ModelPathUtils,
                                   BuiltInParameter, BuiltInCategory, Level, Wall, LocationCurve, FamilySymbol,
                                   FamilyInstance)
    from Autodesk.Revit.DB.Structure import StructuralType
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = u"ARV - Tạo cửa đi từ CAD"
SCRIPT_TAG = u"ARV_TaoCuaTuCAD_v1"
R_RANGE_MM = (300.0, 1500.0)     # Bán kính cung = bề rộng cánh
SWEEP_RANGE_DEG = (30.0, 100.0)  # Cửa vẽ mở 90° hoặc 45°
HOST_TOL_MM = 60.0               # Bản lề lệch khỏi mặt tường chủ tối đa
ALONG_COS = math.cos(math.radians(10.0))  # Cánh đóng song song tim tường (lệch ≤ 10°)
DUP_ARC_MM = 5.0                 # Cung trùng
DOUBLE_TOL_MM = 100.0            # Hai cánh gặp nhau giữa ô (cửa 2 cánh)
JAMB_BACK_MM = 300.0             # Tìm đầu tường phía bản lề: lùi tối đa sau bản lề
JAMB_FRONT_MM = 60.0             #   … và tiến tối đa vào ô cửa
JAMB_FAR_MIN = 0.6               # Đầu tường phía đối diện: từ 0.6 × bán kính
JAMB_FAR_EXTRA_MM = 300.0        #   … tới bán kính + 300
BAND_TOL_MM = 30.0               # Dải bề dày tường để lấy đầu mút nét tường CAD
FRAME_TOL_MM = 2.0               # Khuôn cửa được chạm mép khe tường
FRAME_NEAR_MAX_MM = 5.0          # Nét khuôn phía bản lề: tới bản lề (+5); phía đối diện: từ đầu cánh (−5)
EXIST_DOOR_MM = 100.0            # Ô đã có cửa
TYPE_PATTERN = u"DW01_{w}X{h}"


# --- Hình học 2D thuần (mm) – chạy được ngoài Revit để thử --------------------------
def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def unit(v):
    l = math.hypot(v[0], v[1])
    return (v[0] / l, v[1] / l)


def fmt(p):
    return u"({:.0f}, {:.0f})".format(p[0], p[1])


class HostWall(object):
    def __init__(self, wid, a, b, width, name=u""):
        self.id, self.a, self.b, self.width, self.name = wid, a, b, width, name
        self.length = math.hypot(b[0] - a[0], b[1] - a[1])
        self.u = unit(sub(b, a))
        self.n = (-self.u[1], self.u[0])

    def local(self, p):
        d = sub(p, self.a)
        return dot(d, self.u), dot(d, self.n)

    def point(self, s):
        return (self.a[0] + self.u[0] * s, self.a[1] + self.u[1] * s)


class Leaf(object):
    """Một cánh cửa: cung CAD trên tường chủ. t = (s - s_h) * sign là toạ độ dọc tường hướng vào ô cửa."""

    def __init__(self, arc, wall, s_h, sign, swing):
        self.arc, self.wall, self.s_h, self.sign, self.swing = arc, wall, s_h, sign, swing
        self.r = arc["r"]
        self.partner = None


class Door(object):
    def __init__(self, leaf):
        self.leaf = leaf
        self.status = u""
        self.width = None       # mm, đã làm tròn
        self.raw_width = None   # phủ bì khuôn cửa CAD
        self.gap_width = None   # khe lỗ tường CAD
        self.s_center = None
        self.type_name = u""
        self.eid = u""

    def center(self):
        return self.leaf.wall.point(self.s_center) if self.s_center is not None else self.leaf.arc["c"]


def arc_sweep_deg(arc):
    v0, v1 = unit(sub(arc["p0"], arc["c"])), unit(sub(arc["p1"], arc["c"]))
    return math.degrees(math.acos(max(-1.0, min(1.0, dot(v0, v1)))))


def door_arcs(arcs):
    """Lọc cung cánh cửa, bỏ cung trùng. Trả về (danh sách, số cung bỏ qua theo kích thước)."""
    kept, skipped = [], 0
    for a in arcs:
        if not (R_RANGE_MM[0] <= a["r"] <= R_RANGE_MM[1]) or not (
                SWEEP_RANGE_DEG[0] <= arc_sweep_deg(a) <= SWEEP_RANGE_DEG[1]):
            skipped += 1
            continue
        if any(math.hypot(*sub(a["c"], k["c"])) <= DUP_ARC_MM and abs(a["r"] - k["r"]) <= DUP_ARC_MM
               and min(math.hypot(*sub(a["p0"], k["p0"])) + math.hypot(*sub(a["p1"], k["p1"])),
                       math.hypot(*sub(a["p0"], k["p1"])) + math.hypot(*sub(a["p1"], k["p0"]))) <= 2 * DUP_ARC_MM
               for k in kept):
            continue
        kept.append(a)
    return kept, skipped


def find_leaf(arc, walls):
    """Tường chủ có tim đi qua bản lề và một đầu cung nằm dọc tim tường → Leaf, None nếu không có."""
    best = None
    for w in walls:
        s, d = w.local(arc["c"])
        if s < -HOST_TOL_MM or s > w.length + HOST_TOL_MM or abs(d) > w.width / 2.0 + HOST_TOL_MM:
            continue
        ends = []
        for e, o in ((arc["p0"], arc["p1"]), (arc["p1"], arc["p0"])):
            v = unit(sub(e, arc["c"]))
            if abs(dot(v, w.u)) >= ALONG_COS:
                ends.append((abs(dot(v, w.u)), e, o))
        if not ends:
            continue
        _, closed, opened = max(ends)
        sign = 1 if dot(sub(closed, arc["c"]), w.u) > 0 else -1
        swing = 1 if dot(sub(opened, arc["c"]), w.n) > 0 else -1
        if best is None or abs(d) < best[0]:
            best = (abs(d), Leaf(arc, w, s, sign, swing))
    return best[1] if best else None


def pair_doubles(leaves):
    """Hai cánh cùng tường, bản lề hai đầu, cánh đóng gặp nhau giữa ô → đánh dấu partner."""
    for i, a in enumerate(leaves):
        for b in leaves[i + 1:]:
            if a.partner or b.partner or a.wall is not b.wall or a.sign == b.sign:
                continue
            tip_a, tip_b = a.s_h + a.sign * a.r, b.s_h + b.sign * b.r
            if abs(tip_a - tip_b) <= DOUBLE_TOL_MM and (b.s_h - a.s_h) * a.sign > 0:
                a.partner, b.partner = b, a


def wall_endpoints(wall, segs):
    """Toạ độ dọc tường s của đầu mút nét CAD nằm trong dải bề dày tường chủ."""
    h = wall.width / 2.0 + BAND_TOL_MM
    result = []
    for a, b in segs:
        for p in (a, b):
            s, d = wall.local(p)
            if abs(d) <= h and -JAMB_BACK_MM - R_RANGE_MM[1] <= s <= wall.length + JAMB_BACK_MM + R_RANGE_MM[1]:
                result.append(s)
    return result


def measure_gap(leaf, ends):
    """(t_bản_lề, t_đối_diện) của hai đầu tường CAD quanh ô cửa, None nếu thiếu."""
    ts = [(s - leaf.s_h) * leaf.sign for s in ends]
    near = [t for t in ts if -JAMB_BACK_MM <= t <= JAMB_FRONT_MM]
    far = [t for t in ts if JAMB_FAR_MIN * leaf.r <= t <= leaf.r + JAMB_FAR_EXTRA_MM]
    if not near or not far:
        return None
    return max(near), min(far)


def measure_frame(leaf, gap, door_ends):
    """Mép ngoài khuôn cửa CAD (đỉnh nét layer cửa trong dải bề dày tường) nằm trong khe tường gap = (t0, t1):
    phía bản lề lấy điểm xa nhất về sau bản lề, phía đối diện lấy điểm xa nhất qua đầu cánh.
    Trả về (t0, t1) của khuôn, None nếu một phía không có nét khuôn."""
    t0, t1 = gap
    ts = [(s - leaf.s_h) * leaf.sign for s in door_ends]
    near = [t for t in ts if t0 - FRAME_TOL_MM <= t <= FRAME_NEAR_MAX_MM]
    far = [t for t in ts if leaf.r - FRAME_NEAR_MAX_MM <= t <= t1 + FRAME_TOL_MM]
    if not near or not far:
        return None
    return min(near), max(far)


def round_to(x, step):
    return int(round(x / step) * step) if step > 0 else int(round(x))


def analyse(arcs, segs, door_segs, walls, round_mm, existing=None):
    """arcs: [{"c","r","p0","p1"}] mm; segs: nét tường CAD [(a, b)]; door_segs: nét thẳng layer cửa (khuôn);
    walls: [HostWall]. existing: {wall_id: [(x, y)]} tâm cửa đã có. Trả về (doors, thống kê)."""
    stats = {}
    kept, stats["arc_skipped"] = door_arcs(arcs)
    stats["arcs"] = len(kept)
    leaves, doors = [], []
    for a in kept:
        leaf = find_leaf(a, walls)
        if leaf is None:
            d = Door(Leaf(a, None, 0.0, 1, 1))
            d.status = u"Bỏ qua – không có tường Revit đi qua bản lề"
            doors.append(d)
        else:
            leaves.append(leaf)
    pair_doubles(leaves)
    ends_cache, door_cache = {}, {}
    done = set()
    for leaf in leaves:
        if id(leaf) in done:
            continue
        d = Door(leaf)
        doors.append(d)
        if leaf.partner is not None:
            done.add(id(leaf.partner))
            d.s_center = (leaf.s_h + leaf.partner.s_h) / 2.0
            d.raw_width = abs(leaf.partner.s_h - leaf.s_h)
            d.status = u"Bỏ qua – cửa 2 cánh (chưa có family 2 cánh)"
            continue
        w = leaf.wall
        if w.id not in ends_cache:
            ends_cache[w.id] = wall_endpoints(w, segs)
        gap = measure_gap(leaf, ends_cache[w.id])
        if gap is None:
            d.status = u"Bỏ qua – không tìm thấy đủ hai đầu tường CAD quanh ô cửa"
            continue
        d.gap_width = gap[1] - gap[0]
        if w.id not in door_cache:
            door_cache[w.id] = wall_endpoints(w, door_segs)
        frame = measure_frame(leaf, gap, door_cache[w.id])
        if frame is None:
            d.status = u"Bỏ qua – không thấy khuôn cửa CAD ở một bên ô cửa"
            continue
        t0, t1 = frame
        d.raw_width = t1 - t0
        d.width = round_to(d.raw_width, round_mm)
        d.s_center = leaf.s_h + leaf.sign * (t0 + t1) / 2.0
        if not (0 <= d.s_center <= w.length):
            d.status = u"Bỏ qua – tâm ô cửa nằm ngoài tường chủ"
            continue
        c = d.center()
        old = [e for e in (existing or {}).get(w.id, []) if math.hypot(*sub(c, e[0])) <= EXIST_DOOR_MM]
        if old:
            p, eid, tname, ow = old[0]
            d.eid = eid
            if ow is not None and abs(ow - d.width) > max(round_mm / 2.0, 1.0):
                d.status = u"Bỏ qua – ô đã có cửa SAI RỘNG (Id {}, {} rộng {:.0f} ≠ {}) – xoá cửa cũ rồi Run lại".format(
                    eid, tname, ow, d.width)
            else:
                d.status = u"Bỏ qua – ô đã có cửa"
            continue
        d.status = u"OK"
    doors.sort(key=lambda d: (-round(d.center()[1]), round(d.center()[0])))
    return doors, stats


def norm(s):
    return unicodedata.normalize("NFC", (s or u"")).strip()


# --- Revit ---------------------------------------------------------------------------
def to_mm(feet):
    return UnitUtils.ConvertFromInternalUnits(feet, UnitTypeId.Millimeters)


def from_mm(mm):
    return UnitUtils.ConvertToInternalUnits(mm, UnitTypeId.Millimeters)


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


def layer_of(geo_obj):
    style = doc.GetElement(geo_obj.GraphicsStyleId)
    if style is not None and style.GraphicsStyleCategory is not None:
        return style.GraphicsStyleCategory.Name
    return None


def cad_objects(cad):
    """Mọi đối tượng hình học của CAD, kể cả trong block lồng nhau."""
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


def match_layers(all_layers, filters):
    return set(l for l in all_layers if any(f.lower() in l.lower() for f in filters))


class StopReport(Exception):
    def __init__(self, lines):
        Exception.__init__(self, lines[0])
        self.lines = lines


def pick_cad(cad_filter, filters):
    """Chọn bản CAD theo tên; để trống thì lấy bản CAD duy nhất có layer khớp. Trả về (cad, tên, objects, layers)."""
    found = []
    for inst in FilteredElementCollector(doc).OfClass(ImportInstance).ToElements():
        name = get_name(doc.GetElement(inst.GetTypeId()))
        if cad_filter and cad_filter.lower() not in name.lower():
            continue
        objects = cad_objects(inst)
        all_layers = sorted(set(l for l in (layer_of(o) for o in objects) if l))
        found.append((inst, name, objects, all_layers))
    hits = [f for f in found if match_layers(f[3], filters)]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise StopReport([u"DỪNG: không có bản CAD{} nào có layer chứa '{}'.".format(
            u" khớp '{}'".format(cad_filter) if cad_filter else u"", u"; ".join(filters))])
    raise StopReport([u"DỪNG: {} bản CAD có layer khớp – nhập tên bản CAD vào ô IN[0]: {}".format(
        len(hits), u", ".join(h[1] for h in hits))])


def find_level(name):
    levels = list(FilteredElementCollector(doc).OfClass(Level).ToElements())
    for l in levels:
        if norm(l.Name) == norm(name):
            return l
    raise StopReport([u"DỪNG: không có level '{}'. Các level: {}".format(
        name, u", ".join(l.Name for l in sorted(levels, key=lambda x: x.Elevation)))])


def xy(p):
    return (to_mm(p.X), to_mm(p.Y))


def read_arcs(objects, layers):
    arcs = []
    for obj in objects:
        if isinstance(obj, Arc) and obj.IsBound and layer_of(obj) in layers:
            arcs.append({"c": xy(obj.Center), "r": to_mm(obj.Radius),
                         "p0": xy(obj.GetEndPoint(0)), "p1": xy(obj.GetEndPoint(1))})
    return arcs


def read_segments(objects, layers):
    segs = []
    for obj in objects:
        if layer_of(obj) not in layers:
            continue
        if isinstance(obj, Line):
            pts = [obj.GetEndPoint(0), obj.GetEndPoint(1)]
        elif isinstance(obj, PolyLine):
            pts = list(obj.GetCoordinates())
        else:
            continue
        pts = [xy(p) for p in pts]
        segs.extend(zip(pts[:-1], pts[1:]))
    return segs


def host_walls(level):
    result, by_id = [], {}
    for wl in FilteredElementCollector(doc).OfClass(Wall).ToElements():
        loc = wl.Location
        if wl.LevelId == level.Id and isinstance(loc, LocationCurve) and isinstance(loc.Curve, Line):
            c = loc.Curve
            hw = HostWall(wl.Id.Value, xy(c.GetEndPoint(0)), xy(c.GetEndPoint(1)), to_mm(wl.Width), get_name(wl))
            result.append(hw)
            by_id[hw.id] = wl
    return result, by_id


def existing_doors():
    """{id tường chủ: [(tâm cửa mm, Id, tên type, rộng mm)]} của mọi cửa đi đã có."""
    result = {}
    for fi in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType() \
            .ToElements():
        host = getattr(fi, "Host", None)
        loc = getattr(fi, "Location", None)
        if host is None or loc is None or not hasattr(loc, "Point"):
            continue
        sym = getattr(fi, "Symbol", None)
        width = symbol_size(sym)[0] if sym is not None else None
        result.setdefault(host.Id.Value, []).append(
            (xy(loc.Point), fi.Id.Value, get_name(sym) if sym is not None else u"?", width))
    return result


def length_param(element, name):
    p = element.LookupParameter(name)
    return p if p is not None and not p.IsReadOnly else None


def door_symbols(family_name):
    symbols = [s for s in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors)
               .WhereElementIsElementType().ToElements() if isinstance(s, FamilySymbol)]
    result = [s for s in symbols if norm(s.FamilyName) == norm(family_name)]
    if not result:
        raise StopReport([u"DỪNG: không có family cửa '{}' (IN[3]). Các family cửa: {}".format(
            family_name, u", ".join(sorted(set(s.FamilyName for s in symbols))) or u"không có")])
    return result


def symbol_size(s):
    w = s.get_Parameter(BuiltInParameter.DOOR_WIDTH) or s.LookupParameter("Width")
    h = s.get_Parameter(BuiltInParameter.DOOR_HEIGHT) or s.LookupParameter("Height")
    return (to_mm(w.AsDouble()) if w else None, to_mm(h.AsDouble()) if h else None)


def match_symbol(symbols, width, height, tol):
    for s in symbols:
        w, h = symbol_size(s)
        if w is not None and h is not None and abs(w - width) <= tol and abs(h - height) <= 1.0:
            return s
    return None


def set_size(symbol, width, height):
    for bip, name, v in ((BuiltInParameter.DOOR_WIDTH, "Width", width), (BuiltInParameter.DOOR_HEIGHT, "Height", height)):
        p = symbol.get_Parameter(bip) or symbol.LookupParameter(name)
        if p is None or p.IsReadOnly:
            raise Exception(u"Type '{}' không đặt được tham số {}.".format(get_name(symbol), name))
        p.Set(from_mm(v))


def orient(fi, wall, leaf):
    """Lật cửa cho đúng phía mở (Facing) và phía bản lề (Hand) theo cung CAD.
    Quy ước family (đã thử trong Revit 2026 với D1_WO_OP1, 7/7 cửa khớp bản lề + phía mở): FacingOrientation chỉ
    về phía cánh mở vào, HandOrientation chỉ về phía bản lề."""
    doc.Regenerate()
    swing_vec = (wall.n[0] * leaf.swing, wall.n[1] * leaf.swing)
    hinge_vec = (-wall.u[0] * leaf.sign, -wall.u[1] * leaf.sign)
    f = fi.FacingOrientation
    if FACING_TO_SWING * dot((f.X, f.Y), swing_vec) < 0:
        fi.flipFacing()
    doc.Regenerate()
    h = fi.HandOrientation
    if HAND_TO_HINGE * dot((h.X, h.Y), hinge_vec) < 0:
        fi.flipHand()


# Quy ước hướng của family (+1 / -1), xác định bằng thử nghiệm trong Revit – xem orient()
FACING_TO_SWING = 1
HAND_TO_HINGE = 1


def preview_lines(pairs, z_mm):
    try:
        clr.AddReference("ProtoGeometry")
        from Autodesk.DesignScript.Geometry import Point as DSPoint, Line as DSLine
        return [DSLine.ByStartPointEndPoint(DSPoint.ByCoordinates(a[0], a[1], z_mm),
                                            DSPoint.ByCoordinates(b[0], b[1], z_mm)) for a, b in pairs]
    except Exception:
        return []


LOG_HEADER = [u"STT", u"Bản lề (mm)", u"Bán kính cung (mm)", u"Tâm ô cửa (mm)", u"Khe tường CAD (mm)",
              u"Khuôn cửa CAD (mm)", u"Rộng (mm)", u"Tường chủ", u"Type", u"Kết quả", u"ElementId"]


def write_log(rows, source, dry_run):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoCuaTuCAD_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
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


def main(cad_filter, door_filters, wall_filters, family_name, level_name, template_name, round_mm, height_mm,
         dry_run):
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."], []
    cad, cad_name, objects, all_layers = pick_cad(cad_filter, door_filters)
    door_layers = match_layers(all_layers, door_filters)
    wall_layers = match_layers(all_layers, wall_filters)
    if not wall_layers:
        raise StopReport([u"DỪNG: bản CAD không có layer tường chứa '{}' (IN[2]).".format(u"; ".join(wall_filters))])
    symbols = door_symbols(family_name)
    template = None
    for s in symbols:
        if norm(get_name(s)) == norm(template_name):
            template = s
    if template is None:
        raise StopReport([u"DỪNG: family '{}' không có type mẫu '{}' (IN[5]). Các type: {}".format(
            family_name, template_name, u", ".join(sorted(get_name(s) for s in symbols)))])
    level = find_level(level_name)
    walls, wall_by_id = host_walls(level)
    if not walls:
        raise StopReport([u"DỪNG: level '{}' chưa có tường thẳng nào để gắn cửa.".format(level_name)])

    arcs = read_arcs(objects, door_layers)
    segs = read_segments(objects, wall_layers)
    door_segs = read_segments(objects, door_layers)
    doors, stats = analyse(arcs, segs, door_segs, walls, round_mm, existing_doors())

    tol = max(round_mm / 2.0, 1.0)
    planned_types = {}   # rộng → FamilySymbol có sẵn hoặc tên type sẽ nhân bản
    rows, jobs = [], []
    for idx, d in enumerate(doors, 1):
        leaf = d.leaf
        if d.status == u"OK":
            if d.width not in planned_types:
                s = match_symbol(symbols, d.width, height_mm, tol)
                planned_types[d.width] = s if s is not None else TYPE_PATTERN.format(
                    w=d.width, h=int(round(height_mm)))
            t = planned_types[d.width]
            d.type_name = get_name(t) if not isinstance(t, (str, type(u""))) else t + u" (mới)"
            d.status = u"Sẽ tạo" if dry_run else u"Chờ tạo"
            jobs.append((d, len(rows)))
        c = d.center()
        rows.append([idx, fmt(leaf.arc["c"]), u"{:.0f}".format(leaf.r), fmt(c),
                     u"{:.0f}".format(d.gap_width) if d.gap_width is not None else u"—",
                     u"{:.0f}".format(d.raw_width) if d.raw_width is not None else u"—",
                     d.width if d.width is not None else u"—",
                     u"{} ({})".format(leaf.wall.id, leaf.wall.name) if leaf.wall else u"—",
                     d.type_name or u"—", d.status, d.eid])

    if not dry_run and jobs:
        TransactionManager.Instance.ForceCloseTransaction()
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        try:
            for w in sorted(planned_types):
                t = planned_types[w]
                if isinstance(t, (str, type(u""))):
                    existing = [s for s in symbols if norm(get_name(s)) == norm(t)]
                    new_type = existing[0] if existing else template.Duplicate(t)
                    set_size(new_type, w, height_mm)
                    planned_types[w] = new_type
            for d, ri in jobs:
                sym = planned_types[d.width]
                if not sym.IsActive:
                    sym.Activate()
                    doc.Regenerate()
                wall = wall_by_id[d.leaf.wall.id]
                c = d.center()
                z = wall.Location.Curve.GetEndPoint(0).Z
                fi = doc.Create.NewFamilyInstance(XYZ(from_mm(c[0]), from_mm(c[1]), z), sym, wall, level,
                                                  StructuralType.NonStructural)
                sill = fi.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)
                if sill is not None and not sill.IsReadOnly:
                    sill.Set(0.0)
                orient(fi, d.leaf.wall, d.leaf)
                rows[ri][9] = u"Đã tạo"
                rows[ri][10] = fi.Id.Value
            tx.Commit()
        except Exception as ex:
            tx.RollBack()
            return [u"LỖI khi tạo cửa, mọi thay đổi đã được hoàn tác: {}".format(ex)], []

    report = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN")]
    report.append(u"CAD: {} – layer cửa: {} – layer tường: {}".format(
        cad_name, u"; ".join(sorted(door_layers)), u"; ".join(sorted(wall_layers))))
    report.append(u"Level tường chủ: {} – family: {} – cao {:.0f} mm, Sill 0 – làm tròn rộng {:.0f} mm".format(
        level.Name, family_name, height_mm, round_mm))
    report.append(u"Cung cánh cửa: {} (bỏ {} cung không phải cánh cửa) – {}: {}".format(
        stats["arcs"], stats["arc_skipped"], u"sẽ tạo" if dry_run else u"đã tạo", len(jobs)))
    counts = {}
    for d in doors:
        key = d.status.split(u" – ")[1] if d.status.startswith(u"Bỏ qua") else None
        if key:
            counts[key] = counts.get(key, 0) + 1
    for k in sorted(counts):
        report.append(u"Bỏ qua {} cửa: {}".format(counts[k], k))
    new_types = sorted(set(d.type_name for d, _ in jobs if d.type_name.endswith(u"(mới)")))
    if new_types:
        report.append(u"Type {}: {} (nhân bản từ '{}')".format(
            u"sẽ tạo" if dry_run else u"đã tạo", u", ".join(new_types), template_name))
    try:
        report.append(u"Log: " + write_log(rows, cad_name, dry_run))
    except Exception as ex:
        report.append(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        report.append(u"Kiểm tra ô cửa (đoạn xanh trong Dynamo) + log. Đúng thì đổi Dry-run = False và Run lại. "
                      u"Undo bằng mục \"{}\".".format(TRANSACTION_NAME))
    report.append(u" | ".join(LOG_HEADER))
    report += [u" | ".join(u"{}".format(v) for v in r) for r in rows]
    z_mm = to_mm(level.Elevation)
    pairs = []
    for d, _ in jobs:
        w = d.leaf.wall
        pairs.append((w.point(d.s_center - d.width / 2.0), w.point(d.s_center + d.width / 2.0)))
    return report, preview_lines(pairs, z_mm)


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
    try:
        OUT = list(main(
            (IN[0] or u"").strip(),
            [s.strip() for s in (IN[1] or u"A-Door").split(u";") if s.strip()],
            [s.strip() for s in (IN[2] or u"A-Wall").split(u";") if s.strip()],
            (IN[3] or u"D1_WO_OP1").strip(),
            (IN[4] or u"TẦNG 2"),
            (IN[5] or u"DW01_900X2200 2").strip(),
            float(IN[6] if IN[6] is not None else 5.0),
            float(IN[7] or 2200.0),
            True if IN[8] is None else bool(IN[8]),
        ))
    except StopReport as ex:
        OUT = [ex.lines, []]
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], []]
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with io.open(os.path.join(folder, "TaoCuaTuCAD_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))), "w", encoding="utf-8-sig") as f:
                f.write(u"\n".join(OUT[0]))
        except Exception:
            pass
    note = force_rerun_next_time()
    if note:
        OUT[0].append(u"LƯU Ý: " + note)
