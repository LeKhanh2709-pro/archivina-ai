# TRẠNG THÁI: ĐÃ DUYỆT (BIM Manager, 2026-10-30)
# Mã nguồn của Python node trong 14. ARV_TaoLavaboTuCAD_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Tạo lavabo (Plumbing Fixtures) từ mặt bằng DWG đã Link, NHẬN DIỆN THEO HÌNH DẠNG (không cần biết layer):
#   1. Lavabo trên CAD = MẶT BÀN CHỮ NHẬT có LÒNG CHẬU CONG bên trong (đo trên G19 2026-10-30: block động
#      "设计行-半挂式台盆" layer A-Interior WC = polyline kín 900×500 + elip / cung / spline lòng chậu; lòng chậu ghép
#      nhiều nét hở nên không nhận theo lòng chậu):
#      - chữ nhật: polyline kín 4 đỉnh, hoặc nét thẳng nối đầu mút thành vòng 4 góc vuông (kể cả trong block);
#      - cạnh dài trong [IN[7], IN[8]] (mặc định 600–1500), cạnh ngắn trong [300, IN[9]] (mặc định 650);
#      - các nét cong (cung, elip, spline, tròn) nằm trọn trong mặt bàn gộp lại phủ ≥ 200 × 200 mm (lòng chậu) – loại
#        bàn phấn, tủ. Trong Revit lòng chậu G19 là chữ nhật bo góc (đoạn thẳng + 4 cung góc ~50 mm).
#      Chữ nhật trùng tâm (≤ 80 mm) → lấy cái lớn. IN[1] trống = dò mọi layer; có chuỗi = chỉ layer chứa chuỗi đó.
#   2. Room chứa tâm mặt bàn phải có tên chứa một chuỗi trong IN[6] (mặc định "WC;vệ sinh"; trống = mọi phòng) – loại
#      chậu rửa bếp.
#   3. Tường dựa: tường thẳng Revit trên level IN[2] (dày ≥ 50 mm) gần mép mặt bàn nhất (khe ≤ IN[10], mặc định
#      100 mm), mặt bàn nằm trọn một phía tường.
#   4. Lavabo bề rộng cố định IN[5] (mặc định 900 – người dùng chốt 2026-10-30), tâm theo tâm mặt bàn CAD dọc tường,
#      mép sau áp mặt tường – hoặc mặt ngoài lớp ốp / hoàn thiện mỏng (tường < 50 mm, VD ốp gạch 10 mm của tool 09)
#      để gương không chìm vào lớp ốp. Mặt bàn chạm tường / lớp ốp vuông góc (lavabo ở góc) → dời áp mặt đó.
#      Lavabo của tool đã có (Comments) mà sai cao độ hoặc lệch vị trí → sửa (Offset 0, dời), không tạo lại.
#   5. Type: người dùng chọn type mẫu ở IN[3] (node Family Types hoặc chuỗi "Family : Type"). Type cùng family có tham
#      số bề rộng IN[4] = IN[5] → dùng (ưu tiên type mẫu); chưa có → nhân bản type mẫu, đặt bề rộng. Chiều sâu, chiều
#      cao giữ theo type mẫu.
#   6. Đặt instance tại giữa mép sau (gốc family = giữa mép sát tường, mặt trước theo +Y như các family lavabo của dự
#      án), xoay mặt trước ra khỏi tường; IN[11] = True nếu family quay ngược. Family gắn tường → gắn vào tường dựa.
#      Comments = "ARV-TaoLavaboTuCAD". Đã có thiết bị cùng family tại vị trí → bỏ qua.
# INPUT
#   IN[0] (str)   Một phần tên bản CAD (để trống = bản CAD duy nhất trong mô hình / có layer khớp IN[1])
#   IN[1] (str)   Lọc layer, nhiều chuỗi cách ';' (khớp chuỗi con); trống = dò mọi layer (mặc định – nét layer 0 trong
#                 block có thể mang layer "0" thay vì layer block "A-Interior WC"; G19: mọi layer + lọc WC = 32/32 WC)
#   IN[2] (str)   Tên level đặt lavabo, VD "TẦNG 3"
#   IN[3] (FamilyType | str) Type mẫu lavabo (chọn ở node Family Types, hoặc "Lavabo_BanAm1 : 900" – người dùng
#                 chọn 2026-10-30; Width = 900, Depth = 450). Lavabo của tool đặt bằng family khác → đổi type tại chỗ.
#   IN[4] (str)   Tên tham số TYPE bề rộng, VD "Width"; trống = dùng thẳng type mẫu, không nhân bản (family có bề
#                 rộng cố định – lưu ý "AV-Bàn Lavabo khong ban da : 900" thực tế rộng 600, không dùng cho 900)
#   IN[5] (float) Bề rộng lavabo (mm), VD 900 – dùng để căn tâm / áp tường bên và đặt tham số IN[4]
#   IN[6] (str)   Tên Room chứa lavabo, nhiều chuỗi cách ';', VD "WC;vệ sinh" (trống = mọi phòng)
#   IN[7] (float) Cạnh dài mặt bàn lavabo tối thiểu (mm), VD 600
#   IN[8] (float) Cạnh dài mặt bàn lavabo tối đa (mm), VD 1500
#   IN[9] (float) Cạnh ngắn mặt bàn lavabo tối đa (mm), VD 650
#   IN[10] (float) Khe mặt bàn – mặt tường tối đa (mm), VD 100
#   IN[11] (bool) Đảo hướng: True nếu family có mặt trước theo −Y (lavabo quay vào tường khi chạy)
#   IN[12] (bool) Dry-run: True = chỉ báo cáo + xem trước, không ghi vào mô hình (mặc định True)
# OUTPUT
#   OUT[0] (list[str])  Báo cáo: tóm tắt, đường dẫn log, rồi từng lavabo
#   OUT[1] (list[Line]) Xem trước: mặt bàn CAD nhận diện + khung lavabo IN[5] áp mặt tường (mm)

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
                                   TransactionStatus, UnitUtils, UnitTypeId, ModelPathUtils, BuiltInParameter,
                                   BuiltInCategory, Level, Wall, LocationCurve, LocationPoint, FamilySymbol,
                                   FamilyPlacementType, ElementTransformUtils, StorageType,
                                   SpatialElementBoundaryOptions, SpatialElementBoundaryLocation, ElementId)
    from Autodesk.Revit.DB.Structure import StructuralType
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = u"ARV - Tạo lavabo từ CAD"
SCRIPT_TAG = u"ARV_TaoLavaboTuCAD_v1"
COMMENT_TAG = u"ARV-TaoLavaboTuCAD"
MAX_EDGE_MM = 2000.0             # Nét dài hơn không thể là cạnh mặt bàn lavabo – bỏ khi đọc CAD cho nhanh
SNAP_MM = 1.0                    # Đầu mút cách nhau ≤ chừng này coi là nối nhau
MAX_LOOP_EDGES = 64
MIN_SHORT_MM = 300.0             # Cạnh ngắn mặt bàn tối thiểu
RIGHT_COS = 0.02                 # Góc vuông: |cos| ≤ chừng này (lệch ≤ ~1°)
MIN_BOWL_MM = 200.0              # Vùng các nét cong lòng chậu (gộp) tối thiểu mỗi chiều
INSIDE_TOL_MM = 5.0              # Nét lòng chậu lấn ra ngoài mặt bàn tối đa
NESTED_MM = 80.0                 # Hai mặt bàn có tâm cách ≤ chừng này = cùng một lavabo
WALL_TOL_MM = 30.0               # Cho phép nét lấn vào mặt tường chừng này
MIN_HOST_WIDTH_MM = 50.0         # Tường mỏng hơn là lớp hoàn thiện, không làm tường dựa
SIDE_DEPTH_MM = 300.0            # Tường vuông góc trong dải này tính từ mặt tường dựa → chặn mép bàn
MAX_SIDE_SHIFT_MM = 50.0         # Dời áp tường bên tối đa (trát + ốp); lớn hơn = vướng tường khác → giữ theo CAD
                                 # (lần chạy 2026-10-30 10:40 dời 225 mm, tạo trùng lavabo ở 4 WC)
