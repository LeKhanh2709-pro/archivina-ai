# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong ARV_TaoCuaSoTuCAD_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Tạo cửa sổ và cửa lùa (ra logia) gắn vào tường Revit có sẵn từ mặt bằng DWG đã Link. Tường Revit phải LIỀN qua
# ô cửa (VD dựng bằng ARV_TaoTuongTuCAD_v1). Ô cửa nhận theo cụm nét nằm TRONG DẢI BỀ DÀY tường chủ:
#   1. Tường chủ = tường thẳng Revit trên level IN[5]. Nét CAD (line / polyline) trên layer cửa sổ IN[1], cửa lùa
#      IN[2], chỉ báo cáo IN[3] mà mọi đỉnh nằm trong dải bề dày tường (± nửa dày + 30 mm) → gom theo toạ độ dọc
#      tường (khe ≤ 60 mm nối cụm). Cụm dài < 300 mm bỏ qua (khuôn cửa đi mở quay). Cụm có cung cửa (tâm trong dải)
#      → cửa đi mở quay, bỏ qua (dùng ARV_TaoCuaTuCAD_v1).
#   2. Bề rộng ô = phủ bì cụm nét (khuôn CAD lấp kín khe tường thô), làm tròn IN[16] mm. Khe tường A-Wall chỉ ghi log.
#   3. Phía ngoài / logia: bắn tia vuông góc tường từ tâm ô về hai phía, phía gặp tường Revit đầu tiên XA hơn là
#      phía ngoài (logia không có tường Revit lan can; cửa sổ nhìn ra sân trong gặp khối đối diện xa hơn phòng).
#      Hai phía chênh < 500 mm → báo "KIỂM TRA HƯỚNG", vẫn tạo theo phía xa hơn.
#   4. Cửa sổ: rộng ≥ IN[10] → family IN[6] (type mẫu IN[7]); nhỏ hơn → family IN[8] (type mẫu IN[9]).
#      Type có Width = rộng và Height = IN[11] → dùng; chưa có → nhân bản type mẫu, tên theo mẫu "<tiền tố>{rộng}x{cao}".
#      Sill = IN[12]. Facing → phía ngoài. Hand giữ mặc định (CAD không thể hiện cánh lật).
#   5. Cửa lùa: family IN[13], type có Width = khe − IN[15] và Height = Height của type mẫu IN[14] → dùng; chưa có →
#      nhân bản type mẫu, tên "<tiền tố>{khe}X<cao trong tên mẫu>". Sill 0. Facing → logia. Hand theo CAD: cánh vẽ
#      phía logia nằm bên nào của ô thì cánh phía Facing của family nằm bên đó (DA01: cánh phía Facing ở phía +Hand).
#   6. Sau khi lật, đo khối đặc của cửa dọc tường rồi dời cửa cho tâm khối trùng tâm ô (SA01 có điểm chèn lệch tâm).
#      Ô đã có cửa sổ / cửa đi (gắn vào bất kỳ tường nào, kể cả lớp ốp: tâm khối cửa nằm trong dải bề dày tường chủ
#      + 100 mm và cách tâm ô ≤ max(100 mm, nửa bề rộng ô)) → bỏ qua; khác bề rộng → báo "SAI RỘNG" kèm Id.
#   Tường dày < 30 mm (lớp ốp / hoàn thiện, VD "GO-Gạch ốp-300x600" 10 mm) không làm tường chủ: cửa đặt vào lớp ốp
#   bị Revit xoá ("Can't cut instance out of Wall").
# INPUT
#   IN[0]  (str)   Một phần tên bản CAD (trống = bản CAD duy nhất có layer khớp IN[1])
#   IN[1]  (str)   Layer cửa sổ, cách nhau ';' (khớp đúng tên, kể cả trong xref "...$0$<tên>" bị loại) – VD "A-Window;A-Windows"
#   IN[2]  (str)   Layer cửa lùa ra logia – VD "A-Door;A-Cửa"
#   IN[3]  (str)   Layer chỉ báo cáo, không tạo – VD "A-Glaz"
#   IN[4]  (str)   Layer tường CAD (đo khe để ghi log) – VD "A-Wall"
#   IN[5]  (str)   Level tường chủ – VD "Tầng 1"
#   IN[6]  (str)   Family cửa sổ lớn – VD "AV-CuaSo1fix+1Lat"
#   IN[7]  (str)   Type mẫu cửa sổ lớn – VD "SA01-2200x2500"
#   IN[8]  (str)   Family cửa sổ nhỏ – VD "AV-Cửa nhôm kính mở lùa hai cánh trên fix dưới"
#   IN[9]  (str)   Type mẫu cửa sổ nhỏ – VD "1800x1300"
#   IN[10] (float) Rộng tối thiểu dùng family cửa sổ lớn (mm) – VD 1800
#   IN[11] (float) Chiều cao cửa sổ (mm) – VD 2500
#   IN[12] (float) Sill cửa sổ (mm) – VD 750
#   IN[13] (str)   Family cửa lùa – VD "AV_Cửa Nhôm kính hai cánh mở trượt"
#   IN[14] (str)   Type mẫu cửa lùa – VD "DA01_2200X2450"
#   IN[15] (float) Width cửa lùa = khe − giá trị này (mm) – VD 40
#   IN[16] (float) Làm tròn bề rộng (mm) – VD 5
#   IN[17] (bool)  Dry-run: True = chỉ báo cáo + xem trước, không ghi vào mô hình (mặc định True)
# OUTPUT
#   OUT[0] (list[str])  Báo cáo: tóm tắt, đường dẫn log, rồi từng ô
#   OUT[1] (list[Line]) Xem trước: đoạn ô cửa trên tim tường + mũi chỉ phía ngoài (mm)

