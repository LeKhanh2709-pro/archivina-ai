# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong ARV_TaoDamTuCAD_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Tạo dầm kết cấu từ mặt bằng kết cấu sàn (DWG đã Link vào Revit).
#   Cách nhận dầm (theo NHÃN, không đoán theo nét):
#   - Mỗi nhãn tiết diện "bxh" (VD "25X40", "D1 (220x500)") trên layer nhãn là một dầm.
#   - Phương dầm = phương chữ của nhãn. Tìm cặp nét song song (layer cạnh dầm) cách nhau đúng b,
#     nằm sát nhãn → trục dầm là đường giữa cặp nét.
#   - Chiều dài dầm = đoạn hai cạnh cùng có nét; chỗ một cạnh bị ngắt do dầm khác đâm vào (cạnh kia
#     liền) được nối qua. Đầu dầm chạm cạnh một dầm vuông góc thì kéo tới trục dầm đó.
#   - Dầm liên tục ghi 1 nhãn: các nhịp tiếp theo của cùng cặp nét (cách nhau qua cột ≤ IN[10]) được tạo
#     theo nhãn đó cho tới nhịp có nhãn khác.
#   - Nhãn không tìm được cặp nét → bỏ qua, ghi vào báo cáo để vẽ tay.
#   Chữ trong bản link Revit không đọc được nên nhãn được đọc từ BẢN SAO file DWG qua AutoCAD Core Console.
# INPUT
#   IN[0] (str)   Một phần tên bản CAD (để trống nếu mô hình chỉ có 1 bản CAD)
#   IN[1] (str)   Layer cạnh dầm, nhiều chuỗi cách nhau bằng ';' – layer chứa một trong các chuỗi được dùng
#   IN[2] (str)   Layer nhãn tiết diện dầm (khớp chuỗi con)
#   IN[3] (float) Hệ số đổi số trong nhãn ra mm (nhãn ghi cm → 10; ghi mm → 1)
#   IN[4] (str)   Tên family dầm kết cấu tiết diện chữ nhật
#   IN[5] (str)   Tên parameter type bề rộng (VD "b")
#   IN[6] (str)   Tên parameter type chiều cao (VD "h")
#   IN[7] (str)   Tên level tham chiếu của dầm
#   IN[8] (float) Cao độ đỉnh dầm so với level (mm), mặc định 0
#   IN[9] (bool)  Dry-run: True = chỉ báo cáo, không ghi vào mô hình (mặc định True)
#   IN[10] (float) Nối nhịp không nhãn qua cột: khe tối đa (mm) giữa hai nhịp thẳng hàng cùng cặp nét
#                 (bề rộng cột / vách / nút dầm). Một nhãn áp cho cả dầm liên tục, mỗi nhịp tạo một dầm.
#                 0 = tắt (chỉ tạo nhịp có nhãn). Mặc định 2500.
# OUTPUT
#   OUT (list[str]) Báo cáo: tóm tắt, layer đã dùng, đường dẫn log, rồi từng dầm:
#                   Nhãn | Điểm đầu | Điểm cuối | Dài | Type | Kết quả | ElementId

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
                                   PolyLine, Line, XYZ, Transaction, UnitUtils, UnitTypeId, ModelPathUtils,
                                   BuiltInParameter, BuiltInCategory, Level, LocationCurve, StorageType)
    from Autodesk.Revit.DB.Structure import StructuralType, YJustification, ZJustification
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager

    doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = u"ARV - Tạo dầm kết cấu từ CAD"
WIDTH_TOL_MM = 15.0        # Sai lệch cho phép giữa khoảng cách cặp nét và bề rộng b ghi trên nhãn
LABEL_TOL_MM = 800.0       # Nhãn cách mép dầm tối đa
JOIN_TOL_MM = 5.0          # Nối các đoạn nét thẳng hàng sát nhau
MERGE_GAP_MM = 2000.0      # Một cạnh bị ngắt (cạnh kia liền) tối đa bao nhiêu thì vẫn nối qua
END_SNAP_MM = 50.0         # Đầu dầm cách mép dầm vuông góc ≤ giá trị này thì kéo tới trục dầm đó
MIN_LENGTH_MM = 300.0      # Bỏ dầm ngắn hơn
DUP_TOL_MM = 5.0
ANGLE_TOL = 1e-3
CORE_TIMEOUT_S = 180
# [cần xác nhận] standards chưa quy định tên type dầm; BIM Manager chốt rồi sửa tại đây
BEAM_TYPE_NAME = u"{b} x {h}mm"

LABEL_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*[xX×]\s*(\d+(?:[.,]\d+)?)")


