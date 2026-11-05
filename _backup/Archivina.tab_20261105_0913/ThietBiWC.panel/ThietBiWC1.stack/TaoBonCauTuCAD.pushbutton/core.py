# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong 16. ARV_TaoBonCauTuCAD_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Tạo bồn cầu (Plumbing Fixtures) từ mặt bằng DWG đã Link, NHẬN DIỆN THEO HÌNH DẠNG (không cần biết layer):
#   1. Bồn cầu trên CAD = HÌNH CHỮ U KHÉP BẰNG CUNG (đo trên G19 TẦNG 3 2026-10-30, file chẩn đoán của tool 14: layer
#      A-Interior WC, 32 bộ = polyline hở 519 × 380 (lưng + két nước + hai cạnh thân) + cung 181 × 380 (mũi bồn cầu)
#      nối hai đầu polyline; tổng dài 700, rộng 380):
#      - cung: dây cung trong [IN[5], IN[6]] (mặc định 300–550), độ võng ≥ 1/4 dây cung (loại cung bo góc, cánh cửa);
#      - hai đầu cung nối được với nhau qua các đoạn nét nằm trong dải bồn cầu → hình kín. Nối theo MỌI ĐỈNH polyline
#        (G19: polyline thân 10 đỉnh vẽ đi vẽ lại lưng → két → quay về, dừng ở mép két; nét đáy 329 mm nối đầu cung với
#        đỉnh giữa polyline – dry-run 2026-10-30 14:27 nối theo đầu mút thì 0/32). Lưng = điểm xa nhất của cả cụm nét;
#      - chiều dài từ lưng tới mũi trong [IN[7], IN[8]] (mặc định 550–900), bề rộng ≤ dây cung + 50.
#      Hướng mặt trước = từ dây cung tới đỉnh cung; lưng = điểm xa nhất phía ngược lại (sát tường).
#      IN[1] trống = dò mọi layer; có chuỗi = chỉ layer chứa chuỗi đó.
#   2. Room chứa tâm bồn cầu phải có tên chứa một chuỗi trong IN[4] (mặc định "WC;vệ sinh"; trống = mọi phòng).
#   3. Mặt dựa: mặt song song tường sau lưng bồn cầu CAD (± 150 mm), lấy trong biên Room ở mặt hoàn thiện (Finish –
#      gồm cả tường link KC) và mặt tường Revit trên level IN[2] (gồm lớp ốp mỏng) → lưng bồn cầu áp lớp hoàn thiện.
#   4. Vị trí dọc tường (yêu cầu người dùng 2026-10-30, ảnh 2 WC G19): GIỮA hai biên hai bên bồn cầu – VÁCH KÍNH TẮM
#      và MẶT TƯỜNG HOÀN THIỆN, hoặc MẶT TƯỜNG và MẶT TƯỜNG. Biên = mặt vuông góc mặt dựa, chạm dải 300 mm trước mặt
#      dựa, gần tâm bồn cầu nhất mỗi phía:
#      - vách kính CAD: vòng kín chữ nhật dày ≤ IN[9] (mặc định 30), dài 300–3000 mm (G19: polyline 10 × 482…710);
#        tường Revit có tên chứa "kinh" / "glass" cũng coi là vách kính;
#      - vách kính Revit (family "AV-Vách Kính Tắm Thẳng", "AV-Vách Tắm Góc 2 chieu", Comments của tool 17): mặt tấm kính
#        đọc từ khối đặc (dày ≤ IN[9]). Có vách Revit ở một phía thì BỎ vách CAD phía đó – người dùng chỉnh thông thủy trên
#        Revit 2026-10-30 (x 2830 → 2925), CAD còn vị trí cũ nên bồn cầu lệch 403 / 498;
#      - tường: biên Room (Finish), mặt tường Revit, lớp ốp;
#      - MÉP LAVABO đã đặt trong mô hình (người dùng chốt 2026-10-30: 12/32 bồn cầu G19 nằm cạnh lavabo cùng tường, trước
#        đó bị đo tới tường sau lavabo): khung bao instance family tên chứa "lavabo" hoặc Comments của tool 14; chỉ làm
#        biên hai bên, không làm mặt dựa.
#      Thiếu biên một / hai phía, hoặc phải dời > IN[10] (mặc định 300 mm) → giữ theo tâm bồn cầu CAD, báo "CẦN SOÁT".
#   5. Type: chọn ở IN[3] (node Family Types hoặc chuỗi "Family : Type"), mặc định "AV-Toilet1 : AV-Toilet 2" (bồn cầu
#      một khối có sẵn trong mô hình G19; còn "AV-Toilet : AV-Toilet" cùng hình). Dùng thẳng type, không nhân bản.
#      Family đặt theo level (Elevation from Level = 0) hoặc Work Plane Based ("AV-Toilet1" – lần chạy 2026-10-30 báo
#      WorkPlaneBased): đặt lên mặt phẳng level qua Level.GetPlaneReference(), Offset from Host = 0.
#   6. Căn theo HÌNH KHỐI THẬT của family (không cần biết gốc / hướng family – type "AV-Toilet" có khung bao kiểu
#      −250…1722 × −1664…411 mm vì vùng thông thủy, không dùng được): đặt tại điểm trên mặt dựa, mặt trước family (+Y)
#      theo hướng ra phòng; đọc các khối đặc (Solid, mỗi khối ≤ 1500 mm trên mặt bằng – bỏ khối thông thủy) rồi:
#      - thân dài nằm ngang dọc tường → xoay 90°;
#      - két nước (phần khối cao ≥ 550 mm so với level) nằm phía trước → xoay 180°;
#      - dời cho lưng khối áp mặt dựa, TRỤC QUA GỐC FAMILY theo vị trí dọc tường (bước 4) – khung khối lệch trục 9,5 mm;
#      Không có khối cao (bồn cầu treo tường không két) → giữ hướng +Y, chỉ dời. Comments = "ARV-TaoBonCauTuCAD".
#      Đã có bồn cầu cùng family gần đó (tâm khối cách tâm bồn cầu CAD ≤ 600 mm) → bỏ qua; bồn cầu của tool lệch
#      vị trí / sai hướng / sai cao độ / khác type → sửa tại chỗ (không xoá, không tạo lại).
# INPUT
#   IN[0] (str)   Một phần tên bản CAD (để trống = bản CAD duy nhất trong mô hình / có layer khớp IN[1])
#   IN[1] (str)   Lọc layer, nhiều chuỗi cách ';' (khớp chuỗi con); trống = dò mọi layer (mặc định)
#   IN[2] (str)   Tên level đặt bồn cầu, VD "TẦNG 3"
#   IN[3] (FamilyType | str) Type bồn cầu (node Family Types, hoặc "AV-Toilet1 : AV-Toilet 2")
#   IN[4] (str)   Tên Room chứa bồn cầu, nhiều chuỗi cách ';', VD "WC;vệ sinh" (trống = mọi phòng)
#   IN[5] (float) Bề rộng bồn cầu CAD (dây cung mũi) tối thiểu (mm), VD 300
#   IN[6] (float) Bề rộng bồn cầu CAD tối đa (mm), VD 550
#   IN[7] (float) Chiều dài bồn cầu CAD (lưng → mũi) tối thiểu (mm), VD 550
#   IN[8] (float) Chiều dài bồn cầu CAD tối đa (mm), VD 900
#   IN[9] (float) Chiều dày vách kính CAD tối đa (mm), VD 30
#   IN[10] (float) Dời dọc tường tối đa so với tâm bồn cầu CAD (mm), VD 300
#   IN[11] (bool) Dry-run: True = chỉ báo cáo + xem trước, không ghi vào mô hình (mặc định True)
# OUTPUT
#   OUT[0] (list[str])  Báo cáo: tóm tắt, đường dẫn log, rồi từng bồn cầu
#   OUT[1] (list[Line]) Xem trước: hình bồn cầu CAD, đoạn thông thủy giữa hai biên, khung bồn cầu sẽ đặt (mm)

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
                                   SpatialElementBoundaryLocation, ElementId, Solid, ViewDetailLevel)
    from Autodesk.Revit.DB.Structure import StructuralType
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = u"ARV - Tạo bồn cầu từ CAD"
SCRIPT_TAG = u"ARV_TaoBonCauTuCAD_v1"
COMMENT_TAG = u"ARV-TaoBonCauTuCAD"
LAVABO_TAG = u"ARV-TaoLavaboTuCAD"
GLASS_TAG = u"ARV-TaoVachKinhTamTuCAD"
CAD_GLASS = u"vách kính CAD"
REVIT_GLASS = u"vách kính Revit"
MAX_EDGE_MM = 3000.0             # Nét dài hơn không thể là nét bồn cầu / vách kính – bỏ khi đọc CAD
SNAP_MM = 1.0                    # Đầu mút cách nhau ≤ chừng này coi là nối nhau (vòng kín vách kính)
JOIN_MM = 3.0                    # … khi nối hình U bồn cầu (nới so với SNAP_MM – dry-run G19 2026-10-30: 0/80 cung)
NEAR_MM = 50.0                   # Chẩn đoán: tìm đầu mút lân cận đầu cung trong khoảng này
MAX_PATH_EDGES = 40              # Số bước duyệt tối đa trong cụm nét bồn cầu (polyline tách thành từng đoạn)
MAX_LOOP_EDGES = 64
RIGHT_COS = 0.02                 # Góc vuông: |cos| ≤ chừng này (lệch ≤ ~1°)
SAG_RATIO = 0.25                 # Độ võng cung mũi ≥ tỉ lệ này × dây cung
WIDTH_TOL_MM = 50.0              # Bề rộng hình bồn cầu vượt dây cung tối đa
SAME_MM = 100.0                  # Hai bồn cầu có lưng cách ≤ chừng này = cùng một ký hiệu
PARALLEL_COS = 0.995             # Mặt song song / vuông góc mặt dựa: |cos| ≥ chừng này
MOUNT_TOL_MM = 150.0             # Mặt dựa cách lưng bồn cầu CAD tối đa (phía sau)
MOUNT_FRONT_MM = 50.0            # … hoặc lấn vào trong bồn cầu CAD tối đa
STRIP_MM = 300.0                 # Biên hai bên phải chạm dải này trước mặt dựa
SIDE_RANGE_MM = 1500.0           # Tìm biên hai bên trong khoảng này tính từ tâm bồn cầu
GLASS_MIN_MM = 300.0             # Vách kính CAD dài tối thiểu / tối đa
GLASS_MAX_MM = 3000.0
PANEL_MIN_MM = 200.0             # Tấm kính trong family vách kính dài tối thiểu (bỏ thanh, tay nắm)
EXIST_TOL_MM = 600.0             # Tâm khối bồn cầu cùng family cách tâm bồn cầu CAD ≤ chừng này → đã có (400 không đủ
                                 # nhận bồn cầu lệch 480 mm của lần chạy 14:30; bồn cầu gần nhau nhất G19 cách > 2000)
