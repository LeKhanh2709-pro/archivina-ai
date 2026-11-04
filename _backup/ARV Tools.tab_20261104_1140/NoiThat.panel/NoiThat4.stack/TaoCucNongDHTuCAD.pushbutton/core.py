# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong 20. ARV_TaoCucNongDHTuCAD_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Đặt cục nóng điều hòa (Mechanical Equipment) ở logia từ mặt bằng DWG đã Link, cùng khuôn với tool 19 máy giặt:
#   1. Cục nóng trên CAD (đo trên G19 TẦNG 3 2026-10-31, DWG TDH_LINK-REVIT: 17 block "Mini-VRF - 4-6HP (12.0-16.0kW) 1250" layer
#      AUDIT_D_260526144445-144, mỗi căn một cục ở logia LG1) = HÌNH CHỮ NHẬT 1100 × 500 chứa MŨI TÊN hướng thổi. Revit gộp nét
#      block vào một GeometryInstance nên không dùng tên block; nét layer 0 vào Revit mang layer của block (file chẩn đoán
#      2026-10-31 09:36: hình chữ nhật = PolyLine 5 đỉnh khép kín). IN[1] có chuỗi = chỉ layer chứa chuỗi đó; trống = dò mọi
#      layer, chỉ nhận hình có mũi tên.
#   2. Hướng: mặt trước = hướng mũi tên trên CAD, cạnh dài đối diện là lưng. Mũi tên trên CAD không đồng nhất giữa các căn
#      (có căn thổi ra lan can, có căn thổi vào logia, CH10 thổi vào tường cuối logia): giữ theo CAD, thổi vào tường thì báo
#      "cần soát". Không thấy mũi tên → cạnh dài gần tường / biên Room nhất làm lưng, báo "cần soát".
#   3. Room chứa tâm cục nóng phải có tên chứa một chuỗi trong IN[4] (mặc định "logia;lô gia"; trống = mọi phòng).
#   4. Lưng áp mặt nhô ra phòng nhất trong biên Room (Finish) và mặt tường Revit ngang tầm cục nóng (len chân tường, tường thấp
#      dưới đáy cục không tính), cách lưng CAD ≤ IN[7]. Mặc định 50, nhỏ hơn máy giặt: CAD cố ý để hở 100 mm ở vài căn (CH05, 08, 09, 13), snap xa hơn sẽ dời sai.
#      Không có mặt nào → giữ theo CAD (cục đứng tự do sau lưng, không phải lỗi).
#   5. Dọc tường: có mặt bên cách cạnh CAD ≤ IN[8] thì áp mặt đó; hai bên đều có thì đặt giữa; không có thì giữ tâm CAD.
#      Hốc hẹp hơn 1100 (CH01, 04, 14, 17: 1085; CH10: 1035) → đặt giữa hoặc áp mặt bên có tường, khung type lấn ra ngoài, báo "lòi khỏi Room".
#   6. Cao độ: Elevation from Level = IN[11] (mặc định 1500 mm so với LEVEL, không phải so với sàn logia), mọi cục như nhau.
#   7. Type: chọn ở IN[3], mặc định "AV_MT_cuc nong dieu hoa loai dai1 : AV_Cuc nong DH 3" (Mechanical Equipment, đặt theo
#      level, khung −550…550 × −476…0, cao 880). Giả định gốc ở giữa mép lưng, mặt trước về −Y như family máy giặt, chưa xem
#      được hình family: quay ngược → IN[9] = True. Comments = "ARV-TaoCucNongDHTuCAD". Cục của tool đã có mà lệch / sai
#      hướng / sai cao độ / khác type → sửa tại chỗ; cục cùng family người dùng tự đặt → bỏ qua.
# INPUT
#   IN[0] (str)   Một phần tên bản CAD (để trống = bản CAD duy nhất trong mô hình / có layer khớp IN[1])
#   IN[1] (str)   Lọc layer, nhiều chuỗi cách ';' (khớp chuỗi con), VD "AUDIT_D_260526144445-144"; trống = dò mọi layer
#   IN[2] (str)   Tên level đặt cục nóng, VD "TẦNG 3"
#   IN[3] (FamilyType | str) Type cục nóng (node Family Types, hoặc "AV_MT_cuc nong dieu hoa loai dai1 : AV_Cuc nong DH 3")
#   IN[4] (str)   Tên Room chứa cục nóng, nhiều chuỗi cách ';', VD "logia;lô gia" (trống = mọi phòng)
#   IN[5] (float) Cạnh dài hình chữ nhật CAD tối thiểu (mm), VD 1000
#   IN[6] (float) Cạnh dài hình chữ nhật CAD tối đa (mm), VD 1200
#   IN[7] (float) Lưng CAD cách mặt tường tối đa để áp tường (mm), VD 50
#   IN[8] (float) Cạnh bên CAD cách mặt bên tối đa để áp mặt bên (mm), VD 50
#   IN[9] (bool)  Đảo hướng: True nếu cục nóng quay lưng về phía mũi tên CAD (mặc định False)
#   IN[10] (bool) Dry-run: True = đặt thử, báo cáo rồi hoàn tác, không ghi vào mô hình (mặc định True)
#   IN[11] (float) Cao độ cục nóng so với level (mm), VD 1500
# OUTPUT
#   OUT[0] (list[str])  Báo cáo: tóm tắt, đường dẫn log, rồi từng cục nóng
#   OUT[1] (list[Line]) Xem trước: hình chữ nhật CAD, khung cục nóng sẽ đặt, đoạn hướng mặt trước (mm)

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
                                   FamilyPlacementType,
                                   ElementTransformUtils, SpatialElementBoundaryOptions,
                                   SpatialElementBoundaryLocation, ElementId, Solid, ViewDetailLevel,
                                   WorksharingUtils, CheckoutStatus)
    from Autodesk.Revit.DB.Structure import StructuralType
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = u"ARV - Tạo cục nóng điều hòa từ CAD"
SCRIPT_TAG = u"ARV_TaoCucNongDHTuCAD_v1"
COMMENT_TAG = u"ARV-TaoCucNongDHTuCAD"
MAX_EDGE_MM = 3000.0             # Nét dài hơn không thể là nét cục nóng – bỏ khi đọc CAD
SNAP_MM = 1.0                    # Đầu mút cách nhau ≤ chừng này coi là nối nhau
MAX_LOOP_EDGES = 64
RIGHT_COS = 0.02                 # Góc vuông: |cos| ≤ chừng này (lệch ≤ ~1°)
SHORT_MIN = 0.3                  # Cạnh ngắn / cạnh dài của hình chữ nhật (G19: 500 / 1100)
SHORT_MAX = 0.6
ARROW_MIN_MM = 20.0              # Nét chéo đầu mũi tên dài trong khoảng này (G19: 32)
ARROW_MAX_MM = 60.0
ARROW_COS = (0.3, 0.9)           # |cos| giữa nét chéo mũi tên và cạnh dài
ARROW_SPAN_MM = 100.0            # Mũi tên nằm cách tâm hình chữ nhật dọc cạnh dài tối đa (G19: 25)
PARALLEL_COS = 0.995             # Mặt song song / vuông góc: |cos| ≥ chừng này
SAME_MM = 100.0                  # Hai hình chữ nhật có tâm cách ≤ chừng này = cùng một ký hiệu
EXIST_TOL_MM = 500.0             # Cục cùng family có tâm cách tâm CAD ≤ chừng này → đã có
BODY_MAX_MM = 1500.0             # Khối đặc của family lớn hơn (trên mặt bằng) = vùng thông thủy – bỏ
TOP_MM = 1000.0                  # Tường có chân cao hơn đáy cục chừng này không vướng cục nóng (cao 880)
ROOM_INSET_MM = 5.0              # Kiểm tra cục nóng nằm trong Room: thu khung vào chừng này
BLOW_MM = 150.0                  # Tường trước mũi tên trong khoảng này = thổi vào tường


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


