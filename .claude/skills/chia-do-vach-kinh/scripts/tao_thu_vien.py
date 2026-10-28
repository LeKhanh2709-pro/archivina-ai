# -*- coding: utf-8 -*-
"""Tạo thư viện block vách kính sạch (VK_*) từ 3 file DXF người dùng cấp.

Đầu vào (thư mục --nguon), tên file chứa:
  - "thanh dung" : hình thanh đứng (đố) vẽ rời trong model
  - "cua so mo"  : 2 đố (block) + lá cửa sổ mở
  - "cua di"     : 2 đố (block) + lá cửa đi, bản lề, tay nắm

Đầu ra: <out>.dxf chứa block VK_DoDung, VK_CuaSoMo, VK_CuaDi (điểm chèn = tâm đố trái,
vách chạy theo trục X, mọi đối tượng trên layer A-Window, giữ màu / nét như bản gốc)
+ <out>.json ghi khoảng tâm-tâm và vị trí kính đo được.

Chạy: python tao_thu_vien.py --nguon "<thư mục block>" --out "<skill>\\assets\\VK_thu_vien.dxf"
"""
import argparse
import json
import math
import os
import sys

import ezdxf
from ezdxf import bbox
from ezdxf.math import Matrix44

LAYER = "A-Window"
LAYER_DIM = "A-Dimension"
DIMSTYLE = "dim cua"


def ten_sach(name):
    """Bỏ tiền tố xref đã bind: 'Xref-...$0$CENTER2' -> 'CENTER2'."""
    return name.split("$")[-1] if "$" in name else name


def chuan_do(doc, ins):
    """Ma trận đưa thế giới về hệ chuẩn của đố `ins`: tâm đố = gốc, bề rộng đố theo X,
    chiều sâu theo Y (mặt kẹp kính hướng +Y)."""
    blk = doc.blocks.get(ins.dxf.name)
    c = bbox.extents(blk).center
    mi = ins.matrix44()
    mi.inverse()  # ezdxf: đảo ngược tại chỗ
    return Matrix44.chain(mi, Matrix44.translate(-c.x, -c.y, 0), Matrix44.z_rotate(math.pi / 2))


class Phang:
    """Nổ đệ quy, giải màu / nét BYLAYER / BYBLOCK thành giá trị cụ thể, đưa về layer A-Window."""

    def __init__(self, src, dst):
        self.src, self.dst = src, dst

    def thuoc_tinh_layer(self, layer):
        lay = self.src.layers.get(layer) if self.src.layers.has_entry(layer) else None
        if lay is None:
            return 7, None, "Continuous"
        return abs(lay.dxf.color), lay.dxf.get("true_color"), lay.dxf.linetype

    def dam_bao_linetype(self, name):
        sach = ten_sach(name)
        if sach.upper() in ("CONTINUOUS", "BYLAYER", "BYBLOCK"):
            return "Continuous"
        if self.dst.linetypes.has_entry(sach):
            return sach
        if not self.src.linetypes.has_entry(name):
            return "Continuous"
        lt = self.src.linetypes.get(name)
        if lt.pattern_tags.is_complex_type():  # nét có chữ / hình: không chép đơn giản được
            return "Continuous"
        dash = [t.value for t in lt.pattern_tags.tags if t.code == 49]
        if not dash:
            return "Continuous"
        self.dst.linetypes.add(sach, pattern=[sum(abs(x) for x in dash)] + dash, description=lt.dxf.description)
        return sach

    def chay(self, ents, m, cha=None):
        """ents: thực thể trong hệ cha; m: ma trận cha -> hệ chuẩn; cha: (layer, color, true_color, linetype)."""
        out = []
        for e in ents:
            if e.dxftype() == "HATCH":  # bỏ hatch trong block vách kính (người dùng chốt 28/10/2026)
                continue
            layer = e.dxf.layer
            if cha and layer == "0":
                layer = cha[0]
            l_col, l_tc, l_lt = self.thuoc_tinh_layer(layer)
            col = e.dxf.get("color", 256)
            tc = e.dxf.get("true_color")
            if col == 256 and tc is None:
                col, tc = l_col, l_tc
            elif col == 0 and cha:
                col, tc = cha[1], cha[2]
            lt = e.dxf.get("linetype", "BYLAYER")
            if lt.upper() == "BYLAYER":
                lt = l_lt
            elif lt.upper() == "BYBLOCK" and cha:
                lt = cha[3]
            if e.dxftype() == "INSERT":
                con = list(e.virtual_entities())
                out += self.chay(con, m, (layer, col, tc, lt))
                continue
            v = e.copy()
            try:
                v.transform(m)
            except Exception as ex:  # thực thể không biến đổi được: báo, không bỏ im lặng
                print(f"  ! bỏ {e.dxftype()} ({ex})", file=sys.stderr)
                continue
            v.dxf.layer = LAYER
            v.dxf.color = col if col not in (0, 256) else 7
            if tc is not None:
                v.dxf.true_color = tc
            elif v.dxf.hasattr("true_color"):
                v.dxf.discard("true_color")
            v.dxf.linetype = self.dam_bao_linetype(lt)
            out.append(v)
        return out