BODY_MAX_MM = 1500.0             # Khối đặc của family lớn hơn (trên mặt bằng) = vùng thông thủy – bỏ
TANK_Z_MM = 550.0                # Phần khối cao hơn chừng này so với level = két nước (phía lưng)
AXIS_TOL_MM = 30.0               # Gốc family lệch tâm khung khối ≤ chừng này → coi gốc nằm trên trục bồn cầu
LONG_RATIO = 1.15               # Thân dọc tường dài hơn chừng này × chiều sâu → family đang nằm ngang, xoay 90°


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


class Toilet(object):
    """Bồn cầu nhận diện được trên CAD + bồn cầu sẽ đặt. Hệ trục riêng: gốc = giữa lưng bồn cầu CAD, dir = hướng mặt
    trước (ra phòng), u = dọc tường; s = toạ độ dọc tường, d = toạ độ ra phòng (lưng CAD d = 0, mũi d = length)."""

    def __init__(self, back, d, width, length, outline):
        self.back, self.width, self.length, self.outline = back, width, length, outline
        self.dir = d
        self.u = (-d[1], d[0])
        self.c = self.world(0.0, length / 2.0)      # tâm bồn cầu CAD
        self.mount_d = 0.0       # mặt dựa (d)
        self.lo = self.hi = None  # (s, kind, tên) biên hai bên
        self.s = 0.0             # vị trí tâm bồn cầu dọc tường (s)
        self.room = u""
        self.status = u""
        self.type_name = u""
        self.eid = u""
        self.note = u""
        self.dups = []

    def local(self, p):
        q = sub(p, self.back)
        return dot(q, self.u), dot(q, self.dir)

    def world(self, s, d):
        return (self.back[0] + self.u[0] * s + self.dir[0] * d, self.back[1] + self.u[1] * s + self.dir[1] * d)

    def insert_point(self):
        return self.world(self.s, self.mount_d)

    def target_center(self):
        return self.world(self.s, self.mount_d + self.length / 2.0)


