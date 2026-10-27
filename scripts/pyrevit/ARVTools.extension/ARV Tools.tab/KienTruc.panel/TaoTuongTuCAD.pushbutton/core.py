# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong ARV_TaoTuongTuCAD_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
# Bản Dynamo của nút pyRevit KienTruc.panel/TaoTuongTuCAD – mỗi chiều dày CAD một wall type (bảng IN[2]).
#
# Tạo tường kiến trúc từ mặt bằng tường xây (DWG đã Link/Import vào Revit):
#   1. Đọc đoạn thẳng (line, polyline, kể cả trong block) trên layer tường.
#   2. Ghép cặp hai nét song song cách nhau trong dải chiều dày → đường tim tường. Cặp gần nhau nhất trước;
#      không ghép hai nét có nét thứ ba nằm giữa (tường vẽ cả mặt thô lẫn mặt hoàn thiện không bị tạo đôi).
#   3. Gộp đoạn thẳng hàng cùng chiều dày bị ngắt tại chỗ giao tường.
#   4. Tường liền qua ô cửa: hai đoạn thẳng hàng cách nhau ≤ IN[7] mà trong khe có nét của layer cửa (IN[6])
#      → nối thành tường liền (chèn cửa sau). Khe không có nét cửa (lối đi mở) giữ nguyên. Khe ≤ 150 mm giữa hai
#      tường thẳng hàng khác chiều dày cũng được nối.
#   5. Kéo dài đầu tường tới tim tường không song song để nối góc L / chữ T (cả khi đầu tường hụt mặt tường giao
#      ≤ 50 mm). Bỏ mẩu tường nằm trọn trong thân tường khác (cặp nét giả ở nút giao), kéo dài lại; cắt chỗ hai
#      tường thẳng hàng chồng đầu nhau → không có tường đè.
#   6. Tạo tường theo wall type gán cho chiều dày CAD (IN[2]), chân / đỉnh theo level, Location Line = Core
#      Centerline (lõi tường trùng hai nét CAD, lớp trát chia đều hai bên). Chiều dày CAD = chiều dày LÕI (nét A-Wall
#      là mặt thô; nét trát nằm ở layer khác). Type trong IN[2] chưa có → nhân bản type mẫu IN[3], đổi lõi = chiều dày
#      CAD. Chiều dày không có trong IN[2] chỉ báo cáo. Bỏ qua tường chồng lên tường đã có.
# INPUT
#   IN[0] (str)   Một phần tên bản CAD (để trống = bản CAD duy nhất có layer khớp IN[1])
#   IN[1] (str)   Chuỗi lọc layer tường, nhiều chuỗi cách nhau bằng ';' (khớp chuỗi con, không phân biệt hoa thường)
#   IN[2] (str)   Bảng chiều dày lõi CAD (mm) = wall type (Basic), cách nhau bằng ';'
#                 VD "150=WB 15-150-15;100=WB 15-100-15". Khớp chiều dày ±2 mm.
#   IN[3] (str)   Wall type mẫu để nhân bản khi type trong IN[2] chưa có (VD "WB 15-220-15"); trống = không tự tạo
#   IN[4] (str)   Tên level chân tường
#   IN[5] (str)   Tên level đỉnh tường
#   IN[6] (str)   Chuỗi lọc layer cửa đi / cửa sổ, cách nhau bằng ';', khớp chuỗi con (VD "Door;Window;Glaz;Cửa" lấy cả
#                 A-Door, A-Window(s), A-Glaz, A-Cửa, 23-DOOR trong xref); trống = không nối
#   IN[7] (float) Ô cửa rộng tối đa được nối tường liền (mm), 0 = không nối
#   IN[8] (float) Top Offset so với level đỉnh (mm), VD -120 nếu xây tới đáy sàn dày 120
#   IN[9] (bool)  Dry-run: True = chỉ báo cáo + xem trước đường tim, không ghi vào mô hình (mặc định True)
# OUTPUT
#   OUT[0] (list[str]) Báo cáo: tóm tắt, layer đã dùng, đường dẫn log, rồi từng tường
#   OUT[1] (list[Line]) Đường tim tường sẽ tạo / đã tạo (xem trước trong Dynamo, đơn vị mm)

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
                                   BuiltInParameter, Level, Wall, WallType, WallKind, LocationCurve)
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = u"ARV - Tạo tường kiến trúc từ CAD"
SCRIPT_TAG = u"ARV_TaoTuongTuCAD_v1"
JOIN_TOL_MM = 1.0          # Sai số toạ độ / thẳng hàng
THICK_TOL_MM = 2.0         # Gộp chiều dày lệch nhỏ (109/110/111 → 110)
DUP_TOL_MM = 10.0          # Khoảng cách tim coi là trùng tường đã có
MIN_LENGTH_MM = 50.0       # Bỏ đoạn tường ngắn hơn
ANGLE_TOL = 1e-3           # Sai số song song (rad)
PAIR_RANGE_MM = (60.0, 400.0)  # Dải ghép cặp; chỉ tạo tường có chiều dày nằm trong bảng IN[2]
STEP_GAP_MM = 150.0        # Khe giữa hai tường thẳng hàng khác chiều dày → luôn nối
OPENING_MARGIN_MM = 50.0   # Nới vùng tìm nét cửa ra hai bên mặt tường
GRID_MM = 500.0            # Ô lưới tra cứu điểm nét cửa
ABSORB_TOL_MM = 5.0        # Sai số khi xét đoạn tường nằm trọn trong thân tường khác
INSIDE_TOL_MM = 10.0       # Sai số xét tường mỏng nằm trong thân tường dày (CAD vẽ lệch tim vài mm)
END_GAP_MM = 50.0         # Đầu tường hụt mặt tường giao ≤ giá trị này vẫn được kéo tới tim tường giao
DUP_LABEL = u"Bỏ qua – chồng lên tường cũ"


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