EXIST_TOL_MM = 150.0             # Thiết bị cùng family cách điểm đặt ≤ chừng này → đã có


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


class HostWall(object):
    """Tường trên mặt bằng (mm): trục a → b, pháp tuyến n (bên trái chiều vẽ)."""

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


class Item(object):
    """Một nét CAD: danh sách điểm (mm) + có phải nét cong."""

    def __init__(self, pts, curved):
        self.pts, self.curved = pts, curved


def same(p, q):
    return abs(p[0] - q[0]) <= SNAP_MM and abs(p[1] - q[1]) <= SNAP_MM


def find_loops(items):
    """Vòng kín từ nét thẳng: polyline tự khép (hoặc polyline 4 đỉnh – Revit có thể bỏ điểm khép), hoặc chuỗi nét nối
    đầu mút mà mọi nút có đúng 2 nét. Trả về [điểm]."""
    loops, opens = [], []
    for it in items:
        if it.curved:
            continue
        if len(it.pts) >= 4 and same(it.pts[0], it.pts[-1]):
            loops.append(it.pts[:-1])
        elif len(it.pts) == 4:
            loops.append(it.pts)
        elif len(it.pts) >= 2:
            opens.append(it)
    nodes = {}

    def key(p):
        return (int(round(p[0] / SNAP_MM)), int(round(p[1] / SNAP_MM)))

    for i, it in enumerate(opens):
        nodes.setdefault(key(it.pts[0]), []).append(i)
        nodes.setdefault(key(it.pts[-1]), []).append(i)
    used = set()
    for start in range(len(opens)):
        if start in used:
            continue
        k0, k = key(opens[start].pts[0]), key(opens[start].pts[-1])
        if len(nodes[k0]) != 2 or len(nodes[k]) != 2:
            continue
        chain, pts, cur = [start], list(opens[start].pts), start
        closed = False
        while len(chain) <= MAX_LOOP_EDGES:
            if k == k0 and len(chain) > 1:
                closed = True
                break
            if len(nodes[k]) != 2:
                break
            nxt = nodes[k][0] if nodes[k][1] == cur else nodes[k][1]
            if nxt == cur or nxt in chain:
                break
            seg = opens[nxt].pts
            if key(seg[0]) != k:
                seg = seg[::-1]
            pts.extend(seg[1:])
            chain.append(nxt)
            cur, k = nxt, key(seg[-1])
        if closed:
            used.update(chain)
            loops.append(pts[:-1])
    return loops


class Basin(object):
    """Mặt bàn lavabo nhận diện được (chữ nhật CAD) + lavabo sẽ đặt."""

    def __init__(self, corners, axis, long_side, short_side):
        self.pts, self.axis = corners, axis
        self.long, self.short = long_side, short_side
        self.area = long_side * short_side
        self.c = (sum(p[0] for p in corners) / 4.0, sum(p[1] for p in corners) / 4.0)
        self.wall = None
        self.side = 0            # +1 / -1: phía lavabo theo pháp tuyến n của tường
        self.s0 = self.s1 = 0.0  # mép lavabo theo trục tường
        self.face = 0.0          # mặt tường (khoảng cách tới tim, dương)
        self.front = 0.0         # mép trước mặt bàn CAD
        self.gap = 0.0
        self.room = u""
        self.status = u""
        self.type_name = u""
        self.eid = u""
        self.note = u""
        self.dups = []           # Id lavabo cùng family trùng chỗ (thừa)

    def insert_point(self):
        """Giữa mép sau lavabo, trên mặt tường."""
        return self.wall.point((self.s0 + self.s1) / 2.0, self.side * self.face)

    def facing(self):
        return (self.wall.n[0] * self.side, self.wall.n[1] * self.side)