def find_toilets(items, min_w, max_w, min_len, max_len, stats=None, diag=None):
    """Cung mũi bồn cầu (dây cung min_w–max_w, võng ≥ SAG_RATIO) có hai đầu nối được qua chuỗi nét khác → hình U kín.
    diag (list): nhận mỗi cung đúng cỡ một dòng chẩn đoán (tâm dây cung, dây, võng, đầu mút lân cận, kết quả)."""
    nodes, coarse = {}, {}

    def key(p):
        return (int(round(p[0] / JOIN_MM)), int(round(p[1] / JOIN_MM)))

    def ckey(p):
        return (int(p[0] // NEAR_MM), int(p[1] // NEAR_MM))

    def joined(p, q):
        return abs(p[0] - q[0]) <= JOIN_MM and abs(p[1] - q[1]) <= JOIN_MM

    # Đồ thị theo MỌI ĐỈNH: nét thẳng / polyline tách thành từng đoạn, nét cong là một cạnh. G19: polyline thân bồn cầu
    # vẽ đi vẽ lại (lưng → két → quay về), nét đáy chạm đỉnh GIỮA polyline chứ không chạm đầu mút (dry-run 14:27).
    edges = []                   # (đầu a, đầu b, item, [điểm])
    for i, it in enumerate(items):
        if len(it.pts) < 2:
            continue
        for k, p in enumerate((it.pts[0], it.pts[-1])):
            coarse.setdefault(ckey(p), []).append((p, i, k))
        parts = [it.pts] if it.curved else [[it.pts[k - 1], it.pts[k]] for k in range(1, len(it.pts))]
        for seg in parts:
            if not joined(seg[0], seg[-1]):
                edges.append((seg[0], seg[-1], i, seg))
    for ei, e in enumerate(edges):
        nodes.setdefault(key(e[0]), set()).add(ei)
        nodes.setdefault(key(e[1]), set()).add(ei)

    def ends_near(p, skip):
        """Chẩn đoán: số đầu mút nét khác trong JOIN_MM, nét gần nhất trong NEAR_MM (loại, khoảng cách, số điểm)."""
        c = ckey(p)
        near = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for q, j, k in coarse.get((c[0] + dx, c[1] + dy), []):
                    dist = math.hypot(*sub(q, p))
                    if j != skip and dist <= NEAR_MM:
                        near.append((dist, j))
        if not near:
            return u"không có đầu mút ≤ {:.0f} mm".format(NEAR_MM)
        near.sort()
        dist, j = near[0]
        it = items[j]
        return u"{} nối ≤ {:.0f} mm; gần nhất {:.2f} mm ({} {} điểm{})".format(
            len([1 for x in near if x[0] <= JOIN_MM]), JOIN_MM, dist, u"cong" if it.curved else u"thẳng",
            len(it.pts), u", khép" if same(it.pts[0], it.pts[-1]) else u"")

    def around(p):
        k = key(p)
        hit = set()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                hit |= nodes.get((k[0] + dx, k[1] + dy), set())
        return hit

    def walk(arc_i, starts, inside, goal=None):
        """Duyệt cạnh (bỏ cung arc_i, chỉ cạnh nằm trong dải bồn cầu `inside`) từ các điểm starts, ≤ MAX_PATH_EDGES bước.
        goal ≠ None: True nếu tới được goal. goal = None: trả về mọi cạnh tới được (cụm nét bồn cầu)."""
        frontier = list(starts)
        seen = set()
        for _ in range(MAX_PATH_EDGES):
            nxt = []
            for p in frontier:
                for ei in around(p):
                    if ei in seen:
                        continue
                    a, b, item, seg = edges[ei]
                    if item == arc_i or not inside(seg):
                        continue
                    if joined(a, p):
                        e = b
                    elif joined(b, p):
                        e = a
                    else:
                        continue
                    seen.add(ei)
                    if goal is not None and joined(e, goal):
                        return True
                    nxt.append(e)
            if not nxt:
                break
            frontier = nxt
        return [edges[ei][3] for ei in seen] if goal is None else False

    arcs = chords = closed = 0
    found = []
    for i, it in enumerate(items):
        if not it.curved or len(it.pts) < 3:
            continue
        arcs += 1
        e1, e2 = it.pts[0], it.pts[-1]
        chord = math.hypot(*sub(e2, e1))
        if not (min_w <= chord <= max_w):
            continue
        cm = ((e1[0] + e2[0]) / 2.0, (e1[1] + e2[1]) / 2.0)
        u = unit(sub(e2, e1))
        n = (-u[1], u[0])
        far = max(it.pts, key=lambda p: abs(dot(sub(p, cm), n)))
        sag = dot(sub(far, cm), n)
        if abs(sag) < SAG_RATIO * chord:
            continue
        chords += 1
        d = n if sag > 0 else (-n[0], -n[1])         # hướng mặt trước

        def inside(seg, cm=cm, d=d, u=u, half=chord / 2.0 + WIDTH_TOL_MM, front=abs(sag) + JOIN_MM):
            # Dải bồn cầu: rộng ≤ dây cung + WIDTH_TOL_MM, từ mũi lùi về sau ≤ chiều dài tối đa
            for p in seg:
                q = sub(p, cm)
                t = dot(q, d)
                if abs(dot(q, u)) > half or t > front or t < front - max_len - JOIN_MM:
                    return False
            return True

        row = [fmt(cm), u"{:.0f}".format(chord), u"{:.0f}".format(abs(sag)),
               u"{} | {}".format(ends_near(e1, i), ends_near(e2, i))]
        if diag is not None:
            diag.append(row)
        if not walk(i, [e1], inside, e2):
            row += [u"", u"", u"", u"không khép được hai đầu cung"]
            continue
        closed += 1
        body = walk(i, [e1, e2], inside)
        pts = [p for seg in body for p in seg] + list(it.pts)
        ts = [dot(sub(p, cm), d) for p in pts]
        ss = [dot(sub(p, cm), u) for p in pts]
        t_back = min(ts)
        length = max(ts) - t_back
        width = max(ss) - min(ss)
        row += [len(body), u"{:.0f}".format(length), u"{:.0f}".format(width)]
        if not (min_len <= length <= max_len) or width > chord + WIDTH_TOL_MM:
            row.append(u"sai dài / rộng")
            continue
        row.append(u"bồn cầu")
        back = (cm[0] + d[0] * t_back, cm[1] + d[1] * t_back)
        found.append(Toilet(back, d, chord, length, body + [list(it.pts)]))
    result = []
    for tb in found:
        if all(math.hypot(*sub(tb.back, r.back)) > SAME_MM for r in result):
            result.append(tb)
    if stats is not None:
        stats.update(arcs=arcs, chords=chords, closed=closed)
    return result


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
            segs += [Seg(c[0], c[1], u"glass", CAD_GLASS), Seg(c[2], c[3], u"glass", CAD_GLASS)]
        else:
            segs += [Seg(c[1], c[2], u"glass", CAD_GLASS), Seg(c[3], c[0], u"glass", CAD_GLASS)]
    return segs


def fit_mount(tb, segs):
    """Mặt dựa: mặt song song tường gần lưng bồn cầu CAD nhất (sau lưng ≤ MOUNT_TOL_MM, lấn vào ≤ MOUNT_FRONT_MM),
    phủ tâm bồn cầu. Trả về lỗi hoặc None."""
    best = None
    for sg in segs:
        if sg.kind == u"glass":
            continue
        sa, da = tb.local(sg.a)
        sb, db = tb.local(sg.b)
        ln = math.hypot(sb - sa, db - da)
        if ln < 1.0 or abs(sb - sa) / ln < PARALLEL_COS:
            continue
        if not (min(sa, sb) - 1.0 <= 0.0 <= max(sa, sb) + 1.0):
            continue
        d = (da + db) / 2.0
        if -MOUNT_TOL_MM <= d <= MOUNT_FRONT_MM and (best is None or abs(d) < abs(best)):
            best = d
    if best is None:
        return u"không có mặt tường / hoàn thiện sau lưng bồn cầu (≤ {:.0f} mm)".format(MOUNT_TOL_MM)
    tb.mount_d = best
    return None


def fit_sides(tb, segs, max_shift):
    """Biên hai bên + vị trí dọc tường: giữa vách kính – tường hoặc tường – tường. Trả về ghi chú."""
    sides = ([], [])             # ứng viên biên phía s < 0, s > 0
    for sg in segs:
        sa, da = tb.local(sg.a)
        sb, db = tb.local(sg.b)
        ln = math.hypot(sb - sa, db - da)
        if ln < 1.0 or abs(db - da) / ln < PARALLEL_COS:
            continue
        s = (sa + sb) / 2.0
        if abs(s) > SIDE_RANGE_MM or abs(s) < 1.0:
            continue
        # Phải chạm dải STRIP_MM ngay trước mặt dựa (loại cánh cửa kính mở, tường xa)
        if max(da, db) < tb.mount_d + 1.0 or min(da, db) > tb.mount_d + STRIP_MM:
            continue
        sides[0 if s < 0 else 1].append((s, sg.kind, sg.name))

    def nearest(cands):
        # Vách kính trong mô hình thắng vách kính CAD: người dùng chỉnh thông thủy trên Revit, CAD còn vị trí cũ
        if any(c[1] == u"glass" and c[2] != CAD_GLASS for c in cands):
            cands = [c for c in cands if c[2] != CAD_GLASS]
        return min(cands, key=lambda c: abs(c[0])) if cands else None

    lo, hi = nearest(sides[0]), nearest(sides[1])
    tb.lo, tb.hi = lo, hi
    tb.s = 0.0
    if lo is None or hi is None:
        return u"thiếu biên {} – giữ tâm bồn cầu CAD, cần soát".format(u"hai phía" if lo is None and hi is None
                                                                        else u"một phía")
    mid = (lo[0] + hi[0]) / 2.0
    kinds = sorted((lo[1], hi[1]), key=lambda k: {u"glass": 0, u"lavabo": 1}.get(k, 2))
    kind = u"{} – {}".format(*[{u"glass": u"vách kính", u"lavabo": u"lavabo"}.get(k, u"tường") for k in kinds])
    if abs(mid) > max_shift:
        return u"giữa {} lệch CAD {:+.0f} mm > {:.0f} – giữ tâm bồn cầu CAD, cần soát".format(kind, mid, max_shift)
    tb.s = mid
    return u"giữa {} (thông thủy {:.0f} mm){}".format(
        kind, hi[0] - lo[0], u", dời {:+.0f} mm so với CAD".format(mid) if abs(mid) >= 1.0 else u"")


def body_fit(pts3, tb, level_z, origin=None):
    """Căn hình khối family theo bồn cầu đích. pts3: [(x, y, z) mm] đỉnh các khối đặc của instance (đang đặt);
    origin: gốc family (x, y mm) – dọc tường căn theo trục qua gốc, xem AXIS_TOL_MM.
    Trả về (góc xoay rad quanh điểm đặt, dời (dx, dy), [việc], dài khối) – None nếu không có khối."""
    if not pts3:
        return None
    p0 = tb.insert_point()
    pts = [(p[0], p[1]) for p in pts3]
    tall = [i for i, p in enumerate(pts3) if p[2] - level_z >= TANK_Z_MM]
    ang, todo = 0.0, []

    def frame(ps):
        ss = [dot(sub(p, p0), tb.u) for p in ps]
        ds = [dot(sub(p, p0), tb.dir) for p in ps]
        return ss, ds

    ss, ds = frame(pts)
    if max(ss) - min(ss) > LONG_RATIO * (max(ds) - min(ds)):
        ang += math.pi / 2.0
        pts = [rotate(p, math.pi / 2.0, p0) for p in pts]
        ss, ds = frame(pts)
    if tall:
        tank = sum(ds[i] for i in tall) / len(tall)
        if tank > (min(ds) + max(ds)) / 2.0:
            ang += math.pi
            pts = [rotate(p, math.pi, p0) for p in pts]
            ss, ds = frame(pts)
    ang = math.atan2(math.sin(ang), math.cos(ang))
    if abs(ang) > 1e-3:
        todo.append(u"xoay {:.0f}°".format(math.degrees(ang)))
    if not tall:
        todo.append(u"không thấy két nước (khối cao ≥ {:.0f} mm) – giữ hướng mặt trước +Y family".format(TANK_Z_MM))
    # ss, ds đo từ điểm đặt (đã gồm tb.s, tb.mount_d) → đích là 0; cộng lại tb.s / tb.mount_d là dời hai lần (lần chạy
    # 2026-10-30 14:30: #19, #20 lệch 240 mm dọc tường, lưng lấn 50 mm vào tường)
    m_s = -(min(ss) + max(ss)) / 2.0
    if origin is not None:
        # Khung khối không đối xứng (AV-Toilet1 lệch 9,5 mm so với trục qua gốc family – người dùng đo 2026-10-30: 413/432,
        # 440/460) → dọc tường căn theo trục gốc family; gốc lệch xa khung (family không đối xứng qua gốc) → giữ tâm khung
        o = dot(sub(rotate(origin, ang, p0), p0), tb.u)
        if abs(o + m_s) <= AXIS_TOL_MM:
            m_s = -o
    m_d = -min(ds)
    move = (tb.u[0] * m_s + tb.dir[0] * m_d, tb.u[1] * m_s + tb.dir[1] * m_d)
    return ang, move, todo, max(ds) - min(ds)


def analyse(items, walls, min_w, max_w, min_len, max_len, max_t, max_shift, room_at=None, room_keys=(), stats=None,
            diag=None, lavabos=(), revit_glass=()):
    """items: [Item] mm; walls: [HostWall] trên level (gồm lớp ốp mỏng); room_at(pt) → (tên, [vòng]) | None.
    Trả về [Toilet] đã gán trạng thái (chưa xét bồn cầu đã có)."""
    toilets = find_toilets(items, min_w, max_w, min_len, max_len, stats, diag)
    glass = find_glass(find_loops(items), max_t)
    wall_segs = [f for w in walls for f in w.faces()]
    if stats is not None:
        stats.update(glass=len(glass) // 2)
    room_segs = {}
    for tb in toilets:
        hit = room_at(tb.c) if room_at is not None else None
        tb.room = hit[0] if hit else u""
        if room_at is not None and room_keys and not any(k in loose(tb.room) for k in room_keys):
            tb.status = u"Bỏ qua – không nằm trong phòng {} (phòng: {})".format(
                u"/".join(room_keys), tb.room or u"không có Room")
            continue
        key = id(hit[1]) if hit else None
        if key not in room_segs:
            segs = list(wall_segs)
            for pts in (hit[1] if hit else []):
                segs += [Seg(pts[i - 1], pts[i], u"room", u"biên Room") for i in range(len(pts))]
            room_segs[key] = segs
        segs = room_segs[key]
        err = fit_mount(tb, segs)
        if err:
            tb.status = u"Bỏ qua – " + err
            continue
        # Lavabo chỉ làm biên hai bên, không làm mặt dựa
        tb.note = fit_sides(tb, segs + glass + list(revit_glass) + list(lavabos), max_shift)
        tb.status = u"OK"
    toilets.sort(key=lambda x: (-round(x.c[1]), round(x.c[0])))
    return toilets


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
    """Nét ngắn trên các layer – ứng viên nét bồn cầu (thẳng + cong) và vách kính. Trả về (items, {loại: số})."""
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
            elif isinstance(obj, (Arc, Ellipse, NurbSpline, HermiteSpline)) and obj.Length <= 2 * lim:
                items.append(Item([xy(p) for p in obj.Tessellate()], True))
    return items, kinds


def level_walls(level):
    """Tường thẳng trên level (mọi chiều dày, gồm lớp ốp mỏng) → [HostWall]."""
    result = []
    for wl in FilteredElementCollector(doc).OfClass(Wall).ToElements():
        loc = wl.Location
        if wl.LevelId == level.Id and isinstance(loc, LocationCurve) and isinstance(loc.Curve, Line):
            c = loc.Curve
            hw = HostWall(wl.Id.Value, xy(c.GetEndPoint(0)), xy(c.GetEndPoint(1)), to_mm(wl.Width), get_name(wl))
            if hw.length >= 1.0:
                result.append(hw)
    return result


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


def pick_template(value):
    """IN[3]: FamilyType của node Family Types (Dynamo) hoặc chuỗi "Family : Type" → FamilySymbol bồn cầu."""
    symbols = fixture_symbols()
    families = u", ".join(sorted(set(s.FamilyName for s in symbols))) or u"không có"
    if isinstance(value, str):
        parts = [norm(p) for p in value.split(u":")]
        if len(parts) != 2 or not all(parts):
            raise StopReport([u"DỪNG: ô IN[3] phải là type chọn từ node Family Types hoặc chuỗi 'Family : Type' "
                              u"(đang là '{}').".format(value)])
        hits = [s for s in symbols if norm(s.FamilyName) == parts[0] and norm(get_name(s)) == parts[1]]
        if not hits:
            raise StopReport([u"DỪNG: không có type bồn cầu '{}'. Family thiết bị vệ sinh: {}".format(value, families)])
        return hits[0]
    sym = UnwrapElement(value) if value is not None else None
    if not isinstance(sym, FamilySymbol):
        raise StopReport([u"DỪNG: chưa chọn type bồn cầu ở IN[3]."])
    if sym.Category is None or sym.Category.BuiltInCategory != BuiltInCategory.OST_PlumbingFixtures:
        raise StopReport([u"DỪNG: type '{} : {}' không thuộc Plumbing Fixtures. Family thiết bị vệ sinh: {}".format(
            sym.FamilyName, get_name(sym), families)])
    return sym


def body_points(fi):
    """Đỉnh (x, y, z mm) các khối đặc của instance; bỏ khối lớn hơn BODY_MAX_MM trên mặt bằng (vùng thông thủy)."""
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
                if not pts:
                    continue
                xs, ys = [to_mm(p.X) for p in pts], [to_mm(p.Y) for p in pts]
                if max(max(xs) - min(xs), max(ys) - min(ys)) > BODY_MAX_MM:
                    continue
                result.extend((x, y, to_mm(p.Z)) for x, y, p in zip(xs, ys, pts))

    geo = fi.get_Geometry(opt)
    if geo is not None:
        walk(geo)
    return result


def glass_panels(fi, max_t):
    """Hai mặt dài (Seg "glass") của mỗi tấm kính trong instance: khối đặc mỏng ≤ max_t, dài ≥ PANEL_MIN_MM, song song
    trục toạ độ (cánh vát góc không thoả – bỏ, đúng ý: biên hai bên chỉ là tấm vuông góc mặt dựa)."""
    opt = Options()
    opt.DetailLevel = ViewDetailLevel.Fine
    segs = []

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
                x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
                y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
                w, h = x1 - x0, y1 - y0
                if min(w, h) > max_t or max(w, h) < PANEL_MIN_MM:
                    continue
                if w >= h:
                    segs.extend(Seg((x0, y), (x1, y), u"glass", REVIT_GLASS) for y in (y0, y1))
                else:
                    segs.extend(Seg((x, y0), (x, y1), u"glass", REVIT_GLASS) for x in (x0, x1))

    geo = fi.get_Geometry(opt)
    if geo is not None:
        walk(geo)
    return segs


def glass_fixtures(level, max_t):
    """Vách kính đã đặt trên level: family tên chứa "vach kinh" / "vach tam" hoặc Comments của tool 17 (tool đặt cả hai
    family của G19). Trả về (segs, số vách, số vách không đọc được tấm kính)."""
    segs, n, miss = [], 0, 0
    for fi in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures) \
            .WhereElementIsNotElementType().ToElements():
        sym = getattr(fi, "Symbol", None)
        if sym is None or fi.LevelId != level.Id:
            continue
        name = loose(sym.FamilyName)
        cm = fi.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        if u"vach kinh" not in name and u"vach tam" not in name and (cm is None or cm.AsString() != GLASS_TAG):
            continue
        n += 1
        panels = glass_panels(fi, max_t)
        if panels:
            segs += panels
        else:
            miss += 1
    return segs, n, miss


def lavabo_edges(level):
    """4 cạnh khung bao (Seg "lavabo") của lavabo trên level: family tên chứa "lavabo" hoặc Comments của tool 14.
    Trả về (segs, số lavabo)."""
    segs, n = [], 0
    for fi in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures) \
            .WhereElementIsNotElementType().ToElements():
        sym = getattr(fi, "Symbol", None)
        if sym is None or fi.LevelId != level.Id:
            continue
        cm = fi.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        if u"lavabo" not in loose(sym.FamilyName) and (cm is None or cm.AsString() != LAVABO_TAG):
            continue
        bb = fi.get_BoundingBox(None)
        if bb is None:
            continue
        x0, y0 = xy(bb.Min)
        x1, y1 = xy(bb.Max)
        box = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        segs += [Seg(box[i - 1], box[i], u"lavabo", u"lavabo") for i in range(4)]
        n += 1
    return segs, n


def existing_fixtures(family_name, level):
    """[(tâm khối mm, Id, có Comments của tool)] bồn cầu đã đặt trên level: cùng family, hoặc do tool tạo."""
    result = []
    for fi in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures) \
            .WhereElementIsNotElementType().ToElements():
        sym = getattr(fi, "Symbol", None)
        if sym is None or not isinstance(getattr(fi, "Location", None), LocationPoint):
            continue
        # Family Work Plane Based đặt trên mặt level: LevelId có thể trống, host là level
        host = getattr(fi, "Host", None)
        if fi.LevelId != level.Id and (host is None or host.Id != level.Id):
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