import os
import io
import re
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
                                   Solid, ElementTransformUtils, ViewDetailLevel)
    from Autodesk.Revit.DB.Structure import StructuralType
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = u"ARV - Tạo cửa sổ và cửa lùa từ CAD"
SCRIPT_TAG = u"ARV_TaoCuaSoTuCAD_v1"
BAND_TOL_MM = 30.0        # Dải bề dày tường: ± nửa dày + 30
END_TOL_MM = 50.0         # Nét được vượt đầu tường chủ
JOIN_MM = 60.0            # Khe nối cụm nét
MIN_OPEN_MM = 300.0       # Cụm ngắn hơn → khuôn cửa đi mở quay, bỏ
GAP_SEARCH_MM = 300.0     # Tìm đầu tường CAD quanh ô
SIDE_MIN_DIFF_MM = 500.0  # Hai phía chênh ít hơn → KIỂM TRA HƯỚNG
EXIST_MM = 100.0          # Ô đã có cửa
EXIST_BAND_MM = 100.0     #   … tâm cửa cũ lệch khỏi mặt tường chủ tối đa
THIN_WALL_MM = 30.0       # Tường mỏng hơn = lớp ốp / hoàn thiện, không làm tường chủ
FAR_MM = 1.0e6            # Tia không gặp tường

KIND_WIN, KIND_SLIDE, KIND_REPORT = u"Cửa sổ", u"Cửa lùa", u"Chỉ báo cáo"


# --- Hình học 2D thuần (mm) – chạy được ngoài Revit để thử --------------------------
def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def unit(v):
    l = math.hypot(v[0], v[1])
    return (v[0] / l, v[1] / l)


def fmt(p):
    return u"({:.0f}, {:.0f})".format(p[0], p[1])


def norm(s):
    return unicodedata.normalize("NFC", (s or u"")).strip()


class HostWall(object):
    def __init__(self, wid, a, b, width, name=u""):
        self.id, self.a, self.b, self.width, self.name = wid, a, b, width, name
        self.length = math.hypot(b[0] - a[0], b[1] - a[1])
        self.u = unit(sub(b, a))
        self.n = (-self.u[1], self.u[0])

    def local(self, p):
        d = sub(p, self.a)
        return dot(d, self.u), dot(d, self.n)

    def point(self, s, d=0.0):
        return (self.a[0] + self.u[0] * s + self.n[0] * d, self.a[1] + self.u[1] * s + self.n[1] * d)