def rect_corners(pts):
    """4 góc nếu vòng là hình chữ nhật (bỏ điểm trùng / thẳng hàng), None nếu không."""
    clean = []
    for p in pts:
        if not clean or not same(p, clean[-1]):
            clean.append(p)
    if len(clean) > 1 and same(clean[0], clean[-1]):
        clean.pop()
    corners = []
    n = len(clean)
    for i in range(n):
        a, b, c = clean[i - 1], clean[i], clean[(i + 1) % n]
        u, v = sub(b, a), sub(c, b)
        lu, lv = math.hypot(*u), math.hypot(*v)
        if lu < 1e-6 or lv < 1e-6:
            return None
        cos = dot(u, v) / (lu * lv)
        if cos > 1.0 - 1e-6:
            continue                    # thẳng hàng
        if abs(cos) > RIGHT_COS:
            return None
        corners.append(b)
    return corners if len(corners) == 4 else None


def counter_shape(pts, min_long, max_long, max_short):
    """Vòng kín là mặt bàn chữ nhật đúng cỡ → Basin, không thì None."""
    corners = rect_corners(pts)
    if corners is None:
        return None
    e1, e2 = sub(corners[1], corners[0]), sub(corners[2], corners[1])
    l1, l2 = math.hypot(*e1), math.hypot(*e2)
    long_side, short_side = max(l1, l2), min(l1, l2)
    if not (min_long <= long_side <= max_long and MIN_SHORT_MM <= short_side <= max_short):
        return None
    axis = unit(e1) if l1 >= l2 else unit(e2)
    return Basin(corners, axis, long_side, short_side)


def has_bowl(b, curves):
    """Mặt bàn có lòng chậu: các nét cong nằm trọn trong mặt bàn, gộp lại phủ vùng ≥ MIN_BOWL_MM × MIN_BOWL_MM.
    Revit 2027 đổi elip / spline của block thành PolyLine; lòng chậu G19 vào Revit là chữ nhật bo góc (cạnh thẳng +
    4 cung góc ~50 mm, chẩn đoán 2026-10-30 10:12) nên xét cả các cung nhỏ gộp lại."""
    nrm = (-b.axis[1], b.axis[0])
    hu, hv = b.long / 2.0 + INSIDE_TOL_MM, b.short / 2.0 + INSIDE_TOL_MM
    us, vs = [], []
    for pts in curves:
        loc = [(dot(sub(p, b.c), b.axis), dot(sub(p, b.c), nrm)) for p in pts]
        if all(abs(u) <= hu and abs(v) <= hv for u, v in loc):
            us += [u for u, _ in loc]
            vs += [v for _, v in loc]
    return bool(us) and max(us) - min(us) >= MIN_BOWL_MM and max(vs) - min(vs) >= MIN_BOWL_MM


def covers(b, p):
    """Điểm p nằm trong mặt bàn b."""
    q = sub(p, b.c)
    return abs(dot(q, b.axis)) <= b.long / 2.0 and abs(dot(q, (-b.axis[1], b.axis[0]))) <= b.short / 2.0


def find_basins(items, min_long, max_long, max_short, stats=None):
    loops = find_loops(items)
    found = [b for b in (counter_shape(p, min_long, max_long, max_short) for p in loops) if b]
    bowls = [it.pts for it in items if it.curved]
    if stats is not None:
        stats.update(loops=len(loops), rects=len(found), bowls=len(bowls))
    found = [b for b in found if has_bowl(b, bowls)]
    # Chữ nhật trùng tâm hoặc chồng lên nhau (vẽ chồng / trạng thái block động) → giữ cái lớn
    found.sort(key=lambda b: -b.area)
    result = []
    for b in found:
        if all(math.hypot(b.c[0] - r.c[0], b.c[1] - r.c[1]) > NESTED_MM and not covers(r, b.c) for r in result):
            result.append(b)
    return result


def fit_wall(b, walls, max_gap):
    """Tường dựa = tường song song cạnh dài mặt bàn (lavabo ở góc chạm cả tường bên), gần mép mặt bàn nhất, mặt bàn
    nằm trọn một phía. Trả về lỗi hoặc None."""
    best = None
    for w in walls:
        loc = [w.local(p) for p in b.pts]
        ds = [d for _, d in loc]
        h = w.width / 2.0 - WALL_TOL_MM
        if min(ds) >= h:
            side = 1
        elif max(ds) <= -h:
            side = -1
        else:
            continue
        near = min(side * d for d in ds)
        gap = near - w.width / 2.0
        if gap > max_gap:
            continue
        sc = w.local(b.c)[0]
        if not (0.0 <= sc <= w.length):
            continue
        key = (abs(dot(w.u, b.axis)) >= 0.9, -gap)
        if best is None or key > best[0]:
            best = (key, gap, w, side, sc, max(side * d for d in ds))
    if best is None:
        return u"không có tường Revit cách mép mặt bàn ≤ {:.0f} mm".format(max_gap)
    _, b.gap, b.wall, b.side, sc, b.front = best
    b.face = b.wall.width / 2.0
    b.s0, b.s1 = sc, sc
    return None


def finish_offset(b, thin):
    """Bề dày lớp ốp / hoàn thiện mỏng (tường < MIN_HOST_WIDTH_MM) áp mặt tường dựa ở phía lavabo, phủ vị trí lavabo
    → mặt sau lavabo (gương) áp mặt ngoài lớp ốp. Lần chạy 2026-10-30: gương chìm 10 mm trong lớp ốp
    "WA_F1_10_Op gach 300x600" do tool 09 dựng."""
    w = b.wall
    mid = (b.s0 + b.s1) / 2.0
    extra = 0.0
    for x in thin:
        if abs(abs(dot(x.u, w.u)) - 1.0) > 1e-3:
            continue
        sa, da = w.local(x.a)
        sb, _ = w.local(x.b)
        d = b.side * da
        if abs(d - x.width / 2.0 - b.face) > 3.0:
            continue
        if not (min(sa, sb) - 1.0 <= mid <= max(sa, sb) + 1.0):
            continue
        extra = max(extra, d + x.width / 2.0 - b.face)
    return extra