class Seg(object):
    """Đoạn CAD trong hệ toạ độ của nhóm song song: off = toạ độ pháp tuyến, [s0, s1] = hình chiếu."""

    def __init__(self, a, b, u, n):
        self.off = (dot(a, n) + dot(b, n)) / 2.0
        sa, sb = dot(a, u), dot(b, u)
        self.s0, self.s1 = min(sa, sb), max(sa, sb)
        self.free = [(self.s0, self.s1)]   # Phần chưa được dùng làm mặt tường


class WallPiece(object):
    def __init__(self, gid, u, n, off, s0, s1, thick):
        self.gid, self.u, self.n, self.off = gid, u, n, off
        self.s0, self.s1 = s0, s1
        self.thick = thick        # mm, đo từ CAD
        self.t = None             # mm nguyên, sau khi gộp chiều dày

    def point(self, s):
        return (self.u[0] * s + self.n[0] * self.off, self.u[1] * s + self.n[1] * self.off)


def canonical(a, b):
    """Hướng chuẩn hoá về góc [-tol, π - tol) để hai đường ngược chiều vẫn cùng nhóm."""
    u = unit(sub(b, a))
    ang = math.atan2(u[1], u[0])
    if ang < -ANGLE_TOL:
        ang += math.pi
        u = (-u[0], -u[1])
    if ang >= math.pi - ANGLE_TOL:
        ang -= math.pi
        u = (-u[0], -u[1])
    return u, ang


def parallel_groups(segs):
    data = sorted((canonical(a, b)[1], canonical(a, b)[0], a, b) for a, b in segs)
    groups, current = [], []
    for d in data:
        if current and d[0] - current[-1][0] > ANGLE_TOL:
            groups.append(current)
            current = []
        current.append(d)
    if current:
        groups.append(current)
    return groups


def clip(free, a, b):
    return [(max(x, a), min(y, b)) for x, y in free if min(y, b) > max(x, a)]


def intersect(f1, f2):
    result = []
    for x, y in f1:
        result.extend(clip(f2, x, y))
    return result


def subtract(free, a, b):
    out = []
    for x, y in free:
        if y <= a or x >= b:
            out.append((x, y))
            continue
        if x < a:
            out.append((x, a))
        if y > b:
            out.append((b, y))
    return out


def pair_group(gid, group, tmin, tmax):
    """Ghép cặp các nét trong một nhóm song song, ưu tiên cặp gần nhau nhất.
    Bỏ phần có nét thứ ba nằm giữa cặp (mặt thô + mặt hoàn thiện cùng layer → chỉ ghép cặp trong cùng)."""
    u = group[0][1]
    n = (-u[1], u[0])
    tol = JOIN_TOL_MM
    segs = sorted([Seg(a, b, u, n) for _, _, a, b in group], key=lambda s: s.off)

    cands = []
    for i in range(len(segs)):
        si = segs[i]
        for j in range(i + 1, len(segs)):
            sj = segs[j]
            d = sj.off - si.off
            if d > tmax + tol:
                break
            if d < tmin - tol:
                continue
            a, b = max(si.s0, sj.s0), min(si.s1, sj.s1)
            if b - a >= MIN_LENGTH_MM:
                cands.append((d, b - a, i, j, a, b))

    # Gần nhất trước; cùng khoảng cách thì ưu tiên đoạn chồng dài hơn
    cands.sort(key=lambda c: (round(c[0], 1), -c[1]))
    pieces = []
    for d, _, i, j, a, b in cands:
        si, sj = segs[i], segs[j]
        free = intersect(clip(si.free, a, b), sj.free)
        for k in range(i + 1, j):
            sk = segs[k]
            if sk.off - si.off > tol and sj.off - sk.off > tol:
                free = subtract(free, sk.s0, sk.s1)
        for x, y in free:
            if y - x < MIN_LENGTH_MM:
                continue
            si.free = subtract(si.free, x, y)
            sj.free = subtract(sj.free, x, y)
            pieces.append(WallPiece(gid, u, n, (si.off + sj.off) / 2.0, x, y, d))
    return pieces


def snap_thicknesses(pieces):
    """Gộp chiều dày lệch nhỏ về giá trị xuất hiện nhiều nhất trong cụm."""
    counts = {}
    for p in pieces:
        k = int(round(p.thick))
        counts[k] = counts.get(k, 0) + 1
    mapping, cluster = {}, []

    def close(cl):
        rep = max(cl, key=lambda k: counts[k])
        for k in cl:
            mapping[k] = rep

    for k in sorted(counts):
        if cluster and k - cluster[-1] > THICK_TOL_MM:
            close(cluster)
            cluster = []
        cluster.append(k)
    if cluster:
        close(cluster)
    for p in pieces:
        p.t = mapping[int(round(p.thick))]


