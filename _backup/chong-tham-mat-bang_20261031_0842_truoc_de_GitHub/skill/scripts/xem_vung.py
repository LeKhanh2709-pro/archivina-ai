#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Xuat anh PNG cac vung cua mat bang (nen that cua DXF) kem duong bo / net ven / dao trong <ten>_chongtham.json,
de nguoi dung duyet truoc khi ve.

    python xem_vung.py <file_aec.dxf> <ten>_chongtham.json --out-dir <thu muc> --id 4,30,62
    python xem_vung.py <file_aec.dxf> <ten>_chongtham.json --out-dir <thu muc> --khung x0,y0,x1,y1 [--khung ...]
    python xem_vung.py <file_aec.dxf> <ten>_chongtham.json --out-dir <thu muc> --luoi 3x4   (chia ca tang thanh luoi anh)
"""
import argparse
import json
import os

import ezdxf
from ezdxf import bbox as ezbbox
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

MAU = {"se_ve": "#00c000", "da_co": "#999999", "can_xem": "#ff8800", "bo_qua": "#3366ff"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dxf")
    ap.add_argument("json")
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--id", default="", help="danh sach id vung, cach nhau dau phay")
    ap.add_argument("--khung", action="append", default=[], help="x0,y0,x1,y1 (viet --khung=-100,...)")
    ap.add_argument("--luoi", default="", help="CxR: chia khung bao moi vung thanh luoi anh")
    ap.add_argument("--le", type=float, default=2500.0, help="le quanh vung khi xem theo id (mm)")
    ap.add_argument("--truc", action="store_true", help="hien truc toa do + luoi (de doc toa do khi do loi)")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    kq = json.load(open(a.json, encoding="utf-8"))
    vung = kq["vung"]
    khung = []
    for s in a.khung:
        khung.append(("khung_" + s.replace(",", "_").replace("-", "m"), [float(v) for v in s.split(",")]))
    for i in [int(x) for x in a.id.split(",") if x.strip()]:
        v = next((v for v in vung if v["id"] == i), None)
        if v:
            xs = [p[0] for p in v["bo"]]
            ys = [p[1] for p in v["bo"]]
            khung.append((f"vung_{i}", [min(xs) - a.le, min(ys) - a.le, max(xs) + a.le, max(ys) + a.le]))
    if a.luoi and vung:
        c, r = (int(x) for x in a.luoi.lower().split("x"))
        xs = [p[0] for v in vung for p in v["bo"]]
        ys = [p[1] for v in vung for p in v["bo"]]
        x0, x1, y0, y1 = min(xs) - 2000, max(xs) + 2000, min(ys) - 2000, max(ys) + 2000
        w, h = (x1 - x0) / c, (y1 - y0) / r
        for j in range(r):
            for i in range(c):
                khung.append((f"luoi_{j + 1}_{i + 1}", [x0 + i * w, y1 - (j + 1) * h, x0 + (i + 1) * w, y1 - j * h]))
    if not khung:
        ap.error("can --id, --khung hoac --luoi")
    print("Doc DXF...", flush=True)
    doc = ezdxf.readfile(a.dxf)
    msp = doc.modelspace()
    hop = []
    for e in msp:
        try:
            b = ezbbox.extents([e], fast=True)
        except Exception:
            continue
        if b.has_data and b.size.x < 60000 and b.size.y < 60000:
            hop.append((e.dxf.handle, b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y))
    ctx = RenderContext(doc)
    for ten, (x0, y0, x1, y1) in khung:
        hs = {h for h, a0, b0, a1, b1 in hop if not (a1 < x0 or a0 > x1 or b1 < y0 or b0 > y1)}
        fig = plt.figure(figsize=(14, 14 * (y1 - y0) / (x1 - x0)))
        ax = fig.add_axes([0.05, 0.04, 0.94, 0.95] if a.truc else [0, 0, 1, 1])
        ax.set_facecolor("#1e1e1e")
        Frontend(ctx, MatplotlibBackend(ax)).draw_layout(msp, finalize=False, filter_func=lambda e: e.dxf.handle in hs)
        for v in vung:
            xs = [p[0] for p in v["bo"]]
            ys = [p[1] for p in v["bo"]]
            if max(xs) < x0 or min(xs) > x1 or max(ys) < y0 or min(ys) > y1:
                continue
            m = MAU.get(v["trang_thai"], "#00c000")
            b = v["bo"] + [v["bo"][0]]
            ax.fill([p[0] for p in b], [p[1] for p in b], color=m, alpha=0.18, lw=0)
            ax.plot([p[0] for p in b], [p[1] for p in b], color=m, lw=1.0)
            for d in v["dao"]:
                d2 = d + [d[0]]
                ax.plot([p[0] for p in d2], [p[1] for p in d2], color="#4499ff", lw=1.0)
            for l in v["ven"]:
                pts = l["dinh"] + ([l["dinh"][0]] if l["dong"] else [])
                ax.plot([p[0] for p in pts], [p[1] for p in pts], color="red", lw=2.0)
            ax.text(v["tam"][0], v["tam"][1], f'#{v["id"]} {v["ten_loai"].split(" /")[0]}\n{v["can"]} {v["dien_tich"]} m²',
                    ha="center", va="center", fontsize=8, color="yellow")
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_aspect("equal")
        if a.truc:
            ax.tick_params(colors="#aaaaaa", labelsize=7)
            ax.grid(color="#555555", lw=0.3)
        p = os.path.join(a.out_dir, ten + ".png")
        fig.savefig(p, dpi=110, facecolor="#1e1e1e")
        plt.close(fig)
        print(p, flush=True)


if __name__ == "__main__":
    main()
