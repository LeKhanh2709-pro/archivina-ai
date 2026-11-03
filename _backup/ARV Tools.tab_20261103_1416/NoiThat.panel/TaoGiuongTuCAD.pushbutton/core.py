# TRẠNG THÁI: ĐÃ DUYỆT (BIM Manager, 2026-10-31)
# Mã nguồn của Python node trong 22. ARV_TaoGiuongTuCAD_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Đặt giường (Furniture 2D) trong phòng ngủ từ mặt bằng DWG đã Link, NHẬN DIỆN THEO HÌNH DẠNG như tool 19 máy giặt (Revit gộp nét block
# vào một GeometryInstance nên không dùng tên block). Tách từ phần giường của tool 21 (Dry-run 2026-10-31 15:23, G19 TẦNG 3: 33/33 giường).
#   1. Giường trên CAD, layer A-Nội thất = hình chữ nhật 1600 / 1800 × 2000 có gối và nét chéo gấp chăn (G19: 25 giường 1600, 8 giường 1800).
#      Đầu giường = cạnh ngắn gần các nét bên trong (gối) nhất; hướng ra phòng = từ đầu giường về chân giường.
#   2. Room chứa tâm giường phải có tên chứa một chuỗi trong IN[5] (mặc định "phòng ngủ"). Báo cáo liệt kê phòng lọc mà không có giường.
#   3. Type: rộng CAD ≤ IN[8] dùng IN[3] (1600), lớn hơn dùng IN[4] (1800). Rộng CAD lệch type > 2 mm thì báo "cần soát".
#   4. Vị trí: đầu giường áp mặt nhô ra phòng nhất trong biên Room (Finish) và mặt tường Revit (cả len chân tường tool 11), cách đầu giường
#      CAD ≤ IN[6]; không có → giữ theo CAD, báo "cần soát". Dọc tường giữ tâm CAD.
#   5. Hướng family (suy từ khung type −2000…0 × ±800 / ±900, cần xem trên mặt bằng): gốc giữa đầu giường, đầu giường về +X. Quay ngược → IN[9] = True.
#   6. Cao độ: Elevation from Level = đỉnh sàn tại tâm giường − level + IN[7] (mặc định 1 mm như mẫu người dùng đặt tay: family 2D nằm trên
#      mặt sàn mới thấy trên mặt bằng). Không có sàn → IN[7], báo "cần soát".
#   7. Comments = "ARV-TaoGiuongTuCAD". Giường của tool đã có mà lệch / sai hướng / sai cao độ / khác type → sửa tại chỗ; giường cùng
#      family người dùng tự đặt → bỏ qua.
# INPUT
#   IN[0] (str)   Một phần tên bản CAD (để trống = bản CAD duy nhất trong mô hình / có layer khớp IN[1])
#   IN[1] (str)   Lọc layer, nhiều chuỗi cách ';' (khớp chuỗi con), mặc định "A-Nội thất"; trống = dò mọi layer
#   IN[2] (str)   Tên level đặt giường, VD "TẦNG 3"
#   IN[3] (FamilyType | str) Type giường nhỏ, "Family : Type"
#   IN[4] (FamilyType | str) Type giường lớn, "Family : Type"
#   IN[5] (str)   Tên Room chứa giường, nhiều chuỗi cách ';' (trống = mọi phòng)
#   IN[6] (float) Đầu giường CAD cách mặt tường tối đa để áp tường (mm), VD 100
#   IN[7] (float) Đặt cao hơn mặt sàn (mm), VD 1
#   IN[8] (float) Rộng giường CAD lớn nhất còn dùng type giường nhỏ (mm), VD 1700
#   IN[9] (bool)  Đảo hướng: True nếu giường quay đầu ra phòng (mặc định False)
#   IN[10] (bool) Dry-run: True = đặt thử, báo cáo rồi hoàn tác, không ghi vào mô hình (mặc định True)
# OUTPUT
#   OUT[0] (list[str])  Báo cáo: tóm tắt, đường dẫn log, rồi từng giường
#   OUT[1] (list[Line]) Xem trước: hình CAD, khung sẽ đặt, đoạn hướng ra phòng (mm)

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
                                   Line, Arc, Ellipse, NurbSpline, HermiteSpline, Curve, XYZ, Transaction,
                                   Floor, TransactionStatus, UnitUtils, UnitTypeId, ModelPathUtils,
                                   BuiltInParameter, BuiltInCategory, Level, Wall, LocationCurve, LocationPoint, FamilySymbol,
                                   FamilyPlacementType, ElementTransformUtils, SpatialElementBoundaryOptions,
                                   SpatialElementBoundaryLocation, ElementId, Solid, WorksharingUtils, CheckoutStatus)
    from Autodesk.Revit.DB.Structure import StructuralType
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = u"ARV - Tạo giường từ CAD"
SCRIPT_TAG = u"ARV_TaoGiuongTuCAD_v1"
COMMENT_TAG = u"ARV-TaoGiuongTuCAD"
MAX_EDGE_MM = 3000.0             # Nét dài hơn không thể là nét giường – bỏ khi đọc CAD
SNAP_MM = 1.0                    # Đầu mút cách nhau ≤ chừng này coi là nối nhau
RIGHT_COS = 0.02                 # Góc vuông: |cos| ≤ chừng này (lệch ≤ ~1°)
PARALLEL_COS = 0.995             # Mặt song song / vuông góc: |cos| ≥ chừng này
EDGE_TOL_MM = 5.0                # Cạnh của hình chữ nhật lệch vị trí tối đa
SAME_LEN_MM = 10.0               # Hai cạnh đối của hình chữ nhật lệch dài tối đa
EDGE_MIN_MM = 1300.0             # Cạnh ngắn nhất cần ghép
EDGE_MAX_MM = 2300.0             # Cạnh dài nhất cần ghép
SAME_MM = 100.0                  # Hai hình có tâm cách ≤ chừng này = cùng một giường
GRID_MM = 1000.0                 # Ô lưới tra nét theo vị trí
EXIST_TOL_MM = 500.0             # Giường cùng family có tâm cách tâm CAD ≤ chừng này → đã có
TOP_MM = 1000.0                  # Tường có chân cao hơn level chừng này không vướng
ROOM_INSET_MM = 5.0              # Kiểm tra giường nằm trong Room: thu khung vào chừng này
FIT_TOL_MM = 2.0                 # Cỡ family lệch CAD tối đa, quá thì báo cần soát

