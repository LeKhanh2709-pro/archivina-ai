# TRẠNG THÁI: CHƯA DUYỆT (bản sửa 2026-11-03 – tên type + tham số A; bản duyệt BIM Manager 2026-10-29 là bản trước)
# Mã nguồn của Python node trong ARV_TaoCuaTuCAD_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Tạo cửa đi gắn vào tường Revit có sẵn từ mặt bằng DWG đã Link (cửa trong CAD là nét rời / block ẩn danh,
# nên nhận cửa theo CUNG MỞ CÁNH trên layer cửa):
#   1. Đọc cung tròn và cung elip (block cửa bị scale lệch) trên layer cửa (IN[1]): khoảng cách tâm → hai đầu cung
#      300–1500 mm, góc quét 30°–100° (cửa vẽ mở 90° hoặc 45°). Tâm cung = bản lề, khoảng cách tâm → đầu cung nằm dọc
#      tường = bề rộng cánh. Cung trùng nhau tính một lần. Cung bị loại (và cung dạng cửa ở layer khác) ghi vào file
#      log CHANDOAN để dò cửa còn thiếu.
#   2. Tường chủ: tường Revit trên level IN[4] có tim đi qua bản lề (lệch ≤ nửa bề dày tường + 60 mm) và một đầu
#      cung nằm dọc theo tim tường (cánh ở vị trí đóng). Không có → báo cáo, không tạo.
#   3. Cửa 2 cánh: hai cung trên cùng tường, bản lề hai đầu, cánh đóng gặp nhau giữa ô → chỉ báo cáo (chưa có
#      family 2 cánh).
#   4. Bề rộng = PHỦ BÌ KHUÔN CỬA CAD (= Width của family; khuôn cách mặt tường ~10 mm nên khe tường lớn hơn 20 mm):
#      khe lỗ tường = đầu mút nét layer IN[2] trong dải bề dày tường gần nhất phía bản lề / phía đối diện; khuôn = nét
#      layer cửa IN[1] trong dải đó, nằm trong khe – từ bản lề lùi về sau và từ đầu cánh tiến ra, lấy mép xa nhất.
#      Làm tròn IN[6] mm. Thiếu đầu tường hoặc khuôn ở một bên → báo cáo, không tạo.
#      Family trong WIDTH_FROM_GAP (Width = lỗ tường, VD CuaGoCongNghiep): bề rộng = KHE TƯỜNG CAD, cửa đặt giữa khe.
#   5. Type: type có sẵn của family IN[3] có Width khớp (±IN[6]/2 mm) và Height = IN[7] → dùng; chưa có → nhân bản
#      type mẫu IN[5], tên theo mẫu tên type đó (VD "900x2200" → "800x2200", "DW01_900X2200 2" → "DW01_800X2200"; tên
#      không có dạng rộngxcao → "DW01_{rộng}X{cao}"), đặt Width / Height; tham số "A" (nếu có, không theo công thức)
#      giữ chênh lệch với Width như type mẫu (VD CuaGoCongNghiep: A = Width − 55).
#   6. Tường Revit cùng trục bị chia nhiều đoạn tại ô cửa (Revit xoá cửa có lỗ vượt quá đầu tường chủ): chọn đoạn
#      chứa phần lớn ô cửa làm tường chủ, KÉO DÀI tường chủ phủ hết ô cửa và CẮT NGẮN đoạn kế bên tới mép ô cửa (sửa
#      Location Curve, không xoá tường). Đoạn nằm trọn trong ô cửa → báo cáo, không tạo. Tường đổi đầu mút ghi vào
#      báo cáo + log (Id, toạ độ cũ → mới). Tường mỏng < 50 mm (lớp hoàn thiện) không làm tường chủ.
#   7. Đặt cửa giữa ô (trên tim tường chủ), Sill = 0, lật hướng mở (Facing) và bản lề (Hand) theo cung CAD.
#      Bỏ qua ô đã có cửa (cửa trên các đoạn tường cùng trục, tâm cách ≤ 100 mm); cửa cũ khác bề rộng → báo "SAI RỘNG"
#      kèm Id để xoá. Tường đang bị người khác mượn (workshared) → bỏ qua cửa đó. Sau khi Commit kiểm tra lại cửa vừa
#      tạo; cửa bị Revit xoá (không cắt được tường) → báo trong log.
#   8. Cửa ra logia (khi IN[3] có "LOGIA="): dựng lưới ô GRID_MM trên mặt bằng, đánh dấu tường cắt qua cao độ
#      Level + OUTSIDE_PROBE_Z_MM (bỏ lan can / gờ thấp, bỏ tường kính – lam curtain wall), cộng tường + cột của các
#      link Revit đang nạp (cột / vách BTCT ở mô hình KC – link Unloaded thì khe cột làm phòng "thông" ra ngoài), đóng tạm mọi ô cửa đang
#      xét, loang từ biên vào → vùng ngoài nhà. Cửa có đúng một phía thuộc vùng ngoài nhà (logia hở ra ngoài) →
#      family / type mẫu LOGIA (KTS chốt 2026-11-03: cửa 1 cánh ra logia không dùng chung loại cửa chính / phòng ngủ).
#      Ô đã có cửa (VD lần chạy trước) là cửa ra logia nhưng khác family LOGIA → ĐỔI TYPE sang type logia cùng bề rộng
#      (ChangeTypeId, giữ vị trí, lật lại theo CAD) thay vì bỏ qua.
# INPUT
#   IN[0] (str)   Một phần tên bản CAD (để trống = bản CAD duy nhất có layer khớp IN[1])
#   IN[1] (str)   Chuỗi lọc layer cửa đi, nhiều chuỗi cách nhau bằng ';' (VD "A-Door;A-Cửa"; khớp chuỗi con)
#   IN[2] (str)   Chuỗi lọc layer tường CAD để đo khe lỗ cửa (VD "A-Wall")
#   IN[3] (str)   Tên family cửa 1 cánh (VD "D1_WO_OP1"); thêm ";LOGIA=<family>" → cửa ra logia dùng family đó
#   IN[4] (str)   Tên level của tường chủ (VD "TẦNG 2")
#   IN[5] (str)   Type mẫu để nhân bản khi chưa có type đúng bề rộng (VD "DW01_900X2200 2"); thêm ";LOGIA=<type>"
#                 cho type mẫu của family logia (không có → dùng type mẫu chính)
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
import re
import datetime
import unicodedata

