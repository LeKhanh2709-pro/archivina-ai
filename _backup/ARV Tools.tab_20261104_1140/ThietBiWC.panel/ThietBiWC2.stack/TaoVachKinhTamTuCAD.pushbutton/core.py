# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong 17. ARV_TaoVachKinhTamTuCAD_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Tạo vách kính tắm (Plumbing Fixtures) từ mặt bằng DWG đã Link, NHẬN DIỆN THEO HÌNH DẠNG, nhân bản type từ type người
# dùng chọn cho khớp chiều dài CAD. Đo trên G19 TẦNG 3 2026-10-30 (layer A-Interior WC, 30 buồng trong 32 WC):
#   1. Mốc nhận diện = CUNG MỞ CÁNH: bán kính trong [IN[6], IN[7]] (mặc định 450–900, G19: 620), góc quét 20–60°; tâm
#      cung = bản lề, một đầu cung = mép cánh khi đóng.
#      - Buồng THẲNG (18): tấm kính chữ nhật dày ≤ IN[8] (10 × 295…710) có đầu chạm mép cánh, thẳng hàng bản lề; từ bản
#        lề có thể có dải kính nhỏ tới tường (10 × 120, thân đỡ bản lề) → tuyến vách đi hết tường tới tường.
#      - Buồng VÁT GÓC (12): tấm A (10 × 532) chạm mép cánh, lệch ~45° so với cánh đóng; tấm B (10 × 482…632) chạm bản
#        lề, vuông góc tấm A; cánh đóng nằm chéo, nét cánh 620 trên CAD là cánh vẽ ở vị trí mở.
#      - KHAY VÁT GÓC (2 WC G19 không vẽ kính): polyline kín 5 cạnh, hai cạnh tường + cạnh vát 45° (950 × 900, vát 400) →
#        coi như buồng vát góc, vách theo đúng nét khay, bản lề ở tấm ngắn hơn, cánh = cạnh vát (566). Chỉ dùng cho WC
#        chưa có buồng nhận theo cung cánh.
#   2. Room chứa giữa tấm kính phải có tên chứa một chuỗi trong IN[5] (mặc định "WC;vệ sinh").
#   3. Đầu vách: CAD vẽ tới mặt tường thô, tấm kính lấn 15 mm vào lớp hoàn thiện (đo 2026-10-30: 0 hoặc 15 mm).
#      IN[11] = True: đầu tường của vách dừng ở biên Room Finish đầu tiên tính từ trong phòng, kể cả khi CAD vẽ xuyên cột
#      giật (tấm 632 / 645 của G19 lấn 250 mm); hụt biên > 40 mm thì giữ CAD, báo "CẦN SOÁT".
#   3b. Thông thủy buồng thẳng (quy định, người dùng chốt 2026-10-30): từ mặt kính phía trong buồng tới mặt hoàn thiện đối
#      diện ≥ IN[13] (mặc định 900; 0 = theo CAD). CAD G19 chỉ 805 / 855 / 870 / 970. Phía trong buồng = phía cánh mở trên
#      CAD (cánh mở vào buồng, sen nằm phía này). Thiếu thì dời cả tuyến vách ra xa tường đối diện, rồi mới cắt đầu vách
#      theo bước 3 (dời qua cột giật thì vách dài ra). Buồng góc không dời. Vách đụng thiết bị ở vị trí mới → "cần soát".
#   4. Type: IN[3] type buồng thẳng, IN[4] type buồng vát góc (để trống = bỏ dạng đó). Tham số chiều dài khai báo ở
#      IN[9] / IN[10] dạng "KHOÁ=Tên tham số;…":
#        IN[9]  khoá KINH (dài tấm kính cố định), CUA (rộng cánh), BIEN (dải kính sau bản lề), TONG (tường tới tường);
#        IN[10] khoá CANH1 (cạnh theo tấm A), CANH2 (cạnh theo tấm B), CUA (rộng cánh), CHEO (cạnh vát).
#      Tham số là của type → nhân bản type (buồng thẳng tên = tổng dài, buồng góc thay số "1000x1000" trong tên); tham
#      số instance → đặt trên từng instance. Ô trống: chỉ báo cáo, KHÔNG tạo vách.
#   5. Dry-run đọc family của dạng CHƯA KHAI tham số: EditFamily rồi đóng không lưu (tham số, công thức); đặt thử 1 instance trong Transaction rồi
#      RollBack, ghi từng khối đặc và mức đổi hộp bao khi mỗi tham số dài +100 mm → biết tham số nào điều khiển chiều dài.
#   6. Đặt buồng thẳng theo gốc family "AV-Vách Kính Tắm Thẳng" (dry-run 2026-10-30 15:04, khối đặc Y 0…10): dải sau bản
#      lề ở X −with mid…0, cánh tiếp theo về −X, kính cố định ở đầu −X → X+ của family hướng tường phía bản lề; ký hiệu
#      cánh mở về +Y (hộp bao type Y −70…529) → soi gương khi cánh CAD mở về phía kia.
#      Đặt buồng góc theo family "AV-Vách Tắm Góc 2 chieu" (dry-run 15:11): cạnh W1 chạy dọc −X từ góc vát, W2 dọc −Y, bản
#      lề ở cạnh W1 → W1 = tấm B (tấm chạm bản lề), W2 = tấm A; W đo tới MẶT NGOÀI tấm kính; D1 = cạnh vát = WD / √2
#      (431 ↔ 610). Xoay + soi gương cho hai cạnh về hai đầu tường, dời khớp hai đầu vách.
#      Comments = "ARV-TaoVachKinhTamTuCAD". Vách của tool đã có ở gần mà khác kích thước / vị trí → sửa tại chỗ: đổi type
#      + tham số instance, buồng thẳng dời cho khớp tuyến mới (buồng góc: gốc ở góc vát nên đầu kính tự về đúng chỗ).
#      Vách người dùng tự đặt → bỏ qua.
# INPUT
#   IN[0] (str)   Một phần tên bản CAD (để trống = bản CAD duy nhất trong mô hình / có layer khớp IN[1])
#   IN[1] (str)   Lọc layer, nhiều chuỗi cách ';' (khớp chuỗi con); trống = dò mọi layer (mặc định)
#   IN[2] (str)   Tên level đặt vách, VD "TẦNG 3"
#   IN[3] (FamilyType | str) Type mẫu buồng thẳng, VD "AV-Vách Kính Tắm Thẳng : 1000"
#   IN[4] (FamilyType | str) Type mẫu buồng vát góc, VD "AV-Vách Tắm Góc 2 chieu : VTG3-1000x1000"
#   IN[5] (str)   Tên Room chứa vách, nhiều chuỗi cách ';', VD "WC;vệ sinh" (trống = mọi phòng)
#   IN[6] (float) Bán kính cung mở cánh tối thiểu (mm), VD 450
#   IN[7] (float) Bán kính cung mở cánh tối đa (mm), VD 900
#   IN[8] (float) Chiều dày tấm kính CAD tối đa (mm), VD 30
#   IN[9] (str)   Tham số buồng thẳng, VD "KINH=fix right;CUA=Wight Door;BIEN=with mid" (trống = chỉ báo cáo)
#   IN[10] (str)  Tham số buồng góc, VD "CANH1=W2;CANH2=W1;CUA=WD;CHEO=D1" (trống = chỉ báo cáo)
#   IN[11] (bool) True = đầu vách theo mặt hoàn thiện (Room Finish); False = giữ đúng CAD
#   IN[12] (bool) Dry-run: True = chỉ báo cáo + xem trước, không ghi vào mô hình (mặc định True)
#   IN[13] (float) Thông thủy buồng thẳng tối thiểu (mm), VD 900; 0 = giữ vị trí CAD
# OUTPUT
#   OUT[0] (list[str])  Báo cáo: tóm tắt, tham số family, đường dẫn log, rồi từng buồng
#   OUT[1] (list[Line]) Xem trước: tuyến vách sau khi cắt + cánh mở (mm)

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
                                   Line, Arc, Curve, XYZ, Plane, Transaction, TransactionStatus, UnitUtils, UnitTypeId,
                                   ModelPathUtils, BuiltInParameter, BuiltInCategory, Level, LocationPoint,
                                   FamilySymbol, FamilyPlacementType, ElementTransformUtils, ElementId, Solid,
                                   SpatialElementBoundaryOptions, SpatialElementBoundaryLocation, ViewDetailLevel,
                                   StorageType, SpecTypeId)
    from Autodesk.Revit.DB.Structure import StructuralType
    clr.AddReference("System")
    from System.Collections.Generic import List
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = u"ARV - Tạo vách kính tắm từ CAD"
SCRIPT_TAG = u"ARV_TaoVachKinhTamTuCAD_v1"
COMMENT_TAG = u"ARV-TaoVachKinhTamTuCAD"
MAX_EDGE_MM = 3000.0             # Nét dài hơn không thể là tấm kính / cung cánh – bỏ khi đọc CAD
SNAP_MM = 1.0                    # Đầu mút cách nhau ≤ chừng này coi là nối nhau (vòng kín tấm kính)
MAX_LOOP_EDGES = 64
RIGHT_COS = 0.02                 # Góc vuông: |cos| ≤ chừng này (lệch ≤ ~1°)
GLASS_MIN_MM = 200.0             # Tấm kính CAD dài tối thiểu / tối đa
STUB_MIN_MM = 50.0               # Dải kính sau bản lề dài tối thiểu
GLASS_MAX_MM = 3000.0
SWEEP_MIN_DEG = 20.0             # Góc quét cung mở cánh (G19: 30° buồng thẳng, 45° buồng góc)
SWEEP_MAX_DEG = 60.0
ARC_TOL_MM = 3.0                 # Điểm cung lệch vòng tròn tối đa
TOUCH_MM = 35.0                  # Đầu tấm kính cách đầu cung / bản lề tối đa (G19: cung quét lố ~20 mm)
HALF_GLASS_MM = 5.0              # Nửa dày kính (tim tấm CAD tới mặt kính)
FIX_MOVE_MM = 1.0                # Vách đã có lệch tuyến mới hơn chừng này thì dời
CLEAR_BODY_MM = 1500.0           # Khối đặc thiết bị lớn hơn = vùng thông thủy, không tính vướng
CLASH_TOL_MM = 2.0               # Vách lấn hộp bao thiết bị hơn chừng này = vướng
ALIGN_COS = 0.995                # Tấm kính thẳng hàng cánh đóng / vuông góc tấm kia
TRAY_ARM_MIN_MM = 300.0          # Khay vát góc: cạnh thẳng dài tối thiểu / tối đa, cạnh vát tối thiểu / tối đa
TRAY_ARM_MAX_MM = 1300.0
TRAY_CUT_MIN_MM = 300.0
TRAY_CUT_MAX_MM = 900.0
CHAMFER_LO = 0.60                # Cánh đóng lệch tấm A ~45°: |cos| trong khoảng này
CHAMFER_HI = 0.80
SAME_MM = 100.0                  # Hai buồng có bản lề cách ≤ chừng này = cùng một buồng
FINISH_TOL_MM = 40.0             # Đầu vách hụt biên Room ≤ chừng này thì nối tới biên (lấn biên thì luôn cắt)
NEAR_MM = 40.0                   # Điểm khối family cách tuyến vách ≤ chừng này = nằm trên tuyến
EXIST_TOL_MM = 700.0             # Tâm vách cùng family cách tâm buồng ≤ chừng này → đã có
BODY_MAX_MM = 3500.0             # Khối đặc lớn hơn (trên mặt bằng) không phải vách kính – bỏ
PLANE_BIN_MM = 5.0               # Bước gom điểm khi tìm mặt phẳng tấm kính
GLASS_EDGE_MM = 5.0              # Tim tấm kính CAD tới mặt ngoài (tấm 10): W của family góc đo tới mặt ngoài
PLATE_MM = 15.0                  # Điểm cách mặt phẳng tìm được ≤ chừng này thuộc tấm kính (đo tim tấm)
MAX_SAMPLE = 600                 # Số điểm khối tối đa khi chấm điểm tư thế