def place_counter(b, walls, width):
    """Lavabo rộng width, tâm theo tâm mặt bàn CAD; tường vuông góc chạm mặt bàn (lavabo ở góc) → dời mép bàn áp mặt tường đó.
    Trả về ghi chú dời (hoặc u"")."""
    w = b.wall
    mid = (b.s0 + b.s1) / 2.0
    lo, hi = mid - width / 2.0, mid + width / 2.0
    shift = 0.0
    for x in walls:
        if x is w or abs(dot(x.u, w.u)) > 0.1:
            continue
        sa, da = w.local(x.a)
        sb, db = w.local(x.b)
        ds = sorted((b.side * da, b.side * db))
        # Tường vuông góc phải nằm cùng phía, phủ dải sát mặt tường dựa
        if ds[1] < b.face + 1.0 or ds[0] > b.face + SIDE_DEPTH_MM:
            continue
        s_axis, t = (sa + sb) / 2.0, x.width / 2.0
        if s_axis < mid and s_axis + t > lo:
            shift = max(shift, s_axis + t - lo)
        elif s_axis >= mid and s_axis - t < hi:
            shift = min(shift, s_axis - t - hi)
    if abs(shift) > MAX_SIDE_SHIFT_MM:
        b.s0, b.s1 = lo, hi
        return u"vướng tường bên {:+.0f} mm – giữ theo CAD, cần soát".format(shift)
    b.s0, b.s1 = lo + shift, hi + shift
    return u"dời {:+.0f} mm để áp tường bên".format(shift) if abs(shift) >= 1.0 else u""


def analyse(items, walls, width, min_long, max_long, max_short, max_gap, room_at=None, room_keys=(), existing=(),
            stats=None, thin=()):
    """items: [Item] mm; walls: [HostWall]; room_keys: chuỗi tên Room (đã loose); existing: [(điểm mm, Id)] thiết bị
    cùng family trên level; thin: [HostWall] lớp ốp / hoàn thiện mỏng. Trả về [Basin] đã gán trạng thái."""
    basins = find_basins(items, min_long, max_long, max_short, stats)
    for b in basins:
        if room_at is not None:
            b.room = room_at(b.c) or u""
            if room_keys and not any(k in loose(b.room) for k in room_keys):
                b.status = u"Bỏ qua – không nằm trong phòng {} (phòng: {})".format(
                    u"/".join(room_keys), b.room or u"không có Room")
                continue
        err = fit_wall(b, walls, max_gap)
        if err:
            b.status = u"Bỏ qua – " + err
            continue
        clad = finish_offset(b, thin)
        b.face += clad
        b.note = u"; ".join(v for v in (u"mặt bàn CAD {:.0f}x{:.0f}".format(b.long, b.short),
                                        u"áp mặt lớp ốp {:.0f} mm".format(clad) if clad else u"",
                                        place_counter(b, list(walls) + list(thin), width)) if v)
        p = b.insert_point()
        # Lavabo cùng family đã có trong vùng mặt bàn (không chỉ quanh điểm đặt mới – điểm đặt đổi giữa các bản) →
        # giữ cái gần điểm đặt nhất, các cái còn lại là TRÙNG (báo để xoá tay)
        near = sorted((math.hypot(q[0] - p[0], q[1] - p[1]), eid) for q, eid in existing
                      if math.hypot(q[0] - b.c[0], q[1] - b.c[1]) <= max(b.long, width) / 2.0 + EXIST_TOL_MM)
        if near:
            b.eid = near[0][1]
            b.dups = [eid for _, eid in near[1:]]
            b.status = u"Bỏ qua – đã có lavabo cùng family (Id {})".format(b.eid)
            continue
        b.status = u"OK"
    basins.sort(key=lambda b: (-round(b.c[1]), round(b.c[0])))
    return basins


def new_type_name(template_name, width, taken):
    """Tên type mới theo bề rộng: tên mẫu chỉ là số (VD "900") → "<rộng>"; có số dạng "<rộng>x<sâu>" → đổi số rộng;
    còn lại → "<tên mẫu>_<rộng>". Trùng tên type khác → thêm hậu tố."""
    w = str(int(width))
    m = re.search(r"(\d+)([xX])(\d+)", template_name)
    if re.match(r"^\s*\d+\s*$", template_name):
        name = w
    elif m:
        name = template_name[:m.start()] + w + template_name[m.start(2):]
    else:
        name = u"{}_{}".format(template_name, w)
    base, i = name, 2
    while norm(name) in taken:
        name, i = u"{}_{}".format(base, i), i + 1
    return name


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


def read_items(objects, layers, raw=None):
    """Nét ngắn (≤ MAX_EDGE_MM) trên các layer – ứng viên cạnh mặt bàn và lòng chậu.
    raw (list): nhận mọi đối tượng trên các layer (loại, layer, điểm mm, có dùng) để ghi file chẩn đoán."""
    items, lim = [], from_mm(MAX_EDGE_MM)
    for obj in objects:
        layer = layer_of(obj)
        if layer not in layers:
            continue
        pts, kept = None, False
        if isinstance(obj, PolyLine):
            pts = list(obj.GetCoordinates())
            if len(pts) >= 2:
                ext = max(max(p.X for p in pts) - min(p.X for p in pts), max(p.Y for p in pts) - min(p.Y for p in pts))
                if ext <= lim:
                    items.append(Item([xy(p) for p in pts], False))
                    kept = True
        elif isinstance(obj, Curve):
            try:
                length = obj.Length if obj.IsBound else obj.ApproximateLength
            except Exception:
                length = obj.ApproximateLength
            curved = isinstance(obj, (Arc, Ellipse, NurbSpline, HermiteSpline))
            pts = [obj.GetEndPoint(0), obj.GetEndPoint(1)] if isinstance(obj, Line) else list(obj.Tessellate())
            if (curved and length <= 4 * lim) or (not curved and length <= lim):
                items.append(Item([xy(p) for p in pts], curved))
                kept = True
        elif raw is not None:
            try:
                bb = obj.GetBoundingBox()
                pts = [bb.Transform.OfPoint(bb.Min), bb.Transform.OfPoint(bb.Max)]
            except Exception:
                try:
                    pts = list(obj.Vertices)
                except Exception:
                    pts = None
        if raw is not None:
            raw.append((obj.GetType().Name, layer, [xy(p) for p in pts] if pts else [], kept))
    return items


