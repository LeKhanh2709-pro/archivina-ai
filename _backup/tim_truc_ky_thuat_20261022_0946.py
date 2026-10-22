# -*- coding: utf-8 -*-
"""Tìm trục kỹ thuật / hộp kỹ thuật (HKT) cần hatch ngăn cháy lan trên mặt bằng tầng (DXF).

Nhận diện: mỗi trục/hộp có DẤU X (2 nét chéo nối 4 góc ô chữ nhật) trên các layer
A-Wall-Open, A-Material, A-Truc ME, A-Hidden (đổi bằng --layer-x). Ô X chạm nhau được gộp
thành một vùng (vd. hộp chữ L). Loại trừ: dấu X trong block cabin thang máy (tên block
khớp --block-thang-may) và đồ nội thất (layer khác danh sách trên, vd. máy rửa bát).
Vùng đã có hatch NET trên layer A-HATCH- Color được đánh dấu "da_co" để không vẽ trùng.

Đầu ra (trong --out-dir): <tên>_vung.json (cho ve_hatch_vao_ban_sao.ps1), <tên>_vung.xlsx,
<tên>_vung.png (ảnh xem lại: xanh = sẽ hatch, xám = đã có, đỏ = loại).

Ví dụ:
  python tim_truc_ky_thuat.py "D:\\AI\\_tmp\\x\\MB tang 4.dxf" --out-dir "D:\\AI\\<du an>\\05_NganChay"
"""
import argparse
import fnmatch
import json
import math
import os
import sys

import ezdxf
from ezdxf import bbox as ezbbox
from ezdxf import path as ezpath
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

LAYER_X = ["A-Wall-Open", "A-Material", "A-Truc ME", "A-Hidden"]
BLOCK_THANG_MAY = ["*cabin*", "*thang may*", "*thangmay*", "*elevator*", "*lift*"]
LAYER_HATCH = "A-HATCH- Color"
PATTERN = "NET"
CANH_MIN = 150      # mm, cạnh ô X nhỏ nhất
CANH_MAX = 4000     # mm, cạnh ô X lớn nhất (lớn hơn thì là thông tầng / sảnh, không phải trục)
DUNG_SAI = 40       # mm, sai số khi so 2 nét chéo cùng một ô


def lam_phang(entities, depth=0, eff=None, path=""):
    """Duyệt đệ quy block; layer "0" trong block lấy theo layer của INSERT (layer hiệu lực)."""
    for e in entities:
        lay = e.dxf.get("layer", "0")
        el = eff if (lay == "0" and eff) else lay
        if e.dxftype() == "INSERT" and depth < 8:
            try:
                yield from lam_phang(e.virtual_entities(), depth + 1, el, path + "/" + e.dxf.name)
            except Exception:
                pass
        else:
            yield e, el, path


def khop(ten, mau):
    t = ten.lower()
    return any(fnmatch.fnmatch(t, m.lower()) for m in mau)


def cac_doan(e):
    """Đoạn thẳng trong hệ WCS (LWPOLYLINE phải đổi từ OCS, block lật gương có extrusion -Z)."""
    t = e.dxftype()
    if t == "LINE":
        s, d = e.dxf.start, e.dxf.end
        return [((s.x, s.y), (d.x, d.y))]
    if t == "LWPOLYLINE":
        pts = [(v.x, v.y) for v in e.vertices_in_wcs()]
        if e.closed and pts:
            pts.append(pts[0])
        return list(zip(pts, pts[1:]))
    if t == "POLYLINE" and not e.is_3d_polyline:
        pts = [(v.x, v.y) for v in e.points_in_wcs()] if hasattr(e, "points_in_wcs") else []
        return list(zip(pts, pts[1:]))
    return []


def doc_ban_ve(dxf_path, layer_x, block_tm):
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    cheo, cabin, chu, hatch_co, nen = [], [], [], [], []
    layer_x_l = {l.lower() for l in layer_x}
    for e, el, path in lam_phang(msp):
        t = e.dxftype()
        if block_tm and khop(path, block_tm):
            try:
                b = ezbbox.extents([e])
                if b.has_data:
                    cabin.append(box(b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y))
            except Exception:
                pass
            continue
        if t in ("TEXT", "MTEXT"):
            try:
                txt = e.plain_text() if t == "MTEXT" else e.dxf.text
                p = e.dxf.insert
                chu.append((p.x, p.y, txt.strip()))
            except Exception:
                pass
            continue
        if t == "HATCH":
            if el == LAYER_HATCH and e.dxf.pattern_name.upper() == PATTERN:
                for p in ezpath.from_hatch(e):
                    try:
                        pts = [(v.x, v.y) for v in p.flattening(10)]
                        if len(pts) >= 3:
                            hatch_co.append(Polygon(pts).buffer(0))
                    except Exception:
                        pass
            continue
        if t in ("LINE", "LWPOLYLINE", "POLYLINE"):
            doan = cac_doan(e)
            if el.lower().startswith("a-wall") or el.lower() in ("a-truc me", "a-column"):
                nen.extend(doan)
            if el.lower() not in layer_x_l:
                continue
            if path == "" and el == "A-Material":
                continue  # polyline biên do skill (hoặc người vẽ) tạo, không phải dấu X
            for a, b in doan:
                dx, dy = b[0] - a[0], b[1] - a[1]
                if math.hypot(dx, dy) < CANH_MIN:
                    continue
                goc = math.degrees(math.atan2(abs(dy), abs(dx)))
                if 12 < goc < 78:
                    cheo.append((a, b, el, path))
    return cheo, cabin, chu, hatch_co, nen