DYNAMO = "IN" in globals()

if DYNAMO:
    import clr
    clr.AddReference("RevitAPI")
    from Autodesk.Revit.DB import (FilteredElementCollector, ImportInstance, Options, GeometryInstance, PolyLine,
                                   Line, Arc, Ellipse, XYZ, Transaction, TransactionStatus, UnitUtils, UnitTypeId,
                                   ModelPathUtils, BuiltInParameter, BuiltInCategory, Level, Wall, LocationCurve,
                                   FamilySymbol, FamilyInstance, WorksharingUtils, CheckoutStatus, WallKind,
                                   ElementId, RevitLinkInstance, Transform)
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
COLLINEAR_MM = 5.0               # Đoạn tường cùng trục: tim lệch tối đa
PIECE_OVERLAP_MM = 20.0          # Đoạn tường lấn vào ô cửa tối thiểu để tính là nằm trong ô
MIN_HOST_WIDTH_MM = 50.0         # Tường mỏng hơn là lớp hoàn thiện, không làm tường chủ
MIN_PIECE_MM = 20.0              # Đoạn tường còn lại sau khi cắt ngắn tối thiểu
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
    """Tường chủ trên mặt bằng (mm). Gốc toạ độ dọc tường cố định tại a; đoạn tường là [s0, s1] (đổi khi kéo dài /
    cắt ngắn tường để phủ ô cửa)."""

    def __init__(self, wid, a, b, width, name=u""):
        self.id, self.a, self.b, self.width, self.name = wid, a, b, width, name
        self.length = math.hypot(b[0] - a[0], b[1] - a[1])
        self.u = unit(sub(b, a))
        self.n = (-self.u[1], self.u[0])
        self.s0, self.s1 = 0.0, self.length

    def local(self, p):
        d = sub(p, self.a)
        return dot(d, self.u), dot(d, self.n)

    def point(self, s):
        return (self.a[0] + self.u[0] * s, self.a[1] + self.u[1] * s)


class Leaf(object):
    """Một cánh cửa: cung CAD trên tường chủ. t = (s - s_h) * sign là toạ độ dọc tường hướng vào ô cửa."""

    def __init__(self, arc, wall, s_h, sign, swing, r=None):
        self.arc, self.wall, self.s_h, self.sign, self.swing = arc, wall, s_h, sign, swing
        self.r = arc["r"] if r is None else r
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
        self.note = u""
        self.edits = []         # [(HostWall, s0 mới, s1 mới)] kéo dài / cắt ngắn tường để phủ ô cửa
        self.kind = u""         # "" = family chính, "LOGIA" = cửa ra logia

    def center(self):
        return self.leaf.wall.point(self.s_center) if self.s_center is not None else self.leaf.arc["c"]


def arc_sweep_deg(arc):
    v0, v1 = unit(sub(arc["p0"], arc["c"])), unit(sub(arc["p1"], arc["c"]))
    return math.degrees(math.acos(max(-1.0, min(1.0, dot(v0, v1)))))


def arc_radii(arc):
    return math.hypot(*sub(arc["p0"], arc["c"])), math.hypot(*sub(arc["p1"], arc["c"]))


def arc_reject_reason(arc):
    """Lý do cung không phải cánh cửa, None nếu đạt."""
    r0, r1 = arc_radii(arc)
    if not (R_RANGE_MM[0] <= min(r0, r1) and max(r0, r1) <= R_RANGE_MM[1]):
        return u"bán kính {:.0f}/{:.0f} ngoài {:.0f}–{:.0f} mm".format(r0, r1, *R_RANGE_MM)
    sweep = arc_sweep_deg(arc)
    if not (SWEEP_RANGE_DEG[0] <= sweep <= SWEEP_RANGE_DEG[1]):
        return u"góc mở {:.0f}° ngoài {:.0f}–{:.0f}°".format(sweep, *SWEEP_RANGE_DEG)
    return None


def door_arcs(arcs):
    """Lọc cung cánh cửa, bỏ cung trùng. Trả về (danh sách, [(cung bị loại, lý do)])."""
    kept, rejected = [], []
    for a in arcs:
        reason = arc_reject_reason(a)
        if reason:
            rejected.append((a, reason))
            continue
        if any(math.hypot(*sub(a["c"], k["c"])) <= DUP_ARC_MM and abs(a["r"] - k["r"]) <= DUP_ARC_MM
               and min(math.hypot(*sub(a["p0"], k["p0"])) + math.hypot(*sub(a["p1"], k["p1"])),
                       math.hypot(*sub(a["p0"], k["p1"])) + math.hypot(*sub(a["p1"], k["p0"]))) <= 2 * DUP_ARC_MM
               for k in kept):
            continue
        kept.append(a)
    return kept, rejected


def find_leaf(arc, walls):
    """Tường chủ có tim đi qua bản lề và một đầu cung nằm dọc tim tường → Leaf, None nếu không có."""
    best = None
    for w in walls:
        s, d = w.local(arc["c"])
        if s < w.s0 - HOST_TOL_MM or s > w.s1 + HOST_TOL_MM or abs(d) > w.width / 2.0 + HOST_TOL_MM:
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
            best = (abs(d), Leaf(arc, w, s, sign, swing, math.hypot(*sub(closed, arc["c"]))))
    return best[1] if best else None


def collinear_walls(wall, walls):
    """Các đoạn tường (kể cả chính nó) nằm trên cùng trục tim với wall."""
    return [x for x in walls if abs(abs(dot(x.u, wall.u)) - 1.0) <= 1e-4
            and abs(wall.local(x.a)[1]) <= COLLINEAR_MM and abs(wall.local(x.b)[1]) <= COLLINEAR_MM]