class Opening(object):
    def __init__(self, wall, kind, s0, s1, layers, items):
        self.wall, self.kind, self.s0, self.s1 = wall, kind, s0, s1
        self.layers = layers
        self.items = items          # [(kind, [(s, d)])] nét của cụm, toạ độ tường
        self.raw_width = s1 - s0
        self.width = None           # bề rộng ô đã làm tròn
        self.gap_width = None       # khe tường CAD (log)
        self.ext = 0                # +1 / -1: phía ngoài theo wall.n
        self.ext_note = u""
        self.hand_side = 0          # cửa lùa: +1 / -1 theo wall.u – cánh phía ngoài nằm bên nào
        self.status = u""
        self.family = u""
        self.type_name = u""
        self.type_width = None
        self.eid = u""

    @property
    def s_center(self):
        return (self.s0 + self.s1) / 2.0

    def center(self):
        return self.wall.point(self.s_center)


def ray_first_hit(o, v, segs):
    best = FAR_MM
    for a, b in segs:
        ex, ey = b[0] - a[0], b[1] - a[1]
        den = v[0] * ey - v[1] * ex
        if abs(den) < 1e-9:
            continue
        wx, wy = a[0] - o[0], a[1] - o[1]
        t = (wx * ey - wy * ex) / den
        u = (wx * v[1] - wy * v[0]) / den
        if 1.0 < t < best and -1e-6 <= u <= 1.0 + 1e-6:
            best = t
    return best


def outside_side(op, walls):
    """+1 / -1 theo wall.n: phía có tường Revit đầu tiên xa hơn. Trả về (phía, khoảng cách +, khoảng cách −)."""
    w = op.wall
    segs = [(x.a, x.b) for x in walls if x is not w]
    c = op.center()
    dist = {}
    for sgn in (1, -1):
        v = (w.n[0] * sgn, w.n[1] * sgn)
        o = (c[0] + v[0] * (w.width / 2.0 + 20.0), c[1] + v[1] * (w.width / 2.0 + 20.0))
        dist[sgn] = ray_first_hit(o, v, segs)
    return (1 if dist[1] >= dist[-1] else -1), dist[1], dist[-1]


def slide_hand_side(op):
    """Cửa lùa: cánh CAD (polyline nằm hẳn một phía tim tường) ở phía ngoài nằm bên nào của tâm ô (+1 / -1 theo u)."""
    sc = op.s_center
    votes = 0.0
    for kind, pts in op.items:
        ds = [d for _, d in pts]
        ss = [s for s, _ in pts]
        if len(pts) < 4 or max(ss) - min(ss) < 0.3 * op.raw_width:
            continue
        if min(ds) >= -2.0 and max(ds) > 10.0:
            side = 1
        elif max(ds) <= 2.0 and min(ds) < -10.0:
            side = -1
        else:
            continue
        if side != op.ext:
            continue
        votes += ((min(ss) + max(ss)) / 2.0 - sc)
    return 0 if abs(votes) < 1.0 else (1 if votes > 0 else -1)


def round_to(x, step):
    return int(round(x / step) * step) if step > 0 else int(round(x))


def find_openings(walls, ents, arcs, wall_segs, round_mm):
    """walls: [HostWall]; ents: [(kind, layer, [(x, y)])] nét CAD theo loại; arcs: [(tâm, bán kính)];
    wall_segs: nét tường CAD [(a, b)]. Trả về [Opening]."""
    result = []
    for w in walls:
        h = w.width / 2.0 + BAND_TOL_MM
        items = []
        for kind, layer, pts in ents:
            lp = [w.local(p) for p in pts]
            if all(abs(d) <= h and -END_TOL_MM <= s <= w.length + END_TOL_MM for s, d in lp):
                items.append((min(s for s, _ in lp), max(s for s, _ in lp), kind, layer, lp))
        if not items:
            continue
        items.sort(key=lambda it: it[0])
        clusters = []
        for it in items:
            if clusters and it[0] <= clusters[-1]["s1"] + JOIN_MM:
                c = clusters[-1]
                c["s1"] = max(c["s1"], it[1])
                c["items"].append(it)
            else:
                clusters.append({"s0": it[0], "s1": it[1], "items": [it]})
        arc_s = []
        for c0, r in arcs:
            s, d = w.local(c0)
            if abs(d) <= h:
                arc_s.append(s)
        ends = None
        for c in clusters:
            if c["s1"] - c["s0"] < MIN_OPEN_MM:
                continue
            if any(c["s0"] - 100.0 <= s <= c["s1"] + 100.0 for s in arc_s):
                continue
            kinds = set(it[2] for it in c["items"])
            kind = KIND_REPORT if KIND_REPORT in kinds else (KIND_SLIDE if KIND_SLIDE in kinds else KIND_WIN)
            op = Opening(w, kind, c["s0"], c["s1"], sorted(set(it[3] for it in c["items"])),
                         [(it[2], it[4]) for it in c["items"]])
            if ends is None:
                ends = []
                for a, b in wall_segs:
                    for p in (a, b):
                        s, d = w.local(p)
                        if abs(d) <= h:
                            ends.append(s)
            lo = [s for s in ends if op.s0 - GAP_SEARCH_MM <= s <= op.s0 + 20.0]
            hi = [s for s in ends if op.s1 - 20.0 <= s <= op.s1 + GAP_SEARCH_MM]
            if lo and hi:
                op.gap_width = min(hi) - max(lo)
            op.width = round_to(op.raw_width, round_mm)
            result.append(op)
    return result


