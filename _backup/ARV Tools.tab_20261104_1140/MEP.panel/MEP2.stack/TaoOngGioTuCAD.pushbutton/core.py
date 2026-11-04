# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong ARV_TaoOngGioTuCAD_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Tạo ống gió chữ nhật (Duct) từ mặt bằng thông gió (DWG đã Link vào Revit).
#   Đọc từ BẢN SAO DWG qua AutoCAD Core Console (chữ trong bản link Revit không đọc được):
#   - Nổ (explode) mọi block trên bản sao; nét ở layer 0 trong block nhận layer của block cha (như AutoCAD
#     hiển thị); toạ độ LWPOLYLINE đổi OCS → WCS (block mirror).
#   - Ống: thành ống là cặp nét thẳng song song trên layer IN[1] (LINE / cạnh thẳng LWPOLYLINE). Đoạn thẳng
#     hàng nối nhau qua mặt bích (khe ≤ 60 mm) được gộp. Mỗi thành ống ghép với nét song song gần nhất theo
#     từng khoảng dọc tuyến → tim ống + bề rộng W.
#   - Lọc: ống thật phải có ≥ 1 vạch ngang (mặt bích / đầu ống) dài ≈ W nối hai thành; cặp có tim nằm trong
#     ống dài hơn (cặp vạch mặt bích, nét trong quạt / van) bị loại.
#   - Phụ kiện (theo Routing Preferences của duct type): ghép cặp đầu ống cùng layer, gần nhất trước –
#     thẳng hàng khe ≤ 3 m (chỗ van / đổi tiết diện) → nối liền, cùng cỡ đặt bích, khác cỡ đặt côn (lệch tâm
#     ≤ |ΔW|/2 + 30 mm); trục giao nhau → cút; 2 đầu thẳng hàng + 1 đầu vuông góc → tê (không được thì nối
#     thẳng ống chính + chân rẽ); đầu ống đâm vào thân ống khác → chân rẽ. Khác cao độ → đầu ống cao hơn
#     (nhánh với tê) hạ bằng đoạn dốc ≈ 45° + 2 cút. Mỗi mối nối một SubTransaction; lỗi → hoàn tác, ghi log.
#   - Kích thước + cao độ: chữ "WxH ... BOD: FL+2.300" trên layer IN[3]; gán cho ống gần nhất có cạnh khớp W
#     (±15 mm, ≤ 6 m); ống chưa có chữ nhận theo ống cùng layer, cùng W nối liền (qua cút/côn); tuyến dài
#     ≥ 3 m tìm chữ trong 15 m. Bỏ chữ của thiết bị (SAG, EAG, PAG, OBD, MFD, PRD, TA, NRD…).
#     Ống không có chữ / không có BOD → không dựng, ghi log để vẽ tay.
#   - Cao độ: đáy ống = Level IN[4] + BOD + IN[6]; tâm ống = đáy + H/2.
# INPUT
#   IN[0] (str)   Một phần tên bản CAD (trống = bản CAD duy nhất)
#   IN[1] (str)   Layer ống gió, cách ';' (khớp đúng tên)
#   IN[2] (str)   System theo chuỗi con trong tên layer: "HUT KHOI=AV_M_Hút khói;TANG AP=AV_M_Tăng áp;..."
#   IN[3] (str)   Layer chữ kích thước ống (cách ';'; trống = mọi layer)
#   IN[4] (str)   Level gốc FL (trống = level của view đang mở)
#   IN[5] (str)   Tên Duct type chữ nhật (Rectangular Duct)
#   IN[6] (float) Cộng thêm vào cao độ đáy ống (mm), mặc định 0
#   IN[7] (bool)  Xoá ống + phụ kiện 'ARV-OG' của lần chạy trước rồi dựng lại (mặc định False)
#   IN[8] (bool)  Dry-run: True = chỉ báo cáo (mặc định True)
# OUTPUT
#   OUT (list[str]) Báo cáo: tóm tắt, ống không dựng (toạ độ DWG), đường dẫn log CSV.

import os
import io
import re
import sys
import csv
import glob
import math
import shutil
import tempfile
import datetime
import unicodedata
import subprocess
import collections

DYNAMO = "IN" in globals()

if DYNAMO:
    import clr
    clr.AddReference("RevitAPI")
    from Autodesk.Revit.DB import (FilteredElementCollector, ImportInstance, CADLinkType, XYZ, Transaction,
                                   SubTransaction, ModelPathUtils, BuiltInParameter, BuiltInCategory, Level, Line,
                                   ElementId, ConnectorProfileType)
    from Autodesk.Revit.DB.Mechanical import Duct, DuctType, MechanicalSystemType
    from System.Collections.Generic import List
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager

    doc = DocumentManager.Instance.CurrentDBDocument
    uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument

TRANSACTION_NAME = u"ARV - Tạo ống gió từ CAD"
COMMENT = u"ARV-OG"
ANG = math.radians(0.5)  # dung sai song song
COL = 3.0                # mm, dung sai thẳng hàng khi gộp nét
GAP = 60.0               # mm, khe cho phép khi nối nét thẳng hàng (mặt bích)
MINW, MAXW = 90.0, 6000.0
MIN_RUN = 150.0          # mm, đoạn chồng tối thiểu khi ghép cặp
MIN_DUCT = 200.0         # mm, ống ngắn hơn bỏ qua
TAG_R1, TAG_R2, LONG_RUN = 6000.0, 15000.0, 3000.0
MAX_VERT = 60            # polyline nhiều đỉnh hơn = ký hiệu ống mềm / tiêu âm, bỏ
JOIN_GAP = 3000.0        # mm, khe tối đa nối liền 2 ống thẳng hàng (chỗ van / thiết bị)
CORE_TIMEOUT_S = 300
EQUIP = re.compile(r"(SAG|SEAG|EAG|PAG|OBD|MFD|MPD|PRD|VCD|NRD|\bFD\b|\bTA\b|LOUVER|FAN|AHU|FCU|PAU)", re.I)
SIZE = re.compile(r"(?<![xX\d])(\d{2,4})\s*[xX×]\s*(\d{2,4})(?!\s*[xX×]\s*\d)")
BOD = re.compile(r"FL\s*([+-])\s*(\d+(?:[.,]\d+)?)", re.I)
FIRE = re.compile(r"\bE?I\s*(\d{2,3})\b")


