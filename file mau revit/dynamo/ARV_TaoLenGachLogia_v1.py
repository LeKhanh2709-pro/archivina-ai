# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong ARV_TaoLenGachLogia_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
# Nhân bản từ ARV_TaoLenGo_v1 (không sửa bản gốc) – thêm chia viên len trùng mạch lát sàn logia.
#
# Tạo len gạch chân tường logia (Basic Wall mỏng, type có sẵn "LCT-Gạch"), mỗi viên len một đoạn tường:
#   1. Nguồn biên: sàn hoàn thiện logia (Floor, VD do ARV_TaoSanCanHoTuCAD_v1 tạo – type "SHT-Gach Lat Logia-300x600",
#      Comments "ARV-SanCanHo CHxx LOGIA"). Phạm vi: phần tử đang chọn / Id ở IN[3]; không chọn gì → mọi sàn logia
#      trên level của view đang mở.
#   2. Kích thước viên: đọc Model pattern của vật liệu lớp mặt floor type (VD "300x600": lưới 0° cách 300,
#      lưới 90° cách 600). Không có pattern 2 lưới vuông góc → dừng.
#   3. Mạch lát sàn (đã đo trên G19 2026-10-21, 9 tấm sàn logia, khớp 100%): Revit đặt mẫu sàn với trục 0° của
#      pattern SONG SONG CẠNH DÀI NHẤT của biên sàn, mạch đi qua TÂM HỘP BAO của biên (theo hệ trục cạnh dài nhất).
#      → mạch dọc cạnh dài cách đều lưới 90° (600), mạch ngang cách đều lưới 0° (300). Sàn đã Align mẫu bằng tay
#      thì tool không biết – kiểm tra 3D sau khi tạo.
#   4. Mỗi cạnh biên: bắn tia vuông góc ra ngoài ở giữa chiều cao len, tìm mặt tường / cột Revit trong 60 mm →
#      len áp mặt tường (gồm cả gờ bê tông ARV-GoLogia mặt ngoài logia). Đoạn không có tường → không len.
#   5. Ngắt len tại cửa đi / cửa lùa: dải dọc tường bằng phủ bì khối cửa, bề ngang = dày tường + 60 mm mỗi bên.
#   6. Góc: hai đoạn len kề nhau gặp tại giao tim, kéo thêm nửa chiều dày (góc lồi không hở).
#   7. Chia mỗi đoạn len tại mạch lát sàn cắt ngang nó → mỗi viên một Basic Wall, không tự nối đầu (thấy mạch).
#      Viên vụn < IN[5] ở đầu đoạn (thường là phần kéo góc) gộp vào viên kề.
#   8. Tường len: không Room Bounding, mặt Exterior quay vào phòng, Comments "ARV-LenGachLogia <Id sàn>".
#      Sàn đã có len của tool → bỏ qua (xoá len cũ để làm lại).
#   Wall type phải có sẵn (template công ty) – tool không tạo / đổi type.
# INPUT
#   IN[0] (float) Chiều cao len (mm), mặc định 100
#   IN[1] (float) Chân len so với mặt sàn hoàn thiện (mm), mặc định 0
#   IN[2] (str)   Nhận sàn logia: chuỗi con trong Comments / tên type sàn, cách nhau ';' (mặc định "Logia")
#   IN[3] (str)   Id sàn, cách nhau ';' (trống = đang chọn trong Revit; không chọn = cả level của view)
#   IN[4] (str)   Wall type len (có sẵn), mặc định "LCT-Gạch"
#   IN[5] (float) Viên vụn tối thiểu (mm), mặc định 20 – viên ngắn hơn ở đầu đoạn gộp vào viên kề
#   IN[6] (bool)  Dry-run: True = chỉ báo cáo + xem trước, không ghi vào mô hình (mặc định True)
# OUTPUT
#   OUT[0] (list[str])  Báo cáo: tóm tắt, đường dẫn log, rồi từng viên len
#   OUT[1] (list[Line]) Xem trước: tim các viên len sẽ tạo (mm, tại cao độ chân len)

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
    from Autodesk.Revit.DB import (FilteredElementCollector, XYZ, Line, Transaction, UnitUtils, UnitTypeId,
                                   ModelPathUtils, BuiltInParameter, BuiltInCategory, Floor, Wall, WallType,
                                   WallUtils, Options, ViewDetailLevel, Solid, GeometryInstance, ElementId,
                                   SolidCurveIntersectionOptions, SolidCurveIntersectionMode, ViewType, Outline,
                                   BoundingBoxIntersectsFilter, ElementMulticategoryFilter, FillPatternTarget)
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    from System.Collections.Generic import List
    doc = DocumentManager.Instance.CurrentDBDocument
    uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument

TRANSACTION_NAME = u"ARV - Tạo len gạch logia"
SCRIPT_TAG = u"ARV_TaoLenGachLogia_v1"
COMMENT_TAG = u"ARV-LenGachLogia"
SKIRT_TAGS = (u"ARV-LenGachLogia", u"ARV-LenGo")   # len của các tool khác – không coi là tường chủ
STEP_MM = 100.0         # Bước dò dọc cạnh
END_MM = 2.0            # Điểm dò đầu / cuối cạnh lùi vào
RAY_BACK_MM = 20.0      # Tia bắt đầu lùi vào trong phòng
RAY_MM = 60.0           # Tầm dò mặt tường ra ngoài biên (sàn G19 áp mặt tường, khe 0)
D_TOL_MM = 5.0          # Chênh khe hở cùng một đoạn
BISECT = 9              # Số lần chia đôi tìm điểm đầu / cuối đoạn (100 / 2^9 ≈ 0,2 mm)
MIN_SEG_MM = 30.0       # Đoạn len ngắn hơn → bỏ
SEARCH_MM = 500.0       # Nới hộp bao tìm tường / cửa quanh sàn
DOOR_BAND_MM = 60.0     # Dải cửa: dày tường / 2 + giá trị này về mỗi phía tim tường
ANG_TOL = 1e-3          # Sai số hướng (cos) khi so cạnh với trục mẫu
TIE_MM = 1.0            # Hai cạnh dài nhất chênh ≤ giá trị này mà vuông góc nhau → cảnh báo hướng mẫu


# --- Hình học 2D thuần (mm) – chạy được ngoài Revit để thử --------------------------
def norm(s):
    return unicodedata.normalize("NFC", (s or u"")).strip()


def split_filters(text):
    return [s.strip() for s in (text or u"").split(u";") if s.strip()]


def matches(text, filters):
    t = norm(text).lower()
    return any(norm(f).lower() in t for f in filters)


def fmt_mm(v):
    return (u"{:.0f}" if abs(v - round(v)) < 1e-6 else u"{:.1f}").format(v)


def point_in(pt, pts):
    x, y = pt
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def point_in_evenodd(pt, loops):
    return sum(1 for l in loops if point_in(pt, l)) % 2 == 1


def line_intersect(p1, u1, p2, u2):
    """Giao hai đường p + t·u (2D). Song song → None."""
    den = u1[0] * u2[1] - u1[1] * u2[0]
    if abs(den) < 1e-6:
        return None
    t = ((p2[0] - p1[0]) * u2[1] - (p2[1] - p1[1]) * u2[0]) / den
    return (p1[0] + t * u1[0], p1[1] + t * u1[1])


def in_door_zone(x, y, zones):
    """zones: [(cx, cy, ux, uy, s_min, s_max, half_band)] – dải cửa dọc tim tường."""
    for cx, cy, ux, uy, s0, s1, hb in zones:
        dx, dy = x - cx, y - cy
        s = dx * ux + dy * uy
        if s0 <= s <= s1 and abs(-dx * uy + dy * ux) <= hb:
            return True
    return False