# --- Hình học 2D thuần (mm) – chạy được ngoài Revit để thử --------------------------
def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def add(a, b, k=1.0):
    return (a[0] + b[0] * k, a[1] + b[1] * k)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def unit(v):
    l = math.hypot(v[0], v[1])
    return (v[0] / l, v[1] / l)


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


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


def same(p, q):
    return abs(p[0] - q[0]) <= SNAP_MM and abs(p[1] - q[1]) <= SNAP_MM


def find_loops(items):
    """Vòng kín từ nét thẳng: polyline tự khép (hoặc polyline 4 đỉnh – Revit có thể bỏ điểm khép), hoặc chuỗi nét nối
    đầu mút mà mọi nút có đúng 2 nét. Trả về [điểm]. (Như tool sen tắm.)"""
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


def find_panels(loops, max_t):
    """Tấm kính: vòng chữ nhật dày ≤ max_t → (đầu 1, đầu 2) trên tim tấm."""
    result = []
    for pts in loops:
        c = rect_corners(pts)
        if c is None:
            continue
        l1, l2 = dist(c[0], c[1]), dist(c[1], c[2])
        if min(l1, l2) > max_t or not (STUB_MIN_MM <= max(l1, l2) <= GLASS_MAX_MM):
            continue
        k = 0 if l1 < l2 else 1         # cạnh ngắn c[k]–c[k+1] và cạnh đối diện
        a = ((c[k][0] + c[k + 1][0]) / 2.0, (c[k][1] + c[k + 1][1]) / 2.0)
        b = ((c[(k + 2) % 4][0] + c[(k + 3) % 4][0]) / 2.0, (c[(k + 2) % 4][1] + c[(k + 3) % 4][1]) / 2.0)
        result.append((a, b))
    return result


def circle3(a, b, c):
    """Tâm vòng tròn qua 3 điểm, None nếu thẳng hàng."""
    d = 2.0 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]))
    if abs(d) < 1e-6:
        return None
    sa, sb, sc = dot(a, a), dot(b, b), dot(c, c)
    return ((sa * (b[1] - c[1]) + sb * (c[1] - a[1]) + sc * (a[1] - b[1])) / d,
            (sa * (c[0] - b[0]) + sb * (a[0] - c[0]) + sc * (b[0] - a[0])) / d)