def merge_collinear(pieces, max_gap):
    """Gộp các đoạn thẳng hàng, cùng chiều dày, cách nhau ≤ max_gap (mm)."""
    pieces = sorted(pieces, key=lambda p: (p.gid, p.t, p.off))
    lines, current = [], []
    for p in pieces:
        if current and (p.gid != current[-1].gid or p.t != current[-1].t
                        or p.off - current[-1].off > THICK_TOL_MM):
            lines.append(current)
            current = []
        current.append(p)
    if current:
        lines.append(current)

    merged = []
    for line in lines:
        line.sort(key=lambda p: p.s0)
        cur = line[0]
        for p in line[1:]:
            if p.s0 - cur.s1 <= max_gap:
                cur.s1 = max(cur.s1, p.s1)
            else:
                merged.append(cur)
                cur = p
        merged.append(cur)
    return merged


def extend_to_junctions(pieces):
    """Kéo dài đầu tường tới tim tường không song song gần nhất (nối góc L và chữ T)."""
    tol = JOIN_TOL_MM
    new_ends = []
    for w in pieces:
        ends = [w.s0, w.s1]
        for k, sign in ((0, -1.0), (1, 1.0)):
            e = w.point(ends[k])
            v = (w.u[0] * sign, w.u[1] * sign)
            best = None
            for o in pieces:
                if o is w:
                    continue
                sin = abs(cross(w.u, o.u))
                if sin < ANGLE_TOL:
                    continue
                denom = dot(v, o.n)
                if abs(denom) < ANGLE_TOL:
                    continue
                t = (o.off - dot(e, o.n)) / denom
                # Cho phép đầu tường hụt mặt tường giao tới END_GAP_MM (nét CAD vẽ hở vài mm)
                if t <= tol or t > o.thick / 2.0 / sin + END_GAP_MM:
                    continue
                s = dot((e[0] + v[0] * t, e[1] + v[1] * t), o.u)
                reach = w.thick / 2.0 / sin + tol
                if s < o.s0 - reach or s > o.s1 + reach:
                    continue
                if best is None or t < best:
                    best = t
            if best is not None:
                ends[k] += sign * best
        new_ends.append(ends)
    for w, (a, b) in zip(pieces, new_ends):
        w.s0, w.s1 = a, b


class PointGrid(object):
    """Tra cứu nhanh điểm nét cửa trong một hình chữ nhật xoay."""

    def __init__(self, points):
        self.cells = {}
        for x, y in points:
            self.cells.setdefault((int(math.floor(x / GRID_MM)), int(math.floor(y / GRID_MM))), []).append((x, y))

    def any_in(self, origin, u, n, s0, s1, h):
        """Có điểm nào với s0 < (p-origin)·u < s1 và |(p-origin)·n| ≤ h."""
        corners = [(origin[0] + u[0] * s + n[0] * t, origin[1] + u[1] * s + n[1] * t)
                   for s in (s0, s1) for t in (-h, h)]
        xs, ys = [c[0] for c in corners], [c[1] for c in corners]
        for i in range(int(math.floor(min(xs) / GRID_MM)), int(math.floor(max(xs) / GRID_MM)) + 1):
            for j in range(int(math.floor(min(ys) / GRID_MM)), int(math.floor(max(ys) / GRID_MM)) + 1):
                for p in self.cells.get((i, j), ()):
                    d = sub(p, origin)
                    if s0 < dot(d, u) < s1 and abs(dot(d, n)) <= h:
                        return True
        return False


def bridge_openings(pieces, grid, max_gap):
    """Nối hai đoạn tường thẳng hàng qua ô cửa (khe có nét cửa, ≤ max_gap) hoặc qua khe nhỏ đổi chiều dày.
    Cùng chiều dày, cùng tim → gộp một tường; khác → kéo hai đầu gặp nhau giữa khe. Trả về (số ô cửa, số khe nhỏ)."""
    n_open, n_step = 0, 0
    limit = max(max_gap, STEP_GAP_MM)
    changed = True
    while changed:
        changed = False
        for a in pieces:
            # Đoạn gần nhất phía sau đầu s1 của a, cùng phương, hai mặt tường còn chồng nhau theo chiều dày
            best = None
            for b in pieces:
                if b is a or b.gid != a.gid or abs(b.off - a.off) >= (a.thick + b.thick) / 2.0:
                    continue
                gap = b.s0 - a.s1
                if 0 < gap <= limit and (best is None or gap < best[0]):
                    best = (gap, b)
            if best is None:
                continue
            gap, b = best
            mid_off = (a.off + b.off) / 2.0
            origin = (a.n[0] * mid_off, a.n[1] * mid_off)
            h = max(a.thick, b.thick) / 2.0 + OPENING_MARGIN_MM
            is_door = (max_gap > 0 and grid is not None and gap <= max_gap
                       and grid.any_in(origin, a.u, a.n, a.s1 + JOIN_TOL_MM, b.s0 - JOIN_TOL_MM, h))
            is_step = gap <= STEP_GAP_MM and a.t != b.t
            if not (is_door or is_step):
                continue
            if a.t == b.t and abs(a.off - b.off) <= THICK_TOL_MM:
                a.s1 = max(a.s1, b.s1)
                pieces.remove(b)
            else:
                m = (a.s1 + b.s0) / 2.0
                a.s1, b.s0 = m, m
            if is_door:
                n_open += 1
            else:
                n_step += 1
            changed = True
            break
    return n_open, n_step