def find_runs(length, probe):
    """Các đoạn liên tục trên cạnh dài `length` (mm) mà probe(s) → (d, host) có mặt tường, khe d lệch ≤ D_TOL_MM.
    Trả về [dict(s0, s1, d, hosts, at_start, at_end)]."""
    n = max(1, int(math.ceil(length / STEP_MM)))
    ss = [min(max(i * length / n, END_MM), length - END_MM) for i in range(n + 1)]
    hits = [probe(s) for s in ss]

    def same(h, d):
        return h is not None and abs(h[0] - d) <= D_TOL_MM

    def edge_between(s_in, s_out, d):
        """Chia đôi giữa điểm thuộc đoạn (s_in) và điểm không thuộc (s_out)."""
        for _ in range(BISECT):
            m = (s_in + s_out) / 2.0
            if same(probe(m), d):
                s_in = m
            else:
                s_out = m
        return (s_in + s_out) / 2.0

    runs = []
    i = 0
    while i < len(ss):
        if hits[i] is None:
            i += 1
            continue
        j = i
        ds = [hits[i][0]]
        hosts = set([hits[i][1]])
        while j + 1 < len(ss) and same(hits[j + 1], hits[j][0]):
            j += 1
            ds.append(hits[j][0])
            hosts.add(hits[j][1])
        ds.sort()
        d = ds[len(ds) // 2]
        s0 = 0.0 if i == 0 else edge_between(ss[i], ss[i - 1], d)
        s1 = length if j == len(ss) - 1 else edge_between(ss[j], ss[j + 1], d)
        runs.append(dict(s0=s0, s1=s1, d=d, hosts=hosts, at_start=(i == 0), at_end=(j == len(ss) - 1)))
        i = j + 1
    return runs


def plan_loop(edges, interior_loops, probe_for_edge, thickness):
    """edges: [(a, b)] mm của một vòng biên (theo thứ tự). Trả về các đoạn len:
    [dict(edge, p0, p1, d, hosts, length)] – p0/p1 là tim len (mm)."""
    t2 = thickness / 2.0
    infos = []
    for k, (a, b) in enumerate(edges):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 1.0:
            infos.append(None)
            continue
        u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        n = (u[1], -u[0])     # bên phải
        mid = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        if point_in_evenodd((mid[0] + n[0] * 20.0, mid[1] + n[1] * 20.0), interior_loops):
            n = (-n[0], -n[1])
        runs = find_runs(L, probe_for_edge(a, u, n))
        segs = []
        for r in runs:
            c = r["d"] - t2           # tim len cách cạnh biên (ra ngoài)
            base = (a[0] + n[0] * c, a[1] + n[1] * c)
            segs.append(dict(edge=k, u=u, n=n, base=base, s0=r["s0"], s1=r["s1"], d=r["d"], hosts=r["hosts"],
                             at_start=r["at_start"], at_end=r["at_end"], raw=r["s1"] - r["s0"]))
        infos.append(segs)

    # Góc: đoạn cuối cạnh k + đoạn đầu cạnh k+1 đều chạm đỉnh → gặp tại giao tim, kéo thêm nửa chiều dày
    m = len(edges)
    for k in range(m):
        cur, nxt = infos[k], infos[(k + 1) % m]
        if not cur or not nxt or not cur[-1]["at_end"] or not nxt[0]["at_start"]:
            continue
        s1, s2 = cur[-1], nxt[0]
        p = line_intersect(s1["base"], s1["u"], s2["base"], s2["u"])
        if p is None:
            continue
        s1["s1"] = (p[0] - s1["base"][0]) * s1["u"][0] + (p[1] - s1["base"][1]) * s1["u"][1] + t2
        s2["s0"] = (p[0] - s2["base"][0]) * s2["u"][0] + (p[1] - s2["base"][1]) * s2["u"][1] - t2

    out = []
    for segs in infos:
        for s in segs or []:
            if s["s1"] - s["s0"] < MIN_SEG_MM:
                continue
            bx, by = s["base"]
            ux, uy = s["u"]
            s["p0"] = (bx + ux * s["s0"], by + uy * s["s0"])
            s["p1"] = (bx + ux * s["s1"], by + uy * s["s1"])
            s["length"] = s["s1"] - s["s0"]
            out.append(s)
    return out


# --- Lưới mạch lát sàn ----------------------------------------------------------------
def tile_frame(loops):
    """Hệ trục mẫu sàn theo quy luật Revit: e1 = hướng cạnh dài nhất, tâm = tâm hộp bao theo (e1, e2).
    Trả về (e1, e2, c1, c2, cảnh báo | None)."""
    edges = [(a, b, math.hypot(b[0] - a[0], b[1] - a[1])) for loop in loops for a, b in loop]
    a, b, L = max(edges, key=lambda e: e[2])
    e1 = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    e2 = (-e1[1], e1[0])
    warn = None
    for a2, b2, L2 in edges:
        if L - L2 <= TIE_MM and abs((b2[0] - a2[0]) * e1[0] + (b2[1] - a2[1]) * e1[1]) / L2 < ANG_TOL:
            warn = (u"hai cạnh dài nhất ({:.0f} mm) vuông góc nhau – không chắc hướng mẫu Revit chọn, "
                    u"kiểm tra mạch 3D".format(L))
            break
    pts = [p for loop in loops for e in loop for p in e]
    s1 = [p[0] * e1[0] + p[1] * e1[1] for p in pts]
    s2 = [p[0] * e2[0] + p[1] * e2[1] for p in pts]
    return e1, e2, (min(s1) + max(s1)) / 2.0, (min(s2) + max(s2)) / 2.0, warn


def joint_axis(u, grid):
    """Trục mạch cắt ngang đoạn hướng u: (e, gốc, bước) hoặc None nếu đoạn xiên so với mẫu.
    grid = dict(e1, e2, c1, c2, along, across, o_along, o_across)."""
    d1 = u[0] * grid["e1"][0] + u[1] * grid["e1"][1]
    if abs(abs(d1) - 1.0) < ANG_TOL:
        return grid["e1"], grid["c1"] + grid["o_along"], grid["along"]
    d2 = u[0] * grid["e2"][0] + u[1] * grid["e2"][1]
    if abs(abs(d2) - 1.0) < ANG_TOL:
        return grid["e2"], grid["c2"] + grid["o_across"], grid["across"]
    return None


def split_at_joints(seg, grid, min_piece):
    """Chia đoạn len tại các mạch sàn cắt ngang nó. Trả về (các viên [dict(p0, p1, length)], số viên vụn đã gộp,
    xiên?)."""
    ax = joint_axis(seg["u"], grid)
    L = seg["length"]
    p0 = seg["p0"]
    ux, uy = seg["u"]
    if ax is None:
        return [dict(p0=seg["p0"], p1=seg["p1"], length=L)], 0, True
    e, origin, step = ax
    sa = p0[0] * e[0] + p0[1] * e[1]
    sgn = ux * e[0] + uy * e[1]        # ±1: chiều đoạn so với trục
    lo, hi = sorted((sa, sa + sgn * L))
    k0 = int(math.ceil((lo - origin) / step - 1e-9))
    cuts = []
    k = k0
    while True:
        j = origin + k * step
        if j >= hi - 1e-6:
            break
        if j > lo + 1e-6:
            cuts.append((j - sa) * sgn)   # vị trí cắt tính từ p0 theo chiều đoạn
        k += 1
    cuts.sort()
    merged = 0
    # Viên vụn ở hai đầu đoạn (thường do kéo góc nửa chiều dày len) → bỏ mạch cắt, gộp vào viên kề
    while cuts and cuts[0] < min_piece:
        cuts.pop(0)
        merged += 1
    while cuts and L - cuts[-1] < min_piece:
        cuts.pop()
        merged += 1
    ts = [0.0] + cuts + [L]
    pieces = []
    for i in range(len(ts) - 1):
        a, b = ts[i], ts[i + 1]
        pieces.append(dict(p0=(p0[0] + ux * a, p0[1] + uy * a), p1=(p0[0] + ux * b, p0[1] + uy * b), length=b - a))
    return pieces, merged, False


# =====================================================================================
# PHẦN REVIT
# =====================================================================================
class StopReport(Exception):
    def __init__(self, lines):
        Exception.__init__(self, lines[0])
        self.lines = lines


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


def type_name(t):
    p = t.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
    return p.AsString() if p else get_name(t)


def id_value(eid):
    v = getattr(eid, "Value", None)
    return v if v is not None else eid.IntegerValue


def comments(el):
    p = el.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    return (p.AsString() or u"") if p else u""


def is_central_file(document):
    if not document.IsWorkshared:
        return False
    try:
        central = ModelPathUtils.ConvertModelPathToUserVisiblePath(document.GetWorksharingCentralModelPath())
    except Exception:
        return False
    return os.path.normcase(central or "") == os.path.normcase(document.PathName or "")


# --- Mẫu gạch của floor type --------------------------------------------------------
def tile_pattern(ftype):
    """Model pattern lớp mặt của floor type → dict(along, across, o_along, o_across, name) mm, hoặc None.
    along = bước lưới 90° (mạch vuông góc cạnh dài nhất), across = bước lưới 0°."""
    cs = ftype.GetCompoundStructure()
    if cs is None:
        return None
    for i in range(cs.LayerCount):
        mat = doc.GetElement(cs.GetMaterialId(i))
        fpe = doc.GetElement(mat.SurfaceForegroundPatternId) if mat is not None else None
        if fpe is None:
            continue
        fp = fpe.GetFillPattern()
        if fp.Target != FillPatternTarget.Model or fp.GridCount != 2:
            continue
        g0, g90 = None, None
        for g in fp.GetFillGrids():
            ang = math.degrees(g.Angle) % 180.0
            if min(ang, 180.0 - ang) < 0.1:
                g0 = g
            elif abs(ang - 90.0) < 0.1:
                g90 = g
        if g0 is None or g90 is None:
            continue
        return dict(along=to_mm(g90.Offset), across=to_mm(g0.Offset), o_along=to_mm(g90.Origin.U),
                    o_across=to_mm(g0.Origin.V), name=get_name(fpe), mat=get_name(mat))
    return None


# --- Nguồn biên: sàn logia -----------------------------------------------------------
class Source(object):
    def __init__(self, el, level, base_ft, loops_mm, label):
        self.el = el
        self.level = level
        self.base = base_ft       # cao độ tuyệt đối mặt sàn hoàn thiện (feet)
        self.loops = loops_mm     # [[(a, b)]] cạnh thẳng theo thứ tự, mm
        self.label = label
        self.warn = []
        self.segs = []
        self.pieces = []
        self.grid = None
        self.status = u""
        self.door_mm = 0.0
        self.merged = 0


def floor_source(fl):
    level = doc.GetElement(fl.LevelId)
    sk = doc.GetElement(fl.SketchId) if hasattr(fl, "SketchId") else None
    if sk is None or level is None:
        return None
    off = fl.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM)
    base = level.Elevation + (off.AsDouble() if off else 0.0)
    loops, warn = [], []
    for ca in sk.Profile:
        edges = []
        for c in ca:
            if not isinstance(c, Line):
                warn.append(u"cạnh cong bỏ qua")
                continue
            a, b = c.GetEndPoint(0), c.GetEndPoint(1)
            edges.append(((to_mm(a.X), to_mm(a.Y)), (to_mm(b.X), to_mm(b.Y))))
        if edges:
            loops.append(edges)
    s = Source(fl, level, base, loops, u"{} | {}".format(comments(fl) or u"—", type_name(doc.GetElement(fl.GetTypeId()))))
    s.warn = warn
    return s