def apply_fit(fi, fit, tb):
    """Xoay (quanh điểm đặt) + dời theo kết quả body_fit."""
    ang, move = fit[0], fit[1]
    p = tb.insert_point()
    if abs(ang) > 1e-3:
        pivot = XYZ(from_mm(p[0]), from_mm(p[1]), 0.0)
        ElementTransformUtils.RotateElement(doc, fi.Id, Line.CreateBound(pivot, XYZ(pivot.X, pivot.Y, 1.0)), ang)
    if math.hypot(*move) > 0.5:
        ElementTransformUtils.MoveElement(doc, fi.Id, XYZ(from_mm(move[0]), from_mm(move[1]), 0.0))


def preview_lines(toilets, z_mm):
    try:
        clr.AddReference("ProtoGeometry")
        from Autodesk.DesignScript.Geometry import Point as DSPoint, Line as DSLine

        def seg(a, e):
            return DSLine.ByStartPointEndPoint(DSPoint.ByCoordinates(a[0], a[1], z_mm),
                                               DSPoint.ByCoordinates(e[0], e[1], z_mm))
        lines = []
        for tb in toilets:
            for pts in tb.outline:
                lines += [seg(pts[i - 1], pts[i]) for i in range(1, len(pts)) if not same(pts[i - 1], pts[i])]
            d = tb.mount_d + 20.0
            if tb.lo and tb.hi:
                lines.append(seg(tb.world(tb.lo[0], d), tb.world(tb.hi[0], d)))
            h = tb.width / 2.0
            box = [tb.world(tb.s + a * h, tb.mount_d + b * tb.length) for a, b in ((-1, 0), (1, 0), (1, 1), (-1, 1))]
            lines += [seg(box[i - 1], box[i]) for i in range(4)]
        return lines
    except Exception:
        return []


