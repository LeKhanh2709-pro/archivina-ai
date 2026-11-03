# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong 15. ARV_TaoSenTamTuCAD_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Tạo sen tắm (Plumbing Fixtures) từ mặt bằng DWG đã Link, NHẬN DIỆN THEO HÌNH DẠNG (không cần biết layer):
#   1. Sen tắm trên CAD = Ô VUÔNG có NÉT ỐNG chạy ra tường (đo trên G19 TẦNG 3 2026-10-30: layer A-Interior WC,
#      polyline kín 250×250 + 2 nét thẳng song song cách 20 mm dài 285 mm, một đầu trong ô vuông, đầu kia chạm mặt
#      tường; 24/24 ô vuông 250 trong WC đều có nét ống):
#      - ô vuông: vòng kín 4 góc vuông, cạnh trong [IN[5], IN[6]] (mặc định 200–400), hai cạnh lệch ≤ 15 %;
#      - nét ống: nét thẳng dài 50–1000 mm, một đầu trong ô vuông, đầu kia ngoài, song song cạnh ô vuông. Hướng nét ống
#        (từ ô vuông ra ngoài) = hướng ra tường gắn sen. Ô vuông không có nét ống (phễu thu, hộp kỹ thuật…) → bỏ.
#      IN[1] trống = dò mọi layer; có chuỗi = chỉ layer chứa chuỗi đó.
#   1b. Buồng tắm góc CHƯA VẼ ký hiệu sen (G19 TẦNG 3: 8 WC): Room WC không có ký hiệu sen nhưng có tấm kính CAD đầu
#      chạm tường (≤ 30 mm, cho phép chạm góc giật cột) → sen gắn lên tường mà TẤM KÍNH DÀI HƠN chạm (người dùng chỉ
#      2026-10-30: WC có cửa sổ → tường đặc bên cạnh, tấm 632 mm; WC không cửa sổ → tường tấm 567 mm), vị trí dọc
#      tường luôn giữa hai biên gần nhất (bước 4). Ghi chú "buồng tắm góc chưa có ký hiệu sen CAD".
#   2. Room chứa tâm ô vuông phải có tên chứa một chuỗi trong IN[4] (mặc định "WC;vệ sinh"; trống = mọi phòng).
#   3. Mặt gắn: mặt song song tường gần ô vuông nhất theo hướng nét ống, quanh đầu nét ống (± 150 mm), lấy trong biên
#      Room ở mặt hoàn thiện (Finish – gồm cả tường link KC) và mặt tường Revit trên level IN[2] (gồm lớp ốp mỏng) →
#      sen áp mặt lớp hoàn thiện.
#   4. Vị trí dọc tường (yêu cầu người dùng 2026-10-30): GIỮA VÁCH KÍNH TẮM và MẶT TƯỜNG HOÀN THIỆN đối diện. Biên
#      hai bên = mặt vuông góc với mặt gắn, chạm dải 300 mm trước mặt gắn, gần tâm ô vuông nhất mỗi phía:
#      - vách kính CAD: vòng kín chữ nhật dày ≤ IN[7] (mặc định 30), dài 300–3000 mm (G19: polyline 10 × 532…710);
#        tường Revit có tên chứa "kinh" / "glass" cũng coi là vách kính;
#      - tường: biên Room (Finish), mặt tường Revit, lớp ốp.
#      Có vách kính ở ít nhất một phía → tâm sen = giữa hai biên. Không có vách kính / thiếu biên / phải dời > IN[8]
#      (mặc định 300 mm) → giữ theo tâm ô vuông CAD và ghi chú để soát.
#   5. Type: chọn ở IN[3] (node Family Types hoặc chuỗi "Family : Type", VD "AV- Shower : Sen Tắm"). Dùng thẳng type,
#      không nhân bản. Cao độ instance (Elevation from Level) = IN[9] (mặc định 900 – lần chạy 2026-10-30 đặt 0 thì
#      vòi chìm 160 mm dưới sàn: hình family nằm −160…+1103 mm so với gốc, đặt 900 → 740…2003 mm).
#   6. Family đặt theo level: đặt tại điểm trên mặt gắn, xoay mặt trước (+Y family) ra khỏi tường; IN[10] = True nếu
#      family quay ngược. Family gắn tường ("AV- Shower" là family gắn tường): gắn vào tường Revit ngay sau mặt gắn
#      (không có → bỏ qua), Revit tự đưa điểm về tim tường; phía tường do Revit chọn theo hướng tường, KHÔNG theo điểm
#      đặt (lần chạy 2026-10-30: 13/24 sen lọt sang Logia / phòng bên). Nay: kiểm tra phía theo tâm bbox sen so với
#      tim tường; sai phía → flipFacing trong SubTransaction (family phải có Flip Control – người dùng thêm Double Flip
#      Vertical vào "AV- Shower" 2026-10-30). Không dùng Mirror ("Can't mirror an instance without its host") và
#      không dùng overload có hướng tham chiếu (tạo sen KHÔNG CÓ LEVEL ở cao độ dự án 0, lần chạy 14:02) – sen lỗi đó
#      của tool được xoá rồi tạo lại. Vẫn sai phía → ghi "CÒN SAI PHÍA TƯỜNG". Comments = "ARV-TaoSenTamTuCAD".
#      Đã có sen cùng family gần đó → bỏ qua; sen của tool lệch vị trí dọc tường / sai phía / sai hướng / sai cao độ /
#      khác type → sửa tại chỗ (không xoá, không tạo lại).
# INPUT
#   IN[0] (str)   Một phần tên bản CAD (để trống = bản CAD duy nhất trong mô hình / có layer khớp IN[1])
#   IN[1] (str)   Lọc layer, nhiều chuỗi cách ';' (khớp chuỗi con); trống = dò mọi layer (mặc định)
#   IN[2] (str)   Tên level đặt sen, VD "TẦNG 3"
#   IN[3] (FamilyType | str) Type sen tắm (node Family Types, hoặc "AV- Shower : Sen Tắm")
#   IN[4] (str)   Tên Room chứa sen, nhiều chuỗi cách ';', VD "WC;vệ sinh" (trống = mọi phòng)
#   IN[5] (float) Cạnh ô vuông ký hiệu sen tối thiểu (mm), VD 200
#   IN[6] (float) Cạnh ô vuông ký hiệu sen tối đa (mm), VD 400
#   IN[7] (float) Chiều dày vách kính CAD tối đa (mm), VD 30
#   IN[8] (float) Dời dọc tường tối đa so với tâm ô vuông CAD (mm), VD 300
#   IN[9] (float) Cao độ sen so với level – Elevation from Level (mm), VD 900
#   IN[10] (bool) Đảo hướng (chỉ family đặt theo level): True nếu family có mặt trước theo −Y
#   IN[11] (bool) Dry-run: True = chỉ báo cáo + xem trước, không ghi vào mô hình (mặc định True)
# OUTPUT
#   OUT[0] (list[str])  Báo cáo: tóm tắt, đường dẫn log, rồi từng sen tắm
#   OUT[1] (list[Line]) Xem trước: ô vuông CAD, đoạn thông thủy giữa hai biên trên mặt gắn, hướng sen (mm)

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
                                   FamilyPlacementType, ElementTransformUtils, SpatialElementBoundaryOptions,
                                   SpatialElementBoundaryLocation, ElementId, SubTransaction)
    from Autodesk.Revit.DB.Structure import StructuralType
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = u"ARV - Tạo sen tắm từ CAD"
SCRIPT_TAG = u"ARV_TaoSenTamTuCAD_v1"
COMMENT_TAG = u"ARV-TaoSenTamTuCAD"
MAX_EDGE_MM = 3000.0             # Nét dài hơn không thể là cạnh ô vuông / vách kính / nét ống – bỏ khi đọc CAD
SNAP_MM = 1.0                    # Đầu mút cách nhau ≤ chừng này coi là nối nhau
MAX_LOOP_EDGES = 64
RIGHT_COS = 0.02                 # Góc vuông: |cos| ≤ chừng này (lệch ≤ ~1°)
SQUARE_RATIO = 0.15              # Hai cạnh ô vuông lệch tối đa (tỉ lệ cạnh dài)
SAME_MM = 50.0                   # Hai ô vuông có tâm cách ≤ chừng này = cùng một ký hiệu
PIPE_MIN_MM = 50.0               # Nét ống dài tối thiểu / tối đa
PIPE_MAX_MM = 1000.0
INSIDE_TOL_MM = 2.0              # Đầu nét ống lấn ra ngoài ô vuông tối đa vẫn tính là trong
ALIGN_COS = 0.98                 # Nét ống song song cạnh ô vuông: |cos| ≥ chừng này
PARALLEL_COS = 0.995             # Mặt song song / vuông góc mặt gắn: |cos| ≥ chừng này
MOUNT_TOL_MM = 150.0             # Mặt gắn cách đầu nét ống tối đa
STRIP_MM = 300.0                 # Biên hai bên phải chạm dải này trước mặt gắn
SIDE_RANGE_MM = 1500.0           # Tìm biên hai bên trong khoảng này tính từ tâm ô vuông
GLASS_MIN_MM = 300.0             # Vách kính CAD dài tối thiểu / tối đa
GLASS_MAX_MM = 3000.0
MIN_HOST_WIDTH_MM = 50.0         # Tường mỏng hơn là lớp hoàn thiện, không làm tường gắn
HOST_GAP_MM = 60.0               # Mặt tường gắn (family gắn tường) sau mặt gắn tối đa
EXIST_TOL_MM = 500.0             # Sen cùng family cách điểm đặt / tâm ô vuông ≤ chừng này → đã có
TOUCH_MM = 30.0                  # Đầu tấm kính cách mặt tường ≤ chừng này = chạm tường
TOUCH_END_MM = 60.0              # … và vượt đầu đoạn mặt tường tối đa chừng này (góc giật cột)
CORNER_DEPTH_MM = 300.0          # Buồng tắm góc không ký hiệu: điểm dò cách mặt gắn / tấm kính chừng này
CORNER_SIDE_MM = 250.0


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


