# -*- coding: utf-8 -*-
"""Sinh dữ liệu block mặt đứng nhúng vào VKMD.lsp (lisp\\vkmd_du_lieu.lsp) từ các file DXF người dùng cấp.

Đầu vào (thư mục --nguon), tên file chứa:
  - "md cua di"  : mặt đứng cửa đi kính 2 cánh (lọt lòng 1600 x 2699,51, gốc = giữa mép dưới cửa)
  - "md cua so"  : mặt đứng cửa sổ hất (đố dưới 935 x 65 + cánh 935 x 1399,89, tam giác nét HIDDEN)
  - "thanh ngang": thanh đứng / thanh ngang (hình chữ nhật rộng 65)

Đầu ra: lisp\\vkmd_du_lieu.lsp gồm (toạ độ cửa đi so với giữa mép dưới cửa)
  vkmd:dl-cua-di  : hình cửa đi đã PHẲNG HOÁ: ("LW" kín? ((x y bulge) ...)) | ("ARC" cx cy r a1 a2) | ("LINE" x1 y1 x2 y2)
  vkmd:dl-di-kinh : vị trí ký hiệu kính trong cửa đi ((x y) ...)
  vkmd:dl-di-dim  : kích thước của block cửa đi ((layer "_H"/"_V" x1 y1 x2 y2 xdim ydim) ...)
  vkmd:dl-di-chu  : ghi chú (MULTILEADER) của block cửa đi ((chữ x-mũi-tên y-mũi-tên x-chữ y-chữ cao kiểu-chữ layer) ...)
  vkmd:dl-kinh    : 3 vạch ký hiệu kính (block 3 vạch trong file cửa đi, đã nhân tỉ lệ chèn), tâm (0,0) — dùng
                    cho MỌI ô kính (người dùng chốt 29/10/2026: ký hiệu "///" này thể hiện hatch kính)
  vkmd:dl-*       : số đo kiểm tra (lọt lòng cửa đi, cánh cửa sổ, đố)
Giữ nguyên thông tin block cửa đi (người dùng chốt 29/10/2026): ghi chú + kích thước + ký hiệu kính dựng lại
trong lệnh (kích thước bằng DIMLINEAR, ghi chú bằng MLEADER) theo toạ độ đã kéo giãn.

Chạy: python tao_du_lieu_md.py --nguon "<thư mục block vach kinh>"
"""
import argparse
import math
import os
import sys

import ezdxf
from ezdxf import bbox
from ezdxf.math import Matrix44

# khoảng từ mép cánh cửa đi vào đường kích thước chiều cao cửa (ước theo ảnh người dùng gửi 29/10/2026)
DIM_TRONG_CUA = 300.0


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
    """Phẳng hoá đệ quy về LW / ARC / LINE trong hệ toạ độ ma trận m (bỏ ghi chú, kích thước, ký hiệu kính)."""
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


def chu_lisp(s):
    """Chuỗi tiếng Việt -> mã \\U+XXXX (ASCII) để VKMD.lsp chạy được cả LISPSYS = 0; MText hiểu mã này."""
    return "".join(c if ord(c) < 128 else "\\\\U+%04X" % ord(c) for c in s)


