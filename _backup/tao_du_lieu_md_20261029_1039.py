# -*- coding: utf-8 -*-
"""Sinh dữ liệu block mặt đứng nhúng vào VKMD.lsp (lisp\\vkmd_du_lieu.lsp) từ các file DXF người dùng cấp.

Đầu vào (thư mục --nguon), tên file chứa:
  - "md cua di"  : mặt đứng cửa đi kính 2 cánh (lọt lòng 1600 x 2699,51, gốc = giữa mép dưới cửa)
  - "md cua so"  : mặt đứng cửa sổ hất (đố dưới 935 x 65 + cánh 935 x 1399,89, tam giác nét HIDDEN, ký hiệu kính)
  - "thanh ngang": thanh đứng / thanh ngang (hình chữ nhật rộng 65)

Đầu ra: lisp\\vkmd_du_lieu.lsp gồm
  vkmd:dl-cua-di  : đối tượng cửa đi đã PHẲNG HOÁ (bỏ ghi chú MULTILEADER, kích thước, ký hiệu kính — ký hiệu
                    kính do lệnh tự đặt giữa từng cánh), toạ độ so với giữa mép dưới cửa:
                    ("LW" kín? ((x y bulge) ...)) | ("ARC" cx cy r a1 a2) | ("LINE" x1 y1 x2 y2)
  vkmd:dl-kinh    : 3 vạch ký hiệu kính (block kinh111 trong file cửa sổ, đã nhân tỉ lệ 0,56), tâm (0,0)
  vkmd:dl-*       : số đo kiểm tra (lọt lòng cửa đi, cánh cửa sổ, đố)

Chạy: python tao_du_lieu_md.py --nguon "<thư mục block vach kinh>"
"""
import argparse
import math
import os
import sys

import ezdxf
from ezdxf import bbox
from ezdxf.math import Matrix44


def tim_file(nguon, khoa):
    for f in os.listdir(nguon):
        if f.lower().endswith(".dxf") and khoa in f.lower():
            return os.path.join(nguon, f)
    sys.exit(f"Không thấy file DXF có chữ '{khoa}' trong {nguon}")


def la_ky_hieu_kinh(doc, e):
    """Block 3 vạch chéo (ký hiệu kính): chỉ gồm 3 nét thẳng."""
    if e.dxftype() != "INSERT":
        return False
    con = list(doc.blocks.get(e.dxf.name))
    return len(con) == 3 and all(x.dxftype() in ("LINE", "LWPOLYLINE") for x in con)


def phang(doc, ents, m, out):
    """Phẳng hoá đệ quy về LW / ARC / LINE trong hệ toạ độ ma trận m."""
    for e in ents:
        t = e.dxftype()
        if t in ("MULTILEADER", "DIMENSION", "MTEXT", "TEXT"):
            continue
        if t == "INSERT":
            if la_ky_hieu_kinh(doc, e):
                continue
            phang(doc, list(e.virtual_entities()), m, out)
            continue
        v = e.copy()
        v.transform(m)
        if t == "LWPOLYLINE":
            # đưa về hệ phẳng WCS (pháp tuyến +Z)
            pts = [(round(p[0], 4), round(p[1], 4), round(p[4], 6)) for p in v.get_points("xyseb")]
            if v.dxf.extrusion.z < 0:
                pts = [(-x, y, -b) for x, y, b in pts]
            out.append(("LW", bool(v.closed), pts))
        elif t == "LINE":
            out.append(("LINE", round(v.dxf.start.x, 4), round(v.dxf.start.y, 4),
                        round(v.dxf.end.x, 4), round(v.dxf.end.y, 4)))
        elif t == "ARC":
            c, r = v.dxf.center, v.dxf.radius
            a1, a2 = math.radians(v.dxf.start_angle), math.radians(v.dxf.end_angle)
            cx, cy = c.x, c.y
            if v.dxf.extrusion.z < 0:  # OCS -Z: x đảo dấu, góc đối xứng và đổi chiều
                cx, a1, a2 = -cx, math.pi - a2, math.pi - a1
            out.append(("ARC", round(cx, 4), round(cy, 4), round(r, 4),
                        round(a1 % (2 * math.pi), 8), round(a2 % (2 * math.pi), 8)))
        else:
            print(f"  ! bỏ qua {t}", file=sys.stderr)