# =====================================================================================
# PHẦN HÌNH HỌC – chỉ dùng tuple (x, y) theo mm, không phụ thuộc Revit (chạy thử được ngoài Dynamo)
# =====================================================================================
def parse_label(text, factor):
    """'25X40' → (250, 400) khi factor = 10. Trả về None nếu không phải nhãn tiết diện."""
    s = re.sub(r"%%[A-Za-z]", "", text or u"")
    m = LABEL_RE.search(s)
    if not m:
        return None
    b = float(m.group(1).replace(",", ".")) * factor
    h = float(m.group(2).replace(",", ".")) * factor
    if b <= 0 or h <= 0:
        return None
    return int(round(b)), int(round(h))


def canonical(dx, dy):
    """Vector đơn vị, chiều quy ước (x > 0, hoặc x = 0 và y > 0) để cặp nét ngược chiều vẫn so được."""
    n = math.hypot(dx, dy)
    ux, uy = dx / n, dy / n
    if ux < -1e-9 or (abs(ux) <= 1e-9 and uy < 0):
        ux, uy = -ux, -uy
    return ux, uy


def union(intervals, tol):
    out = []
    for a, b in sorted(intervals):
        if out and a <= out[-1][1] + tol:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def covers(intervals, a, b, tol):
    return any(i0 <= a + tol and i1 >= b - tol for i0, i1 in intervals)


def fill_gaps(side, other, max_gap, tol):
    """Nối khe hở trên một cạnh nếu khe ≤ max_gap và cạnh kia liền suốt khe (dầm khác đâm vào một phía)."""
    out = [list(side[0])] if side else []
    for a, b in side[1:]:
        g0, g1 = out[-1][1], a
        if g1 - g0 <= max_gap and covers(other, g0, g1, tol):
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def intersect(xs, ys):
    out, i, j = [], 0, 0
    while i < len(xs) and j < len(ys):
        a, b = max(xs[i][0], ys[j][0]), min(xs[i][1], ys[j][1])
        if b > a:
            out.append((a, b))
        if xs[i][1] < ys[j][1]:
            i += 1
        else:
            j += 1
    return out


class Beam(object):
    def __init__(self, label, b, h, u, offset, t0, t1, lp):
        self.label, self.b, self.h = label, b, h
        self.u = u                    # phương dầm (đơn vị)
        self.offset = offset          # toạ độ trục theo pháp tuyến n = (-uy, ux)
        self.t0, self.t1 = t0, t1     # toạ độ hai đầu theo u
        self.lp = lp                  # điểm nhãn
        self.lt = lp[0] * u[0] + lp[1] * u[1]   # vị trí nhãn theo u
        self.note = u""

    @property
    def n(self):
        return -self.u[1], self.u[0]

    def point(self, t):
        return (self.n[0] * self.offset + self.u[0] * t, self.n[1] * self.offset + self.u[1] * t)

    @property
    def length(self):
        return self.t1 - self.t0