# =====================================================================================
# PHẦN NHẬN DẠNG ỐNG – chỉ dùng tuple (x, y) theo mm, toạ độ DWG (chạy thử được ngoài Dynamo)
# =====================================================================================
def canon(a, b):
    """Đường thẳng qua a, b: (góc [0, π), offset vuông góc, t0, t1) theo trục chuẩn hoá."""
    th = math.atan2(b[1] - a[1], b[0] - a[0]) % math.pi
    if th > math.pi - ANG / 2:
        th -= math.pi
    ux, uy = math.cos(th), math.sin(th)
    off = -a[0] * uy + a[1] * ux
    t0, t1 = sorted((a[0] * ux + a[1] * uy, b[0] * ux + b[1] * uy))
    return th, off, t0, t1


def merge_lines(segs):
    """Gộp các đoạn cùng đường thẳng, chồng nhau / khe ≤ GAP."""
    c = sorted((canon(a, b) for a, b in segs), key=lambda x: (round(x[0] / ANG), x[1], x[2]))
    out = []
    for th, off, t0, t1 in c:
        for o in out[::-1][:40]:
            if abs(o[0] - th) < ANG and abs(o[1] - off) < COL and t0 <= o[3] + GAP and t1 >= o[2] - GAP:
                o[2] = min(o[2], t0)
                o[3] = max(o[3], t1)
                break
        else:
            out.append([th, off, t0, t1])
    return out


def seg_dist(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / (dx * dx + dy * dy or 1.0)))
    return math.hypot(px - a[0] - t * dx, py - a[1] - t * dy)


def point_on(th, t, off):
    ux, uy = math.cos(th), math.sin(th)
    return (t * ux - off * uy, t * uy + off * ux)


def pair_sides(lines, layer):
    """Mỗi đường: theo từng khoảng dọc tuyến, ghép với đường song song gần nhất phía trên (offset lớn hơn)."""
    long_ = [l for l in lines if l[3] - l[2] > MIN_RUN]
    byth = collections.defaultdict(list)
    for i, l in enumerate(long_):
        byth[round(l[0] / ANG)].append(i)
    res = []
    for i, (th, off, t0, t1) in enumerate(long_):
        cands = []
        k0 = round(th / ANG)
        for k in (k0 - 1, k0, k0 + 1):
            for j in byth.get(k, ()):
                m = long_[j]
                if j == i or abs(m[0] - th) > ANG:
                    continue
                d = m[1] - off
                if not (MINW <= d <= MAXW):
                    continue
                lo, hi = max(t0, m[2]), min(t1, m[3])
                if hi - lo >= MIN_RUN:
                    cands.append((d, lo, hi))
        covered = []
        for d, lo, hi in sorted(cands):
            free = [(lo, hi)]
            for c0, c1 in covered:
                nf = []
                for f0, f1 in free:
                    if c1 <= f0 or c0 >= f1:
                        nf.append((f0, f1))
                        continue
                    if f0 < c0:
                        nf.append((f0, c0))
                    if c1 < f1:
                        nf.append((c1, f1))
                free = nf
            covered.append((lo, hi))
            for f0, f1 in free:
                if f1 - f0 >= MIN_RUN:
                    res.append((th, off + d / 2.0, f0, f1, d))
    # gộp tim thẳng hàng cùng W
    res.sort(key=lambda x: (round(x[0] / ANG), round(x[4]), x[1], x[2]))
    out = []
    for th, off, t0, t1, W in res:
        for o in out[::-1][:60]:
            if abs(o[0] - th) < ANG and abs(o[1] - off) < 5 and abs(o[4] - W) < 5 and t0 <= o[3] + GAP and t1 >= o[2] - GAP:
                o[2] = min(o[2], t0)
                o[3] = max(o[3], t1)
                break
        else:
            out.append([th, off, t0, t1, W])
    return [{"layer": layer, "th": th, "p1": point_on(th, t0, off), "p2": point_on(th, t1, off),
             "W": W, "len": t1 - t0} for th, off, t0, t1, W in out]


def inside_rect(px, py, d, pad):
    ux, uy = math.cos(d["th"]), math.sin(d["th"])
    vx, vy = px - d["p1"][0], py - d["p1"][1]
    t = vx * ux + vy * uy
    n = -vx * uy + vy * ux
    return -pad <= t <= d["len"] + pad and abs(n) <= d["W"] / 2.0 + pad