def write_diag(raw, room_at, room_keys, dry_run):
    """File chẩn đoán: mọi đối tượng CAD có tâm nằm trong Room WC (loại, layer, khung bao, số điểm, khép kín)."""
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    path = os.path.join(folder, "TaoLavaboTuCAD_CHANDOAN_{}.csv".format(
        datetime.datetime.now().strftime("%Y%m%d_%H%M%S")))
    n = 0
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow([u"Phòng", u"Loại", u"Layer", u"Xmin", u"Ymin", u"Rộng X", u"Rộng Y", u"Số điểm", u"Khép kín",
                    u"Dùng"])
        for kind, layer, pts, kept in raw:
            if not pts:
                continue
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            c = ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)
            room = room_at(c) or u""
            if not any(k in loose(room) for k in room_keys):
                continue
            w.writerow([room, kind, layer, u"{:.0f}".format(min(xs)), u"{:.0f}".format(min(ys)),
                        u"{:.0f}".format(max(xs) - min(xs)), u"{:.0f}".format(max(ys) - min(ys)), len(pts),
                        u"có" if len(pts) > 2 and same(pts[0], pts[-1]) else u"", u"có" if kept else u""])
            n += 1
    return path, n


def host_walls(level):
    """(tường dựa ≥ MIN_HOST_WIDTH_MM, {id: Wall}, tường mỏng – lớp ốp / hoàn thiện)."""
    result, by_id, thin = [], {}, []
    for wl in FilteredElementCollector(doc).OfClass(Wall).ToElements():
        loc = wl.Location
        if wl.LevelId == level.Id and isinstance(loc, LocationCurve) and isinstance(loc.Curve, Line):
            c = loc.Curve
            hw = HostWall(wl.Id.Value, xy(c.GetEndPoint(0)), xy(c.GetEndPoint(1)), to_mm(wl.Width), get_name(wl))
            if hw.length < 1.0:
                continue
            if hw.width >= MIN_HOST_WIDTH_MM:
                result.append(hw)
                by_id[hw.id] = wl
            else:
                thin.append(hw)
    return result, by_id, thin


def inside_loops(p, loops):
    """Điểm trong vùng giới hạn bởi các vòng biên (chẵn lẻ – lỗ trong Room tự trừ)."""
    c = False
    for pts in loops:
        for i in range(len(pts)):
            (x1, y1), (x2, y2) = pts[i - 1], pts[i]
            if (y1 > p[1]) != (y2 > p[1]) and p[0] < x1 + (p[1] - y1) * (x2 - x1) / (y2 - y1):
                c = not c
    return c


def room_finder(level):
    """Hàm room_at(pt mm) → tên Room trên level chứa điểm, None nếu không có. Xét trên mặt bằng theo đường biên Room
    (mặt hoàn thiện) – không phụ thuộc cao độ như Room.IsPointInRoom (lần chạy 2026-10-30 10:06 nhận 0/25 bằng
    IsPointInRoom)."""
    opt = SpatialElementBoundaryOptions()
    opt.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.Finish
    rooms = []
    for r in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms)             .WhereElementIsNotElementType().ToElements():
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
        prm = r.get_Parameter(BuiltInParameter.ROOM_NAME)
        rooms.append(((min(xs), min(ys), max(xs), max(ys)), loops, prm.AsString() if prm is not None else u""))

    def room_at(p):
        for box, loops, name in rooms:
            if box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3] and inside_loops(p, loops):
                return name
        return None
    return room_at, len(rooms)


def fixture_symbols():
    return [s for s in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures)
            .WhereElementIsElementType().ToElements() if isinstance(s, FamilySymbol)]


def pick_template(value):
    """IN[3]: FamilyType của node Family Types (Dynamo) hoặc chuỗi "Family : Type" → FamilySymbol lavabo mẫu."""
    symbols = fixture_symbols()
    families = u", ".join(sorted(set(s.FamilyName for s in symbols))) or u"không có"
    if isinstance(value, str):
        parts = [norm(p) for p in value.split(u":")]
        if len(parts) != 2 or not all(parts):
            raise StopReport([u"DỪNG: ô IN[3] phải là type chọn từ node Family Types hoặc chuỗi 'Family : Type' "
                              u"(đang là '{}').".format(value)])
        hits = [s for s in symbols if norm(s.FamilyName) == parts[0] and norm(get_name(s)) == parts[1]]
        if not hits:
            raise StopReport([u"DỪNG: không có type lavabo '{}'. Family thiết bị vệ sinh: {}".format(value, families)])
        return hits[0]
    sym = UnwrapElement(value) if value is not None else None
    if not isinstance(sym, FamilySymbol):
        raise StopReport([u"DỪNG: chưa chọn type mẫu ở IN[3]."])
    if sym.Category is None or sym.Category.BuiltInCategory != BuiltInCategory.OST_PlumbingFixtures:
        raise StopReport([u"DỪNG: type '{} : {}' không thuộc Plumbing Fixtures. Family thiết bị vệ sinh: {}".format(
            sym.FamilyName, get_name(sym), families)])
    return sym


def width_param(symbol, name):
    # Tham số bề rộng là tham số family (không phải shared parameter, không có GUID / BuiltInParameter)
    # nên phải tìm theo tên người dùng nhập ở IN[4].
    return symbol.LookupParameter(name)


