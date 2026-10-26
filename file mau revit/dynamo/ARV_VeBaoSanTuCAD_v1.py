# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong ARV_VeBaoSanTuCAD_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Vẽ đường bao sàn kết cấu (Detail Line) và tạo sàn (Floor) theo vùng hatch của ghi chú, từ mặt bằng
# kết cấu sàn (DWG đã Link vào Revit).
#   Đường bao vẽ (Detail Line, trong view mặt bằng đang mở):
#   - BAO NGOÀI: mép ngoài cùng của mặt bằng (mép ngoài dầm biên / mép sàn) – bỏ mọi nét bên trong.
#   - BAO LỖ MỞ: quanh từng lỗ mở có gạch chéo X (hai ô lỗ chung cạnh gộp một).
#   - BAO VÙNG HATCH: quanh từng vùng hatch có trong ghi chú (VD ANSI31 = sàn DƯL dày 230).
#     Nét chung giữa các đường bao chỉ vẽ một lần.
#   Sàn tạo (Floor kết cấu, level của view):
#   - Mỗi vùng hatch một tấm sàn, chiều dày / hạ cốt theo ghi chú (IN[4]).
#   - Sàn nền (phần không hatch, IN[5]) = bao ngoài − lỗ mở − vùng hatch (khoét, không chồng khối lượng).
#   - Type sàn: dùng type có sẵn đúng chiều dày (ưu tiên tên FLOOR_TYPE_NAME); chưa có → nhân bản type mẫu
#     (IN[6]) và chỉnh lớp kết cấu cho đúng chiều dày.
#   Cách dò:
#   - Nét trên layer mép sàn (mặc định S-Thay + S-Cot vach) tách tại giao điểm, dò ô kín nhỏ nhất.
#     Bao ngoài = biên ngoài của cụm nét không nằm lọt trong ô nào. Lỗ mở = ô chứa tâm dấu X.
#   - Hatch không đọc được trong bản link Revit nên được đọc từ BẢN SAO file DWG qua AutoCAD Core Console
#     (model space + trong block lồng nhau). Biên hatch được hút về nét mép sàn gần nhất (≤ HATCH_SNAP_MM),
#     rồi chia mặt bằng thành ô: ô trong lỗ mở → lỗ; ô trong hatch có ghi chú → vùng đó; còn lại → sàn nền.
# INPUT
#   IN[0] (str)   Một phần tên bản CAD (để trống nếu mô hình chỉ có 1 bản CAD)
#   IN[1] (str)   Layer mép sàn, nhiều chuỗi cách nhau ';' (khớp chuỗi con). Mặc định "S-Thay;S-Cot vach"
#   IN[2] (str)   Layer dấu X lỗ mở. Mặc định "S-Manh"
#   IN[3] (str)   Layer hatch vùng sàn (khớp chuỗi con). Mặc định "S-Hatch"
#   IN[4] (str)   Ghi chú hatch: "MẪU=dày[/cốt];..." mm, cốt âm = hạ cốt.
#                 Vùng hai hatch chồng nhau: "A+B=dày[/cốt]" (VD ANSI37+ANGLE=170/-30).
#                 Mặc định "ANSI31=230;STARS=250;TRIANG=500;ANSI37=450/-50"
#   IN[5] (str)   Sàn nền (khu vực không hatch): "dày[/cốt]". Mặc định "230/-50"
#   IN[6] (str)   Tên type sàn mẫu để nhân bản khi thiếu type đúng chiều dày. Mặc định "Generic 200"
#   IN[7] (str)   Line style của đường bao (phải có sẵn; để trống = mặc định của view)
#   IN[8] (float) Diện tích bao ngoài tối thiểu (m²). Mặc định 10
#   IN[9] (bool)  Dry-run: True = chỉ báo cáo, không ghi vào mô hình (mặc định True)
#                 False = vẽ đường bao + tạo sàn.
# OUTPUT
#   OUT[0] (list[str])   Báo cáo: tóm tắt, cảnh báo, rồi từng đường bao / tấm sàn
#   OUT[1] (list[Elem])  Detail Line đã vẽ
#   OUT[2] (list[Elem])  Sàn đã tạo

import os
import io
import re
import csv
import glob
import math
import shutil
import tempfile
import datetime
import subprocess

DYNAMO = "IN" in globals()

if DYNAMO:
    import clr
    clr.AddReference("RevitAPI")
    from Autodesk.Revit.DB import (FilteredElementCollector, ImportInstance, CADLinkType, Options, GeometryInstance,
                                   PolyLine, Line, Arc, XYZ, UnitUtils, UnitTypeId, ModelPathUtils, BuiltInParameter,
                                   BuiltInCategory, ViewPlan, CurveElement, CurveElementType, GraphicsStyleType,
                                   CurveLoop, Floor, FloorType)
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    from System.Collections.Generic import List

    doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = u"ARV - Vẽ đường bao sàn từ CAD"
SNAP_MM = 5.0          # Đầu nét cách nhau / cách nét khác ≤ giá trị này thì coi là chạm
HATCH_SNAP_MM = 10.0   # Đỉnh biên hatch cách nét mép sàn ≤ giá trị này → hút về nét đó
SLIVER_M2 = 0.01       # Ô nhỏ hơn (khe giữa biên hatch và nét) → nhập vào ô bên cạnh
INNER_MM = 1.0         # Điểm đại diện của ô: lùi vào trong từ trung điểm cạnh dài nhất
ARC_STEP_DEG = 10.0    # Cung tròn trong biên hatch chia đoạn mỗi ≤ 10°
DUP_TOL_MM = 1.0       # Nét mới trùng Detail Line đã có trong view → bỏ qua
CELL_MM = 3000.0       # Ô lưới tra cứu nhanh khi tìm giao điểm
COLLINEAR_SIN = 1e-6
CORE_TIMEOUT_S = 180
# [cần xác nhận] standards chưa quy định tên type sàn; BIM Manager chốt rồi sửa tại đây
FLOOR_TYPE_NAME = u"S-DUL {t}mm"


# =====================================================================================
# PHẦN HÌNH HỌC – chỉ dùng tuple (x, y) theo mm, không phụ thuộc Revit (chạy thử được ngoài Dynamo)
# =====================================================================================
def split_filters(text):
    return [f.strip().lower() for f in (text or u"").split(";") if f.strip()]


def matches(layer, filters):
    return bool(layer) and any(f in layer.lower() for f in filters)


def parse_spec(text):
    """'450/-50' → (450.0, -50.0); '230' → (230.0, 0.0)."""
    parts = [p.strip() for p in (text or u"").replace(",", ".").split("/")]
    t = float(parts[0])
    off = float(parts[1]) if len(parts) > 1 and parts[1] else 0.0
    if t <= 0:
        raise ValueError(text)
    return t, off


def combo_key(patterns):
    """Tên vùng hatch chồng: các mẫu xếp theo ABC nối bằng '+' (VD ANGLE+ANSI37)."""
    return u"+".join(sorted(set(p.strip().upper() for p in patterns if p.strip())))


def parse_legend(text):
    """'ANSI31=230;ANSI37=450/-50;ANSI37+ANGLE=170/-30' → {'ANSI31': (230, 0), 'ANSI37': (450, -50),
    'ANGLE+ANSI37': (170, -30)}. Khoá có '+' = vùng hai hatch chồng lên nhau."""
    out = {}
    for item in (text or u"").split(";"):
        if "=" not in item:
            continue
        k, v = item.split("=", 1)
        try:
            out[combo_key(k.split("+"))] = parse_spec(v)
        except ValueError:
            raise Exception(u"Ghi chú hatch sai định dạng ở '{}' (đúng: MẪU=dày[/cốt])".format(item.strip()))
    return out


def spec_text(spec):
    t, off = spec
    return u"dày {:g}{}".format(t, u", hạ cốt {:g}".format(-off) if off < 0 else
                                (u", nâng cốt {:g}".format(off) if off > 0 else u""))


def signed_area(pts):
    return sum(pts[i - 1][0] * pts[i][1] - pts[i][0] * pts[i - 1][1] for i in range(len(pts))) / 2.0


def point_in(pt, pts):
    x, y, res = pt[0], pt[1], False
    for i in range(len(pts)):
        x1, y1 = pts[i - 1]
        x2, y2 = pts[i]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            res = not res
    return res


def point_in_evenodd(pt, loops):
    return sum(1 for l in loops if point_in(pt, l)) % 2 == 1