def is_glass_name(name):
    n = loose(name)
    return u"kinh" in n or u"glass" in n


class Item(object):
    """Một nét CAD: danh sách điểm (mm) + có phải nét cong."""

    def __init__(self, pts, curved):
        self.pts, self.curved = pts, curved


class Seg(object):
    """Một mặt trên mặt bằng (mm): kind = "room" (biên Room Finish), "wall" (mặt tường Revit), "glass" (vách kính)."""

    def __init__(self, a, b, kind, name=u""):
        self.a, self.b, self.kind, self.name = a, b, kind, name


class HostWall(object):
    """Tường Revit trên mặt bằng (mm): trục a → b, pháp tuyến n (bên trái chiều vẽ)."""

    def __init__(self, wid, a, b, width, name=u""):
        self.id, self.a, self.b, self.width, self.name = wid, a, b, width, name
        self.length = math.hypot(b[0] - a[0], b[1] - a[1])
        self.u = unit(sub(b, a))
        self.n = (-self.u[1], self.u[0])

    def faces(self):
        h = self.width / 2.0
        kind = u"glass" if is_glass_name(self.name) else u"wall"
        return [Seg((self.a[0] + self.n[0] * k * h, self.a[1] + self.n[1] * k * h),
                    (self.b[0] + self.n[0] * k * h, self.b[1] + self.n[1] * k * h), kind, self.name) for k in (1, -1)]


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


class Shower(object):
    """Ký hiệu sen tắm nhận diện được (ô vuông CAD + nét ống) + sen sẽ đặt. Hệ trục riêng: gốc = tâm ô vuông,
    dir = hướng nét ống (ra tường gắn), u = dọc tường; s = toạ độ dọc tường, d = toạ độ về phía tường."""

    def __init__(self, corners, side):
        self.pts, self.side = corners, side
        self.c = (sum(p[0] for p in corners) / 4.0, sum(p[1] for p in corners) / 4.0)
        self.ax = unit(sub(corners[1], corners[0]))
        self.dir = None
        self.u = None
        self.pipe_d = 0.0        # đầu nét ống xa nhất (d)
        self.mount_d = 0.0       # mặt gắn (d)
        self.lo = self.hi = None  # (s, kind, tên) biên hai bên
        self.s = 0.0             # vị trí sen dọc tường (s)
        self.host = None         # HostWall gắn (family gắn tường)
        self.room = u""
        self.status = u""
        self.type_name = u""
        self.eid = u""
        self.note = u""
        self.dups = []
        self.virtual = u""       # ≠ "" = buồng tắm góc không có ký hiệu sen CAD (ghi chú)

    def set_dir(self, d):
        self.dir = d
        self.u = (-d[1], d[0])

    def local(self, p):
        q = sub(p, self.c)
        return dot(q, self.u), dot(q, self.dir)

    def world(self, s, d):
        return (self.c[0] + self.u[0] * s + self.dir[0] * d, self.c[1] + self.u[1] * s + self.dir[1] * d)

    def insert_point(self):
        return self.world(self.s, self.mount_d)

    def facing(self):
        return (-self.dir[0], -self.dir[1])

    def inside(self, p):
        q = sub(p, self.c)
        h = self.side / 2.0 + INSIDE_TOL_MM
        return abs(dot(q, self.ax)) <= h and abs(dot(q, (-self.ax[1], self.ax[0]))) <= h