def find_beams(segments, labels, opt):
    """segments: [(x0, y0, x1, y1)] mm; labels: [(text, (b, h), (x, y), (dx, dy))].

    Trả về (beams, unmatched) – unmatched: [(text, (x, y), lý do)].
    """
    wtol, ltol, jtol = opt["width_tol"], opt["label_tol"], opt["join_tol"]
    segs = []
    for x0, y0, x1, y1 in segments:
        if math.hypot(x1 - x0, y1 - y0) > jtol:
            segs.append((x0, y0, x1, y1, canonical(x1 - x0, y1 - y0)))

    beams, unmatched = [], []
    for text, (b, h), (lx, ly), (dx, dy) in labels:
        u = canonical(dx, dy)
        n = (-u[1], u[0])
        lt, lo = lx * u[0] + ly * u[1], lx * n[0] + ly * n[1]
        # Nét song song với chữ, nằm trong dải ± (b + ltol) quanh nhãn → gom theo toạ độ pháp tuyến
        lines = {}
        for x0, y0, x1, y1, d in segs:
            if abs(d[0] * u[1] - d[1] * u[0]) > ANGLE_TOL:
                continue
            o = x0 * n[0] + y0 * n[1]
            if abs(o - lo) > b + ltol:
                continue
            ta, tb = sorted((x0 * u[0] + y0 * u[1], x1 * u[0] + y1 * u[1]))
            key = int(round(o / jtol))
            lines.setdefault(key, []).append((o, ta, tb))
        rows = []
        for key, items in lines.items():
            o = sum(i[0] for i in items) / len(items)
            rows.append((o, union([(i[1], i[2]) for i in items], jtol)))
        rows.sort()
        best = None
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                (o1, s1), (o2, s2) = rows[i], rows[j]
                if abs((o2 - o1) - b) > wtol:
                    continue
                dist = 0.0 if o1 <= lo <= o2 else min(abs(lo - o1), abs(lo - o2))
                if dist > ltol:
                    continue
                a = fill_gaps(s1, s2, opt["merge_gap"], jtol)
                c = fill_gaps(s2, s1, opt["merge_gap"], jtol)
                parts = intersect(a, c)
                if not parts:
                    continue
                # Đoạn chung chứa (hoặc gần nhất với) vị trí nhãn theo phương dầm
                part = min(parts, key=lambda p: 0.0 if p[0] <= lt <= p[1] else min(abs(lt - p[0]), abs(lt - p[1])))
                gap = 0.0 if part[0] <= lt <= part[1] else min(abs(lt - part[0]), abs(lt - part[1]))
                if gap > ltol:
                    continue
                # Có nét khác nằm giữa cặp nét tại vị trí nhãn → không phải một dầm
                inner = any(o1 + jtol < o < o2 - jtol and covers(s, part[0], part[1], 0) for o, s in rows)
                if inner:
                    continue
                score = (dist + gap, dist)
                if best is None or score < best[0]:
                    clean = [p for p in parts
                             if not any(o1 + jtol < o < o2 - jtol and covers(s, p[0], p[1], 0) for o, s in rows)]
                    best = (score, (o1 + o2) / 2.0, part, chain_parts(clean, part, opt["span_gap"]))
        if best is None:
            unmatched.append((text, (lx, ly), u"không tìm thấy cặp nét song song cách nhau {} mm sát nhãn".format(b)))
            continue
        _, axis, (t0, t1), chain = best
        bm = Beam(text, b, h, u, axis, t0, t1, (lx, ly))
        bm.chain = chain
        beams.append(bm)

    beams = merge_duplicates(beams, unmatched, opt)
    if opt["span_gap"] > 0:
        beams = expand_spans(beams, opt)
    snap_ends(beams, opt)
    kept = []
    for bm in beams:
        if bm.length < opt["min_length"]:
            unmatched.append((bm.label, bm.lp, u"dầm dài {:.0f} mm < {:.0f} mm".format(bm.length, opt["min_length"])))
        else:
            kept.append(bm)
    return kept, unmatched


def chain_parts(parts, own, span_gap):
    """Các nhịp liền nhau của cùng cặp nét, nối từ nhịp có nhãn sang hai phía qua khe ≤ span_gap (cột, vách,
    nút dầm giao chữ thập). span_gap = 0 → chỉ nhịp có nhãn."""
    parts = sorted(parts)
    if own not in parts:
        return [own]
    i0 = i1 = parts.index(own)
    if span_gap > 0:
        while i0 > 0 and parts[i0][0] - parts[i0 - 1][1] <= span_gap:
            i0 -= 1
        while i1 < len(parts) - 1 and parts[i1 + 1][0] - parts[i1][1] <= span_gap:
            i1 += 1
    return parts[i0:i1 + 1]


def expand_spans(beams, opt):
    """Một nhãn áp cho cả dầm liên tục: các nhịp thẳng hàng cùng bề rộng (cùng cặp nét) không có nhãn riêng
    được tạo theo nhãn đó, mỗi nhịp một dầm. Nhịp nằm giữa hai nhãn → theo nhãn gần hơn (tính theo số nhịp)."""
    tol = opt["join_tol"]
    groups = []
    for bm in beams:
        for g in groups:
            o = g[0]
            if abs(o.u[0] * bm.u[1] - o.u[1] * bm.u[0]) < ANGLE_TOL and abs(o.offset - bm.offset) < tol and o.b == bm.b:
                g.append(bm)
                break
        else:
            groups.append([bm])
    result = list(beams)
    for g in groups:
        owned = [(bm.t0, bm.t1) for bm in g]
        claims = {}
        for bm in g:
            chain = getattr(bm, "chain", [])
            own_idx = [k for k, p in enumerate(chain) if p[0] < bm.t1 - tol and p[1] > bm.t0 + tol]
            if not own_idx:
                continue
            for k, p in enumerate(chain):
                if any(p[0] < t1 - tol and p[1] > t0 + tol for t0, t1 in owned):
                    continue        # nhịp đã có nhãn riêng
                dist = min(abs(k - j) for j in own_idx)
                key = (int(round(p[0])), int(round(p[1])))
                claims.setdefault(key, (p, []))[1].append((dist, bm))
        for key, (p, cl) in sorted(claims.items()):
            cl.sort(key=lambda x: (x[0], x[1].lt))
            dist, bm = cl[0]
            nb = Beam(bm.label, bm.b, bm.h, bm.u, bm.offset, p[0], p[1], bm.lp)
            nb.note = u"nhịp nối theo nhãn"
            if len(cl) > 1 and cl[1][0] == dist and (cl[1][1].b, cl[1][1].h) != (bm.b, bm.h):
                nb.note = u"nhịp giữa hai nhãn khác tiết diện '{}' / '{}' – đã lấy '{}', kiểm tra lại".format(
                    bm.label, cl[1][1].label, bm.label)
            result.append(nb)
    return result


