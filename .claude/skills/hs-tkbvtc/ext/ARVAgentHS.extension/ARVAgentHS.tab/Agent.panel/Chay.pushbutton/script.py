#! python3
# -*- coding: utf-8 -*-
# Nút thử của agent hs-tkbvtc (chỉ nạp khi chay_nen.ps1 thêm extension này, xong thì gỡ). Đọc buoc.txt cạnh thư mục
# extension (1 dòng = đường dẫn file việc JSON) rồi chạy scripts\chay_hs.py của skill.
import locale
locale.setlocale(locale.LC_ALL, "C")
import io, os
_d = os.path.dirname(os.path.abspath(__file__))
for _ in range(5):
    _d = os.path.dirname(_d)            # ...\Chay.pushbutton → Agent.panel → tab → extension → ext → skill
_viec = io.open(os.path.join(_d, "ext", "buoc.txt"), encoding="utf-8-sig").read().strip()
_p = os.path.join(_d, "scripts", "chay_hs.py")
exec(compile(io.open(_p, encoding="utf-8").read(), _p, "exec"),
     {"__revit__": __revit__, "__file__": _p, "__name__": "__main__", "VIEC": _viec})