class Snapper(object):
    """Gom điểm gần nhau (≤ tol) về một đỉnh."""

    def __init__(self, tol):
        self.tol, self.pts, self.grid = tol, [], {}

    def get(self, x, y):
        cx, cy = int(math.floor(x / self.tol)), int(math.floor(y / self.tol))
        for i in (cx - 1, cx, cx + 1):
            for j in (cy - 1, cy, cy + 1):
                for k in self.grid.get((i, j), ()):
                    px, py = self.pts[k]
                    if math.hypot(px - x, py - y) <= self.tol:
                        return k
        k = len(self.pts)
        self.pts.append((x, y))
        self.grid.setdefault((cx, cy), []).append(k)
        return k


def _cells(x0, y0, x1, y1, pad):
    for i in range(int(math.floor((min(x0, x1) - pad) / CELL_MM)), int(math.floor((max(x0, x1) + pad) / CELL_MM)) + 1):
        for j in range(int(math.floor((min(y0, y1) - pad) / CELL_MM)), int(math.floor((max(y0, y1) + pad) / CELL_MM)) + 1):
            yield i, j


def _near_params(ax0, ay0, ax1, ay1, pts, tol):
    """Tham số t trên đoạn A của các điểm nằm sát đoạn A (≤ tol)."""
    rx, ry = ax1 - ax0, ay1 - ay0
    l2 = rx * rx + ry * ry
    la = math.sqrt(l2)
    out = []
    for px, py in pts:
        t = ((px - ax0) * rx + (py - ay0) * ry) / l2
        if -tol / la <= t <= 1 + tol / la:
            qx, qy = ax0 + rx * t, ay0 + ry * t
            if math.hypot(px - qx, py - qy) <= tol:
                out.append(min(max(t, 0.0), 1.0))
    return out


def split_segments(segs, tol):
    """segs: [(x0, y0, x1, y1)]. Tách tại giao điểm, chỗ chạm chữ T và đoạn chồng thẳng hàng.

    Trả về (points, edges): points[i] = (x, y); edges = set((i, j)) với i < j.
    """
    segs = [s for s in segs if math.hypot(s[2] - s[0], s[3] - s[1]) > tol]
    params = [[0.0, 1.0] for _ in segs]
    grid = {}
    for k, s in enumerate(segs):
        for c in _cells(s[0], s[1], s[2], s[3], tol):
            grid.setdefault(c, []).append(k)
    done = set()
    for cell in grid.values():
        for ia in range(len(cell)):
            for ib in range(ia + 1, len(cell)):
                a, b = cell[ia], cell[ib]
                if (a, b) in done:
                    continue
                done.add((a, b))
                ax0, ay0, ax1, ay1 = segs[a]
                bx0, by0, bx1, by1 = segs[b]
                if (max(ax0, ax1) < min(bx0, bx1) - tol or max(bx0, bx1) < min(ax0, ax1) - tol or
                        max(ay0, ay1) < min(by0, by1) - tol or max(by0, by1) < min(ay0, ay1) - tol):
                    continue
                params[a] += _near_params(ax0, ay0, ax1, ay1, [(bx0, by0), (bx1, by1)], tol)
                params[b] += _near_params(bx0, by0, bx1, by1, [(ax0, ay0), (ax1, ay1)], tol)
                rx, ry, sx, sy = ax1 - ax0, ay1 - ay0, bx1 - bx0, by1 - by0
                la, lb = math.hypot(rx, ry), math.hypot(sx, sy)
                den = rx * sy - ry * sx
                if abs(den) <= COLLINEAR_SIN * la * lb:
                    continue
                t = ((bx0 - ax0) * sy - (by0 - ay0) * sx) / den
                u = ((bx0 - ax0) * ry - (by0 - ay0) * rx) / den
                if -tol / la <= t <= 1 + tol / la and -tol / lb <= u <= 1 + tol / lb:
                    params[a].append(min(max(t, 0.0), 1.0))
                    params[b].append(min(max(u, 0.0), 1.0))
    snap = Snapper(tol)
    edges = set()
    for (x0, y0, x1, y1), ts in zip(segs, params):
        ids = []
        for t in sorted(set(ts)):
            k = snap.get(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
            if not ids or ids[-1] != k:
                ids.append(k)
        for p, q in zip(ids[:-1], ids[1:]):
            edges.add((min(p, q), max(p, q)))
    return snap.pts, edges


def prune(edges):
    """Bỏ nét cụt (đỉnh bậc 1) lặp lại tới khi hết. Trả về (edges còn lại, đỉnh cụt ban đầu)."""
    adj = {}
    for p, q in edges:
        adj.setdefault(p, set()).add(q)
        adj.setdefault(q, set()).add(p)
    loose = [v for v, n in adj.items() if len(n) == 1]
    stack = list(loose)
    while stack:
        v = stack.pop()
        if v not in adj or len(adj[v]) != 1:
            continue
        w = adj.pop(v).pop()
        adj[w].discard(v)
        if not adj[w]:
            del adj[w]
        elif len(adj[w]) == 1:
            stack.append(w)
    kept = set((p, q) for p, q in edges if p in adj and q in adj.get(p, ()))
    return kept, loose


def faces_of(points, edges):
    """Dò các vòng theo nửa cạnh (mặt bên trái). Trả về (cycles, he_cycle, comp_of_vertex).

    cycles[i] = list nửa cạnh (u, v); diện tích > 0 → ô kín, < 0 → biên ngoài của một cụm nét.
    """
    out = {}
    for p, q in edges:
        out.setdefault(p, []).append(q)
        out.setdefault(q, []).append(p)
    ang = lambda v, w: math.atan2(points[w][1] - points[v][1], points[w][0] - points[v][0])
    order = {}
    for v, ns in out.items():
        ns.sort(key=lambda w: ang(v, w))
        order[v] = dict((w, i) for i, w in enumerate(ns))
    comp, cid = {}, 0
    for v in out:
        if v in comp:
            continue
        stack = [v]
        comp[v] = cid
        while stack:
            a = stack.pop()
            for b in out[a]:
                if b not in comp:
                    comp[b] = cid
                    stack.append(b)
        cid += 1
    he_cycle, cycles = {}, []
    for p, q in edges:
        for start in ((p, q), (q, p)):
            if start in he_cycle:
                continue
            cyc, h = [], start
            while h not in he_cycle:
                he_cycle[h] = len(cycles)
                cyc.append(h)
                u, v = h
                ns = out[v]
                w = ns[(order[v][u] - 1) % len(ns)]
                h = (v, w)
            cycles.append(cyc)
    return cycles, he_cycle, comp


def merge_collinear(pts):
    """Bỏ đỉnh nằm giữa hai cạnh thẳng hàng cùng chiều."""
    pts = list(pts)
    changed = True
    while changed and len(pts) > 3:
        changed = False
        for i in range(len(pts)):
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % len(pts)]
            ux, uy, vx, vy = b[0] - a[0], b[1] - a[1], c[0] - b[0], c[1] - b[1]
            lu, lv = math.hypot(ux, uy), math.hypot(vx, vy)
            if lu < 1e-9 or lv < 1e-9 or (abs(ux * vy - uy * vx) <= 1e-4 * lu * lv and ux * vx + uy * vy > 0):
                del pts[i]
                changed = True
                break
    return pts


X_FILL = 2.0           # Ô lỗ mở được lớn tối đa X_FILL × khung bao dấu X (dấu X vẽ góc–góc ô)


def x_centers(marks, tol):
    """Dấu X: hai nét chéo cắt nhau gần trung điểm của cả hai. Trả về [(tâm, diện tích khung bao dấu X mm²)]."""
    centers = []
    for i in range(len(marks)):
        ax0, ay0, ax1, ay1 = marks[i]
        for j in range(i + 1, len(marks)):
            bx0, by0, bx1, by1 = marks[j]
            ma = ((ax0 + ax1) / 2.0, (ay0 + ay1) / 2.0)
            mb = ((bx0 + bx1) / 2.0, (by0 + by1) / 2.0)
            if math.hypot(ma[0] - mb[0], ma[1] - mb[1]) > tol * 4:
                continue
            rx, ry, sx, sy = ax1 - ax0, ay1 - ay0, bx1 - bx0, by1 - by0
            if abs(rx * sy - ry * sx) <= 0.1 * math.hypot(rx, ry) * math.hypot(sx, sy):
                continue
            xs, ys = (ax0, ax1, bx0, bx1), (ay0, ay1, by0, by1)
            centers.append((ma, (max(xs) - min(xs)) * (max(ys) - min(ys))))
    return centers