LOG_HEADER = [u"STT", u"Tâm bồn cầu CAD (mm)", u"Phòng", u"Biên trái", u"Biên phải", u"Lưng bồn cầu (mm)", u"Type",
              u"Kết quả", u"ElementId", u"Ghi chú"]


def bound_label(b):
    if b is None:
        return u"—"
    return u"{} ({:+.0f})".format({u"glass": u"vách kính", u"lavabo": u"lavabo"}.get(b[1], b[2] or b[1]), b[0])


DIAG_HEADER = [u"Tâm dây cung (mm)", u"Phòng", u"Dây cung", u"Độ võng", u"Đầu mút lân cận (đầu 1 | đầu 2)", u"Số nét khép",
               u"Dài", u"Rộng", u"Kết quả"]
DIAG_RAW = 6                     # Ghi toạ độ mọi nét quanh chừng này cung đầu tiên trong WC (để đo lại hình CAD)
DIAG_BOX_MM = 900.0


def write_diag(diag, items, room_at):
    """File chẩn đoán (chỉ dry-run): mỗi cung đúng cỡ một dòng; kèm toạ độ đầy đủ các nét quanh vài cung đầu trong WC."""
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    path = os.path.join(folder, "TaoBonCauTuCAD_CHANDOAN_{}.csv".format(
        datetime.datetime.now().strftime("%Y%m%d_%H%M%S")))
    centers = []
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(DIAG_HEADER)
        for row in diag:
            c = tuple(float(v) for v in row[0].strip(u"()").split(u","))
            hit = room_at(c) if room_at is not None else None
            room = hit[0] if hit else u""
            w.writerow([row[0], room] + row[1:])
            if room and len(centers) < DIAG_RAW:
                centers.append(c)
        w.writerow([])
        w.writerow([u"NÉT CAD QUANH {} CUNG ĐẦU TRONG PHÒNG (khung ± {:.0f} mm)".format(len(centers), DIAG_BOX_MM)])
        w.writerow([u"Cung số", u"Nét cong", u"Số điểm", u"Toạ độ (x y; …)"])
        for k, c in enumerate(centers, 1):
            for it in items:
                if all(abs(p[0] - c[0]) <= DIAG_BOX_MM and abs(p[1] - c[1]) <= DIAG_BOX_MM for p in it.pts):
                    w.writerow([k, u"có" if it.curved else u"", len(it.pts),
                                u"; ".join(u"{:.1f} {:.1f}".format(p[0], p[1]) for p in it.pts)])
    return path