def find_arcs(items, min_r, max_r):
    """Cung mở cánh: [(bản lề, đầu 1, đầu 2, bán kính)]."""
    result = []
    for it in items:
        if not it.curved or len(it.pts) < 3:
            continue
        e1, e2 = it.pts[0], it.pts[-1]
        c = circle3(e1, it.pts[len(it.pts) // 2], e2)
        if c is None:
            continue
        r = dist(c, e1)
        if not (min_r <= r <= max_r) or any(abs(dist(c, p) - r) > ARC_TOL_MM for p in it.pts):
            continue
        cos = dot(unit(sub(e1, c)), unit(sub(e2, c)))
        sweep = math.degrees(math.acos(max(-1.0, min(1.0, cos))))
        if SWEEP_MIN_DEG <= sweep <= SWEEP_MAX_DEG:
            result.append((c, e1, e2, r))
    return result


def axis_cross(p, u, q, v):
    """Giao hai đường p + t.u và q + s.v."""
    d = u[0] * v[1] - u[1] * v[0]
    t = ((q[0] - p[0]) * v[1] - (q[1] - p[1]) * v[0]) / d
    return (p[0] + u[0] * t, p[1] + u[1] * t)


class Shower(object):
    """Một buồng tắm. kind "THANG": far → near là tấm kính, near → hinge là cánh đóng, hinge → wall là dải kính sau
    bản lề (không có thì wall = hinge). kind "GOC": far → near tấm A,
    far2 → near2 tấm B, corner = giao tim hai tấm (góc bị vát), cánh đóng near → near2."""

    def __init__(self, kind, hinge, closed, opened, far, near, far2=None, near2=None):
        self.kind, self.hinge, self.closed, self.opened = kind, hinge, closed, opened
        self.far, self.near, self.far2, self.near2 = far, near, far2, near2
        self.wall = hinge
        self.tray = False
        self.radius = dist(hinge, closed)
        self.corner = None
        if kind == u"GOC":
            self.corner = axis_cross(far, unit(sub(near, far)), far2, unit(sub(near2, far2)))
        self.room = u""
        self.status = u""
        self.type_name = u""
        self.eid = u""
        self.note = u""
        self.values = {}          # {khoá: mm}

    def center(self):
        pts = self.route()
        return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

    def route(self):
        """Tuyến vách khi cánh đóng."""
        if self.kind == u"THANG":
            return [self.far, self.near, self.hinge, self.wall]
        return [self.far, self.near, self.near2, self.far2]

    def leaf(self):
        """Cánh ở vị trí mở trên CAD."""
        return [self.hinge, self.opened]

    def measure(self):
        if self.kind == u"THANG":
            self.values = {u"KINH": dist(self.far, self.near), u"CUA": dist(self.near, self.hinge),
                           u"BIEN": dist(self.hinge, self.wall), u"TONG": dist(self.far, self.wall)}
        else:
            self.values = {u"CANH1": dist(self.far, self.corner) + GLASS_EDGE_MM,
                           u"CANH2": dist(self.far2, self.corner) + GLASS_EDGE_MM,
                           u"CUA": self.radius, u"CHEO": self.radius / math.sqrt(2.0)}


def find_showers(items, min_r, max_r, max_t, stats=None):
    """Ghép cung mở cánh với tấm kính → [Shower]."""
    panels = find_panels(find_loops(items), max_t)
    arcs = find_arcs(items, min_r, max_r)
    found = []

    def ends(pn):
        return (pn, (pn[1], pn[0]))

    for hinge, e1, e2, r in arcs:
        hit = None
        for closed, opened in ((e1, e2), (e2, e1)):
            v = unit(sub(closed, hinge))
            for pn in panels:
                for near, far in ends(pn):
                    if dist(near, closed) > TOUCH_MM or dist(near, far) < GLASS_MIN_MM:
                        continue
                    d = unit(sub(far, near))
                    cos = dot(d, v)
                    if cos >= ALIGN_COS:
                        # Buồng thẳng: cánh đóng nối tiếp tấm kính; bản lề chiếu lên tim tấm
                        hit = Shower(u"THANG", add(near, d, -dist(near, hinge)), closed, opened, far, near)
                    elif CHAMFER_LO <= abs(cos) <= CHAMFER_HI:
                        for pb in panels:
                            for near2, far2 in ends(pb):
                                if dist(near2, hinge) <= TOUCH_MM and dist(near2, far2) >= GLASS_MIN_MM                                         and abs(dot(d, unit(sub(far2, near2)))) <= 1 - ALIGN_COS:
                                    hit = Shower(u"GOC", hinge, closed, opened, far, near, far2, near2)
                    if hit:
                        break
                if hit:
                    break
            if hit:
                break
        if hit and all(dist(hit.hinge, s.hinge) > SAME_MM for s in found):
            if hit.kind == u"THANG":
                u = unit(sub(hit.hinge, hit.near))
                for pn in panels:
                    for start, stop in ends(pn):
                        if dist(start, hit.hinge) <= TOUCH_MM and dist(start, stop) < GLASS_MIN_MM                                 and dot(unit(sub(stop, start)), u) >= ALIGN_COS:
                            hit.wall = add(hit.hinge, u, dist(start, stop))
            found.append(hit)
    if stats is not None:
        stats.update(panels=len(panels), arcs=len(arcs))
    return found


def find_trays(loops):
    """Khay vát góc: vòng 5 cạnh, cạnh vát lệch 45° với hai cạnh kề vuông góc nhau → [Shower "GOC"]."""
    found = []
    for pts in loops:
        clean = []
        for p in pts:
            if not clean or not same(p, clean[-1]):
                clean.append(p)
        while len(clean) > 1 and same(clean[0], clean[-1]):
            clean.pop()
        if len(clean) < 5:             # vòng suy biến (nhiều nét trùng một điểm trong CAD thật)
            continue
        c = []
        n = len(clean)
        for i in range(n):
            if dot(unit(sub(clean[i], clean[i - 1])), unit(sub(clean[(i + 1) % n], clean[i]))) < 1.0 - 1e-6:
                c.append(clean[i])
        if len(c) != 5:
            continue
        for i in range(5):
            far, a, b, far2 = c[i - 1], c[i], c[(i + 1) % 5], c[(i + 2) % 5]
            cut, la, lb = dist(a, b), dist(far, a), dist(b, far2)
            if not (TRAY_CUT_MIN_MM <= cut <= TRAY_CUT_MAX_MM and TRAY_ARM_MIN_MM <= min(la, lb)
                    and max(la, lb) <= TRAY_ARM_MAX_MM):
                continue
            ua, ub, uc = unit(sub(a, far)), unit(sub(far2, b)), unit(sub(b, a))
            if abs(dot(ua, ub)) > RIGHT_COS or not (CHAMFER_LO <= abs(dot(ua, uc)) <= CHAMFER_HI):
                continue
            if lb > la:                    # tấm chạm bản lề (far2 – near2) là tấm ngắn hơn
                far, a, b, far2 = far2, b, a, far
            sh = Shower(u"GOC", b, a, b, far, a, far2, b)
            sh.opened = add(b, unit(sub(b, far2)), cut)
            sh.tray = True
            found.append(sh)
            break
    return found


def to_finish(end, inner, loops):
    """Đầu vách: tia từ `inner` (trong Room) qua `end` gặp biên Room vuông góc đầu tiên. Lần chạy 15:11 tìm biên trong dải
    ± 40 mm quanh `end` → tấm 632 / 645 của G19 đi xuyên cột giật vẫn bắt vào biên sau cột (đâm 250 mm vào tường).
    Tia có bề dày bằng tấm kính: tấm dời sát mặt cột giật (lần chạy 16:11: tim tấm cách mặt cột 5 mm) phải dừng ở góc cột,
    không chạy dọc mặt cột tới tường sau. Trả về (điểm, mm dời); hụt biên quá FINISH_TOL_MM hoặc không gặp biên →
    (end, None), giữ CAD."""
    u = unit(sub(end, inner))
    n = (-u[1], u[0])
    t = HALF_GLASS_MM + 1.0
    best = None
    for pts in loops:
        for i in range(len(pts)):
            a, b = pts[i - 1], pts[i]
            if dist(a, b) < 1.0 or abs(dot(unit(sub(b, a)), u)) > 1 - ALIGN_COS:
                continue
            sa, sb = dot(sub(a, inner), n), dot(sub(b, inner), n)
            if min(sa, sb) > t or max(sa, sb) < -t:
                continue
            d = dot(sub(a, inner), u)
            if d > 0.5 and (best is None or d < best):
                best = d
    if best is None or best - dist(end, inner) > FINISH_TOL_MM:
        return end, None
    return add(inner, u, best), best - dist(end, inner)


def ray_hit(p, u, loops):
    """Khoảng cách từ p theo hướng u tới biên Room vuông góc đầu tiên, None nếu không gặp."""
    n = (-u[1], u[0])
    best = None
    for pts in loops:
        for i in range(len(pts)):
            a, b = pts[i - 1], pts[i]
            if dist(a, b) < 1.0 or abs(dot(unit(sub(b, a)), u)) > 1 - ALIGN_COS:
                continue
            sa, sb = dot(sub(a, p), n), dot(sub(b, p), n)
            if min(sa, sb) > 0.5 or max(sa, sb) < -0.5:
                continue
            d = dot(sub(a, p), u)
            if d > 0.5 and (best is None or d < best):
                best = d
    return best


def fit_clear(sh, loops, min_clear):
    """Thông thủy buồng thẳng: dời tuyến vách ra xa tường đối diện nếu mặt kính cách mặt hoàn thiện < min_clear."""
    ax = unit(sub(sh.hinge, sh.far))
    side = (-ax[1], ax[0])
    if dot(sub(sh.opened, sh.hinge), side) < 0:
        side = (-side[0], -side[1])       # hướng vào trong buồng = phía cánh mở
    mid = ((sh.far[0] + sh.near[0]) / 2.0, (sh.far[1] + sh.near[1]) / 2.0)
    d = ray_hit(mid, side, loops)
    if d is None:
        return u"không đo được thông thủy – cần soát"
    clear = d - HALF_GLASS_MM
    if clear >= min_clear - 0.5:
        return u"thông thủy {:.0f}".format(clear)
    k = clear - min_clear
    for name in ("far", "near", "hinge", "wall", "closed", "opened"):
        setattr(sh, name, add(getattr(sh, name), side, k))
    return u"thông thủy {:.0f} → {:.0f}, dời vách {:.0f} mm".format(clear, min_clear, -k)


def fit_finish(sh, loops):
    """Kéo các đầu chạm tường về biên Room Finish, ghi chú đoạn dời."""
    notes = []

    def snap(end, inner, label):
        q, d = to_finish(end, inner, loops)
        if d is None:
            notes.append(u"{} không có biên Room ≤ {:.0f} mm, giữ CAD – cần soát".format(label, FINISH_TOL_MM))
        elif abs(d) >= 0.5:
            notes.append(u"{} {:+.0f} mm về mặt hoàn thiện".format(label, d))
        return q

    sh.far = snap(sh.far, sh.near, u"đầu kính")
    if sh.kind == u"THANG":
        sh.wall = snap(sh.wall, sh.near, u"đầu bản lề")
    else:
        sh.far2 = snap(sh.far2, sh.near2, u"đầu kính B")
    return u"; ".join(notes)


def analyse(items, min_r, max_r, max_t, room_at=None, room_keys=(), use_finish=True, stats=None, min_clear=0.0):
    """items: [Item] mm; room_at(pt) → (tên, [vòng]) | None. Trả về [Shower] đã đo chiều dài."""
    showers = find_showers(items, min_r, max_r, max_t, stats)
    trays = find_trays(find_loops(items))
    if stats is not None:
        stats.update(trays=len(trays))

    def in_room(sh):
        return room_at(((sh.far[0] + sh.near[0]) / 2.0, (sh.far[1] + sh.near[1]) / 2.0)) if room_at is not None else None

    taken = set(id(h[1]) for h in (in_room(sh) for sh in showers) if h)
    for tr in trays:
        h = in_room(tr)
        if h and id(h[1]) not in taken:
            taken.add(id(h[1]))
            showers.append(tr)
    for sh in showers:
        hit = in_room(sh)
        sh.room = hit[0] if hit else u""
        if room_at is not None and room_keys and not any(k in loose(sh.room) for k in room_keys):
            sh.status = u"Bỏ qua – không nằm trong phòng {} (phòng: {})".format(
                u"/".join(room_keys), sh.room or u"không có Room")
            continue
        notes = []
        if min_clear > 0 and hit and sh.kind == u"THANG":
            notes.append(fit_clear(sh, hit[1], min_clear))
        if use_finish and hit:
            notes.append(fit_finish(sh, hit[1]))
        sh.note = u"; ".join(v for v in notes if v)
        sh.measure()
        sh.status = u"OK"
        if sh.tray:
            sh.note = u"; ".join(v for v in (u"theo khay vát góc CAD, không có nét kính", sh.note) if v)
    showers.sort(key=lambda s: (-round(s.hinge[1]), round(s.hinge[0])))
    return showers


def seg_dist(p, a, b):
    ab = sub(b, a)
    l2 = dot(ab, ab)
    t = 0.0 if l2 < 1e-9 else max(0.0, min(1.0, dot(sub(p, a), ab) / l2))
    return dist(p, add(a, ab, t))


def plane_mode(vals):
    """Giá trị xuất hiện nhiều nhất (gom theo PLANE_BIN_MM): mặt phẳng tấm kính giữa các khối."""
    bins = {}
    for v in vals:
        k = int(round(v / PLANE_BIN_MM))
        bins[k] = bins.get(k, 0) + 1
    return max(bins, key=lambda k: (bins[k], -k)) * PLANE_BIN_MM


def body_fit(pts, p0, sh):
    """Chọn tư thế family theo khối đặc. pts: [(x, y) mm] đỉnh khối; p0: điểm đặt. Hai dạng đặt theo gốc family (đầu
    file, mục 6), tỉ lệ điểm nằm trên tuyến vách + cánh mở để kiểm tra. Soi gương qua
    đường ngang y = p0.y. Trả về (soi gương?, góc xoay rad, dời (dx, dy), tỉ lệ điểm trên tuyến, dài family | None) –
    None nếu không có khối."""
    if not pts:
        return None
    step = max(1, len(pts) // MAX_SAMPLE)
    pts = pts[::step]
    route = sh.route()
    segs = [(route[i - 1], route[i]) for i in range(1, len(route))] + [tuple(sh.leaf())]
    if sh.kind == u"THANG":
        ax = unit(sub(sh.wall, sh.far))
    else:
        ax = unit(sub(sh.far, sh.corner))
    base = math.atan2(ax[1], ax[0])

    def on_route(ps, move):
        on = 0
        for p in ps:
            q = add(p, move)
            if min(seg_dist(q, a, b) for a, b in segs) <= NEAR_MM:
                on += 1
        return on / float(len(ps))

    if sh.kind == u"THANG":
        n = (-ax[1], ax[0])
        mirror = dot(sub(sh.opened, sh.hinge), n) < 0
        src = [(p[0], 2.0 * p0[1] - p[1]) for p in pts] if mirror else pts
        ps = [rotate(p, base, p0) for p in src]
        us = [dot(sub(p, sh.far), ax) for p in ps]
        vs = [dot(sub(p, sh.far), n) for p in ps]
        mode = plane_mode(vs)
        plate = [v for v in vs if abs(v - mode) <= PLATE_MM]
        move = add((ax[0] * (dist(sh.far, sh.wall) - max(us)), ax[1] * (dist(sh.far, sh.wall) - max(us))),
                   n, -(min(plate) + max(plate)) / 2.0)
        return mirror, base, move, on_route(ps, move), max(us) - min(us)
    ay = unit(sub(sh.far2, sh.corner))
    ang = math.atan2(-ay[1], -ay[0])         # −X family (cạnh W1) theo tấm B
    mirror = dot((ay[1], -ay[0]), ax) > 0    # −Y family (cạnh W2) phải theo tấm A
    src = [(p[0], 2.0 * p0[1] - p[1]) for p in pts] if mirror else pts
    ps = [rotate(p, ang, p0) for p in src]
    sa = max(dot(sub(p, sh.far), ax) for p in ps)
    sb = max(dot(sub(p, sh.far2), ay) for p in ps)
    move = add((ax[0] * -sa, ax[1] * -sa), ay, -sb)
    return mirror, ang, move, on_route(ps, move), None


def run_shift(pts, sh):
    """Dời vách thẳng đã đặt cho khớp tuyến: đầu bản lề về `wall`, tim tấm kính về tuyến. pts: [(x, y) mm] đỉnh khối."""
    ax = unit(sub(sh.wall, sh.far))
    n = (-ax[1], ax[0])
    us = [dot(sub(p, sh.far), ax) for p in pts]
    vs = [dot(sub(p, sh.far), n) for p in pts]
    mode = plane_mode(vs)
    plate = [v for v in vs if abs(v - mode) <= PLATE_MM]
    along = dist(sh.far, sh.wall) - max(us)
    return add((ax[0] * along, ax[1] * along), n, -(min(plate) + max(plate)) / 2.0)


def route_box(sh):
    xs = [p[0] for p in sh.route()]
    ys = [p[1] for p in sh.route()]
    return (min(xs) - HALF_GLASS_MM, min(ys) - HALF_GLASS_MM, max(xs) + HALF_GLASS_MM, max(ys) + HALF_GLASS_MM)


def clashes(sh, boxes):
    """[(Id, tên)] thiết bị có hộp bao bị tuyến vách lấn vào."""
    b = route_box(sh)
    return sorted(set((eid, name) for eid, name, q in boxes
                      if min(b[2], q[2]) - max(b[0], q[0]) > CLASH_TOL_MM
                      and min(b[3], q[3]) - max(b[1], q[1]) > CLASH_TOL_MM))


def parse_map(text):
    """"KINH=L1;CUA=Wight Door" → {"KINH": "L1", "CUA": "Wight Door"}."""
    result = {}
    for part in (text or u"").split(u";"):
        if u"=" in part:
            k, v = part.split(u"=", 1)
            if k.strip() and v.strip():
                result[k.strip().upper()] = v.strip()
    return result


def type_name_for(sh, template_name):
    """Tên type mới theo mẫu tên của type người dùng: thẳng "1000" → tổng dài; góc "VTG3-1000x1000" → thay cặp số."""
    v = sh.values
    if sh.kind == u"THANG":
        total = u"{:.0f}".format(v[u"TONG"])
        return re.sub(r"\d+", total, template_name, count=1) if re.search(r"\d", template_name) else total
    pair = u"{:.0f}x{:.0f}".format(v[u"CANH1"], v[u"CANH2"])
    return re.sub(r"\d+x\d+", pair, template_name, count=1) if re.search(r"\d+x\d+", template_name) \
        else u"{}-{}".format(template_name, pair)


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
    """Nét ngắn trên các layer – ứng viên tấm kính và cung cánh. Trả về (items, {loại: số})."""
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
        elif isinstance(obj, Curve) and obj.IsBound:
            if isinstance(obj, Line):
                if obj.Length <= lim:
                    items.append(Item([xy(obj.GetEndPoint(0)), xy(obj.GetEndPoint(1))], False))
            elif isinstance(obj, Arc) and obj.Length <= lim:
                items.append(Item([xy(p) for p in obj.Tessellate()], True))
    return items, kinds


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
    """Hàm room_at(pt mm) → (tên Room, [vòng biên Finish mm]) trên level chứa điểm, None nếu không có."""
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


def pick_template(value, cell):
    """IN[3] / IN[4]: FamilyType của node Family Types hoặc chuỗi "Family : Type" → FamilySymbol; trống → None."""
    if value is None or value == u"":
        return None
    symbols = fixture_symbols()
    families = u", ".join(sorted(set(s.FamilyName for s in symbols))) or u"không có"
    if isinstance(value, str):
        parts = [norm(p) for p in value.split(u":")]
        if len(parts) != 2 or not all(parts):
            raise StopReport([u"DỪNG: ô {} phải là type chọn từ node Family Types hoặc chuỗi 'Family : Type' "
                              u"(đang là '{}').".format(cell, value)])
        hits = [s for s in symbols if norm(s.FamilyName) == parts[0] and norm(get_name(s)) == parts[1]]
        if not hits:
            raise StopReport([u"DỪNG: không có type '{}'. Family thiết bị vệ sinh: {}".format(value, families)])
        sym = hits[0]
    else:
        sym = UnwrapElement(value)
        if not isinstance(sym, FamilySymbol):
            raise StopReport([u"DỪNG: ô {} không phải type family.".format(cell)])
        if sym.Category is None or sym.Category.BuiltInCategory != BuiltInCategory.OST_PlumbingFixtures:
            raise StopReport([u"DỪNG: type '{} : {}' không thuộc Plumbing Fixtures. Family thiết bị vệ sinh: {}".format(
                sym.FamilyName, get_name(sym), families)])
    if sym.Family.FamilyPlacementType != FamilyPlacementType.OneLevelBased:
        raise StopReport([u"DỪNG: family '{}' kiểu đặt {} – công cụ chỉ hỗ trợ family đặt theo level.".format(
            sym.FamilyName, sym.Family.FamilyPlacementType)])
    return sym


def named_param(element, name):
    """Tham số family không có GUID / BuiltInParameter nên phải tìm theo tên (ngoại lệ LookupParameter): dùng
    GetParameters, bắt buộc đúng một tham số và sửa được; không có → None."""
    hits = [p for p in element.GetParameters(name) if p.StorageType == StorageType.Double and not p.IsReadOnly]
    return hits[0] if len(hits) == 1 else None


def body_solids(fi):
    """[[(x, y, z) mm]] đỉnh từng khối đặc của instance."""
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
                    pts.extend(e.Tessellate())
                if pts:
                    result.append([(to_mm(p.X), to_mm(p.Y), to_mm(p.Z)) for p in pts])

    geo = fi.get_Geometry(opt)
    if geo is not None:
        walk(geo)
    return result


def body_points(fi):
    """Đỉnh (x, y mm) các khối đặc; bỏ khối lớn hơn BODY_MAX_MM trên mặt bằng."""
    result = []
    for pts in body_solids(fi):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        if max(max(xs) - min(xs), max(ys) - min(ys)) <= BODY_MAX_MM:
            result.extend((p[0], p[1]) for p in pts)
    return result


def box_text(pts):
    xs, ys, zs = [p[0] for p in pts], [p[1] for p in pts], [p[2] for p in pts]
    return u"X {:.0f}…{:.0f}, Y {:.0f}…{:.0f}, Z {:.0f}…{:.0f}".format(min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def is_length_def(definition):
    try:
        return definition.GetDataType() == SpecTypeId.Length
    except Exception:
        return False


def read_family(sym):
    """Mở family (không lưu) → dòng báo cáo tham số dài + [tên, là instance, có công thức]. Ngoài Transaction."""
    lines, params = [], []
    fam_doc = doc.EditFamily(sym.Family)
    try:
        fm = fam_doc.FamilyManager
        cur = fm.CurrentType
        for p in fm.GetParameters():
            if not is_length_def(p.Definition):
                continue
            value = u"{:.1f}".format(to_mm(cur.AsDouble(p) or 0.0)) if cur is not None and cur.HasValue(p) else u"—"
            formula = p.Formula if p.IsDeterminedByFormula else u""
            lines.append(u"  {} [{}] = {}{}".format(p.Definition.Name, u"instance" if p.IsInstance else u"type", value,
                                                    u"  công thức: {}".format(formula) if formula else u""))
            params.append((p.Definition.Name, p.IsInstance, bool(formula)))
    finally:
        fam_doc.Close(False)
    return lines, params


def probe_family(sym, level, params):
    """Đặt thử 1 instance rồi RollBack: từng khối đặc + đổi hộp bao khi mỗi tham số dài +100 mm."""
    lines = []
    tx = Transaction(doc, u"ARV - Dò tham số vách kính tắm (hoàn tác)")
    # Đổi tham số thử làm Revit hiện hộp "Constraints between geometry…" (SetClearAfterRollback không tắt được, lần chạy
    # 2026-10-30 15:08) → chỉ dò family khi chưa khai tham số; gặp hộp này bấm OK, mọi thay đổi vẫn được hoàn tác.
    tx.Start()
    try:
        if not sym.IsActive:
            sym.Activate()
            doc.Regenerate()
        fi = doc.Create.NewFamilyInstance(XYZ(0.0, 0.0, 0.0), sym, level, StructuralType.NonStructural)
        doc.Regenerate()
        solids = body_solids(fi)
        for i, pts in enumerate(solids, 1):
            lines.append(u"  Khối {}: {}".format(i, box_text(pts)))

        def extent():
            pts = [p for s in body_solids(fi) for p in s]
            xs, ys, zs = [p[0] for p in pts], [p[1] for p in pts], [p[2] for p in pts]
            return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))

        base = extent()
        for name, is_inst, has_formula in params:
            if has_formula:
                continue
            target = fi if is_inst else sym
            p = named_param(target, name)
            if p is None:
                continue
            old = p.AsDouble()
            try:
                p.Set(old + from_mm(100.0))
                doc.Regenerate()
                new = extent()
                lines.append(u"  {} +100 → hộp bao đổi X {:+.0f}/{:+.0f}, Y {:+.0f}/{:+.0f}, Z {:+.0f}/{:+.0f}".format(
                    name, *[n - b for n, b in zip(new, base)]))
            except Exception as ex:
                lines.append(u"  {} +100 → lỗi: {}".format(name, ex))
            p.Set(old)
            doc.Regenerate()
    finally:
        tx.RollBack()
    return lines


def existing_showers(families, level):
    """[(tâm mm, Id, family, có Comments của tool)] vách đã đặt trên level thuộc các family mẫu."""
    result = []
    for fi in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures) \
            .WhereElementIsNotElementType().ToElements():
        sym = getattr(fi, "Symbol", None)
        if sym is None or fi.LevelId != level.Id or norm(sym.FamilyName) not in families:
            continue
        pts = body_points(fi)
        c = ((min(p[0] for p in pts) + max(p[0] for p in pts)) / 2.0,
             (min(p[1] for p in pts) + max(p[1] for p in pts)) / 2.0) if pts else xy(fi.Location.Point)
        cm = fi.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        result.append((c, fi.Id.Value, norm(sym.FamilyName), cm is not None and cm.AsString() == COMMENT_TAG))
    return result


def fixture_boxes(families, level_z):
    """[(Id, tên family, (xmin, ymin, xmax, ymax) mm)] khối đặc thật của thiết bị vệ sinh ở tầng này, trừ vách kính. Không
    lọc theo LevelId: family Work Plane Based (bồn cầu) không có Level. Không dùng hộp bao instance: bồn cầu có khối vùng
    thông thủy −250…1722 mm (lần chạy 16:11 báo vướng giả ở 12 buồng) – bỏ khối lớn hơn CLEAR_BODY_MM."""
    result = []
    for fi in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures) \
            .WhereElementIsNotElementType().ToElements():
        sym = getattr(fi, "Symbol", None)
        bb = fi.get_BoundingBox(None)
        if sym is None or bb is None or norm(sym.FamilyName) in families:
            continue
        if to_mm(bb.Max.Z) < level_z or to_mm(bb.Min.Z) > level_z + 2000.0:
            continue
        for pts in body_solids(fi):
            xs, ys = [q[0] for q in pts], [q[1] for q in pts]
            if max(max(xs) - min(xs), max(ys) - min(ys)) <= CLEAR_BODY_MM:
                result.append((fi.Id.Value, sym.FamilyName, (min(xs), min(ys), max(xs), max(ys))))
    return result