def rotate(p, ang, c):
    """Xoay điểm p quanh c một góc ang (rad, ngược chiều kim đồng hồ)."""
    ca, sa = math.cos(ang), math.sin(ang)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * ca - y * sa, c[1] + x * sa + y * ca)


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


def find_loops(items):
    """Vòng kín từ nét thẳng: polyline tự khép (hoặc polyline 4 đỉnh – Revit có thể bỏ điểm khép), hoặc chuỗi nét nối
    đầu mút mà mọi nút có đúng 2 nét. Trả về [điểm]. (Như tool sen tắm – dùng để tìm vách kính.)"""
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


def inside_loops(p, loops):
    """Điểm trong vùng giới hạn bởi các vòng biên (chẵn lẻ – lỗ trong Room tự trừ)."""
    c = False
    for pts in loops:
        for i in range(len(pts)):
            (x1, y1), (x2, y2) = pts[i - 1], pts[i]
            if (y1 > p[1]) != (y2 > p[1]) and p[0] < x1 + (p[1] - y1) * (x2 - x1) / (y2 - y1):
                c = not c
    return c

class Condenser(object):
    """Cục nóng nhận diện được trên CAD + cục sẽ đặt. Hệ trục riêng: gốc = giữa lưng CAD, dir = hướng mặt trước (theo
    mũi tên), u = dọc tường; s = toạ độ dọc tường, d = toạ độ về phía mũi tên (lưng CAD d = 0, mặt trước d = depth)."""

    def __init__(self, c, d, width, depth, corners, arrow):
        self.c, self.width, self.depth, self.corners, self.arrow = c, width, depth, corners, arrow
        self.set_dir(d)
        self.mount_d = 0.0       # mặt dựa (d)
        self.sides = []          # [(s mặt tường bên, phía −1 / +1)]
        self.final = None        # khung cục nóng sau khi căn (s0, s1, d0, d1)
        self.room = u""
        self.number = u""
        self.status = u""
        self.type_name = u""
        self.eid = u""
        self.note = u""
        self.dups = []

    def set_dir(self, d):
        self.dir = d
        self.u = (-d[1], d[0])
        self.back = (self.c[0] - d[0] * self.depth / 2.0, self.c[1] - d[1] * self.depth / 2.0)

    def local(self, p):
        q = sub(p, self.back)
        return dot(q, self.u), dot(q, self.dir)

    def world(self, s, d):
        return (self.back[0] + self.u[0] * s + self.dir[0] * d, self.back[1] + self.u[1] * s + self.dir[1] * d)

    def target_s(self, body_width):
        """Tâm cục nóng dọc tường: áp mặt bên; hai bên đều có → giữa; không có → tâm CAD."""
        if len(self.sides) >= 2:
            return sum(s for s, _ in self.sides) / len(self.sides)
        if self.sides:
            return self.sides[0][0] - self.sides[0][1] * body_width / 2.0
        return 0.0