def analyse(walls, ents, arcs, wall_segs, round_mm, existing=None):
    ops = find_openings(walls, ents, arcs, wall_segs, round_mm)
    for op in ops:
        side, dp, dm = outside_side(op, walls)
        op.ext = side
        if abs(dp - dm) < SIDE_MIN_DIFF_MM:
            op.ext_note = u"KIỂM TRA HƯỚNG (tia + {:.0f} / − {:.0f} mm)".format(min(dp, FAR_MM), min(dm, FAR_MM))
        if op.kind == KIND_SLIDE:
            op.hand_side = slide_hand_side(op)
        if op.kind == KIND_REPORT:
            op.status = u"Bỏ qua – layer chỉ báo cáo ({})".format(u"; ".join(op.layers))
            continue
        w = op.wall
        old = []
        for e in existing or []:
            for p in e[0]:
                s, dn = w.local(p)
                ds = abs(s - op.s_center)
                if abs(dn) <= w.width / 2.0 + EXIST_BAND_MM and ds <= max(EXIST_MM, op.raw_width / 2.0):
                    old.append((ds, e))
                    break
        if old:
            p, eid, tname, ow = min(old, key=lambda x: x[0])[1]
            op.eid = eid
            target = op.width if op.kind == KIND_WIN else None
            if target is not None and ow is not None and abs(ow - target) > 1.0:
                op.status = u"Bỏ qua – ô đã có cửa SAI RỘNG (Id {}, {} rộng {:.0f} ≠ {}) – xoá rồi Run lại".format(
                    eid, tname, ow, target)
            else:
                op.status = u"Bỏ qua – ô đã có cửa"
            continue
        op.status = u"OK"
    ops.sort(key=lambda o: (o.kind, -round(o.center()[1]), round(o.center()[0])))
    return ops


TYPE_RE = re.compile(r"^(.*?)(\d+)([xX])(\d+)(.*)$")


def new_type_name(template_name, width, height_text):
    """'SA01-2200x2500' + 1800, '2500' → 'SA01-1800x2500'."""
    m = TYPE_RE.match(template_name)
    if not m:
        return u"{}_{}x{}".format(template_name, width, height_text)
    return u"{}{}{}{}{}".format(m.group(1), width, m.group(3), height_text, m.group(5))


def template_height_text(template_name):
    m = TYPE_RE.match(template_name)
    return m.group(4) if m else None


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


class StopReport(Exception):
    def __init__(self, lines):
        Exception.__init__(self, lines[0])
        self.lines = lines


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


def xy(p):
    return (to_mm(p.X), to_mm(p.Y))


def read_cad(objects, kind_of_layer, wall_layers):
    """→ (ents [(kind, layer, pts)], arcs [(tâm, r)] trên mọi layer cửa, wall_segs)."""
    ents, arcs, wall_segs = [], [], []
    for obj in objects:
        l = layer_of(obj)
        if l in wall_layers:
            if isinstance(obj, Line):
                wall_segs.append((xy(obj.GetEndPoint(0)), xy(obj.GetEndPoint(1))))
            elif isinstance(obj, PolyLine):
                pts = [xy(p) for p in obj.GetCoordinates()]
                wall_segs.extend(zip(pts[:-1], pts[1:]))
            continue
        if l not in kind_of_layer:
            continue
        if isinstance(obj, Arc):
            if obj.IsBound:
                arcs.append((xy(obj.Center), to_mm(obj.Radius)))
            continue
        if isinstance(obj, Line):
            pts = [xy(obj.GetEndPoint(0)), xy(obj.GetEndPoint(1))]
        elif isinstance(obj, PolyLine):
            pts = [xy(p) for p in obj.GetCoordinates()]
        else:
            continue
        ents.append((kind_of_layer[l], l, pts))
    return ents, arcs, wall_segs