def is_logia_floor(fl, filters):
    return matches(comments(fl), filters) or matches(type_name(doc.GetElement(fl.GetTypeId())), filters)


def collect_sources(id_text, filters):
    """Trả về (danh sách Source, mô tả phạm vi)."""
    if id_text:
        elems = [doc.GetElement(ElementId(int(s))) for s in id_text.replace(u",", u";").split(u";") if s.strip()]
        how = u"Id nhập ở IN[3]"
    else:
        elems = [doc.GetElement(i) for i in uidoc.Selection.GetElementIds()]
        how = u"phần tử đang chọn"
    elems = [e for e in elems if isinstance(e, Floor) and is_logia_floor(e, filters)]
    if not elems:
        view = doc.ActiveView
        level = view.GenLevel if view.ViewType in (ViewType.FloorPlan, ViewType.CeilingPlan) else None
        if level is None:
            raise StopReport([u"DỪNG: chưa chọn sàn logia. Chọn sàn logia rồi Run, hoặc mở view mặt bằng của "
                              u"tầng để làm mọi sàn logia trên tầng đó."])
        elems = [f for f in FilteredElementCollector(doc).OfClass(Floor).ToElements()
                 if f.LevelId == level.Id and is_logia_floor(f, filters)]
        how = u"mọi sàn logia trên {}".format(level.Name)
    sources = []
    for e in elems:
        s = floor_source(e)
        if s is not None and s.loops:
            sources.append(s)
    return sources, how


