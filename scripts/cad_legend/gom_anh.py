# -*- coding: utf-8 -*-
r"""Gom ảnh từng ô (kq\anh_o\NN\*.png do thu_anh_o.py xuất) vào thư mục duyệt, đặt tên NN_<tên ô>.png."""
import io, json, os, shutil, glob, sys
G = r"D:\AI\_tmp\ct_cua_legend"
ra = sys.argv[1]
os.makedirs(ra, exist_ok=True)
ten = [o["ten"] for o in json.load(io.open(G + r"\ct_cua.json", encoding="utf-8"))["o"]]
n = 0
for i, t in enumerate(ten):
    fs = glob.glob(os.path.join(G, "kq", "anh_o", "%02d" % (i + 1), "*.png"))
    if not fs:
        print("thiếu ảnh ô", i + 1, t); continue
    sach = "".join(c if c not in '\\/:*?"<>|' else "-" for c in t)
    shutil.copyfile(fs[0], os.path.join(ra, "%02d_%s.png" % (i + 1, sach)))
    n += 1
print("đã chép", n, "ảnh vào", ra)