def tim_file(nguon, khoa):
    for f in os.listdir(nguon):
        if f.lower().endswith(".dxf") and khoa in f.lower():
            return os.path.join(nguon, f)
    sys.exit(f"Không thấy file DXF có chữ '{khoa}' trong {nguon}")


def nhom_cua(path, phang_cls, dst):
    """Cửa sổ / cửa đi: 2 đố (INSERT cùng tên, có tên block xuất hiện 2 lần) + phần còn lại."""
    src = ezdxf.readfile(path)
    msp = src.modelspace()
    dem = {}
    for i in msp.query("INSERT"):
        dem.setdefault(i.dxf.name, []).append(i)
    # đố = block xuất hiện đúng 2 lần, bao ~65 x ~187
    do = None
    for name, lst in dem.items():
        if len(lst) == 2:
            s = bbox.extents(src.blocks.get(name)).size
            if 60 < min(s.x, s.y) < 70 and 150 < max(s.x, s.y) < 220:
                do = lst
    if not do:
        sys.exit(f"Không nhận được 2 đố trong {path}")
    for ref in do:
        m = chuan_do(src, ref)
        o = [x for x in do if x is not ref][0]
        p = m.transform(o.matrix44().transform(bbox.extents(src.blocks.get(o.dxf.name)).center))
        if p.x > 0:
            break
    rong = round(p.x, 3)
    if abs(p.y) > 0.5:
        print(f"  ! 2 đố lệch nhau theo chiều sâu {p.y:.2f} mm", file=sys.stderr)
    ents = phang_cls(src, dst).chay(list(msp), m)
    return ents, rong


def kinh_cua_so(ents):
    """Các tấm kính của lá cửa sổ: LWPOLYLINE dài > 300 song song trục X."""
    tam = []
    for e in ents:
        if e.dxftype() == "LWPOLYLINE":
            b = bbox.extents([e])
            if b.size.x > 300 and b.size.y < 20:
                tam.append((round(b.extmin.y, 2), round(b.extmax.y, 2), e.dxf.color))
    return sorted(set(tam))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Tạo thư viện block vách kính VK_* từ DXF người dùng cấp")
    ap.add_argument("--nguon", required=True, help="thư mục chứa 3 file DXF block")
    ap.add_argument("--out", required=True, help="file DXF thư viện (không ghi đè)")
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f"Đã tồn tại, không ghi đè: {a.out} (chép vào _backup rồi xoá tay nếu muốn tạo lại)")

    f_do = tim_file(a.nguon, "thanh dung")
    f_so = tim_file(a.nguon, "cua so")
    f_di = tim_file(a.nguon, "cua di")

    dst = ezdxf.new("R2018", setup=True)
    dst.units = 4  # mm
    src0 = ezdxf.readfile(f_do)
    lw = src0.layers.get(LAYER)
    dst.layers.add(LAYER, color=lw.dxf.color, linetype="Continuous")

    # thanh đứng: vẽ rời trong model, cùng hệ với block đố (bề sâu theo X, bề rộng theo Y)
    msp0 = list(src0.modelspace())
    c = bbox.extents(msp0).center
    m0 = Matrix44.chain(Matrix44.translate(-c.x, -c.y, 0), Matrix44.z_rotate(math.pi / 2))
    e_do = Phang(src0, dst).chay(msp0, m0)
    b_do = bbox.extents(e_do)

    e_so, rong_so = nhom_cua(f_so, Phang, dst)
    e_di, rong_di = nhom_cua(f_di, Phang, dst)

    # kiểu kích thước cửa "dim cua" (+ kiểu chữ) và layer A-Dimension của bản gốc
    from ezdxf.addons import Importer
    imp = Importer(src0, dst)
    imp.import_tables("styles", "*")
    if src0.dimstyles.has_entry(DIMSTYLE):
        imp.import_tables("dimstyles", [DIMSTYLE])
    if src0.layers.has_entry(LAYER_DIM):
        imp.import_tables("layers", [LAYER_DIM])
    imp.finalize()

    for name, ents in (("VK_DoDung", e_do), ("VK_CuaSoMo", e_so), ("VK_CuaDi", e_di)):
        blk = dst.blocks.new(name, base_point=(0, 0))
        for e in ents:
            blk.add_entity(e)

    info = {
        "nguon": {"thanh_dung": os.path.basename(f_do), "cua_so": os.path.basename(f_so), "cua_di": os.path.basename(f_di)},
        "do_dung": {"block": "VK_DoDung", "rong_do_duoc": round(b_do.size.x, 2), "sau_do_duoc": round(b_do.size.y, 2)},
        "cua_so": {"block": "VK_CuaSoMo", "tam_tam": rong_so},
        "cua_di": {"block": "VK_CuaDi", "tam_tam": rong_di},
        "kinh_cua_so": kinh_cua_so(e_so),
        "ghi_chu": "Điểm chèn = tâm đố trái; vách theo trục X; Y = chiều sâu đố (mặt kẹp kính +Y).",
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    dst.saveas(a.out)
    with open(os.path.splitext(a.out)[0] + ".json", "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print(json.dumps(info, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