def chain(points, hes):
    """Nối các nửa cạnh biên thành vòng kín (danh sách id đỉnh). Đỉnh có nhiều lựa chọn → rẽ phải gấp nhất."""
    starts = {}
    for h in hes:
        starts.setdefault(h[0], []).append(h)
    used, loops = set(), []
    for h0 in hes:
        if h0 in used:
            continue
        loop, h = [], h0
        while h not in used:
            used.add(h)
            loop.append(h[0])
            u, v = h
            cands = [c for c in starts.get(v, ()) if c not in used]
            if not cands:
                break
            back = math.atan2(points[u][1] - points[v][1], points[u][0] - points[v][0])

            def turn(c):
                a = math.atan2(points[c[1]][1] - points[v][1], points[c[1]][0] - points[v][0])
                d = (back - a) % (2 * math.pi)
                return d if d > 1e-12 else 2 * math.pi
            h = min(cands, key=turn)
        loops.append(loop)
    return loops


class Arrangement(object):
    """Mặt phẳng chia bởi các nét: ô kín, cụm nét, đảo (cụm nằm lọt trong ô của cụm khác)."""

    def __init__(self, segs, tol):
        self.points, edges = split_segments(segs, tol)
        self.kept, self.loose = prune(edges)
        self.cycles, self.he_cycle, self.comp = faces_of(self.points, self.kept)
        self.poly = [[self.points[u] for u, _ in c] for c in self.cycles]
        self.area = [signed_area(p) for p in self.poly]
        self.bounded = [i for i in range(len(self.cycles)) if self.area[i] > 1e-6]
        self.owner = dict((i, i) for i in self.bounded)
        self.islands = dict((i, []) for i in self.bounded)
        for i in range(len(self.cycles)):
            if self.area[i] > 1e-6:
                continue
            c = self.comp[self.cycles[i][0][0]]
            best = None
            for f in self.bounded:
                if self.comp[self.cycles[f][0][0]] != c and point_in(self.poly[i][0], self.poly[f]) and \
                        (best is None or self.area[f] < self.area[best]):
                    best = f
            self.owner[i] = best     # None = mặt ngoài cùng
            if best is not None:
                self.islands[best].append(i)

    def face_of(self, h):
        return self.owner.get(self.he_cycle[h])

    def comp_of(self, i):
        return self.comp[self.cycles[i][0][0]]

    def inside_face(self, pt, f):
        return point_in(pt, self.poly[f]) and not any(point_in(pt, self.poly[h]) for h in self.islands[f])

    def rep_point(self, f):
        pts = self.poly[f]
        k = max(range(len(pts)), key=lambda i: math.hypot(pts[(i + 1) % len(pts)][0] - pts[i][0],
                                                          pts[(i + 1) % len(pts)][1] - pts[i][1]))
        a, b = pts[k], pts[(k + 1) % len(pts)]
        l = math.hypot(b[0] - a[0], b[1] - a[1])
        return ((a[0] + b[0]) / 2.0 - (b[1] - a[1]) / l * INNER_MM, (a[1] + b[1]) / 2.0 + (b[0] - a[0]) / l * INNER_MM)

    def boundary(self, fs, with_islands):
        """Vòng biên của hợp các ô fs → (vòng ngoài CCW, vòng lỗ CW, nửa cạnh biên), toạ độ đã gộp thẳng hàng."""
        fset = set(fs)
        cyc = [i for f in fs for i in ([f] + self.islands[f] if with_islands else [f])]
        bnd = [h for i in cyc for h in self.cycles[i] if self.face_of((h[1], h[0])) not in fset]
        loops = [merge_collinear([self.points[v] for v in l]) for l in chain(self.points, bnd)]
        loops = [l for l in loops if len(l) >= 3 and abs(signed_area(l)) > 1e-6]
        return [l for l in loops if signed_area(l) > 0], [l for l in loops if signed_area(l) < 0], bnd


def find_outlines(edge_segs, marks, opt):
    """edge_segs: [(x0, y0, x1, y1)] mm trên layer mép sàn; marks: [(x0, y0, x1, y1)] nét dấu lỗ mở.

    Trả về (blocks, info):
      blocks = [{"outer": [(x, y)], "area": m², "openings": [{"loop": [(x, y)], "area": m², "n": số ô, "edge": bool}]}]
               (edge = lỗ mở chạm bao ngoài – Revit không tạo được lỗ chạm mép sàn)
      info   = {"loose": [(x, y)], "small": [(area, (x, y), lý do)], "stray": [(x, y)] dấu X ngoài ô kín / ngoài bao,
                "xmarks": số dấu X}
    """
    tol = opt["snap"]
    A = Arrangement(edge_segs, tol)

    # --- Bao ngoài: mỗi cụm nét nằm ở mặt ngoài cùng → hợp mọi ô kín của cụm
    blocks, small = [], []
    for i in range(len(A.cycles)):
        if A.area[i] > 1e-6 or A.owner[i] is not None:
            continue
        c = A.comp_of(i)
        fs = [f for f in A.bounded if A.comp_of(f) == c]
        if not fs:
            continue
        outers, _, _ = A.boundary(fs, False)
        if len(outers) != 1:
            small.append((0.0, A.poly[i][0], u"bao ngoài không đơn ({} vòng) – kiểm tra lại nét".format(len(outers))))
            continue
        a = signed_area(outers[0]) / 1e6
        if a < opt["min_area"]:
            small.append((a, outers[0][0], u"vòng kín {:.2f} m² < {:.2f} m²".format(a, opt["min_area"])))
            continue
        blocks.append({"outer": outers[0], "area": a, "openings": []})

    # --- Lỗ mở: ô kín nhỏ nhất chứa tâm dấu X; ô lỗ mở chung cạnh gộp làm một
    centers = x_centers(marks, tol)
    holes, stray, loose_x = set(), [], []
    for pt, xarea in centers:
        cands = [f for f in A.bounded if A.inside_face(pt, f)]
        if not cands:
            stray.append(pt)
            continue
        f = min(cands, key=lambda f: A.area[f])
        if A.area[f] > X_FILL * xarea + 1e4:
            loose_x.append((pt, A.area[f] / 1e6))   # ô quanh dấu X chưa kín → không khoét cả ô lớn
            continue
        holes.add(f)
    parent = dict((f, f) for f in holes)

    def root(f):
        while parent[f] != f:
            parent[f] = parent[parent[f]]
            f = parent[f]
        return f
    for f in holes:
        for u, v in A.cycles[f]:
            g = A.face_of((v, u))
            if g in holes:
                parent[root(g)] = root(f)
    groups = {}
    for f in holes:
        groups.setdefault(root(f), []).append(f)

    for fs in groups.values():
        loops, _, bnd = A.boundary(fs, False)
        touch = any(A.face_of((h[1], h[0])) is None for h in bnd)
        for loop in loops:
            blk = block_of(loop[0], blocks, tol)
            if blk is None:
                stray.append(loop[0])
                continue
            blk["openings"].append({"loop": loop, "area": signed_area(loop) / 1e6, "n": len(fs), "edge": touch})

    blocks.sort(key=lambda b: (-max(p[1] for p in b["outer"]), min(p[0] for p in b["outer"])))
    for b in blocks:
        b["openings"].sort(key=lambda o: (-max(p[1] for p in o["loop"]), min(p[0] for p in o["loop"])))
    info = {"loose": [A.points[v] for v in A.loose], "small": small, "stray": stray, "xmarks": len(centers),
            "loose_x": loose_x}
    return blocks, info


def block_of(pt, blocks, tol):
    best = None
    for b in blocks:
        if point_in(pt, b["outer"]) or any(math.hypot(pt[0] - q[0], pt[1] - q[1]) <= tol for q in b["outer"]):
            if best is None or b["area"] < best["area"]:
                best = b
    return best


def snap_points(pts, segs, tol):
    """Hút đỉnh về đầu nét gần nhất (≤ tol), không có thì về điểm chiếu lên nét gần nhất (≤ tol)."""
    grid = {}
    for k, s in enumerate(segs):
        for c in _cells(s[0], s[1], s[2], s[3], tol):
            grid.setdefault(c, []).append(k)
    out = []
    for x, y in pts:
        cand = set(grid.get((int(math.floor(x / CELL_MM)), int(math.floor(y / CELL_MM))), ()))
        best, bd = None, tol
        for k in cand:
            for px, py in ((segs[k][0], segs[k][1]), (segs[k][2], segs[k][3])):
                d = math.hypot(px - x, py - y)
                if d <= bd:
                    best, bd = (px, py), d
        if best is None:
            for k in cand:
                x0, y0, x1, y1 = segs[k]
                rx, ry = x1 - x0, y1 - y0
                l2 = rx * rx + ry * ry
                if l2 < 1e-9:
                    continue
                t = ((x - x0) * rx + (y - y0) * ry) / l2
                if 0.0 <= t <= 1.0:
                    qx, qy = x0 + rx * t, y0 + ry * t
                    d = math.hypot(qx - x, qy - y)
                    if d <= bd:
                        best, bd = (qx, qy), d
        p = best or (x, y)
        if not out or math.hypot(out[-1][0] - p[0], out[-1][1] - p[1]) > 1e-6:
            out.append(p)
    if len(out) > 1 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= 1e-6:
        out.pop()
    return out


