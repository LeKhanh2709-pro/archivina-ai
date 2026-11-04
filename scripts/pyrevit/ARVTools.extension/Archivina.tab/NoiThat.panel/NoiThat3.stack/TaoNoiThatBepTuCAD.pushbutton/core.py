# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong 26. ARV_TaoNoiThatBepTuCAD_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Đặt nội thất khu bếp trong phòng khách ăn từ mặt bằng DWG đã Link, NHẬN DIỆN THEO HÌNH DẠNG như tool 22–25 (Revit gộp nét block vào một
# GeometryInstance nên không dùng tên block). Một tool cho cả khu bếp (người dùng chọn 2026-11-02) vì đá mặt tủ lấy theo biên tủ, bếp từ và chậu
# rửa nằm trên tủ. Để trống ô type của hạng mục nào thì bỏ hạng mục đó.
#   1. Tủ lạnh = hình chữ nhật sâu 500…750, dài 850…1200 có nét dải cùng dài ngoài cạnh dài (G19: dải 50, cách 30). Dải ở phía ra phòng.
#   2. Bếp từ = hình chữ nhật 450…560 × 550…650 chứa ≥ 2 vòng tròn. Chậu rửa = polyline hở khung 650…850 × 400…520 chứa vòng thoát nước.
#   3. Tủ bếp = hình chữ nhật sâu 550…650 chứa tâm bếp từ hoặc chậu (hình không chứa gì là tủ khác, bỏ). Một hình = tủ thẳng; hai hình vuông
#      góc sát nhau = tủ chữ L. Tủ lạnh nằm trong hình tủ (G19: CH01, 04, 06, 10, 11, 14, 17) thì cắt phần đó khỏi tủ. Tủ phụ = hình tủ không có
#      bếp, chậu nhưng vuông góc và sát đầu nhánh tủ (G19: CH06, CH11, 2100 × 600 chắn giữa bếp và bàn ăn): dùng type IN[4], mặt trước quay về
#      nhánh tủ, không có đá (người dùng chốt 2026-11-02).
#   4. Lưng tủ, tủ lạnh áp mặt nhô ra phòng nhất (biên Room Finish, mặt tường, len), cách lưng CAD ≤ IN[10]; đầu tủ cách tường bên ≤ IN[11]
#      thì kéo chạm tường. Bếp từ, chậu giữ vị trí CAD dọc tường, lưng thẳng lưng tủ (mẫu FPT P4: gốc family nằm trên mặt lưng tủ).
#   5. Cỡ: tool dò tham số instance (đổi +100 mm, đo khung, hoàn tác); tên đã biết: tủ lạnh Chieu dai; tủ thẳng Chieu dai, Chieu sau; tủ L
#      chieu dai L1, chieu dai L2. Không có tham số → giữ cỡ type, báo "cần soát". Bếp từ, chậu giữ cỡ type.
#   6. Hướng family (đối chiếu mẫu FPT P4 2026-11-02): gốc giữa lưng, lưng về +Y, quay ngược → IN[14] = True. Tủ L: gốc ở góc ngoài, trục X
#      = chieu dai L1, trục Y = chieu dai L2 (10 mẫu, góc ngoài trùng góc hai tường). Tool vẫn đọc nét family trên mặt bằng để xác nhận, góc
#      khung không có nét là góc trong; không đọc được thì lấy góc ngoài ở gốc. Mọi góc L đạt được bằng xoay, không cần soi gương.
#   7. Cao độ: Elevation from Level = đỉnh sàn tại tâm món đồ − level + IN[12] (mặc định 21 như mẫu người dùng: sàn 50, nội thất 71).
#   8. Đá mặt tủ = Floor type IN[8], biên theo tủ đã căn (6 đỉnh với tủ L), Height Offset From Level = IN[13] (mặc định 50 như mẫu). Theo mẫu FPT P4:
#      lưng theo lưng tủ, mép trước lùi IN[16] (90: tủ sâu 600, đá sâu 510), đầu không sát tường lùi IN[17] (50), đầu sát tường giữ nguyên.
#   9. Comments = "ARV-TaoNoiThatBepTuCAD <hạng mục>". Món của tool đã có mà lệch / sai hướng / sai cao độ / sai cỡ / khác type → sửa tại chỗ;
#      món cùng family người dùng tự đặt → bỏ qua. Đá của tool đã có mà khác biên → báo Id để xoá tay rồi Run lại, tool không tự xoá.
# INPUT
#   IN[0] (str)   Một phần tên bản CAD (để trống = bản CAD duy nhất trong mô hình / có layer khớp IN[1])
#   IN[1] (str)   Lọc layer, nhiều chuỗi cách ';' (khớp chuỗi con), mặc định "A-Nội thất;A-Interior"; trống = dò mọi layer
#   IN[2] (str)   Tên level đặt, VD "TẦNG 3"
#   IN[3] (str)   Type tủ lạnh, "Family : Type"; trống = bỏ hạng mục
#   IN[4] (str)   Type tủ bếp thẳng, "Family : Type"; trống = bỏ hạng mục
#   IN[5] (str)   Type tủ bếp chữ L, "Family : Type"; trống = bỏ hạng mục
#   IN[6] (str)   Type bếp từ, "Family : Type"; trống = bỏ hạng mục
#   IN[7] (str)   Type chậu rửa, "Family : Type"; trống = bỏ hạng mục
#   IN[8] (str)   Tên Floor type đá mặt tủ; trống = bỏ hạng mục
#   IN[9] (str)   Tên Room chứa khu bếp, nhiều chuỗi cách ';' (trống = mọi phòng)
#   IN[10] (float) Lưng CAD cách mặt tường tối đa để áp tường (mm), VD 100
#   IN[11] (float) Đầu tủ CAD cách tường bên tối đa để kéo chạm tường (mm), VD 100
#   IN[12] (float) Nội thất đặt cao hơn mặt sàn (mm), VD 21
#   IN[13] (float) Height Offset From Level của đá mặt tủ (mm), VD 50
#   IN[14] (bool)  Đảo hướng tủ lạnh, tủ thẳng, bếp từ, chậu: True nếu quay lưng ra phòng (mặc định False)
#   IN[15] (bool)  Dry-run: True = đặt thử, báo cáo rồi hoàn tác, không ghi vào mô hình (mặc định True)
#   IN[16] (float) Đá lùi khỏi mép trước tủ (mm), VD 90
#   IN[17] (float) Đá lùi khỏi đầu tủ không sát tường (mm), VD 50
# OUTPUT
#   OUT[0] (list[str])  Báo cáo: tóm tắt, đường dẫn log, rồi từng món
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
                                   Line, Arc, Ellipse, NurbSpline, HermiteSpline, Curve, CurveLoop, XYZ, Transaction, SubTransaction,
                                   Floor, FloorType, ViewPlan, TransactionStatus, UnitUtils, UnitTypeId, StorageType, ModelPathUtils,
                                   BuiltInParameter, BuiltInCategory, Level, Wall, LocationCurve, LocationPoint, FamilySymbol,
                                   FamilyPlacementType, ElementTransformUtils, SpatialElementBoundaryOptions,
                                   SpatialElementBoundaryLocation, ElementId, Solid, WorksharingUtils, CheckoutStatus)
    from Autodesk.Revit.DB.Structure import StructuralType
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    from System.Collections.Generic import List
    doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = u"ARV - Tạo nội thất bếp từ CAD"