def inside_body(p, q, tol):
    """Đường tim của p nằm trọn trong thân (hình chữ nhật dài × dày) của q."""
    lq = q.s1 - q.s0
    for s in (p.s0, p.s1):
        pt = p.point(s)
        along = dot(pt, q.u) - q.s0
        across = dot(pt, q.n) - q.off
        if along < -tol or along > lq + tol or abs(across) > q.thick / 2.0 + tol:
            return False
    return True


def drop_absorbed(pieces, real=lambda p: True):
    """Bỏ đoạn tường nằm trọn trong thân một tường dài hơn (mẩu do đầu tường / mặt tường giao nhau ở nút T, góc L
    bị ghép nhầm thành cặp). Trả về số đoạn bỏ."""
    order = sorted(pieces, key=lambda p: p.s1 - p.s0)
    dropped = set()
    for p in order:
        lp = p.s1 - p.s0
        for q in pieces:
            if q is p or id(q) in dropped or q.s1 - q.s0 <= lp or not real(q):
                continue
            if inside_body(p, q, ABSORB_TOL_MM):
                dropped.add(id(p))
                break
    pieces[:] = [p for p in pieces if id(p) not in dropped]
    return len(dropped)


def trim_collinear_overlaps(pieces):
    """Hai tường song song, thân chồng nhau theo chiều dày, chồng nhau một đoạn ở đầu (≤ PAIR_RANGE max) → cắt
    tường ngắn hơn lùi về đúng đầu tường dài hơn. Trả về số chỗ cắt."""
    n = 0
    for a in pieces:
        for b in pieces:
            if b is a or b.gid != a.gid or abs(b.off - a.off) >= (a.thick + b.thick) / 2.0:
                continue
            if (b.s1 - b.s0) > (a.s1 - a.s0):
                continue   # chỉ cắt b khi b ngắn hơn (hoặc bằng) a
            ov = min(a.s1, b.s1) - max(a.s0, b.s0)
            if ov <= JOIN_TOL_MM or ov > PAIR_RANGE_MM[1]:
                continue
            if b.s0 < a.s1 < b.s1:
                b.s0 = a.s1
            elif b.s0 < a.s0 < b.s1:
                b.s1 = a.s0
            else:
                continue
            n += 1
    return n


def trim_inside_thicker(pieces, real=lambda p: True):
    """Tường mỏng (hoặc cùng dày) nằm trong thân một tường dày hơn trên một đoạn (VD tường 100 sát mặt tường 200,
    lệch tim 50 – do nét giữa tường dày bị ghép thành cặp riêng) → cắt bỏ đoạn đó khỏi tường mỏng, giữ tường dày.
    Cùng chiều dày thì giữ tường dài hơn. Trả về số đoạn bị cắt."""
    n = 0
    changed = True
    while changed:
        changed = False
        for p in pieces:
            for q in pieces:
                if q is p or q.gid != p.gid or not real(q):
                    continue   # chỉ cắt theo tường sẽ được tạo (cặp nét giả 350, 400… không cắt tường thật)
                if q.thick < p.thick - THICK_TOL_MM:
                    continue
                if abs(q.thick - p.thick) <= THICK_TOL_MM and (q.s1 - q.s0) < (p.s1 - p.s0):
                    continue   # cùng dày: chỉ cắt tường ngắn hơn
                # thân p nằm trong thân q theo chiều dày (nới INSIDE_TOL_MM: CAD hay vẽ lệch tim vài mm)
                if abs(p.off - q.off) + p.thick / 2.0 > q.thick / 2.0 + INSIDE_TOL_MM:
                    continue
                a, b = max(p.s0, q.s0), min(p.s1, q.s1)
                if b - a <= JOIN_TOL_MM:
                    continue
                rest = subtract([(p.s0, p.s1)], a, b)
                rest = [(x, y) for x, y in rest if y - x >= MIN_LENGTH_MM]
                pieces.remove(p)
                for x, y in rest:
                    np_ = WallPiece(p.gid, p.u, p.n, p.off, x, y, p.thick)
                    np_.t = p.t
                    pieces.append(np_)
                n += 1
                changed = True
                break
            if changed:
                break
    return n