def filter_ducts(ducts, segs, log):
    """Giữ ống có vạch ngang ≈ W nối 2 thành; bỏ ống có tim nằm trong ống dài hơn."""
    CELL = 2000.0
    grid = collections.defaultdict(list)
    for a, b in segs:
        m = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        grid[(int(m[0] // CELL), int(m[1] // CELL))].append((a, b, m))

    def crosses(d):
        ux, uy = math.cos(d["th"]), math.sin(d["th"])
        x0, x1 = sorted((d["p1"][0], d["p2"][0]))
        y0, y1 = sorted((d["p1"][1], d["p2"][1]))
        n = 0
        for i in range(int((x0 - d["W"]) // CELL), int((x1 + d["W"]) // CELL) + 1):
            for j in range(int((y0 - d["W"]) // CELL), int((y1 + d["W"]) // CELL) + 1):
                for a, b, m in grid.get((i, j), ()):
                    vx, vy = b[0] - a[0], b[1] - a[1]
                    ln = math.hypot(vx, vy)
                    if abs(vx * ux + vy * uy) > 0.02 * ln or not (d["W"] - 40 <= ln <= d["W"] + 120):
                        continue
                    px, py = m[0] - d["p1"][0], m[1] - d["p1"][1]
                    t = px * ux + py * uy
                    if abs(-px * uy + py * ux) < 0.1 * d["W"] + 15 and -5 <= t <= d["len"] + 5:
                        n += 1
        return n
    keep = []
    for d in ducts:
        if d["len"] < MIN_DUCT:
            log[u"loại: ống ngắn < {:.0f} mm".format(MIN_DUCT)] += 1
        elif crosses(d) == 0:
            log[u"loại: cặp nét không có vạch ngang (khe giữa 2 ống, vạch bích…)"] += 1
        else:
            keep.append(d)
    keep.sort(key=lambda d: -d["len"])
    final = []
    for d in keep:
        mx, my = (d["p1"][0] + d["p2"][0]) / 2.0, (d["p1"][1] + d["p2"][1]) / 2.0
        if any(inside_rect(mx, my, s, -5) for s in final):
            log[u"loại: tim nằm trong ống khác (vạch bích, nét quạt/van)"] += 1
        else:
            final.append(d)
    return final


def parse_tag(s):
    if EQUIP.search(s):
        return None
    m = SIZE.search(s)
    if not m:
        return None
    b = BOD.search(s[m.end():]) or BOD.search(s)
    bod = None
    if b:
        bod = float(b.group(2).replace(",", ".")) * 1000.0 * (-1 if b.group(1) == "-" else 1)
    fire = FIRE.search(s)
    return {"W": int(m.group(1)), "H": int(m.group(2)), "bod": bod, "fire": u"EI" + fire.group(1) if fire else u""}


def assign_tags(ducts, tags, radius, minlen, src):
    for d in ducts:
        if d.get("tag") or d["len"] < minlen:
            continue
        best = None
        for t in tags:
            dist = seg_dist(t["x"], t["y"], d["p1"], d["p2"])
            if abs(t["W"] - d["W"]) <= 15:
                c = (dist, t, t["W"], t["H"])
            elif abs(t["H"] - d["W"]) <= 15 and dist < 2000 and d["len"] >= 1000:   # ghi "400x600", vẽ cạnh 600
                c = (dist + 500, t, t["H"], t["W"])
            else:
                continue
            if best is None or c[0] < best[0]:
                best = c
        if best and best[0] < radius:
            dist, t, w, h = best
            d.update(tag=t["s"], Wt=w, Ht=h, bod=t["bod"], fire=t["fire"], src=src,
                     tagxy=(t["x"], t["y"]), tagdist=dist)


def ends(d):
    return (d["p1"], d["p2"])


def gap(d, s):
    return min(math.hypot(a[0] - b[0], a[1] - b[1]) for a in ends(d) for b in ends(s))


def inherit(ducts):
    changed = True
    while changed:
        changed = False
        for d in ducts:
            if d.get("tag"):
                continue
            best = None
            for s in ducts:
                if s is d or not s.get("tag") or s["layer"] != d["layer"] or abs(s["W"] - d["W"]) > 15:
                    continue
                g = gap(d, s)
                if g < max(2.5 * d["W"], 2000.0) and (best is None or g < best[0]):
                    best = (g, s)
            if best:
                s = best[1]
                d.update(tag=s["tag"], Wt=s["Wt"], Ht=s["Ht"], bod=s["bod"], fire=s["fire"],
                         src=u"kế thừa ống nối", tagxy=s.get("tagxy"))
                changed = True
    for d in ducts:   # chữ không ghi BOD → lấy theo ống nối liền cùng layer
        if d.get("tag") and d["bod"] is None:
            nb = [s for s in ducts if s.get("tag") and s["bod"] is not None and s["layer"] == d["layer"] and gap(d, s) < 3000]
            if nb:
                d["bod"] = min(nb, key=lambda s: gap(d, s))["bod"]
                d["src"] += u" + BOD ống nối"


def find_ducts(ents, layers, text_layers):
    """ents: dict segs[(layer,a,b)], texts[(layer,(x,y),text)]. Trả về (ducts, log, tags)."""
    log = collections.Counter()
    segs = collections.defaultdict(list)
    for lay, a, b in ents["segs"]:
        if lay in layers and math.hypot(b[0] - a[0], b[1] - a[1]) > 1:
            segs[lay].append((a, b))
    tags = []
    for lay, p, s in ents["texts"]:
        if text_layers and lay not in text_layers:
            continue
        t = parse_tag(s)
        if t:
            t.update(x=p[0], y=p[1], s=s)
            tags.append(t)
    log[u"chữ kích thước ống"] = len(tags)
    ducts = []
    for lay in layers:
        cand = pair_sides(merge_lines(segs[lay]), lay)
        ducts += filter_ducts(cand, segs[lay], log)
    for d in ducts:
        d["tag"] = None
    assign_tags(ducts, tags, TAG_R1, 0, u"chữ gần")
    inherit(ducts)
    assign_tags(ducts, tags, TAG_R2, LONG_RUN, u"chữ xa (tuyến dài)")
    inherit(ducts)
    return ducts, log, tags


def unit2(a, b):
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    return ((b[0] - a[0]) / L, (b[1] - a[1]) / L)


def plan_joints(B):
    """B: ống sẽ dựng (có Wt, Ht, bod). Ghép cặp đầu ống cùng layer → mối nối.
    kind: 'thang' (thẳng hàng: bích / côn), 'cut' (cút), 'te' (đầu ống đâm vào thân ống khác).
    Mỗi đầu ống dùng một lần, ưu tiên cặp gần nhất. Trả về (joints, đầu ống hở)."""
    E = []
    for i, d in enumerate(B):
        for k in (0, 1):
            P, Q = (d["p1"], d["p2"]) if k == 0 else (d["p2"], d["p1"])
            E.append({"i": i, "k": k, "P": P, "u": unit2(Q, P)})   # u: hướng ra khỏi ống
    cands = []
    for x, a in enumerate(E):
        da = B[a["i"]]
        for y in range(x + 1, len(E)):
            b = E[y]
            db = B[b["i"]]
            if a["i"] == b["i"] or da["layer"] != db["layer"]:
                continue
            ua, ub = a["u"], b["u"]
            cr = ua[0] * ub[1] - ua[1] * ub[0]
            vx, vy = b["P"][0] - a["P"][0], b["P"][1] - a["P"][1]
            if abs(cr) < 0.01:      # song song
                if ua[0] * ub[0] + ua[1] * ub[1] > -0.99:
                    continue
                along = vx * ua[0] + vy * ua[1]
                lat = abs(vx * ua[1] - vy * ua[0])
                if 0 <= along <= JOIN_GAP and lat <= max(20.0, abs(da["Wt"] - db["Wt"]) / 2.0 + 30):   # côn lệch 1 phía
                    P = ((a["P"][0] + b["P"][0]) / 2.0, (a["P"][1] + b["P"][1]) / 2.0)
                    cands.append((along, "thang", x, y, P))
            else:                   # giao trục → cút
                t = (vx * ub[1] - vy * ub[0]) / cr
                s = (vx * ua[1] - vy * ua[0]) / cr
                lim = 2.0 * max(da["Wt"], db["Wt"]) + 500      # chân cút sát; chân kia được thêm khe van
                ang = math.degrees(math.acos(max(-1.0, min(1.0, -(ua[0] * ub[0] + ua[1] * ub[1])))))
                if -10 <= t and -10 <= s and min(t, s) <= lim and max(t, s) <= lim + JOIN_GAP and 30 <= ang <= 150:
                    P = (a["P"][0] + t * ua[0], a["P"][1] + t * ua[1])
                    cands.append((t + s, "cut", x, y, P))
    for x, a in enumerate(E):       # tê: đầu ống đâm vào thân ống khác
        da = B[a["i"]]
        for j, m in enumerate(B):
            if j == a["i"] or m["layer"] != da["layer"]:
                continue
            um = unit2(m["p1"], m["p2"])
            t = (a["P"][0] - m["p1"][0]) * um[0] + (a["P"][1] - m["p1"][1]) * um[1]
            if not (da["Wt"] / 2.0 + 100 <= t <= m["len"] - da["Wt"] / 2.0 - 100):
                continue
            q = (m["p1"][0] + t * um[0], m["p1"][1] + t * um[1])
            dist = math.hypot(q[0] - a["P"][0], q[1] - a["P"][1])
            if dist <= m["Wt"] / 2.0 + 1000 and dist > 1 and \
                    ((q[0] - a["P"][0]) * a["u"][0] + (q[1] - a["P"][1]) * a["u"][1]) / dist > 0.95:
                cands.append((dist + 10000.0, "te", x, j, q))
    # tê 3 nhánh: 2 đầu thẳng hàng đối nhau + 1 đầu vuông góc chĩa vào khe giữa (ưu tiên trước cút)
    used, joints = set(), []
    for cost, kind, x, y, P in sorted([c for c in cands if c[1] == "thang"], key=lambda c: c[0]):
        if x in used or y in used:
            continue
        a, b = E[x], E[y]
        da = B[a["i"]]
        best = None
        for z, c in enumerate(E):
            if z in used or z in (x, y) or c["i"] in (a["i"], b["i"]) or B[c["i"]]["layer"] != da["layer"]:
                continue
            if abs(c["u"][0] * a["u"][0] + c["u"][1] * a["u"][1]) > 0.1:     # nhánh vuông góc
                continue
            # điểm Q trên trục chính mà nhánh chĩa tới
            vx, vy = c["P"][0] - a["P"][0], c["P"][1] - a["P"][1]
            tq = vx * a["u"][0] + vy * a["u"][1]
            Q = (a["P"][0] + tq * a["u"][0], a["P"][1] + tq * a["u"][1])
            dq = math.hypot(Q[0] - c["P"][0], Q[1] - c["P"][1])
            if not (-50 <= tq <= cost + 50) or dq > da["Wt"] / 2.0 + 1500:
                continue
            inside = dq <= max(da["Wt"], B[b["i"]]["Wt"]) / 2.0 + 20      # đầu nhánh thò vào lòng ống chính
            if not inside and ((Q[0] - c["P"][0]) * c["u"][0] + (Q[1] - c["P"][1]) * c["u"][1]) / dq < 0.95:
                continue
            if best is None or dq < best[0]:
                best = (dq, z, Q)
        if best:
            dq, z, Q = best
            used.update((x, y, z))
            joints.append({"kind": "te3", "a": (a["i"], a["k"]), "b": (b["i"], b["k"]),
                           "c": (E[z]["i"], E[z]["k"]), "P": Q, "gap": cost})
    for cost, kind, x, y, P in sorted(cands, key=lambda c: c[0]):
        if x in used or (kind != "te" and y in used):
            continue
        used.add(x)
        a = E[x]
        j = {"kind": kind, "a": (a["i"], a["k"]), "P": P, "gap": cost - (10000.0 if kind == "te" else 0)}
        if kind == "te":
            j["main"] = y
        else:
            used.add(y)
            j["b"] = (E[y]["i"], E[y]["k"])
        joints.append(j)
    open_ends = [(B[e["i"]], e["P"]) for x, e in enumerate(E) if x not in used]
    return joints, open_ends


def zc(d):
    """Cao độ tâm ống so với FL (mm)."""
    return d["bod"] + d["Ht"] / 2.0


# =====================================================================================
# ĐỌC DWG QUA CORE CONSOLE (bản sao)
# =====================================================================================
# Nổ mọi block (layer 0 nhận layer block cha), rồi xuất LINE / LWPOLYLINE (WCS, bulge) / TEXT / MTEXT.
# Core Console không có ActiveX → AutoLISP thuần (EXPLODE từng block, entmod layer).
DUMP_LISP = u"""(setvar "CMDECHO" 0)
(command "_.-LAYER" "_UNLOCK" "*" "_THAW" "*" "")
(setq _bad nil _n 0 _go T)
(while (and _go (< _n 15))
  (setq _go nil _n (1+ _n) _ss (ssget "_X" '((0 . "INSERT") (410 . "Model"))) _i 0)
  (if _ss
    (repeat (sslength _ss)
      (setq _en (ssname _ss _i) _i (1+ _i) _h (cdr (assoc 5 (entget _en))))
      (if (not (member _h _bad))
        (progn
          (setq _la (cdr (assoc 8 (entget _en))) _last (entlast))
          (command "_.EXPLODE" _en "")
          (if (or (eq _last (entlast)) (entget _en))
            (setq _bad (cons _h _bad))
            (progn
              (setq _go T _e (entnext _last))
              (while _e
                (setq _d (entget _e))
                (if (= (strcase (cdr (assoc 8 _d))) "0") (entmod (subst (cons 8 _la) (assoc 8 _d) _d)))
                (setq _e (entnext _e))))))))))
(setq f (open "{out}" "w" "utf8"))
(defun _p (p) (strcat (rtos (car p) 2 3) "," (rtos (cadr p) 2 3)))
(setq _ss (ssget "_X" '((0 . "LINE,LWPOLYLINE,TEXT,MTEXT") (410 . "Model"))) _i 0)
(if _ss (repeat (sslength _ss)
  (setq e (ssname _ss _i) _i (1+ _i) d (entget e) ty (cdr (assoc 0 d)) la (cdr (assoc 8 d)))
  (cond
    ((= ty "LINE") (write-line (strcat "L|" la "|" (_p (cdr (assoc 10 d))) "|" (_p (cdr (assoc 11 d)))) f))
    ((= ty "LWPOLYLINE")
      (setq z (cdr (assoc 38 d)) vs nil bs nil)
      (if (null z) (setq z 0.0))
      (foreach g d (cond ((= (car g) 10) (setq vs (cons (list (cadr g) (caddr g) z) vs))) ((= (car g) 42) (setq bs (cons (cdr g) bs)))))
      (setq vs (reverse vs) bs (reverse bs) i 0)
      (if (<= (length vs) {maxv})
        (progn
          (setq s (strcat "P|" la "|" (if (= 1 (logand 1 (cdr (assoc 70 d)))) "1" "0") "|"))
          (foreach v vs (setq s (strcat s (_p (trans v e 0)) "," (rtos (if (nth i bs) (nth i bs) 0.0) 2 6) ";") i (1+ i)))
          (write-line s f))))
    ((= ty "MTEXT")
      (setq s "")
      (foreach g d (if (= (car g) 3) (setq s (strcat s (cdr g)))))
      (write-line (strcat "T|" la "|" (_p (cdr (assoc 10 d))) "|" s (cdr (assoc 1 d))) f))
    ((= ty "TEXT") (write-line (strcat "T|" la "|" (_p (trans (cdr (assoc 10 d)) e 0)) "|" (cdr (assoc 1 d))) f)))))
(close f)
"""


def find_accoreconsole():
    found = glob.glob(r"C:\Program Files\Autodesk\AutoCAD *\accoreconsole.exe")
    return sorted(found)[-1] if found else None


def core_env(core):
    """Môi trường sạch cho AutoCAD Core Console (Path của Revit làm Core Console nạp nhầm DLL)."""
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
    s = re.sub(r"\\[Pp~]", " ", s)
    s = re.sub(r"\\S([^;^#/]*)[\^#/]([^;]*);", r"\1/\2", s)
    s = re.sub(r"\\[A-Za-z][^;\\{}]*;", "", s)
    s = re.sub(r"\\[LlOoKk]", "", s)
    return u" ".join(s.replace("{", "").replace("}", "").split())


def parse_dump(text):
    ents = {"segs": [], "texts": []}

    def pt(s):
        x, y = s.split(",")[:2]
        return (float(x), float(y))
    for line in text.splitlines():
        parts = line.split("|")
        try:
            if parts[0] == "L":
                ents["segs"].append((parts[1], pt(parts[2]), pt(parts[3])))
            elif parts[0] == "P":
                vs = []
                for v in parts[3].split(";"):
                    if v:
                        x, y, b = v.split(",")
                        vs.append(((float(x), float(y)), float(b)))
                if parts[2] == "1" and vs:
                    vs.append((vs[0][0], 0.0))
                for i in range(len(vs) - 1):
                    if abs(vs[i][1]) < 1e-6:        # cạnh cung (bulge) thuộc cút cong → bỏ
                        ents["segs"].append((parts[1], vs[i][0], vs[i + 1][0]))
            elif parts[0] == "T":
                ents["texts"].append((parts[1], pt(parts[2]), clean_mtext(u"|".join(parts[3:]))))
        except (ValueError, IndexError):
            continue
    return ents


def read_dwg(dwg_path, core):
    """Thực thể DWG (toạ độ DWG, mm). Chạy trên bản sao trong thư mục tạm – không mở file gốc."""
    work = tempfile.mkdtemp(prefix="ARV_OG_")
    try:
        copy = os.path.join(work, "copy.dwg")
        shutil.copy2(dwg_path, copy)
        out = os.path.join(work, "ents.txt")
        scr = os.path.join(work, "dump.scr")
        with io.open(scr, "w", encoding="utf-8") as f:
            f.write(DUMP_LISP.replace("{out}", out.replace("\\", "/")).replace("{maxv}", str(MAX_VERT)))
        subprocess.run([core, "/i", copy, "/s", scr, "/l", "en-US"], stdin=subprocess.DEVNULL,
                       env=core_env(core), cwd=os.path.dirname(core),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=CORE_TIMEOUT_S, creationflags=0x08000000)
        if not os.path.isfile(out):
            raise Exception(u"Core Console không xuất được dữ liệu DWG")
        return parse_dump(io.open(out, "r", encoding="utf-8-sig", errors="replace").read())
    finally:
        shutil.rmtree(work, ignore_errors=True)


def fmt(p):
    return u"({:.0f}, {:.0f})".format(p[0], p[1])


def short(layer):
    return layer.replace(u"AV-M-TG-", u"")


# =====================================================================================
# PHẦN REVIT
# =====================================================================================
def parse_map(s):
    out = []
    for part in (s or u"").split(u";"):
        if u"=" in part:
            k, v = part.split(u"=", 1)
            out.append((k.strip(), v.strip()))
    return out


def get_name(e):
    try:
        return e.Name
    except Exception:
        p = e.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
        return p.AsString() if p else u""


def is_central_file(document):
    if not document.IsWorkshared:
        return False
    try:
        central = ModelPathUtils.ConvertModelPathToUserVisiblePath(document.GetWorksharingCentralModelPath())
    except Exception:
        return False
    return os.path.normcase(central or "") == os.path.normcase(document.PathName or "")


def pick_cad(cad_filter):
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


def write_log(rows, source, dry_run):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoOngGioTuCAD_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(u"# Dự án: {}\n# Bản CAD: {}\n# Ngày xuất: {}\n# Chế độ: {}\n# Đơn vị: mm, toạ độ theo DWG\n".format(
            doc.Title, source, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            u"Chạy thử (dry-run)" if dry_run else u"Thực hiện"))
        w = csv.writer(f)
        w.writerow([u"Kết quả", u"Layer", u"Đầu 1 (DWG)", u"Đầu 2 (DWG)", u"Dài (mm)", u"W đo (mm)",
                    u"W×H", u"BOD (mm)", u"Nguồn kích thước", u"Chữ", u"Lý do / Id"])
        w.writerows(rows)
    return path


JOINT_NAME = {"thang": u"nối thẳng (bích / côn)", "cut": u"cút", "te3": u"tê 3 nhánh", "te": u"chân rẽ"}


class Fitter(object):
    """Nối phụ kiện giữa các ống đã dựng (Transaction đang mở). Mỗi mối nối một SubTransaction:
    lỗi / ống bị lẹm, đổi chiều → hoàn tác mối nối đó, trả lý do. Phụ kiện lấy theo Routing Preferences."""

    def __init__(self, B, made, tf, dtype, level):
        self.B, self.made, self.tf, self.dtype, self.level = B, made, tf, dtype, level
        self.ft = 1.0 / 304.8
        self.min_len = 50.0 * self.ft
        self.ramps = 0
        self.dirs = {}
        for i, du in made.items():   # hướng ra ngoài của đầu k (mặt bằng, toạ độ Revit)
            a = tf.OfPoint(XYZ(B[i]["p1"][0] * self.ft, B[i]["p1"][1] * self.ft, 0))
            b = tf.OfPoint(XYZ(B[i]["p2"][0] * self.ft, B[i]["p2"][1] * self.ft, 0))
            u = b.Subtract(a).Normalize()
            self.dirs[i] = {0: u.Negate(), 1: u}

    def pt(self, p, z):
        q = self.tf.OfPoint(XYZ(p[0] * self.ft, p[1] * self.ft, 0))
        return XYZ(q.X, q.Y, z)

    @staticmethod
    def curve(duct):
        return duct.Location.Curve

    def side(self, h):
        c = self.curve(h[0])
        return 0 if c.GetEndPoint(0).Subtract(c.GetEndPoint(1)).DotProduct(h[1]) > 0 else 1

    def end(self, h):
        return self.curve(h[0]).GetEndPoint(self.side(h))

    def far(self, h):
        return self.curve(h[0]).GetEndPoint(1 - self.side(h))

    def set_end(self, h, P):
        k = self.side(h)
        c = self.curve(h[0])
        e = [c.GetEndPoint(0), c.GetEndPoint(1)]
        e[k] = P
        h[0].Location.Curve = Line.CreateBound(e[0], e[1])

    @staticmethod
    def con(duct, P):
        return min(list(duct.ConnectorManager.Connectors), key=lambda c: c.Origin.DistanceTo(P))

    def tag(self, fi, note):
        try:
            fi.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set(u"{} | {}".format(COMMENT, note))
        except Exception:
            pass
        return fi

    def new_duct(self, like, a, b, note):
        d = Duct.Create(doc, like.get_Parameter(BuiltInParameter.RBS_DUCT_SYSTEM_TYPE_PARAM).AsElementId(),
                        self.dtype.Id, self.level.Id, a, b)
        d.get_Parameter(BuiltInParameter.RBS_CURVE_WIDTH_PARAM).Set(like.Width)
        d.get_Parameter(BuiltInParameter.RBS_CURVE_HEIGHT_PARAM).Set(like.Height)
        c = like.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).AsString() or COMMENT
        d.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set(c + u" | " + note)
        return d

    def ramp(self, h, zt, P):
        """Đổi cao độ ở đầu ống h: rút ống, thêm đoạn dốc (≈ 45°) + đoạn ngang ở cao độ zt tới điểm nối P.
        Trả handle mới (đoạn ngang) thay cho h."""
        duct, u = h
        E = self.end(h)
        z = E.Z
        c = max(duct.Width, duct.Height) + 200.0 * self.ft          # chỗ cho cút đứng + phụ kiện mặt bằng
        Lr = max(abs(zt - z), duct.Height, 300.0 * self.ft)         # hình chiếu đoạn dốc
        P2 = XYZ(P.X - u.X * c, P.Y - u.Y * c, zt)
        S = XYZ(P2.X - u.X * Lr, P2.Y - u.Y * Lr, z)
        if S.Subtract(self.far(h)).DotProduct(u) < 300.0 * self.ft:
            raise Exception(u"ống quá ngắn để chuyển cao độ")
        self.set_end(h, S)
        r = self.new_duct(duct, S, P2, u"chuyển cao độ")
        pc = self.new_duct(duct, P2, XYZ(P.X, P.Y, zt), u"chuyển cao độ")
        doc.Regenerate()
        self.tag(doc.Create.NewElbowFitting(self.con(duct, S), self.con(r, S)), u"cút chuyển cao độ")
        self.tag(doc.Create.NewElbowFitting(self.con(r, P2), self.con(pc, P2)), u"cút chuyển cao độ")
        self.ramps += 1
        return (pc, u), [r, pc]

    def pair(self, ha, hb, P, note):
        """Nối 2 đầu ống đối nhau tại P: cùng cỡ → bích (union), khác cỡ → côn."""
        self.set_end(ha, P)
        self.set_end(hb, P)
        doc.Regenerate()
        ca, cb = self.con(ha[0], P), self.con(hb[0], P)
        same = abs(ha[0].Width - hb[0].Width) < 1e-6 and abs(ha[0].Height - hb[0].Height) < 1e-6
        if same:
            return self.tag(doc.Create.NewUnionFitting(ca, cb), u"bích " + note)
        return self.tag(doc.Create.NewTransitionFitting(ca, cb), u"côn " + note)

    def joint(self, j):
        kind = j["kind"]
        keys = [j[k] for k in ("a", "b", "c") if k in j]
        if any(i not in self.made for i, k in keys) or ("main" in j and j["main"] not in self.made):
            return u"thiếu ống (ống không dựng được)"
        H = dict((k, (self.made[j[k][0]], self.dirs[j[k][0]][j[k][1]])) for k in ("a", "b", "c") if k in j)
        watch = [h[0] for h in H.values()] + ([self.made[j["main"]]] if "main" in j else [])
        d0 = [self.curve(w).Direction for w in watch]
        st = SubTransaction(doc)
        st.Start()
        why, extra = None, []
        try:
            if kind in ("thang", "cut"):
                za, zb = self.end(H["a"]).Z, self.end(H["b"]).Z
                zt = min(za, zb)
                if abs(za - zb) > 5 * self.ft:      # đổi cao độ ở đầu ống cao hơn
                    k = "a" if za > zb else "b"
                    H[k], new = self.ramp(H[k], zt, self.pt(j["P"], zt))
                    extra += new
                P = self.pt(j["P"], zt)
                if kind == "cut":
                    self.set_end(H["a"], P)
                    self.set_end(H["b"], P)
                    doc.Regenerate()
                    self.tag(doc.Create.NewElbowFitting(self.con(H["a"][0], P), self.con(H["b"][0], P)), u"cút")
                else:
                    self.pair(H["a"], H["b"], P, u"")
            elif kind == "te3":
                za, zb = self.end(H["a"]).Z, self.end(H["b"]).Z
                if abs(za - zb) > 5 * self.ft:
                    raise Exception(u"2 đoạn ống chính khác cao độ")
                if abs(self.end(H["c"]).Z - za) > 5 * self.ft:
                    H["c"], new = self.ramp(H["c"], za, self.pt(j["P"], za))
                    extra += new
                P = self.pt(j["P"], za)
                for k in ("a", "b", "c"):
                    self.set_end(H[k], P)
                doc.Regenerate()
                sub = SubTransaction(doc)
                try:
                    sub.Start()
                    self.tag(doc.Create.NewTeeFitting(self.con(H["a"][0], P), self.con(H["b"][0], P),
                                                      self.con(H["c"][0], P)), u"tê")
                    sub.Commit()
                except Exception:
                    if sub.HasStarted() and not sub.HasEnded():
                        sub.RollBack()
                    # dự phòng: nối thẳng ống chính lệch qua khỏi nhánh, nhánh dùng chân rẽ (takeoff) trên ống a
                    s = H["c"][0].Width / 2.0 + 300.0 * self.ft
                    ua = H["a"][1]
                    Pj = XYZ(P.X + ua.X * s, P.Y + ua.Y * s, P.Z)
                    self.pair(H["a"], H["b"], Pj, u"(tê)")
                    doc.Regenerate()
                    self.tag(doc.Create.NewTakeoffFitting(self.con(H["c"][0], P), H["a"][0]), u"chân rẽ")
            else:   # te: đầu nhánh đâm vào thân ống chính
                main = self.made[j["main"]]
                zm = self.curve(main).GetEndPoint(0).Z
                if abs(self.end(H["a"]).Z - zm) > 5 * self.ft:
                    H["a"], new = self.ramp(H["a"], zm, self.pt(j["P"], zm))
                    extra += new
                P = self.pt(j["P"], zm)
                self.set_end(H["a"], P)
                doc.Regenerate()
                self.tag(doc.Create.NewTakeoffFitting(self.con(H["a"][0], P), main), u"chân rẽ")
            doc.Regenerate()
            for w in watch + extra + [h[0] for h in H.values()]:
                if not w.IsValidObject:
                    raise Exception(u"ống bị xoá khi đặt phụ kiện")
                if self.curve(w).Length < self.min_len:
                    raise Exception(u"ống còn quá ngắn sau khi đặt phụ kiện")
            for w, dr in zip(watch, d0):
                if self.curve(w).Direction.DotProduct(dr) < 0.99:
                    raise Exception(u"ống bị đổi chiều (khe quá ngắn cho phụ kiện)")
        except Exception as ex:
            why = u"{}".format(ex)
        if why is None:
            st.Commit()
        else:
            st.RollBack()
            self.ramps -= sum(1 for e in extra[::2])
        return why


def main():
    cad_filter = (IN[0] or u"").strip()
    layers = [s.strip() for s in (IN[1] or u"").split(u";") if s.strip()]
    sys_map = parse_map(IN[2])
    text_layers = set(s.strip() for s in (IN[3] or u"").split(u";") if s.strip())
    level_name = (IN[4] or u"").strip()
    duct_type_name = (IN[5] or u"").strip()
    extra = float(IN[6]) if IN[6] is not None else 0.0
    del_old = bool(IN[7]) if len(IN) > 8 else False
    dry_run = True if IN[-1] is None else bool(IN[-1])

    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."]
    cad = pick_cad(cad_filter)
    cad_name = get_name(doc.GetElement(cad.GetTypeId()))
    path = cad_file_path(cad)
    if path is None:
        return [u"DỪNG: bản CAD phải được LINK (không Import) và file DWG phải còn ở đường dẫn gốc."]
    core = find_accoreconsole()
    if core is None:
        return [u"DỪNG: không tìm thấy AutoCAD Core Console (C:\\Program Files\\Autodesk\\AutoCAD *\\accoreconsole.exe)."]

    # level, duct type, system
    if level_name:
        lv = [l for l in FilteredElementCollector(doc).OfClass(Level).ToElements() if l.Name == level_name]
        if not lv:
            return [u"DỪNG: không có level '{}'. Các level: {}".format(level_name, u", ".join(
                sorted(l.Name for l in FilteredElementCollector(doc).OfClass(Level).ToElements())))]
        level = lv[0]
    else:
        level = doc.ActiveView.GenLevel
        if level is None:
            return [u"DỪNG: view đang mở không gắn level – nhập tên level vào IN[4]."]
    rect = [t for t in FilteredElementCollector(doc).OfClass(DuctType).ToElements()
            if t.Shape == ConnectorProfileType.Rectangular]
    dtype = [t for t in rect if get_name(t) == duct_type_name]
    if not dtype:
        return [u"DỪNG: không có Rectangular Duct type '{}'. Các type chữ nhật: {}".format(
            duct_type_name, u", ".join(sorted(get_name(t) for t in rect)))]
    dtype = dtype[0]
    nfc = lambda s: unicodedata.normalize("NFC", s or u"")
    systems = dict((nfc(get_name(s)), s) for s in FilteredElementCollector(doc).OfClass(MechanicalSystemType).ToElements())
    lsys = {}
    for lay in layers:
        for k, v in sys_map:
            if k == u"*" or nfc(k).lower() in nfc(lay).lower():
                lsys[lay] = nfc(v)
                break
    bad = sorted(set(v for v in lsys.values() if v not in systems))
    nosys = [l for l in layers if l not in lsys]
    if bad or nosys:
        return [u"DỪNG: IN[2] chưa gán system cho layer: {} | system không có: {}. Các system: {}".format(
            u", ".join(nosys) or u"-", u", ".join(bad) or u"-", u", ".join(sorted(systems)))]

    ents = read_dwg(path, core)
    all_layers = set(l for l, a, b in ents["segs"])
    found = [l for l in layers if l in all_layers]
    if not found:
        return [u"DỪNG: không có layer ống nào trong IN[1]. Các layer có nét thẳng trong DWG:"] + sorted(all_layers)
    missing = [l for l in layers if l not in all_layers]
    ducts, log, tags = find_ducts(ents, found, text_layers)

    tf = cad.GetTotalTransform()
    ft = 1.0 / 304.8

    plan, rows = [], []
    for d in sorted(ducts, key=lambda d: (d["layer"], -d["len"])):
        base = [short(d["layer"]), fmt(d["p1"]), fmt(d["p2"]), u"{:.0f}".format(d["len"]), u"{:.0f}".format(d["W"])]
        if not d.get("tag"):
            rows.append([u"KHÔNG DỰNG"] + base + [u"", u"", u"", u"", u"không có chữ kích thước (thiết bị / ống thiếu ghi chú) – vẽ tay nếu là ống"])
            continue
        size = u"{}x{}".format(d["Wt"], d["Ht"])
        info = [size, u"" if d["bod"] is None else u"{:.0f}".format(d["bod"]), d["src"], d["tag"]]
        if d["bod"] is None:
            rows.append([u"KHÔNG DỰNG"] + base + info + [u"chữ không có BOD"])
            continue
        plan.append((d, base, info))

    lines = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"THỰC HIỆN"),
             u"Bản CAD: {} | layer: {}{}".format(cad_name, u"; ".join(short(l) for l in found),
                                                 u" | KHÔNG có layer: " + u"; ".join(missing) if missing else u""),
             u"Level gốc FL: {} ({:+.0f} mm) | Duct type: {} | cộng thêm BOD {:+.0f} mm".format(
                 level.Name, level.Elevation * 304.8, duct_type_name, extra),
             u"Nhận dạng: {} đoạn ống thẳng → dựng {} | không dựng {} (xem log)".format(
                 len(ducts), len(plan), len(ducts) - len(plan))]
    by = collections.defaultdict(lambda: [0, 0.0])
    for d, base, info in plan:
        k = (lsys[d["layer"]], u"{}x{}".format(d["Wt"], d["Ht"]), d["bod"])
        by[k][0] += 1
        by[k][1] += d["len"] / 1000.0
    for (sname, size, bod), (n, L) in sorted(by.items()):
        lines.append(u"  {} | {} | BOD {:.0f} | {} ống | {:.1f} m".format(sname, size, bod, n, L))
    lines.append(u"Nguồn kích thước: " + u", ".join(u"{} {}".format(k, v) for k, v in sorted(
        collections.Counter(d["src"] for d, b, i in plan).items())))
    lines.append(u"Xử lý: " + u", ".join(u"{} {}".format(k, v) for k, v in log.items()))
    # mối nối / phụ kiện
    B = [d for d, base, info in plan]
    joints, open_ends = plan_joints(B)
    jk = collections.Counter()
    for j in joints:
        jk[JOINT_NAME[j["kind"]]] += 1
        if abs(zc(B[j["a"][0]]) - zc(B[j["b"][0]] if "b" in j else B[j["main"]])) > 5 or \
                ("c" in j and abs(zc(B[j["c"][0]]) - zc(B[j["a"][0]])) > 5):
            jk[u"trong đó chuyển cao độ (ống dốc 2 cút)"] += 1
    lines.append(u"Mối nối dự kiến: " + u", ".join(u"{} {}".format(k, v) for k, v in sorted(jk.items())) +
                 u" | đầu ống hở (cửa gió, quạt, trục…): {}".format(len(open_ends)))
    for d, P in open_ends:
        rows.append([u"ĐẦU HỞ", short(d["layer"]), fmt(P), u"", u"", u"", u"{}x{}".format(d["Wt"], d["Ht"]),
                     u"{:.0f}".format(d["bod"]), u"", u"", u"không có ống để nối (≤ 3 m) – kiểm tra / nối tay"])

    old = [e for e in list(FilteredElementCollector(doc).OfClass(Duct).ToElements()) +
           list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_DuctFitting).WhereElementIsNotElementType().ToElements())
           if (e.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).AsString() or u"").startswith(COMMENT)]
    n_old = len(old)
    if n_old and not del_old:
        lines.append(u"DỪNG GHI: mô hình đã có {} ống / phụ kiện '{}' của lần chạy trước. Đặt IN[7] = True để xoá "
                     u"chúng trước khi dựng lại, hoặc xoá tay (lọc Comments).".format(n_old, COMMENT))
    elif n_old:
        lines.append(u"Sẽ xoá {} ống / phụ kiện '{}' cũ trước khi dựng (IN[7] = True).".format(n_old, COMMENT))

    if dry_run or (n_old and not del_old):
        for d, base, info in plan:
            rows.append([u"SẼ DỰNG" if not (n_old and not del_old) else u"CHƯA DỰNG"] + base + info + [lsys[d["layer"]]])
    else:
        TransactionManager.Instance.ForceCloseTransaction()
        t = Transaction(doc, TRANSACTION_NAME)
        t.Start()
        made, fail = {}, 0
        try:
            if n_old:
                ids = List[ElementId]([e.Id for e in old if e.IsValidObject])
                doc.Delete(ids)
                lines.append(u"Đã xoá {} ống / phụ kiện cũ.".format(n_old))
            for i, (d, base, info) in enumerate(plan):
                z = level.Elevation + (d["bod"] + extra + d["Ht"] / 2.0) * ft
                a = tf.OfPoint(XYZ(d["p1"][0] * ft, d["p1"][1] * ft, 0))
                b = tf.OfPoint(XYZ(d["p2"][0] * ft, d["p2"][1] * ft, 0))
                try:
                    du = Duct.Create(doc, systems[lsys[d["layer"]]].Id, dtype.Id, level.Id,
                                     XYZ(a.X, a.Y, z), XYZ(b.X, b.Y, z))
                    du.get_Parameter(BuiltInParameter.RBS_CURVE_WIDTH_PARAM).Set(d["Wt"] * ft)
                    du.get_Parameter(BuiltInParameter.RBS_CURVE_HEIGHT_PARAM).Set(d["Ht"] * ft)
                    du.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set(u"{} | {} | {}{}".format(
                        COMMENT, short(d["layer"]), info[0], u" " + d["fire"] if d["fire"] else u""))
                    rows.append([u"ĐÃ DỰNG"] + base + info + [u"Id {}".format(du.Id)])
                    made[i] = du
                except Exception as ex:
                    rows.append([u"LỖI"] + base + info + [u"{}".format(ex)])
                    fail += 1
            doc.Regenerate()
            fitter = Fitter(B, made, tf, dtype, level)
            ok, bad = collections.Counter(), collections.Counter()
            order = {"thang": 0, "cut": 1, "te3": 2, "te": 3}
            for j in sorted(joints, key=lambda j: order[j["kind"]]):
                why = fitter.joint(j)
                name = JOINT_NAME[j["kind"]]
                if why is None:
                    ok[name] += 1
                else:
                    bad[name] += 1
                    d = B[j["a"][0]]
                    rows.append([u"PHỤ KIỆN LỖI", short(d["layer"]), fmt(j["P"]), u"", u"", u"", name, u"", u"", u"",
                                 why])
            t.Commit()
        except Exception as ex:
            if t.HasStarted() and not t.HasEnded():
                t.RollBack()
            return lines + [u"LỖI khi dựng ống, mọi thay đổi đã được hoàn tác: {}".format(ex)]
        lines.append(u"ĐÃ TẠO {} ống gió + {} ống chuyển cao độ (Comments '{} | …'), lỗi {}.".format(
            len(made), fitter.ramps * 2, COMMENT, fail))
        lines.append(u"Phụ kiện đã nối: " + (u", ".join(u"{} {}".format(k, v) for k, v in sorted(ok.items())) or u"0") +
                     u" | không nối được (nối tay, xem log): " + (u", ".join(u"{} {}".format(k, v) for k, v in sorted(bad.items())) or u"0"))
    try:
        lines.append(u"Log: " + write_log(rows, cad_name, dry_run))
    except Exception as ex:
        lines.append(u"Không ghi được file log: {}".format(ex))
    return lines + [u"{} | {} | {} → {} | dài {} | W {} | {} | {}".format(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[-1])
                    for r in rows if r[0] in (u"PHỤ KIỆN LỖI", u"LỖI", u"KHÔNG DỰNG")][:200]


if DYNAMO:
    try:
        OUT = main()
    except Exception as ex:
        import traceback
        OUT = [u"LỖI: {}".format(ex), traceback.format_exc()]
elif __name__ == "__main__" and len(sys.argv) > 2:
    # Thử ngoài Revit: python ARV_TaoOngGioTuCAD_v1.py <file.dwg> <out.json> [layer;layer] [layer chữ]
    import json
    lay = (sys.argv[3] if len(sys.argv) > 3 else u"AV-M-TG-CAP KHI BU;AV-M-TG-HUT KHOI;AV-M-TG-TANG AP").split(u";")
    tl = set((sys.argv[4] if len(sys.argv) > 4 else u"AV-M-AC-text 1").split(u";"))
    E = read_dwg(sys.argv[1], find_accoreconsole())
    D, L, T = find_ducts(E, [l for l in lay if l], tl)
    with io.open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(D, f, ensure_ascii=False)
    print(u"đoạn nét {} | chữ {} | ống {} | có kích thước {} | có BOD {}".format(
        len(E["segs"]), len(E["texts"]), len(D), sum(1 for d in D if d.get("tag")),
        sum(1 for d in D if d.get("tag") and d["bod"] is not None)))
    print(dict(L))