def find_regions(edge_segs, marks, zones, base_spec, opt, legend=None):
    """Chia mặt bằng thành vùng sàn.

    zones: [{"pattern": str, "spec": (dày, cốt) | None, "loops": [[(x, y)]]}] – hatch có trong ghi chú (toạ độ mô
           hình, mm); spec None = mẫu chỉ dùng trong ghi chú hatch chồng (khoá 'A+B' của legend).
    Ô nằm trong nhiều hatch: tra legend theo khoá 'A+B'; không có khoá thì lấy hatch vẽ sau (đếm conflict).
    Trả về (blocks, regions, info) với regions = [{"block": i, "pattern": str | None, "spec": (dày, cốt),
             "outer": [(x, y)], "holes": [[(x, y)]], "area": m²}] (pattern None = sàn nền).
    """
    tol = opt["snap"]
    blocks, info = find_outlines(edge_segs, marks, opt)
    zsegs, zloops = [], []
    for z in zones:
        loops = []
        for l in z["loops"]:
            s = snap_points(l, edge_segs, opt["hatch_snap"])
            if len(s) >= 3 and abs(signed_area(s)) > 1e-6:
                loops.append(s)
                zsegs += [(p[0], p[1], q[0], q[1]) for p, q in zip(s, s[1:] + s[:1])]
        zloops.append(loops)
    A = Arrangement(edge_segs + zsegs, tol)

    key = {}
    conflict = 0
    for f in A.bounded:
        rp = A.rep_point(f)
        blk = None
        for bi, b in enumerate(blocks):
            if point_in(rp, b["outer"]):
                blk = bi
                break
        if blk is None:
            continue
        if any(point_in(rp, o["loop"]) for o in blocks[blk]["openings"]):
            key[f] = (blk, "lo", None)
            continue
        hit = [zi for zi, loops in enumerate(zloops) if loops and point_in_evenodd(rp, loops)]
        pats = combo_key(zones[zi]["pattern"] for zi in hit)
        if u"+" in pats and legend and pats in legend:
            key[f] = (blk, "vung", (pats, legend[pats]))
            continue
        hit = [zi for zi in hit if zones[zi]["spec"] is not None]
        if hit:
            conflict += 1 if u"+" in pats else 0
            z = zones[hit[-1]]
            key[f] = (blk, "vung", (z["pattern"], z["spec"]))
        else:
            conflict += 1 if pats else 0
            key[f] = (blk, "nen", None)

    # Ô vụn (khe giữa biên hatch và nét) → theo ô bên cạnh có cạnh chung dài nhất
    slivers = 0
    for f in sorted(key, key=lambda f: A.area[f]):
        if A.area[f] / 1e6 >= SLIVER_M2 or key[f][1] == "lo":
            continue
        shared = {}
        for i in [f] + A.islands[f]:
            for u, v in A.cycles[i]:
                g = A.face_of((v, u))
                if g in key and g != f and key[g][0] == key[f][0]:
                    shared[key[g]] = shared.get(key[g], 0.0) + math.hypot(
                        A.points[v][0] - A.points[u][0], A.points[v][1] - A.points[u][1])
        shared.pop((key[f][0], "lo", None), None)
        if shared:
            best = max(shared, key=shared.get)
            if best != key[f]:
                key[f] = best
                slivers += 1

    # Gom ô liền kề cùng loại thành vùng
    parent = dict((f, f) for f in key)

    def root(f):
        while parent[f] != f:
            parent[f] = parent[parent[f]]
            f = parent[f]
        return f
    for f in key:
        for i in [f] + A.islands[f]:
            for u, v in A.cycles[i]:
                g = A.face_of((v, u))
                if g in key and key[g] == key[f]:
                    parent[root(g)] = root(f)
    groups = {}
    for f in key:
        if key[f][1] != "lo":
            groups.setdefault(root(f), []).append(f)

    regions, bad = [], []
    for fs in groups.values():
        blk, kind, zs = key[fs[0]]
        outers, holes, _ = A.boundary(fs, True)
        if len(outers) != 1:
            bad.append((A.rep_point(fs[0]), u"vùng {} không đơn ({} vòng ngoài)".format(
                zs[0] if zs else u"sàn nền", len(outers))))
            continue
        a = (signed_area(outers[0]) + sum(signed_area(h) for h in holes)) / 1e6
        regions.append({"block": blk, "pattern": zs[0] if zs else None, "spec": zs[1] if zs else base_spec,
                        "outer": outers[0], "holes": holes, "area": a})
    regions.sort(key=lambda r: (r["block"], r["pattern"] is not None, r["pattern"] or u"",
                                -max(p[1] for p in r["outer"]), min(p[0] for p in r["outer"])))
    info.update({"slivers": slivers, "conflict": conflict, "bad": bad,
                 "zone_loops": sum(len(l) for l in zloops)})
    return blocks, regions, info