def host_walls(level):
    result, by_id = [], {}
    for wl in FilteredElementCollector(doc).OfClass(Wall).ToElements():
        loc = wl.Location
        if wl.LevelId == level.Id and isinstance(loc, LocationCurve) and isinstance(loc.Curve, Line) \
                and to_mm(wl.Width) >= THIN_WALL_MM:
            c = loc.Curve
            hw = HostWall(wl.Id.Value, xy(c.GetEndPoint(0)), xy(c.GetEndPoint(1)), to_mm(wl.Width), get_name(wl))
            result.append(hw)
            by_id[hw.id] = wl
    return result, by_id


def symbol_size(s):
    w = s.get_Parameter(BuiltInParameter.FAMILY_WIDTH_PARAM) or s.LookupParameter("Width")
    h = s.get_Parameter(BuiltInParameter.FAMILY_HEIGHT_PARAM) or s.LookupParameter("Height")
    return (to_mm(w.AsDouble()) if w else None, to_mm(h.AsDouble()) if h else None)


def instance_points(fi):
    """Điểm đại diện của cửa: điểm chèn + tâm hộp bao (điểm chèn SA01 lệch tâm ô, hộp bao của family có cánh mở 3D
    lại lệch khỏi tường) – khớp một trong hai là đủ."""
    pts = []
    loc = getattr(fi, "Location", None)
    if loc is not None and hasattr(loc, "Point"):
        pts.append(xy(loc.Point))
    bb = fi.get_BoundingBox(None)
    if bb is not None:
        pts.append(xy(bb.Min.Add(bb.Max).Multiply(0.5)))
    return pts


def existing_openings():
    """[([điểm mm], Id, tên type, rộng mm)] của mọi cửa sổ + cửa đi đã có (mọi tường chủ, kể cả lớp ốp)."""
    result = []
    for bic in (BuiltInCategory.OST_Windows, BuiltInCategory.OST_Doors):
        for fi in FilteredElementCollector(doc).OfCategory(bic).WhereElementIsNotElementType().ToElements():
            c = instance_points(fi)
            if not c:
                continue
            sym = getattr(fi, "Symbol", None)
            width = symbol_size(sym)[0] if sym is not None else None
            result.append((c, fi.Id.Value, get_name(sym) if sym is not None else u"?", width))
    return result


def family_symbols(family_name, label):
    symbols = [s for s in FilteredElementCollector(doc).OfClass(FamilySymbol).ToElements()
               if norm(s.FamilyName) == norm(family_name)]
    if not symbols:
        raise StopReport([u"DỪNG: không có family '{}' ({}).".format(family_name, label)])
    return symbols


def pick_template(symbols, family_name, template_name, label):
    for s in symbols:
        if norm(get_name(s)) == norm(template_name):
            return s
    raise StopReport([u"DỪNG: family '{}' không có type mẫu '{}' ({}). Các type: {}".format(
        family_name, template_name, label, u", ".join(sorted(get_name(s) for s in symbols)))])


def match_symbol(symbols, width, height):
    for s in symbols:
        w, h = symbol_size(s)
        if w is not None and h is not None and abs(w - width) <= 1.0 and abs(h - height) <= 1.0:
            return s
    return None


def set_size(symbol, width, height):
    for bip, name, v in ((BuiltInParameter.FAMILY_WIDTH_PARAM, "Width", width),
                         (BuiltInParameter.FAMILY_HEIGHT_PARAM, "Height", height)):
        p = symbol.get_Parameter(bip) or symbol.LookupParameter(name)
        if p is None or p.IsReadOnly:
            raise Exception(u"Type '{}' không đặt được tham số {}.".format(get_name(symbol), name))
        p.Set(from_mm(v))