def rehost(leaf, wall):
    """Chuyển cánh sang đoạn tường cùng trục: tính lại s bản lề, đảo sign/swing nếu đoạn mới vẽ ngược chiều."""
    k = 1 if dot(leaf.wall.u, wall.u) > 0 else -1
    return Leaf(leaf.arc, wall, wall.local(leaf.arc["c"])[0], leaf.sign * k, leaf.swing * k, leaf.r)


def extent_in(w, x):
    """Đoạn [lo, hi] của tường x theo toạ độ dọc tường w."""
    sa, sb = w.local(x.point(x.s0))[0], w.local(x.point(x.s1))[0]
    return min(sa, sb), max(sa, sb)


def set_extent(x, w, lo, hi):
    """Đặt đoạn tường x = [lo, hi] cho theo toạ độ tường w."""
    sa, sb = x.local(w.point(lo))[0], x.local(w.point(hi))[0]
    x.s0, x.s1 = min(sa, sb), max(sa, sb)


def fit_host(d, pieces):
    """Ô cửa phải nằm trọn trong tường chủ (Revit xoá cửa có lỗ vượt quá đầu tường). Chọn đoạn tường cùng trục chứa
    phần lớn ô cửa làm tường chủ, kéo dài nó phủ hết ô cửa, cắt ngắn các đoạn khác lấn vào ô cửa tới mép ô.
    Ghi d.edits và áp ngay vào HostWall (cửa sau trên cùng trục thấy tường đã sửa). Trả về lỗi (str) hoặc None."""
    w = d.leaf.wall
    half = max(d.raw_width, d.width) / 2.0
    o0, o1 = d.s_center - half, d.s_center + half
    hits = []
    for x in pieces:
        lo, hi = extent_in(w, x)
        ov = min(hi, o1) - max(lo, o0)
        if ov > 0.5:
            hits.append((ov, x))
    if not hits:
        return None
    hits.sort(key=lambda h: -h[0])
    best = hits[0][1]
    if best is not w:
        c = w.point(d.s_center)
        d.leaf = rehost(d.leaf, best)
        w = best
        d.s_center = w.local(c)[0]
        o0, o1 = d.s_center - half, d.s_center + half
    h0, h1 = min(w.s0, o0), max(w.s1, o1)
    trims = []
    for _, x in hits[1:]:
        lo, hi = extent_in(w, x)
        if lo < h0 - 0.5 and hi > h1 + 0.5:
            return u"tường cùng trục Id {} chồng lên tường chủ Id {}".format(x.id, w.id)
        if lo < h0 - 0.5 and h0 - lo >= MIN_PIECE_MM:
            trims.append((x, lo, h0))
        elif hi > h1 + 0.5 and hi - h1 >= MIN_PIECE_MM:
            trims.append((x, h1, hi))
        else:
            return u"tường cùng trục Id {} nằm trọn trong ô cửa – cần xoá đoạn này".format(x.id)
    for x, lo, hi in trims:     # cắt ngắn trước, kéo dài sau → tường không chồng nhau giữa chừng
        set_extent(x, w, lo, hi)
        d.edits.append((x, x.s0, x.s1))
    if (h0, h1) != (w.s0, w.s1):
        w.s0, w.s1 = h0, h1
        d.edits.append((w, w.s0, w.s1))
    return None


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
    lo, hi = wall.s0 - JAMB_BACK_MM - R_RANGE_MM[1], wall.s1 + JAMB_BACK_MM + R_RANGE_MM[1]
    result = []
    for a, b in segs:
        for p in (a, b):
            s, d = wall.local(p)
            if abs(d) <= h and lo <= s <= hi:
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


def analyse(arcs, segs, door_segs, walls, round_mm, existing=None, use_gap=False):
    """arcs: [{"c","r","p0","p1"}] mm; segs: nét tường CAD [(a, b)]; door_segs: nét thẳng layer cửa (khuôn);
    walls: [HostWall]. existing: {wall_id: [(x, y)]} tâm cửa đã có. Trả về (doors, thống kê)."""
    stats = {}
    kept, stats["rejected"] = door_arcs(arcs)
    stats["arc_skipped"] = len(stats["rejected"])
    stats["arcs"] = len(kept)
    leaves, doors = [], []
    for a in kept:
        leaf = find_leaf(a, walls)
        if leaf is None:
            d = Door(Leaf(a, None, 0.0, 1, 1))
            d.status = u"Bỏ qua – không có tường Revit (dày ≥ 50 mm) đi qua bản lề, cần dựng tường trước"
            doors.append(d)
        else:
            leaves.append(leaf)
    pair_doubles(leaves)
    ends_cache, door_cache, line_cache = {}, {}, {}
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
        if use_gap:
            d.width = round_to(d.gap_width, round_mm)
            d.s_center = leaf.s_h + leaf.sign * (gap[0] + gap[1]) / 2.0
        else:
            d.width = round_to(d.raw_width, round_mm)
            d.s_center = leaf.s_h + leaf.sign * (t0 + t1) / 2.0
        if w.id not in line_cache:
            line_cache[w.id] = collinear_walls(w, walls)
        pieces = line_cache[w.id]
        c = d.center()
        old = [e for x in pieces for e in (existing or {}).get(x.id, []) if math.hypot(*sub(c, e[0])) <= EXIST_DOOR_MM]
        if old:
            p, eid, tname, ow = old[0]
            d.eid = eid
            if ow is not None and abs(ow - d.width) > max(round_mm / 2.0, 1.0):
                d.status = u"Bỏ qua – ô đã có cửa SAI RỘNG (Id {}, {} rộng {:.0f} ≠ {}) – xoá cửa cũ rồi Run lại".format(
                    eid, tname, ow, d.width)
            else:
                d.status = u"Bỏ qua – ô đã có cửa"
            continue
        err = fit_host(d, pieces)
        if err:
            d.status = u"Bỏ qua – " + err
            continue
        w = d.leaf.wall
        if not (w.s0 <= d.s_center <= w.s1):
            d.status = u"Bỏ qua – tâm ô cửa nằm ngoài tường chủ"
            continue
        if d.edits:
            d.note = u"; ".join(u"tường {} {} đoạn {:.0f}→{:.0f}".format(
                x.id, u"kéo dài" if x is w else u"cắt ngắn", s0, s1) for x, s0, s1 in d.edits)
        d.status = u"OK"
    doors.sort(key=lambda d: (-round(d.center()[1]), round(d.center()[0])))
    return doors, stats


