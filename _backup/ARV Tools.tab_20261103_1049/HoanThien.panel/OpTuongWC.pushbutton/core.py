# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong ARV_OpTuongWC_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Tạo lớp ốp gạch tường WC (Basic Wall mỏng, type "GO-Gạch ốp-…") cao IN[2] tính từ mặt sàn hoàn thiện WC:
#   1. Nguồn biên WC: sàn hoàn thiện WC (Floor, VD do ARV_TaoSanCanHoTuCAD_v1 tạo – Comments "ARV-SanCanHo CHxx WC")
#      hoặc Room tên WC / vệ sinh (biên "At wall finish"). Phạm vi: phần tử đang chọn / Id ở IN[5]; không chọn gì
#      → mọi WC trên level của view đang mở (ưu tiên sàn; không có sàn WC mới lấy Room).
#   2. Mỗi cạnh biên: bắn tia vuông góc ra phía ngoài (ở cao 300 trên chân ốp và sát đỉnh ốp) tìm mặt tường /
#      cột Revit → khoảng hở d (sàn WC lùi 10 mm so với mặt tường; Room = 0). Lớp ốp: mặt ngoài áp mặt tường, dày
#      bằng type. Đoạn không có tường ở cả hai cao độ (lối mở, hộp kỹ thuật hở) → không ốp. Ô cửa (có lanh tô) ốp
#      liền rồi nối khối (Join) với tường chủ → cửa đi / cửa sổ tự cắt lớp ốp (đã kiểm: cửa 830 cắt 1,87 m²).
#   3. Góc: hai lớp ốp kề nhau gặp nhau tại giao tim, kéo thêm nửa chiều dày (không hở góc lồi / cột).
#   4. Wall type theo kích thước gạch IN[0] + hướng IN[1]: "GO-Gạch ốp-{nhỏ}x{lớn}" (+ "-dọc"). Chưa có → nhân bản
#      type mẫu IN[6], vật liệu "Gạch Ceramic {nhỏ}x{lớn}mm" (+ " dọc") với mẫu Model pattern đúng ô gạch
#      (lưới ngang cách = cao viên, lưới đứng cách = rộng viên; dùng lại pattern có sẵn nếu trùng lưới).
#   5. Tường ốp: không Room Bounding, không tự nối đầu (DisallowWallJoinAtEnd), Comments "ARV-OpTuongWC <Id nguồn>".
#      WC đã có ốp của tool (tường ốp nằm trong biên WC, không phụ thuộc Id sàn – sàn dựng lại đổi Id) → bỏ qua,
#      hoặc xoá ốp cũ rồi dựng lại khi IN[10] = True (chỉ xoá tường có Comments "ARV-OpTuongWC…").
#   6. Căn mạch theo lát sàn (IN[9], thêm 2026-10-21) – đã đo trên G19:
#      - Mạch ĐỨNG của mẫu gạch trên tường bắt đầu từ ĐIỂM ĐẦU đường định vị tường (dời điểm đầu → mạch dời theo,
#        Flip không đổi). Vị trí mạch sàn đo trực tiếp trên mặt sàn WC (Dimension tới đường mạch của Model pattern trên
#        view mặt bằng tạm, rồi hoàn tác) → mỗi đoạn ốp tách đôi tại một mạch sàn, hai nửa cùng bắt đầu từ điểm đó →
#        mạch đứng ốp nối tiếp mạch sàn (bước gạch tường / sàn là bội của nhau thì mọi mạch sàn đều có mạch tường).
#      - Mạch NGANG bắt đầu từ cốt LEVEL chân tường (không theo Base Offset). Sàn WC −15 → dùng Model pattern có gốc
#        lưới ngang dời −15 (Origin V) để hàng gạch đầu tiên bắt đầu từ mặt sàn: type "GO-Gạch ốp-300x600 (mạch -15)".
#      Nguồn là Room (không có sàn) → không căn được mạch đứng, báo cáo.
# INPUT
#   IN[0] (str)   Kích thước gạch ốp (mm), VD "300x600", "300x300", "600x600", "400x800"
#   IN[1] (str)   Hướng lát: "NGANG" (cạnh dài nằm ngang) / "DOC" (cạnh dài đứng); gạch vuông bỏ qua
#   IN[2] (float) Chiều cao ốp (mm), mặc định 2400
#   IN[3] (float) Chân ốp so với mặt sàn hoàn thiện WC (mm), mặc định 0
#   IN[4] (str)   Nhận WC: chuỗi con trong Comments / tên type sàn / tên phòng, cách nhau ';' (mặc định "WC;vệ sinh")
#   IN[5] (str)   Id sàn / phòng WC, cách nhau ';' (trống = đang chọn trong Revit; không chọn = cả level của view)
#   IN[6] (str)   Wall type ốp mẫu để nhân bản (mặc định "GO-Gạch ốp-300x600")
#   IN[7] (bool)  Nối khối lớp ốp với tường chủ để cửa đi / cửa sổ cắt lớp ốp (mặc định True)
#   IN[8] (bool)  Dry-run: True = chỉ báo cáo + xem trước, không ghi vào mô hình (mặc định True)
#   IN[9] (bool)  Căn mạch ốp trùng mạch lát sàn (mạch đứng + hàng gạch đầu từ mặt sàn) (mặc định True)
#   IN[10] (bool) Xoá ốp cũ của tool trong các WC được chọn rồi dựng lại (mặc định False = bỏ qua WC đã có ốp)
# OUTPUT
#   OUT[0] (list[str])  Báo cáo: tóm tắt, đường dẫn log, rồi từng đoạn ốp
#   OUT[1] (list[Line]) Xem trước: tim các đoạn ốp sẽ tạo (mm, tại cao độ chân ốp)

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
    from Autodesk.Revit.DB import (FilteredElementCollector, XYZ, UV, Line, Transaction, UnitUtils, UnitTypeId,
                                   ModelPathUtils, BuiltInParameter, BuiltInCategory, Floor, Wall, WallType,
                                   WallUtils, JoinGeometryUtils, Options, ViewDetailLevel, Solid, GeometryInstance,
                                   ElementId, SolidCurveIntersectionOptions, SolidCurveIntersectionMode, ViewType,
                                   Material, FillPattern, FillPatternElement, FillPatternTarget, FillGrid,
                                   FillPatternHostOrientation, Outline, BoundingBoxIntersectsFilter,
                                   ElementMulticategoryFilter, SpatialElementBoundaryOptions,
                                   SpatialElementBoundaryLocation, FamilyInstance, HostObjectUtils, ViewPlan,
                                   ViewFamilyType, ViewFamily, ReferenceArray, Reference, SubTransaction,
                                   LocationCurve)
    from Autodesk.Revit.DB.Architecture import Room
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    from System.Collections.Generic import List
    doc = DocumentManager.Instance.CurrentDBDocument
    uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument

TRANSACTION_NAME = u"ARV - Tạo ốp tường WC"
SCRIPT_TAG = u"ARV_OpTuongWC_v1"
COMMENT_TAG = u"ARV-OpTuongWC"
TYPE_PREFIX = u"GO-Gạch ốp-"          # [cần xác nhận] quy ước tên type ốp mới (theo type có sẵn GO-Gạch ốp-300x600)
MATERIAL_PREFIX = u"Gạch Ceramic "     # [cần xác nhận] tên vật liệu mới: "Gạch Ceramic 300x600mm"
STEP_MM = 100.0         # Bước dò dọc cạnh
END_MM = 2.0            # Điểm dò đầu / cuối cạnh lùi vào
RAY_BACK_MM = 20.0      # Tia bắt đầu lùi vào trong WC
RAY_MM = 60.0           # Tầm dò mặt tường ra ngoài biên (G19: khe sàn WC – mặt tường = 10; dò xa hơn sẽ bắt
                        # nhầm tường phía sau lối mở / hộp kỹ thuật ở 85–260 mm)
LOW_MM = 300.0          # Cao độ tia dò thấp (trên chân ốp)
HIGH_GAP_MM = 50.0      # Tia dò cao: dưới đỉnh ốp
D_TOL_MM = 5.0          # Chênh khe hở cùng một đoạn
BISECT = 9              # Số lần chia đôi tìm điểm đầu / cuối đoạn (100 / 2^9 ≈ 0,2 mm)
MIN_SEG_MM = 20.0
SEARCH_MM = 500.0       # Nới hộp bao tìm tường quanh WC
MIN_PIECE_MM = 50.0     # Điểm tách tại mạch sàn cách hai đầu đoạn ốp tối thiểu (tránh mẩu ốp vụn)
HATCH_TRY = 24          # Số chỉ số đường mạch thử khi đo mạch sàn (dừng khi có 3 vị trí)
OLD_PAD_MM = 60.0       # Tường ốp cũ có trung điểm trong hộp bao biên WC nới thêm giá trị này → thuộc WC đó


# --- Hình học 2D thuần (mm) – chạy được ngoài Revit để thử --------------------------
def norm(s):
    return unicodedata.normalize("NFC", (s or u"")).strip()


def split_filters(text):
    return [s.strip() for s in (text or u"").split(u";") if s.strip()]


def matches(text, filters):
    t = norm(text).lower()
    return any(norm(f).lower() in t for f in filters)


def parse_tile(text, direction):
    """'300x600' + 'NGANG'/'DOC' → (nhỏ, lớn, rộng viên, cao viên, hậu tố tên)."""
    t = norm(text).lower().replace(u"×", u"x").replace(u"*", u"x").replace(u" ", u"").replace(u"mm", u"")
    parts = t.split(u"x")
    if len(parts) != 2:
        raise ValueError(u"Kích thước gạch '{}' không đúng dạng AxB (VD 300x600)".format(text))
    a, b = float(parts[0]), float(parts[1])
    if not (50 <= a <= 3000 and 50 <= b <= 3000):
        raise ValueError(u"Kích thước gạch '{}' ngoài khoảng 50–3000 mm".format(text))
    small, large = min(a, b), max(a, b)
    d = norm(direction).upper().replace(u"Ọ", u"O")
    vertical = d.startswith(u"D") and small != large
    w, h = (small, large) if vertical else (large, small)
    return small, large, w, h, (u"-dọc" if vertical else u"")


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
    """edges: [(a, b)] mm của một vòng biên (theo thứ tự). Trả về các đoạn ốp:
    [dict(edge, p0, p1, d, hosts, length)] – p0/p1 là tim lớp ốp (mm)."""
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
            c = r["d"] - t2           # tim lớp ốp cách cạnh biên (ra ngoài)
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