def arrow_front(items, cen, along, across, depth):
    """Hướng mũi tên: các nét chéo đầu mũi tên quanh tâm hình chữ nhật, hai bên trục mũi tên, chụm về phía mũi. None nếu không có."""
    parts = []
    for it in items:
        if it.curved:
            continue
        for k in range(1, len(it.pts)):
            a, b = it.pts[k - 1], it.pts[k]
            ln = math.hypot(*sub(b, a))
            if not (ARROW_MIN_MM <= ln <= ARROW_MAX_MM):
                continue
            if not (ARROW_COS[0] <= abs(dot(sub(b, a), along)) / ln <= ARROW_COS[1]):
                continue
            sa, da = dot(sub(a, cen), along), dot(sub(a, cen), across)
            sb, db = dot(sub(b, cen), along), dot(sub(b, cen), across)
            if max(abs(sa), abs(sb)) <= ARROW_SPAN_MM and max(abs(da), abs(db)) <= depth / 2.0:
                parts.append((sa, da, sb, db))
    if len(parts) < 2:
        return None
    axis = sum(p[0] + p[2] for p in parts) / (2.0 * len(parts))
    if not (any(p[0] + p[2] > 2.0 * axis for p in parts) and any(p[0] + p[2] < 2.0 * axis for p in parts)):
        return None
    vote = 0.0
    for sa, da, sb, db in parts:
        vote += (db - da) if abs(sb - axis) < abs(sa - axis) else (da - db)
    if abs(vote) < 1.0:
        return None
    return across if vote > 0 else (-across[0], -across[1])


def make_unit(c, items):
    """Cục nóng từ 4 góc hình chữ nhật + các nét để tìm mũi tên."""
    l1, l2 = math.hypot(*sub(c[1], c[0])), math.hypot(*sub(c[2], c[1]))
    cen = ((c[0][0] + c[2][0]) / 2.0, (c[0][1] + c[2][1]) / 2.0)
    e1, e2 = unit(sub(c[1], c[0])), unit(sub(c[2], c[1]))
    along, across, length, depth = (e1, e2, l1, l2) if l1 >= l2 else (e2, e1, l2, l1)
    front = arrow_front(items, cen, along, across, depth)
    return Condenser(cen, front or across, length, depth, c, front is not None)


def find_units(items, min_long, max_long, stats=None, need_arrow=False):
    """Hình chữ nhật cạnh dài min_long–max_long, tỉ lệ SHORT_MIN–MAX; need_arrow = chỉ nhận hình có mũi tên (dò mọi layer)."""
    rectangles = arrows = 0
    result = []
    for c in (rect_corners(pts) for pts in find_loops(items)):
        if c is None:
            continue
        l1, l2 = math.hypot(*sub(c[1], c[0])), math.hypot(*sub(c[2], c[1]))
        long_side, short_side = max(l1, l2), min(l1, l2)
        if not (min_long <= long_side <= max_long and SHORT_MIN <= short_side / long_side <= SHORT_MAX):
            continue
        u = make_unit(c, items)
        if any(math.hypot(*sub(u.c, r.c)) <= SAME_MM for r in result):
            continue
        rectangles += 1
        arrows += 1 if u.arrow else 0
        if u.arrow or not need_arrow:
            result.append(u)
    if stats is not None:
        stats.update(rects=rectangles, arrows=arrows)
    return result


def mount_offset(w, segs, tol):
    """d của mặt song song lưng cục nóng, chạm bề rộng cục nóng, cách lưng CAD ≤ tol: mặt NHÔ RA PHÒNG NHẤT để cục nóng không ăn vào lớp nào
    (len chân tường 10 mm nằm trước biên Room, lần chạy 2026-10-31); None nếu không có."""
    best = None
    half = w.width / 2.0
    for sg in segs:
        sa, da = w.local(sg.a)
        sb, db = w.local(sg.b)
        ln = math.hypot(sb - sa, db - da)
        if ln < 1.0 or abs(sb - sa) / ln < PARALLEL_COS or max(sa, sb) <= -half or min(sa, sb) >= half:
            continue
        d = (da + db) / 2.0
        if abs(d) <= tol and (best is None or d > best):
            best = d
    return best