# --- Dò mặt tường, cửa ---------------------------------------------------------------
def element_solids(element):
    opt = Options()
    opt.DetailLevel = ViewDetailLevel.Fine
    result = []

    def walk(geo):
        for g in geo:
            if isinstance(g, Solid) and g.Volume > 0:
                result.append(g)
            elif isinstance(g, GeometryInstance):
                walk(g.GetInstanceGeometry())

    geo = element.get_Geometry(opt)
    if geo is not None:
        walk(geo)
    return result


def nearby(src, top, cats):
    pts = [p for loop in src.loops for e in loop for p in e]
    pad = SEARCH_MM
    mn = XYZ(from_mm(min(p[0] for p in pts) - pad), from_mm(min(p[1] for p in pts) - pad), src.base - from_mm(pad))
    mx = XYZ(from_mm(max(p[0] for p in pts) + pad), from_mm(max(p[1] for p in pts) + pad), top)
    return FilteredElementCollector(doc).WherePasses(ElementMulticategoryFilter(List[BuiltInCategory](cats))) \
        .WherePasses(BoundingBoxIntersectsFilter(Outline(mn, mx))).WhereElementIsNotElementType().ToElements()


def is_skirting(el, wtype):
    c = comments(el)
    return any(c.startswith(t) for t in SKIRT_TAGS) or (isinstance(el, Wall) and el.GetTypeId() == wtype.Id)


def obstacle_solids(src, top, wtype):
    """Khối tường + cột quanh sàn (trừ len): [(solid, element)]."""
    out = []
    for el in nearby(src, top, [BuiltInCategory.OST_Walls, BuiltInCategory.OST_StructuralColumns,
                                BuiltInCategory.OST_Columns]):
        if is_skirting(el, wtype):
            continue
        for s in element_solids(el):
            out.append((s, el))
    return out


def door_zones(src, top):
    """Dải cửa đi quanh sàn: (cx, cy, ux, uy, s_min, s_max, half_band) mm – phủ bì khối cửa dọc tim tường chủ."""
    zones = []
    for d in nearby(src, top, [BuiltInCategory.OST_Doors]):
        host = getattr(d, "Host", None)
        if not isinstance(host, Wall) or d.Location is None:
            continue
        lc = getattr(host.Location, "Curve", None)
        lp = getattr(d.Location, "Point", None)
        if not isinstance(lc, Line) or lp is None:
            continue
        u = lc.Direction
        L = math.hypot(u.X, u.Y)
        if L < 1e-9:
            continue
        ux, uy = u.X / L, u.Y / L
        cx, cy = to_mm(lp.X), to_mm(lp.Y)
        s_min, s_max = None, None
        for solid in element_solids(d):
            for e in solid.Edges:
                for p in e.Tessellate():
                    s = (to_mm(p.X) - cx) * ux + (to_mm(p.Y) - cy) * uy
                    s_min = s if s_min is None else min(s_min, s)
                    s_max = s if s_max is None else max(s_max, s)
        if s_min is None:
            w = d.Symbol.get_Parameter(BuiltInParameter.DOOR_WIDTH) or d.get_Parameter(BuiltInParameter.DOOR_WIDTH)
            hw = to_mm(w.AsDouble()) / 2.0 if w else 0.0
            s_min, s_max = -hw, hw
        # gốc dải = chân vuông góc của điểm chèn cửa trên tim tường chủ (dải ngang đo từ tim tường)
        p0 = lc.GetEndPoint(0)
        t = (cx - to_mm(p0.X)) * ux + (cy - to_mm(p0.Y)) * uy
        ox, oy = to_mm(p0.X) + ux * t, to_mm(p0.Y) + uy * t
        zones.append((ox, oy, ux, uy, s_min, s_max, to_mm(host.Width) / 2.0 + DOOR_BAND_MM))
    return zones