def wrap(v, period):
    """Đưa v về khoảng (-period/2, period/2]."""
    r = math.fmod(v, period)
    if r <= -period / 2.0:
        r += period
    elif r > period / 2.0:
        r -= period
    return r


def axis_key(u):
    """Trục không hướng của vector 2D: (góc độ 0–180 làm tròn 0,1°, vector đơn vị chuẩn)."""
    ang = math.degrees(math.atan2(u[1], u[0])) % 180.0
    if ang > 179.95:
        ang = 0.0
    a = math.radians(ang)
    return round(ang, 1), (math.cos(a), math.sin(a))


def joint_grid(positions):
    """Các vị trí mạch (mm, dọc trục) → (bước, pha) với mạch tại pha + k·bước; None nếu không đủ dữ liệu."""
    ps = sorted(set(round(p, 1) for p in positions))
    diffs = [b - a for a, b in zip(ps, ps[1:]) if b - a > 1.0]
    if not diffs:
        return None
    step = min(diffs)
    if any(abs(d / step - round(d / step)) > 0.01 for d in diffs):
        return None
    step = round(step * 2.0) / 2.0
    return step, math.fmod(ps[0], step) % step


def split_at_joint(seg, axis_u, grid):
    """Tách đoạn ốp tại mạch sàn gần đầu đoạn nhất (cách hai đầu ≥ MIN_PIECE_MM). Cả hai nửa BẮT ĐẦU tại điểm tách
    (gốc mạch đứng của tường = điểm đầu) → [đoạn]. Không có mạch phù hợp → [seg] (seg["align"] ghi lý do)."""
    step, phase = grid
    t0 = seg["p0"][0] * axis_u[0] + seg["p0"][1] * axis_u[1]
    sign = 1.0 if seg["u"][0] * axis_u[0] + seg["u"][1] * axis_u[1] > 0 else -1.0
    L = seg["length"]
    best = None
    k0 = int(math.floor((min(t0, t0 + sign * L) - phase) / step)) - 1
    k1 = int(math.ceil((max(t0, t0 + sign * L) - phase) / step)) + 1
    for k in range(k0, k1 + 1):
        s = (phase + k * step - t0) * sign      # khoảng cách dọc đoạn từ p0
        if MIN_PIECE_MM <= s <= L - MIN_PIECE_MM and (best is None or s < best):
            best = s
    if best is None:
        seg["align"] = u"không tách (đoạn ngắn, không có mạch sàn cách đầu ≥ {:.0f})".format(MIN_PIECE_MM)
        return [seg]
    ux, uy = seg["u"]
    p = (seg["p0"][0] + ux * best, seg["p0"][1] + uy * best)
    a = dict(seg)
    b = dict(seg)
    a.update(p0=p, p1=seg["p0"], length=best, align=u"tách tại mạch sàn ({:.0f}, {:.0f}) – nửa đầu".format(*p))
    b.update(p0=p, p1=seg["p1"], length=L - best, align=u"tách tại mạch sàn ({:.0f}, {:.0f}) – nửa sau".format(*p))
    return [a, b]


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


# --- Wall type / vật liệu / mẫu gạch -------------------------------------------------
def wall_types_by_name():
    return dict((norm(type_name(t)), t) for t in FilteredElementCollector(doc).OfClass(WallType).ToElements())


def grid_match(fpe, w, h, v0=0.0):
    """Model pattern đúng ô gạch: lưới ngang (0°) cách h, gốc V ≡ v0 (mod h); lưới đứng (90°) cách w, gốc U ≡ 0
    (mod w); không nét đứt. (Đã đo: Origin V của lưới 0° dời mạch ngang, Origin U của lưới 90° dời mạch đứng.)"""
    fp = fpe.GetFillPattern()
    if fp.Target != FillPatternTarget.Model or fp.GridCount != 2:
        return False
    got = set()
    for g in fp.GetFillGrids():
        if g.GetSegments().Count:
            return False
        ang = int(round(math.degrees(g.Angle))) % 180
        step = to_mm(g.Offset)
        if step <= 0:
            return False
        org = to_mm(g.Origin.V) if ang == 0 else to_mm(g.Origin.U)
        got.add((ang, int(round(step)), int(round(wrap(org, step)))))
    return got == set([(0, int(round(h)), int(round(wrap(v0, h)))), (90, int(round(w)), 0)])


def find_pattern(w, h, v0=0.0):
    for fpe in FilteredElementCollector(doc).OfClass(FillPatternElement).ToElements():
        if grid_match(fpe, w, h, v0):
            return fpe
    return None


def mach_suffix(v0):
    """Hậu tố tên khi mạch ngang dời khỏi cốt level: ' (mạch -15)'."""
    return u"" if abs(v0) < 0.5 else u" (mạch {:+.0f})".format(v0).replace(u"+", u"")


def create_pattern(w, h, v0=0.0):
    name = u"{}x{}{}".format(fmt_mm(h), fmt_mm(w), u"" if abs(v0) < 0.5 else u" ({:.0f})".format(v0))
    existing = set(get_name(f) for f in FilteredElementCollector(doc).OfClass(FillPatternElement).ToElements())
    while name in existing:
        name += u" ARV"
    fp = FillPattern(name, FillPatternTarget.Model, FillPatternHostOrientation.ToHost)
    g1, g2 = FillGrid(), FillGrid()
    g1.Angle, g1.Offset, g1.Origin = 0.0, from_mm(h), UV(0, from_mm(v0))
    g2.Angle, g2.Offset, g2.Origin = math.pi / 2.0, from_mm(w), UV(0, 0)
    fp.SetFillGrids(List[FillGrid]([g1, g2]))
    return FillPatternElement.Create(doc, fp)