# Nhận diện: (cạnh ngắn min, max, cạnh dài min, max)
SIZE_BED = (1400.0, 2000.0, 1900.0, 2200.0)
BED_DIAG_MM = 300.0              # Nét chéo gấp chăn dài tối thiểu (G19: 636)
BED_DIAG_COS = (0.5, 0.87)       # |cos| nét chéo với cạnh dài


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


def loose(s):
    """So tên không phân biệt dấu / hoa thường: "Vệ sinh" ≈ "VE SINH"."""
    s = unicodedata.normalize("NFD", norm(s).replace(u"đ", u"d").replace(u"Đ", u"D"))
    return u"".join(c for c in s if unicodedata.category(c) != "Mn").lower()


class Item(object):
    """Một nét CAD: danh sách điểm (mm) + có phải nét cong."""

    def __init__(self, pts, curved):
        self.pts, self.curved = pts, curved


class Seg(object):
    """Một đoạn biên Room trên mặt bằng (mm)."""

    def __init__(self, a, b):
        self.a, self.b = a, b


def same(p, q):
    return abs(p[0] - q[0]) <= SNAP_MM and abs(p[1] - q[1]) <= SNAP_MM


def inside_loops(p, loops):
    """Điểm trong vùng giới hạn bởi các vòng biên (chẵn lẻ – lỗ trong Room tự trừ)."""
    c = False
    for pts in loops:
        for i in range(len(pts)):
            (x1, y1), (x2, y2) = pts[i - 1], pts[i]
            if (y1 > p[1]) != (y2 > p[1]) and p[0] < x1 + (p[1] - y1) * (x2 - x1) / (y2 - y1):
                c = not c
    return c


class Rect(object):
    """Hình chữ nhật trên CAD: tâm, trục cạnh dài / ngắn, cỡ, 4 góc."""

    def __init__(self, c):
        l1, l2 = math.hypot(*sub(c[1], c[0])), math.hypot(*sub(c[2], c[1]))
        e1, e2 = unit(sub(c[1], c[0])), unit(sub(c[2], c[1]))
        self.corners = c
        self.c = ((c[0][0] + c[2][0]) / 2.0, (c[0][1] + c[2][1]) / 2.0)
        self.along, self.across = (e1, e2) if l1 >= l2 else (e2, e1)
        self.long, self.short = max(l1, l2), min(l1, l2)

    def fits(self, size):
        return size[0] <= self.short <= size[1] and size[2] <= self.long <= size[3]

    def contains(self, p, tol=SNAP_MM):
        q = sub(p, self.c)
        return abs(dot(q, self.along)) <= self.long / 2.0 + tol and abs(dot(q, self.across)) <= self.short / 2.0 + tol

class Bed(object):
    """Một giường nhận diện được + giường sẽ đặt. Hệ trục riêng: gốc = giữa đầu giường CAD, dir = hướng ra phòng, u = dọc tường;
    s = toạ độ dọc tường, d = toạ độ ra phòng (đầu giường CAD d = 0)."""

    def __init__(self, rect, d):
        self.rect, self.c, self.corners = rect, rect.c, rect.corners
        self.width, self.depth = rect.short, rect.long
        self.dir = d
        self.u = (-d[1], d[0])
        self.back = (self.c[0] - d[0] * self.depth / 2.0, self.c[1] - d[1] * self.depth / 2.0)
        self.mount_d = 0.0       # mặt dựa (d)
        self.final = None        # khung sau khi căn (s0, s1, d0, d1)
        self.room = u""
        self.number = u""
        self.hit = None
        self.status = u""
        self.eid = u""
        self.note = u""
        self.dups = []

    def local(self, p):
        q = sub(p, self.back)
        return dot(q, self.u), dot(q, self.dir)

    def world(self, s, d):
        return (self.back[0] + self.u[0] * s + self.dir[0] * d, self.back[1] + self.u[1] * s + self.dir[1] * d)


