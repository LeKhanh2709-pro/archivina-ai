# -*- coding: utf-8 -*-
r"""Gộp LoMo_ShaftOpening.py = LoMo_ShaftOpening_nguon.py + hằng số nhận trục + khối "PHẦN CHUNG" của NganChay_TrucHKT.py.

Hai công cụ Ngăn cháy lan và Lỗ mở shaft nhận trục / hộp kỹ thuật bằng cùng một quy tắc; Python node của Dynamo phải là
một file độc lập nên phần chung được chép vào khi gộp. Sửa quy tắc nhận trục thì sửa NganChay_TrucHKT.py, sửa phần tạo
lỗ mở thì sửa LoMo_ShaftOpening_nguon.py, rồi chạy lại:
    python gop_lomo_shaft.py
Không sửa tay LoMo_ShaftOpening.py.
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def doc(ten):
    with io.open(os.path.join(HERE, ten), encoding="utf-8") as f:
        return f.read()


def main():
    chung = doc("NganChay_TrucHKT.py")
    nguon = doc("LoMo_ShaftOpening_nguon.py")
    i0 = chung.index("\n# ==== PHẦN CHUNG")
    i1 = chung.index("# ==== HẾT PHẦN CHUNG ====")
    khoi = chung[i0 + 1:i1 + len("# ==== HẾT PHẦN CHUNG ====")]
    h0 = chung.index("\nO_LON_MM = ")
    h1 = chung.index("\n", chung.index("\nTU_SAN_KC = ") + 1)
    hang_so = chung[h0 + 1:h1]
    for moc in ("# @@GHI_CHU_GOP@@", "# @@HANG_SO_CHUNG@@", "# @@PHAN_CHUNG@@"):
        assert nguon.count(moc) == 1, moc
    kq = (nguon.replace("# @@GHI_CHU_GOP@@", "# File gộp tự động bằng gop_lomo_shaft.py – KHÔNG sửa tay "
                                            "(sửa LoMo_ShaftOpening_nguon.py / NganChay_TrucHKT.py rồi gộp lại).")
          .replace("# @@HANG_SO_CHUNG@@", hang_so)
          .replace("# @@PHAN_CHUNG@@", khoi))
    ra = os.path.join(HERE, "LoMo_ShaftOpening.py")
    with io.open(ra, "w", encoding="utf-8") as f:
        f.write(kq)
    print("Da gop: %s (%d dong)" % (ra, kq.count("\n") + 1))


if __name__ == "__main__":
    main()