def find_pipe(sh, pipes):
    """Nét ống: một đầu trong ô vuông, đầu kia ngoài, song song cạnh ô vuông. Gán hướng + đầu xa nhất; False nếu không có."""
    votes = {}
    r = sh.side + PIPE_MAX_MM
    for p0, p1 in pipes:
        if abs(p0[0] - sh.c[0]) > r or abs(p0[1] - sh.c[1]) > r:
            continue
        i0, i1 = sh.inside(p0), sh.inside(p1)
        if i0 == i1:
            continue
        a, e = (p0, p1) if i0 else (p1, p0)
        length = math.hypot(*sub(e, a))
        if not (PIPE_MIN_MM <= length <= PIPE_MAX_MM):
            continue
        v = unit(sub(e, a))
        best = None
        for ax in (sh.ax, (-sh.ax[1], sh.ax[0]), (-sh.ax[0], -sh.ax[1]), (sh.ax[1], -sh.ax[0])):
            if dot(v, ax) >= ALIGN_COS:
                best = ax
        if best is None:
            continue
        k = (round(best[0], 3), round(best[1], 3))
        far = dot(sub(e, sh.c), best)
        n, f, _ = votes.get(k, (0, 0.0, best))
        votes[k] = (n + 1, max(f, far), best)
    if not votes:
        return False
    n, far, best = max(votes.values(), key=lambda t: t[0])
    sh.set_dir(best)
    sh.pipe_d = far
    return True


def find_showers(items, min_side, max_side, stats=None):
    loops = find_loops(items)
    squares = []
    for pts in loops:
        c = rect_corners(pts)
        if c is None:
            continue
        l1, l2 = math.hypot(*sub(c[1], c[0])), math.hypot(*sub(c[2], c[1]))
        if min_side <= min(l1, l2) and max(l1, l2) <= max_side and abs(l1 - l2) <= SQUARE_RATIO * max(l1, l2):
            squares.append(Shower(c, (l1 + l2) / 2.0))
    result = []
    for sh in sorted(squares, key=lambda x: -x.side):
        if all(math.hypot(*sub(sh.c, r.c)) > SAME_MM for r in result):
            result.append(sh)
    pipes = [(it.pts[0], it.pts[-1]) for it in items if not it.curved and len(it.pts) == 2]
    found = [sh for sh in result if find_pipe(sh, pipes)]
    if stats is not None:
        stats.update(loops=len(loops), squares=len(result), no_pipe=len(result) - len(found), pipes=len(pipes))
    return found, loops


def find_glass(loops, max_t):
    """Vách kính CAD: vòng chữ nhật dày ≤ max_t, dài GLASS_MIN_MM–GLASS_MAX_MM → 2 mặt dài (Seg "glass")."""
    segs = []
    for pts in loops:
        c = rect_corners(pts)
        if c is None:
            continue
        l1, l2 = math.hypot(*sub(c[1], c[0])), math.hypot(*sub(c[2], c[1]))
        if not (min(l1, l2) <= max_t and GLASS_MIN_MM <= max(l1, l2) <= GLASS_MAX_MM):
            continue
        if l1 >= l2:
            segs += [Seg(c[0], c[1], u"glass", u"vách kính CAD"), Seg(c[2], c[3], u"glass", u"vách kính CAD")]
        else:
            segs += [Seg(c[1], c[2], u"glass", u"vách kính CAD"), Seg(c[3], c[0], u"glass", u"vách kính CAD")]
    return segs


def fit_mount(sh, segs):
    """Mặt gắn: mặt song song tường gần ô vuông nhất theo hướng nét ống, quanh đầu nét ống. Trả về lỗi hoặc None."""
    best = None
    for sg in segs:
        if sg.kind == u"glass":
            continue
        sa, da = sh.local(sg.a)
        sb, db = sh.local(sg.b)
        ln = math.hypot(sb - sa, db - da)
        if ln < 1.0 or abs(sb - sa) / ln < PARALLEL_COS:
            continue
        if not (min(sa, sb) - 1.0 <= 0.0 <= max(sa, sb) + 1.0):
            continue
        d = (da + db) / 2.0
        if sh.side / 2.0 - 10.0 <= d <= sh.pipe_d + MOUNT_TOL_MM and (best is None or d < best):
            best = d
    if best is None:
        return u"không có mặt tường / hoàn thiện ở đầu nét ống (≤ {:.0f} mm)".format(MOUNT_TOL_MM)
    sh.mount_d = best
    return None


def fit_sides(sh, segs, max_shift):
    """Biên hai bên + vị trí dọc tường: giữa vách kính và mặt tường hoàn thiện. Buồng tắm góc không ký hiệu
    (sh.virtual): luôn giữa hai biên gần nhất – biên phía vách kính có thể là góc giật cột sát tấm kính. Trả về ghi
    chú."""
    lo, hi = None, None
    for sg in segs:
        sa, da = sh.local(sg.a)
        sb, db = sh.local(sg.b)
        ln = math.hypot(sb - sa, db - da)
        if ln < 1.0 or abs(db - da) / ln < PARALLEL_COS:
            continue
        s = (sa + sb) / 2.0
        if abs(s) > SIDE_RANGE_MM or abs(s) < 1.0:
            continue
        # Phải chạm dải STRIP_MM ngay trước mặt gắn (loại cánh cửa kính mở, tường xa)
        if max(da, db) < sh.mount_d - STRIP_MM or min(da, db) > sh.mount_d - 1.0:
            continue
        if s < 0 and (lo is None or s > lo[0]):
            lo = (s, sg.kind, sg.name)
        elif s > 0 and (hi is None or s < hi[0]):
            hi = (s, sg.kind, sg.name)
    sh.lo, sh.hi = lo, hi
    sh.s = 0.0
    if lo is None or hi is None:
        return u"thiếu biên {} – giữ tâm ô vuông CAD, cần soát".format(u"hai phía" if lo is None and hi is None
                                                                         else u"một phía")
    if lo[1] != u"glass" and hi[1] != u"glass" and not sh.virtual:
        return u"không thấy vách kính (thông thủy {:.0f} mm giữa 2 tường) – giữ tâm ô vuông CAD".format(hi[0] - lo[0])
    mid = (lo[0] + hi[0]) / 2.0
    if abs(mid) > max_shift:
        return u"giữa vách kính – tường lệch CAD {:+.0f} mm > {:.0f} – giữ tâm ô vuông CAD, cần soát".format(
            mid, max_shift)
    sh.s = mid
    return u"giữa vách kính – tường (thông thủy {:.0f} mm){}".format(
        hi[0] - lo[0], u", dời {:+.0f} mm so với CAD".format(mid) if abs(mid) >= 1.0 else u"")