def material_pattern(mat):
    return doc.GetElement(mat.SurfaceForegroundPatternId) if mat is not None else None


def pick_material(small, large, suffix, w, h, v0=0.0):
    """Vật liệu có sẵn chứa '{nhỏ}x{lớn}mm' (+ ' dọc') và mẫu đúng ô gạch + gốc mạch; None nếu chưa có."""
    key = u"{}x{}mm".format(fmt_mm(small), fmt_mm(large))
    for m in FilteredElementCollector(doc).OfClass(Material).ToElements():
        name = norm(m.Name)
        if key in name.replace(u" ", u"") and ((u"dọc" in name.lower()) == bool(suffix)):
            fpe = material_pattern(m)
            if fpe is not None and grid_match(fpe, w, h, v0):
                return m
    return None


def type_material(wt):
    cs = wt.GetCompoundStructure()
    if cs is None or cs.LayerCount == 0:
        return None
    return doc.GetElement(cs.GetMaterialId(0))


def ensure_wall_type(name, template, small, large, suffix, w, h, notes, v0=0.0):
    """Gọi trong Transaction. Nhân bản template → name, gán vật liệu đúng mẫu gạch (gốc mạch ngang v0)."""
    mat = pick_material(small, large, suffix, w, h, v0)
    if mat is None:
        fpe = find_pattern(w, h, v0)
        if fpe is None:
            fpe = create_pattern(w, h, v0)
            notes.append(u"ĐÃ TẠO Model pattern '{}' (ô {} rộng × {} cao, mạch ngang dời {:.0f})".format(
                get_name(fpe), fmt_mm(w), fmt_mm(h), v0))
        base = type_material(template)
        mname = u"{}{}x{}mm{}{}".format(MATERIAL_PREFIX, fmt_mm(small), fmt_mm(large), u" dọc" if suffix else u"",
                                        mach_suffix(v0))
        names = set(norm(m.Name) for m in FilteredElementCollector(doc).OfClass(Material).ToElements())
        while norm(mname) in names:
            mname += u" ARV"
        mat = base.Duplicate(mname) if base is not None else doc.GetElement(Material.Create(doc, mname))
        mat.SurfaceForegroundPatternId = fpe.Id
        notes.append(u"ĐÃ TẠO vật liệu '{}' (mẫu '{}')".format(mat.Name, get_name(fpe)))
    new = template.Duplicate(name)
    cs = new.GetCompoundStructure()
    for i in range(cs.LayerCount):
        cs.SetMaterialId(i, mat.Id)
    new.SetCompoundStructure(cs)
    notes.append(u"ĐÃ NHÂN BẢN wall type '{}' từ '{}' (vật liệu '{}')".format(name, type_name(template), mat.Name))
    return new


# --- Nguồn biên WC -------------------------------------------------------------------
class Source(object):
    def __init__(self, el, kind, level, base_ft, loops_mm, label):
        self.el = el
        self.kind = kind          # "Sàn" / "Phòng"
        self.level = level
        self.base = base_ft       # cao độ tuyệt đối mặt sàn hoàn thiện (feet)
        self.loops = loops_mm     # [[(a, b)]] cạnh thẳng theo thứ tự, mm
        self.label = label
        self.warn = []
        self.segs = []
        self.status = u""
        self.old = []             # Id tường ốp cũ của tool trong WC
        self.v0 = 0.0             # gốc mạch ngang so với cốt level (mm)
        self.tname = u""
        self.grids = None         # mạch sàn đo được {trục: (bước, pha)}


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
    s = Source(fl, u"Sàn", level, base, loops, u"{} | {}".format(comments(fl) or u"—", type_name(doc.GetElement(fl.GetTypeId()))))
    s.warn = warn
    return s


def room_source(room):
    level = room.Level
    if level is None or room.Area <= 0:
        return None
    off = room.get_Parameter(BuiltInParameter.ROOM_LOWER_OFFSET)
    base = level.Elevation + (off.AsDouble() if off else 0.0)
    opt = SpatialElementBoundaryOptions()
    opt.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.Finish
    loops, warn = [], []
    for segs in room.GetBoundarySegments(opt) or []:
        edges = []
        for sg in segs:
            c = sg.GetCurve()
            if not isinstance(c, Line):
                warn.append(u"cạnh cong bỏ qua")
                continue
            a, b = c.GetEndPoint(0), c.GetEndPoint(1)
            edges.append(((to_mm(a.X), to_mm(a.Y)), (to_mm(b.X), to_mm(b.Y))))
        if edges:
            loops.append(edges)
    s = Source(room, u"Phòng", level, base, loops, norm(room.Name))
    s.warn = warn
    return s


def is_wc_floor(fl, filters):
    return matches(comments(fl), filters) or matches(type_name(doc.GetElement(fl.GetTypeId())), filters)