def split_values(sh, mapping, sym):
    """{khoá: mm} → (giá trị type {tên tham số: mm}, giá trị instance, khoá không khớp tham số nào)."""
    on_type, on_inst, unknown = {}, {}, []
    for key, pname in mapping.items():
        if key not in sh.values:
            unknown.append(key)
            continue
        value = float(round(sh.values[key]))
        if named_param(sym, pname) is not None:
            on_type[pname] = value
        else:
            on_inst[pname] = value
    return on_type, on_inst, unknown


def make_type(sym, name, on_type):
    """Type có tên `name` trong family: có sẵn thì dùng nếu đúng giá trị, không thì nhân bản từ `sym` và đặt tham số."""
    for tid in sym.Family.GetFamilySymbolIds():
        cur = doc.GetElement(tid)
        if norm(get_name(cur)) == norm(name):
            for pname, value in on_type.items():
                p = named_param(cur, pname)
                if p is None or abs(to_mm(p.AsDouble()) - value) > 0.5:
                    return None
            return cur
    new = sym.Duplicate(name)
    for pname, value in on_type.items():
        named_param(new, pname).Set(from_mm(value))
    return new


def apply_fit(fi, fit, p0):
    """Soi gương (qua đường ngang y = p0.y) → xoay quanh điểm đặt → dời."""
    mirror, ang, move = fit[0], fit[1], fit[2]
    pivot = XYZ(from_mm(p0[0]), from_mm(p0[1]), 0.0)
    if mirror:
        ids = List[ElementId]()
        ids.Add(fi.Id)
        ElementTransformUtils.MirrorElements(doc, ids, Plane.CreateByNormalAndOrigin(XYZ(0.0, 1.0, 0.0), pivot), False)
    if abs(ang) > 1e-6:
        ElementTransformUtils.RotateElement(doc, fi.Id, Line.CreateBound(pivot, XYZ(pivot.X, pivot.Y, 1.0)), ang)
    ElementTransformUtils.MoveElement(doc, fi.Id, XYZ(from_mm(move[0]), from_mm(move[1]), 0.0))