def fit_back(w, segs, tol):
    """Mặt dựa. Có mũi tên → lưng theo CAD, thiếu mặt thì giữ CAD (cục đứng tự do). Không có → thử 2 cạnh dài. Trả về ghi chú."""
    if w.arrow:
        d = mount_offset(w, segs, tol)
        if d is not None:
            w.mount_d = d
        return u""
    best = None
    for k in (0, 2):
        trial = (w.dir[0], w.dir[1])
        w.set_dir(rotate(trial, k * math.pi / 2.0, (0.0, 0.0)))
        d = mount_offset(w, segs, tol)
        if d is not None and (best is None or abs(d) < abs(best[0])):
            best = (d, w.dir)
        w.set_dir(trial)
    if best is None:
        return u"không thấy mũi tên, không có tường quanh cục nóng – giữ theo CAD, hướng cần soát"
    w.mount_d = best[0]
    w.set_dir(best[1])
    return u"không thấy mũi tên – lấy cạnh dài gần tường nhất làm lưng, cần soát hướng"


def blows_into_wall(w, walls):
    """Mũi tên CAD chỉ thẳng vào mặt tường Revit trước mặt cục nóng (cách ≤ BLOW_MM)."""
    half = w.width / 2.0
    for sg in walls:
        sa, da = w.local(sg.a)
        sb, db = w.local(sg.b)
        ln = math.hypot(sb - sa, db - da)
        if ln < 1.0 or abs(sb - sa) / ln < PARALLEL_COS or max(sa, sb) <= -half or min(sa, sb) >= half:
            continue
        if 0.0 <= (da + db) / 2.0 - w.depth <= BLOW_MM:
            return True
    return False


def fit_sides(w, segs, tol):
    """Mặt bên: vuông góc mặt dựa, chạm dải chiều sâu cục nóng, cách cạnh CAD ≤ tol, nhô vào cục nóng nhất. Trả về ghi chú."""
    half = w.width / 2.0
    best = {}
    for sg in segs:
        sa, da = w.local(sg.a)
        sb, db = w.local(sg.b)
        ln = math.hypot(sb - sa, db - da)
        if ln < 1.0 or abs(db - da) / ln < PARALLEL_COS:
            continue
        if max(da, db) < w.mount_d + 1.0 or min(da, db) > w.mount_d + w.depth:
            continue
        s = (sa + sb) / 2.0
        side = 1 if s > 0 else -1
        # Mặt nhô vào cục nóng nhất trong khoảng tol: len chân tường trước mặt tường
        if abs(abs(s) - half) <= tol and (side not in best or abs(s) < abs(best[side])):
            best[side] = s
    w.sides = [(best[k], k) for k in sorted(best)]
    if not w.sides:
        return u""
    return u"giữa hai mặt bên" if len(w.sides) == 2 else u"áp mặt bên"


def analyse(items, min_long, max_long, back_tol, side_tol, room_at=None, room_keys=(), stats=None, walls=(), need_arrow=False):
    """items: [Item] mm; room_at(pt) → (tên, [vòng], số phòng) | None; walls: [Seg] mặt tường trên level. Trả về [Condenser] đã
    gán trạng thái."""
    units = find_units(items, min_long, max_long, stats, need_arrow)
    for w in units:
        hit = room_at(w.c) if room_at is not None else None
        w.room = hit[0] if hit else u""
        w.number = hit[2] if hit else u""
        if room_at is not None and room_keys and not any(k in loose(w.room) for k in room_keys):
            w.status = u"Bỏ qua – không nằm trong phòng {} (phòng: {})".format(
                u"/".join(room_keys), w.room or u"không có Room")
            continue
        segs = [Seg(pts[i - 1], pts[i]) for pts in (hit[1] if hit else []) for i in range(len(pts))] + list(walls)
        note = fit_back(w, segs, back_tol)
        side_note = fit_sides(w, segs, side_tol)
        blow = u"mũi tên CAD thổi vào tường, cần soát hướng" if w.arrow and blows_into_wall(w, walls) else u""
        w.note = u"; ".join(v for v in (note, side_note, blow) if v)
        w.status = u"OK"
    units.sort(key=lambda x: (-round(x.c[1]), round(x.c[0])))
    return units


def wall_faces(p0, p1, along_x):
    """Hai mặt bên (Seg) của tường song song trục X / Y từ khung bao (p0, p1 mm): khung bao đúng cả khi Location Line của
    tường không ở tim."""
    if along_x:
        return [Seg((p0[0], y), (p1[0], y)) for y in (p0[1], p1[1])]
    return [Seg((x, p0[1]), (x, p1[1])) for x in (p0[0], p1[0])]


def body_fit(pts, w):
    """Căn khung khối (điểm (x, y) mm của instance) theo cục nóng đích. Trả về (dời (dx, dy), khung (s0, s1, d0, d1))."""
    ss = [w.local(p)[0] for p in pts]
    ds = [w.local(p)[1] for p in pts]
    body_w = max(ss) - min(ss)
    m_s = w.target_s(body_w) - (min(ss) + max(ss)) / 2.0
    m_d = w.mount_d - min(ds)
    move = (w.u[0] * m_s + w.dir[0] * m_d, w.u[1] * m_s + w.dir[1] * m_d)
    return move, (min(ss) + m_s, max(ss) + m_s, min(ds) + m_d, max(ds) + m_d)