def solid_extent_along(fi, origin, u):
    """(min, max) toạ độ dọc u (mm, tính từ origin) của các khối đặc của cửa."""
    opt = Options()
    opt.DetailLevel = ViewDetailLevel.Fine
    lo, hi = [None], [None]

    def walk(geo):
        for obj in geo:
            if isinstance(obj, GeometryInstance):
                walk(obj.GetInstanceGeometry())
            elif isinstance(obj, Solid) and obj.Volume > 0:
                for e in obj.Edges:
                    for p in e.Tessellate():
                        s = to_mm((p.X - origin.X) * u[0] + (p.Y - origin.Y) * u[1])
                        lo[0] = s if lo[0] is None else min(lo[0], s)
                        hi[0] = s if hi[0] is None else max(hi[0], s)

    geo = fi.get_Geometry(opt)
    if geo is not None:
        walk(geo)
    return (lo[0], hi[0]) if lo[0] is not None else None


# Quy ước hướng của family (+1 / -1). Đã đo trong Revit 2026 (G19): DA01 cánh phía Facing nằm phía +Hand.
# FACING_TO_OUTSIDE = 1: Facing của cửa sổ / cửa lùa chỉ ra ngoài nhà / logia (quy ước family cửa sổ Revit) –
# nếu kiểm tra 3D thấy ngược thì đổi thành -1.
FACING_TO_OUTSIDE = 1
SLIDE_FACING_LEAF_HAND = 1


def orient(fi, op):
    w = op.wall
    ext_vec = (w.n[0] * op.ext, w.n[1] * op.ext)
    doc.Regenerate()
    f = fi.FacingOrientation
    if FACING_TO_OUTSIDE * dot((f.X, f.Y), ext_vec) < 0:
        fi.flipFacing()
        doc.Regenerate()
    if op.kind == KIND_SLIDE and op.hand_side != 0:
        want = (w.u[0] * op.hand_side * SLIDE_FACING_LEAF_HAND, w.u[1] * op.hand_side * SLIDE_FACING_LEAF_HAND)
        # Cánh phía Facing nằm phía +Hand; Facing đã chỉ ra ngoài nếu FACING_TO_OUTSIDE = 1
        h = fi.HandOrientation
        if FACING_TO_OUTSIDE * dot((h.X, h.Y), want) < 0:
            fi.flipHand()
            doc.Regenerate()


def recenter(fi, op, z):
    """Dời cửa dọc tường cho tâm khối đặc trùng tâm ô. Trả về độ dời (mm)."""
    w = op.wall
    c = op.center()
    origin = XYZ(from_mm(c[0]), from_mm(c[1]), z)
    ext = solid_extent_along(fi, origin, w.u)
    if ext is None:
        return None
    shift = -(ext[0] + ext[1]) / 2.0
    if abs(shift) > 0.5:
        ElementTransformUtils.MoveElement(doc, fi.Id, XYZ(from_mm(w.u[0] * shift), from_mm(w.u[1] * shift), 0))
    return shift


def preview_lines(ops, z_mm):
    try:
        clr.AddReference("ProtoGeometry")
        from Autodesk.DesignScript.Geometry import Point as DSPoint, Line as DSLine
        out = []
        for op in ops:
            w = op.wall
            a, b = w.point(op.s0), w.point(op.s1)
            m, e = w.point(op.s_center), w.point(op.s_center, op.ext * 600.0)
            for p, q in ((a, b), (m, e)):
                out.append(DSLine.ByStartPointEndPoint(DSPoint.ByCoordinates(p[0], p[1], z_mm),
                                                       DSPoint.ByCoordinates(q[0], q[1], z_mm)))
        return out
    except Exception:
        return []


LOG_HEADER = [u"STT", u"Loại", u"Layer", u"Tâm ô (mm)", u"Khuôn CAD (mm)", u"Khe tường CAD (mm)", u"Rộng ô (mm)",
              u"Phía ngoài", u"Tường chủ", u"Family", u"Type", u"Kết quả", u"ElementId"]


def write_log(rows, source, dry_run):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoCuaSoTuCAD_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
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