SCRIPT_TAG = u"ARV_TaoNoiThatBepTuCAD_v1"
COMMENT_TAG = u"ARV-TaoNoiThatBepTuCAD"
MAX_EDGE_MM = 4000.0             # Nét dài hơn không thể là nét đồ nội thất – bỏ khi đọc CAD
SNAP_MM = 1.0                    # Đầu mút cách nhau ≤ chừng này coi là nối nhau
RIGHT_COS = 0.02                 # Góc vuông: |cos| ≤ chừng này (lệch ≤ ~1°)
PARALLEL_COS = 0.995             # Mặt song song / vuông góc: |cos| ≥ chừng này
EDGE_TOL_MM = 5.0                # Cạnh của hình chữ nhật lệch vị trí tối đa
SAME_LEN_MM = 10.0               # Hai cạnh đối của hình chữ nhật lệch dài tối đa
EDGE_MIN_MM = 300.0              # Cạnh ngắn nhất cần ghép
EDGE_MAX_MM = 3800.0             # Cạnh dài nhất cần ghép (tủ thẳng + tủ lạnh, G19: 3485)
SAME_MM = 100.0                  # Hai hình cùng loại có tâm cách ≤ chừng này = cùng một món
GRID_MM = 1000.0                 # Ô lưới tra nét theo vị trí
EXIST_TOL_MM = 500.0             # Món cùng family có tâm cách tâm sẽ đặt ≤ chừng này → đã có
TOP_MM = 1000.0                  # Tường có chân cao hơn level chừng này không vướng
ROOM_INSET_MM = 5.0              # Kiểm tra món đồ nằm trong Room: thu khung vào chừng này
PROBE_MM = 100.0                 # Bước dò tham số dài của family
FIT_TOL_MM = 2.0                 # Cỡ đặt được lệch đích tối đa, quá thì báo cần soát
L_GAP_MM = 100.0                 # Hai nhánh tủ cách nhau tối đa để ghép chữ L
NOTCH_MM = 200.0                 # Góc khung cách nét family ≥ chừng này = góc trong chữ L
BODY_MM = 60.0                   # Các góc khác cách nét family ≤ chừng này
STONE_TOL_MM = 2.0               # Biên đá lệch tối đa để coi là đã đúng

# Nhận diện: (cạnh ngắn min, max, cạnh dài min, max)
SIZE_FRIDGE = (500.0, 750.0, 850.0, 1200.0)
SIZE_HOB = (450.0, 560.0, 550.0, 650.0)
SIZE_SINK = (400.0, 520.0, 650.0, 850.0)
SIZE_CABINET = (550.0, 650.0, 580.0, EDGE_MAX_MM)
STRIP_GAP = (10.0, 130.0)        # Nét dải tủ lạnh cách cạnh dài (G19: 30 và 80)
RING_MM = 100.0                  # Vòng bếp từ đường kính tối thiểu
DRAIN_MM = (50.0, 130.0)         # Vòng thoát nước chậu rửa đường kính (G19: 75)

FRIDGE, STRAIGHT, CORNER, EXTRA, HOB, SINK, STONE = u"TU LANH", u"TU THANG", u"TU L", u"TU PHU", u"BEP TU", u"CHAU RUA", u"DA MAT TU"
KIND_NAMES = {FRIDGE: u"Tủ lạnh", STRAIGHT: u"Tủ bếp thẳng", CORNER: u"Tủ bếp chữ L", EXTRA: u"Tủ bếp phụ", HOB: u"Bếp từ", SINK: u"Chậu rửa",
              STONE: u"Đá mặt tủ"}
KIND_ORDER = (FRIDGE, STRAIGHT, CORNER, EXTRA, HOB, SINK, STONE)
KIND_INPUT = {FRIDGE: u"IN[3]", STRAIGHT: u"IN[4]", CORNER: u"IN[5]", HOB: u"IN[6]", SINK: u"IN[7]"}
# Tham số cỡ đã biết của family (không có GUID nên phải theo tên): khung không phản ứng khi dò thì vẫn thử đặt, set_size báo nếu không đạt
SIZE_NAMES = {FRIDGE: {u"Chieu dai": "X"}, STRAIGHT: {u"Chieu dai": "X", u"Chieu sau": "Y"}, EXTRA: {u"Chieu dai": "X", u"Chieu sau": "Y"},
              CORNER: {u"chieu dai L1": "X", u"chieu dai L2": "Y"}}


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


def add_note(p, text):
    p.note = u"; ".join(v for v in (p.note, text) if v)


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


def box_rect(x0, y0, x1, y1):
    return Rect([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


class Piece(object):
    """Một món đồ nhận diện được + món sẽ đặt. Hệ trục riêng: gốc = giữa lưng CAD, dir = hướng ra phòng, u = dọc tường;
    s = toạ độ dọc tường, d = toạ độ ra phòng (lưng CAD d = 0)."""

    def __init__(self, kind, rect, d, sure):
        self.kind, self.rect, self.c, self.corners, self.sure = kind, rect, rect.c, rect.corners, sure
        along_short = abs(dot(d, rect.across)) > 0.5
        self.width = rect.long if along_short else rect.short
        self.depth = rect.short if along_short else rect.long
        self.set_dir(d)
        self.mount_d = 0.0       # mặt dựa (d)
        self.s0, self.s1 = -self.width / 2.0, self.width / 2.0     # hai đầu sẽ đặt (s)
        self.final = None        # khung sau khi căn (s0, s1, d0, d1)
        self.walled = set()      # đầu tủ sát tường: −1 (s0), 1 (s1)
        self.outline = None      # tủ, đá: đỉnh biên (x, y mm)
        self.stone = None        # tủ: đỉnh biên đá mặt tủ
        self.boxes = None        # tủ L: khung từng nhánh
        self.room, self.number, self.hit = u"", u"", None
        self.status, self.eid, self.note = u"", u"", u""
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

    def target_s(self):
        return (self.s0 + self.s1) / 2.0

    def goal(self):
        """Tâm món sẽ đặt."""
        return self.world(self.target_s(), self.mount_d + self.depth / 2.0)

    def box(self):
        """Khung sẽ đặt (x0, y0, x1, y1)."""
        a, b = self.world(self.s0, self.mount_d), self.world(self.s1, self.mount_d + self.depth)
        return min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])