def collect_sources(id_text, filters):
    """Trả về (danh sách Source, mô tả phạm vi)."""
    if id_text:
        elems = [doc.GetElement(ElementId(int(s))) for s in id_text.replace(u",", u";").split(u";") if s.strip()]
        how = u"Id nhập ở IN[5]"
    else:
        elems = [doc.GetElement(i) for i in uidoc.Selection.GetElementIds()]
        how = u"phần tử đang chọn"
    elems = [e for e in elems if isinstance(e, (Floor, Room))]
    if not elems:
        view = doc.ActiveView
        level = view.GenLevel if view.ViewType in (ViewType.FloorPlan, ViewType.CeilingPlan) else None
        if level is None:
            raise StopReport([u"DỪNG: chưa chọn sàn / phòng WC. Chọn sàn hoàn thiện WC (hoặc Room WC) rồi Run, hoặc mở "
                              u"view mặt bằng của tầng để làm mọi WC trên tầng đó."])
        floors = [f for f in FilteredElementCollector(doc).OfClass(Floor).ToElements()
                  if f.LevelId == level.Id and is_wc_floor(f, filters)]
        if floors:
            elems, how = floors, u"mọi sàn WC trên {}".format(level.Name)
        else:
            elems = [r for r in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).ToElements()
                     if isinstance(r, Room) and r.LevelId == level.Id and r.Area > 0 and matches(r.Name, filters)]
            how = u"mọi Room WC trên {} (không có sàn WC)".format(level.Name)
    sources = []
    for e in elems:
        s = floor_source(e) if isinstance(e, Floor) else room_source(e)
        if s is not None and s.loops:
            sources.append(s)
    return sources, how


# --- Dò mặt tường --------------------------------------------------------------------
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


def obstacle_solids(src, top):
    """Khối tường + cột quanh WC (trừ lớp ốp của tool): [(solid, element)]."""
    pts = [p for loop in src.loops for e in loop for p in e]
    pad = SEARCH_MM
    mn = XYZ(from_mm(min(p[0] for p in pts) - pad), from_mm(min(p[1] for p in pts) - pad), src.base)
    mx = XYZ(from_mm(max(p[0] for p in pts) + pad), from_mm(max(p[1] for p in pts) + pad), top)
    cats = List[BuiltInCategory]([BuiltInCategory.OST_Walls, BuiltInCategory.OST_StructuralColumns,
                                  BuiltInCategory.OST_Columns])
    out = []
    for el in FilteredElementCollector(doc).WherePasses(ElementMulticategoryFilter(cats)) \
            .WherePasses(BoundingBoxIntersectsFilter(Outline(mn, mx))).WhereElementIsNotElementType().ToElements():
        if comments(el).startswith(COMMENT_TAG):
            continue
        for s in element_solids(el):
            out.append((s, el))
    return out


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


def make_probe(solids, z_list):
    def probe_for_edge(a, u, n):
        def probe(s):
            # Lấy mặt gần nhất trong các cao độ: ô cửa tia thấp lọt qua, tia cao gặp lanh tô
            x, y = a[0] + u[0] * s, a[1] + u[1] * s
            best = None
            for z in z_list:
                p0 = XYZ(from_mm(x - n[0] * RAY_BACK_MM), from_mm(y - n[1] * RAY_BACK_MM), z)
                p1 = XYZ(from_mm(x + n[0] * RAY_MM), from_mm(y + n[1] * RAY_MM), z)
                h = first_hit(solids, p0, p1)
                if h is not None and (best is None or h[0] < best[0]):
                    best = h
            return None if best is None else (to_mm(best[0]) - RAY_BACK_MM, id_value(best[1].Id))
        return probe
    return probe_for_edge


# --- Đo mạch lát sàn -----------------------------------------------------------------
_PLAN_VIEWS = {}


def temp_plan(level):
    """View mặt bằng tạm của level (gọi trong Transaction sẽ RollBack)."""
    key = id_value(level.Id)
    if key not in _PLAN_VIEWS:
        vft = [t for t in FilteredElementCollector(doc).OfClass(ViewFamilyType).ToElements()
               if t.ViewFamily == ViewFamily.FloorPlan][0]
        v = ViewPlan.Create(doc, vft.Id, level.Id)
        if v.ViewTemplateId is not None and id_value(v.ViewTemplateId) > 0:
            v.ViewTemplateId = ElementId.InvalidElementId
        doc.Regenerate()
        _PLAN_VIEWS[key] = v
    return _PLAN_VIEWS[key]


