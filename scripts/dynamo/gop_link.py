# -*- coding: utf-8 -*-
r"""Chép khối "PHẦN CHUNG FILE LINK" (Link_chung.py) vào các công cụ cần đọc đối tượng trong file link.

Python node của Dynamo phải là một file độc lập nên khối chung được chép thẳng vào từng công cụ, giữa 2 mốc. Chưa có mốc thì
chèn ngay trước "def _chinh(" hoặc mốc CHEN trong DICH. Sửa khối thì sửa Link_chung.py rồi chạy lại:
    python gop_link.py
Bản cũ chép vào <gốc>\_backup trước khi ghi. Không xoá gì.
"""
import io
import os
import shutil
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
GOC = os.path.dirname(os.path.dirname(HERE))
# file công cụ → chuỗi mở đầu chỗ chèn lần đầu
DICH = {
    "ChongTham_VeVenChanTuong.py": "\n# ---------- cửa ----------\n",
    "NganChay_TrucHKT.py": "\n# ---------- quét lưới dấu chân tường ----------\n",
    "TagCua_TuDong.py": "\ndef mark(e):",
    "LanCanLouver_TuDong.py": "\ndef mark(e):",
    "ThongKeCua_TuDong.py": "\ndef dem_trong_view(",
    "ThongKeLanCan_TuDong.py": "\ndef mark(e):",
    "ChiTietCua_TuDong.py": None,
    "ARV_MBTuongXayTang_v1.py": "\ndef collect_walls(level):",
    "LoMo_ShaftOpening_nguon.py": None,
}
MOC0 = "# ==== PHẦN CHUNG FILE LINK"
MOC1 = "# ==== HẾT PHẦN CHUNG FILE LINK ===="


def doc(duong):
    with io.open(duong, encoding="utf-8", newline="") as f:
        return f.read()


def main(chi=None):
    khoi = doc(os.path.join(HERE, "Link_chung.py")).strip()
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
            if chen is None:
                print("Bo qua (chua co moc): %s" % ten)
                continue
            c = chen.replace("\n", xd)
            i = s.index(c)
            moi = s[:i + len(xd)] + k + xd + xd + xd + s[i + len(xd):]
        if moi == s:
            print("Khong doi: %s" % ten)
            continue
        bk = os.path.join(GOC, "_backup", "%s_%s_truoc_link.py" % (ten[:-3], datetime.now().strftime("%Y%m%d_%H%M")))
        if not os.path.exists(bk):
            shutil.copy2(duong, bk)
        with io.open(duong, "w", encoding="utf-8", newline="") as f:
            f.write(moi)
        print("Da chep khoi link vao %s" % ten)


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
