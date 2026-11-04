# -*- coding: utf-8 -*-
r"""Chép khối "PHẦN CHUNG ĐẶT SHEET" (DatSheet_chung.py) vào các công cụ cần đặt mặt bằng lên bản vẽ.

Python node của Dynamo phải là một file độc lập nên khối chung được chép thẳng vào từng file công cụ, giữa 2 dòng mốc
"# ==== PHẦN CHUNG ĐẶT SHEET" … "# ==== HẾT PHẦN CHUNG ĐẶT SHEET ====" (chưa có mốc thì chèn ngay trước "def xuat_anh(").
Sửa phần đặt sheet thì sửa DatSheet_chung.py rồi chạy lại:
    python gop_dat_sheet.py
Phần còn lại của file công cụ không bị đụng tới. Bản cũ chép vào <gốc>\_backup trước khi ghi.
"""
import io
import os
import shutil
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
GOC = os.path.dirname(os.path.dirname(HERE))
DICH = ["ChongTham_VeVenChanTuong.py", "NganChay_TrucHKT.py"]
MOC0 = "# ==== PHẦN CHUNG ĐẶT SHEET"
MOC1 = "# ==== HẾT PHẦN CHUNG ĐẶT SHEET ===="


def doc(duong):
    with io.open(duong, encoding="utf-8", newline="") as f:
        return f.read()


def main():
    khoi = doc(os.path.join(HERE, "DatSheet_chung.py")).strip("\n")
    assert khoi.startswith(MOC0) and khoi.endswith(MOC1)
    for ten in DICH:
        duong = os.path.join(HERE, ten)
        s = doc(duong)
        if MOC0 in s:
            i0 = s.index(MOC0)
            i1 = s.index(MOC1) + len(MOC1)
            moi = s[:i0] + khoi + s[i1:]
        else:
            i = s.index("\ndef xuat_anh(")
            moi = s[:i + 1] + khoi + "\n\n\n" + s[i + 1:]
        if moi == s:
            print("Khong doi: %s" % ten)
            continue
        bk = os.path.join(GOC, "_backup", "%s_%s.py" % (ten[:-3], datetime.now().strftime("%Y%m%d_%H%M%S")))
        shutil.copy2(duong, bk)
        with io.open(duong, "w", encoding="utf-8", newline="") as f:
            f.write(moi)
        print("Da chep khoi dat sheet vao %s (ban cu: %s)" % (ten, bk))


if __name__ == "__main__":
    main()