class Index(object):
    """Tra nét thẳng theo vị trí: mỗi đoạn ghi vào ô lưới chứa đầu mút của nó."""

    def __init__(self, items):
        self.cells = {}
        for it in items:
            if it.curved:
                continue
            for k in range(1, len(it.pts)):
                a, b = it.pts[k - 1], it.pts[k]
                if math.hypot(*sub(b, a)) >= 1.0:
                    self.cells.setdefault((int(a[0] // GRID_MM), int(a[1] // GRID_MM)), []).append((a, b))

    def segs_in(self, r):
        n = int((r.long / 2.0) // GRID_MM) + 1
        cx, cy = int(r.c[0] // GRID_MM), int(r.c[1] // GRID_MM)
        return [(a, b) for dx in range(-n, n + 1) for dy in range(-n, n + 1) for a, b in self.cells.get((cx + dx, cy + dy), [])
                if r.contains(a) and r.contains(b)]


def edge_rects(items):
    """[4 góc] hình chữ nhật ghép từ các cạnh (Revit có thể gộp nét trùng thành PolyLine đi hai vòng, tool 19, nên không dựa vòng kín):
    hai cạnh song song cùng dài, hai đầu có cạnh vuông góc."""
    segs, cells = [], {}

    def cell(p):
        return (int(p[0] // EDGE_MAX_MM), int(p[1] // EDGE_MAX_MM))

    for it in items:
        if it.curved:
            continue
        for k in range(1, len(it.pts)):
            a, b = it.pts[k - 1], it.pts[k]
            ln = math.hypot(*sub(b, a))
            if EDGE_MIN_MM <= ln <= EDGE_MAX_MM:
                m = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
                cells.setdefault(cell(m), []).append(len(segs))
                segs.append((m, unit(sub(b, a)), ln))

    def around(p):
        c = cell(p)
        return [i for dx in (-1, 0, 1) for dy in (-1, 0, 1) for i in cells.get((c[0] + dx, c[1] + dy), [])]

    def has_edge(p, u):
        for i in around(p):
            m, v, _ = segs[i]
            if abs(dot(u, v)) <= RIGHT_COS and math.hypot(*sub(m, p)) <= EDGE_TOL_MM:
                return True
        return False

    result = []
    for i, (m, u, ln) in enumerate(segs):
        n = (-u[1], u[0])
        for j in around(m):
            m2, u2, ln2 = segs[j]
            if j <= i or abs(dot(u, u2)) < PARALLEL_COS or abs(ln - ln2) > SAME_LEN_MM:
                continue
            v = sub(m2, m)
            h = dot(v, n)
            if abs(dot(v, u)) > EDGE_TOL_MM or not (EDGE_MIN_MM <= abs(h) <= ln + SAME_LEN_MM):
                continue
            k = ln / 2.0
            c = [(m[0] - u[0] * k, m[1] - u[1] * k), (m[0] + u[0] * k, m[1] + u[1] * k)]
            c += [(c[1][0] + n[0] * h, c[1][1] + n[1] * h), (c[0][0] + n[0] * h, c[0][1] + n[1] * h)]
            mid1 = ((c[1][0] + c[2][0]) / 2.0, (c[1][1] + c[2][1]) / 2.0)
            mid2 = ((c[0][0] + c[3][0]) / 2.0, (c[0][1] + c[3][1]) / 2.0)
            if has_edge(mid1, u) and has_edge(mid2, u):
                result.append(c)
    return result


def bed_head(r, idx):
    """Hướng ra phòng của giường (từ đầu giường về chân) nếu có nét chéo gấp chăn; None nếu không phải giường.
    Đầu giường = cạnh ngắn gần tâm các nét bên trong (gối, mép chăn)."""
    inner = []
    diag = False
    for a, b in idx.segs_in(r):
        ln = math.hypot(*sub(b, a))
        cos = abs(dot(unit(sub(b, a)), r.along))
        if ln >= BED_DIAG_MM and BED_DIAG_COS[0] <= cos <= BED_DIAG_COS[1]:
            diag = True
        if max(abs(dot(sub(p, r.c), r.along)) for p in (a, b)) < r.long / 2.0 - 1.0 or cos < 0.1:
            inner.append(dot(sub(((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0), r.c), r.along))
    if not diag or not inner:
        return None
    mean = sum(inner) / len(inner)
    return (-r.along[0], -r.along[1]) if mean > 0 else r.along


def mount_offset(p, segs, tol):
    """d của mặt song song lưng, chạm bề rộng món đồ, cách lưng CAD ≤ tol: mặt NHÔ RA PHÒNG NHẤT để không ăn vào lớp nào; None nếu
    không có."""
    best = None
    half = p.width / 2.0
    for sg in segs:
        sa, da = p.local(sg.a)
        sb, db = p.local(sg.b)
        ln = math.hypot(sb - sa, db - da)
        if ln < 1.0 or abs(sb - sa) / ln < PARALLEL_COS or max(sa, sb) <= -half or min(sa, sb) >= half:
            continue
        d = (da + db) / 2.0
        if abs(d) <= tol and (best is None or d > best):
            best = d
    return best

def fit_back(b, segs, tol):
    """Mặt dựa của đầu giường. Trả về ghi chú."""
    d = mount_offset(b, segs, tol)
    if d is None:
        return u"không có tường sau đầu giường (≤ {:.0f} mm) – giữ theo CAD, cần soát".format(tol)
    b.mount_d = d
    return u""


def find_beds(items, room_at, keys, stats=None):
    """[Bed] trong Room khớp keys. room_at(pt) → (tên, [vòng], số phòng) | None. Giường ngoài phòng lọc bỏ qua, đếm vào stats."""
    idx = Index(items)
    rects = [Rect(c) for c in edge_rects(items)]
    rects.sort(key=lambda r: -r.long * r.short)
    sized = [r for r in rects if r.fits(SIZE_BED)]
    found, outside = [], 0
    for r in sized:
        d = bed_head(r, idx)
        if d is None or any(math.hypot(*sub(q.c, r.c)) <= SAME_MM for q in found):
            continue
        b = Bed(r, d)
        hit = room_at(r.c) if room_at is not None else None
        if room_at is not None and keys and not (hit and any(k in loose(hit[0]) for k in keys)):
            outside += 1
            continue
        if hit:
            b.room, b.number, b.hit = hit[0], hit[2], hit
        found.append(b)
    if stats is not None:
        stats.update(rects=len(sized), outside=outside)
    return found


def analyse(items, back_tol, room_at=None, keys=(), stats=None, walls=()):
    """items: [Item] mm; walls: [Seg] mặt tường trên level. Trả về [Bed] đã căn đầu giường; sắp theo phòng."""
    beds = find_beds(items, room_at, keys, stats)
    for b in beds:
        loops = b.hit[1] if b.hit else []
        segs = [Seg(pts[i - 1], pts[i]) for pts in loops for i in range(len(pts))] + list(walls)
        b.note = fit_back(b, segs, back_tol)
        b.status = u"OK"
    beds.sort(key=lambda q: (q.number, -round(q.c[1]), round(q.c[0])))
    return beds


def wall_faces(p0, p1, along_x):
    """Hai mặt bên (Seg) của tường song song trục X / Y từ khung bao (p0, p1 mm): khung bao đúng cả khi Location Line của
    tường không ở tim."""
    if along_x:
        return [Seg((p0[0], y), (p1[0], y)) for y in (p0[1], p1[1])]
    return [Seg((x, p0[1]), (x, p1[1])) for x in (p0[0], p1[0])]


def body_fit(pts, p):
    """Căn khung (điểm (x, y) mm của instance) theo món đích. Trả về (dời (dx, dy), khung (s0, s1, d0, d1))."""
    ss = [p.local(q)[0] for q in pts]
    ds = [p.local(q)[1] for q in pts]
    m_s = -(min(ss) + max(ss)) / 2.0
    m_d = p.mount_d - min(ds)
    move = (p.u[0] * m_s + p.dir[0] * m_d, p.u[1] * m_s + p.dir[1] * m_d)
    return move, (min(ss) + m_s, max(ss) + m_s, min(ds) + m_d, max(ds) + m_d)


def inside_room(p, loops):
    """Bốn góc khung (thu vào ROOM_INSET_MM) nằm trong Room."""
    s0, s1, d0, d1 = p.final
    k = ROOM_INSET_MM
    return all(inside_loops(p.world(s, d), loops) for s in (s0 + k, s1 - k) for d in (d0 + k, d1 - k))


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
    # So khớp không phân biệt hoa thường, chuẩn hoá Unicode; không lọc = mọi layer
    if not filters:
        return set(all_layers)
    return set(l for l in all_layers if any(norm(f).lower() in norm(l).lower() for f in filters))


class StopReport(Exception):
    def __init__(self, lines):
        Exception.__init__(self, lines[0])
        self.lines = lines


def pick_cad(cad_filter, filters):
    """Chọn bản CAD theo tên; để trống thì lấy bản CAD duy nhất (có layer khớp). Trả về (cad, tên, objects, layers)."""
    found = []
    for inst in FilteredElementCollector(doc).OfClass(ImportInstance).ToElements():
        name = get_name(doc.GetElement(inst.GetTypeId()))
        if cad_filter and cad_filter.lower() not in name.lower():
            continue
        objects = cad_objects(inst)
        all_layers = sorted(set(l for l in (layer_of(o) for o in objects) if l))
        found.append((inst, name, objects, all_layers))
    hits = [f for f in found if f[2] and match_layers(f[3], filters)]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        lines = [u"DỪNG: không có bản CAD{} nào{} đọc được hình học (link CAD chưa load?).".format(
            u" khớp '{}'".format(cad_filter) if cad_filter else u"",
            u" có layer chứa '{}'".format(u"; ".join(filters)) if filters else u"")]
        for inst, name, _, layers in found:
            lines.append(u"Layer của {}: {}".format(name, u", ".join(layers) or u"(không đọc được hình học)"))
        raise StopReport(lines)
    raise StopReport([u"DỪNG: {} bản CAD – nhập tên bản CAD vào ô IN[0]: {}".format(
        len(hits), u", ".join(h[1] for h in hits))])


def find_level(name):
    levels = list(FilteredElementCollector(doc).OfClass(Level).ToElements())
    for l in levels:
        if norm(l.Name).lower() == norm(name).lower():
            return l
    raise StopReport([u"DỪNG: không có level '{}'. Các level: {}".format(
        name, u", ".join(l.Name for l in sorted(levels, key=lambda x: x.Elevation)))])


def xy(p):
    return (to_mm(p.X), to_mm(p.Y))


def block_name(inst):
    """Tên block của GeometryInstance CAD; rỗng nếu Revit không cho biết."""
    try:
        sym = doc.GetElement(inst.GetSymbolGeometryId().SymbolId)
        if sym is not None:
            return get_name(sym)
    except Exception:
        pass
    try:
        return get_name(inst.Symbol)
    except Exception:
        return u""


def read_items(objects, layers):
    """Nét ngắn – ứng viên nét giường (thẳng + cong); layers = None: mọi nét, kể cả nét Revit không trả tên layer.
    Trả về (items, {loại: số})."""
    items, kinds, lim = [], {}, from_mm(MAX_EDGE_MM)
    for obj in objects:
        if layers is not None and layer_of(obj) not in layers:
            continue
        kind = obj.GetType().Name
        kinds[kind] = kinds.get(kind, 0) + 1
        if isinstance(obj, PolyLine):
            pts = list(obj.GetCoordinates())
            if len(pts) >= 2:
                ext = max(max(p.X for p in pts) - min(p.X for p in pts), max(p.Y for p in pts) - min(p.Y for p in pts))
                if ext <= lim:
                    # PolyLine ≥ 12 đỉnh = cung Revit đã chia đoạn (Revit 2027 đổi elip / spline thành PolyLine, tool 14)
                    items.append(Item([xy(p) for p in pts], len(pts) >= 12))
        elif isinstance(obj, Arc) and not obj.IsBound:
            # Vòng tròn CAD: Arc không giới hạn, tự chia theo tâm + bán kính
            c, r = xy(obj.Center), to_mm(obj.Radius)
            if r <= MAX_EDGE_MM:
                items.append(Item([(c[0] + r * math.cos(k * math.pi / 12.0), c[1] + r * math.sin(k * math.pi / 12.0))
                                   for k in range(25)], True))
        elif isinstance(obj, Curve) and obj.IsBound:
            if isinstance(obj, Line):
                if obj.Length <= lim:
                    items.append(Item([xy(obj.GetEndPoint(0)), xy(obj.GetEndPoint(1))], False))
            elif isinstance(obj, (Arc, Ellipse, NurbSpline, HermiteSpline)) and obj.Length <= 2 * lim:
                items.append(Item([xy(p) for p in obj.Tessellate()], True))
    return items, kinds


def room_finder(level):
    """(room_at, rooms): room_at(pt mm) → (tên Room, [vòng biên Finish mm], số Room) trên level chứa điểm, None nếu không có;
    rooms: [(khung, vòng, tên, số)] mọi Room trên level."""
    opt = SpatialElementBoundaryOptions()
    opt.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.Finish
    rooms = []
    for r in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms) \
            .WhereElementIsNotElementType().ToElements():
        if r.LevelId != level.Id or r.Area <= 0:
            continue
        loops = []
        for segs in r.GetBoundarySegments(opt) or []:
            pts = []
            for seg in segs:
                pts.extend(xy(q) for q in list(seg.GetCurve().Tessellate())[:-1])
            if len(pts) >= 3:
                loops.append(pts)
        if not loops:
            continue
        xs = [q[0] for l in loops for q in l]
        ys = [q[1] for l in loops for q in l]
        name = r.get_Parameter(BuiltInParameter.ROOM_NAME)
        number = r.get_Parameter(BuiltInParameter.ROOM_NUMBER)
        rooms.append(((min(xs), min(ys), max(xs), max(ys)), loops, name.AsString() if name is not None else u"",
                      number.AsString() if number is not None else u""))

    def room_at(p):
        for box, loops, name, number in rooms:
            if box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3] and inside_loops(p, loops):
                return name, loops, number
        return None
    return room_at, rooms


def wall_segs(level):
    """[Seg] mặt tường thẳng song song trục toạ độ trên level, gồm lớp ốp, trát, len chân tường (tool 09, 11, 12); bỏ tường có
    chân cao hơn TOP_MM so với level (không vướng)."""
    segs = []
    lim = level.Elevation + from_mm(TOP_MM)
    for wl in FilteredElementCollector(doc).OfClass(Wall).ToElements():
        loc, bb = wl.Location, wl.get_BoundingBox(None)
        if wl.LevelId != level.Id or bb is None or bb.Min.Z > lim:
            continue
        if not isinstance(loc, LocationCurve) or not isinstance(loc.Curve, Line):
            continue
        d = loc.Curve.Direction
        if max(abs(d.X), abs(d.Y)) >= PARALLEL_COS:
            segs += wall_faces(xy(bb.Min), xy(bb.Max), abs(d.X) > abs(d.Y))
    return segs


def furniture_symbols():
    return [s for s in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Furniture)
            .WhereElementIsElementType().ToElements() if isinstance(s, FamilySymbol)]


def level_floors(level):
    """[(x0, y0, x1, y1, đỉnh sàn so với level mm)] mọi sàn trên level."""
    result = []
    for fl in FilteredElementCollector(doc).OfClass(Floor).OfCategory(BuiltInCategory.OST_Floors):
        bb = fl.get_BoundingBox(None)
        if fl.LevelId != level.Id or bb is None:
            continue
        x0, y0 = xy(bb.Min)
        x1, y1 = xy(bb.Max)
        result.append((x0, y0, x1, y1, to_mm(bb.Max.Z - level.Elevation)))
    return result


def floor_top(floors, p):
    """Đỉnh sàn tại điểm p; None nếu không có sàn. Lấy sàn THẤP NHẤT trong các sàn có khung bao chứa p: khung bao sàn WC (+65) và gờ logia
    (+165) có thể trùm vào phòng ngủ (+50), còn sàn phòng ngủ luôn nằm trong số đó."""
    hits = [f[4] for f in floors if f[0] <= p[0] <= f[2] and f[1] <= p[1] <= f[3]]
    return min(hits) if hits else None


def pick_template(value, label):
    """FamilyType của node Family Types (Dynamo) hoặc chuỗi "Family : Type" → FamilySymbol."""
    symbols = furniture_symbols()
    families = u", ".join(sorted(set(u"{} : {}".format(s.FamilyName, get_name(s)) for s in symbols))) or u"không có"
    if isinstance(value, str):
        parts = [norm(p) for p in value.split(u":")]
        if len(parts) != 2 or not all(parts):
            raise StopReport([u"DỪNG: ô {} phải là type chọn từ node Family Types hoặc chuỗi 'Family : Type' "
                              u"(đang là '{}').".format(label, value)])
        hits = [s for s in symbols if norm(s.FamilyName) == parts[0] and norm(get_name(s)) == parts[1]]
        if not hits:
            raise StopReport([u"DỪNG: không có type '{}' ({}). Type Furniture: {}".format(value, label, families)])
        return hits[0]
    sym = UnwrapElement(value) if value is not None else None
    if not isinstance(sym, FamilySymbol):
        raise StopReport([u"DỪNG: chưa chọn type ở {}.".format(label)])
    if sym.Category is None or sym.Category.BuiltInCategory != BuiltInCategory.OST_Furniture:
        raise StopReport([u"DỪNG: type '{} : {}' ({}) không thuộc Furniture. Type Furniture: {}".format(
            sym.FamilyName, get_name(sym), label, families)])
    return sym


def body_points(fi):
    """Khung instance trên mặt bằng (x, y mm). Family 2D có khung cao gần 0 nhưng vẫn có X, Y."""
    bb = fi.get_BoundingBox(None)
    if bb is None:
        # Không có khung instance: dùng khung type đưa về vị trí instance
        tb, tf = fi.Symbol.get_BoundingBox(None), fi.GetTransform()
        if tb is None:
            return []
        pts = [tf.OfPoint(XYZ(x, y, 0.0)) for x in (tb.Min.X, tb.Max.X) for y in (tb.Min.Y, tb.Max.Y)]
        xs, ys = [to_mm(q.X) for q in pts], [to_mm(q.Y) for q in pts]
        return [(min(xs), min(ys)), (max(xs), min(ys)), (max(xs), max(ys)), (min(xs), max(ys))]
    x0, y0 = xy(bb.Min)
    x1, y1 = xy(bb.Max)
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

def existing_fixtures(families, level):
    """[(tâm mm, Id, có Comments của tool)] giường đã đặt trên level: cùng family, hoặc do tool tạo."""
    result = []
    for fi in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Furniture) \
            .WhereElementIsNotElementType().ToElements():
        sym = getattr(fi, "Symbol", None)
        if sym is None or fi.LevelId != level.Id or not isinstance(getattr(fi, "Location", None), LocationPoint):
            continue
        cm = fi.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        mine = cm is not None and cm.AsString() == COMMENT_TAG
        if norm(sym.FamilyName) not in families and not mine:
            continue
        pts = body_points(fi)
        if pts:
            c = ((pts[0][0] + pts[2][0]) / 2.0, (pts[0][1] + pts[2][1]) / 2.0)
        else:
            c = xy(fi.Location.Point)
        result.append((c, fi.Id.Value, mine))
    return result


def elevation_param(fi):
    """Cao độ instance so với level ("Elevation from Level" / "Offset from Host")."""
    return fi.get_Parameter(BuiltInParameter.INSTANCE_ELEVATION_PARAM) or \
        fi.get_Parameter(BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM)

def facing_for(b, flip):
    """FacingOrientation (trục +Y family) cần có để trục +X family (đầu giường) chỉ về tường."""
    back = b.dir if flip else (-b.dir[0], -b.dir[1])
    return (-back[1], back[0])


def settle(fi, b, sym, elev, flip):
    """Trong Transaction: đổi type, xoay, đặt cao độ, dời cho khung về đúng đích. Trả về [việc đã làm], [ghi chú cần soát]."""
    todo, warn = [], []
    if fi.Symbol.Id != sym.Id:
        todo.append(u"đổi type {} : {}".format(fi.Symbol.FamilyName, get_name(fi.Symbol)))
        fi.ChangeTypeId(sym.Id)
    doc.Regenerate()
    want = facing_for(b, flip)
    f = fi.FacingOrientation
    ang = math.atan2(f.X * want[1] - f.Y * want[0], f.X * want[0] + f.Y * want[1])
    if abs(ang) > 1e-3:
        q = fi.Location.Point
        ElementTransformUtils.RotateElement(doc, fi.Id, Line.CreateBound(q, XYZ(q.X, q.Y, q.Z + 1.0)), ang)
        todo.append(u"xoay {:.0f}°".format(math.degrees(ang)))
    ep = elevation_param(fi)
    if ep is None or ep.IsReadOnly:
        warn.append(u"không đặt được cao độ, cần soát")
    elif abs(to_mm(ep.AsDouble()) - elev) > 0.5:
        todo.append(u"cao độ {:.0f} → {:.0f}".format(to_mm(ep.AsDouble()), elev))
        ep.Set(from_mm(elev))
    doc.Regenerate()
    pts = body_points(fi)
    if not pts:
        b.final = (-b.width / 2.0, b.width / 2.0, b.mount_d, b.mount_d + b.depth)
        return todo, warn + [u"không đọc được khung của family – đặt theo gốc family, cần soát"]
    move, b.final = body_fit(pts, b)
    if math.hypot(*move) > 0.5:
        ElementTransformUtils.MoveElement(doc, fi.Id, XYZ(from_mm(move[0]), from_mm(move[1]), 0.0))
        todo.append(u"dời {:.0f} mm".format(math.hypot(*move)))
    if abs((b.final[1] - b.final[0]) - b.width) > FIT_TOL_MM or abs((b.final[3] - b.final[2]) - b.depth) > FIT_TOL_MM:
        warn.append(u"cỡ type khác CAD, cần soát")
    return todo, warn


DIAG_HEADER = [u"Phòng", u"Số phòng", u"Loại", u"Layer", u"Xmin", u"Ymin", u"Rộng X", u"Rộng Y", u"Số điểm", u"Khép kín",
               u"Bán kính", u"Thể tích (mm3)", u"Toạ độ (x y; …)"]


def object_points(obj):
    """Điểm (x, y mm) của một đối tượng CAD để chẩn đoán; [] nếu không đọc được."""
    try:
        if isinstance(obj, PolyLine):
            return [xy(p) for p in obj.GetCoordinates()]
        if isinstance(obj, Arc) and not obj.IsBound:
            c, r = xy(obj.Center), to_mm(obj.Radius)
            return [(c[0] - r, c[1] - r), (c[0] + r, c[1] + r)]
        if isinstance(obj, Curve):
            return [xy(p) for p in obj.Tessellate()]
        if isinstance(obj, Solid):
            return [xy(p) for e in obj.Edges for p in e.Tessellate()]
    except Exception:
        pass
    return []


def write_diag(cad, objects, room_at, keys):
    """File chẩn đoán (chỉ dry-run): mọi đối tượng CAD có tâm trong Room khớp keys, kèm số lượng theo tên block."""
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    path = os.path.join(folder, "TaoGiuongTuCAD_CHANDOAN_{}.csv".format(datetime.datetime.now().strftime("%Y%m%d_%H%M%S")))
    names = {}
    opt = Options()
    if cad.ViewSpecific:
        opt.View = doc.GetElement(cad.OwnerViewId)

    def walk(geo, depth):
        for obj in geo:
            if isinstance(obj, GeometryInstance):
                k = (depth, block_name(obj))
                names[k] = names.get(k, 0) + 1
                walk(obj.GetInstanceGeometry(), depth + 1)

    geo = cad.get_Geometry(opt)
    if geo is not None:
        walk(geo, 0)
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(DIAG_HEADER)
        for obj in objects:
            pts = object_points(obj)
            if not pts:
                continue
            x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
            y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
            hit = room_at(((x0 + x1) / 2.0, (y0 + y1) / 2.0))
            if hit is None or (keys and not any(k in loose(hit[0]) for k in keys)):
                continue
            w.writerow([hit[0], hit[2], obj.GetType().Name, layer_of(obj) or u"(không có)", u"{:.1f}".format(x0),
                        u"{:.1f}".format(y0), u"{:.1f}".format(x1 - x0), u"{:.1f}".format(y1 - y0), len(pts),
                        u"có" if len(pts) > 2 and same(pts[0], pts[-1]) else u"",
                        u"{:.1f}".format(to_mm(obj.Radius)) if isinstance(obj, Arc) else u"",
                        u"{:.0f}".format(obj.Volume * to_mm(1.0) ** 3) if isinstance(obj, Solid) else u"",
                        u"; ".join(u"{:.1f} {:.1f}".format(p[0], p[1]) for p in pts[:40])])
        w.writerow([])
        w.writerow([u"TÊN BLOCK", u"Độ sâu", u"Số lần"])
        for (depth, name), n in sorted(names.items(), key=lambda kv: (kv[0][0], u"{}".format(kv[0][1]))):
            w.writerow([name or u"(không đọc được tên)", depth, n])
    return path


def preview_lines(pieces, z_mm):
    try:
        clr.AddReference("ProtoGeometry")
        from Autodesk.DesignScript.Geometry import Point as DSPoint, Line as DSLine

        def seg(a, e):
            return DSLine.ByStartPointEndPoint(DSPoint.ByCoordinates(a[0], a[1], z_mm),
                                               DSPoint.ByCoordinates(e[0], e[1], z_mm))
        lines = []
        for p in pieces:
            lines += [seg(p.corners[i - 1], p.corners[i]) for i in range(4)]
            if p.final is not None:
                s0, s1, d0, d1 = p.final
                box = [p.world(s0, d0), p.world(s1, d0), p.world(s1, d1), p.world(s0, d1)]
                lines += [seg(box[i - 1], box[i]) for i in range(4)]
                s = (s0 + s1) / 2.0
                lines.append(seg(p.world(s, (d0 + d1) / 2.0), p.world(s, d1 + 200.0)))
        return lines
    except Exception:
        return []


LOG_HEADER = [u"STT", u"Tâm CAD (mm)", u"Phòng", u"Số phòng", u"Cỡ CAD (rộng × dài, mm)", u"Cỡ đặt (rộng × dài, mm)",
              u"Cao độ so với level (mm)", u"Type", u"Kết quả", u"ElementId", u"Ghi chú"]


def write_log(rows, source, dry_run):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoGiuongTuCAD_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
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

def main(cad_filter, layer_filters, level_name, templates, room_keys, back_tol, lift, small_max, flip, dry_run):
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."], []
    if re.search(r"[-_]S[-_]", doc.Title or u""):
        return [u"DỪNG: tên file '{}' là mô hình Kết cấu (S) – giường chỉ đặt trên mô hình Kiến trúc (A).".format(
            doc.Title)], []
    small, large = pick_template(templates[0], u"IN[3]"), pick_template(templates[1], u"IN[4]")
    for s in (small, large):
        if s.Family.FamilyPlacementType not in (FamilyPlacementType.OneLevelBased, FamilyPlacementType.WorkPlaneBased):
            raise StopReport([u"DỪNG: family '{}' kiểu đặt {} – công cụ chỉ hỗ trợ family đặt theo level hoặc Work Plane "
                              u"Based.".format(s.FamilyName, s.Family.FamilyPlacementType)])

    def symbol_of(b):
        return small if b.width <= small_max else large

    def label_of(s):
        return u"{} : {}".format(norm(s.FamilyName), get_name(s))

    cad, cad_name, objects, all_layers = pick_cad(cad_filter, layer_filters)
    layers = match_layers(all_layers, layer_filters)
    level = find_level(level_name)
    level_z = to_mm(level.Elevation)
    room_at, rooms = room_finder(level)
    keys = [loose(k) for k in room_keys if k.strip()]
    if keys and not rooms:
        raise StopReport([u"DỪNG: level '{}' chưa có Room – cần Room để lọc phòng ngủ (hoặc để trống IN[5]).".format(level_name)])

    items, kinds = read_items(objects, layers if layer_filters else None)
    stats = {}
    walls = wall_segs(level)
    beds = analyse(items, back_tol, room_at, keys, stats, walls)
    floors = level_floors(level)
    existing = existing_fixtures(set([norm(small.FamilyName), norm(large.FamilyName)]), level)

    rows, jobs, fixes = [], [], []
    for idx, b in enumerate(beds, 1):
        near = sorted((math.hypot(*sub(c, b.c)), eid, mine) for c, eid, mine in existing
                      if math.hypot(*sub(c, b.c)) <= EXIST_TOL_MM)
        if near:
            b.eid = near[0][1]
            b.dups = [eid for _, eid, _ in near[1:]]
            b.status = u"Bỏ qua – đã có giường cùng family (Id {})".format(b.eid)
            if near[0][2]:
                fi = doc.GetElement(ElementId(b.eid))
                if WorksharingUtils.GetCheckoutStatus(doc, fi.Id) == CheckoutStatus.OwnedByOtherUser:
                    b.status = u"Bỏ qua – người khác đang mượn (Id {})".format(b.eid)
                else:
                    fixes.append((fi, len(rows), b))
        else:
            jobs.append((b, len(rows)))
        rows.append([idx, fmt(b.c), b.room or u"—", b.number or u"—", u"{:.0f} × {:.0f}".format(b.width, b.depth), u"—", u"—",
                     u"—", b.status, b.eid, u"; ".join(v for v in [b.note] + [u"TRÙNG Id {}".format(d) for d in b.dups] if v)])

    changed = 0
    created = []
    if jobs or fixes:
        # Dry-run cũng đặt thử rồi RollBack: Báo cáo là số đo thật của family, không ghi vào mô hình
        TransactionManager.Instance.ForceCloseTransaction()
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        try:
            for s in (small, large):
                if not s.IsActive:
                    s.Activate()
            doc.Regenerate()

            def finish(fi, ri, b, notes, elev, done, sym):
                if b.final is not None:
                    rows[ri][5] = u"{:.0f} × {:.0f}".format(b.final[1] - b.final[0], b.final[3] - b.final[2])
                    if b.hit is not None and not inside_room(b, b.hit[1]):
                        notes = notes + [u"lòi khỏi Room, cần soát"]
                rows[ri][6] = u"{:.0f}".format(elev)
                rows[ri][7] = label_of(sym)
                rows[ri][8] = done
                rows[ri][9] = fi.Id.Value
                rows[ri][10] = u"; ".join(v for v in [rows[ri][10]] + notes if v)

            def height_of(b):
                top = floor_top(floors, b.c)
                if top is None:
                    return lift, [u"không có sàn – cao độ {:.0f}, cần soát".format(lift)]
                return top + lift, []

            for fi, ri, b in fixes:
                sym = symbol_of(b)
                elev, note = height_of(b)
                todo, warn = settle(fi, b, sym, elev, flip)
                if todo:
                    changed += 1
                    finish(fi, ri, b, note + todo + warn, elev, u"Sẽ sửa" if dry_run else u"Đã sửa", sym)
                else:
                    finish(fi, ri, b, note + warn, elev, u"Bỏ qua – đã đúng (Id {})".format(fi.Id.Value), sym)
            # Family đặt theo level: Revit hiểu Z của điểm đặt là độ lệch so với level → Z = 0 rồi đặt Elevation from Level
            # (bài học tool lavabo 2026-10-30 10:16)
            for b, ri in jobs:
                sym = symbol_of(b)
                elev, note = height_of(b)
                q = b.world(0.0, b.mount_d)
                if sym.Family.FamilyPlacementType == FamilyPlacementType.WorkPlaneBased:
                    pt = XYZ(from_mm(q[0]), from_mm(q[1]), level.Elevation)
                    fi = doc.Create.NewFamilyInstance(level.GetPlaneReference(), pt, XYZ(1.0, 0.0, 0.0), sym)
                else:
                    pt = XYZ(from_mm(q[0]), from_mm(q[1]), 0.0)
                    fi = doc.Create.NewFamilyInstance(pt, sym, level, StructuralType.NonStructural)
                _, warn = settle(fi, b, sym, elev, flip)
                cm = fi.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
                if cm is not None and not cm.IsReadOnly:
                    cm.Set(COMMENT_TAG)
                finish(fi, ri, b, note + warn, elev, u"Sẽ tạo" if dry_run else u"Đã tạo", sym)
                if dry_run:
                    rows[ri][9] = u""
                created.append((fi, ri))
            if dry_run:
                tx.RollBack()
            else:
                status = tx.Commit()
                if status != TransactionStatus.Committed:
                    return [u"LỖI: Revit không lưu được Transaction ({}), mọi thay đổi đã được hoàn tác.".format(
                        status)], []
        except Exception as ex:
            if tx.HasStarted() and not tx.HasEnded():
                tx.RollBack()
            return [u"LỖI khi đặt giường, mọi thay đổi đã được hoàn tác: {}".format(ex)], []
        if not dry_run:
            for fi, ri in created:
                if not fi.IsValidObject:
                    rows[ri][8] = u"Revit đã xoá sau khi tạo"

    report = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (đã hoàn tác, không ghi vào mô hình)" if dry_run
                                else u"ĐÃ THỰC HIỆN")]
    report.append(u"CAD: {} – dò {} – {} nét – {} hình chữ nhật cỡ giường – level {} – phòng chứa: {}".format(
        cad_name, u"layer " + u"; ".join(sorted(layers)) if layer_filters else u"mọi layer ({})".format(len(layers)),
        len(items), stats.get("rects", 0), level.Name, u"; ".join(room_keys) if keys else u"mọi phòng"))
    n_small = sum(1 for b in beds if symbol_of(b).Id == small.Id)
    report.append(u"Giường: nhận diện {} – {}: {} – {}: {}{}".format(
        len(beds), label_of(small), n_small, label_of(large), len(beds) - n_small, u" – đảo hướng" if flip else u""))
    report.append(u"Giường {}: {}".format(u"sẽ tạo" if dry_run else u"đã tạo", len(jobs)))
    if fixes:
        report.append(u"Giường của tool {}: {} / {}".format(u"sẽ sửa" if dry_run else u"đã sửa", changed, len(fixes)))
    if stats.get("outside"):
        report.append(u"Cùng hình nhưng ngoài phòng lọc (bỏ qua): {}".format(stats["outside"]))
    if keys:
        have = set(b.number for b in beds)
        lack = sorted(r[3] for r in rooms if any(k in loose(r[2]) for k in keys) and r[3] not in have)
        report.append(u"Phòng lọc không có giường: {}".format(u", ".join(lack) or u"không"))
    dups = [(b, d) for b in beds for d in b.dups]
    if dups:
        report.append(u"TRÙNG: {} giường thừa cạnh nhau – xoá tay (giữ Id trong ngoặc): {}".format(
            len(dups), u", ".join(u"{} (giữ {})".format(d, b.eid) for b, d in dups)))
    soat = [r for r in rows if u"cần soát" in u"{}".format(r[10])]
    if soat:
        report.append(u"CẦN SOÁT: {} giường – xem cột Ghi chú".format(len(soat)))
    skip = sum(1 for r in rows if r[8].startswith(u"Bỏ qua – đã có"))
    if skip:
        report.append(u"Bỏ qua {} giường người dùng đã đặt cùng family".format(skip))
    report.append(u"Chẩn đoán: {} mặt tường – {} sàn – Room trên level: {}".format(len(walls), len(floors), len(rooms)))
    report.append(u"Đối tượng CAD theo loại: " + u", ".join(u"{} {}".format(k, v) for k, v in sorted(kinds.items())))
    try:
        report.append(u"Log: " + write_log(rows, cad_name, dry_run))
        if dry_run:
            report.append(u"Chẩn đoán nét CAD trong phòng: " + write_diag(cad, objects, room_at, keys))
    except Exception as ex:
        report.append(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        report.append(u"Kiểm tra hình CAD + khung sẽ đặt + đoạn hướng ra phòng (nét xanh trong Dynamo) và log. Đúng thì đổi "
                      u"Dry-run = False và Run lại. Undo bằng mục \"{}\".".format(TRANSACTION_NAME))
    else:
        report.append(u"Soát hướng trên mặt bằng: quay ngược → Undo mục \"{}\", IN[9] = True, Run lại.".format(TRANSACTION_NAME))
    report.append(u" | ".join(LOG_HEADER))
    report += [u" | ".join(u"{}".format(v) for v in r) for r in rows]
    return report, preview_lines([b for b, _ in jobs] + [f[2] for f in fixes], level_z)


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


def num(i, default):
    return float(IN[i]) if len(IN) > i and IN[i] is not None else default


if DYNAMO:
    import traceback
    try:
        OUT = list(main(
            (IN[0] or u"").strip(),
            [s.strip() for s in (u"A-Nội thất" if IN[1] is None else IN[1]).split(u";") if s.strip()],
            (IN[2] or u"TẦNG 3"),
            [IN[3] if IN[3] is not None else u"AV_FT_Giuong 1600x2000 : AV_FT_Giuong 1600x2000",
             IN[4] if IN[4] is not None else u"AV_FT_Giuong 1800x2000 : AV_FT_Giuong 1800x2000"],
            (u"phòng ngủ" if IN[5] is None else IN[5]).split(u";"),
            num(6, 100.0),
            num(7, 1.0),
            num(8, 1700.0),
            False if IN[9] is None else bool(IN[9]),
            True if IN[10] is None else bool(IN[10]),
        ))
    except StopReport as ex:
        OUT = [ex.lines, []]
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], []]
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with io.open(os.path.join(folder, "TaoGiuongTuCAD_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))), "w", encoding="utf-8-sig") as f:
                f.write(u"\n".join(OUT[0]))
        except Exception:
            pass
    note = force_rerun_next_time()
    if note:
        OUT[0].append(u"LƯU Ý: " + note)