def ghep_dau_x(cheo):
    """Ghép 2 nét chéo ngược hướng có cùng khung chữ nhật thành một ô X."""
    def khung(s):
        (x1, y1), (x2, y2) = s[0], s[1]
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

    luoi = {}
    for i, s in enumerate(cheo):
        k = khung(s)
        luoi.setdefault((round(k[0] / 50), round(k[1] / 50)), []).append(i)
    o_x = []
    for i, s in enumerate(cheo):
        k = khung(s)
        w, h = k[2] - k[0], k[3] - k[1]
        if not (CANH_MIN <= w <= CANH_MAX and CANH_MIN <= h <= CANH_MAX):
            continue
        huong = (s[1][1] - s[0][1]) * (s[1][0] - s[0][0])
        gx, gy = round(k[0] / 50), round(k[1] / 50)
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                for j in luoi.get((gx + ox, gy + oy), []):
                    if j <= i:
                        continue
                    t = cheo[j]
                    k2 = khung(t)
                    if all(abs(a - b) < DUNG_SAI for a, b in zip(k, k2)):
                        if huong * (t[1][1] - t[0][1]) * (t[1][0] - t[0][0]) < 0:
                            o_x.append(dict(khung=k, layer=s[2], path=s[3]))
    # bỏ ô trùng (cùng một dấu X vẽ chồng nhiều nét)
    kq = []
    for o in o_x:
        if not any(all(abs(a - b) < 60 for a, b in zip(o["khung"], q["khung"])) for q in kq):
            kq.append(o)
    return kq


def gop_vung(o_x):
    """Ô X chạm nhau (chung cạnh) gộp thành một vùng; ô cách nhau bởi tường thì giữ riêng."""
    hinh = [box(*o["khung"]) for o in o_x]
    hop = unary_union([h.buffer(5, join_style=2) for h in hinh])
    gs = list(hop.geoms) if hasattr(hop, "geoms") else [hop]
    vung = []
    for g in gs:
        g = g.buffer(-5, join_style=2).simplify(1)
        if g.is_empty:
            continue
        if g.geom_type != "Polygon":
            g = max(g.geoms, key=lambda x: x.area)
        thanh_phan = [o for o, h in zip(o_x, hinh) if h.intersects(g)]
        vung.append((Polygon(g.exterior.coords), thanh_phan))
    return vung


def nguon(path):
    p = [x for x in path.split("/") if x]
    return p[0] if p else "(model)"