def inside_room(w, loops):
    """Bốn góc khung cục nóng (thu vào ROOM_INSET_MM) nằm trong Room."""
    s0, s1, d0, d1 = w.final
    k = ROOM_INSET_MM
    return all(inside_loops(w.world(s, d), loops) for s in (s0 + k, s1 - k) for d in (d0 + k, d1 - k))


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
    """Nét ngắn – ứng viên nét cục nóng (thẳng + cong); layers = None: mọi nét, kể cả nét Revit không trả tên layer.
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
    """Hàm room_at(pt mm) → (tên Room, [vòng biên Finish mm], số Room) trên level chứa điểm, None nếu không có."""
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
    return room_at, len(rooms)


def wall_segs(level, elev):
    """[Seg] mặt tường thẳng song song trục toạ độ trên level, gồm lớp ốp, trát (tool 09, 12) ngang tầm cục nóng đáy ở elev mm
    so với level: bỏ tường có đỉnh thấp hơn đáy cục (len chân tường tool 11, tường thấp) và tường có chân cao hơn đáy cục TOP_MM."""
    segs = []
    bottom = level.Elevation + from_mm(elev)
    lim = bottom + from_mm(TOP_MM)
    for wl in FilteredElementCollector(doc).OfClass(Wall).ToElements():
        loc, bb = wl.Location, wl.get_BoundingBox(None)
        if wl.LevelId != level.Id or bb is None or bb.Min.Z > lim or bb.Max.Z < bottom:
            continue
        if not isinstance(loc, LocationCurve) or not isinstance(loc.Curve, Line):
            continue
        d = loc.Curve.Direction
        if max(abs(d.X), abs(d.Y)) >= PARALLEL_COS:
            segs += wall_faces(xy(bb.Min), xy(bb.Max), abs(d.X) > abs(d.Y))
    return segs


def equipment_symbols():
    return [s for s in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_MechanicalEquipment)
            .WhereElementIsElementType().ToElements() if isinstance(s, FamilySymbol)]


def pick_template(value):
    """IN[3]: FamilyType của node Family Types (Dynamo) hoặc chuỗi "Family : Type" → FamilySymbol cục nóng."""
    symbols = equipment_symbols()
    families = u", ".join(sorted(set(s.FamilyName for s in symbols))) or u"không có"
    if isinstance(value, str):
        parts = [norm(p) for p in value.split(u":")]
        if len(parts) != 2 or not all(parts):
            raise StopReport([u"DỪNG: ô IN[3] phải là type chọn từ node Family Types hoặc chuỗi 'Family : Type' "
                              u"(đang là '{}').".format(value)])
        hits = [s for s in symbols if norm(s.FamilyName) == parts[0] and norm(get_name(s)) == parts[1]]
        if not hits:
            raise StopReport([u"DỪNG: không có type cục nóng '{}'. Family Mechanical Equipment: {}".format(value, families)])
        return hits[0]
    sym = UnwrapElement(value) if value is not None else None
    if not isinstance(sym, FamilySymbol):
        raise StopReport([u"DỪNG: chưa chọn type cục nóng ở IN[3]."])
    if sym.Category is None or sym.Category.BuiltInCategory != BuiltInCategory.OST_MechanicalEquipment:
        raise StopReport([u"DỪNG: type '{} : {}' không thuộc Mechanical Equipment. Family Mechanical Equipment: {}".format(
            sym.FamilyName, get_name(sym), families)])
    return sym


def body_points(fi):
    """Khung cục nóng trên mặt bằng (x, y mm): 4 góc khung TYPE đưa về vị trí instance (dùng được cả family 2.5D, khung cao 0, không
    có khối đặc); không có khung thì đỉnh các khối đặc, rồi khung bao instance."""
    bb = fi.Symbol.get_BoundingBox(None)
    if bb is not None and bb.Max.X - bb.Min.X > 1e-3 and bb.Max.Y - bb.Min.Y > 1e-3:
        tf = fi.GetTransform()
        return [xy(tf.OfPoint(XYZ(x, y, 0.0))) for x in (bb.Min.X, bb.Max.X) for y in (bb.Min.Y, bb.Max.Y)]
    opt = Options()
    opt.DetailLevel = ViewDetailLevel.Fine
    result = []

    def walk(geo):
        for obj in geo:
            if isinstance(obj, GeometryInstance):
                walk(obj.GetInstanceGeometry())
            elif isinstance(obj, Solid) and obj.Volume > 1e-6:
                pts = []
                for e in obj.Edges:
                    pts.extend(xy(p) for p in e.Tessellate())
                if not pts:
                    continue
                xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                if max(max(xs) - min(xs), max(ys) - min(ys)) <= BODY_MAX_MM:
                    result.extend(pts)

    geo = fi.get_Geometry(opt)
    if geo is not None:
        walk(geo)
    if result:
        return result
    bb = fi.get_BoundingBox(None)
    if bb is None:
        return []
    x0, y0 = xy(bb.Min)
    x1, y1 = xy(bb.Max)
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def existing_fixtures(family_name, level):
    """[(tâm mm, Id, có Comments của tool)] cục nóng đã đặt trên level: cùng family, hoặc do tool tạo."""
    result = []
    for fi in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_MechanicalEquipment) \
            .WhereElementIsNotElementType().ToElements():
        sym = getattr(fi, "Symbol", None)
        if sym is None or fi.LevelId != level.Id or not isinstance(getattr(fi, "Location", None), LocationPoint):
            continue
        cm = fi.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        mine = cm is not None and cm.AsString() == COMMENT_TAG
        if norm(sym.FamilyName) != family_name and not mine:
            continue
        pts = body_points(fi)
        if pts:
            c = ((min(p[0] for p in pts) + max(p[0] for p in pts)) / 2.0,
                 (min(p[1] for p in pts) + max(p[1] for p in pts)) / 2.0)
        else:
            c = xy(fi.Location.Point)
        result.append((c, fi.Id.Value, mine))
    return result


def elevation_param(fi):
    """Cao độ instance so với level ("Elevation from Level" / "Offset from Host")."""
    return fi.get_Parameter(BuiltInParameter.INSTANCE_ELEVATION_PARAM) or \
        fi.get_Parameter(BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM)


def settle(fi, w, want, elev, sym):
    """Trong Transaction: đổi type, xoay, đặt cao độ, dời cho khung khối về đúng đích. Trả về [việc đã làm]."""
    todo = []
    if fi.Symbol.Id != sym.Id:
        todo.append(u"đổi type {} : {}".format(fi.Symbol.FamilyName, get_name(fi.Symbol)))
        fi.ChangeTypeId(sym.Id)
    doc.Regenerate()
    f = fi.FacingOrientation
    ang = math.atan2(f.X * want[1] - f.Y * want[0], f.X * want[0] + f.Y * want[1])
    if abs(ang) > 1e-3:
        p = fi.Location.Point
        ElementTransformUtils.RotateElement(doc, fi.Id, Line.CreateBound(p, XYZ(p.X, p.Y, p.Z + 1.0)), ang)
        todo.append(u"xoay {:.0f}°".format(math.degrees(ang)))
    ep = elevation_param(fi)
    if ep is None or ep.IsReadOnly:
        todo.append(u"không đặt được cao độ, cần soát")
    elif abs(to_mm(ep.AsDouble()) - elev) > 0.5:
        todo.append(u"cao độ {:.0f} → {:.0f}".format(to_mm(ep.AsDouble()), elev))
        ep.Set(from_mm(elev))
    doc.Regenerate()
    pts = body_points(fi)
    if not pts:
        w.final = (w.target_s(w.width) - w.width / 2.0, w.target_s(w.width) + w.width / 2.0,
                   w.mount_d, w.mount_d + w.depth)
        return todo + [u"không đọc được khung của family – đặt theo gốc family, cần soát"]
    move, w.final = body_fit(pts, w)
    if math.hypot(*move) > 0.5:
        ElementTransformUtils.MoveElement(doc, fi.Id, XYZ(from_mm(move[0]), from_mm(move[1]), 0.0))
        todo.append(u"dời {:.0f} mm".format(math.hypot(*move)))
    return todo


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
    path = os.path.join(folder, "TaoCucNongDHTuCAD_CHANDOAN_{}.csv".format(datetime.datetime.now().strftime("%Y%m%d_%H%M%S")))
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


def preview_lines(units, z_mm):
    try:
        clr.AddReference("ProtoGeometry")
        from Autodesk.DesignScript.Geometry import Point as DSPoint, Line as DSLine

        def seg(a, e):
            return DSLine.ByStartPointEndPoint(DSPoint.ByCoordinates(a[0], a[1], z_mm),
                                               DSPoint.ByCoordinates(e[0], e[1], z_mm))
        lines = []
        for w in units:
            lines += [seg(w.corners[i - 1], w.corners[i]) for i in range(4)]
            if w.final is not None:
                s0, s1, d0, d1 = w.final
                box = [w.world(s0, d0), w.world(s1, d0), w.world(s1, d1), w.world(s0, d1)]
                lines += [seg(box[i - 1], box[i]) for i in range(4)]
                s = (s0 + s1) / 2.0
                lines.append(seg(w.world(s, (d0 + d1) / 2.0), w.world(s, d1 + 200.0)))
        return lines
    except Exception:
        return []


LOG_HEADER = [u"STT", u"Tâm cục nóng CAD (mm)", u"Phòng", u"Số phòng", u"Đo khối (rộng × sâu, mm)", u"Cao độ so với level (mm)",
              u"Type", u"Kết quả", u"ElementId", u"Ghi chú"]


def write_log(rows, source, dry_run):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoCucNongDHTuCAD_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
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


def main(cad_filter, layer_filters, level_name, template_in, room_keys, min_long, max_long, back_tol, side_tol, flip,
         dry_run, elev):
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."], []
    if re.search(r"[-_]S[-_]", doc.Title or u""):
        return [u"DỪNG: tên file '{}' là mô hình Kết cấu (S) – cục nóng chỉ đặt trên mô hình Kiến trúc (A).".format(
            doc.Title)], []
    sym = pick_template(template_in)
    fam = norm(sym.FamilyName)
    type_label = u"{} : {}".format(fam, get_name(sym))
    if sym.Family.FamilyPlacementType != FamilyPlacementType.OneLevelBased:
        raise StopReport([u"DỪNG: family '{}' kiểu đặt {} – công cụ chỉ hỗ trợ family đặt theo level.".format(
            fam, sym.Family.FamilyPlacementType)])
    cad, cad_name, objects, all_layers = pick_cad(cad_filter, layer_filters)
    layers = match_layers(all_layers, layer_filters)
    level = find_level(level_name)
    level_z = to_mm(level.Elevation)
    room_at, n_rooms = room_finder(level)
    keys = [loose(k) for k in room_keys if k.strip()]
    if keys and not n_rooms:
        raise StopReport([u"DỪNG: level '{}' chưa có Room – cần Room để lọc cục nóng ở logia (hoặc để trống IN[4])."
                          .format(level_name)])

    items, kinds = read_items(objects, layers if layer_filters else None)
    stats = {}
    walls = wall_segs(level, elev)
    units = analyse(items, min_long, max_long, back_tol, side_tol, room_at, keys, stats, walls, not layer_filters)
    existing = existing_fixtures(fam, level)

    rows, jobs, fixes = [], [], []
    for idx, w in enumerate(units, 1):
        if w.status == u"OK":
            near = sorted((math.hypot(*sub(c, w.c)), eid, mine) for c, eid, mine in existing
                          if math.hypot(*sub(c, w.c)) <= EXIST_TOL_MM)
            if near:
                w.eid = near[0][1]
                w.dups = [eid for _, eid, _ in near[1:]]
                w.status = u"Bỏ qua – đã có cục cùng family (Id {})".format(w.eid)
                if near[0][2]:
                    fi = doc.GetElement(ElementId(w.eid))
                    if WorksharingUtils.GetCheckoutStatus(doc, fi.Id) == CheckoutStatus.OwnedByOtherUser:
                        w.status = u"Bỏ qua – người khác đang mượn cục nóng (Id {})".format(w.eid)
                    else:
                        fixes.append((fi, len(rows), w))
            else:
                jobs.append((w, len(rows)))
        rows.append([idx, fmt(w.c), w.room or u"—", w.number or u"—", u"—", u"—", u"—", w.status, w.eid,
                     u"; ".join(v for v in [w.note] + [u"TRÙNG Id {}".format(d) for d in w.dups] if v)])

    changed = 0
    created = []
    if jobs or fixes:
        # Dry-run cũng đặt thử rồi RollBack: Báo cáo là số đo khối thật của family, không ghi vào mô hình
        TransactionManager.Instance.ForceCloseTransaction()
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        try:
            if not sym.IsActive:
                sym.Activate()
                doc.Regenerate()

            def finish(fi, ri, w, todo, done):
                if w.final is not None:
                    rows[ri][4] = u"{:.0f} × {:.0f}".format(w.final[1] - w.final[0], w.final[3] - w.final[2])
                    hit = room_at(w.c)
                    if hit is not None and not inside_room(w, hit[1]):
                        todo = todo + [u"lòi khỏi Room theo khung type, cần soát"]
                rows[ri][5] = u"{:.0f}".format(elev)
                rows[ri][6] = type_label
                rows[ri][7] = done
                rows[ri][8] = fi.Id.Value
                rows[ri][9] = u"; ".join(v for v in [rows[ri][9]] + todo if v)

            for fi, ri, w in fixes:
                want = w.dir if flip else (-w.dir[0], -w.dir[1])
                todo = settle(fi, w, want, elev, sym)
                if todo:
                    changed += 1
                    finish(fi, ri, w, todo, u"Sẽ sửa" if dry_run else u"Đã sửa")
                else:
                    finish(fi, ri, w, [], u"Bỏ qua – đã đúng (Id {})".format(fi.Id.Value))
            # Family đặt theo level: Revit hiểu Z của điểm đặt là độ lệch so với level → Z = 0 rồi đặt Elevation from Level
            # (bài học tool lavabo 2026-10-30 10:16)
            for w, ri in jobs:
                p = w.world(w.target_s(w.width), w.mount_d)
                pt = XYZ(from_mm(p[0]), from_mm(p[1]), 0.0)
                fi = doc.Create.NewFamilyInstance(pt, sym, level, StructuralType.NonStructural)
                want = w.dir if flip else (-w.dir[0], -w.dir[1])
                todo = settle(fi, w, want, elev, sym)
                cm = fi.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
                if cm is not None and not cm.IsReadOnly:
                    cm.Set(COMMENT_TAG)
                keep = [t for t in todo if u"cần soát" in t]
                finish(fi, ri, w, keep, u"Sẽ tạo" if dry_run else u"Đã tạo")
                if dry_run:
                    rows[ri][8] = u""
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
            return [u"LỖI khi đặt cục nóng, mọi thay đổi đã được hoàn tác: {}".format(ex)], []
        if not dry_run:
            for fi, ri in created:
                if not fi.IsValidObject:
                    rows[ri][7] = u"Revit đã xoá sau khi tạo"

    report = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (đã hoàn tác, không ghi vào mô hình)" if dry_run
                                else u"ĐÃ THỰC HIỆN")]
    report.append(u"CAD: {} – dò {} – {} nét – nhận diện {} cục nóng (hình chữ nhật chứa mũi tên)".format(
        cad_name, u"layer " + u"; ".join(sorted(layers)) if layer_filters else u"mọi layer ({})".format(len(layers)),
        len(items), len(units)))
    report.append(u"Cục nóng: {} – level {}, cao độ {:.0f} mm so với level – phòng chứa: {} – mặt trước family {}".format(
        type_label, level.Name, elev, u"; ".join(room_keys) if keys else u"mọi phòng",
        u"+Y (đảo hướng)" if flip else u"−Y (Facing ngược mũi tên)"))
    report.append(u"Cục nóng {}: {}".format(u"sẽ tạo" if dry_run else u"đã tạo", len(jobs)))
    if fixes:
        report.append(u"Cục của tool {}: {} / {} cục đã có".format(u"sẽ sửa" if dry_run else u"đã sửa", changed, len(fixes)))
    dups = [(w, d) for w in units for d in w.dups]
    if dups:
        report.append(u"TRÙNG: {} cục thừa cạnh nhau – xoá tay (giữ Id trong ngoặc): {}".format(
            len(dups), u", ".join(u"{} (giữ {})".format(d, w.eid) for w, d in dups)))
    soat = [r for r in rows if u"cần soát" in u"{}".format(r[9])]
    if soat:
        report.append(u"CẦN SOÁT: {} cục – xem cột Ghi chú".format(len(soat)))
    counts = {}
    for r in rows:
        if r[7].startswith(u"Bỏ qua"):
            k = re.sub(r"[\d(].*", u"", r[7].split(u" – ", 1)[1]).strip()
            counts[k] = counts.get(k, 0) + 1
    for k in sorted(counts):
        report.append(u"Bỏ qua {} cục: {}".format(counts[k], k))
    report.append(u"Chẩn đoán nhận diện: {} hình chữ nhật cạnh dài {:.0f}–{:.0f} mm – {} có mũi tên – {} mặt tường – "
                  u"Room trên level: {}".format(stats.get("rects", 0), min_long, max_long, stats.get("arrows", 0),
                                                len(walls), n_rooms))
    report.append(u"Đối tượng CAD theo loại: " + u", ".join(u"{} {}".format(k, v) for k, v in sorted(kinds.items())))
    try:
        report.append(u"Log: " + write_log(rows, cad_name, dry_run))
        if dry_run:
            report.append(u"Chẩn đoán nét CAD trong logia: " + write_diag(cad, objects, room_at, keys))
    except Exception as ex:
        report.append(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        report.append(u"Kiểm tra hình chữ nhật CAD + khung cục nóng + đoạn hướng mặt trước (nét xanh trong Dynamo) và log. Thiếu "
                      u"cục → xem IN[1], IN[5], IN[6]. Đúng thì đổi Dry-run = False và Run lại. Undo bằng mục \"{}\"."
                      .format(TRANSACTION_NAME))
    else:
        report.append(u"Soát hướng vài cục trên 3D: quay ngược → Undo mục \"{}\", IN[9] = True, Run lại.".format(
            TRANSACTION_NAME))
    report.append(u" | ".join(LOG_HEADER))
    report += [u" | ".join(u"{}".format(v) for v in r) for r in rows
               if not r[7].startswith(u"Bỏ qua – không nằm trong phòng")]
    return report, preview_lines([w for w, _ in jobs] + [f[2] for f in fixes], level_z + elev)


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
            IN[3] if IN[3] is not None else u"AV_MT_cuc nong dieu hoa loai dai1 : AV_Cuc nong DH 3",
            (u"logia;lô gia" if IN[4] is None else IN[4]).split(u";"),
            num(5, 1000.0),
            num(6, 1200.0),
            num(7, 50.0),
            num(8, 50.0),
            False if IN[9] is None else bool(IN[9]),
            True if IN[10] is None else bool(IN[10]),
            num(11, 1500.0),
        ))
    except StopReport as ex:
        OUT = [ex.lines, []]
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], []]
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with io.open(os.path.join(folder, "TaoCucNongDHTuCAD_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))), "w", encoding="utf-8-sig") as f:
                f.write(u"\n".join(OUT[0]))
        except Exception:
            pass
    note = force_rerun_next_time()
    if note:
        OUT[0].append(u"LƯU Ý: " + note)