def measure_floor_joints(src, axes):
    """Vị trí mạch của Model pattern trên mặt sàn WC theo từng trục (đo bằng Dimension tới đường mạch – chuỗi tham chiếu
    '<mặt sàn>/k' – trên view mặt bằng tạm). Gọi trong Transaction sẽ RollBack. Trả về {khóa trục: (bước, pha)}."""
    fl = src.el
    tops = HostObjectUtils.GetTopFaces(fl)
    if not tops or tops.Count == 0:
        return {}
    fs = tops[0].ConvertToStableRepresentation(doc)
    view = temp_plan(src.level)
    pts = [p for loop in src.loops for e in loop for p in e]
    z = src.level.Elevation
    result = {}
    for key, u in axes.items():
        n = (-u[1], u[0])
        ts = [p[0] * u[0] + p[1] * u[1] for p in pts]
        cs = [p[0] * n[0] + p[1] * n[1] for p in pts]
        tmin, tmax = min(ts) - 500.0, max(ts) + 500.0
        cn = (min(cs) + max(cs)) / 2.0

        def pt(t, c):
            return XYZ(from_mm(u[0] * t + n[0] * c), from_mm(u[1] * t + n[1] * c), z)

        rp = doc.Create.NewReferencePlane(pt(tmin, cn - 1000.0), pt(tmin, cn + 1000.0), XYZ.BasisZ, view)
        doc.Regenerate()
        line = Line.CreateBound(pt(tmin - 100.0, cn), pt(tmax, cn))
        pos = []
        for k in range(HATCH_TRY):
            if len(set(round(p, 1) for p in pos)) >= 3:
                break
            st = SubTransaction(doc)
            st.Start()
            try:
                ra = ReferenceArray()
                ra.Append(rp.GetReference())
                ra.Append(Reference.ParseFromStableRepresentation(doc, u"{}/{}".format(fs, k)))
                d = doc.Create.NewDimension(view, line, ra)
                doc.Regenerate()
                v = d.Value
                if v is not None and v > 0:
                    pos.append(tmin + to_mm(v))
            except Exception:
                pass
            finally:
                st.RollBack()
        g = joint_grid(pos)
        if g is not None:
            result[key] = g
    return result


# --- Tạo tường ốp --------------------------------------------------------------------
def existing_cladding():
    """Tường ốp của tool: [(Id, (x, y) trung điểm mm)]."""
    out = []
    for w in FilteredElementCollector(doc).OfClass(Wall).ToElements():
        if comments(w).startswith(COMMENT_TAG) and isinstance(w.Location, LocationCurve):
            p = w.Location.Curve.Evaluate(0.5, True)
            out.append((id_value(w.Id), (to_mm(p.X), to_mm(p.Y)), w.LevelId))
    return out


def old_cladding_in(src, old):
    pts = [p for loop in src.loops for e in loop for p in e]
    x0, x1 = min(p[0] for p in pts) - OLD_PAD_MM, max(p[0] for p in pts) + OLD_PAD_MM
    y0, y1 = min(p[1] for p in pts) - OLD_PAD_MM, max(p[1] for p in pts) + OLD_PAD_MM
    return [i for i, (x, y), lv in old if lv == src.level.Id and x0 <= x <= x1 and y0 <= y <= y1]


def create_cladding(src, seg, wtype, height_ft, offset_ft):
    z = src.level.Elevation
    p0 = XYZ(from_mm(seg["p0"][0]), from_mm(seg["p0"][1]), z)
    p1 = XYZ(from_mm(seg["p1"][0]), from_mm(seg["p1"][1]), z)
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


def face_room(w, seg):
    """Mặt ngoài (Exterior) của lớp ốp quay vào WC."""
    o = w.Orientation
    if o.X * seg["n"][0] + o.Y * seg["n"][1] > 0:
        w.Flip()


def join_hosts(w, seg):
    ok, fail = 0, []
    for hid in seg["hosts"]:
        host = doc.GetElement(ElementId(int(hid)))
        if host is None:
            continue
        try:
            if not JoinGeometryUtils.AreElementsJoined(doc, w, host):
                JoinGeometryUtils.JoinGeometry(doc, w, host)
            ok += 1
        except Exception:
            fail.append(hid)
    return ok, fail


def preview_lines(sources, extra_z_ft):
    try:
        clr.AddReference("ProtoGeometry")
        from Autodesk.DesignScript.Geometry import Point as DSPoint, Line as DSLine
        out = []
        for src in sources:
            z = to_mm(src.base + extra_z_ft)
            for s in src.segs:
                out.append(DSLine.ByStartPointEndPoint(DSPoint.ByCoordinates(s["p0"][0], s["p0"][1], z),
                                                       DSPoint.ByCoordinates(s["p1"][0], s["p1"][1], z)))
        return out
    except Exception:
        return []


HEADER = [u"Nguồn", u"Id nguồn", u"Mô tả", u"Đoạn", u"Dài (mm)", u"Khe tới mặt tường (mm)", u"Tường / cột chủ",
          u"Wall type", u"Căn mạch", u"Kết quả", u"ElementId", u"Nối khối"]


def write_log(rows, dry_run, settings):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "OpTuongWC_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
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