def main(cad_filter, win_layers, slide_layers, report_layers, wall_layers, level_name,
         big_family, big_template, small_family, small_template, big_min, win_h, win_sill,
         slide_family, slide_template, slide_deduct, round_mm, dry_run):
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."], []
    kind_of_layer = {}
    for layers, kind in ((win_layers, KIND_WIN), (slide_layers, KIND_SLIDE), (report_layers, KIND_REPORT)):
        for l in layers:
            kind_of_layer[l] = kind
    cad, cad_name, objects, all_layers = pick_cad(cad_filter, win_layers | slide_layers)
    missing = sorted((win_layers | slide_layers | wall_layers) - all_layers)

    big_syms = family_symbols(big_family, u"IN[6]")
    big_tpl = pick_template(big_syms, big_family, big_template, u"IN[7]")
    small_syms = family_symbols(small_family, u"IN[8]")
    small_tpl = pick_template(small_syms, small_family, small_template, u"IN[9]")
    slide_syms = family_symbols(slide_family, u"IN[13]")
    slide_tpl = pick_template(slide_syms, slide_family, slide_template, u"IN[14]")
    slide_h = symbol_size(slide_tpl)[1]
    slide_h_text = template_height_text(get_name(slide_tpl)) or u"{:.0f}".format(slide_h)
    level = find_level(level_name)
    walls, wall_by_id = host_walls(level)
    if not walls:
        raise StopReport([u"DỪNG: level '{}' chưa có tường thẳng nào để gắn cửa.".format(level_name)])

    ents, arcs, wall_segs = read_cad(objects, kind_of_layer, wall_layers)
    ops = analyse(walls, ents, arcs, wall_segs, round_mm, existing_openings())

    planned = {}   # (family, rộng, cao) → FamilySymbol có sẵn hoặc tên type sẽ nhân bản
    rows, jobs = [], []
    for idx, op in enumerate(ops, 1):
        if op.status == u"OK":
            if op.kind == KIND_WIN:
                big = op.width >= big_min
                fam, syms, tpl = (big_family, big_syms, big_tpl) if big else (small_family, small_syms, small_tpl)
                tw, th, htext = op.width, win_h, u"{:.0f}".format(win_h)
                name_w = op.width
            else:
                fam, syms, tpl = slide_family, slide_syms, slide_tpl
                tw, th, htext = op.width - slide_deduct, slide_h, slide_h_text
                name_w = op.width
            op.family, op.type_width = fam, tw
            key = (fam, int(round(tw)), int(round(th)))
            if key not in planned:
                s = match_symbol(syms, tw, th)
                planned[key] = s if s is not None else (new_type_name(get_name(tpl), name_w, htext), tpl, syms)
            t = planned[key]
            op.type_name = get_name(t) if not isinstance(t, tuple) else t[0] + u" (mới)"
            op.status = u"Sẽ tạo" if dry_run else u"Chờ tạo"
            jobs.append((op, key, len(rows)))
        side = u"{}{}".format(u"+n" if op.ext > 0 else u"−n", (u" – " + op.ext_note) if op.ext_note else u"")
        rows.append([idx, op.kind, u"; ".join(op.layers), fmt(op.center()), u"{:.0f}".format(op.raw_width),
                     u"{:.0f}".format(op.gap_width) if op.gap_width is not None else u"—", op.width, side,
                     u"{} ({})".format(op.wall.id, op.wall.name), op.family or u"—", op.type_name or u"—",
                     op.status, op.eid])

    if not dry_run and jobs:
        TransactionManager.Instance.ForceCloseTransaction()
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        try:
            for key in sorted(planned):
                t = planned[key]
                if isinstance(t, tuple):
                    name, tpl, syms = t
                    same = [s for s in syms if norm(get_name(s)) == norm(name)]
                    new_type = same[0] if same else tpl.Duplicate(name)
                    set_size(new_type, key[1], key[2])
                    planned[key] = new_type
            for op, key, ri in jobs:
                sym = planned[key]
                if not sym.IsActive:
                    sym.Activate()
                    doc.Regenerate()
                wall = wall_by_id[op.wall.id]
                c = op.center()
                z = wall.Location.Curve.GetEndPoint(0).Z
                fi = doc.Create.NewFamilyInstance(XYZ(from_mm(c[0]), from_mm(c[1]), z), sym, wall, level,
                                                  StructuralType.NonStructural)
                sill = fi.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)
                if sill is not None and not sill.IsReadOnly:
                    sill.Set(from_mm(win_sill) if op.kind == KIND_WIN else 0.0)
                orient(fi, op)
                doc.Regenerate()
                recenter(fi, op, z)
                rows[ri][11] = u"Đã tạo"
                rows[ri][12] = fi.Id.Value
            tx.Commit()
        except Exception as ex:
            tx.RollBack()
            return [u"LỖI khi tạo cửa, mọi thay đổi đã được hoàn tác: {}".format(ex)], []

    report = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN")]
    report.append(u"CAD: {} – level: {} – cửa sổ cao {:.0f}, Sill {:.0f} – cửa lùa Width = khe − {:.0f}, Sill 0".format(
        cad_name, level.Name, win_h, win_sill, slide_deduct))
    if missing:
        report.append(u"LƯU Ý: bản CAD không có layer: {}".format(u"; ".join(missing)))
    counts = {}
    for op in ops:
        k = (op.kind, op.status.split(u" – ")[1] if op.status.startswith(u"Bỏ qua") else None)
        counts[k] = counts.get(k, 0) + 1
    for kind in (KIND_WIN, KIND_SLIDE, KIND_REPORT):
        n_job = len([1 for op, _, _ in jobs if op.kind == kind])
        n_all = len([1 for op in ops if op.kind == kind])
        if n_all:
            report.append(u"{}: {} ô – {}: {}".format(kind, n_all, u"sẽ tạo" if dry_run else u"đã tạo", n_job))
    for (kind, why), n in sorted(counts.items(), key=lambda kv: (kv[0][0], kv[0][1] or u"")):
        if why:
            report.append(u"  Bỏ qua {} {}: {}".format(n, kind.lower(), why))
    checks = [op for op in ops if op.ext_note]
    if checks:
        report.append(u"KIỂM TRA HƯỚNG {} ô: {}".format(len(checks), u", ".join(fmt(o.center()) for o in checks)))
    nohand = [op for op, _, _ in jobs if op.kind == KIND_SLIDE and op.hand_side == 0]
    if nohand:
        report.append(u"Cửa lùa không đọc được cánh CAD (giữ Hand mặc định): {}".format(
            u", ".join(fmt(o.center()) for o in nohand)))
    new_types = sorted(set(op.type_name for op, _, _ in jobs if op.type_name.endswith(u"(mới)")))
    if new_types:
        report.append(u"Type {}: {}".format(u"sẽ tạo" if dry_run else u"đã tạo", u", ".join(new_types)))
    try:
        report.append(u"Log: " + write_log(rows, cad_name, dry_run))
    except Exception as ex:
        report.append(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        report.append(u"Xem trước: đoạn ô cửa + vạch 600 mm chỉ phía ngoài / logia. Đúng thì đổi Dry-run = False "
                      u"và Run lại. Undo bằng mục \"{}\".".format(TRANSACTION_NAME))
    report.append(u" | ".join(LOG_HEADER))
    report += [u" | ".join(u"{}".format(v) for v in r) for r in rows]
    return report, preview_lines([op for op, _, _ in jobs], to_mm(level.Elevation))


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
            split_layers(_s(1, u"A-Window;A-Windows")),
            split_layers(_s(2, u"A-Door;A-Cửa")),
            split_layers(_s(3, u"A-Glaz")),
            split_layers(_s(4, u"A-Wall")),
            _s(5, u"Tầng 1"),
            norm(_s(6, u"AV-CuaSo1fix+1Lat")),
            norm(_s(7, u"SA01-2200x2500")),
            norm(_s(8, u"AV-Cửa nhôm kính mở lùa hai cánh trên fix dưới")),
            norm(_s(9, u"1800x1300")),
            float(_s(10, 1800.0)),
            float(_s(11, 2500.0)),
            float(_s(12, 750.0)),
            norm(_s(13, u"AV_Cửa Nhôm kính hai cánh mở trượt")),
            norm(_s(14, u"DA01_2200X2450")),
            float(_s(15, 40.0)),
            float(_s(16, 5.0)),
            True if (len(IN) <= 17 or IN[17] is None) else bool(IN[17]),
        ))
    except StopReport as ex:
        OUT = [ex.lines, []]
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], []]
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with io.open(os.path.join(folder, "TaoCuaSoTuCAD_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))), "w", encoding="utf-8-sig") as f:
                f.write(u"\n".join(OUT[0]))
        except Exception:
            pass
    note = force_rerun_next_time()
    if note:
        OUT[0].append(u"LƯU Ý: " + note)