def lisp(x):
    if isinstance(x, bool):
        return "T" if x else "nil"
    if isinstance(x, str):
        return '"' + chu_lisp(x) + '"'
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
    ox, oy = (bk.extmin.x + bk.extmax.x) / 2, bk.extmin.y
    goc = Matrix44.translate(-ox, -oy, 0)
    di_rong, di_cao = round(bk.size.x, 2), round(bk.size.y, 2)
    di = []
    phang(d_di, list(msp), goc, di)

    # ký hiệu kính của cửa đi: vị trí trong cửa + hình 3 vạch (nhân tỉ lệ chèn) dùng cho mọi ô kính
    di_kinh, kinh = [], []
    for e in msp.query("INSERT"):
        if la_ky_hieu_kinh(d_di, e):
            di_kinh.append((round(e.dxf.insert.x - ox, 4), round(e.dxf.insert.y - oy, 4)))
            if not kinh:
                m_kinh = Matrix44.translate(-e.dxf.insert.x, -e.dxf.insert.y, 0)
                for x in e.virtual_entities():
                    x.transform(m_kinh)
                    p = list(x.get_points("xy")) if x.dxftype() == "LWPOLYLINE" else [x.dxf.start, x.dxf.end]
                    kinh.append(("LINE", round(p[0][0], 4), round(p[0][1], 4), round(p[-1][0], 4), round(p[-1][1], 4)))

    # kích thước của cửa đi (DIMLINEAR dựng lại): điểm gốc 2 đường gióng + điểm đường kích thước
    di_dim = []
    for e in msp.query("DIMENSION"):
        ang = e.dxf.get("angle", 0.0) or 0.0
        huong = "_V" if abs(abs(ang) % 180 - 90) < 1 else "_H"
        p1, p2, p3 = e.dxf.defpoint2, e.dxf.defpoint3, e.dxf.defpoint
        xd = p3.x - ox
        # dim đứng nằm ngoài cửa (dim cao cửa ở -961) -> đưa vào trong phạm vi cửa, cách mép cánh DIM_TRONG_CUA
        # (người dùng chốt 29/10/2026: "dim chiều cao cửa trong phạm vi của cửa")
        if huong == "_V" and abs(xd) > di_rong / 2:
            xd = math.copysign(di_rong / 2 - DIM_TRONG_CUA, xd)
        di_dim.append((e.dxf.layer, huong, round(p1.x - ox, 4), round(p1.y - oy, 4), round(p2.x - ox, 4),
                       round(p2.y - oy, 4), round(xd, 4), round(p3.y - oy, 4)))

    # ghi chú MULTILEADER: mũi tên = điểm đầu đường dẫn, chữ = điểm cuối (landing)
    di_chu = []
    for e in msp.query("MULTILEADER"):
        c = e.context
        if not (c.mtext and c.leaders and c.leaders[0].lines):
            continue
        dau = c.leaders[0].lines[0].vertices[0]
        cuoi = c.leaders[0].last_leader_point
        kieu = d_di.entitydb.get(c.mtext.style_handle)
        di_chu.append((c.mtext.default_content, round(dau.x - ox, 4), round(dau.y - oy, 4), round(cuoi.x - ox, 4),
                       round(cuoi.y - oy, 4), round(c.char_height, 4), kieu.dxf.name if kieu else "", e.dxf.layer))

    # ---- cửa sổ: đố dưới + cánh
    d_so = ezdxf.readfile(tim_file(a.nguon, "md cua so"))
    ms = d_so.modelspace()
    ten_canh = [e for e in ms.query("INSERT")][0]
    canh = [x for x in ten_canh.virtual_entities() if x.dxftype() == "LWPOLYLINE"][0]
    bc = bbox.extents([canh])
    do_duoi = bbox.extents(list(ms.query("LWPOLYLINE")))
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
        f.write(";;; Mọi danh sách phải có dấu ' (thiếu thì APPLOAD dừng giữa file, lỗi 29/10/2026)\n")
        f.write(f";;; nguồn: {', '.join(os.path.basename(tim_file(a.nguon, k)) for k in ('md cua di', 'md cua so', 'thanh ngang'))}\n")
        f.write(f"(setq vkmd:dl-do-rong {do_rong})\n")
        f.write(f"(setq vkmd:dl-di-rong {di_rong} vkmd:dl-di-cao {di_cao})\n")
        f.write(f"(setq vkmd:dl-so-rong {round(bc.size.x, 2)} vkmd:dl-so-cao {round(bc.size.y, 2)}"
                f" vkmd:dl-so-do {round(do_duoi.size.y, 2)} vkmd:dl-so-mau {mau_canh})\n")
        f.write(f'(setq vkmd:dl-so-net "{lt_ten}" vkmd:dl-so-net-tile {float(lt_scale)}'
                f" vkmd:dl-so-net-mau '{lisp(lt_mau)})\n")
        f.write("(setq vkmd:dl-kinh '" + lisp(kinh) + ")\n")
        f.write("(setq vkmd:dl-di-kinh '" + lisp(di_kinh) + ")\n")
        f.write("(setq vkmd:dl-di-dim '" + lisp(di_dim) + ")\n")
        f.write("(setq vkmd:dl-di-chu '" + lisp(di_chu) + ")\n")
        f.write("(setq vkmd:dl-cua-di '(\n")
        for x in di:
            f.write("  " + lisp(x) + "\n")
        f.write("))\n")
    print(out)
    print(f"cửa đi lọt lòng {di_rong} x {di_cao}, {len(di)} đối tượng, {len(di_kinh)} ký hiệu kính, {len(di_dim)} dim,"
          f" {len(di_chu)} ghi chú; cửa sổ cánh {bc.size.x:.2f} x {bc.size.y:.2f}, đố dưới {do_duoi.size.x:.2f} x"
          f" {do_duoi.size.y:.2f}; nét {lt_ten} tỉ lệ {lt_scale} mẫu {lt_mau}; kính {len(kinh)} vạch; đố rộng {do_rong}")


if __name__ == "__main__":
    main()