class LineSet(object):
    """Gom các đoạn cần vẽ, bỏ phần chồng thẳng hàng với đoạn đã có → mỗi nét chỉ vẽ một lần."""

    def __init__(self, tol):
        self.tol, self.rows, self.out = tol, {}, []

    def add(self, a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        l = math.hypot(dx, dy)
        if l <= self.tol:
            return 0
        ux, uy = dx / l, dy / l
        if ux < -1e-9 or (abs(ux) <= 1e-9 and uy < 0):
            ux, uy = -ux, -uy
        off = -uy * a[0] + ux * a[1]
        k = (int(round(math.degrees(math.atan2(uy, ux)) * 100)), int(round(off / self.tol)))
        ta, tb = sorted((ux * a[0] + uy * a[1], ux * b[0] + uy * b[1]))
        have = self.rows.setdefault(k, [])
        pieces = [(ta, tb)]
        for h0, h1 in have:
            nxt = []
            for p0, p1 in pieces:
                if h1 <= p0 + self.tol or h0 >= p1 - self.tol:
                    nxt.append((p0, p1))
                    continue
                if h0 > p0 + self.tol:
                    nxt.append((p0, h0))
                if h1 < p1 - self.tol:
                    nxt.append((h1, p1))
            pieces = nxt
        n = 0
        for p0, p1 in pieces:
            have.append((p0, p1))
            self.out.append(((ux * p0 - uy * off, uy * p0 + ux * off), (ux * p1 - uy * off, uy * p1 + ux * off)))
            n += 1
        return n

    def add_loop(self, loop):
        return sum(self.add(a, b) for a, b in zip(loop, loop[1:] + loop[:1]))


# --- Hatch trong DWG -----------------------------------------------------------------
def _xy(v):
    parts = v.split(",")
    return float(parts[0]), float(parts[1])


def _arc(c, r, s, e, ccw):
    """Cung tròn biên hatch (độ) → các điểm. Cung thuận chiều kim đồng hồ: góc lưu dạng đảo (360 - góc)."""
    if ccw:
        while e <= s:
            e += 360.0
    else:
        s, e = 360.0 - s, 360.0 - e
        while e >= s:
            e -= 360.0
    n = max(2, int(math.ceil(abs(e - s) / ARC_STEP_DEG)))
    return [(c[0] + r * math.cos(math.radians(s + (e - s) * i / n)), c[1] + r * math.sin(math.radians(s + (e - s) * i / n)))
            for i in range(n + 1)]


def _bulge(p, q, b):
    """Đoạn polyline có bulge → các điểm từ p tới q (không gồm q)."""
    if abs(b) < 1e-9:
        return [p]
    sweep = 4.0 * math.atan(b)
    d = math.hypot(q[0] - p[0], q[1] - p[1])
    r = d / (2.0 * math.sin(abs(sweep) / 2.0))
    mx, my = (p[0] + q[0]) / 2.0, (p[1] + q[1]) / 2.0
    h = math.sqrt(max(r * r - d * d / 4.0, 0.0)) * (1 if abs(sweep) <= math.pi else -1)
    nx, ny = -(q[1] - p[1]) / d, (q[0] - p[0]) / d
    s = 1 if b > 0 else -1
    cx, cy = mx + s * nx * h, my + s * ny * h
    a0 = math.atan2(p[1] - cy, p[0] - cx)
    n = max(2, int(math.ceil(math.degrees(abs(sweep)) / ARC_STEP_DEG)))
    return [(cx + r * math.cos(a0 + sweep * i / n), cy + r * math.sin(a0 + sweep * i / n)) for i in range(n)]


def parse_hatch(codes):
    """codes: [(mã, chuỗi)] của HATCH. Trả về (pattern, [vòng [(x, y)]] theo OCS)."""
    pattern, mirror, i = None, False, 0
    while i < len(codes) and codes[i][0] != 91:
        k, v = codes[i]
        if k == 2 and pattern is None:
            pattern = v
        if k == 210:
            parts = v.split(",")
            mirror = len(parts) > 2 and float(parts[2]) < 0
        i += 1
    if i >= len(codes):
        raise ValueError(u"không có biên")
    npath = int(codes[i][1])
    i += 1
    loops = []
    for _ in range(npath):
        flag = int(codes[i][1])
        i += 1
        pts = []
        if flag & 2:
            hasb = int(codes[i][1])
            n = int(codes[i + 2][1])
            i += 3
            verts = []
            for _ in range(n):
                p = _xy(codes[i][1])
                i += 1
                b = 0.0
                if hasb and i < len(codes) and codes[i][0] == 42:
                    b = float(codes[i][1])
                    i += 1
                verts.append((p, b))
            for k in range(len(verts)):
                pts += _bulge(verts[k][0], verts[(k + 1) % len(verts)][0], verts[k][1])
        else:
            n = int(codes[i][1])
            i += 1
            for _ in range(n):
                t = int(codes[i][1])
                i += 1
                if t == 1:
                    pts.append(_xy(codes[i][1]))
                    i += 2
                elif t == 2:
                    c, r = _xy(codes[i][1]), float(codes[i + 1][1])
                    s, e, ccw = float(codes[i + 2][1]), float(codes[i + 3][1]), int(codes[i + 4][1])
                    pts += _arc(c, r, s, e, ccw)[:-1]
                    i += 5
                else:
                    raise ValueError(u"biên hatch có cạnh {} (ellipse/spline) chưa hỗ trợ".format(
                        u"ellipse" if t == 3 else u"spline"))
        while i < len(codes) and codes[i][0] == 97:
            i += 1
        if mirror:
            pts = [(-x, y) for x, y in pts]
        if len(pts) >= 3:
            loops.append(pts)
    return pattern, loops


# Đọc HATCH ở model space VÀ trong block (lồng nhau, tối đa 8 cấp), kèm ma trận affine (a b c d e f) của
# INSERT cha (x' = a x + b y + e; y' = c x + d y + f). Hatch nằm trên layer "0" trong block lấy layer INSERT cha.
DUMP_LISP = u"""(setq f (open "{out}" "w" "utf8"))
(defun _ap (m p) (list (+ (* (nth 0 m) (car p)) (* (nth 1 m) (cadr p)) (nth 4 m))
                       (+ (* (nth 2 m) (car p)) (* (nth 3 m) (cadr p)) (nth 5 m))))
(defun _mul (p c) (list (+ (* (nth 0 p) (nth 0 c)) (* (nth 1 p) (nth 2 c)))
                        (+ (* (nth 0 p) (nth 1 c)) (* (nth 1 p) (nth 3 c)))
                        (+ (* (nth 2 p) (nth 0 c)) (* (nth 3 p) (nth 2 c)))
                        (+ (* (nth 2 p) (nth 1 c)) (* (nth 3 p) (nth 3 c)))
                        (+ (* (nth 0 p) (nth 4 c)) (* (nth 1 p) (nth 5 c)) (nth 4 p))
                        (+ (* (nth 2 p) (nth 4 c)) (* (nth 3 p) (nth 5 c)) (nth 5 p))))
(defun _ins (d / a sx sy ip bp ca sa m)
  (setq a (cdr (assoc 50 d)) sx (cdr (assoc 41 d)) sy (cdr (assoc 42 d)) ip (cdr (assoc 10 d))
        bp (cdr (assoc 10 (tblsearch "BLOCK" (cdr (assoc 2 d))))) ca (cos a) sa (sin a))
  (setq m (list (* ca sx) (- (* sa sy)) (* sa sx) (* ca sy) 0.0 0.0) bp (_ap m bp))
  (list (nth 0 m) (nth 1 m) (nth 2 m) (nth 3 m) (- (car ip) (car bp)) (- (cadr ip) (cadr bp))))
(defun _lay (d parent / l) (setq l (cdr (assoc 8 d))) (if (and parent (= l "0")) parent l))
(defun _v (x) (cond ((= (type x) 'REAL) (rtos x 2 6)) ((= (type x) 'INT) (itoa x)) ((= (type x) 'STR) x)
                    ((and (= (type x) 'LIST) (numberp (car x)))
                      (strcat (rtos (car x) 2 6) "," (rtos (cadr x) 2 6) (if (caddr x) (strcat "," (rtos (caddr x) 2 6)) "")))
                    (T "?")))
(defun _h (d m lay / s)
  (setq s (strcat "H|" lay "|" (rtos (nth 0 m) 2 9) "," (rtos (nth 1 m) 2 9) "," (rtos (nth 2 m) 2 9) ","
                  (rtos (nth 3 m) 2 9) "," (rtos (nth 4 m) 2 6) "," (rtos (nth 5 m) 2 6) "|"))
  (foreach g d (if (member (car g) '(2 91 92 93 72 73 10 11 40 42 50 51 97 210))
                 (setq s (strcat s (itoa (car g)) "=" (_v (cdr g)) ";"))))
  (write-line s f))
(defun _walk (name m parent depth / e d)
  (setq e (cdr (assoc -2 (tblsearch "BLOCK" name))))
  (while e
    (setq d (entget e))
    (cond ((= (cdr (assoc 0 d)) "HATCH") (_h d m (_lay d parent)))
          ((and (= (cdr (assoc 0 d)) "INSERT") (< depth 8))
            (_walk (cdr (assoc 2 d)) (_mul m (_ins d)) (_lay d parent) (1+ depth))))
    (setq e (entnext e))))
(if (setq ss (ssget "_X" '((0 . "HATCH,INSERT") (410 . "Model"))))
  (progn (setq i 0)
    (repeat (sslength ss)
      (setq d (entget (ssname ss i)) i (1+ i))
      (if (= (cdr (assoc 0 d)) "INSERT")
        (_walk (cdr (assoc 2 d)) (_ins d) (cdr (assoc 8 d)) 1)
        (_h d '(1.0 0.0 0.0 1.0 0.0 0.0) (cdr (assoc 8 d)))))))
(close f)
"""


def find_accoreconsole():
    found = glob.glob(r"C:\Program Files\Autodesk\AutoCAD *\accoreconsole.exe")
    return sorted(found)[-1] if found else None


def core_env(core):
    """Môi trường sạch cho AutoCAD Core Console. Gọi từ Revit, tiến trình con kế thừa Path có thư mục Revit 2026
    → Core Console nạp nhầm DLL của Revit, báo "Unable to load the Modeler DLLs" và thoát, không xuất file
    (đã kiểm 2026-10-19). Chỉ giữ biến hệ thống, Path = thư mục AutoCAD + Windows."""
    keep = ("SYSTEMROOT", "WINDIR", "SYSTEMDRIVE", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "USERNAME",
            "USERDOMAIN", "PROGRAMDATA", "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432", "COMMONPROGRAMFILES",
            "COMMONPROGRAMFILES(X86)", "COMMONPROGRAMW6432", "ALLUSERSPROFILE", "COMPUTERNAME", "HOMEDRIVE",
            "HOMEPATH", "OS", "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE", "PUBLIC", "COMSPEC", "PATHEXT")
    env = dict((k, v) for k, v in os.environ.items() if k.upper() in keep)
    root = env.get("SYSTEMROOT") or os.environ.get("SystemRoot") or r"C:\Windows"
    temp = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "Temp")
    env["TEMP"] = env["TMP"] = temp if os.path.isdir(temp) else tempfile.gettempdir()
    env["PATH"] = u";".join([os.path.dirname(core), os.path.join(root, "System32"), root,
                             os.path.join(root, "System32", "Wbem")])
    return env