def fit_host(sh, walls):
    """Tường Revit (≥ MIN_HOST_WIDTH_MM) song song, mặt ngay sau mặt gắn, phủ vị trí sen – cho family gắn tường."""
    p = sh.insert_point()
    best = None
    for w in walls:
        if w.width < MIN_HOST_WIDTH_MM or abs(dot(w.u, sh.u)) < PARALLEL_COS:
            continue
        s, d = dot(sub(p, w.a), w.u), dot(sub(p, w.a), w.n)
        if not (0.0 <= s <= w.length):
            continue
        gap = abs(d) - w.width / 2.0                # mặt gắn tới mặt tường (dương = mặt gắn trước mặt tường)
        if -1.0 <= gap <= HOST_GAP_MM and (best is None or gap < best[0]):
            best = (gap, w)
    sh.host = best[1] if best else None


def find_panels(loops, max_t):
    """Tấm kính CAD (như find_glass) → [(đầu 0, đầu 1, dài)]: đầu = trung điểm cạnh ngắn."""
    panels = []
    for pts in loops:
        c = rect_corners(pts)
        if c is None:
            continue
        l1, l2 = math.hypot(*sub(c[1], c[0])), math.hypot(*sub(c[2], c[1]))
        if not (min(l1, l2) <= max_t and GLASS_MIN_MM <= max(l1, l2) <= GLASS_MAX_MM):
            continue
        mid = lambda p, q: ((p[0] + q[0]) / 2.0, (p[1] + q[1]) / 2.0)
        if l1 >= l2:
            panels.append((mid(c[1], c[2]), mid(c[3], c[0]), l1))
        else:
            panels.append((mid(c[0], c[1]), mid(c[2], c[3]), l2))
    return panels


def touching_end(panel, segs):
    """Đầu tấm kính chạm mặt tường / biên Room (vuông góc tấm kính, cách ≤ TOUCH_MM) → (đầu chạm, đầu kia) | None."""
    for e, f in ((panel[0], panel[1]), (panel[1], panel[0])):
        ax = unit(sub(e, f))
        for sg in segs:
            if sg.kind == u"glass":
                continue
            v = sub(sg.b, sg.a)
            ln = math.hypot(*v)
            if ln < 1.0 or abs(dot(v, ax)) / ln > 1.0 - PARALLEL_COS:
                continue
            # Đầu tấm kính có thể chạm đúng góc giật cột (G19: tấm 632 mm cách đầu đoạn biên Room 40 mm)
            t = dot(sub(e, sg.a), v) / (ln * ln)
            if not (-TOUCH_END_MM / ln <= t <= 1.0 + TOUCH_END_MM / ln):
                continue
            if abs(dot(sub(e, sg.a), (-v[1] / ln, v[0] / ln))) <= TOUCH_MM:
                return e, f
    return None


