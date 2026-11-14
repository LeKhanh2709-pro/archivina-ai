# -*- coding: utf-8 -*-
"""Xem các vùng hatch Revit không nhận (kq\\hatch_loi.json do thu_hatch.py ghi): in số đo + vẽ ảnh từng vùng.
Chạy: python xem_hatch_loi.py [hatch_loi.json] [ảnh ra.png]"""
import json, sys, math, io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from shapely.validation import make_valid, explain_validity

src = sys.argv[1] if len(sys.argv) > 1 else r"D:\AI\_tmp\ct_cua_legend\kq\hatch_loi.json"
out = sys.argv[2] if len(sys.argv) > 2 else r"D:\AI\_tmp\ct_cua_legend\kq\hatch_loi.png"
d = json.load(io.open(src, encoding="utf-8"))
print("tổng:", d["tong"])


def cung_3_diem(p0, pm, p1):
    ax, ay = p0; bx, by = pm; cx, cy = p1
    dd = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(dd) < 1e-9:
        return None
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / dd
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / dd
    return ux, uy, math.hypot(ax - ux, ay - uy)


def diem(l, n_cung=12):
    pts = []
    for s in l:
        if s[0] == "L":
            pts.append((s[1], s[2]))
        else:
            k = cung_3_diem((s[1], s[2]), (s[3], s[4]), (s[5], s[6]))
            if k is None:
                pts.append((s[1], s[2])); continue
            cx, cy, r = k
            a0 = math.atan2(s[2] - cy, s[1] - cx); am = math.atan2(s[4] - cy, s[3] - cx); a1 = math.atan2(s[6] - cy, s[5] - cx)
            # chiều đi qua điểm giữa
            def ccw(a, b):
                return (b - a) % (2 * math.pi)
            if ccw(a0, am) <= ccw(a0, a1):
                q = ccw(a0, a1)
            else:
                q = -ccw(a1, a0)
            for i in range(n_cung):
                t = a0 + q * i / n_cung
                pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return pts


def dai(s):
    return math.hypot(s[-2] - s[1], s[-1] - s[2])


H = d["hong"]
n = len(H)
cot = 6
hang = max(1, (n + cot - 1) // cot)
fig, axs = plt.subplots(hang, cot, figsize=(cot * 3.2, hang * 3.2), squeeze=False)
for ax in axs.flat:
    ax.axis("off")
for i, h in enumerate(H):
    ax = axs.flat[i]
    ax.set_aspect("equal")
    xs = []; ys = []
    ngan = 1e9; so_cung = 0; so_doan = 0
    dt = 0.0
    for l in h["loops"]:
        p = diem(l)
        xs += [q[0] for q in p]; ys += [q[1] for q in p]
        ax.plot([q[0] for q in p] + [p[0][0]], [q[1] for q in p] + [p[0][1]], "-", lw=0.8)
        ax.plot([s[1] for s in l], [s[2] for s in l], ".", ms=3, color="k")
        for s in l:
            so_doan += 1; so_cung += s[0] == "A"; ngan = min(ngan, dai(s))
        try:
            pg = Polygon(p)
            dt += pg.area
            hl = explain_validity(pg)
        except Exception as ex:
            hl = str(ex)
    w_, h_ = max(xs) - min(xs), max(ys) - min(ys)
    loi_v = [v["loi_vung"][:40] if v["loi_vung"] else "ok" for v in h["vong"]]
    loi_d = sum(len(v["loi_doan"]) for v in h["vong"])
    ho = [v["ho"] for v in h["vong"]]
    ax.set_title("%d %s z%d\n%s %.1fx%.1f" % (i, h["o"][:14], h["z"], h["kieu"], w_, h_), fontsize=7)
    print("%2d | %-22s | %s idx %d z %d | %s | vòng %d (ok %d) đoạn %d cung %d | bao %.2f x %.2f | đoạn ngắn nhất %.3f | dt %.2f | hợp lệ: %s | đoạn lỗi %d hở %s | mức: %s"
          % (i, h["o"][:22], h["loai"], h["idx"], h["z"], h["kieu"], h["so_vong"], h["vong_ok"], so_doan, so_cung, w_, h_, ngan, dt,
             hl[:40], loi_d, ho, h["muc"]))
    for v in h["vong"]:
        if v["loi_doan"] or v["loi_noi"]:
            print("      đoạn lỗi:", v["loi_doan"][:3], "| nối:", v["loi_noi"])
fig.savefig(out, dpi=110)
print("ảnh:", out)