def preview_lines(showers, z_mm):
    try:
        clr.AddReference("ProtoGeometry")
        from Autodesk.DesignScript.Geometry import Point as DSPoint, Line as DSLine

        def seg(a, e):
            return DSLine.ByStartPointEndPoint(DSPoint.ByCoordinates(a[0], a[1], z_mm),
                                               DSPoint.ByCoordinates(e[0], e[1], z_mm))
        lines = []
        for sh in showers:
            pts = sh.route()
            lines += [seg(pts[i - 1], pts[i]) for i in range(1, len(pts))]
            lines.append(seg(*sh.leaf()))
        return lines
    except Exception:
        return []


LOG_HEADER = [u"STT", u"Dạng", u"Bản lề (mm)", u"Phòng", u"Kính + dải / cạnh 1", u"Cửa", u"Tổng / cạnh 2", u"Type", u"Kết quả",
              u"ElementId", u"Ghi chú"]


def size_cells(sh):
    v = sh.values
    if not v:
        return [u"—", u"—", u"—"]
    if sh.kind == u"THANG":
        return [u"{:.0f} + {:.0f}".format(v[u"KINH"], v[u"BIEN"]), u"{:.0f}".format(v[u"CUA"]), u"{:.0f}".format(v[u"TONG"])]
    return [u"{:.0f}".format(v[u"CANH1"]), u"{:.0f}".format(v[u"CUA"]), u"{:.0f}".format(v[u"CANH2"])]