SCI_OPT = None


def first_hit(solids, a, b):
    """Khoảng cách (feet, từ a) tới khối đầu tiên trên đoạn a→b và phần tử; None nếu không gặp / a nằm trong khối."""
    global SCI_OPT
    if SCI_OPT is None:
        SCI_OPT = SolidCurveIntersectionOptions()
        SCI_OPT.ResultType = SolidCurveIntersectionMode.CurveSegmentsInside
    line = Line.CreateBound(a, b)
    best, host = None, None
    for s, el in solids:
        try:
            res = s.IntersectWithCurve(line, SCI_OPT)
        except Exception:
            continue
        for i in range(res.SegmentCount):
            c = res.GetCurveSegment(i)
            t = min(c.GetEndPoint(0).DistanceTo(a), c.GetEndPoint(1).DistanceTo(a))
            if best is None or t < best:
                best, host = t, el
    if best is None or best < from_mm(0.5):
        return None
    return best, host


def make_probe(solids, z, zones):
    def probe_for_edge(a, u, n):
        def probe(s):
            x, y = a[0] + u[0] * s, a[1] + u[1] * s
            if in_door_zone(x, y, zones):
                return None
            p0 = XYZ(from_mm(x - n[0] * RAY_BACK_MM), from_mm(y - n[1] * RAY_BACK_MM), z)
            p1 = XYZ(from_mm(x + n[0] * RAY_MM), from_mm(y + n[1] * RAY_MM), z)
            h = first_hit(solids, p0, p1)
            return None if h is None else (to_mm(h[0]) - RAY_BACK_MM, id_value(h[1].Id))
        return probe
    return probe_for_edge


def door_length(loop, zones):
    """Chiều dài biên (mm) rơi vào dải cửa – chỉ để báo cáo."""
    door = 0.0
    for a, b in loop:
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 1.0:
            continue
        u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        k = max(1, int(L / 10.0))
        for i in range(k):
            s = (i + 0.5) * L / k
            if in_door_zone(a[0] + u[0] * s, a[1] + u[1] * s, zones):
                door += L / k
    return door


# --- Tạo len -------------------------------------------------------------------------
def existing_skirting():
    tags = {}
    for w in FilteredElementCollector(doc).OfClass(Wall).ToElements():
        c = comments(w)
        if c.startswith(COMMENT_TAG + u" "):
            tags.setdefault(c[len(COMMENT_TAG) + 1:].strip(), []).append(id_value(w.Id))
    return tags


def create_piece(src, pc, wtype, height_ft, offset_ft):
    z = src.level.Elevation
    p0 = XYZ(from_mm(pc["p0"][0]), from_mm(pc["p0"][1]), z)
    p1 = XYZ(from_mm(pc["p1"][0]), from_mm(pc["p1"][1]), z)
    w = Wall.Create(doc, Line.CreateBound(p0, p1), wtype.Id, src.level.Id, height_ft, offset_ft, False, False)
    rb = w.get_Parameter(BuiltInParameter.WALL_ATTR_ROOM_BOUNDING)
    if rb is not None and not rb.IsReadOnly:
        rb.Set(0)
    cm = w.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    if cm is not None and not cm.IsReadOnly:
        cm.Set(u"{} {}".format(COMMENT_TAG, id_value(src.el.Id)))
    WallUtils.DisallowWallJoinAtEnd(w, 0)
    WallUtils.DisallowWallJoinAtEnd(w, 1)
    return w


def face_room(w, n):
    """Mặt ngoài (Exterior) của len quay vào phòng."""
    o = w.Orientation
    if o.X * n[0] + o.Y * n[1] > 0:
        w.Flip()


def preview_lines(sources, extra_z_ft):
    try:
        clr.AddReference("ProtoGeometry")
        from Autodesk.DesignScript.Geometry import Point as DSPoint, Line as DSLine
        out = []
        for src in sources:
            z = to_mm(src.base + extra_z_ft)
            for pc in src.pieces:
                out.append(DSLine.ByStartPointEndPoint(DSPoint.ByCoordinates(pc["p0"][0], pc["p0"][1], z),
                                                       DSPoint.ByCoordinates(pc["p1"][0], pc["p1"][1], z)))
        return out
    except Exception:
        return []


