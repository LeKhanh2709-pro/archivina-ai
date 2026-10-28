# -*- coding: utf-8 -*-
"""Chia đố thanh đứng và dựng vách kính (mặt bằng) từ chiều dài vách.

Quy tắc (người dùng chốt 28/10/2026):
  - Đố rộng 65: tâm đố đầu / cuối cách mép ngoài vách 32,5.
  - Khoảng cần chia S = L - 65 (tâm đố đầu -> tâm đố cuối).
  - Trừ khoảng tâm-tâm của cửa (cửa sổ mở 1000, cửa đi 1665, đo từ block), phần còn lại
    chia đều thành N ô kính, N nhỏ nhất để mỗi ô < 1200. Không làm tròn.
  - Cửa đặt vào ô thứ k (tính từ trái, kể cả ô cửa); không ghi k: 1 cửa thì đặt ô giữa.

Kết quả: DXF mới (không ghi đè) có block VACH KINH <L> trên layer A-Window, chuỗi kích thước
"dim cua" trong block, layer Defpoints, ảnh PNG xem lại, JSON toạ độ đố.

Ví dụ: python chia_do.py --dai 4210 --mo so@3 --out "...\\05_VachKinh\\VK_4210.dxf"
"""
import argparse
import json
import math
import os
import sys
from decimal import ROUND_HALF_UP, Decimal

import ezdxf
from ezdxf.addons import Importer

LAYER = "A-Window"
LAYER_DIM = "Defpoints"
DIMSTYLE = "dim cua"
LOAI = {"so": "cua_so", "di": "cua_di"}


def chia(dai, mo, do_rong=65.0, toi_da=1200.0, rong_cua=None):
    """Trả về danh sách ô [(loại, rộng tâm-tâm)] và vị trí tâm đố (tính từ mép ngoài trái)."""
    S = dai - do_rong
    tong_cua = sum(rong_cua[l] for l, _ in mo)
    R = S - tong_cua
    if R < -1e-6:
        raise ValueError(f"Vách {dai} quá ngắn: cửa chiếm {tong_cua} > khoảng chia {S}")
    n = 0 if R < 1e-6 else int(math.floor(R / toi_da)) + 1
    tong_o = n + len(mo)
    o = [None] * tong_o
    chua_k = [x for x in mo if x[1] is None]
    if len(chua_k) > 1:
        raise ValueError("Có nhiều cửa: ghi rõ ô cho từng cửa, vd. so@2 di@4")
    for loai, k in mo:
        if k is None:
            k = tong_o // 2 + 1
        if not 1 <= k <= tong_o:
            raise ValueError(f"Ô {k} ngoài khoảng 1..{tong_o}")
        if o[k - 1] is not None:
            raise ValueError(f"Hai cửa cùng ô {k}")
        o[k - 1] = (loai, rong_cua[loai])
    b = R / n if n else 0.0
    o = [x if x is not None else ("kinh", b) for x in o]
    tam = [do_rong / 2]
    for _, w in o:
        tam.append(tam[-1] + w)
    return o, tam, b


def ten_moi(doc, goc):
    name, i = goc, 2
    while doc.blocks.get(name) is not None:
        name, i = f"{goc} {i}", i + 1
    return name


def file_moi(path):
    if not os.path.exists(path):
        return path
    goc, duoi = os.path.splitext(path)
    i = 2
    while os.path.exists(f"{goc}_{i}{duoi}"):
        i += 1
    return f"{goc}_{i}{duoi}"