def read_dwg_hatches(dwg_path, core):
    """[(layer, pattern, [vòng [(x, y)]] toạ độ DWG)], [(layer, lỗi)]. Chạy trên bản sao trong thư mục tạm."""
    work = tempfile.mkdtemp(prefix="ARV_BaoSan_")
    try:
        copy = os.path.join(work, "copy.dwg")
        shutil.copy2(dwg_path, copy)
        out = os.path.join(work, "hatch.txt")
        scr = os.path.join(work, "dump.scr")
        with io.open(scr, "w", encoding="utf-8") as f:
            f.write(DUMP_LISP.replace("{out}", out.replace("\\", "/")))
        subprocess.run([core, "/i", copy, "/s", scr, "/l", "en-US"], stdin=subprocess.DEVNULL,
                       env=core_env(core), cwd=os.path.dirname(core),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=CORE_TIMEOUT_S, creationflags=0x08000000)
        if not os.path.isfile(out):
            raise Exception(u"Core Console không xuất được danh sách hatch")
        hatches, errors = [], []
        with io.open(out, "r", encoding="utf-8-sig", errors="replace") as f:
            for line in f.read().splitlines():
                parts = line.split("|", 3)
                if len(parts) < 4 or parts[0] != "H":
                    continue
                layer = parts[1]
                try:
                    a, b, c, d, e, g = [float(v) for v in parts[2].split(",")]
                    codes = []
                    for kv in parts[3].split(";"):
                        if "=" in kv:
                            k, v = kv.split("=", 1)
                            codes.append((int(k), v))
                    pattern, loops = parse_hatch(codes)
                except Exception as ex:
                    errors.append((layer, u"{}".format(ex)))
                    continue
                loops = [[(a * x + b * y + e, c * x + d * y + g) for x, y in l] for l in loops]
                hatches.append((layer, (pattern or u"").upper(), loops))
        return hatches, errors
    finally:
        shutil.rmtree(work, ignore_errors=True)


# =====================================================================================
# PHẦN REVIT
# =====================================================================================
def to_mm(feet):
    return UnitUtils.ConvertFromInternalUnits(feet, UnitTypeId.Millimeters)


def from_mm(mm):
    return UnitUtils.ConvertToInternalUnits(mm, UnitTypeId.Millimeters)


def fmt(p):
    return u"({:.0f}, {:.0f})".format(p[0], p[1])


def get_name(element):
    try:
        return element.Name
    except Exception:
        p = element.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
        return p.AsString() if p else u""


def type_name(t):
    p = t.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
    return p.AsString() if p else get_name(t)


def is_central_file(document):
    if not document.IsWorkshared:
        return False
    try:
        central = ModelPathUtils.ConvertModelPathToUserVisiblePath(document.GetWorksharingCentralModelPath())
    except Exception:
        return False
    return os.path.normcase(central or "") == os.path.normcase(document.PathName or "")


def pick_cad(cad_filter):
    all_cad = list(FilteredElementCollector(doc).OfClass(ImportInstance).ToElements())
    instances = all_cad
    if cad_filter:
        instances = [i for i in all_cad if cad_filter.lower() in get_name(doc.GetElement(i.GetTypeId())).lower()]
    if len(instances) != 1:
        names = [get_name(doc.GetElement(i.GetTypeId())) for i in all_cad]
        raise Exception(u"Tìm thấy {} bản CAD khớp '{}'. Nhập tên bản CAD vào ô IN[0]. Các bản CAD: {}".format(
            len(instances), cad_filter, u", ".join(names) or u"không có"))
    return instances[0]


def cad_file_path(inst):
    link = doc.GetElement(inst.GetTypeId())
    if not inst.IsLinked or not isinstance(link, CADLinkType):
        return None
    try:
        path = ModelPathUtils.ConvertModelPathToUserVisiblePath(link.GetExternalFileReference().GetAbsolutePath())
    except Exception:
        return None
    return path if path and os.path.isfile(path) else None


def layer_of(geo_obj):
    style = doc.GetElement(geo_obj.GraphicsStyleId)
    if style is not None and style.GraphicsStyleCategory is not None:
        return style.GraphicsStyleCategory.Name
    return None


def cad_items(cad):
    """[(layer, [(x, y)], là cung)] của CAD (kể cả trong block lồng nhau), toạ độ mô hình (mm)."""
    opt = Options()
    if cad.ViewSpecific:
        opt.View = doc.GetElement(cad.OwnerViewId)
    items, other = [], {}

    def pts_of(coords):
        return [(to_mm(p.X), to_mm(p.Y)) for p in coords]

    def walk(geo):
        for obj in geo:
            if isinstance(obj, GeometryInstance):
                walk(obj.GetInstanceGeometry())
            elif isinstance(obj, PolyLine):
                items.append((layer_of(obj), pts_of(obj.GetCoordinates()), False))
            elif isinstance(obj, Line):
                items.append((layer_of(obj), pts_of([obj.GetEndPoint(0), obj.GetEndPoint(1)]), False))
            elif isinstance(obj, Arc):
                items.append((layer_of(obj), pts_of(obj.Tessellate()), True))
            else:
                n = obj.GetType().Name
                other[n] = other.get(n, 0) + 1

    geo = cad.get_Geometry(opt)
    if geo is not None:
        walk(geo)
    return items, other


def find_line_style(name):
    if not name:
        return None
    cat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Lines)
    subs = list(cat.SubCategories)
    for c in subs:
        if c.Name == name:
            return c.GetGraphicsStyle(GraphicsStyleType.Projection)
    raise Exception(u"Không có line style '{}' trong dự án (không tự tạo). Các line style: {}".format(
        name, u", ".join(sorted(c.Name for c in subs))))


def existing_lines(view):
    out = []
    for e in FilteredElementCollector(doc, view.Id).OfClass(CurveElement).ToElements():
        if e.CurveElementType != CurveElementType.DetailCurve:
            continue
        c = e.GeometryCurve
        if isinstance(c, Line):
            p, q = c.GetEndPoint(0), c.GetEndPoint(1)
            out.append(((to_mm(p.X), to_mm(p.Y)), (to_mm(q.X), to_mm(q.Y))))
    return out


def is_dup(a, b, lines):
    def same(p, q):
        return math.hypot(p[0] - q[0], p[1] - q[1]) <= DUP_TOL_MM
    return any((same(a, p) and same(b, q)) or (same(a, q) and same(b, p)) for p, q in lines)


# --- Type sàn --------------------------------------------------------------------------
def floor_width_mm(ft):
    cs = ft.GetCompoundStructure()
    return round(to_mm(cs.GetWidth()), 1) if cs is not None else None


class FloorTypes(object):
    """Tìm / tạo type sàn theo chiều dày. Ưu tiên tên FLOOR_TYPE_NAME, sau đó type thường bất kỳ đúng chiều dày."""

    def __init__(self, template_name):
        self.types = [t for t in FilteredElementCollector(doc).OfClass(FloorType).ToElements() if not t.IsFoundationSlab]
        self.template_name = template_name
        self.cache = {}

    def template(self):
        for t in self.types:
            if type_name(t) == self.template_name:
                return t
        raise Exception(u"Không có type sàn mẫu '{}'. Các type sàn: {}".format(
            self.template_name, u", ".join(sorted(type_name(t) for t in self.types))))

    def plan(self, t_mm):
        """(type có sẵn hoặc None, tên type)."""
        name = FLOOR_TYPE_NAME.format(t=int(round(t_mm)))
        for t in self.types:
            if type_name(t) == name:
                if floor_width_mm(t) != round(t_mm, 1):
                    raise Exception(u"Type '{}' đã có nhưng dày {} mm (cần {:g} mm) – sửa type hoặc đổi tên.".format(
                        name, floor_width_mm(t), t_mm))
                return t, name
        same = [t for t in self.types if floor_width_mm(t) == round(t_mm, 1)]
        if same:
            return sorted(same, key=type_name)[0], type_name(sorted(same, key=type_name)[0])
        return None, name

    def get(self, t_mm):
        """Type đúng chiều dày; chưa có thì nhân bản type mẫu (phải đang trong Transaction)."""
        if t_mm in self.cache:
            return self.cache[t_mm]
        ft, name = self.plan(t_mm)
        if ft is None:
            src = self.template()
            ft = doc.GetElement(src.Duplicate(name).Id)
            cs = ft.GetCompoundStructure()
            idx = cs.StructuralMaterialIndex
            if idx < 0:
                idx = max(range(cs.LayerCount), key=lambda i: cs.GetLayerWidth(i))
            rest = to_mm(cs.GetWidth()) - to_mm(cs.GetLayerWidth(idx))
            if t_mm - rest <= 0:
                raise Exception(u"Type mẫu '{}' có các lớp khác dày {:g} mm ≥ {:g} mm – chọn type mẫu khác.".format(
                    self.template_name, rest, t_mm))
            cs.SetLayerWidth(idx, from_mm(t_mm - rest))
            ft.SetCompoundStructure(cs)
            self.types.append(ft)
        self.cache[t_mm] = ft
        return ft