def corner_showers(panels, room_of, room_segs, skip_rooms):
    """Buồng tắm góc chưa vẽ ký hiệu sen (G19 TẦNG 3: 8 WC, mỗi WC 2 tấm kính cố định chạm 2 tường + cửa kính chéo).
    Sen gắn lên tường mà TẤM KÍNH DÀI HƠN chạm vào (người dùng chỉ 2026-10-30: WC có cửa sổ → tường đặc, tấm 632 mm;
    WC không cửa sổ → tường tấm 567 mm; tấm 532 mm chạm tường còn lại), vị trí dọc tường do fit_sides tính.
    room_of(pt) → khoá Room | None; room_segs[khoá] = mặt tường + biên Room; skip_rooms: Room đã có ký hiệu sen."""
    by_room = {}
    for p in panels:
        key = room_of(((p[0][0] + p[1][0]) / 2.0, (p[0][1] + p[1][1]) / 2.0))
        if key is None or key in skip_rooms:
            continue
        hit = touching_end(p, room_segs[key])
        if hit:
            by_room.setdefault(key, []).append((p[2], hit))
    result = []
    for key, touch in by_room.items():
        touch.sort(key=lambda t: -t[0])
        length, (e, f) = touch[0]
        d = unit(sub(e, f))                       # hướng ra tường gắn
        u = (-d[1], d[0])
        if len(touch) > 1:
            q = touch[1][1][0]                    # đầu chạm tường của tấm kính kia → phía buồng tắm
        else:
            # Chỉ một tấm kính chạm tường → phía buồng tắm lấy về phía trọng tâm đỉnh biên Room
            pts = [sg.a for sg in room_segs[key] if sg.kind == u"room"]
            q = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)) if pts else f
        sgn = 1.0 if dot(sub(q, e), u) >= 0 else -1.0
        c = (e[0] - d[0] * CORNER_DEPTH_MM + u[0] * sgn * CORNER_SIDE_MM,
             e[1] - d[1] * CORNER_DEPTH_MM + u[1] * sgn * CORNER_SIDE_MM)
        h = 100.0
        corners = [(c[0] + (u[0] * a + d[0] * b) * h, c[1] + (u[1] * a + d[1] * b) * h)
                   for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        sh = Shower(corners, 2 * h)
        sh.set_dir(d)
        sh.pipe_d = dot(sub(e, c), d)
        sh.virtual = u"buồng tắm góc chưa có ký hiệu sen CAD – gắn tường tấm kính {:.0f} mm chạm".format(length)
        result.append(sh)
    return result


def analyse(items, walls, min_side, max_side, max_t, max_shift, room_at=None, room_keys=(), existing=(),
            stats=None, extra_glass=()):
    """items: [Item] mm; walls: [HostWall] trên level (gồm lớp ốp mỏng); room_at(pt) → (tên, [vòng]) | None;
    existing: [(điểm mm, Id)] sen cùng family / của tool trên level. Trả về [Shower] đã gán trạng thái."""
    showers, loops = find_showers(items, min_side, max_side, stats)
    glass = find_glass(loops, max_t) + list(extra_glass)
    wall_segs = [f for w in walls for f in w.faces()]
    if stats is not None:
        stats.update(glass=len(glass) // 2)
    room_segs = {}

    def room_of(p):
        """Khoá Room (id vòng biên) chứa p, đúng tên IN[4]; ghi kèm mặt tường + biên Room."""
        hit = room_at(p) if room_at is not None else None
        if room_at is not None and hit is None:
            return None
        if hit and room_keys and not any(k in loose(hit[0]) for k in room_keys):
            return None
        key = (id(hit[1]),) if hit else ("",)
        if key not in room_segs:
            segs = list(wall_segs)
            for pts in (hit[1] if hit else []):
                segs += [Seg(pts[i - 1], pts[i], u"room", u"biên Room") for i in range(len(pts))]
            room_segs[key] = segs
        return key

    done = set()
    for sh in showers:
        if room_at is not None:
            hit = room_at(sh.c)
            sh.room = hit[0] if hit else u""
            if room_keys and not any(k in loose(sh.room) for k in room_keys):
                sh.status = u"Bỏ qua – không nằm trong phòng {} (phòng: {})".format(
                    u"/".join(room_keys), sh.room or u"không có Room")
                continue
        key = room_of(sh.c)
        if key is not None:
            done.add(key)
    extra = corner_showers(find_panels(loops, max_t), room_of, room_segs, done)
    for sh in extra:
        hit = room_at(sh.c) if room_at is not None else None
        sh.room = hit[0] if hit else u""
    if stats is not None:
        stats.update(corner=len(extra))
    showers += extra
    for sh in showers:
        if sh.status:
            continue
        segs = room_segs.get(room_of(sh.c)) or list(wall_segs)
        err = fit_mount(sh, segs)
        if err:
            sh.status = u"Bỏ qua – " + err
            continue
        note = fit_sides(sh, segs + glass, SIDE_RANGE_MM if sh.virtual else max_shift)
        if sh.virtual:
            # Không có ký hiệu CAD → "dời so với CAD" vô nghĩa
            note = re.sub(u", dời [^)]*? so với CAD", u"", note).replace(u"tâm ô vuông CAD", u"điểm dò")
        sh.note = u"; ".join(v for v in (sh.virtual, note) if v)
        fit_host(sh, walls)
        p = sh.insert_point()
        near = sorted((math.hypot(*sub(q, p)), eid) for q, eid in existing
                      if min(math.hypot(*sub(q, p)), math.hypot(*sub(q, sh.c))) <= EXIST_TOL_MM)
        if near:
            sh.eid = near[0][1]
            sh.dups = [eid for _, eid in near[1:]]
            sh.status = u"Bỏ qua – đã có sen cùng family (Id {})".format(sh.eid)
            continue
        sh.status = u"OK"
    showers.sort(key=lambda x: (-round(x.c[1]), round(x.c[0])))
    return showers


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


def read_items(objects, layers):
    """Nét ngắn (≤ MAX_EDGE_MM) trên các layer – ứng viên ô vuông, nét ống, vách kính. Trả về (items, {loại: số})."""
    items, kinds, lim = [], {}, from_mm(MAX_EDGE_MM)
    for obj in objects:
        if layer_of(obj) not in layers:
            continue
        kind = obj.GetType().Name
        kinds[kind] = kinds.get(kind, 0) + 1
        if isinstance(obj, PolyLine):
            pts = list(obj.GetCoordinates())
            if len(pts) >= 2:
                ext = max(max(p.X for p in pts) - min(p.X for p in pts), max(p.Y for p in pts) - min(p.Y for p in pts))
                if ext <= lim:
                    items.append(Item([xy(p) for p in pts], False))
        elif isinstance(obj, Curve):
            # Nét cong không dùng để nhận diện sen – bỏ cho nhanh
            if isinstance(obj, Line) and obj.IsBound and obj.Length <= lim:
                items.append(Item([xy(obj.GetEndPoint(0)), xy(obj.GetEndPoint(1))], False))
    return items, kinds


def level_walls(level):
    """Tường thẳng trên level (mọi chiều dày, gồm lớp ốp mỏng) → ([HostWall], {id: Wall})."""
    result, by_id = [], {}
    for wl in FilteredElementCollector(doc).OfClass(Wall).ToElements():
        loc = wl.Location
        if wl.LevelId == level.Id and isinstance(loc, LocationCurve) and isinstance(loc.Curve, Line):
            c = loc.Curve
            hw = HostWall(wl.Id.Value, xy(c.GetEndPoint(0)), xy(c.GetEndPoint(1)), to_mm(wl.Width), get_name(wl))
            if hw.length >= 1.0:
                result.append(hw)
                by_id[hw.id] = wl
    return result, by_id


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
    """Hàm room_at(pt mm) → (tên Room, [vòng biên Finish mm]) trên level chứa điểm, None nếu không có. Xét trên mặt
    bằng theo đường biên Room (mặt hoàn thiện – gồm cả tường link KC) như tool lavabo."""
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
        prm = r.get_Parameter(BuiltInParameter.ROOM_NAME)
        rooms.append(((min(xs), min(ys), max(xs), max(ys)), loops, prm.AsString() if prm is not None else u""))

    def room_at(p):
        for box, loops, name in rooms:
            if box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3] and inside_loops(p, loops):
                return name, loops
        return None
    return room_at, len(rooms)


def fixture_symbols():
    return [s for s in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures)
            .WhereElementIsElementType().ToElements() if isinstance(s, FamilySymbol)]


def pick_template(value):
    """IN[3]: FamilyType của node Family Types (Dynamo) hoặc chuỗi "Family : Type" → FamilySymbol sen tắm."""
    symbols = fixture_symbols()
    families = u", ".join(sorted(set(s.FamilyName for s in symbols))) or u"không có"
    if isinstance(value, str):
        parts = [norm(p) for p in value.split(u":")]
        if len(parts) != 2 or not all(parts):
            raise StopReport([u"DỪNG: ô IN[3] phải là type chọn từ node Family Types hoặc chuỗi 'Family : Type' "
                              u"(đang là '{}').".format(value)])
        hits = [s for s in symbols if norm(s.FamilyName) == parts[0] and norm(get_name(s)) == parts[1]]
        if not hits:
            raise StopReport([u"DỪNG: không có type sen tắm '{}'. Family thiết bị vệ sinh: {}".format(value, families)])
        return hits[0]
    sym = UnwrapElement(value) if value is not None else None
    if not isinstance(sym, FamilySymbol):
        raise StopReport([u"DỪNG: chưa chọn type sen tắm ở IN[3]."])
    if sym.Category is None or sym.Category.BuiltInCategory != BuiltInCategory.OST_PlumbingFixtures:
        raise StopReport([u"DỪNG: type '{} : {}' không thuộc Plumbing Fixtures. Family thiết bị vệ sinh: {}".format(
            sym.FamilyName, get_name(sym), families)])
    return sym


def existing_fixtures(family_name, level):
    """[(điểm mm, Id)] sen đã đặt trên level: cùng family, hoặc do tool tạo (Comments) bằng family khác."""
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