def _count(items):
    result = {}
    for i in items:
        result[i] = result.get(i, 0) + 1
    return result


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
    # So khớp không phân biệt hoa thường, chuẩn hoá Unicode (tên layer tiếng Việt như "A-Cửa" có thể lưu dạng tổ hợp)
    return set(l for l in all_layers if any(norm(f).lower() in norm(l).lower() for f in filters))


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


def read_arcs(objects):
    """Mọi cung tròn / cung elip hở trên mọi layer: {"c","r","p0","p1","layer","kind"}; r = khoảng cách xa nhất từ tâm
    tới đầu cung (cung elip do block cửa bị scale lệch – hai đầu cung cách tâm khác nhau)."""
    arcs = []
    for obj in objects:
        if isinstance(obj, Arc):
            kind = u"cung tròn"
        elif isinstance(obj, Ellipse):
            kind = u"cung elip"
        else:
            continue
        if not obj.IsBound:
            continue
        a = {"c": xy(obj.Center), "p0": xy(obj.GetEndPoint(0)), "p1": xy(obj.GetEndPoint(1)),
             "layer": layer_of(obj) or u"", "kind": kind}
        a["r"] = max(arc_radii(a))
        arcs.append(a)
    return arcs


def write_diagnosis(door_arcs_rejected, other_arcs, source):
    """File CHANDOAN: cung trên layer cửa bị loại (kèm lý do) và cung dạng cánh cửa ở layer khác."""
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    path = os.path.join(folder, "TaoCuaTuCAD_CHANDOAN_{}.csv".format(
        datetime.datetime.now().strftime("%Y%m%d_%H%M%S")))
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(u"# Dự án: {}\n".format(doc.Title))
        f.write(u"# File nguồn: {}\n".format(source))
        f.write(u"# Ngày xuất: {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write(u"# Đơn vị: mm\n")
        w = csv.writer(f)
        w.writerow([u"Nhóm", u"Layer", u"Loại", u"Tâm (mm)", u"Đầu 1 (mm)", u"Đầu 2 (mm)", u"R1", u"R2", u"Góc (°)",
                    u"Lý do"])
        for group, items in ((u"Layer cửa – bị loại", door_arcs_rejected), (u"Layer khác – dạng cánh cửa",
                                                                          [(a, u"") for a in other_arcs])):
            for a, reason in items:
                r0, r1 = arc_radii(a)
                w.writerow([group, a.get("layer", u""), a.get("kind", u""), fmt(a["c"]), fmt(a["p0"]), fmt(a["p1"]),
                            u"{:.0f}".format(r0), u"{:.0f}".format(r1), u"{:.0f}".format(arc_sweep_deg(a)), reason])
    return path


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
        if wl.LevelId == level.Id and isinstance(loc, LocationCurve) and isinstance(loc.Curve, Line) \
                and to_mm(wl.Width) >= MIN_HOST_WIDTH_MM:
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


def type_name_for(template_name, width, height):
    """Tên type mới theo mẫu tên type mẫu: <tiền tố><rộng><x|X><cao>, bỏ phần sau (VD " 2")."""
    m = re.match(r"^(.*?)\d{3,4}([xX])\d{3,4}", template_name or u"")
    if m:
        return u"{}{}{}{}".format(m.group(1), width, m.group(2), height)
    return TYPE_PATTERN.format(w=width, h=height)


def keep_a_offset(new_type, template, width):
    """Tham số "A" không theo công thức (family không tự tính theo Width) → giữ chênh lệch A − Width của type mẫu."""
    pa = length_param(new_type, "A")
    ta = template.LookupParameter("A")
    w0 = symbol_size(template)[0]
    if pa is not None and ta is not None and w0 is not None:
        pa.Set(ta.AsDouble() + from_mm(width - w0))


def parse_spec(text, default):
    """"Tên;LOGIA=Tên khác" → (tên chính, {"LOGIA": tên khác})."""
    main, extra = default, {}
    for part in (text or u"").split(u";"):
        part = part.strip()
        if not part:
            continue
        if u"=" in part:
            k, v = part.split(u"=", 1)
            extra[k.strip().upper()] = v.strip()
        else:
            main = part
    return main, extra


def pick_template(symbols, family_name, template_name):
    for s in symbols:
        if norm(get_name(s)) == norm(template_name):
            return s
    raise StopReport([u"DỪNG: family '{}' không có type mẫu '{}' (IN[5]). Các type: {}".format(
        family_name, template_name, u", ".join(sorted(get_name(s) for s in symbols)))])


def wall_segments(document, tf, zc, segs):
    """Thêm tim tường (mm, toạ độ mô hình chủ qua tf) cắt qua cao độ zc vào segs. Trả về số tường."""
    n = 0
    for w in FilteredElementCollector(document).OfClass(Wall).ToElements():
        try:
            if w.WallType.Kind == WallKind.Curtain:
                continue
        except Exception:
            pass
        bb = w.get_BoundingBox(None)
        lc = w.Location
        if bb is None or not isinstance(lc, LocationCurve):
            continue
        z0, z1 = tf.OfPoint(bb.Min).Z, tf.OfPoint(bb.Max).Z
        if min(z0, z1) > zc or max(z0, z1) < zc:
            continue
        crv = lc.Curve
        pts = [crv.GetEndPoint(0), crv.GetEndPoint(1)] if isinstance(crv, Line) else list(crv.Tessellate())
        pts = [tf.OfPoint(q) for q in pts]
        hw = to_mm(w.Width) / 2.0
        for a, b in zip(pts[:-1], pts[1:]):
            segs.append(((to_mm(a.X), to_mm(a.Y)), (to_mm(b.X), to_mm(b.Y)), hw))
        n += 1
    return n


def column_segments(document, tf, zc, segs):
    """Cột kết cấu: hộp bao → đoạn dọc cạnh dài, nửa bề dày = cạnh ngắn / 2. Trả về số cột."""
    n = 0
    for col in FilteredElementCollector(document).OfCategory(BuiltInCategory.OST_StructuralColumns) \
            .WhereElementIsNotElementType().ToElements():
        bb = col.get_BoundingBox(None)
        if bb is None:
            continue
        z0, z1 = tf.OfPoint(bb.Min).Z, tf.OfPoint(bb.Max).Z
        if min(z0, z1) > zc or max(z0, z1) < zc:
            continue
        cs = [tf.OfPoint(XYZ(x, y, bb.Min.Z)) for x, y in ((bb.Min.X, bb.Min.Y), (bb.Max.X, bb.Min.Y),
                                                            (bb.Max.X, bb.Max.Y), (bb.Min.X, bb.Max.Y))]
        cs = [(to_mm(q.X), to_mm(q.Y)) for q in cs]
        mid = lambda a, b: ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        l1 = math.hypot(cs[1][0] - cs[0][0], cs[1][1] - cs[0][1])
        l2 = math.hypot(cs[3][0] - cs[0][0], cs[3][1] - cs[0][1])
        if l1 >= l2:
            segs.append((mid(cs[0], cs[3]), mid(cs[1], cs[2]), l2 / 2.0))
        else:
            segs.append((mid(cs[0], cs[1]), mid(cs[3], cs[2]), l1 / 2.0))
        n += 1
    return n


def exterior_grid(level, doors):
    """Lưới vùng ngoài nhà: (x0, y0, nx, ny, blocked, outside, thống kê) – ô GRID_MM, toạ độ mm."""
    zc = level.Elevation + from_mm(OUTSIDE_PROBE_Z_MM)
    segs = []
    stats = dict(walls=0, link_walls=0, link_cols=0, links=0, unloaded=0)
    ident = Transform.Identity
    stats["walls"] = wall_segments(doc, ident, zc, segs)
    for li in FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements():
        ldoc = li.GetLinkDocument()
        if ldoc is None:
            stats["unloaded"] += 1
            continue
        tf = li.GetTotalTransform()
        stats["links"] += 1
        stats["link_walls"] += wall_segments(ldoc, tf, zc, segs)
        stats["link_cols"] += column_segments(ldoc, tf, zc, segs)
    for dr in doors:     # tường Revit có thể hở tại ô cửa chưa đặt cửa → đóng tạm để phòng không thông ra ô cửa
        if dr.s_center is None or dr.width is None:
            continue
        w = dr.leaf.wall
        segs.append((w.point(dr.s_center - dr.width / 2.0 - 100.0), w.point(dr.s_center + dr.width / 2.0 + 100.0),
                     w.width / 2.0))
    if not segs:
        return None
    g = GRID_MM
    xs = [q[0] for s in segs for q in s[:2]]
    ys = [q[1] for s in segs for q in s[:2]]
    x0, y0 = min(xs) - 1000.0, min(ys) - 1000.0
    nx = int((max(xs) + 1000.0 - x0) / g) + 1
    ny = int((max(ys) + 1000.0 - y0) / g) + 1
    blocked = bytearray(nx * ny)
    for a, b, hw in segs:
        r = hw + 0.6 * g        # tường mỏng vẫn phủ ≥ 2 ô liền – không rò chéo
        vx, vy = b[0] - a[0], b[1] - a[1]
        ll = vx * vx + vy * vy
        i0 = max(int((min(a[0], b[0]) - r - x0) / g), 0)
        i1 = min(int((max(a[0], b[0]) + r - x0) / g) + 1, nx - 1)
        j0 = max(int((min(a[1], b[1]) - r - y0) / g), 0)
        j1 = min(int((max(a[1], b[1]) + r - y0) / g) + 1, ny - 1)
        for j in range(j0, j1 + 1):
            py = y0 + (j + 0.5) * g
            row = j * nx
            for i in range(i0, i1 + 1):
                px = x0 + (i + 0.5) * g
                t = ((px - a[0]) * vx + (py - a[1]) * vy) / ll if ll > 0 else 0.0
                t = min(max(t, 0.0), 1.0)
                dx, dy = px - (a[0] + vx * t), py - (a[1] + vy * t)
                if dx * dx + dy * dy <= r * r:
                    blocked[row + i] = 1
    outside = bytearray(nx * ny)
    stack = [k for k in list(range(nx)) + list(range((ny - 1) * nx, ny * nx)) +
             [j * nx for j in range(ny)] + [j * nx + nx - 1 for j in range(ny)] if not blocked[k]]
    for k in stack:
        outside[k] = 1
    while stack:
        k = stack.pop()
        i, j = k % nx, k // nx
        for q in ((k - 1) if i > 0 else -1, (k + 1) if i < nx - 1 else -1,
                  (k - nx) if j > 0 else -1, (k + nx) if j < ny - 1 else -1):
            if q >= 0 and not blocked[q] and not outside[q]:
                outside[q] = 1
                stack.append(q)
    return x0, y0, nx, ny, blocked, outside, stats


def opens_outside(dr, grid):
    """True nếu đúng một phía cửa thuộc vùng ngoài nhà (cửa ra logia hở)."""
    x0, y0, nx, ny, blocked, outside = grid[:6]
    w = dr.leaf.wall
    c = dr.center()
    sides = []
    for sg in (1.0, -1.0):
        hit = None
        for extra in SIDE_PROBES_MM:
            dd = w.width / 2.0 + extra
            i = int((c[0] + sg * w.n[0] * dd - x0) / GRID_MM)
            j = int((c[1] + sg * w.n[1] * dd - y0) / GRID_MM)
            if not (0 <= i < nx and 0 <= j < ny) or blocked[j * nx + i]:
                continue
            hit = bool(outside[j * nx + i])
            break
        sides.append(hit)
    return sides.count(True) == 1


def set_family_params(symbol):
    """Đặt tham số type cố định theo FAMILY_TYPE_PARAMS (mm). Tham số không có / chỉ đọc → bỏ qua."""
    for name, v in FAMILY_TYPE_PARAMS.get(norm(symbol.FamilyName).lower(), {}).items():
        p = length_param(symbol, name)
        if p is not None and abs(to_mm(p.AsDouble()) - v) > 0.01:
            p.Set(from_mm(v))


def set_size(symbol, width, height):
    for bip, name, v in ((BuiltInParameter.DOOR_WIDTH, "Width", width), (BuiltInParameter.DOOR_HEIGHT, "Height", height)):
        p = symbol.get_Parameter(bip) or symbol.LookupParameter(name)
        if p is None or p.IsReadOnly:
            raise Exception(u"Type '{}' không đặt được tham số {}.".format(get_name(symbol), name))
        p.Set(from_mm(v))


def orient(fi, wall, leaf):
    """Lật cửa cho đúng phía mở (Facing) và phía bản lề (Hand) theo cung CAD.
    Quy ước family (đã thử trong Revit 2026 với D1_WO_OP1, 7/7 cửa khớp bản lề + phía mở): FacingOrientation chỉ
    về phía cánh mở vào, HandOrientation chỉ về phía bản lề. Family khác quy ước → khai báo ở FAMILY_SIGNS."""
    facing_sign, hand_sign = FAMILY_SIGNS.get(norm(fi.Symbol.FamilyName).lower(), (FACING_TO_SWING, HAND_TO_HINGE))
    doc.Regenerate()
    swing_vec = (wall.n[0] * leaf.swing, wall.n[1] * leaf.swing)
    hinge_vec = (-wall.u[0] * leaf.sign, -wall.u[1] * leaf.sign)
    f = fi.FacingOrientation
    if facing_sign * dot((f.X, f.Y), swing_vec) < 0:
        fi.flipFacing()
    doc.Regenerate()
    h = fi.HandOrientation
    if hand_sign * dot((h.X, h.Y), hinge_vec) < 0:
        fi.flipHand()


def wall_xyz(wall):
    c = wall.Location.Curve
    return c.GetEndPoint(0), c.GetEndPoint(1)


def set_wall_extent(wall, hw, s0, s1):
    """Đặt Location Curve của tường theo đoạn [s0, s1] dọc trục hw, giữ chiều vẽ và cao độ. Trả về (cũ, mới) dạng chữ."""
    p0, p1 = wall_xyz(wall)
    z = p0.Z
    if hw.local(xy(p0))[0] > hw.local(xy(p1))[0]:
        s0, s1 = s1, s0
    a, b = hw.point(s0), hw.point(s1)
    old = u"{} → {}".format(fmt(xy(p0)), fmt(xy(p1)))
    wall.Location.Curve = Line.CreateBound(XYZ(from_mm(a[0]), from_mm(a[1]), z), XYZ(from_mm(b[0]), from_mm(b[1]), z))
    return old, u"{} → {}".format(fmt(a), fmt(b))


def owned_by_other(element_id):
    return doc.IsWorkshared and WorksharingUtils.GetCheckoutStatus(doc, element_id) == CheckoutStatus.OwnedByOtherUser


# Quy ước hướng của family (+1 / -1), xác định bằng thử nghiệm trong Revit – xem orient()
FACING_TO_SWING = 1
HAND_TO_HINGE = 1
# Family có quy ước ngược (tên thường → (Facing, Hand)). CuaGoCongNghiep: cánh nằm phía −Facing, bản lề phía −Hand
# (HQV 2026-11-03: 146 cửa tạo theo quy ước D1_WO_OP1 bị xoay 180° so với CAD)
FAMILY_SIGNS = {u"cuagocongnghiep": (-1, -1)}
# Family có Width = lỗ tường, không phải phủ bì khuôn (HQV 2026-11-03: khe CAD 800 mà type 780 → hở 10 mm mỗi bên)
WIDTH_FROM_GAP = {u"cuagocongnghiep"}
# Tham số type đặt cố định theo family. CuaGoCongNghiep: "Thk vữa" = 15 làm lỗ tường rộng hơn Width 15 mm mỗi bên
# (tường thụt vào cạnh cửa) – Width đã lấy theo khe tường CAD nên đặt 0 (HQV 2026-11-03)
FAMILY_TYPE_PARAMS = {u"cuagocongnghiep": {u"Thk vữa": 0.0}}
# Cửa nhôm 1 cánh ra logia (HQV): giả định cùng quy ước CuaGoCongNghiep (bbox family: cánh phía −Y, Width = lỗ tường)
# – CHƯA THỬ, soát hướng mở / bề rộng sau lần chạy đầu
FAMILY_SIGNS[u"cuanhom_1canh_moquay"] = (-1, -1)
WIDTH_FROM_GAP.add(u"cuanhom_1canh_moquay")
GRID_MM = 50.0               # Ô lưới dò vùng ngoài nhà
OUTSIDE_PROBE_Z_MM = 1500.0  # Tường tính là chắn nếu cắt qua Level + giá trị này (bỏ lan can, gờ logia)
SIDE_PROBES_MM = (250.0, 400.0, 600.0)   # Điểm dò hai phía cửa, cách mặt tường


def preview_lines(pairs, z_mm):
    try:
        clr.AddReference("ProtoGeometry")
        from Autodesk.DesignScript.Geometry import Point as DSPoint, Line as DSLine
        return [DSLine.ByStartPointEndPoint(DSPoint.ByCoordinates(a[0], a[1], z_mm),
                                            DSPoint.ByCoordinates(b[0], b[1], z_mm)) for a, b in pairs]
    except Exception:
        return []


LOG_HEADER = [u"STT", u"Bản lề (mm)", u"Bán kính cung (mm)", u"Tâm ô cửa (mm)", u"Khe tường CAD (mm)",
              u"Khuôn cửa CAD (mm)", u"Rộng (mm)", u"Tường chủ", u"Type", u"Kết quả", u"ElementId", u"Ghi chú"]


WALL_LOG_HEADER = [u"Cửa STT", u"Tường (ElementId)", u"Việc", u"Tim tường cũ (mm)", u"Tim tường mới (mm)"]


def write_log(rows, source, dry_run, wall_rows=()):
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
        if wall_rows:
            f.write(u"# Tường sửa đầu mút để phủ ô cửa\n")
            w.writerow(WALL_LOG_HEADER)
            w.writerows(wall_rows)
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
    family_name, fam_extra = parse_spec(family_name, u"D1_WO_OP1")
    template_name, tpl_extra = parse_spec(template_name, u"DW01_900X2200 2")
    symbols = door_symbols(family_name)
    template = pick_template(symbols, family_name, template_name)
    fams = {u"": (family_name, symbols, template)}
    logia_family = fam_extra.get(u"LOGIA")
    if logia_family:
        ls = door_symbols(logia_family)
        fams[u"LOGIA"] = (logia_family, ls, pick_template(ls, logia_family, tpl_extra.get(u"LOGIA") or template_name))
    level = find_level(level_name)
    walls, wall_by_id = host_walls(level)
    if not walls:
        raise StopReport([u"DỪNG: level '{}' chưa có tường thẳng nào để gắn cửa.".format(level_name)])

    all_arcs = read_arcs(objects)
    arcs = [a for a in all_arcs if a["layer"] in door_layers]
    other_arcs = [a for a in all_arcs if a["layer"] not in door_layers and arc_reject_reason(a) is None]
    segs = read_segments(objects, wall_layers)
    door_segs = read_segments(objects, door_layers)
    doors, stats = analyse(arcs, segs, door_segs, walls, round_mm, existing_doors(),
                           norm(family_name).lower() in WIDTH_FROM_GAP)

    n_logia, swap_ids = 0, set()
    if logia_family:
        grid = exterior_grid(level, doors)
        for dr in doors:
            if grid is None or dr.s_center is None:
                continue
            existing_ok = dr.status == u"Bỏ qua – ô đã có cửa" and dr.eid
            if not (dr.status == u"OK" or existing_ok) or dr.leaf.partner is not None or not opens_outside(dr, grid):
                continue
            dr.kind = u"LOGIA"
            dr.note = (dr.note + u"; " if dr.note else u"") + u"cửa ra logia → {}".format(logia_family)
            n_logia += 1
            if existing_ok:
                el = doc.GetElement(ElementId(int(dr.eid)))
                if el is not None and norm(el.Symbol.FamilyName) != norm(logia_family):
                    if owned_by_other(el.Id):
                        dr.status = u"Bỏ qua – cửa logia cũ đang bị người khác mượn"
                    else:
                        dr.status = u"DOI"
                        swap_ids.add(id(dr))

    tol = max(round_mm / 2.0, 1.0)
    planned_types = {}   # (loại, rộng) → FamilySymbol có sẵn hoặc tên type sẽ nhân bản
    rows, jobs, wall_rows, swaps = [], [], [], []
    for idx, d in enumerate(doors, 1):
        leaf = d.leaf
        if d.status == u"OK":
            busy = [i for i in set([leaf.wall.id] + [x.id for x, _, _ in d.edits]) if owned_by_other(wall_by_id[i].Id)]
            if busy:
                d.status = u"Bỏ qua – tường đang bị người khác mượn (Id {})".format(u", ".join(str(i) for i in busy))
                d.edits = []
        if d.status == u"OK":
            key = (d.kind, d.width)
            if key not in planned_types:
                f_syms, f_tpl = fams[d.kind][1], fams[d.kind][2]
                s = match_symbol(f_syms, d.width, height_mm, tol)
                planned_types[key] = s if s is not None else type_name_for(
                    get_name(f_tpl), d.width, int(round(height_mm)))
            t = planned_types[key]
            d.type_name = get_name(t) if not isinstance(t, (str, type(u""))) else t + u" (mới)"
            d.status = u"Sẽ tạo" if dry_run else u"Chờ tạo"
            jobs.append((d, len(rows)))
        elif d.status == u"DOI":
            key = (d.kind, d.width)
            if key not in planned_types:
                f_syms, f_tpl = fams[d.kind][1], fams[d.kind][2]
                s = match_symbol(f_syms, d.width, height_mm, tol)
                planned_types[key] = s if s is not None else type_name_for(
                    get_name(f_tpl), d.width, int(round(height_mm)))
            t = planned_types[key]
            d.type_name = get_name(t) if not isinstance(t, (str, type(u""))) else t + u" (mới)"
            d.status = (u"Sẽ đổi" if dry_run else u"Chờ đổi") + u" cửa cũ sang family logia"
            swaps.append((d, len(rows)))
            for x, s0, s1 in d.edits:
                wl = wall_by_id[x.id]
                p0, p1 = wall_xyz(wl)
                a, b = (x.point(s0), x.point(s1)) if x.local(xy(p0))[0] <= x.local(xy(p1))[0] else \
                    (x.point(s1), x.point(s0))
                wall_rows.append([idx, x.id, u"kéo dài (tường chủ)" if x is leaf.wall else u"cắt ngắn",
                                  u"{} → {}".format(fmt(xy(p0)), fmt(xy(p1))), u"{} → {}".format(fmt(a), fmt(b))])
        c = d.center()
        rows.append([idx, fmt(leaf.arc["c"]), u"{:.0f}".format(leaf.r), fmt(c),
                     u"{:.0f}".format(d.gap_width) if d.gap_width is not None else u"—",
                     u"{:.0f}".format(d.raw_width) if d.raw_width is not None else u"—",
                     d.width if d.width is not None else u"—",
                     u"{} ({})".format(leaf.wall.id, leaf.wall.name) if leaf.wall else u"—",
                     d.type_name or u"—", d.status, d.eid, d.note])

    created, lost = [], 0
    if not dry_run and (jobs or swaps):
        TransactionManager.Instance.ForceCloseTransaction()
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        try:
            for key in sorted(planned_types):
                kind, w = key
                t = planned_types[key]
                if isinstance(t, (str, type(u""))):
                    f_syms, f_tpl = fams[kind][1], fams[kind][2]
                    existing = [s for s in f_syms if norm(get_name(s)) == norm(t)]
                    new_type = existing[0] if existing else f_tpl.Duplicate(t)
                    set_size(new_type, w, height_mm)
                    if not existing:
                        keep_a_offset(new_type, f_tpl, w)
                    planned_types[key] = new_type
            for t in set(planned_types.values()):
                if not isinstance(t, (str, type(u""))):
                    set_family_params(t)
            for d, ri in swaps:
                sym = planned_types[(d.kind, d.width)]
                if not sym.IsActive:
                    sym.Activate()
                    doc.Regenerate()
                fi = doc.GetElement(ElementId(int(d.eid)))
                fi.ChangeTypeId(sym.Id)
                orient(fi, d.leaf.wall, d.leaf)
                rows[ri][9] = u"Đã đổi cửa cũ sang family logia"
            for d, ri in jobs:
                for x, s0, s1 in d.edits:
                    set_wall_extent(wall_by_id[x.id], x, s0, s1)
                if d.edits:
                    doc.Regenerate()
                sym = planned_types[(d.kind, d.width)]
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
                created.append((fi, ri))
            status = tx.Commit()
        except Exception as ex:
            tx.RollBack()
            return [u"LỖI khi tạo cửa, mọi thay đổi đã được hoàn tác: {}".format(ex)], []
        if status != TransactionStatus.Committed:
            return [u"LỖI: Revit không lưu được Transaction ({}), mọi thay đổi đã được hoàn tác.".format(status)], []
        for fi, ri in created:
            if not fi.IsValidObject:
                rows[ri][9] = u"Revit đã xoá sau khi tạo (không cắt được tường)"
                lost += 1

    report = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN")]
    report.append(u"CAD: {} – layer cửa: {} – layer tường: {}".format(
        cad_name, u"; ".join(sorted(door_layers)), u"; ".join(sorted(wall_layers))))
    report.append(u"Level tường chủ: {} – family: {} – cao {:.0f} mm, Sill 0 – làm tròn rộng {:.0f} mm".format(
        level.Name, family_name, height_mm, round_mm))
    if logia_family:
        report.append(u"Cửa ra logia (một phía thông ra ngoài nhà, tường cao > {:.0f} mm): {} cửa → family '{}' "
                      u"({} cửa cũ {} sang family logia) – soát cột Ghi chú".format(
                          OUTSIDE_PROBE_Z_MM, n_logia, logia_family, len(swaps), u"sẽ đổi" if dry_run else u"đã đổi"))
        if grid is not None:
            st = grid[6]
            report.append(u"Lưới dò logia: {} tường KT + {} link đang nạp ({} tường, {} cột KC){}".format(
                st["walls"], st["links"], st["link_walls"], st["link_cols"],
                u" – CẢNH BÁO: {} link chưa nạp (Unloaded), khe cột / vách KC làm phòng thông ra ngoài → nhận nhầm "
                u"cửa logia".format(st["unloaded"]) if st["unloaded"] else u""))
    report.append(u"Cung cánh cửa: {} (bỏ {} cung không phải cánh cửa) – {}: {}".format(
        stats["arcs"], stats["arc_skipped"], u"sẽ tạo" if dry_run else u"đã tạo", len(jobs)))
    counts = {}
    for d in doors:
        key = d.status.split(u" – ")[1] if d.status.startswith(u"Bỏ qua") else None
        if key:
            counts[key] = counts.get(key, 0) + 1
    for k in sorted(counts):
        report.append(u"Bỏ qua {} cửa: {}".format(counts[k], k))
    if lost:
        report.append(u"CẢNH BÁO: Revit đã xoá {} cửa ngay sau khi tạo (không cắt được tường) – xem cột Kết quả."
                      .format(lost))
    if wall_rows:
        report.append(u"Tường {} đầu mút để ô cửa nằm trọn trong tường chủ: {} lượt (tường chủ kéo dài, đoạn cùng trục "
                      u"cắt ngắn tới mép ô cửa, không xoá tường) – chi tiết cuối log:".format(
                          u"sẽ sửa" if dry_run else u"đã sửa", len(wall_rows)))
        report += [u"  Cửa {} – tường {} {}: {} ⇒ {}".format(*r) for r in wall_rows]
    report.append(u"Cung dạng cánh cửa ở layer KHÁC layer cửa: {}{}".format(
        len(other_arcs), u" ({})".format(u", ".join(u"{}: {}".format(l, n) for l, n in sorted(
            _count(a["layer"] for a in other_arcs).items()))) if other_arcs else u""))
    try:
        report.append(u"Chẩn đoán cung bị loại / ở layer khác: " + write_diagnosis(
            stats["rejected"], other_arcs, cad_name))
    except Exception as ex:
        report.append(u"Không ghi được file chẩn đoán: {}".format(ex))
    new_types = sorted(set(d.type_name for d, _ in jobs if d.type_name.endswith(u"(mới)")))
    if new_types:
        report.append(u"Type {}: {} (nhân bản từ type mẫu: {})".format(
            u"sẽ tạo" if dry_run else u"đã tạo", u", ".join(new_types),
            u", ".join(u"{} / {}".format(v[0], get_name(v[2])) for v in fams.values())))
    try:
        report.append(u"Log: " + write_log(rows, cad_name, dry_run, wall_rows))
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
            [s.strip() for s in (IN[1] or u"A-Door;A-Cửa").split(u";") if s.strip()],
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