class Index(object):
    """Tra nét theo vị trí: mỗi đoạn thẳng / nét cong ghi vào ô lưới chứa các điểm của nó."""

    def __init__(self, items):
        self.segs, self.curves = {}, {}
        for it in items:
            if it.curved:
                self.add(self.curves, it.pts[0], it)
                continue
            for k in range(1, len(it.pts)):
                a, b = it.pts[k - 1], it.pts[k]
                if math.hypot(*sub(b, a)) >= 1.0:
                    self.add(self.segs, a, (a, b))

    @staticmethod
    def add(cells, p, v):
        cells.setdefault((int(p[0] // GRID_MM), int(p[1] // GRID_MM)), []).append(v)

    @staticmethod
    def around(cells, p, reach):
        n = int(reach // GRID_MM) + 1
        cx, cy = int(p[0] // GRID_MM), int(p[1] // GRID_MM)
        return [v for dx in range(-n, n + 1) for dy in range(-n, n + 1) for v in cells.get((cx + dx, cy + dy), [])]

    def curves_in(self, r):
        return [it for it in self.around(self.curves, r.c, r.long / 2.0) if all(r.contains(p) for p in it.pts)]


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


def span(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return max(xs) - min(xs), max(ys) - min(ys)


def is_ring(it, lo, hi):
    """Nét cong khép kín đường kính lo…hi."""
    if len(it.pts) < 12 or not same(it.pts[0], it.pts[-1]):
        return False
    return lo <= min(span(it.pts)) and max(span(it.pts)) <= hi


def fridge_front(r, idx):
    """Hướng ra phòng của tủ lạnh (về phía nét dải); None nếu không có nét dải."""
    for a, b in idx.around(idx.segs, r.c, r.long):
        if abs(math.hypot(*sub(b, a)) - r.long) > SAME_LEN_MM or abs(dot(unit(sub(b, a)), r.along)) < PARALLEL_COS:
            continue
        m = sub(((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0), r.c)
        t = dot(m, r.across)
        if STRIP_GAP[0] <= abs(t) - r.short / 2.0 <= STRIP_GAP[1] and abs(dot(m, r.along)) <= EDGE_TOL_MM * 6:
            return r.across if t > 0 else (-r.across[0], -r.across[1])
    return None


def is_hob(r, idx):
    return sum(1 for it in idx.curves_in(r) if is_ring(it, RING_MM, r.long)) >= 2


def sink_rects(items, idx):
    """[Rect] khung chậu rửa: polyline khung có khe vòi nên không ghép cạnh được, nhận theo khung bao + vòng thoát nước."""
    result = []
    for it in items:
        if it.curved or not 5 <= len(it.pts) <= 8:
            continue
        xs, ys = [p[0] for p in it.pts], [p[1] for p in it.pts]
        r = box_rect(min(xs), min(ys), max(xs), max(ys))
        if r.fits(SIZE_SINK) and any(is_ring(c, DRAIN_MM[0], DRAIN_MM[1]) for c in idx.curves_in(r)):
            result.append(r)
    return result


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


def fit_back(p, segs, tol):
    """Mặt dựa. Hướng chưa chắc (tủ bếp) → thử cạnh dài đối diện, cạnh gần tường hơn là lưng. Trả về ghi chú."""
    if p.sure:
        d = mount_offset(p, segs, tol)
        if d is None:
            return u"không có tường sau lưng (≤ {:.0f} mm) – giữ theo CAD, cần soát".format(tol)
        p.mount_d = d
        return u""
    best = None
    first = p.dir
    for dr in (first, (-first[0], -first[1])):
        p.set_dir(dr)
        d = mount_offset(p, segs, tol)
        if d is not None and (best is None or abs(d) < abs(best[0])):
            best = (d, dr)
    if best is None:
        p.set_dir(first)
        return u"không có tường quanh tủ – giữ theo CAD, hướng cần soát"
    p.mount_d = best[0]
    p.set_dir(best[1])
    return u""


def fit_sides(p, segs, tol):
    """Tường bên: mặt vuông góc mặt dựa, chạm dải chiều sâu, cách đầu CAD ≤ tol, nhô vào món đồ nhất; kéo hai đầu tới đó."""
    half = p.width / 2.0
    best = {}
    for sg in segs:
        sa, da = p.local(sg.a)
        sb, db = p.local(sg.b)
        ln = math.hypot(sb - sa, db - da)
        if ln < 1.0 or abs(db - da) / ln < PARALLEL_COS:
            continue
        if max(da, db) < p.mount_d + 1.0 or min(da, db) > p.mount_d + p.depth:
            continue
        s = (sa + sb) / 2.0
        side = 1 if s > 0 else -1
        if abs(abs(s) - half) <= tol and (side not in best or abs(s) < abs(best[side])):
            best[side] = s
    p.s0 = best.get(-1, p.s0)
    p.s1 = best.get(1, p.s1)
    p.walled = set(best)


def cut_fridge(arm, fridge):
    """Hình tủ bếp vẽ trùm tủ lạnh (G19: CH01, 04, 06, 10, 11, 14, 17): cắt đầu tủ tới mép tủ lạnh."""
    ss, ds = zip(*[arm.local(q) for q in fridge.corners])
    if min(ds) >= arm.mount_d + arm.depth - 1.0 or max(ds) <= arm.mount_d + 1.0 or min(ss) >= arm.s1 - 1.0 or max(ss) <= arm.s0 + 1.0:
        return
    if (min(ss) + max(ss)) / 2.0 < arm.target_s():
        arm.s0 = max(arm.s0, max(ss))
        arm.walled.discard(-1)
    else:
        arm.s1 = min(arm.s1, min(ss))
        arm.walled.discard(1)


def rect_outline(p):
    x0, y0, x1, y1 = p.box()
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def stone_rect(p, front, end):
    """Biên đá tủ thẳng: mép trước lùi front, đầu không sát tường lùi end."""
    s0 = p.s0 + (0.0 if -1 in p.walled else end)
    s1 = p.s1 - (0.0 if 1 in p.walled else end)
    d0, d1 = p.mount_d, p.mount_d + p.depth - front
    return [p.world(s0, d0), p.world(s1, d0), p.world(s1, d1), p.world(s0, d1)]


def end_touch(r, a):
    """Hình r vuông góc nhánh tủ a và sát một đầu nhánh."""
    if abs(dot(r.along, a.rect.along)) > RIGHT_COS:
        return False
    q = sub(r.c, a.rect.c)
    return abs(abs(dot(q, a.rect.along)) - a.rect.long / 2.0 - r.short / 2.0) <= EDGE_TOL_MM and abs(dot(q, a.rect.across)) <= r.long / 2.0


def far_end(p, axis, corner):
    """(toạ độ đầu nhánh xa góc, đầu đó có sát tường) theo trục axis (0 = X, 1 = Y)."""
    d = p.mount_d
    ends = [(p.world(p.s0, d)[axis], -1), (p.world(p.s1, d)[axis], 1)]
    v, side = max(ends, key=lambda e: abs(e[0] - corner))
    return v, side in p.walled


def join_corner(a, b, front, end):
    """Piece tủ L từ hai nhánh vuông góc đã căn (a, b); None nếu không ghép được. Mọi góc tính từ lưng hai nhánh."""
    if abs(dot(a.dir, b.dir)) > RIGHT_COS:
        return None
    h, v = (a, b) if abs(a.dir[1]) > 0.5 else (b, a)     # h: nhánh chạy theo X, v: nhánh chạy theo Y
    hb, vb = h.box(), v.box()
    cy = h.world(h.target_s(), h.mount_d)[1]
    cx = v.world(v.target_s(), v.mount_d)[0]
    far_x, wall_x = far_end(h, 0, cx)
    far_y, wall_y = far_end(v, 1, cy)
    fy = cy + h.dir[1] * h.depth
    fx = cx + v.dir[0] * v.depth
    if not hb[0] - L_GAP_MM <= fx <= hb[2] + L_GAP_MM or not vb[1] - L_GAP_MM <= fy <= vb[3] + L_GAP_MM:
        return None
    outline = [(cx, cy), (far_x, cy), (far_x, fy), (fx, fy), (fx, far_y), (cx, far_y)]
    x0, x1, y0, y1 = min(cx, far_x), max(cx, far_x), min(cy, far_y), max(cy, far_y)
    p = Piece(CORNER, box_rect(x0, y0, x1, y1), h.dir, True)
    p.outer = (1 if cx > far_x else -1, 1 if cy > far_y else -1)     # hướng góc ngoài so với tâm khung
    p.outline = outline
    # Đá mặt tủ: mép trong lùi front, đầu nhánh không sát tường lùi end
    sx = far_x + (0.0 if wall_x else math.copysign(end, cx - far_x))
    sy = far_y + (0.0 if wall_y else math.copysign(end, cy - far_y))
    ifx, ify = cx + v.dir[0] * (v.depth - front), cy + h.dir[1] * (h.depth - front)
    p.stone = [(cx, cy), (sx, cy), (sx, ify), (ifx, ify), (ifx, sy), (cx, sy)]
    p.boxes = [(x0, min(cy, fy), x1, max(cy, fy)), (min(cx, fx), y0, max(cx, fx), y1)]
    return p


def sort_key(p):
    return (p.number, KIND_ORDER.index(p.kind), -round(p.c[1]), round(p.c[0]))


def place_on(kind, r, arms):
    """Piece bếp từ, chậu: hướng theo nhánh tủ chứa tâm, lưng thẳng lưng nhánh đó; không có tủ → hướng theo cạnh ngắn, cần soát."""
    for a in arms:
        if a.rect.contains(r.c):
            p = Piece(kind, r, a.dir, True)
            p.mount_d = p.local(a.world(a.target_s(), a.mount_d))[1]
            return p
    p = Piece(kind, r, r.across, True)
    p.note = u"không nằm trên tủ bếp, hướng cần soát"
    return p


def find_kitchens(items, room_at, keys):
    """{số Room: {"hit", "fridges", "hobs", "sinks", "cabinets"}} hình nhận diện trong Room khớp keys."""
    idx = Index(items)
    rects = [Rect(c) for c in edge_rects(items)]
    rects.sort(key=lambda r: -r.long * r.short)
    found = {}

    def slot(r):
        hit = room_at(r.c) if room_at is not None else None
        name = hit[0] if hit else u""
        if room_at is not None and (hit is None or (keys and not any(k in loose(name) for k in keys))):
            return None
        return found.setdefault(hit[2] if hit else u"", {"hit": hit, "fridges": [], "hobs": [], "sinks": [], "cabinets": []})

    def add(lst, r):
        if not any(math.hypot(*sub(q.c, r.c)) <= SAME_MM for q in lst):
            lst.append(r)

    for r in rects:
        if not (r.fits(SIZE_FRIDGE) or r.fits(SIZE_HOB) or r.fits(SIZE_CABINET)):
            continue
        k = slot(r)
        if k is None:
            continue
        if r.fits(SIZE_HOB) and is_hob(r, idx):
            add(k["hobs"], r)
        elif r.fits(SIZE_FRIDGE) and fridge_front(r, idx) is not None:
            add(k["fridges"], r)
        elif r.fits(SIZE_CABINET):
            add(k["cabinets"], r)
    for r in sink_rects(items, idx):
        k = slot(r)
        if k is not None:
            add(k["sinks"], r)
    return found, idx, len(rects)


def build_kitchen(k, idx, back_tol, side_tol, walls, front, end):
    """[Piece] một khu bếp."""
    hit = k["hit"]
    segs = [Seg(pts[i - 1], pts[i]) for pts in (hit[1] if hit else []) for i in range(len(pts))] + list(walls)
    pieces = []

    def stamp(p):
        p.room, p.number, p.hit = (hit[0], hit[2], hit) if hit else (u"", u"", None)
        pieces.append(p)
        return p

    fridges = []
    for r in k["fridges"]:
        p = Piece(FRIDGE, r, fridge_front(r, idx), True)
        # Không kéo đầu tủ lạnh theo tường bên: hốc tủ lạnh rộng hơn CAD thì tủ lấn sang tủ bếp (G19: CH07, CH12 lấn 90 mm)
        p.note = fit_back(p, segs, back_tol)
        fridges.append(stamp(p))
    marks = [r.c for r in k["hobs"] + k["sinks"]]
    cabinets = [r for r in k["cabinets"] if any(r.contains(c) for c in marks)]
    # Khung chậu + nét mép tủ tạo hình chữ nhật 750 × 600 nằm trong hình tủ (G19: CH06, CH11): không phải tủ
    cabinets = [r for r in cabinets if not any(q is not r and q.long > r.long and all(q.contains(c) for c in r.corners) for q in cabinets)]
    arms = []
    for r in cabinets[:2]:
        p = Piece(STRAIGHT, r, r.across, False)
        p.note = fit_back(p, segs, back_tol)
        fit_sides(p, segs, side_tol)
        for f in fridges:
            cut_fridge(p, f)
        arms.append(p)
    extras = []
    for r in k["cabinets"]:
        a = next((a for a in arms if r not in cabinets and end_touch(r, a)), None)
        if a is not None:
            # Hai cạnh dài không dựa tường: giữ theo CAD, mặt trước quay về nhánh tủ
            front_dir = r.across if dot(sub(a.rect.c, r.c), r.across) > 0 else (-r.across[0], -r.across[1])
            p = Piece(EXTRA, r, front_dir, True)
            fit_sides(p, segs, side_tol)
            extras.append(p)
    tops = []
    if len(arms) == 2:
        p = join_corner(arms[0], arms[1], front, end)
        if p is not None:
            add_note(p, u"; ".join(a.note for a in arms if a.note))
            tops.append(stamp(p))
        else:
            add_note(arms[0], u"hai nhánh tủ không ghép được chữ L, đặt hai tủ thẳng, cần soát")
    if not tops:
        tops = [stamp(a) for a in arms]
    if len(cabinets) > 2:
        add_note(tops[0], u"có {} hình tủ chứa bếp, chậu – chỉ lấy 2 hình lớn nhất, cần soát".format(len(cabinets)))
    for p in tops:
        p.outline = p.outline or rect_outline(p)
        s = stamp(Piece(STONE, p.rect, p.dir, True))
        s.outline = p.stone or stone_rect(p, front, end)
    for p in extras:
        p.outline = rect_outline(p)
        stamp(p)
    for kind, rs in ((HOB, k["hobs"]), (SINK, k["sinks"])):
        for r in rs:
            stamp(place_on(kind, r, arms))
    pieces.sort(key=sort_key)
    return pieces


def analyse(items, back_tol, side_tol, room_at=None, keys=(), walls=(), front=90.0, end=50.0):
    """items: [Item] mm; walls: [Seg] mặt tường trên level. Trả về ([Piece] đã căn, sắp theo phòng; {số Room: tên}; số hình chữ nhật)."""
    found, idx, nrect = find_kitchens(items, room_at, keys)
    pieces = []
    for number in sorted(found):
        pieces += build_kitchen(found[number], idx, back_tol, side_tol, walls, front, end)
    return pieces, found, nrect


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
    m_s = p.target_s() - (min(ss) + max(ss)) / 2.0
    m_d = p.mount_d - min(ds)
    move = (p.u[0] * m_s + p.dir[0] * m_d, p.u[1] * m_s + p.dir[1] * m_d)
    return move, (min(ss) + m_s, max(ss) + m_s, min(ds) + m_d, max(ds) + m_d)


def inside_room(p, loops):
    """Góc từng khung (thu vào ROOM_INSET_MM) nằm trong Room. Tủ L xét từng nhánh vì góc khung chung nằm ngoài chữ L."""
    k = ROOM_INSET_MM
    boxes = p.boxes
    if boxes is None:
        s0, s1, d0, d1 = p.final
        a, b = p.world(s0, d0), p.world(s1, d1)
        boxes = [(min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))]
    return all(inside_loops((x, y), loops) for b in boxes for x in (b[0] + k, b[2] - k) for y in (b[1] + k, b[3] - k))


def outer_in_family(corners_near):
    """Hướng góc ngoài chữ L trong hệ family từ {(sx, sy): khoảng cách góc khung tới nét family gần nhất}; None nếu không rõ."""
    far = [c for c, d in corners_near.items() if d >= NOTCH_MM]
    near = [c for c, d in corners_near.items() if d <= BODY_MM]
    if len(far) != 1 or len(near) != 3:
        return None
    return (-far[0][0], -far[0][1])


def turn_to(outer_fam, outer_world):
    """FacingOrientation (trục +Y family) để góc ngoài family trùng góc ngoài cần đặt: hai hướng chéo lệch nhau bội 90°."""
    a = math.atan2(outer_world[1], outer_world[0]) - math.atan2(outer_fam[1], outer_fam[0])
    return (round(-math.sin(a)), round(math.cos(a)))


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
    """Nét ngắn – ứng viên nét đồ nội thất (thẳng + cong); layers = None: mọi nét, kể cả nét Revit không trả tên layer.
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
    (+165) có thể trùm vào phòng khách (+50), còn sàn phòng khách luôn nằm trong số đó."""
    hits = [f[4] for f in floors if f[0] <= p[0] <= f[2] and f[1] <= p[1] <= f[3]]
    return min(hits) if hits else None


def stone_floors(level, tag):
    """[(x0, y0, x1, y1, Id)] đá mặt tủ của tool trên level."""
    result = []
    for fl in FilteredElementCollector(doc).OfClass(Floor).OfCategory(BuiltInCategory.OST_Floors):
        bb = fl.get_BoundingBox(None)
        cm = fl.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        if fl.LevelId == level.Id and bb is not None and cm is not None and cm.AsString() == tag:
            x0, y0 = xy(bb.Min)
            x1, y1 = xy(bb.Max)
            result.append((x0, y0, x1, y1, fl.Id.Value))
    return result


def pick_symbol(value, label):
    """Chuỗi "Family : Type" → FamilySymbol Furniture; trống → None (bỏ hạng mục)."""
    if not norm(value):
        return None
    symbols = furniture_symbols()
    families = u", ".join(sorted(set(u"{} : {}".format(s.FamilyName, get_name(s)) for s in symbols))) or u"không có"
    parts = [norm(p) for p in value.split(u":")]
    if len(parts) != 2 or not all(parts):
        raise StopReport([u"DỪNG: ô {} phải là chuỗi 'Family : Type' (đang là '{}').".format(label, value)])
    hits = [s for s in symbols if norm(s.FamilyName) == parts[0] and norm(get_name(s)) == parts[1]]
    if not hits:
        raise StopReport([u"DỪNG: không có type '{}' ({}). Type Furniture: {}".format(value, label, families)])
    sym = hits[0]
    if sym.Family.FamilyPlacementType not in (FamilyPlacementType.OneLevelBased, FamilyPlacementType.WorkPlaneBased):
        raise StopReport([u"DỪNG: family '{}' kiểu đặt {} – công cụ chỉ hỗ trợ family đặt theo level hoặc Work Plane "
                          u"Based.".format(sym.FamilyName, sym.Family.FamilyPlacementType)])
    return sym


def pick_floor_type(value):
    """Tên Floor type → FloorType; trống → None (bỏ hạng mục)."""
    if not norm(value):
        return None
    types = list(FilteredElementCollector(doc).OfClass(FloorType).ToElements())
    for t in types:
        if norm(get_name(t)) == norm(value):
            return t
    raise StopReport([u"DỪNG: không có Floor type '{}' (IN[8]). Floor type: {}".format(
        value, u", ".join(sorted(get_name(t) for t in types)))])


def plan_view(level):
    """Mặt bằng của level để đọc nét 2D family; None nếu không có."""
    for v in FilteredElementCollector(doc).OfClass(ViewPlan).ToElements():
        if not v.IsTemplate and v.GenLevel is not None and v.GenLevel.Id == level.Id:
            return v
    return None


def family_points(fi, view):
    """[(x, y mm)] điểm nét của instance trong hệ family (nét 2D chỉ có khi đọc theo view)."""
    if view is None:
        return []
    opt = Options()
    opt.View = view
    tf = fi.GetTransform().Inverse
    pts = []

    def walk(geo):
        for obj in geo:
            if isinstance(obj, GeometryInstance):
                walk(obj.GetInstanceGeometry())
            elif isinstance(obj, PolyLine):
                pts.extend(tf.OfPoint(q) for q in obj.GetCoordinates())
            elif isinstance(obj, Curve) and obj.IsBound:
                pts.extend(tf.OfPoint(q) for q in obj.Tessellate())

    geo = fi.get_Geometry(opt)
    if geo is not None:
        walk(geo)
    return [(to_mm(q.X), to_mm(q.Y)) for q in pts]


def read_outer(fi, view):
    """Góc ngoài chữ L trong hệ family (sx, sy); None nếu không đọc được từ nét family."""
    pts = family_points(fi, view)
    if len(pts) < 4:
        return None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    corners = {}
    for sx, x in ((-1, min(xs)), (1, max(xs))):
        for sy, y in ((-1, min(ys)), (1, max(ys))):
            corners[(sx, sy)] = min(math.hypot(p[0] - x, p[1] - y) for p in pts)
    return outer_in_family(corners)


def body_points(fi):
    """Khung instance trên mặt bằng (x, y mm). Không dùng khung type như tool 19: đồ kéo dài theo tham số instance nên khung type luôn là
    cỡ gốc. Family 2D có khung cao 0 nhưng vẫn có X, Y."""
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


def measure(fi):
    """{"X": cỡ theo trục X family, "Y": cỡ theo trục Y family} (mm), từ khung instance; đồ xoay bội 90° nên chiếu thẳng được."""
    pts = body_points(fi)
    if not pts:
        return None
    dx, dy = pts[2][0] - pts[0][0], pts[2][1] - pts[0][1]
    bx = fi.GetTransform().BasisX
    if abs(bx.X) >= abs(bx.Y):
        return {"X": dx, "Y": dy}
    return {"X": dy, "Y": dx}


def length_params(fi):
    """Tham số Double ghi được, không built-in. Không lọc theo SpecTypeId: Dry-run tool 24 2026-10-31 14:55 lọc Length thì không ra tham số nào."""
    return [p for p in fi.GetOrderedParameters()
            if p.StorageType == StorageType.Double and not p.IsReadOnly and p.Id.Value >= 0]


def probe_sizes(fi, names, log):
    """Dò tham số instance đổi cỡ family: tăng PROBE_MM trong SubTransaction, đo khung, hoàn tác. Trả về {trục: (Id tham số, tên, hệ số)}.
    log: [mô tả từng tham số] để đưa vào Báo cáo."""
    found = {}
    base = measure(fi)
    if base is None:
        log.append(u"không đọc được khung instance")
        return found
    params = length_params(fi)
    if not params:
        log.append(u"không có tham số Double ghi được")
    for p in params:
        st = SubTransaction(doc)
        st.Start()
        now, err, value, name = None, u"", to_mm(p.AsDouble()), p.Definition.Name
        try:
            p.Set(p.AsDouble() + from_mm(PROBE_MM))
            doc.Regenerate()
            now = measure(fi)
        except Exception as ex:
            err = u"{}".format(ex)
        st.RollBack()
        if now is None:
            log.append(u"{} = {:.0f}: lỗi {}".format(name, value, err))
            continue
        ds = dict((k, now[k] - base[k]) for k in ("X", "Y"))
        log.append(u"{} = {:.0f}: +{:.0f} → X {:+.0f}, Y {:+.0f}".format(name, value, PROBE_MM, ds["X"], ds["Y"]))
        moved = [k for k in ds if abs(ds[k]) >= 1.0]
        if len(moved) == 1 and moved[0] not in found:
            found[moved[0]] = (p.Id.Value, name, ds[moved[0]] / PROBE_MM)
    for p in params:
        axis = names.get(norm(p.Definition.Name))
        if axis is not None and axis not in found:
            found[axis] = (p.Id.Value, p.Definition.Name, 1.0)
    doc.Regenerate()
    return found


def set_size(fi, info, axis, want):
    """Đặt cỡ theo trục family về want (mm). Trả về ghi chú lỗi, rỗng nếu đạt."""
    cur = measure(fi)
    if cur is None or abs(cur[axis] - want) <= 0.5:
        return u""
    pid, name, k = info
    for p in length_params(fi):
        if p.Id.Value == pid:
            try:
                p.Set(p.AsDouble() + from_mm((want - cur[axis]) / k))
                doc.Regenerate()
            except Exception as ex:
                return u"không đặt được {} = {:.0f} ({}), cần soát".format(name, want, ex)
            now = measure(fi)
            if now is None or abs(now[axis] - want) > FIT_TOL_MM:
                return u"{} không đạt {:.0f} mm, cần soát".format(name, want)
            return u""
    return u"không thấy tham số {}, cần soát".format(name)


def existing_fixtures(level):
    """[(tâm mm, Id, Comments, tên family)] Furniture đã đặt trên level."""
    result = []
    for fi in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Furniture) \
            .WhereElementIsNotElementType().ToElements():
        sym = getattr(fi, "Symbol", None)
        if sym is None or fi.LevelId != level.Id or not isinstance(getattr(fi, "Location", None), LocationPoint):
            continue
        pts = body_points(fi)
        if pts:
            c = ((pts[0][0] + pts[2][0]) / 2.0, (pts[0][1] + pts[2][1]) / 2.0)
        else:
            c = xy(fi.Location.Point)
        cm = fi.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        result.append((c, fi.Id.Value, (cm.AsString() or u"") if cm is not None else u"", norm(sym.FamilyName)))
    return result


def elevation_param(fi):
    """Cao độ instance so với level ("Elevation from Level" / "Offset from Host")."""
    return fi.get_Parameter(BuiltInParameter.INSTANCE_ELEVATION_PARAM) or \
        fi.get_Parameter(BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM)


def size_targets(p, facing):
    """[(trục family, cỡ đích, bắt buộc)]. Tủ L: trục X family nằm theo X hay Y thế giới tuỳ hướng xoay."""
    if p.kind == FRIDGE:
        return [("X", p.s1 - p.s0, True)]
    if p.kind in (STRAIGHT, EXTRA):
        return [("X", p.s1 - p.s0, True), ("Y", p.depth, False)]
    if p.kind == CORNER:
        x0, y0, x1, y1 = p.box()
        w, h = x1 - x0, y1 - y0
        return [("X", h if abs(facing[0]) > 0.5 else w, True), ("Y", w if abs(facing[0]) > 0.5 else h, True)]
    return []


def settle(fi, p, sym, elev, flip, memo, view):
    """Trong Transaction: đổi type, đặt cỡ, xoay, đặt cao độ, dời cho khung về đúng đích. memo: thông tin family dùng chung các món cùng hạng
    mục. Trả về [việc đã làm], [ghi chú cần soát]."""
    todo, warn = [], []
    if fi.Symbol.Id != sym.Id:
        todo.append(u"đổi type {} : {}".format(fi.Symbol.FamilyName, get_name(fi.Symbol)))
        fi.ChangeTypeId(sym.Id)
    doc.Regenerate()
    if p.kind == CORNER:
        if "outer" not in memo:
            memo["outer"] = read_outer(fi, view)
        outer = memo["outer"]
        if outer is None:
            outer = (1, 1)     # Gốc family ở góc ngoài (10 mẫu FPT P4)
        facing = turn_to(outer, p.outer)
    else:
        facing = p.dir if flip else (-p.dir[0], -p.dir[1])
    targets = size_targets(p, facing)
    if targets and "sizes" not in memo:
        memo["sizes"] = probe_sizes(fi, SIZE_NAMES.get(p.kind, {}), memo.setdefault("probes", []))
    before = measure(fi)
    for axis, want, must in targets:
        info = memo["sizes"].get(axis)
        if info is not None:
            bad = set_size(fi, info, axis, want)
            if bad:
                warn.append(bad)
        elif must and before is not None and abs(before[axis] - want) > FIT_TOL_MM:
            warn.append(u"family không có tham số dài, giữ {:.0f} (đích {:.0f}), cần soát".format(before[axis], want))
    after = measure(fi)
    if before is not None and after is not None and abs(before["X"] - after["X"]) + abs(before["Y"] - after["Y"]) > 0.5:
        todo.append(u"đặt cỡ {:.0f} × {:.0f}".format(after["X"], after["Y"]))
    f = fi.FacingOrientation
    ang = math.atan2(f.X * facing[1] - f.Y * facing[0], f.X * facing[0] + f.Y * facing[1])
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
        p.final = (p.s0, p.s1, p.mount_d, p.mount_d + p.depth)
        return todo, warn + [u"không đọc được khung của family – đặt theo gốc family, cần soát"]
    move, p.final = body_fit(pts, p)
    if math.hypot(*move) > 0.5:
        ElementTransformUtils.MoveElement(doc, fi.Id, XYZ(from_mm(move[0]), from_mm(move[1]), 0.0))
        todo.append(u"dời {:.0f} mm".format(math.hypot(*move)))
    return todo, warn


def create_stone(p, ftype, level, offset, tag):
    """Floor đá mặt tủ theo biên p.outline, trả về Floor."""
    loop = CurveLoop()
    pts = [XYZ(from_mm(q[0]), from_mm(q[1]), level.Elevation) for q in p.outline]
    for i in range(len(pts)):
        loop.Append(Line.CreateBound(pts[i], pts[(i + 1) % len(pts)]))
    loops = List[CurveLoop]()
    loops.Add(loop)
    fl = Floor.Create(doc, loops, ftype.Id, level.Id, False, None, 0.0)
    fl.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(from_mm(offset))
    cm = fl.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    if cm is not None and not cm.IsReadOnly:
        cm.Set(tag)
    return fl


def outline_box(p):
    xs, ys = [q[0] for q in p.outline], [q[1] for q in p.outline]
    return min(xs), min(ys), max(xs), max(ys)


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
    path = os.path.join(folder, "TaoNoiThatBepTuCAD_CHANDOAN_{}.csv".format(datetime.datetime.now().strftime("%Y%m%d_%H%M%S")))
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

        def loop(pts):
            return [seg(pts[i - 1], pts[i]) for i in range(len(pts))]

        lines = []
        for p in pieces:
            if p.kind == STONE or p.kind == CORNER:
                lines += loop(p.outline)
                continue
            lines += loop(p.corners)
            if p.final is not None:
                s0, s1, d0, d1 = p.final
                lines += loop([p.world(s0, d0), p.world(s1, d0), p.world(s1, d1), p.world(s0, d1)])
                s = (s0 + s1) / 2.0
                lines.append(seg(p.world(s, (d0 + d1) / 2.0), p.world(s, d1 + 200.0)))
        return lines
    except Exception:
        return []


LOG_HEADER = [u"STT", u"Hạng mục", u"Tâm CAD (mm)", u"Phòng", u"Số phòng", u"Cỡ CAD (dài × sâu, mm)", u"Cỡ đặt (dài × sâu, mm)",
              u"Cao độ so với level (mm)", u"Type", u"Kết quả", u"ElementId", u"Ghi chú"]


def write_log(rows, source, dry_run):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoNoiThatBepTuCAD_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
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


def main(cad_filter, layer_filters, level_name, templates, stone_name, room_keys, back_tol, side_tol, lift, stone_offset, flip, dry_run,
         stone_front, stone_end):
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."], []
    if re.search(r"[-_]S[-_]", doc.Title or u""):
        return [u"DỪNG: tên file '{}' là mô hình Kết cấu (S) – nội thất bếp chỉ đặt trên mô hình Kiến trúc (A).".format(
            doc.Title)], []
    syms = dict((k, pick_symbol(v, KIND_INPUT[k])) for k, v in templates.items())
    syms[EXTRA] = syms[STRAIGHT]
    ftype = pick_floor_type(stone_name)
    if ftype is None and not any(syms.values()):
        raise StopReport([u"DỪNG: chưa chọn hạng mục nào (IN[3]…IN[8] đều trống)."])
    labels = dict((k, u"{} : {}".format(norm(s.FamilyName), get_name(s))) for k, s in syms.items() if s is not None)
    if ftype is not None:
        labels[STONE] = get_name(ftype)

    cad, cad_name, objects, all_layers = pick_cad(cad_filter, layer_filters)
    layers = match_layers(all_layers, layer_filters)
    level = find_level(level_name)
    level_z = to_mm(level.Elevation)
    room_at, rooms = room_finder(level)
    keys = [loose(k) for k in room_keys if k.strip()]
    if keys and not rooms:
        raise StopReport([u"DỪNG: level '{}' chưa có Room – cần Room để lọc phòng khách (hoặc để trống IN[9]).".format(level_name)])

    items, kinds = read_items(objects, layers if layer_filters else None)
    walls = wall_segs(level)
    pieces, kitchens, nrect = analyse(items, back_tol, side_tol, room_at, keys, walls, stone_front, stone_end)
    floors = level_floors(level)
    existing = existing_fixtures(level)
    stone_tag = u"{} {}".format(COMMENT_TAG, STONE)
    stones = stone_floors(level, stone_tag)
    view = plan_view(level)

    rows, jobs, fixes, chosen = [], [], [], []
    for p in pieces:
        if labels.get(p.kind) is None:
            continue
        chosen.append(p)
        tag = u"{} {}".format(COMMENT_TAG, p.kind)
        goal = p.goal()
        if p.kind == STONE:
            box = outline_box(p)
            goal = ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)
            area = 0.5 * abs(sum(p.outline[i - 1][0] * p.outline[i][1] - p.outline[i][0] * p.outline[i - 1][1]
                                 for i in range(len(p.outline)))) / 1e6
            size = u"{:.0f} × {:.0f} ({:.2f} m²)".format(box[2] - box[0], box[3] - box[1], area)
            hits = [s for s in stones if s[0] <= goal[0] <= s[2] and s[1] <= goal[1] <= s[3]]
            if hits:
                p.eid = hits[0][4]
                diff = max(abs(a - b) for a, b in zip(hits[0][:4], box))
                if diff <= STONE_TOL_MM:
                    p.status = u"Bỏ qua – đã đúng (Id {})".format(p.eid)
                else:
                    p.status = u"Bỏ qua – khác biên {:.0f} mm (Id {})".format(diff, p.eid)
                    add_note(p, u"xoá tay Id {} rồi Run lại, cần soát".format(p.eid))
            else:
                jobs.append((p, len(rows)))
                p.status = u"Sẽ tạo" if dry_run else u"Đã tạo"
        else:
            size = u"{:.0f} × {:.0f}".format(p.s1 - p.s0 if p.kind != CORNER else p.width, p.depth)
            family = norm(syms[p.kind].FamilyName)
            near = sorted((math.hypot(*sub(c, goal)), eid, cm == tag) for c, eid, cm, fam in existing
                          if (cm == tag or fam == family) and math.hypot(*sub(c, goal)) <= EXIST_TOL_MM)
            if near:
                p.eid = near[0][1]
                p.dups = [eid for _, eid, _ in near[1:]]
                p.status = u"Bỏ qua – đã có cùng family (Id {})".format(p.eid)
                if near[0][2]:
                    fi = doc.GetElement(ElementId(p.eid))
                    if WorksharingUtils.GetCheckoutStatus(doc, fi.Id) == CheckoutStatus.OwnedByOtherUser:
                        p.status = u"Bỏ qua – người khác đang mượn (Id {})".format(p.eid)
                    else:
                        fixes.append((fi, len(rows), p))
            else:
                jobs.append((p, len(rows)))
        rows.append([len(rows) + 1, KIND_NAMES[p.kind], fmt(p.c), p.room or u"—", p.number or u"—", size, u"—", u"—",
                     labels[p.kind], p.status, p.eid, u"; ".join(v for v in [p.note] + [u"TRÙNG Id {}".format(d) for d in p.dups] if v)])

    changed = 0
    created = []
    memo = dict((k, {}) for k in KIND_ORDER)
    if jobs or fixes:
        # Dry-run cũng đặt thử rồi RollBack: Báo cáo là số đo thật của family, không ghi vào mô hình
        TransactionManager.Instance.ForceCloseTransaction()
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        try:
            for s in syms.values():
                if s is not None and not s.IsActive:
                    s.Activate()
            doc.Regenerate()

            def finish(fi, ri, p, notes, elev, done):
                if p.final is not None:
                    rows[ri][6] = u"{:.0f} × {:.0f}".format(p.final[1] - p.final[0], p.final[3] - p.final[2])
                    if p.hit is not None and not inside_room(p, p.hit[1]):
                        notes = notes + [u"lòi khỏi Room, cần soát"]
                rows[ri][7] = u"{:.0f}".format(elev)
                rows[ri][9] = done
                rows[ri][10] = fi.Id.Value
                rows[ri][11] = u"; ".join(v for v in [rows[ri][11]] + notes if v)

            def height_of(p):
                top = floor_top(floors, p.goal())
                if top is None:
                    return lift, [u"không có sàn – cao độ {:.0f}, cần soát".format(lift)]
                return top + lift, []

            for fi, ri, p in fixes:
                elev, note = height_of(p)
                todo, warn = settle(fi, p, syms[p.kind], elev, flip, memo[p.kind], view)
                if todo:
                    changed += 1
                    finish(fi, ri, p, note + todo + warn, elev, u"Sẽ sửa" if dry_run else u"Đã sửa")
                else:
                    finish(fi, ri, p, note + warn, elev, u"Bỏ qua – đã đúng (Id {})".format(fi.Id.Value))
            # Family đặt theo level: Revit hiểu Z của điểm đặt là độ lệch so với level → Z = 0 rồi đặt Elevation from Level
            # (bài học tool lavabo 2026-10-30 10:16)
            for p, ri in jobs:
                if p.kind == STONE:
                    fl = create_stone(p, ftype, level, stone_offset, stone_tag)
                    rows[ri][6] = rows[ri][5]
                    rows[ri][7] = u"{:.0f}".format(stone_offset)
                    rows[ri][9] = u"Sẽ tạo" if dry_run else u"Đã tạo"
                    rows[ri][10] = u"" if dry_run else fl.Id.Value
                    created.append((fl, ri))
                    continue
                sym = syms[p.kind]
                elev, note = height_of(p)
                q = p.goal()
                if sym.Family.FamilyPlacementType == FamilyPlacementType.WorkPlaneBased:
                    pt = XYZ(from_mm(q[0]), from_mm(q[1]), level.Elevation)
                    fi = doc.Create.NewFamilyInstance(level.GetPlaneReference(), pt, XYZ(1.0, 0.0, 0.0), sym)
                else:
                    pt = XYZ(from_mm(q[0]), from_mm(q[1]), 0.0)
                    fi = doc.Create.NewFamilyInstance(pt, sym, level, StructuralType.NonStructural)
                _, warn = settle(fi, p, sym, elev, flip, memo[p.kind], view)
                cm = fi.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
                if cm is not None and not cm.IsReadOnly:
                    cm.Set(u"{} {}".format(COMMENT_TAG, p.kind))
                finish(fi, ri, p, note + warn, elev, u"Sẽ tạo" if dry_run else u"Đã tạo")
                if dry_run:
                    rows[ri][10] = u""
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
            return [u"LỖI khi đặt nội thất bếp, mọi thay đổi đã được hoàn tác: {}".format(ex)], []
        if not dry_run:
            for e, ri in created:
                if not e.IsValidObject:
                    rows[ri][9] = u"Revit đã xoá sau khi tạo"

    report = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (đã hoàn tác, không ghi vào mô hình)" if dry_run
                                else u"ĐÃ THỰC HIỆN")]
    report.append(u"CAD: {} – dò {} – {} nét – {} hình chữ nhật – level {} – phòng chứa: {}".format(
        cad_name, u"layer " + u"; ".join(sorted(layers)) if layer_filters else u"mọi layer ({})".format(len(layers)),
        len(items), nrect, level.Name, u"; ".join(room_keys) if keys else u"mọi phòng"))
    report.append(u"Khu bếp nhận diện: {} phòng".format(len(kitchens)))
    job_kinds = [p.kind for p, _ in jobs]
    have = {}
    for p in pieces:
        have.setdefault(p.kind, set()).add(p.number)
    for k in KIND_ORDER:
        n = sum(1 for p in pieces if p.kind == k)
        if k in labels:
            report.append(u"{}: nhận diện {} – {} {} – {}".format(
                KIND_NAMES[k], n, u"sẽ tạo" if dry_run else u"đã tạo", job_kinds.count(k), labels[k]))
        elif n:
            report.append(u"{}: nhận diện {} – ô type trống, bỏ qua".format(KIND_NAMES[k], n))
    if fixes:
        report.append(u"Món của tool {}: {} / {}".format(u"sẽ sửa" if dry_run else u"đã sửa", changed, len(fixes)))
    if flip:
        report.append(u"Đảo hướng: có (tủ lạnh, tủ thẳng, bếp từ, chậu)")
    for k in (FRIDGE, STRAIGHT, CORNER, EXTRA):
        info = memo[k]
        for axis in ("X", "Y"):
            if info.get("sizes", {}).get(axis):
                report.append(u"{}: tham số cỡ trục {} = {} (×{:.2f})".format(
                    KIND_NAMES[k], axis, info["sizes"][axis][1], info["sizes"][axis][2]))
        if info.get("probes"):
            report.append(u"{}: dò tham số: {}".format(KIND_NAMES[k], u"; ".join(info["probes"])))
    if "outer" in memo[CORNER]:
        report.append(u"Tủ L: góc ngoài trong family {}".format(memo[CORNER]["outer"] or u"không đọc được nét, lấy (1, 1) theo mẫu FPT P4"))
    if keys:
        numbers = sorted(r[3] for r in rooms if any(k in loose(r[2]) for k in keys))
        for k in (FRIDGE, HOB, SINK):
            lack = [n for n in numbers if n not in have.get(k, ())]
            report.append(u"Phòng lọc không có {} trên CAD: {}".format(KIND_NAMES[k].lower(), u", ".join(lack) or u"không"))
        lack = [n for n in numbers if n not in have.get(STRAIGHT, ()) and n not in have.get(CORNER, ())]
        report.append(u"Phòng lọc không có tủ bếp trên CAD: {}".format(u", ".join(lack) or u"không"))
    dups = [(p, d) for p in chosen for d in p.dups]
    if dups:
        report.append(u"TRÙNG: {} món thừa cạnh nhau – xoá tay (giữ Id trong ngoặc): {}".format(
            len(dups), u", ".join(u"{} (giữ {})".format(d, p.eid) for p, d in dups)))
    soat = [r for r in rows if u"cần soát" in u"{}".format(r[11])]
    if soat:
        report.append(u"CẦN SOÁT: {} món – xem cột Ghi chú".format(len(soat)))
    skip = sum(1 for r in rows if u"{}".format(r[9]).startswith(u"Bỏ qua – đã có"))
    if skip:
        report.append(u"Bỏ qua {} món người dùng đã đặt cùng family".format(skip))
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
        report.append(u"Soát hướng trên mặt bằng: quay ngược → Undo mục \"{}\", IN[14] = True, Run lại.".format(TRANSACTION_NAME))
    report.append(u" | ".join(LOG_HEADER))
    report += [u" | ".join(u"{}".format(v) for v in r) for r in rows]
    return report, preview_lines([p for p, _ in jobs] + [f[2] for f in fixes], level_z)


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


def text(i, default):
    """Ô chuỗi: None (chưa nối) → mặc định; chuỗi trống → trống (bỏ hạng mục)."""
    return default if len(IN) <= i or IN[i] is None else IN[i]


if DYNAMO:
    import traceback
    try:
        OUT = list(main(
            (IN[0] or u"").strip(),
            [s.strip() for s in text(1, u"A-Nội thất;A-Interior").split(u";") if s.strip()],
            (IN[2] or u"TẦNG 3"),
            {FRIDGE: text(3, u"AV_FT_tu lanh : AV_FT_tu lanh"),
             STRAIGHT: text(4, u"AV_FT_tu bep dai : AV_FT_tu bep dai"),
             CORNER: text(5, u"AV_FT_tu bep chu L : chieu sau L2"),
             HOB: text(6, u"AV_FT_bep tu 3 : AV_FT_bep tu"),
             SINK: text(7, u"AV_FT_chau rua1 : AV_FT_chau rua 2")},
            text(8, u"FA_FF_M40-TL10_Ceramic600x600_MauSang"),
            text(9, u"phòng khách").split(u";"),
            num(10, 100.0),
            num(11, 100.0),
            num(12, 21.0),
            num(13, 50.0),
            False if IN[14] is None else bool(IN[14]),
            True if IN[15] is None else bool(IN[15]),
            num(16, 90.0),
            num(17, 50.0),
        ))
    except StopReport as ex:
        OUT = [ex.lines, []]
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], []]
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with io.open(os.path.join(folder, "TaoNoiThatBepTuCAD_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))), "w", encoding="utf-8-sig") as f:
                f.write(u"\n".join(OUT[0]))
        except Exception:
            pass
    note = force_rerun_next_time()
    if note:
        OUT[0].append(u"LƯU Ý: " + note)