def lisp(x):
    if isinstance(x, bool):
        return "T" if x else "nil"
    if isinstance(x, str):
        return '"' + x + '"'
    if isinstance(x, (int, float)):
        return repr(float(x))
    return "(" + " ".join(lisp(i) for i in x) + ")"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Sinh dữ liệu block mặt đứng vách kính cho VKMD.lsp")
    ap.add_argument("--nguon", required=True, help="thư mục chứa 3 file DXF mặt đứng")
    a = ap.parse_args()
    skill = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # ---- cửa đi: gốc = giữa mép dưới khung bao lọt lòng (đã đúng trong file người dùng)
    d_di = ezdxf.readfile(tim_file(a.nguon, "md cua di"))
    msp = d_di.modelspace()
    khung = max(msp.query("LWPOLYLINE"), key=lambda e: bbox.extents([e]).size.x * bbox.extents([e]).size.y)
    bk = bbox.extents([khung])
    goc = Matrix44.translate(-(bk.extmin.x + bk.extmax.x) / 2, -bk.extmin.y, 0)
    di_rong, di_cao = round(bk.size.x, 2), round(bk.size.y, 2)
    di = []
    phang(d_di, list(msp), goc, di)

    # ---- cửa sổ: đố dưới + cánh; ký hiệu kính kinh111
    d_so = ezdxf.readfile(tim_file(a.nguon, "md cua so"))
    ms = d_so.modelspace()
    ten_canh = [e for e in ms.query("INSERT")][0]
    canh = [x for x in ten_canh.virtual_entities() if x.dxftype() == "LWPOLYLINE"][0]
    bc = bbox.extents([canh])
    do_duoi = bbox.extents(list(ms.query("LWPOLYLINE")))
    kinh_ins = [x for x in ten_canh.virtual_entities() if x.dxftype() == "INSERT"][0]
    kinh = []
    m_kinh = Matrix44.translate(-kinh_ins.dxf.insert.x, -kinh_ins.dxf.insert.y, 0)
    for x in kinh_ins.virtual_entities():
        x.transform(m_kinh)
        kinh.append(("LINE", round(x.dxf.start.x, 4), round(x.dxf.start.y, 4),
                     round(x.dxf.end.x, 4), round(x.dxf.end.y, 4)))
    tg = [x for x in ten_canh.virtual_entities() if x.dxftype() == "LINE"]
    lt_scale = tg[0].dxf.get("ltscale", 1.0) if tg else 1.0
    lt_ten = tg[0].dxf.get("linetype", "HIDDEN") if tg else "HIDDEN"
    mau_canh = canh.dxf.get("color", 256)
    lt = d_so.linetypes.get(lt_ten)
    lt_mau = [t.value for t in lt.pattern_tags.tags if t.code == 49]

    # ---- thanh đứng / ngang
    d_do = ezdxf.readfile(tim_file(a.nguon, "thanh ngang"))
    bd = bbox.extents(list(d_do.modelspace()))
    do_rong = round(min(bd.size.x, bd.size.y), 2)

    out = os.path.join(skill, "lisp", "vkmd_du_lieu.lsp")
    with open(out, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(";;; Dữ liệu block mặt đứng — SINH TỰ ĐỘNG bằng scripts\\tao_du_lieu_md.py, không sửa tay\n")
        f.write(f";;; nguồn: {', '.join(os.path.basename(tim_file(a.nguon, k)) for k in ('md cua di', 'md cua so', 'thanh ngang'))}\n")
        f.write(f"(setq vkmd:dl-do-rong {do_rong})\n")
        f.write(f"(setq vkmd:dl-di-rong {di_rong} vkmd:dl-di-cao {di_cao})\n")
        f.write(f"(setq vkmd:dl-so-rong {round(bc.size.x, 2)} vkmd:dl-so-cao {round(bc.size.y, 2)}"
                f" vkmd:dl-so-do {round(do_duoi.size.y, 2)} vkmd:dl-so-mau {mau_canh})\n")
        f.write(f'(setq vkmd:dl-so-net "{lt_ten}" vkmd:dl-so-net-tile {float(lt_scale)}'
                f" vkmd:dl-so-net-mau '{lisp(lt_mau)})\n")  # danh sách phải có ' (thiếu thì APPLOAD dừng ở đây)
        f.write("(setq vkmd:dl-kinh '" + lisp(kinh) + ")\n")
        f.write("(setq vkmd:dl-cua-di '(\n")
        for x in di:
            f.write("  " + lisp(x) + "\n")
        f.write("))\n")
    print(out)
    print(f"cửa đi lọt lòng {di_rong} x {di_cao}, {len(di)} đối tượng; cửa sổ cánh {bc.size.x:.2f} x {bc.size.y:.2f},"
          f" đố dưới {do_duoi.size.x:.2f} x {do_duoi.size.y:.2f}; nét {lt_ten} tỉ lệ {lt_scale} mẫu {lt_mau};"
          f" kính {len(kinh)} vạch; đố rộng {do_rong}")


if __name__ == "__main__":
    main()