def length_params(symbol):
    return sorted(set(p.Definition.Name for p in symbol.Parameters
                      if p.StorageType == StorageType.Double and not p.IsReadOnly))


def symbol_width(s, name):
    p = width_param(s, name)
    return to_mm(p.AsDouble()) if p is not None else None


def existing_fixtures(family_name, level):
    """[(điểm mm, Id)] lavabo đã đặt trên level: cùng family, hoặc do tool tạo (Comments) bằng family khác – người
    dùng đổi family 2026-10-30 ("AV-Bàn Lavabo khong ban da" thực tế rộng 600 → "Lavabo_BanAm1 : 900")."""
    result = []
    for fi in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures) \
            .WhereElementIsNotElementType().ToElements():
        loc = getattr(fi, "Location", None)
        sym = getattr(fi, "Symbol", None)
        if sym is None or not isinstance(loc, LocationPoint) or fi.LevelId != level.Id:
            continue
        cm = fi.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        if norm(sym.FamilyName) == family_name or (cm is not None and cm.AsString() == COMMENT_TAG):
            result.append((xy(loc.Point), fi.Id.Value))
    return result


def elevation_param(fi):
    """Cao độ instance so với level ("Elevation from Level" / "Offset from Host")."""
    return fi.get_Parameter(BuiltInParameter.INSTANCE_ELEVATION_PARAM) or         fi.get_Parameter(BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM)


def set_elevation_zero(fi):
    p = elevation_param(fi)
    if p is not None and not p.IsReadOnly and abs(p.AsDouble()) > 1e-9:
        p.Set(0.0)


def orient(fi, want, pivot):
    """Xoay instance quanh trục đứng qua pivot cho FacingOrientation trùng hướng want (2D)."""
    doc.Regenerate()
    f = fi.FacingOrientation
    ang = math.atan2(f.X * want[1] - f.Y * want[0], f.X * want[0] + f.Y * want[1])
    if abs(ang) > 1e-6:
        axis = Line.CreateBound(pivot, XYZ(pivot.X, pivot.Y, pivot.Z + 1.0))
        ElementTransformUtils.RotateElement(doc, fi.Id, axis, ang)


def preview_lines(basins, z_mm):
    try:
        clr.AddReference("ProtoGeometry")
        from Autodesk.DesignScript.Geometry import Point as DSPoint, Line as DSLine

        def seg(a, e):
            return DSLine.ByStartPointEndPoint(DSPoint.ByCoordinates(a[0], a[1], z_mm),
                                               DSPoint.ByCoordinates(e[0], e[1], z_mm))
        lines = []
        for b in basins:
            pts = b.pts
            lines += [seg(pts[i - 1], pts[i]) for i in range(len(pts)) if math.hypot(*sub(pts[i], pts[i - 1])) > 1.0]
            w = b.wall
            corners = [w.point(s, b.side * d) for s, d in ((b.s0, b.face), (b.s1, b.face), (b.s1, b.front),
                                                           (b.s0, b.front))]
            lines += [seg(a, e) for a, e in zip(corners, corners[1:] + corners[:1])]
        return lines
    except Exception:
        return []


LOG_HEADER = [u"STT", u"Tâm mặt bàn (mm)", u"Mặt bàn CAD (mm)", u"Rộng lavabo (mm)", u"Phòng", u"Tường dựa", u"Type",
              u"Kết quả", u"ElementId", u"Ghi chú"]


def write_log(rows, source, dry_run):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoLavaboTuCAD_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
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


