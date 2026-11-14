#! python3
# -*- coding: utf-8 -*-
# Bọc thử: đặt biến môi trường rồi chạy ve_legend.py trên bản sao (chỉ dùng khi thử nền)
import os, io
G = r"D:\AI\_tmp\ct_cua_legend"
cfg = io.open(os.path.join(G, "thu_cfg.txt"), encoding="utf-8").read().splitlines()
for dong in cfg:
    if "=" in dong:
        k, v = dong.split("=", 1); os.environ[k.strip()] = v.strip()
p = os.path.join(G, "ve_legend.py")
exec(compile(io.open(p, encoding="utf-8").read(), p, "exec"), {"__revit__": __revit__, "__file__": p, "__name__": "__main__"})