def split_point(a, c, beams):
    """Vị trí cắt giữa hai nhãn a, c trên cùng một trục: trục của dầm cắt ngang RỘNG NHẤT nằm giữa hai nhãn
    (dầm chính làm gối – chỗ đổi tiết diện), cùng bề rộng thì lấy dầm gần giữa hai nhãn; không có thì lấy
    điểm giữa hai nhãn."""
    lo, hi = sorted((a.lt, c.lt))
    best = None
    for o in beams:
        if abs(o.u[0] * a.u[1] - o.u[1] * a.u[0]) < 0.1:
            continue
        denom = a.u[0] * o.n[0] + a.u[1] * o.n[1]
        t = (o.offset - a.offset * (a.n[0] * o.n[0] + a.n[1] * o.n[1])) / denom
        p = a.point(t)
        s = p[0] * o.u[0] + p[1] * o.u[1]
        if lo < t < hi and o.t0 - a.b <= s <= o.t1 + a.b:
            key = (-o.b, abs(t - (lo + hi) / 2.0))
            if best is None or key < best[0]:
                best = (key, t)
    return best[1] if best is not None else (lo + hi) / 2.0


def merge_duplicates(beams, unmatched, opt):
    """Hai nhãn trên cùng một dầm (cùng trục, chồng chiều dài):
    - cùng tiết diện → gộp thành một dầm;
    - khác tiết diện → hai nhịp khác nhau, cắt tại trục dầm cắt ngang giữa hai nhãn."""
    tol = opt["join_tol"]
    out = []
    for bm in beams:
        dup = None
        for o in out:
            if abs(o.u[0] * bm.u[1] - o.u[1] * bm.u[0]) < ANGLE_TOL and abs(o.offset - bm.offset) < tol \
                    and bm.t0 < o.t1 - tol and bm.t1 > o.t0 + tol:
                dup = o
                break
        if dup is None:
            out.append(bm)
        elif (dup.b, dup.h) != (bm.b, bm.h) and abs(dup.lt - bm.lt) > tol:
            t = split_point(dup, bm, beams)
            first, second = (dup, bm) if dup.lt < bm.lt else (bm, dup)
            first.t1, second.t0 = min(first.t1, t), max(second.t0, t)
            out.append(bm)
        elif (dup.b, dup.h) != (bm.b, bm.h):
            dup.note = u"trùng dầm với nhãn '{}' khác tiết diện – kiểm tra lại".format(bm.label)
            unmatched.append((bm.label, bm.lp, u"trùng vị trí với dầm '{}' – đã bỏ".format(dup.label)))
        else:
            dup.t0, dup.t1 = min(dup.t0, bm.t0), max(dup.t1, bm.t1)
    return out


def snap_ends(beams, opt):
    """Đầu dầm chạm mép một dầm vuông góc / xiên → kéo tới trục dầm đó để Revit nối dầm."""
    snap = opt["end_snap"]
    ends = []
    for bm in beams:
        for which in (0, 1):
            t = bm.t0 if which == 0 else bm.t1
            p = bm.point(t)
            best = None
            for o in beams:
                if o is bm or abs(o.u[0] * bm.u[1] - o.u[1] * bm.u[0]) < 0.1:
                    continue
                d = p[0] * o.n[0] + p[1] * o.n[1] - o.offset          # khoảng cách tới trục dầm kia
                s = p[0] * o.u[0] + p[1] * o.u[1]
                # Nút góc (chữ L): đầu dầm kia cũng dừng ở mép dầm này → cho phép lệch thêm nửa bề rộng
                reach = bm.b / 2.0 + snap
                if abs(d) > o.b / 2.0 + snap or s < o.t0 - reach or s > o.t1 + reach:
                    continue
                # Giao của trục dầm này với trục dầm kia
                denom = bm.u[0] * o.n[0] + bm.u[1] * o.n[1]
                t_new = t - d / denom
                # Chỉ kéo dài ra phía ngoài, không rút ngắn vào trong nhịp
                if (which == 0 and t_new > t + 1) or (which == 1 and t_new < t - 1):
                    continue
                if best is None or abs(t_new - t) < abs(best - t):
                    best = t_new
            if best is not None:
                ends.append((bm, which, best))
    for bm, which, t in ends:
        if which == 0:
            bm.t0 = t
        else:
            bm.t1 = t