def main():
    ap = argparse.ArgumentParser(description="Tìm trục/hộp kỹ thuật cần hatch ngăn cháy lan (dấu X).")
    ap.add_argument("dxf")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--layer-x", default=",".join(LAYER_X), help="Layer chứa dấu X, phân cách bằng dấu phẩy")
    ap.add_argument("--block-thang-may", default=",".join(BLOCK_THANG_MAY),
                    help="Mẫu tên block cabin/giếng thang máy cần loại (wildcard, phân cách dấu phẩy)")
    ap.add_argument("--khong-anh", action="store_true", help="Không vẽ ảnh PNG xem lại")
    a = ap.parse_args()

    layer_x = [x.strip() for x in a.layer_x.split(",") if x.strip()]
    block_tm = [x.strip() for x in a.block_thang_may.split(",") if x.strip()]
    os.makedirs(a.out_dir, exist_ok=True)
    ten = os.path.splitext(os.path.basename(a.dxf))[0]
    f_json = os.path.join(a.out_dir, ten + "_vung.json")
    f_xlsx = os.path.join(a.out_dir, ten + "_vung.xlsx")
    f_png = os.path.join(a.out_dir, ten + "_vung.png")
    for f in (f_json, f_xlsx):
        if os.path.exists(f):
            sys.exit(f"Đã tồn tại, không ghi đè: {f} (chuyển bản cũ vào D:\\AI\\_backup trước)")

    print("Đang đọc DXF...", flush=True)
    cheo, cabin, chu, hatch_co, nen = doc_ban_ve(a.dxf, layer_x, block_tm)
    o_x = ghep_dau_x(cheo)
    vung = gop_vung(o_x)
    cabin_u = unary_union(cabin) if cabin else None
    hatch_u = unary_union(hatch_co) if hatch_co else None

    ds = []
    for i, (g, tp) in enumerate(sorted(vung, key=lambda v: (-round(v[0].centroid.y / 500), v[0].centroid.x)), 1):
        c = g.centroid
        x0, y0, x1, y1 = g.bounds
        vien = g.buffer(30)
        nhan = sorted({t for (x, y, t) in chu if t and vien.contains(Point(x, y))})
        trang_thai, ghi_chu = "se_hatch", ""
        if cabin_u is not None and g.intersection(cabin_u).area > 0.2 * g.area:
            trang_thai, ghi_chu = "loai", "Trùng cabin thang máy"
        elif hatch_u is not None and g.intersection(hatch_u).area > 0.8 * g.area:
            trang_thai, ghi_chu = "da_co", "Đã có hatch NET"
        if trang_thai == "se_hatch" and min(x1 - x0, y1 - y0) > 1400 and max(x1 - x0, y1 - y0) > 1400:
            ghi_chu = "Ô lớn, kiểm tra lại có phải giếng thang / lỗ mở sàn không (Cần xác nhận lại)"
        ds.append(dict(
            id=i, trang_thai=trang_thai, ghi_chu=ghi_chu,
            cx=round(c.x), cy=round(c.y), rong=round(x1 - x0), dai=round(y1 - y0),
            dien_tich_m2=round(g.area / 1e6, 3),
            nguon=sorted({nguon(o["path"]) for o in tp}),
            layer_x=sorted({o["layer"] for o in tp}),
            nhan=nhan,
            dinh=[[round(x, 1), round(y, 1)] for x, y in list(g.exterior.coords)[:-1]],
        ))

    json.dump(dict(dxf=os.path.abspath(a.dxf), layer_hatch=LAYER_HATCH, pattern=PATTERN, vung=ds),
              open(f_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Truc - HKT"
    ws.append(["STT", "Trạng thái", "Tâm X", "Tâm Y", "Rộng (mm)", "Dài (mm)", "Diện tích (m²)",
               "Nguồn (xref/block)", "Layer dấu X", "Chữ trong ô", "Ghi chú"])
    nhan_tt = {"se_hatch": "Sẽ hatch", "da_co": "Đã có hatch", "loai": "Loại"}
    for v in ds:
        ws.append([v["id"], nhan_tt[v["trang_thai"]], v["cx"], v["cy"], v["rong"], v["dai"], v["dien_tich_m2"],
                   ", ".join(v["nguon"]), ", ".join(v["layer_x"]), ", ".join(v["nhan"]), v["ghi_chu"]])
    for col, w in zip("ABCDEFGHIJK", (6, 12, 9, 9, 10, 10, 13, 34, 26, 16, 50)):
        ws.column_dimensions[col].width = w
    wb.save(f_xlsx)

    if not a.khong_anh and ds:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.collections import LineCollection
        xs = [p[0] for v in ds for p in v["dinh"]]
        ys = [p[1] for v in ds for p in v["dinh"]]
        pad = 3000
        X0, X1, Y0, Y1 = min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad
        fig, ax = plt.subplots(figsize=(16, 16 * (Y1 - Y0) / max(X1 - X0, 1)))
        seg = [s for s in nen if X0 < s[0][0] < X1 and Y0 < s[0][1] < Y1]
        ax.add_collection(LineCollection(seg, colors="#999999", linewidths=0.3))
        mau = {"se_hatch": "#1a9e3a", "da_co": "#7f7f7f", "loai": "#d62728"}
        for v in ds:
            p = plt.Polygon(v["dinh"], closed=True, fc=mau[v["trang_thai"]], ec="k", lw=0.5, alpha=0.7)
            ax.add_patch(p)
            ax.text(v["cx"], v["cy"], str(v["id"]), fontsize=6, ha="center", va="center", color="k")
        ax.set_xlim(X0, X1)
        ax.set_ylim(Y0, Y1)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title("Xanh = sẽ hatch, xám = đã có, đỏ = loại (thang máy)")
        fig.savefig(f_png, dpi=150, bbox_inches="tight")

    dem = {k: sum(1 for v in ds if v["trang_thai"] == k) for k in ("se_hatch", "da_co", "loai")}
    print(f"Ô X: {len(o_x)} | vùng: {len(ds)} | sẽ hatch: {dem['se_hatch']} | đã có: {dem['da_co']} | loại: {dem['loai']}")
    print(f_json)
    print(f_xlsx)
    if not a.khong_anh:
        print(f_png)


if __name__ == "__main__":
    main()