def existing_floors(level):
    out = []
    for f in FilteredElementCollector(doc).OfClass(Floor).ToElements():
        if f.LevelId != level.Id:
            continue
        p = f.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
        bb = f.get_BoundingBox(None)
        out.append((f, p.AsDouble() * 0.09290304 if p else 0.0,
                    ((to_mm(bb.Min.X) + to_mm(bb.Max.X)) / 2.0, (to_mm(bb.Min.Y) + to_mm(bb.Max.Y)) / 2.0) if bb else None))
    return out


def curve_loop(pts, z):
    cl = CurveLoop()
    for a, b in zip(pts, pts[1:] + pts[:1]):
        cl.Append(Line.CreateBound(XYZ(from_mm(a[0]), from_mm(a[1]), z), XYZ(from_mm(b[0]), from_mm(b[1]), z)))
    return cl


LOG_HEADER = [u"Đối tượng", u"Loại / Ghi chú", u"Diện tích (m²)", u"Số nét / lỗ", u"Type", u"Kết quả", u"ElementId",
              u"Điểm mốc (mm)"]


def write_log(rows, source, dry_run):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "VeBaoSanTuCAD_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(u"# Dự án: {}\n".format(doc.Title))
        f.write(u"# Bản CAD: {}\n".format(source))
        f.write(u"# Ngày xuất: {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write(u"# Chế độ: {}\n".format(u"Chạy thử (dry-run)" if dry_run else u"Thực hiện"))
        f.write(u"# Đơn vị: mm\n")
        w = csv.writer(f)
        w.writerow(LOG_HEADER)
        w.writerows(rows)
    return path


def main(cad_filter, edge_filters, mark_filters, hatch_filters, legend, base_spec, template_name, style_name,
         min_area, make_floors, dry_run):
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."], [], []
    view = doc.ActiveView
    if not isinstance(view, ViewPlan) or view.IsTemplate or view.GenLevel is None:
        return [u"DỪNG: view đang mở phải là mặt bằng (Structural/Floor Plan). Mở view mặt bằng tầng cần vẽ rồi Run."], [], []
    level = view.GenLevel
    style = find_line_style(style_name)

    cad = pick_cad(cad_filter)
    cad_name = get_name(doc.GetElement(cad.GetTypeId()))
    items, other = cad_items(cad)
    layers = sorted(set(l for l, _, _ in items if l))
    edge_layers = [l for l in layers if matches(l, edge_filters)]
    if not edge_layers:
        return [u"DỪNG: không có layer nào chứa '{}'. Các layer nét trong CAD:".format(u"; ".join(edge_filters))] \
            + layers, [], []
    mark_layers = [l for l in layers if matches(l, mark_filters)]
    segs, marks, arcs = [], [], 0
    for layer, pts, is_arc in items:
        if layer in edge_layers:
            segs += [(p[0], p[1], q[0], q[1]) for p, q in zip(pts[:-1], pts[1:])]
            arcs += 1 if is_arc else 0
        if layer in mark_layers and len(pts) == 2:
            marks.append((pts[0][0], pts[0][1], pts[1][0], pts[1][1]))

    # --- Hatch: đọc từ bản sao DWG
    warnings, zones, unknown, hatch_layers, other_hatch = [], [], {}, set(), {}
    legend_pats = set(p for k in legend for p in k.split(u"+"))
    path = cad_file_path(cad)
    core = find_accoreconsole()
    if path is None:
        return [u"DỪNG: bản CAD phải được LINK (không Import) và file DWG phải còn ở đường dẫn gốc để đọc hatch."], [], []
    if core is None:
        return [u"DỪNG: không tìm thấy AutoCAD Core Console (C:\\Program Files\\Autodesk\\AutoCAD *\\accoreconsole.exe)."], [], []
    raw, errors = read_dwg_hatches(path, core)
    tf = cad.GetTotalTransform()
    for layer, pattern, loops in raw:
        if not matches(layer, hatch_filters):
            if pattern in legend_pats:
                other_hatch[layer] = other_hatch.get(layer, 0) + 1
            continue
        hatch_layers.add(layer)
        if pattern not in legend_pats:
            unknown[pattern] = unknown.get(pattern, 0) + 1
            continue
        mloops = []
        for l in loops:
            ps = [tf.OfPoint(XYZ(from_mm(x), from_mm(y), 0)) for x, y in l]
            mloops.append([(to_mm(p.X), to_mm(p.Y)) for p in ps])
        zones.append({"pattern": pattern, "spec": legend.get(pattern), "loops": mloops})
    for layer, err in errors:
        if matches(layer, hatch_filters):
            warnings.append(u"CẢNH BÁO: bỏ 1 hatch trên layer {}: {}".format(layer, err))

    blocks, regions, info = find_regions(segs, marks, zones, base_spec,
                                         {"snap": SNAP_MM, "hatch_snap": HATCH_SNAP_MM, "min_area": min_area}, legend)

    # --- Đường bao cần vẽ: bao ngoài, lỗ mở, vùng hatch (nét chung vẽ một lần)
    lines = LineSet(DUP_TOL_MM)
    rows, plan_lines = [], []
    for k, b in enumerate(blocks):
        n = lines.add_loop(b["outer"])
        rows.append([u"Bao ngoài {:02d}".format(k + 1), u"đường bao", u"{:.2f}".format(b["area"]), n, u"", u"", u"",
                     fmt(b["outer"][0])])
        for j, o in enumerate(b["openings"]):
            n = lines.add_loop(o["loop"])
            note = u"lỗ mở" + (u" (gộp {} ô)".format(o["n"]) if o["n"] > 1 else u"")
            if o["edge"]:
                note += u" – CHẠM BAO NGOÀI"
            rows.append([u"Lỗ mở {:02d}-{:02d}".format(k + 1, j + 1), note, u"{:.2f}".format(o["area"]), n, u"", u"", u"",
                         fmt(o["loop"][0])])
    zcount = {}
    for r in regions:
        if r["pattern"] is None:
            continue
        zcount[r["pattern"]] = zcount.get(r["pattern"], 0) + 1
        r["name"] = u"Vùng {} {:02d}".format(r["pattern"], zcount[r["pattern"]])
        n = lines.add_loop(r["outer"]) + sum(lines.add_loop(h) for h in r["holes"])
        rows.append([r["name"], u"đường bao – " + spec_text(r["spec"]), u"{:.2f}".format(r["area"]), n, u"", u"", u"",
                     fmt(r["outer"][0])])
    nbase = 0
    for r in regions:
        if r["pattern"] is None:
            nbase += 1
            r["name"] = u"Sàn nền {:02d}".format(nbase)

    z = level.ProjectElevation
    old = existing_lines(view)
    todo = [(a, b) for a, b in lines.out if not is_dup(a, b, old)]
    skipped = len(lines.out) - len(todo)

    ftypes = FloorTypes(template_name) if make_floors else None
    old_floors = existing_floors(level) if make_floors else []
    drawn, floors, new_types = [], [], []
    if make_floors:
        for t in sorted(set(r["spec"][0] for r in regions)):
            ft, name = ftypes.plan(t)
            if ft is None:
                ftypes.template()
                new_types.append(name)

    if not dry_run:
        TransactionManager.Instance.EnsureInTransaction(doc)
    try:
        if not dry_run:
            for a, b in todo:
                dc = doc.Create.NewDetailCurve(view, Line.CreateBound(XYZ(from_mm(a[0]), from_mm(a[1]), z),
                                                                      XYZ(from_mm(b[0]), from_mm(b[1]), z)))
                if style is not None:
                    dc.LineStyle = style
                drawn.append(dc)
        if make_floors:
            for r in regions:
                t, off = r["spec"]
                label = u"sàn – " + spec_text(r["spec"]) + (u" (không hatch)" if r["pattern"] is None else u"")
                ft_plan, tname = ftypes.plan(t)
                cx = (min(p[0] for p in r["outer"]) + max(p[0] for p in r["outer"])) / 2.0
                cy = (min(p[1] for p in r["outer"]) + max(p[1] for p in r["outer"])) / 2.0
                dup = [f for f, a, c in old_floors
                       if type_name(doc.GetElement(f.GetTypeId())) == tname and abs(a - r["area"]) <= 0.05 and c is not None
                       and abs(c[0] - cx) < 50 and abs(c[1] - cy) < 50]
                result, eid = u"", u""
                if dup:
                    result, eid = u"đã có – bỏ qua", str(dup[0].Id.Value)
                elif dry_run:
                    result = u"Sẽ tạo" + (u" (type mới)" if ft_plan is None else u"")
                else:
                    try:
                        ft = ftypes.get(t)
                        loops = List[CurveLoop]()
                        loops.Add(curve_loop(r["outer"], z))
                        for h in r["holes"]:
                            loops.Add(curve_loop(h, z))
                        fl = Floor.Create(doc, loops, ft.Id, level.Id, True, None, 0.0)
                        fl.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(from_mm(off))
                        floors.append(fl)
                        result, eid = u"Đã tạo", str(fl.Id.Value)
                    except Exception as ex:
                        result = u"LỖI: {}".format(ex)
                rows.append([r["name"], label, u"{:.2f}".format(r["area"]), len(r["holes"]), tname, result, eid,
                             fmt(r["outer"][0])])
    finally:
        if not dry_run:
            TransactionManager.Instance.TransactionTaskDone()

    log = write_log(rows, cad_name, dry_run)
    nz = sum(1 for r in regions if r["pattern"] is not None)
    report = [
        u"{}: {} bao ngoài, {} lỗ mở, {} vùng hatch – {} nét{}{}".format(
            u"CHẠY THỬ (dry-run)" if dry_run else u"ĐÃ THỰC HIỆN", len(blocks),
            sum(len(b["openings"]) for b in blocks), nz, len(lines.out),
            u"" if dry_run else u" (đã vẽ {})".format(len(drawn)),
            (u"; {} tấm sàn".format(len(regions)) + (u"" if dry_run else u" (đã tạo {})".format(len(floors))))
            if make_floors else u"; không tạo sàn"),
        u"Bản CAD: {} | View: {} | Level: {}".format(cad_name, view.Name, level.Name),
        u"Layer mép sàn: {} | dấu lỗ mở: {} ({} dấu X) | hatch: {}".format(
            u", ".join(edge_layers), u", ".join(mark_layers) or u"không có", info["xmarks"],
            u", ".join(sorted(hatch_layers)) or u"không có"),
        u"Ghi chú: {} | không hatch: {}".format(
            u"; ".join(u"{} = {}".format(k, spec_text(v)) for k, v in sorted(legend.items())), spec_text(base_spec)),
        u"Log: {}".format(log),
    ]
    if new_types:
        report.append(u"{} type sàn mới (nhân bản từ '{}'): {}".format(
            u"Sẽ tạo" if dry_run else u"Đã tạo", template_name, u", ".join(new_types)))
    if make_floors and old_floors:
        report.append(u"CẢNH BÁO: level {} đã có {} sàn (Id {}) – sàn mới sẽ chồng lên; xoá tay sàn cũ nếu thay thế.".format(
            level.Name, len(old_floors), u", ".join(str(f.Id.Value) for f, _, _ in old_floors)))
    if unknown:
        report.append(u"Hatch không có trong ghi chú (bỏ qua): {}".format(
            u", ".join(u"{} ×{}".format(k or u"?", v) for k, v in sorted(unknown.items()))))
    report += warnings
    if info["conflict"]:
        report.append(u"CẢNH BÁO: {} ô nằm trong 2 hatch khác ghi chú – lấy hatch vẽ sau.".format(info["conflict"]))
    for p, why in info["bad"]:
        report.append(u"CẢNH BÁO: bỏ {} tại {} – kiểm tra lại nét / biên hatch.".format(why, fmt(p)))
    edge_open = [r[0] for r in rows if u"CHẠM BAO NGOÀI" in r[1]]
    if edge_open:
        report.append(u"CẢNH BÁO: lỗ mở chạm bao ngoài ({}) – sàn nền sẽ được khoét vào mép.".format(u", ".join(edge_open)))
    if info["stray"]:
        report.append(u"CẢNH BÁO: {} dấu X không nằm trong ô kín nào của bao ngoài (không vẽ): {}".format(
            len(info["stray"]), u", ".join(fmt(p) for p in info["stray"][:10])))
    if info["loose_x"]:
        report.append(u"CẢNH BÁO: {} dấu X nằm trong ô lớn hơn nhiều so với dấu X (đường bao lỗ mở chưa kín trên layer "
                      u"mép sàn) – KHÔNG khoét, kiểm tra nét quanh: {}".format(len(info["loose_x"]), u", ".join(
                          u"{} (ô {:.1f} m²)".format(fmt(p), a) for p, a in info["loose_x"][:10])))
    if other_hatch:
        report.append(u"GỢI Ý: hatch đúng mẫu ghi chú nhưng nằm ngoài layer hatch IN[3] (bỏ qua): {} – thêm vào IN[3] "
                      u"nếu là vùng sàn.".format(u", ".join(u"{} ×{}".format(k, v) for k, v in sorted(other_hatch.items()))))
    if info["loose"]:
        report.append(u"CẢNH BÁO: {} đầu nét cụt/hở (đã bỏ) – nếu thiếu đường bao, kiểm tra nét tại: {}{}".format(
            len(info["loose"]), u", ".join(fmt(p) for p in info["loose"][:10]), u" …" if len(info["loose"]) > 10 else u""))
        cand = [l for l in layers if l not in edge_layers and
                any(k in l.lower() for k in (u"cot", u"cột", u"vach", u"vách", u"wall", u"col"))]
        if cand:
            report.append(u"GỢI Ý: mép sàn thường bị đứt tại cột / vách – thử thêm layer cột/vách vào IN[1]: {}".format(
                u", ".join(cand)))
    for a, p, why in info["small"]:
        report.append(u"Bỏ qua vòng tại {}: {}".format(fmt(p), why))
    if arcs:
        report.append(u"CẢNH BÁO: {} cung tròn trên layer mép sàn được vẽ thành đoạn gấp khúc.".format(arcs))
    if other:
        report.append(u"Bỏ qua đối tượng CAD không hỗ trợ: {}".format(
            u", ".join(u"{} ×{}".format(k, v) for k, v in sorted(other.items()))))
    if skipped:
        report.append(u"{} nét trùng Detail Line đã có trong view → không vẽ lại.".format(skipped))
    if dry_run:
        report.append(u"Đúng thì đổi Dry-run = False và Run lại. Undo bằng mục \"{}\".".format(TRANSACTION_NAME))
    report.append(u" | ".join(LOG_HEADER))
    report += [u" | ".join(str(c) for c in r) for r in rows]
    return report, drawn, floors


def force_rerun_next_time():
    """Dynamo chỉ chạy lại node khi có đầu vào đổi → sau Undo / xoá trong Revit, bấm Run lần 2 không có tác dụng.
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
            if u"ARV_VeBaoSanTuCAD_v1" in (getattr(n, "Script", None) or u""):
                n.MarkNodeAsModified(True)
                return None
        return u"Không tìm thấy node để đánh dấu chạy lại."
    except Exception as ex:
        return u"Không đánh dấu được node chạy lại ({}) – lần sau đổi một ô đầu vào rồi Run.".format(ex)


if DYNAMO:
    import traceback
    # Graph cũ còn ô "Tạo sàn" ở IN[9] và Dry-run ở IN[10] → bỏ qua ô "Tạo sàn", lấy Dry-run ở ô cuối
    _dry = IN[10] if len(IN) > 10 else IN[9]
    DRY_RUN = True if _dry is None else bool(_dry)
    try:
        OUT = list(main(
            (IN[0] or u"").strip(),
            split_filters(IN[1] or u"S-Thay;S-Cot vach"),
            split_filters(IN[2] or u"S-Manh"),
            split_filters(IN[3] or u"S-Hatch"),
            parse_legend(IN[4] or u"ANSI31=230;STARS=250;TRIANG=500;ANSI37=450/-50"),
            parse_spec(IN[5] or u"230/-50"),
            (IN[6] or u"Generic 200").strip(),
            (IN[7] or u"").strip(),
            float(10.0 if IN[8] is None else IN[8]),
            True,                                   # luôn tạo sàn (ô "Tạo sàn" đã bỏ – dễ bấm nhầm với Dry-run)
            DRY_RUN,
        ))
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], [], []]
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with io.open(os.path.join(folder, "VeBaoSanTuCAD_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))), "w", encoding="utf-8-sig") as f:
                f.write(u"\n".join(OUT[0]))
        except Exception:
            pass
    note = force_rerun_next_time()
    if note:
        OUT[0].append(u"LƯU Ý: " + note)
