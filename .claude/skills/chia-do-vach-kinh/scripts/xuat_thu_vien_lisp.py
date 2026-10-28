# -*- coding: utf-8 -*-
"""Tạo file thư viện cho lệnh LISP VK từ assets\\VK_thu_vien.dxf.

LISP nạp block bằng "-INSERT <file.dwg>" rồi huỷ ở bước chọn điểm: chỉ các định nghĩa được tham chiếu
trong model của file mới chắc chắn được chép sang. Vì vậy file này đặt sẵn trong model 1 bản chèn của
mỗi block VK_* và 1 kích thước kiểu "dim cua" (kéo theo kiểu chữ, mũi tên).

Chạy: python xuat_thu_vien_lisp.py --out "<skill>\\assets\\VK_thu_vien_lisp.dxf"
rồi dxf_to_dwg.ps1 -Dxf ... -OutDwg "<skill>\\assets\\VK_thu_vien.dwg"
"""
import argparse
import os
import sys

import ezdxf
from ezdxf.addons import Importer


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    skill = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description="Tạo file thư viện block cho lệnh LISP VK")
    ap.add_argument("--thu-vien", default=os.path.join(skill, "assets", "VK_thu_vien.dxf"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f"Đã tồn tại, không ghi đè: {a.out}")
    tv = ezdxf.readfile(a.thu_vien)
    doc = ezdxf.new("R2018")
    doc.units = 4
    imp = Importer(tv, doc)
    imp.import_blocks(["VK_DoDung", "VK_CuaSoMo", "VK_CuaDi"])
    imp.import_tables("layers", ["A-Window"])
    ds = tv.dimstyles.get("dim cua")
    imp.import_tables("styles", [ds.dxf.dimtxsty])
    imp.import_tables("dimstyles", ["dim cua"])
    imp.finalize()
    msp = doc.modelspace()
    for i, name in enumerate(["VK_DoDung", "VK_CuaSoMo", "VK_CuaDi"]):
        msp.add_blockref(name, (0, -1000 * i), dxfattribs={"layer": "A-Window"})
    d = msp.add_aligned_dim(p1=(0, 1000), p2=(1000, 1000), distance=200, dimstyle="dim cua",
                            dxfattribs={"layer": "Defpoints"})
    d.render()
    doc.saveas(a.out)
    print(a.out, "blocks:", [b.name for b in doc.blocks if not b.name.startswith("*")])


if __name__ == "__main__":
    main()