def main(cad_filter, layer_filters, level_name, template_in, w_name, width, room_keys, min_long, max_long,
         max_short, max_gap, reverse, dry_run):
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."], []
    if re.search(r"[-_]S[-_]", doc.Title or u""):
        return [u"DỪNG: tên file '{}' là mô hình Kết cấu (S) – lavabo chỉ dựng trên mô hình Kiến trúc (A).".format(
            doc.Title)], []
    if width <= 0:
        raise StopReport([u"DỪNG: bề rộng lavabo IN[5] phải > 0."])
    tpl = pick_template(template_in)
    fam, tname = norm(tpl.FamilyName), norm(get_name(tpl))
    fixed_type = not w_name
    if not fixed_type and width_param(tpl, w_name) is None:
        raise StopReport([u"DỪNG: type '{} : {}' không có tham số type '{}'. Tham số chiều dài sửa được: {} – nhập lại "
                          u"IN[4], hoặc để trống IN[4] để dùng thẳng type mẫu (bề rộng cố định trong family)."
                          .format(fam, tname, w_name, u", ".join(length_params(tpl)))])
    placement = tpl.Family.FamilyPlacementType
    if placement not in (FamilyPlacementType.OneLevelBased, FamilyPlacementType.OneLevelBasedHosted):
        raise StopReport([u"DỪNG: family '{}' kiểu đặt {} – công cụ chỉ hỗ trợ family đặt theo level hoặc gắn tường."
                          .format(fam, placement)])
    cad, cad_name, objects, all_layers = pick_cad(cad_filter, layer_filters)
    layers = match_layers(all_layers, layer_filters)
    level = find_level(level_name)
    walls, wall_by_id, thin = host_walls(level)
    if not walls:
        raise StopReport([u"DỪNG: level '{}' chưa có tường thẳng nào để đặt lavabo sát tường.".format(level_name)])
    room_at, n_rooms = room_finder(level)
    keys = [loose(k) for k in room_keys if k.strip()]
    if keys and not n_rooms:
        raise StopReport([u"DỪNG: level '{}' chưa có Room – cần Room để lọc lavabo trong WC (hoặc để trống IN[6])."
                          .format(level_name)])

    raw = []
    items = read_items(objects, layers, raw)
    stats = {}
    basins = analyse(items, walls, width, min_long, max_long, max_short, max_gap, room_at, keys,
                     existing_fixtures(fam, level), stats, thin)

    # Type: ưu tiên type mẫu, rồi type cùng family đã có bề rộng này; chưa có → nhân bản
    symbols = [s for s in fixture_symbols() if norm(s.FamilyName) == fam]
    sym = tpl if fixed_type else None
    for s in ([] if fixed_type else [tpl] + [s for s in symbols if s.Id != tpl.Id]):
        sw = symbol_width(s, w_name)
        if sw is not None and abs(sw - width) <= 1.0:
            sym = s
            break
    new_name = None if sym is not None else new_type_name(tname, width, set(norm(get_name(s)) for s in symbols))
    type_label = u"{} : {}".format(fam, get_name(sym) if sym is not None else new_name + u" (mới)")

    rows, jobs, fixes = [], [], []
    for idx, b in enumerate(basins, 1):
        if b.status == u"OK":
            b.type_name = type_label
            b.status = u"Sẽ tạo" if dry_run else u"Chờ tạo"
            jobs.append((b, len(rows)))
        elif b.eid:
            # Lavabo của tool đã có nhưng sai cao độ (bản 10:16 đặt Offset = cao độ level) hoặc lệch vị trí (bản trước
            # chưa tính lớp ốp) → sửa: Offset về 0, dời tới điểm đặt mới. Chỉ sửa lavabo có Comments của tool.
            fi = doc.GetElement(ElementId(b.eid))
            cm = fi.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS) if fi is not None else None
            if cm is not None and cm.AsString() == COMMENT_TAG:
                todo = []
                retype = sym is None or fi.Symbol.Id != sym.Id
                if retype:
                    todo.append(u"đổi type {} : {} → {}".format(fi.Symbol.FamilyName, get_name(fi.Symbol),
                                                                type_label.split(u" : ", 1)[1]))
                ep = elevation_param(fi)
                elev = ep is not None and abs(to_mm(ep.AsDouble())) > 1.0
                if elev:
                    todo.append(u"cao độ {:.0f} → 0".format(to_mm(ep.AsDouble())))
                cur, want_p = xy(fi.Location.Point), b.insert_point()
                move = (want_p[0] - cur[0], want_p[1] - cur[1])
                if math.hypot(*move) > 1.0:
                    todo.append(u"dời {:.0f} mm".format(math.hypot(*move)))
                else:
                    move = None
                f = b.facing()
                want = (-f[0], -f[1]) if reverse else f
                ff = fi.FacingOrientation
                turn = ff.X * want[0] + ff.Y * want[1] < 0.9998       # lệch > ~1°
                if turn:
                    todo.append(u"xoay {:.0f}°".format(math.degrees(math.atan2(
                        ff.X * want[1] - ff.Y * want[0], ff.X * want[0] + ff.Y * want[1]))))
                if retype and not turn:
                    # Family mới có thể khác hướng gốc → luôn kiểm tra lại hướng sau khi đổi type
                    want_retype = want
                else:
                    want_retype = want if turn else None
                if todo:
                    b.note = u"; ".join(v for v in [b.note] + todo if v)
                    b.status = u"Sẽ sửa" if dry_run else u"Chờ sửa"
                    fixes.append((fi, len(rows), elev, move, want_retype, want_p, retype))
        rows.append([idx, fmt(b.c), u"{:.0f}x{:.0f}".format(b.long, b.short),
                     int(width) if b.wall else u"—", b.room or u"—",
                     u"{} ({})".format(b.wall.id, b.wall.name) if b.wall else u"—", b.type_name or u"—", b.status,
                     b.eid, u"; ".join(v for v in [b.note] + [u"TRÙNG Id {}".format(d) for d in b.dups] if v)])

    created = []
    if not dry_run and (jobs or fixes):
        TransactionManager.Instance.ForceCloseTransaction()
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        try:
            if sym is None:
                sym = tpl.Duplicate(new_name)
                p = width_param(sym, w_name)
                if p is None or p.IsReadOnly:
                    raise Exception(u"Type '{}' không đặt được tham số {}.".format(new_name, w_name))
                p.Set(from_mm(width))
            if not sym.IsActive:
                sym.Activate()
                doc.Regenerate()
            # Revit hiểu Z của điểm đặt là độ lệch so với level (Z = cao độ level → Offset = cao độ level, lỗi lần
            # chạy 2026-10-30 10:16) → đặt Z = 0 và gán lại Offset = 0 sau khi tạo
            z = 0.0
            for fi, ri, elev, move, want, want_p, retype in fixes:
                if retype:
                    fi.ChangeTypeId(sym.Id)
                    doc.Regenerate()
                    set_elevation_zero(fi)
                if elev:
                    set_elevation_zero(fi)
                if move:
                    ElementTransformUtils.MoveElement(doc, fi.Id, XYZ(from_mm(move[0]), from_mm(move[1]), 0.0))
                if want:
                    orient(fi, want, XYZ(from_mm(want_p[0]), from_mm(want_p[1]), 0.0))
                rows[ri][7] = u"Đã sửa"
            for b, ri in jobs:
                p = b.insert_point()
                pt = XYZ(from_mm(p[0]), from_mm(p[1]), z)
                if placement == FamilyPlacementType.OneLevelBasedHosted:
                    fi = doc.Create.NewFamilyInstance(pt, sym, wall_by_id[b.wall.id], level,
                                                      StructuralType.NonStructural)
                else:
                    fi = doc.Create.NewFamilyInstance(pt, sym, level, StructuralType.NonStructural)
                f = b.facing()
                want = (-f[0], -f[1]) if reverse else f
                if placement == FamilyPlacementType.OneLevelBasedHosted:
                    doc.Regenerate()
                    ff = fi.FacingOrientation
                    if ff.X * want[0] + ff.Y * want[1] < 0 and fi.CanFlipFacing:
                        fi.flipFacing()
                else:
                    orient(fi, want, pt)
                set_elevation_zero(fi)
                cm = fi.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
                if cm is not None and not cm.IsReadOnly:
                    cm.Set(COMMENT_TAG)
                rows[ri][7] = u"Đã tạo"
                rows[ri][8] = fi.Id.Value
                created.append((fi, ri))
            status = tx.Commit()
        except Exception as ex:
            tx.RollBack()
            return [u"LỖI khi tạo lavabo, mọi thay đổi đã được hoàn tác: {}".format(ex)], []
        if status != TransactionStatus.Committed:
            return [u"LỖI: Revit không lưu được Transaction ({}), mọi thay đổi đã được hoàn tác.".format(status)], []
        for fi, ri in created:
            if not fi.IsValidObject:
                rows[ri][7] = u"Revit đã xoá sau khi tạo"

    report = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN")]
    report.append(u"CAD: {} – dò {} – {} nét ngắn – nhận diện {} mặt bàn lavabo (chữ nhật có lòng chậu)".format(
        cad_name, u"layer " + u"; ".join(sorted(layers)) if layer_filters else u"mọi layer ({})".format(len(layers)),
        len(items), len(basins)))
    report.append(u"Lavabo: {} – {} – level {} – phòng chứa: {}".format(
        type_label, u"dùng thẳng type mẫu (IN[4] trống), bề rộng đặt chỗ {:.0f} mm".format(width) if fixed_type
        else u"{} = {:.0f} mm".format(w_name, width), level.Name, u"; ".join(room_keys) if keys else u"mọi phòng"))
    report.append(u"Lavabo {}: {}".format(u"sẽ tạo" if dry_run else u"đã tạo", len(jobs)))
    if fixes:
        report.append(u"Lavabo của tool {}: {} (đổi type: {}, cao độ về 0: {}, dời: {}, xoay/kiểm hướng: {})".format(
            u"sẽ sửa" if dry_run else u"đã sửa", len(fixes), len([1 for f in fixes if f[6]]),
            len([1 for f in fixes if f[2]]), len([1 for f in fixes if f[3]]), len([1 for f in fixes if f[4]])))
    dups = [(b, d) for b in basins for d in b.dups]
    if dups:
        report.append(u"TRÙNG: {} lavabo cùng family thừa trong cùng WC – xoá tay (giữ Id bên phải): {}".format(
            len(dups), u", ".join(u"{} (giữ {})".format(d, b.eid) for b, d in dups)))
    counts = {}
    for b in basins:
        if b.status.startswith(u"Bỏ qua"):
            k = re.sub(r"[\d(].*", u"", b.status.split(u" – ", 1)[1]).strip()
            counts[k] = counts.get(k, 0) + 1
    for k in sorted(counts):
        report.append(u"Bỏ qua {} lavabo: {}".format(counts[k], k))
    by_room = {}
    for b in basins:
        if b.status.startswith(u"Bỏ qua – không nằm trong phòng"):
            by_room[b.room or u"không có Room"] = by_room.get(b.room or u"không có Room", 0) + 1
    if by_room:
        report.append(u"  – phòng chứa các mặt bàn bị loại: " + u", ".join(
            u"{} ×{}".format(k, v) for k, v in sorted(by_room.items(), key=lambda kv: -kv[1])))
    report.append(u"Chẩn đoán nhận diện: {} vòng kín – {} chữ nhật đúng cỡ – {} nét cong – {} mặt bàn có lòng chậu (nét cong "
                  u"phủ ≥ {:.0f} mm) – Room trên level: {}".format(stats.get("loops", 0), stats.get("rects", 0),
                                                    stats.get("bowls", 0), len(basins), MIN_BOWL_MM, n_rooms))
    kinds = {}
    for kind, _, _, _ in raw:
        kinds[kind] = kinds.get(kind, 0) + 1
    report.append(u"Đối tượng CAD theo loại: " + u", ".join(u"{} {}".format(k, v) for k, v in sorted(kinds.items())))
    if keys:
        try:
            path, n = write_diag(raw, room_at, keys, dry_run)
            report.append(u"Chẩn đoán WC: {} đối tượng CAD trong Room WC → {}".format(n, path))
        except Exception as ex:
            report.append(u"Không ghi được file chẩn đoán: {}".format(ex))
    try:
        report.append(u"Log: " + write_log(rows, cad_name, dry_run))
    except Exception as ex:
        report.append(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        report.append(u"Kiểm tra mặt bàn CAD + khung lavabo (đoạn xanh trong Dynamo) và log. Thiếu lavabo → nới IN[7]–IN[10]. "
                      u"Đúng thì đổi Dry-run = False và Run lại. Undo bằng mục \"{}\".".format(TRANSACTION_NAME))
    else:
        report.append(u"Soát hướng vài lavabo (quay ngược vào tường → Undo, đổi IN[11] rồi Run lại). Undo bằng mục "
                      u"\"{}\".".format(TRANSACTION_NAME))
    report.append(u" | ".join(LOG_HEADER))
    # Mặt bàn ngoài WC (bàn bếp, bàn phấn…) chỉ ghi trong log, không liệt kê ở đây
    report += [u" | ".join(u"{}".format(v) for v in r) for r in rows
               if not r[7].startswith(u"Bỏ qua – không nằm trong phòng")]
    return report, preview_lines([b for b, _ in jobs], to_mm(level.Elevation))


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
            [s.strip() for s in (IN[1] or u"").split(u";") if s.strip()],
            (IN[2] or u"TẦNG 3"),
            IN[3],
            (IN[4] or u"").strip(),
            num(5, 900.0),
            (u"WC;vệ sinh" if IN[6] is None else IN[6]).split(u";"),
            num(7, 600.0),
            num(8, 1500.0),
            num(9, 650.0),
            num(10, 100.0),
            False if IN[11] is None else bool(IN[11]),
            True if IN[12] is None else bool(IN[12]),
        ))
    except StopReport as ex:
        OUT = [ex.lines, []]
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], []]
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with io.open(os.path.join(folder, "TaoLavaboTuCAD_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))), "w", encoding="utf-8-sig") as f:
                f.write(u"\n".join(OUT[0]))
        except Exception:
            pass
    note = force_rerun_next_time()
    if note:
        OUT[0].append(u"LƯU Ý: " + note)
