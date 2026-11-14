# -*- coding: utf-8 -*-
r"""Chép khối "PHẦN CHUNG VÁCH KÍNH" (VachKinh_chung.py) vào các công cụ tag / thống kê có liên quan vách kính.

Python node của Dynamo phải là một file độc lập nên khối chung được chép thẳng vào từng công cụ, giữa 2 mốc. Chưa có mốc thì
chèn ngay trước chuỗi ghi trong DICH. Sửa khối thì sửa VachKinh_chung.py rồi chạy lại:
    python gop_vach_kinh.py
rồi sinh lại nút (scripts\pyrevit\build_from_dynamo.py ... --chi ThongKeCua,TagCua). Bản cũ chép vào <gốc>\_backup trước khi
ghi. Không xoá gì.
"""
import io
import os
import shutil
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
GOC = os.path.dirname(os.path.dirname(HERE))
# file công cụ → chuỗi mở đầu chỗ chèn lần đầu (khối đặt ngay trước chuỗi này)
DICH = {
    "ThongKeCua_TuDong.py": "\ndef _chinh():",
    "TagCua_TuDong.py": "\ndef mark(e):",
}
MOC0 = "# ==== PHẦN CHUNG VÁCH KÍNH"
MOC1 = "# ==== HẾT PHẦN CHUNG VÁCH KÍNH ===="


def doc(duong):
    with io.open(duong, encoding="utf-8", newline="") as f:
        return f.read()


def main(chi=None):
    khoi = doc(os.path.join(HERE, "VachKinh_chung.py")).strip()
    khoi = khoi.replace("\r\n", "\n")
    assert khoi.startswith(MOC0) and khoi.endswith(MOC1)
    for ten, chen in DICH.items():
        if chi and ten not in chi:
            continue
        duong = os.path.join(HERE, ten)
        s = doc(duong)
        xd = "\r\n" if "\r\n" in s else "\n"
        k = khoi.replace("\n", xd)
        if MOC0 in s:
            i0 = s.index(MOC0)
            i1 = s.index(MOC1) + len(MOC1)
            moi = s[:i0] + k + s[i1:]
        else:
            c = chen.replace("\n", xd)
            i = s.index(c)
            moi = s[:i + len(xd)] + k + xd + xd + xd + s[i + len(xd):]
        if moi == s:
            print("Khong doi: %s" % ten)
            continue
        bk = os.path.join(GOC, "_backup", "%s_%s_truoc_vach_kinh_chung.py" % (ten[:-3], datetime.now().strftime("%Y%m%d_%H%M")))
        if not os.path.exists(bk):
            shutil.copy2(duong, bk)
        with io.open(duong, "w", encoding="utf-8", newline="") as f:
            f.write(moi)
        print("Da chep khoi vach kinh vao %s" % ten)


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