HEADER = [u"Id sàn", u"Mô tả", u"Đoạn", u"Viên", u"Dài viên (mm)", u"Khe tới mặt tường (mm)", u"Tường / cột chủ",
          u"Kết quả", u"ElementId"]


def write_log(rows, dry_run, settings):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoLenGachLogia_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(u"# Dự án: {}\n".format(doc.Title))
        f.write(u"# Ngày xuất: {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write(u"# Chế độ: {}\n".format(u"Chạy thử (dry-run)" if dry_run else u"Thực hiện"))
        f.write(u"# Thiết lập: {}\n".format(settings))
        f.write(u"# Đơn vị: mm\n")
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(rows)
    return path


def main(height_mm, base_mm, filters, id_text, wtype_name, min_piece, dry_run):
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."], []
    if height_mm <= 0:
        raise StopReport([u"DỪNG: chiều cao len IN[0] phải > 0."])

    types = dict((norm(type_name(t)), t) for t in FilteredElementCollector(doc).OfClass(WallType).ToElements())
    wtype = types.get(norm(wtype_name))
    if wtype is None:
        raise StopReport([u"DỪNG: không có wall type '{}' (IN[4]) – tool không tạo type mới. Các type len có sẵn: {}"
                          .format(wtype_name, u", ".join(sorted(k for k in types if k.upper().startswith(u"LCT")))
                                  or u"không có")])
    thickness = to_mm(wtype.Width)
    if thickness <= 0 or thickness > 40:
        raise StopReport([u"DỪNG: type '{}' dày {:.1f} mm – không phải len.".format(wtype_name, thickness)])

    sources, how = collect_sources(id_text, filters)
    if not sources:
        raise StopReport([u"DỪNG: không tìm thấy sàn logia ({}; lọc '{}').".format(how, u";".join(filters))])

    done = existing_skirting()
    height_ft, base_ft = from_mm(height_mm), from_mm(base_mm)
    patterns = {}
    for src in sources:
        key = str(id_value(src.el.Id))
        if key in done:
            src.status = u"Bỏ qua: đã có {} viên len (Id {}) – xoá để làm lại".format(
                len(done[key]), u", ".join(str(i) for i in done[key][:5]))
            continue
        ftype = doc.GetElement(src.el.GetTypeId())
        tid = id_value(ftype.Id)
        if tid not in patterns:
            patterns[tid] = tile_pattern(ftype)
        pat = patterns[tid]
        if pat is None:
            src.status = u"Bỏ qua: floor type '{}' không có Model pattern 2 lưới vuông góc ở lớp mặt".format(
                type_name(ftype))
            continue
        e1, e2, c1, c2, tie = tile_frame(src.loops)
        if tie:
            src.warn.append(tie)
        if abs(pat["o_along"]) > 0.01 or abs(pat["o_across"]) > 0.01:
            src.warn.append(u"pattern '{}' có gốc lưới lệch ({:.1f}; {:.1f}) – quy luật mạch chỉ đo với gốc 0, "
                            u"kiểm tra 3D".format(pat["name"], pat["o_along"], pat["o_across"]))
        src.grid = dict(e1=e1, e2=e2, c1=c1, c2=c2, along=pat["along"], across=pat["across"],
                        o_along=pat["o_along"], o_across=pat["o_across"], name=pat["name"])
        bottom = src.base + base_ft
        top = bottom + height_ft
        solids = obstacle_solids(src, top, wtype)
        zones = door_zones(src, top)
        probe = make_probe(solids, bottom + height_ft / 2.0, zones)
        interior = [[e[0] for e in loop] for loop in src.loops]
        for loop in src.loops:
            src.segs += plan_loop(loop, interior, probe, thickness)
            src.door_mm += door_length(loop, zones)
        slanted = 0
        for k, seg in enumerate(src.segs, 1):
            pieces, merged, slant = split_at_joints(seg, src.grid, min_piece)
            src.merged += merged
            slanted += 1 if slant else 0
            for j, pc in enumerate(pieces, 1):
                pc.update(seg=k, no=j, n=seg["n"], d=seg["d"], hosts=seg["hosts"])
                src.pieces.append(pc)
        if slanted:
            src.warn.append(u"{} đoạn len xiên so với mẫu sàn – không chia mạch".format(slanted))
        if not src.segs:
            src.status = u"Không tìm thấy mặt tường quanh biên"
        perim = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for loop in src.loops for a, b in loop)
        bare = perim - sum(s["raw"] for s in src.segs) - src.door_mm
        if bare > 100.0:
            src.warn.append(u"{:.2f} m biên không có tường / cột trong {:.0f} mm (lối mở, thiếu tường / gờ?) "
                            u"– không len".format(bare / 1000.0, RAY_MM))

    jobs = [s for s in sources if s.pieces and not s.status]
    if not dry_run and jobs:
        TransactionManager.Instance.ForceCloseTransaction()
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        try:
            created = []
            for src in jobs:
                offset = (src.base - src.level.Elevation) + base_ft
                for pc in src.pieces:
                    w = create_piece(src, pc, wtype, height_ft, offset)
                    pc["id"] = id_value(w.Id)
                    created.append((w, pc))
                src.status = u"Đã tạo"
            doc.Regenerate()
            for w, pc in created:
                face_room(w, pc["n"])
            tx.Commit()
        except Exception as ex:
            tx.RollBack()
            return [u"LỖI khi tạo len, mọi thay đổi đã được hoàn tác: {}".format(ex)], []

    # Báo cáo
    rows = []
    total_len, nseg, npc, door_len, merged = 0.0, 0, 0, 0.0, 0
    for src in sources:
        door_len += src.door_mm
        merged += src.merged
        nseg += len(src.segs)
        if not src.pieces:
            rows.append([id_value(src.el.Id), src.label, u"—", u"", u"", u"", u"", src.status, u""])
            continue
        for pc in src.pieces:
            total_len += pc["length"]
            npc += 1
            rows.append([id_value(src.el.Id), src.label, pc["seg"], pc["no"], u"{:.0f}".format(pc["length"]),
                         u"{:.1f}".format(pc["d"]), u", ".join(str(h) for h in sorted(pc["hosts"])),
                         src.status or (u"Sẽ tạo" if dry_run else u""), pc.get("id", u"")])
    report = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN")]
    report.append(u"Phạm vi: {} – {} sàn logia ({} đã có len, bỏ qua)".format(
        how, len(sources), sum(1 for s in sources if s.status.startswith(u"Bỏ qua: đã có"))))
    report.append(u"Wall type '{}' dày {:.0f} mm – cao {} mm, chân len = mặt sàn logia {:+.0f} mm".format(
        type_name(wtype), thickness, fmt_mm(height_mm), base_mm))
    for tid, pat in patterns.items():
        if pat is not None:
            report.append(u"Mẫu gạch '{}' ({}): mạch cách {} dọc cạnh dài nhất sàn, {} ngang – qua tâm hộp bao sàn".format(
                pat["name"], pat["mat"], fmt_mm(pat["along"]), fmt_mm(pat["across"])))
    report.append(u"Len {}: {} đoạn → {} viên – tổng dài {:.2f} m. Viên vụn < {} mm gộp vào viên kề: {}".format(
        u"sẽ tạo" if dry_run else u"đã tạo", nseg, npc, total_len / 1000.0, fmt_mm(min_piece), merged))
    report.append(u"Ngắt tại cửa đi / cửa lùa: {:.2f} m biên".format(door_len / 1000.0))
    for src in sources:
        if src.status.startswith(u"Bỏ qua: floor"):
            report.append(u"CẢNH BÁO sàn {} ({}): {}".format(id_value(src.el.Id), src.label, src.status))
        for w in sorted(set(src.warn)):
            report.append(u"CẢNH BÁO sàn {} ({}): {}".format(id_value(src.el.Id), src.label, w))
    settings = u"type {}, cao {}, chân {}, lọc sàn {}, viên vụn {}".format(
        type_name(wtype), fmt_mm(height_mm), fmt_mm(base_mm), u";".join(filters), fmt_mm(min_piece))
    try:
        report.append(u"Log: " + write_log(rows, dry_run, settings))
    except Exception as ex:
        report.append(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        report.append(u"Kiểm tra tim len (OUT[1]) + log. Đúng thì đổi Dry-run = False và Run lại. "
                      u"Undo bằng mục \"{}\".".format(TRANSACTION_NAME))
    report.append(u" | ".join(HEADER))
    report += [u" | ".join(u"{}".format(v) for v in r) for r in rows]
    return report, preview_lines(sources, base_ft)


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

    def _num(v, default):
        try:
            return float(v) if v is not None and u"{}".format(v).strip() != u"" else default
        except Exception:
            return default

    try:
        OUT = list(main(
            _num(IN[0], 100.0),
            _num(IN[1], 0.0),
            split_filters(IN[2] or u"Logia"),
            (IN[3] or u"").strip(),
            (IN[4] or u"LCT-Gạch").strip(),
            _num(IN[5], 20.0),
            True if IN[6] is None else bool(IN[6]),
        ))
    except StopReport as ex:
        OUT = [ex.lines, []]
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], []]
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with io.open(os.path.join(folder, "TaoLenGachLogia_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))), "w", encoding="utf-8-sig") as f:
                f.write(u"\n".join(OUT[0]))
        except Exception:
            pass
    note = force_rerun_next_time()
    if note:
        OUT[0].append(u"LƯU Ý: " + note)