def broken_fixtures(level_walls_ids):
    """Sen của tool (Comments) KHÔNG CÓ LEVEL, gắn vào tường của level đang chạy – lỗi bản 2026-10-30 14:02 (tạo bằng
    overload có hướng tham chiếu: nằm ở cao độ dự án 0). Trả về [(Id, điểm mm)] để xoá rồi tạo lại."""
    result = []
    for fi in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures) \
            .WhereElementIsNotElementType().ToElements():
        cm = fi.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        if cm is None or cm.AsString() != COMMENT_TAG or fi.LevelId != ElementId.InvalidElementId:
            continue
        host = getattr(fi, "Host", None)
        if host is not None and host.Id.Value in level_walls_ids and isinstance(fi.Location, LocationPoint):
            result.append((fi.Id.Value, xy(fi.Location.Point)))
    return result


def elevation_param(fi):
    """Cao độ instance so với level ("Elevation from Level" / "Offset from Host")."""
    return fi.get_Parameter(BuiltInParameter.INSTANCE_ELEVATION_PARAM) or \
        fi.get_Parameter(BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM)


def set_elevation(fi, mm):
    p = elevation_param(fi)
    if p is not None and not p.IsReadOnly and abs(to_mm(p.AsDouble()) - mm) > 0.5:
        p.Set(from_mm(mm))


def on_room_side(fi, sh):
    """Sen gắn tường nằm đúng phía phòng: tâm bbox ở phía mặt gắn so với tim tường gắn (FacingOrientation của family
    không đáng tin – lần chạy 2026-10-30 flipFacing theo FacingOrientation không có tác dụng)."""
    bb = fi.get_BoundingBox(None)
    if bb is None or sh.host is None:
        return True
    c = ((to_mm(bb.Min.X) + to_mm(bb.Max.X)) / 2.0, (to_mm(bb.Min.Y) + to_mm(bb.Max.Y)) / 2.0)
    w = sh.host
    side = dot(sub(sh.insert_point(), w.a), w.n)      # mặt gắn nằm phía nào của tim tường
    return dot(sub(c, w.a), w.n) * side > 0


NO_FLIP_NOTE = (u"KHÔNG lật được vào phòng: family không có điều khiển lật (CanFlipFacing = False) – thêm Flip "
                u"Control (Double Flip Vertical) vào family (Family Editor: Create > Control) rồi load lại và Run lại, "
                u"hoặc lật tay")


def put_room_side(fi, sh):
    """Đưa sen gắn tường về phía phòng bằng flipFacing (trong SubTransaction, sai thì RollBack). Không dùng Mirror
    (Revit báo "Can't mirror an instance without its host") và không tạo lại theo hướng tham chiếu
    (NewFamilyInstance(điểm, type, hướng, host) không đổi được phía và tạo sen KHÔNG CÓ LEVEL ở cao độ dự án 0 – lần
    chạy 2026-10-30 14:02, Id 3379524–3379531). Trả về (ghi chú, đúng phía?)."""
    doc.Regenerate()
    if on_room_side(fi, sh):
        return u"", True
    if fi.CanFlipFacing:
        st = SubTransaction(doc)
        st.Start()
        try:
            fi.flipFacing()
            doc.Regenerate()
            if on_room_side(fi, sh):
                st.Commit()
                return u"lật phía tường (flipFacing)", True
        except Exception:
            pass
        st.RollBack()
    return NO_FLIP_NOTE, False


def orient(fi, want, pivot):
    """Xoay instance quanh trục đứng qua pivot cho FacingOrientation trùng hướng want (2D)."""
    doc.Regenerate()
    f = fi.FacingOrientation
    ang = math.atan2(f.X * want[1] - f.Y * want[0], f.X * want[0] + f.Y * want[1])
    if abs(ang) > 1e-6:
        axis = Line.CreateBound(pivot, XYZ(pivot.X, pivot.Y, pivot.Z + 1.0))
        ElementTransformUtils.RotateElement(doc, fi.Id, axis, ang)


def preview_lines(showers, z_mm):
    try:
        clr.AddReference("ProtoGeometry")
        from Autodesk.DesignScript.Geometry import Point as DSPoint, Line as DSLine

        def seg(a, e):
            return DSLine.ByStartPointEndPoint(DSPoint.ByCoordinates(a[0], a[1], z_mm),
                                               DSPoint.ByCoordinates(e[0], e[1], z_mm))
        lines = []
        for sh in showers:
            pts = sh.pts
            lines += [seg(pts[i - 1], pts[i]) for i in range(len(pts))]
            d = sh.mount_d - 20.0
            if sh.lo and sh.hi:
                lines.append(seg(sh.world(sh.lo[0], d), sh.world(sh.hi[0], d)))
            p = sh.insert_point()
            f = sh.facing()
            lines.append(seg(p, (p[0] + f[0] * 400.0, p[1] + f[1] * 400.0)))
        return lines
    except Exception:
        return []


LOG_HEADER = [u"STT", u"Tâm ô vuông CAD (mm)", u"Phòng", u"Biên trái", u"Biên phải", u"Điểm đặt (mm)", u"Type",
              u"Kết quả", u"ElementId", u"Ghi chú"]


def bound_label(b):
    if b is None:
        return u"—"
    return u"{} ({:+.0f})".format(u"vách kính" if b[1] == u"glass" else b[2] or b[1], b[0])


def write_log(rows, source, dry_run):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoSenTamTuCAD_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
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