def write_report(report):
    """Ghi toàn bộ Báo cáo (kèm tham số family) ra file để đọc lại ngoài Dynamo."""
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    path = os.path.join(folder, "TaoVachKinhTamTuCAD_BAOCAO_{}.txt".format(
        datetime.datetime.now().strftime("%Y%m%d_%H%M%S")))
    with io.open(path, "w", encoding="utf-8-sig") as f:
        f.write(u"\n".join(report))
    return path


def write_log(rows, source, dry_run):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoVachKinhTamTuCAD_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
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


def main(cad_filter, layer_filters, level_name, tpl_line, tpl_corner, room_keys, min_r, max_r, max_t, map_line,
         map_corner, use_finish, dry_run, min_clear):
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."], []
    if re.search(r"[-_]S[-_]", doc.Title or u""):
        return [u"DỪNG: tên file '{}' là mô hình Kết cấu (S) – vách kính tắm chỉ dựng trên mô hình Kiến trúc (A).".format(
            doc.Title)], []
    syms = {u"THANG": pick_template(tpl_line, u"IN[3]"), u"GOC": pick_template(tpl_corner, u"IN[4]")}
    maps = {u"THANG": parse_map(map_line), u"GOC": parse_map(map_corner)}
    cad, cad_name, objects, all_layers = pick_cad(cad_filter, layer_filters)
    layers = match_layers(all_layers, layer_filters)
    level = find_level(level_name)
    level_z = to_mm(level.Elevation)
    room_at, n_rooms = room_finder(level)
    keys = [loose(k) for k in room_keys if k.strip()]
    if keys and not n_rooms:
        raise StopReport([u"DỪNG: level '{}' chưa có Room – cần Room để lọc buồng tắm trong WC (hoặc để trống IN[5]."
                          u")".format(level_name)])
    items, kinds = read_items(objects, layers)
    stats = {}
    showers = analyse(items, min_r, max_r, max_t, room_at, keys, use_finish, stats, min_clear)

    # Đọc family trước khi mở Transaction ghi (EditFamily không chạy trong Transaction)
    TransactionManager.Instance.ForceCloseTransaction()
    fam_report = []
    if dry_run:
        for kind, sym in syms.items():
            if sym is None or maps[kind]:
                continue
            label = u"{} : {}".format(sym.FamilyName, get_name(sym))
            try:
                lines, params = read_family(sym)
                fam_report.append(u"Tham số dài của {}:".format(label))
                fam_report += lines or [u"  (không có tham số dài)"]
                fam_report.append(u"Khối đặc và thử tham số của {} (đặt thử rồi hoàn tác):".format(label))
                fam_report += probe_family(sym, level, params)
            except Exception as ex:
                fam_report.append(u"Không đọc được family {}: {}".format(label, ex))

    families = set(norm(s.FamilyName) for s in syms.values() if s is not None)
    existing = existing_showers(families, level)
    boxes = fixture_boxes(families, level_z)
    rows, jobs, fixes, new_types = [], [], [], {}
    for idx, sh in enumerate(showers, 1):
        if sh.status == u"OK":
            sym, mapping = syms[sh.kind], maps[sh.kind]
            fam = norm(sym.FamilyName) if sym is not None else u""
            near = sorted((dist(e[0], sh.center()), e[1], e[3]) for e in existing
                          if e[2] == fam and dist(e[0], sh.center()) <= EXIST_TOL_MM)
            if sym is None:
                sh.status = u"Bỏ qua – chưa chọn type dạng này"
            elif near:
                sh.eid = near[0][1]
                sh.status = u"Bỏ qua – đã có vách (Id {})".format(sh.eid)
                if near[0][2] and mapping:
                    # Vách của tool khác kích thước → sửa tại chỗ; vách người dùng tự đặt giữ nguyên
                    on_type, on_inst, unknown = split_values(sh, mapping, sym)
                    fi = doc.GetElement(ElementId(sh.eid))
                    name = type_name_for(sh, get_name(sym))
                    todo = []
                    if not unknown and norm(get_name(fi.Symbol)) != norm(name):
                        todo.append(u"type {} → {}".format(get_name(fi.Symbol), name))
                    for pname, value in on_inst.items():
                        p = named_param(fi, pname)
                        if p is not None and abs(to_mm(p.AsDouble()) - value) > 0.5:
                            todo.append(u"{} {:.0f} → {:.0f}".format(pname, to_mm(p.AsDouble()), value))
                    if sh.kind == u"THANG":
                        move = run_shift(body_points(fi), sh)
                        if math.hypot(*move) > FIX_MOVE_MM:
                            todo.append(u"dời {:.0f} mm".format(math.hypot(*move)))
                    if todo and not unknown:
                        sh.type_name = name
                        new_types[(sym.Id.Value, name)] = on_type
                        sh.note = u"; ".join(v for v in [sh.note] + todo if v)
                        sh.status = u"Sẽ sửa" if dry_run else u"Chờ sửa"
                        fixes.append((sh, len(rows), sym, on_type, on_inst, fi))
            elif not mapping:
                sh.status = u"Bỏ qua – chưa khai tham số chiều dài ({})".format(u"IN[9]" if sh.kind == u"THANG" else u"IN[10]")
            else:
                on_type, on_inst, unknown = split_values(sh, mapping, sym)
                if unknown:
                    sh.status = u"Bỏ qua – khoá tham số không hợp lệ: {}".format(u", ".join(unknown))
                else:
                    sh.type_name = type_name_for(sh, get_name(sym))
                    new_types[(sym.Id.Value, sh.type_name)] = on_type
                    sh.status = u"Sẽ tạo" if dry_run else u"Chờ tạo"
                    jobs.append((sh, len(rows), sym, on_type, on_inst))
        if sh.values:                     # gồm cả vách đã có: mỗi lần chạy đều soát lại vướng thiết bị
            hits = clashes(sh, boxes)
            if hits:
                sh.note = u"; ".join(v for v in [sh.note, u"vướng {} – cần soát".format(
                    u", ".join(u"{} (Id {})".format(n, i) for i, n in hits))] if v)
        rows.append([idx, u"thẳng" if sh.kind == u"THANG" else u"vát góc", fmt(sh.hinge), sh.room or u"—"] + size_cells(sh) +
                    [sh.type_name or u"—", sh.status, sh.eid, sh.note])

    created = []
    if not dry_run and (jobs or fixes):
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        try:
            cache = {}
            for sh, ri, sym, on_type, on_inst, fi in fixes:
                k = (sym.Id.Value, sh.type_name)
                if k not in cache:
                    cache[k] = make_type(sym, sh.type_name, on_type)
                    if cache[k] is None:
                        raise Exception(u"type '{}' đã có nhưng khác kích thước".format(sh.type_name))
                    if not cache[k].IsActive:
                        cache[k].Activate()
                        doc.Regenerate()
                if fi.Symbol.Id != cache[k].Id:
                    fi.ChangeTypeId(cache[k].Id)
                for pname, value in on_inst.items():
                    p = named_param(fi, pname)
                    if p is not None:
                        p.Set(from_mm(value))
                doc.Regenerate()
                if sh.kind == u"THANG":
                    move = run_shift(body_points(fi), sh)
                    if math.hypot(*move) > FIX_MOVE_MM:
                        ElementTransformUtils.MoveElement(doc, fi.Id, XYZ(from_mm(move[0]), from_mm(move[1]), 0.0))
                rows[ri][8] = u"Đã sửa"
            for sh, ri, sym, on_type, on_inst in jobs:
                k = (sym.Id.Value, sh.type_name)
                if k not in cache:
                    cache[k] = make_type(sym, sh.type_name, on_type)
                    if cache[k] is None:
                        raise Exception(u"type '{}' đã có nhưng khác kích thước".format(sh.type_name))
                    if not cache[k].IsActive:
                        cache[k].Activate()
                        doc.Regenerate()
                c = sh.center()
                pt = XYZ(from_mm(c[0]), from_mm(c[1]), 0.0)
                fi = doc.Create.NewFamilyInstance(pt, cache[k], level, StructuralType.NonStructural)
                missing = []
                for pname, value in on_inst.items():
                    p = named_param(fi, pname)
                    if p is None:
                        missing.append(pname)
                    else:
                        p.Set(from_mm(value))
                doc.Regenerate()
                fit = body_fit(body_points(fi), c, sh)
                note = u""
                if fit is None:
                    note = u"không đọc được khối đặc của family – cần soát"
                else:
                    apply_fit(fi, fit, c)
                    note = u"{:.0f} % khối nằm trên tuyến CAD".format(fit[3] * 100.0)
                    if fit[4] is not None and abs(fit[4] - sh.values[u"TONG"]) > 2.0:
                        note += u"; family dài {:.0f} mm, tuyến CAD {:.0f} mm – cần soát".format(fit[4], sh.values[u"TONG"])
                if missing:
                    note = u"; ".join([note, u"không có tham số: {}".format(u", ".join(missing))])
                cm = fi.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
                if cm is not None and not cm.IsReadOnly:
                    cm.Set(COMMENT_TAG)
                rows[ri][8] = u"Đã tạo"
                rows[ri][9] = fi.Id.Value
                rows[ri][10] = u"; ".join(v for v in (rows[ri][10], note) if v)
                created.append((fi, ri))
            status = tx.Commit()
        except Exception as ex:
            tx.RollBack()
            return [u"LỖI khi tạo vách, mọi thay đổi đã được hoàn tác: {}".format(ex)], []
        if status != TransactionStatus.Committed:
            return [u"LỖI: Revit không lưu được Transaction ({}), mọi thay đổi đã được hoàn tác.".format(status)], []
        for fi, ri in created:
            if not fi.IsValidObject:
                rows[ri][8] = u"Revit đã xoá sau khi tạo"

    report = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN")]
    report.append(u"CAD: {} – dò {} – {} nét – {} tấm kính, {} cung mở cánh, {} khay vát góc – Room trên level: {}".format(
        cad_name, u"layer " + u"; ".join(sorted(layers)) if layer_filters else u"mọi layer ({})".format(len(layers)),
        len(items), stats.get("panels", 0), stats.get("arcs", 0), stats.get("trays", 0), n_rooms))
    inside = [s for s in showers if s.values]
    report.append(u"Nhận diện {} buồng trong phòng {}: {} thẳng, {} vát góc, trong đó {} theo khay CAD (level {})".format(
        len(inside), u"/".join(room_keys) if keys else u"bất kỳ", len([s for s in inside if s.kind == u"THANG"]),
        len([s for s in inside if s.kind == u"GOC"]), len([s for s in inside if s.tray]), level.Name))
    report.append(u"Vách {}: {} – vách của tool {}: {} – type dùng {} ({})".format(
        u"sẽ tạo" if dry_run else u"đã tạo", len(jobs), u"sẽ sửa" if dry_run else u"đã sửa", len(fixes), len(new_types),
        u", ".join(sorted(k[1] for k in new_types)) or u"—"))
    soat = [s for s in inside if u"cần soát" in s.note]
    if soat:
        report.append(u"CẦN SOÁT: {} buồng (đầu vách không tới biên Room / vướng thiết bị) – xem cột Ghi chú".format(len(soat)))
    counts = {}
    for sh in showers:
        if sh.status.startswith(u"Bỏ qua") and sh.values:
            k = re.sub(r"\(Id.*", u"", sh.status.split(u" – ", 1)[1]).strip()
            counts[k] = counts.get(k, 0) + 1
    for k in sorted(counts):
        report.append(u"Bỏ qua {} buồng: {}".format(counts[k], k))
    report.append(u"Đối tượng CAD theo loại: " + u", ".join(u"{} {}".format(k, v) for k, v in sorted(kinds.items())))
    report += fam_report
    try:
        report.append(u"Log: " + write_log(rows, cad_name, dry_run))
    except Exception as ex:
        report.append(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        report.append(u"Kiểm tra tuyến vách + cánh mở (nét xanh trong Dynamo) và log. Khai IN[9] / IN[10] theo các dòng "
                      u"\"+100\" ở trên. Đúng thì đổi Dry-run = False và Run lại. Undo bằng mục \"{}\"."
                      .format(TRANSACTION_NAME))
    else:
        report.append(u"Soát vài vách (đầu kính, hướng mở cánh). Undo bằng mục \"{}\".".format(TRANSACTION_NAME))
    report.append(u" | ".join(LOG_HEADER))
    report += [u" | ".join(u"{}".format(v) for v in r) for r in rows
               if not r[8].startswith(u"Bỏ qua – không nằm trong phòng")]
    try:
        report.insert(2, u"Báo cáo đầy đủ: " + write_report(report))
    except Exception as ex:
        report.append(u"Không ghi được file báo cáo: {}".format(ex))
    return report, preview_lines([j[0] for j in jobs] + [f[0] for f in fixes] or [s for s in showers if s.values],
                                 level_z)


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
            IN[4],
            (u"WC;vệ sinh" if IN[5] is None else IN[5]).split(u";"),
            num(6, 450.0),
            num(7, 900.0),
            num(8, 30.0),
            IN[9] or u"",
            IN[10] or u"",
            True if IN[11] is None else bool(IN[11]),
            True if IN[12] is None else bool(IN[12]),
            num(13, 900.0),
        ))
    except StopReport as ex:
        OUT = [ex.lines, []]
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], []]
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with io.open(os.path.join(folder, "TaoVachKinhTamTuCAD_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))), "w", encoding="utf-8-sig") as f:
                f.write(u"\n".join(OUT[0]))
        except Exception:
            pass
    note = force_rerun_next_time()
    if note:
        OUT[0].append(u"LƯU Ý: " + note)