def analyse(segs, opening_pts=None, max_gap=0.0, stats=None, thick_keys=None):
    """segs: [((x0, y0), (x1, y1))] mm; opening_pts: điểm nét cửa (mm); thick_keys: chiều dày sẽ tạo tường (bảng IN[2],
    None = mọi chiều dày). Trả về WallPiece đã gộp, nối góc, sắp xếp."""
    real = (lambda p: True) if thick_keys is None else (lambda p: map_thickness(p.t, thick_keys) is not None)
    pieces = []
    for gid, group in enumerate(parallel_groups(segs)):
        pieces.extend(pair_group(gid, group, PAIR_RANGE_MM[0], PAIR_RANGE_MM[1]))
    if not pieces:
        return []
    snap_thicknesses(pieces)
    # Luôn nối qua chỗ giao tường (khe ≤ chiều dày lớn nhất)
    pieces = merge_collinear(pieces, PAIR_RANGE_MM[1] + JOIN_TOL_MM)
    n_open, n_step = bridge_openings(pieces, PointGrid(opening_pts) if opening_pts else None, max_gap)
    # Kéo dài nối góc, bỏ mẩu nằm trong thân tường khác, kéo dài lần nữa (đầu tường trước bị mẩu chặn → tới tim
    # tường thật)
    extend_to_junctions(pieces)
    n_drop = drop_absorbed(pieces, real)
    if n_drop:
        extend_to_junctions(pieces)
    n_inside = trim_inside_thicker(pieces, real)
    n_trim = trim_collinear_overlaps(pieces)
    if stats is not None:
        stats["openings"], stats["steps"], stats["absorbed"], stats["trimmed"] = n_open, n_step, n_drop, n_trim
        stats["inside"] = n_inside
    pieces = [p for p in pieces if p.s1 - p.s0 >= MIN_LENGTH_MM]
    pieces.sort(key=lambda p: (p.t, round(p.point(p.s0)[1]), round(p.point(p.s0)[0])))
    return pieces


def overlaps_existing(p0, p1, existing):
    """Tường mới trùng tim và chồng > 50% chiều dài tường mới HOẶC tường cũ (tường liền qua cửa chồng lên các
    đoạn cũ bị ngắt ở cửa cũng bị nhận ra). existing: [(a, b, id)] mm."""
    up = unit(sub(p1, p0))
    for a, b, eid in existing:
        d = sub(b, a)
        length = math.hypot(d[0], d[1])
        if length < DUP_TOL_MM:
            continue
        ue = (d[0] / length, d[1] / length)
        if abs(cross(ue, up)) > ANGLE_TOL:
            continue
        ne = (-ue[1], ue[0])
        if abs(dot(sub(p0, a), ne)) > DUP_TOL_MM:
            continue
        s_a, s_b = sorted([dot(sub(p0, a), ue), dot(sub(p1, a), ue)])
        if min(s_b, length) - max(s_a, 0.0) > 0.5 * min(s_b - s_a, length):
            return eid
    return None


def parse_type_map(text):
    """'150=Tường 150;100=Tường 100' → {150: 'Tường 150', 100: 'Tường 100'}; tên trống giữ '' (chưa gán)."""
    result = {}
    for item in (text or u"").split(u";"):
        if not item.strip():
            continue
        if u"=" not in item:
            raise Exception(u"Ô IN[2] sai định dạng ở '{}'. Nhập dạng <dày>=<wall type>;..., "
                            u"VD 150=Tường 150;100=Tường 100.".format(item.strip()))
        k, v = item.split(u"=", 1)
        try:
            t = int(round(float(k.strip())))
        except ValueError:
            raise Exception(u"Ô IN[2]: chiều dày '{}' không phải số.".format(k.strip()))
        result[t] = v.strip()
    if not result:
        raise Exception(u"Ô IN[2] trống. Nhập dạng <dày>=<wall type>;..., VD 150=Tường 150;100=Tường 100.")
    return result


def map_thickness(t, type_map):
    """Chiều dày CAD → khoá trong bảng IN[2] (±THICK_TOL_MM), None nếu không có."""
    for k in type_map:
        if abs(k - t) <= THICK_TOL_MM:
            return k
    return None


def norm(s):
    return unicodedata.normalize("NFC", (s or u"")).strip()


def fmt(p):
    return u"({:.0f}, {:.0f})".format(p[0], p[1])


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


def model_role(document):
    # Trường Bộ môn (Role) theo tên file ISO 19650: PRJ-ARV-T1-ZZ-M3-A-0001
    parts = (document.Title or "").split("-")
    return parts[5].upper() if len(parts) >= 7 else None


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
    # NFC: tên layer tiếng Việt (VD "A-Cửa") có thể ở dạng dựng sẵn hoặc tổ hợp
    return set(l for l in all_layers if any(norm(f).lower() in norm(l).lower() for f in filters))


def pick_cad(cad_filter, filters):
    """Chọn bản CAD theo tên; để trống thì lấy bản CAD duy nhất có layer khớp. Trả về (cad, tên, objects, layers)."""
    found = []
    for inst in FilteredElementCollector(doc).OfClass(ImportInstance).ToElements():
        name = get_name(doc.GetElement(inst.GetTypeId()))
        if cad_filter and cad_filter.lower() not in name.lower():
            continue
        objects = cad_objects(inst)
        all_layers = sorted(set(l for l in (layer_of(o) for o in objects) if l))
        found.append((inst, name, objects, all_layers, match_layers(all_layers, filters)))
    hits = [f for f in found if f[4]]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        lines = [u"DỪNG: không có bản CAD{} nào có layer chứa '{}'.".format(
            u" khớp '{}'".format(cad_filter) if cad_filter else u"", u"; ".join(filters))]
        for _, name, _, all_layers, _ in found:
            lines.append(u"Layer của '{}': {}".format(name, u", ".join(all_layers)))
        raise StopReport(lines)
    raise StopReport([u"DỪNG: {} bản CAD có layer khớp – nhập tên bản CAD vào ô IN[0]: {}".format(
        len(hits), u", ".join(h[1] for h in hits))])