def main(cad_filter, layer_filters, level_name, template_in, room_keys, min_side, max_side, max_t, max_shift,
         elevation, reverse, dry_run):
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."], []
    if re.search(r"[-_]S[-_]", doc.Title or u""):
        return [u"DỪNG: tên file '{}' là mô hình Kết cấu (S) – sen tắm chỉ dựng trên mô hình Kiến trúc (A).".format(
            doc.Title)], []
    sym = pick_template(template_in)
    fam = norm(sym.FamilyName)
    type_label = u"{} : {}".format(fam, get_name(sym))
    placement = sym.Family.FamilyPlacementType
    if placement not in (FamilyPlacementType.OneLevelBased, FamilyPlacementType.OneLevelBasedHosted):
        raise StopReport([u"DỪNG: family '{}' kiểu đặt {} – công cụ chỉ hỗ trợ family đặt theo level hoặc gắn tường."
                          .format(fam, placement)])
    hosted = placement == FamilyPlacementType.OneLevelBasedHosted
    cad, cad_name, objects, all_layers = pick_cad(cad_filter, layer_filters)
    layers = match_layers(all_layers, layer_filters)
    level = find_level(level_name)
    walls, wall_by_id = level_walls(level)
    room_at, n_rooms = room_finder(level)
    keys = [loose(k) for k in room_keys if k.strip()]
    if keys and not n_rooms:
        raise StopReport([u"DỪNG: level '{}' chưa có Room – cần Room để lọc sen trong WC (hoặc để trống IN[4])."
                          .format(level_name)])

    items, kinds = read_items(objects, layers)
    stats = {}
    broken = broken_fixtures(set(wall_by_id.keys()))
    showers = analyse(items, walls, min_side, max_side, max_t, max_shift, room_at, keys,
                      existing_fixtures(fam, level), stats)

    rows, jobs, fixes = [], [], []
    for idx, sh in enumerate(showers, 1):
        if sh.status == u"OK" and hosted and sh.host is None:
            sh.status = u"Bỏ qua – family gắn tường nhưng không có tường Revit ngay sau mặt gắn"
        if sh.status == u"OK":
            sh.type_name = type_label
            sh.status = u"Sẽ tạo" if dry_run else u"Chờ tạo"
            jobs.append((sh, len(rows)))
        elif sh.eid:
            # Sen của tool đã có nhưng lệch vị trí / sai phía tường / sai hướng / sai cao độ / khác type → sửa tại chỗ.
            # Chỉ sửa sen có Comments của tool; sen người dùng tự đặt giữ nguyên.
            fi = doc.GetElement(ElementId(sh.eid))
            cm = fi.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS) if fi is not None else None
            if cm is not None and cm.AsString() == COMMENT_TAG:
                todo = []
                retype = fi.Symbol.Id != sym.Id
                if retype:
                    todo.append(u"đổi type {} : {} → {}".format(fi.Symbol.FamilyName, get_name(fi.Symbol), type_label))
                ep = elevation_param(fi)
                elev = ep is not None and abs(to_mm(ep.AsDouble()) - elevation) > 1.0
                if elev:
                    todo.append(u"cao độ {:.0f} → {:.0f}".format(to_mm(ep.AsDouble()), elevation))
                cur, want_p = xy(fi.Location.Point), sh.insert_point()
                move = (want_p[0] - cur[0], want_p[1] - cur[1])
                if hosted:
                    # Sen gắn tường: Revit giữ điểm trên tim tường – chỉ dời dọc tường
                    m = dot(move, sh.u)
                    move = (sh.u[0] * m, sh.u[1] * m)
                if math.hypot(*move) > 1.0:
                    todo.append(u"dời {:.0f} mm{}".format(math.hypot(*move), u" dọc tường" if hosted else u""))
                else:
                    move = None
                f = sh.facing()
                want, side = None, False
                if hosted:
                    side = sh.host is not None and not on_room_side(fi, sh)
                    if side:
                        todo.append(u"đang nằm sai phía tường → {}".format(
                            u"lật (flipFacing)" if fi.CanFlipFacing else
                            u"family không cho lật – sẽ thử đặt lại đúng phía (thay Id, xoá sen cũ của tool)"))
                else:
                    want = (-f[0], -f[1]) if reverse else f
                    ff = fi.FacingOrientation
                    if ff.X * want[0] + ff.Y * want[1] < 0.9998:       # lệch > ~1°
                        todo.append(u"xoay {:.0f}°".format(math.degrees(math.atan2(
                            ff.X * want[1] - ff.Y * want[0], ff.X * want[0] + ff.Y * want[1]))))
                    elif not retype:
                        want = None
                if todo:
                    sh.type_name = type_label
                    sh.note = u"; ".join(v for v in [sh.note] + todo if v)
                    sh.status = u"Sẽ sửa" if dry_run else u"Chờ sửa"
                    # Đổi type: family mới có thể khác hướng gốc / phía → luôn kiểm tra lại sau khi đổi
                    fixes.append((fi, len(rows), sh, elev or retype, move, want, side or (hosted and retype), retype))
        rows.append([idx, fmt(sh.c), sh.room or u"—", bound_label(sh.lo), bound_label(sh.hi),
                     fmt(sh.insert_point()) if sh.mount_d else u"—", sh.type_name or u"—", sh.status, sh.eid,
                     u"; ".join(v for v in [sh.note] + [u"TRÙNG Id {}".format(d) for d in sh.dups] if v)])

    created = []
    if not dry_run and (jobs or fixes or broken):
        TransactionManager.Instance.ForceCloseTransaction()
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        try:
            # Sen lỗi của bản trước (không có level, nằm ở cao độ dự án 0) – chỉ sen của tool, đã liệt kê ở dry-run
            for eid, _ in broken:
                doc.Delete(ElementId(eid))
            if not sym.IsActive:
                sym.Activate()
                doc.Regenerate()
            # Revit hiểu Z của điểm đặt là độ lệch so với level → đặt Z = 0 rồi gán Elevation from Level = IN[9]
            # (bài học tool lavabo 2026-10-30 10:16)
            for fi, ri, sh, elev, move, want, side, retype in fixes:
                if retype:
                    fi.ChangeTypeId(sym.Id)
                    doc.Regenerate()
                if elev:
                    set_elevation(fi, elevation)
                if move:
                    ElementTransformUtils.MoveElement(doc, fi.Id, XYZ(from_mm(move[0]), from_mm(move[1]), 0.0))
                if want:
                    p = sh.insert_point()
                    orient(fi, want, XYZ(from_mm(p[0]), from_mm(p[1]), 0.0))
                note, ok = u"", True
                if side:
                    note, ok = put_room_side(fi, sh)
                rows[ri][7] = u"Đã sửa" if ok else u"Đã sửa – CÒN SAI PHÍA TƯỜNG"
                if note:
                    rows[ri][9] = u"; ".join(v for v in (rows[ri][9], note) if v)
            for sh, ri in jobs:
                p = sh.insert_point()
                pt = XYZ(from_mm(p[0]), from_mm(p[1]), 0.0)
                f = sh.facing()
                note, ok = u"", True
                if hosted:
                    fi = doc.Create.NewFamilyInstance(pt, sym, wall_by_id[sh.host.id], level,
                                                      StructuralType.NonStructural)
                    note, ok = put_room_side(fi, sh)
                    if ok:
                        note = u""                  # sen mới lật ngay khi tạo – không cần ghi chú
                else:
                    fi = doc.Create.NewFamilyInstance(pt, sym, level, StructuralType.NonStructural)
                    orient(fi, (-f[0], -f[1]) if reverse else f, pt)
                set_elevation(fi, elevation)
                cm = fi.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
                if cm is not None and not cm.IsReadOnly:
                    cm.Set(COMMENT_TAG)
                rows[ri][7] = u"Đã tạo" if ok else u"Đã tạo – CÒN SAI PHÍA TƯỜNG"
                rows[ri][8] = fi.Id.Value
                if note:
                    rows[ri][9] = u"; ".join(v for v in (rows[ri][9], note) if v)
                created.append((fi, ri))
            status = tx.Commit()
        except Exception as ex:
            tx.RollBack()
            return [u"LỖI khi tạo sen tắm, mọi thay đổi đã được hoàn tác: {}".format(ex)], []
        if status != TransactionStatus.Committed:
            return [u"LỖI: Revit không lưu được Transaction ({}), mọi thay đổi đã được hoàn tác.".format(status)], []
        for fi, ri in created:
            if not fi.IsValidObject:
                rows[ri][7] = u"Revit đã xoá sau khi tạo"

    report = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN")]
    report.append(u"CAD: {} – dò {} – {} nét thẳng – nhận diện {} ký hiệu sen (ô vuông có nét ống)".format(
        cad_name, u"layer " + u"; ".join(sorted(layers)) if layer_filters else u"mọi layer ({})".format(len(layers)),
        len(items), len(showers)))
    report.append(u"Sen tắm: {} ({}) – cao độ {:.0f} mm so với level {} – phòng chứa: {}".format(
        type_label, u"gắn tường" if hosted else u"đặt theo level", elevation, level.Name,
        u"; ".join(room_keys) if keys else u"mọi phòng"))
    report.append(u"Sen {}: {}".format(u"sẽ tạo" if dry_run else u"đã tạo", len(jobs)))
    if fixes:
        report.append(u"Sen của tool {}: {} (đổi type: {}, cao độ: {}, dời: {}, xoay: {}, lật phía tường: {})".format(
            u"sẽ sửa" if dry_run else u"đã sửa", len(fixes), len([1 for f in fixes if f[7]]),
            len([1 for f in fixes if f[3]]), len([1 for f in fixes if f[4]]), len([1 for f in fixes if f[5]]),
            len([1 for f in fixes if f[6]])))
    wrong = [r for r in rows if u"CÒN SAI PHÍA" in u"{}".format(r[7])]
    if wrong:
        report.append(u"CÒN SAI PHÍA TƯỜNG: {} sen (Id {}) – family không lật được bằng API; thêm Flip Control vào family "
                      u"`{}` (Family Editor: Create > Control), load lại rồi Run lại".format(
                          len(wrong), u", ".join(u"{}".format(r[8]) for r in wrong), fam))
    dups = [(sh, d) for sh in showers for d in sh.dups]
    if dups:
        report.append(u"TRÙNG: {} sen cùng family thừa cạnh nhau – xoá tay (giữ Id trong ngoặc): {}".format(
            len(dups), u", ".join(u"{} (giữ {})".format(d, sh.eid) for sh, d in dups)))
    centred = [sh for sh in showers if sh.status in (u"Sẽ tạo", u"Chờ tạo", u"Đã tạo", u"Sẽ sửa", u"Chờ sửa")]
    if broken:
        report.append(u"{} {} sen lỗi của bản trước (không có Level, nằm ở cao độ dự án 0 – chỉ sen có Comments của tool) "
                      u"rồi tạo lại đúng tầng: Id {}".format(u"Sẽ xoá" if dry_run else u"Đã xoá", len(broken),
                                                           u", ".join(u"{}".format(e) for e, _ in broken)))
    kept = [sh for sh in centred if u"giữa vách kính – tường (" not in sh.note]
    if kept:
        report.append(u"CẦN SOÁT: {} sen giữ theo tâm ô vuông CAD (không thấy vách kính / thiếu biên / lệch nhiều) – "
                      u"xem cột Ghi chú".format(len(kept)))
    counts = {}
    for sh in showers:
        if sh.status.startswith(u"Bỏ qua"):
            k = re.sub(r"[\d(].*", u"", sh.status.split(u" – ", 1)[1]).strip()
            counts[k] = counts.get(k, 0) + 1
    for k in sorted(counts):
        report.append(u"Bỏ qua {} sen: {}".format(counts[k], k))
    report.append(u"Chẩn đoán nhận diện: {} vòng kín – {} ô vuông cạnh {:.0f}–{:.0f} mm ({} không có nét ống, bỏ) – "
                  u"{} vách kính CAD (dày ≤ {:.0f} mm) – {} buồng tắm góc chưa có ký hiệu sen (thêm sen ở tường tấm "
                  u"kính dài hơn chạm) – Room trên level: {}".format(
                      stats.get("loops", 0), stats.get("squares", 0), min_side, max_side, stats.get("no_pipe", 0),
                      stats.get("glass", 0), max_t, stats.get("corner", 0), n_rooms))
    report.append(u"Đối tượng CAD theo loại: " + u", ".join(u"{} {}".format(k, v) for k, v in sorted(kinds.items())))
    try:
        report.append(u"Log: " + write_log(rows, cad_name, dry_run))
    except Exception as ex:
        report.append(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        report.append(u"Kiểm tra ô vuông + đoạn thông thủy + hướng sen (đoạn xanh trong Dynamo) và log. Thiếu sen → nới "
                      u"IN[5]–IN[7]. Đúng thì đổi Dry-run = False và Run lại. Undo bằng mục \"{}\".".format(
                          TRANSACTION_NAME))
    else:
        report.append(u"Soát hướng vài sen (quay vào tường → Undo, đổi IN[10] rồi Run lại). Undo bằng mục \"{}\"."
                      .format(TRANSACTION_NAME))
    report.append(u" | ".join(LOG_HEADER))
    report += [u" | ".join(u"{}".format(v) for v in r) for r in rows
               if not r[7].startswith(u"Bỏ qua – không nằm trong phòng")]
    return report, preview_lines([sh for sh, _ in jobs], to_mm(level.Elevation))


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
            IN[3] if IN[3] is not None else u"AV- Shower : Sen Tắm",
            (u"WC;vệ sinh" if IN[4] is None else IN[4]).split(u";"),
            num(5, 200.0),
            num(6, 400.0),
            num(7, 30.0),
            num(8, 300.0),
            num(9, 900.0),
            False if IN[10] is None else bool(IN[10]),
            True if IN[11] is None else bool(IN[11]),
        ))
    except StopReport as ex:
        OUT = [ex.lines, []]
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], []]
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with io.open(os.path.join(folder, "TaoSenTamTuCAD_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))), "w", encoding="utf-8-sig") as f:
                f.write(u"\n".join(OUT[0]))
        except Exception:
            pass
    note = force_rerun_next_time()
    if note:
        OUT[0].append(u"LƯU Ý: " + note)