def doc_mo(ds):
    """'so@3,di' -> [('so', 3), ('di', None)]"""
    out = []
    for tok in ",".join(ds or []).split(","):
        tok = tok.strip().lower()
        if not tok:
            continue
        loai, _, k = tok.partition("@")
        if loai not in LOAI:
            raise ValueError(f"Loại cửa '{loai}' không hợp lệ (so / di)")
        out.append((loai, int(k) if k else None))
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    skill = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description="Chia đố thanh đứng, dựng vách kính mặt bằng ra DXF + PNG")
    ap.add_argument("--dai", type=float, required=True, help="chiều dài vách, mép ngoài - mép ngoài (mm)")
    ap.add_argument("--mo", action="append", help="cửa trong vách: so / di, kèm @ô, vd. so@3 hoặc so@2,di@4")
    ap.add_argument("--out", required=True, help="file DXF kết quả (đã có thì thêm _2, _3…)")
    ap.add_argument("--goc", type=float, default=0.0, help="góc vách (độ), mặc định 0 = theo trục X")
    ap.add_argument("--x", type=float, default=0.0, help="toạ độ mép ngoài đầu vách")
    ap.add_argument("--y", type=float, default=0.0)
    ap.add_argument("--lat", action="store_true", help="lật vách (mặt kẹp kính sang phía -Y)")
    ap.add_argument("--khong-kinh", action="store_true", help="không vẽ kính ô cố định")
    ap.add_argument("--khong-dim", action="store_true", help="không ghi chuỗi kích thước")
    ap.add_argument("--khong-anh", action="store_true")
    ap.add_argument("--thu-vien", default=os.path.join(skill, "assets", "VK_thu_vien.dxf"))
    ap.add_argument("--do-rong", type=float, default=65.0, help="bề rộng đố dùng để chia (người dùng chốt 65)")
    ap.add_argument("--toi-da", type=float, default=1200.0, help="khoảng tâm-tâm phải nhỏ hơn giá trị này")
    a = ap.parse_args()

    tv = ezdxf.readfile(a.thu_vien)
    with open(os.path.splitext(a.thu_vien)[0] + ".json", encoding="utf-8") as f:
        info = json.load(f)
    rong_cua = {"so": info["cua_so"]["tam_tam"], "di": info["cua_di"]["tam_tam"]}
    try:
        mo = doc_mo(a.mo)
        o, tam, b = chia(a.dai, mo, a.do_rong, a.toi_da, rong_cua)
    except ValueError as ex:
        sys.exit(f"LỖI: {ex}")

    doc = ezdxf.new("R2018")
    doc.units = 4
    imp = Importer(tv, doc)
    imp.import_blocks(["VK_DoDung", "VK_CuaSoMo", "VK_CuaDi"])
    imp.import_tables("layers", [LAYER, LAYER_DIM])
    if tv.dimstyles.has_entry(DIMSTYLE):
        imp.import_tables("styles", [tv.dimstyles.get(DIMSTYLE).dxf.dimtxsty])
        imp.import_tables("dimstyles", [DIMSTYLE])
    imp.finalize()
    if not doc.layers.has_entry(LAYER_DIM):
        lay = tv.layers.get(LAYER_DIM) if tv.layers.has_entry(LAYER_DIM) else None
        doc.layers.add(LAYER_DIM, color=lay.dxf.color if lay else 7)

    ten = ten_moi(doc, f"VACH KINH {a.dai:g}")
    blk = doc.blocks.new(ten, base_point=(0, 0))
    sy = -1 if a.lat else 1
    phu = set()  # tâm đố đã có trong block cửa
    for i, (loai, w) in enumerate(o):
        x0 = tam[i]
        if loai in LOAI:
            name = info[LOAI[loai]]["block"]
            blk.add_blockref(name, (x0, 0), dxfattribs={"layer": LAYER, "yscale": sy})
            phu.update({i, i + 1})
        elif not a.khong_kinh:
            for y0, y1, col in info["kinh_cua_so"]:
                xa, xb = x0 + a.do_rong / 2, x0 + w - a.do_rong / 2
                blk.add_lwpolyline([(xa, sy * y0), (xb, sy * y0), (xb, sy * y1), (xa, sy * y1)], close=True,
                                   dxfattribs={"layer": LAYER, "color": 256})
    for i, x in enumerate(tam):
        if i not in phu:
            blk.add_blockref("VK_DoDung", (x, 0), dxfattribs={"layer": LAYER, "yscale": sy})

    if not a.khong_dim:
        # chuỗi kích thước kiểm tra: mép ngoài - tâm các đố - mép ngoài, phía mặt kẹp kính,
        # nằm TRONG block, layer Defpoints (không in) — người dùng chốt 28/10/2026
        moc = [0.0] + tam + [a.dai]
        ten_dim = DIMSTYLE if doc.dimstyles.has_entry(DIMSTYLE) else "Standard"
        dec = doc.dimstyles.get(ten_dim).dxf.get("dimdec", 0)
        for p, q in zip(moc, moc[1:]):
            # làm tròn nửa lên như AutoCAD (32,5 -> 33), Python round() làm tròn về số chẵn
            chu = str(Decimal(str(q - p)).quantize(Decimal(1).scaleb(-dec), rounding=ROUND_HALF_UP))
            dim = blk.add_aligned_dim(p1=(p, 0), p2=(q, 0), distance=sy * 400.0,
                                      text=chu, dimstyle=ten_dim, dxfattribs={"layer": LAYER_DIM})
            dim.render()

    msp = doc.modelspace()
    msp.add_blockref(ten, (a.x, a.y), dxfattribs={"layer": LAYER, "rotation": a.goc})

    out = file_moi(a.out)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    doc.saveas(out)

    ket_qua = {
        "dai": a.dai, "block": ten, "o_kinh": len([x for x in o if x[0] == "kinh"]),
        "rong_o_kinh": round(b, 4), "o": [{"loai": l, "rong": round(w, 4)} for l, w in o],
        "tam_do": [round(x, 4) for x in tam], "dxf": out,
    }
    with open(os.path.splitext(out)[0] + ".json", "w", encoding="utf-8") as f:
        json.dump(ket_qua, f, ensure_ascii=False, indent=2)

    if not a.khong_anh:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from ezdxf.addons.drawing import Frontend, RenderContext
        from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
        fig = plt.figure(figsize=(16, 4), dpi=150)
        ax = fig.add_axes([0, 0, 1, 1])
        Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(msp, finalize=True)
        png = os.path.splitext(out)[0] + ".png"
        fig.savefig(png, facecolor="black")
        ket_qua["png"] = png

    chuoi = " | ".join(f"{w:g}" if l == "kinh" else f"{l.upper()} {w:g}" for l, w in o)
    print(f"Vách {a.dai:g}: {len(o)} ô [{chuoi}], ô kính {b:.4f} mm, {len(tam)} vị trí tâm đố")
    print(json.dumps(ket_qua, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