class StopReport(Exception):
    def __init__(self, lines):
        Exception.__init__(self, lines[0])
        self.lines = lines


def find_level(name):
    levels = list(FilteredElementCollector(doc).OfClass(Level).ToElements())
    for l in levels:
        if norm(l.Name) == norm(name):
            return l
    raise StopReport([u"DỪNG: không có level '{}'. Các level: {}".format(
        name, u", ".join(l.Name for l in sorted(levels, key=lambda x: x.Elevation)))])


def core_range(wall_type):
    """(chỉ số lớp lõi đầu, cuối) của type Basic, None nếu không có cấu trúc lớp."""
    cs = wall_type.GetCompoundStructure()
    if cs is None or cs.GetFirstCoreLayerIndex() < 0:
        return None
    return cs.GetFirstCoreLayerIndex(), cs.GetLastCoreLayerIndex()


def core_width_mm(wall_type):
    rng = core_range(wall_type)
    if rng is None:
        return to_mm(wall_type.Width)
    cs = wall_type.GetCompoundStructure()
    return to_mm(sum(cs.GetLayerWidth(i) for i in range(rng[0], rng[1] + 1)))


def resolve_wall_types(type_map, template_name):
    """{dày: tên} → ({dày: WallType | None}, {dày: tên type sẽ nhân bản}, type mẫu).
    Tên trống = chưa gán (None). Tên chưa có + có type mẫu → nhân bản; không có mẫu → dừng, liệt kê type."""
    types = [t for t in FilteredElementCollector(doc).OfClass(WallType).ToElements() if t.Kind == WallKind.Basic]
    by_name = dict((norm(get_name(t)), t) for t in types)
    template = None
    if template_name:
        template = by_name.get(norm(template_name))
        if template is None:
            raise StopReport([u"DỪNG: không có wall type mẫu '{}' (IN[3]).".format(template_name)])
        rng = core_range(template)
        if rng is None or rng[0] != rng[1]:
            raise StopReport([u"DỪNG: type mẫu '{}' phải có đúng một lớp lõi để đổi chiều dày.".format(
                template_name)])
    result, to_create, missing = {}, {}, []
    for k, name in type_map.items():
        if not name:
            result[k] = None
        elif norm(name) in by_name:
            result[k] = by_name[norm(name)]
        elif template is not None:
            result[k] = None
            to_create[k] = name
        else:
            missing.append(u"{}={}".format(k, name))
    if missing:
        raise StopReport([u"DỪNG: không có wall type Basic: {} và ô IN[3] (type mẫu) trống. Các wall type (dày mm): {}"
                          .format(u"; ".join(missing), u", ".join(sorted(
                              u"{} ({:.0f})".format(get_name(t), to_mm(t.Width)) for t in types)))])
    return result, to_create, template


def duplicate_with_core(template, name, core_mm):
    """Nhân bản type mẫu, đặt lớp lõi = core_mm (lớp hoàn thiện giữ nguyên). Gọi trong Transaction."""
    new_type = template.Duplicate(name)
    cs = new_type.GetCompoundStructure()
    idx = cs.GetFirstCoreLayerIndex()
    cs.SetLayerWidth(idx, from_mm(core_mm))
    new_type.SetCompoundStructure(cs)
    return new_type


def read_segments(objects, layers):
    """Đoạn thẳng (mm, Z=0) trên các layer; đếm cung tròn bỏ qua."""
    segs, arcs = [], 0
    for obj in objects:
        if layer_of(obj) not in layers:
            continue
        if isinstance(obj, Line):
            pts = [obj.GetEndPoint(0), obj.GetEndPoint(1)]
        elif isinstance(obj, PolyLine):
            pts = list(obj.GetCoordinates())
        elif isinstance(obj, Arc):
            arcs += 1
            continue
        else:
            continue
        pts = [(to_mm(p.X), to_mm(p.Y)) for p in pts]
        for a, b in zip(pts[:-1], pts[1:]):
            if math.hypot(b[0] - a[0], b[1] - a[1]) > JOIN_TOL_MM:
                segs.append((a, b))
    return segs, arcs


def read_points(objects, layers):
    """Đỉnh / đầu mút (mm) của mọi nét trên các layer cửa."""
    pts = []
    for obj in objects:
        if layer_of(obj) not in layers:
            continue
        if isinstance(obj, PolyLine):
            raw = list(obj.GetCoordinates())
        else:
            try:
                if not obj.IsBound:
                    continue
                raw = [obj.GetEndPoint(0), obj.GetEndPoint(1)]
            except Exception:
                continue
        pts.extend((to_mm(p.X), to_mm(p.Y)) for p in raw)
    return pts


def existing_walls(level):
    result = []
    for wl in FilteredElementCollector(doc).OfClass(Wall).ToElements():
        loc = wl.Location
        if wl.LevelId == level.Id and isinstance(loc, LocationCurve) and isinstance(loc.Curve, Line):
            a, b = loc.Curve.GetEndPoint(0), loc.Curve.GetEndPoint(1)
            result.append(((to_mm(a.X), to_mm(a.Y)), (to_mm(b.X), to_mm(b.Y)), wl.Id.Value))
    return result