def write_log(rows, source, dry_run):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoBonCauTuCAD_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
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


def main(cad_filter, layer_filters, level_name, template_in, room_keys, min_w, max_w, min_len, max_len, max_t,
         max_shift, dry_run):
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."], []
    if re.search(r"[-_]S[-_]", doc.Title or u""):
        return [u"DỪNG: tên file '{}' là mô hình Kết cấu (S) – bồn cầu chỉ dựng trên mô hình Kiến trúc (A).".format(
            doc.Title)], []
    sym = pick_template(template_in)
    fam = norm(sym.FamilyName)
    type_label = u"{} : {}".format(fam, get_name(sym))
    placement = sym.Family.FamilyPlacementType
    if placement not in (FamilyPlacementType.OneLevelBased, FamilyPlacementType.WorkPlaneBased):
        raise StopReport([u"DỪNG: family '{}' kiểu đặt {} – công cụ chỉ hỗ trợ family bồn cầu đặt theo level hoặc "
                          u"theo mặt phẳng làm việc (Work Plane Based).".format(fam, placement)])
    on_plane = placement == FamilyPlacementType.WorkPlaneBased
    cad, cad_name, objects, all_layers = pick_cad(cad_filter, layer_filters)
    layers = match_layers(all_layers, layer_filters)
    level = find_level(level_name)
    level_z = to_mm(level.Elevation)
    walls = level_walls(level)
    room_at, n_rooms = room_finder(level)
    keys = [loose(k) for k in room_keys if k.strip()]
    if keys and not n_rooms:
        raise StopReport([u"DỪNG: level '{}' chưa có Room – cần Room để lọc bồn cầu trong WC (hoặc để trống IN[4])."
                          .format(level_name)])

    items, kinds = read_items(objects, layers)
    stats = {}
    diag = []
    lav_segs, n_lav = lavabo_edges(level)
    glass_segs, n_glass, glass_miss = glass_fixtures(level, max_t)
    toilets = analyse(items, walls, min_w, max_w, min_len, max_len, max_t, max_shift, room_at, keys, stats, diag,
                      lav_segs, glass_segs)
    existing = existing_fixtures(fam, level)

    rows, jobs, fixes = [], [], []
    for idx, tb in enumerate(toilets, 1):
        if tb.status == u"OK":
            near = sorted((math.hypot(*sub(c, tb.c)), eid, mine) for c, eid, mine in existing
                          if math.hypot(*sub(c, tb.c)) <= EXIST_TOL_MM)
            if near:
                tb.eid = near[0][1]
                tb.dups = [eid for _, eid, _ in near[1:]]
                tb.status = u"Bỏ qua – đã có bồn cầu cùng family (Id {})".format(tb.eid)
                if near[0][2]:
                    # Bồn cầu của tool đã có → lệch / sai hướng / sai cao độ / khác type thì sửa tại chỗ.
                    # Bồn cầu người dùng tự đặt giữ nguyên.
                    fi = doc.GetElement(ElementId(tb.eid))
                    todo = []
                    retype = fi.Symbol.Id != sym.Id
                    if retype:
                        todo.append(u"đổi type {} : {} → {}".format(fi.Symbol.FamilyName, get_name(fi.Symbol),
                                                                    type_label))
                    ep = elevation_param(fi)
                    elev = ep is not None and abs(to_mm(ep.AsDouble())) > 1.0
                    if elev:
                        todo.append(u"cao độ {:.0f} → 0".format(to_mm(ep.AsDouble())))
                    fit = None
                    if not retype:
                        # Đổi type thì hình khối đổi – căn lại sau khi đổi trong Transaction
                        fit = body_fit(body_points(fi), tb, level_z + (to_mm(ep.AsDouble()) if elev else 0.0),
                                       xy(fi.Location.Point))
                        if fit is not None and (abs(fit[0]) > 1e-3 or math.hypot(*fit[1]) > 1.0):
                            todo += [t for t in fit[2] if t.startswith(u"xoay")]
                            if math.hypot(*fit[1]) > 1.0:
                                todo.append(u"dời {:.0f} mm".format(math.hypot(*fit[1])))
                        else:
                            fit = None
                    if todo:
                        tb.type_name = type_label
                        tb.note = u"; ".join(v for v in [tb.note] + todo if v)
                        tb.status = u"Sẽ sửa" if dry_run else u"Chờ sửa"
                        fixes.append((fi, len(rows), tb, retype, elev, fit))
            else:
                tb.type_name = type_label
                tb.status = u"Sẽ tạo" if dry_run else u"Chờ tạo"
                jobs.append((tb, len(rows)))
        rows.append([idx, fmt(tb.c), tb.room or u"—", bound_label(tb.lo), bound_label(tb.hi),
                     u"—" if tb.status.startswith(u"Bỏ qua – không") else fmt(tb.insert_point()), tb.type_name or u"—", tb.status, tb.eid,
                     u"; ".join(v for v in [tb.note] + [u"TRÙNG Id {}".format(d) for d in tb.dups] if v)])

    created = []
    if not dry_run and (jobs or fixes):
        TransactionManager.Instance.ForceCloseTransaction()
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        try:
            if not sym.IsActive:
                sym.Activate()
                doc.Regenerate()
            for fi, ri, tb, retype, elev, fit in fixes:
                if retype:
                    fi.ChangeTypeId(sym.Id)
                if elev:
                    set_elevation_zero(fi)
                doc.Regenerate()
                if retype:
                    fit = body_fit(body_points(fi), tb, level_z, xy(fi.Location.Point))
                if fit is not None:
                    apply_fit(fi, fit, tb)
                rows[ri][7] = u"Đã sửa"
            # Family đặt theo level: Revit hiểu Z của điểm đặt là độ lệch so với level → Z = 0, Elevation from Level = 0
            # (bài học tool lavabo 2026-10-30 10:16). Family Work Plane Based ("AV-Toilet1", lần chạy 2026-10-30): đặt
            # lên mặt phẳng của level (Level.GetPlaneReference), điểm đặt ở cao độ tuyệt đối của level, Offset = 0.
            for tb, ri in jobs:
                p = tb.insert_point()
                if on_plane:
                    pt = XYZ(from_mm(p[0]), from_mm(p[1]), level.Elevation)
                    fi = doc.Create.NewFamilyInstance(level.GetPlaneReference(), pt,
                                                      XYZ(tb.u[0], tb.u[1], 0.0), sym)
                else:
                    pt = XYZ(from_mm(p[0]), from_mm(p[1]), 0.0)
                    fi = doc.Create.NewFamilyInstance(pt, sym, level, StructuralType.NonStructural)
                orient(fi, tb.dir, pt)
                set_elevation_zero(fi)
                doc.Regenerate()
                fit = body_fit(body_points(fi), tb, level_z, xy(fi.Location.Point))
                note = u""
                if fit is None:
                    note = u"không đọc được khối đặc của family – đặt theo gốc family, mặt trước +Y, cần soát"
                else:
                    apply_fit(fi, fit, tb)
                    note = u"; ".join(fit[2])
                    if abs(fit[3] - tb.length) > 150.0:
                        note = u"; ".join(v for v in (note, u"family dài {:.0f} mm, bồn cầu CAD dài {:.0f} mm".format(
                            fit[3], tb.length)) if v)
                cm = fi.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
                if cm is not None and not cm.IsReadOnly:
                    cm.Set(COMMENT_TAG)
                rows[ri][7] = u"Đã tạo"
                rows[ri][8] = fi.Id.Value
                if note:
                    rows[ri][9] = u"; ".join(v for v in (rows[ri][9], note) if v)
                created.append((fi, ri))
            status = tx.Commit()
        except Exception as ex:
            tx.RollBack()
            return [u"LỖI khi tạo bồn cầu, mọi thay đổi đã được hoàn tác: {}".format(ex)], []
        if status != TransactionStatus.Committed:
            return [u"LỖI: Revit không lưu được Transaction ({}), mọi thay đổi đã được hoàn tác.".format(status)], []
        for fi, ri in created:
            if not fi.IsValidObject:
                rows[ri][7] = u"Revit đã xoá sau khi tạo"

    report = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN")]
    report.append(u"CAD: {} – dò {} – {} nét – nhận diện {} bồn cầu (hình U khép bằng cung mũi)".format(
        cad_name, u"layer " + u"; ".join(sorted(layers)) if layer_filters else u"mọi layer ({})".format(len(layers)),
        len(items), len(toilets)))
    report.append(u"Bồn cầu: {} ({}) – level {} – phòng chứa: {}".format(
        type_label, u"Work Plane Based, đặt trên mặt level" if on_plane else u"đặt theo level", level.Name, u"; ".join(room_keys) if keys else u"mọi phòng"))
    report.append(u"Bồn cầu {}: {}".format(u"sẽ tạo" if dry_run else u"đã tạo", len(jobs)))
    if fixes:
        report.append(u"Bồn cầu của tool {}: {} (đổi type: {}, cao độ: {}, xoay / dời: {})".format(
            u"sẽ sửa" if dry_run else u"đã sửa", len(fixes), len([1 for f in fixes if f[3]]),
            len([1 for f in fixes if f[4]]), len([1 for f in fixes if f[5] is not None])))
    dups = [(tb, d) for tb in toilets for d in tb.dups]
    if dups:
        report.append(u"TRÙNG: {} bồn cầu thừa cạnh nhau – xoá tay (giữ Id trong ngoặc): {}".format(
            len(dups), u", ".join(u"{} (giữ {})".format(d, tb.eid) for tb, d in dups)))
    placed = [tb for tb in toilets if tb.status in (u"Sẽ tạo", u"Chờ tạo", u"Đã tạo", u"Sẽ sửa", u"Chờ sửa")]
    kept = [tb for tb in placed if u"cần soát" in tb.note]
    if kept:
        report.append(u"CẦN SOÁT: {} bồn cầu giữ theo tâm CAD (thiếu biên / lệch nhiều) – xem cột Ghi chú".format(
            len(kept)))
    counts = {}
    for tb in toilets:
        if tb.status.startswith(u"Bỏ qua"):
            k = re.sub(r"[\d(].*", u"", tb.status.split(u" – ", 1)[1]).strip()
            counts[k] = counts.get(k, 0) + 1
    for k in sorted(counts):
        report.append(u"Bỏ qua {} bồn cầu: {}".format(counts[k], k))
    report.append(u"Chẩn đoán nhận diện: {} nét cong – {} cung dây {:.0f}–{:.0f} mm đủ võng – {} khép thành hình U – "
                  u"{} bồn cầu dài {:.0f}–{:.0f} mm – {} vách kính CAD (dày ≤ {:.0f} mm) – {} vách kính Revit "
                  u"({} tấm, {} vách không đọc được tấm) – {} lavabo làm biên – "
                  u"Room trên level: {}".format(
                      stats.get("arcs", 0), stats.get("chords", 0), min_w, max_w, stats.get("closed", 0),
                      len(toilets), min_len, max_len, stats.get("glass", 0), max_t, n_glass, len(glass_segs) // 2,
                      glass_miss, n_lav, n_rooms))
    report.append(u"Đối tượng CAD theo loại: " + u", ".join(u"{} {}".format(k, v) for k, v in sorted(kinds.items())))
    try:
        report.append(u"Log: " + write_log(rows, cad_name, dry_run))
        if dry_run and diag:
            report.append(u"Chẩn đoán cung mũi bồn cầu: " + write_diag(diag, items, room_at))
    except Exception as ex:
        report.append(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        report.append(u"Kiểm tra hình bồn cầu CAD + đoạn thông thủy + khung bồn cầu sẽ đặt (nét xanh trong Dynamo) và log. "
                      u"Thiếu bồn cầu → nới IN[5]–IN[8]. Đúng thì đổi Dry-run = False và Run lại. Undo bằng mục \"{}\"."
                      .format(TRANSACTION_NAME))
    else:
        report.append(u"Soát hướng vài bồn cầu (két nước sát tường). Undo bằng mục \"{}\".".format(TRANSACTION_NAME))
    report.append(u" | ".join(LOG_HEADER))
    report += [u" | ".join(u"{}".format(v) for v in r) for r in rows
               if not r[7].startswith(u"Bỏ qua – không nằm trong phòng")]
    return report, preview_lines([tb for tb, _ in jobs] + [f[2] for f in fixes], level_z)


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
            IN[3] if IN[3] is not None else u"AV-Toilet1 : AV-Toilet 2",
            (u"WC;vệ sinh" if IN[4] is None else IN[4]).split(u";"),
            num(5, 300.0),
            num(6, 550.0),
            num(7, 550.0),
            num(8, 900.0),
            num(9, 30.0),
            num(10, 300.0),
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
            with io.open(os.path.join(folder, "TaoBonCauTuCAD_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))), "w", encoding="utf-8-sig") as f:
                f.write(u"\n".join(OUT[0]))
        except Exception:
            pass
    note = force_rerun_next_time()
    if note:
        OUT[0].append(u"LƯU Ý: " + note)