# =====================================================================================
# PHẦN REVIT
# =====================================================================================
cad_filter = ((IN[0] if DYNAMO else u"") or u"").strip()
edge_filters = [s.strip().lower() for s in ((IN[1] if DYNAMO else u"") or u"").split(u";") if s.strip()]
label_filter = ((IN[2] if DYNAMO else u"") or u"").strip().lower()
label_factor = float(IN[3]) if DYNAMO and IN[3] else 10.0
family_name = ((IN[4] if DYNAMO else u"") or u"").strip()
param_b = ((IN[5] if DYNAMO else u"") or u"b").strip()
param_h = ((IN[6] if DYNAMO else u"") or u"h").strip()
level_name = ((IN[7] if DYNAMO else u"") or u"").strip()
top_offset_mm = float(IN[8]) if DYNAMO and IN[8] else 0.0
dry_run = True if not DYNAMO or IN[9] is None else bool(IN[9])
span_gap_mm = max(0.0, float(IN[10])) if DYNAMO and len(IN) > 10 and IN[10] is not None else 2500.0


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


def is_central_file(document):
    if not document.IsWorkshared:
        return False
    try:
        central = ModelPathUtils.ConvertModelPathToUserVisiblePath(document.GetWorksharingCentralModelPath())
    except Exception:
        return False
    return os.path.normcase(central or "") == os.path.normcase(document.PathName or "")


def model_role(document):
    # Trường Bộ môn (Role) theo tên file ISO 19650: PRJ-ARV-T1-ZZ-M3-S-0001
    parts = (document.Title or "").split("-")
    return parts[5].upper() if len(parts) >= 7 else None


# --- Bản CAD ------------------------------------------------------------------------
def pick_cad():
    instances = list(FilteredElementCollector(doc).OfClass(ImportInstance).ToElements())
    if cad_filter:
        instances = [i for i in instances if cad_filter.lower() in get_name(doc.GetElement(i.GetTypeId())).lower()]
    if len(instances) != 1:
        names = [get_name(doc.GetElement(i.GetTypeId())) for i in
                 FilteredElementCollector(doc).OfClass(ImportInstance).ToElements()]
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


def cad_segments(cad):
    """Mọi đoạn thẳng của CAD (kể cả trong block lồng nhau), toạ độ mô hình, kèm tên layer."""
    opt = Options()
    if cad.ViewSpecific:
        opt.View = doc.GetElement(cad.OwnerViewId)
    result = []

    def add(layer, p0, p1):
        result.append((layer, (to_mm(p0.X), to_mm(p0.Y), to_mm(p1.X), to_mm(p1.Y))))

    def walk(geo):
        for obj in geo:
            if isinstance(obj, GeometryInstance):
                walk(obj.GetInstanceGeometry())
            elif isinstance(obj, PolyLine):
                pts = list(obj.GetCoordinates())
                for p0, p1 in zip(pts[:-1], pts[1:]):
                    add(layer_of(obj), p0, p1)
            elif isinstance(obj, Line):
                add(layer_of(obj), obj.GetEndPoint(0), obj.GetEndPoint(1))

    geo = cad.get_Geometry(opt)
    if geo is not None:
        walk(geo)
    return result


# --- Đọc nhãn dầm từ DWG bằng AutoCAD Core Console ----------------------------------
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


def clean_mtext(s):
    s = re.sub(r"\\[A-Za-z][^;\\{}]*;", "", s)   # \fArial|b0;  \H2.5;  \C1; ...
    s = re.sub(r"\\[Pp~]", " ", s)
    return s.replace("{", "").replace("}", "").strip()


# Đọc TEXT/MTEXT ở model space VÀ trong block (lồng nhau, tối đa 8 cấp): toạ độ + góc chữ đổi về WCS theo
# ma trận affine (a b c d e f) của từng INSERT (điểm chèn, tỉ lệ, góc xoay, base point của block).
# Chữ nằm trên layer "0" trong block lấy layer của INSERT cha.
# TEXT căn lề khác Left lấy điểm căn (mã 11), còn lại lấy điểm chèn (mã 10); góc chữ mã 50 (radian)
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
(defun _txt (d m lay / p r q v)
  (setq p (if (and (= (cdr (assoc 0 d)) "TEXT") (or (/= 0 (cdr (assoc 72 d))) (/= 0 (cdr (assoc 73 d)))))
            (cdr (assoc 11 d)) (cdr (assoc 10 d))))
  (setq r (if (assoc 50 d) (cdr (assoc 50 d)) 0.0))
  (setq q (_ap m p) v (_ap (list (nth 0 m) (nth 1 m) (nth 2 m) (nth 3 m) 0.0 0.0) (list (cos r) (sin r))))
  (write-line (strcat (substr (cdr (assoc 0 d)) 1 1) "|" lay "|" (rtos (car q) 2 3) "," (rtos (cadr q) 2 3) "|"
                      (rtos (atan (cadr v) (car v)) 2 6) "|" (cdr (assoc 1 d))) f))