def main(tile_text, direction, height_mm, base_mm, filters, id_text, template_name, do_join, dry_run,
         align=True, replace_old=False):
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."], []
    try:
        small, large, tw, th, suffix = parse_tile(tile_text, direction)
    except ValueError as ex:
        raise StopReport([u"DỪNG: {}".format(ex)])
    if height_mm <= 0:
        raise StopReport([u"DỪNG: chiều cao ốp IN[2] phải > 0."])

    types = wall_types_by_name()
    tname = u"{}{}x{}{}".format(TYPE_PREFIX, fmt_mm(small), fmt_mm(large), suffix)
    template = types.get(norm(template_name)) if template_name else None
    base_type = types.get(norm(tname))
    if base_type is None and template is None:
        raise StopReport([u"DỪNG: chưa có wall type '{}' và không có type mẫu '{}' (IN[6]) để nhân bản. Các type ốp: {}"
                          .format(tname, template_name, u", ".join(sorted(k for k in types if k.startswith(norm(TYPE_PREFIX))))
                                  or u"không có")])
    ref_type = base_type or template
    thickness = to_mm(ref_type.Width)
    if thickness <= 0 or thickness > 60:
        raise StopReport([u"DỪNG: type '{}' dày {:.1f} mm – không phải lớp ốp.".format(type_name(ref_type), thickness)])

    sources, how = collect_sources(id_text, filters)
    if not sources:
        raise StopReport([u"DỪNG: không tìm thấy sàn / phòng WC ({}; lọc '{}').".format(how, u";".join(filters))])

    old = existing_cladding()
    height_ft, base_ft = from_mm(height_mm), from_mm(base_mm)
    z_rel = [from_mm(LOW_MM), max(from_mm(LOW_MM), height_ft - from_mm(HIGH_GAP_MM))]
    for src in sources:
        src.old = old_cladding_in(src, old)
        if src.old and not replace_old:
            src.status = u"Bỏ qua: đã có {} đoạn ốp của tool (Id {}…) – bật IN[10] để xoá và dựng lại".format(
                len(src.old), u", ".join(str(i) for i in src.old[:3]))
            continue
        bottom = src.base + base_ft
        solids = obstacle_solids(src, bottom + height_ft)
        probe = make_probe(solids, [bottom + z for z in z_rel])
        interior = []
        for loop in src.loops:
            interior.append([e[0] for e in loop])
        for loop in src.loops:
            src.segs += plan_loop(loop, interior, probe, thickness)
        if not src.segs:
            src.status = u"Không tìm thấy mặt tường quanh biên"
        perim = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for loop in src.loops for a, b in loop)
        bare = perim - sum(s["raw"] for s in src.segs)
        if bare > 100.0:
            src.warn.append(u"{:.2f} m biên không có tường / cột trong {:.0f} mm (lối mở, hộp kỹ thuật, thiếu "
                            u"tường?) – không ốp".format(bare / 1000.0, RAY_MM))
        # Gốc mạch ngang so với cốt level chân tường (mạch ngang của mẫu tính từ level)
        src.v0 = wrap(to_mm(src.base - src.level.Elevation) + base_mm, th) if align else 0.0
        src.tname = tname + mach_suffix(src.v0)
        for s in src.segs:
            s["align"] = u"tắt" if not align else u""

    jobs = [s for s in sources if s.segs and not s.status]

    # Căn mạch đứng: đo mạch sàn (transaction tạm, luôn hoàn tác) rồi tách đoạn ốp tại một mạch sàn
    if align and jobs:
        floor_jobs = [s for s in jobs if isinstance(s.el, Floor)]
        for s in jobs:
            if not isinstance(s.el, Floor):
                s.warn.append(u"nguồn là Room – không có mặt sàn để căn mạch đứng")
        grids = {}
        if floor_jobs:
            TransactionManager.Instance.ForceCloseTransaction()
            tx = Transaction(doc, u"ARV - đo mạch sàn (tạm)")
            tx.Start()
            try:
                for s in floor_jobs:
                    axes = dict(axis_key(seg["u"]) for seg in s.segs)
                    try:
                        grids[id_value(s.el.Id)] = measure_floor_joints(s, axes)
                    except Exception as ex:
                        s.warn.append(u"không đo được mạch sàn ({})".format(ex))
            finally:
                tx.RollBack()
                _PLAN_VIEWS.clear()
        for s in floor_jobs:
            g = grids.get(id_value(s.el.Id), {})
            new = []
            for seg in s.segs:
                key, au = axis_key(seg["u"])
                if key in g:
                    new += split_at_joint(seg, au, g[key])
                else:
                    seg["align"] = u"không đo được mạch sàn theo trục {:.1f}°".format(key)
                    new.append(seg)
            s.segs = new
            s.grids = g

    # Wall type theo từng gốc mạch ngang
    need = sorted(set(s.tname for s in jobs))
    v0_of = dict((s.tname, s.v0) for s in jobs)
    missing = [n for n in need if norm(n) not in types]
    notes = []
    join_fail = []
    deleted = 0
    if not dry_run and jobs:
        TransactionManager.Instance.ForceCloseTransaction()
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        try:
            wtypes = {}
            for n in need:
                wtypes[n] = types.get(norm(n)) or ensure_wall_type(n, base_type or template, small, large, suffix,
                                                                   tw, th, notes, v0_of[n])
            for src in jobs:
                for i in src.old:
                    el = doc.GetElement(ElementId(int(i)))
                    if el is not None and comments(el).startswith(COMMENT_TAG):
                        doc.Delete(el.Id)
                        deleted += 1
            created = []
            for src in jobs:
                offset = (src.base - src.level.Elevation) + base_ft
                for seg in src.segs:
                    w = create_cladding(src, seg, wtypes[src.tname], height_ft, offset)
                    seg["id"] = id_value(w.Id)
                    created.append((w, seg))
                src.status = u"Đã tạo"
            doc.Regenerate()
            for w, seg in created:
                face_room(w, seg)
                if do_join:
                    ok, fail = join_hosts(w, seg)
                    seg["join"] = u"{} / {}".format(ok, ok + len(fail))
                    join_fail += [(seg["id"], f) for f in fail]
            tx.Commit()
        except Exception as ex:
            tx.RollBack()
            return [u"LỖI khi tạo ốp tường, mọi thay đổi đã được hoàn tác: {}".format(ex)], []

    # Báo cáo
    rows = []
    total_len = 0.0
    nseg = nsplit = 0
    for src in sources:
        if not src.segs:
            rows.append([src.kind, id_value(src.el.Id), src.label, u"—", u"", u"", u"", u"", u"", src.status, u"", u""])
            continue
        for k, s in enumerate(src.segs, 1):
            total_len += s["length"]
            nseg += 1
            nsplit += 1 if s.get("align", u"").startswith(u"tách") else 0
            rows.append([src.kind, id_value(src.el.Id), src.label, k, u"{:.0f}".format(s["length"]),
                         u"{:.1f}".format(s["d"]), u", ".join(str(h) for h in sorted(s["hosts"])), src.tname,
                         s.get("align", u""), src.status or (u"Sẽ tạo" if dry_run else u""), s.get("id", u""),
                         s.get("join", u"")])
    area = total_len * height_mm / 1e6
    report = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN")]
    n_skip = sum(1 for s in sources if s.status.startswith(u"Bỏ qua"))
    n_old = sum(len(s.old) for s in jobs)
    report.append(u"Phạm vi: {} – {} nguồn ({} đã có ốp, bỏ qua){}".format(
        how, len(sources), n_skip, u" – ốp cũ {} {} đoạn".format(u"sẽ xoá" if dry_run else u"đã xoá",
                                                                  n_old if dry_run else deleted) if n_old else u""))
    report.append(u"Gạch {}x{} {} – dày {:.0f} mm – ô mẫu {} rộng × {} cao".format(
        fmt_mm(small), fmt_mm(large), u"đặt dọc" if suffix else (u"đặt ngang" if small != large else u"vuông"),
        thickness, fmt_mm(tw), fmt_mm(th)))
    for n in need:
        report.append(u"Wall type '{}' {}".format(n, u"(có sẵn)" if n not in missing else (
            u"(sẽ nhân bản từ '{}', mẫu mạch ngang dời {:.0f})".format(type_name(base_type or template), v0_of[n])
            if dry_run else u"(đã nhân bản)")))
    report.append(u"Cao ốp {} mm, chân ốp = mặt sàn WC {:+.0f} mm. Đoạn ốp {}: {} – tổng dài {:.2f} m – diện tích "
                  u"thô ≈ {:.2f} m² (chưa trừ cửa)".format(fmt_mm(height_mm), base_mm,
                                                          u"sẽ tạo" if dry_run else u"đã tạo", nseg,
                                                          total_len / 1000.0, area))
    if align:
        report.append(u"Căn mạch theo lát sàn: BẬT – {} / {} đoạn bắt đầu tại mạch sàn; hàng gạch đầu từ mặt sàn WC.".format(
            nsplit, nseg))
        for src in jobs:
            g = getattr(src, "grids", None)
            if g:
                report.append(u"  Mạch sàn {} ({}): {}".format(id_value(src.el.Id), src.label, u"; ".join(
                    u"trục {:.0f}° bước {:.0f} pha {:.1f}".format(k, v[0], v[1]) for k, v in sorted(g.items()))))
    for n in notes:
        report.append(n)
    if do_join:
        report.append(u"Nối khối lớp ốp với tường chủ: BẬT – cửa đi / cửa sổ cắt lớp ốp.")
    else:
        report.append(u"CẢNH BÁO: tắt nối khối (IN[7]) – lớp ốp chạy liền qua ô cửa có lanh tô, phải tự cắt.")
    if join_fail:
        report.append(u"CẢNH BÁO: {} cặp không nối được (ốp Id – tường Id): {}".format(
            len(join_fail), u"; ".join(u"{}–{}".format(a, b) for a, b in join_fail[:10])))
    for src in sources:
        for w in sorted(set(src.warn)):
            report.append(u"CẢNH BÁO {} {} ({}): {}".format(src.kind, id_value(src.el.Id), src.label, w))
    settings = u"gạch {}x{}{}, cao {}, chân {}, căn mạch {}, type {}".format(
        fmt_mm(small), fmt_mm(large), suffix, fmt_mm(height_mm), fmt_mm(base_mm), u"bật" if align else u"tắt",
        u", ".join(need))
    try:
        report.append(u"Log: " + write_log(rows, dry_run, settings))
    except Exception as ex:
        report.append(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        report.append(u"Kiểm tra tim lớp ốp (OUT[1]) + log. Đúng thì đổi Dry-run = False và Run lại. "
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
            (IN[0] or u"300x600").strip(),
            (IN[1] or u"NGANG").strip(),
            _num(IN[2], 2400.0),
            _num(IN[3], 0.0),
            split_filters(IN[4] or u"WC;vệ sinh"),
            (IN[5] or u"").strip(),
            (IN[6] or u"GO-Gạch ốp-300x600").strip(),
            True if IN[7] is None else bool(IN[7]),
            True if IN[8] is None else bool(IN[8]),
            True if len(IN) <= 9 or IN[9] is None else bool(IN[9]),
            False if len(IN) <= 10 or IN[10] is None else bool(IN[10]),
        ))
    except StopReport as ex:
        OUT = [ex.lines, []]
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], []]
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with io.open(os.path.join(folder, "OpTuongWC_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))), "w", encoding="utf-8-sig") as f:
                f.write(u"\n".join(OUT[0]))
        except Exception:
            pass
    note = force_rerun_next_time()
    if note:
        OUT[0].append(u"LƯU Ý: " + note)