def preview_lines(pairs, z_mm):
    try:
        clr.AddReference("ProtoGeometry")
        from Autodesk.DesignScript.Geometry import Point as DSPoint, Line as DSLine
        return [DSLine.ByStartPointEndPoint(DSPoint.ByCoordinates(a[0], a[1], z_mm),
                                            DSPoint.ByCoordinates(b[0], b[1], z_mm)) for a, b in pairs]
    except Exception:
        return []


LOG_HEADER = [u"STT", u"Điểm đầu (mm)", u"Điểm cuối (mm)", u"Dày CAD (mm)", u"Dài (mm)", u"Wall type",
              u"Kết quả", u"ElementId", u"Giá trị cũ", u"Giá trị mới"]


def write_log(rows, source, dry_run):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoTuongTuCAD_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    # CSV UTF-8 có BOM để Excel đọc đúng tiếng Việt
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


def main(cad_filter, filters, type_map, template_name, base_name, top_name, door_filters, max_gap, top_offset_mm,
         dry_run):
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."], []
    report = []
    if model_role(doc) == "S":
        report.append(u"CẢNH BÁO: đây có vẻ là mô hình Kết cấu (S). Tường kiến trúc thuộc mô hình Kiến trúc (A).")

    cad, cad_name, objects, all_layers, layers = pick_cad(cad_filter, filters)
    door_layers = match_layers(all_layers, door_filters) - layers if door_filters else set()
    if door_filters and max_gap > 0 and not door_layers:
        report.append(u"CẢNH BÁO: không có layer cửa nào chứa '{}' → không nối tường qua ô cửa.".format(
            u"; ".join(door_filters)))
    wtypes, to_create, template = resolve_wall_types(type_map, template_name)
    base_level = find_level(base_name)
    top_level = find_level(top_name)
    top_offset = from_mm(top_offset_mm)
    height = top_level.Elevation + top_offset - base_level.Elevation
    if height <= 0:
        raise StopReport([u"DỪNG: chiều cao tường ≤ 0 – level đỉnh '{}' phải cao hơn level chân '{}'.".format(
            top_name, base_name)])

    segs, arcs = read_segments(objects, layers)
    door_pts = read_points(objects, door_layers) if door_layers and max_gap > 0 else []
    stats = {}
    pieces = analyse(segs, door_pts, max_gap, stats, type_map)
    existing = existing_walls(base_level)
    z = base_level.Elevation
    z_mm = to_mm(z)

    rows, jobs, unmapped, unassigned, used_new = [], [], {}, {}, set()
    for idx, p in enumerate(pieces, 1):
        p0, p1 = p.point(p.s0), p.point(p.s1)
        key = map_thickness(p.t, type_map)
        wtype = wtypes.get(key) if key is not None else None
        if wtype is not None:
            type_name = get_name(wtype)
        elif key in to_create:
            type_name = to_create[key] + u" (mới)"
        else:
            type_name = u"—"
        row = [idx, fmt(p0), fmt(p1), p.t, u"{:.0f}".format(p.s1 - p.s0), type_name, u"", u"", u"—", type_name]
        dup = overlaps_existing(p0, p1, existing)
        if key is None:
            row[6] = u"Bỏ qua – dày {} mm không có trong bảng IN[2]".format(p.t)
            unmapped[p.t] = unmapped.get(p.t, 0) + 1
        elif wtype is None and key not in to_create:
            row[6] = u"Bỏ qua – chưa gán wall type cho dày {} mm".format(key)
            unassigned[key] = unassigned.get(key, 0) + 1
        elif dup is not None:
            row[6] = DUP_LABEL
            row[7] = dup
        else:
            core = key if wtype is None else int(round(core_width_mm(wtype)))
            note = u"" if abs(core - p.t) <= THICK_TOL_MM else u" (lõi type {} ≠ CAD {})".format(core, p.t)
            row[6] = (u"Sẽ tạo" if dry_run else u"Chờ tạo") + note
            jobs.append((p0, p1, key, len(rows)))
            if wtype is None:
                used_new.add(key)
        rows.append(row)

    if not dry_run and jobs:
        TransactionManager.Instance.ForceCloseTransaction()
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        try:
            for k in sorted(used_new):
                wtypes[k] = duplicate_with_core(template, to_create[k], k)
            for p0, p1, key, ri in jobs:
                line = Line.CreateBound(XYZ(from_mm(p0[0]), from_mm(p0[1]), z), XYZ(from_mm(p1[0]), from_mm(p1[1]), z))
                wall = Wall.Create(doc, line, wtypes[key].Id, base_level.Id, height, 0.0, False, False)
                wall.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET).Set(0.0)
                wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE).Set(top_level.Id)
                wall.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET).Set(top_offset)
                # Location Line = Core Centerline (1), rồi đặt lại đường định vị để tim lõi trùng tim cặp nét CAD
                wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(1)
                wall.Location.Curve = line
                rows[ri][6] = rows[ri][6].replace(u"Chờ tạo", u"Đã tạo")
                rows[ri][7] = wall.Id.Value
            tx.Commit()
        except Exception as ex:
            tx.RollBack()
            return [u"LỖI khi tạo tường, mọi thay đổi đã được hoàn tác: {}".format(ex)], []

    counts = {}
    for p in pieces:
        counts[p.t] = counts.get(p.t, 0) + 1
    report.append(u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run
                                     else u"ĐÃ THỰC HIỆN"))
    report.append(u"CAD: {} – layer: {}".format(cad_name, u"; ".join(sorted(layers))))
    report.append(u"Level {} → {} (Top Offset {:.0f} mm)".format(base_level.Name, top_level.Name, top_offset_mm))
    report.append(u"Tường liền qua ô cửa ≤ {:.0f} mm: {} ô (layer cửa: {}; {} điểm nét cửa); nối khe đổi chiều dày "
                  u"≤ {:.0f} mm: {} chỗ".format(max_gap, stats.get("openings", 0),
                                                u"; ".join(sorted(door_layers)) or u"không có", len(door_pts),
                                                STEP_GAP_MM, stats.get("steps", 0)))
    report.append(u"Chống đè: bỏ {} mẩu nằm trong thân tường khác (nút T / góc L), cắt {} đoạn tường mỏng nằm trong "
                  u"thân tường dày, cắt {} chỗ hai tường thẳng hàng chồng đầu".format(
                      stats.get("absorbed", 0), stats.get("inside", 0), stats.get("trimmed", 0)))
    def type_label(k):
        w = wtypes.get(k)
        if w is not None and k not in used_new:
            return u"{} (lõi {:.0f}, tổng {:.0f})".format(get_name(w), core_width_mm(w), to_mm(w.Width))
        if k in to_create:
            outer = to_mm(template.Width) - core_width_mm(template)
            state = (u"không có tường dùng, không tạo" if k not in used_new
                     else u"SẼ NHÂN BẢN" if dry_run else u"ĐÃ NHÂN BẢN")
            return u"{} – {} từ '{}' (lõi {}, tổng {:.0f})".format(
                to_create[k], state, get_name(template), k, k + outer)
        return u"CHƯA GÁN"
    report.append(u"Bảng dày lõi → wall type (Location Line = Core Centerline): " + u"; ".join(
        u"{} → {}".format(k, type_label(k)) for k in sorted(type_map)))
    report.append(u"Đoạn CAD đã đọc: {} – tường tìm được: {} – {}: {} – trùng tường cũ: {}".format(
        len(segs), len(pieces), u"sẽ tạo" if dry_run else u"đã tạo", len(jobs),
        sum(1 for r in rows if r[6] == DUP_LABEL)))
    if any(r[6] == DUP_LABEL for r in rows):
        report.append(u"LƯU Ý: tường chồng lên tường cũ không được tạo. Muốn dựng lại (VD tường liền qua cửa) → "
                      u"xoá các tường cũ có Id trong log trước rồi Run lại.")
    report.append(u"Chiều dày tìm được (mm × số đoạn): " + u", ".join(
        u"{} × {}".format(t, counts[t]) for t in sorted(counts)))
    if unassigned:
        report.append(u"Chưa gán wall type, không tạo: " + u", ".join(
            u"{} mm × {}".format(t, unassigned[t]) for t in sorted(unassigned)) + u" – điền tên type vào IN[2].")
    if unmapped:
        report.append(u"Không có trong bảng IN[2], không tạo: " + u", ".join(
            u"{} mm × {}".format(t, unmapped[t]) for t in sorted(unmapped)) + u" – thêm vào IN[2] nếu là tường thật.")
    if arcs:
        report.append(u"Bỏ qua {} cung tròn (tường cong cần vẽ tay).".format(arcs))
    try:
        report.append(u"Log: " + write_log(rows, cad_name, dry_run))
    except Exception as ex:
        report.append(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        report.append(u"Kiểm tra đường tim xanh trong Dynamo + log. Đúng thì đổi Dry-run = False và Run lại. "
                      u"Undo bằng mục \"{}\".".format(TRANSACTION_NAME))
    report.append(u" | ".join(LOG_HEADER[:8]))
    report += [u" | ".join(u"{}".format(v) for v in r[:8]) for r in rows]
    return report, preview_lines([(p0, p1) for p0, p1, _, _ in jobs], z_mm)


def force_rerun_next_time():
    """Dynamo chỉ chạy lại node khi có đầu vào đổi → sau Undo trong Revit, bấm Run lần 2 không có tác dụng.
    Đánh dấu node này 'đã sửa' để lần Run sau luôn chạy lại. Chỉ làm ở chế độ Manual (Automatic sẽ lặp vô hạn)."""
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
        # CPython3 (pythonnet) có thể trả enum dưới dạng số (Manual = 0) → so cả giá trị lẫn tên
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
            [s.strip() for s in (IN[1] or u"A-Wall").split(u";") if s.strip()],
            parse_type_map(IN[2] or u"150=;100=;200="),
            (IN[3] or u"").strip(),
            (IN[4] or u"TẦNG 2"),
            (IN[5] or u"TẦNG 3"),
            [s.strip() for s in (IN[6] or u"").split(u";") if s.strip()],
            float(IN[7] or 0.0),
            float(IN[8] or 0.0),
            True if IN[9] is None else bool(IN[9]),
        ))
    except StopReport as ex:
        OUT = [ex.lines, []]
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], []]
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with io.open(os.path.join(folder, "TaoTuongTuCAD_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))), "w", encoding="utf-8-sig") as f:
                f.write(u"\n".join(OUT[0]))
        except Exception:
            pass
    note = force_rerun_next_time()
    if note:
        OUT[0].append(u"LƯU Ý: " + note)