(defun _walk (name m parent depth / e d)
  (setq e (cdr (assoc -2 (tblsearch "BLOCK" name))))
  (while e
    (setq d (entget e))
    (cond ((member (cdr (assoc 0 d)) '("TEXT" "MTEXT")) (_txt d m (_lay d parent)))
          ((and (= (cdr (assoc 0 d)) "INSERT") (< depth 8))
            (_walk (cdr (assoc 2 d)) (_mul m (_ins d)) (_lay d parent) (1+ depth))))
    (setq e (entnext e))))
(if (setq ss (ssget "_X" '((0 . "TEXT,MTEXT,INSERT") (410 . "Model"))))
  (progn (setq i 0)
    (repeat (sslength ss)
      (setq d (entget (ssname ss i)) i (1+ i))
      (if (= (cdr (assoc 0 d)) "INSERT")
        (_walk (cdr (assoc 2 d)) (_ins d) (cdr (assoc 8 d)) 1)
        (_txt d '(1.0 0.0 0.0 1.0 0.0 0.0) (cdr (assoc 8 d)))))))
(close f)
"""


def read_dwg_labels(dwg_path, core):
    """[(layer, text, x, y, góc)] theo toạ độ DWG. Chạy trên bản sao trong thư mục tạm – không mở file gốc."""
    work = tempfile.mkdtemp(prefix="ARV_TaoDam_")
    try:
        copy = os.path.join(work, "copy.dwg")
        shutil.copy2(dwg_path, copy)
        out = os.path.join(work, "labels.txt")
        scr = os.path.join(work, "dump.scr")
        with io.open(scr, "w", encoding="utf-8") as f:
            f.write(DUMP_LISP.replace("{out}", out.replace("\\", "/")))
        subprocess.run([core, "/i", copy, "/s", scr, "/l", "en-US"], stdin=subprocess.DEVNULL,
                       env=core_env(core), cwd=os.path.dirname(core),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=CORE_TIMEOUT_S, creationflags=0x08000000)
        if not os.path.isfile(out):
            raise Exception(u"Core Console không xuất được danh sách chữ")
        labels = []
        with io.open(out, "r", encoding="utf-8-sig", errors="replace") as f:
            for line in f.read().splitlines():
                parts = line.split("|")
                if len(parts) < 5:
                    continue
                kind, layer, xy, rot = parts[0], parts[1], parts[2], parts[3]
                text = u"|".join(parts[4:])
                if kind == "M":
                    text = clean_mtext(text)
                try:
                    x, y = [float(v) for v in xy.split(",")]
                    a = float(rot)
                except ValueError:
                    continue
                if text.strip():
                    labels.append((layer, text.strip(), x, y, a))
        return labels
    finally:
        shutil.rmtree(work, ignore_errors=True)


# --- Type, level ---------------------------------------------------------------------
def find_level(name):
    for l in FilteredElementCollector(doc).OfClass(Level).ToElements():
        if l.Name == name:
            return l
    names = sorted(l.Name for l in FilteredElementCollector(doc).OfClass(Level).ToElements())
    raise Exception(u"Không có level '{}'. Các level: {}".format(name, u", ".join(names)))


def beam_symbols():
    symbols = list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_StructuralFraming)
                   .WhereElementIsElementType().ToElements())
    result = [s for s in symbols if s.Family.Name == family_name]
    if not result:
        names = sorted(set(s.Family.Name for s in symbols))
        raise Exception(u"Không có family dầm '{}'. Các family dầm: {}".format(
            family_name, u", ".join(names) or u"không có"))
    for pname in (param_b, param_h):
        p = result[0].LookupParameter(pname)
        if p is None or p.StorageType != StorageType.Double:
            raise Exception(u"Family '{}' không có parameter type '{}' kiểu chiều dài.".format(family_name, pname))
    return result


# --- Log -------------------------------------------------------------------------------
LOG_HEADER = [u"Nhãn", u"Điểm đầu (mm)", u"Điểm cuối (mm)", u"Dài (mm)", u"Type", u"Kết quả",
              u"ElementId", u"Giá trị cũ", u"Giá trị mới"]


def write_log(rows, source):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoDamTuCAD_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    # CSV UTF-8 có BOM để Excel đọc đúng tiếng Việt
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


# --- Chương trình chính -----------------------------------------------------------
def main():
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."]
    warnings = []
    if model_role(doc) == "A":
        warnings.append(u"CẢNH BÁO: đây có vẻ là mô hình Kiến trúc (A). Dầm kết cấu thuộc mô hình Kết cấu (S).")

    cad = pick_cad()
    cad_name = get_name(doc.GetElement(cad.GetTypeId()))
    segments = cad_segments(cad)
    all_layers = sorted(set(l for l, _ in segments if l))
    edge_layers = set(l for l in all_layers if any(f in l.lower() for f in edge_filters))
    if not edge_layers:
        return [u"DỪNG: không có layer nào chứa '{}'. Các layer nét trong CAD:".format(u"; ".join(edge_filters))] \
            + all_layers

    path = cad_file_path(cad)
    if path is None:
        return [u"DỪNG: bản CAD phải được LINK (không Import) và file DWG phải còn ở đường dẫn gốc "
                u"để đọc nhãn dầm."]
    core = find_accoreconsole()
    if core is None:
        return [u"DỪNG: không tìm thấy AutoCAD Core Console (C:\\Program Files\\Autodesk\\AutoCAD *\\accoreconsole.exe)."]
    raw = read_dwg_labels(path, core)
    raw_layers = sorted(set(r[0] for r in raw))
    tf = cad.GetTotalTransform()
    labels = []
    for layer, text, x, y, a in raw:
        if label_filter and label_filter not in layer.lower():
            continue
        size = parse_label(text, label_factor)
        if size is None:
            continue
        p = tf.OfPoint(XYZ(from_mm(x), from_mm(y), 0))
        d = tf.OfVector(XYZ(math.cos(a), math.sin(a), 0))
        labels.append((text, size, (to_mm(p.X), to_mm(p.Y)), (d.X, d.Y)))
    if not labels:
        return [u"DỪNG: không có nhãn dạng 'bxh' trên layer chứa '{}'. Các layer chữ trong DWG:".format(
            label_filter)] + raw_layers

    level = find_level(level_name)
    opt = {"width_tol": WIDTH_TOL_MM, "label_tol": LABEL_TOL_MM, "join_tol": JOIN_TOL_MM,
           "merge_gap": MERGE_GAP_MM, "end_snap": END_SNAP_MM, "min_length": MIN_LENGTH_MM,
           "span_gap": span_gap_mm}
    beams, unmatched = find_beams([s for l, s in segments if l in edge_layers], labels, opt)

    # --- Type theo b × h
    symbols = beam_symbols()
    types, new_types = {}, {}
    used_names = set(get_name(s) for s in symbols)
    for s in symbols:
        types.setdefault((int(round(to_mm(s.LookupParameter(param_b).AsDouble()))),
                          int(round(to_mm(s.LookupParameter(param_h).AsDouble())))), s)

    # --- Dầm đã có trên level này: bỏ qua nếu cùng trục (song song, lệch ≤ DUP_TOL) và chồng chiều dài
    #     (chạy lại sau khi sửa script: đầu dầm có thể xê dịch vài chục mm nhưng vẫn là dầm cũ)
    existing = []
    for e in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_StructuralFraming) \
            .WhereElementIsNotElementType().ToElements():
        loc = e.Location
        ref = e.get_Parameter(BuiltInParameter.INSTANCE_REFERENCE_LEVEL_PARAM)
        if isinstance(loc, LocationCurve) and isinstance(loc.Curve, Line) and ref and ref.AsElementId() == level.Id:
            c = loc.Curve
            a, b = c.GetEndPoint(0), c.GetEndPoint(1)
            existing.append(((to_mm(a.X), to_mm(a.Y)), (to_mm(b.X), to_mm(b.Y)), e.Id.Value))

    def existing_dup(bm):
        n = bm.n
        for a, b, eid in existing:
            if math.hypot(b[0] - a[0], b[1] - a[1]) < 1.0:
                continue
            d = canonical(b[0] - a[0], b[1] - a[1])
            if abs(d[0] * bm.u[1] - d[1] * bm.u[0]) > ANGLE_TOL:
                continue
            if abs(a[0] * n[0] + a[1] * n[1] - bm.offset) > DUP_TOL_MM:
                continue
            s0, s1 = sorted((a[0] * bm.u[0] + a[1] * bm.u[1], b[0] * bm.u[0] + b[1] * bm.u[1]))
            # Chồng > 50% dầm ngắn hơn mới coi là trùng (nhịp liền kề chỉ chạm nhau ở nút thì không tính)
            if min(s1, bm.t1) - max(s0, bm.t0) > 0.5 * min(s1 - s0, bm.t1 - bm.t0):
                return eid
        return None

    z = level.Elevation
    rows, jobs = [], []
    for bm in sorted(beams, key=lambda x: (-x.point(x.t0)[1], x.point(x.t0)[0])):
        k = (bm.b, bm.h)
        if k in types:
            type_name = get_name(types[k])
        elif k in new_types:
            type_name = new_types[k]
        else:
            type_name = BEAM_TYPE_NAME.format(b=k[0], h=k[1])
            suffix = 1
            while type_name in used_names:
                type_name = BEAM_TYPE_NAME.format(b=k[0], h=k[1]) + u"_{}".format(suffix)
                suffix += 1
            used_names.add(type_name)
            new_types[k] = type_name
        p0, p1 = bm.point(bm.t0), bm.point(bm.t1)
        row = [bm.label, fmt(p0), fmt(p1), u"{:.0f}".format(bm.length),
               type_name + (u" (mới)" if k in new_types else u""), u"", u"", u"—", type_name]
        dup_id = existing_dup(bm)
        if dup_id is not None:
            row[5] = u"Bỏ qua – đã có dầm cùng trục"
            row[6] = dup_id
        else:
            row[5] = (u"Sẽ tạo" if dry_run else u"Chờ tạo") + (u" – " + bm.note if bm.note else u"")
            jobs.append((p0, p1, k, len(rows)))
        rows.append(row)
    for text, p, why in unmatched:
        rows.append([text, fmt(p), u"", u"", u"", u"Bỏ qua – " + why, u"", u"—", u"—"])

    # --- Ghi vào mô hình
    if not dry_run and jobs:
        # Đóng transaction của Dynamo để dùng Transaction có tên riêng (Undo được trong Revit)
        TransactionManager.Instance.ForceCloseTransaction()
        t = Transaction(doc, TRANSACTION_NAME)
        t.Start()
        try:
            for k, name in new_types.items():
                sym = symbols[0].Duplicate(name)
                sym.LookupParameter(param_b).Set(from_mm(k[0]))
                sym.LookupParameter(param_h).Set(from_mm(k[1]))
                types[k] = sym
            offset = from_mm(top_offset_mm)
            for p0, p1, k, idx in jobs:
                sym = types[k]
                if not sym.IsActive:
                    sym.Activate()
                    doc.Regenerate()
                curve = Line.CreateBound(XYZ(from_mm(p0[0]), from_mm(p0[1]), z), XYZ(from_mm(p1[0]), from_mm(p1[1]), z))
                inst = doc.Create.NewFamilyInstance(curve, sym, level, StructuralType.Beam)
                # Mặc định dự án có thể để y-justification = Right → ép Center (trục CAD là tim dầm), đỉnh dầm = Top
                inst.get_Parameter(BuiltInParameter.Y_JUSTIFICATION).Set(int(YJustification.Center))
                inst.get_Parameter(BuiltInParameter.Z_JUSTIFICATION).Set(int(ZJustification.Top))
                inst.get_Parameter(BuiltInParameter.STRUCTURAL_BEAM_END0_ELEVATION).Set(offset)
                inst.get_Parameter(BuiltInParameter.STRUCTURAL_BEAM_END1_ELEVATION).Set(offset)
                rows[idx][5] = u"Đã tạo"
                rows[idx][6] = inst.Id.Value
            t.Commit()
        except Exception as ex:
            if t.HasStarted() and not t.HasEnded():
                t.RollBack()
            return warnings + [u"LỖI khi tạo dầm, mọi thay đổi đã được hoàn tác: {}".format(ex)]

    summary = (u"{} – {}: {} nhãn tiết diện, {} dầm ({} nhịp nối theo nhãn), {} nhãn/dầm bỏ qua. "
               u"Nối nhịp qua cột: {}. Level {} {:+.0f} mm. Type mới: {}.").format(
        TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN",
        len(labels), len(beams), sum(1 for bm in beams if bm.note.startswith(u"nhịp")), len(unmatched),
        u"khe ≤ {:.0f} mm".format(span_gap_mm) if span_gap_mm > 0 else u"tắt", level.Name, top_offset_mm,
        u", ".join(sorted(new_types.values())) or u"không có")
    try:
        log_line = u"Log: " + write_log(rows, cad_name)
    except Exception as ex:
        log_line = u"Không ghi được file log: {}".format(ex)
    return warnings + [summary, u"Layer cạnh dầm: " + u"; ".join(sorted(edge_layers)), log_line] \
        + [u" | ".join(u"{}".format(v) for v in r[:7]) for r in rows]


if DYNAMO:
    try:
        OUT = main()
    except Exception as ex:
        OUT = [u"LỖI: {}".format(ex)]
